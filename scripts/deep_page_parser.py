#!/usr/bin/env python3
"""
500.com Deep Analysis Page Parser v3.0
=======================================
Parses ALL data from raw GB2312 HTML of 6 deep analysis pages:
  ouzhi   - 百家欧赔: SPF + Kelly + probability% + return rate + dispersion (30+ bookmakers)
  yazhi   - 亚盘对比: handicap + water level + change timestamps (17+ companies)
  rangqiu - 让球指数: RQSPF including 竞彩 official odds
  daxiao  - 大小指数: OU line + water level + change timestamps (18+ companies)
  shuju   - 数据分析: pre-match info, H2H, form, lineup
  touzhu  - 投注分析: Betfair volume, P&L, hot/cold index, simulated P&L, distribution

Usage:
  python3 deep_page_parser.py --page ouzhi --html path/to/raw.html [--json]
  python3 deep_page_parser.py --page all --date 2026-06-12 --cache-dir ~/.cache/shared-football
"""

import re
import json
import os
import sys
import argparse
from collections import OrderedDict

# ─── GB2312 → UTF-8 解码 ───────────────────────────────────
def decode_gb2312(raw_bytes):
    """Decode GB2312 bytes to UTF-8 string."""
    try:
        return raw_bytes.decode('gb2312', errors='replace')
    except:
        return raw_bytes.decode('gbk', errors='replace')

def read_html_file(filepath):
    """Read GB2312 HTML file and return UTF-8 decoded string."""
    with open(filepath, 'rb') as f:
        raw = f.read()
    return decode_gb2312(raw)

# ─── Ouzhi (百家欧赔) Parser ────────────────────────────────
def parse_ouzhi(html_text):
    """
    Extract ALL bookmaker data from ouzhi page.

    Table structure per bookmaker row:
      td.tb_plgs: name (title attr = full name)
      td: open SPF H/D/A (3 consecutive TDs, may contain span.odds_chart)
      td: current SPF H/D/A (3 TDs)
      td: open probability% H/D/A (3 TDs, has class="plgreen")
      td: current probability% H/D/A (3 TDs)
      td: return rate% open/current (2 TDs)
      td: current Kelly H/D/A (3 TDs, has class="bd_red/blue/green")

    Summary row: average / max / min / dispersion (离散值)

    Returns: {bookmakers: [...], pinnacle: {...}, jingcai: {...}|null, summary: {...}}
    """
    result = {"bookmakers": [], "jingcai_spf": None, "pinnacle": None, "summary": {}}

    # Extract bookmaker rows
    # Each row: <td row="1" class="tb_plgs" title="COMPANY_NAME">
    # Followed by data cells
    row_pattern = re.compile(
        r'<td\s+row="1"\s+class="tb_plgs"\s+title="([^"]*)"[^>]*>.*?</td>',
        re.DOTALL
    )

    # Extract all <tr> blocks containing bookmaker data
    tr_blocks = re.findall(r'<tr[^>]*>(.*?)</tr>', html_text, re.DOTALL)

    bookmakers = []
    for tr in tr_blocks:
        name_match = re.search(r'class="tb_plgs"\s+title="([^"]*)"', tr)
        if not name_match:
            continue
        name = name_match.group(1).strip()

        # Extract all number values from the row (in order)
        # Numbers appear as: plain text, or inside <span>, or inside <em>
        values = re.findall(r'(?:>|^)\s*([\d.]+)\s*(?:<|$)', tr)

        if len(values) < 14:
            continue  # Not a valid data row

        # Row format (17 values per bookmaker):
        # [open_h, open_d, open_a, curr_h, curr_d, curr_a,
        #  prob_open_h, prob_open_d, prob_open_a, prob_curr_h, prob_curr_d, prob_curr_a,
        #  return_open, return_curr, kelly_h, kelly_d, kelly_a]
        # But we extract ALL numbers and map by position

        try:
            # The exact position mapping depends on the order extracted
            # Let's use a more robust approach: find bookmaker index, then parse structured
            cid_match = re.search(r'cid=(\d+)', tr)
            cid = int(cid_match.group(1)) if cid_match else 0

            # Extract SPF data (open + current) - look for odds data pattern
            spf_data = re.findall(r'([\d.]+)\s*\n', tr)

            # More precise extraction: look for the data pattern
            # Format: open_h open_d open_a current_h current_d current_a
            #          prob_open% prob_open% prob_open% prob_curr% prob_curr% prob_curr%
            #          return_open% return_curr% kelly_h kelly_d kelly_a

            all_nums = [float(v) for v in re.findall(r'([\d.]+)', tr)]

            bm = {
                "name": name,
                "cid": cid,
            }

            # We need at minimum SPF (6 numbers: open×3 + current×3)
            if len(all_nums) >= 6:
                bm["spf_open"] = {"home": all_nums[0], "draw": all_nums[1], "away": all_nums[2]}
                bm["spf_current"] = {"home": all_nums[3], "draw": all_nums[4], "away": all_nums[5]}

            # If we have 14+ numbers, we have probability + return + kelly
            if len(all_nums) >= 14:
                bm["prob_open"] = {"home": all_nums[6], "draw": all_nums[7], "away": all_nums[8]}
                bm["prob_current"] = {"home": all_nums[9], "draw": all_nums[10], "away": all_nums[11]}
                bm["return_rate_open"] = all_nums[12]
                bm["return_rate_current"] = all_nums[13]

            if len(all_nums) >= 17:
                bm["kelly_current"] = {"home": all_nums[14], "draw": all_nums[15], "away": all_nums[16]}

            bookmakers.append(bm)

        except (ValueError, IndexError):
            continue

    result["bookmakers"] = bookmakers

    # Find Pinnacle (title contains "Pinnacle" or "Pi****le" or cid=1055)
    for bm in bookmakers:
        if bm.get("cid") == 1055 or "innacle" in bm.get("name", "").lower() or "Pi" in bm.get("name", ""):
            result["pinnacle"] = bm
            break

    # Find 竞彩官方 (title contains "竞*官*" or cid=1 with country 中国)
    for bm in bookmakers:
        if "竞" in bm.get("name", "") or bm.get("cid") == 1:
            result["jingcai_spf"] = bm
            break

    # Extract summary row (平均值/最高值/最低值/离散值)
    summary_match = re.search(
        r'平均值.*?([\d.]+).*?([\d.]+).*?([\d.]+).*?([\d.]+).*?([\d.]+).*?([\d.]+)',
        html_text, re.DOTALL
    )
    if summary_match:
        result["summary"]["avg_spf_current"] = {
            "home": float(summary_match.group(1)),
            "draw": float(summary_match.group(2)),
            "away": float(summary_match.group(3)),
        }
        result["summary"]["avg_spf_open"] = {
            "home": float(summary_match.group(4)),
            "draw": float(summary_match.group(5)),
            "away": float(summary_match.group(6)),
        }

    # Extract dispersion (离散值)
    disp_match = re.search(r'离散值\s*([\d.]+)\s*([\d.]+)\s*([\d.]+)', html_text)
    if disp_match:
        result["summary"]["dispersion"] = {
            "home": float(disp_match.group(1)),
            "draw": float(disp_match.group(2)),
            "away": float(disp_match.group(3)),
        }

    result["total_bookmakers"] = len(bookmakers)
    return result


# ─── Yazhi (亚盘对比) Parser ─────────────────────────────────
def parse_yazhi(html_text):
    """
    Extract ALL Asian Handicap data from yazhi page.

    Table structure per company row:
      td.tb_plgs: company name
      Current: water_h / handicap / water_a | change_time
      Open: water_h / handicap / water_a | open_time (if different)

    Handicap format: 半球=0.5, 平手/半球=0.25, 受半球=-0.5, etc.
    Water level format: 0.92, 1.05, etc.

    Returns: {companies: [...], pinnacle: {...}, summary: {...}}
    """
    result = {"companies": [], "pinnacle": None, "summary": {}}

    # Find all company rows
    tr_blocks = re.findall(r'<tr[^>]*>(.*?)</tr>', html_text, re.DOTALL)

    companies = []
    for tr in tr_blocks:
        name_match = re.search(r'class="tb_plgs"\s+title="([^"]*)"', tr)
        if not name_match:
            continue
        name = name_match.group(1).strip()

        cid_match = re.search(r'cid=(\d+)', tr)
        cid = int(cid_match.group(1)) if cid_match else 0

        # Extract all numeric values and handicap strings
        # Pattern: water values (0.xx-1.xx), handicap values (integers or fractions)
        water_vals = re.findall(r'([\d.]+)\s*[↑↓]', tr)  # water with arrow
        if not water_vals:
            water_vals = re.findall(r'>([\d.]+)<', tr)

        # Extract handicap strings
        handicap_strs = re.findall(r'([\d./]+半|平手/\S+|受\S+半|\S+半/\S+|[\d]+\s*\n)', tr)

        # Simpler approach: extract all numbers from the row
        all_nums = [float(v) for v in re.findall(r'([\d.]+)', tr) if 0.01 < float(v) < 3.0]

        co = {"name": name, "cid": cid}

        # Current water and handicap (first few numbers)
        if len(all_nums) >= 2:
            co["current_water_home"] = all_nums[0]
            co["current_water_away"] = all_nums[1]
            # Handicap is between water values, need to parse separately

        # Extract handicap from text
        hcap_match = re.search(r'([受平手半/\d]+球半?)', tr)
        if hcap_match:
            co["current_handicap_str"] = hcap_match.group(1).strip()

        companies.append(co)

    result["companies"] = companies

    # Find Pinnacle
    for co in companies:
        if co.get("cid") == 1055 or "innacle" in co.get("name", "").lower() or "Pi" in co.get("name", ""):
            result["pinnacle"] = co
            break

    result["total_companies"] = len(companies)
    return result


# ─── Rangqiu (让球指数) Parser ───────────────────────────────
def parse_rangqiu(html_text):
    """
    Extract RQSPF data including 竞彩 official odds from rangqiu page.

    Key row: "竞*官*" (row 1) - 竞彩官方让球胜平负赔率
    Format per row:
      Company name | [handicap][open_h][open_d][open_a][curr_h][curr_d][curr_a]
      All numbers concatenated without separators!

    Example: "-12.253.182.702.003.253.11"
      → handicap=-1, open=2.25/3.18/2.70, current=2.00/3.25/3.11

    Returns: {jingcai_rqspf: {...}, bookmakers: [...]}
    """
    result = {"jingcai_rqspf": None, "bookmakers": []}

    tr_blocks = re.findall(r'<tr[^>]*>(.*?)</tr>', html_text, re.DOTALL)

    for tr in tr_blocks:
        name_match = re.search(r'class="tb_plgs"\s+title="([^"]*)"', tr)
        if not name_match:
            continue
        name = name_match.group(1).strip()

        # Extract the concatenated number string after the company name cell
        # The format: handicap sign + digit, followed by 6 three-decimal numbers
        # Example: -12.253.182.702.003.253.11
        num_block = re.search(r'(-?\d)\s*(?:([\d.]{3,}))', tr)
        if not num_block:
            continue

        # Get the text content after the company name cell
        text = re.sub(r'<[^>]+>', ' ', tr)
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove the company name part
        text_without_name = text.replace(name, '', 1).strip()

        # Parse handicap + odds
        parsed = _parse_rqspf_number_block(text_without_name)
        if parsed:
            bm = {"name": name, **parsed}
            result["bookmakers"].append(bm)

            if "竞" in name:
                result["jingcai_rqspf"] = bm

    return result


def _parse_rqspf_number_block(text):
    """Parse RQSPF number block like '-12.253.182.702.003.253.11'"""
    # Remove spaces and extract the pattern
    text = re.sub(r'\s+', '', text)

    # Match: optional sign + digit, followed by 6 floating point numbers
    # The handicap is: sign + 1 digit
    # Then 6 odds values (each 1-3 digits before decimal + 2 digits after)
    match = re.match(r'^([+-]?\d)([\d.]+)$', text)
    if not match:
        return None

    handicap = int(match.group(1))
    rest = match.group(2)

    # Try to split 6 odds values
    odds = re.findall(r'(\d+\.\d{2})', rest)
    if len(odds) >= 6:
        return {
            "handicap": handicap,
            "open": {"home": float(odds[0]), "draw": float(odds[1]), "away": float(odds[2])},
            "current": {"home": float(odds[3]), "draw": float(odds[4]), "away": float(odds[5])},
        }

    return None


# ─── Daxiao (大小指数) Parser ────────────────────────────────
def parse_daxiao(html_text):
    """
    Extract OU (Over/Under) data from daxiao page.

    Table structure per company row:
      Company name | current_over_water / line / under_water | change_time
                    | open_over_water / line / under_water | open_time

    Returns: {companies: [...], summary: {...}}
    """
    result = {"companies": [], "summary": {}}

    tr_blocks = re.findall(r'<tr[^>]*>(.*?)</tr>', html_text, re.DOTALL)

    companies = []
    for tr in tr_blocks:
        name_match = re.search(r'class="tb_plgs"\s+title="([^"]*)"', tr)
        if not name_match:
            continue
        name = name_match.group(1).strip()

        cid_match = re.search(r'cid=(\d+)', tr)
        cid = int(cid_match.group(1)) if cid_match else 0

        # Extract numbers
        nums = re.findall(r'([\d.]+)', tr)
        nums = [float(n) for n in nums if 0.01 < float(n) < 100]

        co = {"name": name, "cid": cid}

        # First numbers are over_water, line, under_water (current)
        if len(nums) >= 3:
            co["current_over_water"] = nums[0]
            co["current_under_water"] = nums[1]
            # Line is in the middle format like "2/2.5" or "2.5"
            line_match = re.search(r'([\d./]+)\s*[↓↑]?', re.sub(r'<[^>]+>', '', tr))
            # Get the text between water values for line
            water_text = re.sub(r'<[^>]+>', ' ', tr)
            water_parts = re.split(r'[\d.]+\s*[↑↓]', water_text)
            for part in water_parts:
                part = part.strip()
                if re.match(r'^[\d./]+$', part):
                    co["current_line_str"] = part
                    break

        if len(nums) >= 6:
            co["open_over_water"] = nums[3]
            co["open_under_water"] = nums[4]

        companies.append(co)

    result["companies"] = companies

    # Summary
    avg_match = re.search(r'共(\d+)家公司', html_text)
    if avg_match:
        result["total_companies"] = int(avg_match.group(1))
    else:
        result["total_companies"] = len(companies)

    return result


# ─── Shuju (数据分析) Parser ─────────────────────────────────
def parse_shuju(html_text):
    """
    Extract pre-match analysis data from shuju page.
    v2.6 fields: formation, key_absences, form_trend, avg_goals, etc.
    """
    result = {"pre_match_info": {}}

    # FIFA ranking
    rank_match = re.search(r'\[世(\d+)\]', html_text)
    if rank_match:
        result["home_rank"] = int(rank_match.group(1))

    away_rank_match = re.search(r'客.*?\[世(\d+)\]', html_text)
    if away_rank_match:
        result["away_rank"] = int(away_rank_match.group(1))

    # H2H
    h2h_match = re.search(
        r'双方近(\d+)次交战[，,]\s*(\S+?)\s*(\d+)胜(\d+)平(\d+)负[，,]\s*进(\d+)球[，,]\s*失(\d+)球',
        html_text
    )
    if h2h_match:
        result["h2h"] = {
            "matches": int(h2h_match.group(1)),
            "team": h2h_match.group(2),
            "wins": int(h2h_match.group(3)),
            "draws": int(h2h_match.group(4)),
            "losses": int(h2h_match.group(5)),
            "goals_for": int(h2h_match.group(6)),
            "goals_against": int(h2h_match.group(7)),
        }

    # Recent form (近10场)
    form_match = re.search(
        r'近(\d+)场战绩[：:]?\s*(\d+)胜(\d+)平(\d+)负[，,]?\s*进(\d+)球[，,]?\s*失(\d+)球',
        html_text
    )
    if form_match:
        result["recent_form"] = {
            "matches": int(form_match.group(1)),
            "wins": int(form_match.group(2)),
            "draws": int(form_match.group(3)),
            "losses": int(form_match.group(4)),
            "goals_for": int(form_match.group(5)),
            "goals_against": int(form_match.group(6)),
        }

    # Lineup / Injuries
    # Look for starters, injuries, suspensions
    injury_pattern = re.findall(r'(停赛|伤病|伤缺|缺席)[：:]*\s*([^<\n]{2,20})', html_text)
    if injury_pattern:
        result["key_absences"] = []
        for reason, name in injury_pattern:
            result["key_absences"].append({"name": name.strip(), "reason": reason})

    # Formation
    formation_match = re.search(r'(\d-\d-\d)', html_text)
    if formation_match:
        result["formation"] = formation_match.group(1)

    return result


# ─── Touzhu (投注分析) Parser ─────────────────────────────────
def parse_touzhu(html_text):
    """
    Extract Betfair exchange data, hot/cold index, and simulated P&L from touzhu page.

    Data sections:
      1. 热度分析 (Hot/Cold Analysis) - 百家欧赔 vs 必发指数 comparison table
      2. 必发指数 (Betfair Index) - ECharts charts with embedded data
      3. 必发大额交易 (Large Transactions) - detailed transaction records
      4. 模拟盈亏 (Simulated P&L) - bookmaker P&L simulation

    Returns: {betfair: {...}, hot_cold: {...}, large_transactions: [...], simulated_pl: {...}}
    """
    result = {
        "betfair": {"home": {}, "draw": {}, "away": {}},
        "hot_cold_index": {},
        "large_transactions": [],
        "simulated_pl": [],
        "summary": "",
    }

    # ── 热度分析 table ──
    # Extract the hot/cold analysis table
    hot_table = re.search(r'热度分析.*?<table[^>]*>(.*?)</table>', html_text, re.DOTALL)
    if hot_table:
        table_html = hot_table.group(1)
        # Parse rows: each has <td> elements
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)

        # Data rows: odd text between <td> tags
        for row_text in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row_text, re.DOTALL)
            cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]

            if len(cells) >= 10:
                outcome = cells[0]  # 主胜/平局/客胜
                if outcome in ["主胜", "平局", "客胜"]:
                    key = "home" if "主" in outcome else ("away" if "客" in outcome else "draw")

                    result["betfair"][key] = {
                        "euro_odds": cells[1] if cells[1] else None,
                        "euro_prob_pct": cells[2] if cells[2] else None,
                        "betfair_price": cells[5] if len(cells) > 5 else None,
                        "betfair_volume": cells[6] if len(cells) > 6 else None,
                        "bookmaker_pl": cells[7] if len(cells) > 7 else None,
                    }

        # Summary row
        for row_text in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row_text, re.DOTALL)
            cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
            if "数据提点" in row_text or "交易规模" in row_text or "过热" in row_text:
                for c in cells:
                    if len(c) > 10:
                        result["summary"] = c
                        break

    # ── 必发大额交易明细 ──
    large_trade_section = re.search(r'必发大额交易明细.*?<table[^>]*>(.*?)</table>', html_text, re.DOTALL)
    if large_trade_section:
        table_html = large_trade_section.group(1)
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
        for row_text in rows[1:]:  # Skip header
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row_text, re.DOTALL)
            cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
            if len(cells) >= 5:
                result["large_transactions"].append({
                    "outcome": cells[0],
                    "side": cells[1],
                    "volume": cells[2],
                    "time": cells[3],
                    "ratio_pct": cells[4],
                })

    # ── 模拟盈亏 ──
    pl_section = re.search(r'模拟盈亏.*?<table[^>]*>(.*?)</table>', html_text, re.DOTALL)
    if pl_section:
        table_html = pl_section.group(1)
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
        for row_text in rows[1:]:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row_text, re.DOTALL)
            cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
            if len(cells) >= 3:
                result["simulated_pl"].append(cells)

    # ── Hot/Cold Index ──
    # Extract index numbers from the hot/cold table
    index_match = re.findall(r'必发指数.*?<td[^>]*>(\d+)</td>', html_text)
    if len(index_match) >= 3:
        result["hot_cold_index"] = {
            "home": int(index_match[0]) if len(index_match) > 0 else None,
            "draw": int(index_match[1]) if len(index_match) > 1 else None,
            "away": int(index_match[2]) if len(index_match) > 2 else None,
        }

    # ── Volume totals ──
    total_volume = re.search(r'总交易额[：:]?\s*([\d,]+)', html_text)
    if total_volume:
        result["total_volume"] = total_volume.group(1).replace(',', '')

    # Distribution percentages
    dist_match = re.findall(r'(\d+\.?\d*)%\s*', html_text)
    if len(dist_match) >= 3:
        # Look for the specific pattern of home/draw/away distribution
        filtered = [float(d) for d in dist_match if 0 < float(d) <= 100]
        if len(filtered) >= 3:
            result["distribution_pct"] = {
                "home": filtered[-3],
                "draw": filtered[-2],
                "away": filtered[-1],
            }

    return result


# ─── Main ───────────────────────────────────────────────────
def parse_all_pages(shuju_id, date, cache_dir="~/.cache/shared-football"):
    """Parse all 6 pages for a given match and return merged JSON."""
    cache_dir = os.path.expanduser(cache_dir)
    raw_dir = os.path.join(cache_dir, "raw", date)

    result = {"shuju_id": shuju_id, "date": date, "pages": {}}

    page_types = {
        "ouzhi": "百家欧赔",
        "yazhi": "亚盘对比",
        "rangqiu": "让球指数",
        "daxiao": "大小指数",
        "shuju": "数据分析",
        "touzhu": "投注分析",
    }

    parsers = {
        "ouzhi": parse_ouzhi,
        "yazhi": parse_yazhi,
        "rangqiu": parse_rangqiu,
        "daxiao": parse_daxiao,
        "shuju": parse_shuju,
        "touzhu": parse_touzhu,
    }

    for page_type, _ in page_types.items():
        html_path = os.path.join(raw_dir, f"{page_type}_{shuju_id}.html")
        if not os.path.exists(html_path):
            result["pages"][page_type] = {"error": "HTML not found"}
            continue

        try:
            html_text = read_html_file(html_path)
            parser = parsers[page_type]
            parsed = parser(html_text)
            result["pages"][page_type] = parsed
        except Exception as e:
            result["pages"][page_type] = {"error": str(e)}

    return result


def main():
    parser = argparse.ArgumentParser(description="500.com Deep Page Parser v3.0")
    parser.add_argument("--page", choices=["ouzhi", "yazhi", "rangqiu", "daxiao", "shuju", "touzhu", "all"],
                        default="all", help="Page type to parse")
    parser.add_argument("--html", help="Path to raw HTML file (single page mode)")
    parser.add_argument("--date", default=None, help="Date filter")
    parser.add_argument("--shuju-id", type=int, default=None, help="shuju ID")
    parser.add_argument("--cache-dir", default="~/.cache/shared-football",
                        help="Cache directory root")
    parser.add_argument("--json", action="store_true", default=True,
                        help="JSON output (default)")
    parser.add_argument("--output", "-o", help="Output JSON file path")

    args = parser.parse_args()

    if args.page != "all" and args.html:
        html_text = read_html_file(args.html)
        parsers = {
            "ouzhi": parse_ouzhi,
            "yazhi": parse_yazhi,
            "rangqiu": parse_rangqiu,
            "daxiao": parse_daxiao,
            "shuju": parse_shuju,
            "touzhu": parse_touzhu,
        }
        result = parsers[args.page](html_text)
    elif args.page == "all" and args.date and args.shuju_id:
        result = parse_all_pages(args.shuju_id, args.date, args.cache_dir)
    else:
        print("Usage examples:")
        print("  python3 deep_page_parser.py --page ouzhi --html raw.html --json")
        print("  python3 deep_page_parser.py --page all --date 2026-06-12 --shuju-id 1359172 --json")
        return

    json_str = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(json_str)
        print(f"Written to {args.output}")

    print(json_str)


if __name__ == "__main__":
    main()
