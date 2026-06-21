---
name: 500com-football-scraper
description: "Scrape full football odds data from 500.com. Default deep mode (6 analysis pages per match: ouzhi/yazhi/rangqiu/daxiao/shuju/touzhu). Supports --quick fast mode. Outputs standardized JSON."
agent_created: true
version: "2.0"
---

# 500.com Football Odds Scraper v2.0

> Default deep mode: fetches 6 deep analysis pages per match (European odds, Asian handicap comparison, RQSPF, OU, fundamentals, betting flow), covering 30 bookmakers including Pinnacle.
> Outputs standardized JSON consumed by `football-odds-analyst`. 12-hour cache reuse.

## Triggers

- User mentions "500.com", "scrape odds", "pull data"
- Called as dependency by `football-odds-analyst`
- Any scenario needing structured 500.com data

---

## Two Modes

### Deep Mode (default)

6 analysis pages + basic trade page + XML per match. Outputs full JSON.

```bash
python3 references/parser.py --date 2026-06-22 --json
```

### Quick Mode (`--quick`)

Only trade page + XML. Outputs basic odds. For quick preview.

```bash
python3 references/parser.py --date 2026-06-22 --quick --json
```

---

## Execution Flow (Deep Mode)

### Phase 1: Get match list + shuju IDs

```
1. WebFetch https://trade.500.com/jczq/?playid=312&g=2
   Extract: match code, team names, rankings, time, shuju ID (from /fenxi/shuju-XXXXXXX.shtml links)
2. Filter by date
3. Build match_list = [{code, datetime, home_team, away_team, home_rank, away_rank, shuju_id, handicap_rqspf}]
```

### Phase 2: Fetch 6 deep analysis pages per match

For each match, WebFetch these 6 URLs ({id} = shuju_id):

| Page | URL Template | Key Data |
|:---|:---|:---|
| **ouzhi** | `https://odds.500.com/fenxi/ouzhi-{id}.shtml` | 30 bookmakers SPF open→current, probability, Kelly index, dispersion |
| **yazhi** | `https://odds.500.com/fenxi/yazhi-{id}.shtml` | 16 bookmakers AH open→current, water level, handicap change timestamps |
| **rangqiu** | `https://odds.500.com/fenxi/rangqiu-{id}.shtml` | RQSPF open→current, including official odds |
| **daxiao** | `https://odds.500.com/fenxi/daxiao-{id}.shtml` | OU open→current, line direction |
| **shuju** | `https://odds.500.com/fenxi/shuju-{id}.shtml` | FIFA ranking, H2H, recent form, expected lineup, avg stats |
| **touzhu** | `https://odds.500.com/fenxi/touzhu-{id}.shtml` | Betfair volume, bookmaker P&L, hot/cold index, distribution |

### Phase 3: Parse key data

#### ouzhi parsing

```
Pinnacle = row 10 ("Pi****le" — Pinnacle sportsbook)
Extract: open SPF (first 3 numbers) / current SPF (last 3 numbers) / open probability / current probability / Kelly index

All 30 bookmakers row format:
  index | name | open H/D/A | current H/D/A | open prob%/%/% | current prob%/%/% | return rate | current Kelly H/D/A

Average row (last row): extract mean + max + min + dispersion
```

#### yazhi parsing

```
Pinnacle = row 10
Extract: current water / current handicap / away water | change time | open water / open handicap / away water | open time

Chinese handicap → numeric mapping:
  平手=0, 平手/半球=0.25, 半球=0.5, 半球/一球=0.75, 一球=1.0, 一球/球半=1.25,
  球半=1.5, 球半/两球=1.75, 两球=2.0, 两球/两球半=2.25, 两球半=2.5, 两球半/三球=2.75, 三球=3.0
  受X球 = -X (home team receiving handicap)

Direction: 升 = handicap deepens, 降 = handicap retreats, ↓ = water drops, ↑ = water rises
```

#### shuju parsing

```
FIFA ranking: "西班牙\[世2\]" → home_rank=2
H2H: "双方近3次交战，西班牙3胜0平0负，进9球，失2球" → {matches:3, home_wins:3, draws:0, ...}
Recent form: "近10场战绩6胜4平0负进25球失4球" → {matches:10, wins:6, draws:4, losses:0, goals_for:25, goals_against:4}
Home/Away records: same format
Expected lineup: starters + substitutes + injuries/suspensions (name lists)
```

#### touzhu parsing

```
Betfair volume: "1.13 1,176,453 -31,357" → price=1.13, volume=1176453, pl=-31357
Distribution: "86.3% 9.7% 3.9%" → home=86.3, draw=9.7, away=3.9
Betfair index: extract hot/cold index and P&L index
```

### Phase 4: Merge and output

Standardized JSON schema (see ouzhi/yazhi/rangqiu/daxiao/shuju/touzhu sub-schemas above). Output fields use Chinese team/league names where appropriate (data, not metadata).

### Phase 5: Cache

```
Cache location: .cache/500com/{date}_deep.json
Expiration: 12 hours
--no-cache: force fresh fetch, overwrite cache
```

---

## Notes

1. **Encoding**: trade.500.com returns GB2312, must convert to UTF-8. Deep analysis pages are UTF-8, no conversion needed.
2. **shuju ID extraction**: From trade page links like `<a href="/fenxi/shuju-XXXXXXX.shtml">`.
3. **Pinnacle row**: Row 10 in ouzhi page ("Pi****le"), same position in yazhi page.
4. **Not-yet-open**: RQSPF showing "未开售" → set field to null.
5. **Network**: 6 pages × N matches = many pages. Fetch 2-3 pages concurrently.

---

## Quick Mode

Only fetches trade page + XML. Outputs basic JSON (no ouzhi/yazhi/rangqiu/daxiao/shuju/touzhu deep data).

```bash
python3 references/parser.py --date 2026-06-22 --quick --json
```

Output structure same as v1.0: contains `basic` section (SPF/RQSPF/AH/OU/JQS/BF/BQC), no deep sections.

---

## CLI Reference

| Flag | Description | Default |
|:---|:---|:---|
| `--date YYYY-MM-DD` | Filter by date | All |
| `--quick` | Fast mode (basic only) | Deep mode |
| `--json` | JSON output | Text output |
| `--no-cache` | Skip cache, force refresh | Use cache |
| `--match NAME` | Filter by team name | All |
| `--cache-dir DIR` | Cache directory | .cache/500com/ |
