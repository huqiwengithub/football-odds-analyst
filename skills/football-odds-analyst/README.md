# Football Odds & Asian Handicap Analyst

A professional odds analysis Skill for WorkBuddy. Analyzes football matches using OddsPapi API with intelligent quota management.

## Features

- **Single API dependency**: Only needs OddsPapi (oddspapi.io)
- **Quota-optimized**: Auto-selects data source based on time-to-kickoff
- **Free historical data**: `/v4/historical-odds` permanently free, unlimited
- **12-step analysis**: Standardized process from fundamentals to probability synthesis
- **6-dimension scoring**: Objective match quality assessment with quantified criteria
- **Weighted probability model**: Mathematics-driven directional projection with mandatory normalization
- **Market liquidity analysis**: Trading volume, spread tightness, water fluctuation indicators
- **External factor quantification**: Weather, travel, rest days scored with explicit rules
- **Dynamic team name verification**: WebSearch fallback for unmapped team names
- **Quantitative trap detection**: All 7 traps + 14 universal rules with numerical triggers
- **Enhanced HTML reports**: Chart.js visualization, dynamic timestamps, optimized hierarchy

## Changelog (2026-06-19 Expert Review)

Based on comprehensive expert evaluation, the following improvements were made:

1. **Math formulas**: Renamed "implied total probability" → "overround"; added mandatory normalization step
2. **Market liquidity**: New Section 4(14.9) with 5 quantitative indicators (water fluctuation, spread, change frequency, SBOBet gap, limit direction)
3. **External factors**: New Section 4(14.10) with explicit 4-factor scoring (weather, travel, rest, altitude)
4. **Team names**: Dynamic verification protocol with WebSearch fallback + ⚠️ red error banners
5. **xG model**: Enhanced with team form correction path + model limitations disclosure
6. **6D scoring**: Fully quantified — each dimension has explicit pass/fail thresholds with numerical metrics
7. **Trap detection**: All 7 traps now have quantitative triggers; added Trap #13 (illegal sites) and #14 (referee influence)
8. **HTML template**: Added Chart.js charts, dynamic timestamps, core conclusions priority layout, name error banners
9. **Data source**: Platform name verification, SBOBet fallback plan, API parameter verification checklist

## Quota Efficiency

| Phase | Action | Cost |
|-------|--------|:----:|
| Phase 0 (one-time) | Cache all fixtureIds + outcome IDs | 4 quota |
| Phase 1-3 (daily) | /historical-odds only (free) | 0 |
| **Lifetime per tournament** | | **4 / 250** |

## How It Works

1. User registers at https://oddspapi.io for free API key (250 requests/month)
2. Provides key to WorkBuddy
3. Sends match analysis request
4. Skill auto-detects time-to-kickoff:
   - >1h before → `/historical-odds` only (free)
   - ≤1h before → `/odds` (1 quota) + `/historical-odds` (free)
5. Executes full 12-step analysis with probability projection + score prediction

## Files

- `SKILL.md` - The WorkBuddy skill definition (English)
- `要求.md` - Original requirements (Chinese)
- `assets/report-template.html` - Enhanced HTML report template
- `football-odds-analyst.zip` - Distributable skill package
