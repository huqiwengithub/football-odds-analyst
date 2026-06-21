# Football Odds & Asian Handicap Analyst v3.0

Two-skill pipeline for WorkBuddy: 500.com deep data scraper + MBI multi-bookmaker intelligence analysis.

## Architecture

```
football-odds-analyst (v3.0)
├── Pipeline (Step 0): Auto-check data → invoke scraper if needed
├── MBI Framework: 30-bookmaker weighted consensus
│   ├── SCS (Sharp Consensus Score) — tier-weighted voting
│   ├── DRI (Dispersion Risk Index) — normalized across 30 books
│   ├── Lead-Lag Chain — who moved first?
│   ├── Water Flow — 16 AH bookmaker direction
│   ├── Exchange Divergence — Betfair real money
│   └── Kelly Consensus — 30-book collective value
├── 12+1 Step Analysis (KB-0 through KB-10)
├── 6D Scoring + 19 Traps (15 original + 4 MBI)
└── Mixed Parlay Optimization (Rules 1-7)

500com-football-scraper (v2.0)
├── Deep mode (default): 6 pages per match
│   ├── ouzhi: 30 bookmaker SPF open→current + dispersion
│   ├── yazhi: 16 bookmaker AH open→current + timestamps
│   ├── rangqiu: RQSPF with official odds
│   ├── daxiao: OU open→current + direction
│   ├── shuju: H2H, form, lineups, FIFA rank
│   └── touzhu: Betfair volume, P&L, hot/cold index
├── Quick mode (--quick): basic SPF/AH/JQS/BF/BQC
└── Output: standardized JSON → .cache/500com/{date}_deep.json
```

## Bookmaker Tiers

| Tier | Weight | Members |
|:---|:---:|:---|
| Sharp | 55% | Pinnacle, bet365, IBC(SBO) |
| Asian | 25% | 澳门, 皇冠, 利记, 易胜博, 12bet |
| Retail | 20% | 威廉希尔, 立博, Interwetten, 必发 |

## Key Metrics

- **W/L direction accuracy**: 79.2% (28 matches)
- **Mixed parlay ROI**: +107.8% (6/6 tickets)
- **Skip rate**: 39% (11/28 correctly skipped)
- **Data**: 30 bookmakers, zero API quota consumption

## Files

| File | Purpose |
|:---|:---|
| `skills/football-odds-analyst/` | Analysis engine v3.0 |
| `skills/500com-football-scraper/` | Data pipeline v2.0 |
| `skills/football-odds-analyst/references/knowledge-base.md` | Full KB (KB-0 through KB-10) |
| `世界杯_2026-06-22_分析报告.html` | Sample analysis report |
| `世界杯_2026-06-22_赔率数据.json` | Sample raw data output |

## Changelog

### v3.0 (2026-06-21)
- MBI multi-bookmaker intelligence framework (KB-10)
- Auto-dependency pipeline: analyst auto-invokes scraper
- 30-bookmaker consensus replacing Pinnacle-only reference
- 4 new MBI trap rules (Trap #16-#19)
- Bookmaker tier classification (Sharp/Asian/Retail)

### v2.9 (2026-06-19)
- Quantitative trap detection with numerical triggers
- 6D scoring fully quantified
- Market liquidity indicators
- Enhanced HTML reports with Chart.js
