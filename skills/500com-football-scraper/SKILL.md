---
name: 500com-football-scraper
description: "从 500.com 爬取竞彩足球全量赔率数据，默认 deep 模式（每场6页深度分析：ouzhi/yazhi/rangqiu/daxiao/shuju/touzhu），支持 --quick 快速模式，输出标准化 JSON"
agent_created: true
version: "2.0"
---

# 500.com 竞彩足球数据爬虫 v2.0

> 默认 deep 模式：每场抓取 6 个深度分析页（百家欧赔/亚盘对比/让球指数/大小指数/数据分析/投注分析），覆盖 30 家博彩公司含 Pinnacle。
> 输出标准化 JSON，供 `football-odds-analyst` 直接消费。12h 缓存复用。

## 触发

- 用户提到「500.com」「竞彩」「拉取赔率」「爬数据」
- `football-odds-analyst` 依赖调用
- 任何需要 500.com 结构化数据的场景

---

## 两种模式

### deep 模式（默认）

每场抓取 6 个分析页 + 基础 trade 页 + XML，输出全量 JSON。

```bash
python3 references/parser.py --date 2026-06-22 --json
```

### quick 模式（`--quick`）

仅 trade 页 + XML，输出基础赔率。用于快速预览。

```bash
python3 references/parser.py --date 2026-06-22 --quick --json
```

---

## 执行流程（deep 模式）

### Phase 1：获取比赛列表 + shuju ID

```
1. WebFetch https://trade.500.com/jczq/?playid=312&g=2
   提取：比赛编号、队名、排名、时间、shuju ID（从 /fenxi/shuju-XXXXXXX.shtml 链接）
2. 按日期过滤
3. 得到 match_list = [{code, datetime, home_team, away_team, home_rank, away_rank, shuju_id, handicap_rqspf}]
```

### Phase 2：每场抓取 6 个深度分析页

对每场比赛，WebFetch 以下 6 个 URL（{id} 替换为 shuju_id）：

| 页面 | URL 模板 | 核心数据 |
|:---|:---|:---|
| **ouzhi** 百家欧赔 | `https://odds.500.com/fenxi/ouzhi-{id}.shtml` | 30 家博彩公司 SPF 初盘→即时，概率，凯利指数，离散值 |
| **yazhi** 亚盘对比 | `https://odds.500.com/fenxi/yazhi-{id}.shtml` | 16 家公司 AH 初盘→即时，水位，盘口变化时间戳 |
| **rangqiu** 让球指数 | `https://odds.500.com/fenxi/rangqiu-{id}.shtml` | RQSPF 初盘→即时，含竞彩官方 |
| **daxiao** 大小指数 | `https://odds.500.com/fenxi/daxiao-{id}.shtml` | OU 初盘→即时，盘口升降 |
| **shuju** 数据分析 | `https://odds.500.com/fenxi/shuju-{id}.shtml` | FIFA排名、H2H、近期战绩、预计阵容、场均数据 |
| **touzhu** 投注分析 | `https://odds.500.com/fenxi/touzhu-{id}.shtml` | 必发成交量、庄家盈亏、冷热指数、投注分布 |

### Phase 3：解析关键数据

#### ouzhi 解析规则

```
Pinnacle = 第 10 行（"Pi****le平*"）
提取: 初盘 SPF（前三位数）/ 即时 SPF（后三位数）/ 初盘概率 / 即时概率 / 凯利指数

全部 30 家逐行提取格式:
  序号 | 公司名 | 初盘胜/平/负 | 即时胜/平/负 | 初盘概率%/%/% | 即时概率%/%/% | 返还率 | 即时凯利胜/平/负

平均值行（最后一行）: 提取均值 + 最高值 + 最低值 + 离散值
```

#### yazhi 解析规则

```
Pinnacle = 第 10 行
提取: 即时水位 / 即时盘口 / 客水位 | 变化时间 | 初盘水位 / 初盘盘口 / 客水位 | 初盘时间

盘口中文→数值映射:
  平手=0, 平手/半球=0.25, 半球=0.5, 半球/一球=0.75, 一球=1.0, 一球/球半=1.25,
  球半=1.5, 球半/两球=1.75, 两球=2.0, 两球/两球半=2.25, 两球半=2.5, 两球半/三球=2.75, 三球=3.0
  受X球 = -X

方向: "升"=盘口加深, "降"=盘口回落, "↓"=水位降, "↑"=水位升
```

#### shuju 解析规则

```
FIFA排名: "西班牙\[世2\]" → home_rank=2
H2H: "双方近3次交战，西班牙3胜0平0负，进9球，失2球"
近期战绩: "近10场战绩6胜4平0负进25球失4球"
主场/客场战绩: 同样格式
预计阵容: 首发 + 替补 + 伤病/停赛（名单）
```

#### touzhu 解析规则

```
必发成交量: "1.13 1,176,453 -31,357" → price=1.13, volume=1176453, pl=-31357
投注比例: "86.3% 9.7% 3.9%" → home=86.3, draw=9.7, away=3.9
必发指数: 提取冷热指数和盈亏指数
```

### Phase 4：合并输出

```json
{
  "meta": {
    "source": "500.com",
    "date": "2026-06-22",
    "fetch_time": "2026-06-21T08:00:00+08:00",
    "match_count": 4
  },
  "matches": [
    {
      "code": "周日037",
      "datetime": "2026-06-22 00:00",
      "home_team": "西班牙",
      "away_team": "沙特阿拉伯",
      "home_rank": 2,
      "away_rank": 61,
      "league": "世界杯",
      "handicap_rqspf": -2,

      "ouzhi": {
        "pinnacle": {
          "open": {"home": 1.11, "draw": 9.11, "away": 18.94},
          "current": {"home": 1.09, "draw": 10.53, "away": 24.70},
          "prob_open": {"home": 84.71, "draw": 10.32, "away": 4.96},
          "prob_current": {"home": 87.14, "draw": 9.02, "away": 3.85},
          "kelly": {"home": 0.94, "draw": 1.02, "away": 0.96}
        },
        "all_bookmakers": [
          {"id": 1, "name": "威廉希尔", "open": [1.10, 8.50, 26.00], "current": [1.10, 9.50, 29.00], ...},
          ...
        ],
        "average": {"open": [1.11, 8.58, 21.60], "current": [1.10, 9.83, 24.58], ...},
        "dispersion": {"home": 6.04, "draw": 109.74, "away": 407.88}
      },

      "yazhi": {
        "pinnacle": {
          "current": {"home_water": 0.99, "handicap": 2.5, "away_water": 0.86},
          "open": {"home_water": 0.85, "handicap": 2.25, "away_water": 0.96},
          "change_time": "06-21 07:35",
          "direction": "升"
        },
        "all_bookmakers": [...16家...],
        "average": {"current": [0.958, -2.469, 0.873], "open": [0.852, -2.125, 0.933]}
      },

      "rangqiu": {
        "pinnacle": {"open": [1.95, 3.92, 2.99], "current": [...]},
        "official": {"open": [2.57, 3.43, 2.35], "current": [...]}
      },

      "daxiao": {
        "pinnacle": {
          "current": {"over_water": 1.00, "line": 3.25, "under_water": 0.85},
          "open": {"over_water": 0.94, "line": 3.00, "under_water": 0.86},
          "direction": "升"
        }
      },

      "shuju": {
        "fifa_rank": {"home": 2, "away": 61},
        "h2h": {"matches": 3, "home_wins": 3, "draws": 0, "away_wins": 0, "home_goals": 9, "away_goals": 2},
        "recent_form": {
          "home": {"matches": 10, "wins": 6, "draws": 4, "losses": 0, "goals_for": 25, "goals_against": 4},
          "away": {"matches": 10, "wins": 2, "draws": 3, "losses": 5, "goals_for": 10, "goals_against": 13}
        },
        "home_away_form": {
          "home_home": {"matches": 10, "wins": 5, "draws": 5, "losses": 0, ...},
          "away_away": {"matches": 10, "wins": 4, "draws": 2, "losses": 4, ...}
        },
        "lineup": {
          "home": {"starters": ["加维","拉波尔特",...], "subs": [...], "injuries": [], "suspensions": []},
          "away": {...}
        }
      },

      "touzhu": {
        "betfair": {
          "home": {"price": 1.13, "volume": 1176453, "pl": -31357},
          "draw": {"price": 12.06, "volume": 7946, "pl": 482683},
          "away": {"price": 30.05, "volume": 3636, "pl": -311045}
        },
        "distribution": {"home": 86.3, "draw": 9.7, "away": 3.9},
        "index": {"hot_cold": {"home": -4, "draw": -47, "away": -5}, "pl_index": {"home": -3, "draw": 37, "away": -24}}
      },

      "basic": {
        "spf_lc": {"home": 1.77, "draw": 4.05, "away": 3.15},
        "spf_avg": {"home": 1.10, "draw": 9.83, "away": 24.58},
        "ah_bet365": {"home_water": 1.0, "handicap": 2.5, "away_water": 0.85},
        "ou_bet365": {"over_water": 1.0, "line": 3.25, "under_water": 0.85},
        "jqs": {"0": 26.0, "1": 7.75, "2": 4.50, "3": 3.60, "4": 4.20, "5": 6.30, "6": 9.70, "7": 11.50},
        "bqc": {"胜胜": 1.26, "胜平": 35.0, ...},
        "bf": {"1:0": 8.0, "2:0": 5.50, ...}
      }
    }
  ]
}
```

### Phase 5：缓存

```
缓存位置: .cache/500com/{date}_deep.json
过期时间: 12 小时
--no-cache: 强制拉取新数据，覆盖缓存
```

---

## 注意事项

1. **编码**: trade.500.com 返回 GB2312，需转为 UTF-8。depth 分析页为 UTF-8，无需转换。
2. **shuju ID 获取**: 从 trade 页的 `<a href="/fenxi/shuju-XXXXXXX.shtml">` 链接提取。
3. **Pinnacle 行定位**: ouzhi 页第 10 行（"Pi****le平*"），yazhi 页同样第 10 行。
4. **未开售**: RQSPF 显示"未开售"时该字段置 null。
5. **网络**: 每场 6 页 × N 场比赛 = 页面多，建议 2-3 页并发拉取。

---

## quick 模式

仅拉取 trade 页 + XML，输出基础 JSON（不包含 ouzhi/yazhi/rangqiu/daxiao/shuju/touzhu 深度数据）。

```bash
python3 references/parser.py --date 2026-06-22 --quick --json
```

输出结构同 v1.0，包含 basic 段（SPF/RQSPF/AH/OU/JQS/BF/BQC），不含 deep 段。

---

## 命令行参考

| 参数 | 说明 | 默认 |
|:---|:---|:---|
| `--date YYYY-MM-DD` | 按日期过滤 | 全部 |
| `--quick` | 快速模式（仅基础） | deep 模式 |
| `--json` | JSON 输出 | 文本输出 |
| `--no-cache` | 跳过缓存强制刷新 | 使用缓存 |
| `--match 队名` | 查找特定球队 | 全部 |
| `--cache-dir DIR` | 缓存目录 | .cache/500com/ |
