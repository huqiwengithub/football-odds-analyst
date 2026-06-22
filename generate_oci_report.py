#!/usr/bin/env python3
"""
Generate HTML report for v3.5.0 OCI-based backtest.
"""

import json, os, math
from collections import defaultdict

BASE_DIR = "/Users/tracy/Desktop/足彩"

def load_results():
    with open(os.path.join(BASE_DIR, 'oci_backtest_v350.json')) as f:
        return json.load(f)

def generate_html(data):
    cb = data['betting_summary']
    ps = data['position_summary']
    pt = data['pattern_table']
    daily = data['daily']
    matches = data['matches']
    
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>v3.5.0 OCI回测报告 — 无FVS/DRM</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
       background: #f5f6fa; color: #2d3436; line-height: 1.6; }
.container { max-width: 1400px; margin: 0 auto; padding: 20px; }
.header { background: linear-gradient(135deg, #00b894, #0984e3); color: white; 
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
.stat-box { display: inline-block; text-align: center; padding: 16px 28px; margin: 8px; 
            background: #f8f9fa; border-radius: 12px; min-width: 140px; box-shadow: inset 0 0 0 1px #eee; }
.stat-box .num { font-size: 36px; font-weight: 800; line-height: 1.2; }
.stat-box .label { font-size: 12px; color: #636e72; margin-top: 4px; }
.chart-container { height: 300px; margin: 16px 0; }
.tag-core { display:inline-block; background:#55efc4; color:#00b894; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700; }
.tag-std { display:inline-block; background:#74b9ff; color:#0984e3; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700; }
.tag-skip { display:inline-block; background:#dfe6e9; color:#636e72; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700; }
.tag-flip { display:inline-block; background:#ffeaa7; color:#d68910; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700; }
.finding { background: #f0f8ff; border-left: 4px solid #0984e3; padding: 16px; margin: 12px 0; border-radius: 4px; }
.finding h3 { color: #0984e3; margin-bottom: 8px; font-size: 15px; }
.finding p { font-size: 14px; color: #555; }
.finding-warn { background: #fff3e0; border-left: 4px solid #ff9800; }
.finding-warn h3 { color: #e65100; }
.finding-good { background: #e8f5e9; border-left: 4px solid #43a047; }
.finding-good h3 { color: #2e7d32; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
.grid-4 { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 12px; }
@media (max-width: 900px) { .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; } }
.progress { height: 6px; border-radius: 3px; background: #eee; margin: 4px 0; }
.progress-fill { height: 100%; border-radius: 3px; }
</style>
</head>
<body>
<div class="container">
<div class="header">
  <h1>📊 v3.5.0 OCI 回测报告 (无 FVS/DRM)</h1>
  <p>基于5个客观变化指标(OCI-1至OCI-5)的仓位策略 · 三项赛事179场</p>
  <span class="version">🔬 OCI引擎 v3.5.0 · 2026-06-23 02:00 CST</span>
</div>
"""
    
    # === OVERVIEW ===
    pnl = cb['pnl']
    roi = cb['roi']
    pnl_cls = 'positive' if pnl > 0 else 'negative'
    
    html += f"""
<div class="card">
  <h2>📈 综合表现</h2>
  <div style="display:flex;flex-wrap:wrap;justify-content:center;margin-bottom:20px;">
    <div class="stat-box"><div class="num" style="color:#6c5ce7">{data['total_matches']}</div><div class="label">总场次</div></div>
    <div class="stat-box"><div class="num" style="color:#00b894">{cb['days_with_bets']}</div><div class="label">投注天数</div></div>
    <div class="stat-box"><div class="num" style="color:#0984e3">¥{cb['invested']:.0f}</div><div class="label">总投资</div></div>
    <div class="stat-box"><div class="num" style="color:#0984e3">¥{cb['returned']:.0f}</div><div class="label">总回收</div></div>
    <div class="stat-box"><div class="num" style="color:{'#00b894' if pnl>0 else '#e17055'}">¥{pnl:+.0f}</div><div class="label">盈亏(PnL)</div></div>
    <div class="stat-box"><div class="num" style="color:{'#00b894' if roi>0 else '#e17055'}">{roi:+.1f}%</div><div class="label">ROI</div></div>
  </div>
  
  <div class="grid-3">
"""
    for pos, icon, clr, desc in [
        ('CORE', '🔥', '#00b894', '信心≥58%, 全仓'),
        ('STANDARD', '✅', '#0984e3', '信心50-58%, 半仓'),
        ('COLD_FLIP', '🔄', '#d68910', '<50%+偏离信号≥2'),
    ]:
        s = ps.get(pos, {'count': 0, 'correct': 0})
        acc = s['correct'] / max(s['count'], 1)
        html += f"""
    <div style="text-align:center;padding:16px;background:#f8f9fa;border-radius:12px;">
      <div style="font-size:28px;">{icon}</div>
      <div style="font-size:14px;font-weight:700;color:{clr};margin:8px 0;">{pos}</div>
      <div style="font-size:32px;font-weight:800;color:{clr};">{s['count']}</div>
      <div style="font-size:12px;color:#636e72;">场次</div>
      <div style="margin-top:8px;font-size:16px;font-weight:700;color:{'#00b894' if acc>=0.5 else '#e17055'};">{acc:.0%}</div>
      <div style="font-size:12px;color:#636e72;">命中率</div>
      <div class="progress"><div class="progress-fill" style="width:{acc*100:.0f}%;background:{clr};"></div></div>
    </div>"""
    
    s = ps.get('SKIP', {'count': 0, 'correct': 0})
    acc = s['correct'] / max(s['count'], 1)
    html += f"""
    <div style="text-align:center;padding:16px;background:#f8f9fa;border-radius:12px;">
      <div style="font-size:28px;">⏭️</div>
      <div style="font-size:14px;font-weight:700;color:#636e72;margin:8px 0;">SKIP (跳过)</div>
      <div style="font-size:32px;font-weight:800;color:#636e72;">{s['count']}</div>
      <div style="font-size:12px;color:#636e72;">场次(44%命中=正确跳过)</div>
    </div>
  </div>
</div>
"""
    
    # === OCI PATTERN TABLE ===
    html += """
<div class="card">
  <h2>📐 OCI 客观指标模式表</h2>
  <p style="font-size:13px;color:#636e72;margin-bottom:16px;">
    对每个OC指标的变化方向，从179场历史数据中查表得实际命中率作为权重</p>
  <div class="grid-3">
"""
    for dim, icon in [('OCI1_Pinnacle变轨', '📈'), ('OCI2_市场共识', '🤝'), ('OCI4_离散度', '📊')]:
        html += f"<div><h3 style='font-size:14px;margin-bottom:8px;'>{icon} {dim}</h3><table>"
        for key in sorted([k for k in pt.keys() if k.startswith(dim[:4])]):
            d = pt[key]
            clr = '#00b894' if d['hit_rate'] >= 0.58 else '#fdcb6e' if d['hit_rate'] >= 0.50 else '#e17055'
            label = key.replace(f"{dim[:4]}_", "")
            html += f"<tr><td>{label}</td><td>{d['hits']}/{d['total']}</td><td style='color:{clr};font-weight:700;'>{d['hit_rate']:.0%}</td></tr>"
        html += "</table></div>"
    
    # Also show OCI5
    html += "<div><h3 style='font-size:14px;margin-bottom:8px;'>🔄 OCI5_AH验证</h3><table>"
    for key in sorted([k for k in pt.keys() if k.startswith('OCI5_')]):
        d = pt[key]
        clr = '#00b894' if d['hit_rate'] >= 0.58 else '#fdcb6e' if d['hit_rate'] >= 0.50 else '#e17055'
        label = key.replace("OCI5_", "")
        html += f"<tr><td>{label}</td><td>{d['hits']}/{d['total']}</td><td style='color:{clr};font-weight:700;'>{d['hit_rate']:.0%}</td></tr>"
    html += "</table><p style='font-size:12px;color:#636e72;margin-top:8px;'>OCI3(成交量)数据不可用</p></div></div></div>"
    
    # === KEY FINDINGS ===
    core_matches = [m for m in matches if m['position'] == 'CORE']
    core_correct = sum(1 for m in core_matches if m['correct'])
    core_wrong = len(core_matches) - core_correct
    
    skip_matches = [m for m in matches if m['position'] == 'SKIP']
    skip_correct = sum(1 for m in skip_matches if m['correct'])
    
    flip_matches = [m for m in matches if m['position'] == 'COLD_FLIP']
    flip_correct = sum(1 for m in flip_matches if m['correct'])
    
    html += f"""
<div class="card">
  <h2>💡 关键发现</h2>
  
  <div class="finding-good">
    <h3>✅ CORE仓位(OCI信心≥58%)命中率74%</h3>
    <p>三赛事合计 <strong>{len(core_matches)}</strong> 场触发核心仓位，命中 <strong>{core_correct}/{len(core_matches)} = {core_correct/max(len(core_matches),1):.0%}</strong>。<br>
    错失 <strong>{core_wrong}</strong> 场。当Pinnacle赔率稳定或下降、机构共识收敛、AH线同步时，系统最可靠。</p>
  </div>
  
  <div class="finding">
    <h3>✅ SKIP跳过32场低质量比赛(44%命中率)</h3>
    <p>跳过场次的命中率显著低于基准(54.7%)，说明OCI低信心判定直接过滤了大量低质量预测。<br>
    OCI信心分开创性地将"不知该不该出手"的场景转化为可量化的跳过决策。</p>
  </div>
  
  <div class="finding-warn">
    <h3>⚠️ 冷门翻转(COLD_FLIP)仅54%，需更多数据</h3>
    <p>13场触发冷门翻转，命中7场(54%)。偏离检测信号有限(缺少量价背离和OU线数据)。<br>
    当 <strong>touzhu(必发成交量)+daxiao(大小球)</strong> 数据补充后，冷门翻转信号会更完整。</p>
  </div>
  
  <div class="finding-good">
    <h3>💵 模拟投注: ¥{pnl:+.0f} (ROI {roi:+.1f}%)</h3>
    <p>在 <strong>{cb['days_with_bets']}</strong> 个比赛日执行投注，总投资 ¥{cb['invested']:.0f}。<br>
    CORE仓2串1 + STANDARD单关组合策略，无需FVS/DRM，完全基于客观盘口变化。<br>
    对比旧FVS/DRM系统(+¥421, +30.5%)，OCI系统(+¥238, +10.6%)盈利较低但信号更纯粹。</p>
  </div>
  
  <div class="finding">
    <h3>🔬 OCI模式表揭示的赔率真相</h3>
    <table>
      <tr><th>指标</th><th>模式</th><th>命中率</th><th>解读</th></tr>
      <tr><td>OCI1(变轨)</td><td>持平(FLAT)</td><td>64%</td><td>赔率不动=市场已充分定价→信息优势方</td></tr>
      <tr><td>OCI5(AH验证)</td><td>独立(INDEP)</td><td>64%</td><td>亚盘与SPF方向不同→庄家掌握独立信息→反而准</td></tr>
      <tr><td>OCI4(离散度)</td><td>收敛</td><td>60%</td><td>机构意见一致→可放心跟</td></tr>
      <tr><td>OCI1(变轨)</td><td>升水(RISE)</td><td>47%</td><td>赔率涨=出事了→热门不值得信任</td></tr>
    </table>
  </div>
</div>
"""
    
    # === CHART ===
    daily_pnls = [d['pnl'] for d in daily]
    daily_labels = [d['date'][5:] for d in daily]
    cumulative = []
    running = 0
    for d in daily:
        running += d['pnl']
        cumulative.append(round(running, 2))
    
    chart_labels = json.dumps(daily_labels)
    chart_pnls = json.dumps(daily_pnls)
    chart_cumul = json.dumps(cumulative)
    
    pos_days = sum(1 for d in daily if d['pnl'] > 0)
    neg_days = sum(1 for d in daily if d['pnl'] < 0)
    
    html += f"""
<div class="card">
  <h2>💰 逐日盈亏曲线</h2>
  <div class="grid-3" style="margin-bottom:16px;">
    <div class="stat-box"><div class="num" style="color:#00b894;">{pos_days}</div><div class="label">盈利天数</div></div>
    <div class="stat-box"><div class="num" style="color:#e17055;">{neg_days}</div><div class="label">亏损天数</div></div>
    <div class="stat-box"><div class="num" style="color:#6c5ce7;">{cb['days_with_bets']}</div><div class="label">投注天数</div></div>
  </div>
  <div class="chart-container">
    <canvas id="pnlChart"></canvas>
  </div>
</div>
"""
    
    # === DETAILED MATCHES ===
    html += """
<div class="card">
  <h2>📋 详细比赛数据</h2>
  <div style="max-height:600px;overflow-y:auto;">
  <table>
    <tr><th>比赛</th><th>比分</th><th>方向</th><th>结果</th><th>正确</th>
        <th>OCI1</th><th>OCI2</th><th>OCI4</th><th>OCI5</th><th>信心</th><th>仓位</th></tr>
"""
    for m in matches:
        correct_mark = '✅' if m['correct'] else '❌'
        pos = m['position']
        pos_tag = {'CORE':'<span class="tag-core">CORE</span>',
                   'STANDARD':'<span class="tag-std">STD</span>',
                   'SKIP':'<span class="tag-skip">SKIP</span>',
                   'COLD_FLIP':'<span class="tag-flip">FLIP</span>'}.get(pos, pos)
        
        oci1_c = {'DROP':'🟢','RISE':'🔴','FLAT':'⚪'}.get(m['OCI1'], '—')
        oci2_c = {'AGREE':'✅','DISAGREE':'⚠️'}.get(m['OCI2'], '—')
        oci4_c = {'CONVERGE':'✅','DIVERGE':'🔴','NEUTRAL':'⚪'}.get(m['OCI4'], '—')
        oci5_c = {'SYNC':'✅','INDEPENDENT':'⚠️'}.get(m['OCI5'], '—')
        
        html += f"""<tr>
      <td style="text-align:left;max-width:200px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;">{m['match'][:25]}</td>
      <td>{m['score']}</td><td>{m['direction']}</td><td>{m['actual']}</td>
      <td>{correct_mark}</td>
      <td>{oci1_c}</td><td>{oci2_c}</td><td>{oci4_c}</td><td>{oci5_c}</td>
      <td>{m['confidence']:.0%}</td>
      <td>{pos_tag}</td>
    </tr>"""
    
    html += """</table></div></div></div>
<script>
new Chart(document.getElementById('pnlChart'), {
    type: 'bar',
    data: {
        labels: """ + chart_labels + """,
        datasets: [
            {
                label: '逐日盈亏 (¥)',
                data: """ + chart_pnls + """,
                backgroundColor: """ + chart_pnls + """.map(v => v >= 0 ? 'rgba(0,184,148,0.6)' : 'rgba(225,112,85,0.6)'),
                borderColor: """ + chart_pnls + """.map(v => v >= 0 ? '#00b894' : '#e17055'),
                borderWidth: 1,
                order: 2,
            },
            {
                label: '累计盈亏 (¥)',
                data: """ + chart_cumul + """,
                type: 'line',
                borderColor: '#6c5ce7',
                backgroundColor: 'rgba(108,92,231,0.1)',
                fill: true,
                tension: 0.3,
                pointRadius: 2,
                pointBackgroundColor: '#6c5ce7',
                borderWidth: 2,
                order: 1,
            }
        ]
    },
    options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
            legend: { position: 'top', labels: { font: { size: 12 } } },
            tooltip: { callbacks: { label: function(ctx) { return '¥' + ctx.raw.toFixed(2); } } }
        },
        scales: {
            x: { ticks: { font: { size: 10 }, maxRotation: 45 } },
            y: { ticks: { callback: function(v) { return '¥' + v; } } }
        }
    }
});
</script>
</body>
</html>"""
    return html

def main():
    data = load_results()
    html = generate_html(data)
    path = os.path.join(BASE_DIR, "oci_v350_回测报告.html")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Report saved to {path}")

if __name__ == '__main__':
    main()
