#!/usr/bin/env python3
"""
500.com 竞彩足球数据解析器 v2.0
数据源: https://www.500.com/static/public/jczq/xml/odds/odds.xml

XML结构:
  <europe avg="H,D,A"> = 欧赔百家平均(SPF)
  <asian am="水,盘口,水"> = 亚盘
  <gl avg="H%,D%,A%"> = 胜平负概率分布
  <rq avg="H,D,A"> = 让球胜平负
  <dxq am="水,盘口,水"> = 大小球
  <bq /> = 半场数据

用法: python3 parser.py [--date YYYY-MM-DD] [--xml-url URL] [--team-data FILE]

队名来源: 需要从 trade.500.com 页面获取 (通过 WebFetch 工具渲染JS后提取)
         或通过 --team-data 传入预解析的队名映射文件
"""

import urllib.request
import xml.etree.ElementTree as ET
import json
import sys
import os
import gzip
import re
import argparse
from datetime import datetime, timedelta
from collections import OrderedDict

XML_URL = "https://www.500.com/static/public/jczq/xml/odds/odds.xml"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# ─── XML 获取与解析 ────────────────────────────────────────
def fetch_xml(url=None, cache_file=None):
    if url is None:
        url = XML_URL
    if cache_file and os.path.exists(cache_file):
        mtime = os.path.getmtime(cache_file)
        if datetime.now().timestamp() - mtime < 600:  # 10分钟缓存
            with gzip.open(cache_file, 'rt', encoding='utf-8') as f:
                return f.read()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Referer": "https://trade.500.com/jczq/"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        xml = resp.read().decode('utf-8', errors='replace')
    if cache_file:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with gzip.open(cache_file, 'wt', encoding='utf-8') as f:
            f.write(xml)
    return xml


def parse_europe(attr_str):
    """解析欧赔: "H,D,A" → {home, draw, away}"""
    parts = attr_str.split(",")
    return {"home": float(parts[0]), "draw": float(parts[1]), "away": float(parts[2])}


def parse_gl(attr_str):
    """解析胜平负概率: "H%,D%,A%" → {home, draw, away} (百分比)"""
    parts = attr_str.split(",")
    return {"home": float(parts[0]), "draw": float(parts[1]), "away": float(parts[2])}


def parse_asian(attr_str):
    """解析亚盘: "主水,盘口,客水" """
    parts = attr_str.split(",")
    if len(parts) >= 3:
        return {"home_water": float(parts[0]), "handicap": parse_handicap_line(parts[1]), "away_water": float(parts[2])}
    return None


def parse_handicap_line(handicap_str):
    """解析盘口: "2.5" 或 "2/2.5" (2.25) 或 "两球半" → float"""
    # 中文盘口映射
    cn_map = {
        "平手": 0, "平手/半球": 0.25, "半球": 0.5, "半球/一球": 0.75,
        "一球": 1.0, "一球/球半": 1.25, "球半": 1.5, "球半/两球": 1.75,
        "两球": 2.0, "两球/两球半": 2.25, "两球半": 2.5, "两球半/三球": 2.75,
        "三球": 3.0, "三球/三球半": 3.25, "三球半": 3.5,
        "受平手": 0, "受平手/半球": 0.25, "受半球": 0.5, "受半球/一球": 0.75,
        "受一球": 1.0, "受一球/球半": 1.25, "受球半": 1.5, "受球半/两球": 1.75,
        "受两球": 2.0, "受两球/两球半": 2.25, "受两球半": 2.5, "受两球半/三球": 2.75,
        "受三球": 3.0, "受三球/三球半": 3.25, "受三球半": 3.5,
    }
    if handicap_str in cn_map:
        return cn_map[handicap_str]
    
    # "2/2.5" → 2.25
    if "/" in handicap_str:
        parts = handicap_str.split("/")
        return (float(parts[0]) + float(parts[1])) / 2
    
    return float(handicap_str)


def parse_dxq(attr_str):
    """解析大小球: "主水,盘口,客水" """
    parts = attr_str.split(",")
    if len(parts) >= 3:
        return {"over_water": float(parts[0]), "line": parse_handicap_line(parts[1]), "under_water": float(parts[2])}
    return None


def parse_rq(attr_str):
    """解析让球胜平负: "H,D,A" """
    parts = attr_str.split(",")
    return {"home": float(parts[0]), "draw": float(parts[1]), "away": float(parts[2])}


def parse_matches(xml_text):
    """解析XML，返回比赛列表"""
    root = ET.fromstring(xml_text)
    matches = []
    
    for m in root.findall(".//match"):
        mid = m.get("id")
        processdate = m.get("processdate")
        
        # 格式化日期
        dt = datetime.strptime(processdate, "%Y-%m-%d")
        
        match = OrderedDict([
            ("id", mid),
            ("date", processdate),
            ("processname", m.get("processname", "")),
        ])
        
        # 欧赔
        europe = m.find("europe")
        if europe is not None:
            for key in ["avg", "wl", "am", "lb", "bet365", "hg"]:
                val = europe.get(key)
                if val:
                    match[f"spf_{key}"] = parse_europe(val)
        
        # 胜平负概率
        gl = m.find("gl")
        if gl is not None:
            for key in ["avg"]:
                val = gl.get(key)
                if val:
                    match[f"prob_{key}"] = parse_gl(val)
        
        # 亚盘
        asian = m.find("asian")
        if asian is not None:
            for key in ["am", "bet365", "hg"]:
                val = asian.get(key)
                if val:
                    match[f"ah_{key}"] = parse_asian(val)
        
        # 大小球
        dxq = m.find("dxq")
        if dxq is not None:
            for key in ["am", "bet365"]:
                val = dxq.get(key)
                if val:
                    match[f"ou_{key}"] = parse_dxq(val)
        
        # 让球胜平负
        rq = m.find("rq")
        if rq is not None:
            val = rq.get("avg")
            if val:
                match["rqspf_avg"] = parse_rq(val)
        
        # 半场
        bq = m.find("bq")
        if bq is not None and bq.get("bet365"):
            match["bq_bet365"] = parse_asian(bq.get("bet365"))
        
        matches.append(match)
    
    return matches


# ─── 队名映射 ──────────────────────────────────────────────
def load_team_names_from_html(html_text):
    """
    从 trade.500.com 页面 HTML 中提取队名。
    依赖 WebFetch 工具渲染JS后的内容。
    
    返回: {match_id: {"home": "队名", "away": "队名", "code": "周日037", ...}}
    """
    team_map = {}
    
    # 从链接中提取 match ID 和队名
    # 模式: href="/fenxi/shuju-1359210.shtml" ... 西班牙 ... 沙特阿拉伯
    shuju_ids = re.findall(r'shuju-(\d+)\.shtml', html_text)
    
    # 按比赛代码分组
    match_blocks = re.split(r'\[(周[一二三四五六日天]\d+)\]', html_text)
    
    for i in range(1, len(match_blocks), 2):
        code = match_blocks[i]
        block = match_blocks[i+1] if i+1 < len(match_blocks) else ""
        
        # 提取日期时间
        dt_match = re.search(r'(\d{2}-\d{2}\s+\d{2}:\d{2})', block)
        dt = dt_match.group(1) if dt_match else ""
        
        # 提取队名
        team_match = re.search(r'\[(\d+)\]\s*<a[^>]*>([^<]+)</a>\s*VS\s*<a[^>]*>([^<]+)</a>\s*\[(\d+)\]', block)
        if team_match:
            rank_h = int(team_match.group(1))
            team_h = team_match.group(2).strip()
            team_a = team_match.group(3).strip()
            rank_a = int(team_match.group(4))
        else:
            # 尝试更宽松的匹配
            team_match2 = re.search(r'<a[^>]*>([^<]+)</a>\s*VS\s*<a[^>]*>([^<]+)</a>', block)
            if team_match2:
                team_h = team_match2.group(1).strip()
                team_a = team_match2.group(2).strip()
                rank_h = rank_a = 0
            else:
                continue
        
        # 提取让球数
        hcap_match = re.search(r'(?:单关)?\s*([+-]?\d+)\s*\n', block)
        handicap = 0
        if hcap_match:
            try:
                handicap = int(hcap_match.group(1).strip())
            except ValueError:
                pass
        
        # 提取 SPF
        spf_match = re.search(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$', block, re.MULTILINE)
        
        key = code
        team_map[key] = {
            "code": code,
            "datetime": dt,
            "home_team": team_h,
            "away_team": team_a,
            "home_rank": rank_h,
            "away_rank": rank_a,
            "handicap_rqspf": handicap,
        }
        
        if spf_match:
            team_map[key].update({
                "spf_home": float(spf_match.group(1)),
                "spf_draw": float(spf_match.group(2)),
                "spf_away": float(spf_match.group(3)),
            })
    
    return team_map


def load_jqs_bf_from_html(html_text):
    """
    从 trade.500.com 页面提取 JQS (进球数) 和 BF (比分) 数据。
    
    返回: {match_code: {"jqs": {...}, "bf": {...}, "bqc": {...}}}
    """
    result = {}
    
    # 按比赛代码分割
    match_blocks = re.split(r'\[(周[一二三四五六日天]\d+)\]', html_text)
    
    for i in range(1, len(match_blocks), 2):
        code = match_blocks[i]
        block = match_blocks[i+1] if i+1 < len(match_blocks) else ""
        
        data = {}
        
        # 进球数
        jqs_match = re.search(
            r'进球数\s+0\s+_([\d.]+)_\s+1\s+_([\d.]+)_\s+2\s+_([\d.]+)_\s+3\s+_([\d.]+)_\s+'
            r'4\s+_([\d.]+)_\s+5\s+_([\d.]+)_\s+6\s+_([\d.]+)_\s+7\+\s+_([\d.]+)_',
            block
        )
        if jqs_match:
            data["jqs"] = OrderedDict([
                ("0", float(jqs_match.group(1))),
                ("1", float(jqs_match.group(2))),
                ("2", float(jqs_match.group(3))),
                ("3", float(jqs_match.group(4))),
                ("4", float(jqs_match.group(5))),
                ("5", float(jqs_match.group(6))),
                ("6", float(jqs_match.group(7))),
                ("7+", float(jqs_match.group(8))),
            ])
        
        # 比分
        bf_scores = re.findall(r'(\d+:\d+|胜其它|平其它|负其它)\s*_([\d.]+)_', block)
        if bf_scores:
            data["bf"] = OrderedDict()
            for score, odds in bf_scores:
                data["bf"][score] = float(odds)
        
        # 半全场
        bqc_match = re.search(
            r'半全场\s+胜胜\s+_([\d.]+)_\s+胜平\s+_([\d.]+)_\s+胜负\s+_([\d.]+)_\s+'
            r'平胜\s+_([\d.]+)_\s+平平\s+_([\d.]+)_\s+平负\s+_([\d.]+)_\s+'
            r'负胜\s+_([\d.]+)_\s+负平\s+_([\d.]+)_\s+负负\s+_([\d.]+)_',
            block
        )
        if bqc_match:
            data["bqc"] = OrderedDict([
                ("胜胜", float(bqc_match.group(1))),
                ("胜平", float(bqc_match.group(2))),
                ("胜负", float(bqc_match.group(3))),
                ("平胜", float(bqc_match.group(4))),
                ("平平", float(bqc_match.group(5))),
                ("平负", float(bqc_match.group(6))),
                ("负胜", float(bqc_match.group(7))),
                ("负平", float(bqc_match.group(8))),
                ("负负", float(bqc_match.group(9))),
            ])
        
        if data:
            result[code] = data
    
    return result


# ─── 衍生计算 ──────────────────────────────────────────────
def compute_jqs_derived(jqs_odds):
    """从JQS赔率反推期望进球和大小球概率"""
    if not jqs_odds:
        return None
    
    overround = sum(1.0/v for v in jqs_odds.values())
    probs = {k: (1.0/v)/overround for k, v in jqs_odds.items()}
    
    # 期望进球
    exp_goals = sum((int(k) if k != "7+" else 7.5) * p for k, p in probs.items())
    
    # OU 2.5
    under_25 = sum(p for k, p in probs.items() if k not in ("7+",) and int(k) < 3)
    over_25 = 1.0 - under_25
    
    return {
        "expected_goals": round(exp_goals, 2),
        "under_2.5_pct": round(under_25 * 100, 1),
        "over_2.5_pct": round(over_25 * 100, 1),
        "prob_dist": {k: round(p*100, 1) for k, p in probs.items()},
    }


def compute_bf_derived(bf_odds):
    """从比分赔率反推最可能比分"""
    if not bf_odds:
        return None
    
    overround = sum(1.0/v for v in bf_odds.values())
    scores = []
    for k, v in bf_odds.items():
        true_prob = (1.0/v) / overround
        if ":" in k:
            h, a = k.split(":")
            scores.append({
                "score": k,
                "h": int(h), "a": int(a),
                "total": int(h) + int(a),
                "odds": v,
                "prob_pct": round(true_prob * 100, 2),
            })
    
    scores.sort(key=lambda x: x["prob_pct"], reverse=True)
    return scores


# ─── 主函数 ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="500.com 竞彩足球数据解析器 v2.0")
    parser.add_argument("--xml-url", default=XML_URL)
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--date", default=None)
    parser.add_argument("--html", default=None, help="预抓取的 trade.500.com HTML 文件 (用于提取队名+JQS+BF)")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-cache", action="store_true")
    
    args = parser.parse_args()
    
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_dir = args.cache_dir or os.path.join(skill_dir, ".cache")
    xml_cache = os.path.join(cache_dir, "odds.xml.gz")
    
    if args.no_cache and os.path.exists(xml_cache):
        os.remove(xml_cache)
    
    # 1. 获取 XML 数据
    xml_text = fetch_xml(args.xml_url, xml_cache)
    matches = parse_matches(xml_text)
    
    # 2. 按日期过滤
    if args.date:
        matches = [m for m in matches if m["date"] == args.date]
    
    # 3. 如果有 HTML，提取队名和 JQS/BF
    team_map = {}
    jqs_bf_map = {}
    if args.html and os.path.exists(args.html):
        with open(args.html, 'r', encoding='utf-8') as f:
            html_text = f.read()
        team_map = load_team_names_from_html(html_text)
        jqs_bf_map = load_jqs_bf_from_html(html_text)
    
    # 4. 合并数据并计算衍生指标
    # 先按日期筛选 team_map 和 jqs_bf_map，再按位置匹配
    # processname 编号体系(1041-1044) ≠ 页面编号(周日037-040)，无法直接匹配
    # 策略: 筛选出同日期的 HTML 条目，按 code 排序后按位置对应
    
    # 按日期筛选 team_map
    filtered_team_codes = []
    for code, info in team_map.items():
        dt = info.get("datetime", "")
        if not dt:
            continue
        # dt 格式: "06-22 00:00"
        parts = dt.split()
        if len(parts) >= 1:
            mm_dd = parts[0]  # "06-22"
            try:
                month, day = mm_dd.split("-")
                match_date = f"2026-{month}-{day.zfill(2)}"
            except ValueError:
                continue
            if args.date and match_date == args.date:
                filtered_team_codes.append(code)
    
    filtered_team_codes.sort()
    
    for i, m in enumerate(matches):
        pn = m.get("processname", "")
        
        # 方法1: processname 后两位匹配
        matched = False
        if len(pn) >= 2:
            match_num = pn[-2:]
            for code, team_info in team_map.items():
                if match_num in code or code.endswith(match_num):
                    m.update(team_info)
                    matched = True
                    break
        
        # 方法2: 按位置匹配 (processname 编号与页面编号不对齐时)
        if not matched and i < len(filtered_team_codes):
            code = filtered_team_codes[i]
            if code in team_map:
                m.update(team_map[code])
        
        # JQS/BF - 同样先尝试按 processname 匹配，再按位置匹配
        jb_matched = False
        if len(pn) >= 2:
            match_num = pn[-2:]
            for code, jb_data in jqs_bf_map.items():
                if match_num in code or code.endswith(match_num):
                    jb_matched = True
                    if "jqs" in jb_data:
                        m["jqs"] = jb_data["jqs"]
                        m["jqs_derived"] = compute_jqs_derived(jb_data["jqs"])
                    if "bf" in jb_data:
                        m["bf"] = jb_data["bf"]
                        m["bf_top10"] = compute_bf_derived(jb_data["bf"])
                    if "bqc" in jb_data:
                        m["bqc"] = jb_data["bqc"]
                    break
        
        # 按位置匹配 JQS/BF (JQS/BF map 的 key 也是 code 格式)
        if not jb_matched and i < len(filtered_team_codes):
            code = filtered_team_codes[i]
            if code in jqs_bf_map:
                jb_data = jqs_bf_map[code]
                if "jqs" in jb_data:
                    m["jqs"] = jb_data["jqs"]
                    m["jqs_derived"] = compute_jqs_derived(jb_data["jqs"])
                if "bf" in jb_data:
                    m["bf"] = jb_data["bf"]
                    m["bf_top10"] = compute_bf_derived(jb_data["bf"])
                if "bqc" in jb_data:
                    m["bqc"] = jb_data["bqc"]
    
    # 5. 输出
    if args.json:
        print(json.dumps(matches, ensure_ascii=False, indent=2))
    else:
        for m in matches:
            print(f"\n{'='*60}")
            hn = m.get("home_team", f"ID:{m['id']}")
            an = m.get("away_team", f"ID:{m['id']}")
            code = m.get("code", "???")
            dt_str = m.get("datetime", m["date"])
            print(f"{code} | {dt_str} | {hn} vs {an}")
            
            if "spf_avg" in m:
                s = m["spf_avg"]
                print(f"  SPF: {s['home']} / {s['draw']} / {s['away']}")
            if "rqspf_avg" in m:
                r = m["rqspf_avg"]
                print(f"  RQSPF: {r['home']} / {r['draw']} / {r['away']}")
            if "ou_bet365" in m:
                ou = m["ou_bet365"]
                print(f"  OU: O{ou['over_water']} / {ou['line']} / U{ou['under_water']}")
            if "jqs_derived" in m:
                jd = m["jqs_derived"]
                print(f"  xG: {jd['expected_goals']} | OU2.5: U{jd['under_2.5_pct']}% / O{jd['over_2.5_pct']}%")
            if "bf_top10" in m:
                print(f"  TOP 5 比分:")
                for s in m["bf_top10"][:5]:
                    print(f"    {s['score']}: {s['prob_pct']}% (x{s['odds']})")

    print(f"\n共 {len(matches)} 场比赛")


if __name__ == "__main__":
    main()
