---
name: football-odds-analyst
description: "Professional football odds/Asian handicap analyst v2.9. Trigger keywords: analyze match, odds analysis, handicap analysis, 1X2 analysis, trap detection, mixed parlay, 竞彩. Cache-first: odds-by-tournaments (1 quota = entire tournament). W/L 79.2% (28 matches). Mixed parlay +107.8% ROI (6/6 tickets)."
allowed-tools: Read, Write, Bash, WebSearch, WebFetch
agent_created: true
version: 2.9
released: 2026-06-21
references: references/knowledge-base.md
---

# Football Odds Analyst v2.9 — Execution Engine

> **HOW TO USE**: This file is the API-call gatekeeper + betting execution rules. All analysis details live in `references/knowledge-base.md` (§KB-N). Read KB-2 + KB-4 first for every match. This file + KB = the complete skill.
>
> **Golden triangle**: Pinnacle (sharp benchmark) + SBOBet (AH king) + bet365 (retail heat). Cache-first. Historical-odds always free.

---

## ⚠️ QUOTA SAFETY (READ FIRST — ALWAYS)

```
① Only /v4/historical-odds and /v4/account are free. All others = 1 quota/call.
② 🔴 CONFIRM BEFORE SPENDING: GET /v4/account → show user:
   "Need: [endpoint] × [N] = [N] quota. Current: X/250. Continue? (yes/no)"
   No "yes"/"确认" → NO REQUEST. Every single time. Never assume.
③ /v4/historical-odds fails → NEVER silently switch to /v4/odds.
④ All calls SERIAL. Validate previous response before next call.
⑤ 🕐 Timezone: user's local. "tomorrow"/"today" → date +%Z.
⑥ CACHE-FIRST: .cache/oddspapi/{id}.json exists? → use it. Not? → ask → pull → cache.
⑦ ALWAYS prefer /v4/odds-by-tournaments (1 quota all matches) over /v4/odds (1/match).
⑧ SBOBET: first call no AH data → fallback Singbet or bet365 dual-purpose. Mark accordingly.
⑨ 🔴 DOMAIN: api.oddspapi.io (NOT .com). If behind proxy → curl --noproxy "*".
⑩ 🔴 RATE LIMIT: /v4/historical-odds needs ≥3s gap. Sequential only. Never parallel.
⑪ Historical-odds files 4-10MB → write to /tmp/, never load in memory. Market 101=1X2.
⑫ FIRST-TIME: never start with real-time. Use cached fixtures + free historical first.
```

### API Endpoints
```
FREE (0 quota):
  GET https://api.oddspapi.io/v4/account?apiKey=KEY
  GET https://api.oddspapi.io/v4/historical-odds?fixtureId=X&bookmakers=pinnacle,sbobet,bet365&apiKey=KEY

BILLED (1 quota each):
  GET https://api.oddspapi.io/v4/odds-by-tournaments?tournamentIds=X&bookmaker=Y&apiKey=KEY
  GET https://api.oddspapi.io/v4/fixtures?tournamentId=X&apiKey=KEY

Params iron law: bookmaker (singular slug) | tournamentIds (plural) | fixtureId (singular)
NO sportId. NO marketTypeIds. Save in ONE call (-o file.json). Never inspect-only then re-fetch.

Cache: Phase 0 (once): fixtures 1 quota → .cache/oddspapi/fixtures_X.json.
       Phase 1-3 (daily, 0 quota): historical-odds morning/afternoon/T-1h.
       T-1h first pull: odds-by-tournaments 1 quota → cache 1h. Monthly: 2/250.

Tournament IDs: 16=2026WC | 22=Euro 2028 | 4=EPL | 8=UCL
API key stored: 4361418d-c980-4ca1-a460-4b312c9d65cb
```

---

## 12+1 STEP CHECKLIST

> Priority: Anti-Narrative > Squad > WC History > Defensive Tier > Winless Inertia > Home > Final Surge > xG > Pendulum > 1X2 Math > Euro-Asian > Traps > Compression > Movement > Probability

| # | Step | Action | Reference |
|:--:|------|--------|:---:|
| 1 | Data Source | Document endpoints. Team name check (KB-0). Cache check. | $KB-0 |
| 1.5 | 🔴 Anti-Narrative | 3 Q: (a) "known news" driving odds? → −5%. (b) WC debut/long-absence? → +10% mot, draw floor 28%. (c) de-vig draw >27%? → full 3-way. | — |
| 2 | Fundamentals | Injuries/form/H2H. Weights v2.0 (KB-5). Liquidity (KB-7 §14.9). External (KB-7 §14.10). | $KB-5, KB-7 |
| 3 | 1X2 Math | Pinnacle: open→now. De-vig MUST. overround = Σ(1/odds). true = (1/o)/overround. | $KB-1 |
| 4 | Euro-Asian | Theoretical AH vs actual for all 3. Run 15 triggers. HIT → ±10%. ≥2 hits → 🔴 HIGH. 4 opening laws. | $KB-2 |
| 5 | Opening | Opening vs fair value. Deep/shallow/neutral. | $KB-5 |
| 6 | Late Movement | Last 6h→2h→30min. Water trends. Multi-period fusion (KB-7 §14.7). | $KB-7 |
| 7 | 6D Scoring | Score 0–6. Dim 1-6 inline thresholds. ⚠️ Raw=6→eff=5. ≥4→+3%, ≤2→degrade. | $KB-4 |
| 8 | Trap Checklist | All triggered (KB-2+KB-3). 🔴≥2/🟡1/🟢0. ≥3→"systemic risk". | $KB-3 |
| 9 | Summary | W/L direction. Core conclusion → report TOP. Red(win)/amber(draw)/green(loss). | — |
| 9.5 | Readiness | □1X2 □AH □OU □CS □1.5 □2 □7 □Step 9 written? | — |
| 10 | Probability + Score | De-vig base → 11 corrections (KB-6) → 🔴 NORMALIZE. xG → 14.0a-d → 14.4 (WebSearch) → Poisson → top 3. | $KB-6, KB-7 |
| 11 | Disclaimer | Educational only. xG: market-derived, no Opta. 竞彩: ~89% 覆水率. | — |

---

## PRE-OUTPUT VALIDATION (MANDATORY)

```
□ Quota confirmed? □ Beijing time? □ Chinese names? □ Step 1.5 done?
□ 6D v2.0+inflation? □ NORMALIZATION ran? □ 14.0-14.11 applied?
□ W/L first, score second? □ ≥3 traps → warning? □ Conf <50% → warning?
□ CSS matches template? □ Charts init'd? □ Disclaimer?
```

---

## OUTPUT FORMAT

`Read assets/report-template.html` before generating. Core rules:
- W/L PRIMARY, score SECONDARY. Step 9 conclusion at TOP. Red=win, amber=draw, green=loss.
- Chinese names + emoji flags. Only template CSS classes. Prob bars + score cards per template.
- `initOddsChart()` + `initAHCompareChart()` per match. `{{GENERATION_TIME}}` = Beijing. `{{NAME_ERROR_ACTIVE}}` = `active` if English fallback.
- Liquidity grid + external factor table in Step 2.

---

## 🏗️ PORTFOLIO CONSTRUCTION RULES (v2.9)

> **Iterative optimization. Universal — no match-specific names.**

### Rule 1: Single-Point Failure Audit (MANDATORY before output)
```
① List all matches appearing as anchors in ANY ticket.
② If any match appears in ALL tickets → 🚨 SINGLE-POINT FAILURE.
   P(total loss) ≥ P(anchor miss). Even 64.8% favorite fails 35.2% of time.
③ Fix: add ≥1 ticket whose anchor appears NOWHERE else.
④ Re-audit: count distinct anchors. Must ≥2. If 2 anchors combined fail prob <15%, add 3rd.
```

### Rule 2: P(全灭) Must Be Computed Correctly
```
🔴 NEVER approximate as "P(anchor fails) × P(other fails)". Misses "anchor passes, legs fail" case.
🔴 CORRECT: enumerate ALL outcome combos of top-N matches. Sum P of combos where no ticket hits.
   3 binary matches → 8 combos. Example: anchor-fail=19.8%, anchor-pass+legs-fail=9.5%.
   True P(全灭)=29.3%, NOT 19.8%.
```

### Rule 3: Pairwise Coverage
```
When 3+ high-prob SPF picks exist (individual P>55%), create all 3 pairwise 2-folds as core.
Higher-P combos get heavier weight. Guarantees: any 2 of 3 win → ≥1 ticket hits.
Without: "anchor-fails but other-2-win" (~12%) has zero coverage.
```

### Rule 4: Pyramid Allocation
```
🔴 Highest-P_hit ticket MUST cover total budget alone:
     Weight_best × Odds_best ≥ Total_Budget
   → P(不亏) = P(best ticket hits), typically 35-45%.
   Remaining budget cascades to lower-P tickets as upside.
🔴 NEVER equal-weight. Drops P(不亏) by 15-20pp vs pyramid.
```

### Rule 5: JQS Precision
```
🔴 JQS = exact number: 0/1/2/3/4/5/6/7+. NO ranges. Pick max from Poisson(total_goals; λ).
```

### Rule 6: Output Language
```
🔴 Parlay section: 100% Chinese. Full Chinese team names. Play types: 胜平负 / 让球胜平负(±N) / 总进球数.
   No GER/JPN/NED abbreviations. Tech sections may retain AH, xG, SPF.
```

### Rule 7: Profit Range Output
```
Every mixed parlay output MUST include:
  □ Scenario table: tickets hitting under each outcome combination
  □ Profit table: best/typical/worst case, each with probability
  □ P(全灭) via Rule 2 enumeration
  □ P(不亏 ≥ Budget) — primary quality metric
  □ EV = Σ(P_i × Return_i) − Budget
```

---

## MIXED PARLAY (竞彩) — QUICK REFERENCE

### Data & Plays
```
Betting odds: https://trade.500.com/jczq/?playid=312&g=2 (Row 1 = settlement SPF. 百家平均=ref only)
Rules: https://www.lottery.gov.cn/bzzx/yxgz/20191119/1040217.html
覆水率: JCL ~89% vs international ~97%. Odds significantly lower.

Play types: SPF(8关)⭐main | RSPF(8关)⭐when SPF too low | JQS(6关)⭐exact number only | BQC(4关)⭐HT≥80% | BF(4关)❌never
Rules: football only. Same match=1 play. Cap=min(plays). Prize=¥2×∏(odds). Amounts MUST be ¥2 multiples.
```

### Selection + Allocation
```
Select: 6D≥3 only. Draw>27%→skip. Probs within 15pp→skip. <2 matches→full skip. KO→more selective (14.0d).
Barbell: 3 tickets, DIFFERENT anchors. Alloc_i = P_hit,i/ΣP_hit × Budget → round to ¥2.
         保守 Alloc × Odds ≥ Budget (cover). P_hit from Pinnacle de-vig × Poisson, NOT JCL implied.
Verify: distinct anchors ≥2. P(total loss) ≤30%. Else add hedge. Cons P_hit<0.10→skip. Agg P_hit<0.02→merge.
Blowout days: ≥75% draws OR ≥2 matches <1.30 fail OR ≥2 debut/long-absence teams → skip.
Backtest: ¥600→¥1,246 (+107.8%). 6/6 tickets. 11/28 correctly skipped (39%).
```

---

## KNOWLEDGE BASE INDEX

| $KB | Content | When |
|:---:|---------|------|
| KB-0 | Pre-flight: team name map + verification protocol | Step 1 |
| KB-1 | Math formulas + Euro→Asian conversion table | Step 3 |
| KB-2 | 15 Euro-Asian traps (full triggers) | Step 4 |
| KB-3 | 28 universal trap rules | Step 8 |
| KB-4 | 6D scoring (full criteria + thresholds + inflation) | Step 7 |
| KB-5 | Fundamental weights + compression grades + Back-to-Wall | Steps 2,5 |
| KB-6 | Probability synthesis (11 correction factors + normalization) | Step 10 |
| KB-7 | Score refinements (14.0–14.11) | Step 10 |
| KB-8 | Methodology: Kelly, AH patterns, OU, league traits, bankroll | Supplementary |
| KB-9 | Post-mortem: 28-match cycle, root causes, key lessons | Retrospective |

**Strategy**: Read KB-2 + KB-4 every match. Then KB-6 + KB-7 for Step 10. KB-8 + KB-9 supplementary.

> ⚠️ **ALL betting analysis details are in the knowledge base.** This file handles only: quota gatekeeping, API call logic, step execution order, portfolio construction rules, and mixed parlay selection criteria. For trap definitions, scoring formulas, probability math, and methodology — Read `references/knowledge-base.md`.

## BOUNDARIES
- Educational only. No betting advice. Overround → negative expectation.
- xG: market-derived base + team form (KB-7 §14.4), no Opta/StatsBomb. Score bias: ±1 goal extreme mismatches.
- Comply with local laws. Live matches only (status=1). Confidence <50% → force warning. Quota >250 → WebSearch.
- W/L direction first, score second. Never skip normalization. Never skip quota confirmation.
