---
name: 500com-football-scraper
description: "Scrape full football odds data from 500.com. v2.7: 全六页结构化解析+GB2312编码规范+竞彩双源提取(ouzhi+rangqiu)."
agent_created: true
version: "2.7"
---

# 500.com Football Odds Scraper v2.7

> **v2.7 全六页结构化数据提取**: 新增 ouzhi 页凯利指数/概率%/返还率/离散度全量解析; yazhi/daxiao 页完整水位+盘口变动时间戳; touzhu 页必发成交+模拟盈亏+冷热指数; rangqiu 页让球赔率全量; GB2312 编码处理规范。

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
| **ouzhi** | `https://odds.500.com/fenxi/ouzhi-{id}.shtml` | **30家博彩公司** (含 竞彩官方 row 1) SPF 开盘→即时, 凯利指数, 概率百分比, 返还率, 离散度 |
| **yazhi** | `https://odds.500.com/fenxi/yazhi-{id}.shtml` | **17家博彩公司** AH 开盘→即时, 水位, 盘口变动时间戳 |
| **rangqiu** | `https://odds.500.com/fenxi/rangqiu-{id}.shtml` | **18家博彩公司** RQSPF 开盘→即时 (含 竞彩官方 row 1 "竞*官*") |
| **daxiao** | `https://odds.500.com/fenxi/daxiao-{id}.shtml` | **18家博彩公司** OU 开盘→即时, 大小球界线+水位+变动时间戳 |
| **shuju** | `https://odds.500.com/fenxi/shuju-{id}.shtml` | FIFA 排名, H2H, 近期状态, 预计阵容, 场均统计 |
| **touzhu** | `https://odds.500.com/fenxi/touzhu-{id}.shtml` | 必发成交量, 庄家盈亏, 冷热指数, 投注分布, 大额交易明细, 模拟盈亏 |

抓取前先检查 `.cache/shared-football/raw/{date}/{page}_{shuju_id}.html` 是否存在，存在则跳过 WebFetch。

> ⚠️ **v2.7 GB2312 编码铁律**: 500.com 深分页使用 GB2312 编码。WebFetch 工具保存时可能损坏中文字符。
> 使用 Python `urllib` 直接抓取 → `open(path, "wb")` 保存原始字节 → 读取时 `raw.decode("gb2312")`。
> 集成方案: `python3 scripts/fetch_and_parse.py --shuju-id ID --date DATE`

### Phase 3: Parse key data

#### ouzhi parsing — 全量字段提取 (v2.7)

```
HTML 结构: 每行 = <td class="tb_plgs" title="公司名"> + 17 个数字单元格

关键发现:
  ⭐ Row 1 = 竞彩官方 SPF 赔率 (title="竞*官*", country=中国, cid=1)
  ⭐ Row ~12 = Pinnacle (title="Pi****le平*", cid=1055)

每行提取 17 个字段 (按顺序):
  [0-2]   开盘 SPF (主/平/客)
  [3-5]   即时 SPF (主/平/客)
  [6-8]   开盘概率% (主/平/客) — 含 class="plgreen"
  [9-11]  即时概率% (主/平/客)
  [12]    返还率开盘%
  [13]    返还率即时%
  [14-16] 即时凯利指数 (主/平/客) — 含 class="bd_red/blue/green"

表格底部汇总:
  平均值: 即时/开盘各3值
  最高值/最低值: 同理
  离散值: 3 个数值 (主胜离散/平局离散/客胜离散)

总共: 30家博彩公司 × 17字段 = 510个数据点/场

All 30 bookmakers row format:
  index | name | open H/D/A | current H/D/A | open prob%/%/% | current prob%/%/% | return rate | current Kelly H/D/A

Average row (last row): extract mean + max + min + dispersion
```

#### yazhi parsing — 17家完整数据 (v2.7)

```
HTML 结构: <td class="tb_plgs"><a title="公司名"> (名称在 <a> 而非 <td> 上)

每家博彩公司行:
  公司名 | 即时水位/盘口/水位 | 变动时间 | 开盘水位/盘口/水位 | 开盘时间

提取字段:
  name, cid, current_water_home, current_handicap, current_water_away, change_time,
  open_water_home, open_handicap, open_water_away, open_time

Pinnacle = title="Pi****le平*" (cid=1055), 共 17 家公司
水位变化标记: ↑ = 升高, ↓ = 降低

中文盘口 → 数字映射:
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

#### shuju parsing — 赛前基本面数据（v2.6 新增结构化字段）

```
FIFA ranking: "西班牙\[世2\]" → home_rank=2

H2H: "双方近3次交战，西班牙3胜0平0负，进9球，失2球"
  → {matches:3, home_wins:3, draws:0, away_wins:0, goals_for:9, goals_against:2}

Recent form: "近10场战绩6胜4平0负进25球失4球"
  → {matches:10, wins:6, draws:4, losses:0, goals_for:25, goals_against:4, form_trend:"上升/平稳/下降"}

Home/Away records: same format

Expected lineup: starters + substitutes + injuries/suspensions (name lists)
  → starters: [{name, position, is_key:true/false}]
  → injuries: [{name, position, impact:"high/medium/low"}]
  → formation: "4-3-3" (从页面提取阵型文本，可能做正则匹配)

**v2.6 新增结构化字段**（用于 analyst 赛前信息检查）:
  pre_match_info: {
    formation: "4-3-3",              // 主队阵型
    away_formation: "4-4-2",         // 客队阵型
    key_absences: [                   // 核心球员缺阵
      {name:"凯恩", position:"前锋", impact:"high", reason:"伤病"},
      {name:"赖斯", position:"中场", impact:"medium", reason:"停赛"}
    ],
    lineup_stability: "主力11人基本不变/3处轮换/大幅轮换",
    form_trend_home: "上升/平稳/下降",  // 主队近5场趋势
    form_trend_away: "上升/平稳/下降",  // 客队近5场趋势
    avg_goals_scored_home: 2.1,        // 主队场均进球
    avg_goals_conceded_home: 0.8,      // 主队场均失球
    avg_goals_scored_away: 1.3,        // 客队场均进球
    avg_goals_conceded_away: 1.5,      // 客队场均失球
    coach: "主队教练名",                 // 来自页面
    away_coach: "客队教练名"
  }
```

#### touzhu parsing — 必发全量数据 (v2.7)

```
HTML 静态包含 4 个数据区块 (不需要 JS):

1. 热度分析表:
   列: 百家欧赔/必发指数/必发成交(成交价+成交量+庄家盈亏)/指数分析(必发指数+冷热指数+盈亏指数)
   每行: 主胜/平局/客胜 各有完整数值

2. 必发总成交额 + 成交量明细 (主/平/客三向)

3. 必发大额交易明细:
   逐笔记录: 结果|方向|成交额|交易时间|交易比例

4. 模拟盈亏表: 庄家在不同价格区间的盈亏模拟

提取脚本: scripts/fetch_and_parse.py → parse_touzhu()
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

1. **Encoding**: ⚠️ v2.7 关键修正 — **深分页全部使用 GB2312 编码**，不是 UTF-8。WebFetch 工具保存时可能导致中文字符损坏。使用 Python `urllib` 直接抓取 + `open("wb")` 保存原始字节 + `decode("gb2312")` 读取。详见上方 "GB2312 编码铁律" 章节。
2. **shuju ID extraction**: From trade page links like `<a href="/fenxi/shuju-XXXXXXX.shtml">`.
3. **Pinnacle**: ouzhi 页 row ~12 (title="Pi****le平*", cid=1055); yazhi/daxiao 页同样 cid=1055。
4. **竞彩官方赔率双源提取 (v2.7)**:
   - **SPF (胜平负)**: ouzhi 页 row 1 = "竞*官*" (title, country=中国, cid=1) → 竞彩官方 SPF
   - **RQSPF (让球胜平负)**: rangqiu 页 row 1 = "竞*官*" → 竞彩官方 RQSPF (让球数+赔率)
   - 深盘场次: 竞彩可能只开 RQSPF 不开 SPF (ouzhi 页仍有 row 1 但赔率不可用)
5. **Not-yet-open**: RQSPF showing "未开售" → set field to null.
6. **Network**: 6 pages × N matches = many pages. Fetch 2-3 pages concurrently with random delay (0.5-1.5s).
7. **数据分层**:
   - 分析层数据: ouzhi(30家+Pinnacle+凯利+概率+离散) / yazhi(17家亚盘) / daxiao(18家大小球) / shuju(基本面) / touzhu(必发成交+模拟盈亏+冷热指数)
     用于 football-odds-analyst 的盘口分析、MBI、OCI等全部分析步骤
   - 执行层数据: ouzhi页 row 1 竞彩SPF + rangqiu页 row 1 竞彩RQSPF
     专供 football-odds-analyst 的 Step 11 (投注建议/EV计算) 使用
   - **数据源不能混淆**: 分析用全球数据，投注用竞彩赔率
8. **集成解析脚本**: `scripts/fetch_and_parse.py` — 一次运行抓取+解析所有6页，输出结构化JSON到缓存。

---

## 数据结构手册 & 踩坑记录 (2026-06-24 验证通过)

> ⚠️ **以下为实测验证过的数据格式，后续解析必须遵守。**

### 各页 HTML 结构差异

| 页面 | 名称提取方式 | 数据结构 | 数量 |
|:---|:---|:---|:---:|
| ouzhi | `<td title="NAME">` | 4 个嵌套 `<table>`，每表 2 行(开/即) | 30 家 |
| rangqiu | `<td title="NAME">` (同 ouzhi) | 同 ouzhi + 让球数在第一个 table 前 | 16 家 |
| yazhi | `<td><a title="NAME">` (不同!) | 2 个嵌套 `<table>` (即时/开盘) | 17 家 |
| daxiao | `<td><a title="NAME">` (同 yazhi) | 2 个嵌套 `<table>`，无 `cid=` | 18 家 |
| touzhu | 无 tb_plgs，队名在纯文本 | 热度分析表: `队名 \| \| 数据 \| \| 数据...` | 3 行 |
| shuju | 正则提取 | H2H/战绩仅赛前有，赛后清空 | — |

### 关键正则模式

**ouzhi / rangqiu: 提取 20 个字段**
```
策略: finditer 定位所有 tb_plgs → 位置切片 chunk → 提取嵌套 <table> → 逐表 regex numbers
注意: 不能用 re.findall(r'<tr>.*?</tr>') — 嵌套 <tr> 会截断
```

**touzhu: 双 pipe 分隔符**
```
原始: 阿根廷| |1.45| |65.3%| |-| |90.2%| |1.48| |49,153,016| |-18,242,900| |-| |38| |-34
                      ↑↑ 两个 pipe 中间有空格，不是单个 pipe!
regex: ([\u4e00-\u9fff]+)\s*\|\s*\|\s*([\d.]+)\s*\|\s*\|\s*([\d.]+)% ...
```

**竞彩双源**:
| 赔率类型 | 页面 | 位置 | cid |
|:---|:---|:---|:---|
| SPF (胜平负) | ouzhi | row 1 `title="竞*官*"` | 1 |
| RQSPF (让球) | rangqiu | row 1 `title="竞*官*"` | — |
| 深盘未开 SPF | ouzhi row 1 存在但无赔率 | 仅 RQSPF 可用 | — |

### 踩过的坑

1. **GB2312 编码**: WebFetch 保存 → 中文损坏。必须 `urllib` 取 → `open("wb")` 存 → `decode("gb2312")` 读
2. **嵌套 table**: `re.findall(r'<tr>(.*?)</tr>')` 会因为嵌套 `<tr>` 截断外层的行。用位置切片替代
3. **cid 缺失**: daxiao 页链接无 `cid=` 参数。通过 `title` 属性匹配替代
4. **shuju H2H 数据**: 赛后 500.com 清空赛前分析。实时使用 OK，回测无法获取
5. **ouzhi row count**: 始终 30 家，不是 50+。AJAX 分页 `start=30` 返回空
6. **竞彩未开售**: ouzhi row 1 存在但 SPF 赔率为空。检查 `spf_current` 是否包含数据

### 集成用法

```bash
# 单场
python3 scripts/fetch_and_parse.py --shuju-id 1359172 --date 2026-06-12 [--no-cache]

# 批量（脚本会自动处理 GB2312 + 嵌套 table + 所有 6 页）
for sid in $(cat match_ids.txt); do
    python3 scripts/fetch_and_parse.py --shuju-id $sid --date $date --no-cache
done
```

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
