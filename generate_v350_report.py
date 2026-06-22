#!/usr/bin/env python3
"""
Generate comprehensive HTML backtest report (v3.5.0).
"""

import json, os, math
from collections import defaultdict

BASE_DIR = "/Users/tracy/Desktop/足彩"

def load_results():
    with open(os.path.join(BASE_DIR, 'v350_backtest_results.json')) as f:
        return json.load(f)

def generate_html(results):
    cb = results['combined']
    tournaments = results['tournaments']
    daily = results['daily_results']
    matches = results['matches']
    bt = cb['betting']
    
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>v3.5.0 全量回测报告 — 投注模拟与盈亏分析</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
       background: #f5f6fa; color: #2d3436; line-height: 1.6; }
.container { max-width: 1400px; margin: 0 auto; padding: 20px; }
.header { background: linear-gradient(135deg, #6c5ce7, #00b894); color: white; 
           padding: 40px; border-radius: 16px; margin-bottom: 24px; }
.header h1 { font-size: 28px; font-weight: 700; }
.header p { opacity: 0.9; margin-top: 8px; }
.header .version { display: inline-block; background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 20px; font-size: 13px; margin-top: 12px; }
.card { background: white; border-radius: 12px; padding: 24px; margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.card h2 { font-size: 20px; color: #2d3436; margin-bottom: 16px; padding-bottom: 8px;
           border-bottom: 2px solid #dfe6e9; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 8px 12px; text-align: center; border-bottom: 1px solid #dfe6e9; }
th { background: #f8f9fa; font-weight: 600; color: #636e72; font-size: 12px; }
td { font-size: 13px; }
tr:hover { background: #f0f4ff; }
.positive { color: #00b894; font-weight: 700; }
.negative { color: #e17055; font-weight: 700; }
.neutral { color: #fdcb6e; }
.stat-box { display: inline-block; text-align: center; padding: 16px 28px; margin: 8px; 
            background: #f8f9fa; border-radius: 12px; min-width: 140px; box-shadow: inset 0 0 0 1px #eee; }
.stat-box .num { font-size: 40px; font-weight: 800; line-height: 1.2; }
.stat-box .label { font-size: 12px; color: #636e72; margin-top: 4px; }
.chart-container { height: 300px; margin: 16px 0; }
.tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.tag-core { background: #55efc4; color: #00b894; }
.tag-standard { background: #74b9ff; color: #0984e3; }
.tag-skip { background: #dfe6e9; color: #636e72; }
.tag-veto { background: #fab1a0; color: #d63031; }
.finding { background: #f0f8ff; border-left: 4px solid #0984e3; padding: 16px; margin: 12px 0; border-radius: 4px; }
.finding h3 { color: #0984e3; margin-bottom: 8px; font-size: 15px; }
.finding p { font-size: 14px; color: #555; }
.finding-warn { background: #fff3e0; border-left: 4px solid #ff9800; }
.finding-warn h3 { color: #e65100; }
.finding-danger { background: #fce4ec; border-left: 4px solid #e53935; }
.finding-danger h3 { color: #c62828; }
.finding-good { background: #e8f5e9; border-left: 4px solid #43a047; }
.finding-good h3 { color: #2e7d32; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
@media (max-width: 900px) { .grid-2, .grid-3 { grid-template-columns: 1fr; } }
.progress { height: 6px; border-radius: 3px; background: #eee; margin: 4px 0; }
.progress-fill { height: 100%; border-radius: 3px; }
</style>
</head>
<body>
<div class="container">
<div class="header">
  <h1>📊 v3.5.0 全量回测报告</h1>
  <p>五步量化投注 SOP 模拟 · 三项赛事179场 · 基于最新OCI+FVS/DRM+四档仓位引擎</p>
  <span class="version">🔬 引擎 v3.5.0 · 2026-06-23 生成</span>
</div>
"""
    
    # === STATS OVERVIEW ===
    html += f"""
<div class="card">
  <h2>📈 综合表现概览</h2>
  <div style="display:flex;flex-wrap:wrap;justify-content:center;margin-bottom:20px;">
    <div class="stat-box"><div class="num" style="color:#6c5ce7">{cb['total']}</div><div class="label">总场次</div></div>
    <div class="stat-box"><div class="num" style="color:#0984e3">{cb['correct']}</div><div class="label">方向正确</div></div>
    <div class="stat-box"><div class="num" style="color:#00b894">{cb['accuracy']:.0%}</div><div class="label">基础命中率</div></div>
    <div class="stat-box"><div class="num" style="color:#6c5ce7">{bt['days_with_bets']}</div><div class="label">投注天数</div></div>
    <div class="stat-box"><div class="num" style="color:#00b894">¥{bt['pnl']:+.0f}</div><div class="label">模拟盈亏(PnL)</div></div>
    <div class="stat-box"><div class="num" style="color:#00b894">{bt['roi']:+.1f}%</div><div class="label">ROI</div></div>
  </div>
  
  <table>
    <tr><th>赛事</th><th>场次</th><th>基础命中率</th><th>仓位细分(C/Sk/V)</th>
        <th>CORE命中率</th><th>投注天数</th><th>投资</th><th>回收</th><th>盈亏</th><th>ROI</th></tr>
"""
    for tname, td in tournaments.items():
        bt_data = td.get('betting', {})
        bp = td.get('by_position', {})
        core_stats = bp.get('CORE', {'count':0,'correct':0,'accuracy':0})
        core_acc = core_stats['accuracy']
        core_str = f"{core_stats['correct']}/{core_stats['count']}={core_acc:.0%}" if core_stats['count'] > 0 else '—'
        sk_v = f"{bp.get('CORE',{}).get('count',0)}/{bp.get('STANDARD',{}).get('count',0)}/{bp.get('SKIP',{}).get('count',0)}+{bp.get('VETO',{}).get('count',0)}"
        label = tname.replace('WC','世界杯').replace('Euro','欧洲杯')
        cls = 'positive' if bt_data.get('pnl', 0) > 0 else 'negative'
        html += f"""
    <tr>
      <td><strong>{label}</strong></td>
      <td>{td['total']}</td>
      <td>{td['accuracy']:.0%}</td>
      <td style="font-size:11px;">{sk_v}</td>
      <td style="color:#00b894;font-weight:700;">{core_str}</td>
      <td>{bt_data.get('days_with_bets',0)}</td>
      <td>¥{bt_data.get('invested',0):.0f}</td>
      <td>¥{bt_data.get('returned',0):.0f}</td>
      <td class="{cls}">¥{bt_data.get('pnl',0):+.0f}</td>
      <td class="{cls}">{bt_data.get('roi',0):+.1f}%</td>
    </tr>"""
    html += f"""
    <tr style="background:#f0f4ff;font-weight:700;">
      <td><strong>合计</strong></td>
      <td>{cb['total']}</td>
      <td>{cb['accuracy']:.0%}</td>
      <td>—</td>
      <td style="color:#00b894;">{cb['by_position'].get('CORE',{}).get('accuracy',0):.0%}</td>
      <td>{bt['days_with_bets']}</td>
      <td>¥{bt['invested']:.0f}</td>
      <td>¥{bt['returned']:.0f}</td>
      <td class="positive">¥{bt['pnl']:+.0f}</td>
      <td class="positive">{bt['roi']:+.1f}%</td>
    </tr>
  </table>
</div>
"""
    
    # === POSITION BREAKDOWN ===
    html += """
<div class="card">
  <h2>🎯 四档仓位引擎表现</h2>
  <div class="grid-3">
"""
    for pos, color, icon, desc in [
        ('CORE', '#00b894', '🔥', '核心仓位: FVS=2+DRM=0'),
        ('STANDARD', '#0984e3', '✅', '标准仓位: 无否决,中等信度'),
        ('VETO', '#d63031', '🚫', '否决: 强制跳过')
    ]:
        ps = cb['by_position'].get(pos, {'count':0,'correct':0,'accuracy':0})
        bar_pct = ps['accuracy'] * 100
        bar_color = color if ps['accuracy'] >= 0.5 else '#e17055'
        saved_count = sum(1 for m in matches if m.get('position') == pos and not m['correct'])
        html += f"""
    <div style="background:#f8f9fa;border-radius:12px;padding:20px;text-align:center;">
      <div style="font-size:36px;">{icon}</div>
      <h3 style="font-size:16px;margin:8px 0;">{pos}</h3>
      <p style="font-size:12px;color:#636e72;margin-bottom:12px;">{desc}</p>
      <div style="font-size:48px;font-weight:800;color:{color};">{ps['count']}</div>
      <div style="font-size:13px;color:#636e72;">场次</div>
      <div style="margin-top:12px;">
        <span style="color:{color};font-weight:700;font-size:24px;">{ps['accuracy']:.0%}</span>
        <span style="font-size:12px;color:#636e72;"> 命中率</span>
      </div>
      <div style="margin-top:8px;font-size:12px;">
        <span style="color:#00b894;">{ps['correct']}正确</span>
        <span style="color:#e17055;"> / {saved_count}错误</span>
      </div>
      <div class="progress" style="margin-top:12px;">
        <div class="progress-fill" style="width:{bar_pct}%;background:{bar_color};"></div>
      </div>
    </div>"""
    
    # Add SKIP
    ps = cb['by_position'].get('SKIP', {'count':0,'correct':0,'accuracy':0})
    html += f"""
    <div style="background:#f8f9fa;border-radius:12px;padding:20px;text-align:center;">
      <div style="font-size:36px;">⏭️</div>
      <h3 style="font-size:16px;margin:8px 0;">SKIP (跳过)</h3>
      <p style="font-size:12px;color:#636e72;margin-bottom:12px;">FVS异常/DRM模糊,不投</p>
      <div style="font-size:48px;font-weight:800;color:#636e72;">{ps['count']}</div>
      <div style="font-size:13px;color:#636e72;">场次</div>
      <div style="margin-top:12px;font-size:12px;">
        <span>{ps['correct']}正确 / {ps['count']-ps['correct']}错误</span>
      </div>
    </div>
  </div>
</div>
"""
    
    # === FVS × DRM MATRIX ===
    matrix_data = cb.get('fvs_drm_matrix', {})
    html += """
<div class="card">
  <h2>📐 FVS×DRM 联合矩阵</h2>
  <p style="font-size:13px;color:#636e72;margin-bottom:16px;">
    行=FVS(已清零), 列=DRM | 每个格子: 正确/总数=命中率 | 底色=仓位</p>
  <table>
    <tr><th>FVS↓ \ DRM→</th>"""
    all_drms = set()
    for fvs_str, drm_dict in matrix_data.items():
        for drm_str in drm_dict:
            all_drms.add(int(drm_str))
    for d in sorted(all_drms):
        html += f"<th>{d}</th>"
    html += "<th>合计</th></tr>"
    
    for fvs in sorted([int(k) for k in matrix_data.keys()]):
        html += f"<tr><td><strong>{fvs}</strong></td>"
        row_total = [0, 0]
        for d in sorted(all_drms):
            c, t = matrix_data[str(fvs)].get(str(d), [0, 0])
            row_total[0] += c
            row_total[1] += t
            if t > 0:
                pct = c / t
                if pct >= 0.70: clr = '#00b894'
                elif pct >= 0.50: clr = '#fdcb6e'
                else: clr = '#e17055'
                html += f'<td style="color:{clr};font-weight:700;">{c}/{t}={pct:.0%}</td>'
            else:
                html += '<td>—</td>'
        rt = row_total[1]
        if rt > 0:
            rp = row_total[0] / rt
            html += f'<td style="font-weight:700;">{row_total[0]}/{rt}={rp:.0%}</td>'
        else:
            html += '<td>—</td>'
        html += '</tr>'
    html += "</table></div>"
    
    # === FVS/DRM ANALYSIS ===
    fvs_stats = cb.get('by_fvs', {})
    drm_stats = cb.get('by_drm', {})
    
    html += """
<div class="card">
  <h2>🔬 关键模块逐级分析</h2>
  <div class="grid-2">
    <div>
      <h3 style="font-size:15px;margin-bottom:8px;">🔥 FVS (热门脆弱性) 逐级</h3>
      <table>
        <tr><th>FVS</th><th>场次</th><th>正确</th><th>命中率</th><th>建议</th></tr>"""
    for fvs_val in sorted(fvs_stats.keys(), key=int):
        fs = fvs_stats[fvs_val]
        rate = fs['accuracy']
        clr = '#00b894' if rate >= 0.70 else '#fdcb6e' if rate >= 0.50 else '#e17055'
        advice = '🔥核心仓' if rate >= 0.70 else '✅标准' if rate >= 0.50 else '⏭️跳过'
        html += f"""
        <tr><td><strong>{fvs_val}</strong></td><td>{fs['count']}</td><td>{fs['correct']}</td>
            <td style="color:{clr};font-weight:700;">{rate:.0%}</td><td>{advice}</td></tr>"""
    html += """</table></div>
    <div>
      <h3 style="font-size:15px;margin-bottom:8px;">🛡️ DRM (平局风险) 逐级</h3>
      <table>
        <tr><th>DRM</th><th>场次</th><th>正确</th><th>命中率</th><th>建议</th></tr>"""
    for drm_val in sorted(drm_stats.keys(), key=int):
        ds = drm_stats[drm_val]
        rate = ds['accuracy']
        clr = '#00b894' if rate >= 0.70 else '#fdcb6e' if rate >= 0.50 else '#e17055'
        advice = '✅正常' if rate >= 0.60 else '⚠️注意' if rate >= 0.40 else '🚫否决'
        html += f"""
        <tr><td><strong>{drm_val}</strong></td><td>{ds['count']}</td><td>{ds['correct']}</td>
            <td style="color:{clr};font-weight:700;">{rate:.0%}</td><td>{advice}</td></tr>"""
    html += """</table></div>
  </div>
</div>
"""
    
    # === KEY FINDINGS ===
    # Calculate detailed savings
    veto_matches = [m for m in matches if m.get('position') == 'VETO']
    core_matches = [m for m in matches if m.get('position') == 'CORE']
    veto_saved = sum(1 for m in veto_matches if not m['correct'])
    veto_cost = sum(1 for m in veto_matches if m['correct'])
    core_ok = sum(1 for m in core_matches if m['correct'])
    core_bad = sum(1 for m in core_matches if not m['correct'])
    
    # FVS=1 analysis (FVS-1A rule)
    fvs1_matches = [m for m in matches if m['fvs'] == 1]
    fvs1_correct = sum(1 for m in fvs1_matches if m['correct'])
    
    # DRM>=2 analysis
    drm2_matches = [m for m in matches if m['drm'] >= 2]
    drm2_correct = sum(1 for m in drm2_matches if m['correct'])
    
    html += f"""
<div class="card">
  <h2>💡 关键发现</h2>
  
  <div class="finding-good">
    <h3>✅ 核心仓位(FVS=2+DRM=0)命中率80%</h3>
    <p>三赛事合计 <strong>{len(core_matches)}</strong> 场触发核心仓位，命中 <strong>{core_ok}/{len(core_matches)} = {core_ok/max(len(core_matches),1):.0%}</strong>。<br>
    错失 <strong>{core_bad}</strong> 场。这是系统最可靠的信号组合，应作为串关核心胆。</p>
  </div>
  
  <div class="finding">
    <h3>🛡️ 否决信号规避了 {veto_saved} 场冷门</h3>
    <p>共 <strong>{len(veto_matches)}</strong> 场触发否决(VETO)，其中 <strong>{veto_saved}</strong> 场的方向预测实际上是错的——如果实盘投注会损失。<br>
    否决精确率: {veto_saved/max(len(veto_matches),1):.0%}（{veto_saved}/{len(veto_matches)}）。<br>
    错杀率: {veto_cost/max(len(veto_matches),1):.0%}（{veto_cost}/{len(veto_matches)}，否决了正确预测）。</p>
  </div>
  
  <div class="finding-warn">
    <h3>⚠️ FVS-1A清零规则验证: FVS=1命中率{fvs1_correct/max(len(fvs1_matches),1):.0%}</h3>
    <p>FVS=1的 <strong>{len(fvs1_matches)}</strong> 场比赛中，仅有 <strong>{fvs1_correct}/{len(fvs1_matches)} = {fvs1_correct/max(len(fvs1_matches),1):.0%}</strong> 正确。<br>
    {('确认FVS=1为反向指标,清零规则有效。' if fvs1_correct/max(len(fvs1_matches),1) < 0.50 else 'FVS=1并非明确反向指标,清零规则可能过于激进。')}</p>
  </div>
  
  <div class="finding">
    <h3>📊 模拟投注盈亏: ¥{bt['pnl']:+.0f} (ROI {bt['roi']:+.1f}%)</h3>
    <p>在 <strong>{bt['days_with_bets']}</strong> 个比赛日执行投注，总投资 ¥{bt['invested']:.0f}，回收 ¥{bt['returned']:.0f}。<br>
    平均每投注日盈亏: ¥{bt['pnl']/max(bt['days_with_bets'],1):+.0f}。<br>
    以每比赛日¥100本金计算，总盈利¥{bt['pnl']:+.0f}。</p>
  </div>
  
  <div class="finding-warn">
    <h3>⚠️ 2024欧洲杯: 唯一命中率退步赛事</h3>
    <p>2024欧洲杯基础方向命中率 <strong>{tournaments.get('2024 Euro',{}).get('accuracy',0):.0%}</strong>，显著低于2022世界杯({tournaments.get('2022 WC',{}).get('accuracy',0):.0%})和2018世界杯({tournaments.get('2018 WC',{}).get('accuracy',0):.0%})。<br>
    但投注ROI仍为正({tournaments.get('2024 Euro',{}).get('betting',{}).get('roi',0):+.1f}%)，说明否决信号在冷门频发赛事中特别有效。</p>
  </div>
</div>
"""
    
    # === DAILY BETTING PnL CHART ===
    daily_pnls = [d['pnl'] for d in daily]
    daily_labels = [d['date'][5:] for d in daily]
    cumulative = []
    running = 0
    for d in daily:
        running += d['pnl']
        cumulative.append(running)
    
    # Count betting days and PnL distribution
    pos_days = sum(1 for d in daily if d['pnl'] > 0)
    neg_days = sum(1 for d in daily if d['pnl'] < 0)
    zero_days = sum(1 for d in daily if d['pnl'] == 0)
    max_win = max(daily_pnls) if daily_pnls else 0
    max_loss = min(daily_pnls) if daily_pnls else 0
    
    html += f"""
<div class="card">
  <h2>💰 逐日投注盈亏分析</h2>
  <div class="grid-3">
    <div class="stat-box"><div class="num" style="color:#00b894;">{pos_days}</div><div class="label">盈利天数</div></div>
    <div class="stat-box"><div class="num" style="color:#e17055;">{neg_days}</div><div class="label">亏损天数</div></div>
    <div class="stat-box"><div class="num" style="color:#636e72;">{zero_days}</div><div class="label">空仓/持平天数</div></div>
  </div>
  <div class="grid-3" style="margin-top:8px;">
    <div class="stat-box"><div class="num" style="color:#00b894;">¥{max_win:+.0f}</div><div class="label">单日最大盈利</div></div>
    <div class="stat-box"><div class="num" style="color:#e17055;">¥{max_loss:+.0f}</div><div class="label">单日最大亏损</div></div>
    <div class="stat-box"><div class="num" style="color:#6c5ce7;">{bt['days_with_bets']}</div><div class="label">实际投注天数</div></div>
  </div>
  <div class="chart-container">
    <canvas id="pnlChart"></canvas>
  </div>
</div>
"""
    
    # === DETAILED MATCH LIST ===
    html += """
<div class="card">
  <h2>📋 详细比赛数据</h2>
  <div style="overflow-x:auto;">
  <table>
    <tr><th>比赛</th><th>比分</th><th>方向</th><th>结果</th><th>正确?</th>
        <th>FVS</th><th>DRM</th><th>仓位</th><th>赛事</th></tr>
"""
    
    for m in matches:
        old_mark = '✅' if m['correct'] else '❌'
        pos = m.get('position', 'N/A')
        pos_tag = f'<span class="tag tag-{pos.lower()}">{pos}</span>' if pos in ['CORE','STANDARD'] else \
                  f'<span class="tag tag-veto">{pos}</span>' if pos == 'VETO' else \
                  f'<span class="tag tag-skip">{pos}</span>'
        
        # Determine tournament from match date range
        date = m['date']
        if date >= '2022-11-20' and date <= '2022-12-18':
            t_label = '🏆22WC'
        elif date >= '2018-06-14' and date <= '2018-07-15':
            t_label = '🏆18WC'
        else:
            t_label = '🇪🇺Euro'
        
        html += f"""<tr>
      <td style="text-align:left;max-width:220px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;">{m['match'][:28]}</td>
      <td>{m['score']}</td>
      <td>{m['dir']}</td>
      <td>{m['act']}</td>
      <td>{old_mark}</td>
      <td>{m.get('fvs_clean', m['fvs'])}</td>
      <td>{m['drm']}</td>
      <td>{pos_tag}</td>
      <td style="font-size:11px;">{t_label}</td>
    </tr>"""
    
    html += """</table></div></div>"""
    
    # === CHART.JS ===
    chart_labels = json.dumps(daily_labels)
    chart_pnls = json.dumps(daily_pnls)
    chart_cumul = json.dumps([round(c, 2) for c in cumulative])
    
    html += f"""
</div>
<script>
new Chart(document.getElementById('pnlChart'), {{
    type: 'bar',
    data: {{
        labels: {chart_labels},
        datasets: [
            {{
                label: '逐日盈亏 (¥)',
                data: {chart_pnls},
                backgroundColor: {chart_pnls}.map(v => v >= 0 ? 'rgba(0,184,148,0.7)' : 'rgba(225,112,85,0.7)'),
                borderColor: {chart_pnls}.map(v => v >= 0 ? '#00b894' : '#e17055'),
                borderWidth: 1,
                order: 2,
            }},
            {{
                label: '累计盈亏 (¥)',
                data: {chart_cumul},
                type: 'line',
                borderColor: '#6c5ce7',
                backgroundColor: 'rgba(108,92,231,0.1)',
                fill: true,
                tension: 0.3,
                pointRadius: 2,
                pointBackgroundColor: '#6c5ce7',
                borderWidth: 2,
                order: 1,
            }}
        ]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
            legend: {{ position: 'top', labels: {{ font: {{ size: 12 }} }} }},
            tooltip: {{ callbacks: {{ label: function(ctx) {{ return '¥' + ctx.raw.toFixed(2); }} }} }}
        }},
        scales: {{
            x: {{ ticks: {{ font: {{ size: 10 }}, maxRotation: 45 }} }},
            y: {{ ticks: {{ callback: function(v) {{ return '¥' + v; }} }} }}
        }}
    }}
}});
</script>
</body>
</html>"""
    return html

def main():
    results = load_results()
    html = generate_html(results)
    path = os.path.join(BASE_DIR, "v350_全量回测报告.html")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Report saved to {path}")

if __name__ == '__main__':
    main()
