# 竞彩官网数据源协议 v2.0

> **P0 铁律**: 投注赔率以竞彩官网 (sporttery.cn) 为权威主源。500.com 为后备。
>   **优先级反转**: v1.0 时 500.com 为主 → v2.0 竞彩官网为主。
>   原因: 竞彩官网是中国体育彩票唯一官方数据源，500.com 可能有延迟。

---

## 一、主数据源: 竞彩官方 API

```
API 端点: https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry
页面入口: https://m.sporttery.cn/mjc/jsq/zqspf/

返回数据结构 (来自 SportteryAPI 逆向):
{
  "matches": [
    {
      "matchId": 2040239,
      "matchNumStr": "周五029",
      "home": {"abbName": "美国"},
      "away": {"abbName": "澳大利亚"},
      "league": {"abbName": "世界杯"},
      "markets": {
        "had": {                              // SPF 胜平负
          "poolNameZh": "胜平负",
          "outcomes": [
            {"key": "home", "odds": 1.44, "trend": "down"},
            {"key": "draw", "odds": 3.90},
            {"key": "away", "odds": 5.60}
          ]
        },
        "hhad": {                             // RQSPF 让球胜平负
          "poolNameZh": "让球胜平负",
          "goalLine": "-1",                   // 主队让球数
          "outcomes": [
            {"key": "home", "odds": 2.10},
            {"key": "draw", "odds": 3.35},
            {"key": "away", "odds": 2.95}
          ]
        }
      }
    }
  ]
}

⚠️ 限制: 该 API 对数据中心 IP 返回 HTTP 567。
         从国内本地机器或通过代理可正常访问。
```

## 二、获取流程 (带优雅降级)

```
Step 0 竞彩数据获取:

1. 尝试竞彩官方 API (主源):
   WebFetch https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry
   
   → 返回 JSON 数组 → ✅ 主源获取成功
     提取: 每场 matchId / SPF赔率(had) / RQSPF赔率(hhad) / 让球数(goalLine)
     标记: DATA_SOURCE=SPORTTERY_CN
   
   → 返回 HTTP 567 (被拦截) → ⚠️ 主源不可用, 降级到后备源

2. 后备源: 500.com (主源不可用时):
   WebFetch https://trade.500.com/jczq/?playid=312&g=2
   提取: SPF 赔率 (该页为竞彩官方赔率)
   
   对每场:
     RQSPF: 从 rangqiu 页 "竞*官*" 行提取
     标记: DATA_SOURCE=FALLBACK_500COM

3. 交叉验证 (两者均可用时):
   对每场同时有竞彩官网和 500.com 赔率的比赛:
     对比 SPF 主胜赔率差异
     差异 > 3% → ⚠️ 标记 CROSSCHECK_WARN, 以竞彩官网为准
     差异 ≤ 3% → ✅ 标记 CROSSCHECK_OK

4. 报告中的数据来源声明:
   "[数据来源: 竞彩官网 sporttery.cn]" 或
   "[数据来源: 500.com (竞彩官网不可用)]" 或
   "[数据来源: 竞彩官网, 500.com 交叉验证通过]"
```

## 三、竞彩官网数据的关键指标

```
从竞彩官方赔率直接推导:

  noVigProb (竞彩去水概率):
    had 池: noVigProb_i = (1/odds_i) / (1/h + 1/d + 1/a)
    这反映的是中国竞彩市场对该方向的实际定价

  returnRate (竞彩返还率):
    单关: 1 / (1/h + 1/d + 1/a)
    典型值: 88-89% (SPF), 略低 (让球)
    
  EV (基于竞彩去水):
    EV_single = noVigProb × odds − 1
    EV_parlay = ∏ noVigProb_i × ∏ odds_i − 1

  goalLine (让球数, 来自 hhad 池):
    正数 = 主队让球, 负数 = 客队让球
    用于判定让球深度和穿盘风险
```

## 四、为什么竞彩官网为主

```
1. 权威性: 中国体育彩票唯一官方数据源
2. 实时性: 赔率变动实时更新
3. 完整性: 含 SPF + RQSPF + 比分 + 总进球 + 半全场全部玩法
4. 一致性: EV 计算使用竞彩市场自身定价，不需 Pinnacle 换算
5. 可用性: SPF 是否开售 / RQSPF 让球数 一目了然

500.com 的问题:
  1. 赔率可能是几分钟前的快照，赛前关键时段延迟影响大
  2. rangqiu 页 "竞*官*" 行需要手动解析，易出错
  3. 不会标注 SPF 为何未开售（深盘? 未开? 已停?）
```

## 五、数据源优先级 (v2.0 反转)

```
竞彩 SPF 赔率获取:
  1. webapi.sporttery.cn API                ← 🥇 主源, 实时官方
  2. trade.500.com/jczq/?playid=312&g=2     ← 🥈 后备, 可能有延迟

竞彩 RQSPF 赔率获取:
  1. webapi.sporttery.cn API (hhad pool)    ← 🥇 主源, 含让球数+实时赔率
  2. odds.500.com rangqiu页 "竞*官*"行      ← 🥈 后备, 需手动解析

单关可用性:
  1. webapi.sporttery.cn API (如含单关标记) ← 🥇
  2. trade.500.com/jczq/?playid=312&g=1     ← 🥈
```
