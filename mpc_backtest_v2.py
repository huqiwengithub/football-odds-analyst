"""MPC backtest v2 — corrected CID mapping from KB-14.6"""
import json

with open('/Users/tracy/Desktop/足彩/.cache/wc2022_backtest_data.json') as f:
    data = json.load(f)
matches = data['matches']

TIER = {
    1055: 'S', 3: 'S', 9: 'S', 11: 'S', 14: 'S', 2: 'S',
    293: 'S', 4: 'S', 6: 'S', 1487: 'S', 18: 'S', 13: 'S', 15: 'S',
    5: 'A', 280: 'A', 127: 'A', 122: 'A', 502: 'A', 12: 'A', 348: 'A', 103: 'A', 1250: 'A',
    1: 'R', 16: 'R', 291: 'R', 275: 'R', 140: 'R', 651: 'R',
    1259: 'R', 132: 'R', 413: 'R', 8: 'R', 66: 'R', 67: 'R',
    863: 'R', 1354: 'R', 142: 'R', 734: 'R', 1001: 'R', 422: 'R', 177: 'R',
}
SHARP = {c for c,t in TIER.items() if t == 'S'}
ASIAN = {c for c,t in TIER.items() if t == 'A'}
RETAIL = {c for c,t in TIER.items() if t == 'R'}

def tier_direction(bms, tier_set):
    """Return (favored_outcome, confidence) for a tier group."""
    avg = {"home":0,"draw":0,"away":0}
    cnt = 0
    for bm in bms:
        if bm['cid'] not in tier_set or bm['cid'] == 1055:
            continue
        for o in avg:
            avg[o] += (bm[f'closing_{o}'] - bm[f'opening_{o}']) / bm[f'opening_{o}']
        cnt += 1
    if not cnt:
        return None, 0
    for k in avg: avg[k] /= cnt
    fav = min(avg, key=avg.get)
    return fav, abs(avg[fav])

def result(m):
    h, a = m['home_score'], m['away_score']
    return "home" if h > a else ("away" if a > h else "draw")

results = []
for m in matches:
    bms = m['ouzhi']['bookmakers']
    p = m['ouzhi']['pinnacle']
    
    # PVD: Pinnacle movement direction vs market average
    pd_h = (p['closing_home'] - p['opening_home']) / p['opening_home']
    pd_d = (p['closing_draw'] - p['opening_draw']) / p['opening_draw']
    pd_a = (p['closing_away'] - p['opening_away']) / p['opening_away']
    pinn_deltas = {"home": pd_h, "draw": pd_d, "away": pd_a}
    pinn_fav = min(pinn_deltas, key=pinn_deltas.get)
    pinn_pct = abs(pinn_deltas[pinn_fav]) * 100
    
    # Market avg direction
    mkt = {"home":0,"draw":0,"away":0}
    cnt = 0
    for bm in bms:
        if bm['cid'] == 1055: continue
        for o in mkt: mkt[o] += (bm[f'closing_{o}'] - bm[f'opening_{o}']) / bm[f'opening_{o}']
        cnt += 1
    for k in mkt: mkt[k] /= cnt
    mkt_fav = min(mkt, key=mkt.get)
    mkt_pct = abs(mkt[mkt_fav]) * 100
    div = abs(pinn_pct - mkt_pct)
    
    if pinn_pct < 0.5: pvd = 0.0
    elif pinn_pct >= 2 and div < 1: pvd = 1.0
    elif pinn_pct >= 2: pvd = -0.5
    elif pinn_pct >= 1: pvd = 0.5
    else: pvd = 0.0
    
    # CD: Sharp direction vs market-wide direction
    sharp_dir, _ = tier_direction(bms, SHARP)
    asian_dir, _ = tier_direction(bms, ASIAN)
    retail_dir, _ = tier_direction(bms, RETAIL)
    
    if not sharp_dir:
        cd = 0.0
    else:
        # Mass direction checking
        popular_dirs = [d for d in [asian_dir, retail_dir] if d]
        if len(popular_dirs) >= 2 and popular_dirs[0] == popular_dirs[1] and popular_dirs[0] != sharp_dir:
            cd = 1.0  # Channel divergence
        elif len(popular_dirs) >= 1 and popular_dirs[0] == sharp_dir:
            cd = 0.5  # Leading follow
        else:
            cd = 0.0  # Mixed signals
    
    mpc = 0.6 * pvd + 0.4 * cd
    
    if abs(mpc) < 0.2:
        status = "NORMAL"
    elif mpc < -0.8:
        status = "BREAKER"
    elif mpc < -0.5:
        status = "VETO"
    else:
        status = "NORMAL"
    
    res = result(m)
    hp, dp, ap = 1/p['closing_home'], 1/p['closing_draw'], 1/p['closing_away']
    t = hp + dp + ap
    pred = max({"home": hp/t, "draw": dp/t, "away": ap/t}, key=lambda k: {"home": hp/t, "draw": dp/t, "away": ap/t}[k])
    
    results.append({
        "home": m['home_team'], "away": m['away_team'],
        "result": res, "pred": pred, "correct": pred == res,
        "pvd": round(pvd,2), "cd": round(cd,2), "mpc": round(mpc,2),
        "status": status, "score": f"{m['home_score']}-{m['away_score']}"
    })

total = len(results)
base_acc = sum(1 for r in results if r["correct"]) / total
affected = [r for r in results if r["mpc"] >= 0.2 or r["mpc"] <= -0.5]
aff_acc = sum(1 for r in affected if r["correct"]) / len(affected) if affected else 0
vetoed = [r for r in results if r["status"] in ("VETO","BREAKER")]
veto_acc = sum(1 for r in vetoed if not r["correct"]) / len(vetoed) if vetoed else 0

print(f"=== MPC Backtest v2 (KB-14.6 CID Mapping) ===")
print(f"Total: {total}")
print(f"Baseline accuracy: {base_acc:.1%}")
print(f"MPC affected: {len(affected)}, acc: {aff_acc:.1%}, gain: {aff_acc-base_acc:+.1%}")
print(f"Veto/Breaker: {len(vetoed)}, correct rejection: {veto_acc:.1%}")
print()
for r in vetoed:
    m = "✅" if not r["correct"] else "❌"
    print(f"  {m} {r['home']} vs {r['away']} ({r['score']}) MPC={r['mpc']} ({r['status']}) pred={r['pred']} act={r['result']}")
