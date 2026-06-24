---
name: 500com-football-scraper
description: "Scrape full football odds data from 500.com. v2.5: 按比赛 ID 查缓存 + JSON字段中文友好."
agent_created: true
version: "2.5"
---

# 500.com Football Odds Scraper v2.5

> **v2.5 按比赛 ID 查缓存 + JSON字段中文友好**: Phase 0 三步流——取 shuju_id → 按 ID 查缓存 → 仅抓缺失场次。
> 每场比赛独立缓存为 `{date}_{shuju_id}.json`，JSON 字段命名英文、值用中文。

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

### Phase 0: Shared Cache Protocol — 先取比赛 ID，按 ID 查缓存，再抓取缺失

> ⚠️ **所有足彩技能必须遵守此协议**。这是所有技能共用的数据缓存层。
> **核心逻辑**：先通过 Liansai API 或 trade 页面获取比赛 ID（轻量请求），再用 ID 逐场检查缓存，只抓取真正缺失的比赛。

#### Step 0a — 获取比赛列表 + shuju ID（先取 ID，不盲目搜缓存）

```
目标: 获取目标日期的比赛列表，每场含 shuju_id（后续抓取和缓存的唯一钥匙）

优先用 Liansai API（1 次 JSON 请求 = 全部比赛）:
  1. 如已知赛季 ID（sid），调用 Liansai API：
     GET https://liansai.500.com/index.php?c=match&a=getmatch&sid={sid}&round={round}
     返回 JSON 数组，每场含 fid（=shuju_id）、队伍、比分、百家平均赔率
  2. 如需获取赛季 ID，打开 https://liansai.500.com/ 找到目标赛事 URL
     从 https://liansai.500.com/zuqiu-{sid}/ 提取 sid

后备方案（无赛季 ID 时用 trade 页面）:
  1. WebFetch https://trade.500.com/jczq/?playid=312&g=2
     提取: 比赛 code、队名、排名、时间、shuju_id（从 /fenxi/shuju-XXXXXXX.shtml 链接）
  2. WebFetch https://trade.500.com/jczq/?playid=312&g=1
     提取单关标记: single_match_available = true/false
  3. Filter by date

输出 match_list: [{shuju_id, datetime, home_team, away_team, ...}]
```

> 💡 **Liansai API 比 trade 页面轻量 10 倍**（纯 JSON，无 HTML 解析成本）。
> 有赛季 ID 时优先用 Liansai API。

#### Step 0b — 按 shuju_id 逐场检查缓存

```
拿到 match_list 后，对每场比赛的 shuju_id 逐场检查共享缓存:

  对 match_list 中的每场比赛:
    shuju_id = match["shuju_id"]
    cache_path = .cache/shared-football/parsed/{date}_{shuju_id}.json

    如果 cache_path 存在且 mtime < 12h:
      → 标记为 CACHED（跳过后续全部抓取）
    如果不存在或过期:
      → 标记为 NEED_FETCH（后续逐场抓取）

汇总:
  cached_count = 命中缓存的场次数
  fetch_count  = 需要抓取的场次数
```

> ⚠️ **不再盲目搜索 `{date}_deep.json`**。每场比赛按自己的 shuju_id 独立检查缓存，
> 不同比赛不会互相污染。一场数据过时不影响其他场。

#### Step 0c — 逐场抓取 + 保存

```
对 NEED_FETCH 的比赛:

1. 对该场的每个页面类型（ouzhi/yazhi/rangqiu/daxiao/shuju/touzhu）:
   → 检查 .cache/shared-football/raw/{date}/{page}_{shuju_id}.html 是否存在
   → 存在则跳过该页的 WebFetch，直接解析
   → 不存在才 WebFetch → 保存到 raw/ → 解析

2. 该场 6 页全部就绪后:
   → 解析合并为结构化 JSON
   → 写入 .cache/shared-football/parsed/{date}_{shuju_id}.json（单场独立）
   → 可选: 同时更新 parsed/{date}_deep.json（全量汇总，非必需）

3. 并发控制: 同时处理 2-3 场比赛
```

> **每场比赛独立缓存的好处**:
> - 不同技能需要不同场次时，只抓取自己缺的场次
> - 某天新增一场比赛，只抓那一场，不影响已有缓存
> - 过期策略按场次独立控制

#### 三种读路径（按优先级）

| 优先级 | 路径 | 动作 | JSON需要 | WebFetch |
|:---:|:---|:---|:---:|:---:|
| 1️⃣ | `parsed/{date}_{shuju_id}.json` 命中 | 直接读取该场 JSON | **✅ 最快** | **0 次** |
| 2️⃣ | `raw/{date}/` 有部分 HTML | 解析已有 HTML 写回 parsed/ | 少量 | **0 次**（已有页） |
| 3️⃣ | 完全缺失 | 按 ID 逐页抓取 → 保存到 raw/ + parsed/ | 按需 | **仅缺失页** |

#### 关键规则

```
1. 先取 ID (Step 0a)，再检缓存 (Step 0b)，最后抓取 (Step 0c)
2. 缓存按 shuju_id 独立（非按日期聚合），一场的缓存不影响另一场
3. 每页面独立检查 raw/，只抓缺失页，绝不重复
4. 过期检查: 每个 shuju_id JSON 的 mtime < 12h
5. 并发: 2-3 场同时处理，每场内串行抓 6 页
6. 跨技能: 其他技能（analyst/backtest）发起时，同样走 Step 0a→Step 0b→Step 0c
```

#### Token 节省策略

```
✅ 先走 Liansai API（纯 JSON，1 次请求搞定所有 shuju_id）
✅ 按 shuju_id 独立缓存（不盲目搜深文件）
✅ 每场逐页检查 raw/，只抓缺失页
✅ 多场并发（2-3 场同时）
❌ 绝不盲目搜 `{date}_deep.json` 这种日期级文件
❌ 绝不重复抓取同一 shuju_id 的同一 page
❌ 绝不爬没出现在 match_list 中的比赛
```

> **🎯 精髓**: 两步轻量获取 ID（Liansai API 或 trade 页）→ 拿着 ID 精准查缓存 →
> 只抓缺失的场次和页面。不盲目搜索，不重复爬取。

### Phase 1: 按 shuju_id 逐场抓取 6 页

> ⚠️ match_list 已在 Phase 0 Step 0a 获取，此处直接按 NEED_FETCH 列表中的 shuju_id 抓取。

对 `NEED_FETCH` 列表中的每个 shuju_id，按以下6个页面并行（2-3场并发，场内串行）：

| Page | URL Template | Key Data |
|:---|:---|:---|
| **ouzhi** | `https://odds.500.com/fenxi/ouzhi-{id}.shtml` | 30 bookmakers SPF open→current, probability, Kelly index, dispersion |
| **yazhi** | `https://odds.500.com/fenxi/yazhi-{id}.shtml` | 16 bookmakers AH open→current, water level, handicap change timestamps |
| **rangqiu** | `https://odds.500.com/fenxi/rangqiu-{id}.shtml` | RQSPF open→current, including official odds |
| **daxiao** | `https://odds.500.com/fenxi/daxiao-{id}.shtml` | OU open→current, line direction |
| **shuju** | `https://odds.500.com/fenxi/shuju-{id}.shtml` | FIFA ranking, H2H, recent form, expected lineup, avg stats |
| **touzhu** | `https://odds.500.com/fenxi/touzhu-{id}.shtml` | Betfair volume, bookmaker P&L, hot/cold index, distribution |

抓取前先检查 `.cache/shared-football/raw/{date}/{page}_{shuju_id}.html` 是否存在，存在则跳过 WebFetch。

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

#### rangqiu parsing

```
竞彩官方让球胜平负赔率（关键数据 — 用于投注建议）:
  Row 1 = "竞*官*" — 竞彩官方赔率（唯一真实竞彩赔率源）
  行格式: 公司名 | [让球数][初盘主][初盘平][初盘客][即时主][即时平][即时客]
    数字连续无分隔符，按长度解析:
      让球数: 正负号+1位数字 (如 -1, 0, +2)
      初盘3值: 主/平/客 (每个值1-3位小数)
      即时3值: 主/平/客
    示例: "-12.253.182.702.003.253.11"
      → 让球=-1, 初盘=2.25/3.18/2.70, 即时=2.00/3.25/3.11

  输出到JSON的 jingcai_rqspf 字段:
  {
    "handicap": -1,
    "open": {"home": 2.25, "draw": 3.18, "away": 2.70},
    "current": {"home": 2.00, "draw": 3.25, "away": 3.11}
  }

其他博彩公司行: 格式同上，仅用于赔率对比参考，不作为投注依据
未开售: "未开售" → jingcai_rqspf = null
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

### Phase 5: Cache (共享缓存 — 按 shuju_id 独立)

```
原始HTML:  .cache/shared-football/raw/{date}/{page}_{shuju_id}.html
  (每个页面独立缓存，其他技能可直接复用单页)

解析JSON:  .cache/shared-football/parsed/{date}_{shuju_id}.json
  (每场比赛独立缓存，不互相污染)

汇总JSON:  .cache/shared-football/parsed/{date}_deep.json  (可选)
  (全量汇总，仅用于需要全部场次时的批量读取)

过期: 12小时（检查每个 shuju_id JSON 的 mtime）
--no-cache: 强制刷新，覆盖某个 shuju_id 的缓存
```

---

## Notes

1. **Encoding**: trade.500.com returns GB2312, must convert to UTF-8. Deep analysis pages are UTF-8, no conversion needed.
2. **shuju ID extraction**: From trade page links like `<a href="/fenxi/shuju-XXXXXXX.shtml">`.
3. **Pinnacle row**: Row 10 in ouzhi page ("Pi****le"), same position in yazhi page.
4. **Not-yet-open**: RQSPF showing "未开售" → set field to null.
5. **Network**: 6 pages × N matches = many pages. Fetch 2-3 pages concurrently.
6. **数据分层**:
   - 分析层数据: ouzhi(30家+Pinnacle) / yazhi(16家亚盘) / shuju(基本面) / touzhu(必发成交量)
     用于足球-odds-analyst 的盘口分析、MBI、OCI等全部分析步骤
   - 执行层数据: rangqiu页"竞*官*"行 → jingcai_rqspf
     专供足球-odds-analyst 的Step 11(投注建议/EV计算)使用
   - **数据源不能混淆**: 分析用全球数据，投注用竞彩赔率

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
| `--no-cache` | 跳过缓存，强制刷新 | 使用缓存 |
| `--match NAME` | 按队伍名过滤 | 所有比赛 |
| `--cache-dir DIR` | 解析JSON缓存目录 | `.cache/shared-football/parsed/` |
| `--raw-dir DIR` | 原始HTML缓存 | `.cache/shared-football/raw/` |

---

## Liansai API (赛事/联赛数据) — v2.1 新增

> 从 liansai.500.com 内部API获取完整赛事赛程、比分和shuju ID，**比页面抓取快10倍**。
> 支持: 小组赛/联赛/杯赛全阶段（含淘汰赛占位符）。

### API 端点

```
GET https://liansai.500.com/index.php?c=match&a=getmatch&sid={season_id}&round={round}
```

| 参数 | 说明 | 示例 |
|:---|:---|:---|
| `sid` | 赛季ID（从liansai URL提取） | 19476 (= 2026世界杯) |
| `round` | 轮次/组别 | `A` (组名) 或 `1` (轮次号) |

### 获取 Season ID

1. 打开目标赛事的 liansai 页面
2. 从URL中提取: `https://liansai.500.com/zuqiu-{sid}/`
3. 示例: 2026世界杯 = `zuqiu-19476/` → sid=19476

### 响应格式

```json
[
  {
    "fid": 1359172,        // shuju ID (用于后续 fetch_ouzhi/yazhi 等)
    "stime": "2026-06-12 03:00",  // 开赛时间
    "hid": 16,             // 主队内部ID
    "gid": 9,              // 客队内部ID
    "hscore": 2,           // 主队全场进球 (未赛=0)
    "gscore": 0,           // 客队全场进球
    "hhalfscore": 1,       // 半场主队进球
    "ghalfscore": 0,       // 半场客队进球
    "status": 5,           // 比赛状态: 1=未开始, 2=上半场, 3=半场,
                           //   4=下半场, 5=已结束, 6=取消, 7=改期
    "hname": "墨西哥",     // 主队全名
    "hsxname": "墨西哥",   // 主队简称
    "gname": "南非",       // 客队全名
    "gsxname": "南非",     // 客队简称
    "channel": "",         // 直播频道
    "win": 1.43,           // 百家平均主胜赔率
    "draw": 4.3,           // 百家平均平赔
    "lost": 8.21           // 百家平均客胜赔率
  },
  ...
]
```

### 用法

#### 获取赛事全部比赛 (推荐)

对每个组别/轮次依次请求，例如12组比赛:

```python
for group in "ABCDEFGHIJKL":
    url = f"https://liansai.500.com/index.php?c=match&a=getmatch&sid={sid}&round={group}"
    # fetch JSON → parse → collect all matches
```

#### 区分状态

| status | 含义 | 动作 |
|:---:|:---|:---|
| 1 | 未开始 | `score="?"`, 回测中跳过 |
| 5 | 已结束 | `score = "{hscore}:{gscore}"`, 可回测 |
| 2-4, 6-11 | 进行中/取消/改期 | 跳过或特殊处理 |

### 与 Phase 0 共享缓存协议的配合

```
在 Phase 0 Step 0a 中优先使用 Liansai API 获取比赛列表 + shuju_id:
  Step 1: Liansai API → 获取该赛事所有比赛 (含 shuju_id + 赛果)
  Step 2: 按 shuju_id 逐场检查共享缓存 (Phase 0 Step 0b)
  Step 3: 仅 NEED_FETCH 的 shuju_id → 按 Phase 1 逐场抓取 (Phase 0 Step 0c)
  Step 4: 保存到 .cache/shared-football/parsed/{date}_{shuju_id}.json
```

### 已知 Season ID

| 赛事 | sid | 备注 |
|:---|:---:|:---|
| 2026世界杯 | 19476 | 48队, 12组 |
| 2025非洲杯 | 18603 | 参考 |
| (其他赛事可从URL提取) | | |

> ⚠️ 该API返回百家平均赔率(win/draw/lost)，**非Pinnacle赔率**。Pinnacle赔率仍需通过
> `fetch_ouzhi(shuju_id)` 从 odds.500.com/fenxi/ouzhi-{id}.shtml 单独获取。

---

## 数据输出规范 — JSON 字段命名友好

> 本机输出 JSON 供其他技能消费（非直接给用户看），但字段命名和注释应便于人类阅读。

### JSON 字段命名规则

```json
{
  "match_id": 12345,           // ✓ 好: 英文小写下划线，一眼看懂
  "home_team": "巴西",          // ✓ 好: 球队名用中文原名
  "away_team": "阿根廷",
  "pinnacle_spf": {            // ✓ 好: Pinnacle 保留原名（品牌名不翻译）
    "open": {"home": 1.45, "draw": 4.30, "away": 7.00},
    "current": {"home": 1.42, "draw": 4.50, "away": 7.50}
  }
}
```

### 命名原则

```
1. 字段名用英文小写下划线（JSON 标准，其他技能直接消费）
2. 字段值中的文字用中文（队名、状态、联赛名等）
3. 博彩公司名保留原名（Pinnacle、bet365、威廉希尔等）
4. 让球数、盘口值用数字，不用中文描述
5. 注释用中文（便于直接人审阅 JSON）
```

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
