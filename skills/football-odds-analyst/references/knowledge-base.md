# Knowledge Base Reference — Football Odds Analyst v3.5.0: OCI客观指标体系

> **Load trigger**: Read this file when SKILL.md instructs you to reference a specific section ($KB-N). Contains all detailed rules, formulas, trap definitions, scoring criteria, and methodology.
>
> **Reading strategy**: Start with KB-16 (OCI客观指标) + KB-18 (仓位决策) — v3.5.0核心. Then KB-6 + KB-7 for Step 10. KB-2 + KB-4 for traps/scoring. KB-10 for MBI.

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

### Logit-space Correction (v3.0.1 CORE CHANGE)

**Original v3.0 applied p ± X% additive correction in probability space, violating probability axioms. Corrected to logit space**:

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

> **v3.2.0 重分类**: 每条陷阱标注 A/B/C 三层分类。C=信息型(真实警告) / B=诱导型(可能强化原方向) / A=仓位型(噪音/忽略)。计数阈值(≥2→🔴)已废弃，以分类加权判定为准。

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

Each HIT → Category-based correction (see above). ~~≥2 traps on same match → 🔴 HIGH severity~~ (deprecated).

---

## KB-3: Twenty-Eight Universal Trap Rules

> **v3.2.0**: 每条标注 A/B/C 分类。C=信息型 / B=诱导型 / A=仓位型。分类加权规则同 KB-2。

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

## KB-4: Six-Dimension Scoring Model v3.0 — Continuous

> **v3.0.1 major upgrade**: Changed from binary (0/1) to 0–1 continuous scoring. Removed overlapping dimensions (old D2 and D6 both measured institutional consensus — merged). Full-score reverse penalty replaced with weight recalibration.

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

Default weights (v3.0.1, pending backtest calibration):
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

### Inflation Penalty (REPLACED v3.0.1)

**Old rule** (6/6→5) has been removed. That phenomenon indicates model calibration bias, not "perfect score is untrustworthy." Resolution:
- Recalibrate dimension weights via historical backtest
- If a dimension negatively correlates with outcome → flip or delete that dimension
- Pending 500+ match backtest

### Dimension Overlap Resolution (v3.0.1)

| Old Dim Pair | Overlap | Resolution |
|:---|:---|:---|
| D2 (Euro-Asian) + D6 (no hype) | Both measure institutional consensus | **Merged into new D2** |
| D1 (fundamentals) + D3 (opening) | Both involve strength assessment | D1: team-side; D3: market-side. Keep separate, apply 0.8× dampening if both in same direction |
| D4 (traps) + D2 (consensus) | Traps often detected from AH divergence | D4 triggered → D2 floor at 0.3 (trap implies disagreement) |

### Minimum Data Requirements

```
D1: requires shuju page (H2H + recent form) → if missing, D1 = 0.5 (neutral)
D2: requires ouzhi + yazhi pages → if missing, skip scoring entirely
D3: requires yazhi opening handicap → if missing, D3 = 0.5
D4: requires yazhi change timestamps → if missing, D4 = 0.5
D5: requires yazhi water data → if missing, D5 = 0.5
```

---

## KB-5: Fundamental Factor Weights (v2.0)

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

## KB-6: Unified Logit Correction Pipeline

> **v3.3.0 重大重构**: 废除概率空间加法（`base + Σ(corrections)`），全部迁移到 logit 空间。与 KB-10.8 MBI 在同一个 logit 管线中串行叠加，避免双轨冲突和边界溢出。

### 6.1 换算基准

中位锚定法（base 50%，logit=0）:
```
概率 +10%  →  logit +0.40
概率  +8%  →  logit +0.32
概率  +7%  →  logit +0.28
概率  +5%  →  logit +0.20
概率  +3%  →  logit +0.12
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

> **v3.2.0 重大改动**: 砍除 Poisson Top 3 比分精确输出。原因：Poisson 独立性假设在足球中不成立（进球概率随比分状态变化、上下半场 λ 不同、红牌/伤病扰动）。精确比分预测是虚假精度，庄家全场比分盘(Correct Score)的抽水远高于 SPF 盘，印证连庄家都无法精确定价。改为输出进球倾向三档判定。

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

Step 2: 应用校正因子（以下从原 14.x 简化保留）
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

### ⛔ 已移除

以下原 KB-7 内容因虚假精度已移除，不再参与任何计算：
- ~~Poisson 比分概率分布~~ (独立性假设不成立)
- ~~Top 3 比分及百分比~~ (误导用户产生确定性幻觉)
- ~~14.0c Host Historic xG~~ (缺乏跨赛事验证)
- ~~14.1 AH Water Calibration~~ (与 OU 判定无直接关系)
- ~~14.3 CS Market Calibration~~ (用 CS 盘校正，等于用庄家校正自己)
- ~~14.7 Multi-Period Fusion~~ (与进球倾向判定无直接关系)
- ~~14.8 Dispersion Confidence Penalty~~ (输出级别已不适用)
- ~~14.11 Draw Inertia~~ (与进球倾向无关)
- ~~14.0d Knockout Draw Baseline~~ (与进球倾向无关)
- ~~14.0e Ultra-Low Odds Fragility~~ (与进球倾向无关)

---

## KB-8: Supplementary Methodology

### Kelly Index
```
Kelly[H] = payout_rate × avgP[H] / (1/odds_H)
Interpretation: Kelly >1.05 → positive signal; all <0.90 → high vig, downgrade
```

### AH Live 4 Patterns
```
1. Late drop (AH −0.25 in 4h) → against dropping side (38% cover)
2. Late rise (AH +0.25 in 6h) → for rising side (65% cover)
3. Water rise >0.15 → against that side (42%)
4. Water drop >0.10 → for that side (genuine confidence)
```

### Heat Manipulation 3 Tactics
```
1. Water heating: water 1.95→1.75, AH unchanged + Betfair vol >60% → confirmed, reverse
2. Line suppression: opening ≥0.25 shallow + later rises → genuine signal
3. Water baiting: underdog water 2.30→2.00, AH unchanged → favorite is true direction
```

### Live AH Four Mantras
| AH Change | Water Change | Meaning | Action |
|-----------|-------------|---------|--------|
| Rise | Drop | Genuinely bullish | Follow fav |
| Rise | Rise | Bait (false) | Avoid/under |
| Drop | Rise | Bearish | Follow under |
| Drop | Drop | Suppress (false) | Bet favorite |

### OU Analysis
```
Expected goals = (GF_home×GA_away/avg + GF_away×GA_home/avg) / 2
  Expected > OU +0.5 → over; < OU −0.5 → under; within ±0.5 → neutral

Draw exclusion (all 4 true → low draw → over boost):
  1. Both no 0-0 in last 3  2. Combined GF >2.5
  3. OU 2.5 over water ≤1.85  4. No defensive fortress (Rule #27)

OU pathways:
  Over water drop + AH unchanged → +15% over | Over water rise >0.15 → check Betfair
  Water stable (<0.05) → initial analysis | OU 2.5→2.75 + over water drop → strong over
  OU 2.5→2.25 → market lean under | 1X2 2.XX-3.XX-2.XX → draw +8-12% → under
  AH deep (≥-1.5) + OU moderate → fav covers, limited goals
  AH shallow (±0.25) + OU high (≥3.0) → attacking, both score likely
```

### Signal Weight System
- 1X2: Kelly>1.05 (+12%) | BF divergence (−15%) | BF vol>65% (−10%)
- AH: Rise+water same (+15%) | Drop+water same (−15%) | Water drop>0.10 (+10%)
- OU: Expected>OU+0.5 (+15% over) | Draw exclusion all (+10% over) | 2-3-2 odds (−10% over)
- **Cap**: max 90%, min 10%

---

## KB-9: Post-Mortem (Historical)

### 28-Match Cycle (6/12–6/19)
- W/L accuracy: 18/28 raw → ~22/28 corrected (79.2%)
- Exact score: 3/24 (12.5%); Within 1 goal: 14/24 (58.3%)
- Mixed parlay: 6/6 tickets, +107.8% ROI; 11/28 matches (39%) correctly skipped

### Root Causes of Score Bias (±1 goal systematic error)
1. xG too conservative in extreme mismatches → 14.0b Stomp fix
2. Host nation xG explosion overlooked → 14.0c Host fix
3. Multi-factor nonlinear compounding → cross-trigger cap

### Key Individual Learnings
| Date | Match | Error | Lesson |
|------|-------|-------|--------|
| 6/19 | CZE 1-1 RSA | Called CZE win | Narrative compression → Step 1.5, Trap #7 |
| 6/19 | SUI 4-1 BIH | Called narrow | One match ≠ ability; 3+ match form needed |
| 6/19 | CAN 6-0 QAT | Predicted 2-0 | Host nation xG → 14.0c |
| 6/19 | MEX 1-0 KOR | Predicted KOR | WC history > continental ranking |
| 6/16 | All 4 draws | Called outcomes | Draw prob >30% = uncertainty; full skip rule |
| 6/13-14 | Debut upsets | Fav overconfidence | First-point hunger + heat discount (Rules #27-28) |

### 2022WC KO Backtest: 16 matches, SPF direction 94%, parlay +62% (intl) / +37% (JCL)
### Key: 70% of betting days correctly skipped — not hit rate, but selectivity

---

## KB-9b: 2022WC回测观察 (Historical)

> **数据源**: Pinnacle 收盘赔率 × 30家博彩公司 × 64场
> **基准准确率**: Pinnacle 34/64 = 53.1% | 开盘价 36/64 = 56.2% | 30家平均 = 53.1% (无额外信息)
> **⚠️ 重要声明**: 以下所有内容均为"待验证观察项"，非方法论修正。
>   加入规则的门槛: (1) 在 **≥2 个独立赛事** (如 2018 WC + 五大联赛) 被验证;
>   (2) 回测中不会降低已有系统的准确率;
>   (3) 通过 Step 13 权重合成模型的叠加测试 (新增因子不能与现有因子过度共线)。

---

### OBS-1: 淘汰赛平局概率偏差 (待验证, ⚠️ 64场单源, 逐阶段样本≤8)

| 阶段 | 场次 | 实际平局 | 市场定价 | 偏差 | 统计有效性 |
|:---|:---:|:---:|:---:|:---:|:---:|
| R16 | 8 | 25% | 23% | +2pp | ❌ 样本太小 |
| QF | 4 | 50% | 27% | +23pp | ❌ 4场 |
| SF | 2 | 0% | 29% | -29pp | ❌ 2场 |
| Final | 1 | 100% | 31% | +69pp | ❌ 1场 |
| 3rd | 1 | 0% | 27% | -27pp | ❌ 1场 |
| **淘汰赛合计** | **16** | **31%** | **25%** | **+6pp** | ⚠️ 边缘 |
| 小组赛(对照) | 48 | 21% | 24% | -3pp | 基准 |

**现状**: 淘汰赛+6pp vs 小组赛-3pp, 差异9pp。单看淘汰赛自身是小样本噪音 (每阶段1-8场)。
**建议**: 不写入规则。在淘汰赛分析时口头备注"注意平局概率可能被低估", 但不做自动修正。
**验证条件**: 需用 2018 WC (16场淘汰赛) + 欧冠淘汰赛 (32场) 验证后再定阈值。

---

### OBS-2: 小组赛60-70% "死亡区间" (待验证, 11场)

| 去水胜率区间 | 场次 | 准确率 | 判定 |
|:---|:---:|:---:|:---:|
| 50-55% | 9 | 56% | 随机 |
| 55-60% | 8 | **75%** | ✅ 良好 |
| 60-65% | 4 | 50% | ⚠️ |
| **65-70%** | **7** | **43%** | **⚠️ 低于基准** |
| 70-80% | 3 | 67% | 小样本 |
| >80% | 5 | 80% | ✅ 良好 |

**现状**: 60-70% 区间 11 场仅 45% 准确率, 低于 Pinnacle 整体 53%。但逐区间样本量太小。
**建议**: 不写入规则。在 Step 7 6D 评分中, 如果小组赛 + 去水胜率在60-70%之间 → 6D自动-1 (通胀警告)。已有 6D 通胀惩罚机制覆盖此场景, 不需要新增规则。
**验证条件**: 用 2018 WC 小组赛 + 2026 当前小组赛数据验证。

---

### OBS-3: 超低赔率(>70%)失误率 (已排除, 10场仅1个真冷门)

P≥70% 的比赛 10 场 80% 准确。唯一不可解释的冷门: 阿根廷 1-2 沙特 (P=86%)。
其余所有失误在模型误差的合理范围内。

**不形成规则的理由**: 
- 10场8正确 = 20%失误率, 在统计学上与模型预期一致
- 没有可复现的模式可供规则捕捉
- 如果强行加"反叙事检查" → 会把所有高置信度预测都打折扣, 反而降低准确率

**建议**: 删除"超低赔率反叙事检查"的构想。

---

### OBS-4: 开盘 vs 收盘分歧 (已排除, 2/64场无统计意义)

开盘56.2% vs 收盘53.1% 相差 3.1pp, 但:
- 开盘正确而收盘错误: 仅 2 场
- 开盘错误而收盘正确: 0 场
- 双双错误: 28 场 (88% 的错误场次)

这意味着: **当开盘和收盘方向一致时 (62/64场), 两者正确率完全相同**。
分歧仅发生在 2/64 场, 不足以支撑任何权重调整。

**不形成规则的理由**:
- "开盘权重0.6/收盘权重0.4"会改变 62/64 场本来一致的方向, 引入不确定性
- 2 场分歧中开盘都对, 但样本太小无法确认这是规律还是运气
- 30家市场平均 = Pinnacle收盘, 说明收盘已收敛到最优定价

**建议**: 删除"开盘尊重原则"构想。保持现状: Pinnacle收盘作为基准, 开盘仅作为 Step 5 背景参考。

---

### OBS-5: C档排除 (通过验证, 可嵌入已有 6D 系统)

| 去水胜率 | 场次 | 准确率 |
|:---|:---:|:---:|
| <50% | 19 | 32% |
| <45% | 16 | 25% |
| <40% | 7 | 14% |

**趋势清晰**: 置信度越低 → 准确率越低, 且下降速度远超线性。
**但现有 6D 系统已有覆盖**: 6D < 3 时已标记"有限参考", 6D ≤ 2 时标记"高风险跳过"。
去水<45% = 6D 自然≤3。不需要新增规则。

**建议**: 在 6D 评分指标中明确注解: "去水<45% 的比赛, 无论 6D 评分如何, 自动至少降1档"。
此条是唯一通过验证的观察项, 且不新增规则, 只是强化已有 6D 系统的执行边界。

---

### 总结: KB-9b 方法论影响

| 原"修正" | 结论 | 实际动作 |
|:---|:---|:---|
| #1 淘汰赛平局 | ❌ 不写入 | 口头备注, 待 2018 WC 验证 |
| #2 小组赛陷阱 | ❌ 不写入 | 6D 通胀惩罚已覆盖此场景 |
| #3 超低赔率 | ❌ 删除构想 | 不新增规则 |
| #4 开盘尊重 | ❌ 删除构想 | 保持 Pinnacle 收盘基准不变 |
| #5 C档排除 | ✅ 可强化 | 6D 评分边界注解: 去水<45% → 自动-1 |
    (a) 单场投注 (非串关) 且 Kelly 系数 < 0.08
    (b) 超过 2 个以上 C 档比赛同日出现 → 当日全跳过
```

### 64 场错误模式统计

| 错误类型 | 场次 | 占比 | 发生场景 |
|:---|:---:|:---:|:---|
| 热门→平局 (Home→Draw) | 8 | 27% | 小组赛, 热门1.50-2.50 |
| 客热→平局 (Away→Draw) | 7 | 23% | 淘汰赛居多 (5/7) |
| 大冷(主→客) | 9 | 30% | 小组赛叙事驱动 |
| 大冷(客→主) | 6 | 20% | 小组赛末轮/轮换 |

### 对 500.com 竞彩的校准
```
500.com 百家平均 SPF 与 Pinnacle 收盘方向完全一致 (64/64 相同)。
差别只在赔率绝对值 (竞彩抽水~11% vs 国际~3%):
  - 竞彩 SPF = 国际 SPF × (0.89~0.93)
  - 竞彩 2 串 1 过关 = 国际过关 × 0.85 (二次抽水)
  预测方向时不需要区分数据源。
```

---

## KB-10: MBI — Multi-Bookmaker Intelligence Framework

> **Rationale**: Pinnacle is the gold standard but not infallible. 30-bookmaker data from 500.com enables consensus-weighted analysis that captures signals Pinnacle alone misses.

### 10.0 Bookmaker Tier Classification

| Tier | Weight | Members | Characteristics |
|:---|:---:|:---|:---|
| **Sharp** | 0.55 | Pinnacle, bet365, IBC(沙巴) | Accept winning players, razor-thin margins, lead price discovery |
| **Asian** | 0.25 | 澳门, 皇冠, 利记, 易胜博, 12bet, 18bet | Regional capital flow, water-level sensitive, macro-policy influenced |
| **Retail** | 0.20 | 威廉希尔, 立博, Interwetten, 必发(exchange), 伟德, Bwin | Public sentiment, recreational volume, exchange reveals real money |

### 10.1 Sharp Consensus Score (SCS) — v3.2.0 revised

> **⚠️ v3.2.0 重要警告**: Sharp 机构调价不一定是"判断赛果"。Pinnacle 的商业模式是抽水驱动的做市商——调价可能仅是响应单边持仓压力（仓位驱动），而非信息驱动。SCS 信号必须配合 **10.3b 量价交叉验证** 使用，否则会系统性高估 Sharp 调价的信息含量。

```
For each outcome (H/D/A), across all 30 bookmakers:
  SCS_outcome = Σ(tier_weight_i × direction_i) / Σ(tier_weight_i)

  direction_i: +1 if odds↓, −1 if odds↑, 0 if |change|<noise_threshold
  
  noise_threshold = max(0.02 × odds_current, 1.5 × σ_historical)
    (adaptive threshold: at least 2% change AND exceeds 1.5σ of historical volatility)

  magnitude_weight = min(|change_pct| / 0.10, 1.0)
    (magnitude weighting: larger moves get higher weight, 10% change = full weight)

  time_decay = exp(−hours_since_change / 24)
    (time decay: half-life of 24h, changes closer to kickoff weighted more heavily)

  direction_i_weighted = direction_i × magnitude_weight × time_decay

Final SCS = SCS_favorite × 0.6 + SCS_draw × 0.2 + SCS_underdog × 0.2
  (favorite = lowest current odds among H/D/A, not fixed to home)
```

**v3.2.0 新增交叉验证要求**:
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

### 10.2 Dispersion Risk Index (DRI) — v3.0.1 revised

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

信息驱动 vs 混乱型离散 (v3.0.1 NEW):
  如果 DRI 高 AND Pinnacle 领涨 (Lead-Lag STRONG):
    → Info-driven dispersion (market repricing), DRI_signal halved
  如果 DRI 高 AND Lead-Lag = NOISE:
    → Chaos-type dispersion (retail noise), DRI_signal fully applied
```

**v3.0.1 improvements**:
- League-level quantile calibration (eliminates natural differences across leagues)
- Distinguishes information-driven vs chaotic dispersion
- Weights dynamically follow favorite side

#### 10.2.1 DRI Tier-Variance Analysis (NEW v3.0.3)

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

### 10.3 Lead-Lag Chain Detection — v3.2.0 revised

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

#### 10.3b Volume×Price Cross-Validation (v3.2.0 NEW)

> **核心逻辑**: Pinnacle 调价 ≠ 判断赛果。区分仓位驱动调价 vs 信息驱动调价 vs 庄家诱导。

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

### 10.4 Water Flow Analysis — v3.0.1 revised

**v3.0.1 major correction**: Water level changes must first be controlled to compare only under the same handicap level, otherwise water changes caused by handicap upgrades/downgrades will be misidentified as capital flow.

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

#### 10.4.1 Sharp Counter-Betting Asian Heat (NEW v3.0.3)

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

### 10.5 Exchange-Traditional Divergence — v3.0.1 upgraded

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

**v3.0.1 additions**:
- VWAP (volume-weighted average price) replaces pure volume ratio to distinguish "smart money" vs "retail chasing"
- Bookmaker P&L exposure detection — loss side requires odds adjustment, affecting future price direction
- Event size discount — minor events have extremely low Betfair volume, reference value approaches zero
- Composite signal: multiple dimensions synthesized rather than used individually

### 10.6 Kelly Consensus (v3.0.2 — Two-Framework Approach)

**Core correction**: Kelly index has no absolute directional interpretation — the same value means completely opposite things in different contexts. Must segment by scenario, by phase, and cross-validate.

#### 10.6.1 Basic Definition

```
Kelly = 赔率 × 市场去抽水真实概率
Meaning: the payout ratio the bookmaker owes if this outcome hits

Key insight: absolute Kelly values are meaningless → must interpret relative to each bookmaker's return rate
  Pinnacle 返还率 ~98%  → "高" = Kelly > 0.98
  竞彩返还率 ~89%      → "高" = Kelly > 0.89
  threshold = bookmaker_return_rate × 1.02
```

#### 10.6.2 Two Interpretation Frameworks (not "pick one" — "use different one per scenario")

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

#### 10.6.6 Application in Step 10

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

### 10.8 Integration into Step 10 (Probability Synthesis)

**v3.0.1 major correction**: Original v3.0 applied additive correction in probability space (p ± X%) which violates probability axioms (boundary violation, non-Bayesian update). Corrected to **logit-space correction**:

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

**Advantages of logit space**:
- Probabilities always stay within (0, 1) interval, never overflow
- Equivalent to log-odds multiplication in Bayesian updating, mathematically correct
- Correction magnitude naturally compresses near extreme probabilities (e.g., 90%+), consistent with intuition

### MBI Composite (#12) in logit space (v3.3.0)

> **v3.3.0 重大升级**: 引入四组相关降权 + 总量 cap，与 KB-6 统一 logit 管线串联执行。

```
#12 MBI Composite 作为 logit 偏移量:
  mbi_raw = SCS_raw + DRI_raw + LeadLag_raw + Kelly_raw + WaterFlow_raw + VolXPrice_raw

  各模块原始信号 (raw signal):
  SCS_raw (v3.2.0: 需量价交叉验证):
    SCS ≥ 0.70 + 量价确认 → +0.40
    SCS ≥ 0.70 + 量价不配合 → +0.15
    SCS 0.40–0.70 → 0
    SCS < 0.40 → −0.20

  DRI_raw:
    DRI < 15 → +0.20
    DRI 15–40 → 0
    DRI 40–70 → −0.35
    DRI > 70 → −0.70

  LeadLag_raw (v3.2.0: 带量价校正):
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

  VolXPrice_raw (v3.2.0):
    主动降价(信息驱动) → +0.17
    主动抬价(诱导) → −0.20
    被动调价(仓位驱动) → 0
    资金离场(被动抬价+量增) → −0.15
```

### Factor Correlation Dampening (v3.3.0 EXPANDED)

**v3.3.0 重大升级**: 原 v3.0.1 仅降权 SCS↔WaterFlow (太温和，只覆盖 ≤2 模块)。v3.3.0 扩展到四组，覆盖所有 15 项校正（KB-6 9项 + MBI 6项）。

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

### MBI Composite Final (v3.3.0)

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

### 10.9 Quick MBI Assessment (for report)

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

### 10.11 Data Quality Validation (NEW v3.0.2)

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

> Solves the "garbage in, garbage out" problem, ensuring model input signals are clean and comparable.

### 11.1 Dynamic Bookmaker Deduplication

```
血缘图谱（预设）:
  沙巴系: IBC(沙巴), 12bet, 18bet, M88
  Crown group: 皇冠, 利记, 易胜博, 明升
  Entain系: 立博, Bwin, Coral
  Kindred系: Unibet, 32Red
  Pinnacle系: 独立
  bet365系: 独立
  澳门系: 独立

动态血缘检测（每周）:
  Compute Pearson correlation of odds movement time series for all bookmaker pairs
  r > 0.95 + timestamp sync → identified as same source → update lineage map

去重权重:
  Cluster N same-source bookmakers into 1 independent node
  Node weight = original tier single-bookmaker weight × √N
  （√N 而非 N，避免过度稀释）

脏数据熔断:
  Single-bookmaker change > tier mean 3σ + no timestamp match → scrape anomaly, discard
  Post-dedup independent sources < 5 → DRI threshold raised 1 notch, Water Flow weight ×0.5
```

### 11.2 Cross-Bookmaker Water Normalization

```
Problem: Macau 0.90 water vs Pinnacle 0.975 water — direct comparison is meaningless
      Each bookmaker has different return rates; water levels cannot be directly compared

校准公式:
  Normalized water = raw water × (0.95 / bookmaker standard return rate)
  
  Example: Macau raw 0.90, return rate 0.92 → normalized = 0.90 × (0.95/0.92) = 0.929
      Pinnacle 原始 0.975, 返还率 0.98 → 归一化 = 0.975 × (0.95/0.98) = 0.945

Hard constraint: uncalibrated raw water MUST NOT be used directly in Water Flow direction stats
        All cross-bookmaker water comparisons MUST be normalized first
```

### 11.3 True Opening Odds Anchor

```
Abandon 72h early odds: low liquidity, mostly bookmaker trial balloons

Redefine "true opening odds":
  Take the odds node between 24-48h pre-match meeting these conditions:
    (a) 必发成交量首次突破 £100K  OR
    (b) 亚盘成交量首次突破 HK$100K

  Take the odds corresponding to whichever condition triggers first as true opening baseline
  If neither triggers within 24h → use 24h pre-match node as fallback

Comparison baseline: all subsequent "open→current" comparisons use this true opening uniformly
```

### 11.4 Event Tiering (Three-tier event parameter isolation)

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

> All logit corrections must correspond to specific bookmaker manipulation techniques.

### 12.1 Lead-Lag Retracement Validation

```
Retracement validation (anti-probing false moves):
  After lead bookmaker adjustment, within 4h retracement:
    > 50% → identified as probing false move → signal cleared
    < 20% + 趋势保持 → 信号确认生效
    20%-50% → 信号减半

  Asian event lead: SBO + Macau (NOT Pinnacle)
  Western event lead: Pinnacle (SBO as verification)
```

### 12.2 AH Level Change: True vs Trap Break

| Type | Condition | Logit | Trap # |
|:---|:---|:---:|:---:|
| **Genuine Up/Down** | Corresponding direction water ≤ 0.925 + Sharp tier moved first | ±0.18 | — |
| **Bait Up/Down** | Corresponding direction water ≥ 1.00 + Only Asian tier moved / Sharp static | **Opposite ±0.22** | #20/#21 |

```
时间权重:
  临场 1h 内信号 × 1.3
  开赛 24h 外早期信号 × 0.7

深盘约束:
  Ultra-deep odds SPF < 1.35, level changes mostly passive book-balancing
  → 信号权重强制 × 0.5
```

### 12.3 Betfair Order Book Resistance Wall

```
Resistance wall detection (real money standing firm):
  Favorite ask-1 ≥ bid-1 ×3 + sustained 30min + cancellation rate < 20% as price approaches
  → 触发阻力墙 → 热门方 logit −0.25

下盘阻力墙加权:
  Retail naturally favors the favorite → underdog resistance wall = clearer bookmaker intent
  → 反向校正 × 1.3

支撑墙正向信号:
  Favorite bid-1 ≥ ask ×2 + price steadily moving down
  → 真实资金突破 → logit +0.20

⚠️ Note: use only bid/ask level 1 (levels 2-3 are mostly market-maker ghost orders)
         Only enabled when Betfair volume > £100K (insufficient liquidity → order book meaningless)
```

### 12.4 Opening-Receiving Gap Analysis

```
初受盘差:
  At true opening node, Sharp vs Asian tier handicap gap ≥ 0.25 ball
  → 标记为「高波动场次」
  → 全场信号权重 × 0.5
  → 禁入串关核心胆

反市场操作加权:
  Condition: Betfair bid-1 ratio > 80% (public extremely bullish on favorite)
        + handicap counter-trend downgrade (bookmaker not playing along)
        + 无对应新闻解释
  → Identified as bookmaker active counter-market operation
  → Signal strength × 1.5 (bookmaker active behavior more informative than passive following)
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

### 13.2 Signal Confidence Tiering (A/B/C)

| Tier | Criteria | Kelly Coefficient | Single-Match Cap | Parlay Admission |
|:---:|------|:---:|:---:|:---|
| **A (Strong)** | ≥2 core modules same-direction resonance + no high-risk traps + 6D≥4 | 0.25× | 5% | Can be core anchor |
| **B (Medium)** | 1 core positive + no high-risk traps + 6D≥3 | 0.15× | 3% | Only pair with A-tier |
| **C (Weak)** | Weak module positive + has minor traps + 6D=3 | 0.08× | 1.5% | No parlay, light position singles only |

```
核心模块 = Lead-Lag / Water Flow / Exchange VWAP
High-risk traps = #13,#16,#19,#20,#21 (≥1 trigger = high risk)
```

### 13.3 Circuit Breakers

```
单日熔断:
  Daily actual loss ≥ 3% of bankroll → immediately stop all betting for the day → enter review

周度熔断:
  Weekly cumulative loss ≥ 8% of bankroll → suspend live trading → force shadow testing
  → 1 week consecutive shadow win rate ≥ 65% → resume live (half-size recovery period)

模块熔断:
  Single module 7 consecutive wrong calls → temporarily disable that module
  → Investigate root cause → restore only after fix
```

### 13.4 Risk Day Index & Auto-Empty

```
一级空仓（全日停手）:
  ① ≥3 matches trigger Trap #16 tier divergence on the day
  ② ≥4 matches trigger Trap #20/#21 level-change traps (collective bookmaker manipulation day)
  ③ 当日野鸡赛事占比 ≥ 70% + DRI均值 > 50
  ④ 2 consecutive days total loss + loss reaching daily cap ×2 (emotional cooldown)

二级降仓（仓位 ×0.5，仅打 2串1）:
  ① 当日必发异动场次占比 ≥ 30%
  ② 24h before transfer window closes / national team squad announcement day
  ③ League final 3 rounds relegation battles / cup 2nd leg with 1st leg margin ≥ 3 goals

串关相关性隔离:
  Same league + same kickoff time + same faction → max 1 match per parlay
  Prevent systemic black swan from killing entire parlay chain
```

### 13.5 Iron Rules (Uncrossable Red Lines)

```
❌ 临场 30 分钟禁令:
   Absolutely forbidden: any betting decision within 30min of kickoff
   All decisions MUST be finalized >1h before kickoff

❌ 禁止倍投:
   Chasing losses after losing streaks = #1 cause of account blowup
   Strictly follow Kelly coefficient, single-match hard cap 5%, NO exceptions ever

❌ 禁止无意义对冲:
   Buying both sides simultaneously in 竞彩 = double vig bleeding accelerated
   看不懂 → 直接空仓

❌ 串关赔率结构底线:
   串关几何平均 ≥ 1.50
   Parlays with 3+ legs all odds <1.35 FORBIDDEN (EV deeply negative)
   Ultra-low odds (<1.35): single bet only or M串N fault-tolerant base

❌ 竞彩 EV 底线:
   Under 0.89 return rate, single parlay EV ≥ −5% required for inclusion
   All EV uniformly uses slippage + return rate adjusted odds
```

### 13.5b M串N Risk Distribution Rules (v3.1.1 — Dynamic Position Sizing Engine)

> 静态 70/30 仅为教学模型。真实交易中的防守/进攻比例，是赔率结构、信号质量、风险暴露和账户净值四方博弈后的动态均衡解。以下四步决策树替代一切固定比例。

```
M串N 玩法强制约束:
  ✅ 3串4（3×2串1 + 1×3串1）: 3-4场候选时使用，容错1场
  ✅ 4串11（6×2串1 + 4×3串1 + 1×4串1）: 5+场候选时使用，容错2场
  ❌ N串1（无容错）: 绝对禁止，错一场即全损
  ❌ 候选<3场: 跳过当日（容错空间不足）

三不选相关性隔离:
  ❌ 同联赛: 同一串关 ≤1 场同联赛
  ❌ 同开球时间: 同一串关不含同时开球场次
  ❌ 同战意类型: 不含两场以上同类型生死战
  ❌ 同派系: 同一资本系/派系球队不入同一串关

杠铃赔率结构底线:
  底座（胆）: 1-2 场 A 类信号，赔率 1.50-1.80
  矛头（拖）: 1-2 场反市场/博弈信号，赔率 2.50-3.50

  串关赔率阈值表（强制）:
    | 类型   | 最低阈值         | 防御目标                | 未达标动作                  |
    |:------:|:---------------:|:----------------------|:--------------------------|
    | 2串1   | ≥ 1.80         | 覆盖滑点+容错回本底线    | 放弃串关→降级单关或等待      |
    | 3串1   | ≥ 4.50         | 抵消连乘滑点+进攻仓补偿   | 剔除弱信号→缩为2串1或空仓    |
    | 4串11  | 核心2串1≥1.80   | 确保错2场仍有回血能力     | 核心不达标→整个4串11计划作废  |

  滑点后复验: 将 3.5% 滑点乘入后重新检查上表，不达标执行右侧动作

赔率阈值数学逻辑（为什么达不到就不投）:
  一、2串1 ≥ 1.80 — 跨越真实盈亏平衡点:
    ① 返还率陷阱: 竞彩返还率 0.89，2串1 的理论公平赔率 = 1/(0.89²) ≈ 1.26
       1.26 仅为"不亏给庄家"的底线，不含时间/分析/资金成本
    ② 滑点侵蚀: 临场 3% 单场滑点，1.35×1.35=1.82 → 滑点后 1.71
       账面看起来 1.82，落地只剩 1.71。1.80 底线预留 3-5% 缓冲带
    ③ 容错回本刚需: 3串4/4串11 中 2串1 是防守核心
       若赔率仅 1.60，错 1 场时回收资金无法覆盖其他失败组合的本金
       1.80 = "错 1 场仍能保本或微利"的数学门槛

  二、3串1 ≥ 4.50 — 对抗联合概率衰减与长串毒性:
    ① 联合概率非线性崩塌: 3 场各 60% 概率 → 联合 21.6%
       3串1 理论公平赔率 = 1/(0.89³) ≈ 1.42，但这不含任何安全边际
    ② 滑点乘法放大: 单场 3% × 3 场 ≈ 0.913 倍 → 仅滑点吞噬近 9% 理论收益
       若目标赔率仅 3.50，扣除滑点+返还率后真实 EV 深度负值
       4.50 阈值预留 15-20% 安全溢价
    ③ 进攻仓风险补偿: 低命中率标的必须提供高赔率溢价
       < 4.50 的 Alpha 不足以补偿波动风险 → 不如全投 2串1 防守仓

  三、不达标不投的第一性原理:
    ① 避免温水煮青蛙: 低于阈值→长期必输，大数定律不可违
    ② 保护机会成本: 无效投注消耗本金，真正高EV信号出现时无筹码可用
    ③ 保护心理资本: 低赔容错失败 → 挫败感 → 倍投追损（毁灭性行为）
    ④ 维持系统可验证性: 坚守阈值 = 坚守系统纯洁性
       所有入池注单满足数学底线 → 复盘才有统计意义 → 模型迭代有据可依

C类信号禁入:
  C类（弱信号）→ 禁入任何 M串N 组合
  仅可极轻仓单关（cap: 1.5% bankroll）

单日限制:
  每日最多 1 组 M串N（3串4 或 4串11）
  ❌ 严禁"黑了再买一组追损"
```

#### 13.5b.1 Break-Even Reverse — 确定硬性防守底线

不看"想怎么分"，只看"数学要求必须怎么分"。防守仓的唯一使命是确保在"错1场"（次优结果）下，总回收资金 ≥ 总投入本金。

```
防守底线 = 总预算(B) / 最强2串1滑点后赔率(O_def)

案例: B=¥1000, O_def=2.72 → 防守底线 = 1000/2.72 ≈ ¥368
  → ¥368 必须压在最强 A+A 2串1 上
  → 剩余 ¥632 进入下一步分配池

⚠️ IF 防守底线 > B × 80%:
   → 赔率太低（全是深盘），串关数学上不具备容错价值
   → 直接放弃该串关，不要勉强出手
```

#### 13.5b.2 EV Differential Kelly Tilt — 决定剩余资金方向

打破"低赔=防守、高赔=进攻"的刻板印象。资金永远向 MBI 计算出的 EV 最高节点倾斜。

```
FOR 每个串关组合: EV_i = adjusted_odds × prob − 1
  （adjusted_odds 已包含 3.5% 滑点 + 0.89 返还率折扣）

IF EV(defense_strongest) > EV(attack_any) + 5%:
  → Sharp 与 Asian 机构严重背离，庄家在稳胆上露破绽
  → 剩余资金的 90% 继续加仓最强防守2串1
  → 进攻单只买最低限额 ¥2，保留火种

ELIF EV(attack_any) > EV(defense_strongest):
  → 模型捕捉到高价值冷门/阻力墙信号
  → 剩余资金的 40%-50% 分配给进攻仓（3串1 + 含拖2串1）

ELSE:
  → 按 EV 比例分配剩余资金
```

#### 13.5b.3 Risk Parity Cap — 用数学锁死进攻仓天花板

高赔率（进攻）天然伴随高波动。真正的风险均摊是"风险贡献度"的均摊，而非资金均摊。

```
组合 i 的权重 = (1/Odds_i) / Σ(1/Odds_j)

计算步骤:
  1. 对所有入选组合取赔率倒数
  2. 进攻仓上限 = Σ(高赔组合倒数) / Σ(所有组合倒数) × B
  3. IF 第二步进攻占比 > 风险平价上限 → 削减至上限，超出部分回流防守

案例:
  防守单@2.50: 倒数=0.40 | 进攻单@6.00: 倒数=0.16
  → 进攻上限 = 0.16/0.56 = 28.6%
  
  进攻单@15.00: 倒数=0.067
  → 进攻上限 = 0.067/(0.40+0.067) ≈ 14.4%（自动压缩）
```

此步作为**强制上限检查器**：无论信号多好，进攻仓不超风险平价上限。

#### 13.5b.4 Account Equity State — 心理账户量化调节

顺风局用利润冒险，逆风局守本金。将行为金融学的心理账户概念用量化纪律约束。

```
状态 A（净值创历史新高·盈利期）:
  提取超额利润的 20% 作为纯进攻基金
  进攻仓可上浮至风险平价上限（通常 ≤30%）
  逻辑: 全损也只伤利润，不伤本金

状态 B（净值回撤·连黑亏损期）:
  触发防守收缩机制
  进攻仓强制压缩至 ≤10% 或归零
  所有资金集中于最强防守2串1，或直接降级为纯单关
  ❌ 绝对禁止在回撤期放大进攻仓"搏一把回本"
     这是破产的最快路径，没有例外
```

#### 13.5b.5 四步动态仓位执行顺序（禁止跳过任何一步）

```
Step 1（算底线）→ Break-Even Reverse → 硬性防守底座金额
Step 2（看信号）→ EV Differential Kelly → 剩余资金向高EV倾斜
Step 3（控风险）→ Risk Parity Cap → 进攻仓 ≤ 数学上限
Step 4（看账户）→ Account Equity State → 连黑砍进攻/连红放利润
```

此四步为五步 SOP 的"第三步: EV计算与非对称注码"的核心子流程。

#### 13.5b.6 物理拆分规则（五步 SOP 第二步）

```
禁止终端机套餐:
  ❌ 绝不在终端机直接购买"3串4"或"4串11"
     系统强制的均注分配违背非对称资金原则

拆分规范:
  3串4 → 3 个独立 2串1 下单 + 1 个独立 3串1 下单
  4串11 → 6 个独立 2串1 + 4 个独立 3串1 + 1 个独立 4串1

独立定价:
  对每个拆分后的组合独立计算:
    滑点后赔率 = 账面赔率 × (1 − 3.5%)^N
    滑点后 EV = 滑点后赔率 × 模型胜率 − 1

入池门槛:
  拆分后任一组合的滑点后 EV < −5% → 直接删除该注
  例: 3串1 EV=−8% → 删除该注，仅保留 3 个 2串1
```

#### 13.5b.7 滚动风控与独立复盘（五步 SOP 第五步）

滚动风控（利用分时段比赛的时间差）:
```
若比赛分时段进行（如 18:00 / 20:00 / 22:00）:

18点场次结果出来后:
  - 该场黑了 → 立即取消或缩减所有未开赛的含该场的注单
  - 该场红了 → 后续正常执行，不追加

时间差止损逻辑:
  M串N 拆分为独立标的后的结构性优势
  单关不具备这种"看到部分结果后再调整后续注单"的能力
  这是容错拆分的额外风控收益
```

独立复盘规范:
```
赛后必须逐注拆解验证，禁止只看"今天整体盈亏":

逐注检查清单:
  1. 每注的 EV 是否兑现？(实际赔率 vs 模型预期)
  2. 每注的胜率是否符合模型预期？(命中率 vs 概率)
  3. 被 EV 门槛剔除的注单是否实际命中？
     若高概率命中 → 检讨 EV 门槛是否过于保守
  4. 滚动风控取消的注单是否最终命中？
     若命中 → 检讨实时止损规则的敏感度

复盘目的:
  区分两个失败原因:
    A) 分析模型失效 → 升级 KB / 调整权重 / 回测
    B) 赔率结构不合格 → 调整阈值 / 改善入场时机
  只有逐注复盘，胜率/EV/回撤等指标才具备统计意义
```

### 13.6 Shadow Testing Acceptance Criteria

```
### 13.6 Shadow Testing & Backtesting

#### Data Sources

```
Prediction side: analyst report → {date}_predictions.json (auto-saved after each analysis run)
  Fields: match_code, predicted_W/L, confidence_tier, each module signal contribution

Result side: 500.com wanchang → {date}_results.json (scraper --wanchang mode)
  URL: https://live.500.com/wanchang.php
  Fields: home_team, away_team, ft_score, ht_score

Matching: pair predictions with results by team names + date
  If exact match not found → fuzzy match (Levenshtein distance < 3)
```

#### Backtesting Workflow

```
1. After each analysis: auto-save predictions to .cache/backtest/{date}_predictions.json
2. After matches complete: scraper fetches https://live.500.com/wanchang.php?date={date}
   → parses completed match results → saves to .cache/backtest/{date}_results.json
3. Compare script (can be run anytime):
   - Load predictions + results for all dates in backtest range
   - Pair by team name + date
   - Compute metrics:
     □ Overall W/L direction accuracy
     □ Accuracy by confidence tier (A/B/C)
     □ Counter signal (traps/resistance wall) accuracy
     □ P(全灭) actual vs predicted
     □ Simulated EV (with 0.89 return rate + slippage)
     □ Per-module information gain (which modules add signal)
4. Calibrate:
   - If any dimension in 6D shows negative correlation → flag for removal
   - If DRI thresholds misaligned → adjust by league percentile
   - If fractional Kelly over/under-betting → tune coefficient
```

#### Minimum Sample Size

```
Before ANY parameter change: ≥ 100 matches per league tier
Before live trading: ≥ 300 matches total (all tiers combined)
Before removing a module: ≥ 50 matches where that module fired
```

#### Wanchang Fetch Mode (Scraper)

```bash
# Fetch completed match results for a date
python3 references/parser.py --wanchang --date 2026-06-20 --json

# Output: .cache/500com/{date}_wanchang.json
# Schema: [{date, time, league, home_team, away_team, home_rank, away_rank, ft_score, ht_score}]
```
  对应规则优化建议
```

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

### 13.8 竞彩市场转换层 (v3.3.0 NEW)

> **v3.3.0 新增**: 分析层（Pinnacle/Betfair, 返奖率 ~98%）与执行层（竞彩, 串关返奖率 ~71%）存在市场错配。所有概率分析必须在竞彩 EV 框架下重新评估。

#### 13.8a 竞彩 EV 转换公式

```
竞彩 EV = deVigProb × 竞彩赔率 × 串关返奖率(0.71) − 1

竞彩隐含概率: Q_h = (1/C_h) / (1/C_h + 1/C_d + 1/C_a) × R
```

#### 13.8b EV 阈值分级

```
EV > +0.05:       正期望，正常投
−0.05 ≤ EV ≤ +0.05: 边界，仅限小仓（≤1% 本金）
EV < −0.05:       负期望，标注 ⚠️ 警告，仓位 × 0.50
EV < −0.15:       严重负期望，🔴 禁止入选串关核心

示例（deVigProb=55% 主胜, 竞彩赔率 1.60, R=0.71）:
  EV = 0.55 × 1.60 × 0.71 − 1 = −0.375
  → 🔴 严重负期望 — MBI 可能仍说"方向看好"，但竞彩无正EV
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

> v3.1.2 | 扩展 MBI 框架的"庄家读心"层。不改变方向判定，只调节置信度。
> 从博弈对抗痕迹和跨市场错位中提取信号，而非仅依赖赔率数值。

---

### 14.1 Module 1: Pulsation (拉锯战指数)

**核心逻辑**：赔率变化的"犹豫程度"比"变化幅度"更能反映庄家真实意图。

#### 14.1.1 数据采集

时间窗口: 赛前 6h → 30min，每 30 分钟一帧（12 帧），Pinnacle ouzhi 时序
缓存: .cache/500com/{date}_pulsation.json
采样容错: F 分母 = 实际有效间隔数 | 后 2h 帧赋予更高权重

#### 14.1.2 核心指标

| 指标 | 计算 | 含义 |
|:---|:---|:---|
| 振荡频率 F | 方向改变次数 / (有效采样数 − 1) | 高频 ≥ 0.4 = 犹豫 |
| 净位移 D | \|首末差值\| / 首值 × 100% | 低幅 < 1.5% = 微弱 |
| TWQ | F / (D + 0.001) | TWQ > 50 = 严重拉锯 |

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

**Score 映射（只输出 [-1,+1]，不直接改信度）：**

| 状态 | 条件 | Score |
|:---|:---|:---:|
| 真实推动 | 赔率降(升) + 必发量暴增(>2x) | +1.0 |
| 量在价先 | 赔率未变 + 必发量已暴增 | +1.0 |
| 虚假信号 | 赔率降(升) + 必发量萎缩/平平 | −1.0 |
| 散户驱动 | 赔率降 + 散户渠道量增 + 必发平平 | −0.5 |
| 无可比性 | 必发缺失或量极低 | 0.0 |

#### 14.2.2 CD — Channel Divergence (渠道背离)

**基准锚点（铁律）：所有修正只作用于 Sharp 层指向的方向。**

**Score 映射：**

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

### 14.4 回测

**核心指标**: 信息增益率 = Σ(MPC修正后命中率 − 修正前) / 受影响的场次数
MPC > 0.3 场次中修正后命中率提升 ≥ 3% → 模块有效

**Veto/CB 命中率**: CB 触发场次中正确否决的比例 ≥ 60% → 有效

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

## KB-15: External Signal Injection Roadmap

> **核心理念**: 赔率不是信息源，是庄家的风险管理工具。真正的 edge 在赔率之外。
> 本模块为长期演进路线图，标注实施优先级和代价。

### 15.1 伤停/首发信息自动抓取 (优先级: ⭐⭐⭐)

**逻辑**: 赛前 1-2h 首发公布 → 提取关键位置变化 → 对比赔率变动时间戳。

```
执行流程:
  1. 赛前 2h: 抓取 500.com 伤停页面或竞彩官网首发
  2. 提取: 主力前锋缺阵? 核心中场轮休? 防线核心停赛?
  3. 时间戳对比:
     赔率在首发公布前已调整 → 信息提前泄露，市场已定价 → 无 edge
     赔率在首发公布后仍未调整 → 市场未反应 → 真正的 edge
  
  4. 量化:
     关键缺阵 (前锋/中场/门将) → 对应方 logit −0.15
     双核缺阵 → logit −0.30
     防线重组 (≥2人换位) → 对方 logit +0.10
```

**数据源**: 500.com shuju 页面已有伤停信息（部分联赛）。竞彩官网赛前1h 公布首发。
**实现代价**: 低。在 Step 1.5 反叙事筛查中嵌入首发抓取逻辑。

### 15.2 赛程密度体能模型 (优先级: ⭐⭐)

**逻辑**: 7 天 3 赛的球队体能衰减高度可预测，但赔率定价滞后。

```
体能扣分表:
  7 天 2 赛 (正常): ×1.00
  7 天 3 赛 (密集): ×0.92 (总进球倾向降低)
  7 天 4 赛 (极端): ×0.85
  
  双线作战 (联赛+杯赛): 自动降 1 档
  跨洲旅行 (>3h 时差): 自动降 1 档
  
  轮换概率:
    密集赛程 + 对手为弱旅 → 轮换概率高 → 深盘穿盘概率降低
    密集赛程 + 对手为强敌 → 轮换概率低 → 体能衰减影响防守端
```

**数据源**: 比赛日程公开数据，无需外部 API。
**实现代价**: 中。需要在 Step 2 基本面分析中嵌入赛程体能模块。

### 15.3 天气/场地信息 (优先级: ⭐)

**逻辑**: 对特定联赛（北欧、英冠冬季、J 联赛雨季），天气对进球数的预测力高于赔率。

```
天气影响矩阵:
  暴雨/大雪 → 总进球倾向 −1 档（偏小球）
  高温 >32°C → 总进球倾向 −1 档（体能消耗加速）
  大风 >8 级 → 技术型球队受影响 > 力量型球队
  人工草皮 → 客队不适应 → 主场优势 +5%
  场地积水 → 长传冲吊队受益，控球队受损
```

**数据源**: OpenWeatherMap API 或比赛地天气网页抓取。
**实现代价**: 中高（需要稳定 API 或定时抓取）。

### 15.4 实施优先级总结

| 信号源 | 预期信息增益 | 实现代价 | 状态 |
|:---|:---:|:---:|:---|
| 首发伤停 | **高** — 信息驱动，庄家常滞后 | 低 | 📋 待实现 |
| 赛程体能 | 中 — 可预测但庄家也在看 | 中 | 📋 待实现 |
| 天气场地 | 中低 — 特定联赛有效 | 中高 | 📋 待实现 |
| NLP 新闻 | ⛔ 黑名单 — 新闻是庄家鱼饵 (KB-13.7) | — | 永久排除 |

### 15.5 与外源信号联动

所有外源信号统一在 Step 1.5 (反叙事筛查) 和 Step 2 (基本面分析) 中注入。
输出时在「信号来源分解」面板的第四行「赔率之外还需要知道的」中显性标注。
空白 = 边界明确 → 提醒用户该判断完全基于赔率。

---

## KB-16: 客观指标分析 — 5维度变化测量 (v3.5.0)

> **v3.5.0 重构**: 废除全部13条静态FVS规则和固定+1/+2/+3分数体系。
> 改用5个可测量客观维度的变化方向和幅度，每条规则的权重从179场历史数据中查表获得。
> 核心原则: 不依赖任何主观标签(赛事/淘汰赛/日期)，只问"市场赔率怎么变了"。

### 16.1 设计原则

```
客观指标分析的方向判定:
  系统方向判定仍来自 Pinnacle 收盘赔率(谁赔率低→谁是热门)
  客观指标不改变方向判定，只改变仓位信心和金额

权重获取方式:
  对每场比赛、每个指标 → 在179场历史库中查找相同变化模式的场次
  取该模式下的历史命中率作为指标权重
  例: Pinnacle降水>3% + 量增>100% → 历史有15场同样模式 → 命中13场(87%) → 权重+0.87

最终决策:
  5个指标加权平均 → 综合信心分 → 匹配三档仓位(核心/标准/跳过) + 冷门翻转条件

> 数据校准依据: 179场跨赛事(2022WC+2018WC+2024Euro)
> 每次回测后自动更新指标权重表
```

### 16.2 5个客观变化指标

```
编号: OCI-1 至 OCI-5 (Odds Change Indicator)

OCI-1: Pinnacle 赔率变轨
  测量: 开盘赔率 → 当前赔率的变化方向 + 幅度
  客观数据: opening_home/draw/away  vs  closing_home/draw/away
  分类:
    降水 ≥3%(热门赔率↓): 机构在降低赔付 → 对热门有信心
    升水 ≥3%(热门赔率↑): 机构在提升赔付 → 吸引了抛压/信息流出
    持平(变动<3%): 市场稳定，无增量信息
  权重查表: 在179场中按(降水/升水/持平)分组，取各自历史命中率

OCI-2: 市场共识变轨
  测量: 30家博彩公司当前均值的 6h 变化方向
  客观数据: 30家 closing 均值 vs opening 均值
  分类:
    方向与Pinnacle一致 → 市场共识形成
    方向与Pinnacle不一致 → 分歧(分歧幅度=差值%)

OCI-3: 成交量结构
  测量: 必发成交占比 + 赔率同步性
  客观数据: touzhu(必发)页面成交量分布
  分类:
    量价同步(成交增+赔率降): 真金白银跟踪 → 正向确认
    量价背离(成交增+赔率不降/反升): 对赌/过热 → 警告信号

OCI-4: 机构离散度
  测量: 30家赔率的标准差/极差的 6h 变化
  客观数据: shuju 页面的离散值
  分类:
    收敛(离散度↓): 机构意见趋于一致 → 市场信心增强
    发散(离散度↑): 机构分歧扩大 → 不确定性增加

OCI-5: AH/OU 线验证
  测量: 让球线和大小球线是否同步移动
  客观数据: yazhi(亚盘)和 daxiao(大小球)页面的线位变化
  分类:
    同步移动(AH+SPF方向一致): 盘口合拢 → 支持SPF方向
    独立移动(AH+SPF方向不同): 盘口分裂 → 有独立信息
```

### 16.3 权重查表流程

```
对一场新比赛:

  步骤A: 计算5个OCI指标的当前变化方向和幅度
  步骤B: 对每个OCI, 在179场历史库中查找:
    - 找出历史上与该场比赛"该指标变化模式相同"的场次
    - 取这些场次的平均命中率 = 该指标权重
  步骤C: 5个权重加权平均 = 综合信心分
    权重为负(命中率<50%) → 该指标拉低信心
    权重为正(命中率≥50%) → 该指标提升信心
  步骤D: 综合信心分 → 匹配三级仓位或冷门翻转

模式匹配规则:
  - 每个OCI仅用"变化方向+幅度"匹配，不用球队/赛事/日期
  - 最少要求3场历史匹配，<3场则该指标标记为"样本不足"降权50%
  - 随时间积累，历史数据库每增加50场更新一次权重表
```

---

## KB-17: DRM — Draw Risk Module (v3.5.0)

> **v3.5.0 清理**: 废除DRM-7(淘汰赛+2)，删除样本不足的DRM-9/10。DRM改为OCI(客观指标)的补充因子，不再独立计分。

### 17.1 功能定位

```
DRM 不再独立产生分数，而是为 OCI-4(离散度)和OCI-5(AH/OU验证)提供补充:

  OCI-4 + DRM判断:
    离散度收敛 + deVig(平)>25% -> 共识性平局 -> 仓位x0.70
    离散度发散 + deVig(平)>25% -> 分歧性平局 -> 仓位x0.85

  OCI-5 + DRM判断:
    AH线稳定 + OU线下调 -> 进球少、平局增
    AH线移动 + OU线稳定 -> 盘口分裂，有独立信息

  平局判断阈值:
    deVig(平) > 28% -> 仓位x0.80
    deVig(平) > 32% -> 改推双方进球或大小球
```

### 17.2 保留的 DRM 因子

```
DRM-1: deVig(平)检测
  测量: Pinnacle去抽水后的平局概率
  阈值: >28% -> 仓位x0.80 / >32% -> 换玩法
  变化感知: 若deVig(平)在6h内上升>2pp -> 额外x0.90

DRM-2: OU线检测 (改为变化测量)
  OU线<2.0 -> 低进球预期 -> 注意平局
  OU线从2.5降至2.25(6h内) -> 市场下调进球预期 -> 注意平局

DRM-3: 近期平局惯性
  任一方近5场>=2平 -> 注意
  双方上轮均平 -> 加强注意
```

### 17.3 已废除规则（v3.5.0）

```
- DRM-7 淘汰赛阶段 +2: KO平局率未显著高于常规赛，DRM=4时命中率仅46%
- DRM-9 平局即出线: 样本不足
- DRM-10 夺冠反脆弱: 样本不足
- DRM-4/5/6/8: 样本不足，暂保留但不激活
```

## KB-18: 三档仓位引擎 — 由信而赌 (v3.5.0)

> **v3.5.0 更新**: 新增第四档(冷门翻转)，仓位逻辑改为由OCI(客观指标)加权分驱动。

### 18.1 四档定义

```
仓位由OCI加权综合信心分决定:

  信心分 >= 65% -> 🔥 核心仓位 (全仓, 入串关核心)
    条件: 5个OCI中>=3个正向, 无偏离信号
    来源: FVS=2+DRM=0模式(80%命中)

  信心分 50-65% -> ✅ 标准仓位 (半仓, 入容错腿)
    条件: 多数OCI正向但有1个中性
    来源: FVS=0+DRM=0模式(52%)

  信心分 < 50% 且 偏离信号<2 -> 🚫 跳过
    条件: OCI多数负向或中性, 无偏离
    来源: FVS=1或DRM>=2模式(<50%)

  信心分 < 50% 且 偏离信号>=2 -> 🔄 冷门翻转
    条件: OCI指向负面, 且偏离检测触发
    动作: 反转系统方向, 押冷门/平局
    来源: FVS=0+DRM=4(40%平率) + FVS=1(58%冷门)
```

### 18.2 偏离检测条件

```
满足>=2条即触发冷门翻转:

  [ ] Pinnacle升水 > 3% (热门赔率在上升)
  [ ] 成交量与赔率方向背离 (量增但赔率不降)
  [ ] 30家均值方向与Pinnacle方向不一致
  [ ] deVig(平) > 28% (平局概率高)
  [ ] OU线下调 > 0.25 (进球预期降低)

翻转后动作:
  平局偏向(>=3个偏离指向平局) -> 押平局
  逆转偏向(<3个偏离但多数指向逆转) -> 押反方向
  仓位: 标准仓位x0.50 (因为冷门命中率约40-58%)
```

### 18.3 串关资格

```
  核心仓位: 可入串关核心
  标准仓位: 仅入容错腿
  跳过: 不入任何串关
  冷门翻转: 仅单关 (翻转信号不够强, 不能串)
```

## KB-19: 客观偏离检测 + 冷门翻转触发 (v3.5.0)

> **v3.5.0 重写**: 废除赛事类型感知(主观标签), 改为纯客观偏离检测。
> 偏离信号 = 冷门翻转的触发条件。

### 19.1 偏离信号矩阵

```
偏离信号1: Pinnacle升水
  测量: 热门方收盘赔率 / 开盘赔率 - 1
  客观数据: pinnacle opening_home/draw/away vs closing_home/draw/away
  阈值: >= +3% -> 偏离信号
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

### 19.2 综合判断

```
  偏离计数 0-1: 无偏离, 正常执行三档仓位
  偏离计数 2:  进入冷门翻转候选, 需判断平局vs逆转
  偏离计数 3+: 强偏离, 确认冷门翻转

  翻转方向判断:
    deVig(平) > 28% + OU下调 -> 押平局
    量价背离 + 升水 -> 押反方向
    市场分歧 + 升水 -> 押反方向
```## KB-20: 跨赛事回测验证框架 (v3.4.0)

> **v3.4.0 新增**: 每次技能修正后的强制性验证流程。
> 数据源: `.cache/tournament_data/wc2018_backtest.json` / `euro2024_backtest.json` / `wc2022_backtest_data.json`

### 20.1 三关验证流程

```
任何规则修改、参数调整、阈值变更后，必须过三关:



## KB-20: 跨赛事回测验证框架 + 模式库查表 (v3.5.0)

> **v3.5.0 更新**: 新增OCI模式库查表流程。

### 20.1 OCI模式库查表流程

```
每次执行OCI分析时:
  1. 提取5个OCI指标的当前变化方向+幅度
  2. 在历史数据库中查找相同变化模式的场次
  3. 取这些场次的平均命中率作为该指标权重
  4. 最少要求3场匹配, 不足3场则降权50%
  5. 每新增50场数据自动更新权重表
```

### 20.2 三关验证

```
第一关: 改善（Improvement）
  - 所有三个赛事回测命中率均不下降（允许持平）
  - 综合命中率提升 ≥1%
  - 核心仓位（FVS=2+DRM=0）命中率不下降

第二关: 一致性（Consistency）
  - 三个赛事改善方向一致（允许幅度不同，不允许方向相悖）
  - 若某一赛事退步 → 该赛事的校准因子须独立调整
  - 若两赛事退步 → 回滚改动

第三关: 统计显著性（Statistical Significance）
  - 改善不是由 ≤3 场极端比赛驱动（5-折交叉验证）
  - 核心仓位样本量 ≥20 场
  - 否决精确率 ≥40%
```

### 20.2 回测执行脚本

```bash
# 跨赛事回测
cd ~/Desktop/足彩
python3 cross_tournament_backtest.py

# 查看报告
open 跨赛事FVSDRM回测报告.html
```

### 20.3 版本升级检查清单

```
每次升级v3.x.x时:
□ 三个赛事数据完整（WC2022/WC2018/Euro2024）
□ cross_tournament_backtest.py 已更新为新规则
□ 三关验证全部通过
□ 回测报告已生成
□ KB-9（复盘）已更新
□ 如改善 >5% → 考虑推送git
```

