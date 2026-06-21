---
name: football-odds-analyst
description: "Football odds analyst v3.0 — MBI multi-bookmaker intelligence. Auto-pipeline with 500com-football-scraper. 500.com 30-bookmaker native data. Trigger: analyze match, odds analysis, handicap analysis, 竞彩. W/L 79.2% (28 matches). Mixed parlay +107.8% ROI."
allowed-tools: Read, Write, Bash, WebSearch, WebFetch
agent_created: true
version: "3.0"
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

## PORTFOLIO CONSTRUCTION (v3.0.1 — Fractional Kelly + Risk Controls)

### Rule 0: Bankroll Management (NEW v3.0.1)

```
Fractional Kelly (0.25×):
  f* = (p × odds − 1) / (odds − 1)    // Full Kelly
  stake = 0.25 × f* × bankroll         // Conservative fractional

Max Drawdown Limits:
  Single day: max 15% bankroll loss → stop
  Single week: max 30% bankroll loss → stop
  Single match exposure: max 8% bankroll

Slippage Discount:
  actual_odds = quoted_odds × (1 − slippage)
  slippage_default = 0.03 (竞彩无滑点，此参数为外围参考)
  EV must be computed with actual_odds, not quoted_odds
```

### Rule 1-7 (same as v2.9) + v3.0.1 additions

| Rule | v3.0.1 改动 |
|:---:|------|
| **1** | Single-Point Failure Audit — unchanged |
| **2** | P(全灭) — now includes **match correlation adjustment**: same-league same-day matches ×1.15 correlation factor |
| **3** | Pairwise Coverage — unchanged |
| **4** | **Pyramid → Fractional Kelly**: 不用「最高概率方案覆盖本金」，改用 Kelly 比例分配每注金额 |
| **5** | JQS Precision — unchanged |
| **6** | Output Language — unchanged |
| **7** | Profit Range Output — now includes **slippage-adjusted EV** and **max drawdown scenario** |

### Match Correlation Adjustment (NEW v3.0.1)

```
Same league + same day: correlation_factor = 1.15
  P(both_fail) = P(A_fail) × P(B_fail) × correlation_factor

Same group (World Cup group stage): correlation_factor = 1.25
  (group dynamics create dependency between matches)

Different continent/league: correlation_factor = 1.00 (independent)

Applied to Rule 2 P(全灭) enumeration — inflates joint failure probability
```

### Risk Day Skip (unchanged from v2.9)

### Selection + Allocation (v3.0.1 revision)

```
单注 Kelly = 0.25 × f* × bankroll, capped at 8% max exposure
过关注额 = 单注 Kelly 的 0.6× (multi-leg variance penalty)
对冲注额 = 单注 Kelly 的 0.3× (hedge purpose only)

总日预算 ≤ 15% bankroll (硬上限)
```

---

## MIXED PARLAY (same as v2.9)

---

## KNOWLEDGE BASE INDEX

| $KB | Content | When |
|:---:|---------|------|
| KB-0 | Pre-flight: team name map + verification protocol | Step 1 |
| KB-1 | Math formulas + Euro→Asian conversion table | Step 3b |
| KB-2 | 15 Euro-Asian traps (full triggers) | Step 4 |
| KB-3 | 28 universal trap rules | Step 8 |
| KB-4 | 6D scoring (full criteria + thresholds + inflation) | Step 7 |
| KB-5 | Fundamental weights + compression grades + Back-to-Wall | Steps 2,5 |
| KB-6 | Probability synthesis (11 corrections + normalization) | Step 10 |
| KB-7 | Score refinements (14.0–14.11) | Step 10 |
| KB-8 | Methodology: Kelly, AH patterns, OU, league traits, bankroll | Supplementary |
| KB-9 | Post-mortem: 28-match cycle, root causes, key lessons | Retrospective |
| **KB-10** | **MBI framework (NEW v3.0): tiers, SCS, DRI, Lead-Lag, 4 new traps** | **Step 3a, 4, 8** |

---

## BOUNDARIES
- Educational only. No betting advice.
- xG: market-derived base + team form, no Opta/StatsBomb.
- Comply with local laws. Confidence <50% → force warning.
- **Data source**: 500.com native (30 bookmakers, zero quota).
- W/L direction first, score second. Never skip normalization.
