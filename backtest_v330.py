#!/usr/bin/env python3
"""
2022 World Cup 64-match backtest: v3.3.0 vs v3.1.2
Tests FVS, DRM, and 竞彩EV modules against historical data.
"""

import json
import math
from collections import defaultdict

# ─── Constants ───
PINNACLE_CID = 1055
LOTTERY_RETURN_RATE = 0.71  # 竞彩串关返奖率
LOGIT_CAP = 1.20  # 总量cap

def load_data(path=".cache/wc2022_backtest_data.json"):
    with open(path) as f:
        return json.load(f)


def get_pinnacle_odds(match):
    """Extract Pinnacle closing and opening SPF odds."""
    for bm in match['ouzhi']['bookmakers']:
        if bm['cid'] == PINNACLE_CID:
            return {
                'close_h': bm['closing_home'],
                'close_d': bm['closing_draw'],
                'close_a': bm['closing_away'],
                'open_h': bm.get('opening_home', bm['closing_home']),
                'open_d': bm.get('opening_draw', bm['closing_draw']),
                'open_a': bm.get('opening_away', bm['closing_away']),
            }
    return None


def get_avg_odds(match):
    """Compute average SPF odds across all bookmakers."""
    h, d, a = [], [], []
    for bm in match['ouzhi']['bookmakers']:
        h.append(bm['closing_home'])
        d.append(bm['closing_draw'])
        a.append(bm['closing_away'])
    return {
        'avg_h': sum(h)/len(h),
        'avg_d': sum(d)/len(d),
        'avg_a': sum(a)/len(a),
    }


def shin_de_vig(o_h, o_d, o_a):
    """Simple proportional de-vig (Shin approximation)."""
    imp_h = 1.0 / o_h
    imp_d = 1.0 / o_d
    imp_a = 1.0 / o_a
    total = imp_h + imp_d + imp_a
    overround = total - 1.0
    # Proportional removal
    p_h = imp_h / total
    p_d = imp_d / total
    p_a = imp_a / total
    return p_h, p_d, p_a, overround


def compute_fvs(match, all_matches, pinn_odds, avg_odds, de_vig):
    """Compute FVS score for a match."""
    p_h, p_d, p_a, _ = de_vig
    fav_odds = min(avg_odds['avg_h'], avg_odds['avg_d'], avg_odds['avg_a'])
    score = 0
    triggers = []
    details = {}

    # ── FVS-1: Ultra-low odds ──
    if fav_odds < 1.18:
        triggers.append('FVS-1(+2)')
        score += 2
    elif fav_odds < 1.25:
        triggers.append('FVS-1(+1)')
        score += 1

    # ── FVS-2: All-low-odds day (systemic) ──
    same_day = [m for m in all_matches if m['date'] == match['date']]
    all_low = True
    for m in same_day:
        m_avg = get_avg_odds(m)
        m_fav = min(m_avg['avg_h'], m_avg['avg_d'], m_avg['avg_a'])
        if m_fav > 1.50:
            all_low = False
            break
    details['FVS-2_systemic'] = all_low
    if all_low:
        triggers.append('FVS-2(+2系统)')
        score += 2

    # ── FVS-3: Same-day mid-odds cluster ──
    mid_count = sum(
        1 for m in same_day
        if 1.20 <= min(get_avg_odds(m)['avg_h'], get_avg_odds(m)['avg_d'], get_avg_odds(m)['avg_a']) <= 1.50
    )
    details['FVS-3_mid_count'] = mid_count
    if mid_count >= 2:
        triggers.append('FVS-3(+1)')
        score += 1

    # ── FVS-6: AH deep deviation ──
    ah_data = match.get('yazhi', {}).get('pinnacle_ah', {})
    if ah_data:
        # Estimate theoretical AH from deVig probability
        theoretical_ah = estimate_ah_from_prob(p_h)
        # Try to parse actual AH (may be garbled)
        handicap_str = ah_data.get('handicap', '')
        actual_ah = parse_ah_handicap(handicap_str)
        if actual_ah is not None:
            deviation = abs(actual_ah - theoretical_ah)
            details['FVS-6_theoretical_ah'] = round(theoretical_ah, 2)
            details['FVS-6_actual_ah'] = actual_ah
            details['FVS-6_deviation'] = round(deviation, 2)
            if deviation >= 0.50:
                triggers.append('FVS-6(+1)')
                score += 1

    # ── FVS-7: Elevated draw probability ──
    if p_d > 0.25 and fav_odds < 1.80:
        triggers.append('FVS-7(+1)')
        score += 1

    # ── FVS-11: Late line reversal ──
    if pinn_odds:
        h_change = (pinn_odds['close_h'] - pinn_odds['open_h']) / pinn_odds['open_h']
        if fav_odds < 1.50 and h_change > 0.02:  # Favorite odds rising >2%
            triggers.append('FVS-11(+2)')
            score += 2

    return score, triggers, details


def compute_drm(match, de_vig, avg_odds):
    """Compute DRM score."""
    p_h, p_d, p_a, _ = de_vig
    score = 0
    triggers = []

    # ── DRM-1: Odds structure favoring draw ──
    if p_d > 0.28:
        triggers.append('DRM-1(+2)')
        score += 2
    elif p_d > 0.25:
        triggers.append('DRM-1(+1)')
        score += 1
    if 1.0 / avg_odds['avg_h'] / (1.0 / avg_odds['avg_a']) < 1.5:
        pass  # Balanced match bonus - can add later

    # ── DRM-7: Knockout stage ──
    if match.get('stage') in ('round16', 'quarter', 'semi', 'final'):
        triggers.append('DRM-7(+2)')
        score += 2

    return score, triggers


def estimate_ah_from_prob(home_prob):
    """Estimate AH handicap from home win probability."""
    diff = home_prob - 0.50
    if diff <= 0.02: return 0       # 平手
    if diff <= 0.08: return 0.25    # 平手/半球
    if diff <= 0.14: return 0.5     # 半球
    if diff <= 0.20: return 0.75    # 半球/一球
    if diff <= 0.27: return 1.0     # 一球
    if diff <= 0.33: return 1.25    # 一球/球半
    if diff <= 0.38: return 1.5     # 球半
    if diff <= 0.42: return 1.75    # 球半/两球
    if diff <= 0.47: return 2.0     # 两球
    return 2.5


def parse_ah_handicap(handicap_str):
    """Try to parse garbled AH handicap string."""
    if not handicap_str:
        return None
    # Common patterns in the garbled data
    # The handicap is likely the numeric part followed by Chinese characters
    import re
    # Try to find a number pattern like "0.880" or "0.940" etc
    # These appear to be water level, not handicap
    # Let's try matching known handicap patterns
    for pattern, value in [
        (r'平手', 0), (r'平半', 0.25), (r'半球', 0.5),
        (r'半一', 0.75), (r'一球', 1.0), (r'一球球半', 1.25),
        (r'球半', 1.5), (r'球半两球', 1.75), (r'两球', 2.0),
        (r'受平手', 0), (r'受平半', -0.25), (r'受半球', -0.5),
        (r'受半一', -0.75), (r'受一球', -1.0),
    ]:
        if pattern in handicap_str:
            return value
    return None


def compute_lottery_ev(de_vig, fav_direction, fav_odds):
    """Compute 竞彩 EV."""
    p_fav = de_vig[0] if fav_direction == 'home' else de_vig[2] if fav_direction == 'away' else de_vig[1]
    ev = p_fav * fav_odds * LOTTERY_RETURN_RATE - 1
    return ev


def determine_direction(pinn_odds):
    """Simple market direction from Pinnacle closing odds."""
    h, d, a = pinn_odds['close_h'], pinn_odds['close_d'], pinn_odds['close_a']
    if h < d and h < a:
        return 'home'
    elif a < h and a < d:
        return 'away'
    else:
        return 'draw'


def backtest():
    data = load_data()
    matches = data['matches']

    results_old = {'correct': 0, 'wrong': 0, 'total': 0, 'vetoed': 0}
    results_new = {'correct': 0, 'wrong': 0, 'total': 0, 'vetoed': 0,
                   'fvs_saved': 0, 'drm_saved': 0, 'ev_saved': 0}
    details = []

    for match in matches:
        pinn = get_pinnacle_odds(match)
        if not pinn:
            continue

        avg = get_avg_odds(match)
        de_vig = shin_de_vig(pinn['close_h'], pinn['close_d'], pinn['close_a'])
        p_h, p_d, p_a, overround = de_vig

        direction = determine_direction(pinn)
        actual = match['result']
        fav_odds = min(avg['avg_h'], avg['avg_d'], avg['avg_a'])

        # ─── Old system (v3.1.2): market direction ───
        results_old['total'] += 1
        old_correct = (direction == actual)
        if old_correct:
            results_old['correct'] += 1
        else:
            results_old['wrong'] += 1

        # ─── New system (v3.3.0) ───
        fvs_score, fvs_triggers, fvs_details = compute_fvs(match, matches, pinn, avg, de_vig)
        drm_score, drm_triggers = compute_drm(match, de_vig, avg)
        lottery_ev = compute_lottery_ev(de_vig, direction, fav_odds)

        # FVS×DRM matrix
        fvs_drm_verdict = '正常'
        if fvs_score >= 6:
            fvs_drm_verdict = '🚫熔断'
        elif fvs_score >= 4:
            fvs_drm_verdict = '🔴严重'
        elif fvs_score >= 2:
            fvs_drm_verdict = '⚠️衰减'
        elif drm_score >= 4:
            fvs_drm_verdict = '🔶高平局'
        elif drm_score >= 2:
            fvs_drm_verdict = '⚠️中平局'

        # Veto logic
        vetoed = False
        veto_reason = []
        if fvs_score >= 4:  # FVS 严重
            vetoed = True
            veto_reason.append(f'FVS-{fvs_score}')
        if lottery_ev < -0.15:  # 严重负EV
            vetoed = True
            veto_reason.append(f'EV-{abs(lottery_ev):.0%}')
        if fvs_score >= 2 and drm_score >= 2:  # 双重警告
            vetoed = True
            veto_reason.append('FVS+DRM双重')

        results_new['total'] += 1
        if vetoed:
            results_new['vetoed'] += 1
            if result_is_right(match, direction):
                # Old system would have picked correctly but we vetoed
                pass  # It was right, veto cost us
            else:
                # Old system would have been wrong and we avoided it!
                results_new['fvs_saved'] += 1
        else:
            new_correct = (direction == actual)
            if new_correct:
                results_new['correct'] += 1
            else:
                results_new['wrong'] += 1

        details.append({
            'match': f"{match['home_team']} vs {match['away_team']}",
            'date': match['date'],
            'stage': match.get('stage', '?'),
            'score': f"{match['home_score']}-{match['away_score']}",
            'direction': direction,
            'actual': actual,
            'pinnacle_close': f"{pinn['close_h']:.2f}/{pinn['close_d']:.2f}/{pinn['close_a']:.2f}",
            'deVig': f"{p_h:.1%}/{p_d:.1%}/{p_a:.1%}",
            'fav_odds': f"{fav_odds:.2f}",
            'fvs_score': fvs_score,
            'fvs_triggers': ','.join(fvs_triggers) if fvs_triggers else '-',
            'drm_score': drm_score,
            'drm_triggers': ','.join(drm_triggers) if drm_triggers else '-',
            'lottery_ev': f"{lottery_ev:.1%}",
            'fvs_drm_verdict': fvs_drm_verdict,
            'vetoed': vetoed,
            'veto_reason': ','.join(veto_reason) if veto_reason else '-',
            'old_correct': old_correct,
            'new_correct': (not vetoed and old_correct),
        })

    return results_old, results_new, details


def result_is_right(match, direction):
    return direction == match['result']


def print_report(results_old, results_new, details):
    print("=" * 80)
    print("2022 WORLD CUP 64-MATCH BACKTEST: v3.3.0 vs v3.1.2")
    print("=" * 80)

    # Overall stats
    old_acc = results_old['correct'] / max(results_old['total'], 1)
    new_total = results_new['total'] - results_new['vetoed']
    new_correct = results_new['correct']
    new_acc = new_correct / max(new_total, 1) if new_total > 0 else 0

    print(f"\n{'':>20} {'v3.1.2 (旧)':>12} {'v3.3.0 (新)':>12}")
    print(f"{'总场次':>20} {results_old['total']:>12} {results_new['total']:>12}")
    print(f"{'预测正确':>20} {results_old['correct']:>12} {results_new['correct']:>12}")
    print(f"{'预测错误':>20} {results_old['wrong']:>12} {results_new['wrong']:>12}")
    print(f"{'被否决(不投)':>20} {'-':>12} {results_new['vetoed']:>12}")
    print(f"{'---':>20} {'---':>12} {'---':>12}")
    print(f"{'命中率':>20} {old_acc:>11.1%} {new_acc:>11.1%}")
    print(f"{'回避的冷门':>20} {'-':>12} {results_new['fvs_saved']:>12}")

    # By stage
    print("\n" + "-" * 80)
    print("BY STAGE:")
    stages = defaultdict(lambda: {'old_c':0, 'old_w':0, 'new_c':0, 'new_w':0, 'veto':0, 'saved':0})
    for d in details:
        s = d['stage']
        stages[s]['old_c'] += 1 if d['old_correct'] else 0
        stages[s]['old_w'] += 0 if d['old_correct'] else 1
        if d['vetoed']:
            stages[s]['veto'] += 1
            if not d['old_correct']:
                stages[s]['saved'] += 1
        else:
            stages[s]['new_c'] += 1 if d['old_correct'] else 0
            stages[s]['new_w'] += 0 if d['old_correct'] else 1

    for stage in ['group', 'round16', 'quarter', 'semi', 'final', 'third']:
        if stage in stages:
            s = stages[stage]
            total = s['old_c'] + s['old_w']
            old_a = s['old_c'] / total
            new_total = s['new_c'] + s['new_w']
            new_a = s['new_c'] / max(new_total, 1)
            print(f"  {stage:>8}: {total:>2}场 | 旧: {old_a:.0%} | 新: {new_a:.0%} | 否决: {s['veto']} | 规避冷门: {s['saved']}")

    # FVS saved matches
    print("\n" + "-" * 80)
    print("FVS/DRM/EV SAVED (OLD WRONG, NEW VETOED):")
    saved = [d for d in details if d['vetoed'] and not d['old_correct']]
    for d in saved[:20]:
        print(f"  {d['date']} {d['match']} | {d['direction']}→{d['actual']}({d['score']}) | "
              f"FVSm:{d['fvs_score']} DRM:{d['drm_score']} EV:{d['lottery_ev']} | "
              f"[{d['veto_reason']}]")

    # Missed opportunities (vetoed correctly)
    print("\n" + "-" * 80)
    print("VETOED BUT WOULD HAVE BEEN RIGHT:")
    missed = [d for d in details if d['vetoed'] and d['old_correct']]
    for d in missed[:10]:
        print(f"  {d['date']} {d['match']} | {d['direction']}→{d['actual']}({d['score']}) | "
              f"FVSm:{d['fvs_score']} DRM:{d['drm_score']} EV:{d['lottery_ev']}")

    # Full detail table
    print("\n" + "=" * 80)
    print("FULL RESULTS:")
    print(f"{'Match':<30} {'Res':>4} {'Dir':>5} {'Old':>4} {'New':>4} {'FVS':>3} {'DRM':>3} {'EV':>6} {'Verdict':>8}")
    print("-" * 80)
    for d in details:
        old_mark = '✅' if d['old_correct'] else '❌'
        if d['vetoed']:
            new_mark = '🛑' if not d['old_correct'] else '⛔'
        else:
            new_mark = old_mark
        print(f"{d['match'][:29]:<30} {d['score']:>4} {d['direction']:>5} {old_mark:>4} {new_mark:>4} "
              f"{d['fvs_score']:>3} {d['drm_score']:>3} {d['lottery_ev']:>6} {d['fvs_drm_verdict']:>8}")

    # Save to JSON
    with open('backtest_v330_results.json', 'w') as f:
        json.dump(details, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to backtest_v330_results.json")


if __name__ == '__main__':
    r_old, r_new, det = backtest()
    print_report(r_old, r_new, det)
