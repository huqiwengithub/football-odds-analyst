#!/usr/bin/env python3
"""Batch fetch 2018 WC data. Known IDs: group 705814-705861, final 742548, 3rd 742549"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
from fetch_tournament_data_v3 import fetch_ouzhi_raw, parse_ouzhi, save_backtest_format

CACHE_DIR = os.path.join(os.path.dirname(__file__), '.cache/tournament_data')
os.makedirs(CACHE_DIR, exist_ok=True)

# Known 2018 WC IDs
group_ids = list(range(705814, 705862))  # 48 matches
ko_ids = [742548, 742549]  # final, 3rd place

all_ids = group_ids + ko_ids
all_ids.sort()

print(f"Fetching {len(all_ids)} known 2018 WC matches...")
matches = []

for i, sid in enumerate(all_ids):
    print(f"  [{i+1}/{len(all_ids)}] {sid}...", end=" ", flush=True)
    result = fetch_ouzhi_raw(sid)
    if result.get('status') == 'ok':
        parsed = parse_ouzhi(result['html'], sid)
        if parsed:
            matches.append(parsed)
            print(f"✓ {parsed.get('home_team','?')} vs {parsed.get('away_team','?')} ({parsed.get('home_score',0)}-{parsed.get('away_score',0)})")
        else:
            print(f"✗ parse failed")
    else:
        print(f"✗ fetch failed: {result.get('code', result.get('msg','?'))}")
    time.sleep(0.3)

# Also find KO matches by scanning
print(f"\nFinding remaining 14 KO matches (R16+QF+SF)...")

# Based on 2022 WC pattern: KO stage ~37000 after group stage
# 2018 group end: 705861, 2018 final: 742548
# The other KO matches should be between these ranges
# Let's try scanning smart ranges

import concurrent.futures

def check_ko(sid):
    """Quick check for 2018 WC KO match."""
    try:
        url = f"https://odds.500.com/fenxi/ouzhi-{sid}.shtml"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            html = resp.read().decode('gb2312', errors='replace')
    except:
        return None
    if '2018世界杯' not in html or 'cid=1055' not in html:
        return None
    # Check date - KO matches are June 30 - July 15
    d = __import__('re').search(r'(\d{4}-\d{2}-\d{2})', html)
    if d:
        date = d.group(1)
        if date >= '2018-06-30':
            m = __import__('re').search(r'<title>(.*?)</title>', html)
            s = __import__('re').search(r'odds_hd_bf.*?<strong>\s*(\d+)\s*:\s*(\d+)\s*</strong>', html)
            score = f"{s.group(1)}-{s.group(2)}" if s else "?-?"
            return (sid, date, score, m.group(1)[:60] if m else '?')
    return None

# Try scanning ranges
ranges_to_try = [(730000, 742548, 5), (720000, 730000, 10), (715000, 720000, 10)]
all_ko = []

for start, end, step in ranges_to_try:
    sids = list(range(start, end, step))
    print(f"  Scanning {start}-{end} (step={step}, {len(sids)} IDs)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        fs = {ex.submit(check_ko, sid): sid for sid in sids}
        for f in concurrent.futures.as_completed(fs):
            r = f.result()
            if r:
                all_ko.append(r)
                sid, date, score, title = r
                print(f"  ✓ KO FOUND: {sid}: {date} [{score}] {title}")
    time.sleep(0.5)

if all_ko:
    all_ko.sort()
    print(f"\nFound {len(all_ko)} more KO matches:")
    for sid, date, score, title in all_ko:
        print(f"  {sid}: {date} [{score}] {title}")
    
    # Fetch full data for new KO matches
    new_sids = [r[0] for r in all_ko if r[0] not in ko_ids]
    print(f"\nFetching full data for {len(new_sids)} new KO matches...")
    for sid in new_sids:
        result = fetch_ouzhi_raw(sid)
        if result.get('status') == 'ok':
            parsed = parse_ouzhi(result['html'], sid)
            if parsed:
                matches.append(parsed)
                print(f"  ✓ {sid}: {parsed.get('home_team','?')} vs {parsed.get('away_team','?')}")
        time.sleep(0.3)

if matches:
    # Deduplicate
    seen = set()
    unique = []
    for m in matches:
        if m['sid'] not in seen:
            seen.add(m['sid'])
            unique.append(m)
    unique.sort(key=lambda x: x.get('date', ''))
    
    print(f"\nTotal unique matches: {len(unique)} (out of 64)")
    save_backtest_format(unique, os.path.join(CACHE_DIR, 'wc2018_backtest.json'), is_wc=True)
else:
    print("No matches found!")
