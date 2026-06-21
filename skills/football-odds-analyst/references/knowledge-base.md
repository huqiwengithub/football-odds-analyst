# Knowledge Base Reference — Football Odds Analyst v2.9

> **Load trigger**: Read this file when SKILL.md instructs you to reference a specific section ($KB-N). Contains all detailed rules, formulas, trap definitions, scoring criteria, and methodology.
>
> **Reading strategy**: Start with KB-2 (traps) + KB-4 (6D) — used every match. Then KB-6 + KB-7 for Step 10. KB-8 + KB-9 are supplementary.

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

**v3.0.1**: 升级为 Shin 去抽水算法。简单比例法会系统性高估热门方概率（热门-长偏差随赔率差距扩大）。

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

**原 v3.0 在概率空间做 p ± X% 的加法校正，违反概率公理。修正为 logit 空间**：

```
Step 1: De-vig → base probability P
Step 2: Convert to logit space
  logit(P) = ln(P / (1 − P))
  
Step 3: Apply all corrections in logit space
  logit' = logit + Σ(Δlogit_i)
  其中 Δlogit_i 为各校正因子的 logit 偏移量

Step 4: Convert back to probability
  P' = 1 / (1 + e^(−logit'))

Step 5: Normalize across H/D/A
  P_final[i] = P'[i] / Σ(P')
```

| Logit Δ | 对应概率偏移 (以 50% 为中心) | 典型信号 |
|:---:|:---|:---|
| +0.10 | +2.5pp | 弱正向信号 |
| +0.20 | +5.0pp | 中正向信号 |
| +0.40 | +10.0pp | 强正向信号 |
| +0.70 | +17.0pp | 极强正向（仅用于多重确认）|

**logit 空间优势**：概率天然有界 (0,1)，等价于贝叶斯更新，极端概率附近校正幅度自动压缩。

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

| # | Pattern | Trigger | Risk |
|:--:|---------|---------|------|
| 1 | Deep odds, shallow handicap | Gap ≥0.25 ball, theoretical AH deeper than actual | Draw/away upset |
| 2 | Shallow odds, deep handicap | Gap ≥0.25 ball, actual deeper than theoretical + SBOBet water >1.00 | Straight outcome |
| 3 | Draw odds dropping + deep handicap | Draw odds ↓ ≥8% from open + AH ≥0.25 deeper than theoretical | Hidden draw |
| 4 | Late odds drop + handicap retreat | Home odds ↓ ≥5% in last 6h + AH retreats ≥0.25 (opposite direction) | Fake news |
| 5 | Favorite deep handicap + water >1.05 | AH ≥0.75 ball + SBOBet water ≥1.05 at close | Favorite struggles |
| 6 | Underdog drops for no reason | Underdog odds ↓ ≥10% + ZERO fundamental support (WebSearch verified) | Minimal reference value |
| 7 | Narrative-driven moderate compression | Compression 5–15% + draw true prob >25% + driver is "known news" | Overvalued favorite |
| 8 | Same-direction compression + AH static | Home odds ↓ ≥5% + AH unchanged | Market lean |
| 9 | Opposite-direction odds vs AH | 1X2 moves one way, AH opposite | Strong trap |
| 10 | SBOBet diverges from Pinnacle | SBOBet AH deviates ≥0.25 from Pinnacle | Asian sharp disagrees |
| 11 | bet365 limit crash | bet365 limit drops >30% in 2h, odds unchanged | Risk aversion |
| 12 | Opening line extreme | Opening AH ≥1.5 balls | Market overconfidence |
| 13 | Illegal betting site manipulation 🚩 | Unregulated bookmaker >0.15 from Pinnacle + limit drops >50% + market suspended (≥2 signs) | RED FLAG — skip |
| 14 | Three-bookmaker consensus break | All 3 diverge ≥0.25 on same market | Systemic uncertainty |
| 15 | Referee-driven odds shift | Referee >0.35 penalties/game or >5.0 cards/game + physical team | Adjust OU ±0.25 |

Each HIT → ±10% correction. ≥2 traps on same match → 🔴 HIGH severity.

---

## KB-3: Twenty-Eight Universal Trap Rules

```
 1: Odds drop ≥8% without fundamentals → trap
 2: Deep open (AH ≥1.0) + never retreat in 24h → true signal
 3: Opening shallow (gap ≥0.25) + paper strength clear → upset warning
 4: Same-direction multi-bookmaker → weight ×1.5
 5: Pinnacle leads movement (>5 min ahead of others) → real signal
 6: Random single-bookmaker deviation ≥0.10 → ignore
 7: Late odds + AH both reverse in last 2h → trap
 8: Odds ↓ ≥5% + AH retreats ≥0.25 → trap
 9: bet365 moves opposite Pinnacle → retail-sharp conflict
10: Odds static (σ<0.03) + water volatile (σ>0.08) → indecision
11: Narrative compression 5–15% → market overreacting (see KB-2 Trap #7)
12: Suspension paradox → suspended teams play MORE defensive
13: Illegal betting site — match 2+ red flags → SKIP (see KB-2 Trap #13)
14: Referee influence → adjust expectations (see KB-2 Trap #15)
15: No fundamental event → movement is noise
16: 1X2 odds drop → verify AH direction match
17: Three-bookmaker consensus strong (≤0.15 ball) → high confidence
18: deVigProb(home) >75% → unusual; check narrative
19: deVigProb(draw) >30% → market uncertain; expect draw risk
20: deVigProb(away) >40% → strong away signal; verify AH
21: Extreme compression >15% → overreaction
22: 1X2 spread across 3 bookmakers >0.30 → uncertainty penalty
23: AH spread across 3 bookmakers >0.50 → high divergence
24: Both teams WC debut → draw prob floor 28%
25: Same-direction water rise >0.15 on all 3 → genuine flow
26: Favorite odds <1.25 → lay risk; max confidence 80%
27: Defensive fortress (qualifying GA<0.5 or 5+ clean sheets) → +3% direction, +15% under
28: Heat discount (>35°C or humidity >80%) → fade favorite; underdog +5% prob
```

---

## KB-4: Six-Dimension Scoring Model v2.0

| Dim | Criterion | Score 1 (PASS) | Score 0 (FAIL) |
|:---:|-----------|----------------|----------------|
| 1 | Fundamental logic | Injuries/motivation/form/H2H align with market + Back-to-Wall passed + narrative clean | (a) Back-to-Wall seeker unaccounted, (b) favorite narrative-driven, (c) fundamentals contradict market |
| 2 | Euro-Asian match | AH gap ≤0.25 for ALL 3 bookmakers + no bookmaker diverges >0.50 | Any gap >0.25 or bookmaker diverges >0.50 |
| 3 | Opening objective | Opening matches strength (no artificial >0.25 ball) + narrative check passed | Opening deliberately deep/shallow OR compression from "known news" |
| 4 | Late movement clean | No trap triggered + no harvest pattern + late 1h passes authenticity rules | Any trap or harvest pattern detected |
| 5 | Water level logical | Changes explainable by fundamentals + draw prob ≤25% + water σ <0.06 | Unexplained water changes OR draw prob >25% with favorite <2.00 OR water σ >0.06 |
| 6 | No one-sided hype | Multi-bookmaker consistent + SBOBet gap <0.25 + bet365 spread <0.05 + no anomalous limit drops | Bookmaker diverges >0.25 OR bet365 spread >0.10 OR limit drops >30% in 6h |

### Thresholds Summary

| Dim | Metric | Pass | Data |
|:---:|--------|:---:|------|
| 2 | Max AH gap (theoretical vs actual) | ≤0.25 | All 3 bookmakers |
| 4 | Traps hit | 0 | KB-2 + KB-3 |
| 5 | Draw probability | ≤25% | De-vigged from Step 3 |
| 5 | Water σ | <0.06 | 24 data points |
| 6 | SBOBet-Pinnacle AH gap | <0.25 | 3-bookmaker comparison |
| 6 | bet365-Pinnacle 1X2 spread | <0.05 | 3-bookmaker 1X2 |

### Inflation Penalty
- **Raw score of 6 → effective score = 5** (6/6 paradoxically indicates overconfident narrative; historically 0% accuracy)
- Score ≥4 → direction confidence +3%. Score ≤2 → all degrade.

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

## KB-6: Weighted Probability Synthesis Model

**Base**: De-vigged home/draw/away from Pinnacle (Step 3).

**Apply corrections in order, then NORMALIZE:**

| # | Correction | Magnitude | Condition |
|:--:|------------|:---------:|-----------|
| 1 | Euro-Asian trap hit | ±10% | Any of 15 traps triggered |
| 2 | Opening odds law hit | ±8% | Any of 4 laws triggered |
| 3 | Late movement authenticity | ±7% | Pass/fail check |
| 4 | Compression intensity | +7/+7/+3.5/0% | Extreme/Strong/Moderate/Weak |
| 5 | Fundamental alignment | ±5% | Weighted fundamental match |
| 6 | Back-to-Wall effect | draw +5~8%, away +5% | Seeker triggered |
| 7 | Narrative discount | favorite −5% | Odds driven by "known news" |
| 8 | 6D score | ±3% | ≥4→+3%; ≤2→−3% |
| 9 | SBOBet divergence | ±3% | Asian sharp vs Pinnacle gap |
| 10 | Market liquidity | confidence × (0.85–1.00) | KB-8 indicators |
| 11 | External factors | xG × (1 ± penalty × 0.03) | KB-8 weather/travel/rest |

**Normalize** (MANDATORY):
```
raw = base + Σ(corrections)
total = raw_home + raw_draw + raw_away
predicted = raw / total × 100%
```

---

## KB-7: Score Prediction Refinements (14.0–14.11)

### Base xG Flow
```
1. home_xG = (OU_line / 2) + (AH_line × 0.5)
   away_xG = (OU_line / 2) − (AH_line × 0.5)
2. Apply 14.4 correction (team form, WebSearch required)
3. Apply external factors (14.10)
4. Adjust by probability: home_xG ×= (pred_home/50%), away_xG ×= (pred_away/50%)
5. Poisson: P(home:n,away:m) = Poisson(n, home_xG) × Poisson(m, away_xG)
6. Rank → top 3 scores
```

### 14.0a Away xG Strong-D Discount
- Away def tier "elite" (GA<0.8/game): away_xG ×0.85, home_xG ×0.92
- Away def tier "ultra-elite" (GA<0.5/game): away_xG ×0.75, home_xG ×0.92

### 14.0b Stomp xG (Extreme Favorite)
- If pred_home ≥70% AND AH ≥1.5: home_xG += 1.5×(pred_home−70%)/30% (max +1.5), away_xG −= 0.3 (floor 0.15)

### 14.0c Host Historic xG
- World Cup host nation → home_xG += 1.0

### 14.0d Knockout Draw Baseline
- KO matches: draw probability floor = 28%

### 14.0e Ultra-Low Odds Fragility
- If any outcome odds <1.25: max confidence = 80%; score range +1 goal each side

### 14.1 AH Water Calibration
- home_xG ×= (1 / home_ah_water), away_xG ×= (1 / away_ah_water)

### 14.2 OU Price Calibration
- adjusted_OU = OU_line + (OU_home_water − 1.90) × 0.5; recalibrate if ≠

### 14.3 CS Market Calibration
- weighted_OU = Σ(score_total × CS_implied_prob); if |weighted_OU − OU_line| >0.25 → override

### 14.4 xG Factor Correction (team form)
- Requires WebSearch for each team's last 6-match avg GF/GA
- home_xG_adjusted = home_xG × (GF_home/avg) × (GA_away/avg); same for away
- If WebSearch unavailable → skip with note "market-only xG"

### 14.5 Phase Conservative Coefficient
- Group R1: ×1.00 / R2: ×0.95 / R3: ×0.90
- KO R16: ×0.88 / QF: ×0.85 / SF: ×0.82 / Final: ×0.80

### 14.6 Poisson Zero-Inflation
- If both teams ≤2 GF/game: P(0-0) +=0.05, P(0-1) +=0.02, then re-normalize

### 14.7 Multi-Period Fusion
- Late-1h present: H_late×0.60 + H_mid×0.25 + H_open×0.15
- Mid only: H_mid×1.0

### 14.8 Dispersion Confidence Penalty
- AH_std = std(3 AH lines), OU_std = std(3 OU lines)
- penalty = max(0, 1 − 0.3×(AH_std+OU_std))
- Top1 prob ×= penalty; if AH_std≥0.25 or OU_std≥0.25 → 🔴 flag

### 14.9 Market Liquidity

| Indicator | Healthy | Warning | Danger |
|-----------|:---:|:---:|:---:|
| Water σ (1h) | <0.03 | 0.03–0.06 | >0.06 |
| Spread tightness | <1.06 | 1.06–1.10 | >1.10 |
| Change frequency (6h) | >20 | 10–20 | <10 |
| SBOBet-Pinnacle AH gap | <0.25 | 0.25–0.50 | >0.50 |
| bet365 limit direction | ↑ | flat | ↓ |

- liquidity_score = avg(indicators mapped to 0–1)
- confidence ×= (0.85 + 0.15 × liquidity_score)

### 14.10 External Factor Quantification

| Factor | 0 (neutral) | −0.5 | −1.0 |
|--------|:---:|:---:|:---:|
| Weather | Clear, 10–25°C | Rain, 5–10 or 25–32°C | Snow/storm, <5 or >32°C |
| Travel | <500km | 500–2000km | >2000km or +3h tz |
| Rest | ≥5 days | 3–4 days | ≤2 days |
| Altitude | <500m | 500–1500m | >1500m |

- external_penalty = Σ(scores for both teams)
- xG ×= (1 + penalty × 0.03)

### 14.11 Draw Inertia
- Either team ≥2 consecutive draws in last 3 → draw prob floor = max(current, 30%)

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

## KB-9: Post-Mortem Summary

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

## KB-10: MBI — Multi-Bookmaker Intelligence Framework (v3.0)

> **Rationale**: Pinnacle is the gold standard but not infallible. 30-bookmaker data from 500.com enables consensus-weighted analysis that captures signals Pinnacle alone misses.

### 10.0 Bookmaker Tier Classification

| Tier | Weight | Members | Characteristics |
|:---|:---:|:---|:---|
| **Sharp** | 0.55 | Pinnacle, bet365, IBC(沙巴) | Accept winning players, razor-thin margins, lead price discovery |
| **Asian** | 0.25 | 澳门, 皇冠, 利记, 易胜博, 12bet, 18bet | Regional capital flow, water-level sensitive, macro-policy influenced |
| **Retail** | 0.20 | 威廉希尔, 立博, Interwetten, 必发(exchange), 伟德, Bwin | Public sentiment, recreational volume, exchange reveals real money |

### 10.1 Sharp Consensus Score (SCS) — v3.0.1 revised

```
For each outcome (H/D/A), across all 30 bookmakers:
  SCS_outcome = Σ(tier_weight_i × direction_i) / Σ(tier_weight_i)

  direction_i: +1 if odds↓, −1 if odds↑, 0 if |change|<noise_threshold
  
  noise_threshold = max(0.02 × odds_current, 1.5 × σ_historical)
    (自适应阈值: 至少 2% 变动, 且超过该结果的历史波动率 1.5σ)

  magnitude_weight = min(|change_pct| / 0.10, 1.0)
    (幅度加权: 变动越大权重越高, 10% 变动达到满权重)

  time_decay = exp(−hours_since_change / 24)
    (时间衰减: 24 小时前半衰, 越靠近开赛权重越高)

  direction_i_weighted = direction_i × magnitude_weight × time_decay

Final SCS = SCS_favorite × 0.6 + SCS_draw × 0.2 + SCS_underdog × 0.2
  (favorite = lowest current odds among H/D/A, not fixed to home)
```

**v3.0.1 改进**：
- 热门方动态判定（不再固定主胜），客场热门时自动调整
- 加入变动幅度加权（0.01 vs 0.1 的信号强度不同）
- 加入时间衰减（临场变动权重大于早期变动）
- 自适应噪音阈值（深盘/浅盘不同标准）

**Thresholds**:
- SCS ≥ 0.70 → Strong consensus → Step 10 correction +10%
- SCS 0.40–0.70 → Moderate → no adjustment
- SCS < 0.40 → Weak consensus → Step 10 penalty −5%

### 10.2 Dispersion Risk Index (DRI) — v3.0.1 revised

```
DRI_raw = ouzhi.dispersion.home × 0.5 + ouzhi.dispersion.draw × 0.3 + ouzhi.dispersion.away × 0.2

联赛校准: DRI_calibrated = DRI_raw / league_median_DRI × 30
  (各联赛取 500+ 场历史比赛的中位数 DRI 作为基准，消除联赛间天然差异)
  WC/EPL/UCL 中位数 ~12-18; 低级别联赛中位数 ~25-40

阈值 (以 WC/top5 联赛为默认):
  DRI_cal < 12 → Tight consensus → confidence × 1.05
  DRI_cal 12–35 → Normal → no adjustment
  DRI_cal 35–60 → High dispersion → confidence × 0.85, ⚠️ warning
  DRI_cal > 60 → Extreme → confidence × 0.70, 🔴 systemic risk flag

信息驱动 vs 混乱型离散 (v3.0.1 NEW):
  如果 DRI 高 AND Pinnacle 领涨 (Lead-Lag STRONG):
    → 信息驱动型离散（市场正在重新定价），DRI_signal 减半处理
  如果 DRI 高 AND Lead-Lag = NOISE:
    → 混乱型离散（散户无序波动），DRI_signal 全额计入
```

**v3.0.1 改进**：
- 联赛层级分位数校准（消除天然差异）
- 区分信息驱动 vs 混乱型离散
- 权重跟随热门方动态调整

### 10.3 Lead-Lag Chain Detection — v3.0.1 revised

```
Parse change_time from yazhi page (format: "MM-DD HH:MM").
时间戳质量校验: 如果 500.com 抓取延迟 >1h，降级为低置信。

领先机构优先级（按赛事类型）:
  欧美赛事 (WC/Euro/EPL/UCL): Pinnacle > bet365 > 澳门
  亚洲赛事 (亚冠/J联赛/K联赛): 沙巴/IBC > 澳门 > Pinnacle
  世界杯: Pinnacle = 沙巴 (权重相等，世界杯全球定价)

链类型:
1. 领先机构先动 → 次级机构 2h 内跟进 → 第三层 4h 内跟进
   → STRONG SIGNAL, logit +0.40
   幅度加权: 如果领头机构调整 ≥5%，额外 +0.10

2. 领先机构动了 → 多数机构 4h 内未跟进
   → WEAK SIGNAL, 忽略

3. 非领先机构先动 → 领先机构长时间静态
   → NOISE, 忽略

4. 三层同时动 (1h 窗口内)
   → GENUINE EVENT, logit +0.20

Default: no clear chain → 0
```

### 10.4 Water Flow Analysis — v3.0.1 revised

**v3.0.1 重大修正**：水位变动必须先控制在相同盘口档位下比较，否则盘口升/降带来的水位变化会被误判为资金流向。

```
前提: 仅统计「盘口档位未变」的机构的 AH 水位变化。
      盘口升/降的机构单独标记，不计入流向统计。

机构去重: 16 家亚盘公司中存在同集团白标（皇冠/利记/易胜博共用赔率源）。
          先对赔率向量做聚类（correlation > 0.95 视为同源），
          每个聚类只取一个代表。独立数据源数量通常为 6-9 个。

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
```

### 10.5 Exchange-Traditional Divergence

```
From touzhu data (必发 Betfair exchange):
  volume_ratio = volume_favorite / total_volume
  
  volume_ratio > 0.80 AND Pinnacle odds static >4h:
    → RESISTANCE: big money buying but price not moving → caution (−5%)
  
  volume_ratio > 0.80 AND Pinnacle odds dropping:
    → BREAKOUT: money flow confirmed by sharp bookmaker (+5%)
  
  volume_ratio < 0.50:
    → LOW CONVICTION: market interest thin → confidence × 0.90
```

### 10.6 Kelly Consensus (CORRECTED v3.0.1)

**原理纠错**：凯利指数 = 机构在该结果上的赔付比例。指数越**低**，说明机构赔付控制越严格，对其打出信心越强。指数越**高**，说明机构愿意给出更高赔付吸引投注，本质是不看好。之前 v3.0 版本将此逻辑完全写反，属于方向性错误。

```
From ouzhi data (30 bookmakers each with Kelly index):

Avg_Kelly_favorite = mean(Kelly on predicted winning outcome)
Avg_Kelly_others = mean(Kelly on other two outcomes)

CORRECT interpretation:
  热门方凯利 < 0.92 AND 其他两方凯利 > 热门方凯利:
    → CONTROL SIGNAL: 机构一致压低热门方赔付，高度看好 (+5%)
  
  热门方凯利 > 1.00:
    → NO CONTROL: 机构未压低热门赔付，存在诱盘风险 (−8%, 降为 amber warning)
  
  热门方凯利介于 0.92–1.00:
    → NEUTRAL: 市场定价均衡，无额外信号

  三方凯利均 < 0.85:
    → HIGH VIG: 整体抽水过高，信号可信度下降，confidence × 0.88

  热门方凯利为三方最低（与另两方差 ≥0.05）:
    → CONFIRMATION: 赔付集中在非热门方，机构集体看好热门 (+3%)
```

**逻辑依据**：博彩公司通过调低某个结果的赔率（对应凯利下降）来限制赔付风险——这是他们对该结果信心的真实表达。赔率给得越高（凯利越高），越是想吸引资金流向该结果，本质是不看好。

### 10.7 Four New MBI Trap Rules

| # | Rule | Trigger | Signal | Action |
|:--:|------|---------|:------:|--------|
| 16 | **Tier Divergence** | Sharp tier vs Asian tier AH gap ≥0.25 ball | 🔴 systemic | Confidence ×0.85, flag match |
| 17 | **Exchange-Volume Spike** | 必发 volume >2× previous + odds static | ⚠️ resistance | Direction confidence −5% |
| 18 | **Kelly Control Gap** | Kelly fav <0.92 + others > fav (CORRECTED: low Kelly = control = confidence) | ✅ value | Direction confidence +5% |
| 19 | **Water Flow Anomaly** | Flow Ratio ≥0.70 + Pinnacle static | ⚠️ suspicious | Flag for manipulation risk |

### 10.8 Integration into Step 10 (Probability Synthesis)

**v3.0.1 重大修正**：原 v3.0 在概率空间做加法校正（p ± X%）违反概率公理（有界性破坏、非贝叶斯更新）。修正为 **logit 空间校正**：

```
Step A: 基础概率 → logit 转换
  logit_h = ln(P_h / (1 − P_h))
  logit_d = ln(P_d / (1 − P_d))
  logit_a = ln(P_a / (1 − P_a))

Step B: 在 logit 空间叠加所有校正
  logit_h' = logit_h + Σ(correction_i)
  其中 correction_i 为各校正因子的 logit 偏移量（来自 KB-6 各条）

Step C: sigmoid 转回概率
  P_h' = 1 / (1 + e^(−logit_h'))
  P_d' = 1 / (1 + e^(−logit_d'))
  P_a' = 1 / (1 + e^(−logit_a'))

Step D: 归一化
  total = P_h' + P_d' + P_a'
  final = [P_h'/total, P_d'/total, P_a'/total]
```

**logit 空间的优势**：
- 概率始终在 (0, 1) 区间，永不越界
- 等价于贝叶斯更新中对数几率乘法，数学上正确
- 极端概率（如 90%+）附近校正幅度自然压缩，符合直觉

### MBI Composite (#12) in logit space

```
#12 MBI Composite 作为 logit 偏移量:
  mbi_logit = SCS_signal + DRI_signal + LeadLag_signal + Kelly_signal + WaterFlow_signal

  SCS_signal:
    SCS ≥ 0.70 → +0.40  (strong consensus)
    SCS 0.40–0.70 → 0
    SCS < 0.40 → −0.20  (weak consensus)

  DRI_signal:
    DRI < 15 → +0.20   (tight)
    DRI 15–40 → 0
    DRI 40–70 → −0.35  (high dispersion)
    DRI > 70 → −0.70   (extreme, plus confidence × 0.70 override)

  LeadLag_signal:
    STRONG chain → +0.40
    GENUINE EVENT → +0.20
    NOISE/WEAK → 0

  Kelly_signal (CORRECTED):
    fav Kelly < 0.92 + lowest → +0.20  (institution control)
    fav Kelly > 1.00 → −0.35  (no control, potential trap)
    neutral → 0

  WaterFlow_signal:
    Flow ≥ 0.70 + Pinnacle leads → +0.30
    Flow ≥ 0.70 + Pinnacle static → −0.20 (suspicious)
    Flow < 0.50 → 0

  Apply: logit_h' = logit_h + mbi_logit
```

### Factor Correlation Dampening (v3.0.1 NEW)

SCS、DRI、Water Flow 本质上都衡量「市场共识强度」，高度相关。直接叠加会导致重复计数。

```
Dampening rule:
  如果 SCS_signal 和 WaterFlow_signal 同向（都正或都负）:
    叠加值 = max(SCS_signal, WaterFlow_signal) + 0.3 × min(SCS_signal, WaterFlow_signal)
  （较大信号全额计入，较小信号打 3 折，避免 1+1=2 的线性放大）

  如果 DRI_signal < −0.35（高离散）且 SCS_signal > 0:
    DRI_signal 减半（信息驱动的离散不等同于混乱型离散）
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
