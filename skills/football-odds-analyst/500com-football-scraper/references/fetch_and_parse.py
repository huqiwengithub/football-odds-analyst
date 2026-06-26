#!/usr/bin/env python3
"""
500.com Deep Page Fetcher + Parser v3.0
=======================================
Fetches raw GB2312 HTML from all 6 deep analysis pages and parses them into
structured JSON. Handles GB2312 encoding correctly (uses direct HTTP, not WebFetch).

6 pages per match:
  ouzhi   - 百家欧赔: 30+ bookmakers with SPF+Kelly+prob%+return rate+dispersion
  yazhi   - 亚盘对比: 17+ companies with handicap+water+change timestamps
  rangqiu - 让球指数: RQSPF including 竞彩 official odds (row 1)
  daxiao  - 大小指数: 18+ companies with OU line+water+timestamps
  shuju   - 数据分析: pre-match info, H2H, form, lineup, ranking
  touzhu  - 投注分析: Betfair volume+P&L+hot/cold index+simulated P&L+distribution

Key findings:
  - ouzhi页 row 1 ALWAYS = 竞彩官方SPF赔率 (with country 中国)
  - rangqiu页 row 1 = "竞*官*" (竞彩官方让球胜平负)
  - 深盘场次竞彩可能只开RSPF不开SPF（待验证）
  - Pinnacle = cid=1055, row ~12

Usage:
  python3 fetch_and_parse.py --shuju-id 1359172 --date 2026-06-12
  python3 fetch_and_parse.py --shuju-id 1359172 --date 2026-06-12 --no-cache
  python3 fetch_and_parse.py --shuju-id all --date 2026-06-12  # 批量

Output: .cache/shared-football/parsed/{date}_{shuju_id}.json
"""

import urllib.request
import urllib.error
import gzip
import re
import json
import os
import sys
import argparse
import time
import random
from collections import OrderedDict

# ─── Configuration ──────────────────────────────────────────
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

PAGE_URLS = {
    "ouzhi":   "https://odds.500.com/fenxi/ouzhi-{shuju_id}.shtml",
    "yazhi":   "https://odds.500.com/fenxi/yazhi-{shuju_id}.shtml",
    "rangqiu": "https://odds.500.com/fenxi/rangqiu-{shuju_id}.shtml",
    "daxiao":  "https://odds.500.com/fenxi/daxiao-{shuju_id}.shtml",
    "shuju":   "https://odds.500.com/fenxi/shuju-{shuju_id}.shtml",
    "touzhu":  "https://odds.500.com/fenxi/touzhu-{shuju_id}.shtml",
}

DEFAULT_CACHE_DIR = os.path.expanduser("~/.cache/shared-football")


# ─── HTTP Fetch with Proper Encoding ────────────────────────
def fetch_page(url, timeout=30):
    """Fetch a GB2312-encoded page and return decoded UTF-8 text."""
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Referer": "https://odds.500.com/",
    })

    # Random delay (0.5-1.5s) to avoid rate limiting
    time.sleep(random.uniform(0.5, 1.5))

    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        raw = resp.read()

        # Handle gzip
        if resp.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)

        # The page's <meta charset="gb2312"> tag says GB2312
        # Try GB2312 first, fall back to GBK, then GB18030
        for enc in ["gb2312", "gbk", "gb18030"]:
            try:
                text = raw.decode(enc)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        else:
            text = raw.decode("utf-8", errors="replace")

        return text

    except urllib.error.HTTPError as e:
        return f"HTTP Error {e.code}"
    except urllib.error.URLError as e:
        return f"URL Error: {e.reason}"
    except Exception as e:
        return f"Error: {e}"


# ─── Ouzhi (百家欧赔) Parser ────────────────────────────────
def parse_ouzhi(html_text):
    """
    Extract ALL 30 bookmaker rows from ouzhi page.
    
    Structure: nested tables inside each bookmaker <tr>:
      Table 1: SPF (row1=open×3, row2=current×3)
      Table 2: Probability% (row1=open×3, row2=current×3)
      Table 3: Return rate% (row1=open, row2=current)
      Table 4: Kelly (row1=open×3, row2=current×3)
    """
    result = {"bookmakers": [], "jingcai_spf": None, "pinnacle": None, "summary": {}, "total": 0}

    # Find all bookmaker positions
    title_pattern = re.compile(r'class="tb_plgs"\s+title="([^"]+)"')
    name_matches = [(m.start(), m.group(1)) for m in title_pattern.finditer(html_text)]
    
    if not name_matches:
        return result

    bookmakers = []
    for i, (start, name) in enumerate(name_matches):
        # Define the chunk: from this bookmaker's tb_plgs to the next one (or end)
        end = name_matches[i+1][0] if i+1 < len(name_matches) else len(html_text)
        chunk = html_text[start:end]

        cid = _extract_cid(chunk)
        
        # Country extraction
        country = ""
        country_m = re.search(r'class="gray">\((.+?)\)<', chunk)
        if country_m:
            country = country_m.group(1)

        # Extract all nested tables
        tables = re.findall(r'<table[^>]*>(.*?)</table>', chunk, re.DOTALL)
        all_nums = []
        for tbl in tables:
            nums = re.findall(r'>\s*([\d.]+)\s*[<%]', tbl)
            all_nums.extend([float(n) for n in nums])

        bm = OrderedDict()
        bm["name"] = name.strip()
        bm["cid"] = cid
        if country:
            bm["country"] = country

        if len(all_nums) >= 6:
            bm["spf_open"] = OrderedDict([
                ("home", all_nums[0]), ("draw", all_nums[1]), ("away", all_nums[2])
            ])
            bm["spf_current"] = OrderedDict([
                ("home", all_nums[3]), ("draw", all_nums[4]), ("away", all_nums[5])
            ])
        
        if len(all_nums) >= 14:
            bm["prob_open_pct"] = OrderedDict([
                ("home", all_nums[6]), ("draw", all_nums[7]), ("away", all_nums[8])
            ])
            bm["prob_current_pct"] = OrderedDict([
                ("home", all_nums[9]), ("draw", all_nums[10]), ("away", all_nums[11])
            ])
            bm["return_open_pct"] = all_nums[12]
            bm["return_current_pct"] = all_nums[13]

        if len(all_nums) >= 20:
            bm["kelly_open"] = OrderedDict([
                ("home", all_nums[14]), ("draw", all_nums[15]), ("away", all_nums[16])
            ])
            bm["kelly_current"] = OrderedDict([
                ("home", all_nums[17]), ("draw", all_nums[18]), ("away", all_nums[19])
            ])
        elif len(all_nums) >= 17:
            bm["kelly_current"] = OrderedDict([
                ("home", all_nums[14]), ("draw", all_nums[15]), ("away", all_nums[16])
            ])

        bookmakers.append(bm)

    result["bookmakers"] = bookmakers
    result["total"] = len(bookmakers)

    # Identify 竞彩官方 (row 1 with country 中国, cid=1)
    for bm in bookmakers:
        if "竞" in bm.get("name", ""):
            result["jingcai_spf"] = bm
            break

    # Identify Pinnacle
    for bm in bookmakers:
        name = bm.get("name", "")
        if bm.get("cid") == 1055 or "innacle" in name.lower() or "Pi" in name:
            result["pinnacle"] = bm
            break

    # Summary row: 平均值/最高值/最低值/离散值
    summary_text = re.sub(r'<[^>]+>', '|', html_text)
    summary_text = re.sub(r'\s+', '', summary_text)

    # Average current SPF (前3个), average open SPF (后3个)
    avg_match = re.search(r'平均值\|?([\d.]+)\|?([\d.]+)\|?([\d.]+).*?([\d.]+)\|?([\d.]+)\|?([\d.]+)', summary_text)
    if avg_match:
        result["summary"]["avg_spf_current"] = {
            "home": float(avg_match.group(1)),
            "draw": float(avg_match.group(2)),
            "away": float(avg_match.group(3)),
        }
        result["summary"]["avg_spf_open"] = {
            "home": float(avg_match.group(4)),
            "draw": float(avg_match.group(5)),
            "away": float(avg_match.group(6)),
        }

    # Dispersion (离散值) - format: 离散值|H|D|A|...
    disp_match = re.search(r'离散值\|?([\d.]+)\|?([\d.]+)\|?([\d.]+)', summary_text)
    if disp_match:
        result["summary"]["dispersion"] = {
            "home": float(disp_match.group(1)),
            "draw": float(disp_match.group(2)),
            "away": float(disp_match.group(3)),
        }

    return result


# ─── Unified Name Extraction ────────────────────────────────
def _extract_bookmaker_name(td_html):
    """
    Extract bookmaker name from a <td class="tb_plgs"> cell.
    Two patterns:
      1. ouzhi/rangqiu: title="NAME" directly on <td>
      2. yazhi/daxiao: title="NAME" on inner <a> tag
    """
    # Pattern 1: title on td itself
    m = re.search(r'<td[^>]*title="([^"]+)"', td_html)
    if m:
        return m.group(1).strip()

    # Pattern 2: title on inner <a>
    m = re.search(r'<a[^>]*title="([^"]+)"', td_html)
    if m:
        return m.group(1).strip()

    # Fallback: get text from quancheng span
    m = re.search(r'class="quancheng"[^>]*>([^<]+)<', td_html)
    if m:
        return m.group(1).strip()

    return None


def _extract_cid(td_html):
    """Extract company ID from cid=NNN in href"""
    m = re.search(r'cid=(\d+)', td_html)
    return int(m.group(1)) if m else 0


# ─── Yazhi (亚盘对比) Parser ─────────────────────────────────
def parse_yazhi(html_text):
    """
    Extract Asian Handicap data.

    Row structure per company:
      <tr class="tr2" id="CID">
        <td class="tb_plgs" row="1"><a title="NAME">...</a></td>
        <td><table>  <!-- current AH -->
          <tr><td>water_h↓</td><td>handicap</td><td>water_a↑</td></tr>
        </table></td>
        <td><time>CHANGE_TIME</time></td>
        <td><table>  <!-- open AH -->
          <tr><td>water_h</td><td>handicap</td><td>water_a</td></tr>
        </table></td>
        <td><time>OPEN_TIME</time></td>
      </tr>
    """
    result = {"companies": [], "pinnacle": None, "total": 0}

    # Find ALL rows containing tb_plgs (not just tr2, some rows have different classes)
    rows = re.findall(r'(<tr[^>]*>.*?</tr>)', html_text, re.DOTALL)
    companies = []

    for row in rows:
        name_match = re.search(r'<td[^>]*class="tb_plgs"[^>]*>(.*?)</td>', row, re.DOTALL)
        if not name_match:
            continue
        name = _extract_bookmaker_name(name_match.group(0))
        if not name:
            continue
        cid = _extract_cid(name_match.group(0))

        co = OrderedDict([("name", name), ("cid", cid)])

        # Extract handicap from the row
        hcap_match = re.search(r'class="\w+">(受?[\d./]+球[半]?|平手[\d./]*球?[半]?)</td>', row)
        if hcap_match:
            co["current_handicap_str"] = hcap_match.group(1)

        # Water levels: look for numbers followed by ↓↑ arrows
        water_current = re.findall(r'([\d.]+)\s*[↓↑]', row)
        if len(water_current) >= 2:
            co["current_water_home"] = float(water_current[0])
            co["current_water_away"] = float(water_current[1])

        # Open water (no arrows)
        open_table_matches = list(re.finditer(r'<table[^>]*class="pl_table_data"(.*?)</table>', row, re.DOTALL))
        if len(open_table_matches) >= 2:
            open_table = open_table_matches[1].group(0)
            open_water = re.findall(r'>([\d.]+)<', open_table)
            if len(open_water) >= 2:
                co["open_water_home"] = float(open_water[0])
                co["open_water_away"] = float(open_water[1])

        companies.append(co)

    result["companies"] = companies
    result["total"] = len(companies)

    for co in companies:
        if co.get("cid") == 1055 or "innacle" in co.get("name", "").lower() or "Pi" in co.get("name", ""):
            result["pinnacle"] = co
            break

    return result


# ─── Rangqiu (让球指数) Parser ───────────────────────────────
def parse_rangqiu(html_text):
    """
    Extract RQSPF including 竞彩 official odds.
    Same nested-table structure as ouzhi — 4 tables per bookmaker.
    Handicap value appears before the first nested <table>.

    Row 1 = "竞*官*" → 竞彩官方让球胜平负
    """
    result = {"jingcai_rqspf": None, "bookmakers": [], "total": 0}

    title_pattern = re.compile(r'class="tb_plgs"\s+title="([^"]+)"')
    name_matches = [(m.start(), m.group(1)) for m in title_pattern.finditer(html_text)]
    
    if not name_matches:
        return result

    for i, (start, name) in enumerate(name_matches):
        end = name_matches[i+1][0] if i+1 < len(name_matches) else len(html_text)
        chunk = html_text[start:end]

        # Extract handicap — appears right before the first nested <table>
        hcap_match = re.search(r'>([+-]?\d)\s*<', chunk)
        handicap = int(hcap_match.group(1)) if hcap_match else 0

        # Extract all nested tables (same as ouzhi)
        tables = re.findall(r'<table[^>]*>(.*?)</table>', chunk, re.DOTALL)
        all_nums = []
        for tbl in tables:
            nums = re.findall(r'>\s*([\d.]+)\s*[<%]', tbl)
            all_nums.extend([float(n) for n in nums])

        bm = OrderedDict([("name", name.strip()), ("handicap", handicap)])

        if len(all_nums) >= 6:
            bm["open"] = OrderedDict([
                ("home", all_nums[0]), ("draw", all_nums[1]), ("away", all_nums[2])
            ])
            bm["current"] = OrderedDict([
                ("home", all_nums[3]), ("draw", all_nums[4]), ("away", all_nums[5])
            ])

        if len(all_nums) >= 14:
            bm["prob_open_pct"] = OrderedDict([
                ("home", all_nums[6]), ("draw", all_nums[7]), ("away", all_nums[8])
            ])
            bm["prob_current_pct"] = OrderedDict([
                ("home", all_nums[9]), ("draw", all_nums[10]), ("away", all_nums[11])
            ])
            bm["return_open_pct"] = all_nums[12]
            bm["return_current_pct"] = all_nums[13]

        if len(all_nums) >= 20:
            bm["kelly_open"] = OrderedDict([
                ("home", all_nums[14]), ("draw", all_nums[15]), ("away", all_nums[16])
            ])
            bm["kelly_current"] = OrderedDict([
                ("home", all_nums[17]), ("draw", all_nums[18]), ("away", all_nums[19])
            ])
        elif len(all_nums) >= 17:
            bm["kelly_current"] = OrderedDict([
                ("home", all_nums[14]), ("draw", all_nums[15]), ("away", all_nums[16])
            ])

        result["bookmakers"].append(bm)
        if "竞" in name:
            result["jingcai_rqspf"] = bm

    result["total"] = len(result["bookmakers"])
    return result


# ─── Daxiao (大小指数) Parser ────────────────────────────────
def parse_daxiao(html_text):
    """
    Extract OU data. Same structure as yazhi (names via <a title> inside tb_plgs).

    Format: over_water / line / under_water | change_timestamp
    """
    result = {"companies": [], "total": 0}

    rows = re.findall(r'(<tr[^>]*>.*?</tr>)', html_text, re.DOTALL)

    for row in rows:
        name_match = re.search(r'<td[^>]*class="tb_plgs"[^>]*>(.*?)</td>', row, re.DOTALL)
        if not name_match:
            continue
        name = _extract_bookmaker_name(name_match.group(0))
        if not name:
            continue
        cid = _extract_cid(name_match.group(0))

        co = OrderedDict([("name", name), ("cid", cid)])

        # OU line: format like "2.5" or "2/2.5" between water values
        hcap_match = re.search(r'class="\w+">([\d./]+)<', row)
        if hcap_match:
            co["current_line_str"] = hcap_match.group(1)

        # Water with arrows (current)
        water_current = re.findall(r'([\d.]+)\s*[↓↑]', row)
        if len(water_current) >= 2:
            co["current_over_water"] = float(water_current[0])
            co["current_under_water"] = float(water_current[1])

        # Open water from second table
        open_tables = list(re.finditer(r'<table[^>]*class="pl_table_data"(.*?)</table>', row, re.DOTALL))
        if len(open_tables) >= 2:
            open_water = re.findall(r'>([\d.]+)<', open_tables[1].group(0))
            if len(open_water) >= 2:
                co["open_over_water"] = float(open_water[0])
                co["open_under_water"] = float(open_water[1])

        result["companies"].append(co)

    result["total"] = len(result["companies"])

    total_match = re.search(r'共(\d+)家公司', html_text)
    if total_match:
        result["total_displayed"] = int(total_match.group(1))

    return result


# ─── Shuju (数据分析) Parser ─────────────────────────────────
def parse_shuju(html_text):
    """Extract pre-match analysis data from shuju page."""
    result = OrderedDict()

    # Clean text for extraction
    plain = re.sub(r'<[^>]+>', ' ', html_text)
    plain = re.sub(r'\s+', ' ', plain)

    # FIFA ranking
    rank_matches = re.findall(r'\[世(\d+)\]', plain)
    if len(rank_matches) >= 2:
        result["home_rank"] = int(rank_matches[0])
        result["away_rank"] = int(rank_matches[1])
    elif len(rank_matches) == 1:
        result["home_rank"] = int(rank_matches[0])

    # Formation
    fm_match = re.search(r'(\d-\d-\d)', plain)
    if fm_match:
        result["formation"] = fm_match.group(1)

    # H2H
    h2h = re.search(
        r'近(\d+)次交战[,，]\s*(\S+?)\s*(\d+)胜(\d+)平(\d+)负[,，]\s*进(\d+)球[,，]\s*失(\d+)球',
        plain
    )
    if h2h:
        result["h2h"] = OrderedDict([
            ("matches", int(h2h.group(1))),
            ("team", h2h.group(2)),
            ("wins", int(h2h.group(3))),
            ("draws", int(h2h.group(4))),
            ("losses", int(h2h.group(5))),
            ("goals_for", int(h2h.group(6))),
            ("goals_against", int(h2h.group(7))),
        ])

    # Recent form (home or general)
    form = re.search(
        r'近(\d+)场\S*[：:]?\s*(\d+)胜(\d+)平(\d+)负[,，]?\s*进(\d+)球[,，]?\s*失(\d+)球',
        plain
    )
    if form:
        result["recent_form"] = OrderedDict([
            ("matches", int(form.group(1))),
            ("wins", int(form.group(2))),
            ("draws", int(form.group(3))),
            ("losses", int(form.group(4))),
            ("goals_for", int(form.group(5))),
            ("goals_against", int(form.group(6))),
        ])

    # Avg goals (look for 场均)
    avg_goals = re.findall(r'场均[：:]?\s*([\d.]+)\s*球', plain)
    if len(avg_goals) >= 2:
        result["avg_goals_scored"] = float(avg_goals[0])
        result["avg_goals_conceded"] = float(avg_goals[1])

    # Injuries/Suspensions
    injuries = re.findall(r'(停赛|伤病|伤缺|缺席)[：:]*\s*([\u4e00-\u9fff·]{2,20})', plain)
    if injuries:
        result["absences"] = [{"reason": r, "player": n.strip()} for r, n in injuries[:5]]

    return result


# ─── Touzhu (投注分析) Parser ─────────────────────────────────
def parse_touzhu(html_text):
    """
    Extract Betfair exchange data from touzhu page (all static HTML).

    Data layout in 热度分析 section:
      [team] | [欧赔] | [概率%] | [北单(-)] | [交易比例%] | [成交价] | [成交量] | [庄家盈亏] | [必发指数(-)] | [冷热指数] | [盈亏指数]
    """
    result = OrderedDict()

    plain = re.sub(r'<[^>]+>', '|', html_text)
    plain = re.sub(r'\|+', '|', plain)
    plain = re.sub(r'\s+', ' ', plain)

    # ── 热度分析: extract 3 data rows ──
    hot_section = re.search(r'热度分析(.*?)数据提点', plain)
    if hot_section:
        section = hot_section.group(1)
        
        # Pattern: team | |odds| |prob%| |-| |volume%| |price| |volume| |pl| |-| |hot_cold| |pl_idx
        # Note the double-pipe "| |" separators between values
        rows = re.findall(
            r'([\u4e00-\u9fff]+)\s*\|\s*\|\s*([\d.]+)\s*\|\s*\|\s*([\d.]+)%\s*\|\s*\|\s*-\s*\|\s*\|\s*([\d.]+)%\s*\|\s*\|\s*([\d.]+)\s*\|\s*\|\s*([\d,]+)\s*\|\s*\|\s*(-?[\d,]+)\s*\|\s*\|\s*\S+\s*\|\s*\|\s*(-?\d+)\s*\|\s*\|\s*(-?\d+)',
            section
        )
        
        if len(rows) >= 3:
            outcomes = ["home", "draw", "away"]
            betfair = OrderedDict()
            for i, row in enumerate(rows[:3]):
                if i < len(outcomes):
                    betfair[outcomes[i]] = OrderedDict([
                        ("team", row[0]),
                        ("euro_odds", float(row[1])),
                        ("euro_prob_pct", float(row[2])),
                        ("volume_ratio_pct", float(row[3])),
                        ("betfair_price", float(row[4])),
                        ("betfair_volume", int(row[5].replace(",", ""))),
                        ("bookmaker_pl", int(row[6].replace(",", ""))),
                        ("hot_cold_index", int(row[7])),
                        ("pl_index", int(row[8])),
                    ])
            if betfair:
                result["betfair"] = betfair

    # ── Total volume ──
    total_vol = re.search(r'([\d,]+)\s*总交易', plain)
    if total_vol:
        result["total_volume"] = int(total_vol.group(1).replace(",", ""))

    # ── Volume distribution (3 values after total) ──
    dist_match = re.search(r'总交易[港币]*\s*\|\s*\|([\d,]+)\|([\d,]+)\|([\d,]+)', plain)
    if dist_match:
        result["volume_distribution"] = {
            "home": int(dist_match.group(1).replace(",", "")),
            "draw": int(dist_match.group(2).replace(",", "")),
            "away": int(dist_match.group(3).replace(",", "")),
        }

    # ── Large trade volume ──
    big_vol = re.search(r'大额交易量.*?([\d,]+)\s*总交易', plain)
    if big_vol:
        result["large_trade_volume"] = int(big_vol.group(1).replace(",", ""))

    # ── Data summary ──
    summary_match = re.search(r'数据提点\s*\|\s*(.*?)(?:暂无数据|必发交易)', plain)
    if summary_match:
        text = summary_match.group(1).replace('|', '').strip()
        result["data_summary"] = text

    # ── 模拟盈亏: Transaction Flow (v3.8.0) ──
    # Parse the structured table: each row = [side, buy/sell, volume, time, ratio%]
    idx_pl = html_text.find('模拟盈亏')
    if idx_pl >= 0:
        chunk = html_text[idx_pl:idx_pl+5000]
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', chunk, re.DOTALL)
        transactions = []
        for row in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            if len(cells) >= 5:
                cell_texts = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
                if cell_texts[0] in ('主', '客', '平') and cell_texts[1] in ('买', '卖'):
                    transactions.append({
                        'side': cell_texts[0],
                        'direction': cell_texts[1],
                        'volume': float(cell_texts[2]) if cell_texts[2] else 0,
                        'time': cell_texts[3],
                        'ratio_pct': float(cell_texts[4].rstrip('%')) if cell_texts[4] else 0,
                    })
        if transactions:
            result["pl_flow"] = {
                'transactions': transactions,
                'count': len(transactions),
                'summary': _compute_pl_flow_summary(transactions),
            }

    return result


def _compute_pl_flow_summary(transactions):
    """Compute net flow direction from transaction log."""
    sides = {'主': 'home', '客': 'away', '平': 'draw'}
    summary = {}
    for cn, en in sides.items():
        side_txns = [t for t in transactions if t['side'] == cn]
        if side_txns:
            buy_vol = sum(t['volume'] for t in side_txns if t['direction'] == '买')
            sell_vol = sum(t['volume'] for t in side_txns if t['direction'] == '卖')
            net = buy_vol - sell_vol
            summary[en] = {
                'buy_volume': buy_vol,
                'sell_volume': sell_vol,
                'net_flow': net,
                'flow_direction': 'absorbing' if net < 0 else 'hedging',
                'tx_count': len(side_txns),
            }
    return summary


# ─── Main: Fetch + Parse All ─────────────────────────────────
def fetch_and_parse(shuju_id, date, cache_dir=DEFAULT_CACHE_DIR, no_cache=False):
    """Fetch all 6 pages for a match and return structured JSON."""

    raw_dir = os.path.join(cache_dir, "raw", date)
    parsed_dir = os.path.join(cache_dir, "parsed")

    # Check parsed cache first
    parsed_path = os.path.join(parsed_dir, f"{date}_{shuju_id}.json")
    if not no_cache and os.path.exists(parsed_path):
        mtime = os.path.getmtime(parsed_path)
        if time.time() - mtime < 3600:  # 1h
            with open(parsed_path, "r", encoding="utf-8") as f:
                return json.load(f)

    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(parsed_dir, exist_ok=True)

    # ── Fetch pages ──
    raw_html = {}
    for page_type, url_tpl in PAGE_URLS.items():
        url = url_tpl.format(shuju_id=shuju_id)
        raw_path = os.path.join(raw_dir, f"{page_type}_{shuju_id}.html")

        if not no_cache and os.path.exists(raw_path):
            with open(raw_path, "rb") as f:
                raw_bytes = f.read()
            # Decode from raw bytes
            for enc in ["gb2312", "gbk", "gb18030"]:
                try:
                    html = raw_bytes.decode(enc)
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            else:
                html = raw_bytes.decode("utf-8", errors="replace")
            raw_html[page_type] = html
            print(f"  [CACHE] {page_type}")
        else:
            print(f"  [FETCH] {page_type} ...", end=" ", flush=True)
            html = fetch_page(url)
            if html.startswith("HTTP Error") or html.startswith("URL Error"):
                print(f"FAILED: {html}")
                raw_html[page_type] = None
                continue
            # Save raw bytes with original encoding (GB2312)
            try:
                raw_bytes = html.encode("gb2312")
            except UnicodeEncodeError:
                raw_bytes = html.encode("utf-8")
            with open(raw_path, "wb") as f:
                f.write(raw_bytes)
            raw_html[page_type] = html
            print(f"OK ({len(raw_bytes)} bytes)")

    # ── Parse pages ──
    parsers = {
        "ouzhi": parse_ouzhi,
        "yazhi": parse_yazhi,
        "rangqiu": parse_rangqiu,
        "daxiao": parse_daxiao,
        "shuju": parse_shuju,
        "touzhu": parse_touzhu,
    }

    result = OrderedDict([
        ("shuju_id", shuju_id),
        ("date", date),
        ("fetched_at", time.strftime("%Y-%m-%d %H:%M:%S")),
    ])

    for page_type, html in raw_html.items():
        if html is None:
            result[page_type] = {"error": "fetch failed"}
        else:
            try:
                result[page_type] = parsers[page_type](html)
            except Exception as e:
                result[page_type] = {"error": f"parse error: {e}"}

    # Write to cache
    with open(parsed_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


# ─── CLI ─────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="500.com Deep Page Fetcher + Parser v3.0")
    parser.add_argument("--shuju-id", type=int, required=True, help="shuju ID (match fixture ID)")
    parser.add_argument("--date", required=True, help="Date YYYY-MM-DD")
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR)
    parser.add_argument("--no-cache", action="store_true", help="Force re-fetch")
    parser.add_argument("--output", "-o", help="Output JSON path (default: auto to cache)")

    args = parser.parse_args()

    print(f"=== 500.com Deep Page Parser v3.0 ===")
    print(f"  shuju_id: {args.shuju_id}")
    print(f"  date:     {args.date}")

    result = fetch_and_parse(args.shuju_id, args.date, args.cache_dir, args.no_cache)

    # Print summary
    print(f"\n=== Parse Results ===")
    for page_type in ["ouzhi", "yazhi", "rangqiu", "daxiao", "shuju", "touzhu"]:
        data = result.get(page_type, {})
        if isinstance(data, dict):
            if "error" in data:
                print(f"  {page_type}: ERROR - {data['error']}")
            elif page_type == "ouzhi":
                bm_count = data.get("total", 0)
                has_jc = "YES" if data.get("jingcai_spf") else "NO"
                has_pin = "YES" if data.get("pinnacle") else "NO"
                print(f"  ouzhi: {bm_count} bookmakers | 竞彩={has_jc} | Pinnacle={has_pin}")
            elif page_type == "rangqiu":
                bm_count = data.get("total", 0)
                has_jc = "YES" if data.get("jingcai_rqspf") else "NO"
                if has_jc and data.get("jingcai_rqspf"):
                    jc = data["jingcai_rqspf"]
                    print(f"  rangqiu: {bm_count} companies | 竞彩RSPF=让{jc.get('handicap', '?')}球 "
                          f"{jc.get('current', {}).get('home', '?')}/{jc.get('current', {}).get('draw', '?')}/{jc.get('current', {}).get('away', '?')}")
                else:
                    print(f"  rangqiu: {bm_count} companies | 竞彩=NONE")
            else:
                count = data.get("total", data.get("total_displayed", data.get("total_companies", "?")))
                print(f"  {page_type}: {count} entries")
        else:
            print(f"  {page_type}: {type(data).__name__}")

    # Output
    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\nOutput: {args.output}")

    print(f"\nCache: {os.path.join(args.cache_dir, 'parsed', f'{args.date}_{args.shuju_id}.json')}")


if __name__ == "__main__":
    main()
