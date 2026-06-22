#!/usr/bin/env python3
"""
v3: Efficient tournament data fetcher.
Strategy: Find shuju IDs by probing ranges, then batch-fetch odds.

Key findings from probes:
- 2018 WC: shuju IDs around 742548 (final). Range ~740000-743000
- 2024 Euro: shuju IDs around 1144464 (final). Range ~1140000-1144500  
"""

import urllib.request, urllib.error
import json, re, time, sys, os, concurrent.futures
from collections import defaultdict

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
PINNACLE_CID = 1055
CACHE_DIR = "/Users/tracy/Desktop/足彩/.cache/tournament_data"

def ensure_cache():
    os.makedirs(CACHE_DIR, exist_ok=True)

def cache_get(sid, page="ouzhi"):
    """Get cached page or fetch it."""
    cpath = os.path.join(CACHE_DIR, f"{page}_{sid}")
    if os.path.exists(cpath + ".json"):
        with open(cpath + ".json") as f:
            return json.load(f)
    return None

def cache_set(sid, data, page="ouzhi"):
    cpath = os.path.join(CACHE_DIR, f"{page}_{sid}.json")
    # Strip HTML from cache to save space (keep parsed data)
    if 'html' in data:
        del data['html']
    with open(cpath, 'w') as f:
        json.dump(data, f)

def fetch_ouzhi_raw(sid):
    """Fetch raw ouzhi page HTML."""
    cached = cache_get(sid)
    if cached:
        return cached
    
    url = f"https://odds.500.com/fenxi/ouzhi-{sid}.shtml"
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Referer": "https://www.500.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        return {"status": "error", "code": e.code, "sid": sid}
    except Exception as e:
        return {"status": "error", "msg": str(e), "sid": sid}
    
    html = raw.decode('gb2312', errors='replace')
    result = {"status": "ok", "sid": sid, "html": html, "len": len(html)}
    return result

def match_quick_check(html):
    """Quick check: is this a match page we're interested in?"""
    if 'cid=1055' not in html:
        return None
    if len(html) < 10000:
        return None
    
    m = re.search(r'<title>(.*?)</title>', html)
    if not m:
        return None
    title = m.group(1)
    return title

def parse_ouzhi(html, sid):
    """Parse ouzhi page for Pinnacle odds and bookmaker data."""
    title = match_quick_check(html)
    if not title:
        return None
    
    # Extract match info
    info = {'sid': sid, 'title': title}
    
    # Teams from title: "法国VS克罗地亚(2018世界杯)-百家欧赔-500彩票网"
    m = re.match(r'(.+?)VS(.+?)\((.+?)\)', title)
    if m:
        info['home_team'] = m.group(1).strip()
        info['away_team'] = m.group(2).strip()
        info['tournament'] = m.group(3).strip()
    else:
        info['home_team'] = info['away_team'] = info['tournament'] = ''
    
    # Score from <strong>X:Y</strong> in odds_hd_bf div
    score_m = re.search(r'odds_hd_bf.*?<strong>\s*(\d+)\s*[:：]\s*(\d+)\s*</strong>', html)
    if score_m:
        info['home_score'] = int(score_m.group(1))
        info['away_score'] = int(score_m.group(2))
    else:
        info['home_score'] = info['away_score'] = 0
    
    # Date from the page
    date_m = re.search(r'(\d{4}-\d{2}-\d{2})\s+\d{2}:\d{2}', html)
    if date_m:
        info['date'] = date_m.group(1)
    else:
        info['date'] = ''
    
    info['result'] = determine_result(info['home_score'], info['away_score'])
    
    # ---- Parse Pinnacle odds ----
    idx = html.find(f'cid={PINNACLE_CID}')
    if idx < 0:
        return None
    
    # Navigate to parent <tr>
    tr_start = html.rfind('<tr', idx - 500, idx)
    if tr_start < 0:
        return None
    
    # Find the matching </tr>
    segment = html[tr_start:]
    depth = 0
    tr_end = -1
    for j in range(len(segment)):
        if segment[j:j+4] == '<tr ' or segment[j:j+3] == '<tr>':
            depth += 1
        elif segment[j:j+5] == '</tr>':
            depth -= 1
            if depth == 0:
                tr_end = tr_start + j + 5
                break
    
    if tr_end < 0:
        return None
    
    row_html = html[tr_start:tr_end]
    
    # Extract odds from the nested table structure
    # Row 1 (td_show_cp): Closing odds (displayed)
    # Row 2: Opening odds
    trs = re.findall(r'<tr[^>]*>(.*?)</tr>', row_html, re.DOTALL)
    
    close_odds = None
    open_odds = None
    
    for tr in trs:
        odds_vals = re.findall(r'<td[^>]*>\s*(\d+\.\d+)\s*</td>', tr)
        # Filter: SPF odds are typically 1.0-50.0
        spf = [float(v) for v in odds_vals if 1.0 < float(v) < 50.0]
        if len(spf) >= 3:
            if 'td_show_cp' in tr:
                close_odds = {'home': spf[0], 'draw': spf[1], 'away': spf[2]}
            else:
                open_odds = {'home': spf[0], 'draw': spf[1], 'away': spf[2]}
    
    # If we couldn't distinguish by class, first match is closing, second is opening
    if not close_odds:
        # First tr with odds = closing, second = opening
        odds_rows = []
        for tr in trs:
            spf = [float(v) for v in re.findall(r'<td[^>]*>\s*(\d+\.\d+)\s*</td>', tr) if 1.0 < float(v) < 50.0]
            if len(spf) >= 3:
                odds_rows.append(spf[:3])
        if len(odds_rows) >= 2:
            close_odds = {'home': odds_rows[0][0], 'draw': odds_rows[0][1], 'away': odds_rows[0][2]}
            open_odds = {'home': odds_rows[1][0], 'draw': odds_rows[1][1], 'away': odds_rows[1][2]}
        elif len(odds_rows) == 1:
            close_odds = {'home': odds_rows[0][0], 'draw': odds_rows[0][1], 'away': odds_rows[0][2]}
    
    info['pinnacle'] = {'closing': close_odds, 'opening': open_odds}
    
    # ---- Parse all bookmaker closing odds (workaround for nested <tr> issues) ----
    # Use depth-counting to extract each bookmaker's full row
    bookmakers = []
    
    # Find each bookmaker row by its ID attribute
    for cid in re.findall(r'\bid="(\d+)"[^>]*ttl[^>]*xls[^>]*', html):
        cid = int(cid)
        if cid <= 0 or cid > 10000:
            continue
        
        # Find this specific row
        id_pattern = f'id="{cid}"'
        midx = html.find(id_pattern)
        if midx < 0:
            continue
        
        # Navigate to <tr> start
        tr_s = html.rfind('<tr', midx - 200, midx)
        if tr_s < 0:
            continue
        
        # Count depth to find proper </tr>
        segment = html[tr_s:]
        depth = 0
        tr_e = -1
        for j in range(len(segment)):
            if segment[j:j+4] == '<tr ' or segment[j:j+3] == '<tr>':
                depth += 1
            elif segment[j:j+5] == '</tr>':
                depth -= 1
                if depth == 0:
                    tr_e = tr_s + j + 5
                    break
        
        if tr_e < 0:
            continue
        
        bm_html = html[tr_s:tr_e]
        
        # Find odds in nested tables
        bm_trs = re.findall(r'<tr[^>]*>(.*?)</tr>', bm_html, re.DOTALL)
        bm_close = None
        bm_open = None
        
        for bm_tr in bm_trs:
            spf = [float(v) for v in re.findall(r'>\s*(\d+\.\d+)\s*<', bm_tr) if 1.0 < float(v) < 50.0]
            if len(spf) >= 3:
                spf = spf[:3]
                if 'td_show_cp' in bm_tr:
                    bm_close = spf
                else:
                    bm_open = spf
        
        if bm_close:
            bm_entry = {
                'cid': cid,
                'closing_home': bm_close[0],
                'closing_draw': bm_close[1],
                'closing_away': bm_close[2],
            }
            if bm_open:
                bm_entry['opening_home'] = bm_open[0]
                bm_entry['opening_draw'] = bm_open[1]
                bm_entry['opening_away'] = bm_open[2]
            bookmakers.append(bm_entry)
    
    info['bookmakers'] = bookmakers
    
    # Compute average closing odds
    if bookmakers:
        avg_h = sum(b['closing_home'] for b in bookmakers) / len(bookmakers)
        avg_d = sum(b['closing_draw'] for b in bookmakers) / len(bookmakers)
        avg_a = sum(b['closing_away'] for b in bookmakers) / len(bookmakers)
        info['avg_closing'] = {'home': avg_h, 'draw': avg_d, 'away': avg_a}
    else:
        info['avg_closing'] = None
    
    return info

def determine_result(hs, aws):
    if hs > aws: return 'home'
    if aws > hs: return 'away'
    return 'draw'

def determine_stage(match_idx, is_wc):
    """Rough stage based on tournament structure."""
    if is_wc:  # 64 matches
        if match_idx < 48: return 'group'
        elif match_idx < 56: return 'round16'
        elif match_idx < 60: return 'quarter'
        elif match_idx < 62: return 'semi'
        elif match_idx < 63: return 'third'
        else: return 'final'
    else:  # Euro 51 matches
        if match_idx < 36: return 'group'
        elif match_idx < 44: return 'round16'
        elif match_idx < 48: return 'quarter'
        elif match_idx < 50: return 'semi'
        else: return 'final'

def efficient_scan(start, end, step=10, tournament_filter=None, max_gap=30):
    """Scan an ID range for tournament matches.
    Uses coarse scan to find clusters, then dense scan."""
    
    ensure_cache()
    
    # Phase 1: Coarse scan
    print(f"Phase 1: Coarse scan {start}..{end} step={step}")
    candidates = []
    
    sids = list(range(start, end + 1, step))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_map = {}
        for sid in sids:
            f = executor.submit(fetch_ouzhi_raw, sid)
            future_map[f] = sid
            time.sleep(0.1)  # Stagger requests
        
        for f in concurrent.futures.as_completed(future_map):
            sid = future_map[f]
            try:
                result = f.result()
                if result.get('status') == 'ok':
                    title = match_quick_check(result.get('html', ''))
                    if title and tournament_filter and tournament_filter in title:
                        candidates.append(sid)
                        print(f"  ✓ {sid}: {title[:60]}")
                    else:
                        pass  # Not our tournament
                elif result.get('status') == 'error' and result.get('code') == 404:
                    pass  # Not found
            except Exception as e:
                pass
    
    if not candidates:
        print("  No matches found in this range.")
        return []
    
    candidates.sort()
    print(f"\nPhase 1 found {len(candidates)} candidate IDs: {candidates[:10]}...")
    
    # Phase 2: Dense scan around each candidate
    print(f"\nPhase 2: Dense scan around candidates...")
    all_found = {}
    
    for sid in candidates:
        # Scan ±50 around each candidate
        dense_range = range(max(start, sid - 50), min(end, sid + 50) + 1)
        
        for dsid in dense_range:
            if dsid in all_found:
                continue
            result = fetch_ouzhi_raw(dsid)
            if result.get('status') == 'ok':
                title = match_quick_check(result.get('html', ''))
                if title and tournament_filter and tournament_filter in title:
                    all_found[dsid] = title
                    print(f"  ✓ {dsid}: {title[:60]}")
            time.sleep(0.3)
    
    found_ids = sorted(all_found.keys())
    print(f"\nDense scan found {len(found_ids)} unique IDs")
    
    # Phase 3: For each shuju ID, fetch and parse the full ouzhi data
    print(f"\nPhase 3: Parsing ouzhi data for {len(found_ids)} matches...")
    matches = []
    
    for sid in found_ids:
        result = fetch_ouzhi_raw(sid)
        if result.get('status') != 'ok':
            continue
        parsed = parse_ouzhi(result['html'], sid)
        if parsed:
            matches.append(parsed)
            print(f"  ✓ {sid}: {parsed.get('home_team','?')} vs {parsed.get('away_team','?')} "
                  f"{parsed.get('home_score',0)}-{parsed.get('away_score',0)} "
                  f"| Pinnacle: {parsed['pinnacle']['closing']}")
        time.sleep(0.2)
    
    return matches

def save_backtest_format(matches, filename, is_wc=True):
    """Save in the same format as wc2022_backtest_data.json."""
    output = {'matches': []}
    
    for i, m in enumerate(matches):
        # Determine stage
        stage = determine_stage(i, is_wc)
        
        match_out = {
            'shuju_id': m['sid'],
            'date': m.get('date', ''),
            'home_team': m.get('home_team', ''),
            'away_team': m.get('away_team', ''),
            'home_score': m.get('home_score', 0),
            'away_score': m.get('away_score', 0),
            'stage': stage,
            'result': m.get('result', ''),
            'ouzhi': {
                'bookmakers': m.get('bookmakers', []),
                'avg_closing': m.get('avg_closing', {}),
            },
        }
        
        # Add Pinnacle specifically
        pinn = m.get('pinnacle', {})
        if pinn.get('closing'):
            match_out['ouzhi']['pinnacle'] = {
                'closing_home': pinn['closing']['home'],
                'closing_draw': pinn['closing']['draw'],
                'closing_away': pinn['closing']['away'],
            }
            if pinn.get('opening'):
                match_out['ouzhi']['pinnacle']['opening_home'] = pinn['opening']['home']
                match_out['ouzhi']['pinnacle']['opening_draw'] = pinn['opening']['draw']
                match_out['ouzhi']['pinnacle']['opening_away'] = pinn['opening']['away']
        
        output['matches'].append(match_out)
    
    # Sort by date first
    output['matches'].sort(key=lambda x: (x['date'], x['shuju_id']))
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # Also save a quick HTML report
    print(f"\nSaved {len(output['matches'])} matches to {filename}")
    
    # Quick stats
    correct = sum(1 for m in output['matches'] if 
                  m['result'] == determine_fav_direction(m))
    total = len(output['matches'])
    print(f"Direction prediction (Pinnacle avg closing = fav): {correct}/{total} = {correct/max(total,1):.1%}")

def determine_fav_direction(m):
    """Get favorite direction from Pinnacle closing odds."""
    oz = m.get('ouzhi', {})
    pinn = oz.get('pinnacle', {})
    if pinn.get('closing_home'):
        h, d, a = pinn['closing_home'], pinn['closing_draw'], pinn['closing_away']
        if h < d and h < a: return 'home'
        if a < h and a < d: return 'away'
    return 'draw'

def scan_wc2018():
    """Scan for 2018 World Cup matches."""
    # Known: final at 742548. Group stage should be in 740000-743000 range
    # Let's try multiple ranges
    matches = []
    
    for start, end in [(740000, 741000, 5), (741000, 742000, 5), (742000, 743000, 5)]:
        found = efficient_scan(start, end, step=5, tournament_filter='2018世界杯', max_gap=30)
        matches.extend(found)
    
    # Deduplicate
    seen = set()
    unique = []
    for m in matches:
        if m['sid'] not in seen:
            seen.add(m['sid'])
            unique.append(m)
    unique.sort(key=lambda x: x['sid'])
    
    save_backtest_format(unique, os.path.join(CACHE_DIR, 'wc2018_backtest.json'), is_wc=True)
    return unique

def scan_euro2024():
    """Scan for 2024 European Championship matches."""
    matches = []
    
    for start, end in [(1140000, 1141000, 10), (1141000, 1142000, 10), 
                       (1142000, 1143000, 10), (1143000, 1144500, 10)]:
        found = efficient_scan(start, end, step=10, tournament_filter='2024欧洲杯', max_gap=30)
        matches.extend(found)
    
    seen = set()
    unique = []
    for m in matches:
        if m['sid'] not in seen:
            seen.add(m['sid'])
            unique.append(m)
    unique.sort(key=lambda x: x['sid'])
    
    save_backtest_format(unique, os.path.join(CACHE_DIR, 'euro2024_backtest.json'), is_wc=False)
    return unique

if __name__ == '__main__':
    ensure_cache()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 fetch_tournament_data_v3.py --test           # Test parsing")
        print("  python3 fetch_tournament_data_v3.py --scan-wc2018    # Scan 2018 WC")
        print("  python3 fetch_tournament_data_v3.py --scan-euro2024  # Scan Euro 2024")
        print("  python3 fetch_tournament_data_v3.py --probe RANGE    # Probe a specific range")
        sys.exit(0)
    
    if sys.argv[1] == '--test':
        for sid in [742548, 1144464]:
            result = fetch_ouzhi_raw(sid)
            if result.get('status') == 'ok':
                parsed = parse_ouzhi(result['html'], sid)
                print(json.dumps(parsed, ensure_ascii=False, indent=2)[:800])
            time.sleep(0.5)
    
    elif sys.argv[1] == '--scan-wc2018':
        scan_wc2018()
    
    elif sys.argv[1] == '--scan-euro2024':
        scan_euro2024()
    
    elif sys.argv[1] == '--probe':
        start = int(sys.argv[2]) if len(sys.argv) > 2 else 740000
        end = int(sys.argv[3]) if len(sys.argv) > 3 else 743000
        step = int(sys.argv[4]) if len(sys.argv) > 4 else 50
        efficient_scan(start, end, step)
