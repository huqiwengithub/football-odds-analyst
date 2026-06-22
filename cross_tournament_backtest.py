#!/usr/bin/env python3
"""
Cross-tournament FVS/DRM backtest: 2022 WC + 2018 WC + 2024 Euro
Tests whether the v3.3.1 calibration (DRM>=2 -> VETO) holds across tournaments.
"""

import json, os, sys
from collections import defaultdict

PINNACLE_CID = 1055
BASE_DIR = "/Users/tracy/Desktop/足彩"

DATASETS = {
    "2022 WC": os.path.join(BASE_DIR, ".cache/wc2022_backtest_data.json"),
    "2018 WC": os.path.join(BASE_DIR, ".cache/tournament_data/wc2018_backtest.json"),
    "2024 Euro": os.path.join(BASE_DIR, ".cache/tournament_data/euro2024_backtest.json"),
}

def load_dataset(path):
    """Load a tournament dataset in the standard format."""
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    return data.get('matches', [])

def de_vig(h, d, a):
    ih, id_, ia = 1.0/h, 1.0/d, 1.0/a
    t = ih + id_ + ia
    return ih/t, id_/t, ia/t, t-1.0

def fav_dir(h, d, a):
    if h < d and h < a: return 'home', h
    if a < h and a < d: return 'away', a
    return 'draw', min(h, d, a)

def pinn_odds(m):
    """Get Pinnacle odds from match data."""
    oz = m.get('ouzhi', {})
    pinn = oz.get('pinnacle', {})
    if not pinn:
        return None
    
    # Handle both flat and nested formats
    if 'closing_home' in pinn:
        return {
            'close_h': pinn['closing_home'],
            'close_d': pinn['closing_draw'],
            'close_a': pinn['closing_away'],
            'open_h': pinn.get('opening_home', pinn['closing_home']),
            'open_d': pinn.get('opening_draw', pinn['closing_draw']),
            'open_a': pinn.get('opening_away', pinn['closing_away']),
        }
    elif 'closing' in pinn and pinn['closing']:
        c = pinn['closing']
        o = pinn.get('opening', {})
        return {
            'close_h': c['home'], 'close_d': c['draw'], 'close_a': c['away'],
            'open_h': o.get('home', c['home']),
            'open_d': o.get('draw', c['draw']),
            'open_a': o.get('away', c['away']),
        }
    return None

def avg_odds(m):
    """Get average closing odds (fallback to Pinnacle if no bookmakers)."""
    oz = m.get('ouzhi', {})
    bms = oz.get('bookmakers', [])
    if bms:
        h = sum(b.get('closing_home', 0) for b in bms if b.get('closing_home'))
        d = sum(b.get('closing_draw', 0) for b in bms if b.get('closing_draw'))
        a = sum(b.get('closing_away', 0) for b in bms if b.get('closing_away'))
        n = len(bms)
        return {'avg_h': h/n, 'avg_d': d/n, 'avg_a': a/n}
    
    # Fallback to Pinnacle
    pinn = oz.get('pinnacle', {})
    if pinn:
        if 'closing_home' in pinn:
            return {'avg_h': pinn['closing_home'], 'avg_d': pinn['closing_draw'], 'avg_a': pinn['closing_away']}
        elif 'closing' in pinn and pinn['closing']:
            return {'avg_h': pinn['closing']['home'], 'avg_d': pinn['closing']['draw'], 'avg_a': pinn['closing']['away']}
    return None

def compute_fvs_drm(m, all_matches, pinn, avg_odds_data, ph, pd, pa):
    """Compute FVS and DRM scores."""
    fvs_s, fvs_t, drm_s, drm_t = 0, [], 0, []
    
    fav_odds = min(avg_odds_data['avg_h'], avg_odds_data['avg_d'], avg_odds_data['avg_a'])
    
    # FVS-1: Ultra-low odds
    if fav_odds < 1.18: fvs_s += 2; fvs_t.append('FVS1+2')
    elif fav_odds < 1.25: fvs_s += 1; fvs_t.append('FVS1+1')
    
    # FVS-2: All-low-odds day (systemic)
    same_day = [x for x in all_matches if x.get('date') == m.get('date')]
    if len(same_day) >= 2:
        all_low = True
        for x in same_day:
            x_avg = avg_odds(x)
            if x_avg:
                x_fav = min(x_avg['avg_h'], x_avg['avg_d'], x_avg['avg_a'])
                if x_fav > 1.50:
                    all_low = False
                    break
        if all_low:
            fvs_s += 2; fvs_t.append('FVS2+2')
    
    # FVS-3: Mid-odds cluster
    if len(same_day) >= 2:
        mid_n = sum(1 for x in same_day if 1.20 <= min(avg_odds(x)['avg_h'], avg_odds(x)['avg_d'], avg_odds(x)['avg_a']) <= 1.50 if avg_odds(x))
        if mid_n >= 2:
            fvs_s += 1; fvs_t.append('FVS3+1')
    
    # FVS-6: AH deviation (simplified - use odds spread)
    o_spread = max(ph, pd, pa) - min(ph, pd, pa)
    if fav_odds < 1.50 and o_spread > 0.55:
        pass  # Clean case
    
    # FVS-7: Elevated draw probability
    if pd > 0.25 and fav_odds < 1.80:
        fvs_s += 1; fvs_t.append('FVS7+1')
    
    # FVS-11: Late reversal
    if pinn:
        if pinn.get('open_h') and fav_odds < 1.50:
            h_change = (pinn['close_h'] - pinn['open_h']) / pinn['open_h']
            if h_change > 0.02:
                fvs_s += 2; fvs_t.append('FVS11+2')
            # Also check if away favorite odds rose
            a_change = (pinn['close_a'] - pinn['open_a']) / pinn['open_a'] if pinn['open_a'] else 0
            if fav_odds < 1.50 and a_change > 0.02:
                fvs_s += 2; fvs_t.append('FVS11+2')
    
    # DRM-1: De-vig draw probability
    if pd > 0.28: drm_s += 2; drm_t.append('DRM1+2')
    elif pd > 0.25: drm_s += 1; drm_t.append('DRM1+1')
    
    # DRM-7: Knockout stage
    if m.get('stage') in ('round16', 'quarter', 'semi', 'final', 'round_of_16'):
        drm_s += 2; drm_t.append('DRM7+2')
    
    return fvs_s, fvs_t, drm_s, drm_t

def verdict(fvs, drm):
    """v3.3.1 calibrated verdict."""
    if fvs >= 6: return '🚫MELT'
    if fvs >= 4 or (fvs >= 2 and drm >= 4): return '🔴HIGH'
    if drm >= 2: return '🔶DRAW_VETO'
    if fvs >= 2: return '⚠️WARN'
    return '✅OK'

def run_backtest(matches, name):
    """Run FVS/DRM backtest on a dataset."""
    if not matches:
        return None
    
    r = {'total':0, 'old_ok':0, 'old_bad':0, 'veto_ok':0, 'veto_bad':0, 'pass_ok':0, 'pass_bad':0}
    rows = []
    
    for m in matches:
        p = pinn_odds(m)
        if not p:
            continue
        
        avg = avg_odds(m)
        if not avg:
            continue
        
        ph, pd, pa, ov = de_vig(p['close_h'], p['close_d'], p['close_a'])
        d, fav_odds = fav_dir(avg['avg_h'], avg['avg_d'], avg['avg_a'])
        act = m.get('result', '')
        if not act:
            continue
        
        fvs, ft, drm, dt = compute_fvs_drm(m, matches, p, avg, ph, pd, pa)
        v = verdict(fvs, drm)
        
        old_right = (d == act)
        vetoed = (fvs >= 4) or (fvs >= 2 and drm >= 4) or (drm >= 2)
        
        r['total'] += 1
        if old_right: r['old_ok'] += 1
        else: r['old_bad'] += 1
        
        if vetoed:
            if not old_right: r['veto_bad'] += 1  # Saved
            else: r['veto_ok'] += 1  # Cost
        else:
            if old_right: r['pass_ok'] += 1
            else: r['pass_bad'] += 1
        
        rows.append({
            'match': f"{m.get('home_team','?')} vs {m.get('away_team','?')}",
            'date': m.get('date', ''),
            'score': f"{m.get('home_score',0)}-{m.get('away_score',0)}",
            'dir': d, 'act': act,
            'fvs': fvs, 'drm': drm,
            'verdict': v,
            'vetoed': vetoed,
            'old': old_right,
        })
    
    return {'stats': r, 'rows': rows, 'name': name}

def print_report(results):
    """Print unified comparison report."""
    print("=" * 100)
    print("   FVS/DRM BACKTEST: CROSS-TOURNAMENT VALIDATION")
    print("   Tests whether v3.3.1 calibration holds across tournaments")
    print("=" * 100)
    
    print(f"\n{'Tournament':<15} {'Total':>6} {'Old Acc':>9} {'New Acc':>9} "
          f"{'Vetoed':>7} {'Saved':>7} {'Cost':>6} {'Prec':>7} {'Recall':>7} {'Chg':>7}")
    print("-" * 100)
    
    totals = {'total':0, 'old_ok':0, 'old_bad':0, 'veto_ok':0, 'veto_bad':0, 'pass_ok':0, 'pass_bad':0}
    
    for name, result in results:
        if not result:
            print(f"{name:<15} {'NO DATA':>50}")
            continue
        s = result['stats']
        tot = s['total']
        old_acc = s['old_ok'] / max(tot, 1)
        new_tot = s['pass_ok'] + s['pass_bad']
        new_acc = s['pass_ok'] / max(new_tot, 1)
        veto_t = s['veto_ok'] + s['veto_bad']
        precision = s['veto_bad'] / max(veto_t, 1)
        recall = s['veto_bad'] / max(s['old_bad'], 1)
        chg = new_acc - old_acc
        
        for k in totals: totals[k] += s[k]
        
        print(f"{name:<15} {tot:>6} {old_acc:>7.1%} {new_acc:>7.1%} "
              f"{veto_t:>7} {s['veto_bad']:>7} {s['veto_ok']:>6} "
              f"{precision:>6.0%} {recall:>6.0%} {chg:>+6.1%}")
    
    # Totals
    tot_all = totals['total']
    old_acc = totals['old_ok'] / max(tot_all, 1)
    new_tot = totals['pass_ok'] + totals['pass_bad']
    new_acc = totals['pass_ok'] / max(new_tot, 1)
    veto_t = totals['veto_ok'] + totals['veto_bad']
    precision = totals['veto_bad'] / max(veto_t, 1)
    recall = totals['veto_bad'] / max(totals['old_bad'], 1)
    chg = new_acc - old_acc
    
    print("-" * 100)
    print(f"{'COMBINED':<15} {tot_all:>6} {old_acc:>7.1%} {new_acc:>7.1%} "
          f"{veto_t:>7} {totals['veto_bad']:>7} {totals['veto_ok']:>6} "
          f"{precision:>6.0%} {recall:>6.0%} {chg:>+6.1%}")
    
    # By DRM tier
    print(f"\n{'─' * 100}")
    print("BY DRM TIER (combined):")
    drm_groups = defaultdict(lambda: [0, 0])
    
    for _, result in results:
        if not result:
            continue
        for row in result['rows']:
            drm_groups[row['drm']][0] += 1 if row['old'] else 0
            drm_groups[row['drm']][1] += 0 if row['old'] else 1
    
    for drm in sorted(drm_groups.keys()):
        t = drm_groups[drm]
        tot = t[0] + t[1]
        if tot:
            print(f"  DRM={drm}: {t[0]}/{tot} = {t[0]/tot:.0%} correct, {t[1]} wrong")
    
    # By FVS tier
    print(f"\n{'─' * 100}")
    print("BY FVS TIER (combined):")
    fvs_groups = defaultdict(lambda: [0, 0])
    
    for _, result in results:
        if not result:
            continue
        for row in result['rows']:
            fvs_groups[row['fvs']][0] += 1 if row['old'] else 0
            fvs_groups[row['fvs']][1] += 0 if row['old'] else 1
    
    for fvs in sorted(fvs_groups.keys()):
        t = fvs_groups[fvs]
        tot = t[0] + t[1]
        if tot:
            print(f"  FVS={fvs}: {t[0]}/{tot} = {t[0]/tot:.0%} correct, {t[1]} wrong")
    
    # FVS+DRM combined matrix
    print(f"\n{'─' * 100}")
    print("FVS × DRM MATRIX (rows=correct/total):")
    
    matrix = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for _, result in results:
        if not result:
            continue
        for row in result['rows']:
            matrix[row['fvs']][row['drm']][0] += 1 if row['old'] else 0
            matrix[row['fvs']][row['drm']][1] += 1
    
    all_drms = sorted(set(drm for fvs_d in matrix.values() for drm in fvs_d))
    all_fvs = sorted(matrix.keys())
    
    # Header
    print(f"  {'FVS':>4}", end="")
    for drm in all_drms:
        print(f"  DRM={drm:>6}", end="")
    print()
    
    for fvs in all_fvs:
        print(f"  {fvs:>4}", end="")
        for drm in all_drms:
            c, t = matrix[fvs][drm]
            if t:
                print(f"  {c}/{t}={c/t:.0%}", end="")
            else:
                print(f"  {'':>8}", end="")
        print()
    
    # Key insight: DRM>=2 performance
    print(f"\n{'─' * 100}")
    print("DRM≥2 VETO ANALYSIS (combined):")
    drm2_tot = [0, 0]
    drm2_breakdown = {'draw': 0, 'home_fail': 0, 'away_fail': 0, 'other': 0}
    
    for _, result in results:
        if not result:
            continue
        for row in result['rows']:
            if row['drm'] >= 2:
                drm2_tot[0] += 1 if row['old'] else 0
                drm2_tot[1] += 1
                if not row['old']:
                    if row['act'] == 'draw':
                        drm2_breakdown['draw'] += 1
                    elif row['dir'] == 'home' and row['act'] == 'away':
                        drm2_breakdown['home_fail'] += 1
                    elif row['dir'] == 'away' and row['act'] == 'home':
                        drm2_breakdown['away_fail'] += 1
                    else:
                        drm2_breakdown['other'] += 1
    
    if drm2_tot[1]:
        print(f"  DRM≥2 total: {drm2_tot[1]} matches")
        print(f"  Old system correct: {drm2_tot[0]} = {drm2_tot[0]/drm2_tot[1]:.0%}")
        print(f"  Wrong (would be saved by VETO): {drm2_tot[1]-drm2_tot[0]} = {(drm2_tot[1]-drm2_tot[0])/drm2_tot[1]:.0%}")
        print(f"    Of which draws: {drm2_breakdown['draw']}")
        print(f"    Of which complete reversal: {drm2_breakdown['home_fail']+drm2_breakdown['away_fail']}")
    
    # Row-by-row for DRM>=2
    print(f"\n{'─' * 100}")
    print("DRM≥2 DETAILS:")
    for _, result in results:
        if not result:
            continue
        for row in result['rows']:
            if row['drm'] >= 2:
                mark = '✅' if row['old'] else '❌'
                print(f"  [{row['date']}] {row['match'][:35]:<35} {row['score']:>4} | "
                      f"Dir:{row['dir']:>5} Act:{row['act']:>4} | FVS:{row['fvs']} DRM:{row['drm']} | {mark}")

def main():
    results = []
    for name, path in DATASETS.items():
        print(f"Loading {name} from {path}...")
        matches = load_dataset(path)
        if matches:
            print(f"  Loaded {len(matches)} matches")
            result = run_backtest(matches, name)
            results.append((name, result))
        else:
            print(f"  NOT FOUND - skippping")
            results.append((name, None))
    
    print_report(results)
    
    # Save summary
    summary = {}
    for name, result in results:
        if result:
            summary[name] = {
                'total': result['stats']['total'],
                'old_accuracy': result['stats']['old_ok'] / max(result['stats']['total'], 1),
                'new_accuracy': result['stats']['pass_ok'] / max(result['stats']['pass_ok'] + result['stats']['pass_bad'], 1),
                'vetoed': result['stats']['veto_ok'] + result['stats']['veto_bad'],
                'saved': result['stats']['veto_bad'],
                'cost': result['stats']['veto_ok'],
                'pass_ok': result['stats']['pass_ok'],
                'pass_bad': result['stats']['pass_bad'],
                'rows': result['rows'],
            }
    
    with open(os.path.join(BASE_DIR, 'cross_tournament_backtest.json'), 'w') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n→ cross_tournament_backtest.json saved")

if __name__ == '__main__':
    main()
