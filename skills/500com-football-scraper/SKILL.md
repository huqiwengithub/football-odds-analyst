---
name: 500com-football-scraper
description: "Scrape full football odds data from 500.com. Default deep mode (6 analysis pages per match: ouzhi/yazhi/rangqiu/daxiao/shuju/touzhu). Supports --quick fast mode. Outputs standardized JSON."
agent_created: true
version: "2.1"
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

## Anti-Scraping Protection

500.com has active anti-scraping measures. **Always follow these rules to avoid being blocked or rate-limited.**

### Browser Simulation (Headers)

Every HTTP request must simulate a real browser visit. Bare minimum headers:

```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.500.com/',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-site',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}
```

Key rules:
- **Referer chain**: Start from `https://www.500.com/` → `https://trade.500.com/jczq/` → deep pages. Always set Referer to the page the user would naturally be on before clicking through.
- **User-Agent**: Must match a real browser. Update the Chrome version periodically.
- **Accept-Encoding**: Include `gzip` so 500.com doesn't suspect raw script access.
- **Cookie header**: Some requests require a session cookie from the homepage. Visit the homepage first and pass the Set-Cookie response on subsequent requests.

### Request Timing

```
# Between individual page fetches (same match): 0.5-2.0s random delay
import random, time
delay = random.uniform(0.5, 2.0)
time.sleep(delay)

# Between different matches: 2.0-5.0s random delay
delay = random.uniform(2.0, 5.0)
time.sleep(delay)

# Maximum concurrent: 2-3 pages per match, 1 match at a time
# DO NOT use high-concurrency (>5) ThreadPoolExecutor for 500.com fetches
```

Never:
- Fetch more than 6 pages per minute from the same IP
- Use more than 3 concurrent connections
- Skip delays between requests
- Fetch during 500.com's peak traffic hours (weekend match times)

### Cookie/Referer Chain

```python
# Step 1: Visit homepage to get session cookie
import urllib.request, http.cookiejar

cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

home_req = urllib.request.Request('https://www.500.com/', headers={
    'User-Agent': '<browser UA>',
    'Accept': 'text/html,...',
})
opener.open(home_req)  # Now cookie_jar has the session cookie

# Step 2: Now scrape deep pages with the same opener
fenxi_req = urllib.request.Request('https://odds.500.com/fenxi/ouzhi-{id}.shtml', headers={
    **headers,
    'Referer': 'https://trade.500.com/jczq/',
})
resp = opener.open(fenxi_req)
```

### Batch Size Limits

- **Max 10 matches per batch**: After 10 matches, pause 30-60 seconds
- **Max 50 matches per session**: After 50 matches, stop and resume at least 1 hour later
- **Backoff on 403/429**: If you get a 403 Forbidden or 429 Too Many Requests, stop immediately and wait at least 30 minutes before retrying

### Reuse the Safe Fetcher Module

A pre-built `scripts/safe_fetcher.py` module is bundled with this skill. Use it instead of writing raw urllib code:

```python
from scripts.safe_fetcher import SafeFetcher

fetcher = SafeFetcher()
html, raw = fetcher.fetch(
    'https://odds.500.com/fenxi/ouzhi-{id}.shtml',
    referer='https://trade.500.com/jczq/'
)
```

It handles: Cookie auto-collection, browser headers, random delays, gzip, and block detection. See the module docstring for all options.

### Detect Block

```python
# Check for block indicators in response:
block_indicators = [
    '403 Forbidden' in str(resp.status),
    len(html) < 1000,                          # Too small = captcha/block page
    '验证' in html or 'captcha' in html.lower(),  # CAPTCHA triggered
    '您访问过于频繁' in html,                     # Rate limit message
    resp.headers.get('Content-Type', '') == 'text/html' and len(html) < 5000,  # Block page
]
if any(block_indicators):
    raise Exception(f"Blocked by 500.com anti-scraping at {url}")
```

### Historical Data (Wanchang/Backtesting)

For historical matches:
1. **Prefer the liansai.500.com JSON API** (`/index.php?c=score&a=getmatch`) over scraping fenxi pages directly — it's lighter and less detectable
2. Only fetch the fenxi pages for matches you actually need to analyze
3. Space out historical fetches at 1 match per 5 seconds
4. Cache the raw output aggressively (indefinitely for historical data — it never changes)

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

---

## Wanchang (Completed Matches) — For Backtesting

### Data Source

```
URL: https://live.500.com/wanchang.php
Content: All completed matches for the most recent matchday
Fields: match ID (fid), kickoff time, league, home team (with rank), away team (with rank),
        full-time score, half-time score
```

### Parsing Rules

```
Extract from the page:
  League: text between "[" and "]" after match date, or standalone league name
  Time: HH:MM format
  Home team: name after ranking bracket, before score
  Away team: name after score, before optional ranking bracket
  Full-time score: "X-Y" format between team names
  Half-time score: second "X-Y" at end of line

Filter: only extract matches where league contains target keywords (e.g., "世界杯" for World Cup)
Output format:
  {
    "fid": "extractable from detail link",
    "date": "2026-06-20",
    "time": "11:00",
    "league": "世界杯",
    "home_team": "土耳其",
    "away_team": "巴拉圭",
    "home_rank": 3,
    "away_rank": 4,
    "ft_score": "0-1",
    "ht_score": "0-1"
  }
```

### Usage with Backtesting

```
1. Scraper fetches wanchang → outputs completed match results JSON
2. Analyst reads prediction log + actual results
3. Compare: predicted W/L direction vs actual outcome
4. Compute: accuracy, EV, win rate per confidence tier (A/B/C), trap accuracy
5. Output: backtest report → parameter calibration recommendations
```
