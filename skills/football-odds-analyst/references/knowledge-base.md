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

**v3.0.1**: Upgraded to Shin de-vigging algorithm. Simple proportional method systematically overestimates favorite probabilities (favorite-longshot bias widens as odds gap grows).

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
    (adaptive threshold: at least 2% change AND exceeds 1.5σ of historical volatility)

  magnitude_weight = min(|change_pct| / 0.10, 1.0)
    (magnitude weighting: larger moves get higher weight, 10% change = full weight)

  time_decay = exp(−hours_since_change / 24)
    (time decay: half-life of 24h, changes closer to kickoff weighted more heavily)

  direction_i_weighted = direction_i × magnitude_weight × time_decay

Final SCS = SCS_favorite × 0.6 + SCS_draw × 0.2 + SCS_underdog × 0.2
  (favorite = lowest current odds among H/D/A, not fixed to home)
```

**v3.0.1 improvements**:
- Dynamic favorite determination (no longer fixed to home win), auto-adjusts when away is favorite
- Added magnitude weighting (0.01 vs 0.1 change has different signal strength)
- Added time decay (late changes weighted higher than early changes)
- Adaptive noise threshold (different standards for deep vs shallow handicap)

**Thresholds**:
- SCS ≥ 0.70 → Strong consensus → Step 10 correction +10%
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

### 10.3 Lead-Lag Chain Detection — v3.0.1 revised

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

SCS, DRI, and Water Flow all essentially measure "market consensus strength" and are highly correlated. Direct stacking would cause double counting.

```
Dampening rule:
  如果 SCS_signal 和 WaterFlow_signal 同向（都正或都负）:
    叠加值 = max(SCS_signal, WaterFlow_signal) + 0.3 × min(SCS_signal, WaterFlow_signal)
  (larger signal fully counted, smaller signal discounted to 30%, avoiding 1+1=2 linear amplification)

  如果 DRI_signal < −0.35（高离散）且 SCS_signal > 0:
    DRI_signal halved (info-driven dispersion ≠ chaos-type dispersion)
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

## KB-11: Data Calibration Layer (v3.0.3 Final)

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

## KB-12: Advanced Signal Quantification (v3.0.3 Final)

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

## KB-13: System Risk Controls & Iron Rules (v3.0.3 Final)

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

### 13.6 Shadow Testing Acceptance Criteria

```
Live trading prerequisites (≥1 month shadow testing):

All met before switching to real money:
  ☐ A类信号胜率 ≥ 65%
  ☐ Counter signals (resistance wall/trap breaks) accuracy ≥ 70%
  ☐ 串关全灭概率 ≤ 25%
  ☐ 竞彩返还率下模拟 EV ≥ −3%
  ☐ 连续 2 周无单周回撤 > 5%

Signal traceability review template (mandatory per match):
  Match info + event tier + signal confidence level (A/B/C)
  Final logit correction + per-module contribution breakdown
  Hit/miss root cause (model misjudgment / new bookmaker tactic / dirty data)
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
