#!/usr/bin/env python3
"""Batch fetch 2024 Euro data. Known: final 1144464"""
import sys, os, json, time, re, concurrent.futures
sys.path.insert(0, os.path.dirname(__file__))
from fetch_tournament_data_v3 import fetch_ouzhi_raw, parse_ouzhi, save_backtest_format

CACHE_DIR = os.path.join(os.path.dirname(__file__), '.cache/tournament_data')
os.makedirs(CACHE_DIR, exist_ok=True)

def quick_check(sid):
    """Quick check for 2024 Euro match."""
    try:
        url = f"https://odds.500.com/fenxi/ouzhi-{sid}.shtml"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            html = resp.read().decode('gb2312', errors='replace')
    except:
        return None
    if '2024欧洲杯' not in html or 'cid=1055' not in html:
        return None
    m = re.search(r'<title>(.*?)</title>', html)
    s = re.search(r'odds_hd_bf.*?<strong>\s*(\d+)\s*:\s*(\d+)\s*</strong>', html)
    d = re.search(r'(\d{4}-\d{2}-\d{2})', html)
    score = f"{s.group(1)}-{s.group(2)}" if s else "?-?"
    date = d.group(1) if d else '?'
    return (sid, date, score, m.group(1)[:60] if m else '?')

# Find all 2024 Euro matches
# Euro 2024: 36 group + 8 R16 + 4 QF + 2 SF + 1 F = 51 matches
# Final: June 14 - July 14, 2024
# Known: final 1144464, semi 1144460-1144463

# Probe known IDs
known_euro = [1144456, 1144457, 1144458, 1144459, 1144460, 1144461, 1144462, 1144463, 1144464]
print(f"Checking {len(known_euro)} known Euro 2024 IDs...")
for sid in known_euro:
    r = quick_check(sid)
    if r:
        print(f"  ✓ {r[0]}: {r[3]} [{r[2]}] {r[1]}")
    time.sleep(0.3)

# Try scanning ranges for group stage
# Based on pattern: final at 1144464, group stage lower
print("\nScanning for Euro 2024 group stage...")

ranges = [(1143000, 1144500, 10),  # Dense scan
          (1140000, 1143000, 25),  # Sparse scan
          (1135000, 1140000, 50)]  # Wide scan

all_euro = []

for start, end, step in ranges:
    sids = list(range(start, end, step))
    print(f"  Scanning {start}-{end} (step={step}, {len(sids)} IDs)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        fs = {ex.submit(quick_check, sid): sid for sid in sids}
        for f in concurrent.futures.as_completed(fs):
            r = f.result()
            if r:
                all_euro.append(r)
                print(f"  ✓ {r[0]}: {r[1]} [{r[2]}] {r[3]}")
    time.sleep(0.5)

if all_euro:
    all_euro.sort()
    euro_ids = sorted(set(r[0] for r in all_euro))
    print(f"\nDiscovered {len(euro_ids)} unique Euro 2024 IDs:")
    print(f"  Range: {min(euro_ids)} - {max(euro_ids)}")
    print(f"  IDs: {euro_ids}")
    
    # If we have less than 51, do a denser scan between the min and max
    if len(euro_ids) < 51:
        print(f"\nDenser scan ({len(euro_ids)} found, need 51)...")
        min_id, max_id = min(euro_ids), max(euro_ids)
        sids = list(range(min_id, max_id + 1))
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            fs = {ex.submit(quick_check, sid): sid for sid in sids}
            for f in concurrent.futures.as_completed(fs):
                r = f.result()
                if r:
                    all_euro.append(r)
                    if r[0] not in euro_ids:
                        print(f"  ✓ NEW {r[0]}: {r[1]} [{r[2]}] {r[3]}")
                        euro_ids.append(r[0])
        
        euro_ids = sorted(set(r[0] for r in all_euro))
        print(f"\nAfter dense scan: {len(euro_ids)} unique IDs")
    
    # Fetch full data
    print(f"\nFetching full ouzhi data for {len(euro_ids)} matches...")
    matches = []
    for sid in euro_ids:
        result = fetch_ouzhi_raw(sid)
        if result.get('status') == 'ok':
            parsed = parse_ouzhi(result['html'], sid)
            if parsed:
                matches.append(parsed)
        time.sleep(0.2)
    
    if matches:
        matches.sort(key=lambda x: x.get('date', ''))
        print(f"\nTotal Euro 2024 matches: {len(matches)}")
        save_backtest_format(matches, os.path.join(CACHE_DIR, 'euro2024_backtest.json'), is_wc=False)
else:
    print("No Euro 2024 matches found!")
