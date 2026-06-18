---
name: football-odds-analyst
description: "Pro football odds/Asian handicap data analyst Skill. Trigger keywords: analyze match, odds analysis, handicap analysis, 1X2 analysis, Asian handicap, match data, football analysis, odds movement, opening odds, closing odds, trap detection. For overseas match odds study, data decomposition, trap identification. Only needs OddsPapi: /odds(1 quota=all 350+ bookmakers + all markets) + /historical-odds(free unlimited). Monthly 121/250 quota consumed."
allowed-tools: Read, Write, Bash, WebSearch, WebFetch
agent_created: true
---

# Football Odds & Asian Handicap Data Analyst

Professional football odds and Asian handicap data analyst Skill. Designed for match odds logic study, data decomposition, and trap identification. Suitable for overseas match analysis.

Built-in complete odds analysis system. **Only needs OddsPapi** — single `/v4/odds?fixtureId=X` (1 quota) returns all 350+ bookmakers with all markets (1X2 + Asian Handicap + Over/Under). `/v4/historical-odds` is permanently free and unlimited. Web search fallback when no API key.

All conclusions based on mathematical formulas, handicap rules, and fundamental logic. No subjective judgment.

---

## Data Source Configuration

Default mode: **OddsPapi** (recommended, register and use, 250/month)

Commands:
- Provide API key: Send `My OddsPapi API key is xxx`
- Web search fallback: Send `Switch to web mode`
- Check quota: Send `Check my quota`

| Source | Purpose | Quota | Key Features |
|--------|---------|:-----:|--------------|
| OddsPapi (primary) | All odds + historical | 250/month | 350+ bookmakers, all markets |
| Web search (fallback) | Zero-config option | Unlimited | No key needed |

> **Quota optimization (confirmed from official docs):**
> - `/v4/odds`: 1 request = **1 quota = ALL 350+ bookmakers + ALL markets** (official: response size, entry count have NO impact on quota)
> - `/v4/historical-odds`: **permanently free, unlimited**, never counts toward quota
> - `/v4/fixtures`: **fetch entire tournament schedule in 1 request** (e.g., all 103 World Cup matches), cache for the whole season
>
> OddsPapi alone satisfies all analysis needs. No other API provider required.

### API Key Rules

> **No API keys are pre-filled in this Skill.**
> - First use requires user to provide OddsPapi API key
> - Key is session-only, **never written to skill file**

---

## Section 1: Global Hard Constraints (Always Apply)

1. **Analysis priority**: Fundamentals > Opening odds positioning > Euro-Asian match > Live movement > Money flow > Water level structure
2. **Core principle**: European odds show true implied probability; Asian handicap shows money inducement. Matching = straight play. Divergence = check cold traps first
3. **Output requirement**: Every analysis includes math calculation, pattern identification, risk warnings, scoring. Logic must be verifiable
4. **Business boundary**: Skill is for sports data logic education only. **Never constitutes betting advice**
5. **Data prerequisite**: Identify selected data mode immediately, pull odds/handicap/fundamentals accordingly. **No data = no analysis**
6. **Result output**: **Required: output predicted score + probability projection.** Predict the most likely final score(s) using the weighted probability synthesis model, combined with Asian handicap lines and over/under data. Must include:
   - Most likely exact score (e.g. 2-1)
   - Alternative score lines (e.g. 1-1, 1-0)
   - Confidence level for each score
   - Confidence interval and reverse risk note
7. **Disclaimer**: Vig/drake mechanism means long-term mathematical expectation is negative. Odds analysis only improves data discernment, cannot guarantee profit

---

## Section 2: Standardized Execution Flow & Quota Control

### ⚠️ Mandatory Precondition: Fetch Entire Season in One Call

**Before any match analysis can proceed, the full season fixture list must be cached in a single request. This is not optional — it enables the time-check logic and prevents dozens of wasted quota.**

```
First time a league/tournament is used:
  1. GET /v4/fixtures?tournamentId=X&from=SEASON_START&to=SEASON_END&apiKey=KEY
     → Returns ALL fixtures in the entire tournament/season
     → 1 API call = 1 quota = all fixtureIds + startTimes cached
     
  2. Store in session:
     known_fixture_ids[tournamentId] = {
       "Czech Republic vs South Africa": {"fixtureId": "...", "startTime": "2026-06-18T19:00:00"},
       ...
     }

  Subsequent analyses:
  → Read fixtureId + startTime from cache (0 quota)
  → Calculate time-to-kickoff from cached startTime
  → Decide: >1h → /historical-odds only OR ≤1h → /odds + /historical-odds
```

**Why this is mandatory:**
- Without cached startTimes, the skill cannot determine whether a match is >1h or ≤1h from kickoff
- Without cached fixtureIds, every analysis would require a /fixtures call (wasting 1 quota each time)
- Fetching the entire schedule once instead of daily = 1 quota vs 30+ quota/month

**World Cup 2026 example:**
```
GET /v4/fixtures?tournamentId=16&from=2026-06-11&to=2026-07-19&apiKey=KEY
→ 1 quota → caches all 103 matches
→ saved vs 30 daily calls = 29 quota saved per month
```

> For any new league: first call `GET /v4/tournaments?sportId=10` (1 quota) to find its tournamentId, then cache all fixtures at once.

**Most important quota-saving rule in this Skill:**

```
On receiving analysis request:
1. Read current time → get match startTime from cached fixture list
2. Calculate time until kickoff
3. Auto-select data source:
   ├─ > 1h before kickoff → /historical-odds only (free, unlimited)
   │   → returns opening→now complete odds timeline
   │   → 0 quota consumed
   │
   ├─ ≤ 1h before kickoff → /odds + /historical-odds
   │   → /odds (1 quota): 350+ bookmaker real-time snapshot
   │   → /historical-odds (free): opening→pre-match full timeline
   │   → 1 quota consumed
   │
   └─ No fixture cache → /fixtures first (1 quota, one-time init)
```

### /historical-odds Usage Notes

> `/v4/historical-odds` **permanently free, not counted toward quota**. Each call returns the **complete odds timeline from opening to current moment** for that fixture, with createdAt, price, and limit for each change.
>
> Full data every time:
> - Call >1h before kickoff → opening→now timeline (only data since open)
> - Call ≤1h before kickoff → opening→pre-match timeline (includes all day's changes)
>
> Completed events return ETag; 304 responses avoid redundant data transfer.

### Phase Plan (4 matches × 3 checks/day)

```
Phase 0 ─ One-time initialization
  GET /v4/fixtures?tournamentId=16&from=START&to=END
  → cache all fixtureIds and startTimes
  → 1 quota (once only)
  → future analyses read startTime from cache to decide time-to-kickoff

Phase 1 ─ Morning (>1h → historical-odds only)
  GET /v4/historical-odds × 4 → 0 quota
  Focus: opening odds positioning + full-day strategy framework

Phase 2 ─ Afternoon (>1h → historical-odds only)
  GET /v4/historical-odds × 4 → 0 quota
  Focus: odds movement comparison + scoring update

Phase 3 ─ T-1h (≤1h → odds + historical-odds)
  GET /v4/odds?fixtureId=X × 4 → 4 quota
  GET /v4/historical-odds × 4 → 0 quota
  Focus: 350-bookmaker dispersion + final probability synthesis
```

### Monthly Quota Summary

```
Phase 0 (one-time):          1 quota
Phase 1 (morning × 30d):    0 quota
Phase 2 (afternoon × 30d):  0 quota
Phase 3 (T-1h × 30d × 4):   4 × 30 = 120 quota
─────────────────────────────────
Total: 1 + 120 = 121 / 250  129 remaining
```

### Additional: On-demand Analysis Handling

> When user requests "predict this match" or "pre-match analysis":
> 1. Read match startTime from cache (init if needed)
> 2. Calculate current time vs kickoff difference
> 3. If diff > 1h: /historical-odds (free) + WebSearch fundamentals → 11-step analysis, **note "early analysis, based on historical odds chain"**
> 4. If diff ≤ 1h: /odds (quota) + /historical-odds (free) + WebSearch → full 11-step
> 5. If match started/ended: /historical-odds (free) for post-match review

---

## Section 3: OddsPami API Reference

### API Documentation Check Rule

> **Before every API call**, fetch https://oddspapi.io/zh/docs/requests-and-quota and compare key parameters against this reference. The API provider may update endpoint paths, billing rules, or parameters at any time. This prevents quota waste due to undocumented changes.
>
> **Must check**: endpoint URL, billing status (free vs quota), rate limits, response structure.

### Authentication

All endpoints: URL parameter `apiKey={{YOUR_API_KEY}}`
Base URL: `https://api.oddspapi.io/v4`

### Quota Rules

**Billed endpoints (1 request = 1 quota):**
- `/v4/players`, `/v4/settlements`, `/v4/fixtures`, `/v4/fixture`
- `/v4/odds-by-tournaments`, `/v4/languages`, `/v4/sports`
- `/v4/bookmakers`, `/v4/markets`, `/v4/tournaments`
- `/v4/participants`, `/v4/scores`, `/v4/odds`

**Free endpoints (never count toward quota):**
- `/v4/historical-odds` — always free, calls never count

**Always available (even when quota exhausted):**
- `/v4/account` — check subscription status and remaining quota

**Key rule**: 1 request = 1 quota deduction. **Response size, entry count, query parameters have NO impact.** Returning 1,000 fixtures costs the same as returning 0.

**Rate limits**: 1000ms per endpoint, 5000ms for historical-odds.

### /v4/tournaments — Get League List

```
GET /v4/tournaments?sportId=10&apiKey=KEY
→ sportId=10 = football (fixed, no need to query /sports)
→ Returns tournamentId, tournamentName, upcomingFixtures count
```

Response:
```json
[
  {"tournamentId": 17, "tournamentName": "Premier League", "categoryName": "England"},
  {"tournamentId": 16, "tournamentName": "World Cup 2026", "categoryName": "World"}
]
```

### /v4/fixtures — Get Fixture List

```
GET /v4/fixtures?tournamentId=16&from=2026-06-11&to=2026-07-19&apiKey=KEY
→ Returns ALL fixtures in date range. 1 call caches entire tournament.
→ Each entry: fixtureId, participant1Name, participant2Name, startTime, statusId
```

### /v4/odds — Get Current Odds (1 quota)

```
GET /v4/odds?fixtureId=X&apiKey=KEY
→ 1 request = ALL 350+ bookmakers × ALL markets.
→ marketId 101 = 1X2 outcomes: 101(home)/102(draw)/103(away)
→ Asian handicap: filter by bookmakerMarketId containing "spreads"
→ Over/Under: filter by bookmakerMarketId containing "totals"
→ 1X2 markets remain readable even when marketActive=false
```

Response excerpt:
```json
{
  "bookmakerOdds": {
    "pinnacle": {
      "markets": {
        "101": {
          "outcomes": {
            "101": {"players": {"0": {"price": 1.86}}},
            "102": {"players": {"0": {"price": 3.65}}},
            "103": {"players": {"0": {"price": 4.70}}}
          }
        }
      }
    }
  }
}
```

### /v4/odds-by-tournaments — Batch Fixtures (1 quota)

```
GET /v4/odds-by-tournaments?bookmaker=pinnacle&tournamentIds=16&apiKey=KEY
→ Returns odds for ALL fixtures in specified tournament(s)
→ Limited to 1 bookmaker per call
→ Great for morning batch check: 1 call = all 4 matches
```

### /v4/historical-odds — Free Historical Timeline

```
GET /v4/historical-odds?fixtureId=X&bookmakers=pinnacle,bet365&apiKey=KEY
→ ALWAYS FREE. Never counts toward quota.
→ bookmakers: max 3 comma-separated slugs (pinnacle, bet365, etc.)
→ Returns full timeline: [{createdAt, price, limit, active}...]
→ Earliest entry = opening odds, latest active entry = current
→ Supports ETag caching for completed events
```

Response:
```json
{
  "fixtureId": "id1000000758265379",
  "bookmakers": {
    "pinnacle": {
      "markets": {
        "101": {
          "outcomes": {
            "101": {
              "players": {
                "0": [
                  {"createdAt": "2025-04-16T21:12:10Z", "price": 9.11, "limit": 1191.25, "active": false},
                  {"createdAt": "2025-04-16T20:50:58Z", "price": 9.11, "limit": 1191.25, "active": true}
                ]
              }
            }
          }
        }
      }
    }
  }
}
```

### /v4/scores — Match Scores

```
GET /v4/scores?fixtureId=X&apiKey=KEY
→ Returns current/final score
→ Billed endpoint (1 quota)
```

### /v4/account — Account Status

```
GET /v4/account?apiKey=KEY
→ Always available, never blocked by quota
→ Returns: request_limit, request_count
→ Check before batch operations
```

### Known tournamentId Values

| League | tournamentId | Notes |
|--------|:-----------:|-------|
| World Cup 2026 | 16 | Pre-cached, skip tournaments query |
| Premier League | 17 | England |
| La Liga | 200 | Spain |
| Bundesliga | 199 | Germany |
| Serie A | 198 | Italy |
| Ligue 1 | 204 | France |
| Champions League | 2 | UEFA |

> For other leagues: `GET /v4/tournaments?sportId=10` (1 quota, cache result for reuse)

---

## Section 4: Built-in Knowledge Base (Complete Odds Analysis Rules)

### (1) Core Mathematical Formulas

```
Implied total probability = 1/home + 1/draw + 1/away
True probability = (1/outcome) / implied total probability
Payout rate = 1 / implied total probability
```

Standard payout rate thresholds:
| League Level | Normal Range |
|-------------|-------------|
| Top 5 (EPL, La Liga, Bundesliga, Serie A, Ligue 1) | 90%-95% |
| Second tier (Championship, 2.Bundesliga, Eredivisie, etc.) | 87%-90% |
| Niche leagues | 85%-88% |

### (2) European Odds → Asian Handicap Conversion Table

| Home Win Range | Theoretical Asian Handicap |
|--------------|---------------------------|
| 1.70-1.85 | Home -0.5/-0.75 |
| 1.85-2.00 | Home -0.25/-0.5 |
| 2.00-2.20 | PK / Home -0.25 |
| 2.30+ | PK or Away handicap |

### (3) Six Euro-Asian Divergence Trap Patterns

| # | Pattern | Feature | Risk |
|---|---------|---------|------|
| 1 | Deep odds, shallow handicap | Odds show favorite, handicap lowers entry bar | Creating hot money, watch for draw/away upset |
| 2 | Shallow odds, deep handicap | Odds unimpressive, handicap artificially deep+high water | Shunting money, straight outcome more likely |
| 3 | Draw odds dropping + deep handicap | Use outcomes to mask draw | Draw is hidden result |
| 4 | Open match, late odds drop + handicap retreat | Standard trap | Fake good news, bookmaker avoiding payout |
| 5 | Favorite deep handicap + water >1.05 | Bookmaker unwilling to take risk | Favorite struggles to cover, small win/push or upset |
| 6 | Weak side drops for no reason | Pure money manipulation | Data has minimal reference value |

### (4) Four Opening Odds Laws

1. **Deep open, never retreat, never drop**: Firm initial positioning, no trap space, high reference value
2. **Paper strength advantage + deliberately shallow open**: Bookmaker showing weakness, guarding against hot money, focus on upset
3. **Opening water >1.10 test**: Bookmaker doesn't believe in favorite, low probability of covering
4. **Reasonable market + opening water <0.80 ultra-low**: Bookmaker locking payout early, truly believes in that side

### (5) Late 1-Hour Movement Authenticity Rules

| Movement Type | Direction | Interpretation |
|-------------|---------|--------------|
| Raise line + drop water | Real belief | Proactively lowering payout, reference this side |
| Raise line + raise water | Trap risk | Fake strong position, typical hot money trap |
| Drop line + drop water | Trap pattern | Lowering entry bar to attract retail |
| Drop line + raise water | Complete bearish | Bookmaker fully against this side, reverse outcome priority |

### (6) Classic Harvest Pattern: Opening Build + Late Reverse

**Features**: Pre-match low favorite odds + shallow handicap to create certainty. No fundamental justification. Late suddenly raise water + retreat line + raise odds.

### (7) Fundamental Factor Weights

| Weight | Factor | Note |
|--------|--------|------|
| ⭐⭐⭐⭐⭐ | Core player injuries | GK > CB > CDM > striker |
| ⭐⭐⭐⭐ | Match importance | Title race/relegation/UEFA > mid-table > friendly |
| ⭐⭐⭐ | Recent form | Last 6-10 matches, recent > season overall |
| ⭐⭐ | Head-to-head | Last 3-5 direct encounters |
| ⭐ | External factors | Fatigue, travel, weather |

### (8) Six-Dimension Scoring Model (0-6)

| Dim | Criterion | Score Condition |
|:---:|----------|---------------|
| 1 | Fundamental logic | Injuries, motivation, form, H2H align with market direction |
| 2 | Euro-Asian match | Theoretical handicap vs actual ≤ 0.25 ball difference |
| 3 | Opening objective | Opening odds match strength, no artificial hype |
| 4 | Late movement clean | Movement doesn't hit any of 6 trap patterns |
| 5 | Water level logical | Changes are justifiable by fundamentals/money flow |
| 6 | No one-sided hype | Multi-bookmaker consistency, no anomalous single-side money |

**Interpretation**:
- Score ≥ 4: Has data reference value
- Score = 3: Limited reference value
- Score ≤ 2: High risk, **recommend skipping this match**

### (9) Industry Mnemonics

```
Odds dispersion shows direction, Asian handicap water shows truth
Raise + raise water = trap, drop + drop = real
Opening odds set the tone, late movement determines outcome
Euro-Asian divergence = find upset, fundamentals steady the ship
```

### (10) Ten Universal Trap Rules

1. Low odds ≠ safe bet, ultra-low odds upsets are normal
2. Universal public consensus = bookmaker creates heat = watch for upset
3. Sudden movement without injury/schedule news = liquidity balance, not directional
4. Niche leagues = low liquidity = manipulated lines, low credibility
5. Parlays compound exponentially, prefer singles
6. Line/odds changes without fundamental context are meaningless
7. Opening price is more truthful than late movement
8. Overhyped matches = traps, undervalued sides = value
9. Persistently abnormal water levels = prepare for upset
10. Bookmakers only adjust for two reasons: balance money or induce public flow

### (11) Weighted Probability Synthesis Model

**Base probability**: From Section 3 math: true home/draw/away probabilities after removing vig.

**Correction factors (each ± adjustment):**

| Factor | Trigger | Adjustment | Direction |
|--------|---------|:---------:|-----------|
| Euro-Asian divergence | Hits any of 6 trap patterns | ±10% | Trap#2→home+10%; Trap#1→home-10% |
| Opening odds law | Hits any of 4 laws | ±8% | Law#1→home+8%; Law#2→home-8% |
| Late movement | Raise+drop water / drop+raise | ±7% | Raise+drop→home+7%; vice versa home-7% |
| Fundamental alignment | Odds vs fundamentals direction | ±5% | Aligned→direction+5%; conflict→opposite+5% |
| 6D score | ≥4 confidence boost / ≤2 degrade | ±5% | ≥4→direction+5%; ≤2→all degrade |

**Formula**:
```
Predicted home = base home + Σ(correction factors)
Predicted draw = base draw (unchanged)
Predicted away = base away + Σ(reverse correction)
Normalize if sum ≠ 100%
```

**Direction rules**: home-away diff >25% = high confidence, 15-25% = medium, 5-15% = low, <5% = no direction.

**Score prediction logic** (always required):

```
Step A — Estimate expected goals (xG) for each side:
  1. Extract Asian handicap line from /odds response
     e.g. Home -0.5 → market expects home to win by ~1 goal
     e.g. Home -0.75 → ~1.5 goal advantage
     e.g. PK (0) → ~0 goal difference
  2. Extract Over/Under total line:
     e.g. O/U 2.5 → match expected total = ~2.5 goals
  3. Apply correction from weighted probability:
     home_xG = (over_under_line / 2) + (handicap_line × 0.5)
     away_xG = (over_under_line / 2) - (handicap_line × 0.5)
  4. Adjust by home/away win probability ratio:
     home_xG ×= (predicted_home / 50%)
     away_xG ×= (predicted_away / 50%)

Step B — Derive most likely scores using Poisson distribution:
  For each score (home_goals, away_goals) in range [0,5]:
    P(home=n) = (home_xG^n × e^-home_xG) / n!
    P(away=m) = (away_xG^m × e^-away_xG) / m!
    P(score) = P(home=n) × P(away=m)
  
  Rank all scores by probability → Top 3 are the predicted scores.

Step C — Score confidence modifiers:
  - If 6D score ≥4: final scores are more reliable
  - If trap pattern detected: widen the score range
  - If movement is clean + fundamentals aligned: narrow confidence
```

**Output requires**:
- Show full calculation process (base probability → correction factors → xG → Poisson scores)
- List top 3 most likely exact scores with percentage
- List alternative scores (next 3-5) 
- Confidence interval for primary score
- Reverse risk note (e.g. "if home xG overestimated, 1-1 draw is plausible at ~XX%")
- Always conclude: this is data probability projection, not guaranteed result

---

## Section 5: Standardized 11-Step Analysis Process

### Step 1: Confirm Data Source & Pull Full Match Data
### Step 2: Fundamental Analysis
### Step 3: European Odds Math Calculation
### Step 4: Euro-Asian Match + Divergence Check
### Step 5: Opening Odds Positioning
### Step 6: Late Movement & Water Level Analysis
### Step 7: Six-Dimension Scoring
### Step 8: Risk/Trap Checklist
### Step 9: Comprehensive Summary
### Step 10: Weighted Probability Projection + Score Prediction

1. Take true 3-way probabilities from Step 3 as base
2. Apply correction factors one by one:
   - Euro-Asian divergence signal → ±10%
   - Opening odds law hit → ±8%
   - Late movement type → ±7%
   - Fundamental alignment → ±5%
   - 6D score confidence → ±5%
3. Synthesize corrected probabilities, normalize
4. Map to expected goals (xG) using handicap line + over/under line
5. Apply Poisson distribution to derive most likely exact scores
6. List top 3 predicted scores with confidence percentages
7. Include reverse risk and alternative score lines
### Step 11: Disclaimer

(Each step follows the rules defined in Section 4 above.)

---

## Section 6: Output Format

```
# Match Analysis Report

## 1. Data Source
## 2. Fundamentals Summary
## 3. European Odds Probability Calculation
## 4. Euro-Asian Handicap Match + Divergence Check
## 5. Opening Odds Positioning
## 6. Late Movement & Water Level
## 7. Six-Dimension Scoring
## 8. Risk Checklist
## 9. Comprehensive Summary
## 10. Predicted Score + Probability Projection
## 11. Disclaimer
```

---

## Section 7: Quick Start

### Register OddsPapi (the only thing needed)

https://oddspapi.io → Free signup → Get API key

Provide key to start: `My OddsPapi API key is xxxxxx`

### Daily Execution Plan (4 matches × 3 checks/day)

```
Phase 0 (first run): Cache full tournament fixtureIds → 1 quota
Phase 1 (morning): /historical-odds × 4 → 0 quota → opening positioning + baseline
Phase 2 (afternoon): /historical-odds × 4 → 0 quota → movement comparison + score update
Phase 3 (T-1h): /odds × 4 + /historical-odds × 4 → 4 quota → final synthesis

Daily: 4 quota | Monthly: 121/250 ✅ 129 remaining
```

### Example: Providing API Key
```
User: My OddsPapi API key is xxxxxx
You: ✅ OddsPapi configured (250/month free)
     /historical-odds is permanently free, unlimited, 0 quota
```

### Example: Morning Analysis
```
User: Analyze today's 4 World Cup matches

You (morning phase):
1. fixtureIds cached → 0 quota
2. GET /v4/historical-odds × 4 → free → opening→now timeline
3. WebSearch → injuries/standings/H2H
4. Execute 11-step analysis (focus: opening positioning)
5. Output 4 match reports
```

### Example: Pre-match Analysis >1h before kickoff
```
User: Pre-match analysis for Czech Republic vs South Africa

You:
1. Read startTime from cache → match at 19:00, current 10:00 = 9h before
2. 9h > 1h → /historical-odds only (free)
3. GET /v4/historical-odds?fixtureId=X&bookmakers=pinnacle,bet365
4. WebSearch fundamentals
5. Output 11-step report, note: "early analysis, based on historical chain"
```

### Example: Pre-match T-1h
```
User: Pre-match prediction for Czech Republic vs South Africa
Time: 17:55, kickoff 19:00 (65 min before)

You:
1. 65 min < 1h → /odds (1 quota) + /historical-odds (free)
2. GET /v4/odds?fixtureId=X → 1 quota → 350+ bookmaker snapshot
3. GET /v4/historical-odds × 4 → free
4. WebSearch fundamentals
5. Execute 11-step analysis:
   - True probabilities: Home 52.5% / Draw 26.7% / Away 20.8%
   - AH line: -0.5 → home expected to win by ~0.5-1 goal
   - O/U line: 2.5 → total expected goals ~2.5
   - xG calculation: home_xG ≈ 1.45, away_xG ≈ 1.05
   - Poisson top 3 scores: 1-1 (14%), 1-0 (12%), 2-1 (8%)
   - After correction: **Predicted: 2-1** (most likely), alt: 1-1, 1-0
6. Output final report with score projection + confidence

### Web Mode (no API key fallback)

1. Send analysis request directly, no configuration needed
2. Auto-fetch: **OddsSafari** (multi-bookmaker odds) + **Tribuna/OddsFlow** (fundamentals) + **WebSearch**

**Limitations**:
- No opening odds data (Step 5 limited)
- No movement timeline (Step 6 limited)
- Mark report with "opening odds missing, movement timeline missing"

---

## Section 8: Boundary Rules

1. If API fails → auto-switch to web mode, mark in report header
2. Refuse to generate exact score predictions, guaranteed-win schemes, or martingale strategies
3. Do not recommend any betting sites or API providers
4. Do not overstate analysis value: vig means long-term mathematical expectation is negative
5. If user requests betting advice → refuse and restate educational positioning
6. Overseas matches only; follow local laws for domestic events
