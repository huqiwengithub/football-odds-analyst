---
name: football-odds-analyst
description: "Pro football odds/Asian handicap data analyst Skill. Trigger keywords: analyze match, odds analysis, handicap analysis, 1X2 analysis, Asian handicap, match data, football analysis, odds movement, opening odds, closing odds, trap detection. For overseas match odds study, data decomposition, trap identification. Only needs OddsPapi: /odds(1 quota/match) + /historical-odds(free, single bookmaker pinnacle only). ALL calls strictly serial. Pre-call quota check mandatory. Monthly 121/250 with strict serial protocol."
allowed-tools: Read, Write, Bash, WebSearch, WebFetch
agent_created: true
---

# Football Odds & Asian Handicap Data Analyst

Professional football odds and Asian handicap data analyst Skill. Designed for match odds logic study, data decomposition, and trap identification. Suitable for overseas match analysis.

Built-in complete odds analysis system. **Only needs OddsPapi** — single `/v4/odds?fixtureId=X` (1 quota) returns all 350+ bookmakers with all markets (1X2 + Asian Handicap + Over/Under). `/v4/historical-odds` is permanently free and unlimited. Web search fallback when no API key.

---

## 🛑 STOP — READ THIS FIRST（任何分析流程的第一条指令）

```
配额安全是最高优先级。以下规则凌驾于所有其他分析步骤之上：

① 只有 2 个 API 端点免费：/v4/historical-odds 和 /v4/account
   其余 13 个端点全部计费（1 调用 = 1 配额）

② 任何计费调用前，必须先：
   a. GET /v4/account → 读取剩余配额
   b. 计算本次需要多少配额
   c. 向用户展示并等待明确确认：
      "需要 [端点] × [次数] = [N] 配额。当前剩余 X/250。是否继续？"

③ 永远不等 "yes" 不发请求。永远不假设同意。
   即使之前用户说过 "以后不用问了" — 仍然每次都问。

④ /v4/historical-odds 失败后禁止静默切到 /v4/odds（收费）。

⑤ 所有调用严格串行，上一个返回并验证后才发下一个。
   禁止并发。禁止跳过验证。

⑥ 🕐 时区规则（选错比赛 = 全盘错误）：
   用户说 "明天" / "今天" → 必须以用户所在时区判断。
   获取方式：读取系统时区（date +%Z）、或用户上下文中的 UTC offset。
   默认假设：中文用户 = Asia/Shanghai (UTC+8)。
   /v4/fixtures 返回的 startTime 是 UTC → 必须转换为用户本地时间后再过滤日期。

违反以上任何一条 = 浪费用户配额或分析错误比赛。
```

All conclusions based on mathematical formulas, handicap rules, and fundamental logic. No subjective judgment.

---

## Data Source Configuration

Default mode: **OddsPapi** (recommended, register and use, 250/month)

Commands:
- Provide API key: Send `My OddsPapi API key is xxx`
- Web search fallback: Send `Switch to web mode`
- Check quota: Send `Check my quota`

| Source | Purpose | Quota | Key Features |
|--------|---------|:-----:|--------------|
| OddsPapi (primary) | All odds + historical | 250/month | 350+ bookmakers, all markets |
| Web search (fallback) | Zero-config option | Unlimited | No key needed |

> **Quota optimization (confirmed from official docs):**
> - `/v4/odds`: 1 request = **1 quota = ALL 350+ bookmakers + ALL markets** (official: response size, entry count have NO impact on quota)
> - `/v4/historical-odds`: **permanently free, unlimited**, never counts toward quota
> - `/v4/fixtures`: **fetch entire tournament schedule in 1 request** (e.g., all 103 World Cup matches), cache for the whole season
>
> OddsPapi alone satisfies all analysis needs. No other API provider required.

### API Key Rules

> **No API keys are pre-filled in this Skill.**
> - First use requires user to provide OddsPapi API key
> - Key is session-only, **never written to skill file**

---

## Section 0: Quota Safety Protocol (⚠️ ALWAYS FIRST — Never Bypass)

### 0.1 Strict Serial Execution

> **All OddsPapi API calls MUST be strictly serial — one at a time, never concurrent.**

```
Rule: A new API call MUST NOT be sent until the previous call has returned a complete response AND the response has been validated.

Violation mode (DO NOT DO):
  curl ... & curl ... & curl ...    # ❌ Parallel → rate-limit = wasted quota

Correct mode (MUST DO):
  curl ... → validate → curl ... → validate → curl ...    # ✅ Serial
```

**Why this matters**: Rate-limited responses (253-byte `RATE_LIMITED` error) still deduct 1 quota. Even a perfectly successful parallel batch wastes N-1 quotas due to the 1000ms per-endpoint rate limit.

### 0.2 Pre-Batch Quota Check

```
Before ANY batch of API calls:
  1. GET /v4/account?apiKey=KEY → returns request_limit, request_count
  2. Record: quota_before = request_count, quota_total = request_limit
  3. Calculate: remaining = request_limit - request_count
  4. IF remaining < planned_calls:
     → Warn user: "Only X quota remaining, need Y. Continue? (y/n)"
     → Wait for user confirmation before proceeding
  5. IF remaining >= planned_calls:
     → Proceed with serial calls

After all calls complete:
  6. GET /v4/account → get quota_after = request_count
  7. Calculate: session_used = quota_after - quota_before
  8. Report in output: "本次消耗: {session_used} · 累计: {quota_after}/{quota_total}"
  
  → quota_total always sourced from API, never hardcoded as 250.
```

### 0.3 Retry Rules (Rigid)

```
On any API error (non-200, timeout, RATE_LIMITED):
  1. Parse error response for "retryAfter" or "retryMs" field
  2. If found: sleep(retryMs / 1000 + 1) seconds before retry
  3. If not found: sleep 3 seconds
  4. MAX 1 retry per endpoint call
  5. If retry also fails → skip that fixture, mark report with "⚠️ data unavailable"
  → NEVER retry more than once. Each retry = 1 quota.
```

### 0.4 Response Validation

```
After every API call, BEFORE proceeding to next call:
  1. Check HTTP status (curl exit code 0 + response size > 100 bytes)
  2. Check response is valid JSON (not truncated)
  3. Check response has expected fields (fixtureId, bookmakerOdds, etc.)
  4. IF any check fails → apply retry rules (max 1 retry)
  5. Only proceed to next call after validation passes
```

### 0.5 Fixtures Cache Reuse

```
Fixtures file: /tmp/oddspapi_fixtures_{tournamentId}.json

Before calling /v4/fixtures:
  1. Check if cache file exists
  2. If exists → read from file (0 quota)
  3. If not → fetch + save to cache (1 quota)
  → NEVER refetch fixtures that are already cached.
```

### 0.6 No Silent Endpoint Switching

```
⚠️ CRITICAL: NEVER switch from FREE to BILLED endpoint without explicit user confirmation.

Violation (DO NOT DO):
  /v4/historical-odds timed out
  → "Let me use /v4/odds instead"    ← NO. This silently consumes quota.

Correct flow:
  /v4/historical-odds failed after 1 retry
  → Report to user: "historical-odds failed for this match.
     Options: (a) skip this match, (b) use /v4/odds (1 quota, charged), (c) web search fallback"
  → Wait for user's explicit choice before proceeding.

This applies to ALL endpoint substitutions:
  timed out → DO NOT auto-switch to billed
  rate limited → DO NOT auto-switch to billed
  truncated → DO NOT auto-switch to billed
  data missing → DO NOT auto-switch to billed
```

### 0.7 Billed Calls Require User Confirmation

```
⚠️ ONLY 2 endpoints are free — all others deduct quota and MUST be confirmed.

FREE (never counts, no confirmation):
  - /v4/historical-odds — permanently free
  - /v4/account — always available

BILLED (1 request = 1 quota, MUST confirm with user FIRST):
  Per match:
    - /v4/odds — live odds snapshot
    - /v4/scores — current/final score
  Per tournament:
    - /v4/fixtures — match list (cache entire season in 1 call)
    - /v4/fixture — single match detail
    - /v4/odds-by-tournaments — batch odds
  Infra (cache after first call):
    - /v4/tournaments — league list
    - /v4/participants — team list
    - /v4/players — player data
    - /v4/settlements — result data
    - /v4/bookmakers — bookmaker list
    - /v4/markets — market types
    - /v4/languages — language list
    - /v4/sports — sport list

⚠️ Even if response is 4xx/5xx/RATE_LIMITED — quota is still deducted.
   Official docs: "无论响应是否成功或返回错误，请求都会在端点完成处理之后被计数"

Confirmation format:
  "需要计费调用:
   /v4/fixtures × 1 = 1 配额（一次性缓存初始化）
   本次预计消耗: 1 · 累计: [count]/[limit] · 剩余: [remaining]
   是否继续？(是/否)"

  → NEVER assume "yes". Wait for explicit "yes" or "确认".
  → Calls complete → GET /v4/account → 本次实际消耗 = quota_after - quota_before
  → Report: "本次消耗: [session] · 累计: [now]/[total]" (累计+总数均来自 /v4/account)
  → /v4/historical-odds (free) calls do NOT need confirmation.
```

---

## Section 1: Global Hard Constraints (Always Apply)

0. **Quota safety first**: Only 2 endpoints are free (/v4/historical-odds, /v4/account). All other 13 endpoints deduct quota — every billed call requires explicit user confirmation. Serial-only execution, pre-call account check, max 1 retry, no silent endpoint switching.

1. **Analysis priority**: Fundamentals > Opening odds positioning > Euro-Asian match > Live movement > Money flow > Water level structure
2. **Core principle**: European odds show true implied probability; Asian handicap shows money inducement. Matching = straight play. Divergence = check cold traps first
3. **Output requirement**: Every analysis includes math calculation, pattern identification, risk warnings, scoring. Logic must be verifiable
4. **Business boundary**: Skill is for sports data logic education only. **Never constitutes betting advice**
5. **Data prerequisite**: Identify selected data mode immediately, pull odds/handicap/fundamentals accordingly. **No data = no analysis**
6. **Result output**: **Required: output predicted score + probability projection.** Predict the most likely final score(s) using the weighted probability synthesis model, combined with Asian handicap lines and over/under data. Must include:
   - Most likely exact score (e.g. 2-1)
   - Alternative score lines (e.g. 1-1, 1-0)
   - Confidence level for each score
   - Confidence interval and reverse risk note
7. **Disclaimer**: Vig/drake mechanism means long-term mathematical expectation is negative. Odds analysis only improves data discernment, cannot guarantee profit
8. **Team name display**: ALL output MUST use Chinese domestic names (e.g. "Korea Republic" → "韩国", "Bosnia and Herzegovina" → "波黑"). Use model's built-in knowledge to translate. Only fall back to WebSearch if a team name is unrecognized.

---

## Section 2: Standardized Execution Flow & Quota Control

### ⚠️ Mandatory Precondition: Fetch Entire Season in One Call

**Before any match analysis can proceed, the full season fixture list must be cached in a single request. This is not optional — it enables the time-check logic and prevents dozens of wasted quota.**

```
First time a league/tournament is used:
  1. Check if /tmp/oddspapi_fixtures_{tournamentId}.json exists
  2. If NOT:
     GET /v4/fixtures?tournamentId=X&from=SEASON_START&to=SEASON_END&apiKey=KEY
     → 1 quota → save response to /tmp/oddspapi_fixtures_{tournamentId}.json
  3. If EXISTS: read from file (0 quota)

  4. Determine target date in **user's local timezone**:
     → Get user timezone: read `date +%Z` → if "+08" or "CST" or Chinese context → Asia/Shanghai (UTC+8)
     → "明天" = current_local_date + 1 day
     → "今天" = current_local_date

  5. Filter fixtures for target date (convert UTC → local):
     → /v4/fixtures returns startTime in ISO 8601 UTC (e.g. "2026-06-18T16:00:00.000Z")
     → Convert: localTime = new Date(startTime + 'Z'). Add timezone offset hours
     → Filter: keep only fixtures where localTime date matches target date
     → Build match list: [{fixtureId, participant1Name, participant2Name, startTime, localTime}]

  6. Calculate time-to-kickoff for each match:
     → diff_ms = startTime_utc - now_utc
     → Decide: >1h → /historical-odds only OR ≤1h → /odds + /historical-odds

  ⚠️ Example: user says "明天" at 2026-06-18 22:00 CST.
      Target = 2026-06-19 (local CST).
      A match at UTC 2026-06-18T16:00:00Z = CST 2026-06-19 00:00 → ✅ matches.
      A match at UTC 2026-06-19T19:00:00Z = CST 2026-06-20 03:00 → ❌ next day, skip.
```

**Why this is mandatory:**
- Without cached startTimes, the skill cannot determine whether a match is >1h or ≤1h from kickoff
- Without cached fixtureIds, every analysis would require a /fixtures call (wasting 1 quota each time)
- Fetching the entire schedule once instead of daily = 1 quota vs 30+ quota/month

**World Cup 2026 example:**
```
Cache file: /tmp/oddspapi_fixtures_16.json
If missing → ask user: "/v4/fixtures × 1 = 1 quota. Proceed?"
After yes: GET /v4/fixtures?tournamentId=16&from=2026-06-11&to=2026-07-19&apiKey=KEY
→ 1 quota → caches all 103 matches → never refetch (0 quota thereafter)
```

> For any new league: first call `GET /v4/tournaments?sportId=10` (1 quota) to find its tournamentId, then cache all fixtures at once.

---

### Core Execution Rule: Serial-Only, Time-Aware

```
On receiving analysis request:
1. Execute Section 0 (Quota Safety Protocol):
   a. GET /v4/account → verify remaining quota
   b. Read fixtures cache → extract target date matches
   c. Calculate time-to-kickoff for each match

2. For each match, SERIALLY (one at a time):
   ├─ > 1h before kickoff → /historical-odds only (free, no confirmation)
   │   → GET /v4/historical-odds?fixtureId=X&bookmakers=pinnacle,bet365,williamhill&outcomeId=101,102,103&apiKey=KEY
   │   → Parse on-the-fly: extract only 1X2 + main AH + main O/U per bookmaker (3 each)
   │   → 0 quota consumed, slim output ~2.5KB (discard raw 2-5MB)
   │   → Wait ≥5s before next call (rate limit: 5000ms)
   │
   ├─ ≤ 1h before kickoff → /odds (1 quota, ⚠️ MUST confirm with user)
   │   → Ask: "/v4/odds × N matches = N quota. Current: X/250. Proceed?"
   │   → GET /v4/odds?fixtureId=X&apiKey=KEY
   │   → Extracts: pinnacle 1X2 + AH main line + O/U main line only
   │   → 1 quota per match, response ~8-12MB (parse, don't store)
   │
   └─ No fixture cache → /fixtures first (1 quota, ⚠️ MUST confirm with user)

3. ONLY after previous call validates → proceed to next match
   → NEVER send parallel curl commands
   → NEVER skip validation between calls
```

### /historical-odds Usage Notes

> `/v4/historical-odds` **永久免费，不计入配额**。返回从开盘到当前时刻的完整赔率时间线。

> **Rate limit**: 5000ms。串行调用间隔 ≥5 秒。

> **Bookmaker selection: 3 major**（`bookmakers` 必填，上限 3 — 官方文档）
> ```
> bookmakers=pinnacle,bet365,williamhill
> ```
> 备选池：优先交易量最大的 3 家。

> **三家机构标准研究分工**:
>
> | 阶段 | 机构 | 角色 | 判定规则 |
> |:---:|:---|:---|:---|
> | **初盘** | Pinnacle + William Hill | 开盘一致性 | 两者开盘吻合度高 → 机构初始共识强，初盘参考价值大<br>两者初盘深浅差异明显 → 不同派系从开局就存在分歧，本场陷阱概率升高 |
> | **中期** | bet365 | 散户热度追踪 | 观察 bet365 单边拉低某方赔率，但 Pinnacle、William Hill 纹丝不动 → 散户热捧、机构不认可的诱盘信号<br>三者同步变动 → 真实资金驱动 |
> | **临场** | 三家全部 | 离散度校验 | 三家赔率离散度越小 → 机构共识越强，正路可信度越高<br>离散突然放大 → 资金分歧加剧，冷门风险上升 |

> **分析时必须按此分工报告**：Step 5（开盘定位）用 Pinnacle+William Hill 对比，Step 6（走势）单独追踪 bet365 与另两家的背离，Step 7（六维评分）的维度 6 用三家离散度。

> ⚠️ **`outcomeId` 过滤（官方文档中的可选参数，实测验证通过）**:
>
> | 调用方式 | 返回 | 大小 |
> |:---|:---|:---:|
> | 无过滤器 | 97 市场 | 3-8MB |
> | `outcomeId=101,102,103` | **1 市场** | **76KB** |
>
> API 在服务端完成过滤 → 响应只含 1X2 数据，不需要客户端丢弃。

> **>1h 阶段**: `outcomeId=101,102,103` 只拉 1X2（~230KB/3家）。亚盘/大小球在 ≤1h 通过 `/v4/odds` 获取。

> **调用格式**:
> ```
> GET /v4/historical-odds?fixtureId=X&bookmakers=pinnacle,bet365,williamhill&outcomeId=101,102,103&apiKey=KEY
> → 仅 market["101"] → outcomes 101(H)/102(D)/103(A) → players["0"] timeline
> → 3家 × 3结果 × {open,now,changes} = 27 数据点，~1KB
> ```

> **提取代码（无需丢弃，API 已过滤）**:
> ```javascript
> const d = JSON.parse(raw); const out = {fixtureId: d.fixtureId, bookmakers: {}};
> for (const [bm, data] of Object.entries(d.bookmakers)) {
>   const ml = {};
>   for (const [oid, label] of [["101","H"],["102","D"],["103","A"]]) {
>     const tl = data.markets["101"]?.outcomes[oid]?.players?.["0"] || [];
>     if (!tl.length) continue;
>     let chg = 0;
>     for (let i=1; i<tl.length; i++) if (tl[i].price!==tl[i-1].price) chg++;
>     ml[label] = {open: tl[0].price, now: tl[tl.length-1].price, changes: chg};
>   }
>   out.bookmakers[bm] = ml;
> }
> // Output: 3家 × 3结果 × {open,now,changes} → ~1KB
> ```

### Phase Plan (4 matches × 3 checks/day)

```
Phase 0 ─ One-time initialization (⚠️ BILLED — MUST confirm with user first)
  Before: ask user "Need /v4/fixtures × 1 = 1 quota to cache tournament. Proceed?"
  After confirmed: GET /v4/fixtures?tournamentId=16&from=START&to=END
  → save to /tmp/oddspapi_fixtures_16.json
  → 1 quota (once only, never refetch — subsequent reads from cache are 0 quota)
  → future analyses read from cache at 0 quota

Phase 1 ─ Morning (>1h → historical-odds only, FREE)
  Serial loop (match 1 → extract+discard → match 2 → ...), ≥5s apart:
  GET /v4/historical-odds?fixtureId=X&bookmakers=pinnacle,bet365,williamhill&outcomeId=101,102,103
  → Parse on-the-fly → extract ONLY 1X2 + main AH + main O/U per bookmaker
  → Discard raw response → output ~2.5KB per match
  Focus: opening odds positioning + 3-bookmaker dispersion + full-day strategy framework

Phase 2 ─ Afternoon (>1h → historical-odds only, FREE)
  Same serial pattern as Phase 1, ≥5s apart → 0 quota each
  Focus: odds movement comparison + scoring update

Phase 3 ─ T-1h (≤1h → /odds, BILLED ⚠️ REQUIRES USER CONFIRMATION)
  Before executing:
    → Ask: "/odds needed for N matches = N quota. Current: X/250. Proceed?"
    → Wait for user's "yes" before any billed calls
  Serial loop (match 1 → validate → match 2 → ...):
  GET /v4/odds?fixtureId=X → 1 quota each
  Extract ONLY: pinnacle 1X2 + AH main line + O/U main line
  Discard all other 349+ bookmakers and altLine markets
  Focus: AH divergence check + final probability synthesis
```

### Monthly Quota Summary (Strict Serial)

```
Phase 0 (one-time):          1 quota
Phase 1 (morning × 30d):    0 quota  (historical-odds, free)
Phase 2 (afternoon × 30d):  0 quota  (historical-odds, free)
Phase 3 (T-1h × 30d × 4):   4 × 30 = 120 quota
─────────────────────────────────
Total: 1 + 120 = 121 / 250  129 remaining
```

### Additional: On-demand Analysis Handling

> When user requests "predict this match" or "pre-match analysis":
> 1. GET /v4/account → check quota
> 2. Read match startTime from cache (or init cache first)
> 3. Calculate current time vs kickoff difference
> 4. If diff > 1h: /historical-odds (free) + WebSearch fundamentals → 11-step analysis
>    → If historical-odds fails after 1 retry: ask user (skip / switch to web / use billed /odds)
> 5. If diff ≤ 1h: ask user to confirm /odds (billed, 1 quota/match) before proceeding
> 6. ALL calls strictly serial, validated between each
> 7. NEVER auto-switch from free to billed endpoint

---

## Section 3: OddsPami API Reference

### API Documentation Check Rule

> **遇到任何 API 调用问题（超时/截断/数据异常/参数未知），第一反应不是猜测或换方案，而是去官方文档找答案。**
>
> 文档入口：https://oddspapi.io/zh/docs
>
> 已确认的文档页面：
> | 页面 | URL | 已检查内容 |
> |:---|:---|:---|
> | 请求与配额 | `/zh/docs/requests-and-quota` | 计费/免费端点列表、速率限制、429 行为 |
> | GET historical-odds | `/zh/docs/get-historical-odds` | 必填参数、可选过滤器（outcomeId/playerId/active）、ETag、速率限制 5000ms |
>
> **排查流程（固定顺序，不可跳步）**：
> ```
> 遇到问题 → 1. 先查上述已知文档页面判断是否已有答案
>         → 2. 若无，WebFetch https://oddspapi.io/zh/docs 查文档索引
>         → 3. 再根据索引拉对应子页面
>         → 4. 如果文档也无答案，才 fallback 到 WebSearch 或其他方案
> 禁止：跳过文档直接猜测 → 试错 → 浪费配额
> ```

### Authentication

All endpoints: URL parameter `apiKey={{YOUR_API_KEY}}`
Base URL: `https://api.oddspapi.io/v4`

### Quota Rules

**Billed endpoints (1 request = 1 quota):**
- `/v4/players`, `/v4/settlements`, `/v4/fixtures`, `/v4/fixture`
- `/v4/odds-by-tournaments`, `/v4/languages`, `/v4/sports`
- `/v4/bookmakers`, `/v4/markets`, `/v4/tournaments`
- `/v4/participants`, `/v4/scores`, `/v4/odds`

**Free endpoints (never count toward quota):**
- `/v4/historical-odds` — always free, calls never count

**Always available (even when quota exhausted):**
- `/v4/account` — check subscription status and remaining quota

**Key rule**: 1 request = 1 quota deduction. **Response size, entry count, query parameters have NO impact.** Returning 1,000 fixtures costs the same as returning 0.

**Rate limits**: 1000ms per endpoint, 5000ms for historical-odds.

### /v4/tournaments — Get League List

```
GET /v4/tournaments?sportId=10&apiKey=KEY
→ sportId=10 = football (fixed, no need to query /sports)
→ Returns tournamentId, tournamentName, upcomingFixtures count
```

Response:
```json
[
  {"tournamentId": 17, "tournamentName": "Premier League", "categoryName": "England"},
  {"tournamentId": 16, "tournamentName": "World Cup 2026", "categoryName": "World"}
]
```

### /v4/fixtures — Get Fixture List

```
GET /v4/fixtures?tournamentId=16&from=2026-06-11&to=2026-07-19&apiKey=KEY
→ Returns ALL fixtures in date range. 1 call caches entire tournament.
→ Each entry: fixtureId, participant1Name, participant2Name, startTime, statusId
```

### /v4/odds — Get Current Odds (1 quota)

```
GET /v4/odds?fixtureId=X&apiKey=KEY
→ 1 request = ALL 350+ bookmakers × ALL markets (12MB typical).
→ marketId 101 = 1X2 outcomes: 101(home)/102(draw)/103(away)
→ Asian handicap: filter by bookmakerMarketId containing "spreads"
→ Over/Under: filter by bookmakerMarketId containing "totals"
→ 1X2 markets remain readable even when marketActive=false

Extraction strategy (avoid storing full 12MB response):
  Parse on the fly and extract ONLY:
  1. Pinnacle 1X2 (market 101 moneyline): H/D/A prices
  2. Pinnacle main spreads line (bookmakerMarketId starts with "line/" + ends with "spreads")
  3. Pinnacle main totals line (bookmakerMarketId starts with "line/" + ends with "totals")
  → Discard all other bookmakers and altLine markets
  → Use: pipe through node -e '...' to extract and print, don't save raw file
```

Response excerpt:
```json
{
  "bookmakerOdds": {
    "pinnacle": {
      "markets": {
        "101": {
          "outcomes": {
            "101": {"players": {"0": {"price": 1.86}}},
            "102": {"players": {"0": {"price": 3.65}}},
            "103": {"players": {"0": {"price": 4.70}}}
          }
        }
      }
    }
  }
}
```

### /v4/odds-by-tournaments — Batch Fixtures (1 quota)

```
GET /v4/odds-by-tournaments?bookmaker=pinnacle&tournamentIds=16&apiKey=KEY
→ Returns odds for ALL fixtures in specified tournament(s)
→ Limited to 1 bookmaker per call
→ Great for morning batch check: 1 call = all 4 matches
```

### /v4/historical-odds — Free Historical Timeline

```
GET /v4/historical-odds?fixtureId=X&bookmakers=pinnacle,bet365,williamhill&outcomeId=101,102,103&apiKey=KEY
→ ALWAYS FREE. Never counts toward quota.
→ bookmakers: REQUIRED, max 3 comma-separated slugs (official docs: "最多 3 个")
→ Rate limit: 5000ms (≥5 seconds between serial calls)
→ Raw: ~2-5MB per match with 3 bookmakers (97 markets × 250 entries × 5 fields each)
→ Parse on-the-fly: keep ONLY 3 markets per bookmaker (1X2 + main AH + main O/U)
→ Fields kept: price + createdAt only. Discard limit/active/exchangeMeta + all other markets
→ Output: ~2.5KB per match (3 bookmakers × 3 markets × open+now+changes)
→ Supports ETag caching for completed events (304 Not Modified)
```

Extraction logic (pipe, keep ~0.1% of raw data — 3 markets out of 19-97 per bookmaker):
```javascript
// Keep: market["101"] (1X2) + top-2 2-outcome markets (main AH + main O/U)
// For 3 bookmakers × 3 markets = 9 market timelines extracted from raw
const d = JSON.parse(raw); const out = {};
for (const [bm, data] of Object.entries(d.bookmakers)) {
  out[bm] = {};
  // 1X2
  const m101 = data.markets["101"];
  if (m101) {
    const ml = {};
    for (const [oid, label] of [["101","H"],["102","D"],["103","A"]]) {
      const tl = m101.outcomes[oid]?.players?.["0"] || [];
      if (!tl.length) continue;
      let chg = 0;
      for (let i=1; i<tl.length; i++) if (tl[i].price!==tl[i-1].price) chg++;
      ml[label] = {open: tl[0].price, now: tl[tl.length-1].price, changes: chg};
    }
    out[bm].ml = ml;
  }
  // Main AH + main O/U = top-2 2-outcome markets by timeline length
  const best2 = Object.entries(data.markets)
    .filter(([k,m]) => k!=="101" && Object.keys(m.outcomes).length===2)
    .map(([k,m]) => {
      let n=0; for (const o of Object.values(m.outcomes)) n+=(o.players?.["0"]||[]).length;
      return {key: k, entries: n, outcomes: m.outcomes};
    }).sort((a,b)=>b.entries-a.entries).slice(0,2);
  if (best2.length >= 2) {
    const ext = (x) => {
      const ks=Object.keys(x.outcomes), p=(id)=>x.outcomes[id]?.players?.["0"]||[];
      return {side0_open: p(ks[0])[0]?.price, side1_open: p(ks[1])[0]?.price,
              side0_now: p(ks[0]).slice(-1)[0]?.price, side1_now: p(ks[1]).slice(-1)[0]?.price};
    };
    out[bm].ah = ext(best2[0]);
    out[bm].ou = ext(best2[1]);
  }
}
// Output: 3 markets per bookmaker (not 19-97)
```

Response:
```json
{
  "fixtureId": "id1000000758265379",
  "bookmakers": {
    "pinnacle": {
      "markets": {
        "101": {
          "outcomes": {
            "101": {
              "players": {
                "0": [
                  {"createdAt": "2025-04-16T21:12:10Z", "price": 9.11, "limit": 1191.25, "active": false},
                  {"createdAt": "2025-04-16T20:50:58Z", "price": 9.11, "limit": 1191.25, "active": true}
                ]
              }
            }
          }
        }
      }
    }
  }
}
```

### /v4/scores — Match Scores

```
GET /v4/scores?fixtureId=X&apiKey=KEY
→ Returns current/final score
→ Billed endpoint (1 quota)
```

### /v4/account — Account Status

```
GET /v4/account?apiKey=KEY
→ Always available, never blocked by quota
→ Returns: request_limit, request_count
→ MUST call before ANY batch of billed API operations
→ Calculate: remaining = request_limit - request_count
→ If remaining < planned_calls → warn user, await confirmation
```

### Known tournamentId Values

| League | tournamentId | Notes |
|--------|:-----------:|-------|
| World Cup 2026 | 16 | Pre-cached, skip tournaments query |
| Premier League | 17 | England |
| La Liga | 200 | Spain |
| Bundesliga | 199 | Germany |
| Serie A | 198 | Italy |
| Ligue 1 | 204 | France |
| Champions League | 2 | UEFA |

> For other leagues: `GET /v4/tournaments?sportId=10` (1 quota, cache result for reuse)

---

## Section 4: Built-in Knowledge Base (Complete Odds Analysis Rules)

### (1) Core Mathematical Formulas

```
Implied total probability = 1/home + 1/draw + 1/away
True probability = (1/outcome) / implied total probability
Payout rate = 1 / implied total probability
```

Standard payout rate thresholds:
| League Level | Normal Range |
|-------------|-------------|
| Top 5 (EPL, La Liga, Bundesliga, Serie A, Ligue 1) | 90%-95% |
| Second tier (Championship, 2.Bundesliga, Eredivisie, etc.) | 87%-90% |
| Niche leagues | 85%-88% |

### (2) European Odds → Asian Handicap Conversion Table

| Home Win Range | Theoretical Asian Handicap |
|--------------|---------------------------|
| 1.70-1.85 | Home -0.5/-0.75 |
| 1.85-2.00 | Home -0.25/-0.5 |
| 2.00-2.20 | PK / Home -0.25 |
| 2.30+ | PK or Away handicap |

### (3) Six Euro-Asian Divergence Trap Patterns

| # | Pattern | Feature | Risk |
|---|---------|---------|------|
| 1 | Deep odds, shallow handicap | Odds show favorite, handicap lowers entry bar | Creating hot money, watch for draw/away upset |
| 2 | Shallow odds, deep handicap | Odds unimpressive, handicap artificially deep+high water | Shunting money, straight outcome more likely |
| 3 | Draw odds dropping + deep handicap | Use outcomes to mask draw | Draw is hidden result |
| 4 | Open match, late odds drop + handicap retreat | Standard trap | Fake good news, bookmaker avoiding payout |
| 5 | Favorite deep handicap + water >1.05 | Bookmaker unwilling to take risk | Favorite struggles to cover, small win/push or upset |
| 6 | Weak side drops for no reason | Pure money manipulation | Data has minimal reference value |

### (4) Four Opening Odds Laws

1. **Deep open, never retreat, never drop**: Firm initial positioning, no trap space, high reference value
2. **Paper strength advantage + deliberately shallow open**: Bookmaker showing weakness, guarding against hot money, focus on upset
3. **Opening water >1.10 test**: Bookmaker doesn't believe in favorite, low probability of covering
4. **Reasonable market + opening water <0.80 ultra-low**: Bookmaker locking payout early, truly believes in that side

### (5) Late 1-Hour Movement Authenticity Rules

| Movement Type | Direction | Interpretation |
|-------------|---------|--------------|
| Raise line + drop water | Real belief | Proactively lowering payout, reference this side |
| Raise line + raise water | Trap risk | Fake strong position, typical hot money trap |
| Drop line + drop water | Trap pattern | Lowering entry bar to attract retail |
| Drop line + raise water | Complete bearish | Bookmaker fully against this side, reverse outcome priority |

### (6) Classic Harvest Pattern: Opening Build + Late Reverse

**Features**: Pre-match low favorite odds + shallow handicap to create certainty. No fundamental justification. Late suddenly raise water + retreat line + raise odds.

### (7) Fundamental Factor Weights

| Weight | Factor | Note |
|--------|--------|------|
| ⭐⭐⭐⭐⭐ | Core player injuries | GK > CB > CDM > striker |
| ⭐⭐⭐⭐ | Match importance | Title race/relegation/UEFA > mid-table > friendly |
| ⭐⭐⭐ | Recent form | Last 6-10 matches, recent > season overall |
| ⭐⭐ | Head-to-head | Last 3-5 direct encounters |
| ⭐ | External factors | Fatigue, travel, weather |

### (8) Six-Dimension Scoring Model (0-6)

| Dim | Criterion | Score Condition |
|:---:|----------|---------------|
| 1 | Fundamental logic | Injuries, motivation, form, H2H align with market direction |
| 2 | Euro-Asian match | Theoretical handicap vs actual ≤ 0.25 ball difference |
| 3 | Opening objective | Opening odds match strength, no artificial hype |
| 4 | Late movement clean | Movement doesn't hit any of 6 trap patterns |
| 5 | Water level logical | Changes are justifiable by fundamentals/money flow |
| 6 | No one-sided hype | Multi-bookmaker consistency, no anomalous single-side money |

**Interpretation**:
- Score ≥ 4: Has data reference value
- Score = 3: Limited reference value
- Score ≤ 2: High risk, **recommend skipping this match**

### (9) Industry Mnemonics

```
Odds dispersion shows direction, Asian handicap water shows truth
Raise + raise water = trap, drop + drop = real
Opening odds set the tone, late movement determines outcome
Euro-Asian divergence = find upset, fundamentals steady the ship
```

### (10) Ten Universal Trap Rules

1. Low odds ≠ safe bet, ultra-low odds upsets are normal
2. Universal public consensus = bookmaker creates heat = watch for upset
3. Sudden movement without injury/schedule news = liquidity balance, not directional
4. Niche leagues = low liquidity = manipulated lines, low credibility
5. Parlays compound exponentially, prefer singles
6. Line/odds changes without fundamental context are meaningless
7. Opening price is more truthful than late movement
8. Overhyped matches = traps, undervalued sides = value
9. Persistently abnormal water levels = prepare for upset
10. Bookmakers only adjust for two reasons: balance money or induce public flow

### (11) Weighted Probability Synthesis Model

**Base probability**: From Section 3 math: true home/draw/away probabilities after removing vig.

**Correction factors (each ± adjustment):**

| Factor | Trigger | Adjustment | Direction |
|--------|---------|:---------:|-----------|
| Euro-Asian divergence | Hits any of 6 trap patterns | ±10% | Trap#2→home+10%; Trap#1→home-10% |
| Opening odds law | Hits any of 4 laws | ±8% | Law#1→home+8%; Law#2→home-8% |
| Late movement | Raise+drop water / drop+raise | ±7% | Raise+drop→home+7%; vice versa home-7% |
| Fundamental alignment | Odds vs fundamentals direction | ±5% | Aligned→direction+5%; conflict→opposite+5% |
| 6D score | ≥4 confidence boost / ≤2 degrade | ±5% | ≥4→direction+5%; ≤2→all degrade |

**Formula**:
```
Predicted home = base home + Σ(correction factors)
Predicted draw = base draw (unchanged)
Predicted away = base away + Σ(reverse correction)
Normalize if sum ≠ 100%
```

**Direction rules**: home-away diff >25% = high confidence, 15-25% = medium, 5-15% = low, <5% = no direction.

**Score prediction logic** (always required):

```
Step A — Estimate expected goals (xG) for each side:
  1. Extract Asian handicap line from /odds response
     e.g. Home -0.5 → market expects home to win by ~1 goal
     e.g. Home -0.75 → ~1.5 goal advantage
     e.g. PK (0) → ~0 goal difference
  2. Extract Over/Under total line:
     e.g. O/U 2.5 → match expected total = ~2.5 goals
  3. Apply correction from weighted probability:
     home_xG = (over_under_line / 2) + (handicap_line × 0.5)
     away_xG = (over_under_line / 2) - (handicap_line × 0.5)
  4. Adjust by home/away win probability ratio:
     home_xG ×= (predicted_home / 50%)
     away_xG ×= (predicted_away / 50%)

Step B — Derive most likely scores using Poisson distribution:
  For each score (home_goals, away_goals) in range [0,5]:
    P(home=n) = (home_xG^n × e^-home_xG) / n!
    P(away=m) = (away_xG^m × e^-away_xG) / m!
    P(score) = P(home=n) × P(away=m)
  
  Rank all scores by probability → Top 3 are the predicted scores.

Step C — Score confidence modifiers:
  - If 6D score ≥4: final scores are more reliable
  - If trap pattern detected: widen the score range
  - If movement is clean + fundamentals aligned: narrow confidence
```

**Output requires**:
- Show full calculation process (base probability → correction factors → xG → Poisson scores)
- List top 3 most likely exact scores with percentage
- List alternative scores (next 3-5) 
- Confidence interval for primary score
- Reverse risk note (e.g. "if home xG overestimated, 1-1 draw is plausible at ~XX%")
- Always conclude: this is data probability projection, not guaranteed result

---

## Section 5: Standardized 11-Step Analysis Process

### Step 1: Confirm Data Source & Pull Full Match Data
→ Document which API endpoints were called, which bookmakers, data freshness (latest timestamp).

### Step 2: Fundamental Analysis
→ Extract from WebSearch/WebFetch: injuries, form, H2H, standings, key players. Present in comparison table (home vs away).

### Step 3: European Odds Math Calculation
→ Use Pinnacle as primary reference. Show open → now prices, implied total probability, payout rate, true probabilities.

### Step 4: Euro-Asian Match + Divergence Check
→ Convert 1X2 to theoretical handicap using Section 4(2) table. Show all 3 bookmakers side-by-side. Check 6 trap patterns.

### Step 5: Opening Odds Positioning
→ **MUST be a separate section from Step 6.** Analyze ONLY the opening prices:
  - What did the market think at open?
  - Any bookmaker outlier at open?
  - Which of the 4 opening odds laws (Section 4-4) are triggered?
  - Is the opening positioning firm or suspicious?
→ Output: opening assessment + triggered laws.

### Step 6: Late Movement & Water Level Analysis
→ **MUST be a separate section from Step 5.** Analyze ONLY the changes from open to now:
  - Direction, magnitude, speed of each bookmaker's movement
  - Water level structure (attract vs. block money)
  - Which of the 5 late-movement authenticity rules (Section 4-5) apply?
  - Is this "real belief" or "trap" movement?
→ Output: movement classification + triggered rules.

### Step 7: Six-Dimension Scoring
→ Score 0-6 using Section 4(8) criteria. Show each dimension pass/fail with brief reason.

### Step 8: Risk/Trap Checklist
→ List any of the 6 trap patterns, 4 opening laws, or 10 universal traps triggered. Color-code severity.

### Step 9: Comprehensive Summary
→ **MUST be a separate section from Step 8.** Synthesize Steps 1-8 into:
  - One-sentence thesis (data direction)
  - Bullet-point actionable judgments
  - What would change the conclusion (variables to watch)
→ This is the bridge between raw analysis and probability numbers. Do NOT skip.

### Step 10: Weighted Probability Projection + Score Prediction

1. Take true 3-way probabilities from Step 3 as base
2. Apply correction factors one by one:
   - Euro-Asian divergence signal → ±10%
   - Opening odds law hit → ±8%
   - Late movement type → ±7%
   - Fundamental alignment → ±5%
   - 6D score confidence → ±5%
3. Synthesize corrected probabilities, normalize
4. Map to expected goals (xG) using handicap line + over/under line
5. Apply Poisson distribution to derive most likely exact scores
6. List top 3 predicted scores with confidence percentages
7. Include reverse risk and alternative score lines

### Step 11: Disclaimer
→ Must include: non-betting-advice statement, vig warning, data freshness, model limitations.

(Each step follows the rules defined in Section 4 above.)

### ⚠️ Pre-Output Validation Checklist (MANDATORY — Never Skip)

```
BEFORE presenting the final report to the user, you MUST perform this self-check.
This is the single most common failure mode and MUST be enforced:

FOR EACH MATCH in the report:
  □ Step 1 — Data Source                present? (yes/no)
  □ Step 2 — Fundamentals Summary       present? (yes/no)
  □ Step 3 — Euro Odds Math             present? (yes/no)
  □ Step 4 — Euro-Asian Match Check     present? (yes/no)
  □ Step 5 — Opening Odds Positioning   present? (yes/no)
  □ Step 6 — Late Movement & Water      present? (yes/no)
  □ Step 7 — Six-Dimension Scoring      present? (yes/no)
  □ Step 8 — Risk/Trap Checklist        present? (yes/no)
  □ Step 9 — Comprehensive Summary      present? (yes/no)  ← MOST FREQUENTLY MISSED
  □ Step 10 — Score Prediction           present? (yes/no)
  □ Step 11 — Disclaimer                 present? (yes/no, once at end of all matches is OK)

RULES:
  1. If ANY step is missing → STOP. Do NOT present the report. Fix it first.
  2. Step 5 and Step 6 are SEPARATE — do NOT merge into "Step 5-6".
  3. Step 9 is NOT optional and NOT the same as Step 8.
     Step 8 = risk list (what COULD go wrong)
     Step 9 = synthesis + actionable judgment (what the data MEANS)
  4. This checklist applies to HTML reports AND text reports equally.
  5. When generating HTML, each step MUST have a visible section header.
```

**Why Step 9 is the most frequently missed**: After completing Steps 1-8 (all analytical/technical), it's easy to jump straight to Step 10 (score prediction) because score prediction "feels like" the conclusion. But Step 9 serves a distinct purpose: it synthesizes all preceding analysis into a single narrative paragraph with an actionable direction judgment. This is the bridge between raw data and the probability numbers. Without it, the report is a pile of numbers without a thesis.

---

## Section 6: Output Format

**所有分析报告必须生成为 HTML 文件，使用内置模板。**

### 模板位置

```
assets/report-template.html — 完整 HTML 模板（~41KB）
```

模板包含：
- 响应式 CSS（卡片、表格、概率条、颜色主题）
- 顶部汇总卡片（4 场比赛一览 + 置信度标签）
- 每场比赛 10 步框架（Step 1-10 HTML 结构）
- Step 11 免責声明
- 中国股市红涨绿跌配色（主胜降赔 = 绿色标记, 客胜升赔 = 红色标记）

### 使用方式

```
1. 读取 assets/report-template.html，理解 CSS 变量和 DOM 结构
2. 用实际分析数据填充：
   - 标题中的日期和配额信息
   - 4 张 summary-card（对阵、比分、置信度）
   - 每场比赛的 step 内容（基本面表格、赔率表格、六维评分、风险清单、比分预测）
3. 输出到当前工作目录，命名为 worldcup_YYYY-MM-DD_analysis.html
4. 调用 present_files 展示结果
```

### 模板占位符替换清单

| 替换区域 | 具体内容 |
|:---|:---|
| 页面标题 / .header h1 | 比赛日日期 |
| .header .meta | 生成时间 + 数据源 |
| .header .quota | 双配额显示: "✅ 本次消耗: N 配额 · 累计: X/总（来源 /v4/account）"<br>本次消耗 = 从 `/v4/account` 调用前 snapshot 计算差值<br>累计/总均从 `/v4/account` 实时获取 |
| .summary-grid ×4 | 对阵、预测比分、置信度标签 (conf-high/conf-mid/conf-low) |
| #m1-#m4 → Step 1 | 数据源详情（端点、博彩商、数据点数） |
| #m1-#m4 → Step 2 | 基本面表格（战绩、伤停、交锋、关键因素） |
| #m1-#m4 → Step 3 | 欧赔计算表（开盘/即时/真实概率 + 返还率） |
| #m1-#m4 → Step 4-6 | 欧亚匹配 + 三家博彩商对比表 + 变动分析 |
| #m1-#m4 → Step 7 | 六维评分（6 行通过/未通过 + 总分 badge） |
| #m1-#m4 → Step 8 | 风险清单（highlight-box 黄色/红色标注） |
| #m1-#m4 → Step 9 | 综合总结（绿色/红色结论框 + 一句话 + 可执行判断） |
| #m1-#m4 → Step 10 | 概率条 + 比分预测卡片（主比分 + 备选比分） |
| .disclaimer | 数据源、配额消耗、模型说明 |

---

## Section 7: Quick Start

### Register OddsPapi (the only thing needed)

https://oddspapi.io → Free signup → Get API key

Provide key to start: `My OddsPapi API key is xxxxxx`

### Daily Execution Plan (4 matches × 3 checks/day)

```
Phase 0 (first run): ⚠️ Ask user to confirm /v4/fixtures × 1 = 1 quota → 1 quota
Phase 1 (morning):   /v4/historical-odds × 4 → 0 quota (free, no confirmation, ≥5s apart)
Phase 2 (afternoon): /v4/historical-odds × 4 → 0 quota (free, no confirmation, ≥5s apart)
Phase 3 (T-1h):      ⚠️ Ask user to confirm /v4/odds × 4 = 4 quota → 4 quota

Daily billed: 0-4 quota | Monthly: 1+120=121/250 | Free calls: unlimited
```

### Example: Providing API Key
```
User: My OddsPapi API key is xxxxxx
You: ✅ OddsPapi configured (250/month)
     Free: /v4/historical-odds (unlimited), /v4/account
     Billed: all other endpoints (1 quota/call, will confirm before each)
```

### Example: Morning Analysis
```
User: Analyze today's 4 World Cup matches

You (morning phase):
1. fixtureIds cached → 0 quota
2. MATCH 1 (serial): GET /v4/historical-odds?...&bookmakers=pinnacle,bet365,williamhill
   → parse on-the-fly → extract ONLY market 101 prices → ~2-5KB slim output
3. MATCH 2 (serial): same pattern → ok
4. MATCH 3 (serial): same pattern → ok
5. MATCH 4 (serial): same pattern → ok
6. WebSearch → injuries/standings/H2H
7. Execute 11-step analysis (focus: opening positioning + multi-bookmaker dispersion)
8. Output 4 match reports
   → Quota used: 0
```

### Example: Pre-match Analysis >1h before kickoff
```
User: Pre-match analysis for Czech Republic vs South Africa

You:
1. GET /v4/account → check quota
2. Read fixture from cache → match at 19:00, current 10:00 = 9h before
3. 9h > 1h → /historical-odds only (free, 3 major bookmakers, cap=max 3)
4. GET /v4/historical-odds?fixtureId=X&bookmakers=pinnacle,bet365,williamhill&outcomeId=101,102,103 → FREE
5. Parse on-the-fly → extract only market 101: {open, now, changes} per bookmaker
6. Discard raw response (no file save needed)
7. WebSearch fundamentals
8. Output 11-step report, note: "early analysis, based on historical odds chain"
   → Quota used: 0
```

### Example: Pre-match T-1h
```
User: Pre-match prediction for Czech Republic vs South Africa
Time: 17:55, kickoff 19:00 (65 min before)

You:
1. GET /v4/account → check remaining
2. 65 min ≤ 1h → /odds needed (1 quota)
3. ⚠️ Ask user: "Live odds needed for this match = 1 quota. Current: X/250. Proceed? (yes/no)"
4. After user confirms "yes":
5. GET /v4/odds?fixtureId=X → 1 quota → 12MB response
6. Parse on-the-fly: extract ONLY pinnacle 1X2 + AH main line + O/U main line
7. WebSearch fundamentals
8. Execute 11-step analysis
9. Output final report with score projection
   → Quota used: 1, remaining: X/250

After this match finishes → proceed to next match (serial).
```

### Example: Multi-match Batch (4 matches, all >1h)
```
User: Analyze today's 4 World Cup matches

You:
1. GET /v4/account → check remaining ≥ 1 (fixtures) + 0 (historical)
2. Check /tmp/oddspapi_fixtures_16.json → exists → read from cache (0 quota)
3. Calculate time-to-kickoff for all 4 → all >1h → /historical-odds only

4. MATCH 1 (serial): GET /v4/historical-odds?...&bookmakers=pinnacle,bet365,williamhill
   → parse on-the-fly → extract only market 101 → ~2-5KB → ok
5. MATCH 2 (serial): same → ok
6. MATCH 3 (serial): same → ok
7. MATCH 4 (serial): same → ok

8. WebSearch fundamentals for all matches
9. Execute 11-step analysis for all 4
   → Quota used: 0 (all historical-odds are free)
```

### Web Mode (no API key fallback)

1. Send analysis request directly, no configuration needed
2. Auto-fetch: **OddsSafari** (multi-bookmaker odds) + **Tribuna/OddsFlow** (fundamentals) + **WebSearch**

**Limitations**:
- No opening odds data (Step 5 limited)
- No movement timeline (Step 6 limited)
- Mark report with "opening odds missing, movement timeline missing"

---

## Section 8: Boundary Rules

1. **Quota safety (non-negotiable)**: Section 0 rules ALWAYS apply — serial calls, pre-check, max 1 retry, response validation, no silent endpoint switching, billed calls require user confirmation. Violating any of these = wasted quota = degraded user experience.
2. **Billed endpoint confirmation**: Any call to a billed endpoint (/v4/odds, /v4/fixtures, /v4/scores, /v4/odds-by-tournaments, /v4/tournaments, etc.) MUST be pre-confirmed by the user. Show quota impact before asking. Never assume consent.
3. **No silent switch**: If a free endpoint (/v4/historical-odds) times out, is rate-limited, truncated, or returns no data → ask the user for options. NEVER auto-switch to a billed endpoint.
4. If API fails (after 1 retry) → auto-switch to web mode for that fixture, mark report header
5. If response truncated → mark as partial data, proceed with available data + note limitation
6. Refuse to generate exact score predictions, guaranteed-win schemes, or martingale strategies
7. Do not recommend any betting sites or API providers
8. Do not overstate analysis value: vig means long-term mathematical expectation is negative
9. If user requests betting advice → refuse and restate educational positioning
10. Overseas matches only; follow local laws for domestic events
11. Never write API credentials to any file (skill, memory, or cache)
12. `/v4/historical-odds` uses 3 major bookmakers (API cap: max 3, rate limit: 5000ms). Keep only 3 markets per bookmaker: market["101"] (1X2) + top-2 2-outcome markets by entry count (main AH + main O/U). Discard all altLines, player props (goalscorers, assists, shots), corner counts, card counts. Fields: price + createdAt only. Raw response is transient (pipe, don't save).
