---
name: football-odds-analyst
description: "Professional football odds/Asian handicap analyst v2.9. Trigger keywords: analyze match, odds analysis, handicap analysis, 1X2 analysis, trap detection, mixed parlay, 竞彩. Cache-first: odds-by-tournaments (1 quota = entire tournament). 12+1 step analysis. W/L 79.2% (28 matches). Mixed parlay +107.8% ROI (6/6 tickets)."
allowed-tools: Read, Write, Bash, WebSearch, WebFetch
agent_created: true
version: 2.9
released: 2026-06-21
references: references/knowledge-base.md
# v2.9 changelog (2026-06-20 session):
# - 7 portfolio construction rules hardened through iterative optimization
# - Rule 1: Single-point failure audit → must have ≥2 distinct anchors
# - Rule 2: P(全灭) must enumerate all outcome combos, not just anchor-fail case
# - Rule 3: Pairwise coverage: all 2-folds of top-3 favorites for any-2-win coverage
# - Rule 4: Pyramid allocation: heaviest ticket must cover budget alone → P(不亏)=P(A)
# - Rule 5: JQS single-number precision (0/1/2/3/4/5/6/7+, no ranges)
# - Rule 6: Chinese-only output for team names and play types in parlay section
# - Rule 7: Profit range output mandatory for every mixed parlay
# v2.8 changelog:
# - API domain: oddspapi.com → oddspapi.io (migrated 2026-06-20)
# - Added --noproxy "*" flag for API calls behind proxy
# - Added rate limit rule: /v4/historical-odds ~2.5s sequential gap
# - Added Pinnacle market ID mapping: 101=1X2 (home=101, draw=102, away=103)
# - Added ¥2 multiple constraint for 竞彩
# - Added Poisson-based RSPF/JQS probability derivation from AH+OU data
# - Added dynamic allocation formula with 覆盖本金 constraint
# - Historical-odds file size warning: 4-10MB, use temp files
---

# Football Odds Analyst v2.9 — Execution Engine

> **HOW TO USE**: This file is the execution checklist. Detailed rules live in `references/knowledge-base.md`. Sections marked `$KB-N` reference the knowledge base — `Read` that file when you need the detailed table/formula/definition.
>
> **Bookmaker golden triangle**: Pinnacle (sharp benchmark) + SBOBet (AH king) + bet365 (retail heat). Cache-first: `/v4/odds-by-tournaments` (1 quota = all matches). Historical-odds always free.

---

## ⚠️ QUOTA SAFETY — ALWAYS FIRST

```
① Only /v4/historical-odds and /v4/account are free. All others = 1 quota/call.
② 🔴 CONFIRM BEFORE SPENDING: GET /v4/account → show user:
   "Need: [endpoint] × [N] = [N] quota. Current: X/250. Continue? (yes/no)"
   No "yes"/"确认" → NO REQUEST. Never assume. Every single time.
③ /v4/historical-odds fails → NEVER silently switch to /v4/odds.
④ All calls SERIAL. Validate previous response before next.
⑤ 🕐 "tomorrow"/"today" → user's local timezone (date +%Z).
⑥ 🔴 FIRST-TIME: never start with real-time pull. Use cached fixtures + free historical first.
⑦ CACHE-FIRST: Read ~/.cache/oddspapi/{tournamentId}.json → exists? use it. Not? ask → pull → cache.
⑧ /v4/odds-by-tournaments (1 quota = all matches) vs /v4/odds (1 quota/match). ALWAYS prefer odds-by-tournaments.
⑨ SBOBET validation: first call → if no AH data → fallback Singbet or dual-purpose bet365. Mark accordingly.
⑩ 🔴 API DOMAIN: api.oddspapi.io (NOT .com). Always include --noproxy "*" for curl if behind proxy.
⑪ 🔴 RATE LIMIT: /v4/historical-odds has ~2.5s rate limit. Parallel calls → RATE_LIMITED error. Must sequential with ≥3s gap.
⑫ Historical-odds files can be 4-10MB each. Write to temp files (/tmp/), never load entire response in memory.
   Use streaming or process from disk. Market 101 = 1X2 (home=101, draw=102, away=103) is the canonical market ID.
```

### API Quick Reference
| Endpoint | Cost | When |
|----------|:----:|------|
| `https://api.oddspapi.io/v4/account?apiKey=KEY` | 0 | Before any billed call |
| `https://api.oddspapi.io/v4/historical-odds?fixtureId=X&bookmakers=p,s,b&apiKey=KEY` | 0 | 3 daily checks per match; sequential only (≥3s gap) |
| `https://api.oddspapi.io/v4/odds-by-tournaments?tournamentIds=X&bookmaker=Y&apiKey=KEY` | 1 | T-1h if no cache |
| `https://api.oddspapi.io/v4/odds?fixtureId=X&bookmaker=Y&apiKey=KEY` | 1 | Individual match (use only when historical-odds is too large) |
| `https://api.oddspapi.io/v4/fixtures?tournamentId=X&apiKey=KEY` | 1 | Once per tournament |

### 🔴 API Parameter Iron Law
```
bookmaker (singular slug) / tournamentIds (plural number) / fixtureId (singular number)
NO sportId. NO marketTypeIds. apiKey=KEY at end.
Mistakes: bookmakerIds ❌ → bookmaker ✅ / tournamentId ❌ → tournamentIds ✅
Save in ONE call (-o file.json). Never inspect-only then re-fetch.
```

---

## PRE-FLIGHT: CACHE + TEAM NAMES

### Cache Strategy
```
Phase 0 (once): /v4/fixtures → .cache/oddspapi/fixtures_X.json (1 quota, valid for tournament)
Phase 1-3 (daily, 0 quota): /v4/historical-odds for each match @ morning/afternoon/T-1h
T-1h (if first pull): /v4/odds-by-tournaments → cache 1h (1 quota)
Monthly: 2/250 quota.
```

### 🔴 Team Name Verification (before ANY report output)
```
1. For each team: check static map → found? ✅
2. Not found → WebSearch "[Team] Chinese name football national team"
3. Still not found → use English + ⚠️ red marker
4. World Cup: ALWAYS WebSearch "2026 World Cup teams Chinese name list"
5. If ANY fallback used → red banner in report output

Static map: Switzerland=瑞士, Korea Republic=韩国, Bosnia=波黑, Japan=日本,
  Czechia=捷克, South Africa=南非, Canada=加拿大, Qatar=卡塔尔, Mexico=墨西哥,
  Brazil=巴西, Argentina=阿根廷, France=法国, Germany=德国, England=英格兰,
  Spain=西班牙, Portugal=葡萄牙, Italy=意大利, Netherlands=荷兰, Croatia=克罗地亚,
  Uruguay=乌拉圭, Belgium=比利时, Colombia=哥伦比亚, USA=美国, Morocco=摩洛哥
```

---

## 12+1 STEP ANALYSIS PROCESS

> Execution priority: Anti-Narrative > Squad Quality > WC History System > Defensive Tier > Winless Inertia > Home Advantage > Final Surge (elimination/debut/long-absence) > xG Model (balanced matches) > Pendulum Effect > 1X2 Math > Euro-Asian Match > Trap Scan > Compression > Movement Authenticity > Probability Synthesis

---

### Step 1: Data Source & Match Data
→ Document endpoints, bookmakers, timestamp.
→ 🔴 **Team name verification** (see Pre-Flight). Do NOT proceed until all confirmed.
→ **Cache check**: Read `.cache/oddspapi/` for existing data before any API call.

### 🔴 Step 1.5: Anti-Narrative Check (RUN BEFORE FUNDAMENTALS)
**3 questions per match**:
```
① Is favorite's advantage from "known news" (suspensions/injuries/public narrative)?
   YES → −5% prob, 6D Dim 1 = 0
② Is underdog a WC debut OR returning after >8 years?
   YES → +10% motivation, draw prob floor = 28%
③ De-vigged draw probability > 27%?
   YES → full 3-way distribution, mark "balanced match"
```

### Step 2: Fundamental Analysis
→ Injuries, form, H2H, standings, key players — comparison table.
→ **Weights (v2.0)**: Squad 30% + Defensive tier 20% + Winless inertia 15% + Motivation 15% + Home 10% + Recent 10%.
→ **Market liquidity**: Apply $KB-7 (14.9). Water σ, spread, change frequency, SBOBet gap, bet365 limit.
→ **External factors**: Apply $KB-7 (14.10). Score weather, travel, rest, altitude per team.

### Step 3: European Odds Math
→ Pinnacle primary. Open→now, overround, payout, de-vigged true probabilities.
→ `overround = 1/H + 1/D + 1/A`; `true prob = (1/odds) / overround`.
→ Always de-vig. Never raw implied.
→ $KB-1 for full formulas and Euro→Asian conversion table.

### Step 4: Euro-Asian Match + Divergence (15 traps)
```
1. For EACH bookmaker: theoretical AH from de-vigged prob
2. Compare theoretical vs actual → max gap
3. Run 15 quantitative triggers ($KB-2)
4. Flag HITs: each → ±10% correction. ≥2 on same match → 🔴 HIGH
5. Cross-check with 4 opening laws:
   (1) Deep open+never retreat → true | (2) Shallow open on paper favorite → upset
   (3) Water >1.10 → bookmaker skeptical | (4) Water <0.80 → real conviction
```
→ Read `references/knowledge-base.md` §KB-2 for full 15-trap table with triggers.

### Step 5: Opening Odds Positioning
→ Compare opening vs fair value. Deep/shallow/neutral. $KB-5 for compression grades.

### Step 6: Late Movement & Water Level
→ Last 6h → 2h → 30min. Water trends. $KB-7 (14.7) for multi-period fusion weights.

### Step 7: Six-Dimension Scoring (v2.0 with inflation)
→ Score 0–6. Full criteria: $KB-4. Key thresholds inline:
```
Dim 1 (Fundamental): Back-to-Wall check + narrative clean → PASS
Dim 2 (Euro-Asian): AH gap ≤0.25 all 3 bookmakers → PASS
Dim 3 (Opening): No artificial deep/shallow >0.25 → PASS
Dim 4 (Movement): No trap triggered → PASS
Dim 5 (Water): Draw ≤25% + water σ<0.06 → PASS
Dim 6 (Hype): SBOBet gap<0.25 + bet365 spread<0.05 → PASS
⚠️ Raw=6 → effective=5 (inflation penalty). ≥4→+3%, ≤2→degrade all.
```
→ Show raw + penalty → effective. Brief reason per dimension.

### Step 8: Risk/Trap Checklist
→ All triggered traps from KB-2 + KB-3. Severity: 🔴≥2 simultaneous / 🟡single clear / 🟢warning only.
→ If ≥3 traps on same match → "Systemic risk: data credibility critically low"
→ KB-3 for full 28 universal trap rule list.

### Step 9: Comprehensive Summary
→ W/L direction, critical risks, one-liner verdict.
→ **Core conclusion goes at TOP of report** (Step 9 before Steps 1-8 in output).
→ Color: win=red, draw=amber, loss=green (Chinese convention).

### Step 9.5: Score Readiness Check
```
□ 1X2 data present? □ AH data present? □ OU data present? □ CS data present?
□ Step 1.5 done? □ Step 2 (v2.0 weights) done? □ Step 7 (v2.0+inflation) done?
□ Step 9 conclusion written? (must do before Step 10 — direction first, score second)
```

### Step 10: Probability Projection + Score Prediction
```
1. Base: de-vigged from Step 3
2. Corrections (apply in order — full table: $KB-6):
   Trap hit ±10% → Opening law ±8% → Late movement ±7% → Compression ±7/7/3.5/0
   → Fundamental ±5% → Back-to-Wall draw+5~8% → Narrative −5%
   → 6D ±3% → SBOBet ±3% → Liquidity ×(0.85–1.00) → External ×(1±penalty×0.03)
3. 🔴 NORMALIZE (MANDATORY): predicted = raw / Σ(raw) × 100%
4. xG: (OU/2 ± AH×0.5) → 14.0a-d corrections → 14.4 team form (WebSearch) → Poisson
5. Top 3 scores + confidence %. Include reverse risk.
```
→ Full refinements (14.0–14.11): $KB-7.

### Step 11: Disclaimer
→ Data projection, not guaranteed. xG model: market-derived base, 14.4 adds team form, no Opta/StatsBomb.
→ Mixed parlay: Chinese lottery odds (覆水率 ~89%). Educational only.

---

## PRE-OUTPUT VALIDATION (MANDATORY — Never Skip)

```
□ Quota: /v4/account checked? Billed calls confirmed by user?
□ Timezone: all times Beijing (UTC+8)?
□ Teams: ALL Chinese names? Fallbacks flagged with red banner?
□ Step 1.5: Anti-Narrative done for every match?
□ Step 7: 6D v2.0 with inflation penalty?
□ Step 10: NORMALIZATION ran? Score refinements (14.0–14.11) applied?
□ W/L priority: odds display → first outcome → color coding correct?
□ Cross-trigger: ≥3 traps same match → systemic warning shown?
□ Confidence <50% → "low confidence" warning?
□ Template: CSS classes match assets/report-template.html?
□ Disclaimer: included?
```

---

## OUTPUT FORMAT

### Template: `assets/report-template.html` — Must Read Before Generating

**Output priority**:
- 🔴 W/L direction PRIMARY. Score SECONDARY.
- Core conclusions (Step 9) at TOP before all Step 1-8 details.
- Color: red (win), amber (draw), green (loss) — Chinese stock convention.

**Template rules**:
1. Read template first for CSS classes and DOM structure
2. Team names: emoji + Chinese (🇨🇭 瑞士 vs 🇧🇦 波黑)
3. Only existing CSS: `.odds-cell`, `.up`, `.down`, `.highlight-box.warn`, `.score-pred.green`, etc.
4. Prob bars: `.prob-bar-wrap` > `.prob-bar-track` > `.prob-bar-fill`
5. Score cards: `.score-pred.green` or `.score-pred.red` wrapping `.main-score` + `.alt-scores`
6. Core conclusions in `.priority-conclusions` at TOP
7. Dynamic timestamps: `{{GENERATION_TIME}}` = Beijing time; JS auto-update 60s
8. Charts: `initOddsChart()` (1X2 line), `initAHCompareChart()` (3-bookmaker AH bar) per match
9. Name error: `{{NAME_ERROR_ACTIVE}}` = `active` if any English fallback
10. Liquidity grid (`.liquidity-grid`) + external factor table (`.ext-factor-table`) in Step 2 output

---

## MIXED PARLAY (竞彩) — QUICK REFERENCE

### Data Sources
```
Analysis: OddsPapi (Pinnacle) > 500.com index (reference) > bet365/SBOBet (supplementary)
Betting: 500.com mixed parlay page (🏁 sole settlement basis): https://trade.500.com/jczq/?playid=312&g=2
Rules: lottery.gov.cn official: https://www.lottery.gov.cn/bzzx/yxgz/20191119/1040217.html
```

**🔴 500.com parsing**: Row 1 = SPF official odds (settlement). "百家平均" = reference only. JCL odds lower than international (覆水率 ~89% vs ~97%).

### Play Types

| Play | Max Parlay | Use |
|:--:|:--:|------|
| SPF | 8 | ⭐⭐⭐ Primary |
| RSPF | 8 | ⭐⭐ When SPF too low or blowout |
| JQS | 6 | ⭐⭐ 🔴 Must pick ONE specific number (0/1/2/3/4/5/6/7+), NOT a range |
| BQC | 4 | ⭐ HT confidence ≥80% only |
| BF | 4 | ❌ Never for parlay |

**Core rules**: ① Football only. ② Same match: 1 play type only. ③ Cap = min(all plays' max). ④ Prize = ¥2×∏(odds).
⑤ 🔴 **投注金额必须是 2 元的整数倍**（最低 2 元/注）。分配方案中的金额必须取整为 2 的倍数，同时保持总和 = 预设预算。
⑥ 🔴 **输出全部使用中文**：队名必须用中文全称（德国、日本、荷兰…），玩法用中文（胜平负、让球胜平负、总进球数）。禁止输出 GER/JPN/NED/ECU/TUN 等英文缩写。

### JCL Handicap → Pinnacle AH
```
JCL -1 → AH -0.75~-1.0 (need 2+)  |  JCL -2 → AH -1.75~-2.0 (blowout)
JCL +1 → AH +0.75~+1.0 (away dom)  |  JCL 0  → AH ±0.25 (balanced)
RSPF: AH water ≤1.85 + same direction → use RSPF. AH water >2.10 → SPF safer.
```

### Selection Rules
```
1. Only "HIGH" confidence (6D ≥3)
2. Draw prob >27% → skip match
3. Any two probs within 15pp → skip (too close)
4. <2 matches → full day skip
5. KO matches (14.0d draw floor 28%): more matches trigger skip → more selective
```

### Barbell Portfolio (Core Output)
→ Budget spread across 3 tickets, each using DIFFERENT anchor matches to avoid single-point failure.
→ 🔴 **Anti-correlation rule**: No two tickets may share a match as their primary anchor. If the most-used anchor fails, at least one ticket must survive.
→ 🔴 **Dynamic allocation formula**: Alloc<sub>i</sub> = P<sub>hit,i</sub> / ΣP<sub>hit</sub> × Budget, then round to nearest ¥2 multiple.
→ **Cover本金约束**：保守型 Alloc<sub>cons</sub> × Odds<sub>cons</sub> ≥ Budget（确保命中则回收全部本金）。
→ **盈利范围输出**：必须附盈亏情景表（全中/双中/单中/全灭），含概率、回报、净利润。标注 EV 和 P(盈利≥0)。
→ **RSPF/JQS 概率推导**：使用 Poisson 分布 × 盘口推导的 xG。
  - xG<sub>home</sub> = (OU_line + |AH_line|) / 2,  xG<sub>away</sub> = (OU_line − |AH_line|) / 2
  - RSPF(N)主胜 = Poisson P(home_goals − away_goals > N)
  - RSPF(N)平 = Poisson P(home_goals − away_goals = N)
  - JQS [N球] = Poisson P(total = N), N∈{0,1,2,3,4,5,6,7+}

```
🔴 CRITICAL: Verify portfolio before output.
   - Count distinct anchors across all 3 tickets. If <2 anchors → redesign.
   - P(total loss) = P(anchor1 fails) × P(all other anchors fail | anchor1 fails) → MUST ≤ 30%.
   - If P(total loss) > 30%, add a hedge ticket independent of the most-used anchor.
   - Conservative P_hit <0.10 → skip day.
   - Aggressive P_hit <0.02 → cancel, merge into balanced.
   - Only 2 matches → conservative+balanced only.
   - 3 straight full-miss days → pause, review logic.
   - P_hit must be computed from Pinnacle de-vigged probs × Poisson distrib, NOT from JCL implied probs.
```
→ Full mixed parlay methodology + barbell formulas: `references/knowledge-base.md` §KB-6, §KB-7.

### Blowout Days
```
All-draw: ≥75% draws → full skip
Ultra-upset: ≥2 matches <1.30 failed → full skip
Debut/long-absence cluster: ≥2 teams trigger Rule #24 → skip or max 1 match
```

### Backtest: ¥600→¥1,246 (+107.8%). 6/6 tickets. 11/28 matches (39%) correctly skipped.
→ Full mixed parlay methodology + barbell formulas: `references/knowledge-base.md` §KB-6, §KB-7.

---

## 🏗️ PORTFOLIO CONSTRUCTION RULES (v2.9)

> **Structured from iterative portfolio optimization. These are universal — no match-specific names.**

### Rule 1: Single-Point Failure Audit (MANDATORY before output)
```
① List all matches that appear as anchors in ANY ticket.
② If any one match appears in ALL tickets → 🚨 SINGLE-POINT FAILURE.
   P(全灭) ≥ P(该锚点未命中). A 64.8% favorite still fails 35.2% of the time.
③ Fix: add at least one ticket whose anchor match appears NOWHERE else.
④ Re-audit after fix: count distinct anchor matches. Must have ≥2.
   If 2 anchors have combined fail prob < 15%, add a 3rd.
```

### Rule 2: P(全灭) Must Be Computed Correctly
```
🔴 NEVER approximate as "P(anchor fails) × P(other fails)". This misses
   the "anchor passes but secondary legs fail" case, which is often large.
🔴 CORRECT: enumerate ALL outcome combinations of the top-N matches used as legs.
   With 3 binary-outcome matches → 8 combos. Sum P of combos where no ticket hits.
   Example: anchor-fail case = 19.8%, anchor-pass + legs-fail case = 9.5%.
   True P(全灭) = 29.3%, NOT 19.8%.
```

### Rule 3: Pairwise Coverage
```
When 3+ high-probability SPF picks exist (individual P > 55%), create all 3
pairwise 2-folds as the core network. Higher-P combos get heavier weight.
This guarantees: any 2 of the 3 favorites winning → ≥1 ticket hits.
Without this: the "anchor-fails but other-2-win" combo (~12%) has zero coverage.
```

### Rule 4: Pyramid Allocation
```
🔴 The highest-P_hit ticket MUST be heavy enough to cover the total budget alone:
     Weight_best × Odds_best ≥ Total_Budget
   This makes P(不亏) = P(best ticket hits) — typically 35-45%.
   Remaining budget cascades to lower-P tickets as supplementary upside.

🔴 NEVER weight tickets equally. Equal weights force multi-ticket coordination
   for budget recovery, dropping P(不亏) by 15-20pp vs pyramid allocation.
```

### Rule 5: JQS Precision
```
🔴 JQS = total goals exact number: 0/1/2/3/4/5/6/7+. NO ranges like "2-3球".
   Select the single most probable value from Poisson(total_goals; λ).
```

### Rule 6: Output Language
```
🔴 Parlay section: 100% Chinese. Teams by full Chinese name. Play types:
   胜平负 / 让球胜平负(±N) / 总进球数. No English abbreviations.
   Technical/analysis sections may retain standard abbreviations (AH, xG, SPF).
```

### Rule 7: Profit Range Output
```
Every mixed parlay output MUST include:
  □ Scenario table: ticket hits under each outcome combination
  □ Profit table: best / typical / worst case, each with probability
  □ P(全灭) computed by Rule 2 enumeration
  □ P(不亏 ≥ Budget) — primary quality metric
  □ EV = Σ(P_i × Return_i) − Budget (structural negative EV is expected)
```

### Rule 7: Profit Range Output
```
Every mixed parlay output MUST include:
  □ Scenario table: which tickets hit under which combination of outcomes
  □ Profit range: best case / typical / worst case, each with probability
  □ P(全灭) with correct computation (Rule 2)
  □ P(不亏 ≥ Budget) = P(anchor ticket hits AND covers budget)
  □ Weighted EV = Σ(P_i × Return_i) − Budget
```

---

## KNOWLEDGE BASE INDEX

All detailed content moved to `references/knowledge-base.md`. Read on demand:

| $KB | Section | When to Read |
|:---:|---------|-------------|
| KB-1 | Math formulas + Euro→Asian conversion | Step 3 |
| KB-2 | 15 Euro-Asian trap patterns (with triggers) | Step 4 |
| KB-3 | 28 universal trap rules | Step 8 |
| KB-4 | 6D scoring model (full criteria + thresholds) | Step 7 |
| KB-5 | Fundamental weights + compression grades + Back-to-Wall | Step 2, Step 5 |
| KB-6 | Weighted probability synthesis (correction factors + normalization) | Step 10 |
| KB-7 | Score prediction refinements (14.0–14.11) | Step 10 |
| KB-8 | Supplementary methodology (Kelly, AH patterns, OU, league traits) | Supplementary analysis |
| KB-9 | Post-mortem summary (28-match cycle, root causes, key lessons) | Retrospective review |

**Reading strategy**: Start with KB-2 (traps) + KB-4 (6D) — these are used every match. Then KB-6 + KB-7 for Step 10. KB-8 + KB-9 are supplementary.

---

## QUICK START

### Setup
1. `WebSearch "oddspapi register"` → register → copy API key.
2. Provide key: `4361418d-c980-4ca1-a460-4b312c9d65cb` (stored in user memory).
3. One-time: `/v4/fixtures?tournamentId=16` (1 quota) → cache for season.

### Daily Run
```
1. Cache check: .cache/oddspapi/{tournamentId}.json
2. 3× historical-odds per match (morning/afternoon/T-1h) → 0 quota
3. T-1h: /v4/odds-by-tournaments (1 quota, first pull only)
4. Execute 12+1 steps per match → generate HTML report + mixed parlay portfolio
```

### Common Tournament IDs
| ID | Tournament | ID | Tournament |
|:--:|------------|:--:|------------|
| 16 | 2026 World Cup | 22 | Euro 2028 |
| 4 | Premier League | 8 | Champions League |

## BOUNDARIES
- Educational only. No betting advice. Overround creates negative long-term expectation.
- Scores systematic bias: ±1 goal in extreme mismatches (14.0b-14.0c partially addressed).
- Comply with local laws. Live matches only (status=1).
- W/L direction first, score second. Confidence <50% → force warning.
- Quota: never bypass confirmation. If >250/month → switch to WebSearch fallback.
