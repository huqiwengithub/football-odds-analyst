# Football Odds Analyst v3.1.1

专业足彩赔率分析技能，基于 500.com 30 家博彩公司原生数据，执行 13 步标准化分析流程。

## 数据架构

```
500.com (30家+Pinnacle) → 500com-football-scraper → {date}_deep.json → Analyst 13-Step
```

- **数据源**：500.com 深析（每场 6 页：欧指/亚指/让球/大小/数据/投注）
- **依赖**：`500com-football-scraper`（自动安装，零 API 配额限制）
- **缓存**：`.cache/500com/{date}_deep.json`，12 小时有效期

## 13 步分析流程

| # | 步骤 | 说明 |
|:--:|------|------|
| 0 | Data Pipeline | 检查缓存 → 缺失则调用 scraper 拉取 |
| 1 | Data Load | 加载 JSON，队名校验，确认 6 页完整性 |
| 1.5 | Anti-Narrative | 新闻驱动/首秀缺席/平局率筛查 |
| 2 | Fundamentals | H2H/状态/伤停/排名分析 |
| 3a | MBI Consensus | 多机构综合判断（共识/分歧/领先/水位/交易/赔付） |
| 3b | 1X2 Math | Shin 去抽水 + 层级均值 overround |
| 4 | Euro-Asian | 理论盘口 vs 实际盘口 + 21 条陷阱检测 |
| 5 | Opening | 开盘 vs 公允价值，层级对比 |
| 6 | Late Movement | 6h→2h→30min 水位趋势，回调验证 |
| 7 | 6D Scoring | 0-6 分连续综合评分 |
| 8 | Trap Checklist | 49 条陷阱规则并行扫描 |
| 9 | Summary | 方向判定（胜/平/负） |
| 10 | Probability | Logit 12 项校正 → Poisson → Top3 比分 |
| 11 | Portfolio | M串N 容错组合 + 四步动态仓位分配 |
| 12 | Report | HTML 报告输出 |

## 投注体系（v3.1 核心升级）

- **M串N 容错**：3串4 / 4串11 替代自杀式 N串1
- **四步动态仓位决策树**：盈亏平衡反推 → EV 凯利倾斜 → 风险平价上限 → 账户净值调节
- **三不选隔离**：同联赛/同时间/同战意禁止共入一串
- **杠铃赔率结构**：底座 1.50-1.80 + 矛头 2.50-3.50
- **单日限制**：最多 1 组 M串N，严禁追损

## MBI 框架

博彩公司三级分类加权：

| 层级 | 权重 | 代表 |
|:---|:---:|:---|
| Sharp（精明庄家） | 55% | Pinnacle, bet365 |
| Asian（亚洲庄家） | 25% | SBOBet, 188Bet, Macauslot |
| Retail（散户庄家） | 20% | William Hill, 竞彩, Ladbrokes |

核心模块：SCS（共识）/ DRI（分歧）/ Lead-Lag / WaterFlow / Exchange / Kelly

## 知识库（14 模块）

所有分析规则和公式存储于 `references/knowledge-base.md`（KB-0 至 PM），按需引用，保持 SKILL.md 精简。

## 输出

- **中文人话报告**：禁止英文术语，内置强制翻译表
- **HTML 可视化**：MBI 面板 + 6D 雷达 + 比分概率 + 过关方案推演
- 模板：`assets/report-template.html`

## 风控铁律

- 熔断：日亏 3% / 周亏 8% / 模块 7 连错
- 影子测试：A类≥65% + 反向≥70% + EV≥−3% 方可实盘
- 临场禁令：赛前 30 分钟不决策
- 赔付率底线：2串1 竞彩乘积 ≥1.80

## 文件结构

```
football-odds-analyst/
├── SKILL.md                          # 执行引擎（13 步流程 + 组合构建 + 输出规范）
├── README.md                         # 本文件
├── references/
│   ├── knowledge-base.md             # KB-0 到 PM（规则和公式）
│   └── postmortem.md                 # 回测观察和版更记录
└── assets/
    └── report-template.html          # HTML 报告模板
```
