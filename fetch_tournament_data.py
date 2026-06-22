#!/usr/bin/env python3
"""
Fetch historical tournament data from 500.com deep analysis pages.
Builds dataset in wc2022_backtest_data.json format for FVS/DRM backtesting.

Usage:
  python3 fetch_tournament_data.py [--tournament wc2018|euro2024] [--scan]
"""

import urllib.request, urllib.error
import json, re, time, sys, os

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
PINNACLE_CID = 1055

def fetch_ouzhi_page(sid):
    """Fetch and parse ouzhi page for a match, returning Pinnacle odds + avg odds."""
    url = f"https://odds.500.com/fenxi/ouzhi-{sid}.shtml"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Referer": "https://www.500.com/"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except Exception:
        return None
    
    html = raw.decode('gb2312', errors='replace')
    
    # Check if it's a valid match page
    if 'cid=1055' not in html:
        return None
    
    # Extract title for match info
    title_m = re.search(r'<title>(.*?)(?:\(|vs)(.*?)(?:\)|VS|vs)(.*?)(?:-|\().*?(\d{4})', html)
    title = re.search(r'<title>(.*?)</title>', html)
    title_text = title.group(1) if title else ''
    
    # Parse Pinnacle odds from the complex nested table structure
    # We need: opening_home, opening_draw, opening_away, closing_home, closing_draw, closing_away
    
    # Find Pinnacle row
    idx = html.find('cid=1055')
    if idx < 0:
        return None
    
    # Strategy: find all numeric odds patterns in the Pinnacle row segment
    # The row contains nested tables with current odds and initial odds
    
    # Find the outer </tr> for this row by counting nested <tr> tags
    segment = html[idx:]
    depth = 0
    tr_end = -1
    for j, c in enumerate(segment):
        if segment[j:j+4] == '<tr ' or segment[j:j+3] == '<tr>':
            depth += 1
        elif segment[j:j+5] == '</tr>':
            depth -= 1
            if depth == 0:
                tr_end = idx + j + 5
                break
    
    if tr_end < 0:
        return None
    
    row_html = html[idx:tr_end]
    
    # Extract all odds numbers from this row
    # Look for patterns like >1.95< or >3.33< etc
    odds = re.findall(r'>(\d+\.\d+)<', row_html)
    # Filter to reasonable SPF odds (1.0 - 50.0)
    odds = [float(o) for o in odds if 1.0 <= float(o) <= 50.0]
    
    # For 2018 WC format, odds typically appear as:
    # [closing_h, closing_d, closing_a] or [opening_h, opening_d, opening_a, closing_h, closing_d, closing_a]
    # or some variation
    
    result = {
        'sid': sid,
        'title': title_text,
        'odds_raw': odds,
    }
    
    # Try to extract opening/closing odds
    # The page usually shows current first, then initial in a hidden row
    # Look for the closing odds (should be the first set visible)
    if len(odds) >= 6:
        result['closing'] = {'home': odds[3], 'draw': odds[4], 'away': odds[5]}
        result['opening'] = {'home': odds[0], 'draw': odds[1], 'away': odds[2]}
    elif len(odds) >= 3:
        result['closing'] = {'home': odds[0], 'draw': odds[1], 'away': odds[2]}
        result['opening'] = None
    
    return result

def fetch_yazhi_page(sid):
    """Fetch yazhi page and extract Pinnacle AH data."""
    url = f"https://odds.500.com/fenxi/yazhi-{sid}.shtml"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
    except Exception:
        return None
    
    html = raw.decode('gb2312', errors='replace')
    
    # Find Pinnacle AH row
    idx = html.find('cid=1055')
    if idx < 0:
        return None
    
    segment = html[idx:idx+2000]
    # Extract handicap data from the row
    # AH format: 水,盘口,水 or similar
    handicap_data = re.findall(r'>([^<]*?(?:平手|半球|一球|球半|两球|受|[0-9./])[^<]*)<', segment)
    
    return {'handicap_raw': handicap_data[:5] if handicap_data else []}

def prob_from_odds(h, d, a):
    """Simple proportional de-vig probabilities."""
    ih, id_, ia = 1.0/h, 1.0/d, 1.0/a
    total = ih + id_ + ia
    return ih/total, id_/total, ia/total

def determine_stage(match_num, total_matches):
    """Determine tournament stage from match index."""
    # For 2018 WC: 48 group + 8 R16 + 4 QF + 2 SF + 1 F + 1 3rd = 64
    # For 2024 Euro: 36 group + 8 R16 + 4 QF + 2 SF + 1 F = 51
    if match_num <= 48:
        return 'group'
    elif match_num <= 56:
        return 'round16'
    elif match_num <= 60:
        return 'quarter'
    elif match_num <= 62:
        return 'semi'
    elif match_num <= 63:
        return 'third'  # 3rd place playoff (for WC)
    else:
        return 'final'

def probe_wc2018():
    """Probe shuju IDs for 2018 World Cup matches."""
    # 2018 WC was June 14 - July 15, 2018
    # Known: final has sid 742548
    # Let's scan likely ranges
    
    known_matches = {}
    
    ranges_to_scan = [
        (742500, 742600, 1),     # Around the final
    ]
    
    for start, end, step in ranges_to_scan:
        print(f"Scanning {start}..{end} (step={step})...")
        for sid in range(start, end + 1, step):
            result = fetch_ouzhi_page(sid)
            if result:
                title = result.get('title', '')
                if '世界杯' in title or 'World Cup' in title:
                    print(f"  ✓ {sid}: {title}")
                    if '2018' in title:
                        known_matches[sid] = result
            time.sleep(0.3)
    
    return known_matches

if __name__ == '__main__':
    # Test with known 2018 WC match
    print("Testing with France vs Croatia (WC 2018 final, sid=742548)...")
    result = fetch_ouzhi_page(742548)
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    print("\n\nTesting with Spain vs England (Euro 2024 final, sid=1144464)...")
    result = fetch_ouzhi_page(1144464)
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # Probe for more matches
    print("\n\nProbing 2018 WC IDs...")
    for sid in [742540, 742541, 742542, 742543, 742544, 742545, 742546, 742547]:
        result = fetch_ouzhi_page(sid)
        if result:
            print(f"  {sid}: {result.get('title','')[:80]} | odds: {result.get('odds_raw',[])}")
        time.sleep(0.3)
    
    print("\n\nProbing Euro 2024 IDs...")
    for sid in [1144460, 1144461, 1144462, 1144463, 1144459, 1144458, 1144457, 1144456]:
        result = fetch_ouzhi_page(sid)
        if result:
            print(f"  {sid}: {result.get('title','')[:80]} | odds: {result.get('odds_raw',[])}")
        time.sleep(0.3)
