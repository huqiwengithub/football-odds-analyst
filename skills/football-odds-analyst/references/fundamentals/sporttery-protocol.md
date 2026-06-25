# 竞彩官网数据源协议 v1.0

> **定位**: 中国体育彩票官方赔率数据源。作为 500.com 竞彩数据的交叉验证源。
> **优先级**: 500.com 为主（可用），竞彩官网为辅（验证用）。

---

## 一、数据源

### 主源: 竞彩官方 API

```
API 端点: https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry
说明: 竞彩官网 m.sporttery.cn 计算器页面使用的未公开公共 API
返回: 完整竞彩赛事列表 + SPF/RQSPF/总进球/比分/半全场赔率

⚠️ 限制: 该 API 对数据中心 IP 返回 HTTP 567（地理封锁）。
         从本地机器（非数据中心 IP）可能可访问。
```

### 开源封装: SportteryAPI

```
仓库: https://github.com/Johnserf-Seed/SportteryAPI
说明: Cloudflare Worker REST API + 本地 MCP Server
功能: 
  - 自动去水概率计算 (noVigProb)
  - 返还率/抽水比例
  - 公平赔率推算
  - Kelly/价值指标

本地 MCP Server 部署:
  git clone https://github.com/Johnserf-Seed/SportteryAPI
  cd SportteryAPI
  npm install && npm run mcp:local
  → MCP Server 运行在本地，可直接从竞彩官网获取数据
```

### 后备: 500.com 竞彩数据 (当前在用)

```
SPF 赔率:  trade.500.com/jczq/?playid=312&g=2
RQSPF 赔率: odds.500.com/fenxi/rangqiu-{match_id}.shtml → "竞*官*"行
单关标记:  trade.500.com/jczq/?playid=312&g=1

⚠️ 500.com 显示的是竞彩官方赔率，但可能有几分钟延迟。
   赛前关键时段以竞彩官网为最终权威。
```

---

## 二、数据对比验证

```
每次分析时执行 (Step 0a 阶段):

1. 从 500.com 获取竞彩 SPF 赔率 (主源, 已实现)
2. 从 500.com 获取竞彩 RQSPF 赔率 (rangqiu页"竞*官*"行, 已实现)
3. (可选) 如果 SportteryAPI MCP 可用:
     对比 500.com 赔率 vs 竞彩官网赔率
     差异 > 3% → 标红警告, 以竞彩官网为准
4. 无 MCP 时: 使用 500.com 数据 + 在报告中注明数据来源
```

---

## 三、SportteryAPI 提供的关键指标

```
从竞彩官方赔率直接推导 (比 Pinnacle deVig 更适合竞彩 EV 计算):

  noVigProb: 竞彩市场的去水真实概率
    计算: (1/odds_i) / Σ(1/odds_j) — 从竞彩赔率自身推导
    优势: 反映的是中国竞彩市场对比赛的真实定价
    
  fairOdds: 竞彩公平赔率
    计算: 1/noVigProb
    
  returnRate (返还率):
    计算: 1 / Σ(1/odds_i)
    竞彩 SPF 返还率通常 ~88-89%
    串关返还率 = 单关返还率^关数 (1关: 0.88, 2关: 0.78, 3关: 0.69)

  margin (抽水):
    计算: 1 − returnRate
    竞彩单关抽水 ~11-12%，远高于 Pinnacle 的 ~2%
```

---

## 四、EV 计算使用竞彩 noVigProb

```
当前做法 (KB-13.8b):
  竞彩 EV = Pinnacle_deVigProb × 竞彩赔率 × 串关返奖率 − 1

问题: Pinnacle 全球市场概率 ≠ 竞彩中国市场概率
      两者之差可能高达 3-5%，导致 EV 系统性偏差

优化方案 (如果 SportteryAPI 可用):
  竞彩 EV = 竞彩_noVigProb × 竞彩赔率 − 1
  串关 EV = ∏ 竞彩_noVigProb_i × ∏ 竞彩赔率_i − 1

后备方案 (当前):
  竞彩 EV = (1/竞彩赔率) / Σ(1/竞彩赔率_j) × 竞彩赔率 − 1
  = 竞彩自身隐含去水概率 × 竞彩赔率 − 1
  完全在竞彩市场内自洽，无需 Pinnacle 介入
```

---

## 五、数据源优先级

```
竞彩 SPF 赔率获取:
  1. SportteryAPI MCP (如果已部署) ← 最准, 实时
  2. trade.500.com/jczq/?playid=312&g=2 ← 可用, 可能有延迟
  3. WebSearch 竞彩官网截图 ← 最后手段

竞彩 RQSPF 赔率获取:
  1. SportteryAPI MCP (hhad pool) ← 最准
  2. odds.500.com/fenxi/rangqiu-{id}.shtml "竞*官*"行 ← 当前可用
  3. WebSearch 竞彩官网让球页面 ← 最后手段
```
