"""
wc2022_mpc_backtest.py
Backtest MPC (Market Pressure Composite) on 2022 World Cup data.
Tests PVD (price-volume divergence) and CD (channel divergence)
using opening-to-closing odds changes across 30 bookmakers.
"""
import json, math, sys
from pathlib import Path

DATA = Path("/Users/tracy/Desktop/足彩/.cache/wc2022_backtest_data.json")
REPORT = Path("/Users/tracy/Desktop/足彩/reports/wc2022_mpc_backtest.html")

# Tier classification from 500.com CIDs (confirmed + inferred)
SHARP_CIDS = {1055, 1, 3, 4, 9, 13, 16, 280, 291}  # Pinnacle, bet365, WH, Ladbrokes, BetVictor, Interwetten, etc
ASIAN_CIDS = {2, 5, 6, 11, 12, 293}  # 澳门, 皇冠, 12bet, 188bet, 易胜博
RETAIL_CIDS = {8, 10, 14, 18, 66, 67, 122, 140, 142, 275, 348, 502, 651, 863, 1259, 1354}

def load_data():
    with open(DATA) as f:
        raw = json.load(f)
    return raw["matches"]

def compute_pvd(match):
    """Compute PVD score using Pinnacle movement vs market consensus."""
    oz = match["ouzhi"]
    pinn = oz["pinnacle"]
    avg_close = oz["avg_closing"]
    
    # Pinnacle odds movement (favored direction)
    pinn_delta_h = (pinn["closing_home"] - pinn["opening_home"]) / pinn["opening_home"]
    pinn_delta_d = (pinn["closing_draw"] - pinn["opening_draw"]) / pinn["opening_draw"]
    pinn_delta_a = (pinn["closing_away"] - pinn["opening_away"]) / pinn["opening_away"]
    
    # Market average movement
    avg_delta_h = (avg_close["home"] - pinn["opening_home"]) / pinn["opening_home"]
    avg_delta_d = (avg_close["draw"] - pinn["opening_draw"]) / pinn["opening_draw"]
    avg_delta_a = (avg_close["away"] - pinn["opening_away"]) / pinn["opening_away"]
    
    # Which direction does Pinnacle favor? (largest negative delta = odds shortening = favorite)
    deltas_pinn = {"home": pinn_delta_h, "draw": pinn_delta_d, "away": pinn_delta_a}
    deltas_avg = {"home": avg_delta_h, "draw": avg_delta_d, "away": avg_delta_a}
    
    pinn_favored = min(deltas_pinn, key=deltas_pinn.get)  # direction Pinnacle pushed
    pinn_pct = deltas_pinn[pinn_favored]
    avg_pct = deltas_avg[pinn_favored]
    
    # If we have touzhu/betfair data, use it. Otherwise, use avg_mkt vs Pinnacle divergence
    # PVD: Pinnacle moves but avg mkt doesn't follow = divergence
    # Both move together = agreement
    divergence = abs(pinn_pct - avg_pct)
    
    if abs(pinn_pct) < 0.005:  # <0.5% movement
        if avg_pct and abs(avg_pct) > 0.02:
            return -0.5  # Pinnacle static, market moved
        return 0.0
    
    # Pinnacle moved significantly
    if abs(pinn_pct) >= 0.02 and divergence < 0.01:
        return 1.0  # Both moved together in same direction
    elif abs(pinn_pct) >= 0.02 and divergence >= 0.03:
        return -0.5  # Pinnacle moved one way, market different
    elif abs(pinn_pct) >= 0.01:
        return 0.5  # Moderate movement
    return 0.0


def compute_cd(match):
    """Compute CD score using Sharp vs Asian vs Retail tier movements."""
    bms = match["ouzhi"]["bookmakers"]
    
    def avg_move(cids):
        moves = []
        for bm in bms:
            if bm["cid"] not in cids:
                continue
            for outcome in ["home", "draw", "away"]:
                op = bm.get(f"opening_{outcome}")
                cl = bm.get(f"closing_{outcome}")
                if op and cl and op > 0:
                    moves.append((cl - op) / op)
        return sum(moves) / len(moves) if moves else 0.0
    
    sharp_move = avg_move(SHARP_CIDS)
    asian_move = avg_move(ASIAN_CIDS)
    retail_move = avg_move(RETAIL_CIDS)
    
    all_moves = {"home": 0.0, "draw": 0.0, "away": 0.0}
    for outcome in ["home", "draw", "away"]:
        h_moves = []
        for bm in bms:
            op = bm.get(f"opening_{outcome}")
            cl = bm.get(f"closing_{outcome}")
            if op and cl and op > 0:
                h_moves.append((cl - op) / op)
        all_moves[outcome] = sum(h_moves) / len(h_moves) if h_moves else 0.0
    
    # Determine Sharp-tier favored direction
    pinn = match["ouzhi"]["pinnacle"]
    pinn_favored = min(
        {"home": (pinn["closing_home"] - pinn["opening_home"]) / pinn["opening_home"],
         "draw": (pinn["closing_draw"] - pinn["opening_draw"]) / pinn["opening_draw"],
         "away": (pinn["closing_away"] - pinn["opening_away"]) / pinn["opening_away"]},
        key=lambda k: (pinn[f"closing_{k}"] - pinn[f"opening_{k}"]) / pinn[f"opening_{k}"]
    )
    
    # Popular direction (Asian + Retail consensus)
    popular_avg = {}
    for outcome in ["home", "draw", "away"]:
        moves = []
        for bm in bms:
            if bm["cid"] in SHARP_CIDS:
                continue
            op = bm.get(f"opening_{outcome}")
            cl = bm.get(f"closing_{outcome}")
            if op and cl and op > 0:
                moves.append((cl - op) / op)
        popular_avg[outcome] = sum(moves) / len(moves) if moves else 0.0
    
    popular_favored = min(popular_avg, key=popular_avg.get)
    
    # Internal Sharp consistency
    sharp_deltas = {}
    for outcome in ["home", "draw", "away"]:
        vals = []
        for bm in bms:
            if bm["cid"] not in SHARP_CIDS:
                continue
            op = bm.get(f"opening_{outcome}")
            cl = bm.get(f"closing_{outcome}")
            if op and cl and op > 0:
                vals.append((cl - op) / op)
        if vals:
            sharp_deltas[outcome] = {"mean": sum(vals)/len(vals), "std": (sum((v - sum(vals)/len(vals))**2 for v in vals)/len(vals))**0.5}
    
    # Consensus: if Sharp has a clear direction
    sharp_consistent = True
    if sharp_deltas:
        for outcome, data in sharp_deltas.items():
            if data["std"] > 0.03:  # More than 3% std = disagreement
                sharp_consistent = False
                break
    
    if not sharp_consistent:
        return -1.0  # Institutional disagreement
    elif pinn_favored != popular_favored:
        return 1.0  # Sharp vs public, channel divergence
    elif pinn_favored == popular_favored:
        return 0.5  # Leading follow, consensus
    else:
        return -0.5  # Public consensus without Sharp lead


def determine_result(match):
    """Determine actual result direction."""
    hs = match["home_score"]
    as_ = match["away_score"]
    if hs > as_:
        return "home"
    elif hs < as_:
        return "away"
    return "draw"


def run_backtest():
    matches = load_data()
    results = []
    
    for m in matches:
        result = determine_result(m)
        pvd = compute_pvd(m)
        cd = compute_cd(m)
        mpc = 0.6 * pvd + 0.4 * cd
        
        # Deadzone filter
        if abs(mpc) < 0.2:
            status = "NORMAL"
            adj = 1.0
        elif mpc >= 0.2:
            status = "NORMAL"
            adj = 1.0 + mpc * 0.10
        else:  # mpc <= -0.5 or between -0.2 and -0.5
            if mpc < -0.8:
                status = "CIRCUIT_BREAKER"
                adj = 0.0
            elif mpc < -0.5:
                status = "VETO"
                adj = 0.0
            else:
                status = "NORMAL"
                adj = 1.0 + mpc * 0.10
        
        # Determine MBI predicted direction
        pinn = m["ouzhi"]["pinnacle"]
        # Use closing odds as "prediction" (market consensus)
        home_prob = 1.0 / pinn["closing_home"]
        draw_prob = 1.0 / pinn["closing_draw"]
        away_prob = 1.0 / pinn["closing_away"]
        total = home_prob + draw_prob + away_prob
        home_prob /= total
        draw_prob /= total
        away_prob /= total
        
        # Predicted direction
        probs = {"home": home_prob, "draw": draw_prob, "away": away_prob}
        pred = max(probs, key=probs.get)
        
        correct_before = (pred == result)
        correct_after = correct_before  # MPC doesn't flip direction, only adjusts confidence
        
        results.append({
            "home": m["home_team"],
            "away": m["away_team"],
            "result": result,
            "pred": pred,
            "pvd": round(pvd, 2),
            "cd": round(cd, 2),
            "mpc": round(mpc, 2),
            "status": status,
            "adj": round(adj, 3),
            "correct": correct_before,
            "score": f"{m['home_score']}-{m['away_score']}",
            "stage": m["stage"],
        })
    
    return results


def generate_html(results):
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    base_acc = correct / total
    
    # MPC affected (deadzone passed)
    affected = [r for r in results if r["mpc"] >= 0.2 or r["mpc"] <= -0.5]
    aff_correct = sum(1 for r in affected if r["correct"])
    aff_acc = aff_correct / len(affected) if affected else 0
    
    # Veto/Breaker stats
    vetoed = [r for r in results if r["status"] in ("VETO", "CIRCUIT_BREAKER")]
    veto_correct = sum(1 for r in vetoed if not r["correct"])  # correctly rejected = prediction was wrong
    veto_accuracy = veto_correct / len(vetoed) if vetoed else 0
    
    # Information gain
    gain = aff_acc - base_acc
    
    # Build table rows
    rows = ""
    for r in sorted(results, key=lambda x: x["status"]):
        status_badge = ""
        if r["status"] == "CIRCUIT_BREAKER":
            status_badge = '<span style="background:#E24B4A;color:white;padding:2px 8px;border-radius:4px;font-size:11px">BREAKER</span>'
        elif r["status"] == "VETO":
            status_badge = '<span style="background:#D85A30;color:white;padding:2px 8px;border-radius:4px;font-size:11px">VETO</span>'
        elif r["mpc"] > 0.2:
            status_badge = '<span style="background:#639922;color:white;padding:2px 8px;border-radius:4px;font-size:11px">BULLISH</span>'
        
        corr_badge = "✅" if r["correct"] else "❌"
        rows += f"<tr><td>{r['home']} vs {r['away']}</td><td>{r['score']}</td><td>{r['pred']}</td><td>{r['result']}</td><td>{corr_badge}</td><td>{r['pvd']}</td><td>{r['cd']}</td><td>{r['mpc']}</td><td>{status_badge}</td><td>{r['stage']}</td></tr>"
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>KB-14 MPC Backtest — 2022 World Cup</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 24px; background: #FAFAFA; color: #2C2C2A; }}
h1 {{ font-size: 18px; font-weight: 500; }}
h2 {{ font-size: 15px; font-weight: 500; margin-top: 24px; }}
.metrics {{ display: flex; gap: 16px; flex-wrap: wrap; margin: 16px 0; }}
.metric {{ background: white; border: 1px solid #D3D1C7; border-radius: 8px; padding: 12px 20px; }}
.metric .value {{ font-size: 28px; font-weight: 500; }}
.metric .label {{ font-size: 12px; color: #5F5E5A; }}
.green {{ color: #3B6D11; }}
.red {{ color: #A32D2D; }}
.neutral {{ color: #5F5E5A; }}
table {{ border-collapse: collapse; width: 100%; font-size: 12px; margin-top: 12px; }}
th, td {{ border: 1px solid #D3D1C7; padding: 6px 10px; text-align: left; }}
th {{ background: #F1EFE8; font-weight: 500; }}
tr:hover {{ background: #F8F6F0; }}
.notes {{ background: #EEEDFE; border-left: 4px solid #7F77DD; padding: 12px 16px; margin: 16px 0; border-radius: 4px; font-size: 13px; line-height: 1.6; }}
</style></head><body>
<h1>KB-14 MPC Backtest — 2022 World Cup (64 matches)</h1>

<div class="metrics">
  <div class="metric"><div class="value">{total}</div><div class="label">Total matches</div></div>
  <div class="metric"><div class="value">{base_acc:.1%}</div><div class="label">Baseline accuracy (market)</div></div>
  <div class="metric"><div class="value {('green' if gain > 0 else 'red')}">{gain:+.1%}</div><div class="label">Information gain (MPC affected)</div></div>
  <div class="metric"><div class="value">{len(affected)}</div><div class="label">MPC affected matches</div></div>
  <div class="metric"><div class="value">{aff_acc:.1%}</div><div class="label">Accuracy on affected</div></div>
  <div class="metric"><div class="value">{len(vetoed)}</div><div class="label">Veto/Breaker triggered</div></div>
  <div class="metric"><div class="value {('green' if veto_accuracy > 0.6 else 'neutral')}">{veto_accuracy:.1%}</div><div class="label">Veto/Breaker accuracy</div></div>
</div>

<div class="notes">
<b>Key indicators:</b><br>
• If <b>affected count ≥ 15</b> (25% of 64), MPC has sufficient coverage to be meaningful in a matchday with ~4-6 matches.<br>
• If <b>information gain > 0%</b>, MPC adds signal on top of baseline — even +1-2% is useful for confidence calibration.<br>
• If <b>Veto/Breaker accuracy ≥ 60%</b>, the rejection mechanism is working: correctly identifying unreliable matches.
</div>

<table>
<thead><tr>
<th>Match</th><th>Score</th><th>Pred</th><th>Result</th><th>Corr</th><th>PVD</th><th>CD</th><th>MPC</th><th>Status</th><th>Stage</th>
</tr></thead>
<tbody>
{rows}
</tbody></table>
<p style="font-size:11px;color:#888780;margin-top:16px">Generated {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')} | KB-14 v3.1.2</p>
</body></html>
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(html, encoding="utf-8")
    print(f"Report written to {REPORT}")


if __name__ == "__main__":
    results = run_backtest()
    generate_html(results)
    
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    print(f"\nTotal: {total}, Baseline accuracy: {correct/total:.1%}")
    
    affected = [r for r in results if r["mpc"] >= 0.2 or r["mpc"] <= -0.5]
    if affected:
        aff_correct = sum(1 for r in affected if r["correct"])
        print(f"MPC affected: {len(affected)}, Accuracy: {aff_correct/len(affected):.1%}")
        print(f"Information gain: {aff_correct/len(affected) - correct/total:+.1%}")
    
    vetoed = [r for r in results if r["status"] in ("VETO", "CIRCUIT_BREAKER")]
    if vetoed:
        veto_correct = sum(1 for r in vetoed if not r["correct"])
        print(f"Veto/Breaker: {len(vetoed)}, Correct rejection: {veto_correct/len(vetoed):.1%}")
