# Knowledge Base Reference — Football Odds Analyst v2.7

> **Load trigger**: Read this file when the main SKILL.md instructs you to reference a specific section ($KB-n). Contains all detailed rules, formulas, trap definitions, scoring criteria, and methodology.

---

## KB-1: Core Math & Conversion

### Formulas
```
Overround (vig) = 1/home_price + 1/draw_price + 1/away_price
True de-vigged probability = (1/outcome_price) / overround
Payout rate = 1 / overround

Normalization (MANDATORY after all corrections):
  adjusted_p[i] = base_p[i] + Σ(corrections_i)
  normalized_p[i] = adjusted_p[i] / Σ(adjusted_p[j])
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
