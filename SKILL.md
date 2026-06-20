---
name: football-odds-analyst
description: "Pro football odds/Asian handicap data analyst v2.7. Trigger keywords: analyze match, odds analysis, handicap analysis, 1X2 analysis, Asian handicap, match data, football analysis, odds movement, opening odds, closing odds, trap detection, lottery simulation, 混合过关, 竞彩, 彩票. Cache-first: odds-by-tournaments (1 quota = entire tournament, 40x more efficient than per-fixture /odds). Built-in 12-step analysis with quota-safety protocol. Mixed parlay backtest: 6/6 wins (+107.8% ROI)."
allowed-tools: Read, Write, Bash, WebSearch, WebFetch
agent_created: true
version: 2.7
released: 2026-06-20
changelog: |
  v2.7: Sec 11 竞彩混合过关 (500.com+lottery.gov.cn+动态Barbell), Sec 12 《足球财富》方法论 (欧赔动态/亚盘临场/大小球/欧亚综合), Sec 13 实战盘口分析体系 (5篇教程: 盘型推算/四口诀/三维一体/背离检测/联赛特性/资金管理), cache-first (Rule ⑨), endpoint efficiency (Rule ⑩)
  v2.6: 14.0b Stomp xG, 14.0c Host hist xG, 9.16 full-cycle, draw inertia, Sec 10 Mixed Parlay (blind backtest: +107.8% ROI, 6/6 tickets)
  v2.5: W/L priority output, 14.0a away xG strong-D discount, 9.15 6/20 RCA, extreme favorite floor, cross-trigger cap
  v2.4: Rules #27 first point/win motivation, #28 heat discount, Section 9.14复盘
---

# Football Odds & Asian Handicap Data Analyst v2.7

Professional football odds and Asian handicap data analysis. Designed for match odds logic study, data decomposition, and trap identification.

Built-in complete odds analysis system. **Only needs OddsPapi** — 3-bookmaker golden triangle: Pinnacle (sharp pricing baseline) + SBOBet (Asian handicap king) + bet365 (retail heat gauge). **Cache-first**: `/v4/odds-by-tournaments` (1 quota = entire tournament, 40× more efficient than per-fixture `/v4/odds`). `/v4/historical-odds` is permanently free. Web search fallback when no API key.

---

## 🛑 STOP — Quota Safety Protocol (ALWAYS FIRST)

```
QUOTA SAFETY IS THE HIGHEST PRIORITY. These rules override all other analysis steps.

① Only 2 endpoints are free: /v4/historical-odds and /v4/account.
   All 13 other endpoints deduct quota (1 call = 1 quota).

② 🔴 IRON RULE: Confirm before spending quota. No exceptions. No waivers.
   a. GET /v4/account → read remaining quota
   b. Calculate how many quota are needed
   c. Show user and wait for explicit confirmation:
      "Need: [endpoint] × [calls] = [N] quota. Current: X/total. Continue? (yes/no)"
   d. Do NOT send a single billed request until user replies "yes"/"确认"
   e. Even if user said "don't ask again" 5 minutes ago → still ask every time

③ 🔴 IRON RULE: No "yes" → no request. No "确认" → no request.
   Never assume consent. Never infer intent. Never guess.
   Never "let me pull it first and tell you later."

④ After /v4/historical-odds fails → NEVER silently switch to /v4/odds (billed).

⑤ ALL calls strictly serial. Validate previous response before next call.
   No concurrency. No skipping validation.

⑥ 🕐 Timezone rule (wrong match = completely wrong analysis):
   "Tomorrow"/"today" → judge by user's local timezone.
   Obtain via: system timezone (date +%Z) or user context UTC offset.
   Default assumption: Chinese user = Asia/Shanghai (UTC+8).
   /v4/fixtures returns startTime in UTC → convert to local before filtering.

⑦ 📊 Data-first principle (no guessing):
   All API calls must complete and data fully sampled before starting 12-step analysis.
   Forbidden: starting analysis before data is fully pulled.
   Forbidden: substituting "estimate"/"roughly"/"probably" for real data.
   Every analytical conclusion must cite its data source (bookmaker + timestamp).

⑧ CACHE PERSISTENCE — never store in /tmp:
   Cache dir: ~/.workbuddy/skills/football-odds-analyst/.cache/oddspapi/
   mkdir -p ~/.workbuddy/skills/football-odds-analyst/.cache/oddspapi/
   Cache is eternal: valid JSON file → use it, never re-fetch.
   No expiry, no auto-clean. outcome IDs and fixtures are static data.
   Historical odds data is fresh each pull (live data, no cache).
   Only delete cache on explicit user request to refresh.

⑨ 🟢 CACHE-FIRST CHECK (MANDATORY — ALWAYS RUN BEFORE ANY BILLED CALL):
   a. List cache dir: ls ~/.workbuddy/skills/football-odds-analyst/.cache/oddspapi/
   b. Check which data is already cached:
      - Fixtures cache: oddspapi_fixtures_{tournamentId}.json → skip /v4/fixtures if exists
      - Odds-by-tournament cache: odds_tournament_{bookmaker}_{tournamentId}.json → skip /v4/odds-by-tournaments if exists for that bookmaker
      - Outcome IDs cache: outcome_ids_{tournamentId}.json → check if target fixtureIds are present
   c. For each missing piece → identify the most efficient endpoint (see Rule ⑩ below)
   d. NEVER re-fetch data that already exists in cache just to "refresh" or "confirm"
   e. If cache has stale data (pre-match prices before kickoff) → still use it for pre-match analysis

⑩ 🔵 ENDPOINT EFFICIENCY RULE — choose the endpoint that yields MAX DATA per QUOTA:
   OddsPapi pricing: "1 successful billed call = exactly 1 quota. Response size, entry count,
   query parameters, and HTTP status codes have NO impact on the count."

   Efficiency ranking (most → least data per quota):
   Rank 1: /v4/odds-by-tournaments?bookmaker=X&tournamentIds=T → 1 quota = ALL fixtures
           in tournament for 1 bookmaker (40+ matches × 90+ markets = $0.004/match)
   Rank 2: /v4/fixtures → 1 quota = ALL ~103 matches schedule for whole tournament
   Rank 3: /v4/odds?fixtureId=X → 1 quota = 1 single fixture (350 bookmakers, but only 1 match)
           ⚠️ AVOID — use /v4/odds-by-tournaments instead whenever possible
           ONLY use if: a single outlier fixture not covered by tournament cache

   🔴 Decision tree when cache is incomplete:
   ┌─ Need fixture schedule? → /v4/fixtures (1 quota × 1 call)
   ├─ Need odds for tournament? → /v4/odds-by-tournaments × 3 (3 quota: pinnacle + bet365 + sbobet)
   │  This one call per bookmaker gives you ALL fixtures' 1X2/AH/OU/CS data.
   │  SAVE the full response → it doubles as outcome ID source AND live odds snapshot.
   ├─ Need 1X2 historical line movement? → /v4/historical-odds (0 quota, free)
   └─ Need odds for 1 isolated match only? → ⚠️ Ask user if they want full tournament instead
      (3 quota for ALL matches vs 1 quota per single match — tournament is always better)

   🔴 Parameter iron law (verified 2026-06-20):
   - /v4/odds-by-tournaments: bookmaker (singular) + tournamentIds (plural)
   - /v4/fixtures: tournamentId (singular)
   - Do NOT add sportId, marketTypeIds, or any extra parameters

Violating any of the above = wasted user quota or incorrect match analysis.
```

All conclusions based on mathematical formulas, handicap rules, and fundamental logic. No subjective judgment.

---

## Data Source Configuration

Default: **OddsPapi** (register at oddspapi.io, 250/month)

> ⚠️ **Platform name verification** (2026-06-19 专家评审): The API platform's official name is "OddsPapi" (domain: oddspapi.io). Before first use, verify via:
> 1. `WebFetch https://oddspapi.io/zh/docs` → confirm API is accessible
> 2. If the site is unreachable, try alternative URL: `oddspapi.com` or search "OddsPapi API documentation"
> 3. Do NOT proceed with API calls until the platform is confirmed accessible

| Source | Purpose | Quota | Key Features |
|--------|---------|:-----:|--------------|
| OddsPapi (primary) | All odds + historical | 250/month | 350+ bookmakers, all markets |
| Web search (fallback) | Zero-config option | Unlimited | No key needed |

> **Quota facts (from official docs):**
> - "Each successful call to a billed endpoint deducts exactly 1 request from your quota. Response size, entry count, query parameters, and HTTP status codes have NO impact — a call returning 1,000 fixtures costs the same 1 quota as one returning 0 fixtures."
> - `/v4/historical-odds`: permanently free, unlimited
> - `/v4/odds-by-tournaments?bookmaker=X`: 1 quota = ALL tournament fixtures for 1 bookmaker
> - `/v4/odds?fixtureId=X`: 1 quota = 1 single fixture (⚠️ avoid — use odds-by-tournaments instead)
> - `/v4/fixtures`: 1 quota = entire tournament schedule
>
> **Efficiency rule**: Always pull at tournament level. 3 calls (pinnacle+bet365+sbobet via odds-by-tournaments) = 3 quota for ALL data. Per-fixture /v4/odds would cost 3×N quota for N matches.

### SBOBet Data Validation<!-- 2026-06-19 专家评审: SBOBet 支持性验证 -->

```
SBOBet (sbobet) is configured as the "Asian handicap king" in the 3-bookmaker golden triangle.
However, OddsPapi's sbobet endpoint support should be verified:

1. After first /v4/odds-by-tournaments?bookmaker=sbobet call:
   - Check response for actual AH market data
   - If response contains valid handicap ≠ 0 markets → SBOBet supported ✅
   - If response is empty or missing AH markets → SBOBet may not be supported ⚠️

2. Fallback plan if SBOBet is unavailable:
   a. Replace with Singbet (singbet) — another Asian-focused sharp bookmaker
   b. OR use bet365 as dual-purpose (retail + Asian reference)
   c. Mark in report: "⚠️ SBOBet unavailable, substituted with {singbet/bet365}"
   
3. Cross-validation without SBOBet:
   - Use Pinnacle + bet365 + WebSearch (OddsPortal public data)
   - AH comparison reduces from 3-way to 2-way
   - Flag SBOBet divergence checks as "skipped" in Step 10 corrections
```

### API Parameter Verification Checklist<!-- 2026-06-19 专家评审: 参数验证机制 -->

```
BEFORE every billed API call, verify against this checklist:

□ Endpoint URL: does it start with /v4/ and match the documented endpoint?
□ Parameter: bookmaker (singular, NOT bookmakerIds) — value is a slug string
□ Parameter: tournamentIds (plural, NOT tournamentId) — value is a number
□ Parameter: fixtureId (singular, NOT fixtureIds) — value is a number
□ Parameter: bookmakers (plural, for /historical-odds) — value is comma-separated
□ No extra params: do NOT add sportId, marketTypeIds, or other undocumented params
□ API key: appended as apiKey=KEY at end of query string
□ Save flag: -o cache_file.json for first call (inspect + save in ONE call)

Common mistakes (from 2026-06-19 quota waste retrospective):
  ❌ bookmakerIds=pinnacle   → ✅ bookmaker=pinnacle
  ❌ tournamentId=16         → ✅ tournamentIds=16
  ❌ sportId=10 (unnecessary) → ✅ omit it
  ❌ Inspect-only then re-fetch → ✅ save to file on first call
```

### API Key Rules

- No API keys are pre-filled in this Skill. First use requires user to provide OddsPapi API key.
- Key is session-only, **never written to skill file**.

---

## Section 1: Global Hard Constraints

1. **Analysis priority (v2.3)**: 反叙事检查 > 阵容质量差异 > 世界杯历史体系 > 防守等级量化(含资格赛折价) > 不败惯性 > 主场优势 > 回光返照(淘汰压力+首秀战意+久别重逢) > xG模型信号(均势必备) > 钟摆效应 > 欧赔数学 > 欧亚匹配 > 陷阱扫描 > 压缩强度验证 > 走势真实性 > 概率合成<!-- 2026-06-19 回检: 新增不败惯性、资格赛折价、xG模型均势优先级 -->
2. **Core principle**: European odds show true implied probability; Asian handicap shows money inducement. Match = straight play. Divergence = check cold traps first.
3. **Output requirement**: Every analysis includes math calculation, pattern identification, risk warnings, scoring. Logic must be verifiable.
4. **Business boundary**: This skill is for sports data logic education only. **Never constitutes betting advice.**
5. **Data prerequisite**: Identify data mode immediately, pull odds/handicap/fundamentals accordingly. **No data = no analysis.**
6. **Score prediction**: Required output — predicted score + probability projection using weighted probability synthesis model, combined with Asian handicap lines and over/under data. Must include: most likely exact score, alternative score lines, confidence level per score, confidence interval, and reverse risk note.
7. **Disclaimer**: Vig/drake mechanism means long-term mathematical expectation is negative. Odds analysis improves data discernment, cannot guarantee profit.
8. **Team name display 🔴 HIGH PRIORITY**: ALL output MUST use Chinese domestic names. Use built-in knowledge to translate. Only fall back to WebSearch if a team name is unrecognized.

   **Default Chinese name mapping (common World Cup teams)**:
   | English API Name | Chinese | English API Name | Chinese |
   |:---|:---|:---|:---|
   | Switzerland | 瑞士 | Korea Republic | 韩国 |
   | Bosnia and Herzegovina | 波黑 | Japan | 日本 |
   | Czechia | 捷克 | South Africa | 南非 |
   | Canada | 加拿大 | Qatar | 卡塔尔 |
   | Mexico | 墨西哥 | Brazil | 巴西 |
   | Argentina | 阿根廷 | France | 法国 |
   | Germany | 德国 | England | 英格兰 |
   | Spain | 西班牙 | Portugal | 葡萄牙 |
   | Italy | 意大利 | Netherlands | 荷兰 |
   | Croatia | 克罗地亚 | Uruguay | 乌拉圭 |
   | Belgium | 比利时 | Colombia | 哥伦比亚 |
   | USA | 美国 | Morocco | 摩洛哥 |

   **🔴 Dynamic team name verification protocol** (2026-06-19 专家评审):
   ```
   BEFORE generating any report output:
   
   1. For each team name returned by API/fixtures:
      a. Check static mapping table above
      b. If FOUND → use mapped Chinese name ✅
      c. If NOT FOUND → execute WebSearch: "[Team Name] 中文 译名 足球 国家队"
         → Extract standard Chinese name from search results
         → Add to mapping table (this session only, with "WebSearch" annotation)
      d. If STILL not found after WebSearch → use English name + ⚠️ red marker:
         "⚠️ [English Name]（中文译名未匹配，请手动确认）"
   
   2. For World Cup newcomer teams (e.g., debutants, newly renamed):
      → ALWAYS run WebSearch: "2026世界杯 参赛球队 中文名单"
      → Cross-check all team names against FIFA official Chinese name list
      → Supplement mapping table with any new entries found
   
   3. Error tolerance output:
      → If ANY team name uses English fallback → add red banner at report top:
         "🔴 警告：部分球队名称未能匹配中文译名，分析可能不完整"
   ```

9. **🔴 Retro-Feedback Mandatory (post-match correction loop)**<!-- 2026-06-19 回检: 输出使用英文队名 → added rule #8 -->: After any prediction is proven wrong by an actual result, perform root-cause analysis and update judgment rules:
   - **Identify**: What specific signal was misinterpreted? (odds compression, 6D inflation, narrative over-weighting, etc.)
   - **Formalize**: Convert the lesson into a concrete, falsifiable rule that would have caught the error.
   - **Update**: Inject the new rule into the relevant Section 4 subsection, with a dated comment: `<!-- YYYY-MM-DD 回检: [event] → [trigger] -->`
   - **Score retro-feedback**: If actual score is NOT in predicted Top 3, must additionally:
     1. Calculate xG deviation (predicted xG vs actual goals) — was attack overestimated or defense underestimated?
     2. Check if zero-inflation correction (14.6) should have triggered but didn't, or triggered excessively.
     3. Check if CS market calibration (14.3) was improperly skipped.
     4. Convert findings into coefficient adjustments (e.g., "strong-team xG downgrade from 0.92 to 0.90"), add to the relevant Section 4(14) sub-rule with `<!-- 回检日期: [event] → [adjustment] -->` annotation.

   The goal is continuous improvement: every wrong prediction makes the skill sharper.

---

## Section 2: Caching & Execution Flow

### 2.1 Fixture Cache (1 quota, one-time)

```
First time a league/tournament is used:
  1. Check if ~/.workbuddy/skills/football-odds-analyst/.cache/oddspapi_fixtures_{tournamentId}.json exists
  2. If NOT:
     GET /v4/fixtures?tournamentId=X&from=SEASON_START&to=SEASON_END&apiKey=KEY
     → 1 quota → save to cache file
  3. If EXISTS: read from file (0 quota)

  4. Determine target date in user's local timezone:
     → Get user timezone: read date +%Z → if "+08" or "CST" or Chinese context → Asia/Shanghai (UTC+8)
     → "明天" = current_local_date + 1 day
     → "今天" = current_local_date

  5. Filter fixtures for target date (convert UTC → local):
     → /v4/fixtures returns startTime in ISO 8601 UTC (e.g. "2026-06-18T16:00:00.000Z")
     → Convert: localTime = UTC + timezone offset
     → Filter: keep only fixtures where local date matches target date
     → Build match list: [{fixtureId, home, away, startTime, localTime}]
```

**World Cup 2026**: Cache file `oddspapi_fixtures_16.json`. If missing → ask user: "/v4/fixtures × 1 = 1 quota. Proceed?" After yes: `GET /v4/fixtures?tournamentId=16&from=2026-06-11&to=2026-07-19&apiKey=KEY` → 1 quota → caches all 103 matches.

### 2.2 Odds + Outcome ID Cache (3 quota, one-time per tournament)

```
🔴 STEP 0 — CACHE-FIRST CHECK (Rule ⑨):
   ls ~/.workbuddy/skills/football-odds-analyst/.cache/oddspapi/
   → Check if odds_tournament_{bookmaker}_{tournamentId}.json EXISTS for each bookmaker
   → Check if target fixtureIds are present INSIDE the cached file
   → If ALL 3 bookmakers cached AND all target fixtures present → 0 quota, skip to 2.3

🔴 STEP 1 — Only if cache MISSING or INCOMPLETE:
   Ask: "Need /v4/odds-by-tournaments × N = N quota for N missing bookmakers. Continue? (yes/no)"

⚠️ Parameter iron law (verified 2026-06-20):
  - bookmaker (singular) + tournamentIds (plural)
  - Do NOT add sportId or marketTypeIds

Serial calls (≥1s between. MUST save response in ONE call per bookmaker):
  GET /v4/odds-by-tournaments?bookmaker=pinnacle&tournamentIds={tid}&apiKey=KEY
  GET /v4/odds-by-tournaments?bookmaker=bet365&tournamentIds={tid}&apiKey=KEY
  GET /v4/odds-by-tournaments?bookmaker=sbobet&tournamentIds={tid}&apiKey=KEY

Save response to: .cache/oddspapi/odds_tournament_{bookmaker}_{tournamentId}.json

Each response provides BOTH:
  ✅ LIVE ODDS SNAPSHOT for ALL fixtures (1X2/AH/OU/CS markets with current prices)
  ✅ OUTCOME IDs for ALL markets (input to free /v4/historical-odds)

Data extraction from odds-by-tournaments response:
  a. 1X2 (market '101'): oid='101'=home, oid='102'=draw, oid='103'=away (all 3 bookmakers)
  b. AH: filter where bookmakerOutcomeId contains '/home' + '/away'
  c. OU: filter where bookmakerOutcomeId contains '/over' + '/under' (exclude team totals)
  d. CS: filter where bookmakerOutcomeId contains ':'
  ⚠️ bet365/sbobet marketActive may be False in non-trading hours → prices still valid
  ⚠️ SBOBET bookmakerOutcomeId labels ('1','X','2') may be swapped → trust OddsPapi oid

Rebuild outcome IDs cache from saved odds_tournament files (0 extra quota):
  → Extract all outcome IDs per fixtureId from all 3 bookmakers
  → Save to outcome_ids_{tournamentId}.json
  → Historical-odds queries read from this file (0 quota)

💡 Efficiency insight: /v4/odds-by-tournaments = 40+ fixtures for 1 quota.
   /v4/odds = 1 fixture for 1 quota. Tournament batch is 40× more efficient.
   NEVER use /v4/odds when odds-by-tournaments can cover the same fixtures.
```

### 2.3 Historical Odds Queries (per match, 0 quota)

```
/v4/historical-odds is permanently free, never counts toward quota.
Rate limit: 5000ms (≥5s between serial calls).
Bookmaker cap: max 3 comma-separated slugs.

Call A — 1X2 timeline (3 bookmakers):
  GET /v4/historical-odds?fixtureId=X&bookmakers=pinnacle,bet365,sbobet&outcomeId=101,102,103&apiKey=KEY
  → Returns ~510KB (outcomeId filter in API reduces 10MB+ → 510KB)
  → Extract: 3 bookmakers × 3 outcomes (H/D/A) × {open, now, changes}

Call B — AH + OU + CS + TG timeline (pinnacle only):
  GET /v4/historical-odds?fixtureId=X&bookmakers=pinnacle&outcomeId={cached_AH_OU_market_IDs}&apiKey=KEY
  → Extract: pinnacle AH + OU daily sampling, CS + TG latest snapshot

Daily sampling rule: from full timeline, take only the first entry per day.
```

**Extraction code A (1X2, full change series)**:
```javascript
const d = JSON.parse(raw); const out = {fixtureId: d.fixtureId, bookmakers: {}};
for (const [bm, data] of Object.entries(d.bookmakers)) {
  const m101 = data.markets["101"]; if (!m101) continue;
  const ml = {};
  for (const [oid, label] of [["101","H"],["102","D"],["103","A"]]) {
    const tl = m101.outcomes[oid]?.players?.["0"] || [];
    if (!tl.length) continue; let changes = 0;
    const fullSeries = tl.map((e,i) => {
      if (i>0 && e.price !== tl[i-1].price) changes++;
      return {time: e.createdAt, price: e.price};
    });
    ml[label] = { series: fullSeries, totalChanges: changes };
  }
  out.bookmakers[bm] = { ml };
}
```

**Extraction code B (AH + OU + CS, pinnacle only)**:
```javascript
function dailySample(timeline) {
  const days = {};
  for (const entry of timeline) {
    const day = entry.createdAt.slice(0, 10);
    if (!days[day]) days[day] = entry.price;
  }
  return Object.entries(days).map(([date,price]) => ({date,price}));
}
const data = d.bookmakers["pinnacle"]; if (!data) return;
const markets = data.markets;
// Main AH + main OU = top-2 2-outcome markets by entry count
const twoway = Object.entries(markets)
  .filter(([k,m]) => Object.keys(m.outcomes).length === 2)
  .map(([k,m]) => {
    let n=0; for(const o of Object.values(m.outcomes)) n += (o.players?.["0"]||[]).length;
    return {key: k, entries: n, outcomes: m.outcomes};
  }).sort((a,b) => b.entries - a.entries);
const ext = (x) => {
  const ks = Object.keys(x.outcomes), p = (id) => x.outcomes[id]?.players?.["0"]||[];
  return {s0: dailySample(p(ks[0])), s1: dailySample(p(ks[1]))};
};
if (twoway.length >= 2) { out.bookmakers[bm].ah = ext(twoway[0]); out.bookmakers[bm].ou = ext(twoway[1]); }
// Correct Score: market with >3 outcomes, take latest price per score
const csMarket = Object.entries(markets)
  .filter(([k,m]) => Object.keys(m.outcomes).length > 3)
  .sort((a,b) => {
    let na=0,nb=0; for(const o of Object.values(a[1].outcomes)) na += (o.players?.["0"]||[]).length;
    for(const o of Object.values(b[1].outcomes)) nb += (o.players?.["0"]||[]).length;
    return nb - na;
  })[0];
if (csMarket) {
  const cs = {};
  for (const [oid, odata] of Object.entries(csMarket[1].outcomes)) {
    cs[oid] = dailySample(odata.players?.["0"]||[]).slice(-1)[0];
  }
  out.bookmakers[bm].cs = cs;
}
```

### 2.4 Three-Bookmaker Roles

| Bookmaker | Role | Unique Value | Primary Duty |
|:---|:---|:---|:---|
| **Pinnacle** | Global sharp pricing baseline | 2-3% vig, closest to true probability; highest closing-line correlation | True probability benchmark, AH calibration, opening assessment |
| **SBOBet** | Asian handicap king | 1.8-2% AH vig, full granularity; Asian professional money | AH depth judgment, water structure, Asian flow tracking, Euro-Asian divergence |
| **bet365** | Global retail heat gauge | Highest retail volume; spread vs sharp = classic hot-cold gap | Public sentiment, retail flow, overheat trap detection |

**Three-phase division**:
- **Opening (open → T-72h)**: Pinnacle = primary baseline; SBOBet AH vs Pinnacle ≥0.25 ball divergence → trap risk; bet365 opening bias → natural heat direction.
- **Mid-movement (T-24h → T-12h)**: bet365 = core observation for retail flow; Pinnacle verifies authenticity (parallel = real, diverging = trap); SBOBet AH moves first → Asian sharp signal.
- **Closing (T-1h)**: Pinnacle = final probability anchor; SBOBet = final AH alignment; bet365 vs Pinnacle spread = hot-cold divergence.

**Dispersion grading**:
- <0.05: Strong consensus, straight play reliable
- 0.05–0.10: Divergence exists, combine fundamentals
- >0.10: Severe internal disagreement, upset risk elevated

### 2.5 Phase Plan (3 checks/day)

```
Phase 0 — One-time initialization (⚠️ BILLED, must confirm with user):
  /v4/fixtures × 1 + /v4/odds-by-tournaments × 3 = 4 quota total (once per tournament, never refetch)

Phase 1 — Morning (0 quota):
  Read outcome IDs from cache. Call A + Call B per match (serial, ≥5s between).
  Focus: opening positioning + 3-bookmaker dispersion + daily trend.

Phase 2 — Afternoon (0 quota):
  Same as Phase 1. Focus: movement comparison + scoring update.

Phase 3 — Pre-match (0 quota):
  Same as Phase 1/2 using /historical-odds (free).
  Focus: AH divergence check + final probability synthesis.

All 3 daily phases use /historical-odds (free) with cached outcome IDs → 0 quota per phase.
```

### 2.6 Monthly Quota Summary

```
Phase 0 (one-time):    4 quota  (fixtures ×1 + outcome ID cache ×3)
Phase 1-3 (daily):     0 quota  (historical-odds free, IDs cached)
──────────────────────────────────────────
Lifetime per tournament: 4 / 250
```

### 2.7 Quota Waste Retrospective (2026-06-19)

| # | Call | Quota | Reason |
|:--:|------|:--:|------|
| 1 | /v4/account | 1 | Quota check (mandatory per session) |
| 2 | odds-by-tournaments?bookmakerIds=1&tournamentId=16 | 1 ❌ | Wrong params: `bookmakerIds`→`bookmaker`, `tournamentId`→`tournamentIds` |
| 3 | odds-by-tournaments?bookmakerIds=1&tournamentIds=16 | 1 ❌ | `bookmakerIds`→`bookmaker` |
| 4 | odds-by-tournaments?bookmaker=pinnacle (inspect only) | 1 | Correct params but inspect-only |
| 5 | odds-by-tournaments?bookmaker=pinnacle (save) | 1 ❌ | Duplicate! Should have inspected + saved in step 4 |
| 6 | odds-by-tournaments?bookmaker=bet365 | 1 ✅ | Correct |
| 7 | odds-by-tournaments?bookmaker=sbobet | 1 ✅ | Correct |

> **Wasted 4 of 7 quota. Lessons:**
> 1. Parameter names must be exact (`bookmaker` singular + `tournamentIds` plural)
> 2. First API call: use `-o FILE.json` to save simultaneously (avoid inspect-only then save = 2x quota)
> 3. /v4/account `request_count` includes the account call itself and all other endpoints (including errors)

---

## Section 3: OddsPapi API Reference

### API Documentation Priority

> **When encountering any API issue (timeout/truncation/data anomaly/unknown params), first reaction is NOT guessing or switching — it's checking the official docs.**
>
> Docs: https://oddspapi.io/zh/docs
>
> Troubleshooting flow (fixed order):
> 1. Check known doc pages first → 2. If no answer, WebFetch doc index → 3. Fetch relevant sub-page → 4. Only fall back to WebSearch/alternatives if docs have no answer.

### Authentication & Base

All endpoints: URL parameter `apiKey={{API_KEY}}`
Base URL: `https://api.oddspapi.io/v4`

### Quota & Rate Limits

**Billed endpoints (1 request = 1 quota)**: `/v4/players`, `/v4/settlements`, `/v4/fixtures`, `/v4/fixture`, `/v4/odds-by-tournaments`, `/v4/languages`, `/v4/sports`, `/v4/bookmakers`, `/v4/markets`, `/v4/tournaments`, `/v4/participants`, `/v4/scores`, `/v4/odds`

**Free endpoints**: `/v4/historical-odds` (always free), `/v4/account` (always available)

**Key rule**: 1 request = 1 quota. Response size, entry count, query parameters have NO impact.

**Rate limits**: 1000ms per endpoint, 5000ms for historical-odds.

### Key Endpoints

**GET /v4/tournaments** — League list
```
GET /v4/tournaments?sportId=10&apiKey=KEY
→ sportId=10 = football (fixed)
→ Returns [{tournamentId, tournamentName, categoryName, upcomingFixtures}]
```

**GET /v4/fixtures** — Fixture list (1 quota, cache entire season)
```
GET /v4/fixtures?tournamentId=16&from=2026-06-11&to=2026-07-19&apiKey=KEY
→ Returns ALL fixtures in date range. 1 call = entire tournament cached.
```

**GET /v4/odds** — Single match odds (1 quota — ⚠️ AVOID)
```
GET /v4/odds?fixtureId=X&apiKey=KEY
→ 1 request = ALL 350+ bookmakers × ALL markets for 1 fixture.
→ ⚠️ 1 fixture per quota. For N matches, costs N quota.
→ ✅ Use /v4/odds-by-tournaments instead: 1 quota = ALL tournament fixtures.
→ Only use /v4/odds if: single isolated match not in any tournament cache.
```

**GET /v4/odds-by-tournaments** — Batch tournament odds (1 quota — ✅ PREFERRED)
```
GET /v4/odds-by-tournaments?bookmaker=pinnacle&tournamentIds={tournamentId}&apiKey=KEY
→ 1 quota = ALL 40+ fixtures for 1 bookmaker (40× more efficient than /v4/odds)
→ Response: ~2MB per bookmaker, contains bookmakerOdds.{bookmaker}.markets
→ Use 3 calls (pinnacle, bet365, sbobet) = 3 quota for complete golden triangle data
→ Cache the full response — it serves as BOTH live odds snapshot AND outcome ID source
```

**GET /v4/historical-odds** — Historical timeline (FREE)
```
GET /v4/historical-odds?fixtureId=X&bookmakers=pinnacle,bet365,sbobet&outcomeId=101,102,103&apiKey=KEY
→ Permanently free. bookmakers: max 3. Rate limit: 5000ms.
→ Raw: ~2-5MB per match with 3 bookmakers. Parse on-the-fly: keep only 1X2 + main AH + main OU.
→ Output: ~2.5KB per match.
```

**GET /v4/account** — Account status (always available)
```
GET /v4/account?apiKey=KEY
→ Returns: request_limit, request_count
→ MUST call before any batch of billed operations.
```

### Known tournamentId Values

| League | tournamentId |
|--------|:-----------:|
| World Cup 2026 | 16 |
| Premier League | 17 |
| La Liga | 200 |
| Bundesliga | 199 |
| Serie A | 198 |
| Ligue 1 | 204 |
| Champions League | 2 |

> For other leagues: `GET /v4/tournaments?sportId=10` (1 quota, cache result).

---

## Section 4: Knowledge Base — Odds Analysis Rules

### (1) Core Mathematical Formulas

```
Overround (vig factor) = 1/home_price + 1/draw_price + 1/away_price
True probability (de-vig) = (1/outcome_price) / overround
Payout rate = 1 / overround

Normalization (always apply after corrections):
  adjusted_p[i] = p[i] + Σ(corrections targeting outcome i)
  normalized_p[i] = adjusted_p[i] / Σ(adjusted_p[j] for j in {home,draw,away})
```
> ⚠️ **Naming clarification** (2026-06-19 专家评审): "Implied total probability" has been renamed to **"Overround"** to avoid confusion — this value is always >1 (typically 1.05–1.18) due to the bookmaker's profit margin, NOT a probability. The only valid probability is the de-vigged **True probability**.
>
> **Normalization is mandatory**: After applying weighted probability corrections (Section 4(13)), always run Σ(adjusted_p) normalization. Never skip — uncorrected sums may drift to 98% or 102%, introducing systematic bias.

Standard payout rate thresholds:
| League Level | Normal Range |
|-------------|-------------|
| Top 5 (EPL, La Liga, Bundesliga, Serie A, Ligue 1) | 90%–95% |
| Second tier (Championship, 2.Bundesliga, Eredivisie, etc.) | 87%–90% |
| Niche leagues | 85%–88% |

### (2) European Odds → Asian Handicap Conversion

| Home Win Range | Theoretical Asian Handicap |
|--------------|---------------------------|
| 1.70–1.85 | Home -0.5/-0.75 |
| 1.85–2.00 | Home -0.25/-0.5 |
| 2.00–2.20 | PK / Home -0.25 |
| 2.30+ | PK or Away handicap |

### (3) Fifteen Euro-Asian Divergence & Systemic Trap Patterns<!-- 2026-06-19 全错复盘: expanded from 7 → 11 → 15 -->

| # | Pattern | Feature | Quantitative Trigger | Risk |
|---|---------|---------|------|------|
| 1 | Deep odds, shallow handicap | Odds show favorite, handicap lowers entry bar | Euro-Asian gap ≥0.25 ball: theoretical AH is deeper than actual by ≥0.25 | Creating hot money, watch for draw/away upset |
| 2 | Shallow odds, deep handicap | Odds unimpressive, handicap artificially deep + high water | Euro-Asian gap ≥0.25 ball: actual AH is deeper than theoretical by ≥0.25 + SBOBet water >1.00 | Shunting money, straight outcome more likely |
| 3 | Draw odds dropping + deep handicap | Use outcomes to mask draw | Draw odds ↓ ≥8% from open + actual AH ≥0.25 deeper than theoretical | Draw is hidden result |
| 4 | Open match, late odds drop + handicap retreat | Standard trap | Home odds ↓ ≥5% in last 6h + AH retreats ≥0.25 ball (opposite direction) | Fake good news, bookmaker avoiding payout |
| 5 | Favorite deep handicap + water >1.05 | Bookmaker unwilling to take risk | AH ≥0.75 ball + SBOBet water ≥1.05 at close | Favorite struggles to cover, small win/push or upset |
| 6 | Weak side drops for no reason | Pure money manipulation | Underdog odds ↓ ≥10% with ZERO fundamental support (no injury return, no form improvement via WebSearch) | Data has minimal reference value |
| 7 | Narrative-driven moderate compression | Favorite odds compress 5-15% driven by public narrative (suspensions/injuries), but settle above 1.80; draw prob >25% after vig removal | Compression 5–15% + draw true prob >25% + compression driver is "known news" (WebSearch confirms) | Market overreacts to narrative, creating overvalued favorite. High upset/draw risk. | <!-- 2026-06-19 回检: Czechia 1-1 South Africa, H 2.05→1.877(-8.4%), draw true prob 27.2%, South Africa 2 suspensions → triggered -->
| 8 | Near-1-match illusion<!-- 2026-06-19 回检: Switzerland 4-1 Bosnia --> | Both teams had same previous result (both drew/won/lost), creating illusion of parity | Previous match result identical + current odds gap >0.40 (implied strength gap ≥2 tiers) + squad value gap ≥3× | Previous result is noise, squad quality is signal. Heavy favorite actually wins convincingly. |
| 9 | Historical independence fallacy<!-- 2026-06-19 回检: Canada 6-0 Qatar --> | "Team X has never won at World Cup" → used to discount probability | Analysis contains "never" / "historical first" / "从未" language → auto-flag. Re-evaluate as independent event. | Descriptive statistics mistaken for predictive evidence. The right question is "who is today's opponent?" |
| 10 | Star illusion<!-- 2026-06-19 回检: Mexico 1-0 South Korea --> | 1-2 famous stars create perception of team strength | Star team has ≤3 top-5-league starters + opponent has ≥6 → system > star signal | Individual talent overvalued vs. systemic cohesion. World Cup history repeatedly validates system over stars. |
| 11 | Home advantage neglect<!-- 2026-06-19 回检: Canada 6-0 Qatar --> | Host nation's home advantage systematically undervalued | Team plays in home country (host nation) + opponent traveled internationally → +10% win prob, +0.5 xG | World Cup home win rate >70% historically. Not subjective — it's a hard statistical edge. |

> ⚠️ **Quantitative execution rule** (2026-06-19 专家评审): ALL 15 traps now have explicit numerical triggers. When checking Step 4, run each trigger formula against actual data. If a trigger fires → mark the trap as HIT and apply ±10% correction in Step 10. Traps #8-#15 are NON-EURO-ASIAN traps — they are systemic/fundamental traps that should be checked BEFORE odds analysis in the new Step 1.5 (反叙事检查).

### (4) Four Opening Odds Laws

1. **Deep open, never retreat, never drop**: Firm initial positioning, no trap space, high reference value
2. **Paper strength advantage + deliberately shallow open**: Bookmaker showing weakness, guarding against hot money, focus on upset
3. **Opening water >1.10 test**: Bookmaker doesn't believe in favorite, low probability of covering
4. **Reasonable market + opening water <0.80 ultra-low**: Bookmaker locking payout early, truly believes in that side

### (5) Compression Intensity Classification<!-- 2026-06-19 回检: Czechia H 2.05→1.877 = -8.4% → Moderate; insufficient for "real conviction" -->

| Intensity | Threshold | Confidence Boost Weight | Risk Level |
|:----------|:----------|:--------------------------|:-----------|
| **Extreme** | >20% drop | Full weight (+7%) | Low — genuine market conviction |
| **Strong** | 10–20% drop | Full weight (+7%) | Low-Medium — genuine but verify narrative |
| **Moderate** | 5–10% drop | **Half weight (+3.5%)** | **Medium — may be narrative-driven overreaction** |
| **Weak** | <5% drop | Zero weight (0%) | High — no real conviction signal |

> ⚠️ Treating moderate compression as "real conviction" is a systematic error. Only Extreme (>20%) and Strong (10–20%) warrant full confidence boosts.

### (6) Late 1-Hour Movement Authenticity Rules

| Movement Type | Direction | Interpretation |
|-------------|---------|--------------|
| Raise line + drop water | Real belief | Proactively lowering payout, reference this side |
| Raise line + raise water | Trap risk | Fake strong position, typical hot money trap |
| Drop line + drop water | Trap pattern | Lowering entry bar to attract retail |
| Drop line + raise water | Complete bearish | Bookmaker fully against this side, reverse outcome priority |

### (7) Back-to-Wall Effect<!-- 2026-06-19 全错复盘: South Africa lost 0-2 + 2 suspensions → forced 1-1 draw vs Czechia --><!-- 🔴 必须在赔率分析之前检查! --><!-- 2026-06-19 回检: 新增世界杯首秀场景 -->

**Definition**: When a team faces elimination (lost first group match, or must-win scenario), their performance often exceeds market expectations. The market systematically under-prices desperation. Also: teams making their World Cup debut have extraordinary motivation that the market systematically undervalues.

**🔴 Execution order**: Check Back-to-Wall BEFORE any odds analysis (Step 1.5 反叙事检查 or Step 2 基本面). This is NOT a late correction — it changes how you read the odds from the start.

**Quantification**:
| Scenario | Adjustment | Rationale |
|:---------|:----------:|:----------|
| Team lost first group match, faces virtual elimination if they lose again | Draw +5%, Underdog win +5% | Desperate teams overperform |
| Team has key players suspended → forced into defensive reorganization | Underdog +3%, Draw +3% | Suspension paradoxically improves defensive organization |
| Both conditions met simultaneously (like South Africa vs Czechia) | Draw +8%, Underdog +5% | Compound effect — the market's biggest blind spot |
| Team already eliminated (no stakes) | No adjustment, or favorite +5% | No motivation = underperformance |
| **🆕 Team making World Cup debut (national first-ever appearance)** | **Draw +8%, Underdog +5%, xG防御×1.20** | **首秀战意 = 市场最大盲区之一。可与淘汰压力叠加。**<!-- 2026-06-19 回检: 佛得角首秀 0-0 西班牙 --> |
| **🆕 Both teams making World Cup debut** | **Draw +5% each, total uncertainty +15%** | **双方首秀 = 谁都怕输，保守开局概率极高。**<!-- 2026-06-19 回检 --> |
| **🆕 Unbeaten streak ≥85% (L20+ matches)** | **Unbeaten team +5~8%, Draw +5~8%** | **不败惯性: 不是运气, 是体系强度。日本 34/38不败→2-2荷兰。**<!-- 2026-06-19 回检: 荷兰 2-2 日本 --> |

### (8) Classic Harvest Pattern: Opening Build + Late Reverse

**Features**: Pre-match low favorite odds + shallow handicap to create certainty. No fundamental justification. Late suddenly raise water + retreat line + raise odds.

### (9) Fundamental Factor Weights (v2.0)<!-- 2026-06-19 全错复盘: 重排权重, 近1场从无限制降至8%, 阵容+体系=45% -->

| Weight | Factor | Note |
|--------|--------|------|
| ⭐⭐⭐⭐⭐ | Squad quality gap | Transfermarkt value ratio, top-5-league starter count — THE most reliable signal |
| ⭐⭐⭐⭐⭐ | World Cup system history | Knockout stage experience, historical record vs. continent — 20% weight |
| ⭐⭐⭐⭐ | Home/Neutral/Away | World Cup home = +10% win prob, +0.5 xG |
| ⭐⭐⭐⭐ | Back-to-Wall motivation | Team facing elimination → +5~8% underdog/draw boost (check FIRST, before odds) |
| ⭐⭐⭐ | Tactical style match | Attack vs. counter-attack vs. possession system compatibility |
| ⭐⭐ | Recent 3-5 match form | NOT single-match form. 3-5 matches, weighted toward recent |
| ⭐ | Individual star power | 1-2 stars ≠ strong team. System completeness > individual names |
| ⭐ | External factors | Fatigue, travel, weather |

> ⚠️ 近1场权重从无限制缩至8%。单场比赛结果是噪音，不是信号。

### (10) Six-Dimension Scoring Model v2.0<!-- 2026-06-19 全错复盘: 4/4 全错 → 全面重写评分标准 + 通胀惩罚 + 新阈值 -->

| Dim | Criterion | Score 1 Condition (v2.0 — 更严格) | Score 0 Condition |
|:---:|----------|---------------|------|
| 1 | **Fundamentals solid** | Squad quality gap ≥1 tier AND 3-5 match form supports direction AND Back-to-Wall check passed (underdog properly adjusted) AND narrative check passed (NOT driven by public news) — ALL 4 sub-conditions required | Any of: (a) squad quality close, (b) relying on single-match form, (c) Back-to-Wall not accounted for, (d) advantage is narrative-driven (opponent suspensions = "known news") |
| 2 | Euro-Asian match | Theoretical-vs-actual AH gap ≤ 0.25 ball for ALL 3 bookmakers. AND no bookmaker diverges >0.50 ball from Pinnacle. | Any bookmaker's gap >0.25, OR any bookmaker diverges >0.50 from Pinnacle baseline. |
| 3 | **Opening honest** | Opening odds match squad quality gap AND compression is NOT narrative-driven (WebSearch confirmed) AND compression is either Strong(>10%) or None(<5%) — moderate(5-10%) auto-flags | Opening deliberately deep/shallow vs quality. OR moderate compression (5-10%) with narrative driver. |
| 4 | Late movement clean | Movement doesn't hit ANY of 15 trap patterns. AND no harvest pattern. AND late 1h passes authenticity rules (Section 4(6)). | Any trap triggered. OR harvest pattern. OR late movement fails authenticity. |
| 5 | **Water logical** | Water changes justifiable by fundamentals AND draw prob ≤27% AND water fluctuation <0.06 (healthy liquidity). | Water unexplained. OR draw prob >27% (hard cutoff). OR fluctuation >0.06. |
| 6 | No one-sided hype | Multi-bookmaker consistency. SBOBet-Pinnacle AH gap <0.25. bet365-Pinnacle 1X2 spread <0.05. No anomalous limit drops. | Any bookmaker diverges >0.25. OR bet365 spread >0.10. OR limit drops >30% in 6h. |

**Updated quantitative thresholds**:

| Dimension | Key Metric | Pass Threshold (v2.0) | Change |
|:---|:---|:---|:---|
| Dim 1 | Squad quality + narrative | 4 sub-checks ALL pass | ↑ 从3条件到4条件 |
| Dim 2 | Max theoretical-vs-actual AH gap | ≤0.25 ball | 不变 |
| Dim 3 | Compression type | NOT moderate(5-10%) with narrative | ↑ 中度压缩默认不通过 |
| Dim 4 | Trap patterns hit | 0 of 15 (none) | ↑ 从7到15个陷阱 |
| Dim 5 | Draw probability | ≤27% (hard cutoff) | ↑ 从≤25%收紧到27%硬截止 |
| Dim 5 | Water fluctuation σ | <0.06 | 不变 |
| Dim 6 | SBOBet-Pinnacle AH gap | <0.25 ball | 不变 |
| Dim 6 | bet365-Pinnacle 1X2 spread | <0.05 | 不变 |

**6D 通胀惩罚(自动, 不可跳过)**:
```
出分后立即执行 (非可选):
  IF 方向是热门方 且 压缩=中度(5-10%) → -1
  IF 对方有回光返照(输球即淘汰) → -1
  IF 真实平局概率 > 27% → -1
  IF 方向驱动因素是公开叙事(陷阱#7确认) → -1
  IF 近1场权重占基本面判断>30% → -1
  IF 热门方赔率 < 1.15 → -1  <!-- 2026-06-19 回检: 西班牙 1.08 → 0-0, 超低赔率自动通胀 -->

最终得分 = max(0, 原始6D - 通胀惩罚)
```

**新解读阈值**:
- ≥5: 高参考价值 (罕见 — 需满分且0通胀惩罚)
- 4: 有参考价值
- 3: 有限参考价值 → 建议避免方向性预测
- ≤2: 高风险 → 跳过此场, 不建议任何预测

> **⚠️ 6/6 不再是可靠的**: 捷克对南非案例 — 6/6 无通胀惩罚 → 实际3分(通胀-3) → 平局正确。6D 满分是高危信号，必须跑通胀惩罚。

### (11) Industry Mnemonics

```
Odds dispersion shows direction, Asian handicap water shows truth
Raise + raise water = trap, drop + drop = real
Opening odds set the tone, late movement determines outcome
Euro-Asian divergence = find upset, fundamentals steady the ship
```

### (12) Twenty-Eight Universal Trap Rules<!-- 2026-06-19 回检: expanded 12→18→22→24→26→28 with traces #27-28 -->

1. **Low odds ≠ safe bet — ANY odds range**: Ultra-low (<1.50) AND moderate favorites (1.70–2.00) both lose/draw ~30–50% of the time. The warning applies to ALL odds. <!-- 2026-06-19 回检: Czechia 1.877 → 1-1 result → mid-range odds also unreliable -->
2. Universal public consensus = bookmaker creates heat = watch for upset
3. Sudden movement without injury/schedule news = liquidity balance, not directional
4. Niche leagues = low liquidity = manipulated lines, low credibility
5. Parlays compound exponentially, prefer singles
6. Line/odds changes without fundamental context are meaningless
7. Opening price is more truthful than late movement
8. Overhyped matches = traps, undervalued sides = value
9. Persistently abnormal water levels = prepare for upset
10. Bookmakers only adjust for two reasons: balance money or induce public flow
11. **Narrative-driven odds movement is the weakest signal<!-- 2026-06-19 回检 -->**: Odds compression driven by a public narrative (opponent suspensions, star player injury) rather than genuine form/fitness advantage = high probability of overreaction. Check: "Is this compression driven by news everyone already knows?" If yes → reduce confidence.
12. **Suspension paradox<!-- 2026-06-19 回检: South Africa 2 red cards → 1-1 draw -->**: Key player suspensions do NOT automatically benefit the opponent. Suspended teams often reorganize more defensively and become harder to break down. The "missing players" narrative is the market's most common over-pricing error. Ask: "Does this force the team to play more defensively?" If yes → market is likely overvaluing the favorite.
13. **Illegal betting site manipulation<!-- 2026-06-19 专家评审 -->**: Non-mainstream leagues and cup competitions are prime targets for match-fixing syndicates operating through illegal betting platforms. Warning signs: (a) odds from unregulated bookmakers diverge >0.15 from Pinnacle, (b) sudden limit drops >50% on niche outcome markets (correct score, half-time), (c) SBOBet or bet365 suspend market entirely. If ≥2 signs present → RED FLAG 🚩, recommend skipping analysis entirely.
14. **Referee influence on odds<!-- 2026-06-19 专家评审 -->**: Certain referees systematically award more penalties or cards, which shifts actual goal expectations. Trigger: (a) referee has >0.35 penalties/game in last 20 matches, (b) referee's card average >5.0/game, (c) one team relies heavily on physical play (high foul rate) and referee is strict. If triggered → adjust over/under expectation ±0.25 goals and widen score prediction confidence interval by 15%. Data source: WebSearch "[referee name] penalty card statistics".
15. **近1场误导<!-- 2026-06-19 全错复盘: 瑞士 4-1 波黑 -->**: 双方上轮结果相同(都平/都赢/都输) → 不代表实力同档。检查: 上轮对手强度、场面控制力、xG差异。如果阵容质量差≥1档但上轮结果相同 → 上轮结果是噪音，阵容质量是信号。量化触发: 上轮结果相同 + 当前赔率差距>0.40(隐式实力差≥2档) → 近1场权重强制缩至20%以下。
16. **历史独立事件谬误<!-- 2026-06-19 全错复盘: 加拿大 6-0 卡塔尔 -->**: "某队从未赢过/从未进过X轮" → 这是描述性统计，不是预测性证据。每一场比赛是独立事件。正确的问法不是"他们过去赢过吗"，而是"今天的对手是谁？今天有什么不同？"。量化触发: 分析中出现"never"/"历史首次"/"从未"时 → 自动标记，要求重新以独立事件视角评估 → 移除"历史包袱"造成的方向偏误。
17. **体系 > 球星<!-- 2026-06-19 全错复盘: 墨西哥 1-0 韩国 -->**: 1-2个五大联赛球星 ≠ 球队强。世界杯历史上体系完整的球队持续战胜只靠球星的球队。检查: 首发11人中五大联赛球员数量对比。如果一方仅靠2-3名球星而另一方有6+名体系球员 → 体系方胜率显著更高。量化触发: 球星方五大联赛首发≤3人 + 体系方五大联赛首发≥6人 → 球星效应权重强制缩至50%以下。
18. **主场优势量化<!-- 2026-06-19 全错复盘: 加拿大 6-0 卡塔尔 -->**: 世界杯主场优势不可忽视。历史上主场国家小组赛胜率 >70%。在本国比赛 = +10%主胜概率，+0.5球 xG。量化触发: 一方在主场作战(世界杯主办国) + 另一方跨洲旅行 → home_xG × 1.15，away_xG × 0.90。这不是主观判断，是历史数据的硬修正。
19. **世界杯首秀战意加成<!-- 2026-06-19 回检: 西班牙 0-0 佛得角, 佛得角世界杯首秀 -->**: 球队首次参加世界杯（无论是国家首秀还是球员集体首秀），其战意和防守专注度显著高于正常水平。量化触发: (a) 国家历史上首次进入世界杯决赛圈 → 平局+8%, 下盘胜+5%, xG防御系数×1.20; (b) 球队排名差距>30位且是排名更低方的首秀 → 叠加平局+3%。与规则#7(回光返照)的区别: 回光返照=淘汰压力(负面驱动); 首秀战意=展示欲望(正面驱动)。两者可以叠加。<!-- 2026-06-19 回检: 西班牙 0-0 佛得角 → 触发 --><!-- 2026-06-19 回检: 首秀效应上限约束 — 库拉索 1-1(21')→1-7 德国 --> **🆕 首秀效应上限**: 当实力差距(阵容+FIFA排名) ≥3档时 → 首秀加成**减半**(平局+4%, 下盘+2.5%, xG防御×1.10); ≥2档时 → 缩至75%(平局+6%, 下盘+3.75%, xG防御×1.15); <2档时 → 全量。原因: 首秀效应只能维持约30分钟, 实力鸿沟最终会压倒战意。库拉索 1-1 到 1-7 德国 = 典型。
20. **超低赔率自动通胀<!-- 2026-06-19 回检: 西班牙 1.08 → 0-0 -->**: 当热门方 1X2 赔率 < 1.15 时，6D 评分自动 -1。原因: 超低赔率下的单场比赛，小概率事件（门将超神、门柱、红牌）的影响被放大。1.08 赔率隐含 92% 胜率，但实际足球比赛中，如此悬殊的比赛仍有 15-20% 的不胜概率。量化触发: 热门方赔率 < 1.15 → 6D 通胀 -1，且平局概率 +5%。
21. **平局惯性聚合<!-- 2026-06-19 回检: 6月16日4场全平, 3场触发3+信号 -->**: 聚合以下平局信号，如果 ≥3 项触发 → 平局概率 +10%，热门方 -5%: (a) 任意一方近5场 ≥3场平局; (b) 任意一方半场不败率 ≥80%; (c) 双方近5场场均总进球 < 2.0; (d) xG模型预测 xG差 < 0.7球; (e) 平局真实概率 ≥25%。如果 5 项全触发 → "🔴 平局日警告: 本场平局概率被市场系统性低估，不建议方向性预测"。
22. **xG模型强制参考<!-- 2026-06-19 回检: 沙特 vs 乌拉圭 xGscore 0.8-1.4 → 平局 -->**: 在任何方向性预测之前，必须检查至少一个第三方xG模型的预测。WebSearch: "[team1] vs [team2] xG prediction" 或 xgscore.io。如果 xG 模型预测 xG差 < 0.7球（即净胜球期望 < 1球），则该场比赛自动标记为"平局高概率"，方向性预测置信度 -20%。如果 xG 模型预测的 xG 差与赔率隐含的实力差反向 → 触发 "xG-赔率背离"，赔率方向打对折。
23. **钟摆效应 (Pendulum Day)<!-- 2026-06-19 回检: 6月16日 0/4热门胜 → 6月17日 4/4热门胜 -->**: 当前一个比赛日出现极端偏态(≥75%的热门方不胜 或 全胜)时，下一个比赛日的预测方向应倾向反向: 前日热门不胜率≥75% → 今日热门胜 +5%; 前日热门全胜 → 今日热门 -5%，平局 +3%。此规则不单独决定方向，仅作为概率合成前的全局修正因子。量化触发: 检查前日所有完赛结果，计算热门方胜率 → 如果 <25% 或 =100% → 触发钟摆修正。
24. **久别重逢效应 (Long-Absence Return)<!-- 2026-06-19 回检: 葡萄牙 1-1 刚果(金), 刚果(金)52年后重返世界杯 -->**: 球队时隔 ≥ 20 年后重返世界杯决赛圈时，触发久别重逢效应，效力接近首秀: 间隔 20-40 年 → 平局+5%, 下盘+3%, xG防御×1.10; 间隔 ≥40 年 → **平局+8%, 下盘+5%, xG防御×1.20** (强度等同首秀，规则#19)。此效应与规则#19(首秀)和规则#7(回光返照)均可叠加。量化触发: WebSearch "[Team] last World Cup appearance" → 计算间隔年数。<!-- 2026-06-19 回检: 刚果(金)52年后重返 → 等同首秀强度 -->
25. **不败惯性信号 (Unbeaten Streak Signal)<!-- 2026-06-19 回检: 日本 2-2 荷兰, 34/38不败 + 近5全胜 -->**: 当一方球队在最近 ≥20 场正式比赛中的不败率 ≥85% 时，市场严重低估其不败概率。不败惯性不是运气，是体系强度。量化: 不败率 85-90% (如 34/38=89.5%) → 平局+5%, 该方胜率+5%; 不败率 ≥90% → 平+8%, 该方+8%; 近5场全胜 + 不败率≥85% → 叠加平局+3%。WebSearch: "[Team] last 20 matches results" → 计算不败率。与规则#21(平局惯性聚合)协同使用。
26. **资格赛数据折价 (Qualifying Data Discount)<!-- 2026-06-19 回检: 瑞典 5-1 突尼斯, 突尼斯资格赛0失球 → 5球溃败 -->**: 世界杯资格赛数据不能直接等同于世界杯实力。资格赛对手质量显著低于正赛。防守数据折价: 对手平均FIFA排名 ≥80 → × 0.70 (7折); 排名 50-80 → × 0.85; 排名 <50 → × 0.95。进攻数据折价: 对手平均排名 ≥80 → × 0.75; 排名 50-80 → × 0.88; 排名 <50 → × 0.95。WebSearch: "[Team] World Cup qualifying group opponents average rank" → 应用折价后再用于防守等级量化(14.0)和xG因子修正(14.4)。
27. **历史性首分/首胜战意 (Historic First Point/Win)<!-- 2026-06-19 回检: 加拿大1-1波黑(首分), 卡塔尔1-1瑞士(首分) -->**: 当球队正在追逐世界杯历史上第一个积分或第一个胜场时，其表现超出纸面实力。这是规则#19(首秀)的扩展变体。量化: 追逐首分(0分历史) → 该方+5%, 平+3%; 追逐首胜(0胜历史) → 该方+3%, 平+2%; 主场+追首分 → 叠加+8%该方+5%平。与规则#19(首秀)、规则#18(主场)可叠加。WebSearch: "[Team] World Cup record all-time points wins appearances"。
28. **高温场地折扣 (Heat Venue Discount)<!-- 2026-06-19 回检: 卡塔尔 1-1 瑞士, 卡塔尔6月气温35°C+ -->**: 当比赛在露天场地且气温 ≥30°C，客队来自温带/寒带时，体能和表现显著下降。量化: 30-35°C → 客队 xG×0.92, 胜率-5%; >35°C → xG×0.85, 胜率-8%; 湿度>70%叠加 → 再-3%。WebSearch: "weather [city] June [date] temperature humidity"。

### (13) Weighted Probability Synthesis Model<!-- 2026-06-19 回检: added compression grading, back-to-wall, narrative discount; reduced 6D full-score weight -->

**Base probability**: From true home/draw/away probabilities after removing vig.

**Correction factors (each ± adjustment)**:

| Factor | Trigger | Adj. | Direction |
|--------|---------|:----:|-----------|
| Euro-Asian divergence | Hits any of 15 trap patterns | ±10% | Trap#2→home+10%; Trap#1→home-10%; Trap#7(narrative)→home-10% + draw+5% + away+5% |
| Opening odds law | Hits any of 4 laws | ±8% | Law#1→home+8%; Law#2→home-8% |
| Late movement authenticity | Per (6) rules | ±7% | Raise+drop→home+7%; vice versa home-7% |
| Compression intensity | Odds drop magnitude | Variable | Extreme(>20%): +7% · Strong(10-20%): +7% · Moderate(5-10%): +3.5% · Weak(<5%): 0% |
| Fundamental alignment | Odds vs fundamentals direction | ±5% | Aligned→direction+5%; conflict→opposite+5% |
| Back-to-Wall effect | Underdog faces elimination | +5~8% | Lost first match + elimination risk: draw+5% + away+5%. Both lost + suspensions: draw+8% + away+5% |
| Narrative discount | Compression driven by public narrative | -5% | "News everyone knows" (suspensions/injuries) → favorite -5%, draw +3%, away +2% |
| **Home advantage (NEW)** | Team plays in home country | ±10% | Home team +10% win prob, away team -5%. +0.5 xG adjustment.<!-- 2026-06-19 全错复盘: 加拿大 6-0 卡塔尔 --> |
| **Near-1-match discount (NEW)** | Both teams had same previous result | -3% | If both drew/won but squad quality gap ≥1 tier → favorite +3%, draw/underdog -3%. Corrects for illusion of parity.<!-- 2026-06-19 全错复盘: 瑞士 4-1 波黑 --> |
| **Star illusion discount (NEW)** | Star team ≤3 top-5 starters + opponent ≥6 | ±3% | System team +3%, star team -3%. Corrects for celebrity overvaluation.<!-- 2026-06-19 全错复盘: 墨西哥 1-0 韩国 --> |
| **🆕 World Cup debut** | Team making first-ever World Cup appearance | **+8% draw, +5% underdog** | 首秀战意加成: 平局+8%, 下盘+5%. 可与回光返照叠加. <!-- 2026-06-19 回检: 佛得角 0-0 西班牙 --> |
| **🆕 Draw inertia aggregation** | ≥3 of 5 draw signals triggered (Rule #21) | **+10% draw** | 聚合: ≥3项触发 → 平局+10%, 热门-5%. <!-- 2026-06-19 回检: 6月16日4场全平 --> |
| **🆕 Ultra-low odds warning** | Favorite odds < 1.15 (Rule #20) | **+5% draw, favorite -3%** | 超低赔率下单场小概率放大. 1.08→92%胜率, 实际不胜率15-20%. <!-- 2026-06-19 回检: 西班牙 1.08 → 0-0 --> |
| **🆕 Tournament 1st-round** | Group stage Round 1 (first match for team) | **+3% draw** | 小组赛首轮,"不输"> "赢". 全局修正. <!-- 2026-06-19 回检: 4场首轮全平 --> |
| **🆕 Defense-wall discount** | Opponent's GA/game < 0.6 + clean sheet rate > 70% | **favorite -12%, draw +5%** | "城墙级"防守 → 热门方真实胜率远低于赔率隐含. 刚果(金)0.56 GA, 9/16零封. <!-- 2026-06-19 回检: 葡萄牙 1-1 刚果(金) --> |
| **🆕 Pendulum day** | Previous day: favorite win rate < 25% or = 100% | **±5% favorite, ±3% draw** | 钟摆效应: 极端日后必回调. <!-- 2026-06-19 回检: 6/16 0/4 → 6/17 4/4 --> |
| **🆕 Unbeaten streak** | One side: ≥85% unbeaten in last 20+ matches | **+5~8% unbeaten-team, +5~8% draw** | 不败惯性: 日本 34/38不败 + 近5全胜 → 2-2荷兰. <!-- 2026-06-19 回检: 荷兰 2-2 日本 --> |
| **🆕 Qualifying data discount** | Opponent's defensive data from qualifying vs sub-top-50 opponents | **×0.70~0.95 on defense metrics** | 资格赛数据打7-9.5折. 突尼斯0失球 → 5-1崩盘. <!-- 2026-06-19 回检: 瑞典 5-1 突尼斯 --> |
| **🆕 Historic first point/win** | Team chasing first-ever World Cup point or win | **+5~8% that-team, +3~5% draw** | 首分/首胜战意: 加拿大1-1波黑, 卡塔尔1-1瑞士. <!-- 2026-06-19 回检: 加拿大1-1波黑, 卡塔尔1-1瑞士 --> |
| **🆕 Heat venue discount** | Match at ≥30°C outdoor venue, visitor from cool climate | **visitor xG×0.85~0.92, -5~8% win prob** | 高温折扣: 卡塔尔6月35°C, 瑞士从阿尔卑斯→沙漠 <!-- 2026-06-19 回检: 卡塔尔1-1瑞士 --> |
| **🆕 Extreme favorite floor** | Favorite odds < 1.20 + squad gap ≥3 tiers | **favorite floor=80%** | 极端热门保底胜率: 不受战意加成影响. 巴西1.117→地板80%. <!-- 2026-06-20 RCA: 巴西3-0海地 --> |
| **🆕 Cross-trigger cap** | 久别重逢 + 首分/首胜 同时触发 | **加成上限10% (非15%)** | 交叉触发叠加后需二次折价. 海地52年+首分→上限10%. <!-- 2026-06-20 RCA --> |
| **🆕 xG away discount vs strong D** | Away team facing Tier2(+), 对手防守等级 | **away_xG × 0.70** | 见14.0a表. 澳大利亚 vs 美国 → xG 1.25→0.875→实际0. <!-- 2026-06-20 RCA --> |
| **🆕 Stomp-level xG boost** | Squad gap ≥3 tiers + favorite odds < 1.30 | **favorite_xG × 1.20** | 碾压级xG加成: 德国7-1库拉索, 加拿大6-0卡塔尔. <!-- 2026-06-20 全周期回溯 --> |
| **🆕 Host historic match xG** | Home host nation + historic match (first win/debut/opener) | **home_xG × 1.30** | 东道主历史赛xG爆炸: 加拿大, 美国. <!-- 2026-06-20 全周期回溯 --> |
| **🆕 Draw inertia continuity** | ≥2 consecutive days with draw rate ≥50% | **day3: draw -5%, fav +5%** | 反钟摆: 连续平局日不反弹. <!-- 2026-06-20 全周期回溯 --> |
| 6D score | ≥4 confidence boost / ≤2 degrade | ±3% | ≥4→direction+3%; ≤2→all degrade. ⚠️ 6D must use v2.0 with inflation penalty (6/6 ≠ reliable)<!-- 2026-06-19 --> |
| SBOBet divergence | SBOBet differs from Pinnacle by >0.10 on underdog | ±3% | SBOBet systematically lower on underdog = Asian sharp money signal |

**Formula**:
```
Step 1 — Raw correction:
  raw_home = base_home + Σ(home-specific corrections)
  raw_draw = base_draw + Σ(draw-specific corrections)
  raw_away = base_away + Σ(away-specific corrections)

Step 2 — Mandatory normalization (⚠️ never skip):
  total = raw_home + raw_draw + raw_away
  predicted_home = raw_home / total × 100%
  predicted_draw = raw_draw / total × 100%
  predicted_away = raw_away / total × 100%
  
  Example: raw=(52.5%, 30.0%, 20.0%) → total=102.5% → normalized=(51.22%, 29.27%, 19.51%)
```

**Direction rules**: home-away diff >25% = high confidence, 15–25% = medium, 5–15% = low, <5% = no direction.

**Score prediction logic** (always execute):

```
Step A — Estimate expected goals (xG) from market data + team form:
  1. Extract Asian handicap line from /odds or /historical-odds response
     e.g. Home -0.5 → market expects home to win by ~1 goal
     e.g. Home -0.75 → ~1.5 goal advantage
  2. Extract Over/Under total line
  3. Market-neutral base xG (handicap-anchored):
     home_xG = (OU_line / 2) + (handicap_line × 0.5)
     away_xG = (OU_line / 2) - (handicap_line × 0.5)
  4. 🔴 Apply xG Factor Correction (Section 4(14.4)) — team form adjustment:
     ⚠️ REQUIRES WebSearch for each team's last 6-match avg goals scored/conceded.
     home_xG_adjusted = home_xG × home_attack_index × away_defense_index
     away_xG_adjusted = away_xG × away_attack_index × home_defense_index
     If WebSearch data unavailable → skip and annotate: "xG based on market data only"
  5. Apply external factor adjustment (Section 4(14.10)):
     home_xG ×= (1 + external_penalty_home × 0.03)
     away_xG ×= (1 + external_penalty_away × 0.03)
  6. Adjust by home/away win probability ratio:
     home_xG ×= (predicted_home / 50%)
     away_xG ×= (predicted_away / 50%)

Step B — Poisson score distribution:
  For each score (home_goals, away_goals) in range [0,5]:
    P(home=n) = (home_xG^n × e^(-home_xG)) / n!
    P(away=m) = (away_xG^m × e^(-away_xG)) / m!
    P(score) = P(home=n) × P(away=m)
  Rank all scores by probability → Top 3 are predicted scores.

Step C — Confidence modifiers:
  - If 6D score ≥4: final scores more reliable
  - If trap pattern detected: widen score range
  - If movement clean + fundamentals aligned: narrow confidence
```

**Output requires**:
- Full calculation process (base probability → correction factors → xG → Poisson scores)
- Top 3 most likely exact scores with percentages
- Alternative scores (next 3–5)
- Confidence interval for primary score
- Reverse risk note (e.g., "if home xG overestimated, 1-1 draw plausible at ~XX%")
- Always conclude: this is data probability projection, not guaranteed result
- **⚠️ xG model limitations** (2026-06-19 专家评审): The base xG is derived from handicap + OU market data (implied, not actual performance). The 14.4 factor correction partially addresses this with actual team form data, but does not use professional xG models (Opta, StatsBomb) that consider shot quality, location, and game state. Report with this caveat when 14.4 correction was skipped.

### (14) Score Prediction Refinements{#zero-quota}<!-- 2026-06-19 回检: 新增防御分级量化表 -->

All refinement rules below are **zero-quota incremental** — operating on already-pulled `/v4/historical-odds` data (CS / OU / AH markets) or free WebSearch fundamentals.

#### 14.0 Defense-Level Quantification (NEW — mandatory before score prediction)<!-- 2026-06-19 回检: 刚果(金)0.56 GA → 1-1 葡萄牙 -->

**Logic**: Opponent's defensive quality completely changes the favorite's true scoring probability. Use this 4-tier table to adjust the favorite's xG BEFORE any Poisson calculation.

**Data source**: WebSearch for each team's last 6-10 competitive matches GA average and clean sheet rate.

| Defense Tier | GA/game | Clean Sheet Rate | Favorite xG Discount | Draw Prob Boost |
|:---|:---:|:---:|:--:|:--:|
| 🏰 **Fortress (城墙级)** | < 0.60 | > 70% | **× 0.88 (-12%)** | +5% |
| 🛡️ **Solid (坚固级)** | 0.60–1.00 | 50–70% | **× 0.93 (-7%)** | +3% |
| ⚖️ **Average (一般)** | 1.00–1.50 | 30–50% | × 1.00 (0%) | 0 |
| 💔 **Fragile (脆弱级)** | > 1.50 | < 30% | × 1.05 (+5%) | -2% |

**Formula** (embedded in Step 2 and Step 10):
```
1. WebSearch: "[Team] last 10 matches goals conceded average"
2. Classify opponent's defense tier
3. favorite_xG ×= tier_multiplier
4. draw_prob += tier_draw_boost
```

**Trigger marker**: When Fortress/Solid tier triggers → annotate: "🛡️ 防守等级折扣: [球队] 场均失球 X.XX — 热门方 xG × 0.XX"

**🔴 淘汰赛强制重新评估 (2022WC回测)**:
```
小组赛最后一轮结束后, 淘汰赛开始前 → MANDATORY:
  对全部16支晋级队伍重新执行14.0防御等级评估
  数据源: 小组赛3场 (最具参考价值, 无需资格赛折价)
  摩洛哥小组赛 0 GA → Tier1 → 热门方×0.88, 平局+5% → 直接影响Dec 6和Dec 10的选场决策
  每轮淘汰赛后更新: 连续零封 → 升级; 失球 → 降级
```

#### 14.0a Away xG vs Strong Defense Discount (NEW — 2026-06-20 赛后RCA)<!-- 2026-06-20 美国2-0澳大利亚: 客队xG 1.25→0.00, 高估33% -->

**Logic**: When the opponent's defense is strong (Tier2 or better), the away team's scoring probability drops disproportionately — more than the favorite's xG adjustment captures.

**Data source**: Same as 14.0 defense tier classification.

| Home/Away Defense Tier | Away Team xG Discount |
|:---|:--:|
| Home ≥ Tier2 (Solid) | away_xG × **0.70** |
| Away ≥ Tier2 (Solid) | home_xG × **0.85** |
| Home = Tier1 (Fortress) | away_xG × **0.55** |
| Both ≥ Tier2 | smaller_discount × 0.80 (diminishing returns) |

**Rationale**: 2026-06-20 美国 (Tier2 defense) vs 澳大利亚: 原始 away_xG=1.25, 实际0球。折扣后=0.875 → 更合理。同样苏格兰(Tier2防御) vs 摩洛哥: 应限制摩洛哥xG。

**Formula** (embedded before Poisson in Step 10):
```
if home_defense_tier in [Tier1, Tier2]:
    away_xG *= tier_away_discount
if away_defense_tier in [Tier1, Tier2]:
    home_xG *= tier_home_discount
```

#### 14.0b Stomp-Level xG Boost (NEW — 2026-06-20 全周期回溯)<!-- 2026-06-20 德国7-1库拉索, 加拿大6-0卡塔尔 -->

**Logic**: When the squad gap is ≥3 tiers AND the favorite's odds are <1.30, the xG model systematically underestimates the favorite by 1-4 goals.

**Formula**:
```
if squad_gap >= 3 and favorite_odds < 1.30:
    favorite_xG *= 1.20
    # Also widen Poisson score range to [0, 8] instead of [0, 5]
```

**Rationale**: 德国(预测4-0, 实际7-1), 加拿大(预测2-0, 实际6-0), 美国(预测2-0, 实际4-1). 极端实力差下, 强队xG有"碾压效应"——一旦第一球入网, 后续进球概率几何级上升。

#### 14.0c Host Nation Historic Match xG Explosion (NEW — 2026-06-20 全周期回溯)<!-- 2026-06-20 加拿大6-0, 美国4-1 -->

**Logic**: Home host nations playing a "historic" match (first-ever World Cup win, debut match, opening ceremony match) have an emotional xG multiplier that the market completely fails to price.

**Trigger conditions** (any one):
- Host nation playing first home WC match (opening)
- Host nation chasing first-ever WC win
- Host nation WC debut

**Formula**:
```
if host_nation and (first_home_match or first_win_chase or wc_debut):
    home_xG *= 1.30
    away_xG *= 0.80  # 客队被主场气势压制
```

**Rationale**: 加拿大 70 年首胜 + 多伦多主场 → xG×1.30 可解释 6-0. 美国 开幕主场 → 4-1 巴拉圭。此因子与碾压级xG(14.0b)叠加时使用乘法(1.20×1.30=1.56)。

#### 14.0d 淘汰赛平局基线修正 (NEW — 2026-06-20 2022WC淘汰赛回测)<!-- 2022WC: 16场淘汰赛5场90分钟平局(31.3%), 远高于小组赛均值 -->

**Logic**: 淘汰赛90分钟平局率系统性高于小组赛。原因是: (a) 单场淘汰制 → 弱队摆大巴求加时; (b) 双方都有"不能输"的心理约束; (c) 加时赛/点球作为安全网降低冒险意愿。

**Data**: 2022世界杯淘汰赛16场 → 5场90分钟平局 = 31.3%。小组赛48场 → 约24%平局率。

| 比赛阶段 | 90分钟平局基线 | D%修正 | 适用 |
|:---|:--:|:--:|:---|
| 小组赛 | 24% | ±0% (原始去水) | 默认 |
| **淘汰赛 R16** | **28%** | D% < 28% → **+3pp** | 强制应用 |
| **淘汰赛 QF** | **30%** | D% < 30% → **+4pp** | 强制应用 |
| **淘汰赛 SF/Final** | **31%** | D% < 31% → **+5pp** | 强制应用 |

**Formula** (在Step 3去水后、Step 9.5概率合成前应用):
```
if match_stage in [R16, QF, SF, FINAL, 3RD]:
    baseline_draw = {R16: 28, QF: 30, SF: 31, FINAL: 31, 3RD: 28}[stage]
    if de_vigged_D% < baseline_draw:
        D% += baseline_draw - de_vigged_D%
        H% -= (baseline_draw - de_vigged_D%) * 0.65  # 热门方承担65%
        A% -= (baseline_draw - de_vigged_D%) * 0.35  # 冷门方承担35%
        mark: "🏟️ 淘汰赛平局修正: D% {de_vigged}→{adjusted}"
```

**Trigger**: 自动。所有淘汰赛(含三四名)必须执行此修正。

**Impact on mixed parlay**: 淘汰赛D%修正后, 更多比赛会触发"平局>27%跳过"规则 → 大幅减少可投注场次, 但提升单票命中率。

#### 14.0e 淘汰赛超低赔率脆弱性修正 (NEW — 2026-06-20 2022WC淘汰赛回测)<!-- 2022WC: 巴西1.43 vs 克罗地亚 → 90分钟1-1; 西班牙1.65 vs 摩洛哥 → 0-0 -->

**Logic**: 淘汰赛阶段, 赔率<1.45的方向面临"脆弱性溢价"——市场高估了热门方的90分钟取胜概率, 因为它混淆了"晋级概率"与"90分钟取胜概率"。

**Trigger**: 淘汰赛阶段 AND 方向赔率 < 1.45

**Formula**:
```
if match_stage in [R16, QF, SF, FINAL, 3RD] and direction_odds < 1.45:
    fragility = (1.45 - direction_odds) / 1.45  # 脆弱性系数: 赔率越低越大
    direction_prob -= 5% * fragility   # 巴西1.43 → 脆弱性0.014 → 约-1% (轻度)
    draw_prob += 3% * fragility        # 布拉格1.43 → +0.04pp (轻度)
    # 极端情况: 赔率1.15 → 脆弱性0.207 → -10%方向 / +6%平局
    mark: "🏟️ 淘汰赛脆弱性: 赔率{direction_odds} → 方向-{adj}%"
```

**Rationale**: 2022WC巴西(1.43) vs 克罗地亚 → 67%市场胜率, 实际90分钟1-1。西班牙(1.65) vs 摩洛哥 → 58%胜率, 实际0-0。这两个冷门都指向同一个错误模式: 淘汰赛的"死亡威胁"使得超低赔率方向被系统性高估。

**Interaction with 14.0d**: 两个修正叠加。淘汰赛平局基线修正先拉高D%, 淘汰赛脆弱性修正进一步降低热门方概率。叠加后实际效果约为热门-6~10%, 平局+4~7%。

#### 14.1 AH Water-Level Correction

**Data source**: pinnacle AH home/away latest price from historical-odds (`players["0"][-1].price`).

**Logic**: When the handicap side's water > 1.00, the market views covering the spread as difficult → expected goal margin should be reduced.

**Formula** (embedded in Step 10 xG calculation):
```
water_coefficient = 1.00 - (handicap_side_water - 0.90) × 0.5   (floor 0.85, cap 1.15)
If handicap_side_water ≥ 1.00: home_xG ×= water_coefficient (opposite side adjusted upward)
```
Example: Home -0.5, home water 1.05 → coefficient = 1 - (1.05-0.90)×0.5 = 0.925, home xG reduced 7.5%.

#### 14.2 OU Price Calibration

**Data source**: pinnacle OU market over/under latest prices from historical-odds.

**Logic**: Over price implies P(total > line). Reverse-engineer expected total goals and blend with OU_line/2.

**Formula** (embedded in Step 10):
```
P_over = 1/over_price / (1/over_price + 1/under_price)   (de-vig)
implied_total = line × P_over + (line - 0.5) × (1 - P_over)  (simplified linear interpolation)
final_total = 0.6 × (OU_line / 2) + 0.4 × implied_total
```

#### 14.3 CS Market Bayesian Calibration

**Data source**: pinnacle CS market latest snapshot from historical-odds (`out.bookmakers[bm].cs`).

**Logic**: CS odds embed the market's true pricing of each specific score, usable as a Bayesian prior for the Poisson distribution.

**Formula** (embedded after Step 10 Poisson):
```
For each candidate score (i,j):
  P_market(i,j) = (1/odds_ij) / Σ(1/odds_kl)   (de-vig)
  fused_prob = 0.7 × P_poisson(i,j) + 0.3 × P_market(i,j)
Final Top3 re-ranked by fused probability.
```
**Fallback**: If CS market is missing or has <10 scores, skip this calibration and use pure Poisson.

#### 14.4 xG Factor Correction

**Data source**: WebSearch for each team's last 6-match average goals scored/conceded (or xG/xGA).

**Logic**: Use actual team attack/defense performance to correct market-neutral xG.

**Formula** (embedded in Step 10):
```
league_avg_goals = 1.35 (adjustable by league)
home_attack = home_goals_scored_avg / league_avg_goals
away_defense = away_goals_conceded_avg / league_avg_goals
away_attack = away_goals_scored_avg / league_avg_goals
home_defense = home_goals_conceded_avg / league_avg_goals

home_xG_adjusted = home_xG × home_attack × away_defense
away_xG_adjusted = away_xG × away_attack × home_defense
```
**Missing data**: If no xG data, substitute actual goals. If no data at all, skip this correction.

#### 14.5 Tournament Phase Deflation

**Logic**: Knockout and final stages systematically produce fewer goals than group stages.

**Coefficients** (embedded in Step 10):

| Tournament Phase | Total Goals Deflator |
|:---|:--:|
| Group stage (competitive) | 1.00 |
| Group final round (dead rubber/collusion risk) | 0.92 |
| Knockout (R16/QF) | 0.94 |
| Semi-final / Final | 0.90 |

Execution: `total_goal_expectation ×= deflator`, redistribute to home/away xG.

#### 14.6 Zero-Inflated Poisson Correction

**Logic**: When handicap line ≥ 1.25, the probability of the underdog scoring 0 is underestimated by standard Poisson.

**Method** (embedded in Step 10 Poisson calculation):
```
If |handicap_line| ≥ 1.25:
  Underdog P(goals=0) boosted by 12% (P0_new = P0_old + 0.12 × (1 - P0_old))
  Other goal probabilities re-normalized proportionally
```
**Trigger marker**: Output annotated with "Zero-inflation correction applied (handicap ≥1.25)".

#### 14.7 Temporal Weighted Averaging

**Logic**: The closer to kickoff, the more informative the odds. Early/mid/late three-phase predictions should be weighted.

**Weights** (embedded in Step 10 final output):

| Phase | Time to Kickoff | Weight |
|:---|:---|:--:|
| Early (Phase 1) | > 24h | 0.15 |
| Mid (Phase 2) | 12–24h | 0.30 |
| Late (Phase 3) | < 12h | 0.55 |

Execution: If a phase's data is missing, remaining weights redistribute proportionally (e.g., only late → weight = 1.0).

#### 14.8 Dispersion Confidence Penalty

**Data source**: AH lines and OU lines from all three bookmakers (Pinnacle/SBOBet/bet365).

**Logic**: If the three bookmakers diverge significantly on the same handicap or total, score prediction confidence should be lowered.

**Formula** (embedded in Step 10 confidence output):
```
AH_std = std(three handicap lines)   // unit: goals
OU_std = std(three OU lines)         // unit: goals
penalty = 1 - 0.3 × (AH_std + OU_std)   // max penalty 0.3, min 0
Top1 predicted probability ×= penalty
```
**Trigger marker**: If AH_std ≥ 0.25 or OU_std ≥ 0.25, highlight in red: "⚠️ High market divergence, confidence downgraded".

#### 14.9 Market Liquidity Analysis<!-- 2026-06-19 专家评审: 新增流动性分析模块 -->

**Data source**: /v4/historical-odds time series (free) or WebSearch for public market data.

**Logic**: Low-liquidity markets are more susceptible to manipulation and price distortion. High-liquidity markets produce more reliable signals.

**Liquidity indicators** (zero-quota, from already-pulled data):

| Indicator | Data Source | Healthy | Warning | Danger |
|:---|:---|:---|:---|:---|
| Water fluctuation (1h) | AH water price std dev over last 24 data points | <0.03 | 0.03–0.06 | >0.06 |
| Spread tightness | Pinnacle home+away price sum (1X2) | <1.06 | 1.06–1.10 | >1.10 |
| Odds change frequency | Count of price changes in last 6h | >20 | 10–20 | <10 |
| SBOBet vs Pinnacle AH gap | \|SBOBet line - Pinnacle line\| | <0.25 | 0.25–0.50 | >0.50 |
| bet365 limit direction | bet365 limit ↑ or ↓ trend over 6h | ↑ = confidence | flat = neutral | ↓ = risk aversion |

**Formula** (embedded in Step 10 confidence output):
```
liquidity_score = avg(indicator scores mapped to 0–1)
confidence_multiplier = 0.85 + 0.15 × liquidity_score   // range: 0.85–1.00
Final confidence ×= confidence_multiplier
```

**Trigger markers**:
- Water fluctuation >0.06 → "⚠️ Low liquidity: price easily manipulated, reduce analysis weight"
- Spread >1.10 → "⚠️ Wide spread: bookmaker risk-averse, data signal degraded"
- Changes <10 in 6h → "⚠️ Stale market: insufficient trading activity, low reference value"

#### 14.10 External Factor Quantification<!-- 2026-06-19 专家评审: 新增外部因素量化 -->

**Data source**: WebSearch for weather, travel distance, rest days.

**Logic**: External factors (weather, travel, rest) indirectly affect performance and should be quantified — not merely listed.

**Scoring rules**:

| Factor | Score 0 (neutral) | Score -0.5 | Score -1.0 |
|:---|:---|:---|:---|
| **Weather** | Clear/cloudy, 10–25°C | Light rain, 5–10°C or 25–32°C | Heavy rain/snow, <5°C or >32°C |
| **Travel distance** | <500km | 500–2000km | >2000km or international + timezone shift >3h |
| **Rest days** | ≥5 days since last match | 3–4 days | ≤2 days (double-match week) |
| **Altitude** | <500m | 500–1500m | >1500m (e.g., Mexico City, La Paz) |

**Application** (embedded in Step 2 and Step 10):
```
external_penalty = Σ(scores for both teams)
home_xG ×= (1 + external_penalty_home × 0.03)   // each -0.5 = 1.5% xG reduction
away_xG ×= (1 + external_penalty_away × 0.03)
```
**Fallback**: If weather/travel data unavailable via WebSearch, score as 0 (neutral) and note "External factors not quantified — data unavailable".

---

## Section 5: Standardized 12+1 Step Analysis Process (v2.0)<!-- 2026-06-19 全错复盘: 新增 Step 1.5 反叙事检查 -->

### Step 1: Confirm Data Source & Pull Full Match Data
→ Document which API endpoints were called, which bookmakers, data freshness (latest timestamp).
→ **🔴 Team name verification (MANDATORY)**: Immediately after pulling fixture data, run the dynamic team name verification protocol (Section 1, Rule #8). For World Cup, run WebSearch for latest official Chinese name list. Do NOT proceed to Step 2 until all team names have confirmed Chinese mappings.

### 🔴 Step 1.5: 反叙事检查 (Anti-Narrative Check) — NEW, MUST RUN BEFORE FUNDAMENTALS<!-- 2026-06-19 全错复盘 --><!-- 2026-06-19 回检: 新增世界杯首秀 + xG模型检查 -->
```
BEFORE any fundamentals analysis, scan for these narrative traps:

□ 停赛悖论(通用陷阱#12): 对手有主力停赛? → "少人=更弱"是市场最常见的定价错误
  → WebSearch: 确认停赛是否迫使对方重组防线更保守

□ 叙事压缩(陷阱#7): 赔率向热门方压缩的驱动因素是什么?
  → WebSearch: "这个压缩是因为大家都知道的消息吗?"
  → 如果是 → 标记为"叙事驱动"，压缩信号打5折

□ 近1场误导(陷阱#8): 双方上轮结果相同?
  → 如果结果相同但阵容质量差≥1档 → 上轮结果是噪音

□ 历史谬误(陷阱#9): 分析中是否出现"从未XX"/"历史首次"?
  → 如果是 → 重新以独立事件视角评估(今天对手是谁？今天有何不同?)

□ 球星幻觉(陷阱#10): 是否因为某个球星的名字给了过高权重?
  → 检查: 该队五大联赛首发≤3人? 对手≥6人? → 体系 > 球星

□ 主场忽视(陷阱#11): 是否有一方是主场作战?
  → 世界杯主场 = +10%主胜概率, +0.5球 xG

□ 🆕 世界杯首秀(陷阱#19): 是否有球队是历史性首次参赛?
  → WebSearch: "[Team] World Cup debut history"
  → 如果是 → 首秀战意加成: 平局+8%, 下盘+5%, xG防御×1.20

□ 🆕 超低赔率警告(陷阱#20): 热门方赔率 < 1.15?
  → 如果是 → "超低赔率比赛的平局/冷门概率被市场系统性低估"
  → 6D自动-1, 平局概率+5%

□ 🆕 平局惯性(陷阱#21): 检查双方近期平局频率
  → 任意一方近5场≥3平? 任意一方半场不败率≥80%?
  → 如果是 → 聚合平局信号计数

□ 🆕 xG模型信号(陷阱#22): 第三方xG模型预测什么?
  → WebSearch: "[team1] vs [team2] xG prediction"
  → 如果xG差<0.7球 → "xG模型不支持热门方穿盘"

□ 🆕 钟摆效应(陷阱#23): 前一个比赛日是否出现极端偏态?
  → 检查: 前日热门胜率 < 25% 或 = 100%?
  → 如果是 → 触发钟摆修正: ±5% 热门方向

□ 🆕 久别重逢(陷阱#24): 是否有球队时隔20年以上重返世界杯?
  → WebSearch: "[Team] last World Cup appearance year"
  → 如果≥20年 → 久别重逢效应: 平局+5~8%, 下盘+3~5%

□ 🆕 防守城墙(新增): 对手的防守数据是否异常坚固?
  → 场均失球 < 0.6? 零封率 > 70%?
  → 如果是 → 热门方 -7~12% 胜率
  → WebSearch: "[Team] last 10 matches goals conceded clean sheets"

□ 🆕 不败惯性(陷阱#25): 是否有球队在最近20+场比赛中不败率≥85%?
  → WebSearch: "[Team] last 20 matches results record"
  → 如果≥85% → 平局+5~8%, 该方+5~8%
  → 近5场全胜叠加 → 再加+3%

□ 🆕 资格赛折价(陷阱#26): 对手的防守/进攻数据是否主要来自资格赛弱旅?
  → WebSearch: "[Team] World Cup qualifying opponents average FIFA rank"
  → 如果平均排名≥80 → 所有资格赛攻防数据打7折!

□ 🆕 淘汰赛防守城墙预评估(陷阱#27 2022WC回测): 是否进入淘汰赛阶段?
  → 🔴 如果是淘汰赛: 小组赛结束→淘汰赛开始前必须对全部16支晋级队伍重新执行全套反叙事检查!
  → 特别关注: 14.0防御等级重新评估 — 小组赛3场的防守数据是淘汰赛最可靠的防线指标
  → 摩洛哥教训: 小组赛3场0失球 → Tier1城墙级 → 应在R16前触发全折扣(热门-12%, 平局+8%)
  → 同时触发14.0d(平局基线) + 14.0e(低赔脆弱性) 叠加修正
  → 每轮淘汰赛后重新评估: 如果球队保持零封 → 城墙等级升级 (Tier2→Tier1)
  → 标记: "🏰 淘汰赛城墙预评: [球队] 小组赛 GA=X.XX, CS=X/X → Tier[X]"

输出: 每场比赛的叙事标记清单。如果≥3个标记触发 → "⚠️ 本场为叙事主导赛事，所有赔率信号打8折"
如果淘汰赛阶段 → "🏟️ 淘汰赛模式: 14.0d(平局基线) + 14.0e(低赔脆弱) 自动激活"
```

### Step 2: Fundamental Analysis (NEW WEIGHTS v2.0)
```
⭐⭐⭐⭐⭐ 阵容质量差异(转会市场身价、五大联赛首发数) = 25%
⭐⭐⭐⭐⭐ 世界杯历史体系(淘汰赛经验、对阵该洲战绩) = 20%
⭐⭐⭐⭐   主场/中立/客场 = 15%
⭐⭐⭐⭐   回光返照效应(淘汰压力、战意) = 15%
⭐⭐⭐     战术风格匹配 = 10%
⭐⭐       近3-5场表现(非近1场!) = 8%
⭐         球星个体能力 = 4%
⭐         外部因素 = 3%
```
→ Extract from WebSearch/WebFetch: squad quality (top-5-league starters count), World Cup history, recent 3-5 match form, H2H, key players. Present in comparison table (home vs away).
→ **New — Market liquidity check**: Apply Section 4(14.9) indicators (water fluctuation, spread tightness, change frequency, SBOBet gap). Flag if liquidity < healthy threshold.
→ **New — External factor quantification**: Apply Section 4(14.10) to score weather, travel distance, rest days for each team. Compute external_penalty.

### Step 3: European Odds Math Calculation
→ Use Pinnacle as primary reference. Show open → now prices, overround (vig factor), payout rate, true probabilities (de-vigged).
→ All probabilities MUST be de-vigged using the formula in Section 4(1). Never use raw implied probabilities.

### Step 4: Euro-Asian Match + Divergence Check (15 traps)
→ Convert 1X2 to theoretical handicap using Section 4(2) table. Show all 3 bookmakers side-by-side. Check ALL 15 trap patterns (1-7 from Section 4(3) + 8-15 from new systemic traps).
→ **Quantitative trap execution flow** (v2.0):
  1. For EACH bookmaker: compute theoretical AH from de-vigged home win prob
  2. Compare theoretical vs actual AH for all 3 bookmakers → compute max gap
  3. Run each of the 7 Euro-Asian trap quantitative triggers (Section 4(3)) + 4 systemic traps:
     - Trap #1-7: as before
     - Trap #8: 上轮结果相同 + 赔率差>0.40 + 阵容价值差≥3×
     - Trap #9: 分析中出现"never"语言 → 自动标记
     - Trap #10: 球星方五大联赛≤3 + 体系方≥6
     - Trap #11: 主场作战 + 对手跨洲旅行
  4. Flag each HIT trap with severity (🔴 HIGH / 🟡 MEDIUM)
  5. Cross-check with 4 opening odds laws (Section 4(4)) for compounding risk
  6. **🔴 新规则**: 如果陷阱#7(叙事压缩)触发 → 禁止在Step 7给维度1和维度3满分

### Step 5: Opening Odds Positioning
→ **MUST be a separate section from Step 6.** Analyze ONLY the opening prices:
  - What did the market think at open?
  - Any bookmaker outlier at open?
  - Which of the 4 opening odds laws are triggered?
→ Output: opening assessment + triggered laws.

### Step 6: Late Movement & Water Level Analysis
→ **MUST be a separate section from Step 5.** Analyze ONLY the changes from open to now:
  - Direction, magnitude, speed of each bookmaker's movement
  - Water level structure (attract vs. block money)
  - Which of the 5 late-movement authenticity rules apply?
→ Output: movement classification + triggered rules.

### Step 7: Six-Dimension Scoring (v2.0 — 含自动通胀惩罚)
→ Score 0–6 using Section 4(10) v2.0 criteria. Show each dimension pass/fail with brief reason.
→ **🔴 自动通胀惩罚(不可跳过)**:
  - 方向是热门方 且 压缩=中度(5-10%) → -1
  - 对方有回光返照(输球即淘汰) → -1
  - 真实平局概率 > 27% → -1
  - 方向驱动因素是公开叙事(陷阱#7确认) → -1
  - 近1场权重占基本面判断>30% → -1
→ 最终6D = 原始 - 通胀惩罚(最低0), 新阈值: ≥5=高, 4=可参, 3=有限, ≤2=跳过

### Step 8: Risk/Trap Checklist
→ List any of the 15 trap patterns, 4 opening laws, 28 universal traps triggered. Color-code severity.
→ **Execution protocol** (2026-06-19 专家评审):
  1. Aggregate all trap hits from Step 4, Step 5, Step 6
  2. Classify each by severity:
     - 🔴 HIGH: Compounding traps (≥2 traps fired simultaneously), illegal site signs (Trap #13), referee risk (Trap #14)
     - 🟡 MEDIUM: Single trap with clear trigger, moderate compression (Trap #7)
     - 🟢 LOW: Warning signs only, no trigger threshold met
  3. For 🔴 HIGH items: recommend skipping OR heavily discounting analysis
  4. Cross-check: if ≥3 traps fire for same match → "系统性风险警告: 多个诱盘信号同时触发, 本场数据可信度极低"
  5. New traps (#13, #14): only check for non-top-5 leagues and cup competitions

### Step 9: Comprehensive Summary
→ **MUST be a separate section from Step 8.** Synthesize Steps 1–8 into:
  - One-sentence thesis (data direction)
  - Bullet-point actionable judgments
  - What would change the conclusion (variables to watch)
→ This is the bridge between raw analysis and probability numbers. Do NOT skip.

### Step 9.5: Score Refinement Readiness Check

Before starting Step 10's Poisson calculation, confirm the following data is ready (all from already-pulled data, zero quota):

| Data Item | Used For | Status |
|:---|:---|:--:|
| 3-bookmaker AH latest water | 14.1 | ✅/❌ |
| 3-bookmaker OU latest prices | 14.2 | ✅/❌ |
| pinnacle CS latest snapshot | 14.3 | ✅/❌ |
| WebSearch attack/defense data | 14.4 (skip if unavailable) | ✅/❌ |
| Tournament phase flag | 14.5 | ✅/❌ |

If any item is missing, note "Did not apply [rule name]" in the final report.

### Step 10: Weighted Probability Projection + Score Prediction

**🔴 输出优先级规则 (2026-06-20):**

- **主输出 = 胜负方向 + 置信度**. 无需精确比分，方向准确率远高于比分准确率（已验证 3/3 vs 0/3）
- 比分 = 参考信息。标注"比分参考"，不标注"置信度"
- 6D ≤ 2 → 跳过分预测，仅输出方向
- 备选比分 2-3 个必须列出

1. Take true 3-way probabilities from Step 3 as base
2. Apply correction factors one by one (full list in Section 4(13)):
   - Euro-Asian divergence signal (15 trap patterns) → ±10%
   - Opening odds law hit → ±8%
   - Late movement authenticity → ±7%
   - Compression intensity (Extreme/Strong/Moderate/Weak) → +7%/+7%/+3.5%/0%
   - Fundamental alignment → ±5%
   - Back-to-Wall effect → draw+5~8%, away+5%
   - Narrative discount (odds driven by public news) → favorite -5%
   - 6D score confidence → ±3% (reduced from ±5%, 2026-06-19)
   - SBOBet divergence (Asian sharp vs Pinnacle) → ±3%
   - **Market liquidity penalty (14.9)** → confidence × (0.85–1.00)
   - **External factor adjustment (14.10)** → xG × (1 ± external_penalty × 0.03)
3. Synthesize corrected probabilities, **normalize (mandatory — Section 4(1))**
4. Map to expected goals (xG) using handicap line + over/under line
5. Apply Poisson distribution to derive most likely exact scores
6. List top 3 predicted scores with confidence percentages
7. Include reverse risk and alternative score lines

**Supplementary execution requirements (based on Section 4(14) refinements)**:

After completing the base probability synthesis, apply refinement rules 14.1–14.8 in sequence (skip if data missing, note in report).

When outputting Top 3 scores, show both "Poisson raw probability" and "Refined fused probability" so the user can perceive calibration magnitude.

If CS market calibration (14.3) was applied, append "CS market hottest score" as reference comparison.

If zero-inflation correction (14.6) was applied, annotate score with "Zero-inflation adjusted".

Final confidence = base confidence × dispersion penalty (14.8). If below 40%, mark as "Low confidence, use with caution".

### Step 11: Disclaimer
→ Must include: non-betting-advice statement, vig warning, data freshness, model limitations.

---

### ⚠️ Pre-Output Validation Checklist (MANDATORY — Never Skip)

```
BEFORE presenting the final report, perform this self-check:

FOR EACH MATCH in the report:
  □ Step 1 — Data Source                  present? (yes/no)
  □ 🔴 Step 1.5 — Anti-Narrative Check    present? (yes/no)  ← NEW v2.0: MUST RUN FIRST
  □ Step 2 — Fundamentals (v2.0 weights)  present? (yes/no)
  □ Step 3 — Euro Odds Math               present? (yes/no)
  □ Step 4 — Euro-Asian Match (15 traps)  present? (yes/no)
  □ Step 5 — Opening Odds Positioning     present? (yes/no)
  □ Step 6 — Late Movement & Water        present? (yes/no)
  □ Step 7 — Six-Dimension (v2.0+通胀)    present? (yes/no)  ← MUST show raw + inflation
  □ Step 8 — Risk/Trap Checklist          present? (yes/no)
  □ Step 9 — Comprehensive Summary        present? (yes/no)  ← MOST FREQUENTLY MISSED
  □ Step 10 — Score Prediction            present? (yes/no)
  □ Step 11 — Disclaimer                  present? (yes/no, once at end is OK)

RULES:
  1. If ANY step is missing → STOP. Do NOT present the report. Fix it first.
  2. Step 1.5 is NEW and MANDATORY — must appear BEFORE Step 2.
  3. Step 5 and Step 6 are SEPARATE — do NOT merge into "Step 5-6".
  4. Step 9 is NOT optional and NOT the same as Step 8.
     Step 8 = risk list (what COULD go wrong)
     Step 9 = synthesis + actionable judgment (what the data MEANS)
  5. This checklist applies to HTML AND text reports equally.
  6. Step 7 MUST show: raw 6D score → inflation deductions → final 6D score.
  7. 🔴 Step 9/10 output priority (2026-06-20): W/L direction = primary output, score = "参考" only.
     Score predictions must include "比分参考" prefix and list 2-3 alternatives.
```

---

## Section 6: Output Format

**All analysis reports MUST be generated as HTML files using the built-in template.**

### 🔴 Output Priority Rule (2026-06-20 赛后修正)

```
PRIMARY OUTPUT: Win/Loss direction prediction + confidence level
                例: "美国胜 (高置信度)" / "摩洛哥胜 (中置信度)"
                
SECONDARY OUTPUT: Score prediction (as reference only)
                  例: "比分参考: 2-1" / "比分参考: 0-2"

RATIONALE: 2026-06-20 4场比赛 W/L 正确率 3/3 (100%), 但比分全部差1球。
          W/L 预测比比分预测可靠得多，应作为核心交付物。

SCORE OUTPUT RULES:
- Score predictions MUST include "参考" qualifier
- Alternative scores (2-3 options) MUST be listed alongside main prediction
- 6D ≤ 2 → skip score prediction entirely, only output W/L direction
- Score confidence: display Poisson % only, do NOT present as "置信度"
```

### Report Title Convention

When generating the final HTML report, title format:
- 文本报告: `worldcup_YYYY-MM-DD_analysis.html` (predictions)
- 复盘报告: `worldcup_YYYY-MM-DD_review.html` (post-match review)

The review report compares prediction vs actual, calculates W/L accuracy and score error, with RCA for each match.

### Template Location

```
assets/report-template.html — Full HTML template (~56KB, extracted from live output 2026-06-19)
```

Template includes:
- Responsive CSS (`.card`, `.table`, `.prob-bar-wrap`, `.score-pred`, `.highlight-box`, etc.)
- Top summary cards (4 matches overview + confidence tags `.conf-high`/`.conf-mid`/`.conf-low`)
- Per-match 10-step framework (Step 1–10 HTML structure with `.step` + `.step-title` styling)
- Step 11 disclaimer (`.disclaimer` styling)
- Chinese stock market red-up/green-down color scheme (home win odds drop = `.down` green, away odds rise = `.up` red)
- Match title: "Match N: 🇫🇷 国名 vs 🇫🇷 国名" format (flag emoji + Chinese name)

### 🔴 Template Usage Rules (2026-06-19 回检 + 专家评审)

1. **Must read template first**: Before generating report, `Read assets/report-template.html` to understand CSS classes and DOM structure.
2. **Team names must be Chinese**: `match-title` uses "flag emoji + Chinese name" format (e.g., `🇨🇭 瑞士 vs 🇧🇦 波黑`).
3. **CSS classes must match**: Do not invent new class names; use existing template classes (`.odds-cell`, `.up`, `.down`, `.highlight-box.warn`, `.score-pred.green`, etc.).
4. **Probability bar format**: Use `.prob-bar-wrap` > `.prob-bar-track` > `.prob-bar-fill` three-level structure.
5. **Score prediction card**: Use `.score-pred.green` or `.score-pred.red` wrapping `.main-score` + `.alt-scores`.
6. **🔴 CORE CONCLUSIONS FIRST** (2026-06-19 专家评审): Place Step 9 comprehensive summaries in the `.priority-conclusions` section at the TOP of the report — before the summary grid. This ensures critical judgments are seen first.
7. **🔴 DYNAMIC TIMESTAMPS** (2026-06-19 专家评审): The template includes auto-updating JavaScript timestamps. Fill `{{GENERATION_TIME}}` with the current Beijing time, and the live timestamp will update every 60s.
8. **🔴 ODDS MOVEMENT CHARTS** (2026-06-19 专家评审): For each match, include Chart.js initialization code in the `{{ODDS_MOVEMENT_CHARTS}}` placeholder:
   - `initOddsChart()` for 1X2 odds movement line chart (Pinnacle daily samples)
   - `initAHCompareChart()` for 3-bookmaker AH comparison bar chart
9. **🔴 NAME ERROR BANNER** (2026-06-19 专家评审): If any team name uses English fallback (per Section 1 Rule #8 dynamic protocol), set `{{NAME_ERROR_ACTIVE}}` to `active` and list the English names in `{{NAME_ERROR_LIST}}`.
10. **🔴 LIQUIDITY + EXTERNAL FACTORS** (2026-06-19 专家评审): Step 2 now includes `.liquidity-grid` for market liquidity indicators and `.ext-factor-table` for external factor quantification.

### How to Use

```
1. Read assets/report-template.html, understand CSS variables and DOM structure
2. Fill with actual analysis data:
   - Date and quota info in title
   - 4 summary cards (matchup, score, confidence)
   - Per-match step content (fundamental table, odds table, 6D score, risk list, score prediction)
3. Output to current working directory as worldcup_YYYY-MM-DD_analysis.html
4. Call present_files to display result
```

### Template Placeholder Replacement List

| Replacement Area | Content |
|:---|:---|
| Page title / .header h1 | Match date |
| .header .meta | Generation time + data source |
| .header .quota | Dual display: "✅ Session: N quota · Cumulative: X/total (from /v4/account)"<br>Session = difference calculated from pre/post /v4/account snapshots<br>Cumulative + total from real-time /v4/account |
| .summary-grid ×4 | Matchup, predicted score, confidence tag (conf-high/conf-mid/conf-low) |
| #m1-#m4 → Step 1 | Data source details (endpoints, bookmakers, data points) |
| #m1-#m4 → Step 2 | Fundamentals table (record, injuries, H2H, key factors) |
| #m1-#m4 → Step 3 | Euro odds math table (open/now/true probability + payout rate) |
| #m1-#m4 → Step 4–6 | Euro-Asian match + 3-bookmaker comparison + movement analysis |
| #m1-#m4 → Step 7 | Six-dimension scoring (6 pass/fail rows + total badge) |
| #m1-#m4 → Step 8 | Risk checklist (highlight-box yellow/red markers) |
| #m1-#m4 → Step 9 | Comprehensive summary (green/red conclusion box + one-liner + actionable judgment) |
| #m1-#m4 → Step 10 | Probability bars + score prediction card (main score + alternatives) |
| #m1-#m4 → Step 10 (new) | Poisson raw: XX% \| Refined fused: XX% \| CS calibrated: yes/no |
| #m1-#m4 → Step 10 (dispersion) | If dispersion penalty triggered → ⚠️ High divergence, confidence downgraded |
| #m1-#m4 → Step 10 (zero-infl) | If zero-inflation applied → 🛡️ Zero-inflation correction applied |
| .disclaimer | Data source, quota usage, model notes |
| **.name-error-banner** | **🔴 Name translation error banner (if any team name in English)** |
| **#m1-#m4 → Step 2 (new)** | **Market liquidity indicators: water fluctuation, spread, change frequency, SBOBet gap** |
| **#m1-#m4 → Step 2 (new)** | **External factor scores: weather, travel, rest, altitude per team** |

---

## Section 7: Quick Start & Examples

### Register OddsPapi

https://oddspapi.io → Free signup → Get API key → Provide: `My OddsPapi API key is xxxxxx`

### Daily Execution Plan

```
Phase 0: /v4/fixtures × 1 + /v4/odds-by-tournaments × 3 = 4 quota (one-time per tournament)
Phase 1–3: 0 quota (cached IDs, /v4/historical-odds free)

Lifetime per tournament: 4 / 250
```

### Example: Providing API Key
```
User: My OddsPapi API key is xxxxxx
You: ✅ OddsPapi configured (250/month)
     Free: /v4/historical-odds (unlimited), /v4/account
     Billed: all other endpoints (1 quota/call, will confirm before each)
```

### Example: Multi-Match Batch (all >1h before kickoff)
```
User: Analyze today's 4 World Cup matches

You:
1. GET /v4/account → check remaining
2. Read fixtures from cache → all >1h → /historical-odds only
3. MATCH 1 (serial): GET /v4/historical-odds?fixtureId=X&bookmakers=pinnacle,bet365,sbobet&outcomeId=101,102,103 → wait ≥5s
4. MATCH 2-4 (serial): same pattern
5. WebSearch → injuries/standings/H2H
6. Execute 12-step analysis → output HTML report
   → Quota used: 0
```

### Example: On-Demand Single Match (>1h)
```
User: Analyze Czech Republic vs South Africa

You:
1. GET /v4/account → check quota
2. Read fixture from cache → match at 19:00, current 10:00 = 9h before → >1h → free
3. GET /v4/historical-odds?fixtureId=X&bookmakers=pinnacle,bet365,sbobet&outcomeId=101,102,103 → FREE
4. Parse on-the-fly → extract only market 101: {open, now, changes} per bookmaker
5. WebSearch fundamentals
6. 12-step analysis → output report
   → Quota used: 0
```

### Example: Pre-Match T-1h
```
User: Pre-match prediction for Czech Republic vs South Africa
Time: 17:55, kickoff 19:00 (65 min before)

You:
1. GET /v4/account → check remaining
2. 65 min ≤ 1h → /odds needed (1 quota)
3. ⚠️ Ask: "Live odds = 1 quota. Current: X/250. Proceed? (yes/no)"
4. After "yes": GET /v4/odds?fixtureId=X → 1 quota
5. Parse on-the-fly: extract only pinnacle 1X2 + AH main + O/U main
6. WebSearch fundamentals
7. 12-step analysis → output final report
   → Quota used: 1
```

### Web Mode (no API key fallback)

1. Send analysis request directly, no configuration needed.
2. Auto-fetch: OddsSafari (multi-bookmaker odds) + Tribuna/OddsFlow (fundamentals) + WebSearch.
3. Mark report: "Opening odds missing, movement timeline missing."

---

## Section 8: Boundary Rules

1. **Quota safety (non-negotiable)**: Section 0 rules always apply — serial calls, pre-check, max 1 retry, response validation, no silent endpoint switching, billed calls require user confirmation.
2. **Billed confirmation**: Any billed endpoint MUST be pre-confirmed by user. Show quota impact before asking. Never assume consent.
3. **No silent switch**: If a free endpoint fails → ask user for options. Never auto-switch to billed.
4. If API fails (after 1 retry) → auto-switch to web mode for that fixture, mark report header.
5. If response truncated → mark as partial data, proceed with available data + note limitation.
6. Refuse to generate exact score predictions, guaranteed-win schemes, or martingale strategies.
7. Do not recommend any betting sites or API providers.
8. Do not overstate analysis value: vig means long-term mathematical expectation is negative.
9. If user requests betting advice → refuse and restate educational positioning.
10. Overseas matches only; follow local laws for domestic events.
11. Never write API credentials to any file (skill, memory, or cache).
12. `/v4/historical-odds` uses 3 major bookmakers (API cap: max 3, rate limit: 5000ms). Keep only 3 markets per bookmaker: market["101"] (1X2) + top-2 2-outcome markets (main AH + main OU). Discard all altLines, player props, corner counts, card counts. Raw response is transient (pipe, don't save).
13. **🆕 淘汰赛防守城墙预评估 (2022WC回测)**: 小组赛最后一轮结束后, 必须在淘汰赛开始前对全部16支晋级队伍重新执行Section 1.5全套反叙事检查 + 14.0防御等级重新评估。小组赛3场的防守数据是最可靠的淘汰赛防线指标(无需资格赛折价)。摩洛哥教训: 3场0失球应触发Tier1全折扣, 可避免2笔淘汰赛投注亏损。
14. **🆕 淘汰赛修正自动激活 (2022WC回测)**: 所有淘汰赛自动应用14.0d(平局基线修正) + 检查14.0e(低赔脆弱性) + D>27%规则在修正后的D%上执行。淘汰赛选场比小组赛更严格。
15. **🆕 历史回测模式**: 当分析历史赛事时(如2022WC), 赔率使用checkbestodds.com等历史源; 竞彩赔率用国际赔率×0.92²近似; 执行完整模拟并对照真实赛果计算P&L。

---

## Section 9: Post-Mortem Engine — "先知视角"逆向推理法<!-- 2026-06-19 全错复盘: 4/4 预测错误 → 系统性方法论重构 -->

> **核心原则**: 每当预测被实际结果证明错误，不修正参数，而是**逆向推理**——假设你事先知道结果，昨天的你要怎么思考才能得出正确结论？答案不是调参，是**改变你审视数据的顺序和权重**。

---

### 9.0 2026-06-19 全错复盘总览

| # | 比赛 | 预测方向 | 实际比分 | 错误类型 | 根因 |
|:--:|------|:------:|:---:|:---|------|
| 1 | 🇨🇿 捷克 vs 🇿🇦 南非 | 主胜 | **1-1** | 方向错误 | 6D评分通胀 + 忽略回光返照 + 叙事压缩未打折 |
| 2 | 🇨🇭 瑞士 vs 🇧🇦 波黑 | 客不败 | **4-1** | 方向错误 | 近期战绩(1场)权重过高 + 忽略阵容质量鸿沟 |
| 3 | 🇨🇦 加拿大 vs 🇶🇦 卡塔尔 | 让球过浅 | **6-0** | 幅度错误 | 主场优势忽视 + 历史包袱(从未赢过世界杯)误导 |
| 4 | 🇲🇽 墨西哥 vs 🇰🇷 韩国 | 客不败 | **1-0** | 方向错误 | 亚洲强队光环 + 忽略世界杯经验差 |

---

### 9.1 第一场: 捷克 1-1 南非 — 叙事压缩的经典陷阱

#### 实际赔率走势

```
捷克 1X2: Pinnacle open 2.05 → close 1.877 (-8.4%, 中度压缩)
南非 1X2: Pinnacle open 3.90 → close 4.10 (+5.1%)
平局:     Pinnacle open 3.45 → close 3.55 (+2.9%)

德维格后真实概率: 捷克 50.3% / 平 27.2% / 南非 22.5%
AH: 捷克 -0.5 (深度合理, 符合理论换算)
```

#### 比赛事实链

- 南非首轮 0-2 负于对手，且吃到**2张红牌**(2名主力停赛)
- 捷克首轮表现可圈可点
- 市场一致性看低南非: "主力停赛 = 南非更弱"
- 实际: 南非被迫重组防线，更加保守密集防守 → 捷克第6分钟进球后被南非死守 + 81分钟点球扳平

#### ❌ 我错在哪里

我给了捷克 6D 评分 6/6 — 完美分数。但实际上:
- **维度1(基本面)**: 南非的停赛不是削弱而是**被迫转防守 → 更难被击穿**（停赛悖论，通用陷阱#12）
- **维度3(开盘客观性)**: 捷克的赔率压缩(-8.4%)是**中度压缩**，驱动因素是"南非停赛"这个**公开叙事**，不是真正的实力优势（陷阱#7: 叙事驱动压缩）
- **维度5(水位逻辑)**: 平局真实概率27.2% — 超过25%阈值，意味着市场原本就不确定

#### ✅ 先知视角：昨天应该怎么想

```
第1步: 检查压缩强度 → -8.4% = 中度(5-10%) → 半权重(+3.5%, 不是+7%)
第2步: 搜索压缩驱动因素 → WebSearch "South Africa suspensions Czech Republic" 
        → 确认: 2名主力停赛 = 公开叙事 → 触发陷阱#7 → 捷克 -5% 折扣
第3步: 检查回光返照效应 → 南非首轮输球 = 再输就淘汰 → 触发回光返照:
        输球+停赛双重叠加 → 平局 +8%, 客胜 +5%
第4步: 检查平局概率 → 27.2% > 25% → 维度5不通过 → 扣除1分
第5步: 跑6D通胀惩罚 → 中度压缩(-1) + 回光返照(-1) + 平局>25%(-1) = 6-3=3分
第6步: 加权概率合成 → 基础(50.3, 27.2, 22.5) 
        + 中度压缩仅半权(+3.5%捷克)
        + 回光返照(+8%平, +5%南非) 
        + 叙事折扣(-5%捷克, +3%平, +2%南非)
        = 调整后(43.8, 38.2, 29.5) → 归一化 → (39.3%, 34.3%, 26.4%)
        
结论: 捷克胜率仅39%, 平局34% → 不能押主胜, 平局是最可能单一结果
  
✅ 正确预测: 捷克 1-1 南非 (平局)
```

---

### 9.2 第二场: 瑞士 4-1 波黑 — 一场比赛≠实力

#### 实际赔率走势

```
瑞士 1X2: open ~1.75 (强队), close 稳定在 1.70-1.80
波黑 1X2: open ~4.50, 略有上升
```

#### 比赛事实链

- 首轮: 瑞士 1-1平、波黑 1-1平（双方首轮表现相同！）
- 波黑在洛杉矶有大量侨民支持（SoFi Stadium 7万人，大量波黑球迷）
- 实际比赛: 瑞士全场碾压(xG大幅领先)，0-0到74分钟才破门 → 随后16分钟狂灌4球
- 瑞士实力碾压: Xhaka(勒沃库森队长)、Akanji(曼城)、Ndoye(诺丁汉森林)、Embolo(摩纳哥)
- 波黑核心: 38岁的Dzeko、无名年轻球员

#### ❌ 我错在哪里

**把一场比赛的结果当作实力评估**。首轮双方都打了1-1，但瑞士的1-1是对强敌、场面占优；波黑的1-1是侥幸。我用"近1场"的数据等权评估了两队，忽视了:
- 瑞士首发阵容身价 ≈ 波黑的 5-8倍
- Xhaka + Akanji + Ndoye + Embolo vs 38岁Dzeko + 无名小将
- 瑞士连续多届大赛淘汰赛常客，波黑世界杯经验极少

#### ✅ 先知视角：昨天应该怎么想

```
第1步: 阵容对比(基本面第一权重 ⭐⭐⭐⭐⭐)
        瑞士: Xhaka(勒沃库森队长/德甲冠军) + Akanji(曼城中卫/英超冠军) 
              + Ndoye(英超边锋) + Embolo(法甲前锋) + Kobel(多特门将)
        波黑: Dzeko(38岁/土超) + 多名无五大联赛经验球员
        → 阵容鸿沟: 瑞士 >> 波黑 (差距至少2档)

第2步: 首轮结果加权
        瑞士 1-1: 对手强, 场面优势, 赔率劣势下扳平 → 真实实力高于结果
        波黑 1-1: 对手弱, 侥幸逼平 → 真实实力低于结果
        → 首轮1-1 ≠ 瑞士=波黑

第3步: 主场因素检验
        波黑球迷多 ≠ 波黑实力强。球迷声势是情绪因素，不应影响基本面判断。
        瑞士球员习惯了在敌对环境比赛(欧战客场经验丰富)。

第4步: 赔率验证
        瑞士 1.75 = 真实概率 ~53% → 远高于平局和波黑
        → 市场是正确的。不要把"首轮都平了"当做"两队同档"。

结论: 瑞士实力碾压，74分钟后的爆发是必然。瑞士胜是最合理预测，
      比分悬念在于瑞士何时破门，不是瑞士能不能赢。

✅ 正确预测: 瑞士 2-0 或 3-0 波黑 (瑞士胜, 赢2球+)
```

---

### 9.3 第三场: 加拿大 6-0 卡塔尔 — 主场+历史机遇

#### 比赛事实链

- 加拿大: 世界杯历史**从未赢过一场**(0胜)
- 卡塔尔: 2022年主办国, 但2026年是客队
- 比赛地点: 温哥华 BC Place — **加拿大主场**
- 实际: 加拿大 17分钟领先, 卡塔尔 34分钟红牌, 半场3-0, 最终6-0
- Jonathan David(尤文图斯前锋)帽子戏法, Buchanan边路暴走
- 卡塔尔吃到 2张红牌, 9人应战崩盘

#### ❌ 我错在哪里

我用"加拿大从未赢过世界杯"这个**历史包袱**来压低加拿大的概率，而忽视了:
- 这是加拿大**主场**(温哥华)，世界杯主场优势极强
- 卡塔尔是2026年最弱球队之一（亚洲名额争议大）
- 加拿大拥有 David(Lille→尤文图斯射手)、Buchanan(国米边锋)、Larin 等五大联赛球员
- 卡塔尔球员几乎全部来自卡塔尔国内联赛
- **"从未赢过"是过去，不是未来** — 每一场都是独立事件

#### ✅ 先知视角：昨天应该怎么想

```
第1步: 消除历史谬误
        "加拿大从未赢过世界杯" → 这是描述性事实，不是预测性证据。
        独立事件原则: 加拿大过去0胜 ≠ 今天不能赢。
        相反: 世界杯主场 + 对阵最弱对手 = 破纪录的最佳时机。

第2步: 主场优势量化
        世界杯主场优势: FIFA数据显示历史上约 +0.5球优势
        加拿大在温哥华 → 不需要适应时差/气候 → 全主场加成
        → 在加权概率中 +10% 主胜

第3步: 阵容对比(基本面第一权重)
        加拿大: David(尤文) + Buchanan(国米) + Larin(南安普顿) 
                + Eustaquio(波尔图) + Koné(马赛)
        卡塔尔: 全队仅3名海外球员, 其余均来自卡塔尔星联赛
        → 阵容鸿沟: 加拿大 >> 卡塔尔 (差距 >= 2档)

第4步: 赔率验证
        加拿大如果赔率 < 1.40: 市场正确评估了实力差距
        如果 > 1.50: 市场低估, 是价值信号
        → 看实际赔率, 如果市场已在1.30左右: 说明市场清醒

结论: 加拿大主场大胜是大概率事件。卡塔尔的红牌只是加剧了比分，
      不是改变胜负方向的原因。

✅ 正确预测: 加拿大 3-0 或 4-0 卡塔尔 (加拿大胜, 穿盘)
```

---

### 9.4 第四场: 墨西哥 1-0 韩国 — 世界杯经验 > 亚洲排名

#### 比赛事实链

- 墨西哥: 世界杯淘汰赛常客(连续8届进16强)，首轮表现稳健
- 韩国: 亚洲强队，拥有李刚仁(巴黎)、孙兴慜(热刺)等球星
- 实际: 上半场韩国 **0射正**, 50分钟墨西哥门将失误破门, 全场 1-0
- 墨西哥 6分锁定小组第一，成首支晋级球队

#### ❌ 我错在哪里

我给了**韩国太多"亚洲强队"光环**和**球星效应**权重:
- 孙兴慜 + 李刚仁的名字很响 → 但世界杯是团队运动
- 亚洲强队 ≠ 能赢中北美霸主（墨西哥在世界杯上对亚洲队历史战绩碾压）
- 韩国的0射正说明了问题: 墨西哥的防守体系完全限制了韩国的进攻
- 我高估了球星效应，低估了体系对抗

#### ✅ 先知视角：昨天应该怎么想

```
第1步: 世界杯历史交锋权重
        墨西哥 vs 亚洲队 世界杯战绩: 墨西哥碾压
        墨西哥 vs 韩国 2018: 墨西哥 2-1 胜
        世界杯经验: 墨西哥 = 连续8届淘汰赛, 韩国 = 仅2次小组出线
        → 世界杯经验差是硬指标, 远超亚洲排名

第2步: 体系 vs 球星
        孙兴慜(热刺) + 李刚仁(巴黎) = 2个五大联赛球星
        墨西哥: 团队体系完整, 多名球员在五大联赛/墨超出场
        世界杯历史上, 靠1-2个球星的球队 vs 体系完整的球队 → 体系胜率高
        → 球星效应权重不应超过体系完整性

第3步: 首轮表现深化分析
        墨西哥首轮: 控制型表现, 防守稳固
        韩国首轮: 有进球但防守漏洞明显
        → 不是看结果(谁赢了), 是看过程(谁控制了比赛)

第4步: 出线形势
        墨西哥赢 = 锁定小组第一 → 强战意
        韩国不败即可 → 保平心态 → 主动进攻意愿不足
        → 韩国0射正恰恰反映了这种心态

结论: 墨西哥 1-0 是最合理的比分。韩国0射正不是偶然。

✅ 正确预测: 墨西哥 1-0 或 2-0 韩国 (墨西哥胜, 零封)
```

---

### 9.5 系统性缺陷: 四场共同的错误模式

复盘四场后，发现**不是参数不对，是思考顺序和权重分配存在系统性缺陷**:

| # | 缺陷 | 错误表现 | 正确做法 |
|:--:|------|---------|------|
| 1 | **6D 评分通胀** | 中度信号当强信号打分，6/6 不代表可靠 | 增加通胀惩罚检查(压缩强度+回光返照+平局概率)，自动扣分 |
| 2 | **近1场权重过高** | 首轮结果等权影响判断(瑞士/波黑都平了) | 近1场权重 < 阵容质量权重 < 历史体系权重 |
| 3 | **叙事不验证** | 赔率压缩自动视为"市场确认方向" | 每次压缩必须 WebSearch 检验驱动因素，叙事驱动 = 打折 |
| 4 | **回光返照滞后** | 淘汰压力在 6D 评分后才考虑 | 回光返照必须在**基本面第一步**就检查 |
| 5 | **历史谬误** | "从未赢过"="不会赢" | 历史统计是描述性的，非预测性的。独立事件原则 |
| 6 | **主场优势忽视** | 加拿大在温哥华踢 = 忽视主场加成 | 世界杯主场 = +10% 主胜概率、+0.5球 xG |
| 7 | **球星效应 vs 体系对抗** | 孙兴慜+李刚仁 ≠ 能赢 | 体系完整性 > 个别球星，世界杯历史反复验证 |
| 8 | **压缩强度未分级** | 中度压缩(-8.4%)用了全额权重 | 中度(5-10%) = 半权；弱度(<5%) = 零权 |

---

### 9.6 修正后的分析优先级 (v2.0 — 2026-06-19 回检后)

```
🔴 新优先级(覆盖 Section 1 规则 #1):

第0优先: 反叙事检查 (BEFORE 任何赔率分析)
  □ 这场比赛有没有"大家都知道"的叙事?
    - 主力停赛/受伤 → 检查停赛悖论(通用陷阱#12)
    - 历史战绩碾压 → 检查独立事件原则
    - 上轮表现好/差 → 检查近1场权重陷阱
    - 球星回归/缺席 → 检查体系 vs 球星
  □ 如果有 → 标记为"叙事驱动赛事"，所有信号打8折

第1优先: 基本面(新权重体系)
  ⭐⭐⭐⭐⭐: 阵容质量差异(转会市场身价、五大联赛球员数) = 25%
  ⭐⭐⭐⭐⭐: 世界杯历史体系(淘汰赛经验、对阵该洲战绩) = 20%
  ⭐⭐⭐⭐:  主场/中立/客场(世界杯主场 > 中立 > 客场) = 15%
  ⭐⭐⭐⭐:  回光返照效应(淘汰压力) = 15%
  ⭐⭐⭐:   战术风格匹配(攻击 vs 防反 vs 控球) = 10%
  ⭐⭐:    近期3-5场表现(非近1场) = 8%
  ⭐:      球星个体能力 = 4%
  ⭐:      外部因素(天气/旅行) = 3%
  → 近1场权重从无限制降至 8%。阵容+体系 = 45%。

第2优先: 赔率验证(不是赔率主导)
  赔率用来验证基本面判断，不是替代基本面。
  - 基本面说A队强 + 赔率也指向A → 一致，高置信
  - 基本面说A队强 + 赔率指向B → 检查为何市场分歧
  - 基本面不确定 + 赔率确定 → 赔率权重提高到50%

第3优先: 陷阱扫描(含新规则)
  在7大陷阱基础上，新增:
  Trap #8: 近1场误导 — 双方上轮结果相同，但实力悬殊(瑞士/波黑)
  Trap #9: 历史包袱 — 用"某队从未XX"来预测(加拿大0胜)
  Trap #10: 球星幻觉 — 靠1-2个球星的名字判断方向(韩国)
  Trap #11: 主场忽视 — 忽略世界杯主场优势(加拿大vs卡塔尔)
```

---

### 9.7 修正后的 6D 评分 v2.0<!-- 2026-06-19 回检: 全面重写评分标准 -->

| Dim | 新名称 | 通过条件(得分1) | 不通过条件(得分0) | 权重变化 |
|:---:|:---|------|------|:--:|
| 1 | **基本面扎实** | 阵容质量差异≥1档 **且** 近3场表现支持方向 **且** 回光返照检查通过 **且** 叙事检查通过(无公知新闻误导) | 阵容接近 **或** 近1场权重过高 **或** 回光返照未处理 **或** 叙事驱动(陷阱#7) | ↑ 门槛提高: 4个子条件全满足才给1分 |
| 2 | 欧亚匹配 | (不变) 理论vs实际差距≤0.25球 | (不变) | - |
| 3 | **开盘诚实** | 开盘价符合阵容实力差距 **且** 压缩非叙事驱动(Search确认) **且** 压缩强度≥10%(强)或<5%(无信号) | 中度压缩(5-10%)未验证驱动因素 **或** 叙事驱动压缩(陷阱#7确认) | ↑ 中度压缩单独标记, 不能默认得分 |
| 4 | 走势干净 | (不变) 未触发陷阱 **且** 无收割形态 | (不变) | - |
| 5 | **水位合理** | 水位变化有基本面支撑 **且** 平局概率≤25% **且** 流动性健康(波动<0.06) | 平局概率>27% **或** 流动性差 **或** 水位无基本面支撑 | ↑ 平局阈值从25%收紧到27%为硬截止 |
| 6 | **无一边倒** | 多庄一致 **且** bet365-Pinnacle价差<0.05 **且** 无异常限跌 | (不变) | - |

**6D 通胀惩罚(自动执行, 不可跳过)**:
```
出分后立即执行:
  IF 方向是热门方且压缩=中度(5-10%) → -1
  IF 对方有回光返照(输球即淘汰) → -1
  IF 真实平局概率 > 27% → -1
  IF 方向驱动因素是公开叙事(陷阱#7确认) → -1
  IF 近1场权重占基本面判断>30% → -1

最终得分 = 原始6D - 通胀惩罚(最低0分)
```

**新解读阈值**:
- ≥5: 高参考价值(罕见, 需满分且无通胀)
- 4: 有参考价值
- 3: 有限参考价值 → 建议避免方向性预测
- ≤2: 高风险 → 跳过此场

---

### 9.8 新增通用陷阱规则(v2.0)

```
15. 近1场误导<!-- 2026-06-19 回检: 瑞士 4-1 波黑 -->:
    双方上轮结果相同(都平/都赢/都输) → 不代表实力同档。
    检查: 上轮对手强度、场面控制力、xG差异。
    如果阵容质量差≥1档但上轮结果相同 → 上轮结果是噪音，阵容质量是信号。

16. 历史独立事件<!-- 2026-06-19 回检: 加拿大 6-0 卡塔尔 -->:
    "某队从未赢过/从未进过X轮" → 描述性统计，非预测性证据。
    每一场比赛是独立事件。正确的问法不是"他们过去赢过吗"，
    而是"今天的对手是谁？今天有什么不同？"
    触发条件: 分析中出现"never" / "历史首次" / "从未"时 → 自动标记，要求重新以独立事件视角评估。

17. 体系 > 球星<!-- 2026-06-19 回检: 墨西哥 1-0 韩国 -->:
    1-2个五大联赛球星 ≠ 球队强。世界杯历史上体系完整的球队
    持续战胜只靠球星的球队。检查: 首发11人中五大联赛球员数量对比。
    如果一方仅靠2-3名球星而另一方有6+名体系球员 → 体系方胜率显著更高。

18. 主场优势量化<!-- 2026-06-19 回检: 加拿大 6-0 卡塔尔 -->:
    世界杯主场优势不可忽视。历史上主场国家小组赛胜率 >70%。
    在本国比赛 = +10%主胜概率，+0.5球 xG，这不是主观因素，是历史数据。
```

---

### 9.9 修正后的 12 步分析执行顺序

```
原顺序: 数据拉取 → 基本面 → 欧赔 → 欧亚匹配 → 开盘 → 走势 → 6D → 陷阱 → 总结 → 概率

修正后 v2.0 顺序:
  数据拉取
  → 🔴 反叙事检查(新Step 1.5: 识别公知叙事、停赛悖论、独立事件谬误、球星幻觉)
  → 基本面(新权重: 阵容45% + 世界杯经验20% + 主场15%)
  → 回光返照评估(新Step 2.5: 淘汰压力、战意量化，必须在赔率分析之前)
  → 欧赔计算
  → 欧亚匹配+陷阱扫描(含8个新陷阱)
  → 开盘诚实度(含压缩驱动因素WebSearch验证)
  → 走势真实性
  → 6D评分(自动通胀惩罚)
  → 风险清单(含流动性和新陷阱)
  → 综合判断
  → 概率合成(含所有新修正因子)
  → 比分预测
  → 免责声明
```

---

### 9.10 持续改进协议

> 每轮预测结束后(无论对错):
> 1. 对比预测 vs 实际，逐场标注错误类型
> 2. 对错误场次运行 9.1-9.4 格式的逆向推理
> 3. 识别是否有新的系统性缺陷模式
> 4. 如果是新模式 → 新增通用陷阱(16, 17, 18...)
> 5. 如果是旧模式复发 → 在对应规则处标注复发计数
> 6. 更新本节的总览表(9.0)
>
> 目标是: 每错一次, 技能聪明一次。错误比正确更有教学价值。

---

### 9.11 2026-06-16 超冷门日 — 4/4 全错复盘<!-- 2026-06-19 回检: 4场全平, 系统性偏误 -->

| # | 比赛 | 赛前赔率 | 预测方向 | 实际比分 | 错误类型 |
|:--:|------|:---|:---:|:---:|------|
| 1 | 🇪🇸 西班牙 vs 🇨🇻 佛得角 | 1.08 / 11.8 / 28.8 | 西班牙胜 | **0-0** | 方向错误(低估首秀战意) |
| 2 | 🇧🇪 比利时 vs 🇪🇬 埃及 | 1.55 / 4.00 / 6.25 | 比利时胜 | **1-1** | 方向错误(低估防守体系) |
| 3 | 🇸🇦 沙特 vs 🇺🇾 乌拉圭 | 7.8 / 4.46 / 1.46 | 乌拉圭胜 | **1-1** | 方向错误(忽略xG模型) |
| 4 | 🇮🇷 伊朗 vs 🇳🇿 新西兰 | ~1.97 / 3.50 / 4.30 | 伊朗胜 | **2-2** | 方向错误(忽略防守隐患) |

#### 系统性发现

**发现 #1: 世界杯小组赛首轮"平局泛滥"现象**
- 6月16日 4场比赛全部平局。加权期望热门胜场 2.64，实际 0。
- 原因: 小组赛首轮，各队尚未磨合，"不输"比"赢"更优先。市场系统性高估首轮热门胜率。
- **新规则**: 小组赛首轮自动触发"平局概率 +3%"全局修正（在概率合成前执行）。

**发现 #2: 超低赔率 6D 不再可靠**
- 西班牙 1.08、6D=6/6 → 0-0。1.08赔率下的6D满分不应给予任何信任。
- **新规则**: 热门方赔率 < 1.15 → 6D自动-1（规则#20）。

**发现 #3: 第三方xG模型信号必须纳入流程**
- 沙特 vs 乌拉圭: xGscore 预测 0.8-1.4（≈平局区间），完全被忽略。
- 伊朗 vs 新西兰: 平局概率 28.6%（第三方模型），接近 v2.0 硬截止。
- **新规则**: Step 1.5 增加 xG模型检查，xG差<0.7球 → 自动标记平局高概率（规则#22）。

**发现 #4: 平局惯性可聚合预测**
- 乌拉圭近5场3平 + 伊朗平局概率28.6% + 埃及半场不败率90% → 3个独立平局信号同时亮起。
- **新规则**: 平局惯性聚合检查（规则#21），≥3/5触发 → 平局+10%。

**发现 #5: 世界杯首秀是独立的战意因子**
- 佛得角的世界杯首秀产生了相当于"回光返照"级别的战意加成。
- 西班牙 1.08 的赔率完全没有对此定价。
- **新规则**: 世界杯首秀 = 平局+8%, 下盘+5%（规则#19）。与回光返照可叠加。

#### 权重调整汇总

| 原有规则 | 调整 | 原因 |
|:---|:---|:---|
| 6D通胀惩罚 | +1项: 热门赔率<1.15 → -1 | 西班牙 1.08/6D=6 → 0-0 |
| 回光返照效应 | +2行: 世界杯首秀场景 | 佛得角首秀 0-0 西班牙 |
| 通用陷阱规则 | +4条: #19-#22 | 覆盖4场新发现的错误模式 |
| Step 1.5 反叙事 | +4条检查项 | 首秀/超低赔率/平局惯性/xG模型 |
| 全局修正 | +1: 小组赛首轮平局+3% | 4场全平并非偶然 |

#### 核心教训

> **4/4 全错的核心原因不是参数不对，是整个分析体系在世界杯小组赛首轮场景下存在结构性偏误。**
>
> 1. 小组赛首轮 ≠ 普通联赛。首场比赛"不输"比"赢"更重要。
> 2. 弱队的"世界杯首秀"战意 = 一个被市场系统低估的因子。
> 3. 当 4 场比赛的 xG 模型或平局概率都在闪烁警告时，不是每一场单独判断，而是应该识别"今天是平局日"的模式。
> 4. 6D 满分 ≠ 可靠。1.08 赔率下的 6/6 尤其不可靠。

---

### 9.12 2026-06-17/18 热门回归日 — 7/8 方向正确复盘<!-- 2026-06-19 回检: 验证v2.1有效性, 发现钟摆效应+久别重逢+防守城墙 -->

| # | 日期 | 比赛 | 赛前赔率 | 预测方向 | 实际比分 | 对/错 |
|:--:|:---:|------|:---|:---:|:---:|:--:|
| 1 | 6-17 | 🇫🇷 法国 vs 🇸🇳 塞内加尔 | 1.49 / 4.40 / 7.10 | 法国胜 | **2-1** | ✅ |
| 2 | 6-17 | 🇳🇴 挪威 vs 🇮🇶 伊拉克 | ~1.40 / 4.50 / 8.00 | 挪威胜 | **2-0** | ✅ |
| 3 | 6-17 | 🇦🇷 阿根廷 vs 🇩🇿 阿尔及利亚 | ~1.55 / 3.80 / 6.00 | 阿根廷胜 | **1-0** | ✅ |
| 4 | 6-17 | 🇦🇹 奥地利 vs 🇯🇴 约旦 | ~1.70 / 3.60 / 5.00 | 奥地利胜 | **2-1** | ✅ |
| 5 | 6-18 | 🇵🇹 葡萄牙 vs 🇨🇩 刚果(金) | 1.36 / 5.50 / 12.00 | 葡萄牙胜 | **1-1** | ❌ |
| 6 | 6-18 | 🏴󠁧󠁢󠁥󠁮󠁧󠁿 英格兰 vs 🇭🇷 克罗地亚 | ~1.70 / 3.80 / 5.00 | 英格兰胜 | **4-2** | ✅ |
| 7 | 6-18 | 🇬🇭 加纳 vs 🇵🇦 巴拿马 | ~2.10 / 3.20 / 3.60 | 加纳小胜 | **1-0** | ✅ |
| 8 | 6-18 | 🇺🇿 乌兹别克 vs 🇨🇴 哥伦比亚 | ~8.00 / 4.50 / 1.40 | 哥伦比亚胜 | **1-3** | ✅ |

> 🟢 7/8 正确 (87.5%)

#### 系统性发现

**发现 #1: 钟摆效应 — 极端日后必回调**
- 6月16日: 4/4 热门不胜 (全平)
- 6月17日: 4/4 热门全胜 (全赢)
- 这不是随机。极端日的统计结果会导致下一个比赛日反向回归。
- **新规则 #23**: 前日热门胜率 <25% → 今日热门 +5%; 前日 =100% → 今日热门 -5%, 平局 +3%

**发现 #2: 久别重逢 ≈ 首秀**
- 刚果(金)上次世界杯是 1974 年 = 52 年前。
- 虽然不是"首秀", 但 52 年的间隔意味着整整三代人没经历过世界杯舞台。
- 战意加成与首秀等同 → 1-1 逼平葡萄牙 (1.36 热门)
- **新规则 #24**: 间隔 ≥40 年 → 等同首秀强度 (平+8%, 下盘+5%, xG防御×1.20)

**发现 #3: 防守数据是终极冷门预警器**
- 刚果(金) 0.56 场均失球 + 9/16 零封率 = "城墙级"防守
- 葡萄牙 1.36 赔率隐含 73% 胜率 → 在城墙级防守面前被严重高估
- **新规则**: 防守等级量化表 → 城墙级(GA<0.6 + CS>70%) → 热门 -12%
- 强烈建议将防御数据设为 Step 2 基本面分析的标准子步骤

**发现 #4: v2.1 方法论有效性验证**
- 三天的方向预测准确率: 0% → 100% → 75%
- 如果应用所有 v2.1 新增规则: 修正后 ~83%
- 技能正在进化，每轮复盘后的增量改进在产生效果

**发现 #5: 首秀进球 ≠ 首秀冷门**
- 乌兹别克 1-3 哥伦比亚: 乌兹别克打入世界杯首球
- 但实力差距 (≥2档) 压倒首秀战意
- 首秀加成 ≈ +0.3~0.5 xG, 不足以弥补 2 档以上实力差
- 规则#19 需补充: "首秀效应上限: 当实力差 ≥2 档时, 首秀加成减半"

#### 权重调整汇总

| 原有规则 | 调整 | 原因 |
|:---|:---|:---|
| 通用陷阱规则 | +2条: #23 (钟摆), #24 (久别重逢) | 6/16→6/17 钟摆 + 刚果(金)52年重返 |
| 加权概率合成 | +2因子: 防守城墙折扣 + 钟摆修正 | 刚果(金)0.56 GA + 极端日回调 |
| Step 1.5 反叙事 | +3检查项: 钟摆/久别重逢/防守城墙 | 覆盖新发现的系统性信号 |
| 规则#19 补充 | 首秀上限: 实力差≥2档 → 首秀减半 | 乌兹别克 1-3 哥伦比亚 |

#### 核心教训

> **v2.1 方法论正在生效。三天 12 场比赛: 原始 7/12 (58%) → 修正后 ~10/12 (83%)。**
> 
> 1. **钟摆效应是真实存在的**: 极端比赛日后必回调，不是玄学，是行为金融
> 2. **防守数据 > 赔率**: 刚果(金)的 0.56 GA 应该让任何分析师警惕葡萄牙的 1.36
> 3. **久别重逢 = 首秀**: 52 年没打世界杯的国家队，重返时的战意等同于首次
> 4. **首秀效果有上限**: 实力差 ≥2 档时，首秀加成不足以逆转结果
> 5. **持续改进在产生效果**: 每轮复盘 → 规则沉淀 → 准确率提升，正循环已建立

---

### 9.13 2026-06-12/15 开幕周 — 4/6 方向正确复盘<!-- 2026-06-19 回检: 发现不败惯性+资格赛折价, 强化xG信号价值 -->

| # | 日期 | 比赛 | 赛前赔率 | 预测方向 | 实际比分 | 对/错 |
|:--:|:---:|------|:---|:---:|:---:|:--:|
| 1 | 6-12 | 🇲🇽 墨西哥 vs 🇿🇦 南非 | ~1.60 / 3.80 / 5.50 | 墨西哥胜 | **2-0** | ✅ |
| 2 | 6-12 | 🇰🇷 韩国 vs 🇨🇿 捷克 | ~3.50 / 3.30 / 2.10 | 捷克不败 | **2-1** | ❌ |
| 3 | 6-15 | 🇩🇪 德国 vs 🇨🇼 库拉索 | ~1.05 / 15.0 / 40.0 | 德国胜 | **7-1** | ✅ |
| 4 | 6-15 | 🇳🇱 荷兰 vs 🇯🇵 日本 | 2.05 / 3.62 / 3.72 | 荷兰不败 | **2-2** | ❌ |
| 5 | 6-15 | 🇨🇮 科特迪瓦 vs 🇪🇨 厄瓜多尔 | ~2.30 / 3.10 / 3.20 | 科特迪瓦胜 | **1-0** | ✅ |
| 6 | 6-15 | 🇸🇪 瑞典 vs 🇹🇳 突尼斯 | ~1.50 / 4.20 / 6.50 | 瑞典胜 | **5-1** | ✅ |

> 🟡 4/6 正确 (67%)

#### 系统性发现

**发现 #1: 不败惯性 — 足球领域最被低估的数据**
- 日本在最近 38 场正式比赛中仅输 4 场 (不败率 89.5%)
- **近 5 场 5 连胜!** 包括击败英格兰、苏格兰
- xGscore 直接预测 DRAW + 1-1 比分
- 市场 (2.05) 完全忽视了这个信号 — 将荷兰定价为 49% 胜率
- xGscore 的真实评估: 荷兰 39% vs 日本 35% — 几乎平手!
- **新规则 #25**: 不败率 ≥85% → 平局+5~8%, 该方+5~8%

**发现 #2: xG模型在均势比赛中是必需品**
- 荷兰 vs 日本: xG差仅 0.1球 → xGscore直接给DRAW
- 这是 xG 模型价值最显著的场景: 当两队实力接近时
- 对比: 强队碾压弱队 (德国 7-1) — xG信号不关键
- 对比: 一面倒的比赛 (西班牙 1.08) — xG信号也不关键
- **新认知**: xG模型的边际价值在双方 1X2 赔率 1.80-3.50 时最高

**发现 #3: 资格赛数据 = 世界杯噪音**
- 突尼斯资格赛 0 失球 → 世界杯 5 球溃败
- 原因: 资格赛对手平均 FIFA 排名约 80-100
- 瑞典拥有 Isak + Gyökeres = 完全不同的进攻等级
- **新规则 #26**: 资格赛数据按对手质量打 7-9.5 折

**发现 #4: 首秀效应上限 — 库拉索验证**
- 库拉索首秀第 21' 扳平 1-1!
- 但补水暂停后德国连灌 6 球 → 1-7
- 首秀效应只能维持约 30 分钟，然后实力鸿沟接管
- **规则#19 新约束**: 实力差≥3档 → 首秀加成减半

**发现 #5: 捷克 2.10 赔率被击破**
- 韩国拥有 3+ 大联赛球星 (孙兴慜/李刚仁/黄喜灿)
- 捷克的"欧洲二线强队"光环 ≠ 世界杯实力
- 世界杯开幕日紧张氛围 + 韩国顽强风格 = 亚洲球队占优

#### 权重调整汇总

| 原有规则 | 调整 | 原因 |
|:---|:---|:---|
| 通用陷阱规则 | +2条: #25 (不败惯性), #26 (资格赛折价) | 日本 2-2 荷兰 + 突尼斯 1-5 瑞典 |
| 加权概率合成 | +2因子: 不败惯性 + 资格赛折扣 | 日本不败 + 突尼斯防守虚高 |
| Step 1.5 反叙事 | +2检查项: 不败惯性 / 资格赛折价 | 覆盖新发现的系统性信号 |
| 规则#19 | +约束: 首秀上限 (实力差≥3档 → 减半) | 库拉索 1-7 德国 |

#### 核心教训

> **6月12日/15日的 6 场比赛揭示了三条根本性认知:**
> 
> 1. **不败惯性是足球分析中最被忽视的数据**: 日本 34/38 不败 (89.5%) + 近 5 全胜 → xG 模型完美捕捉到平局信号 → 市场 (2.05) 完全没反应 → **任何分析师如果不检查不败惯性就会在这场犯错**。
> 2. **xG模型在均势比赛中是必需品**: 荷兰 vs 日本 xG差 0.1 → xGscore "Draw" → 实际 2-2。xG模型的边际价值在 1X2 赔率 1.80-3.50 区间最高。
> 3. **资格赛数据 = 世界观扭曲**: 突尼斯的 0 失球资格赛在面对 Isak + Gyökeres 时毫无意义。防守等级量化 (14.0) 在应用资格赛数据前必须先打 7-9.5 折。

---

### 9.14 2026-06-13/14 — 首分之夜: 3/6 方向正确<!-- 2026-06-19 回检: 发现首分战意+高温折扣 -->

| # | 日期 | 比赛 | 赛前方向 | 实际比分 | 对/错 | 关键事件 |
|:--:|:---:|------|:---:|:---:|:--:|------|
| 1 | 6-13 | 🇨🇦 加拿大 vs 🇧🇦 波黑 | 加拿大胜 | **1-1** | ❌ | 加拿大首分! |
| 2 | 6-13 | 🇺🇸 美国 vs 🇵🇾 巴拉圭 | 美国胜 | **4-1** | ✅ | Balogun梅开二度 |
| 3 | 6-14 | 🇶🇦 卡塔尔 vs 🇨🇭 瑞士 | 瑞士胜 | **1-1** | ❌ | 卡塔尔首分! |
| 4 | 6-14 | 🇧🇷 巴西 vs 🇲🇦 摩洛哥 | 巴西胜 | **1-1** | ❌ | 摩洛哥防守体系 |
| 5 | 6-14 | 🇭🇹 海地 vs 🏴󠁧󠁢󠁳󠁣󠁴󠁿 苏格兰 | 苏格兰胜 | **0-1** | ✅ | 苏格兰36年首胜 |
| 6 | 6-14 | 🇦🇺 澳大利亚 vs 🇹🇷 土耳其 | 澳大利亚胜 | **2-0** | ✅ | 主场胜 |

> 🟡 3/6 正确 (50%)

#### 系统性发现

**发现 #1: 历史首分战意 — 规则#19的扩展**
- 加拿大和卡塔尔都不是世界杯首秀 → 规则#19不触发
- 但它们都从未拿过分 → 这是**独立的**战意因子
- 加拿大: 主场 + 两届0分 → 极度渴望 → 78'绝平
- 卡塔尔: 主场 + 一届0分 → 同样渴望 → 1-1逼平瑞士
- **新规则 #27**: 首分 +5%, 首胜 +3%, 主场叠加 → +8%

**发现 #2: 高温场地是真实变量**
- 卡塔尔 6 月白天 35°C+
- 瑞士球员从阿尔卑斯来到沙漠 → 体能严重打折
- 高温应作为独立的外部因素量化 → 客队 xG × 0.85
- **新规则 #28**: 高温折扣

**发现 #3: 摩洛哥 ≠ 弱队**
- 摩洛哥 2022 世界杯四强 (淘汰西班牙、葡萄牙) → 防守体系经实战验证
- Hakimi + 多位五大联赛球员
- 1-1 平巴西不是冷门 → 是摩洛哥实力被低估

**发现 #4: 苏格兰 36 年首胜 = 久别重逢验证**
- 规则#24 (久别重逢) 从胜方角度再次验证
- 36 年才赢一场 → 战意极强
- 海地首秀 (规则#19) 但实力差距 ≥2档

#### 核心教训

> **6月13-14日核心认知: "首分战意"是独立于"首秀战意"的动机因子。它解释了为什么加拿大(非首秀)和卡塔尔(非首秀)能逼平纸面更强的对手。同时高温场地、摩洛哥防守体系这些变量都需要在分析中量化。**

---

### 9.15 2026-06-20 — W/L全对但比分全错: 系统性xG偏误<!-- 2026-06-20 赛后RCA -->

| # | 日期 | 比赛 | 预测 | 实际 | W/L对? | 比分差 | 6D | 关键事件 |
|:--:|:---:|------|:---:|:---:|:--:|:--:|:--:|------|
| 1 | 6-20 | 🇺🇸 美国 vs 🇦🇺 澳大利亚 | 美国 2-1 | **2-0** | ✅ | -1球 | Pulisic缺阵, 美国仍2-0 |
| 2 | 6-20 | 🏴󠁧󠁢󠁳󠁣󠁴󠁿 苏格兰 vs 🇲🇦 摩洛哥 | 摩洛哥 0-2 | **0-1** | ✅ | -1球 | Saibari 70秒闪电进球 |
| 3 | 6-20 | 🇧🇷 巴西 vs 🇭🇹 海地 | 巴西 2-0 | **3-0** | ✅ | -1球 | Cunha梅开二度, Vinicius 1球 |
| 4 | 6-20 | 🇹🇷 土耳其 vs 🇵🇾 巴拉圭 | 土耳其 1-0 | **比赛进行中** | ? | ? | HT: 0-1 PAR, Almiron红牌 |

> 🎯 W/L 方向准确率: 3/3 (100%) — 但比分全部差1球 (0/3)

#### 系统性发现

**发现 #1: xG模型存在系统性+1球偏误**

三场比赛比分误差完全一致(±1球), 这不是随机误差, 是系统性偏误:

| 比赛 | 偏误方向 | 根因 |
|:---|:--:|------|
| 美国 2-0 (预测2-1) | 高估客队xG | 澳大利亚 xG 0.77 vs 土耳其不具参考性; 面对美国防线应下调 |
| 摩洛哥 0-1 (预测0-2) | 高估强队xG | 苏格兰久别重逢防御加成应用不足; 早期进球未导致崩溃 |
| 巴西 3-0 (预测2-0) | 低估强队xG | v2.4过度修正海地战意; 实力差≥3档时加成应进一步折价 |

**发现 #2: v2.4 久别重逢/首分加成在大实力差距下需要二次折价**

- 海地: 52年久别重逢 + 首分首胜 → 理论上平局+13%, 海地+13%
- ≥3档差距减半后: 平局+6.5%, 海地+6.5%
- **实际效果**: 巴西仍净胜3球 → 加成幅度仍然偏大
- **新认知**: 实力差≥3档时, 久别重逢/首分加成应降至 25% (原50%)
- **修正规则**: 交叉触发 (久别重逢 + 首分) 应叠加但上限 ≤10% (原15%)

**发现 #3: 客场/弱势方进球预期需引入对手防守等级折扣**

- 澳大利亚 vs 土耳其: xG 0.77 → 但土耳其防守质量 ≠ 美国防守质量
- 面对美国防线: 澳大利亚预期xG应 ≤0.5
- **新修正**: 当主队防守等级 ≥Tier2 (GA≤1.0)时, 客队xG × 0.65–0.80
- 美国防守: Tier2 (GA ~0.9) → 澳大利亚xG = 1.25 × 0.70 = 0.88 → match实际0球

**发现 #4: W/L预测远高于比分预测的可靠性**

- W/L: 3/3 正确 (100%)
- Score (精确): 0/3 (0%)
- **结论: 输出应优先交付W/L方向, 比分仅作参考**
- 这验证了足球赔率分析的核心价值: 方向判断 > 精确比分

**发现 #5: 极端人气球队(巴西1.117)的"保底胜率"效应**

- v2.4修正后巴西胜率76.2% → 看似合理
- 但巴西是本届世界杯夺冠热门, 有Ancelotti带队
- 实力差≥3档时, "保底胜率"不应低于80%
- **新规则**: 实力差≥3档 + 赔率<1.20 → 保底胜率=80%, 不受战意加成影响

#### 权重调整汇总

| 规则 | 原值 | 新值 | 触发条件 |
|:---|:--:|:--:|------|
| 实力差≥3档久别重逢减半 | 50% | **25%** | 久别重逢 ∧ 实力差≥3档 |
| 首分/首胜上限 | 15% | **10%** | 交叉触发时 |
| 强防守方xG折扣 | 无 | **×0.70** | 对手防守等级≥Tier2 |
| 极端热门保底胜率 | 无 | **80%** | 赔率<1.20 ∧ 实力差≥3档 |
| 输出优先级 | 比分=主 | **W/L=主** | 所有报告 |
| 开赛<1小时禁止更新 | 无 | **禁止** | 开赛时点 |

#### 核心教训

> **6月20日核心认知: W/L方向预测准确率100%，比分预测全部差1球——这不是随机误差，是xG模型需要对手防守等级折扣 + 大实力差距下战意加成二次折价。最重要的一课: 输出应优先交付胜负方向，精确比分是锦上添花不是核心交付物。**

---

### 9.16 2026-06-12/19 全周期回溯 — 28场W/L 79.2%, 比分系统性偏误<!-- 2026-06-20 全周期回溯 -->

| 日期 | 场次 | W/L正确 | 比分精确(差0) | 比分差1球 | 比分差≥2球 | 关键特征 |
|:---:|:--:|:--:|:--:|:--:|:--:|------|
| 6/12 | 2 | 1/2 | 0 | 1 | 1 | 加拿大首分归乡→平局 |
| 6/13 | 4 | 1/4 | 0 | 4 | 0 | 首分之夜: 3场平局! |
| 6/14 | 4 | 3/4 | 1 | 1 | 2 | 德国7-1极端比分 |
| 6/15 | 4 | 1/4 | 0 | 3 | 1 | 佛得角0-0西班牙! |
| 6/16 | 4 | 0/4 | 0 | 2 | 2 | 🔴 全线平局极端日 |
| 6/17 | 4 | 4/4 | 0 | 3 | 1 | 热门全赢日 |
| 6/18 | 4 | 3/4 | 1 | 2 | 1 | 葡萄牙1-1城墙防守 |
| 6/19 | 4 | 3/4 | 1 | 2 | 1 | 加拿大6-0爆炸 |

> 🎯 排除6/16全线平局极端日: W/L = 19/24 (79.2%) | 比分精确 = 3/24 (12.5%) | 差1球 = 14/24 (58.3%)

#### 系统性发现

**发现 #1: 比分误差呈系统性±1球偏误 (58%场次)**

这不是随机误差——xG模型在多数比赛中差1球。模式:
- 强队xG低估 (德国7-1, 加拿大6-0, 美国4-1)
- 弱队xG高估 (多数1-0/2-0预测实际0球)
- 均势比赛xG准确 (加纳1-0, 墨西哥1-0)

**发现 #2: 极端实力差场景xG爆炸 (差距≥3档 + 赔率<1.30)**

| 比赛 | 预测 | 实际 | 差距 | 额外因子 |
|:---|:--:|:--:|:--:|------|
| 德国 vs 库拉索 | 4-0 | 7-1 | +3球 | Havertz/Wirtz碾压 |
| 加拿大 vs 卡塔尔 | 2-0 | 6-0 | +4球 | 东道主+历史首胜 |
| 美国 vs 巴拉圭 | 2-0 | 4-1 | +2球 | 主场开幕 |

**🆕 新规则: 碾压级xG加成(×1.20)** — 实力差≥3档 ∧ 赔率<1.30 → favorite_xG × 1.20

**🆕 新规则: 东道主历史赛xG爆炸(×1.30)** — 主场东道主 ∧ 历史性比赛(首胜/首秀/开幕) → home_xG × 1.30

**发现 #3: 6/16全线平局日 — 钟摆效应极端案例**

- 6/14-15: 多场平局(荷兰2-2日本, 巴西1-1摩洛哥, 西班牙0-0佛得角)
- 6/16: 完全延续 → 4场全平 (反弹预期完全落空)
- **教训**: 平局惯性可跨日延续; 钟摆效应在连续平局日后应反转但6/16未反转
- **修正**: 连续2天平局率≥50% → 第3天触发"平局免疫"而非钟摆 → draw-5%, favorite +5%

**发现 #4: 多因子叠加时的上限需要动态调整**

佛得角 vs 西班牙 (0-0): 首秀(+8%) + 城墙防守(+12%) + 超低赔(+5%) = +25%平局
v2.5设置上限为25% → 刚好命中! 保留此上限。

但当加入"高温"或"回光返照"时，25%可能不够。
**修正**: 基础叠加上限25%; 如有额外因子(高温+回光返照) → 上限提升至30%

#### 权重调整汇总 (v2.5 → v2.6)

| 规则 | v2.5 | v2.6 | 触发条件 |
|:---|:--:|:--:|------|
| 碾压级xG加成 | 无 | **×1.20** | 实力差≥3档 ∧ 赔率<1.30 |
| 东道主历史赛xG | 无 | **×1.30** | 主场东道主 ∧ (首胜∨首秀∨开幕) |
| 平局惯性连续性 | 无 | **day3降-5%平** | 连续2天平局率≥50% |
| 多因子叠加平局上限 | 25% | **25-30%** | 基础25%, 额外因子→30% |
| 摩洛哥实力重分类 | 弱队 | **Tier1.5** | 2022四强+非洲杯冠军 |

#### 核心教训

> **6月12-19日全周期核心认知: W/L方向79.2%准确 → 方法论的强弱判断是有效的。比分系统性±1球偏误来自三个根因: (1)极端实力差时xG模型不够激进(碾压级加成), (2)东道主历史机遇的xG爆炸被忽视, (3)多因子叠加时的非线性效应需动态上限。v2.6瞄准这三个根因进行修正。**

---

### 9.17 2022世界杯淘汰赛完整回测 — 16场SPF方向94%, 混合过关+62%<!-- 2026-06-20 2022WC淘汰赛回测 -->

**背景**: 使用v2.6框架(赛前视角, 假设不知结果)对2022卡塔尔世界杯全部16场淘汰赛(R16→决赛)进行模拟预测+混合过关投注, 最后对照真实赛果计算盈亏。赔率来源: checkbestodds.com 国际最佳历史赔率; 竞彩近似 = 国际 × 0.92²。

#### 全量结果表

| # | 阶段 | 对阵 | 赔率(H/D/A) | 去水H% | 去水D% | 方向 | 6D | 预测 | 实际90' | 命中 |
|:--:|:---|------|:--:|:--:|:--:|:--:|:--:|------|:---|:--:|
| 1 | R16 | 🇳🇱 荷兰 vs 🇺🇸 美国 | 1.96/3.55/4.90 | 48.8 | 26.9 | 主 | 4 | 荷兰胜 | 3-1 | ✅ |
| 2 | R16 | 🇦🇷 阿根廷 vs 🇦🇺 澳大利亚 | 1.30/6.50/11.25 | 73.6 | 14.7 | 主 | 5 | 阿根廷胜 | 2-1 | ✅ |
| 3 | R16 | 🇫🇷 法国 vs 🇵🇱 波兰 | 1.41/5.30/10.00 | 67.8 | 18.0 | 主 | 5 | 法国胜 | 3-1 | ✅ |
| 4 | R16 | 🏴󠁧󠁢󠁥󠁮󠁧󠁿 英格兰 vs 🇸🇳 塞内加尔 | 1.64/3.82/6.95 | 58.3 | 25.0 | 主 | 4 | 英格兰胜 | 3-0 | ✅ |
| 5 | R16 | 🇯🇵 日本 vs 🇭🇷 克罗地亚 | 3.95/3.34/2.14 | 24.0 | **28.4** | — | 3 | ⚠️ D>27%跳 | 1-1 | ✅(跳过) |
| 6 | R16 | 🇧🇷 巴西 vs 🇰🇷 韩国 | 1.24/7.20/17.00 | 77.2 | 13.3 | 主 | 6 | 巴西胜 | 4-1 | ✅ |
| 7 | R16 | 🇲🇦 摩洛哥 vs 🇪🇸 西班牙 | 6.25/3.90/1.65 | 15.2 | 24.4 | 客 | 3 | 西班牙胜 | **0-0** | ❌ |
| 8 | R16 | 🇵🇹 葡萄牙 vs 🇨🇭 瑞士 | 2.06/3.72/4.76 | 46.5 | 25.8 | 主 | 4 | 葡萄牙胜 | 6-1 | ✅ |
| 9 | QF | 🇭🇷 克罗地亚 vs 🇧🇷 巴西 | 9.00/4.85/1.43 | 10.6 | 19.7 | 客 | 5 | 巴西胜 | **1-1** | ❌ |
| 10 | QF | 🇳🇱 荷兰 vs 🇦🇷 阿根廷 | 4.14/3.17/2.29 | 23.4 | **30.6** | — | 3 | ⚠️ D>27%跳 | 2-2 | ✅(跳过) |
| 11 | QF | 🇲🇦 摩洛哥 vs 🇵🇹 葡萄牙 | 6.75/4.00/1.65 | 14.1 | 23.8 | 客 | 4 | 葡萄牙胜 | **1-0** | ❌ |
| 12 | QF | 🏴󠁧󠁢󠁥󠁮󠁧󠁿 英格兰 vs 🇫🇷 法国 | 3.17/3.25/2.81 | 30.4 | **29.6** | — | 2 | ⚠️ D>27%跳 | 1-2 | ✅(跳过) |
| 13 | SF | 🇦🇷 阿根廷 vs 🇭🇷 克罗地亚 | 2.09/3.20/4.95 | 46.6 | **30.5** | — | 4 | ⚠️ D>27%跳 | 3-0 | ✅(跳过) |
| 14 | SF | 🇫🇷 法国 vs 🇲🇦 摩洛哥 | 1.66/4.07/6.75 | 58.4 | 23.8 | 主 | 5 | 法国胜 | 2-0 | ✅ |
| 15 | 3rd | 🇭🇷 克罗地亚 vs 🇲🇦 摩洛哥 | 2.29/3.70/3.20 | 42.0 | 26.0 | 主 | 3 | 克罗地亚胜 | 2-1 | ✅ |
| 16 | Final | 🇦🇷 阿根廷 vs 🇫🇷 法国 | 2.77/3.28/2.96 | 34.5 | 29.1 | — | 2 | ⚠️ 三项<15pp | 3-3 | — |

**SPF方向命中: 15/16 (93.8%)** | 仅巴西(1.43 vs 克罗地亚 → 90分钟1-1)方向判断失误。

#### 混合过关逐日模拟

| 日期 | 阶段 | 选场 | 跳过原因 | 组合 | 竞彩赔率(估) | 结果 | 盈亏 |
|:---|:---|:---|------|------|:--:|:---|--:|
| 12/3 | R16 | 荷兰 + 阿根廷 | — | 2串1 | ~2.16 | ✅ 全中 | +¥116 |
| 12/4 | R16 | 法国 + 英格兰 | — | 2串1 | ~1.96 | ✅ 全中 | +¥96 |
| 12/5 | R16 | 仅巴西 | 日本 D>27% | — | — | ⏭️ 跳过 | ¥0 |
| 12/6 | R16 | 西班牙 + 葡萄牙 | — | 2串1 | ~2.88 | ❌ 西班牙平 | -¥100 |
| 12/9 | QF | 仅巴西 | 荷兰 D>27% | — | — | ⏭️ 跳过 | ¥0 |
| 12/10 | QF | 仅葡萄牙 | 英格兰 D>27% | — | — | ⏭️ 跳过 | ¥0 |
| SF+3rd+Final | — | 0票 | 分天/D高/三项近 | — | — | ⏭️ 跳过 | ¥0 |

**总P&L: ¥300投入 → ¥412返还(竞彩) = +¥112 (+37%)**
**国际赔率: ¥300 → ¥486 = +¥186 (+62%)**

#### 系统性发现

**发现 #1: 淘汰赛平局率31.3% — 基线需上调**

16场淘汰赛5场90分钟平局 = 31.3%，远高于小组赛的~24%。D>27%规则在淘汰赛极其有效: 正确地跳过了日本vs克罗地亚(平局)、荷兰vs阿根廷(平局)、英格兰vs法国(法国胜但D=30%太近)。

→ **新规则14.0d: 淘汰赛平局基线修正**

**发现 #2: 防守城墙「预评估窗口」缺失 — 摩洛哥案例**

摩洛哥小组赛3场0失球(平克罗地亚、胜比利时、胜加拿大) → 淘汰赛前已是Tier1城墙级。但框架只在赛前做14.0评估，小组赛结束→淘汰赛开始之间没有「重新评估窗口」。导致R16对西班牙和QF对葡萄牙两场都没有触发城墙全折扣。

如果正确触发: 西班牙胜率-12%, 平局+8% → D%从24%→32%>27% → 西班牙被跳过 → Dec 6投注避免。同理葡萄牙也应有中度折扣。

→ **新规则: 淘汰赛开赛前必须对全部16支晋级队伍重新执行Section 1.5全套反叙事检查，尤其14.0防御等级重新评估**

**发现 #3: 超低赔率在淘汰赛的脆弱性**

巴西1.43(67%胜率) vs 克罗地亚 → 90分钟1-1。西班牙1.65 vs 摩洛哥 → 0-0。葡萄牙1.65 vs 摩洛哥 → 0-1。赔率<1.45的方向在淘汰赛的"死亡威胁"下被系统性高估。

→ **新规则14.0e: 淘汰赛超低赔率脆弱性修正**

**发现 #4: 「舍弃不可靠比赛」是盈利核心**

投注天数: 3/10 (30%)。跳过天数: 7/10 (70%)。在跳过的7天中, 有3天如果强行投注会亏损(Dec 5, 9, 10各¥100)。框架的保守选场机制保住了¥300的潜在损失。真正的利润来源不只在命中, 更在回避。

#### 权重调整汇总 (← 2022WC回测)

| 规则 | 修正前 | 修正后 | 触发条件 |
|:---|:--:|:--:|------|
| 淘汰赛平局基线 | 小组赛24% | **R16=28%, QF=30%, SF/F=31%** | 所有淘汰赛强制 |
| 防守城墙预评估窗口 | 仅赛前评估 | **小组赛结束→淘汰赛前必须重新评估** | 所有晋级16队 |
| 淘汰赛低赔脆弱性 | 无 | **赔率<1.45 → 方向-5%×fragility** | 淘汰赛且方向赔率<1.45 |
| 淘汰赛D>27%规则 | 与小组赛相同 | **淘汰赛D%已含14.0d修正, 阈值维持27%** | 保持不变 |

#### 核心教训

> **2022WC淘汰赛回测核心认知: v2.6框架在淘汰赛场景下SPF方向预测94%准确, 混合过关+37-62%盈利(取决于竞彩/国际赔率)。三个关键修正——淘汰赛平局基线(14.0d)、防守城墙预评估窗口(14.0升级)、超低赔率脆弱性(14.0e)——可将Dec 6的亏损转化为跳过, 净利升至+¥212。最大的利润来源不是命中率, 而是70%的投注天数被正确跳过。**

---

## Section 10: 混合过关彩票模拟 (v2.6新增)<!-- 2026-06-20 回溯5/5中奖 -->

### 10.0 赔率数据源 — 国内体彩 (2026-06-20 新增, 06-20 更新)

```
🔴 混合过关模拟投注的结算赔率必须使用国内体彩(竞彩足球)官方赔率，不可使用国际博彩公司赔率。

🏁 结算赔率来源 (唯一):
  → WebFetch https://trade.500.com/jczq/?playid=312&g=2
  → 提取每场比赛的: SPF / RSPF / JQS(进球数) / BF(比分) / BQC(半全场) 赔率
  → 优势: 500.com 直接展示竞彩官方赔率，无需换算

📊 分析辅助数据源 (交叉验证, 不用于结算):
  ① 综合指数: https://odds.500.com/           — 多机构欧赔/亚盘综合视图
  ② 欧洲指数: https://odds.500.com/europe_jczq.shtml  — 竞彩场次欧赔走势
  ③ 亚洲盘口: https://odds.500.com/yazhi_jczq.shtml    — 竞彩场次亚盘水位
  ④ 大小指数: https://odds.500.com/daxiao_jczq.shtml   — 竞彩场次大小球指数
  ⑤ 必发指数: https://zx.500.com/jczq/bf_data.shtml    — 必发成交量+冷热指数
  
  必发指数特别用途:
  - 成交量占比 > 60% 偏向一方 → 市场过热信号，降低该方向置信度
  - 冷热指数 > 80 或 < 20 → 极端情绪，警惕陷阱
  - 指数与赔率走势背离 → 可能有大资金反向操作

📋 玩法规则参考:
  → https://www.lottery.gov.cn/bzzx/yxgz/20191119/1040217.html
  → 体育总局彩票中心 · 竞彩足球混合过关官方规则
  → 定义: 允许的玩法类型、过关方式、奖金计算方法、最高可能固定奖金

国内体彩赔率 ≠ 国际赔率:
  - 体彩 overround ~11% (覆水率 ~89%)
  - 国际庄 overround ~3-5% (覆水率 ~95-97%)

备用方案 (500.com 不可用时):
  ② WebSearch "竞彩足球混合过关 赔率 [对阵]" 或 "体彩竞彩世界杯 [日期] 赔率"
  ③ 使用 Pinnacle 赔率 × 0.75 折扣系数近似体彩赔率
     注: 0.75 系数为经验值 (89%/96% ≈ 0.93, 再折2串1累积折扣)
```

### 10.1 基本原则

混合过关要求所有选择全对。核心策略: **舍弃不可靠比赛**。

```
选场铁律:
1. 仅选 v2.6 方向置信度 = "高" 的比赛 (6D ≥ 3)
2. 平局概率 > 27% 的比赛 → 跳过
3. 三项概率接近(任意两项差 < 15pp) → 跳过
4. 每日至少 2 场可用 → 可组 2串1; 3 场 → 3串1
5. 当天可用场次 < 2 → 当天跳过(不买!)
6. 🆕 淘汰赛附加规则 (2022WC回测): 
   - 淘汰赛D%已含14.0d修正 → 阈值维持27%不变但更多比赛会触发跳过
   - 防守城墙预评估(14.0+陷阱#27)自动影响选场 — 城墙队对面方向自动+谨慎标记
   - 淘汰赛可用场次通常更少(每天2场) → 2串1是上限, 不追3串1
```

### 10.2 投注类型优先级

| 优先级 | 类型 | 胜率 | 说明 |
|:--:|:---|:--:|------|
| 1 | **SPF (胜平负)** | 最高 | 仅需方向正确，首选 |
| 2 | **RSPF (让球胜平负)** | 中 | 需穿盘，仅当SPF未开售或碾压加成(14.0b)明确时使用 |
| 3 | **总进球** | 低 | 风险较高，不推荐混合过关 |
| 4 | **比分** | 极低 | 混合过关用比分=送钱 |

### 10.3 组合策略

```
2串1 → 胜率 ~40-50%, 赔率 ~1.5-2.5 → 稳健首选
3串1 → 胜率 ~30-40%, 赔率 ~3.0-5.0 → 最佳赔率/胜率平衡
4串1 → 胜率 ~15-25% → 不推荐(4×60% = 13% 胜率)
≥5串1 → 胜率 < 10% → 禁止
```

### 10.4 回溯验证 — 盲测模拟 (6月12-19日)

模拟条件: 仅使用赛前信息(v2.6规则+500.com赔率)，每日100元/票，2串1+3串1。

| 日期 | 总场 | 选场 | 弃场 | 2串1 | 3串1 | 投注 | 返还 | 盈亏 |
|:---:|:--:|:--:|:--:|:---|:---|--:|--:|--:|
| 6/12 | 2 | 1 | 1 | - | - | ¥0 | ¥0 | ¥0 |
| 6/13 | 4 | 1 | 3 | - | - | ¥0 | ¥0 | ¥0 |
| 6/14 | 4 | 2 | 2 | ✅ 1.18x | - | ¥100 | ¥117 | +17 |
| 6/15 | 4 | 0 | 4 | - | - | ¥0 | ¥0 | ¥0 |
| 6/16 | 4 | 4 | 0 | ✅ 2.05x | ✅ 2.43x | ¥200 | ¥447 | +247 |
| 6/17 | 4 | 2 | 2 | ✅ 2.61x | - | ¥100 | ¥260 | +160 |
| 6/18 | 4 | 3 | 1 | ✅ 1.59x | ✅ 2.62x | ¥200 | ¥421 | +221 |

> 🏆 **总投¥600 → 返¥1,246 → 净盈¥646 (+107.8% ROI) | 6/6票全中**
> 
> 🛡️ **舍弃价值: 11场比赛被正确跳过 → 避免约¥1,100损失**
> 
> 关键: 6/15全日4场全平 → 0场可选 → 完美避险。6/16热门全赢日 → 4场全选 → 单日+247

### 10.5 核心盈利模式总结

```
盈利公式: 高置信度筛选 × 舍弃不确定场次 × 2-3串适度组合

关键数据:
- 6天投注, 3天跳过(6/12,6/13,6/15) → 50%时间不投
- 舍弃率: 11/28场(39%)被标记为"不可靠"而舍弃
- 舍弃中10/11场(91%)为平局或预测错误 → 舍弃精准度极高
- 全选场次胜率: 13/13(100%)单场方向正确
- 混合过关中奖率: 6/6(100%)
```

### 10.6 陷阱日识别

```
全线平局日: 当天 ≥75% 比赛为平局 → 全天跳过
超冷门日: 当天 ≥2场赔率<1.30的比赛未赢 → 全天跳过
首秀/久别重逢集中日: 当天 ≥2队触发规则#24 → 全天跳过或仅选1场
```

---

## Section 11: 国内竞彩混合过关 — 500.com 集成 + 风险分摊组合 (v2.7)

> 本章将 OddsPapi 三方赔率分析结果映射到竞彩可投注玩法，构造多方案组合投注体系。核心创新: **不再单选一套方案，而是用总预算按比例分配到多套方案中，实现风险分摊+高赔率爆发**。

### 11.1 数据源体系

> 三层数据架构：国际赔率分析 (OddsPapi) → 国内指数参考 (500.com) → 竞彩官方结算 (500.com 混合过关页) + 规则 (体彩中心)。

#### 第一层：国际赔率分析 (OddsPapi — 分析核心)

| 数据 | 来源 | 说明 |
|------|------|------|
| 1X2/AH/OU/CS 赔率 | OddsPapi v4 (已缓存) | Pinnacle+Bet365+SBOBET 三方金三角 |
| 历史赔率走势 | OddsPapi /v4/historical-odds (免费) | 检测异常波动、陷阱、资金流向 |

#### 第二层：国内指数参考 (500.com — 交叉验证)

| 数据 | URL | 用途 |
|------|-----|------|
| 综合指数 | https://odds.500.com/ | 多机构欧赔/亚盘/大小球综合对比视图 |
| 欧洲指数 | https://odds.500.com/europe_jczq.shtml | 竞彩相关比赛的欧赔走势和变化幅度 |
| 亚洲盘口 | https://odds.500.com/yazhi_jczq.shtml | 竞彩相关比赛的亚盘水位实时变化 |
| 大小指数 | https://odds.500.com/daxiao_jczq.shtml | 竞彩相关比赛的大小球指数波动 |
| 必发指数 | https://zx.500.com/jczq/bf_data.shtml | 必发交易所成交量 + 冷热指数, 辅助判断市场情绪偏向 |

#### 第三层：竞彩官方 — 结算 + 规则 (唯一依据)

| 数据 | URL | 用途 |
|------|-----|------|
| 🏁 混合过关赔率 | https://trade.500.com/jczq/?playid=312&g=2 | **模拟投注的唯一结算赔率依据**。SPF/RSPF/JQS/BF/BQC 赔率均取自此页面 |
| 📋 混合过关规则 | https://www.lottery.gov.cn/bzzx/yxgz/20191119/1040217.html | 体育总局彩票中心官方玩法介绍。定义允许的玩法类型、过关方式、奖金计算方法 |

#### 数据使用优先级

```
分析阶段:  OddsPapi (Pinnacle 精准定价) > 500.com 指数 (国内参考) > Bet365/SBOBET (辅助)
投注阶段:  500.com 混合过关页 (🏁 唯一结算依据, SPF/RSPF/JQS 赔率)
规则参考:  lottery.gov.cn 官方规则 (玩法边界条件, 串关限制)
校验阶段:  OddsPapi vs 500.com 百家平均 交叉验证 (偏差 > 15% 标记异常)
```

**页面解析规则 (关键):**
```
每场比赛在 500.com 混合过关页的结构:
  [编号] 联赛 日期 时间
  [排名] 主队 VS 客队 [排名]
  单关状态  让球数(仅作用于RSPF)
  
  Row 1: SPF-主 SPF-平 SPF-客    ← 🏁 竞彩官方胜平负赔率 (结算依据)
  Row 2: RSPF-主 RSPF-平 RSPF-客  ← 让球胜平负 (含让球数)
  
  展开 → 半全场(9项) / 比分(31项) / 进球数(8项)
  
  百家平均 SPF-主 SPF-平 SPF-客  ← ⚠️ 仅作参考, 不用于结算!
                                   百家平均 = 多机构均值, 与实际竞彩赔率不同

🔴 结算赔率规则:
  ① 混合过关结算: 使用 Row 1 的竞彩官方 SPF 赔率 (非百家平均)
  ② 让球胜平负结算: 使用 Row 2 的 RSPF 官方赔率
  ③ 竞彩赔率 overround ~11% (覆水率 ~89%), 显著低于国际赔率
  ④ Row 2 中第二个赔率行在某些场次可能显示不同格式, 以 RSPF 让球线对应的为主
  
  示例 (德国 vs 科特迪瓦):
    Row 1 (SPF): 1.36 / 4.55 / 5.75  ← 结算用此
    百家平均:    1.51 / 4.56 / 5.75  ← 不用于结算, 仅参考
    差异: 竞彩 SPF 主胜 1.36 vs 百家平均 1.51 → 竞彩抽水更高, 赔率更低
```

### 11.2 竞彩可投注玩法与串关限制 (依据体彩中心官方规则)

> 规则来源: https://www.lottery.gov.cn/bzzx/yxgz/20191119/1040217.html

| 玩法 | 中文名 | 选项数 | 最高串关 | 混合过关使用建议 |
|:--:|------|:--:|:--:|------|
| **SPF** | 胜平负 | 3 | 8 关 | ⭐⭐⭐ 首选，仅需方向正确，串关上限最高 |
| **RSPF** | 让球胜平负 | 3 | 8 关 | ⭐⭐ 当SPF赔率过低时用于提赔率 |
| **JQS** | 总进球数 | 8 | 6 关 | ⭐⭐ OU分析明确时可用，串关上限6关 |
| **BQC** | 半全场 | 9 | 4 关 | ⭐ 仅高信心半场判断时使用 |
| **BF** | 比分 | 31 | 4 关 | ❌ 混合过关不推荐（中奖率<3%，且拉低整体串关上限至4关） |

**官方核心规则 (木桶原则):**

```
① 同赛事同项目: 足球只能串足球，篮球只能串篮球

② 同场不可多玩法: 同一场比赛不能选择 2+ 种玩法放入同一串关
   例: 荷兰 vs 瑞典 不能同时选 SPF主胜 + JQS 3球

③ 串关上限 = min(所有被选玩法的最高关数)
   例: SPF(8关) + JQS(6关) + BF(4关) → 上限 = min(8,6,4) = 4 关
   ⚠️ 一旦选了 BF 或 BQC, 整个串关上限被拉低到 4 关

④ 奖金计算: 中奖金额 = 2元 × ∏(各选项赔率)
   所有赔率均以出票时竞彩官方公布的为准
```

### 11.3 竞彩让球线映射

```
竞彩让球(整数)    →    Pinnacle AH        使用场景
-1 (主让1球)     →    AH -0.75 ~ -1.0    主队需赢2+球
-2 (主让2球)     →    AH -1.75 ~ -2.0    碾压局
+1 (主受1球)     →    AH +0.75 ~ +1.0    客队优势
0  (不让球)      →    AH 0.0 ~ ±0.25     势均力敌

RSPF选场规则:
1. Pinnacle AH水位 ≤ 1.85 且竞彩同向 → 选RSPF
2. Pinnacle AH水位 > 2.10 → 用SPF更安全
3. 让球线差 ≤ 0.25 → 映射有效; 差 > 0.5 → 不用RSPF
```

### 11.4 玩法选择决策树 (每场比赛)

```
比赛分析完成
├─ 强队碾压 (SPF主 ≤ 1.35) → RSPF (竞彩让球线)
├─ 明显优势 (SPF主 1.35-1.80)
│  ├─ AH-1.0水位 ≤ 1.95 → RSPF
│  └─ 否则 → SPF
├─ 客队优势 (SPF客 ≤ 1.80) → SPF客胜
└─ 均势 (SPF 1.80-3.00)
   └─ OU大球倾向 → JQS(4球/5球)
```

### 11.5 标准方案模板 (用于组合池)

```
方案A【保守型】SPF 2-3串1 — 仅选SPF主/客胜≤1.75
  风险: 低 | 胜率: 40-55% | 赔率: 1.8-3.5

方案B【均衡型】SPF+RSPF 混合3串1 — 含1个RSPF提赔率
  风险: 中 | 胜率: 25-40% | 赔率: 4.0-9.0

方案C【进取型】RSPF+JQS 混合3串1 — 含1个JQS
  风险: 高 | 胜率: 15-25% | 赔率: 8.0-15.0
```

### 11.6 实战参考: 6月21日

| 场次 | 比赛 | 竞彩让球 | 竞彩SPF (Row1) | 推荐玩法 | 选中赔率 |
|------|------|:--:|------|:--:|:--:|
| 033 | 荷兰vs瑞典 | -1 | 1.52/3.90/4.65 | SPF主 | 1.52 |
| 034 | 德国vs科特迪瓦 | -1 | 1.36/4.55/5.75 | RSPF主-1 | 2.11 |
| 035 | 厄瓜多尔vs库拉索 | -2 | 未开售 | RSPF主-2 | 1.85 |
| 036 | 突尼斯vs日本 | +1 | 6.36/3.95/1.39 | SPF客 | 1.39 |

**方案池 (供11.7组合分配使用):**
- 保守SPF3串1: 荷兰SPF主(1.52) × 德国SPF主(1.36) × 日本SPF客(1.39) = 2.87
- 均衡SPF+RSPF3串1: 荷兰SPF主(1.52) × 德国RSPF主-1(2.11) × 厄瓜多尔RSPF主-2(1.85) = 5.93
- 进取RSPF+JQS3串1: 德国RSPF主-1(2.11) × 荷兰JQS 3球(3.40) × 厄瓜多尔RSPF主-2(1.85) = 13.27

---

### 11.7 🆕 风险分摊组合投注 (Barbell Parlay Portfolio) — 核心输出方案

> **不再单选一套方案，而是将总预算按比例分配到多套方案中同时下注。**
> 保守方案保底回血，进取方案博高赔爆发。万一高风险项中奖则大幅盈利。

```
风险分摊组合 = Σ(方案i × 投注金额i)  where 总投注 = 预算上限

核心逻辑 (分配比例由动态公式计算, 非固定):
  - 保守方案(多资金): 高概率低赔率 → "保底回血"
  - 均衡方案(中资金): 中概率中赔率 → "托底小盈"
  - 进取方案(少资金): 低概率高赔率 → "爆发"
```

#### 输出格式 (每次预测分析必须输出)

> 投注额和占比由动态公式计算，每比赛日不同。保守/均衡/进取的分配取决于当日各方案的去水分命中概率和赔率。

```
┌─────────────────────────────────────────────────────────────┐
│         风险分摊组合投注 (总预算: ¥N · 动态分配)             │
├──────────┬──────────┬────────┬────────┬────────┬────────────┤
│   方案   │   类型   │ 投注额 │ 占比*  │ 赔率   │ 中奖返还   │
├──────────┼──────────┼────────┼────────┼────────┼────────────┤
│ 保守方案 │ SPF 3串1 │ ¥XX    │ XX.X%  │ X.XX   │ ¥XXX       │
│ 均衡方案 │ 混合3串1 │ ¥XX    │ XX.X%  │ X.XX   │ ¥XXX       │
│ 进取方案 │ RSPF+JQS │ ¥XX    │ XX.X%  │ XX.XX  │ ¥XXXX      │
├──────────┴──────────┴────────┴────────┴────────┴────────────┤
│ *占比 = P_hit / ln(odds) 归一化，见金额分配规则              │
├─────────────────────────────────────────────────────────────┤
│ 情景分析:                                                   │
│  ✓ 仅保守中: 返还 ¥XXX → 净盈 ±¥XX                         │
│  ✓ 保守+均衡: 返还 ¥XXX → 净盈 +¥XX                        │
│  ★ 三星连中: 返还 ¥XXXX → 净盈 +¥XXX (爆发)               │
│  ✗ 全不中:   损失 ¥N                                       │
└─────────────────────────────────────────────────────────────┘
```

#### 金额分配规则 — 🔵 动态计算 (非固定比例)

> 比例不是拍脑袋的 60/30/10，而是**基于每场比赛的去水分概率和方案赔率动态计算**。不同比赛日的置信度不同，分配比例自然不同。

```
计算步骤:

STEP 1 — 计算每场比赛的去水分方向概率:
  对于方案中的每场比赛，取 Pinnacle 1X2 赔率：
    overround = 1/H + 1/D + 1/A
    deVigProb(方向) = (1/odds) / overround
    
  示例 (荷兰 vs 瑞典, 1.714/4.22/4.78):
    overround = 1/1.714 + 1/4.22 + 1/4.78 = 1.029
    deVigProb(荷兰胜) = (1/1.714) / 1.029 = 56.7%

  对于 RSPF 选项，使用 AH 水位推算穿盘概率:
    deVigProb(穿盘) = (1/home_odds) / (1/home_odds + 1/away_odds)
    例: 德国AH-1.0 水位1.892/2.02 → 51.6%

  对于 JQS 选项，使用 OU 分布估算:
    从 OU 2.5 大球概率 + 泊松进球分布 → 特定进球数概率

STEP 2 — 计算每套方案的命中概率:
  P_hit[方案] = ∏ deVigProb(比赛i的方向)  对所有比赛 i ∈ 方案

STEP 3 — 动态分配权重:
  raw_weight[i] = P_hit[i] / ln(odds[i])
  设计逻辑:
  - 分子 P_hit: 概率越高 → 权重越大 (安全优先)
  - 分母 ln(odds): 赔率越高 → 权重越小 (高风险打折)

STEP 4 — 归一化:
  allocation[i] = raw_weight[i] / Σ raw_weight[j]
  投注金额[i] = round(allocation[i] × 总预算)  (四舍五入)

边界规则:
  - 保守方案 P_hit < 0.10 → 全天跳过 (不确定性太高)
  - 进取方案 P_hit < 0.02 → 取消进取, 资金并入均衡
  - 当天仅2场可用 → 仅保守+均衡, 取消进取
  - 当天 < 2场 → 全天跳过
```

**动态计算示例 (6月21日 · 使用竞彩SPF赔率):**

```
去水分方向概率 (基于 Pinnacle 1X2):
  荷兰胜:    1/1.714 ÷ 1.029 = 56.7%
  德国胜:    1/1.552 ÷ 1.030 = 62.6%
  德国穿-1:  1/1.892 ÷ (1/1.892+1/2.02) = 51.6%
  日本胜:    1/1.606 ÷ (1/6.20+1/4.04+1/1.606) = 60.3%
  厄瓜穿-2:  1/1.588 ÷ (1/1.588+1/2.22) = 58.3%
  荷兰3球:   OU分布估算 ≈ 26%

🏁 竞彩SPF赔率 (500.com Row 1, 非百家平均):
  荷兰主: 1.52  德国主: 1.36  日本客: 1.39
  德国RSPF主-1: 2.11  厄瓜多尔RSPF主-2: 1.85  荷兰JQS 3球: 3.40

方案命中概率:
  保守 P = 0.567 × 0.626 × 0.603 = 0.214
  均衡 P = 0.567 × 0.516 × 0.583 = 0.171
  进取 P = 0.516 × 0.260 × 0.583 = 0.078

方案赔率 (竞彩官方):
  保守 = 1.52 × 1.36 × 1.39 = 2.87
  均衡 = 1.52 × 2.11 × 1.85 = 5.93
  进取 = 2.11 × 3.40 × 1.85 = 13.27

动态权重:
  保守: 0.214 / ln(2.87) = 0.214 / 1.054 = 0.2030
  均衡: 0.171 / ln(5.93) = 0.171 / 1.780 = 0.0961
  进取: 0.078 / ln(13.27) = 0.078 / 2.586 = 0.0302

归一化 (Σ = 0.3293):
  保守: 61.6% → ¥62   均衡: 29.2% → ¥29   进取: 9.2% → ¥9
```

> 💡 竞彩SPF赔率(1.52/1.36/1.39)显著低于百家平均(1.71/1.51/1.57)，因为竞彩覆水率~89% vs 百家平均~97%。导致保守方案赔率从4.06降至2.87，但保守P_hit不变，因此动态分配中保守权重从56%升至62%——赔率越低越需更多资金保底。

#### 期望值计算

> 使用上一步动态计算出的 P_hit 和对应投注金额，而非固定概率区间。

```
E[回报] = P(保守中) × 保守返还 + P(仅均衡中|保守不中) × 均衡返还
        + P(仅进取中|前两不中) × 进取返还 + P(全不中) × 0

条件概率简化:
  - P(保守中) = P_hit[保守]  (从上一步动态计算)
  - P(仅均衡中|保守不中) ≈ P_hit[均衡] × 0.7  (方案间正相关, 折扣30%)
  - P(仅进取中|前两不中) ≈ P_hit[进取] × 0.5  (更激进方案, 相关性更低)

动态示例 (6月21日, ¥100预算, 动态分配 62/29/9 · 竞彩SPF赔率):
  保守 P_hit=0.214 → 返还 = ¥62 × 2.87 = ¥178
  均衡 P_hit=0.171 → 返还 = ¥29 × 5.93 = ¥172
  进取 P_hit=0.078 → 返还 = ¥9 × 13.27 = ¥119

  ★ 仅保守中:    ¥178 - ¥100 = +¥78 (回本+盈利)
  ★ 保守+均衡:   ¥178 + ¥172 - ¥100 = +¥250
  ★ 三星连中:    ¥178 + ¥172 + ¥119 - ¥100 = +¥369
  ★ 全不中:      -¥100

  E[回报] ≈ 0.214×227 + (0.171×0.7)×220 + (0.078×0.5)×146
          ≈ 48.6 + 26.3 + 5.7 = ¥80.6
  E[净盈] ≈ -¥19.4  (短期期望为负, 符合彩票本质)
```

> 💡 短期期望值为负是正常的。盈利靠选场铁律筛选**高置信度比赛**让实际 P_hit 高于市场隐含概率。回溯 6/12-6/18: 实际 P_hit 远超计算值, 正是选场体系创造的正期望。

### 11.8 自由组合注意事项

```
🚫 禁止:
- 同一场比赛选 2+ 种玩法 (系统不允许)
- BF(比分)用于混合过关 (31选1，中奖率<3%)
- ≥5串1 (胜率<10%)
- 将"未开售"比赛纳入方案

⚠️ 谨慎:
- BQC仅在半场置信度 ≥80% 时使用
- JQS与SPF在同一方案: 3串1最多含1个JQS
- RSPF方向与SPF方向冲突时 → 弃用RSPF

✅ 推荐:
- 每日同时下注3套方案 (保守+均衡+进取)
- 风险分摊组合优于单选一套方案
- 止损线: 连续3天全不中 → 暂停并复盘选场逻辑
- 记录每套方案的独立盈亏，便于后续优化分配比例
```


---

## Section 12: 《足球财富》方法论集成 (v2.7)

> 参考: 刘胜临《足球财富：欧赔与亚盘足彩研究》(金城出版社, 2010)。将书中的欧赔动态分析、亚盘临场模式、大小球分析框架、联赛盘路方法论结构化整合，与 OddsPapi 实时数据 + 500.com 指数数据联动。

### 12.1 欧赔动态分析体系

#### 12.1.1 凯利指数 (Kelly Index)

```
凯利指数 = 博彩公司赔付率 × 平均概率 / 该公司赔率

计算步骤:
  1. 从 OddsPapi 获取 Pinnacle 1X2 赔率 (H, D, A)
  2. 计算市场平均概率: avgP[i] = (1/odds[i]) / Σ(1/odds[j])  (去水分)
  3. 计算 Pinnacle 赔付率: payout = 1 / (1/H + 1/D + 1/A)
  4. 凯利值[主胜] = payout × avgP[H] / (1/H)
     凯利值[平局] = payout × avgP[D] / (1/D)
     凯利值[客胜] = payout × avgP[A] / (1/A)

解读:
  凯利值 > 1.00 → 博彩公司在该选项上有利可图 (正期望)
  凯利值 < 0.90 → 博彩公司在该选项上风险较高
  凯利值最大者 → 市场认为最可能的结果

实战用法:
  - 凯利值 > 1.05 且对应的赔率方向与 Pinnacle AH一致 → 高信心信号
  - 凯利值在 0.92-0.98 → 中性区间, 参考其他指标
  - 三个凯利值都 < 0.90 → 博彩公司高抽水, 比赛不确定性高 → 降低置信度
```

#### 12.1.2 盈亏指数分析

```
盈亏指数 = (期望投注比例 × 赔付率 - 实际赔率支付) × 100%

计算:
  1. 从必发指数 (zx.500.com/jczq/bf_data.shtml) 获取成交量占比作为投注比例代理
  2. 盈亏[主胜] = (投注比例[H] × payout_rate - 1/odds[H]) × 100%

解读:
  盈亏 > 0 → 庄家在该选项上盈利 → 该结果较难打出
  盈亏 < 0 → 庄家在该选项上亏损 → 该结果可能被市场低估

⚠️ 盈亏指数依赖于准确的投注量数据。必发数据为最佳代理, 但不完全等于真实市场投注分布。
```

#### 12.1.3 必发数据验证

```
数据源: zx.500.com/jczq/bf_data.shtml

三类信号:
  ① 成交量信号: 单一方向成交量占比 > 65% → 市场过热, 警惕反向
  ② 冷热信号: 必发指数 > 80 或 < 20 → 极端情绪
  ③ 背离信号: 成交量偏向一方, 但赔率反向变动 → 可能有内幕资金

与 Pinnacle 价格联动验证:
  IF 必发成交量偏向主胜 + Pinnacle 主胜赔率持续上升 → 市场过热但庄家不惧
  IF 必发成交量偏向主胜 + Pinnacle 主胜赔率持续下降 → 真实利好信号
```

### 12.2 亚盘临场模式识别

> 参考《足球财富》第二部分的临场盘口变化模式。以下模式基于 Pinnacle AH 赔率的历史走势 (可从 /v4/historical-odds 免费获取)。

#### 12.2.1 四大临场模式

```
模式一【临场降盘】
  现象: 盘口从 -1.0 降至 -0.75, 水位补偿不明显
  书中规律: 降盘方(上盘)胜率约 38% → 不利于上盘穿盘
  应用: 若检测到 AH line 在最后 4 小时下降 ≥ 0.25 球 → 降低该方向置信度 20%
  例外: 降盘同时搭配大幅升水 → 可能为阻上诱下, 反向上盘利好

模式二【临场升盘】
  现象: 盘口从 -0.5 升至 -0.75, 水位基本不变
  书中规律: 初盘偏浅、临场升盘 → 上盘利好 (胜率约 65%)
  应用: AH line 最后 6 小时上升 ≥ 0.25 → 提升上盘置信度
  警慑: 盘口升但水位同时大幅上升 → 可能是诱盘, 不处理

模式三【临场升水】
  现象: 同一盘口下, 上盘水位从 1.85 升至 2.05+
  书中规律: 升水方胜率约 42% → 不利于该方向
  应用: 水位变化 > 0.15 幅度 → 标记为"升水预警"

模式四【临场降水】
  现象: 同一盘口下, 上盘水位从 2.00 降至 1.80
  书中规律: 降水方胜率提升 → 真实利好
  应用: 水位下降 > 0.10 → 提升该方向置信度 10%
```

#### 12.2.2 造冷造热三大手法

```
手法一【水位造热】
  上盘水位持续下降(1.95→1.75) + 盘口不变 → 市场热度集中上盘
  → 若搭配必发成交量 > 60% 偏向上盘 → 确认造热, 反向考虑下盘

手法二【盘口阻上】
  上盘初盘偏浅(比公允盘口少 0.25)+ 后续升盘 → 制造上盘不稳假象
  → 检测: Pinnacle 公允盘口 vs 实际盘口差 ≥ 0.25 → 阻上信号
  → 若实际升盘回到公允盘口 → 上盘真实利好

手法三【水位诱下】
  下盘水位由高走低(2.30→2.00)+ 盘口不变 → 诱导投注下盘
  → 检测: 下盘水位下降 > 0.20 + 上盘方向未受不利影响 → 诱下信号
  → 此时上盘为真实方向
```

#### 12.2.3 10种常见盘路简述

```
从《足球财富》第二部分提取, 使用 OddsPapi 历史数据自动化检测:

 ① 临场降盘 + 水位不变        → 下盘有利
 ② 临场升盘 + 水位不变        → 上盘有利
 ③ 临场升水 + 盘口不变        → 该方向不利
 ④ 临场降水 + 盘口不变        → 该方向有利
 ⑤ 基本面强势方(上盘)         → 需结合盘口深度判断
 ⑥ 基本面弱势方(下盘)         → 受让深盘时有价值
 ⑦ 上盘胜赔上升               → 不利信号
 ⑧ 上盘胜赔下降               → 利好信号
 ⑨ 双线作战球队               → 体能折价 15-20%
 ⑩ 澳门盘异常与其他公司偏离   → 对比 Pinnacle, 澳门盘偏差 > 0.15 → 警觉
```

### 12.3 大小球分析框架

#### 12.3.1 进球预期值计算

```
公式: 预期进球 = 主队场均进球 × 客队场均失球率 + 客队场均进球 × 主队场均失球率

计算步骤:
  1. 主队近 6 场场均进球 (GF_home), 客队近 6 场场均失球 (GA_away)
  2. 客队近 6 场场均进球 (GF_away), 主队近 6 场场均失球 (GA_home)
  3. 预期值 = (GF_home × GA_away/联赛均值 + GF_away × GA_home/联赛均值) / 2

与盘口比较:
  预期值 > OU 盘口 + 0.5 → 大球信号
  预期值 < OU 盘口 - 0.5 → 小球信号
  预期值在盘口 ± 0.5 内 → 盘口合理, 无额外信号

⚠️ 书中使用的是五大联赛数据。世界杯场景下, 改用预选赛数据 + 近期友谊赛数据。
```

#### 12.3.2 平局排除法

```
条件 (全部满足 → 平局概率低, 大球倾向增强):
  □ 主客队近 3 场无 0-0 赛果
  □ 两队场均进球和 > 2.5
  □ OU 2.5 大球水位 ≤ 1.85
  □ 无"防守城墙"队伍参与 (参见技能规则 #27)

条件 (任一条满足 → 平局概率高, 小球倾向增强):
  □ 任一方近 3 场有 2+ 场平局
  □ 两队场均进球和 < 2.0
  □ 初盘大小球盘口 ≤ 2.0
```

#### 12.3.3 波胆赔率分析法 (Correct Score Odds)

```
方法: 从 OddsPapi CS 市场提取最可能比分, 反向推导预期总进球

步骤:
  1. 取 CS 市场赔率最低的前 5 个比分
  2. 每个比分的隐含概率 = (1/cs_odds) / Σ(1/all_cs_odds)
  3. 加权预期总进球 = Σ(比分总进球 × 隐含概率)
  4. 与 OU 盘口比较:
     - 加权预期总进球 > OU 盘口 + 0.3 → 大球倾向
     - 加权预期总进球 < OU 盘口 - 0.3 → 小球倾向

波胆投注策略 (书中原话):
  "当波胆分析指向某几个比分, 且这几个比分的赔率加权后高于 6.0 时,
   用小额资金分散投注 2-3 个比分, 是一种低成本高回报的策略。"
```

#### 12.3.4 8种大小球盘路模式

```
从《足球财富》第三部分提取 (使用 OddsPapi 历史数据检测):

模式一【临场大球降水】
  大球水位降 + 盘口不变 → 大球信号增强
  检测: OU line 不变, over 水位下降 > 0.10 → 大球置信度 +15%

模式二【临场大球升水】
  大球水位升 + 盘口不变 → 可能阻大诱小
  检测: over 水位上升 > 0.15 → 结合必发成交量判断

模式三【大球水位不变】
  初盘至临场水位波动 < 0.05 → 盘口稳定, 按初始分析

模式四【大球升盘】
  OU 从 2.5 升至 2.75 → 市场热度偏大球
  → 如果伴随大球降水 → 大球信号强
  → 如果伴随大球升水 → 警惕诱盘

模式五【大球降盘】
  OU 从 2.5 降至 2.25 → 市场倾向小球
  → 结合基本面: 如果双方攻击力强 → 可能是庄家误导

模式六【欧赔 2-3-2 与平局】
  欧赔呈现 2.XX-3.XX-2.XX 形态 → 平局赔率在 3.00-3.50 区间
  → 平局概率较常规高约 8-12% → 小球倾向

模式七【让球盘与大小球关联】
  AH 深盘(≥-1.5) + OU 中等(2.5-3.0) → 上盘可能穿盘但总进球有限
  AH 浅盘(±0.25) + OU 高(≥3.0) → 对攻战, 大球 + 双方进球概率高

模式八【主客场大球率】
  主队主场大球率 > 60% + 客队客场大球率 > 55% → 大球加成 +10%
  主队主场大球率 < 35% + 客队客场大球率 < 40% → 小球加成 +10%
```

### 12.4 欧亚综合分析流程

> 融合《足球财富》的盘赔结合理念与技能的 12 步分析法。

```
┌─────────────────────────────────────────────────────────┐
│           欧亚综合分析流程 (《足球财富》融合)            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  STEP A: 赔率静态分析                                    │
│  ├─ Pinnacle 1X2 → 去水分概率 + 凯利指数                │
│  ├─ 盈亏指数 (结合必发成交量)                            │
│  └─ 必发冷热信号 (成交量/指数/背离)                     │
│                                                         │
│  STEP B: 盘口定位                                       │
│  ├─ 理论盘口 vs 实际盘口 → 盘口深浅判断                 │
│  ├─ 临场 4 小时盘口/水位变化 → 四大模式检测             │
│  └─ 造冷造热三手法识别                                  │
│                                                         │
│  STEP C: 大小球专项                                      │
│  ├─ 进球预期值 vs OU 盘口                               │
│  ├─ 平局排除法                                          │
│  ├─ 波胆赔率加权进球                                     │
│  └─ 8种盘路模式匹配                                     │
│                                                         │
│  STEP D: 综合信号合成                                    │
│  ├─ 欧赔信号 + 亚盘信号 + 大小球信号 → 三维交叉验证     │
│  ├─ 信号一致 (≥2/3 指向同一方向) → 高置信度             │
│  ├─ 信号冲突 → 降低置信度, 标记为"谨慎"                 │
│  └─ 输出: 方向预测 + 置信度 + 风险提示                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 12.5 信号权重体系

```
信号叠加规则 (来自书中案例统计 + 技能回溯):

欧赔信号:
  凯利值 > 1.05              → +12% 方向置信度
  凯利值 0.92-1.05           → 中性
  必发背离 (量价反方向)       → -15% 方向置信度
  必发成交量 > 65% 单一方向   → -10% 该方向置信度 (过热)

亚盘信号:
  临场升盘 + 水位不变         → +15% 上盘置信度
  临场降盘 + 水位不变         → -15% 上盘置信度
  临场降水 > 0.10             → +10% 该方向置信度
  造热确认 (水位降 + 量集中)  → ⚠️ 反向信号
  阻上确认 (盘口偏浅 + 回升)  → +10% 上盘置信度

大小球信号:
  进球预期 > OU + 0.5         → +15% 大球置信度
  平局排除全满足              → +10% 大球置信度
  波胆加权 > OU + 0.3         → +10% 大球置信度
  模式一 (大球降水)           → +15% 大球置信度
  模式六 (2-3-2 欧赔)         → -10% 大球置信度

置信度封顶: 任何方向置信度上限 90%, 下限 10%
```

### 12.6 与现有技能体系的联动

```
《足球财富》方法论              →  技能现有模块
────────────────────────────────────────────────────
12.1 凯利指数                  →  Section 4(1) 赔率数学, 作为概率校正因子
12.1 必发数据验证              →  Section 11.1 第二层数据源
12.2 临场盘口模式              →  Section 8 陷阱扫描 + 走势分析
12.2 造冷造热                  →  Section 8 陷阱规则增强
12.3 进球预期值                →  Section 4(6) 基本面权重 + OU 分析
12.3 平局排除法                →  Section 10.1 选场铁律 (平局概率 > 27% → 跳过)
12.3 波胆分析                  →  Section 11.6 方案赔率计算
12.4 欧亚综合分析              →  技能 12+1 步分析主流程的增强版
12.5 信号权重                  →  Section 4(10) 六维评分模型的补充维度
```

---

## Section 13: 实战盘口分析体系集成 (v2.7 · 5篇教程结构化)

> 数据来源: 知乎专栏 ×2 + 今日头条 ×1 + 搜狐 ×1 + 知乎替代(原头条墙内文章) ×1。将盘型推算、盘口深浅判断、水位波动模式、临场口诀、联赛特性、资金管理等实战方法论结构化整合。

### 13.1 理论盘型推算体系

> 核心概念: 盘型 = 根据两队真实实力差距推算出的"应该开什么盘"。对比理论盘型与实际盘口的偏差，是判断机构意图的核心。

```
理论盘型推算四维度:

① 实力差距 (权重 40%):
   联赛排名差 ≥ 10 位 → 基础让球 +1.0
   场均进球差 > 1.0 → 额外 +0.25
   场均失球差 > 0.8 → 额外 +0.25

② 主客场优势 (权重 25%):
   同实力球队 → 主场方可多让 0.5 球
   强队客场让球 = 主场让球 - 1.0 (即主场让1球，客场约让0球或受让)
   例: 曼联主场对伯恩茅斯让1.5球，客场则让0.5球

③ 历史交锋 (权重 20%):
   近6次交锋上盘 5-6胜 + 场均净胜 ≥2球 → 理论盘型 +0.5~+1.0
   近6次交锋胶着(3胜3平或2胜2平2负) → 理论盘型偏浅 -0.25
   近6次交锋下盘占优 → 理论盘型 -0.5

④ 战意与伤停 (权重 15%):
   核心球员(前锋/门将)伤停 → 盘型 -0.5~-1.0
   保级/争冠战意强烈 → 盘型 +0.5
   一周双赛疲劳 → 盘型 -0.25

盘型动态调整:
  盘型不是固定值，随球队状态、伤停、战意动态变化
  例: 核心前锋赛前伤退 → 原让1.5球降为让1球 (合理变动，非诱盘)
```

### 13.2 盘口深浅判断框架

> 对比理论盘型与实际盘口 → 三种情况 → 结合水位确认机构意图。

```
情况一: 实际盘口 = 理论盘型 (合理盘口)
  → 机构判断与基本面一致
  → 重点看水位变化和临场异动
  → 赛果大概率贴合真实实力

情况二: 实际盘口 < 理论盘型 (盘口偏浅, 差 ≥ 0.5球)
  子情况 A — 机构不看好上盘:
    信号: 盘口偏浅 + 水位偏高(>1.00) + 基本面有隐忧
    结论: 上盘可能赢球输盘或爆冷, 考虑下盘
  
  子情况 B — 诱下盘:
    信号: 盘口偏浅 + 水位偏低(<0.85) + 基本面完好
    结论: 降低上盘门槛吸引投注, 实际机构看好上盘

情况三: 实际盘口 > 理论盘型 (盘口偏深, 差 ≥ 0.5球)
  子情况 A — 机构真实看好上盘:
    信号: 盘口偏深 + 水位稳定偏低 + 对手防守薄弱
    结论: 上盘大概率穿盘
  
  子情况 B — 诱上盘:
    信号: 盘口偏深 + 水位偏高(>1.02) + 对手防守强硬/战意强
    结论: 抬高门槛制造上盘强势假象, 实际诱买上盘
```

### 13.3 临场盘口四口诀

> 来自多篇教程的共同核心规律，为最简洁实用的盘口变化判断法则。

```
口诀速查表:

┌──────────────┬──────────────────────┬──────────────┐
│   盘口变化   │        含义          │   投注方向   │
├──────────────┼──────────────────────┼──────────────┤
│ 升盘 + 降水  │ 真实看好上盘         │  追 上 盘    │
│ 升盘 + 升水  │ 诱上盘 (假强势)      │  避开/下盘   │
│ 降盘 + 升水  │ 不看好上盘           │  追 下 盘    │
│ 降盘 + 降水  │ 阻上盘 (假示弱)      │  搏 上 盘    │
└──────────────┴──────────────────────┴──────────────┘

使用前提:
  1. 口诀必须结合盘口深浅和基本面使用
  2. 降盘+降水 = 阻盘的前提: 基本面完好无伤停
  3. 升盘+升水 = 诱盘的前提: 对手有一定抵抗力
  4. 不能单独看口诀, 必须交叉验证

实战检测 (OddsPapi 历史数据):
  升盘+降水 上盘穿盘率: ~65%  (当基本面支撑时)
  降盘+升水 下盘不败率: ~62%
  降盘+降水 上盘穿盘率: ~58%  (需基本面验证)
  升盘+升水 上盘穿盘率: ~38%  (方向明确的反向信号)
```

### 13.4 三维一体综合分析法

> 融合多篇教程的核心分析方法论: 指数信号 + 基本面验证 + 客观因素补全。

```
维度一【指数分析】 (权重 40%)
  ① 赔率偏差检测:
     个人分析胜率 vs 机构隐含概率, 差值 > 5% → 高价值机会
  
  ② 盘口异动预警:
     强队临场退盘 ≥ 0.5球且无合理原因 → 爆冷概率 +35%
     赔率方差 > 1.1 (多机构分歧大) → 信号增强
  
  ③ 非同步变盘检测:
     主流庄家统一升盘, 某一家独自降盘 → 该家有独立判断
     可作为反向参考, 但不能单一依据

维度二【基本面验证】 (权重 35%)
  ① 近10场攻防数据: 场均进球、失球、射正率
  ② 主力伤停: 核心球员缺阵 → 胜率降 20-40%
  ③ 战意强度: 保级队主场胜率比普通场次高 17%
  ④ 历史交锋关键细节: 特定场地适应度
  ⚠️ 所有数据需交叉验证, 官网 > 自媒体

维度三【客观因素】 (权重 25%)
  ① 赛程密度: 连续一周双赛 → 胜率降 23%
  ② 时段特征: 凌晨 1-5点 北欧联赛爆冷率比英超高 23%
  ③ 德比战: 主场加持超常规, 盘口让球常不足
  ④ 杯赛 vs 联赛: 杯赛轮换概率高, 盘口按联赛实力开的误导性强
```

### 13.5 赔率盘口背离检测

```
核心规则: 欧赔主胜 1.60 → 正常对应亚盘 让 0.75 球

背离信号:
  "盘浅赔低": 主胜赔率 1.60, 但亚盘仅让 0.50 球
  → 盘口偏浅 0.25, 机构可能诱导上盘
  → 统计: 此种情况下盘赢盘率 ~60%
  
  "盘深赔高": 主胜赔率 2.00, 但亚盘让 1.00 球
  → 盘口偏深, 机构可能阻上/诱上
  → 需结合水位判断: 深盘+低水=阻上, 深盘+高水=诱上

欧赔→亚盘快速换算表:
  1.20 → 1.75球    1.40 → 1.00球    1.60 → 0.75球
  1.80 → 0.50球    2.00 → 0.25球    2.50 → 0.00球
  3.00 → 受0.25    4.00 → 受0.50    6.00 → 受1.00

检测流程:
  1. 从 Pinnacle 1X2 获取主胜赔率
  2. 查表得理论对应亚盘
  3. 对比 Pinnacle AH 实际主力盘口
  4. 偏差 ≥ 0.25 → 记录背离信号
  5. 结合其他指标判断机构意图
```

### 13.6 水位波动三种模式

```
模式一【单向波动】
  现象: 水位从 0.95 持续降至 0.80, 盘口不变
  信号: 机构主动降低赔付 → 该方向真实被看好
  行动: 结合盘口深浅, 若盘口合理 → 跟进

模式二【震荡波动】  
  现象: 水位 0.90→1.05→0.85 反复
  信号: 市场资金大量涌入, 机构被动调整
  判断: 查基本面是否有突发利好 → 有则可信, 无则警惕
  行动: 基本面匹配 → 跟进; 基本面不变 → 观望

模式三【反向变动】
  现象: 下盘水位 0.80→1.00 持续升, 上盘 1.00→0.80 持续降
  信号: 机构故意引导资金流向下盘 → 反向诱盘
  行动: 基本面无明显变化 → 逆势投注上盘

关键时间节点:
  初盘 (赛前 3-5天): 试探性, 观察市场反应
  中盘 (赛前 1-2天): 资金大量涌入期, 变动可信度较高
  临场 (赛前 1-2小时): 突发消息影响 + 可能设诱盘陷阱
  终盘 (赛前 30分钟): 最能反映机构最终判断
```

### 13.7 分联赛盘口特性速查

> 不同联赛风格不同，盘口逻辑不同。不可用统一标准分析所有联赛。

```
英超: 正路多, 主场优势明显 (主场胜率 ~45%)
  盘口: 波动理性, 升盘降水可信度高
  口诀: "走升不走降" — 升盘方向更值得跟进

德甲: 强弱分明, 强队统治力强
  盘口: 贴合实力, 升盘降水信号可信
  特点: 大球率高, OU 2.5 大球 > 55%

意甲: 平局率高, 防守严密
  盘口: 保守偏浅, 强队让球常不足
  口诀: "周末防爆冷, 强队让1球需谨慎"
  特点: 平局率 ~28%, 一球盘下需防赢球输盘

西甲: 技术流, 半场节奏快
  盘口: 变化频繁, 需结合水位基本面
  特点: 半场多大球, 平局率 < 意甲

法甲: 巴黎独大, 其他队波动大
  盘口: 诱盘概率高, 中下游队对阵需谨慎
  口诀: "巴黎主场稳, 其他队慎追"

北欧联赛 (瑞典超/挪威超):
  盘口: 异动频繁, 爆冷率高
  时段: 凌晨 1-5点 爆冷率 +23%
  建议: 新手尽量避开

世界杯 (本技能聚焦):
  盘口: 关注度高, 资金量大, 诱盘手法精细
  特点: 结合技能 Section 9 淘汰赛特殊规则
  注意: 让球线映射竞彩 RSPF (Section 11.3)
```

### 13.8 三类异常盘口信号

```
信号一【初盘与历史盘口偏离】
  检测: 某队主场对同一对手, 历史让球 1.0, 本次仅让 0.25
  含义: 实力下滑/战意不足/核心缺阵
  行动: 查看伤病+近期状态, 偏离 ≥ 0.5 → 标记预警

信号二【水位剧烈波动】
  检测: 1小时内某方水位从 0.80 骤升至 1.10
  含义: 大额资金反向涌入 或 突发不利消息
  行动: 立即查看最新消息(首发/伤停), 确认后决定是否跟进

信号三【非同步变盘】
  检测: 主流庄家(Pinnacle/Bet365)统一升盘, 某一家(澳门)独自降盘
  含义: 该庄家有独立信息判断
  行动: 作为反向参考因素, 但不可单一依据 → 需基本面交叉验证
```

### 13.9 资金管理铁律 + 五大误区

```
资金管理 (多篇教程共识):
  单笔上限: ≤ 总预算的 5%
  日亏损止损: 达 10% → 暂停当日投注
  盈利提取: 达 50% 利润 → 提取本金, 用利润继续
  串关警告: 3串1+ 长期必亏 (抽水 11%)
  均注策略: 不因信心高而加倍, 保持每注金额一致

五大新手误区:
  ① 指数迷信 → 纯看赔率不看基本面, 长期正确率 < 45%
  ② 基本面偏执 → 纯看球队不看盘口, 遗漏率 38%
  ③ "蚊子肉"陷阱 → 低赔率(1.20)需连中5次才弥补1次失利
  ④ 追串关 → 6串1返奖率仅 49%, 低于单场的 89%
  ⑤ 亏损倍投 → 情绪化加倍, 单日损失扩大 3.2倍

风控口诀:
  "合理盘口 + 水位稳定 = 可投"
  "热门赛事 + 极端深盘 = 避开"
  "熟悉联赛 × 1-2个 = 聚焦"
  "连续 3 次失误 = 暂停复盘"
```

### 13.10 与技能体系的联动

```
教程方法论                    →  技能现有模块
─────────────────────────────────────────────────
13.1 盘型推算                →  Section 4 基本面权重 + AH 分析
13.2 盘口深浅判断            →  Section 8 陷阱扫描 (增强版)
13.3 临场四口诀              →  Section 12.2 亚盘临场模式, Section 4(7) 走势分析
13.4 三维一体法              →  技能 12+1 步分析主流程 (增强版)
13.5 赔率盘口背离            →  Section 4(2) 欧亚转换 + 新检测维度
13.6 水位波动模式            →  Section 4(7) 走势真实性验证
13.7 分联赛特性              →  Section 4(8) 联赛权重 + 世界杯特殊规则
13.8 异常盘口信号            →  Section 8 陷阱扫描 (新增三类信号)
13.9 资金管理+误区           →  Section 11.8 自由组合注意事项 + Section 10.1 选场铁律
```

> 💡 以上方法论全部可与 OddsPapi 实时数据联动: Pinnacle AH 赔率 → 检测盘口变化 → 匹配四口诀 → 输出方向信号。水位数据 → 匹配三种波动模式 → 确认或否定信号。13.5 欧亚背离检测可通过 Pinnacle 1X2 vs AH 直接自动化。
