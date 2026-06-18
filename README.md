# Football Odds & Asian Handicap Analyst

A professional odds analysis Skill for WorkBuddy. Analyzes football matches using OddsPapi API with intelligent quota management.

## Features

- **Single API dependency**: Only needs OddsPapi (oddspapi.io)
- **Quota-optimized**: Auto-selects data source based on time-to-kickoff
- **Free historical data**: `/v4/historical-odds` permanently free, unlimited
- **11-step analysis**: Standardized process from fundamentals to probability synthesis
- **6-dimension scoring**: Objective match quality assessment
- **Weighted probability model**: Mathematics-driven directional projection

## Quota Efficiency

| Phase | Action | Cost |
|-------|--------|:----:|
| Phase 0 (one-time) | Cache all fixtureIds | 1 quota |
| Phase 1 (morning × 30d) | /historical-odds × 4 | 0 |
| Phase 2 (afternoon × 30d) | /historical-odds × 4 | 0 |
| Phase 3 (T-1h × 30d × 4) | /odds × 4 + /historical-odds × 4 | 4/day |
| **Monthly total** | | **121 / 250** |

## How It Works

1. User registers at https://oddspapi.io for free API key (250 requests/month)
2. Provides key to WorkBuddy
3. Sends match analysis request
4. Skill auto-detects time-to-kickoff:
   - >1h before → `/historical-odds` only (free)
   - ≤1h before → `/odds` (1 quota) + `/historical-odds` (free)
5. Executes full 11-step analysis with probability projection

## Files

- `SKILL.md` - The WorkBuddy skill definition (English)
- `要求.md` - Original requirements (Chinese)
- `football-odds-analyst.zip` - Distributable skill package
