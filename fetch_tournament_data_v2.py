#!/usr/bin/env python3
"""
Fetch historical tournament data from 500.com deep analysis pages.
v2: Robust parser for the nested table structure.

Format:
  Each bookmaker row has nested tables with 2 rows:
    Row 1 (td_show_cp): Closing odds (current/live odds closest to match time)
    Row 2 (bg-a/bg-b): Opening odds (initial odds)
"""

import urllib.request, urllib.error
import json, re, time, sys, os, concurrent.futures

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
PINNACLE_CID = 1055
MAX_WORKERS = 3  # Be gentle with 500.com

CACHE_DIR = "/Users/tracy/Desktop/足彩/.cache/tournament_data"

def ensure_cache():
    os.makedirs(CACHE_DIR, exist_ok=True)

def cache_path(sid, page="ouzhi"):
    return os.path.join(CACHE_DIR, f"{page}_{sid}.json")

def fetch_page(sid, page="ouzhi"):
    """Fetch a deep analysis page with caching."""
    cpath = cache_path(sid, page)
    if os.path.exists(cpath):
        with open(cpath) as f:
            return json.load(f)
    
    url = f"https://odds.500.com/fenxi/{page}-{sid}.shtml"
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Referer": "https://www.500.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            result = {"status": "not_found", "sid": sid}
            with open(cpath, 'w') as f:
                json.dump(result, f)
            return result
        return {"status": "error", "sid": sid, "msg": str(e)}
    except Exception as e:
        return {"status": "error", "sid": sid, "msg": str(e)}
    
    html = raw.decode('gb2312', errors='replace')
    result = {"status": "ok", "sid": sid, "html": html}
    with open(cpath, 'w') as f:
        json.dump(result, f, ensure_ascii=False)
    return result

def extract_title(html):
    m = re.search(r'<title>(.*?)</title>', html)
    return m.group(1) if m else ''

def extract_match_info(html):
    """Extract match metadata from HTML."""
    info = {}
    title = extract_title(html)
    info['title'] = title
    
    # Parse title: "法国VS克罗地亚(2018世界杯)-百家欧赔-500彩票网"
    m = re.match(r'(.+?)VS(.+?)\((\d{4}[^)]*)\)', title)
    if m:
        info['home_team'] = m.group(1).strip()
        info['away_team'] = m.group(2).strip()
        info['tournament'] = m.group(3).strip()
    else:
        # Try alternative: "西班牙VS英格兰(2024欧洲杯)-百家欧赔-500彩票网"
        m = re.match(r'(.+?)VS(.+?)\((\d{4}[^)]*)\)', title.replace('(','('))
        if m:
            info['home_team'] = m.group(1).strip()
            info['away_team'] = m.group(2).strip()
            info['tournament'] = m.group(3).strip()
    
    return info

def extract_pinnacle_odds(html):
    """Extract Pinnacle opening and closing odds from ouzhi HTML."""
    # Find Pinnacle row
    idx = html.find(f'cid={PINNACLE_CID}')
    if idx < 0:
        return None
    
    # Navigate to the parent <tr> that contains this cid
    tr_start = html.rfind('<tr', idx - 500, idx)
    if tr_start < 0:
        return None
    
    # Find the closing </tr> by counting nested tags
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
    
    # Extract odds from nested td elements
    # Closing odds (first tr in nested table, td_show_cp)
    close_match = re.findall(r'<tr class="tr_bdb[^"]*"[^>]*>.*?<td[^>]*>\s*(\d+\.\d+)\s*</td>.*?<td[^>]*>\s*(\d+\.\d+)\s*</td>.*?<td[^>]*>\s*(\d+\.\d+)\s*</td>', row_html, re.DOTALL)
    
    if close_match:
        closing = {
            'home': float(close_match[0][0]),
            'draw': float(close_match[0][1]),
            'away': float(close_match[0][2]),
        }
    else:
        # Fallback: use first set of odds numbers
        all_odds = re.findall(r'>\s*(\d+\.\d+)\s*<', row_html)
        spf_odds = [float(o) for o in all_odds if 1.0 < float(o) < 50.0]
        if len(spf_odds) >= 3:
            closing = {'home': spf_odds[0], 'draw': spf_odds[1], 'away': spf_odds[2]}
        else:
            return None
    
    # Opening odds (second tr in nested table)
    # Look for <tr> without td_show_cp class, after the first odds table
    open_match = re.findall(r'<tr(?!.*td_show_cp)[^>]*>.*?<td[^>]*>\s*(\d+\.\d+)\s*</td>.*?<td[^>]*>\s*(\d+\.\d+)\s*</td>.*?<td[^>]*>\s*(\d+\.\d+)\s*</td>', row_html, re.DOTALL)
    
    if open_match:
        opening = {
            'home': float(open_match[-1][0]),  # Take the LAST match (should be the opening row)
            'draw': float(open_match[-1][1]),
            'away': float(open_match[-1][2]),
        }
    else:
        opening = None
    
    return {'closing': closing, 'opening': opening}

def extract_bookmaker_odds(html):
    """Extract odds from ALL bookmakers (for avg computation)."""
    bookmakers = []
    
    # Find all bookmaker rows
    # Pattern: <tr id="CID" ttl="zy" xls="row">
    rows = re.findall(r'<tr[^>]*\bid="(\d+)"[^>]*ttl[^>]*xls[^>]*>(.*?)</tr>', html, re.DOTALL)
    
    for cid_str, row_html in rows:
        cid = int(cid_str)
        if cid == 0 or cid > 10000:
            continue
        
        # Get closing odds from first tr in nested table
        odds = re.findall(r'<tr class="tr_bdb[^"]*"[^>]*>.*?<td[^>]*>\s*(\d+\.\d+)\s*</td>.*?<td[^>]*>\s*(\d+\.\d+)\s*</td>.*?<td[^>]*>\s*(\d+\.\d+)\s*</td>', row_html, re.DOTALL)
        
        if odds:
            bookmakers.append({
                'cid': cid,
                'closing_home': float(odds[0][0]),
                'closing_draw': float(odds[0][1]),
                'closing_away': float(odds[0][2]),
            })
        
        # Get opening odds
        open_odds = re.findall(r'<tr(?!.*td_show_cp)[^>]*>.*?<td[^>]*>\s*(\d+\.\d+)\s*</td>.*?<td[^>]*>\s*(\d+\.\d+)\s*</td>.*?<td[^>]*>\s*(\d+\.\d+)\s*</td>', row_html, re.DOTALL)
        if open_odds and bookmakers:
            bookmakers[-1]['opening_home'] = float(open_odds[-1][0])
            bookmakers[-1]['opening_draw'] = float(open_odds[-1][1])
            bookmakers[-1]['opening_away'] = float(open_odds[-1][2])
    
    return bookmakers

def determine_result(home_score, away_score):
    if home_score > away_score:
        return 'home'
    elif away_score > home_score:
        return 'away'
    else:
        return 'draw'

def determine_stage_from_tournament(tournament, match_index, total_matches):
    """Rough stage determination based on match index."""
    if '世界杯' in tournament:
        # 64 matches: 48 group + 8 R16 + 4 QF + 2 SF + 1 F + 1 3rd
        if match_index < 48:
            return 'group'
        elif match_index < 56:
            return 'round16'
        elif match_index < 60:
            return 'quarter'
        elif match_index < 62:
            return 'semi'
        elif match_index < 63:
            return 'third'
        else:
            return 'final'
    else:
        # Euro: 36 group + 8 R16 + 4 QF + 2 SF + 1 F = 51
        if match_index < 36:
            return 'group'
        elif match_index < 44:
            return 'round16'
        elif match_index < 48:
            return 'quarter'
        elif match_index < 50:
            return 'semi'
        else:
            return 'final'

def fetch_match(sid, tournament_filter=None):
    """Fetch complete match data for a given shuju ID."""
    data = fetch_page(sid)
    if data.get('status') != 'ok':
        return None
    
    html = data['html']
    
    # Check if it's the right tournament
    info = extract_match_info(html)
    tournament = info.get('tournament', '')
    
    if tournament_filter and tournament_filter not in tournament:
        return None
    
    # Extract odds
    pinn = extract_pinnacle_odds(html)
    if not pinn or not pinn.get('closing'):
        return None
    
    bookmakers = extract_bookmaker_odds(html)
    
    # Look for score from the URL context (the page URL often has score info)
    # Try to find score pattern: "4:2" in various contexts
    home_score, away_score = 0, 0
    
    # Search for score patterns in the entire HTML (title, meta, etc.)
    # The title might be: "法国4:2克罗地亚..."
    score_patterns = [
        # Pattern 1: In title like "法国4:2克罗地亚..."
        re.search(r'(?:^|[\u4e00-\u9fff]+)(\d+)[:：](\d+)(?:[\u4e00-\u9fff]+)', html[:500]),
        # Pattern 2: General number:number pattern
        re.search(r'\b(\d+)[:：](\d+)\b', html[:2000]),
    ]
    
    for sp in score_patterns:
        if sp:
            s1, s2 = int(sp.group(1)), int(sp.group(2))
            if s1 <= 20 and s2 <= 20:  # Reasonable score range
                home_score = s1
                away_score = s2
                break
    
    result = determine_result(home_score, away_score)
    
    return {
        'shuju_id': sid,
        'home_team': info.get('home_team', ''),
        'away_team': info.get('away_team', ''),
        'home_score': home_score,
        'away_score': away_score,
        'tournament': tournament,
        'result': result,
        'pinnacle': pinn,
        'bookmakers': bookmakers,
    }

def scan_range(start, end, step=1, tournament_filter=None):
    """Scan a range of shuju IDs for tournament matches."""
    matches = []
    
    for sid in range(start, end + 1, step):
        result = fetch_match(sid, tournament_filter)
        if result:
            matches.append(result)
            print(f"  ✓ {sid}: {result['home_team']} vs {result['away_team']} ({result['tournament']}) | {result['home_score']}-{result['away_score']}")
        time.sleep(0.5)  # Be respectful
    
    return matches

def scan_parallel(sids, tournament_filter=None, max_workers=3):
    """Scan multiple shuju IDs in parallel."""
    matches = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_sid = {
            executor.submit(fetch_match, sid, tournament_filter): sid 
            for sid in sids
        }
        for future in concurrent.futures.as_completed(future_to_sid):
            sid = future_to_sid[future]
            try:
                result = future.result()
                if result:
                    matches.append(result)
                    print(f"  ✓ {sid}: {result['home_team']} vs {result['away_team']} ({result['tournament']}) | {result['home_score']}-{result['away_score']}")
                else:
                    print(f"  - {sid}: no match")
            except Exception as e:
                print(f"  ✗ {sid}: error - {e}")
    
    return matches

def save_dataset(matches, filename):
    """Save matches in the wc2022_backtest_data.json format."""
    output = {
        'matches': []
    }
    
    for i, m in enumerate(matches):
        match_out = {
            'shuju_id': m['shuju_id'],
            'date': '',  # Need to extract date still
            'home_team': m['home_team'],
            'away_team': m['away_team'],
            'home_score': m['home_score'],
            'away_score': m['away_score'],
            'stage': m.get('stage', 'group'),
            'result': m['result'],
            'ouzhi': {
                'pinnacle': {
                    'opening_home': m['pinnacle']['opening']['home'],
                    'opening_draw': m['pinnacle']['opening']['draw'],
                    'opening_away': m['pinnacle']['opening']['away'],
                    'closing_home': m['pinnacle']['closing']['home'],
                    'closing_draw': m['pinnacle']['closing']['draw'],
                    'closing_away': m['pinnacle']['closing']['away'],
                } if m['pinnacle'].get('opening') else {
                    'closing_home': m['pinnacle']['closing']['home'],
                    'closing_draw': m['pinnacle']['closing']['draw'],
                    'closing_away': m['pinnacle']['closing']['away'],
                },
                'bookmakers': m['bookmakers'],
                'avg_closing': {},
            },
        }
        
        # Compute average closing odds if we have bookmakers
        if m['bookmakers']:
            avg_h = sum(b['closing_home'] for b in m['bookmakers']) / len(m['bookmakers'])
            avg_d = sum(b['closing_draw'] for b in m['bookmakers']) / len(m['bookmakers'])
            avg_a = sum(b['closing_away'] for b in m['bookmakers']) / len(m['bookmakers'])
            match_out['ouzhi']['avg_closing'] = {'home': avg_h, 'draw': avg_d, 'away': avg_a}
        
        output['matches'].append(match_out)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved {len(matches)} matches to {filename}")

if __name__ == '__main__':
    ensure_cache()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # Test with known matches
        for sid in [742548, 1144464, 742500]:
            result = fetch_match(sid)
            if result:
                print(json.dumps(result, ensure_ascii=False, indent=2)[:500])
            time.sleep(0.5)
    
    elif len(sys.argv) > 1 and sys.argv[1] == '--scan-wc2018':
        print("Scanning 2018 World Cup matches...")
        # 2018 WC shuju IDs appear to be in 74xxxx range
        # The final is at 742548, so group stage matches should be earlier
        # Let's probe ranges
        all_matches = []
        
        # Probe wide range first to find the cluster
        print("Probing for 2018 WC matches...")
        test_ids = list(range(740000, 743000, 20))
        matches = scan_parallel(test_ids, '2018', max_workers=3)
        all_matches.extend(matches)
        
        if all_matches:
            all_matches.sort(key=lambda m: m['shuju_id'])
            min_id = min(m['shuju_id'] for m in all_matches)
            max_id = max(m['shuju_id'] for m in all_matches)
            print(f"\nFound {len(all_matches)} matches in range {min_id}-{max_id}")
            
            # Now do a dense scan around the found range
            dense = list(range(max(740000, min_id - 100), min(743000, max_id + 100), 1))
            print(f"\nDense scanning {dense[0]}-{dense[-1]}...")
            more = scan_parallel(dense, '2018', max_workers=3)
            all_matches.extend(more)
            
            # Deduplicate and sort
            seen = set()
            unique = []
            for m in all_matches:
                if m['shuju_id'] not in seen:
                    seen.add(m['shuju_id'])
                    unique.append(m)
            unique.sort(key=lambda m: m['shuju_id'])
            
            save_dataset(unique, os.path.join(CACHE_DIR, 'wc2018_dataset.json'))
    
    elif len(sys.argv) > 1 and sys.argv[1] == '--scan-euro2024':
        print("Scanning 2024 European Championship matches...")
        # 2024 Euro final: 1144464
        # Group stage should be in 1144xxx range or perhaps 1143xxx, 1142xxx
        
        all_matches = []
        
        # Probe range
        test_ids = list(range(1144000, 1144500, 10))
        matches = scan_parallel(test_ids, '2024', max_workers=3)
        all_matches.extend(matches)
        
        if all_matches:
            all_matches.sort(key=lambda m: m['shuju_id'])
            min_id = min(m['shuju_id'] for m in all_matches)
            max_id = max(m['shuju_id'] for m in all_matches)
            print(f"\nFound {len(all_matches)} matches in range {min_id}-{max_id}")
        
        seen = set()
        unique = []
        for m in all_matches:
            if m['shuju_id'] not in seen:
                seen.add(m['shuju_id'])
                unique.append(m)
        unique.sort(key=lambda m: m['shuju_id'])
        
        save_dataset(unique, os.path.join(CACHE_DIR, 'euro2024_dataset.json'))
    
    else:
        print("Usage:")
        print("  python3 fetch_tournament_data_v2.py --test           # Test parsing")
        print("  python3 fetch_tournament_data_v2.py --scan-wc2018    # Scan 2018 WC")
        print("  python3 fetch_tournament_data_v2.py --scan-euro2024  # Scan Euro 2024")
