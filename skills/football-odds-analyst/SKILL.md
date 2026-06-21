---
name: football-odds-analyst
description: "Football odds analyst v3.0.3-final — MBI multi-bookmaker intelligence. Auto-pipeline with 500com-football-scraper. 500.com 30-bookmaker native data. Trigger: analyze match, odds analysis, handicap analysis, 竞彩."
allowed-tools: Read, Write, Bash, WebSearch, WebFetch
agent_created: true
version: "3.0.3-final"
released: 2026-06-21
references: references/knowledge-base.md
dependencies:
  - name: 500com-football-scraper
    required: true
    install_from: marketplace
    description: "500.com deep data scraper — provides per-match 6-page deep analysis JSON"
---

# Football Odds Analyst v3.0.3-final

> **执行引擎**。所有分析规则和公式在 `references/knowledge-base.md`（KB-0 到 KB-13）。
> 每次分析先读 KB-2 + KB-4，再按本文件的步骤顺序执行。

---

## 🔌 Step 0: Data Pipeline

```
1. 检查工作目录 {date}_deep.json 是否存在（<12h）
2. 不存在 → 检查 500com-football-scraper 技能 → 未安装则自动安装 → 调用拉取数据
3. 数据就绪 → 加载 JSON → 进入 Step 1
```

所需字段：`ouzhi`（pinnacle + all_bookmakers + dispersion）、`yazhi`、`shuju`、`touzhu`、`basic`。

---

## 13-Step Checklist

| # | Step | 一句话 | 读哪个 KB |
|:--:|------|--------|:---:|
| 0 | Pipeline | 检查数据，缺失则调 scraper | — |
| 1 | Data Load | 加载 JSON，队名校验，确认 6 页全 | KB-0 |
| 1.5 | Anti-Narrative | 已知新闻驱动？首秀/缺席？平局>27%？ | KB-5 |
| 2 | Fundamentals | H2H/状态/伤停/排名，权重 v2.0 | KB-5, KB-11 |
| 3a | MBI Consensus | SCS + DRI + Lead-Lag + WaterFlow + Exchange + Kelly → MBI 面板 | **KB-10** |
| 3b | 1X2 Math | Shin de-vig + 层级均值 overround | KB-1 |
| 4 | Euro-Asian | 理论 AH vs 实际 AH，15+6 条陷阱 | KB-2, KB-10 |
| 5 | Opening | 开盘 vs 公允价值，层级对比 | KB-5 |
| 6 | Late Movement | 6h→2h→30min，水位趋势，回调验证 | KB-7, KB-12 |
| 7 | 6D Scoring | 连续 0-6 分，维度合并去重叠 | KB-4 |
| 8 | Trap Checklist | 21 陷阱 + 28 通用 = 49 规则。≥2→🔴。≥3→systemic | KB-2, KB-3, KB-10 |
| 9 | Summary | 方向判定。红=胜/琥珀=平/绿=负。结论置顶 | — |
| 10 | Probability | Logit 空间 12 项校正 → 归一化 → Poisson → Top3 比分 | KB-6, KB-7 |
| 11 | Portfolio | 分数 Kelly + 串关防御 + 风险日检查 | KB-13 |
| 12 | Report | HTML 输出：MBI 面板 + 6D + 比分 + 过关方案 + 免责 | 本文件 |

---

## Output Format — 人话输出

**核心原则：给用户看的报告不允许出现任何英文缩写和专业术语。** 内部计算保留术语，输出时必须翻译。

### 术语翻译表（强制使用）

| 内部用 | 输出给用户 |
|:---|:---|
| SCS / Sharp Consensus | 机构共识度 |
| DRI / Dispersion Risk | 分歧风险 |
| Lead-Lag | 谁先动谁跟风 |
| Water Flow | 水位走向 |
| Exchange / VWAP | 真实成交量 |
| Kelly | 庄家赔付压力 |
| logit 校正 | 概率调整 |
| Shin de-vig | 去掉庄家抽水 |
| Poisson | 进球可能性 |
| 6D Score | 综合评分 |
| MBI | 多机构综合判断 |
| Fractional Kelly | 合理下注比例 |
| Circuit Breaker | 止损线 |
| P(全灭) | 血本无归的概率 |
| EV | 预期收益 |
| AH / Asian Handicap | 让球盘 |
| OU / Over-Under | 大小球 |
| SPF / 1X2 | 胜平负 |
| Overround | 庄家抽水比例 |
| Trap #N | 陷阱信号 N |
| Tier Divergence | 大机构和小机构看法打架 |
| Resistance Wall | 抛压墙（大单压盘） |

### 输出结构

```
## 今日总览
[一句话总结：几场看好主队，几场看好客队，整体风险高/中/低]

## 每场比赛
### 编号 | 队名 vs 队名 | 时间
> 胜负方向：主胜/平局/客胜（把握：高/中/低）
> 推荐比分：X:X（可能性 Y%）/ X:X（可能性 Z%）
> 让球方向：穿盘/不穿盘
> 大小球：大球/小球

基本面简述：
  [2-3句，不用术语。例："西班牙排名比沙特高59位，最近10场6胜4平没输过。沙特近10场只赢2场。"]

机构怎么看：
  [用人话翻译 MBI 面板。例：
  "30家机构里绝大多数都看好西班牙赢（共识度高）。
   各家看法比较一致，没有明显打架（分歧风险低）。
   平博最先调低西班牙赔率，其他机构陆续跟进（真实信号）。
   水位整体往西班牙方向流（资金看好）。
   庄家在西班牙赢球上的赔付控制很紧（真心看好）。"]

要注意的风险：
  [列出触发的陷阱信号，用人话解释。例：
  "这场赔率实在太低了（赢球才1.1倍），属于'赢了不赚、输了血亏'的类型，做串关核心胆的话万一翻车就全完了。"]

### 综合评分：X/6
[各项得分简述]

### 竞彩建议
- 保守方案：XX串XX，预期收益约X倍，血本无归概率X%
- 进取方案：...
- 对冲方案：...（如有）

## 风险提示
[熔断检查 / 风险日级别 / 仓位建议]
```

### 禁用词清单

输出给用户的报告里，以下词汇绝对不能出现：
❌ SCS、DRI、Lead-Lag、Water Flow、Kelly、VWAP、logit、de-vig、Poisson、MBI、Fractional Kelly、Circuit Breaker、Pinnacle、bet365、AH、OU、SPF、Overround、Shin、Trap #N、Tier Diverge
✅ 机构共识、分歧风险、谁先动、水位、庄家赔付、成交均价、概率调整、去抽水、进球可能、多机构判断、合理下注、止损、平博、让球盘、大小球、胜平负、庄家抽水、陷阱信号、看法打架

---

## Knowledge Base Index (13 modules)

| KB | 内容 | 何时读 |
|:---:|------|:---:|
| 0 | 队名校验协议 | Step 1 |
| 1 | Shin de-vig + logit 校正 + 欧亚转换 | Step 3b |
| 2 | 15 条欧亚陷阱 | Step 4 |
| 3 | 28 条通用陷阱规则 | Step 8 |
| 4 | 6D 连续评分 | Step 7 |
| 5 | 基本面权重 + 压缩等级 + 背水一战 | Steps 2, 5 |
| 6 | 概率合成 (12 校正) | Step 10 |
| 7 | 比分精炼 (14.0–14.11) | Step 10 |
| 8 | 方法补充 (Kelly, AH, OU) | 辅助 |
| 9 | 复盘 (28 场周期) | 回顾 |
| **10** | **MBI 框架: SCS, DRI, Lead-Lag, WaterFlow, Exchange, Kelly, 陷阱 #16-#21** | **Steps 3a, 4, 8** |
| **11** | **数据校准: 机构去重, 水位归一化, 真实初盘, 三档赛事参数** | **Pre-Step 1** |
| **12** | **高级信号: 回调验证, AH真假突破, 阻力墙, 初受盘差, 平局分流** | **Steps 4, 6** |
| **13** | **风控+铁律: 动态滑点, 置信分级, 熔断, 风险日, 影子测试, 黑名单** | **Step 11 + Always** |

---

## Boundaries & Iron Rules

- 教育用途。数据源：500.com（30 家，零配额）。xG 为市场隐含。
- **铁律**: 临场 30min 禁令 ❌ 倍投 ❌ 对冲 ❌ 串关几何平均 <1.50
- **熔断**: 日亏 3%→停 / 周亏 8%→影子测试 / 模块 7 连错→禁用
- **影子测试**: A类≥65% + 反向≥70% + EV≥−3% 方可实盘
