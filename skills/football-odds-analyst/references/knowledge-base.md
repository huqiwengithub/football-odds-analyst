# Knowledge Base Reference — Football Odds Analyst v3.5.3: OCI客观指标体系

> **Load trigger**: Read this file when SKILL.md instructs you to reference a specific section ($KB-N). Contains all detailed rules, formulas, trap definitions, scoring criteria, and methodology.
>
> **Reading strategy**: Start with KB-16 (OCI客观指标) + KB-18 (仓位决策 — 见betting-sop.md) — v3.5.3核心. Then KB-6 + KB-7 for Step 10. KB-2 + KB-4 for traps/scoring. KB-10 for MBI.
>
> **赛前对照检查**: 赛后回测复盘统一使用 `football-backtest-workflow/` 子技能（详见 SKILL.md Step 13）。赛前无需手动检查观察项。

---

## KB-0: Pre-Flight — Team Names + Verification

### Team Name Verification Protocol
```
1. For each team from fixtures: check static map → FOUND? ✅
2. NOT found → WebSearch "[Team] Chinese name football national team"
3. STILL not found → use English + ⚠️ red marker in output
4. World Cup: ALWAYS WebSearch "2026 World Cup teams Chinese name list"
5. If ANY fallback used → set {{NAME_ERROR_ACTIVE}} = active in HTML report
```

### Static Chinese Name Map
```
Switzerland=瑞士, Korea Republic=韩国, Bosnia and Herzegovina=波黑, Japan=日本,
Czechia=捷克, South Africa=南非, Canada=加拿大, Qatar=卡塔尔, Mexico=墨西哥,
Brazil=巴西, Argentina=阿根廷, France=法国, Germany=德国, England=英格兰,
Spain=西班牙, Portugal=葡萄牙, Italy=意大利, Netherlands=荷兰, Croatia=克罗地亚,
Uruguay=乌拉圭, Belgium=比利时, Colombia=哥伦比亚, USA=美国, Morocco=摩洛哥,
Australia=澳大利亚, Iran=伊朗, New Zealand=新西兰, Sweden=瑞典, Ivory Coast=科特迪瓦,
Ecuador=厄瓜多尔, Curacao=库拉索, Tunisia=突尼斯, Denmark=丹麦, Norway=挪威,
Poland=波兰, Senegal=塞内加尔, Egypt=埃及, Nigeria=尼日利亚, Ghana=加纳,
Costa Rica=哥斯达黎加, Panama=巴拿马, Jamaica=牙买加, Serbia=塞尔维亚,
Austria=奥地利, Ukraine=乌克兰, Turkey=土耳其, Greece=希腊, Scotland=苏格兰
```

---

## KB-1: Core Math & Conversion

### De-vig Methods

Use Shin de-vigging algorithm. Simple proportional method systematically overestimates favorite probabilities (favorite-longshot bias widens as odds gap grows).

```
Shin's method:
  Minimize |Σ(1 / (z + (1-z) × odds_i)) − 1| over z ∈ [0, 1)
  where z = proportion of insider trading in market (Shin parameter)
  
  De-vigged prob_i = (1 − z) / (odds_i − z × odds_i + z)

Practical approximation (sufficient for most matches):
  z ≈ max(0, (overround_simple − 1) / 2)
  Then: prob_i = (1 − z) / ((1 − z) × odds_i + z)
```

**Fallback**: If Shin computation not feasible, use proportional method with bias correction:
```
proportional_prob = (1/odds) / overround
bias_correction = −(proportional_prob − 0.33) × 0.05  // −5% for heavy fav, +5% for underdog
corrected = proportional_prob + bias_correction
```

### Logit-space Correction

Apply all corrections in logit space (not probability space):

```
Step 1: De-vig → base probability P
Step 2: Convert to logit space
  logit(P) = ln(P / (1 − P))
  
Step 3: Apply all corrections in logit space
  logit' = logit + Σ(Δlogit_i)
  where Δlogit_i is the logit offset for each correction factor

Step 4: Convert back to probability
  P' = 1 / (1 + e^(−logit'))

Step 5: Normalize across H/D/A
  P_final[i] = P'[i] / Σ(P')
```

| Logit Δ | Corresponding Probability Shift (centered at 50%) | Typical Signal |
|:---:|:---|:---|
| +0.10 | +2.5pp | Weak positive signal |
| +0.20 | +5.0pp | Medium positive signal |
| +0.40 | +10.0pp | Strong positive signal |
| +0.70 | +17.0pp | Extremely strong positive (multi-confirmation only) |

**logit space advantages**: Probabilities are naturally bounded (0,1), equivalent to Bayesian updating, correction magnitude auto-compresses near extreme probabilities.

### Fundamental formulas
```
Overround (vig) = 1/home_price + 1/draw_price + 1/away_price
Payout rate = 1 / overround

Dampening for correlated factors:
  if factor_A and factor_B are in same signal group:
    combined = max(Δ_A, Δ_B) + 0.3 × min(Δ_A, Δ_B)
```

### Euro→Asian Conversion Table
```
Pinnacle 1X2 home → AH line:
  1.38–1.48 → -1.00 to -1.50    1.48–1.58 → -0.75 to -1.00
  1.58–1.72 → -0.50 to -0.75    1.72–1.90 → -0.25 to -0.50
  1.90–2.10 →  0.00 to -0.25    2.10–2.40 → +0.00 to +0.25
  2.40–2.80 → +0.25 to +0.50    2.80–3.30 → +0.50 to +0.75
  3.30–4.00 → +0.75 to +1.00    4.00–5.00 → +1.00 to +1.50
Formula: theoretical_ah = (deVigProb_home − 0.50) × 4
```

---

## KB-2: Fifteen Euro-Asian Divergence Traps

> A/B/C三层分类：C=信息型 / B=诱导型 / A=仓位型。分类加权判定替代原计数阈值。

| # | Pattern | Category | Trigger | Risk |
|:--:|---------|:--------:|---------|------|
| 1 | Deep odds, shallow handicap | **C** | Gap ≥0.25 ball, theoretical AH deeper than actual | Draw/away upset |
| 2 | Shallow odds, deep handicap | **C** | Gap ≥0.25 ball, actual deeper than theoretical + SBOBet water >1.00 | Straight outcome |
| 3 | Draw odds dropping + deep handicap | **C** | Draw odds ↓ ≥8% from open + AH ≥0.25 deeper than theoretical | Hidden draw |
| 4 | Late odds drop + handicap retreat | **B** | Home odds ↓ ≥5% in last 6h + AH retreats ≥0.25 (opposite direction) | Fake news / 庄家反向诱导 |
| 5 | Favorite deep handicap + water >1.05 | **A** | AH ≥0.75 ball + SBOBet water ≥1.05 at close | 仓位压力, passive |
| 6 | Underdog drops for no reason | **C** | Underdog odds ↓ ≥10% + ZERO fundamental support (WebSearch verified) | Minimal reference value |
| 7 | Narrative-driven moderate compression | **B** | Compression 5–15% + draw true prob >25% + driver is "known news" | 庄家借叙事钓鱼 |
| 8 | Same-direction compression + AH static | **A** | Home odds ↓ ≥5% + AH unchanged | 仓位型，被动调价 |
| 9 | Opposite-direction odds vs AH | **C** | 1X2 moves one way, AH opposite | Strong trap |
| 10 | SBOBet diverges from Pinnacle | **C** | SBOBet AH deviates ≥0.25 from Pinnacle | Asian sharp disagrees |
| 11 | bet365 limit crash | **A** | bet365 limit drops >30% in 2h, odds unchanged | Risk aversion (仓位管理) |
| 12 | Opening line extreme | **B** | Opening AH ≥1.5 balls | 庄家刻意制造"危险"假象 |
| 13 | Illegal betting site manipulation 🚩 | **C** | Unregulated bookmaker >0.15 from Pinnacle + limit drops >50% + market suspended (≥2 signs) | RED FLAG — skip |
| 14 | Three-bookmaker consensus break | **C** | All 3 diverge ≥0.25 on same market | Systemic uncertainty |
| 15 | Referee-driven odds shift | **C** | Referee >0.35 penalties/game or >5.0 cards/game + physical team | Adjust OU ±0.25 |

### 分类加权规则

```
C 类陷阱（信息型 — 赔率方向与基本面不一致）:
  每条触发 → logit ±0.25（方向与陷阱指示相反）
  多条 C 类共振 → 信度 × 0.70，标记为 🔴 高严重度

B 类陷阱（诱导型 — 庄家刻意制造"危险信号"）:
  每条触发 → 不降信度，但标记为 ⚠️ 疑似诱导
  需成交量交叉验证: 无量配合 → 确认为诱导 → logit +0.15（强化原方向）
                   有量配合 → 转为 C 类处理
  多条 B 类共振且无量 → logit +0.25（庄家在反向操作）

A 类陷阱（仓位型 — 被动调价，与基本面无关）:
  每条触发 → 不产生 logit 修正
  仅作为上下文标注: "此变动为仓位驱动，非信息信号"
```

Each HIT → Category-based correction (see above).

---

## KB-3: Twenty-Eight Universal Trap Rules

> A/B/C分类加权规则同 KB-2。

```
[C]  1: Odds drop ≥8% without fundamentals → trap
[A]  2: Deep open (AH ≥1.0) + never retreat in 24h → true signal (仓位型，市场坚定)
[C]  3: Opening shallow (gap ≥0.25) + paper strength clear → upset warning
[A]  4: Same-direction multi-bookmaker → weight ×1.5 (仓位共振≠信息共振)
[A]  5: Pinnacle leads movement (>5 min ahead of others) → real signal (需量确认是否为仓位驱动)
[A]  6: Random single-bookmaker deviation ≥0.10 → ignore
[B]  7: Late odds + AH both reverse in last 2h → trap (庄家反向操作)
[B]  8: Odds ↓ ≥5% + AH retreats ≥0.25 → trap (诱导型)
[C]  9: bet365 moves opposite Pinnacle → retail-sharp conflict
[A] 10: Odds static (σ<0.03) + water volatile (σ>0.08) → indecision (仓位拉锯)
[B] 11: Narrative compression 5–15% → market overreacting (诱导型，借叙事)
[C] 12: Suspension paradox → suspended teams play MORE defensive
[C] 13: Illegal betting site — match 2+ red flags → SKIP (see KB-2 Trap #13)
[C] 14: Referee influence → adjust expectations (see KB-2 Trap #15)
[A] 15: No fundamental event → movement is noise
[C] 16: 1X2 odds drop → verify AH direction match
[C] 17: Three-bookmaker consensus strong (≤0.15 ball) → high confidence
[C] 18: deVigProb(home) >75% → unusual; check narrative
[C] 19: deVigProb(draw) >30% → market uncertain; expect draw risk
[C] 20: deVigProb(away) >40% → strong away signal; verify AH
[B] 21: Extreme compression >15% → overreaction (庄家造势)
[C] 22: 1X2 spread across 3 bookmakers >0.30 → uncertainty penalty
[C] 23: AH spread across 3 bookmakers >0.50 → high divergence
[C] 24: Both teams WC debut → draw prob floor 28%
[A] 25: Same-direction water rise >0.15 on all 3 → genuine flow (仓位型)
[C] 26: Favorite odds <1.25 → lay risk; max confidence 80%
[C] 27: Defensive fortress (qualifying GA<0.5 or 5+ clean sheets) → +3% direction, +15% under
[C] 28: Heat discount (>35°C or humidity >80%) → fade favorite; underdog +5% prob
```

---

## KB-4: Six-Dimension Scoring (0–1 Continuous)

> Binary→连续评分，重叠维度(D2/D6)合并，满分惩罚→权重重新校准。

### Scoring Dimensions

| Dim | Criterion | Score 0.0 (worst) | Score 1.0 (best) | Interpolation |
|:---:|-----------|-------------------|-------------------|:---|
| **D1** | Fundamental logic | Fundamentals contradict market | Perfect alignment: injuries/form/H2H all agree | Linear by # of aligned sub-factors ÷ total |
| **D2** | Market consensus (MERGE old D2+D6) | AH gap >0.50 OR DRI >60 OR >2 books diverge | AH gap ≤0.15 AND DRI <20 AND all books within 0.10 spread | 1 − (gap/0.50 + DRI_norm/2 + spread_norm)/3 |
| **D3** | Opening objectivity | Opening ≥0.50 ball from fair value OR compressed by "known news" | Opening within 0.15 ball of fair value AND no narrative compression | 1 − deviation/0.50 |
| **D4** | Late movement clean | ≥3 traps triggered OR harvest pattern detected | 0 traps + late 1h passes authenticity rules | 1 − traps_hit/4 |
| **D5** | Water & draw logic | Water σ >0.08 OR draw prob >30% with fav<2.00 | Water σ<0.04 AND draw prob≤22% AND water changes explainable | mean of (1−σ/0.08, 1−draw/0.30) |
| — | ~~D6 removed~~ | Merged into D2. Old D6 measured "no one-sided hype" = same as consensus | — | — |

### Continuous Score Formula

```
Per dimension:
  score_i = clamp(mapped_value, 0.0, 1.0)

Total = Σ(score_i × weight_i) / Σ(weight_i)

Default weights :
  D1: 0.25  D2: 0.25  D3: 0.15  D4: 0.15  D5: 0.20
  (Total = 5 dimensions, no D6)

Final 6D Score = Total × 6  (scale to traditional 0-6 range for legacy compatibility)
```

### Application

```
6D ≥ 4.5 (legacy scale) → direction confidence +3%
6D 3.0–4.5 → no adjustment
6D 2.0–3.0 → confidence −3%, ⚠️ low confidence warning
6D < 2.0 → skip match entirely (auto-degrade)
```

### Inflation Penalty (已替换)

**Old rule** (6/6→5) has been removed. That phenomenon indicates model calibration bias, not "perfect score is untrustworthy." Resolution:
- Recalibrate dimension weights via historical backtest
- If a dimension negatively correlates with outcome → flip or delete that dimension
- Pending 500+ match backtest

### Dimension Overlap Resolution
| D1(D3)同向→×0.8 | D4触发→D2 floor=0.3 | D2+D6已合并 |

### Minimum Data Requirements

```
D1: requires shuju page (H2H + recent form) → if missing, D1 = 0.5 (neutral)
D2: requires ouzhi + yazhi pages → if missing, skip scoring entirely
D3: requires yazhi opening handicap → if missing, D3 = 0.5
D4: requires yazhi change timestamps → if missing, D4 = 0.5
D5: requires yazhi water data → if missing, D5 = 0.5
```

---

## KB-5: Fundamental Factor Weights

| Factor | Weight | Data Source |
|--------|:------:|-------------|
| Squad quality gap | 30% | FIFA rank + market value |
| Defensive tier (incl. qualifier discount) | 20% | Clean sheets + GA vs qualifier avg |
| Winless inertia (≥6 match streak → +8%) | 15% | 3-match form |
| Motivation (elimination, debut, long-absence) | 15% | Group context |
| Home advantage | 10% | Venue + travel distance |
| Recent form (last 6) | 10% | GF/GA trend |

### Compression Intensity
| Grade | Change | Implication |
|-------|--------|-------------|
| Extreme | ≥15% drop | Real conviction or extreme narrative; verify fundamentals |
| Strong | 10–15% | Significant signal; check fundamentals |
| Moderate | 5–10% | True conviction threshold; cross-verify |
| Weak | <5% | Normal fluctuation; low value |

### Back-to-Wall Effect
- Elimination-threatened seeker → draw +5~8%, away +5%
- WC debut team → +10% motivation bonus
- Long-absence return (>8 years) → +5% motivation

---

---

## KB-5b: 平局专项信号（v3.6.2 新增，2026-06-24 诊断驱动）

> **根因**: 2026-06-16 四场全平局，系统 4 场全预测非平（100% 错误）。
> 诊断发现：系统架构上只允许输出主胜/客胜，平局从未被赋予最高置信度。
> **修复**: 平局必须与主胜/客胜平等竞争，平局专项信号必须参与方向判定。

### 平局信号强度分级

| 等级 | 触发条件（需同时满足） | 置信度调整 |
|:----:|:---|:---:|
| **强** | Pinnacle 平赔 < 3.20 且较开盘下降 ≥ 0.10<br>+ 平局离散度 ≤ 主/客离散度<br>+ 亚盘平手盘（handicap=0） | 平局置信度 +0.12 |
| **中** | Pinnacle 平赔 < 3.50 且较开盘下降<br>+ 任意 2 项（离散度低 / 平手盘 / deVig 平>28%） | 平局置信度 +0.06 |
| **弱** | Pinnacle 平赔 < 3.80<br>+ 亚盘平手盘 或 离散度收敛 | 平局置信度 +0.03 |

### 平局专项 OCI 权重（基于 179 场历史库）

| OCI 模式 | 含义 | 平局命中率 | 权重 |
|:---|:---|---:|:---:|
| OCI-4_CONVERGE + 平赔<3.50 | 机构共识平局 | 58.3% | +0.15 |
| OCI-1_DROP + OCI-4_CONVERGE | Pinnacle 降赔 + 机构共识 | 54.2% | +0.10 |
| OCI-5_SYNC + 平手盘 | 亚盘与欧赔同步指向平局 | 51.7% | +0.05 |
| OCI-4_DIVERGE | 机构分歧（平局无共识） | 38.9% | -0.10 |

### 与 Step 9 方向判定的接口

Step 9 综合信心分计算公式：

```
综合信心分(方向) = MBI评分 × 0.6 + OCI权重 × 0.3 + 陷阱调整 × 0.1

其中 陷阱调整：
  - 触发 A 类平局陷阱（信息型）→ 平局置信度 +0.08
  - 触发 B 类平局陷阱（诱导型）→ 平局置信度 -0.05
  - 触发 C 类平局陷阱（仓位型）→ 忽略（不调整）
```

### 平局方向输出条件

平局可以被输出为最终方向，当且仅当：

1. **平局综合信心分 ≥ 主胜综合信心分 且 ≥ 客胜综合信心分**
2. **平局综合信心分 ≥ 0.08**（否则降档为"跳过"）

若不满足条件 2，即使平局分数最高，仍输出次高分的主胜/客胜方向。

### 与 knowledge-base.md 其他 KB 的关系

- **KB-4（6D 评分）**: 新增 D7 维度 = 平局专项信号（权重 15%）
- **KB-10（MBI 多机构共识）**: SCS/DRI 模块需输出三方向评分，禁止只输出最低赔率方向
- **KB-16（OCI 客观指标）**: OCI-4 离散度需单独报告平局离散度
- **KB-17（DRM 平局因子）**: DRM-1（deVig 平>28%）已纳入，无需重复

---


## KB-6: Unified Logit Correction Pipeline

> 废除概率空间加法，全部迁移到 logit 空间。与 MBI 在同一管线中串行叠加，避免双轨冲突。

### 6.1 换算基准 (概率→logit)
```
+10%→+0.40 | +8%→+0.32 | +7%→+0.28 | +5%→+0.20 | +3%→+0.12
```

### 6.2 12 项校正换算为 logit 偏移

| # | Correction | Logit Δ | Condition |
|:--:|------------|:-------:|-----------|
| 1 | 欧亚陷阱 | ±0.40 | A/B/C 分类加权确定方向（C类→±0.40，B类→±0.20需量确认，A类→0） |
| 2 | 开盘定律 | ±0.32 | Any of 4 laws triggered |
| 3 | 临场真实性 | ±0.28 | Pass/fail check |
| 4 | 压缩强度 | +0.28 / +0.14 | Extreme/Strong → +0.28; Moderate → +0.14; Weak → 0 |
| 5 | 基本面一致 | ±0.20 | Weighted fundamental match |
| 6 | 背水一战 | 平 +0.20~0.32, 客 +0.20 | Seeker triggered |
| 7 | 叙事折扣 | 热门 −0.20 | Odds driven by "known news" |
| 8 | 6D 评分 | ±0.12 | ≥4→+0.12; ≤2→−0.12 |
| 9 | SBO 分歧 | ±0.12 | Asian sharp vs Pinnacle gap |
| 10 | 市场流动性 | conf × (0.85–1.00) | **后置乘数**（sigmoid 后应用，不进 logit 管线） |
| 11 | 外部因素 | xG × (1 ± penalty × 0.03) | **剥离至 KB-7**（进球倾向用，不进概率管线） |

### 6.3 组内降权规则（KB-6 内部）

**组3 — 盘口异常检测**（校正 #1 + #2 + #3，三者测同一现象）:
```
只取 max(|Δ|)，其余两项各 ×0.30
  corrected_组3 = max(|Δ₁|,|Δ₂|,|Δ₃|) × sign + 0.30 × next_largest + 0.30 × smallest
```
**组4 — 基本面/叙事**（校正 #5 + #6 + #7，信息源不同）:
```
线性叠加，不降权（信息源各自独立）
```

### 6.4 统一管线执行顺序（8 步）

```
① Shin de-vig → P_base（概率）
     ↓
② logit_base = ln(P_base / (1 − P_base))
     ↓
③ KB-6 校正（9项 logit偏移，含组3/组4降权）
   logit_ctx = logit_base + dampened_Σ(KB6_correction_i)
     ↓
④ KB-10.8 MBI 校正（6项 logit偏移，见 KB-10.8 降权规则）
   logit_final = logit_ctx + dampened_Σ(MBI_signal_i)
     ↓
⑤ 总量 cap:
   |KB6_correction_total| ≤ 0.80 logit (≈概率 ±20%)
   |MBI_total| ≤ 0.80 logit
   合计 |correction_total| ≤ 1.20 logit
   超出 → 按比例等比压缩到上限
     ↓
⑥ sigmoid: P = 1 / (1 + e^(−logit_final))
     ↓
⑦ 归一化: P_final = P / Σ(P)
     ↓
⑧ 后置乘数: conf' = conf × liquidity_factor (校正 #10)
             P_final 不变，仅压缩置信度
```

### 6.5 logit cap 数学含义

```
base 55% (logit=0.20) + cap 1.20 = logit 1.40 → sigmoid → ≈80% 主胜
  → 足球中 80% 已接近理性上限，杜绝 90%+ 虚假高置信度
```

---

## KB-7: Goal Tendency

> Poisson独立性假设不成立，精确比分预测是虚假精度。改为进球倾向三档判定。

### Base xG Flow (保留用于方向判定)
```
1. home_xG = (OU_line / 2) + (AH_line × 0.5)
   away_xG = (OU_line / 2) − (AH_line × 0.5)
2. Apply team form correction (WebSearch if available)
3. Apply external factors (KB-8 14.10 weather/travel/rest)
4. Adjust by probability: home_xG ×= (pred_home/50%), away_xG ×= (pred_away/50%)
```

### Goal Tendency Classification

```
Step 1: 计算全场预期总进球
  total_xG = home_xG + away_xG

Step 2: 校正因子
  14.0a 客场防守折扣: away def tier "elite" → total_xG ×0.92
  14.0b 深盘压制: pred_home ≥70% AND AH ≥1.5 → total_xG += 0.5 (stomp potential)
  14.2 OU Price Calibration: adjusted_OU = OU_line + (OU_home_water − 1.90) × 0.5
  14.4 xG Factor: team form adjustment (WebSearch, skip if unavailable)
  14.5 Phase Coefficient: Group R1 ×1.00 / R2 ×0.95 / R3 ×0.90 / KO R16 ×0.88 / QF ×0.85 / SF ×0.82 / Final ×0.80
  14.6 Zero-Inflation: both teams ≤2 GF/game → total_xG ×0.90
  14.10 External: weather ≤ −1.0 → total_xG ×0.85; rest deficit → ×0.92

Step 3: 最终校正
  final_xG = total_xG × Π(correction_factors)
  weighted_OU = max(OU_line, final_xG) × 0.4 + min(OU_line, final_xG) × 0.6 (anchor to market OU)

Step 4: 判定
  偏大球: weighted_OU ≥ 2.75 or (weighted_OU ≥ 2.5 and draw exclusion 4/4 true)
  偏小球: weighted_OU ≤ 2.0 or (weighted_OU ≤ 2.25 and both teams defensive fortress)
  中性: 2.0 < weighted_OU < 2.75

Step 5: 置信度
  高: market OU + team trends + external factors all aligned
  中: 2 of 3 aligned
  低: ≤1 aligned or data missing
```

### Draw Exclusion (保留用于大小球判定)
```
All 4 true → over boost:
  1. Both no 0-0 in last 3  2. Combined GF >2.5
  3. OU 2.5 over water ≤1.85  4. No defensive fortress (KB-3 rule #27)
```

### ⛔ 已移除 (原因: 虚假精度/与进球倾向无关)
~~Poisson 比分 / Top3比分 / 14.0c/14.1/14.3/14.7/14.8/14.11/14.0d/14.0e~~

---

## KB-8: Supplementary Methodology (Quick Reference)

### Kelly Criterion
```
f* = (bp - q) / b
where f* = fraction of bankroll, b = net odds, p = win probability, q = loss probability
```

### Asian Handicap Conversion (Quick)
```
Probability -> AH line approximation:
  P(home) - 0.50 > 0.02 -> 0    > 0.08 -> 0.25  > 0.14 -> 0.5
               > 0.20 -> 0.75  > 0.27 -> 1.0   > 0.33 -> 1.25
               > 0.38 -> 1.5   > 0.42 -> 1.75  > 0.47 -> 2.0
```

### Over/Under Line to Goal Expectation
```
OU 2.5 -> xG ~2.5  |  OU 2.0 -> xG ~2.0  |  OU 3.0 -> xG ~3.0
OU 2.25 -> xG ~2.25 |  OU 2.75 -> xG ~2.75
```
## KB-9: 复盘/回测 → 用 football-backtest-workflow

> 赛后回测复盘已统一由 `football-backtest-workflow/` 子技能处理（7 阶段/9 层报告）。
> 详见 analyst SKILL.md Step 13 赛后回测触发器。旧版 postmortem.md 已删除。

---

## KB-10: MBI — Multi-Bookmaker Intelligence Framework

> **Rationale**: Pinnacle is the gold standard but not infallible. 30-bookmaker data from 500.com enables consensus-weighted analysis that captures signals Pinnacle alone misses.

### 博彩公司分级

| Tier | Weight | Members | Characteristics |
|:---|:---:|:---|:---|
| **Sharp** | 0.55 | Pinnacle, bet365, IBC(沙巴) | Accept winning players, razor-thin margins, lead price discovery |
| **Asian** | 0.25 | 澳门, 皇冠, 利记, 易胜博, 12bet, 18bet | Regional capital flow, water-level sensitive, macro-policy influenced |
| **Retail** | 0.20 | 威廉希尔, 立博, Interwetten, 必发(exchange), 伟德, Bwin | Public sentiment, recreational volume, exchange reveals real money |

### SCS — Sharp Consensus Score (需10.3b量价交叉验证)

```
SCS = Σ(tier_w_i × dir_i) / Σ(tier_w_i)
  dir_i: +1↓/−1↑/0|<噪声阈值 | 噪声 = max(0.02×odds, 1.5×σ历史)
  幅度权重 = min(|变化%/10%|, 1.0) | 时间衰减 = exp(−小时/24)
  权重化方向 = dir × 幅度权重 × 时间衰减
```

交叉验证要求:
```
SCS 信号生效需通过 10.3b 量价交叉验证:
  SCS ≥ 0.70 + 成交量确认方向 → 全效，logit +0.40
  SCS ≥ 0.70 + 成交量不配合 → 降效，logit +0.15（可能仓位驱动）
  SCS < 0.40 + 成交量放大 → 分歧有效，logit −0.20
  SCS < 0.40 + 成交量萎缩 → 低流动性噪声，忽略
```

**Thresholds** (均需量价验证):
- SCS ≥ 0.70 → Strong consensus → 经量价验证后 ±logit
- SCS 0.40–0.70 → Moderate → no adjustment
- SCS < 0.40 → Weak consensus → Step 10 penalty −5%

### DRI — Dispersion Risk Index

```
DRI_raw = ouzhi.dispersion.home × 0.5 + ouzhi.dispersion.draw × 0.3 + ouzhi.dispersion.away × 0.2

联赛校准: DRI_calibrated = DRI_raw / league_median_DRI × 30
  (league-specific: take 500+ historical matches per league median DRI as baseline, eliminates natural inter-league differences)
  WC/EPL/UCL median ~12-18; lower-division median ~25-40

阈值 (以 WC/top5 联赛为默认):
  DRI_cal < 12 → Tight consensus → confidence × 1.05
  DRI_cal 12–35 → Normal → no adjustment
  DRI_cal 35–60 → High dispersion → confidence × 0.85, ⚠️ warning
  DRI_cal > 60 → Extreme → confidence × 0.70, 🔴 systemic risk flag

信息驱动 vs 混乱型离散 :
  如果 DRI 高 AND Pinnacle 领涨 (Lead-Lag STRONG):
    → Info-driven dispersion (market repricing), DRI_signal halved
  如果 DRI 高 AND Lead-Lag = NOISE:
    → Chaos-type dispersion (retail noise), DRI_signal fully applied
```



#### DRI Tier-Variance Analysis

```
Information-type dispersion (faction divergence) detection:
  Condition: Sharp-tier internal dispersion < 10 AND Retail-tier internal dispersion < 10
        BUT |Sharp mean − Retail mean| > 0.15

  Meaning: Sharp tier (Pinnacle/bet365/IBC) unified, Retail tier (William Hill/Ladbrokes) unified,
        but opposite directions. Sharp tier has inside information, Retail tier still pricing on old data.

  Action: DRI penalty halved (×0.5)
        Extra Sharp-follow correction: logit +0.20 (follow Sharp direction)
        Marked as "Info-Type Divergence — Follow Sharp"

Chaos-type dispersion detection:
  Condition: Info-type conditions not met, AND DRI > 40

  Meaning: 30 bookmakers in disorder, no tier pattern, random cross-cutting.
        Bookmakers themselves uncertain, pure noise.

  Action: DRI penalty fully applied
```

### 10.3 Lead-Lag Chain Detection

```
Parse change_time from yazhi page (format: "MM-DD HH:MM").
Timestamp quality check: if 500.com scrape delay >1h, downgrade to low confidence.

Lead institution priority (by event type):
  Western events (WC/Euro/EPL/UCL): Pinnacle > bet365 > Macau
  Asian events (AFC CL/J-League/K-League): SBO/IBC > Macau > Pinnacle
  World Cup: Pinnacle = SBO (equal weight, global pricing)

链类型:
1. Lead moves first → secondary follows <2h → tertiary follows <4h
   → STRONG SIGNAL, logit +0.40
   Magnitude bonus: if lead adjusts ≥5%, extra +0.10

2. Lead moved → majority DID NOT follow within 4h
   → WEAK SIGNAL, 忽略

3. Non-lead moved first → lead remained static
   → NOISE, 忽略

4. 三层同时动 (1h 窗口内)
   → GENUINE EVENT, logit +0.20

Default: no clear chain → 0
```

#### 10.3b Volume×Price Cross-Validation



```
四象限判定矩阵（结合 touzhu 页必发成交量数据）:

  ┌─────────────────┬───────────────────┬──────────────────┐
  │ 赔率方向         │ 成交量↑(配合)      │ 成交量→(不配合)    │
  ├─────────────────┼───────────────────┼──────────────────┤
  │ 赔率↓(看好)     │ 被动调价(仓位驱动)  │ 主动降价(信息驱动) │
  │                 │ = 噪音, 忽略       │ = 真信号, ×1.3    │
  │                 │ Lead-Lag 降级      │ Lead-Lag 升级    │
  ├─────────────────┼───────────────────┼──────────────────┤
  │ 赔率↑(看淡)     │ 被动抬价(资金离场)  │ 主动抬价(诱导)     │
  │                 │ = 撤退信号,        │ = 反向信号,       │
  │                 │   logit −0.15      │   logit +0.20    │
  │                 │                   │   (跟庄家反向)    │
  └─────────────────┴───────────────────┴──────────────────┘

判定阈值:
  成交量↑: 必发该方成交量 > 前 4h 均量 × 2
  成交量→: 必发该方成交量 < 前 4h 均量 × 1.2

与 Lead-Lag 集成:
  检测到 Lead 变动 → 立即查必发对应方向成交量
  主动降价 + STRONG chain → logit +0.40 × 1.3 = +0.52 (最强信号)
  被动调价 + STRONG chain → logit +0.40 × 0.5 = +0.20 (降级)
  主动抬价(诱导) + GENUINE EVENT → logit −0.20 (庄家反向操作)

与陷阱 B 类联动:
  B 类陷阱触发 + 赔率变动方向无量配合 → 确认为诱导 → 强化原方向
  B 类陷阱触发 + 赔率变动方向有量配合 → 转为 C 类处理 → 降信度
```

### 10.4 Water Flow Analysis

Water level changes must first be controlled to compare only under the same handicap level:

```
Prerequisite: only count AH water changes from bookmakers whose handicap level DID NOT change.
      Bookmakers with level changes are flagged separately, excluded from flow stats.

Bookmaker dedup: 16 AH companies contain same-group white labels (Crown/Legacy/EasyBet share odds source).
          Cluster odds vectors first (correlation > 0.95 = same source),
          take one representative per cluster. Independent sources typically 6-9.

统计规则 (锁定盘口后):
  flowing_in:  home water↓ OR away water↑ = 看好主队
  flowing_out: home water↑ OR away water↓ = 看淡主队

Flow Ratio = |flowing_in − flowing_out| / N_independent_sources

Flow Ratio ≥ 0.75 (强流向):
  + Pinnacle 领涨 → STRONG，logit +0.30
  + Pinnacle 静态 → SUSPICIOUS，logit −0.20
  flowing_out → logit −0.30

0.50–0.75 → 中度，logit ±0.10
< 0.50 → 分散，无信号

#### Sharp Counter-Betting Asian Heat

```
Asian Heat vs Sharp Counter-Bet Detection:

Trigger: Flow Ratio ≥ 0.70 (Asian tier: Macau/Crown/Legacy/12bet)
          AND (Pinnacle 反向变动 ≥0.03 OR Pinnacle 极度静态 >4h)

Meaning: Asian tier retail money flooding in same direction (water dropping hard),
      but Sharp tier Pinnacle not only fails to follow, it COUNTER-MOVES or absorbs.
      Classic "retail hot vs institution cold" — Sharp tier is counter-betting Asian heat.

处理: 热门方 logit −0.35（强反向）
      Marked as 🔴 counter signal, consider opposing side
      对应 Trap #19 修正
```

### Exchange-Traditional Divergence
```
From touzhu data (必发 Betfair exchange):

┌─ Three-Layer Exchange Analysis ──────────────────────────┐
│ Layer 1: Volume Ratio (成交量占比)                         │
│   volume_ratio = volume_favorite / total_volume            │
│   volume_ratio > 0.80 → heavy interest (don't skip)       │
│   volume_ratio < 0.50 → thin market, confidence ×0.90     │
│                                                           │
│ Layer 2: VWAP vs Bookmaker (成交量加权均价偏离)  NEW       │
│   VWAP = Σ(price_i × volume_i) / Σ(volume_i)              │
│   divergence = (VWAP_favorite / Pinnacle_favorite − 1)     │
│   divergence ≤ −0.03 (VWAP significantly lower):           │
│     → SMART MONEY: big buyers got better price than mkt    │
│     → logit +0.25 (institutional conviction)              │
│   divergence ≥ +0.03 (VWAP higher than Pinnacle):          │
│     → DUMB MONEY: retail paying premium, no conviction     │
│     → logit −0.15                                         │
│   −0.03 < divergence < +0.03:                              │
│     → NEUTRAL: volume at market price, no edge            │
│                                                           │
│ Layer 3: Bookmaker P&L Exposure (庄家盈亏敞口)  NEW       │
│   pl_exposure = bookmaker_PL / total_volume × 100%         │
│   pl_exposure < −20% on favorite:                          │
│     → BOOKMAKER EXPOSED: bookmaker heavily exposed on favorite side          │
│     → May trigger odds increase to balance risk → logit −0.10 (caution)   │
│   pl_exposure > +50% on underdog:                          │
│     → BOOKMAKER HEDGED: 庄家在冷门方盈利充足               │
│     → no signal (bookmaker already protected)             │
│                                                           │
│ Match Size Weighting (赛事体量折扣)  NEW                   │
│   total_volume > £500K  → weight 1.00 (major event)       │
│   total_volume £100K–500K → weight 0.70 (medium)          │
│   total_volume £50K–100K → weight 0.40 (small)            │
│   total_volume < £50K  → weight 0.10 (micro, skip)        │
│                                                           │
│   ALL exchange signals × match_size_weight                 │
└───────────────────────────────────────────────────────────┘

Exchange Composite Signal:
  exchange_logit = (vwap_signal + exposure_signal) × volume_confidence × match_weight
  where volume_confidence = min(1.0, volume_ratio / 0.80)
```



### 10.6 Kelly Consensus

Kelly index has no absolute directional interpretation — must segment by scenario, phase, and cross-validate.

#### 10.6.1 定义
```
Kelly = 赔率 × 去抽水概率
阈值 = bookmaker_return_rate × 1.02
Pinnacle ~98% → Kelly>0.98 = 高 | 竞彩 ~89% → Kelly>0.89 = 高
```

#### 10.6.2 Two Interpretation Frameworks

| Framework | Core Premise | Applicable Scenario | Signal Interpretation |
|:---|:---|:---|:---|
| **Theoretical Market-Making Logic** | Bookmaker balances bets, profits from vig, does not actively take positions | 90% regular leagues, non-marquee matches, stable fund flow events | Lower Kelly → less payout pressure on bookmaker → stronger market consensus → higher outcome probability |
| **Game-Theoretic Bookmaking Logic** | Bookmaker abandons bet balancing, exploits retail cognitive gaps to set traps | Top cup knockout stages, elite club derbies and other capital-surge marquee matches | Favorite side heavy capital inflow but Kelly rises instead of falling → bookmaker unafraid of payout, truly bullish; Kelly keeps falling → bait trap |

#### 10.6.3 Scenario Determination Rules

```
Phase 1: Event Classification
  焦点赛事 (启用博弈逻辑):
    - 世界杯淘汰赛阶段 (R16+)
    - 欧冠淘汰赛
    - 五大联赛争冠/保级关键战
    - 豪门德比 (任何赛事)
    - 必发成交量 > £2M 的任何赛事
  
  普通赛事 (启用理论逻辑):
    - 所有非焦点赛事
    - 联赛中游无欲无求的场次
    - 友谊赛（无论成交量多少，凯利信号不适用）

Phase 2: Time Phase
  Opening phase (>24h to kickoff): market-making logic only (opening odds reflect fundamental assessment)
  Peak betting (<24h to kickoff): focus matches switch to game theory logic, ordinary matches keep market-making logic

Phase 3: Volume Validation
  Betfair volume > £1M: game theory logic enabled
  Betfair volume £200K–£1M: game theory → signal halved
  Betfair volume < £200K: game theory disabled, fall back to market-making logic
```

#### 10.6.4 Core Determination Rules

**Regular Events (Theoretical Logic)**:

| Condition | Signal | Logit Δ |
|:---|:---|:---:|
| Favorite Kelly < (return_rate − 0.05) AND lowest among three | Institution controlling payout, bullish on favorite | +0.15 |
| Favorite Kelly > (return_rate + 0.05) | Institution not controlling payout, favorite questionable | −0.20 |
| Favorite Kelly within range | Neutral | 0 |
| All three Kelly < (return_rate − 0.10) | Excessive vig, signal downgrade | Confidence ×0.88 |

**Marquee Event Peak Betting Phase (Game-Theoretic Logic)**:

| Condition | Signal | Logit Δ |
|:---|:---|:---:|
| Favorite heavy inflow (>70% vol) + Kelly rising vs opening | Bookmaker unafraid of payout, truly bullish | +0.20 |
| Favorite heavy inflow (>70% vol) + Kelly continuously falling vs opening | Bait trap, favorite questionable | −0.25 |
| Favorite Kelly rising vs opening + 3+ Sharp tier books syncing upward | Sharp consensus confirmed | +0.10 (stacked) |
| Insufficient volume (<£200K) | Game-theoretic logic not applicable | Fallback to theoretical logic |

#### 10.6.5 Cross-Validation Rules (MANDATORY)

```
Kelly signals CANNOT act alone, must resonate with other MBI modules:

✅ Kelly positive + Lead-Lag confirmed (STRONG or GENUINE) + Water Flow same direction
   → 信号生效，校正幅度拉满

⚠️ 凯利正向 但 DRI > 40（高分歧）
   → Kelly downgraded, correction halved

❌ Kelly conflicts with SCS consensus or Water Flow direction
   → Kelly invalid; trust Water Flow + Betfair data instead

❌ Kelly conflicts with Betfair VWAP direction
   → Kelly invalid; VWAP is real money voting, higher priority
```

#### 10.6.6 Application

```
kelly_logit = applicable_framework(category, phase, volume) → signal

Cross-validation check:
  if kelly_signal × (LeadLag or WaterFlow) ≥ 0:
    kelly_effective = kelly_logit
  else:
    kelly_effective = 0  (signal invalidated by conflict)

Apply: logit' = logit + kelly_effective
```

### 10.7 Four New MBI Trap Rules

| # | Rule | Trigger | Signal | Action |
|:--:|------|---------|:------:|--------|
| 16 | **Tier Divergence** | Sharp tier vs Asian tier AH gap ≥0.25 ball | 🔴 systemic | Confidence ×0.85, flag match |
| 17 | **Exchange-Volume Spike** | 必发 volume >2× previous + odds static | ⚠️ resistance | Direction confidence −5% |
| 18 | **Kelly Context Gap** | Marquee match betting phase: favorite Kelly rising not falling + 3+ Sharp tier syncing upward + Betfair volume >70% | ✅ context signal | Direction +5%, logit +0.20 (requires cross-validation: Lead-Lag/WaterFlow same direction to activate) |
| 19 | **Sharp Counter-Betting** | Flow Ratio ≥0.70 (Asian tier) + Pinnacle opposing or extremely static >4h | 🔴 counter-bet | Favorite logit −0.35, consider betting underdog |

### MBI logit-space集成



```
Step A: 基础概率 → logit 转换
  logit_h = ln(P_h / (1 − P_h))
  logit_d = ln(P_d / (1 − P_d))
  logit_a = ln(P_a / (1 − P_a))

Step B: 在 logit 空间叠加所有校正
  logit_h' = logit_h + Σ(correction_i)
  where correction_i is the logit offset from each correction factor (from KB-6)

Step C: sigmoid 转回概率
  P_h' = 1 / (1 + e^(−logit_h'))
  P_d' = 1 / (1 + e^(−logit_d'))
  P_a' = 1 / (1 + e^(−logit_a'))

Step D: 归一化
  total = P_h' + P_d' + P_a'
  final = [P_h'/total, P_d'/total, P_a'/total]
```

Probabilities bounded (0,1), Bayesian-equivalent, magnitude auto-compresses near extremes.

### MBI Composite — logit空间

> 四组降权 + cap + 与KB-6串联:

```
#12 MBI Composite 作为 logit 偏移量:
  mbi_raw = SCS_raw + DRI_raw + LeadLag_raw + Kelly_raw + WaterFlow_raw + VolXPrice_raw

  各模块原始信号 (raw signal):
  SCS_raw :
    SCS ≥ 0.70 + 量价确认 → +0.40
    SCS ≥ 0.70 + 量价不配合 → +0.15
    SCS 0.40–0.70 → 0
    SCS < 0.40 → −0.20

  DRI_raw:
    DRI < 15 → +0.20
    DRI 15–40 → 0
    DRI 40–70 → −0.35
    DRI > 70 → −0.70

  LeadLag_raw :
    STRONG chain + 主动降价 → +0.52
    STRONG chain + 被动调价 → +0.20
    STRONG chain (无量数据) → +0.40
    GENUINE EVENT + 主动抬价(诱导) → −0.20
    GENUINE EVENT → +0.20
    NOISE/WEAK → 0

  Kelly_raw:
    fav Kelly < 0.92 + lowest → +0.20
    fav Kelly > 1.00 → −0.35
    neutral → 0

  WaterFlow_raw:
    Flow ≥ 0.70 + Pinnacle leads → +0.30
    Flow ≥ 0.70 + Pinnacle static → −0.20
    Flow < 0.50 → 0

  VolXPrice_raw :
    主动降价(信息驱动) → +0.17
    主动抬价(诱导) → −0.20
    被动调价(仓位驱动) → 0
    资金离场(被动抬价+量增) → −0.15
```

### 四组降权

覆盖KB-6 9项 + MBI 6项:

```
四组降权规则:

组1 — 资金热度/共识 (MBI): SCS + LeadLag + WaterFlow
  三者测同一现象("市场往哪走")，方向几乎总同向。
  处理: 只取 max，其余两项各 ×0.25
  signal_组1 = max(SCS, LeadLag, WaterFlow) + 0.25 × mid + 0.25 × min
  (原: +0.40+0.52+0.30=1.22 → 新: 0.52+0.10+0.075=0.695 logit)

组2 — 市场不确定性 (MBI): DRI + SBO分歧(校正9) + 6D评分(校正8)
  三者测市场噪音/分歧/不确定性。
  处理: 只取最负的一项（风险厌恶原则），其余忽略
  signal_组2 = min(0, DRI_raw, 校正9_raw, 校正8_raw)
  (保留最悲观信号，不叠加)

组3 — 盘口异常检测 (KB-6): 校正1(欧亚陷阱) + 校正2(开盘定律) + 校正3(临场真实性)
  处理: 只取 max(|Δ|)，其余两项各 ×0.30 (同 KB-6.3)
  signal_组3 = max(|Δ₁|,|Δ₂|,|Δ₃|) × sign + 0.30 × next + 0.30 × last

组4 — 基本面/叙事 (KB-6): 校正5(基本面) + 校正6(背水一战) + 校正7(叙事)
  信息源各自独立 → 线性叠加，不降权
  signal_组4 = 校正5 + 校正6 + 校正7

跨组规则:
  KB-6 组(组3+组4) 与 MBI 组(组1+组2) 不额外降权（信息源不同）
```

### MBI Final

```
mbi_logit = signal_组1 + signal_组2

Apply:
  logit_final = logit_ctx + min(mbi_logit, 0.80)
  (MBI 总量 cap 0.80 logit，≈概率 ±20%)
```

### Total Correction Cap

```
|KB6_correction_total| ≤ 0.80 logit  (组3+组4+其他独立项)
|MBI_total| ≤ 0.80 logit  (组1+组2+独立项)
合计 |correction_total| ≤ 1.20 logit

含义（以 base 55%，logit=0.20 为起点）:
  +0 校正   → sigmoid(0.20) = 55%
  +0.60     → sigmoid(0.80) = 69%
  +1.00     → sigmoid(1.20) = 77%
  +1.20 CAP → sigmoid(1.40) = 80%  ← 硬上限
  80% 是足球预测的理性上限，从此杜绝 90%+ 虚假高置信度
```

### 报告中的MBI面板

Each match report MUST include an MBI panel:

```
┌─ MBI Assessment ─────────────────────┐
│ SCS (Sharp Consensus):  ████████░░ 0.82  Strong │
│ DRI (Dispersion Risk):  ██░░░░░░░░ 12.4   Tight │
│ Lead-Lag: Pinnacle→bet365→澳门  STRONG       │
│ Tier Diverge: None                            │
│ Water Flow:  11/16 flowing in (0.69)          │
│ Kelly Avg:    fav 1.02 / others 0.88          │
│ MBI Verdict:  CONFIRM (all signals aligned)   │
└───────────────────────────────────────────────┘
```

### 数据质量验证

```
Before applying ANY MBI module, validate input data quality:

1. Bookmaker Count Check:
   ouzhi requires ≥20 of 30 bookmakers with valid data
   yazhi requires ≥12 of 16 bookmakers with valid data
   < threshold → module marked DEGRADED, confidence ×0.85

2. Timestamp Freshness:
   yazhi change_time within 6h of current time → FULL weight
   within 6–12h → 0.7× weight
   >12h or missing → DEGRADED, 0.4× weight

3. Data Completeness per Match:
   All 6 pages present → FULL analysis
   5/6 → min 4 core modules (ouzhi+yazhi+touzhu+shuju), others skipped
   <4/6 → match flagged LOW QUALITY, confidence ×0.80

4. Betfair Volume Sanity:
   total_volume > £50K → exchange modules enabled
   total_volume < £50K → exchange modules DISABLED for this match
   volume spike >5× league average → suspicious, flag but don't skip

5. Bookmaker Consistency:
   If >5 bookmakers show identical odds (potential data mirroring):
     deduplicate before SCS calculation
     lower effective N in consensus scoring
```

---

## KB-11: Data Calibration

> 确保输入信号干净可比较。

### 11.1 Dynamic Bookmaker Deduplication

```
血缘: 沙巴系(IBC/12bet/18bet/M88) | Crown(皇冠/利记/易胜博/明升) | Entain(立博/Bwin/Coral)
系内去重: N家→1个独立节点, 权重=原权重×√N
动态: Pearson r>0.95+时间戳→更新血缘图
脏数据: 单家>均值3σ+无时间戳→丢弃 | 去重后<5家→DRI升1档, WF×0.5
```

### 11.2 Cross-Bookmaker Water Normalization

```
归一化 = 原始水位 × (0.95/该机构标准返还率)
Macau 0.90/0.92→0.929 | Pinnacle 0.975/0.98→0.945
禁止直接使用未校准原始水位
```

### 11.3 True Opening Odds Anchor

```
弃用72h初盘(低流动性/试盘)
真实初盘=24-48h中首达条件之赔率: (a)必发量>£100K 或 (b)亚盘量>HK$100K
24h内均未达→以24h节点为基准
```

### 11.4 Event Tiering

| Parameter | Top-Tier Events | Second-Tier Events | Low-Tier Events |
|:---|:---|:---|:---|
| **Scope** | 五大联赛/欧冠正赛/世界杯正赛/欧洲杯正赛 | 荷甲/日职/美职/巴甲/欧冠资格赛 | Low divisions/friendlies/preseason/early qualifiers |
| **Bookmaker Weight** | Sharp 0.6 / Asian 0.2 / Retail 0.2 | Sharp 0.45 / Asian 0.35 / Retail 0.2 | Sharp 0.3 / Asian 0.4 / Retail 0.3 |
| **DRI Thresholds** | 12 / 35 / 65 | 18 / 45 / 75 | 25 / 55 / 80 |
| **Kelly Game-Theoretic Logic** | Betfair > £1M enabled | Betfair > £500K enabled | **Fully disabled game-theoretic logic** |
| **Betfair Signal Weight** | 100% | 50% | **0% (disabled)** |
| **Special Restrictions** | None | None | No "draw" bets; DRI > 35 = abandon |

```
动态定级:
  Minnow event single-match Betfair > £500K → auto-upgrade to Secondary
  Top-league reserve teams/cup dead rubbers → auto-downgrade to Secondary
  Friendlies always classified as Minnow, upgrade not applicable
```

---

## KB-12: Advanced Signal Quantification

> 所有 logit 校正须对应庄家操盘手法。

### 12.1 回调验证

```
4h内回调>50%→假测试→清除信号 | <20%+趋势保持→确认
20-50%→减半 | 亚洲赛事SBO+澳门(非Pinnacle) | 西向Pinnacle(SBO验证)
```

### 12.2 AH真假突破

| 类型 | 条件 | 效果 |
|:---|:---|:---:|
| 真突破 | 对应方向水位≤0.925+Sharp先动 | ±0.18 |
| 假突破(Trap) | 水位≥1.00+仅Asian动/Sharp不动 | **反向±0.22** |

临场1h内×1.3 | 24h外×0.7 | SPF<1.35×0.5(被动平衡)


### 12.3 必发订单簿阻力墙

```
热门ask-1≥bid-1×3+持续30min+取消率<20%→阻力墙→logit -0.25
下盘阻力墙(零售逆势)→×1.3 | 支撑墙(热门bid≥ask×2+稳降)→+0.20
仅用level1(2-3层是庄家虚单) | 仅Betfair量>£100K时启用
```

### 12.4 初受盘差分析

```
Sharp vs Asian差≥0.25球→高波动→信号×0.5→禁入串关核心
反市场操作: 必发>80%看好+盘口反向下调+无新闻→庄家主动操作→×1.5
```

### 12.5 Draw Diversion Trap (Bidirectional)

```
Positive diversion (bookmaker setting capital pool):
  Draw Kelly < min(home Kelly, away Kelly) − 0.1
  + 平局必发成交量占比 < 20%
  → Bookmaker uses low Kelly draw to attract capital, genuinely does not expect draw
  → 平局概率下调，热门方 logit +0.12

反向分流（散户追捧平局）:
  Draw Kelly > max(home Kelly, away Kelly) + 0.1
  + 平局必发成交量占比 > 35%
  → Retail crowd frantically buying draw, bookmaker raising payout unafraid of it hitting
  → 平局概率下调，胜负方 logit +0.10
```

---

## KB-13: System Risk Controls

### 13.1 Dynamic Slippage Model

| Phase | Time Window | Slippage | Description |
|:---|:---|:---:|:---|
| Opening | >24h | 1% | Ample liquidity |
| Mid-Betting | 6-24h | 2% | Normal fluctuation |
| Late | 1-6h | 3.5% | Frequent water sweeps |
| Pre-close | <30min | 5% | Extreme volatility |

```
串关滑点叠加:
  Total slippage = single-match slippage × √N  (independent random variable variance stacking)
  3串1 临场总滑点 = 3.5% × √3 ≈ 6.1%

凯利计算前置:
  adjusted_odds = odds × (1 − slippage) × return_rate
  所有 EV 统一使用 adjusted_odds
```

### 13.2 Signal Confidence Tiering → 见 betting-sop.md

> 信号分级、Kelly系数、单场上限、串关准入规则已移入 `references/betting-sop.md`。
> 本模块仅保留分析层面的风险控制。

### 13.7 Permanently Excluded Feature Blacklist

```
❌ 真实赛事数据 (xG/Opta):
   Bookmaker quants already priced into opening odds; retail recalculation = lagged noise

❌ NLP 新闻事件自动量化:
   News is poison bookmakers feed retail; automated news scraping = eating trap baits

❌ LSTM/Transformer 赔率时序预测:
   Odds are human-adjusted based on capital pool, no intrinsic physical laws
   深度学习 = 100% 严重过拟合

❌ 必发三档深度:
   Level 2-3 mostly market-maker ghost orders; inclusion = noise amplifier

❌ Single static parameter set for all events:
   Ignores league transparency differences = top leagues miss signals + minnow leagues hit traps
```

### 13.8 竞彩市场转换层

> ⚠️ **数据源强制分层**: 分析层(Pinnacle, ~98%)用于 Steps 1-10.5 的赔率分析；
> 执行层(竞彩, ~71%)专用于 Step 11 的投注建议和 EV 计算。**两层数据严禁混用**。
> EV阈值分级、串关策略 → 见 betting-sop.md

#### 13.8a 竞彩赔率数据源

```
竞彩官方赔率有两个来源，不可混淆:

源1: 竞彩 SPF (胜平负) 赔率
  来源: trade.500.com/jczq/?playid=312&g=2 页面 → "胜/平/负"三列
  用途: 直接投注胜平负玩法时的赔率
  验证: trade.500.com 首页 SPF 列显示的是竞彩官方赔率, 不是百家平均

源2: 竞彩 RQSPF (让球胜平负) 赔率
  来源: odds.500.com/fenxi/rangqiu-{id}.shtml → 第1行 "竞*官*"
  解析格式: [让球数][初盘主][初盘平][初盘客][即时主][即时平][即时客]
    数字连续无分隔符，按小数点分隔。
    示例: "-12.253.182.702.003.253.11"
      → 让球=-1, 初盘=2.25/3.18/2.70, 即时=2.00/3.25/3.11
  用途: 深盘场 SPF 未开售时的替代玩法

单关玩法可用性:
  参考: trade.500.com/jczq/?playid=312&g=1
  规则: 只有出现在该页面的比赛才支持单关投注
  动作: 在 Step 11 构建单关方案前, 逐场核验 single_match_available 标志
```

#### 13.8b 竞彩 EV 转换公式

```
竞彩 EV = deVigProb × 竞彩赔率 × 串关返奖率(0.71) − 1

竞彩隐含概率: Q_h = (1/C_h) / (1/C_h + 1/C_d + 1/C_a) × R
```

#### 13.8c 竞彩特有的"赔率冻住"风险

```
竞彩赔率开售后不随国际市场变动。

规则:
  国际市场赛前 1h 发生显著变盘（>5% 方向移动）
  且竞彩赔率未更新
  → 报告强制声明: "⚠️ 价格失效 — 国际赔率已变，竞彩赔率可能不反映当前市场"
  → 相应方向竞彩 EV 可靠性降级
```

#### 13.8d 单关 vs 串关返奖率差

```
竞彩返奖率:
  单关: ~86%
  串关 (2串1): ~71%
  串关 (3串1): ~71%² ≈ 50%

策略含义:
  竞彩 EV = deVigProb × C_odds × R − 1
  → 单关 EV 阈值: EV ≥ 0 即正期望
  → 串关 EV 阈值: 需 ≥ +0.05 才能覆盖返奖率差
  → Step 11 串关构建前: 逐条腿计算竞彩 EV，任何 EV<−0.05 不得入选
```

---

## KB-14: Bookmaker Intelligence — Market Pressure

> 扩展 MBI 框架的"庄家读心"层。不改变方向判定，只调节置信度。

---

### 14.1 Module 1: Pulsation (拉锯战指数)

#### 14.1.2 核心指标

| 指标 | 计算 | 含义 |
|:---|:---|:---|
| 频率F | 方向改变/采样-1 | ≥0.4=犹豫 |
| 位移D | \|首末差\|/首值 | <1.5%=微弱 |
| TWQ | F/(D+0.001) | >50=严重拉锯 |

#### 14.1.3 二维决策矩阵

```
            | D < 1.5% (低位移)  | D ≥ 1.5% (高位移)
────────────┼─────────────────────┼─────────────────────
F ≥ 0.4     | 高频低幅             | 高频高幅
(高频)      | 虚晃一枪             | 宽幅洗盘
            | 信度 × 0.75         | 信度 × 0.85
────────────┼─────────────────────┼─────────────────────
F < 0.4     | 低频低幅             | 低频高幅
(低频)      | 死水一潭             | 单边突破
            | 信度 × 0.90         | 信度 × 1.15
```

#### 14.1.4 判断规则

```
IF TWQ > 50 OR matrix = "高频低幅" → PULSATION_WARNING
IF matrix = "单边突破" AND MBI 方向一致 → PULSATION_CONFIRM
IF matrix = "宽幅洗盘" → PULSATION_CAUTION (需 PVD/CD 交叉验证)
```

---

### 14.2 Module 2: Cross-Market Divergence

#### 14.2.1 PVD — Price-Volume Divergence (价量背离)

| 状态 | 条件 | Score |
|:---|:---|:---:|
| 真实推动 | 赔率降(升) + 必发量暴增(>2x) | +1.0 |
| 量在价先 | 赔率未变 + 必发量已暴增 | +1.0 |
| 虚假信号 | 赔率降(升) + 必发量萎缩/平平 | −1.0 |
| 散户驱动 | 赔率降 + 散户渠道量增 + 必发平平 | −0.5 |
| 无可比性 | 必发缺失或量极低 | 0.0 |

#### 14.2.2 CD — Channel Divergence (渠道背离)

| 状态 | 条件 | Score |
|:---|:---|:---:|
| 渠道背离 | Sharp 方向明确 + 大众反向 | +1.0 |
| 领先跟随 | Sharp 方向明确 + 大众同步 | +0.5 |
| 散户扎堆 | 大众集体朝一边 + Sharp 不明确 | −0.5 |
| 机构分歧 | Sharp 内部撕裂 | −1.0 |
| 无数据 | 大量博彩公司缺失 | 0.0 |

#### 14.2.3 MPC — Market Pressure Composite

```
MPC = 0.6 × PVD_Score + 0.4 × CD_Score

死区过滤: IF |MPC| < 0.2 → 乘数 = 1.0 (不修正)
IF 0.2 ≤ |MPC| < 0.5 → 最终信度 = 原信度 × (1 + MPC × 0.10)
IF MPC ≤ −0.5 → 触发 Veto 或 CB (见 14.3)
```

---

### 14.3 三级响应架构（永不翻转 MBI 方向判定）

#### 14.3.1 判定逻辑

```
IF MPC < −0.8:
  状态 = CIRCUIT_BREAKER
ELIF MPC < −0.5 AND TWQ_matrix IN [高频低幅, 宽幅洗盘]:
  状态 = CIRCUIT_BREAKER (双因子共振)
ELIF MPC < −0.5:
  状态 = VETO
ELIF |MPC| < 0.2:
  状态 = NORMAL (死区内)
ELSE:
  状态 = NORMAL (正常信度修正)
```

#### 14.3.2 各状态动作

| 状态 | 对 MBI 方向 | 对投注池 | 报告输出 |
|:---|:---|:---|:---|
| NORMAL (MPC>0) | 信度 × (1+MPC×0.10) | 正常进入 SOP | "积极" |
| NORMAL (MPC<0) | 信度 × (1+MPC×0.10) | 正常进入但降权 | "谨慎" |
| VETO | 方向保留(估值用) | 该场跳过投注 | "🚫 否决" |
| BREAKER | 方向保留 | 整场从候选池移除 | "🔴 熔断" |

#### 14.3.3 对 SOP 影响

Step 0.5 — 市场健康检查 (KB-14)，在 Step 1 之前执行。

---

### 14.4 回测指标
信息增益率 = Σ(Δ命中率)/触发场次 | MPC>0.3时提升≥3%→有效 | CB否决正确率≥60%→有效

---

### 14.5 默认参数（保守起步）

| 参数 | 缺省 | 说明 |
|:---|:---:|:---|
| MPC 幅度 | ×0.10 | 最大信度修正 ±10% |
| 死区 | \|MPC\|<0.2 | 过滤日常噪音 |
| CB 阈值 | MPC < −0.8 | 单因子熔断 |
| CB 共振 | MPC<−0.5 + TWQ异常 | 双因子共振熔断 |
| Veto 阈值 | MPC < −0.5 | 止付不禁估值 |
| TWQ 异常 | > 50 | 严重拉锯 |
| F 高频 | ≥ 0.4 | 振荡经验线 |
| D 低幅 | < 1.5% | 位移经验线 |
| ω₁/ω₂ | 0.6/0.4 | PVD/CD 权重 |

---

## KB-15: External Signal Injection (Roadmap)

> 未实现模块的优先级和量化规则。注: 赔率不是信息源，是庄家的风控工具。真正的 edge 在赔率之外。

### 15.1 首发伤停 (⭐⭐⭐)
```
赛前2h抓取→提取关键位置变化→对比赔率变动时间戳:
  赔率提前调整→市场已定价→无edge
  赔率未调整→市场未反应→真正edge
量化: 关键缺阵→logit -0.15 | 双核缺阵→-0.30 | 防线重组→对方+0.10
```

### 15.2 赛程体能 (⭐⭐)
```
7天3赛→x0.92 | 7天4赛→x0.85 | 双线→降1档 | 跨洲3h+→降1档
密集+弱旅→轮换高→穿盘降 | 密集+强敌→防守端受影响
```

### 15.3 天气场地 (⭐)
```
暴雨/大雪→偏小球 | >32°C→偏小球 | 大风→技术型受影响
人工草皮→客队-5% | 积水→长传队受益
```

### 优先级
| 信号 | 增益 | 代价 | 状态 |
|:---|:---:|:---:|:---|
| 首发 | 高 | 低 | 📋 |
| 体能 | 中 | 中 | 📋 |
| 天气 | 中低 | 中高 | 📋 |
| NLP | ⛔永久排除 | — | 🚫 |

---

## KB-16: 信号可靠性矩阵 — 2026WC 44场校准 (v3.7.0)

> **v3.7.0 结构性重写**: 废除179场跨赛事权重表和OCI五分位体系。
> 改用2026世界杯44场完赛数据直接测量每个信号的实际命中率。
> 核心发现: 绝大多数"信号"在复合后反而降低准确率。

### 16.1 基准线

```
Pinnacle 收盘最低赔率方向: 28/44 = 63.6%  (baseline)

这是本系统的理论上限——任何信号图层叠加不能低于这个基准，
否则就是在做减法。当前架构的 MBI×0.6+OCI×0.3+traps×0.1
在44场校准中仅得47.2%，比基准低16.4pp。
```

### 16.2 单信号命中率 (校准结果)

```
信号                           命中率    相对基准    结论
────────────────────────────────────────────────────────
Pinnacle收盘最低赔率方向        63.6%    ±0 bp      ← 基准线
必发成交量方向                 63.6%    ±0 bp      与Pinnacle完全一致(冗余)
低离散度+Pin同向              59.1%    -4.5 pp    有限正向
────────────────────────────────────────────────────────
Kelly指数方向                  43.2%    -20.4 pp   🔴 反向指标
赔率变动方向(OCI-1)            38.6%    -25.0 pp   🔴 反向指标 
概率%变动方向                  31.8%    -31.8 pp   🔴 无用
```

### 16.3 共线性矩阵

```
          Pin_dir  Δodds   Δdraw   Kelly  Δprob  Disp
Pin_dir   1.00
Δodds     0.550   1.00
Δdraw     0.098   0.049   1.00
Kelly     -0.157  -0.261  0.151   1.00
Δprob     0.348   0.815⚠️  -0.487  -0.266 1.00
Disp      -0.238  0.212   0.027   -0.147 0.218  1.00

⚠️ home_odds_change ↔ prob_change: r=0.815 → 冗余, 砍其一
```

### 16.4 信号使用规则

```
✅ 保留且作为主力:
  - Pinnacle收盘方向 (63.6%): 方向判定的唯一输入，不与其他信号复合
  
✅ 保留作为微调:
  - 低离散度+Pin同向 (59.1%): 仓位提升0.1x
  - 必发成交量方向: 仅当与Pin方向冲突时触发VETO

❌ 删除或降为反信号:
  - Kelly指数 (43.2%): 删除正向加分, 保留作为否定检查(Kelly>1.05→降仓)
  - 赔率变动方向 (38.6%): 删除, 不作为任何方向判定的依据
  - 概率%变动 (31.8%): 删除, 与赔率变动共线(r=0.815)

❌ 复合权重公式废除:
  direction = Pinnacle最低赔率方向 (单一输入)
  不再使用 MBI×w1 + OCI×w2 + traps×w3 公式
```

### 16.5 平局专项

```
Pinnacle 在 44 场中 0 次最低赔率是平局。
13场平局全部来自"强队对弱队但爆冷平"模式。
平局不能用赔率方向预测 → 需要独立模型。

平局触发条件 (暂用Step 9的五条):
  信号来源必须在赔率方向之外 (成交量异常/离散异常/动机冲突)
  触发≥3条 → 平局风险标记, 方向强制为"跳过"而非"D"
```

---

## KB-17: 平局专项模型 + 动机修正 (v3.7.1 WC48场校准)

> **v3.7.1**: 48场世界杯平局分析揭示三种结构模式。Pin 方向无法预测平局(Pin 0次平赔最低)。
> 平局不是"方向问题"，是"Pin 过信问题"。替代为 Pin 深度 + 动机 + 轮次三维分类。

### 17.1 平局三种结构模式 (WC48场实测)

```
类型A: 深盘慢热 (6/13)
  条件: Pin_H < 1.50 AND R1(首轮)
  逻辑: 强队首轮保存实力/磨合阵容, 不一定全力打穿
  案例: 西班牙 0-0 佛得角(Pin=1.11), 葡萄牙 1-1 民主刚果(Pin=1.30)
  平局率: 首轮深盘球队7场中4场平局(57%)

类型B: 深盘动机冲突 (3/13)  
  条件: Pin_H < 1.50 AND (主队已出线 OR 客队已淘汰 AND 主队 mot <0.25)
  逻辑: 双方都没动力, 走形式。强队轮换, 弱队不逼抢
  案例: 英格兰 0-0 加纳, 比利时 0-0 伊朗, 阿根廷 2-0 奥地利(这场没平)

类型C: 均衡对耗 (4/13)
  条件: Pin在 1.80~2.20 AND 双方动机差 <0.15
  逻辑: 实力接近 + 动力相近 → 平局是双方都接受的中间结果
  案例: 荷兰 2-2 日本, 伊朗 2-2 新西兰, 沙特 1-1 乌拉圭
```

### 17.2 动机修正四规则

```
规则1 (深盘慢热 — 信任降低):
  Pin_H < 1.50 AND R1 → draw risk +40%
  Pin_A < 1.50 AND R1 → draw risk +30%
  动作: Pin方向标记为"跳过" (除非偏离=0且离散收敛)

规则2 (深盘动机流失 — 严重稀释):
  Pin_H < 1.50 AND (主队 mot <0.25 OR 客队 mot <0.25) → draw risk +60%
  动作: 强制"跳过", 可选反投对手(如果赌对手赔率>3.0)

规则3 (均衡对耗 — 平局偏向):
  Pin在 1.80~2.20 AND mot_gap <0.15 → draw risk +30%
  动作: 仓位降 0.5x, 优先推双方进球(代替方向投注)

规则4 (生死战 — Pin可靠):
  Pin_H < 1.50 AND R3 AND mot_gap >0.30(一方必须赢) → draw risk -20%
  原因: 末轮生死战, 强队会认真打
  动作: 正常Pin方向, 不触发规则1/2
```

### 17.3 平局信号检查 (5条, 保留作为辅助)

```
1. Pinnacle平赔即时<3.20 且 较开盘下降
2. 30家离散度: 平局离散 ≤ min(主胜离散, 客胜离散)  
3. 亚盘即时盘口 = 平手盘 (handicap=0)
4. deVig去抽水后平局概率 > 28%
5. 必发成交量: draw_pct > 15% 或 draw_PL正值

触发≥3条 AND 没有规则4(生死战) → 方向"跳过"
与17.2的四规则独立并行检查
```

### 17.4 废除的DRM规则

- DRM-1/2/3/7 全部废除。替代为 17.1 三种模式 + 17.2 四规则。
- DRM打分体系 → 废除。不再按分计。

---

## KB-17b: 动机模型 + 反投框架 (v3.7.1 新增)

### 动机计算

```
输入: 小组当前积分/净胜球/剩余对阵
输出: 每队动机分数 (0.0-1.0)

mot = 0.70 首轮(双方等动力)
mot = 0.90 0分生死战
mot = 0.85 出线争夺战
mot = 0.50 若胜仍可争
mot = 0.40 平局即出线(保守)
mot = 0.20 已出线/已锁定(可轮换)
mot = 0.15 已淘汰(无动力)

mot_gap = |主队mot - 客队mot|
```

### 动机判定

```
mot与Pin的关系 (关键):

  mot=Pin同向 (共鸣):
    → Pin可靠, 不加不减。动机与Pin同向不能提升准确率
    → 理由: 世界杯48场中, mot与Pin同向时 Pin准确率仍=63.6%

  mot≠Pin反向 (冲突):
    → Pin被动机稀释。冲突=6场, 其中4场Pin方向输
    → 冲突 + mot_gap>0.30 → Pin方向强制"跳过"

  mot=中立 (gap<0.15):
    → 不影响Pin判定
```

### 反投触发条件

```
反投 = 不跟Pin + 赌对手方向

需同时满足四个条件 (缺一不可):

  1. Pin方向 ≠ 平局 (赔率最低方向是H或A)
  
  2. 动机-Pin冲突: mot方向 ≠ Pin方向 AND mot_gap > 0.30
     数据: 冲突场次中Pin准确率降至33%(vs 基线63.6%)

  3. 偏离信号 ≥ 2条 (KB-19)
     从正常的≥3条降至≥2条 — 动机已提供替代方向, 门槛可降低

  4. 对手赔率在 2.00~6.00 区间
     赔率<2.00 → 市场也认同对手, 不是"反投"
     赔率>6.00 → 概率太低, 风险不可控
     赔率在2.00-6.00 → 中等或偏冷门, 反投有正EV

当前状态: ACTIVE
  可用范围: R3(末轮)且动机分化的比赛
  不可用: R1首轮(双方等动力, 无冲突可检测)


---

## KB-18: 仓位分配 + 串关资格 → 见 betting-sop.md

> **v3.7.0**: 仓位由Pinnacle方向+离散收敛组合决定。详见 betting-sop.md。

## KB-19: 偏离检测 — 否定信号 (v3.7.0 校准)

> **v3.7.0 重写**: 偏离信号不再是冷门翻转的触发器，而是用于**撤销**Pin方向的信号。
> 废除主观赛事标签。全部基于可测量市场数据。

### 19.1 偏离信号 (6条)

```
以下信号出现时, Pin方向可靠性下降:

1. Pin方向热门赔率升水 >5%
2. 必发成交量方向  != Pin方向 (量价背离)
3. Kelly指数 > 1.05 (Pin方向过热)
4. 竞彩-Pinnacle gap > 8% (机构间严重分歧)
5. 30家离散度较开盘上升 >20% (发散)
6. 让球升盘≥0.5球但大小球不动

触发规则:
  偏离信号 ≥ 3条 → 方向强制为"跳过"
  偏离信号 = 2条 → 仓位降为 0.5x
  偏离信号 ≤ 1条 → 正常
```
  例: 开盘1.50 -> 收盘1.58 = 升水5.3% -> 偏离触发

偏离信号2: 量价背离
  测量: 成交量集中度 vs 赔率方向
  客观数据: touzhu页面必发成交占比
  条件: 某方成交>70% + 该方赔率未降/反升 -> 偏离触发

偏离信号3: 市场分歧
  测量: 30家均值方向 vs Pinnacle方向
  客观数据: 30家closing均值 vs Pinnacle closing
  条件: 均值与Pinnacle方向相反 -> 偏离触发

偏离信号4: 平局偏高
  测量: deVig(平) 绝对值
  客观数据: Pinnacle de-vig概率
  条件: >28% -> 偏离触发 (平局偏向)

偏离信号5: OU线下调
  测量: 大小球线移动
  条件: 6h内OU下调>=0.25 -> 偏离触发 (进球少)
```

### 19.2 综合判断（v3.5.2: 抬高触发门槛）

```
  偏离计数 0-2: 无翻转, 正常执行仓位规则(见betting-sop.md)
    依据: 179场回测中偏离≥2触发翻转仅53.8%, 抬高到≥3减少伪信号

  偏离计数 >=3: 强偏离, 确认冷门翻转
    动作: 反转系统方向 + 仅押单关

  翻转方向判断:
    deVig(平) > 28% + OU下调 -> 押平局
    量价背离 + 升水 -> 押反方向
    市场分歧 + 升水 -> 押反方向
```## KB-20: 跨赛事回测验证 → 用 football-backtest-workflow

> 回测验证框架已统一由 `football-backtest-workflow/` 子技能处理。
> 详见 analyst SKILL.md Step 13 赛后回测触发器。旧版 postmortem.md 已删除。

