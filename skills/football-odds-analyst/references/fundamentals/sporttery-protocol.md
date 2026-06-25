# 竞彩官网数据源协议 v2.1

> **P0 铁律**: 投注赔率以竞彩官网 (sporttery.cn) 为权威主源。500.com 为后备。
> **两种接入方式**: ① SportteryAPI MCP (推荐) ② 直接调竞彩官网 API
> **页面入口**: https://m.sporttery.cn/mjc/jsq/zqspf/

---

## 一、方式 A: SportteryAPI MCP Server (推荐)

> **仓库**: https://github.com/Johnserf-Seed/SportteryAPI
> **优势**: 本地运行无地理封锁, 预计算 noVigProb/fairOdds/Kelly, 含过关计算器

### 部署

```bash
git clone https://github.com/Johnserf-Seed/SportteryAPI.git
cd SportteryAPI
npm install
npm run dev              # 启动本地 HTTP API → http://localhost:8787
```

### 调用方式 (本地 HTTP API)

```
GET  http://localhost:8787/api/matches?pools=had,hhad
     → 返回当日全部竞彩赛事 + SPF(had) + RQSPF(hhad) 赔率
     → 每场含: odds / noVigProb / fairOdds / returnRate / trend

GET  http://localhost:8787/api/match/{matchId}
     → 单场比赛全部玩法池

POST http://localhost:8787/api/value
     Body: {"offered":[竞彩赔率], "reference":[Pinnacle赔率], "labels":["主胜","平","主负"]}
     → 凯利指数 / 价值对比 (竞彩 vs 全球市场)

POST http://localhost:8787/api/parlay
     Body: {"legs":[{odds, deVigProb}], "passType":"3串3", "multiplier":1}
     → 串关 EV / 奖金计算
```

### MCP Server 方式

```
MCP 服务器通过 stdio 协议运行, 暴露 7 个工具:
  get_matches — 获取最新赔率+衍生指标
  get_match   — 单场比赛
  derive_odds — 赔率推导(去水概率/返还率)
  compare_value — 凯利/价值对比
  calc_parlay — 过关奖金计算
  list_parlay_types — M串N参考表
  get_meta — 玩法标签/公式说明

WorkBuddy 中配置 MCP (需 Node.js ≥ 22.6):
  在 ~/.workbuddy/mcp.json 中添加 sporttery-odds 条目
```

---

## 二、方式 B: 直接调竞彩官网 API

```
API 端点: https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry
页面入口: https://m.sporttery.cn/mjc/jsq/zqspf/

⚠️ 限制: 对数据中心 IP 返回 HTTP 567
         从国内本地机器或通过 MCP 本地代理可正常访问

返回: 完整竞彩赛事列表 + SPF/RQSPF/总进球/比分/半全场赔率
      含赔率变动趋势 (trend: up/flat/down)

数据结构:
{
  "matches": [{
    "matchId": 2040239,
    "matchNumStr": "周五029",
    "home": {"abbName": "美国"},
    "away": {"abbName": "澳大利亚"},
    "league": {"abbName": "世界杯"},
    "markets": {
      "had": {                    // SPF 胜平负
        "outcomes": [
          {"key":"home", "odds":1.44, "trend":"down"},
          {"key":"draw", "odds":3.90},
          {"key":"away", "odds":5.60}
        ]
      },
      "hhad": {                   // RQSPF 让球胜平负
        "goalLine": "-1",
        "outcomes": [
          {"key":"home", "odds":2.10},
          {"key":"draw", "odds":3.35},
          {"key":"away", "odds":2.95}
        ]
      }
    }
  }]
}
```

---

## 三、获取流程 (带多重降级)

```
Step 0 竞彩数据获取:

1. 🥇 尝试 SportteryAPI MCP (推荐):
   如果 MCP sporttery-odds 已连接:
     调用 get_matches → 获取完整数据 + noVigProb/fairOdds
     标记 DATA=MCP_SPORTTERY

2. 🥈 尝试 SportteryAPI HTTP (本地 8787):
   如果 MCP 未连接但本地服务在运行:
     WebFetch http://localhost:8787/api/matches?pools=had,hhad
     标记 DATA=LOCAL_SPORTTERY

3. 🥉 尝试竞彩官网 API 直连:
   WebFetch https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry
   → JSON → 标记 DATA=SPORTTERY_CN_API
   → HTTP 567 → ⚠️ 降级到后备源

4. 🏅 后备源 500.com:
   WebFetch https://trade.500.com/jczq/?playid=312&g=2
   提取: SPF 赔率 (竞彩官网赔率, 可能有延迟)
   RQSPF: odds.500.com rangqiu 页 "竞*官*" 行
   标记 DATA=500COM_FALLBACK
```

---

## 四、为什么 SportteryAPI MCP 是最佳方案

```
1. 本地运行 → 无地理封锁, 无 IP 限制
2. 预计算指标: noVigProb / fairOdds / Kelly 开箱即用
3. 内置过关计算: calc_parlay 直接算 3串3/3串4 EV
4. 价值对比: compare_value 对比竞彩 vs Pinnacle 定价偏差
5. 代码开源, 纯数学推导, 可审计
```

---

## 五、数据使用规则

```
竞彩官网 / SportteryAPI 提供的数据用于:
  ✅ SPF 赔率 (had pool)
  ✅ RQSPF 赔率 (hhad pool + goalLine)
  ✅ 竞彩 noVigProb (替代 Pinnacle deVig)
  ✅ 竞彩 fairOdds
  ✅ 竞彩 returnRate / margin
  ✅ 串关 EV 计算 (P_hit × payout − 1)
  ✅ 单关可用性判定
  ✅ 赔率变动趋势 (trend: up/down/flat)

Pinnacle / 百家平均 仅用于:
  ✅ Steps 1-10.5 分析层 (方向/MBI/OCI/陷阱)
  ❌ 不进入 Step 11 投注计算
```
