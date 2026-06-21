---
name: football-odds-analyst
description: "Football odds analyst v3.0 — MBI multi-bookmaker intelligence. Auto-pipeline with 500com-football-scraper. 500.com 30-bookmaker native data. Trigger: analyze match, odds analysis, handicap analysis, 竞彩. W/L 79.2% (28 matches). Mixed parlay +107.8% ROI."
allowed-tools: Read, Write, Bash, WebSearch, WebFetch
agent_created: true
version: "3.0.3-final"
released: 2026-06-21
references: references/knowledge-base.md
dependencies:
  - name: 500com-football-scraper
    required: true
    install_from: marketplace
    description: "500.com deep data scraper — provides per-match 6-page deep analysis JSON"
---

# Football Odds Analyst v3.0 — MBI + Pipeline Engine

> **HOW TO USE**: Read KB-2 + KB-4 first for every match. This file = execution flow. references/knowledge-base.md = all rules.
>
> **MBI (Multi-Bookmaker Intelligence)**: Pinnacle (sharp anchor ×0.40) + bet365/IBC (retail ×0.25) + 澳门/皇冠 (Asian ×0.20) + 30-bookmaker dispersion → weighted consensus. **Not just Pinnacle.**

---

## 🔌 DATA PIPELINE (ALWAYS RUN FIRST)

```
Step 0: Check if {date}_deep.json exists in workspace
  YES → Load and skip to Step 1
  NO  → Check if 500com-football-scraper skill exists
         YES → Invoke 500com-football-scraper with --date {date}
         NO  → Install from marketplace, then invoke
              → Wait for scraper to output JSON
              → Load JSON
```

**Data file spec**: The scraper outputs standardized JSON to the workspace. Key fields: `ouzhi.pinnacle`, `ouzhi.all_bookmakers`, `ouzhi.dispersion`, `yazhi`, `shuju`, `touzhu`, `basic`.

**Note for AI execution**: You are the analyst. When scraper is invoked, it will run in a separate conversation context. It outputs a JSON file to the workspace. Wait for it to complete, then read the JSON and proceed with analysis.

---

## 12+1 STEP CHECKLIST (v3.0 MBI-aware)

| # | Step | Action | Reference |
|:--:|------|--------|:---:|
| 0 | 🔌 Pipeline | Check data → invoke scraper if needed | Pipeline above |
| 1 | Data Source | Load JSON. Team name check (KB-0). Confirm all 6 deep pages per match loaded. | $KB-0 |
| 1.5 | 🔴 Anti-Narrative | 3 Q: (a) "known news" driving odds? −5%. (b) WC debut/long-absence? +10% mot, draw floor 28%. (c) de-vig draw >27%? full 3-way. | — |
| 2 | Fundamentals | Injuries/form/H2H from shuju. Weights v2.0 (KB-5). | $KB-5 |
| **3a** | **MBI Consensus** | **Sharp Consensus Score (SCS) with 30-bookmaker weighted voting. Dispersion Risk Index (DRI). Lead-Lag chain detection.** | **$KB-10** |
| 3b | 1X2 Math | Pinnacle: open→now. De-vig. Also compute tier-average de-vig. Overround check. | $KB-1 |
| 4 | Euro-Asian | Theoretical AH vs actual. Run 15+4 MBI traps. HIT → ±10%. ≥2 hits → 🔴 HIGH. | $KB-2, $KB-10 |
| 5 | Opening | Opening vs fair value. Deep/shallow/neutral. Tier comparison. | $KB-5 |
| 6 | Late Movement | Last 6h→2h→30min. Water trends across 16 AH bookmakers. | $KB-7 |
| 7 | 6D Scoring | Score 0–6. Dim 2 now uses all 16 AH bookmakers. D6 includes dispersion check. | $KB-4 |
| 8 | Trap Checklist | KB-2 + KB-3 + 4 new MBI rules (KB-10). ≥2→🔴. ≥3→"systemic risk". | $KB-3, $KB-10 |
| 9 | Summary | W/L direction. Core conclusion → report TOP. Red(win)/amber(draw)/green(loss). | — |
| 9.5 | Readiness | □Pipeline □1X2 □AH □OU □CS □MBI □6D □Step 9 | — |
| 10 | Probability + Score | De-vig base → 11 corrections → NORMALIZE. MBI consensus as correction #12. xG → Poisson → top 3. | $KB-6, KB-7 |
| 11 | Disclaimer | Educational. Market-derived xG. 竞彩 ~89% 覆水率. | — |

---

## MBI FRAMEWORK QUICK REFERENCE (Step 3a)

### Bookmaker Tiers (for weighted voting)

| Tier | Weight | Members | Signal |
|:---|:---:|:---|:---|
| Sharp | 0.55 | Pinnacle, bet365, IBC(沙巴) | Highest signal |
| Asian | 0.25 | 澳门, 皇冠, 利记, 易胜博, 12bet | Regional flow |
| Retail | 0.20 | 威廉希尔, 立博, Interwetten, 必发 | Public sentiment |

### Sharp Consensus Score (SCS)

```
For each outcome (H/D/A):
  SCS = Σ(tier_weight_i × direction_i) / Σ(tier_weight_i)
  where direction_i = +1 if odds ↓, -1 if ↑, 0 if unchanged
  
SCS ≥ 0.7 → Strong consensus (+10% to Step 10 correction)
SCS 0.4–0.7 → Moderate (no adjustment)
SCS < 0.4 → Weak consensus (−5% penalty)
```

### Dispersion Risk Index (DRI)

```
DRI = normalized(ouzhi.dispersion.home × 0.5 + ouzhi.dispersion.draw × 0.3 + ouzhi.dispersion.away × 0.2)
Threshold: DRI > 40 → confidence × 0.85
           DRI > 70 → confidence × 0.70 + warning "extreme dispersion"
           DRI < 15 → confidence × 1.05 (tight consensus)
```

### Lead-Lag Chain

```
Pinnacle moves first + bet365 follows <2h + 澳门 follows → STRONG (+10%)
Pinnacle moves + others DON'T follow within 4h → WEAK (ignore movement)
Retail moves first + Pinnacle static → NOISE (ignore)
All three tiers move simultaneously → GENUINE EVENT (+5%)
```

### 4 New MBI Trap Rules (§KB-10)

| # | Rule | Trigger | Signal |
|:--:|------|---------|--------|
| 16 | Tier Divergence | Sharp vs Asian disagree ≥0.25 ball on AH | 🔴 system risk |
| 17 | Exchange-Volume Spike | 必发 volume >2× avg + odds static | Resistance level |
| 18 | Kelly Consensus Gap | Avg Kelly on favorite >1.05 but <0.90 on others | Value signal |
| 19 | Water Flow Anomaly | ≥70% of 16 AH bookmakers move water same direction in <1h | Coordinated move |

---

## OUTPUT FORMAT

`Read assets/report-template.html` before generating. Core rules:
- W/L PRIMARY, score SECONDARY. Step 9 conclusion at TOP. Red=win, amber=draw, green=loss.
- Chinese names + emoji flags. Prob bars + score cards inline.
- **NEW v3.0**: MBI panel per match showing SCS, DRI, Lead-Lag, Tier Divergence.
- `{{GENERATION_TIME}}` = Beijing. `{{NAME_ERROR_ACTIVE}}` = `active` if English fallback.
- Liquidity grid + external factor table in Step 2.

---

## PORTFOLIO CONSTRUCTION (v3.0.2 — Tighter Controls + Correlation)

### Rule 0: Bankroll Management (v3.0.2)

```
Fractional Kelly (0.25×):
  f* = (p × odds − 1) / (odds − 1)    // Full Kelly
  stake = 0.25 × f* × bankroll         // Conservative fractional

Max Drawdown Limits (TIGHTENED v3.0.2):
  Single day: max 5% bankroll loss → stop
  Single week: max 15% bankroll loss → stop for rest of week
  Single match: max 5% bankroll exposure

Slippage & Return Rate Discount:
  actual_odds = quoted_odds × (1 − slippage) × return_rate
  slippage_default = 0.00 (竞彩无滑点); 0.03 (外围)
  return_rate_default = 0.89 (竞彩); 0.97 (外围)
  EV must be computed with actual_odds, NOT quoted_odds
```

### Rule 2: Match Correlation (UPDATED v3.0.2)

```
Correlation coefficients (not multipliers):
  Same league + same day: corr = 0.25
  Derby / 派系战: corr = 0.55
  Same group (World Cup group stage): corr = 0.30
  Different continent/league: corr = 0.00 (independent)

Applied via:
  P_both_fail = P(A_fail) × P(B_fail) + corr × min(P(A_fail), P(B_fail))
  This inflates joint failure prob without going above individual probs.
```

### Selection + Allocation (v3.0.2)

```
单注 Kelly = 0.25 × f* × bankroll, capped at 5% max per match
过关注额 = 单注 Kelly 的 0.6× (multi-leg variance penalty)
对冲注额 = 单注 Kelly 的 0.3× (hedge purpose only)

总日预算 ≤ 5% bankroll (硬上限)

总日预算 ≤ 15% bankroll (硬上限)
```

---

## MIXED PARLAY (v3.0.3 — + Odds Structure Defense)

### Play Types (same)
```
SPF(8关)⭐main | RSPF(8关)⭐when SPF too low | JQS(6关)⭐exact only | BQC(4关) | BF(4关)❌
```

### Selection (updated v3.0.3)

```
Basic filters:
  6D≥3 only. Draw>27%→skip. Probs within 15pp→skip. <2 matches→skip.

Odds Structure Defense (NEW v3.0.3):
  Parlay geo-mean ≥ 1.50 (2串1 total ≥ 2.50, 3串1 ≥ 3.38)
  FORBIDDEN: 3+ legs all odds <1.35 (竞彩 0.89 return rate → EV deeply negative)
  Ultra-low odds (<1.35): single bet only OR M串N fault-tolerant base
  Rationale: 1.20×1.25×1.30 = 1.95 total. After 0.89 return rate → effective 1.74.
            One miss = total loss with near-zero recovery potential.

分配 (Fractional Kelly):
  stake = 0.25 × (p×odds−1)/(odds−1) × bankroll | cap 5% per match | cap 5% daily
  过关注额 = 0.6× | 对冲 = 0.3×

校验:
  distinct anchors ≥2 | P(total loss) ≤30% | all EV ×0.89 (竞彩 return rate)
```

---

## KNOWLEDGE BASE INDEX (v3.0.3 Final — 13 modules)

| $KB | Content | When |
|:---:|---------|------|
| KB-0 | Pre-flight: team name map + verification protocol | Step 1 |
| KB-1 | Math: Shin de-vig, logit-space corrections, Euro→Asian | Step 3b |
| KB-2 | 15 Euro-Asian traps | Step 4 |
| KB-3 | 28 universal trap rules | Step 8 |
| KB-4 | 6D continuous scoring v3.0 | Step 7 |
| KB-5 | Fundamental weights + compression + Back-to-Wall | Steps 2,5 |
| KB-6 | Probability synthesis (12 corrections in logit space) | Step 10 |
| KB-7 | Score refinements (14.0–14.11) | Step 10 |
| KB-8 | Methodology: Kelly, AH patterns, OU, league traits | Supplementary |
| KB-9 | Post-mortem: 28-match cycle | Retrospective |
| KB-10 | MBI framework: SCS, DRI, Lead-Lag, WaterFlow, Exchange, Kelly, traps #16-#21 | Step 3a, 4, 8 |
| **KB-11** | **Data calibration: dedup, water normalization, true opening, event tiering** | **Pre-Step 1** |
| **KB-12** | **Advanced signals: retracement, AH break, order book, open-gap, draw diversion** | **Step 4, 6** |
| **KB-13** | **Risk & iron rules: slippage, confidence tiering, circuit breakers, risk day, blacklist** | **Portfolio + Always** |

---
## BOUNDARIES & IRON RULES
- Educational only. No betting advice. Data source: 500.com native (30 bookmakers, zero quota).
- xG: market-derived, no Opta. W/L direction first.
- **Iron Rule**: 临场 30min 禁令。禁止倍投。禁止无意义对冲。
- **Circuit Breaker**: 单日亏 3%→停。单周亏 8%→影子测试。单模块连错 7 场→禁用。
- **Confidence Tier**: A(0.25×Kelly,可做胆) / B(0.15×,仅搭配) / C(0.08×,仅单关)。
- **Shadow Testing**: A类 ≥65% + 反向 ≥70% + EV ≥−3% → 方可实盘。`
