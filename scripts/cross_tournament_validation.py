#!/usr/bin/env python3
"""
跨赛事验证: 头脑风暴6假设 + 3开放问题的数据驱动检验
数据源: WC2022(64) + EURO2024(51) + WC2018(64) = 179场

基于 2026-06-25 头脑风暴，验证以下假设:
  H1: Pin方向分段准确率 ≠ 63.6% 全量平均 — 低赔率区间更高
  H2: Kelly edge公式用全量63.6%导致低赔区误判 — 应使用分段准确率
  H3: 亚盘穿盘率随让球深度增加而下降 — 深盘SPF vs RQSPF风险不对等
  H4: (部分) 亚盘水位变动是否携带独立于SPF变动的信息
"""

import json
import math
import os
from collections import defaultdict

# ─── 数据加载 ───

def load_dataset(path, name):
    with open(path) as f:
        data = json.load(f)
    matches = data.get('matches', data) if isinstance(data, dict) else data
    if isinstance(matches, dict):
        matches = list(matches.values())
    print(f"  {name}: {len(matches)} matches")
    return matches

print("=" * 70)
print("跨赛事方法论文档验证")
print("=" * 70)

BASE = "/Users/tracy/Desktop/足彩/.cache"
wc22 = load_dataset(f"{BASE}/500com_wc2022/wc2022_backtest_data.json", "WC2022")
eu24 = load_dataset(f"{BASE}/tournament_data/euro2024_backtest.json", "EURO2024")
wc18 = load_dataset(f"{BASE}/tournament_data/wc2018_backtest.json", "WC2018")

all_matches = []
for m in wc22:
    m['_source'] = 'WC2022'
    all_matches.append(m)
for m in eu24:
    m['_source'] = 'EURO2024'
    all_matches.append(m)
for m in wc18:
    m['_source'] = 'WC2018'
    all_matches.append(m)

print(f"\n总计: {len(all_matches)} matches\n")

# ─── 工具函数 ───

def get_pin_odds(m):
    """返回 (pin_direction, pin_odds, home_odds, draw_odds, away_odds)"""
    pin = m.get('ouzhi', {}).get('pinnacle', {})
    h = pin.get('closing_home', 999)
    d = pin.get('closing_draw', 999)
    a = pin.get('closing_away', 999)
    
    if h == 999:
        # fallback to avg_closing
        avg = m.get('ouzhi', {}).get('avg_closing', {})
        h = avg.get('home', 999)
        d = avg.get('draw', 999)
        a = avg.get('away', 999)
    
    min_odds = min(h, d, a)
    if min_odds == h:
        direction = 'home'
        pin_odds = h
    elif min_odds == a:
        direction = 'away'
        pin_odds = a
    else:
        direction = 'draw'
        pin_odds = d
    
    return direction, pin_odds, h, d, a

def get_actual_result(m):
    hs = m.get('home_score', 0)
    aws = m.get('away_score', 0)
    if hs > aws:
        return 'home'
    elif hs < aws:
        return 'away'
    else:
        return 'draw'

def parse_handicap(raw_hand):
    """Parse handicap string like '0.880受' or '1.000'
    Returns (handicap_value, side) where:
      - positive handicap_value = home team gives
      - negative handicap_value = away team gives (home team receives, 受)
      - side: 'home' or 'away' (which team is giving)
    """
    if not raw_hand or raw_hand == 'N/A':
        return 0.0, None
    
    s = str(raw_hand).strip()
    
    # Check for "受" character (home receives) - may be garbled as "��"
    is_home_receive = ('受' in s) or ('\ufffd' in s) or (len(s) > 6 and s[-1] != '0' and s[-1] != '5')
    
    # Also check if the last char is non-numeric (Chinese chars)
    try:
        float(s)
        is_pure_number = True
    except ValueError:
        is_pure_number = False
    
    if not is_pure_number:
        # Extract numeric portion
        num_str = ''
        for ch in s:
            if ch.isdigit() or ch == '.' or ch == '-':
                num_str += ch
        try:
            val = float(num_str)
        except ValueError:
            return 0.0, None
        
        if '受' in s:
            # Home team receives = away team gives
            return val, 'away'
        else:
            # Try to detect garbled "受" vs other chars
            # "受" is a single 3-byte UTF-8 char; garbled shows as ��
            # If the string has non-numeric trailing chars and no "让", assume 受
            return val, 'away'  # default: trailing char = 受 = away gives
    else:
        val = float(s)
        return val, 'home'  # pure number = home team gives

def get_handicap_depth(m):
    """Get handicap line for the Pin direction team.
    Returns handicap depth (negative = giving, positive = receiving) and cover result.
    """
    yazhi = m.get('yazhi', {})
    if not yazhi:
        return None, None
    
    pa = yazhi.get('pinnacle_ah', {})
    if not pa:
        # Try first bookmaker
        handicaps = yazhi.get('handicaps', [])
        if handicaps:
            pa = handicaps[0]
        else:
            return None, None
    
    raw = pa.get('handicap', 'N/A')
    hw = pa.get('home_water', 'N/A')
    aw = pa.get('away_water', 'N/A')
    
    try:
        hw_f = float(hw) if hw != 'N/A' else 0
        aw_f = float(aw) if aw != 'N/A' else 0
    except ValueError:
        hw_f, aw_f = 0, 0
    
    handicap_val, giving_side = parse_handicap(raw)
    
    if handicap_val == 0 and giving_side is None:
        return None, None
    
    # Determine which team is giving the handicap
    # Positive = home gives, Negative = away gives
    depth = handicap_val
    if giving_side == 'away':
        depth = -handicap_val  # away team gives = home team receives
    
    # Get actual goal difference
    hs = m.get('home_score', 0)
    aws = m.get('away_score', 0)
    gd = hs - aws  # home goal diff
    
    # Check if the handicap-giving team covered
    # If depth > 0: home gives → home covers if gd > depth, pushes if gd == depth
    # If depth < 0: away gives → away covers if -gd > abs(depth) (away wins by more)
    
    if depth > 0:
        # Home team gives handicap
        if gd > depth:
            cover = 'home_cover'
        elif gd == depth:
            cover = 'push'
        else:
            cover = 'home_fail'
    elif depth < 0:
        # Away team gives handicap
        away_give = abs(depth)
        if -gd > away_give:
            cover = 'away_cover'
        elif -gd == away_give:
            cover = 'push'
        else:
            cover = 'away_fail'
    else:
        cover = 'level'
    
    return depth, cover

# ─── 验证 1: Pin方向分段准确率 ───

print("=" * 70)
print("验证 1: Pin方向分段准确率 vs 全量 63.6% 基准")
print("=" * 70)

# 赔率分箱 (Pin方向最低赔率值)
bins = [
    (1.01, 1.20, "超深热门 1.01-1.20"),
    (1.21, 1.35, "深热门 1.21-1.35"),
    (1.36, 1.50, "强热门 1.36-1.50"),
    (1.51, 1.70, "中等热门 1.51-1.70"),
    (1.71, 2.00, "浅热门 1.71-2.00"),
    (2.01, 2.50, "弱优势 2.01-2.50"),
    (2.51, 99.0, "无优势 2.51+"),
]

bin_results = {label: {'correct': 0, 'total': 0, 'home_correct': 0, 'away_correct': 0, 'draw_correct': 0} for _, _, label in bins}
overall = {'correct': 0, 'total': 0}

for m in all_matches:
    pin_dir, pin_odds, _, _, _ = get_pin_odds(m)
    actual = get_actual_result(m)
    
    correct = (pin_dir == actual)
    overall['correct'] += correct
    overall['total'] += 1
    
    for lo, hi, label in bins:
        if lo <= pin_odds <= hi:
            bin_results[label]['correct'] += correct
            bin_results[label]['total'] += 1
            if pin_dir == actual == 'home':
                bin_results[label]['home_correct'] += 1
            elif pin_dir == actual == 'away':
                bin_results[label]['away_correct'] += 1
            elif pin_dir == actual == 'draw':
                bin_results[label]['draw_correct'] += 1
            break

print(f"\n{'赔率区间':<28} {'场次':>5} {'命中':>5} {'准确率':>8} {'95%CI':>14} {'vs基准Δ':>8}")
print("-" * 75)

baseline = 0.636
for lo, hi, label in bins:
    r = bin_results[label]
    if r['total'] == 0:
        continue
    acc = r['correct'] / r['total']
    se = math.sqrt(acc * (1 - acc) / r['total'])
    ci_lo = max(0, acc - 1.96 * se)
    ci_hi = min(1, acc + 1.96 * se)
    delta = acc - baseline
    bar = "█" * max(1, int(r['total'] / 2))
    print(f"{label:<28} {r['total']:>5} {r['correct']:>5} {acc:>7.1%}  [{ci_lo:.1%}-{ci_hi:.1%}] {delta:>+7.1%}  {bar}")

# Summary
acc = overall['correct'] / overall['total']
se = math.sqrt(acc * (1 - acc) / overall['total'])
ci_lo = max(0, acc - 1.96 * se)
ci_hi = min(1, acc + 1.96 * se)
print("-" * 75)
print(f"{'全量总计':<28} {overall['total']:>5} {overall['correct']:>5} {acc:>7.1%}  [{ci_lo:.1%}-{ci_hi:.1%}]")

# ─── 验证 2: Kelly edge公式校准 ───

print("\n" + "=" * 70)
print("验证 2: Kelly edge公式校准 — 实际 edge vs 公式 edge")
print("=" * 70)

print(f"\n当前公式: edge = 0.636 - (1/Pin_odds)")
print(f"{'赔率区间':<28} {'场次':>5} {'实际Win%':>9} {'隐含Prob':>9} {'实际Edge':>9} {'公式Edge':>9} {'偏差':>9}")
print("-" * 85)

for lo, hi, label in bins:
    r = bin_results[label]
    if r['total'] == 0:
        continue
    
    # 计算该区间平均赔率
    avg_odds = 0
    count = 0
    for m in all_matches:
        pin_dir, pin_odds, _, _, _ = get_pin_odds(m)
        if lo <= pin_odds <= hi:
            avg_odds += pin_odds
            count += 1
    if count == 0:
        continue
    avg_odds /= count
    
    actual_win_pct = r['correct'] / r['total']
    implied_prob = 1.0 / avg_odds
    actual_edge = actual_win_pct - implied_prob
    formula_edge = baseline - implied_prob
    
    print(f"{label:<28} {r['total']:>5} {actual_win_pct:>8.1%} {implied_prob:>8.1%} {actual_edge:>+8.1%} {formula_edge:>+8.1%} {actual_edge-formula_edge:>+8.1%}")

# ─── 验证 3: 亚盘穿盘率 (WC2022 only) ───

print("\n" + "=" * 70)
print("验证 3: 亚盘穿盘率 — 让球深度 vs 实际穿盘 (WC2022 64场)")
print("=" * 70)

wc22_only = [m for m in all_matches if m['_source'] == 'WC2022']

# Group by handicap depth
depth_bins = defaultdict(lambda: {'total': 0, 'cover': 0, 'fail': 0, 'push': 0, 'spf_win': 0, 'spf_total': 0})

for m in wc22_only:
    pin_dir, pin_odds, _, _, _ = get_pin_odds(m)
    actual = get_actual_result(m)
    depth, cover = get_handicap_depth(m)
    
    if depth is None or cover is None:
        continue
    
    # Round depth to nearest quarter
    depth_key = round(depth * 4) / 4  # 0.25 increments
    
    # Which team is giving?
    giving_team = 'home' if depth > 0 else 'away'
    pin_team = pin_dir  # 'home' or 'away'
    
    # Only count if Pin direction matches the giving team
    # (the market expects Pin direction team to be the one giving handicap)
    if giving_team == 'away':
        # Away team gives → Pin direction should be away
        if pin_dir != 'away':
            continue
    else:
        # Home team gives → Pin direction should be home
        if pin_dir != 'home':
            continue
    
    depth_bins[depth_key]['total'] += 1
    if 'cover' in cover:
        depth_bins[depth_key]['cover'] += 1
    elif 'fail' in cover:
        depth_bins[depth_key]['fail'] += 1
    elif 'push' in cover:
        depth_bins[depth_key]['push'] += 1
    
    # Track SPF win vs handicap
    depth_bins[depth_key]['spf_total'] += 1
    if (giving_team == 'home' and actual == 'home') or (giving_team == 'away' and actual == 'away'):
        depth_bins[depth_key]['spf_win'] += 1

print(f"\n{'让球深度':>10} {'场次':>5} {'穿盘':>5} {'未穿':>5} {'走水':>5} {'穿盘率':>8} {'SPF胜率':>8} {'降幅':>8}")
print("-" * 65)

depth_sorted = sorted(depth_bins.items(), key=lambda x: abs(x[0]))
for depth, r in depth_sorted:
    if r['total'] == 0:
        continue
    cover_rate = r['cover'] / r['total']
    spf_rate = r['spf_win'] / r['spf_total'] if r['spf_total'] > 0 else 0
    diff = spf_rate - cover_rate
    
    # Determine direction text
    if depth > 0:
        dir_text = f"主让{depth:.2f}"
    elif depth < 0:
        dir_text = f"客让{abs(depth):.2f}"
    else:
        dir_text = "平手"
    
    print(f"{dir_text:>10} {r['total']:>5} {r['cover']:>5} {r['fail']:>5} {r['push']:>5} {cover_rate:>7.1%} {spf_rate:>7.1%} {diff:>+7.1%}")

# ─── 验证 4: Pin方向=draw时的特殊处理 ───

print("\n" + "=" * 70)
print("验证 4: Pin方向=平局 的实际情况")
print("=" * 70)

draw_pin = [m for m in all_matches if get_pin_odds(m)[0] == 'draw']
draw_correct = sum(1 for m in draw_pin if get_actual_result(m) == 'draw')
print(f"Pin=平局: {len(draw_pin)}场, 实际平局: {draw_correct}场, 准确率: {draw_correct/len(draw_pin):.1%}" if draw_pin else "Pin=平局: 0场 (Pinnacle从不把平局排最低)")

# ─── 验证 5: Euro 2024 vs WC 2018 vs WC 2022 跨赛事稳定性 ───

print("\n" + "=" * 70)
print("验证 5: 跨赛事 Pin 准确率稳定性")
print("=" * 70)

print(f"\n{'赛事':<15} {'场次':>5} {'正确':>5} {'准确率':>8} {'95%CI':<14} {'vs63.6%':>8}")
print("-" * 60)

for source in ['WC2022', 'EURO2024', 'WC2018']:
    matches = [m for m in all_matches if m['_source'] == source]
    correct = sum(1 for m in matches if get_pin_odds(m)[0] == get_actual_result(m))
    total = len(matches)
    acc = correct / total
    se = math.sqrt(acc * (1 - acc) / total)
    ci_lo = acc - 1.96 * se
    ci_hi = acc + 1.96 * se
    delta = acc - baseline
    print(f"{source:<15} {total:>5} {correct:>5} {acc:>7.1%} [{ci_lo:.2f}-{ci_hi:.2f}] {delta:>+7.1%}")

# ─── 总结 ───

print("\n" + "=" * 70)
print("诊断总结")
print("=" * 70)

# Find the 1.33 segment specifically
print("\n--- H1: Pin分段准确率 ---")
for lo, hi, label in bins:
    r = bin_results[label]
    if r['total'] > 0:
        acc = r['correct'] / r['total']
        if '1.21-1.35' in label:
            print(f"  【关键】{label}: {r['correct']}/{r['total']} = {acc:.1%}")
            print(f"    → 德国 1.33 属于此区间, 实际准确率 {acc:.1%} vs 公式假设 63.6%")
            if acc > 0.636:
                print(f"    → 结论: Kelly公式低估了低赔热门胜率 {acc-0.636:.1%}")
            else:
                print(f"    → 结论: 低赔热门并未显著高于全量平均")

print("\n--- H2: Kelly edge公式 ---")
print("  核心发现见验证2表格 — 比较 '实际Edge' 列 vs '公式Edge' 列")
print("  若实际Edge > 0 但公式Edge < 0 → 公式导致放弃正EV投注")

print("\n--- H3: 让球穿盘率 ---")
for depth, r in depth_sorted:
    if abs(depth) >= 1.0 and r['total'] > 0:
        cover_rate = r['cover'] / r['total']
        spf_rate = r['spf_win'] / r['spf_total'] if r['spf_total'] > 0 else 0
        print(f"  让{abs(depth):.1f}球: 穿盘{cover_rate:.1%} vs SPF{spf_rate:.1%}")
        if cover_rate < 0.4:
            print(f"    → 深盘穿盘率<40%, 选RQSPF比选SPF风险高 {spf_rate-cover_rate:.0%}")

print("\n--- H4: 跨赛事稳定性 ---")
print("  若三个赛事Pin准确率均>60%且std<5pp → Pin作为基线的可靠性确认")

print("\n验证完成。")
