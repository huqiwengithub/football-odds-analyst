---
name: football-odds-analyst
description: "Football odds analyst v3.0 — MBI multi-bookmaker intelligence with 500.com 30-bookmaker deep data pipeline. Two-skill architecture (scraper + analyst). Auto-dependency resolution."
version: "3.0"
released: 2026-06-21
---

# Football Odds Analyst v3.0 — Project Root

> **主技能**: `skills/football-odds-analyst/SKILL.md`（分析引擎 v3.0）
> **数据管道**: `skills/500com-football-scraper/SKILL.md`（数据爬虫 v2.0）
> **知识库**: `skills/football-odds-analyst/references/knowledge-base.md`（KB-0 到 KB-10）

## 架构

```
用户 → football-odds-analyst (v3.0)
         ├─ Step 0: 检查数据 → 缺失时自动调用
         └─ 500com-football-scraper (v2.0)
              └─ 每场 6 个深度分析页 → JSON 输出
```

## 安装

1. 在 WorkBuddy 市场中安装 `football-odds-analyst`
2. `500com-football-scraper` 会在首次运行时自动安装
3. 说一句「分析 6 月 22 日世界杯」即可

## 分析报告示例

- `世界杯_2026-06-22_分析报告.html` — 本日完整分析（含 MBI、6D 评分、Poisson 比分、竞彩混合过关）
- `世界杯_2026-06-22_赔率数据.html` — 原始赔率数据展示
- `世界杯_2026-06-22_赔率数据.json` — 结构化原始数据
