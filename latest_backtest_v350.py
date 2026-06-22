#!/usr/bin/env python3
"""
Latest v3.5.0 Full Backtest — Simulate Real Betting Decisions
Applies OCI-based framework and three-tier position engine on 179 matches
from 2022WC + 2018WC + 2024Euro. Simulates ¥100 per match day.
"""

import json, os, math
from collections import defaultdict

BASE_DIR = "/Users/tracy/Desktop/足彩"
OUTPUT_FILE = os.path.join(BASE_DIR, "v350_backtest_results.json")

def load_data():
    """Load cross-tournament data with raw odds for OCI computation."""
    with open(os.path.join(BASE_DIR, "cross_tournament_backtest.json")) as f:
        ct_data = json.load(f)
    return ct_data

def load_raw_matches(tournament, path):
    """Load raw match data for OCI computation."""
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    return data.get('matches', [])

def de_vig(h, d, a):
    ih, id_, ia = 1.0/h, 1.0/d, 1.0/a
    t = ih + id_ + ia
    return ih/t, id_/t, ia/t, t-1.0

def get_best_odds(bmks, side='home'):
    """Get closing odds from all bookmakers for a given side."""
    vals = []
    for b in bmks:
        v = b.get(f'closing_{side}', 0)
        if v > 1.0:
            vals.append(v)
    return vals

def compute_oci(match):
    """
    Compute OCI (Odds Change Indicator) dimensions from raw data.
    Returns dict of OCI-1 through OCI-5 scores.
    Since OCI-3 (touzhu volume) data is missing, use available proxies.
    """
    oci = {'OCI1': 0, 'OCI2': 0, 'OCI4': 0, 'OCI5': 0, 'available': 0}
    
    oz = match.get('ouzhi', {})
    yz = match.get('yazhi', {})
    
    # OCI-1: Pinnacle odds change
    pinn = oz.get('pinnacle', {})
    if pinn:
        if 'closing_home' in pinn and 'opening_home' in pinn:
            ch = pinn['closing_home']; oh = pinn['opening_home']
            ca = pinn['closing_away']; oa = pinn.get('opening_away', ca)
            if oh and ch:
                h_chg = (ch - oh) / oh
                a_chg = (ca - oa) / oa if oa else 0
                # Determine favorite: lower odds = favorite
                if ch < ca:  # home is favorite
                    oci['OCI1'] = -h_chg * 100  # positive = odds dropped (good for fav)
                else:  # away is favorite
                    oci['OCI1'] = -a_chg * 100
                oci['available'] += 1
    
    # OCI-2: Market consensus change (30-bookmaker avg vs Pinnacle)
    bmks = oz.get('bookmakers', [])
    if bmks and pinn:
        avg_h = sum(b.get('closing_home', 0) for b in bmks if b.get('closing_home', 0) > 1) / max(len([b for b in bmks if b.get('closing_home', 0) > 1]), 1)
        avg_a = sum(b.get('closing_away', 0) for b in bmks if b.get('closing_away', 0) > 1) / max(len([b for b in bmks if b.get('closing_away', 0) > 1]), 1)
        
        if 'closing_home' in pinn and 'closing_away' in pinn:
            # Check if 30-bookmaker avg direction matches Pinnacle
            pinn_fav = 'home' if pinn['closing_home'] < pinn['closing_away'] else 'away'
            avg_fav = 'home' if avg_h < avg_a else 'away'
            oci['OCI2'] = 1.0 if pinn_fav == avg_fav else -0.5
            oci['available'] += 1
    
    # OCI-4: Institution dispersion (30-bookmaker std dev)
    if bmks:
        homes = [b.get('closing_home', 0) for b in bmks if b.get('closing_home', 0) > 1]
        aways = [b.get('closing_away', 0) for b in bmks if b.get('closing_away', 0) > 1]
        if len(homes) >= 3:
            mean_h = sum(homes) / len(homes)
            var_h = sum((x - mean_h)**2 for x in homes) / len(homes)
            std_h = math.sqrt(var_h)
            # Lower std = more consensus
            oci['OCI4'] = 1.0 if std_h < 0.15 else (0.5 if std_h < 0.30 else 0.0)
            oci['available'] += 1
    
    # OCI-5: AH line verification (yazhi data)
    hcs = yz.get('handicaps', [])
    pinn_ah = yz.get('pinnacle_ah', {})
    if hcs:
        # Check if AH direction matches SPF direction
        oci['OCI5'] = 0.5  # partial credit — insufficient AH data
        oci['available'] += 1
    
    return oci

def apply_fvs1a_cleanup(fvs_score):
    """FVS-1A: FVS=1 → 0 (confirmed reverse indicator at 42% across 3 tournaments)."""
    return 0 if fvs_score == 1 else fvs_score

def three_tier_position(fvs_clean, drm_score):
    """
    v3.4.0+ Three-tier position engine.
    Based on cross-tournament backtest data:
    - FVS=2, DRM=0: 73-80% → CORE
    - FVS=0/2, DRM=0/1: 52-58% → STANDARD
    - FVS=0, DRM≥2: <50% → SKIP
    - FVS≥3+DRM≥1 or FVS≥4: VETO
    - FVS=0, DRM=0: 48-58% → STANDARD
    """
    # Check VETO conditions first
    if fvs_clean >= 4:
        return 'VETO', 0.0
    if fvs_clean >= 3 and drm_score >= 1:
        return 'VETO', 0.0
    if drm_score >= 2 and fvs_clean == 0:
        return 'VETO', 0.0  # Pure DRM veto
    
    # Three-tier position
    if fvs_clean == 2 and drm_score == 0:
        return 'CORE', 0.80  # ~78% hit rate
    elif fvs_clean == 2 and drm_score == 1:
        return 'STANDARD', 0.50  # ~58%
    elif fvs_clean == 0 and drm_score == 0:
        return 'STANDARD', 0.50  # ~52%
    elif fvs_clean == 0 and drm_score == 1:
        return 'STANDARD', 0.50  # ~55%
    elif fvs_clean == 3 and drm_score == 0:
        return 'STANDARD', 0.40  # ~60%
    elif fvs_clean >= 7:
        return 'VETO', 0.0
    else:
        return 'SKIP', 0.0

def simulate_betting(all_matches):
    """
    Simulate daily betting decisions.
    For each match day:
      1. CORE matches (>=2 available) → build 2串1 core parlay with ¥80
      2. STANDARD matches → singles with ¥20 total
      3. VETO/SKIP → no bet
    Total per day: ¥100
    """
    # Group matches by date
    by_date = defaultdict(list)
    for m in all_matches:
        by_date[m['date']].append(m)
    
    daily_results = []
    total_invested = 0
    total_returned = 0
    total_days = 0
    days_with_bets = 0
    
    matches_with_position = []
    
    for date in sorted(by_date.keys()):
        day_matches = by_date[date]
        day_invested = 0
        day_returned = 0
        
        core_matches = []
        standard_matches = []
        
        for m in day_matches:
            fvs_clean = apply_fvs1a_cleanup(m['fvs'])
            position, multiplier = three_tier_position(fvs_clean, m['drm'])
            
            m['fvs_clean'] = fvs_clean
            m['position'] = position
            m['multiplier'] = multiplier
            
            matches_with_position.append(m)
            
            if position == 'CORE':
                core_matches.append(m)
            elif position == 'STANDARD':
                standard_matches.append(m)
        
        # Build betting plan for this day
        if len(core_matches) >= 2:
            # Build a 2串1 with top 2 core matches
            m1, m2 = core_matches[:2]
            odds1 = float(m.get('fav_odds', 2.0) or 2.0)
            # Simulate: use the favorite's close odds
            # Extract odds from the match data
            m1_fav_odds = float(m1.get('fav_odds', 2.0))
            m2_fav_odds = float(m2.get('fav_odds', 2.0))
            
            # 2串1 with 3.5% slippage per leg
            parlay_odds = m1_fav_odds * m2_fav_odds * (1 - 0.035)**2
            # Core investment: ¥80 for 2串1
            core_invest = 80.0
            
            # Check if parlay wins
            m1_wins = (m1['dir'] == m1['act'])
            m2_wins = (m2['dir'] == m2['act'])
            parlay_wins = m1_wins and m2_wins
            
            if parlay_wins:
                core_return = core_invest * parlay_odds
            else:
                core_return = 0.0
            
            day_invested += core_invest
            day_returned += core_return
            
        elif len(core_matches) == 1:
            # Single bet on the core match + standard singles
            m = core_matches[0]
            fav_odds = float(m.get('fav_odds', 2.0)) * (1 - 0.035)
            single_wins = (m['dir'] == m['act'])
            single_return = 40.0 * fav_odds if single_wins else 0.0
            day_invested += 40.0
            day_returned += single_return
        else:
            # No core matches — skip day or small standard singles
            pass
        
        # Standard match singles (¥20 total if no core, or supplement)
        if standard_matches:
            std_per_match = min(20.0 / max(len(standard_matches), 1), 10.0)
            for sm in standard_matches:
                fav_odds = float(sm.get('fav_odds', 2.0)) * (1 - 0.035)
                single_wins = (sm['dir'] == sm['act'])
                single_return = std_per_match * fav_odds if single_wins else 0.0
                day_invested += std_per_match
                day_returned += single_return
        
        if day_invested > 0:
            days_with_bets += 1
        
        total_days += 1
        total_invested += day_invested
        total_returned += day_returned
        
        daily_results.append({
            'date': date,
            'matches': len(day_matches),
            'core': len(core_matches),
            'standard': len(standard_matches),
            'invested': round(day_invested, 2),
            'returned': round(day_returned, 2),
            'pnl': round(day_returned - day_invested, 2),
        })
    
    return daily_results, matches_with_position, total_invested, total_returned, total_days, days_with_bets

def calculate_ev_simulation(all_matches):
    """
    Calculate simplified EV for each match based on:
    - deVig probability (Pinnacle's "true" probability)
    - Direction accuracy
    - Simulated betting with ¥100 strategy
    """
    results = []
    for m in all_matches:
        fvs_clean = apply_fvs1a_cleanup(m['fvs'])
        position, multiplier = three_tier_position(fvs_clean, m['drm'])
        
        # Get the actual free odds we'd bet at
        fav_odds = float(m.get('fav_odds', 2.0) or 2.0)
        
        results.append({
            'match': m['match'],
            'date': m['date'],
            'score': m['score'],
            'direction': m['dir'],
            'actual': m['act'],
            'correct': m['dir'] == m['act'],
            'fvs': m['fvs'],
            'drm': m['drm'],
            'fvs_clean': fvs_clean,
            'position': position,
            'multiplier': multiplier,
            'fav_odds': fav_odds,
        })
    
    return results

def build_combined_analysis():
    """Build combined analysis from the three tournaments."""
    ct_data = load_data()
    
    all_tournaments = {}
    all_matches_flat = []
    
    raw_paths = {
        "2022 WC": os.path.join(BASE_DIR, ".cache/wc2022_backtest_data.json"),
        "2018 WC": os.path.join(BASE_DIR, ".cache/tournament_data/wc2018_backtest.json"),
        "2024 Euro": os.path.join(BASE_DIR, ".cache/tournament_data/euro2024_backtest.json"),
    }
    
    for tname, tdata in ct_data.items():
        rows = tdata.get('rows', [])
        if not rows:
            continue
        
        # Load raw match data for OCI (if available)
        raw_path = raw_paths.get(tname)
        raw_matches = load_raw_matches(tname, raw_path) if raw_path else None
        raw_map = {}
        if raw_matches:
            for rm in raw_matches:
                key = f"{rm.get('home_team','')} vs {rm.get('away_team','')}"
                raw_map[key] = rm
        
        # Build enhanced match data
        enhanced = []
        for r in rows:
            oci = compute_oci(raw_map.get(r['match'], {}))
            enhanced.append({**r, 'oci': oci})
        
        all_matches_flat.extend(enhanced)
        all_tournaments[tname] = enhanced
    
    return all_tournaments, all_matches_flat

def compute_summary_stats(all_matches, name=""):
    """Compute comprehensive summary stats."""
    total = len(all_matches)
    correct = sum(1 for m in all_matches if m['dir'] == m['act'])
    accuracy = correct / max(total, 1)
    
    # By position
    by_pos = defaultdict(list)
    for m in all_matches:
        by_pos[m.get('position', 'N/A')].append(m)
    
    pos_stats = {}
    for pos, ms in by_pos.items():
        c = sum(1 for m in ms if m['dir'] == m['act'])
        pos_stats[pos] = {
            'count': len(ms),
            'correct': c,
            'accuracy': c / max(len(ms), 1)
        }
    
    # By FVS
    by_fvs = defaultdict(list)
    for m in all_matches:
        by_fvs[m.get('fvs_clean', m['fvs'])].append(m)
    
    fvs_stats = {}
    for fvs_val, ms in sorted(by_fvs.items()):
        c = sum(1 for m in ms if m['dir'] == m['act'])
        fvs_stats[fvs_val] = {
            'count': len(ms),
            'correct': c,
            'accuracy': c / max(len(ms), 1)
        }
    
    # By DRM
    by_drm = defaultdict(list)
    for m in all_matches:
        by_drm[m['drm']].append(m)
    
    drm_stats = {}
    for drm_val, ms in sorted(by_drm.items()):
        c = sum(1 for m in ms if m['dir'] == m['act'])
        drm_stats[drm_val] = {
            'count': len(ms),
            'correct': c,
            'accuracy': c / max(len(ms), 1)
        }
    
    # FVS × DRM matrix
    matrix = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for m in all_matches:
        f = m.get('fvs_clean', m['fvs'])
        d = m['drm']
        matrix[f][d][0] += 1 if m['dir'] == m['act'] else 0
        matrix[f][d][1] += 1
    
    return {
        'total': total,
        'correct': correct,
        'accuracy': accuracy,
        'by_position': pos_stats,
        'by_fvs': fvs_stats,
        'by_drm': drm_stats,
        'fvs_drm_matrix': {str(k): {str(k2): v2 for k2, v2 in v.items()} for k, v in matrix.items()}
    }

def main():
    print("=" * 70)
    print("  v3.5.0 完整回测 — 模拟真实投注决策")
    print("  数据: 2022世界杯 + 2018世界杯 + 2024欧洲杯 (共179场比赛)")
    print("=" * 70)
    
    # Load and analyze
    all_tournaments, all_matches_flat = build_combined_analysis()
    
    # Apply FVS-1A cleanup and position assignment
    for m in all_matches_flat:
        fvs_clean = apply_fvs1a_cleanup(m['fvs'])
        m['fvs_clean'] = fvs_clean
        position, multiplier = three_tier_position(fvs_clean, m['drm'])
        m['position'] = position
        m['multiplier'] = multiplier
    
    # Simulate betting
    daily_results, _, total_invested, total_returned, total_days, days_with_bets = \
        simulate_betting(all_matches_flat)
    
    # Tournament summaries
    tournament_summaries = {}
    for tname, tmatches in all_tournaments.items():
        summary = compute_summary_stats(tmatches, tname)
        # Betting simulation per tournament
        t_daily, _, t_inv, t_ret, t_days, t_bet_days = simulate_betting(tmatches)
        summary['betting'] = {
            'days': t_days,
            'days_with_bets': t_bet_days,
            'invested': round(t_inv, 2),
            'returned': round(t_ret, 2),
            'pnl': round(t_ret - t_inv, 2),
            'roi': round((t_ret - t_inv) / max(t_inv, 1) * 100, 2)
        }
        tournament_summaries[tname] = summary
    
    # Combined summary
    combined = compute_summary_stats(all_matches_flat, "ALL")
    combined['betting'] = {
        'total_days': total_days,
        'days_with_bets': days_with_bets,
        'invested': round(total_invested, 2),
        'returned': round(total_returned, 2),
        'pnl': round(total_returned - total_invested, 2),
        'roi': round((total_returned - total_invested) / max(total_invested, 1) * 100, 2)
    }
    
    # Print summary
    print(f"\n{'─' * 70}")
    print(f"  赛事        总场  旧命中率  新命中率  投资(PnL)    ROI")
    print(f"{'─' * 70}")
    
    for tname in ['2022 WC', '2018 WC', '2024 Euro']:
        if tname not in tournament_summaries:
            continue
        ts = tournament_summaries[tname]
        old_acc = ts.get('accuracy', 0)
        # New accuracy (after position filtering — only matches we bet on)
        bet_positions = ['CORE', 'STANDARD']
        bet_matches = [m for m in all_tournaments.get(tname, []) if m.get('position') in bet_positions]
        new_correct = sum(1 for m in bet_matches if m['dir'] == m['act'])
        new_acc = new_correct / max(len(bet_matches), 1)
        bt = ts.get('betting', {})
        pnl = bt.get('pnl', 0)
        roi = bt.get('roi', 0)
        print(f"  {tname:<12} {ts['total']:>4}  {old_acc:>7.1%}  {new_acc:>7.1%}  "
              f"{'¥'+str(pnl):>10}  {roi:>+6.1f}%")
    
    cb = combined
    bt = cb['betting']
    print(f"{'─' * 70}")
    print(f"  {'合计':<12} {cb['total']:>4}  {cb['accuracy']:>7.1%}  "
          f"{'—':>9}  {'¥'+str(bt['pnl']):>10}  {bt['roi']:>+6.1f}%")
    print(f"{'─' * 70}")
    
    # Position breakdown
    print(f"\n{'─' * 70}")
    print("  仓位分配分析 (按"+"所有赛事合计):")
    print(f"{'─' * 70}")
    for pos in ['CORE', 'STANDARD', 'SKIP', 'VETO']:
        if pos in combined['by_position']:
            ps = combined['by_position'][pos]
            print(f"  {pos:<10}: {ps['count']:>4}场, 命中 {ps['correct']:>3}/{ps['count']:>3} = {ps['accuracy']:.0%}")
    
    # Save results
    results = {
        "version": "v3.5.0",
        "generated": "2026-06-23",
        "tournaments": tournament_summaries,
        "combined": combined,
        "daily_results": daily_results,
        "matches": [{
            'match': m['match'],
            'date': m['date'],
            'score': m['score'],
            'dir': m['dir'],
            'act': m['act'],
            'correct': m['dir'] == m['act'],
            'fvs': m['fvs'],
            'drm': m['drm'],
            'fvs_clean': m['fvs_clean'],
            'position': m['position'],
        } for m in all_matches_flat]
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n→ Results saved to {OUTPUT_FILE}")
    
    return results, all_matches_flat, daily_results

if __name__ == '__main__':
    results, all_matches, daily = main()
