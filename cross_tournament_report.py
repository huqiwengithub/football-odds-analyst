#!/usr/bin/env python3
"""Generate HTML report from cross-tournament backtest results."""

import json, os
from collections import defaultdict

BASE_DIR = "/Users/tracy/Desktop/足彩"

def load_results():
    with open(os.path.join(BASE_DIR, 'cross_tournament_backtest.json')) as f:
        return json.load(f)

def generate_html(results):
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>跨赛事FVS/DRM回测报告</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
       background: #f5f6fa; color: #2d3436; line-height: 1.6; }
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
.header { background: linear-gradient(135deg, #6c5ce7, #0984e3); color: white; 
           padding: 40px; border-radius: 16px; margin-bottom: 24px; }
.header h1 { font-size: 28px; font-weight: 700; }
.header p { opacity: 0.9; margin-top: 8px; }
.card { background: white; border-radius: 12px; padding: 24px; margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.card h2 { font-size: 20px; color: #2d3436; margin-bottom: 16px; padding-bottom: 8px;
           border-bottom: 2px solid #dfe6e9; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 10px 14px; text-align: center; border-bottom: 1px solid #dfe6e9; }
th { background: #f8f9fa; font-weight: 600; color: #636e72; font-size: 13px; }
td { font-size: 14px; }
tr:hover { background: #f0f4ff; }
.positive { color: #00b894; font-weight: 700; }
.negative { color: #e17055; font-weight: 700; }
.neutral { color: #fdcb6e; }
.stat-box { display: inline-block; text-align: center; padding: 12px 24px; margin: 8px; 
            background: #f8f9fa; border-radius: 8px; min-width: 120px; }
.stat-box .num { font-size: 36px; font-weight: 800; line-height: 1.2; }
.stat-box .label { font-size: 12px; color: #636e72; margin-top: 4px; }
.chart-container { height: 300px; margin: 16px 0; }
.detail-row { font-family: 'SF Mono', 'Consolas', monospace; font-size: 12px; }
.tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.tag-ok { background: #55efc4; color: #00b894; }
.tag-veto { background: #fab1a0; color: #d63031; }
.tag-saved { background: #74b9ff; color: #0984e3; }
.finding { background: #fff3e0; border-left: 4px solid #ff9800; padding: 16px; margin: 12px 0; border-radius: 4px; }
.finding h3 { color: #e65100; margin-bottom: 8px; }
.finding p { font-size: 14px; color: #555; }
</style>
</head>
<body>
<div class="container">
<div class="header">
  <h1>📊 跨赛事 FVS/DRM 回测报告</h1>
  <p>v3.3.1 校准验证 · 2022世界杯 + 2018世界杯 + 2024欧洲杯 · 共179场比赛</p>
</div>
"""

    # Summary stats
    all_rows = []
    for name in ['2022 WC', '2018 WC', '2024 Euro']:
        all_rows.extend(results.get(name, {}).get('rows', []))
    
    total = len(all_rows)
    old_ok = sum(1 for r in all_rows if r['old'])
    old_acc = old_ok / max(total, 1)
    vetoed = sum(1 for r in all_rows if r['vetoed'])
    veto_saved = sum(1 for r in all_rows if r['vetoed'] and not r['old'])
    veto_cost = sum(1 for r in all_rows if r['vetoed'] and r['old'])
    passed = sum(1 for r in all_rows if not r['vetoed'])
    pass_ok = sum(1 for r in all_rows if not r['vetoed'] and r['old'])
    new_acc = pass_ok / max(passed, 1)
    
    drm2 = [r for r in all_rows if r['drm'] >= 2]
    drm2_ok = sum(1 for r in drm2 if r['old'])
    drm2_fail = len(drm2) - drm2_ok
    drm2_ok_pct = drm2_ok / max(len(drm2), 1)
    drm2_draws = sum(1 for r in drm2 if not r['old'] and r['act'] == 'draw')
    
    html += f"""
<div class="card">
  <h2>📈 综合表现</h2>
  <div style="display:flex;flex-wrap:wrap;justify-content:center;margin-bottom:16px;">
    <div class="stat-box"><div class="num" style="color:#6c5ce7">{total}</div><div class="label">总场次</div></div>
    <div class="stat-box"><div class="num" style="color:#0984e3">{old_ok}</div><div class="label">旧系统正确</div></div>
    <div class="stat-box"><div class="num" style="color:#00b894">{pass_ok}</div><div class="label">新系统正确</div></div>
    <div class="stat-box"><div class="num" style="color:#e17055">{vetoed}</div><div class="label">否决(不投)</div></div>
    <div class="stat-box"><div class="num" style="color:#0984e3">{veto_saved}</div><div class="label">规避冷门</div></div>
    <div class="stat-box"><div class="num" style="color:#fdcb6e">{veto_cost}</div><div class="label">错杀场次</div></div>
  </div>
  
  <table>
    <tr><th>赛事</th><th>总场次</th><th>旧系统命中率</th><th>新系统命中率</th><th>变化</th>
        <th>否决</th><th>规避冷门</th><th>错杀</th><th>精确率</th><th>召回率</th></tr>
"""
    for name in ['2022 WC', '2018 WC', '2024 Euro']:
        d = results.get(name)
        if not d:
            continue
        s = d
        tot = s['total']
        oa = s['old_accuracy']
        na = s['new_accuracy']
        chg = na - oa
        veto = s['vetoed']
        saved = s['saved']
        cost = s['cost']
        prec = saved / max(veto, 1)
        rec = saved / max(tot - int(oa * tot), 1)
        cls = 'positive' if chg > 0 else 'negative'
        html += f"""
    <tr>
      <td><strong>{name.replace('WC','世界杯').replace('Euro','欧洲杯')}</strong></td>
      <td>{tot}</td>
      <td>{oa:.1%}</td>
      <td>{na:.1%}</td>
      <td class="{cls}">{chg:+.1%}</td>
      <td>{veto}</td>
      <td>{saved}</td>
      <td>{cost}</td>
      <td>{prec:.0%}</td>
      <td>{rec:.0%}</td>
    </tr>"""
    
    chg_combined = new_acc - old_acc
    cls_combined = 'positive' if chg_combined > 0 else 'negative'
    prec_all = veto_saved / max(vetoed, 1)
    rec_all = veto_saved / max(total - old_ok, 1)
    html += f"""
    <tr style="background:#f0f4ff;font-weight:700;">
      <td><strong>综合</strong></td>
      <td>{total}</td>
      <td>{old_acc:.1%}</td>
      <td>{new_acc:.1%}</td>
      <td class="{cls_combined}">{chg_combined:+.1%}</td>
      <td>{vetoed}</td>
      <td>{veto_saved}</td>
      <td>{veto_cost}</td>
      <td>{prec_all:.0%}</td>
      <td>{rec_all:.0%}</td>
    </tr>
  </table>
</div>
"""

    # DRM analysis
    drm_groups = defaultdict(lambda: [0, 0])
    for r in all_rows:
        drm_groups[r['drm']][0] += 1 if r['old'] else 0
        drm_groups[r['drm']][1] += 1
    
    html += f"""
<div class="card">
  <h2>🛡️ DRM（平局风险）逐级分析</h2>
  <div class="finding">
    <h3>DRM≥2 否决信号验证</h3>
    <p>三个赛事中共有 <strong>{len(drm2)}</strong> 场比赛触发DRM≥2否决。
       旧系统在这些比赛中仅 <strong>{drm2_ok_pct:.0%}</strong> 正确，
       否决后规避了 <strong>{drm2_fail}</strong> 场错误（含 <strong>{drm2_draws}</strong> 场平局和 <strong>{drm2_fail - drm2_draws}</strong> 场完全逆转）。</p>
  </div>
  <table>
    <tr><th>DRM等级</th><th>场次</th><th>正确</th><th>错误</th><th>命中率</th><th>参考建议</th></tr>
"""
    colors = {0: '#00b894', 1: '#fdcb6e', 2: '#e17055', 3: '#d63031', 4: '#6c5ce7'}
    for drm in sorted(drm_groups.keys()):
        c, t = drm_groups[drm]
        tot = c + (t - c)
        rate = c / max(t, 1)
        advice = {0: '✅ 正常投注', 1: '⚠️ 轻微注意', 2: '🔶 否决SPF', 3: '🔶 否决SPF', 4: '🚫 强否决'}.get(drm, '')
        html += f"""
    <tr>
      <td><strong>DRM={drm}</strong></td>
      <td>{t}</td>
      <td>{c}</td>
      <td>{t-c}</td>
      <td style="color:{colors.get(drm, '#333')};font-weight:700;">{rate:.0%}</td>
      <td>{advice}</td>
    </tr>"""
    html += """</table></div>"""

    # FVS analysis
    fvs_groups = defaultdict(lambda: [0, 0])
    for r in all_rows:
        fvs_groups[r['fvs']][0] += 1 if r['old'] else 0
        fvs_groups[r['fvs']][1] += 1
    
    html += f"""
<div class="card">
  <h2>🔥 FVS（热门脆弱性）逐级分析</h2>
  <table>
    <tr><th>FVS等级</th><th>场次</th><th>正确</th><th>错误</th><th>命中率</th></tr>
"""
    for fvs in sorted(fvs_groups.keys()):
        c, t = fvs_groups[fvs]
        rate = c / max(t, 1)
        clr = '#00b894' if rate > 0.6 else '#fdcb6e' if rate > 0.4 else '#e17055'
        html += f"""
    <tr>
      <td><strong>FVS={fvs}</strong></td>
      <td>{t}</td>
      <td>{c}</td>
      <td>{t-c}</td>
      <td style="color:{clr};font-weight:700;">{rate:.0%}</td>
    </tr>"""
    html += """</table></div>"""

    # Key findings
    html += """
<div class="card">
  <h2>🔬 关键发现</h2>
  
  <div class="finding">
    <h3>1️⃣ DRM≥2 否决是最强单一信号</h3>
    <p>三赛事综合：DRM≥2的 <strong>86</strong> 场比赛中，旧系统仅 <strong>51%</strong> 正确。否决后可避免 <strong>49%</strong> 的预测错误。平局（25场）和完全逆转（17场）占比近乎各半，说明DRM既能抓平局也能防冷门。</p>
  </div>
  
  <div class="finding">
    <h3>2️⃣ FVS=2 是"甜蜜点"</h3>
    <p>FVS=2的26场比赛命中率高达 <strong>73%</strong>（三赛事综合），远高于FVS=0（51%）和FVS=1（42%）。FVS=1实际上是反向指标——轻微警告反而意味着热门更安全？这可能是因为微弱FVS信号来自庄家刻意制造的"假危险"。</p>
  </div>
  
  <div class="finding">
    <h3>3️⃣ 2024欧洲杯是唯一退步的赛事</h3>
    <p>2024欧洲杯上，新系统表现不如旧系统（51.0%→48.3%）。可能是因为欧洲杯整体冷门率极高（49%的比赛热门失败），否决信号过于频繁反而减少了样本量。FVS/DRM校准可能具有赛事依赖性。</p>
  </div>
  
  <div class="finding">
    <h3>4️⃣ 综合改善有限但方向一致</h3>
    <p>三赛事综合命中率从 <strong>54.7%→57.6%</strong>（+2.9pp）。虽然不如2022世界杯单独回测的改善幅度（+12.8pp），但在所有赛事中方向一致（除欧洲杯）。精确率48%意味着约一半的否决是正确规避了冷门。</p>
  </div>
</div>
"""

    # Matches table
    html += """
<div class="card">
  <h2>📋 详细赛事数据</h2>
  <div style="overflow-x:auto;">
  <table>
    <tr><th>赛事</th><th>日期</th><th>比赛</th><th>比分</th><th>方向</th><th>结果</th>
        <th>FVS</th><th>DRM</th><th>旧</th><th>否决</th></tr>
"""
    for name in ['2022 WC', '2018 WC', '2024 Euro']:
        d = results.get(name)
        if not d:
            continue
        rows = d.get('rows', [])
        label = name.replace('WC','世界杯').replace('Euro','欧洲杯')
        for r in rows:
            old_mark = '✅' if r['old'] else '❌'
            if r['vetoed']:
                new_mark = '🛑' if not r['old'] else '⛔'
            else:
                new_mark = old_mark
            html += f"""<tr class="detail-row">
      <td>{label}</td>
      <td>{r['date']}</td>
      <td style="text-align:left;max-width:250px;overflow:hidden;">{r['match'][:30]}</td>
      <td>{r['score']}</td>
      <td>{r['dir']}</td>
      <td>{r['act']}</td>
      <td>{r['fvs']}</td>
      <td>{r['drm']}</td>
      <td>{old_mark}</td>
      <td>{new_mark}</td>
    </tr>"""
    html += """</table></div></div></div></body></html>"""
    
    return html

if __name__ == '__main__':
    results = load_results()
    html = generate_html(results)
    path = os.path.join(BASE_DIR, '跨赛事FVSDRM回测报告.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Report saved to {path}")
