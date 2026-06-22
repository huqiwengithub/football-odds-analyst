#!/usr/bin/env python3
"""
v3.3.0 Backtest v2: FVS/DRM as primary filters, EV as info only.
Tests: can FVS predict when favorites will lose?
"""

import json
from collections import defaultdict

PINNACLE_CID = 1055

def load():
    with open('.cache/wc2022_backtest_data.json') as f:
        return json.load(f)

def pinn_odds(m):
    for b in m['ouzhi']['bookmakers']:
        if b['cid'] == PINNACLE_CID:
            return b
    return None

def avg_odds(m):
    h=d=a=0
    n=len(m['ouzhi']['bookmakers'])
    for b in m['ouzhi']['bookmakers']:
        h+=b['closing_home']; d+=b['closing_draw']; a+=b['closing_away']
    return h/n, d/n, a/n

def de_vig(h,d,a):
    ih,id_,ia=1/h,1/d,1/a
    t=ih+id_+ia
    return ih/t, id_/t, ia/t, t-1

def fav_dir(h,d,a):
    if h<d and h<a: return 'home',h
    if a<h and a<d: return 'away',a
    return 'draw',min(h,d,a)

def fvs_drm(m, matches, ph, pd, pa, fav_odds, pinn):
    fvs_s, fvs_t = 0, []
    drm_s, drm_t = 0, []

    # FVS-1
    if fav_odds < 1.18: fvs_s+=2; fvs_t.append('FVS1+2')
    elif fav_odds < 1.25: fvs_s+=1; fvs_t.append('FVS1+1')

    # FVS-2 systemic
    same = [x for x in matches if x['date']==m['date']]
    all_low = all(min(avg_odds(x)) <= 1.50 for x in same)
    if all_low: fvs_s+=2; fvs_t.append('FVS2+2')

    # FVS-3 mid-odds cluster
    mid_n = sum(1 for x in same if 1.20 <= min(avg_odds(x)) <= 1.50)
    if mid_n>=2: fvs_s+=1; fvs_t.append('FVS3+1')

    # FVS-4: 0-trap check (simplified - looking at odds spread)
    o_spread = max(ph,pd,pa) - min(ph,pd,pa)
    if fav_odds < 1.50 and o_spread > 0.55:  # big favorite, big spread = little divergence
        fvs_s += 0  # This is the "clean" case O-6 warned about

    # FVS-6: AH deep deviation
    ah = m.get('yazhi',{}).get('pinnacle_ah',{})
    if ah:
        try:
            hw = float(ah.get('home_water',1.0))
            aw = float(ah.get('away_water',1.0))
            if fav_odds < 1.30 and hw > 1.0:
                fvs_s+=1; fvs_t.append('FVS6+1')
        except (ValueError, TypeError):
            pass  # garbled handicap data

    # FVS-7 draw prob
    if pd > 0.25 and fav_odds < 1.80:
        fvs_s+=1; fvs_t.append('FVS7+1')

    # FVS-11 late reversal
    if pinn:
        o_h, c_h = pinn.get('opening_home',0), pinn['closing_home']
        o_a, c_a = pinn.get('opening_away',0), pinn['closing_away']
        if o_h and fav_odds < 1.50 and c_h > o_h * 1.02:
            fvs_s+=2; fvs_t.append('FVS11+2')

    # DRM-1
    if pd > 0.28: drm_s+=2; drm_t.append('DRM1+2')
    elif pd > 0.25: drm_s+=1; drm_t.append('DRM1+1')

    # DRM-7: KO
    if m.get('stage') in ('round16','quarter','semi','final'):
        drm_s+=2; drm_t.append('DRM7+2')

    return fvs_s, fvs_t, drm_s, drm_t

def verdict(fvs, drm):
    if fvs>=6: return '🚫MELT'
    if fvs>=4 or (fvs>=2 and drm>=4): return '🔴HIGH'
    if fvs>=2 or drm>=4: return '⚠️WARN'
    if drm>=2: return '🔶DRAW'
    return '✅OK'

def run():
    data = load()
    ms = data['matches']

    r = {'old_ok':0,'old_bad':0, 'new_veto_ok':0,'new_veto_bad':0,'new_pass_ok':0,'new_pass_bad':0,
         'by_stage':defaultdict(lambda:[0,0,0,0,0,0])}  # [old_ok,old_bad,veto_ok,veto_bad,pass_ok,pass_bad]
    rows = []

    for m in ms:
        p = pinn_odds(m)
        if not p: continue
        ah,ad,aa = avg_odds(m)
        ph,pd,pa,ov = de_vig(p['closing_home'],p['closing_draw'],p['closing_away'])
        d, fav_odds = fav_dir(ah,ad,aa)
        act = m['result']
        fvs,ft,drm,dt = fvs_drm(m, ms, ph, pd, pa, fav_odds, p)
        v = verdict(fvs, drm)

        old_right = (d == act)
        vetoed = fvs >= 4 or (fvs >= 2 and drm >= 4)

        st = m.get('stage','?')
        if old_right: r['old_ok']+=1; r['by_stage'][st][0]+=1
        else: r['old_bad']+=1; r['by_stage'][st][1]+=1

        if vetoed:
            if not old_right: r['new_veto_bad']+=1; r['by_stage'][st][3]+=1
            else: r['new_veto_ok']+=1; r['by_stage'][st][2]+=1
        else:
            if old_right: r['new_pass_ok']+=1; r['by_stage'][st][4]+=1
            else: r['new_pass_bad']+=1; r['by_stage'][st][5]+=1

        ev_71 = ph * fav_odds * 0.71 - 1
        rows.append({
            'match': f"{m['home_team']} vs {m['away_team']}",
            'date':m['date'],'stage':st,'score':f"{m['home_score']}-{m['away_score']}",
            'dir':d,'act':act,'fvs':fvs,'drm':drm,
            'fvs_t':','.join(ft) if ft else '-',
            'drm_t':','.join(dt) if dt else '-',
            'verdict':v,'vetoed':vetoed,
            'old':old_right,
            'ev':f"{ev_71:.1%}",
            'fav_odds':f"{fav_odds:.2f}"
        })

    # Print report
    tot = r['old_ok']+r['old_bad']
    old_acc = r['old_ok']/tot
    veto_t = r['new_veto_ok']+r['new_veto_bad']
    pass_t = r['new_pass_ok']+r['new_pass_bad']
    new_acc = r['new_pass_ok']/pass_t if pass_t else 0

    print("="*90)
    print("2022 WORLD CUP BACKTEST: FVS/DRM AS PREDICTORS OF FAVORITE FAILURE")
    print("="*90)
    print(f"\n{'':>22} {'v3.1.2(OLD)':>12} {'v3.3.0(NEW)':>12}")
    print(f"{'Total matches':>22} {tot:>12} {tot:>12}")
    print(f"{'Old system correct':>22} {r['old_ok']:>12} {'-':>12}")
    print(f"{'Old system WRONG':>22} {r['old_bad']:>12} {'-':>12}")
    print(f"{'FVS/DRM VETOED':>22} {'-':>12} {veto_t:>12}")
    print(f"{'  Veto saved (was wrong)':>22} {'-':>12} {r['new_veto_bad']:>12}")
    print(f"{'  Veto cost (was right)':>22} {'-':>12} {r['new_veto_ok']:>12}")
    print(f"{'Passed (no veto)':>22} {'-':>12} {pass_t:>12}")
    print(f"{'  Pass+Correct':>22} {'-':>12} {r['new_pass_ok']:>12}")
    print(f"{'  Pass+Wrong':>22} {'-':>12} {r['new_pass_bad']:>12}")
    print(f"{'---':>22} {'---':>12} {'---':>12}")
    print(f"{'HIT RATE':>22} {old_acc:>11.1%} {new_acc:>11.1%}")
    
    if veto_t > 0:
        precision = r['new_veto_bad']/veto_t
        recall = r['new_veto_bad']/max(r['old_bad'],1)
        print(f"{'FVS veto PRECISION':>22} {'-':>12} {precision:>11.1%}")
        print(f"{'FVS veto RECALL':>22} {'-':>12} {recall:>11.1%}")

    print(f"\n{'─'*90}")
    print("BY FVS/DRM TIER:")
    tiers = defaultdict(lambda:[0,0])  # [right, wrong]
    for row in rows:
        if not row['vetoed']:
            tiers[row['verdict']][0] += 1 if row['old'] else 0
            tiers[row['verdict']][1] += 0 if row['old'] else 1
    
    for tier in ['✅OK','🔶DRAW','⚠️WARN']:
        t = tiers[tier]
        tot_t = t[0]+t[1]
        if tot_t:
            print(f"  {tier}: {t[0]}/{tot_t} = {t[0]/tot_t:.0%}")

    print(f"\n{'─'*90}")
    print("FVS VETO SAVED (OLD WRONG, NEW VETOED):")
    saved = [x for x in rows if x['vetoed'] and not x['old']]
    for x in saved:
        print(f"  {x['date']} {x['match'][:35]:<35} {x['dir']}→{x['act']}({x['score']}) FVS:{x['fvs']} DRM:{x['drm']} [{x['fvs_t']}|{x['drm_t']}]")

    print(f"\n{'─'*90}")
    print("FVS VETO COST (OLD RIGHT, NEW VETOED):")
    cost = [x for x in rows if x['vetoed'] and x['old']]
    for x in cost:
        print(f"  {x['date']} {x['match'][:35]:<35} {x['dir']}→{x['act']}({x['score']}) FVS:{x['fvs']} DRM:{x['drm']} [{x['fvs_t']}|{x['drm_t']}]")

    print(f"\n{'─'*90}")
    print("PASSED BUT WRONG (NEW SYSTEM FAILURES):")
    missed = [x for x in rows if not x['vetoed'] and not x['old']]
    for x in missed:
        print(f"  {x['date']} {x['match'][:35]:<35} {x['dir']}→{x['act']}({x['score']}) FVS:{x['fvs']} DRM:{x['drm']} [{x['fvs_t']}|{x['drm_t']}]")

    print(f"\n{'='*90}")
    print("MATCH-BY-MATCH:")
    print(f"{'Match':<32} {'Scr':>4} {'Dir':>5} {'Old':>4} {'New':>4} {'FVS':>3} {'DRM':>3} {'Verdict':>8}")
    print(f"{'─'*90}")
    for x in rows:
        om = '✅' if x['old'] else '❌'
        if x['vetoed']:
            nm = '🛑' if not x['old'] else '⛔'
        else:
            nm = om
        print(f"{x['match'][:31]:<32} {x['score']:>4} {x['dir']:>5} {om:>4} {nm:>4} {x['fvs']:>3} {x['drm']:>3} {x['verdict']:>8}")

    # By stage
    print(f"\n{'='*90}")
    print("BY STAGE:")
    for st in ['group','round16','quarter','semi','final','third']:
        if st in r['by_stage']:
            s = r['by_stage'][st]
            tot_s = s[0]+s[1]
            print(f"  {st:>8}: {tot_s:>2}g | OLD:{s[0]/tot_s:.0%} | VETO_OK:{s[2]} VETO_BAD:{s[3]} PASS_OK:{s[4]} PASS_BAD:{s[5]}")

    with open('backtest_v330_v2.json','w') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"\n→ backtest_v330_v2.json")

if __name__ == '__main__':
    run()
