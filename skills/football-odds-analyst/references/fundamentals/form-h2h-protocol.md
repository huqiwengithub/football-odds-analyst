# 近期形态 + 交锋历史 获取协议 v1.0

> **定位**: 填补基本面 B 类(近期形态) + C 类(交锋历史)的数据管道空缺。
> **数据源**: 500.com 每场比赛的 shuju 分析页，无需新增抓取源。
> **URL**: `https://odds.500.com/fenxi/shuju-{shuju_id}.shtml` (scraper 已抓取此页)

---

## 一、数据提取

### 1.1 近期形态 (Recent Form)

```
WebFetch https://odds.500.com/fenxi/shuju-{shuju_id}.shtml

从"近期战绩"区块提取两队数据:

主队:
  total_10: 近10场战绩 X胜X平X负进X球失X球
  home_10:  近10场主场战绩 X胜X平X负进X球失X球
  away_10:  近10场客场战绩 X胜X平X负进X球失X球
  last_5:   [最近5场结果列表: 日期/对手/比分/主客场/赛事]

客队:
  total_10 / home_10 / away_10 / last_5 (同上)

输出结构化字段:
{
  "home_form": {
    "total":   {"P": 10, "W": 3, "D": 6, "L": 1, "GF": 11, "GA": 6},
    "home":    {"P": 10, "W": 7, "D": 3, "L": 0, "GF": 15, "GA": 2},
    "away":    {"P": 10, "W": 1, "D": 5, "L": 4, "GF": 4,  "GA": 9},
    "last_5":  ["D0-0(vs库拉索,H)", "L0-1(vs科特迪瓦,A)", "W3-0(vs危地马拉,H)", "W2-1(vs沙特,H)", "D1-1(vs荷兰,A)"]
  },
  "away_form": { ... }
}
```

### 1.2 交锋历史 (H2H)

```
从"交战历史"区块提取:

双方近N次交战: X胜 X平 X负, 进X球, 失X球

历史交锋记录列表 (每场):
  日期 / 赛事 / 主队 vs 客队 / 比分 / 半场

输出结构化字段:
{
  "h2h": {
    "total_matches": 2,
    "home_wins": 0, "draws": 0, "away_wins": 2,
    "home_goals": 2, "away_goals": 7,
    "last_meeting": {
      "date": "2013-05-30",
      "competition": "友谊赛",
      "home_team": "厄瓜多尔",
      "away_team": "德国",
      "score": "2:4",
      "result": "客胜"
    },
    "recent_5": [
      {"date": "2013-05-30", "home": "厄瓜多尔", "away": "德国", "score": "2:4", "result": "客胜"},
      {"date": "2006-06-20", "home": "德国", "away": "厄瓜多尔", "score": "3:0", "result": "主胜"}
    ]
  }
}
```

---

## 二、量化指标计算

### 2.1 形态趋势分 (Form Score)

```
form_score = (W×3 + D×1) / (P×3)  // 近10场得分率, 区间 [0,1]

主客场分拆:
  home_form_score = home_W×3 + home_D×1 / (home_P×3)
  away_form_score = away_W×3 + away_D×1 / (away_P×3)

形态方向判定:
  form_score ≥ 0.70 → 🔥 强势
  form_score 0.40-0.70 → ➡️ 一般
  form_score < 0.40 → ⚠️ 低迷

主客场落差:
  |home_form_score − away_form_score| > 0.30 → 主客场分裂 (主场龙/客场虫)
```

### 2.2 H2H 压制分 (H2H Score)

```
时效窗口:
  最近5年内 (≥2021) → 权重 1.0
  5-10年前 (2016-2020) → 权重 0.5
  10年以上 → 权重 0.2 (纯参考, 不参与判定)

h2h_score (对主队):
  时效期内: win_score = (W + 0.5×D) / P  // 归一化到 [0,1]
  如果无时效期内交锋 → h2h_score = null (无参考价值)

h2h 方向 (对主队):
  h2h_score ≥ 0.60 → 主队历史占优
  h2h_score 0.40-0.60 → 均势
  h2h_score < 0.40 → 客队历史占优
  h2h_score = null → 无有效参考
```

### 2.3 形态×实力交互

```
交互信号:
  形态逆势: form_score < 0.40 但 ELO 领先 > 100
    → 强队近期低迷, 谨慎 (仓位降 0.5x)
  
  形态悖论: form_score > 0.70 但 ELO 落后 > 100
    → 弱队近期爆种, 可能是短期峰值 (仓位降 0.5x)
  
  形态共振: form_score > 0.70 且 ELO 领先 > 100
    → 强队状态+实力双优 (不加不减, 默认仓位)
```

---

## 三、整合流程

```
Step 0a 执行时 (在积分榜获取后):

3. 获取形态+H2H数据:
   对每场候选比赛:
     WebFetch https://odds.500.com/fenxi/shuju-{shuju_id}.shtml
     提取:
       a. 近期形态 (tables: recent_form_total, home_form, away_form)
       b. 交锋历史 (table: h2h_history)
       c. 预计阵容 (optional: expected_lineup, 有伤病标注)

4. 结构化输出 → 传入 Step 2
```

---

## 四、Step 2 输出格式更新

```
[场次] 基本面量化:
  ELO差: [+XXX]  → 预期净胜球: [X.X], 冷门概率: [XX%]
  实力档: [S/A/B/C/D/E] vs [S/A/B/C/D/E]
  
  近期形态:
    主队: 近10场 [XW-XD-XL], GF[X] GA[X], 形态分: [X.XX]
          主场 [XW-XD-XL], 客场 [XW-XD-XL]
          状态: [强势/一般/低迷], 主客分裂: [有/无]
    客队: (同上)
  
  交锋历史:
    近[X]次交锋: 主[X]胜 [X]平 客[X]胜
    时效性: [有效(<5年)/降权(5-10年)/过旧(>10年)]
    H2H方向: [主队占优/均势/客队占优/无参考]
  
  伤病: [X人核心缺阵] → logit [-0.XX]
  赛程: 休息[X]天, 下一场[X]天后 → 体能: [充分/一般/紧张]
  形势: [生死战/无关紧要/正常], mot: [X.XX]
  
  基本面倾向: [方向], 量化强度: [高/中/低]
    (强度规则: ELO差≥100+无核心缺阵+form_score≥0.50→高 
              ELO差50-99或form_score=0.30-0.49→中 
              ELO差<50或form_score<0.30→低)

  特殊标记: [形态逆势] [形态悖论] [形态共振] [主客分裂]
```
