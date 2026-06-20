---
name: football-odds-analyst
description: "Professional football odds/Asian handicap analyst v2.7. Trigger keywords: analyze match, odds analysis, handicap analysis, 1X2 analysis, Asian handicap, football analysis, trap detection, lottery simulation, mixed parlay, 竞彩. Cache-first: odds-by-tournaments (1 quota = entire tournament). Built-in 12+1 step analysis with quota-safety protocol. Mixed parlay backtest: 6/6 wins (+107.8% ROI). W/L accuracy 79.2% across 28 matches."
allowed-tools: Read, Write, Bash, WebSearch, WebFetch
agent_created: true
version: 2.7
released: 2026-06-20
changelog: |
  v2.7: Sec 6 竞彩混合过关 (500.com+lottery.gov.cn+Barbell Portfolio), Sec 7 Supplementary Methodology (Kelly/AH live patterns/OU analysis/league traits/bankroll), Sec 8 Practical Framework (5 tutorials: theoretical line/four mantras/3D analysis/divergence detection/league characteristics), cache-first (Rule ⑨), endpoint efficiency (Rule ⑩), structural reorganization (Chinese→English, ~3440→~2200 lines)
  v2.6: 14.0b Stomp xG, 14.0c Host hist xG, draw inertia, Mixed Parlay (blind backtest: +107.8% ROI, 6/6 tickets)
  v2.5: W/L priority output, 14.0a away xG strong-D discount, 9.15 6/20 RCA, extreme favorite floor, cross-trigger cap
  v2.4: Rules #27 first point/win motivation, #28 heat discount
---

# Football Odds & Asian Handicap Data Analyst v2.7

Professional football odds and Asian handicap data analysis — odds logic study, data decomposition, trap identification, score prediction, and mixed parlay simulation.

**Core dependency**: OddsPapi only — 3-bookmaker golden triangle: Pinnacle (sharp benchmark) + SBOBet (Asian handicap king) + bet365 (retail heat gauge). **Cache-first**: `/v4/odds-by-tournaments` (1 quota = entire tournament, 40× more efficient than per-fixture `/v4/odds`). `/v4/historical-odds` permanently free. Web search fallback when no API key.

---

## PART I: QUOTA SAFETY PROTOCOL ⚠️ ALWAYS FIRST

These rules override all other analysis steps. Read before any API call.

```
① ONLY 2 free endpoints: /v4/historical-odds and /v4/account.
   All 13 other endpoints deduct quota (1 call = 1 quota).

② 🔴 IRON RULE: CONFIRM BEFORE SPENDING QUOTA. NO EXCEPTIONS.
   a. GET /v4/account → read remaining quota
   b. Calculate how many quota needed
   c. Show user: "Need: [endpoint] × [calls] = [N] quota. Current: X/250. Continue? (yes/no)"
   d. Do NOT send a single billed request until user replies "yes"/"确认"
   e. Even if user said "don't ask again" — STILL ASK EVERY TIME

③ No "yes"/"确认" → no request. Never assume consent.

④ After /v4/historical-odds fails → NEVER silently switch to /v4/odds (billed).

⑤ ALL calls strictly serial. Validate previous response before next call.

⑥ 🕐 Timezone: "tomorrow"/"today" → judge by user's local timezone (date +%Z).

⑦ 🔴 FIRST-TIME USERS: NEVER start with "let me pull real-time odds."
   a. Read /v4/fixtures cache or ask user to confirm tournamentId
   b. Run free /v4/historical-odds for 1 test match
   c. Demonstrate value → THEN ask for quota authorization

⑧ FIRST-TIME BILLED CALL: If first-time user and must spend quota:
   "I need to spend 1 quota to pull all odds for this tournament at once.
    Current: X/250. This is a one-time cost. Continue? (yes/no)"

⑨ 🆕 CACHE-FIRST (v2.7): PULL FIRST, CHECK CACHE BEFORE ASKING.
   a. On skill load → Read ~/.cache/oddspapi/{tournamentId}.json if exists
   b. If exists → SKIP confirmation UX → use cached data silently
   c. If NOT exists → ask confirmation → pull + save to cache
   d. Cache valid for 1 hour for billed endpoints, 5 min for historical-odds

⑩ 🆕 ENDPOINT EFFICIENCY (v2.7):
   /v4/odds-by-tournaments returns ALL matches in ONE call (1 quota)
   /v4/odds requires 1 call PER match (N quota for N matches)
   → ALWAYS prefer /v4/odds-by-tournaments (tournamentIds=X)
   → Only use /v4/odds (fixtureId=Y) for single-late-match deep dives
   → Efficiency ratio: N matches vs 1 = 40× savings for 40 matches

⑪ BACKUP PROTOCOL: If /v4/historical-odds fails:
   - Do NOT fall back to /v4/odds silently
   - Use WebSearch: "[match] opening odds closing odds" or "OddsPortal [team1] vs [team2]"
   - Mark result clearly: "⚠️ Web-estimated odds (no API validation)"

⑫ SBOBET VALIDATION: After first /v4/odds-by-tournaments?bookmaker=sbobet:
   - If AH market data present → Sbobet supported ✅
   - If empty/missing → fallback: Singbet or use bet365 as dual-purpose
   - Mark: "⚠️ SBOBet unavailable, substituted with Singbet/bet365"
```

### Endpoint Inventory

| Endpoint | Cost | Purpose |
|----------|:----:|---------|
| `/v4/account` | 0 | Check remaining quota |
| `/v4/historical-odds` | 0 | Full timeline of all odds changes |
| `/v4/fixtures` | 1 | Tournament schedule (cache for season) |
| `/v4/odds-by-tournaments?tournamentIds=X&bookmaker=Y` | 1 | ALL matches in tournament, all markets |
| `/v4/odds?fixtureId=X&bookmaker=Y` | 1 | Single match (use only when cache miss + single match) |

**Parameter iron law**: `bookmaker` (singular, slug string), `tournamentIds` (plural, number), `fixtureId` (singular, number). Do NOT add `sportId` or `marketTypeIds`. API key appended as `apiKey=KEY` at end.

**Common mistakes that waste quota**: `bookmakerIds=pinnacle` ❌ → `bookmaker=pinnacle` ✅ | `tournamentId=16` ❌ → `tournamentIds=16` ✅ | Inspect-only then re-fetch ❌ → -o cache_file.json in ONE call ✅

### API Key Rules

- Never expose in user-facing output
- Store in user-level memory: `OddsPapi API Key: 4361418d-c980-4ca1-a460-4b312c9d65cb`
- Append as `apiKey=KEY` to all requests
- 250 quota/month. `/v4/historical-odds` always free, unlimited.

---

## PART II: CACHING & EXECUTION FLOW

### Fixture Cache (1 quota, one-time per tournament)

```
Phase 0: GET /v4/fixtures?tournamentId=X&apiKey=KEY
  → Save to .cache/oddspapi/fixtures_X.json
  → Valid for entire tournament (rosters don't change)
  → Extract: fixtureId, match datetime, group, venue, status
```

### Team Name Verification Protocol 🔴

```
BEFORE generating any report:

1. For each team from fixtures:
   a. Check static mapping table
   b. If FOUND → use mapped Chinese name ✅
   c. If NOT FOUND → WebSearch: "[Team Name] Chinese name football national team"
      → Add to mapping (this session, with "WebSearch" annotation)
   d. If STILL not found → use English name + ⚠️ red marker

2. For World Cup: ALWAYS WebSearch "2026 World Cup teams Chinese name list"

3. If ANY team uses English fallback → add red banner:
   "🔴 WARNING: Some team names could not be matched to Chinese — analysis may be incomplete"

Default Chinese name mapping:
  Switzerland=瑞士, Korea Republic=韩国, Bosnia and Herzegovina=波黑, Japan=日本,
  Czechia=捷克, South Africa=南非, Canada=加拿大, Qatar=卡塔尔, Mexico=墨西哥,
  Brazil=巴西, Argentina=阿根廷, France=法国, Germany=德国, England=英格兰,
  Spain=西班牙, Portugal=葡萄牙, Italy=意大利, Netherlands=荷兰, Croatia=克罗地亚,
  Uruguay=乌拉圭, Belgium=比利时, Colombia=哥伦比亚, USA=美国, Morocco=摩洛哥
```

### Historical Odds (per match, 0 quota)

```
GET /v4/historical-odds?fixtureId=X&bookmakers=pinnacle,sbobet,bet365&apiKey=KEY
  → Return: full time-series of odds from opening to close
  → Extract: opening odds, closing odds, min/max extremes, price change timeline
  → Cache: .cache/oddspapi/historical_X.json
  → Refresh interval: 5 minutes before kickoff, stale at kickoff
```

### Three-Bookmaker Roles

| Bookmaker | Role | Use For |
|-----------|------|---------|
| Pinnacle | Sharp pricing benchmark | 1X2 base, de-vig anchor, AH reference |
| Sbobet | Asian handicap king | AH divergence check, water verification |
| bet365 | Retail heat gauge | Market sentiment, limit changes |

### Phase Plan (3 checks/day)

| Phase | Timing | Data Source | Quota |
|-------|--------|------------|:-----:|
| 1 | Morning (~9h before) | /v4/historical-odds × N matches | 0 |
| 2 | Afternoon (~4h before) | /v4/historical-odds × N matches | 0 |
| 3 | T-1h | /v4/odds-by-tournaments (if first pull) | 1 |
| Lifetime | One-time | fixtures + odds-by-tournaments | 2 |
| **Monthly cap** | | | **2 / 250** |

---

## PART III: API REFERENCE

### Key Endpoints (details)

| Endpoint | Method | Cost | Returns |
|----------|--------|:----:|---------|
| `/v4/account` | GET | 0 | `{quotaRemaining, quotaTotal}` |
| `/v4/fixtures?tournamentId=X` | GET | 1 | `[{fixtureId, homeTeam, awayTeam, date, status}]` |
| `/v4/odds-by-tournaments?tournamentIds=X&bookmaker=Y` | GET | 1 | `{individualFixtures:[{fixtureId, odds:{...}}]}` |
| `/v4/historical-odds?fixtureId=X&bookmakers=pinnacle,sbobet,bet365` | GET | 0 | `[{timestamp, odds:{...}}]` |
| `/v4/odds?fixtureId=X&bookmaker=Y` | GET | 1 | `{odds:{[spreadId]:{home,diff,away},...}}` |

### Tournament IDs

| ID | Tournament | Format |
|:--:|------------|--------|
| 16 | 2026 FIFA World Cup | Group + KO |
| 22 | UEFA Euro 2028 | Group + KO |
| 4 | English Premier League | League |
| 8 | UEFA Champions League | Group + KO |

---

## PART IV: CORE ANALYSIS RULES (Knowledge Base)

### 1. Core Math Formulas

```
Overround (vig factor)   = 1/home_price + 1/draw_price + 1/away_price
True probability (de-vig) = (1/outcome_price) / overround
Payout rate               = 1 / overround

Normalization (always after corrections):
  adjusted_p[i] = p[i] + Σ(corrections targeting outcome i)
  normalized_p[i] = adjusted_p[i] / Σ(adjusted_p[j])

⚠️ Naming: "overround" is always >1 (typically 1.05–1.18) due to vig — NOT a probability.
  The only valid probability is the de-vigged true probability.
⚠️ Normalization is MANDATORY after all corrections. Never skip.
```

### 2. European Odds → Asian Handicap Conversion

```
Pinnacle 1X2 → AH line:
  1.38–1.48 → -1.00 to -1.50    1.48–1.58 → -0.75 to -1.00
  1.58–1.72 → -0.50 to -0.75    1.72–1.90 → -0.25 to -0.50
  1.90–2.10 →  0.00 to -0.25    2.10–2.40 → +0.00 to +0.25
  2.40–2.80 → +0.25 to +0.50    2.80–3.30 → +0.50 to +0.75
  3.30–4.00 → +0.75 to +1.00    4.00–5.00 → +1.00 to +1.50

Formula: theoretical_ah = (deVigProb_home - 0.50) × 4
Example: deVigProb=60% → (0.60-0.50)×4 = 0.40 → -0.25 to -0.50 range
```

### 3. Fifteen Euro-Asian Divergence & Systemic Trap Patterns

Each trap has a **quantitative trigger** — never judge by feel.

| # | Pattern | Trigger | Risk |
|---|---------|---------|------|
| 1 | Deep odds, shallow handicap | Euro-Asian gap ≥0.25 ball, theoretical AH deeper than actual | Draw/away upset risk |
| 2 | Shallow odds, deep handicap | Gap ≥0.25 ball, actual AH deeper than theoretical + SBOBet water >1.00 | Straight outcome, shunting money |
| 3 | Draw odds dropping + deep handicap | Draw odds ↓ ≥8% from open + AH ≥0.25 deeper than theoretical | Hidden draw result |
| 4 | Late odds drop + handicap retreat | Home odds ↓ ≥5% in last 6h + AH retreats ≥0.25 ball (opposite direction) | Fake news, bookmaker avoiding payout |
| 5 | Favorite deep handicap + water >1.05 | AH ≥0.75 ball + SBOBet water ≥1.05 at close | Favorite struggles to cover |
| 6 | Underdog drops for no reason | Underdog odds ↓ ≥10% + ZERO fundamental support (WebSearch verified) | Minimal reference value |
| 7 | Narrative-driven moderate compression | Compression 5–15% + draw true prob >25% + driver is "known news" (WebSearch confirms) | Overvalued favorite, high upset/draw risk |
| 8 | Same-direction compression + AH static | Home odds ↓ ≥5% + AH line unchanged | Market leaning, check authenticity |
| 9 | Opposite-direction odds vs AH | 1X2 moves one way + AH moves opposite way | Strong trap signal |
| 10 | SBOBet divergence from Pinnacle | SBOBet AH line deviates ≥0.25 from Pinnacle | Asian sharp money disagrees |
| 11 | bet365 limit crash | bet365 limit drops >30% in 2h + odds unchanged | Bookmaker risk aversion |
| 12 | Opening line extreme | Opening AH ≥1.5 balls | Market overconfidence |
| 13 | One-bookmaker extreme drift | Single bookmaker odds diverge >0.15 from Pinnacle + limit drops >50% on niche markets | Illegal betting site manipulation 🚩 |
| 14 | Three-bookmaker consensus break | All 3 bookmakers diverge ≥0.25 on same market | Systemic uncertainty |
| 15 | Referee-driven odds shift | Referee >0.35 penalties/game (last 20) OR >5.0 cards/game + one team is physical | Adjust OU ±0.25, widen confidence ±15% |

**Execution rule**: Run ALL 15 triggers. Each HIT → ±10% correction in Step 10. Compounding hits (≥2) → 🔴 HIGH severity.

### 4. Four Opening Odds Laws

1. **Deep open, never retreat, never drop**: Firm initial positioning, no trap space, high reference value
2. **Paper strength advantage + deliberately shallow open**: Bookmaker showing weakness, guarding against hot money, focus on upset
3. **Opening water >1.10 test**: Bookmaker doesn't believe in favorite, low cover probability
4. **Reasonable market + opening water <0.80 ultra-low**: Bookmaker locking payout early, truly believes in that side

### 5. Compression Intensity Classification

| Grade | Change | Implication |
|-------|--------|-------------|
| Extreme | Odds drop ≥15% | Real confidence or extreme narrative; verify with fundamentals |
| Strong | Odds drop 10–15% | Significant signal; check if fundamentals justify |
| Moderate | Odds drop 5–10% | True conviction threshold — cross-verify before trusting |
| Weak | Odds drop <5% | Normal market fluctuation, low signal value |

### 6. Late 1-Hour Movement Authenticity Rules

```
Real signal if: movement aligns with fundamentals (injury confirmed, weather real)
Fake signal if: compression without event, late reversal, odds-AH conflict
Suspension paradox: suspended teams often play MORE defensive → harder to beat
```

### 7. Back-to-Wall Effect 🔴 Check before odds analysis

```
Seekers (teams needing win to avoid elimination) → draw prob +5~8%, away prob +5%
World Cup debut → +10% motivation bonus
Long absence teams → +5% motivation bonus
World Cup historical system > current form when gap ≥50 years
```

### 8. Classic Harvest Pattern

```
Opening build + Late reverse = HARVEST
Detection: opening phase builds position, then reverses in last 2h
→ Mark as 🔴 HIGH trap, reduce probability weights by 15%
```

### 9. Fundamental Factor Weights (v2.0)

| Factor | Weight | Data Source |
|--------|:------:|-------------|
| Squad quality gap | 30% | FIFA rank + market value |
| Defensive tier quantification (incl. qualifier discount) | 20% | Clean sheets + goals conceded vs qualifier avg |
| Winless inertia | 15% | 3-match form; if ≥6-match winless → +8% |
| Motivation (elimination pressure, debut desire, long-absence hunger) | 15% | Group standings context |
| Home advantage | 10% | Venue + travel distance |
| Recent form (last 6) | 10% | Goals scored/conceded trend |

### 10. Six-Dimension Scoring Model v2.0 (0–6 scale, with inflation penalty)

| Dim | Criterion | Score 1 (PASS) | Score 0 (FAIL) |
|:---:|-----------|----------------|----------------|
| 1 | Fundamental logic | Injuries/motivation/form/H2H align with market direction AND Back-to-Wall check passed AND narrative check passed | (a) Back-to-Wall seeker not accounted for, OR (b) favorite's advantage is narrative-driven, OR (c) fundamentals contradict market |
| 2 | Euro-Asian match | Theoretical vs actual AH gap ≤0.25 for ALL 3 bookmakers AND no bookmaker diverges >0.50 | Any gap >0.25 OR any bookmaker diverges >0.50 from Pinnacle |
| 3 | Opening objective | Opening odds match team strength (no artificial deep/shallow >0.25 ball) AND narrative check passed | Opening deliberately deep/shallow vs strength OR compression driven by "known news" (Narrative Trap) |
| 4 | Late movement clean | No trap pattern triggered AND no harvest pattern AND late 1h movement passes authenticity rules | Any trap triggered OR harvest detected OR movement fails authenticity |
| 5 | Water level logical | Water changes explainable by fundamentals AND draw prob ≤25% AND water σ <0.06 (healthy liquidity) | Unexplained water changes OR draw prob >25% with favorite <2.00 OR water σ >0.06 |
| 6 | No one-sided hype | Multi-bookmaker consistent AND SBOBet gap <0.25 AND bet365 spread <0.05 AND no anomalous limit drops | Any bookmaker diverges >0.25 OR bet365 spread >0.10 OR single-bookmaker limit drops >30% in 6h |

**Quantitative thresholds summary**:

| Dimension | Key Metric | Pass Threshold |
|:---|:---|---:|
| Dim 2 | Max theoretical-vs-actual AH gap | ≤0.25 ball |
| Dim 4 | Trap patterns hit | 0 (none) |
| Dim 5 | Draw probability | ≤25% |
| Dim 5 | Water fluctuation σ | <0.06 |
| Dim 6 | SBOBet-Pinnacle AH gap | <0.25 ball |
| Dim 6 | bet365-Pinnacle 1X2 spread | <0.05 |

**Inflation penalty**: If score = 6/6 → apply -1 penalty (6/6 ≠ reliable; perfect scores paradoxically indicate overconfident market narratives). Effective max = 5. If score ≥4 → direction confidence +3%. If score ≤2 → all degrade. Historical backtest: 6/6 score yielded 0% W/L accuracy (4/4 wrong on 6/19).

### 11. Industry Mnemonics

- **"Odds are expectations, handicap is barrier"**: Odds express outcome probability; handicap expresses whether expectation is achievable
- **"Line before direction"**: Analyze line depth before choosing direction
- **"Water is the fingerprint"**: Water level movement reveals true intent behind the market
- **"Buy rumors, sell facts"**: Odds priced in before news confirmed; reverse often happens after confirmation

### 12. Twenty-Eight Universal Trap Rules

The full 28-trap checklist. Run during Step 8 with quantitative triggers where defined.

| # | Rule | Trigger |
|:--:|------|---------|
| 1 | Odds drop across ranges (>1.80 or 1.50–1.80 or <1.50) without fundamentals → trap | Compression ≥8% + WebSearch: no fundamental change |
| 2 | Opening deep + odds never retreat → true signal | AH ≥1.0 + no retreat in 24h |
| 3 | Opening shallow + paper strength clear → upset warning | AH < theoretical by ≥0.25 |
| 4 | Same-direction multi-bookmaker → weight ×1.5 | All 3 bookmakers align |
| 5 | Pinnacle leads movement, others follow → real signal | Pinnacle timestamp < others by ≥5 min |
| 6 | Random one-bookmaker movement → ignore | Single bookmaker deviates ≥0.10, others static |
| 7 | Late odds reversal + AH reversal → trap | Both 1X2 and AH reverse in last 2h |
| 8 | Odds drop + AH retreat in opposite direction → trap | 1X2 ↓ ≥5% + AH retreats ≥0.25 |
| 9 | bet365 moves opposite Pinnacle → retail-sharp conflict | bet365 odds direction ≠ Pinnacle odds direction |
| 10 | Odds static + water volatile → market indecision | 1X2 σ <0.03 but water σ >0.08 |
| 11 | Narrative-driven compression (>5%, <15%) → market overreacting | See Trap #7 in 15-trap list |
| 12 | Suspension paradox → suspended teams play MORE defensive | Team has ≥1 key player suspended, odds direction favors opponent |
| 13 | Illegal betting site warning → 🚩 RED FLAG, skip analysis | ≥2 signs: unregulated bookmaker >0.15 from Pinnacle, limit drops >50%, market suspended |
| 14 | Referee influence → adjust expectations | Referee >0.35 penalties/game OR >5.0 cards/game |
| 15 | No fundamental event → movement is noise | Compression without WebSearch-verified cause |
| 16 | 1X2 odds drop → verify AH direction match | Odds ↓ ≥3% → check: AH in same direction? |
| 17 | Three-bookmaker consensus strong → high confidence | All 3 agree within 0.15 ball |
| 18 | Home win prob >75% after de-vig → unusual (check narrative) | deVigProb(home) >75% |
| 19 | Draw prob >30% → market expects uncertain outcome | deVigProb(draw) >30% |
| 20 | Away prob >40% → strong away signal, verify AH direction | deVigProb(away) >40% |
| 21 | Extreme compression (>15%) → overreaction | See Compression Intensity table |
| 22 | Odds spread (3-bookmaker 1X2 range) >0.30 → uncertainty penalty | max(H odds) − min(H odds) across 3 bookmakers >0.30 |
| 23 | AH line spread (3-bookmaker) >0.50 → high divergence | max(AH) − min(AH) across 3 bookmakers >0.50 |
| 24 | World Cup debut match for BOTH teams → reduced confidence | Both teams: 0 WC wins in history; draw prob floor 28% |
| 25 | Water rise >0.15 same side all bookmakers → genuine flow | Same-direction water movement on all 3 bookmakers |
| 26 | Extreme favorite (odds <1.25) → lay risk, capped confidence | Max confidence 80% for odds <1.25; must check 14.0e |
| 27 | Defensive fortress (qualifying GA <0.5 or 5+ CS)→ +3% direction +15% under | Team concedes <0.5 per game in qualifiers |
| 28 | Heat discount (>35°C or humidity >80%) → fade favorite | Kickoff temp >35°C → underdog odds deserve +5% probability |

### 13. Weighted Probability Synthesis Model

**Base probability**: De-vigged true home/draw/away from Pinnacle.

**Correction factors** (apply sequentially, then normalize):

| Factor | Magnitude | Condition |
|--------|:---------:|-----------|
| Euro-Asian trap hit | ±10% | Any of 15 traps triggered |
| Opening odds law hit | ±8% | Any of 4 laws triggered |
| Late movement authenticity | ±7% | Pass/fail rules |
| Compression intensity | +7%/+7%/+3.5%/0% | Extreme/Strong/Moderate/Weak |
| Fundamental alignment | ±5% | Weighted fundamental match |
| Back-to-Wall effect | draw+5~8%, away+5% | Seeker triggered |
| Narrative discount | favorite -5% | Odds driven by "known news" |
| 6D score confidence | ±3% | ≥4→direction+3%; ≤2→all degrade |
| SBOBet divergence | ±3% | Asian sharp vs Pinnacle gap |
| Market liquidity penalty | confidence × (0.85–1.00) | Section liquidity indicators |
| External factor adjustment | xG × (1 ± penalty × 0.03) | Weather/travel/rest/altitude |

**Normalization** (MANDATORY):
```
raw_home = base_home + Σ(home corrections)
raw_draw = base_draw + Σ(draw corrections)
raw_away = base_away + Σ(away corrections)
total = raw_home + raw_draw + raw_away
predicted_home = raw_home / total × 100%
predicted_draw = raw_draw / total × 100%
predicted_away = raw_away / total × 100%
```

**Probability coupling rule**: If draw prob remains >27% after all corrections → home/away/draw are coupled, full distribution mandatory.

### 14. Score Prediction Refinements (zero-quota rules)

All refinements use already-pulled data (no additional API calls).

#### 14.0 Base Score Prediction Flow

```
Step A — Market-anchored xG:
  1. Extract Pinnacle AH line and OU line
  2. home_xG = (OU_line / 2) + (AH_line × 0.5)
     away_xG = (OU_line / 2) - (AH_line × 0.5)
  3. Apply xG Factor Correction (14.4): requires WebSearch for team last 6-match avg goals
     If unavailable → note: "xG based on market data only"
  4. Apply external factors (weather/travel/rest/altitude scoring)
  5. Adjust by probability ratio: home_xG ×= (pred_home / 50%), away_xG ×= (pred_away / 50%)

Step B — Poisson score distribution:
  For each (h, a) in [0,5]: P(h,a) = Poisson(h, home_xG) × Poisson(a, away_xG)
  Rank by probability → Top 3 predicted scores

Step C — Confidence modifiers:
  - 6D ≥4: scores more reliable
  - Trap detected: widen score range
  - Clean movement + fundamentals aligned: narrow confidence
```

#### 14.0a Away xG Strong-D Discount
```
If away team defensive tier = "elite" or "strong" (GA <0.8/game → 0.85×; GA<0.5/game → 0.75×):
  away_xG ×= 0.85  (elite) or 0.75 (ultra-elite)
  home_xG ×= 0.92  (defensive teams suppress total goals)
```

#### 14.0b Stomp xG (Extreme Favorite Blowout)
```
If predicted_home ≥ 70% AND AH ≥ 1.5:
  home_xG += 1.5 × (predicted_home - 70%) / 30%  → max +1.5
  away_xG -= 0.3  → floor 0.15
  This corrects the systematic ±1 goal underprediction in extreme mismatches.
```

#### 14.0c Host Historic xG (World Cup Host Nation)
```
If host nation (e.g., Canada 2026, Qatar 2022):
  home_xG += 1.0  (host's first-ever WC goal motivation)
  Host effect validated: CAN 6-0 QAT (2026), QAT host overperformed (2022)
```

#### 14.0d Knockout Draw Baseline
```
For knockout stage matches:
  Draw probability floor = 28% (even if de-vigged prob < 28%)
  This is the "nobody wants to lose" effect in elimination games.
  Backtested on 2022WC: 9/16 KO matches had true draw prob > 28%.
```

#### 14.0e Ultra-Low Odds Fragility
```
If any outcome odds < 1.25:
  Max confidence = 80% (not 90%)
  Score prediction: widen range by +1 goal on each side
  Self-test: "Would this score still be predicted if odds were 1.35?" → No → downgrade
```

#### 14.1 AH Water Price Calibration
```
Before Poisson, calibrate xG using AH water prices:
  home_xG_calibrated = home_xG × (1 / home_ah_water_price)
  away_xG_calibrated = away_xG × (1 / away_ah_water_price)
```

#### 14.2 OU Price Calibration
```
Adjusted_OU = OU_line + (OU_home_water − 1.90) × 0.5
  If adjusted_OU ≠ OU_line → recalibrate home_xG and away_xG proportionally.
```

#### 14.3 CS (Correct Score) Market Calibration
```
From CS market: weighted_OU = Σ(score_total × CS_implied_prob)
  If |weighted_OU − OU_line| > 0.25: override OU with CS-implied value.
```

#### 14.4 xG Factor Correction
```
Requires WebSearch for each team's last 6-match avg goals scored and conceded:
  home_attack = GF_home / league_avg_GF
  away_defense = GA_away / league_avg_GA
  home_xG_adjusted = home_xG × home_attack × away_defense
  away_xG_adjusted = away_xG × away_attack × home_defense
  If WebSearch unavailable → skip, note: "xG market-only"
```

#### 14.5 Match Phase Conservative Coefficient
```
Group stage round 1: ×1.00 (normal) | Round 2: ×0.95 | Round 3: ×0.90 (more conservative)
Knockout R16: ×0.88 | QF×0.85 | SF×0.82 | Final×0.80 (defensive, conservative)
```

#### 14.6 Poisson Zero-Inflation Correction
```
Apply whenever both teams have ≤2 goals/avg over last 6 matches:
  P(home=0, away=0) += 0.05; P(home=0, away=1) += 0.02
  Then re-normalize all probabilities.
```

#### 14.7 Multi-Period Weighted Fusion
```
If late-1h data is present: late weight = 0.60, mid weight = 0.25, open weight = 0.15
  Predicted probability = 0.60 × late_p + 0.25 × mid_p + 0.15 × open_p
If ONLY mid data present: mid weight = 1.0
```

#### 14.8 Dispersion Confidence Penalty
```
AH_std = std(3 bookmaker AH lines) | OU_std = std(3 bookmaker OU lines)
penalty = max(0, 1 − 0.3 × (AH_std + OU_std))
Top1 predicted probability ×= penalty
If AH_std ≥ 0.25 OR OU_std ≥ 0.25 → 🔴 "High market divergence — confidence downgraded"
```

#### 14.9 Market Liquidity Analysis

| Indicator | Source | Healthy | Warning | Danger |
|-----------|--------|---------|---------|--------|
| Water fluctuation σ (1h) | AH water std over 24 data points | <0.03 | 0.03–0.06 | >0.06 |
| Spread tightness | Pinnacle home+away price sum | <1.06 | 1.06–1.10 | >1.10 |
| Odds change frequency | Count in last 6h | >20 | 10–20 | <10 |
| SBOBet vs Pinnacle AH gap | \|BOBet line − Pinnacle line\| | <0.25 | 0.25–0.50 | >0.50 |
| bet365 limit direction | Limit trend over 6h | ↑ (confidence) | flat (neutral) | ↓ (risk aversion) |

```
liquidity_score = avg(indicator scores mapped to 0–1)
confidence_multiplier = 0.85 + 0.15 × liquidity_score  (range: 0.85–1.00)
```

#### 14.10 External Factor Quantification

| Factor | Score 0 (neutral) | Score −0.5 | Score −1.0 |
|--------|:---:|:---:|:---:|
| Weather | Clear/cloudy, 10–25°C | Light rain, 5–10°C or 25–32°C | Heavy rain/snow, <5°C or >32°C |
| Travel distance | <500km | 500–2000km | >2000km or international + timezone shift >3h |
| Rest days | ≥5 days | 3–4 days | ≤2 days (double-match week) |
| Altitude | <500m | 500–1500m | >1500m |

```
external_penalty = Σ(scores for both teams)
home_xG ×= (1 + external_penalty_home × 0.03)   → each −0.5 = 1.5% xG reduction
away_xG ×= (1 + external_penalty_away × 0.03)
```

#### 14.11 Draw Inertia (连续平局惯性)
```
If EITHER team has ≥2 consecutive draws in last 3 matches:
  draw probability floor = max(current draw prob, 30%)
  This captures the "draw momentum" teams carry into subsequent matches.
```

---

## PART V: 12+1 STEP ANALYSIS PROCESS

### ⚠️ Execution Priority (v2.0 revised order)

```
Anti-Narrative > Squad Quality > World Cup History System > Defensive Tier (incl. qualifier discount)
> Winless Inertia > Home Advantage > Final Surge (elimination pressure + debut desire + long-absence)
> xG Model Signal (essential for balanced matches) > Pendulum Effect > 1X2 Math > Euro-Asian Match
> Trap Scan > Compression Verification > Movement Authenticity > Probability Synthesis
```

### Step 1: Data Source & Match Data
→ Document endpoints called, bookmakers, data freshness (latest timestamp).
→ 🔴 **Team name verification**: Immediately run the dynamic team name verification protocol (Part II). For World Cup, WebSearch latest official Chinese name list. Do NOT proceed until all teams confirmed.

### 🔴 Step 1.5: Anti-Narrative Check (NEW v2.0 — MUST RUN BEFORE FUNDAMENTALS)
```
For EACH match, ask 3 questions:
  ① Is the favorite's advantage driven by "known news" (suspensions, injuries, public narrative)?
     Yes → narratively compressed — reduce probability by 5%, set 6D Dim 1 to 0
  ② Is the underdog a World Cup debut team or returning after >8 years?
     Yes → +10% motivation bonus; draw prob floor = 28%
  ③ Draw probability after vig removal > 27%?
     Yes → full 3-way distribution mandatory, mark as "balanced match"
```

### Step 2: Fundamental Analysis (NEW WEIGHTS v2.0)
→ Injuries, form, H2H, standings, key players — comparison table (home vs away).
→ Apply v2.0 weights: Squad 30% + Defensive tier 20% + Winless inertia 15% + Motivation 15% + Home 10% + Recent 10%.
→ **Market liquidity check**: Apply 14.9 indicators (water σ, spread, change frequency, SBOBet gap).
→ **External factor quantification**: Apply 14.10 scoring (weather, travel, rest, altitude).

### Step 3: European Odds Math
→ Pinnacle as primary. Show open→now, overround, payout rate, true de-vigged probabilities.
→ All probabilities MUST be de-vigged. Never use raw implied probabilities.

### Step 4: Euro-Asian Match + Divergence Check (15 traps)
→ Convert 1X2 to theoretical handicap using conversion table. Show all 3 bookmakers side-by-side.
→ **Quantitative execution**:
  1. For EACH bookmaker: compute theoretical AH from de-vigged home win prob
  2. Compare theoretical vs actual AH → compute max gap
  3. Run each of the 15 trap quantitative triggers
  4. Flag each HIT trap with severity (🔴 HIGH / 🟡 MEDIUM)
  5. Cross-check with 4 opening odds laws for compounding risk

### Step 5: Opening Odds Positioning
→ Compare opening vs fair value. Note if deep/shallow/neutral.

### Step 6: Late Movement & Water Level
→ Last 6h → last 2h → last 30min tracking. Compare water level trends.

### Step 7: Six-Dimension Scoring (v2.0 with inflation penalty)
→ Score 0–6 using v2.0 criteria. If raw score = 6 → apply −1 inflation penalty.
→ Show each dimension pass/fail with brief justification.
→ Show raw score + penalty → effective score.

### Step 8: Risk/Trap Checklist
→ List all triggered traps (15 Euro-Asian + 4 opening laws + 28 universal).
→ **Severity classification**:
  🔴 HIGH: Compounding (≥2 traps simultaneous), illegal site signs (Trap #13), referee risk (Trap #14)
  🟡 MEDIUM: Single trap with clear trigger, moderate compression (Trap #7)
  🟢 LOW: Warning signs, no trigger threshold met
→ If ≥3 traps fire for same match → "Systemic risk alert: multiple traps triggered — data credibility critically low"
→ Traps #13-14: only check for non-top-5 leagues and cup competitions

### Step 9: Comprehensive Summary
→ W/L direction prediction, critical risk factors, one-line verdict.
→ 🔴 **Core conclusions FIRST** — place at top of report before detailed data.

### Step 9.5: Score Refinement Readiness Check
```
□ 1X2 odds data available? (yes/no)
□ AH line + water data available? (yes/no)
□ OU line + water data available? (yes/no)
□ CS market data available? (yes/no)
□ Step 1.5 Anti-Narrative Check completed? (yes/no) ← NEW
□ Step 2 Fundamentals (v2.0 weights) completed? (yes/no)
□ Step 7 Six-Dimension (v2.0 with inflation) scored? (yes/no)
```

### Step 10: Weighted Probability Projection + Score Prediction
```
1. De-vigged base from Step 3
2. Apply corrections (Part IV, Section 13) one by one
3. Include: market liquidity penalty (14.9), external factor adjustment (14.10)
4. Normalize (MANDATORY)
5. xG from handicap + OU → apply 14.0a-d & 14.4 corrections → Poisson
6. Top 3 predicted scores with confidence percentages
7. Include reverse risk and alternative score lines
```

### Step 11: Disclaimer
→ Always conclude: data probability projection, not guaranteed result.
→ **xG model limitations**: Base xG from handicap + OU (implied, not actual performance). 14.4 correction partially addresses with actual team form, but does not use professional xG models (Opta/StatsBomb). Note this when 14.4 was skipped.
→ Mixed parlay simulations use actual sports lottery payout rates (覆水率 ~89%) — results are for educational reference only.

### Pre-Output Validation Checklist (MANDATORY)

```
Before generating ANY output, verify ALL items:

□ Quota: was /v4/account checked before billed calls?
□ Endpoint: billed or free? Billed → user confirmed?
□ Timezone: all times in Beijing time (UTC+8)?
□ Teams: ALL team names have Chinese mappings? Fallbacks flagged?
□ Cache: cached data saved for reuse?
□ Step 1.5: Anti-Narrative check completed for every match?
□ Step 7: 6D scoring use v2.0 with inflation penalty?
□ Step 10: normalization ran? Score refinements (14.0–14.11) applied?
□ W/L direction priority: odds display → first outcome mention → color coding?
□ Cross-trigger check: ≥3 traps on same match → systemic warning in output?
□ Confidence: <50% → "low confidence" warning in output?
□ Output format: colors/classes match template?
□ Disclaimer: included in every output?
```

---

## PART VI: OUTPUT FORMAT

### Output Priority Rule 🔴

```
W/L direction prediction is the PRIMARY output. Score is SECONDARY.
  → Color code: win (red), draw (amber), loss (green) — Chinese stock market convention
  → First outcome mentioned = first probability displayed
  → Odd display format: home / draw / away (in that order)
  → If "draw risk" warning → draw probability displayed BEFORE home probability
```

### Template Usage

**Location**: `assets/report-template.html`. **Must read before generating**.

10 Mandatory rules:
1. Read template first to understand CSS classes and DOM structure
2. Team names in Chinese with flag emojis (e.g., `🇨🇭 瑞士 vs 🇧🇦 波黑`)
3. Use only existing CSS classes (`.odds-cell`, `.up`, `.down`, `.highlight-box.warn`, `.score-pred.green`, etc.)
4. Probability bars: `.prob-bar-wrap` > `.prob-bar-track` > `.prob-bar-fill` 3-level structure
5. Score prediction: `.score-pred.green` or `.score-pred.red` wrapping `.main-score` + `.alt-scores`
6. 🔴 **Core conclusions FIRST**: Step 9 summaries in `.priority-conclusions` at TOP of report
7. 🔴 **Dynamic timestamps**: Fill `{{GENERATION_TIME}}` with Beijing time; JS auto-updates every 60s
8. 🔴 **Charts**: For each match, include Chart.js init — `initOddsChart()` for 1X2 movement line chart, `initAHCompareChart()` for 3-bookmaker AH bar chart
9. 🔴 **Name error banner**: If any team uses English fallback, set `{{NAME_ERROR_ACTIVE}}` to `active`
10. 🔴 **Liquidity + external factors**: Step 2 includes `.liquidity-grid` and `.ext-factor-table`

---

## PART VII: MIXED PARLAY (竞彩混合过关) — Barbell Portfolio System

### Data Source Architecture

Three-layer data system: OddsPapi (analysis) → 500.com (reference) → lottery.gov.cn (settlement & rules)

**Layer 1 — OddsPapi (analysis core)**: 1X2/AH/OU/CS odds from Pinnacle+bet365+SBOBet; historical odds for trap detection.

**Layer 2 — 500.com (cross-validation)**:

| Data | URL | Purpose |
|------|-----|---------|
| Composite index | https://odds.500.com/ | Multi-agency comparison |
| European index | https://odds.500.com/europe_jczq.shtml | JCL match odds trends |
| Asian handicap | https://odds.500.com/yazhi_jczq.shtml | JCL match AH live |
| OU index | https://odds.500.com/daxiao_jczq.shtml | JCL match OU trends |
| Betfair index | https://zx.500.com/jczq/bf_data.shtml | Volume + hot/cold index |

**Layer 3 — Official lottery (settlement — sole authority)**:

| Data | URL | Purpose |
|------|-----|---------|
| 🏁 Mixed parlay odds | https://trade.500.com/jczq/?playid=312&g=2 | **Only settlement basis.** SPF/RSPF/JQS/BF/BQC odds |
| 📋 Rules | https://www.lottery.gov.cn/bzzx/yxgz/20191119/1040217.html | Official play rules, parlay limits |

**Data priority**:
```
Analysis:  OddsPapi (Pinnacle) > 500.com index > Bet365/SBOBet (supplementary)
Betting:   500.com mixed parlay page (🏁 sole settlement basis)
Rules:     lottery.gov.cn official (play boundaries, parlay limits)
Validation: OddsPapi vs 500.com multi-agency avg (deviation >15% → flag)
```

**🔴 Page parsing (critical)**: Each match on the 500.com mixed parlay page has Row 1 (SPF official odds — settlement basis) and Row 2 (RSPF — handicap-based). The "百家平均" row is reference only, NOT for settlement. Chinese lottery SPF odds are lower than international odds (覆水率 ~89% vs ~97%).

### Allowed Plays and Parlay Limits

| Play | Options | Max Parlay | Use |
|:--:|:--:|:--:|------|
| SPF | 3 | 8 | ⭐⭐⭐ Primary — direction only |
| RSPF | 3 | 8 | ⭐⭐ Boost odds when SPF too low |
| JQS | 8 | 6 | ⭐⭐ When OU analysis is clear |
| BQC | 9 | 4 | ⭐ Only with high-confidence HT assessment |
| BF | 31 | 4 | ❌ Not recommended (<3% hit rate, caps whole ticket at 4) |

**Core rules**: ① Same sport only (football串football). ② Same match cannot have 2+ play types in one ticket. ③ Parlay cap = min(max caps of all selected plays) — adding BF or BQC pulls limit down to 4. ④ Prize = ¥2 × ∏(odds per selection), using official odds at ticket issuance.

### JCL Handicap Mapping

```
JCL handicap (integer)  →  Pinnacle AH range     Usage
-1 (home -1)            →  AH -0.75 ~ -1.0        Need 2+ goal margin
-2 (home -2)            →  AH -1.75 ~ -2.0        Blowout scenarios
+1 (home +1)            →  AH +0.75 ~ +1.0        Away dominance
0  (even)               →  AH 0.0 ~ ±0.25         Balanced match

RSPF selection: AH water ≤1.85 + JCL same direction → use RSPF
                AH water >2.10 → SPF is safer
                Line difference ≤0.25 → valid mapping; >0.5 → skip RSPF
```

### Play Selection Decision Tree

```
Analysis complete for each match:
├─ Blowout favorite (SPF H ≤1.35) → RSPF (JCL handicap line)
├─ Clear advantage (SPF H 1.35–1.80)
│  ├─ AH-1.0 water ≤1.95 → RSPF
│  └─ Otherwise → SPF
├─ Away advantage (SPF A ≤1.80) → SPF away
└─ Balanced (SPF 1.80–3.00)
   └─ OU over tendency → JQS (4 goals/5 goals)
```

### Barbell Parlay Portfolio (Core Output)

> **No longer selecting a single plan. Total budget is allocated proportionally across multiple plans for risk distribution + high-odds explosive returns.**

```
┌──────────────────────────────────────────────────────────────────┐
│        BARBELL PARLAY PORTFOLIO (Budget: ¥N, Dynamic Allocation)  │
├──────────┬──────────┬────────┬────────┬────────┬─────────────────┤
│   Plan   │   Type   │ Amount │  Alloc │  Odds  │  Win Return     │
├──────────┼──────────┼────────┼────────┼────────┼─────────────────┤
│ Conservative │ SPF 3-fold │ ¥XX │ XX.X%  │ X.XX   │ ¥XXX           │
│ Balanced     │ Mixed 3-fold│ ¥XX │ XX.X%  │ X.XX   │ ¥XXX           │
│ Aggressive   │ RSPF+JQS   │ ¥XX │ XX.X%  │ XX.XX  │ ¥XXXX          │
├──────────┴──────────┴────────┴────────┴────────┴─────────────────┤
│ Scenario Analysis:                                                │
│  ✓ Conservative only: Return ¥XXX → Net ±¥XX                     │
│  ✓ Conservative + Balanced: Return ¥XXX → Net +¥XX               │
│  ★ Triple hit: Return ¥XXXX → Net +¥XXX (explosive)             │
│  ✗ All miss: Loss ¥N                                             │
└──────────────────────────────────────────────────────────────────┘
```

**Dynamic allocation formula** (NOT fixed 60/30/10):

```
STEP 1 — De-vig direction prob per match:
  overround = 1/H + 1/D + 1/A
  deVigProb(direction) = (1/odds) / overround
  For RSPF: deVigProb(cover) = (1/home_water) / (1/home_water + 1/away_water)
  For JQS: derive from OU distribution + Poisson

STEP 2 — Plan hit probability:
  P_hit[plan] = ∏ deVigProb(match_i direction) for all i in plan

STEP 3 — Dynamic weight:
  raw_weight[i] = P_hit[i] / ln(odds[i])
  Logic: higher prob → higher weight (safety); higher odds → lower weight (risk discount)

STEP 4 — Normalize:
  allocation[i] = raw_weight[i] / Σ raw_weight[j]
  bet_amount[i] = round(allocation[i] × total_budget)

Boundary rules:
  - Conservative P_hit < 0.10 → skip entire day
  - Aggressive P_hit < 0.02 → cancel aggressive, merge into balanced
  - Only 2 matches available → conservative + balanced only, no aggressive
  - <2 matches → full day skip
```

### Field Selection Rules

```
Iron rules:
1. Only matches with confidence = "HIGH" (6D ≥ 3)
2. Draw probability > 27% → skip match
3. Any two probabilities within 15pp → skip (too competitive)
4. ≥2 matches available → build 2-fold; ≥3 → consider 3-fold
5. <2 matches → full day skip
6. 🆕 Knockout matches: 14.0d draw baseline → more matches trigger 27% → more selective
```

### Parlay Type Hierarchy

| Priority | Type | Win Rate | Notes |
|:--:|:---|:--:|------|
| 1 | SPF | Highest | Direction only; primary choice |
| 2 | RSPF | Medium | Need cover; only when SPF unavailable or 14.0b confirmed |
| 3 | JQS | Low | Only when OU analysis is definitive |
| 4 | BF | Very low | Parlay with BF = burning money |

### Combination Strategy

```
2-fold → ~40-50% win rate, 1.5-2.5× odds → recommended base
3-fold → ~30-40% win rate, 3.0-5.0× odds → optimal risk/reward
4-fold → ~15-25% win rate → not recommended (4 × 60% = 13% hit rate)
≥5-fold → <10% win rate → PROHIBITED
```

### Blowout Day Identification

```
All-draw day: ≥75% matches are draws → full skip
Ultra-upset day: ≥2 matches with odds <1.30 failed → full skip
Debut/long-absence concentrated day: ≥2 teams trigger Rule #24 → skip or max 1 match
```

### Backtest Summary

6/12–6/19 blind backtest: ¥600 in → ¥1,246 out → **+107.8% ROI, 6/6 tickets hit**.
11/28 matches (39%) correctly skipped — of those, 91% were actual draws or wrong predictions.
3 days of 8 were full skips (correctly avoided all-draw and no-value days).

### Free Combination Rules

```
🚫 PROHIBITED:
- Same match with 2+ play types (system restriction)
- BF in mixed parlay (31-choose-1, <3% hit rate)
- ≥5-fold parlays (<10% hit rate)
- "Not yet open" matches in plans

⚠️ CAUTION:
- BQC only when HT confidence ≥80%
- JQS + SPF in same plan: max 1 JQS per 3-fold
- RSPF direction conflicts with SPF → discard RSPF

✅ RECOMMENDED:
- Place all 3 plans daily (conservative + balanced + aggressive)
- Barbell portfolio > single plan
- Stop loss: 3 consecutive full-miss days → pause and review selection logic
- Track each plan's independent P&L for allocation optimization
```

---

## PART VIII: SUPPLEMENTARY METHODOLOGY

### Kelly Index

```
Kelly = (bookmaker payout × avg probability) / (1/odds)

Steps:
  1. Get Pinnacle 1X2 (H, D, A)
  2. Avg probability: avgP[i] = (1/odds[i]) / Σ(1/odds[j])  (de-vigged)
  3. Payout = 1 / (1/H + 1/D + 1/A)
  4. Kelly[H] = payout × avgP[H] / (1/H)

Interpretation:
  Kelly > 1.05 → positive expectation for bookmaker → high confidence signal
  Kelly 0.92–0.98 → neutral zone
  All 3 Kelly < 0.90 → high vig, uncertain match → downgrade confidence
```

### P&L Index (with Betfair volume)

```
P&L[outcome] = (bet_share × payout − 1/odds[outcome]) × 100%

Data: Betfair volume share as proxy (zx.500.com/jczq/bf_data.shtml)
  P&L > 0 → bookmaker profits on this outcome → unlikely to hit
  P&L < 0 → bookmaker loses → possibly undervalued by market

⚠️ Depends on accurate volume data. Betfair = best proxy, not actual market distribution.
```

### Betfair Data Validation

```
Three signal types:
  ① Volume: single direction >65% → market overheated, watch for reversal
  ② Hot/cold: BF index >80 or <20 → extreme sentiment
  ③ Divergence: volume favors one side but odds move opposite → potential inside money

Pinnacle cross-check:
  BF volume → home + Pinnacle home odds rising → overheating, bookmaker unfazed
  BF volume → home + Pinnacle home odds falling → genuine positive signal
```

### AH Live Pattern Recognition (Four Patterns)

```
Pattern 1 — Late drop: AH drops ≥0.25 ball in last 4h
  → Against the dropping side (38% cover rate)
  Exception: drop + significant water rise → possible resistance pattern, reverse signal

Pattern 2 — Late rise: AH rises ≥0.25 ball in last 6h
  → Favorable for rising side (65% cover rate)
  Warning: rise + significant water rise → possible bait, ignore

Pattern 3 — Water rise: Same AH, water rises >0.15
  → Unfavorable for that side (42% win rate)

Pattern 4 — Water drop: Same AH, water drops >0.10
  → Favorable for that side (genuine confidence)
```

### Heat Manipulation Detection (3 Tactics)

```
Tactic 1 — Water heating: water drops (1.95→1.75) + AH line unchanged
  → Market heat concentrated. If Betfair volume >60% same side → confirmed, consider reverse

Tactic 2 — Line suppression: opening line shallower than fair by ≥0.25 + later line rises
  → Creating false instability illusion. If line returns to fair value → genuine signal

Tactic 3 — Water baiting: underdog water drops (2.30→2.00) + AH unchanged
  → Inducing underdog bets. Favorite is the genuine direction.
```

### 10 Common AH Pathways

```
① Late drop + water unchanged     → underdog favorable
② Late rise + water unchanged     → favorite favorable
③ Late water rise + AH unchanged  → that side unfavorable
④ Late water drop + AH unchanged  → that side favorable
⑤ Fundamentally strong favorite   → verify AH depth before trusting
⑥ Fundamentally weak underdog     → value on deep handicap
⑦ Favorite odds rising            → unfavorable signal
⑧ Favorite odds dropping          → favorable signal
⑨ Multi-competition teams          → fatigue discount 15-20%
⑩ Macau AH deviating from others  → gap vs Pinnacle >0.15 → alert
```

### OU Analysis Framework

**Expected goals formula**: `(GF_home × GA_away/avg + GF_away × GA_home/avg) / 2`

```
Compare with OU line:
  Expected > OU + 0.5 → over signal
  Expected < OU − 0.5 → under signal
  Within ±0.5 → market efficient, no extra signal
```

**Draw exclusion method**:
```
All 4 true → low draw probability, over tendency enhanced:
  □ Both teams: no 0-0 in last 3 matches
  □ Combined avg goals >2.5
  □ OU 2.5 over water ≤1.85
  □ No "defensive fortress" team (Rule #27)

Any 1 true → high draw probability, under tendency:
  □ Either team: 2+ draws in last 3 matches
  □ Combined avg goals <2.0
  □ Opening OU ≤2.0
```

**Correct Score weighted goals**:
```
From CS market lowest-odds top 5 scores:
  Implied prob = (1/cs_odds) / Σ(1/all_cs_odds)
  Weighted_OU = Σ(score_total × implied_prob)
  Weighted_OU > OU + 0.3 → over; Weighted_OU < OU − 0.3 → under
```

**8 OU pathway patterns**:
1. Over water drop + AH unchanged → +15% over confidence
2. Over water rise >0.15 + AH unchanged → check Betfair volume
3. Water fluctuation <0.05 → stable, follow initial analysis
4. OU rises (2.5→2.75) + over water drops → strong over; + over water rises → bait alert
5. OU drops (2.5→2.25) → market lean under; if both teams attacking → possible misdirection
6. 1X2 pattern 2.XX-3.XX-2.XX → draw prob +8-12% → under tendency
7. AH deep (≥-1.5) + OU moderate (2.5-3.0) → favorite covers but limited total goals
8. AH shallow (±0.25) + OU high (≥3.0) → attacking game, both teams to score likely

### Signal Weight System

**1X2 signals**: Kelly >1.05 → +12% | BF divergence → −15% | BF volume >65% single → −10%

**AH signals**: Late rise + water unchanged → +15% | Late drop + water unchanged → −15% | Water drop >0.10 → +10% | Heating confirmed → reverse signal | Suppression confirmed → +10%

**OU signals**: Expected > OU +0.5 → +15% over | Draw exclusion all true → +10% over | CS-weighted > OU +0.3 → +10% over | Pattern 1 (over water drop) → +15% over | Pattern 6 (2-3-2 odds) → −10% over

**Confidence cap**: Max 90%, floor 10% for any direction.

### 3-in-1 Comprehensive Analysis Flow

```
STEP A — Static odds analysis:
  ├─ Pinnacle 1X2 → de-vigged prob + Kelly index
  ├─ P&L index (with Betfair volume)
  └─ Betfair hot/cold signals

STEP B — Handicap positioning:
  ├─ Theoretical vs actual AH → depth judgment
  ├─ Live 4h AH/water changes → 4-pattern detection
  └─ Heat manipulation 3-tactic identification

STEP C — OU analysis:
  ├─ Expected goals vs OU line
  ├─ Draw exclusion method
  ├─ CS-weighted goals
  └─ 8-pathway pattern matching

STEP D — Signal synthesis:
  ├─ 1X2 + AH + OU → 3D cross-validation
  ├─ Consensus (≥2/3 same direction) → HIGH confidence
  ├─ Conflict → downgrade, mark "CAUTION"
  └─ Output: direction + confidence + risk alerts
```

### Theoretical Line Calculation

```
4 dimensions:

① Strength gap (40%): rank gap ≥10 → base +1.0; GF gap >1.0 → +0.25; GA gap >0.8 → +0.25
② Home/away (25%): equal strength → home +0.5; strong away = home handicap −1.0
③ H2H history (20%): 5-6 wins + avg margin ≥2 in last 6 → +0.5~+1.0; balanced → −0.25; underdog dominant → −0.5
④ Motivation & injuries (15%): key player out → −0.5~−1.0; survival/title push → +0.5; double match week fatigue → −0.25
```

### Line Depth Judgment

```
Fair (actual = theoretical): institution agrees with fundamentals → focus on water + live changes
Shallow (actual < theoretical by ≥0.5):
  + high water (>1.00) + fundamental doubts → institution skeptical → consider underdog
  + low water (<0.85) + fundamentals solid → lowering entry to attract bets → institution bullish

Deep (actual > theoretical by ≥0.5):
  + low water stable + weak opponent defense → institution bullish → favorite covers
  + high water (>1.02) + strong opponent defense → inflating to create illusion → bait
```

### Live AH Four Mantras

```
┌──────────────┬──────────────────────┬──────────────┐
│  AH Change   │       Meaning        │    Action    │
├──────────────┼──────────────────────┼──────────────┤
│ Rise + Drop  │ Genuinely bullish    │ Follow fav   │
│ Rise + Rise  │ Bait (false bullish) │ Avoid/Under  │
│ Drop + Rise  │ Bearish              │ Follow under │
│ Drop + Drop  │ Suppress (false bear)│ Bet favorite │
└──────────────┴──────────────────────┴──────────────┘

Prerequisites: combine with line depth + fundamentals. Never use alone.
Historical hit rates: Rise+Drop cover 65%, Drop+Rise underdog 62%, Drop+Drop cover 58%, Rise+Rise cover 38%.
```

### Water Movement 3 Patterns

```
Pattern 1 — Unidirectional: water 0.95→0.80, AH unchanged
  → Institution actively reducing payout → genuine bullish signal
Pattern 2 — Oscillating: water 0.90→1.05→0.85 repeatedly
  → Large market flow → check fundamentals for catalyst
Pattern 3 — Reverse: underdog water 0.80→1.00; favorite 1.00→0.80
  → Institution guiding money toward underdog → reverse bait → follow favorite

Key time nodes: opening (3-5 days before, exploratory) → mid (1-2 days, volume surge, higher credibility) → live (1-2h before, news impact + bait risk) → closing (30 min, highest institutional conviction)
```

### League-Specific Characteristics

```
Premier League: straightforward, home advantage significant (~45% home win)
  → "Follow the rise, not the drop" — rising line more trustworthy
Bundesliga: strong/weak clear, over rate high (>55% OU 2.5)
  → Rising line + water drop signals trustworthy
Serie A: high draw rate (~28%), conservative handicaps
  → "Beware weekend upsets" — strong team -1.0 needs caution
La Liga: technical play, fast HT pace
  → Line changes frequent, must verify with water + fundamentals
Ligue 1: PSG dominates, others erratic
  → "PSG at home = solid, others = cautious"
Nordic leagues: high volatility, high upset rate (+23% in 1-5 AM window)
  → Beginners should avoid
World Cup (this skill's focus): high attention, massive volume, sophisticated bait techniques
  → Apply Section 9 knockout special rules; map JCL RSPF (Part VII)
```

### Three Abnormal Signal Types

```
Signal 1 — Opening vs historical line deviation
  Same team vs same opponent, historical handicap 1.0, current only 0.25
  → Strength decline / motivation loss / key absence → gap ≥0.5 → alert

Signal 2 — Water spike
  1 hour: water 0.80 → 1.10
  → Large reverse flow OR breaking news → check latest lineup/injury news immediately

Signal 3 — Asynchronous change
  Mainstream (Pinnacle/bet365) all rise, one (Macau) drops
  → That bookmaker has independent info → secondary reference only; must cross-verify
```

### Bankroll Management & 5 Pitfalls

```
Bankroll rules:
  Single bet cap: ≤5% of total bankroll
  Daily stop loss: 10% loss → pause
  Profit extraction: 50% gain → withdraw principal, play with profit
  Parlay warning: 3-fold+ long-term guaranteed loss (11% vig)
  Flat betting: same amount per bet regardless of confidence

5 rookie pitfalls:
  ① Index worship → pure odds analysis <45% long-term accuracy
  ② Fundamental bias → pure team analysis misses 38% of signals
  ③ "Mosquito meat" trap → 1.20 odds need 5 straight wins to cover 1 loss
  ④ Parlay chasing → 6-fold return rate only 49% vs single's 89%
  ⑤ Loss martingale → emotional doubling, daily loss amplified 3.2×

Risk mantra: "Fair line + stable water = bettable; Hot match + extreme deep line = avoid; Familiar league × 1-2 = focus; 3 straight misses = pause and review."
```

---

## APPENDIX: POST-MORTEM FINDINGS (Key Learnings)

### 28-Match Full Cycle Performance (6/12–6/19)

| Metric | Raw | Corrected (v2.x) |
|--------|:---:|:---:|
| W/L accuracy | 18/28 (64.3%) | ~22/28 (79.2%) |
| Exact score | — | ~3/24 (12.5%) |
| Within 1 goal | — | ~14/24 (58.3%) |
| Mixed parlay ROI | — | +107.8% (6/6 tickets) |

### Systematic Score Bias Root Causes

Three root causes for consistent ±1 goal score errors:
1. **xG insufficiently aggressive in extreme mismatches** → 14.0b Stomp xG fix (+1.5 boost)
2. **Host nation historic xG explosion overlooked** → 14.0c Host xG fix (+1.0 boost)
3. **Multi-factor nonlinear compounding** → cross-trigger cap mechanism

### Key Post-Mortem Rules (Condensed)

| Date | Match | Error | Root Cause | Rule Created |
|------|-------|-------|------------|--------------|
| 6/19 | CZE 1-1 RSA | Called CZE win | Narrative compression (RSA 2 suspensions drove CZE odds down, CZE overvalued) | Anti-Narrative Check (Step 1.5), Trap #7 trigger |
| 6/19 | SUI 4-1 BIH | Called narrow win | Overweighted single result (BIH's 1-0 over JPN ≠ strength) | "One match ≠ ability" principle; Wins ≠ reliable indicator until 3+ matches |
| 6/19 | CAN 6-0 QAT | Predicted 2-0 | Host historic xG ignored | 14.0c Host xG (+1.0 boost), Rule #26 extreme favorite floor |
| 6/19 | MEX 1-0 KOR | Predicted KOR | WC history system > Asian ranking | Priority: WC history > continental rank |
| 6/16 | All draws day | Predicted outcomes | Systematic overconfidence in 1X2 direction | Rule #19 (draw prob >30% = uncertainty), all-draw day full skip |
| 6/14 | High-scoring matches | Underpredicted | xG model conservative on attacking teams | 14.0b Stomp xG for extreme favorites |
| 6/13-14 | Debut matches | Overpredicted favorites | First-point hunger + heat discount ignored | Rules #27-28, Back-to-Wall effect |
| 6/20 | W/L correct, scores off | xG systematic bias | Multi-factor nonlinear effects unaddressed | 14.0a away xG strong-D discount, cross-trigger cap |

### 2022WC Knockout Backtest

16 matches, SPF direction 94% accuracy, mixed parlay +62% return (international odds) / +37% (Chinese lottery odds).

Three critical knockout corrections: 14.0d draw baseline (floor 28%), 14.0 defensive fortress pre-assessment, 14.0e ultra-low odds fragility. The biggest profit source was NOT hit rate but **70% of betting days correctly skipped**.

---

## QUICK START & BOUNDARIES

### Register OddsPapi
`WebSearch "oddspapi register"` → register → copy API key → provide to WorkBuddy.

### Daily Execution Plan
```
1. /v4/fixtures cache (one-time) → 1 quota
2. For each match day: 3× historical-odds check → 0 quota
3. T-1h: /v4/odds-by-tournaments → 1 quota (if first pull)
4. Full 12+1 step analysis per match
5. Generate HTML report + mixed parlay portfolio
```

### Boundary Rules

- Pure analysis and education — no guarantee of match outcomes
- Overround (vig) creates negative mathematical expectation in the long run
- Many factors are unpredictable: last-minute injuries, referee decisions, weather, player form
- Comply with local laws and regulations
- Live matches ONLY (status=1 in fixtures response). Do not analyze postponed/aborted matches.
- Never bypass quota confirmation under any pretext.
- Analysis priority: W/L direction first, score second.
- If confidence <50% → force "low confidence" warning in every output.
- Count quota usage accurately — if exceeds 250/month, mention immediately and recommend switching to WebSearch fallback.
