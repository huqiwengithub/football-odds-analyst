# Knowledge Base Reference — Football Odds Analyst v3.9.0: Pin分箱准确率+死亡区间屏蔽

> **Load trigger**: Read this file when SKILL.md instructs you to reference a specific section ($KB-N). Contains all detailed rules, formulas, trap definitions, scoring criteria, and methodology.
>
> **Reading strategy**: Start with KB-16 (Pin分箱准确率) + KB-17 (平局+动机修正) — v3.9.0核心. Then KB-6 + KB-7 for Step 10. KB-2 + KB-4 for traps/scoring. KB-10 for MBI.
>
> **赛前对照检查**: 赛后回测复盘统一使用 `football-backtest-workflow/` 子技能（详见 SKILL.md Step 13）。赛前无需手动检查观察项。

---

## KB-0: Pre-Flight — Team Names + Verification

### Team Name Verification Protocol
```
1. For each team from fixtures: check static map → FOUND? ✅
2. NOT found → WebSearch "[Team] Chinese name football national team"
3. STILL not found → use English + ⚠️ red marker in output
4. World Cup: ALWAYS WebSearch "2026 World Cup teams Chinese name list"
5. If ANY fallback used → set {{NAME_ERROR_ACTIVE}} = active in HTML report
```

### Static Chinese Name Map
```
Switzerland=瑞士, Korea Republic=韩国, Bosnia and Herzegovina=波黑, Japan=日本,
Czechia=捷克, South Africa=南非, Canada=加拿大, Qatar=卡塔尔, Mexico=墨西哥,
Brazil=巴西, Argentina=阿根廷, France=法国, Germany=德国, England=英格兰,
Spain=西班牙, Portugal=葡萄牙, Italy=意大利, Netherlands=荷兰, Croatia=克罗地亚,
Uruguay=乌拉圭, Belgium=比利时, Colombia=哥伦比亚, USA=美国, Morocco=摩洛哥,
Australia=澳大利亚, Iran=伊朗, New Zealand=新西兰, Sweden=瑞典, Ivory Coast=科特迪瓦,
Ecuador=厄瓜多尔, Curacao=库拉索, Tunisia=突尼斯, Denmark=丹麦, Norway=挪威,
Poland=波兰, Senegal=塞内加尔, Egypt=埃及, Nigeria=尼日利亚, Ghana=加纳,
Costa Rica=哥斯达黎加, Panama=巴拿马, Jamaica=牙买加, Serbia=塞尔维亚,
Austria=奥地利, Ukraine=乌克兰, Turkey=土耳其, Greece=希腊, Scotland=苏格兰
```

---

## KB-1: Core Math & Conversion

### De-vig Methods

Use Shin de-vigging algorithm. Simple proportional method systematically overestimates favorite probabilities (favorite-longshot bias widens as odds gap grows).

```
Shin's method:
  Minimize |Σ(1 / (z + (1-z) × odds_i)) − 1| over z ∈ [0, 1)
  where z = proportion of insider trading in market (Shin parameter)
  
  De-vigged prob_i = (1 − z) / (odds_i − z × odds_i + z)

Practical approximation (sufficient for most matches):
  z ≈ max(0, (overround_simple − 1) / 2)
  Then: prob_i = (1 − z) / ((1 − z) × odds_i + z)
```

**Fallback**: If Shin computation not feasible, use proportional method with bias correction:
```
proportional_prob = (1/odds) / overround
bias_correction = −(proportional_prob − 0.33) × 0.05  // −5% for heavy fav, +5% for underdog
corrected = proportional_prob + bias_correction
```

### Logit-space Correction

Apply all corrections in logit space (not probability space):

```
Step 1: De-vig → base probability P
Step 2: Convert to logit space
  logit(P) = ln(P / (1 − P))
  
Step 3: Apply all corrections in logit space
  logit' = logit + Σ(Δlogit_i)
  where Δlogit_i is the logit offset for each correction factor

Step 4: Convert back to probability
  P' = 1 / (1 + e^(−logit'))

Step 5: Normalize across H/D/A
  P_final[i] = P'[i] / Σ(P')
```

| Logit Δ | Corresponding Probability Shift (centered at 50%) | Typical Signal |
|:---:|:---|:---|
| +0.10 | +2.5pp | Weak positive signal |
| +0.20 | +5.0pp | Medium positive signal |
| +0.40 | +10.0pp | Strong positive signal |
| +0.70 | +17.0pp | Extremely strong positive (multi-confirmation only) |

**logit space advantages**: Probabilities are naturally bounded (0,1), equivalent to Bayesian updating, correction magnitude auto-compresses near extreme probabilities.

### Fundamental formulas
```
Overround (vig) = 1/home_price + 1/draw_price + 1/away_price
Payout rate = 1 / overround

Dampening for correlated factors:
  if factor_A and factor_B are in same signal group:
    combined = max(Δ_A, Δ_B) + 0.3 × min(Δ_A, Δ_B)
```

### Euro→Asian Conversion Table
```
Pinnacle 1X2 home → AH line:
  1.38–1.48 → -1.00 to -1.50    1.48–1.58 → -0.75 to -1.00
  1.58–1.72 → -0.50 to -0.75    1.72–1.90 → -0.25 to -0.50
  1.90–2.10 →  0.00 to -0.25    2.10–2.40 → +0.00 to +0.25
  2.40–2.80 → +0.25 to +0.50    2.80–3.30 → +0.50 to +0.75
  3.30–4.00 → +0.75 to +1.00    4.00–5.00 → +1.00 to +1.50
Formula: theoretical_ah = (deVigProb_home − 0.50) × 4
```

---

## KB-2: Fifteen Euro-Asian Divergence Traps

> A/B/C三层分类：C=信息型 / B=诱导型 / A=仓位型。分类加权判定替代原计数阈值。

| # | Pattern | Category | Trigger | Risk |
|:--:|---------|:--------:|---------|------|
| 1 | Deep odds, shallow handicap | **C** | Gap ≥0.25 ball, theoretical AH deeper than actual | Draw/away upset |
| 2 | Shallow odds, deep handicap | **C** | Gap ≥0.25 ball, actual deeper than theoretical + SBOBet water >1.00 | Straight outcome |
| 3 | Draw odds dropping + deep handicap | **C** | Draw odds ↓ ≥8% from open + AH ≥0.25 deeper than theoretical | Hidden draw |
| 4 | Late odds drop + handicap retreat | **B** | Home odds ↓ ≥5% in last 6h + AH retreats ≥0.25 (opposite direction) | Fake news / 庄家反向诱导 |
| 5 | Favorite deep handicap + water >1.05 | **A** | AH ≥0.75 ball + SBOBet water ≥1.05 at close | 仓位压力, passive |
| 6 | Underdog drops for no reason | **C** | Underdog odds ↓ ≥10% + ZERO fundamental support (WebSearch verified) | Minimal reference value |
| 7 | Narrative-driven moderate compression | **B** | Compression 5–15% + draw true prob >25% + driver is "known news" | 庄家借叙事钓鱼 |
| 8 | Same-direction compression + AH static | **A** | Home odds ↓ ≥5% + AH unchanged | 仓位型，被动调价 |
| 9 | Opposite-direction odds vs AH | **C** | 1X2 moves one way, AH opposite | Strong trap |
| 10 | SBOBet diverges from Pinnacle | **C** | SBOBet AH deviates ≥0.25 from Pinnacle | Asian sharp disagrees |
| 11 | bet365 limit crash | **A** | bet365 limit drops >30% in 2h, odds unchanged | Risk aversion (仓位管理) |
| 12 | Opening line extreme | **B** | Opening AH ≥1.5 balls | 庄家刻意制造"危险"假象 |
| 13 | Illegal betting site manipulation 🚩 | **C** | Unregulated bookmaker >0.15 from Pinnacle + limit drops >50% + market suspended (≥2 signs) | RED FLAG — skip |
| 14 | Three-bookmaker consensus break | **C** | All 3 diverge ≥0.25 on same market | Systemic uncertainty |
| 15 | Referee-driven odds shift | **C** | Referee >0.35 penalties/game or >5.0 cards/game + physical team | Adjust OU ±0.25 |

### 分类加权规则

```
C 类陷阱（信息型 — 赔率方向与基本面不一致）:
  每条触发 → logit ±0.25（方向与陷阱指示相反）
  多条 C 类共振 → 信度 × 0.70，标记为 🔴 高严重度

B 类陷阱（诱导型 — 庄家刻意制造"危险信号"）:
  每条触发 → 不降信度，但标记为 ⚠️ 疑似诱导
  需成交量交叉验证: 无量配合 → 确认为诱导 → logit +0.15（强化原方向）
                   有量配合 → 转为 C 类处理
  多条 B 类共振且无量 → logit +0.25（庄家在反向操作）

A 类陷阱（仓位型 — 被动调价，与基本面无关）:
  每条触发 → 不产生 logit 修正
  仅作为上下文标注: "此变动为仓位驱动，非信息信号"
```

Each HIT → Category-based correction (see above).

---

## KB-3: Twenty-Eight Universal Trap Rules

> A/B/C分类加权规则同 KB-2。

```
[C]  1: Odds drop ≥8% without fundamentals → trap
[A]  2: Deep open (AH ≥1.0) + never retreat in 24h → true signal (仓位型，市场坚定)
[C]  3: Opening shallow (gap ≥0.25) + paper strength clear → upset warning
[A]  4: Same-direction multi-bookmaker → weight ×1.5 (仓位共振≠信息共振)
[A]  5: Pinnacle leads movement (>5 min ahead of others) → real signal (需量确认是否为仓位驱动)
[A]  6: Random single-bookmaker deviation ≥0.10 → ignore
[B]  7: Late odds + AH both reverse in last 2h → trap (庄家反向操作)
[B]  8: Odds ↓ ≥5% + AH retreats ≥0.25 → trap (诱导型)
[C]  9: bet365 moves opposite Pinnacle → retail-sharp conflict
[A] 10: Odds static (σ<0.03) + water volatile (σ>0.08) → indecision (仓位拉锯)
[B] 11: Narrative compression 5–15% → market overreacting (诱导型，借叙事)
[C] 12: Suspension paradox → suspended teams play MORE defensive
[C] 13: Illegal betting site — match 2+ red flags → SKIP (see KB-2 Trap #13)
[C] 14: Referee influence → adjust expectations (see KB-2 Trap #15)
[A] 15: No fundamental event → movement is noise
[C] 16: 1X2 odds drop → verify AH direction match
[C] 17: Three-bookmaker consensus strong (≤0.15 ball) → high confidence
[C] 18: deVigProb(home) >75% → unusual; check narrative
[C] 19: deVigProb(draw) >30% → market uncertain; expect draw risk
[C] 20: deVigProb(away) >40% → strong away signal; verify AH
[B] 21: Extreme compression >15% → overreaction (庄家造势)
[C] 22: 1X2 spread across 3 bookmakers >0.30 → uncertainty penalty
[C] 23: AH spread across 3 bookmakers >0.50 → high divergence
[C] 24: Both teams WC debut → draw prob floor 28%
[A] 25: Same-direction water rise >0.15 on all 3 → genuine flow (仓位型)
[C] 26: Favorite odds <1.25 → lay risk; max confidence 80%
[C] 27: Defensive fortress (qualifying GA<0.5 or 5+ clean sheets) → +3% direction, +15% under
[C] 28: Heat discount (>35°C or humidity >80%) → fade favorite; underdog +5% prob
```

---

## KB-4: Six-Dimension Scoring (0–1 Continuous)

> Binary→连续评分，重叠维度(D2/D6)合并，满分惩罚→权重重新校准。

### Scoring Dimensions

| Dim | Criterion | Score 0.0 (worst) | Score 1.0 (best) | Interpolation |
|:---:|-----------|-------------------|-------------------|:---|
| **D1** | Fundamental logic | Fundamentals contradict market | Perfect alignment: injuries/form/H2H all agree | Linear by # of aligned sub-factors ÷ total |
| **D2** | Market consensus (MERGE old D2+D6) | AH gap >0.50 OR DRI >60 OR >2 books diverge | AH gap ≤0.15 AND DRI <20 AND all books within 0.10 spread | 1 − (gap/0.50 + DRI_norm/2 + spread_norm)/3 |
| **D3** | Opening objectivity | Opening ≥0.50 ball from fair value OR compressed by "known news" | Opening within 0.15 ball of fair value AND no narrative compression | 1 − deviation/0.50 |
| **D4** | Late movement clean | ≥3 traps triggered OR harvest pattern detected | 0 traps + late 1h passes authenticity rules | 1 − traps_hit/4 |
| **D5** | Water & draw logic | Water σ >0.08 OR draw prob >30% with fav<2.00 | Water σ<0.04 AND draw prob≤22% AND water changes explainable | mean of (1−σ/0.08, 1−draw/0.30) |
| — | ~~D6 removed~~ | Merged into D2. Old D6 measured "no one-sided hype" = same as consensus | — | — |

### Continuous Score Formula

```
Per dimension:
  score_i = clamp(mapped_value, 0.0, 1.0)

Total = Σ(score_i × weight_i) / Σ(weight_i)

Default weights :
  D1: 0.25  D2: 0.25  D3: 0.15  D4: 0.15  D5: 0.20
  (Total = 5 dimensions, no D6)

Final 6D Score = Total × 6  (scale to traditional 0-6 range for legacy compatibility)
```

### Application

```
6D ≥ 4.5 (legacy scale) → direction confidence +3%
6D 3.0–4.5 → no adjustment
6D 2.0–3.0 → confidence −3%, ⚠️ low confidence warning
6D < 2.0 → skip match entirely (auto-degrade)
```

### Inflation Penalty (已替换)

**Old rule** (6/6→5) has been removed. That phenomenon indicates model calibration bias, not "perfect score is untrustworthy." Resolution:
- Recalibrate dimension weights via historical backtest
- If a dimension negatively correlates with outcome → flip or delete that dimension
- Pending 500+ match backtest

### Dimension Overlap Resolution
| D1(D3)同向→×0.8 | D4触发→D2 floor=0.3 | D2+D6已合并 |

### Minimum Data Requirements

```
D1: requires shuju page (H2H + recent form) → if missing, D1 = 0.5 (neutral)
D2: requires ouzhi + yazhi pages → if missing, skip scoring entirely
D3: requires yazhi opening handicap → if missing, D3 = 0.5
D4: requires yazhi change timestamps → if missing, D4 = 0.5
D5: requires yazhi water data → if missing, D5 = 0.5
```

---

## KB-5: Fundamental Factor Weights

| Factor | Weight | Data Source |
|--------|:------:|-------------|
| Squad quality gap | 30% | FIFA rank + market value |
| Defensive tier (incl. qualifier discount) | 20% | Clean sheets + GA vs qualifier avg |
| Winless inertia (≥6 match streak → +8%) | 15% | 3-match form |
| Motivation (elimination, debut, long-absence) | 15% | Group context |
| Home advantage | 10% | Venue + travel distance |
| Recent form (last 6) | 10% | GF/GA trend |

### Compression Intensity
| Grade | Change | Implication |
|-------|--------|-------------|
| Extreme | ≥15% drop | Real conviction or extreme narrative; verify fundamentals |
| Strong | 10–15% | Significant signal; check fundamentals |
| Moderate | 5–10% | True conviction threshold; cross-verify |
| Weak | <5% | Normal fluctuation; low value |

### Back-to-Wall Effect
- Elimination-threatened seeker → draw +5~8%, away +5%
- WC debut team → +10% motivation bonus
- Long-absence return (>8 years) → +5% motivation

---

---

## KB-5b: 平局专项信号（v3.6.2 新增，2026-06-24 诊断驱动）

> **根因**: 2026-06-16 四场全平局，系统 4 场全预测非平（100% 错误）。
> 诊断发现：系统架构上只允许输出主胜/客胜，平局从未被赋予最高置信度。
> **修复**: 平局必须与主胜/客胜平等竞争，平局专项信号必须参与方向判定。

### 平局信号强度分级

| 等级 | 触发条件（需同时满足） | 置信度调整 |
|:----:|:---|:---:|
| **强** | Pinnacle 平赔 < 3.20 且较开盘下降 ≥ 0.10<br>+ 平局离散度 ≤ 主/客离散度<br>+ 亚盘平手盘（handicap=0） | 平局置信度 +0.12 |
| **中** | Pinnacle 平赔 < 3.50 且较开盘下降<br>+ 任意 2 项（离散度低 / 平手盘 / deVig 平>28%） | 平局置信度 +0.06 |
| **弱** | Pinnacle 平赔 < 3.80<br>+ 亚盘平手盘 或 离散度收敛 | 平局置信度 +0.03 |

### 平局专项 OCI 权重（基于 179 场历史库）

| OCI 模式 | 含义 | 平局命中率 | 权重 |
|:---|:---|---:|:---:|
| OCI-4_CONVERGE + 平赔<3.50 | 机构共识平局 | 58.3% | +0.15 |
| OCI-1_DROP + OCI-4_CONVERGE | Pinnacle 降赔 + 机构共识 | 54.2% | +0.10 |
| OCI-5_SYNC + 平手盘 | 亚盘与欧赔同步指向平局 | 51.7% | +0.05 |
| OCI-4_DIVERGE | 机构分歧（平局无共识） | 38.9% | -0.10 |

### 与 Step 9 方向判定的接口

Step 9 综合信心分计算公式：

```
综合信心分(方向) = MBI评分 × 0.6 + OCI权重 × 0.3 + 陷阱调整 × 0.1

其中 陷阱调整：
  - 触发 A 类平局陷阱（信息型）→ 平局置信度 +0.08
  - 触发 B 类平局陷阱（诱导型）→ 平局置信度 -0.05
  - 触发 C 类平局陷阱（仓位型）→ 忽略（不调整）
```

### 平局方向输出条件

平局可以被输出为最终方向，当且仅当：

1. **平局综合信心分 ≥ 主胜综合信心分 且 ≥ 客胜综合信心分**
2. **平局综合信心分 ≥ 0.08**（否则降档为"跳过"）

若不满足条件 2，即使平局分数最高，仍输出次高分的主胜/客胜方向。

### 与 knowledge-base.md 其他 KB 的关系

- **KB-4（6D 评分）**: 新增 D7 维度 = 平局专项信号（权重 15%）
- **KB-10（MBI 多机构共识）**: SCS/DRI 模块需输出三方向评分，禁止只输出最低赔率方向
- **KB-16（OCI 客观指标）**: OCI-4 离散度需单独报告平局离散度
- **KB-17（DRM 平局因子）**: DRM-1（deVig 平>28%）已纳入，无需重复

---


## KB-6: Unified Logit Correction Pipeline

> 废除概率空间加法，全部迁移到 logit 空间。与 MBI 在同一管线中串行叠加，避免双轨冲突。

### 6.1 换算基准 (概率→logit)
```
+10%→+0.40 | +8%→+0.32 | +7%→+0.28 | +5%→+0.20 | +3%→+0.12
```

### 6.2 12 项校正换算为 logit 偏移

| # | Correction | Logit Δ | Condition |
|:--:|------------|:-------:|-----------|
| 1 | 欧亚陷阱 | ±0.40 | A/B/C 分类加权确定方向（C类→±0.40，B类→±0.20需量确认，A类→0） |
| 2 | 开盘定律 | ±0.32 | Any of 4 laws triggered |
| 3 | 临场真实性 | ±0.28 | Pass/fail check |
| 4 | 压缩强度 | +0.28 / +0.14 | Extreme/Strong → +0.28; Moderate → +0.14; Weak → 0 |
| 5 | 基本面一致 | ±0.20 | Weighted fundamental match |
| 6 | 背水一战 | 平 +0.20~0.32, 客 +0.20 | Seeker triggered |
| 7 | 叙事折扣 | 热门 −0.20 | Odds driven by "known news" |
| 8 | 6D 评分 | ±0.12 | ≥4→+0.12; ≤2→−0.12 |
| 9 | SBO 分歧 | ±0.12 | Asian sharp vs Pinnacle gap |
| 10 | 市场流动性 | conf × (0.85–1.00) | **后置乘数**（sigmoid 后应用，不进 logit 管线） |
| 11 | 外部因素 | xG × (1 ± penalty × 0.03) | **剥离至 KB-7**（进球倾向用，不进概率管线） |

### 6.3 组内降权规则（KB-6 内部）

**组3 — 盘口异常检测**（校正 #1 + #2 + #3，三者测同一现象）:
```
只取 max(|Δ|)，其余两项各 ×0.30
  corrected_组3 = max(|Δ₁|,|Δ₂|,|Δ₃|) × sign + 0.30 × next_largest + 0.30 × smallest
```
**组4 — 基本面/叙事**（校正 #5 + #6 + #7，信息源不同）:
```
线性叠加，不降权（信息源各自独立）
```

### 6.4 统一管线执行顺序（8 步）

```
① Shin de-vig → P_base（概率）
     ↓
② logit_base = ln(P_base / (1 − P_base))
     ↓
③ KB-6 校正（9项 logit偏移，含组3/组4降权）
   logit_ctx = logit_base + dampened_Σ(KB6_correction_i)
     ↓
④ KB-10.8 MBI 校正（6项 logit偏移，见 KB-10.8 降权规则）
   logit_final = logit_ctx + dampened_Σ(MBI_signal_i)
     ↓
⑤ 总量 cap:
   |KB6_correction_total| ≤ 0.80 logit (≈概率 ±20%)
   |MBI_total| ≤ 0.80 logit
   合计 |correction_total| ≤ 1.20 logit
   超出 → 按比例等比压缩到上限
     ↓
⑥ sigmoid: P = 1 / (1 + e^(−logit_final))
     ↓
⑦ 归一化: P_final = P / Σ(P)
     ↓
⑧ 后置乘数: conf' = conf × liquidity_factor (校正 #10)
             P_final 不变，仅压缩置信度
```

### 6.5 logit cap 数学含义

```
base 55% (logit=0.20) + cap 1.20 = logit 1.40 → sigmoid → ≈80% 主胜
  → 足球中 80% 已接近理性上限，杜绝 90%+ 虚假高置信度
```

---

## KB-7: Goal Tendency

> Poisson独立性假设不成立，精确比分预测是虚假精度。改为进球倾向三档判定。

### Base xG Flow (保留用于方向判定)
```
1. home_xG = (OU_line / 2) + (AH_line × 0.5)
   away_xG = (OU_line / 2) − (AH_line × 0.5)
2. Apply team form correction (WebSearch if available)
3. Apply external factors (KB-8 14.10 weather/travel/rest)
4. Adjust by probability: home_xG ×= (pred_home/50%), away_xG ×= (pred_away/50%)
```

### Goal Tendency Classification

```
Step 1: 计算全场预期总进球
  total_xG = home_xG + away_xG

Step 2: 校正因子
  14.0a 客场防守折扣: away def tier "elite" → total_xG ×0.92
  14.0b 深盘压制: pred_home ≥70% AND AH ≥1.5 → total_xG += 0.5 (stomp potential)
  14.2 OU Price Calibration: adjusted_OU = OU_line + (OU_home_water − 1.90) × 0.5
  14.4 xG Factor: team form adjustment (WebSearch, skip if unavailable)
  14.5 Phase Coefficient: Group R1 ×1.00 / R2 ×0.95 / R3 ×0.90 / KO R16 ×0.88 / QF ×0.85 / SF ×0.82 / Final ×0.80
  14.6 Zero-Inflation: both teams ≤2 GF/game → total_xG ×0.90
  14.10 External: weather ≤ −1.0 → total_xG ×0.85; rest deficit → ×0.92

Step 3: 最终校正
  final_xG = total_xG × Π(correction_factors)
  weighted_OU = max(OU_line, final_xG) × 0.4 + min(OU_line, final_xG) × 0.6 (anchor to market OU)

Step 4: 判定
  偏大球: weighted_OU ≥ 2.75 or (weighted_OU ≥ 2.5 and draw exclusion 4/4 true)
  偏小球: weighted_OU ≤ 2.0 or (weighted_OU ≤ 2.25 and both teams defensive fortress)
  中性: 2.0 < weighted_OU < 2.75

Step 5: 置信度
  高: market OU + team trends + external factors all aligned
  中: 2 of 3 aligned
  低: ≤1 aligned or data missing
```

### Draw Exclusion (保留用于大小球判定)
```
All 4 true → over boost:
  1. Both no 0-0 in last 3  2. Combined GF >2.5
  3. OU 2.5 over water ≤1.85  4. No defensive fortress (KB-3 rule #27)
```

### ⛔ 已移除 (原因: 虚假精度/与进球倾向无关)
~~Poisson 比分 / Top3比分 / 14.0c/14.1/14.3/14.7/14.8/14.11/14.0d/14.0e~~

---

## KB-8: Supplementary Methodology (Quick Reference)

### Kelly Criterion
```
f* = (bp - q) / b
where f* = fraction of bankroll, b = net odds, p = win probability, q = loss probability
```

### Asian Handicap Conversion (Quick)
```
Probability -> AH line approximation:
  P(home) - 0.50 > 0.02 -> 0    > 0.08 -> 0.25  > 0.14 -> 0.5
               > 0.20 -> 0.75  > 0.27 -> 1.0   > 0.33 -> 1.25
               > 0.38 -> 1.5   > 0.42 -> 1.75  > 0.47 -> 2.0
```

### Over/Under Line to Goal Expectation
```
OU 2.5 -> xG ~2.5  |  OU 2.0 -> xG ~2.0  |  OU 3.0 -> xG ~3.0
OU 2.25 -> xG ~2.25 |  OU 2.75 -> xG ~2.75
```
## KB-9: 复盘/回测 → 用 football-backtest-workflow

> 赛后回测复盘已统一由 `football-backtest-workflow/` 子技能处理（7 阶段/9 层报告）。
> 详见 analyst SKILL.md Step 13 赛后回测触发器。旧版 postmortem.md 已删除。

---

## KB-10: MBI — Multi-Bookmaker Intelligence Framework

> **Rationale**: Pinnacle is the gold standard but not infallible. 30-bookmaker data from 500.com enables consensus-weighted analysis that captures signals Pinnacle alone misses.

### 博彩公司分级

| Tier | Weight | Members | Characteristics |
|:---|:---:|:---|:---|
| **Sharp** | 0.55 | Pinnacle, bet365, IBC(沙巴) | Accept winning players, razor-thin margins, lead price discovery |
| **Asian** | 0.25 | 澳门, 皇冠, 利记, 易胜博, 12bet, 18bet | Regional capital flow, water-level sensitive, macro-policy influenced |
| **Retail** | 0.20 | 威廉希尔, 立博, Interwetten, 必发(exchange), 伟德, Bwin | Public sentiment, recreational volume, exchange reveals real money |

### SCS — Sharp Consensus Score (需10.3b量价交叉验证)

```
SCS = Σ(tier_w_i × dir_i) / Σ(tier_w_i)
  dir_i: +1↓/−1↑/0|<噪声阈值 | 噪声 = max(0.02×odds, 1.5×σ历史)
  幅度权重 = min(|变化%/10%|, 1.0) | 时间衰减 = exp(−小时/24)
  权重化方向 = dir × 幅度权重 × 时间衰减
```

交叉验证要求:
```
SCS 信号生效需通过 10.3b 量价交叉验证:
  SCS ≥ 0.70 + 成交量确认方向 → 全效，logit +0.40
  SCS ≥ 0.70 + 成交量不配合 → 降效，logit +0.15（可能仓位驱动）
  SCS < 0.40 + 成交量放大 → 分歧有效，logit −0.20
  SCS < 0.40 + 成交量萎缩 → 低流动性噪声，忽略
```

**Thresholds** (均需量价验证):
- SCS ≥ 0.70 → Strong consensus → 经量价验证后 ±logit
- SCS 0.40–0.70 → Moderate → no adjustment
- SCS < 0.40 → Weak consensus → Step 10 penalty −5%

### DRI — Dispersion Risk Index

```
DRI_raw = ouzhi.dispersion.home × 0.5 + ouzhi.dispersion.draw × 0.3 + ouzhi.dispersion.away × 0.2

联赛校准: DRI_calibrated = DRI_raw / league_median_DRI × 30
  (league-specific: take 500+ historical matches per league median DRI as baseline, eliminates natural inter-league differences)
  WC/EPL/UCL median ~12-18; lower-division median ~25-40

阈值 (以 WC/top5 联赛为默认):
  DRI_cal < 12 → Tight consensus → confidence × 1.05
  DRI_cal 12–35 → Normal → no adjustment
  DRI_cal 35–60 → High dispersion → confidence × 0.85, ⚠️ warning
  DRI_cal > 60 → Extreme → confidence × 0.70, 🔴 systemic risk flag

信息驱动 vs 混乱型离散 :
  如果 DRI 高 AND Pinnacle 领涨 (Lead-Lag STRONG):
    → Info-driven dispersion (market repricing), DRI_signal halved
  如果 DRI 高 AND Lead-Lag = NOISE:
    → Chaos-type dispersion (retail noise), DRI_signal fully applied
```



#### DRI Tier-Variance Analysis

```
Information-type dispersion (faction divergence) detection:
  Condition: Sharp-tier internal dispersion < 10 AND Retail-tier internal dispersion < 10
        BUT |Sharp mean − Retail mean| > 0.15

  Meaning: Sharp tier (Pinnacle/bet365/IBC) unified, Retail tier (William Hill/Ladbrokes) unified,
        but opposite directions. Sharp tier has inside information, Retail tier still pricing on old data.

  Action: DRI penalty halved (×0.5)
        Extra Sharp-follow correction: logit +0.20 (follow Sharp direction)
        Marked as "Info-Type Divergence — Follow Sharp"

Chaos-type dispersion detection:
  Condition: Info-type conditions not met, AND DRI > 40

  Meaning: 30 bookmakers in disorder, no tier pattern, random cross-cutting.
        Bookmakers themselves uncertain, pure noise.

  Action: DRI penalty fully applied
```

### 10.3 Lead-Lag Chain Detection

```
Parse change_time from yazhi page (format: "MM-DD HH:MM").
Timestamp quality check: if 500.com scrape delay >1h, downgrade to low confidence.

Lead institution priority (by event type):
  Western events (WC/Euro/EPL/UCL): Pinnacle > bet365 > Macau
  Asian events (AFC CL/J-League/K-League): SBO/IBC > Macau > Pinnacle
  World Cup: Pinnacle = SBO (equal weight, global pricing)

链类型:
1. Lead moves first → secondary follows <2h → tertiary follows <4h
   → STRONG SIGNAL, logit +0.40
   Magnitude bonus: if lead adjusts ≥5%, extra +0.10

2. Lead moved → majority DID NOT follow within 4h
   → WEAK SIGNAL, 忽略

3. Non-lead moved first → lead remained static
   → NOISE, 忽略

4. 三层同时动 (1h 窗口内)
   → GENUINE EVENT, logit +0.20

Default: no clear chain → 0
```

#### 10.3b Volume×Price Cross-Validation



```
四象限判定矩阵（结合 touzhu 页必发成交量数据）:

  ┌─────────────────┬───────────────────┬──────────────────┐
  │ 赔率方向         │ 成交量↑(配合)      │ 成交量→(不配合)    │
  ├─────────────────┼───────────────────┼──────────────────┤
  │ 赔率↓(看好)     │ 被动调价(仓位驱动)  │ 主动降价(信息驱动) │
  │                 │ = 噪音, 忽略       │ = 真信号, ×1.3    │
  │                 │ Lead-Lag 降级      │ Lead-Lag 升级    │
  ├─────────────────┼───────────────────┼──────────────────┤
  │ 赔率↑(看淡)     │ 被动抬价(资金离场)  │ 主动抬价(诱导)     │
  │                 │ = 撤退信号,        │ = 反向信号,       │
  │                 │   logit −0.15      │   logit +0.20    │
  │                 │                   │   (跟庄家反向)    │
  └─────────────────┴───────────────────┴──────────────────┘

判定阈值:
  成交量↑: 必发该方成交量 > 前 4h 均量 × 2
  成交量→: 必发该方成交量 < 前 4h 均量 × 1.2

与 Lead-Lag 集成:
  检测到 Lead 变动 → 立即查必发对应方向成交量
  主动降价 + STRONG chain → logit +0.40 × 1.3 = +0.52 (最强信号)
  被动调价 + STRONG chain → logit +0.40 × 0.5 = +0.20 (降级)
  主动抬价(诱导) + GENUINE EVENT → logit −0.20 (庄家反向操作)

与陷阱 B 类联动:
  B 类陷阱触发 + 赔率变动方向无量配合 → 确认为诱导 → 强化原方向
  B 类陷阱触发 + 赔率变动方向有量配合 → 转为 C 类处理 → 降信度
```

### 10.4 Water Flow Analysis

Water level changes must first be controlled to compare only under the same handicap level:

```
Prerequisite: only count AH water changes from bookmakers whose handicap level DID NOT change.
      Bookmakers with level changes are flagged separately, excluded from flow stats.

Bookmaker dedup: 16 AH companies contain same-group white labels (Crown/Legacy/EasyBet share odds source).
          Cluster odds vectors first (correlation > 0.95 = same source),
          take one representative per cluster. Independent sources typically 6-9.

统计规则 (锁定盘口后):
  flowing_in:  home water↓ OR away water↑ = 看好主队
  flowing_out: home water↑ OR away water↓ = 看淡主队

Flow Ratio = |flowing_in − flowing_out| / N_independent_sources

Flow Ratio ≥ 0.75 (强流向):
  + Pinnacle 领涨 → STRONG，logit +0.30
  + Pinnacle 静态 → SUSPICIOUS，logit −0.20
  flowing_out → logit −0.30

0.50–0.75 → 中度，logit ±0.10
< 0.50 → 分散，无信号

#### Sharp Counter-Betting Asian Heat

```
Asian Heat vs Sharp Counter-Bet Detection:

Trigger: Flow Ratio ≥ 0.70 (Asian tier: Macau/Crown/Legacy/12bet)
          AND (Pinnacle 反向变动 ≥0.03 OR Pinnacle 极度静态 >4h)

Meaning: Asian tier retail money flooding in same direction (water dropping hard),
      but Sharp tier Pinnacle not only fails to follow, it COUNTER-MOVES or absorbs.
      Classic "retail hot vs institution cold" — Sharp tier is counter-betting Asian heat.

处理: 热门方 logit −0.35（强反向）
      Marked as 🔴 counter signal, consider opposing side
      对应 Trap #19 修正
```

### Exchange-Traditional Divergence
```
From touzhu data (必发 Betfair exchange):

┌─ Three-Layer Exchange Analysis ──────────────────────────┐
│ Layer 1: Volume Ratio (成交量占比)                         │
│   volume_ratio = volume_favorite / total_volume            │
│   volume_ratio > 0.80 → heavy interest (don't skip)       │
│   volume_ratio < 0.50 → thin market, confidence ×0.90     │
│                                                           │
│ Layer 2: VWAP vs Bookmaker (成交量加权均价偏离)  NEW       │
│   VWAP = Σ(price_i × volume_i) / Σ(volume_i)              │
│   divergence = (VWAP_favorite / Pinnacle_favorite − 1)     │
│   divergence ≤ −0.03 (VWAP significantly lower):           │
│     → SMART MONEY: big buyers got better price than mkt    │
│     → logit +0.25 (institutional conviction)              │
│   divergence ≥ +0.03 (VWAP higher than Pinnacle):          │
│     → DUMB MONEY: retail paying premium, no conviction     │
│     → logit −0.15                                         │
│   −0.03 < divergence < +0.03:                              │
│     → NEUTRAL: volume at market price, no edge            │
│                                                           │
│ Layer 3: Bookmaker P&L Exposure (庄家盈亏敞口)  NEW       │
│   pl_exposure = bookmaker_PL / total_volume × 100%         │
│   pl_exposure < −20% on favorite:                          │
│     → BOOKMAKER EXPOSED: bookmaker heavily exposed on favorite side          │
│     → May trigger odds increase to balance risk → logit −0.10 (caution)   │
│   pl_exposure > +50% on underdog:                          │
│     → BOOKMAKER HEDGED: 庄家在冷门方盈利充足               │
│     → no signal (bookmaker already protected)             │
│                                                           │
│ Match Size Weighting (赛事体量折扣)  NEW                   │
│   total_volume > £500K  → weight 1.00 (major event)       │
│   total_volume £100K–500K → weight 0.70 (medium)          │
│   total_volume £50K–100K → weight 0.40 (small)            │
│   total_volume < £50K  → weight 0.10 (micro, skip)        │
│                                                           │
│   ALL exchange signals × match_size_weight                 │
└───────────────────────────────────────────────────────────┘

Exchange Composite Signal:
  exchange_logit = (vwap_signal + exposure_signal) × volume_confidence × match_weight
  where volume_confidence = min(1.0, volume_ratio / 0.80)
```



### 10.6 Kelly Consensus

Kelly index has no absolute directional interpretation — must segment by scenario, phase, and cross-validate.

#### 10.6.1 定义
```
Kelly = 赔率 × 去抽水概率
阈值 = bookmaker_return_rate × 1.02
Pinnacle ~98% → Kelly>0.98 = 高 | 竞彩 ~89% → Kelly>0.89 = 高
```

#### 10.6.2 Two Interpretation Frameworks

| Framework | Core Premise | Applicable Scenario | Signal Interpretation |
|:---|:---|:---|:---|
| **Theoretical Market-Making Logic** | Bookmaker balances bets, profits from vig, does not actively take positions | 90% regular leagues, non-marquee matches, stable fund flow events | Lower Kelly → less payout pressure on bookmaker → stronger market consensus → higher outcome probability |
| **Game-Theoretic Bookmaking Logic** | Bookmaker abandons bet balancing, exploits retail cognitive gaps to set traps | Top cup knockout stages, elite club derbies and other capital-surge marquee matches | Favorite side heavy capital inflow but Kelly rises instead of falling → bookmaker unafraid of payout, truly bullish; Kelly keeps falling → bait trap |

#### 10.6.3 Scenario Determination Rules

```
Phase 1: Event Classification
  焦点赛事 (启用博弈逻辑):
    - 世界杯淘汰赛阶段 (R16+)
    - 欧冠淘汰赛
    - 五大联赛争冠/保级关键战
    - 豪门德比 (任何赛事)
    - 必发成交量 > £2M 的任何赛事
  
  普通赛事 (启用理论逻辑):
    - 所有非焦点赛事
    - 联赛中游无欲无求的场次
    - 友谊赛（无论成交量多少，凯利信号不适用）

Phase 2: Time Phase
  Opening phase (>24h to kickoff): market-making logic only (opening odds reflect fundamental assessment)
  Peak betting (<24h to kickoff): focus matches switch to game theory logic, ordinary matches keep market-making logic

Phase 3: Volume Validation
  Betfair volume > £1M: game theory logic enabled
  Betfair volume £200K–£1M: game theory → signal halved
  Betfair volume < £200K: game theory disabled, fall back to market-making logic
```

#### 10.6.4 Core Determination Rules

**Regular Events (Theoretical Logic)**:

| Condition | Signal | Logit Δ |
|:---|:---|:---:|
| Favorite Kelly < (return_rate − 0.05) AND lowest among three | Institution controlling payout, bullish on favorite | +0.15 |
| Favorite Kelly > (return_rate + 0.05) | Institution not controlling payout, favorite questionable | −0.20 |
| Favorite Kelly within range | Neutral | 0 |
| All three Kelly < (return_rate − 0.10) | Excessive vig, signal downgrade | Confidence ×0.88 |

**Marquee Event Peak Betting Phase (Game-Theoretic Logic)**:

| Condition | Signal | Logit Δ |
|:---|:---|:---:|
| Favorite heavy inflow (>70% vol) + Kelly rising vs opening | Bookmaker unafraid of payout, truly bullish | +0.20 |
| Favorite heavy inflow (>70% vol) + Kelly continuously falling vs opening | Bait trap, favorite questionable | −0.25 |
| Favorite Kelly rising vs opening + 3+ Sharp tier books syncing upward | Sharp consensus confirmed | +0.10 (stacked) |
| Insufficient volume (<£200K) | Game-theoretic logic not applicable | Fallback to theoretical logic |

#### 10.6.5 Cross-Validation Rules (MANDATORY)

```
Kelly signals CANNOT act alone, must resonate with other MBI modules:

✅ Kelly positive + Lead-Lag confirmed (STRONG or GENUINE) + Water Flow same direction
   → 信号生效，校正幅度拉满

⚠️ 凯利正向 但 DRI > 40（高分歧）
   → Kelly downgraded, correction halved

❌ Kelly conflicts with SCS consensus or Water Flow direction
   → Kelly invalid; trust Water Flow + Betfair data instead

❌ Kelly conflicts with Betfair VWAP direction
   → Kelly invalid; VWAP is real money voting, higher priority
```

#### 10.6.6 Application

```
kelly_logit = applicable_framework(category, phase, volume) → signal

Cross-validation check:
  if kelly_signal × (LeadLag or WaterFlow) ≥ 0:
    kelly_effective = kelly_logit
  else:
    kelly_effective = 0  (signal invalidated by conflict)

Apply: logit' = logit + kelly_effective
```

### 10.7 Four New MBI Trap Rules

| # | Rule | Trigger | Signal | Action |
|:--:|------|---------|:------:|--------|
| 16 | **Tier Divergence** | Sharp tier vs Asian tier AH gap ≥0.25 ball | 🔴 systemic | Confidence ×0.85, flag match |
| 17 | **Exchange-Volume Spike** | 必发 volume >2× previous + odds static | ⚠️ resistance | Direction confidence −5% |
| 18 | **Kelly Context Gap** | Marquee match betting phase: favorite Kelly rising not falling + 3+ Sharp tier syncing upward + Betfair volume >70% | ✅ context signal | Direction +5%, logit +0.20 (requires cross-validation: Lead-Lag/WaterFlow same direction to activate) |
| 19 | **Sharp Counter-Betting** | Flow Ratio ≥0.70 (Asian tier) + Pinnacle opposing or extremely static >4h | 🔴 counter-bet | Favorite logit −0.35, consider betting underdog |

### MBI logit-space集成



```
Step A: 基础概率 → logit 转换
  logit_h = ln(P_h / (1 − P_h))
  logit_d = ln(P_d / (1 − P_d))
  logit_a = ln(P_a / (1 − P_a))

Step B: 在 logit 空间叠加所有校正
  logit_h' = logit_h + Σ(correction_i)
  where correction_i is the logit offset from each correction factor (from KB-6)

Step C: sigmoid 转回概率
  P_h' = 1 / (1 + e^(−logit_h'))
  P_d' = 1 / (1 + e^(−logit_d'))
  P_a' = 1 / (1 + e^(−logit_a'))

Step D: 归一化
  total = P_h' + P_d' + P_a'
  final = [P_h'/total, P_d'/total, P_a'/total]
```

Probabilities bounded (0,1), Bayesian-equivalent, magnitude auto-compresses near extremes.

### MBI Composite — logit空间

> 四组降权 + cap + 与KB-6串联:

```
#12 MBI Composite 作为 logit 偏移量:
  mbi_raw = SCS_raw + DRI_raw + LeadLag_raw + Kelly_raw + WaterFlow_raw + VolXPrice_raw

  各模块原始信号 (raw signal):
  SCS_raw :
    SCS ≥ 0.70 + 量价确认 → +0.40
    SCS ≥ 0.70 + 量价不配合 → +0.15
    SCS 0.40–0.70 → 0
    SCS < 0.40 → −0.20

  DRI_raw:
    DRI < 15 → +0.20
    DRI 15–40 → 0
    DRI 40–70 → −0.35
    DRI > 70 → −0.70

  LeadLag_raw :
    STRONG chain + 主动降价 → +0.52
    STRONG chain + 被动调价 → +0.20
    STRONG chain (无量数据) → +0.40
    GENUINE EVENT + 主动抬价(诱导) → −0.20
    GENUINE EVENT → +0.20
    NOISE/WEAK → 0

  Kelly_raw:
    fav Kelly < 0.92 + lowest → +0.20
    fav Kelly > 1.00 → −0.35
    neutral → 0

  WaterFlow_raw:
    Flow ≥ 0.70 + Pinnacle leads → +0.30
    Flow ≥ 0.70 + Pinnacle static → −0.20
    Flow < 0.50 → 0

  VolXPrice_raw :
    主动降价(信息驱动) → +0.17
    主动抬价(诱导) → −0.20
    被动调价(仓位驱动) → 0
    资金离场(被动抬价+量增) → −0.15
```

### 四组降权

覆盖KB-6 9项 + MBI 6项:

```
四组降权规则:

组1 — 资金热度/共识 (MBI): SCS + LeadLag + WaterFlow
  三者测同一现象("市场往哪走")，方向几乎总同向。
  处理: 只取 max，其余两项各 ×0.25
  signal_组1 = max(SCS, LeadLag, WaterFlow) + 0.25 × mid + 0.25 × min
  (原: +0.40+0.52+0.30=1.22 → 新: 0.52+0.10+0.075=0.695 logit)

组2 — 市场不确定性 (MBI): DRI + SBO分歧(校正9) + 6D评分(校正8)
  三者测市场噪音/分歧/不确定性。
  处理: 只取最负的一项（风险厌恶原则），其余忽略
  signal_组2 = min(0, DRI_raw, 校正9_raw, 校正8_raw)
  (保留最悲观信号，不叠加)

组3 — 盘口异常检测 (KB-6): 校正1(欧亚陷阱) + 校正2(开盘定律) + 校正3(临场真实性)
  处理: 只取 max(|Δ|)，其余两项各 ×0.30 (同 KB-6.3)
  signal_组3 = max(|Δ₁|,|Δ₂|,|Δ₃|) × sign + 0.30 × next + 0.30 × last

组4 — 基本面/叙事 (KB-6): 校正5(基本面) + 校正6(背水一战) + 校正7(叙事)
  信息源各自独立 → 线性叠加，不降权
  signal_组4 = 校正5 + 校正6 + 校正7

跨组规则:
  KB-6 组(组3+组4) 与 MBI 组(组1+组2) 不额外降权（信息源不同）
```

### MBI Final

```
mbi_logit = signal_组1 + signal_组2

Apply:
  logit_final = logit_ctx + min(mbi_logit, 0.80)
  (MBI 总量 cap 0.80 logit，≈概率 ±20%)
```

### Total Correction Cap

```
|KB6_correction_total| ≤ 0.80 logit  (组3+组4+其他独立项)
|MBI_total| ≤ 0.80 logit  (组1+组2+独立项)
合计 |correction_total| ≤ 1.20 logit

含义（以 base 55%，logit=0.20 为起点）:
  +0 校正   → sigmoid(0.20) = 55%
  +0.60     → sigmoid(0.80) = 69%
  +1.00     → sigmoid(1.20) = 77%
  +1.20 CAP → sigmoid(1.40) = 80%  ← 硬上限
  80% 是足球预测的理性上限，从此杜绝 90%+ 虚假高置信度
```

### 报告中的MBI面板

Each match report MUST include an MBI panel:

```
┌─ MBI Assessment ─────────────────────┐
│ SCS (Sharp Consensus):  ████████░░ 0.82  Strong │
│ DRI (Dispersion Risk):  ██░░░░░░░░ 12.4   Tight │
│ Lead-Lag: Pinnacle→bet365→澳门  STRONG       │
│ Tier Diverge: None                            │
│ Water Flow:  11/16 flowing in (0.69)          │
│ Kelly Avg:    fav 1.02 / others 0.88          │
│ MBI Verdict:  CONFIRM (all signals aligned)   │
└───────────────────────────────────────────────┘
```

### 数据质量验证

```
Before applying ANY MBI module, validate input data quality:

1. Bookmaker Count Check:
   ouzhi requires ≥20 of 30 bookmakers with valid data
   yazhi requires ≥12 of 16 bookmakers with valid data
   < threshold → module marked DEGRADED, confidence ×0.85

2. Timestamp Freshness:
   yazhi change_time within 6h of current time → FULL weight
   within 6–12h → 0.7× weight
   >12h or missing → DEGRADED, 0.4× weight

3. Data Completeness per Match:
   All 6 pages present → FULL analysis
   5/6 → min 4 core modules (ouzhi+yazhi+touzhu+shuju), others skipped
   <4/6 → match flagged LOW QUALITY, confidence ×0.80

4. Betfair Volume Sanity:
   total_volume > £50K → exchange modules enabled
   total_volume < £50K → exchange modules DISABLED for this match
   volume spike >5× league average → suspicious, flag but don't skip

5. Bookmaker Consistency:
   If >5 bookmakers show identical odds (potential data mirroring):
     deduplicate before SCS calculation
     lower effective N in consensus scoring
```

---

## KB-11: Data Calibration

> 确保输入信号干净可比较。

### 11.1 Dynamic Bookmaker Deduplication

```
血缘: 沙巴系(IBC/12bet/18bet/M88) | Crown(皇冠/利记/易胜博/明升) | Entain(立博/Bwin/Coral)
系内去重: N家→1个独立节点, 权重=原权重×√N
动态: Pearson r>0.95+时间戳→更新血缘图
脏数据: 单家>均值3σ+无时间戳→丢弃 | 去重后<5家→DRI升1档, WF×0.5
```

### 11.2 Cross-Bookmaker Water Normalization

```
归一化 = 原始水位 × (0.95/该机构标准返还率)
Macau 0.90/0.92→0.929 | Pinnacle 0.975/0.98→0.945
禁止直接使用未校准原始水位
```

### 11.3 True Opening Odds Anchor

```
弃用72h初盘(低流动性/试盘)
真实初盘=24-48h中首达条件之赔率: (a)必发量>£100K 或 (b)亚盘量>HK$100K
24h内均未达→以24h节点为基准
```

### 11.4 Event Tiering

| Parameter | Top-Tier Events | Second-Tier Events | Low-Tier Events |
|:---|:---|:---|:---|
| **Scope** | 五大联赛/欧冠正赛/世界杯正赛/欧洲杯正赛 | 荷甲/日职/美职/巴甲/欧冠资格赛 | Low divisions/friendlies/preseason/early qualifiers |
| **Bookmaker Weight** | Sharp 0.6 / Asian 0.2 / Retail 0.2 | Sharp 0.45 / Asian 0.35 / Retail 0.2 | Sharp 0.3 / Asian 0.4 / Retail 0.3 |
| **DRI Thresholds** | 12 / 35 / 65 | 18 / 45 / 75 | 25 / 55 / 80 |
| **Kelly Game-Theoretic Logic** | Betfair > £1M enabled | Betfair > £500K enabled | **Fully disabled game-theoretic logic** |
| **Betfair Signal Weight** | 100% | 50% | **0% (disabled)** |
| **Special Restrictions** | None | None | No "draw" bets; DRI > 35 = abandon |

```
动态定级:
  Minnow event single-match Betfair > £500K → auto-upgrade to Secondary
  Top-league reserve teams/cup dead rubbers → auto-downgrade to Secondary
  Friendlies always classified as Minnow, upgrade not applicable
```

---

## KB-12: Advanced Signal Quantification

> 所有 logit 校正须对应庄家操盘手法。

### 12.1 回调验证

```
4h内回调>50%→假测试→清除信号 | <20%+趋势保持→确认
20-50%→减半 | 亚洲赛事SBO+澳门(非Pinnacle) | 西向Pinnacle(SBO验证)
```

### 12.2 AH真假突破

| 类型 | 条件 | 效果 |
|:---|:---|:---:|
| 真突破 | 对应方向水位≤0.925+Sharp先动 | ±0.18 |
| 假突破(Trap) | 水位≥1.00+仅Asian动/Sharp不动 | **反向±0.22** |

临场1h内×1.3 | 24h外×0.7 | SPF<1.35×0.5(被动平衡)


### 12.3 必发订单簿阻力墙

```
热门ask-1≥bid-1×3+持续30min+取消率<20%→阻力墙→logit -0.25
下盘阻力墙(零售逆势)→×1.3 | 支撑墙(热门bid≥ask×2+稳降)→+0.20
仅用level1(2-3层是庄家虚单) | 仅Betfair量>£100K时启用
```

### 12.4 初受盘差分析

```
Sharp vs Asian差≥0.25球→高波动→信号×0.5→禁入串关核心
反市场操作: 必发>80%看好+盘口反向下调+无新闻→庄家主动操作→×1.5
```

### 12.5 Draw Diversion Trap (Bidirectional)

```
Positive diversion (bookmaker setting capital pool):
  Draw Kelly < min(home Kelly, away Kelly) − 0.1
  + 平局必发成交量占比 < 20%
  → Bookmaker uses low Kelly draw to attract capital, genuinely does not expect draw
  → 平局概率下调，热门方 logit +0.12

反向分流（散户追捧平局）:
  Draw Kelly > max(home Kelly, away Kelly) + 0.1
  + 平局必发成交量占比 > 35%
  → Retail crowd frantically buying draw, bookmaker raising payout unafraid of it hitting
  → 平局概率下调，胜负方 logit +0.10
```

---

## KB-13: System Risk Controls

### 13.1 Dynamic Slippage Model

| Phase | Time Window | Slippage | Description |
|:---|:---|:---:|:---|
| Opening | >24h | 1% | Ample liquidity |
| Mid-Betting | 6-24h | 2% | Normal fluctuation |
| Late | 1-6h | 3.5% | Frequent water sweeps |
| Pre-close | <30min | 5% | Extreme volatility |

```
串关滑点叠加:
  Total slippage = single-match slippage × √N  (independent random variable variance stacking)
  3串1 临场总滑点 = 3.5% × √3 ≈ 6.1%

凯利计算前置:
  adjusted_odds = odds × (1 − slippage) × return_rate
  所有 EV 统一使用 adjusted_odds
```

### 13.2 Signal Confidence Tiering → 见 betting-sop.md

> 信号分级、Kelly系数、单场上限、串关准入规则已移入 `references/betting-sop.md`。
> 本模块仅保留分析层面的风险控制。

### 13.7 Permanently Excluded Feature Blacklist

```
❌ 真实赛事数据 (xG/Opta):
   Bookmaker quants already priced into opening odds; retail recalculation = lagged noise

❌ NLP 新闻事件自动量化:
   News is poison bookmakers feed retail; automated news scraping = eating trap baits

❌ LSTM/Transformer 赔率时序预测:
   Odds are human-adjusted based on capital pool, no intrinsic physical laws
   深度学习 = 100% 严重过拟合

❌ 必发三档深度:
   Level 2-3 mostly market-maker ghost orders; inclusion = noise amplifier

❌ Single static parameter set for all events:
   Ignores league transparency differences = top leagues miss signals + minnow leagues hit traps
```

### 13.8 竞彩市场转换层

> ⚠️ **数据源强制分层**: 分析层(Pinnacle, ~98%)用于 Steps 1-10.5 的赔率分析；
> 执行层(竞彩, ~71%)专用于 Step 11 的投注建议和 EV 计算。**两层数据严禁混用**。
> EV阈值分级、串关策略 → 见 betting-sop.md

#### 13.8a 竞彩赔率数据源

```
竞彩官方赔率有两个来源，不可混淆:

源1: 竞彩 SPF (胜平负) 赔率
  来源: trade.500.com/jczq/?playid=312&g=2 页面 → "胜/平/负"三列
  用途: 直接投注胜平负玩法时的赔率
  验证: trade.500.com 首页 SPF 列显示的是竞彩官方赔率, 不是百家平均

源2: 竞彩 RQSPF (让球胜平负) 赔率
  来源: odds.500.com/fenxi/rangqiu-{id}.shtml → 第1行 "竞*官*"
  解析格式: [让球数][初盘主][初盘平][初盘客][即时主][即时平][即时客]
    数字连续无分隔符，按小数点分隔。
    示例: "-12.253.182.702.003.253.11"
      → 让球=-1, 初盘=2.25/3.18/2.70, 即时=2.00/3.25/3.11
  用途: 深盘场 SPF 未开售时的替代玩法

单关玩法可用性:
  参考: trade.500.com/jczq/?playid=312&g=1
  规则: 只有出现在该页面的比赛才支持单关投注
  动作: 在 Step 11 构建单关方案前, 逐场核验 single_match_available 标志
```

#### 13.8b 竞彩 EV 转换公式 (v3.10.0 更新)

> **v3.10.0**: 从 Pinnacle_deVigProb 切换到竞彩自身去水概率。竞彩市场自洽, 无需 Pinnacle 介入。

```
竞彩自身隐含概率法:
  竞彩_SPF_总概率 = 1/C_h + 1/C_d + 1/C_a
  竞彩_去水概率_h = (1/C_h) / 竞彩_SPF_总概率
  竞彩_返还率 = 1 / 竞彩_SPF_总概率

单关 EV:
  EV_single = 竞彩_去水概率_i × 竞彩赔率_i − 1

串关 EV:
  P_hit = ∏ 竞彩_去水概率_i  (各腿独立)
  payout = ∏ 竞彩赔率_i
  EV_parlay = P_hit × payout − 1

  注意: 串关 EV 已内嵌竞彩返奖率结构, 无需额外乘系数

  验证: 如果竞彩市场定价完美(无偏差):
    竞彩_去水概率_i × 竞彩赔率_i = 1/竞彩返还率 > 1
    → 单关 EV > 0 是系统性正期望 (因为 deVig 去掉了抽水)
    → 串关 P_hit × payout = ∏(1/返还率) >> 1
    → 但串关实际返奖率低, 所以需要更严格的 EV 阈值

串关 EV 阈值:
  3串1 腿: EV > −0.05 → 保留 (有容错机制兜底)
  4串1 腿: EV > 0 → 保留 (无容错, 必须正期望)
  2串1: EV > −0.08 → 保留

旧公式 (废弃):
  竞彩 EV = Pinnacle_deVigProb × 竞彩赔率 × 串关返奖率 − 1
  问题: Pinnacle 全球市场概率 ≠ 竞彩中国市场概率, 偏差 3-5%
```

#### 13.8c 竞彩特有的"赔率冻住"风险

```
竞彩赔率开售后不随国际市场变动。

规则:
  国际市场赛前 1h 发生显著变盘（>5% 方向移动）
  且竞彩赔率未更新
  → 报告强制声明: "⚠️ 价格失效 — 国际赔率已变，竞彩赔率可能不反映当前市场"
  → 相应方向竞彩 EV 可靠性降级
```

#### 13.8d 单关 vs 串关返奖率差

```
竞彩返奖率:
  单关: ~86%
  串关 (2串1): ~71%
  串关 (3串1): ~71%² ≈ 50%

策略含义:
  竞彩 EV = deVigProb × C_odds × R − 1
  → 单关 EV 阈值: EV ≥ 0 即正期望
  → 串关 EV 阈值: 需 ≥ +0.05 才能覆盖返奖率差
  → Step 11 串关构建前: 逐条腿计算竞彩 EV，任何 EV<−0.05 不得入选
```

---

## KB-14: Bookmaker Intelligence — Market Pressure

> 扩展 MBI 框架的"庄家读心"层。不改变方向判定，只调节置信度。

---

### 14.1 Module 1: Pulsation (拉锯战指数)

#### 14.1.2 核心指标

| 指标 | 计算 | 含义 |
|:---|:---|:---|
| 频率F | 方向改变/采样-1 | ≥0.4=犹豫 |
| 位移D | \|首末差\|/首值 | <1.5%=微弱 |
| TWQ | F/(D+0.001) | >50=严重拉锯 |

#### 14.1.3 二维决策矩阵

```
            | D < 1.5% (低位移)  | D ≥ 1.5% (高位移)
────────────┼─────────────────────┼─────────────────────
F ≥ 0.4     | 高频低幅             | 高频高幅
(高频)      | 虚晃一枪             | 宽幅洗盘
            | 信度 × 0.75         | 信度 × 0.85
────────────┼─────────────────────┼─────────────────────
F < 0.4     | 低频低幅             | 低频高幅
(低频)      | 死水一潭             | 单边突破
            | 信度 × 0.90         | 信度 × 1.15
```

#### 14.1.4 判断规则

```
IF TWQ > 50 OR matrix = "高频低幅" → PULSATION_WARNING
IF matrix = "单边突破" AND MBI 方向一致 → PULSATION_CONFIRM
IF matrix = "宽幅洗盘" → PULSATION_CAUTION (需 PVD/CD 交叉验证)
```

---

### 14.2 Module 2: Cross-Market Divergence

#### 14.2.1 PVD — Price-Volume Divergence (价量背离)

| 状态 | 条件 | Score |
|:---|:---|:---:|
| 真实推动 | 赔率降(升) + 必发量暴增(>2x) | +1.0 |
| 量在价先 | 赔率未变 + 必发量已暴增 | +1.0 |
| 虚假信号 | 赔率降(升) + 必发量萎缩/平平 | −1.0 |
| 散户驱动 | 赔率降 + 散户渠道量增 + 必发平平 | −0.5 |
| 无可比性 | 必发缺失或量极低 | 0.0 |

#### 14.2.2 CD — Channel Divergence (渠道背离)

| 状态 | 条件 | Score |
|:---|:---|:---:|
| 渠道背离 | Sharp 方向明确 + 大众反向 | +1.0 |
| 领先跟随 | Sharp 方向明确 + 大众同步 | +0.5 |
| 散户扎堆 | 大众集体朝一边 + Sharp 不明确 | −0.5 |
| 机构分歧 | Sharp 内部撕裂 | −1.0 |
| 无数据 | 大量博彩公司缺失 | 0.0 |

#### 14.2.3 MPC — Market Pressure Composite

```
MPC = 0.6 × PVD_Score + 0.4 × CD_Score

死区过滤: IF |MPC| < 0.2 → 乘数 = 1.0 (不修正)
IF 0.2 ≤ |MPC| < 0.5 → 最终信度 = 原信度 × (1 + MPC × 0.10)
IF MPC ≤ −0.5 → 触发 Veto 或 CB (见 14.3)
```

---

### 14.3 三级响应架构（永不翻转 MBI 方向判定）

#### 14.3.1 判定逻辑

```
IF MPC < −0.8:
  状态 = CIRCUIT_BREAKER
ELIF MPC < −0.5 AND TWQ_matrix IN [高频低幅, 宽幅洗盘]:
  状态 = CIRCUIT_BREAKER (双因子共振)
ELIF MPC < −0.5:
  状态 = VETO
ELIF |MPC| < 0.2:
  状态 = NORMAL (死区内)
ELSE:
  状态 = NORMAL (正常信度修正)
```

#### 14.3.2 各状态动作

| 状态 | 对 MBI 方向 | 对投注池 | 报告输出 |
|:---|:---|:---|:---|
| NORMAL (MPC>0) | 信度 × (1+MPC×0.10) | 正常进入 SOP | "积极" |
| NORMAL (MPC<0) | 信度 × (1+MPC×0.10) | 正常进入但降权 | "谨慎" |
| VETO | 方向保留(估值用) | 该场跳过投注 | "🚫 否决" |
| BREAKER | 方向保留 | 整场从候选池移除 | "🔴 熔断" |

#### 14.3.3 对 SOP 影响

Step 0.5 — 市场健康检查 (KB-14)，在 Step 1 之前执行。

---

### 14.4 回测指标
信息增益率 = Σ(Δ命中率)/触发场次 | MPC>0.3时提升≥3%→有效 | CB否决正确率≥60%→有效

---

### 14.5 默认参数（保守起步）

| 参数 | 缺省 | 说明 |
|:---|:---:|:---|
| MPC 幅度 | ×0.10 | 最大信度修正 ±10% |
| 死区 | \|MPC\|<0.2 | 过滤日常噪音 |
| CB 阈值 | MPC < −0.8 | 单因子熔断 |
| CB 共振 | MPC<−0.5 + TWQ异常 | 双因子共振熔断 |
| Veto 阈值 | MPC < −0.5 | 止付不禁估值 |
| TWQ 异常 | > 50 | 严重拉锯 |
| F 高频 | ≥ 0.4 | 振荡经验线 |
| D 低幅 | < 1.5% | 位移经验线 |
| ω₁/ω₂ | 0.6/0.4 | PVD/CD 权重 |

---

## KB-15: External Signal Injection (Roadmap)

> 未实现模块的优先级和量化规则。注: 赔率不是信息源，是庄家的风控工具。真正的 edge 在赔率之外。

### 15.1 首发伤停 (⭐⭐⭐)
```
赛前2h抓取→提取关键位置变化→对比赔率变动时间戳:
  赔率提前调整→市场已定价→无edge
  赔率未调整→市场未反应→真正edge
量化: 关键缺阵→logit -0.15 | 双核缺阵→-0.30 | 防线重组→对方+0.10
```

### 15.2 赛程体能 (⭐⭐)
```
7天3赛→x0.92 | 7天4赛→x0.85 | 双线→降1档 | 跨洲3h+→降1档
密集+弱旅→轮换高→穿盘降 | 密集+强敌→防守端受影响
```

### 15.3 天气场地 (⭐)
```
暴雨/大雪→偏小球 | >32°C→偏小球 | 大风→技术型受影响
人工草皮→客队-5% | 积水→长传队受益
```

### 优先级
| 信号 | 增益 | 代价 | 状态 |
|:---|:---:|:---:|:---|
| 首发 | 高 | 低 | 📋 |
| 体能 | 中 | 中 | 📋 |
| 天气 | 中低 | 中高 | 📋 |
| NLP | ⛔永久排除 | — | 🚫 |

---

## KB-16: Pin方向分箱准确率 — 179场跨赛事校准 (v3.9.0)

> **v3.9.0 跨赛事重校准**: WC2022(64) + EURO2024(51) + WC2018(64) = 179场。
> 废除 63.6% 单一基准（来自WC2026 44场偏估值）。替代为 54.7% 全量基线 + 7区间分箱表。
> 核心发现: Pin方向准确率在不同赔率区间差异极大——1.21-1.35区间达85.7%, 1.36-1.50区间仅40%。

### 16.1 Pin方向分箱准确率表 (179场, 3赛事)

```
赔率区间          场次   命中    准确率    95%CI        边际Edge   结论
─────────────────────────────────────────────────────────────────
超深热门 1.01-1.20   7     5    71.4%   [38%-100%]   -14.4%    样本过小
深热门 1.21-1.35    21    18    85.7%   [71%-100%]    +8.1%    🔥 最优区间
强热门 1.36-1.50    20     8    40.0%   [19%-62%]    -29.8%    🚫 死亡区间
中等 1.51-1.70      31    19    61.3%   [44%-78%]     -1.1%    接近有效
浅热门 1.71-2.00    37    19    51.4%   [35%-68%]     -2.8%    微负
弱优势 2.01-2.50    43    20    46.5%   [32%-61%]     +2.4%    微正
无优势 2.51+        20     9    45.0%   [23%-67%]     +7.2%    正但方差大
─────────────────────────────────────────────────────────────────
全量               179    98    54.7%   [47%-62%]     —        跨赛事基线
```

**边际Edge计算公式**: edge = 分箱准确率 − (1 / 分箱平均赔率)

### 16.2 分箱对方法论的影响

```
🔥 1.21-1.35 区间 (n=21, 85.7%):
  - 这是系统的甜蜜点。Pinnacle低赔率+深盘热门在跨赛事中极其可靠。
  - 单关edge = +8.1% → 可以独立下注。
  - 入串关: 匹配准确率85.7% → 作为"胆"的可靠性极高。
  - 德国SPF 1.33 (2026-06-20) 属于此区间 → 被旧公式误判为"不要投"。
  
🚫 1.36-1.50 区间 (n=20, 40.0%):
  - 死亡区间。赔率看起来是热门(~1.40)，实际胜率低于抛硬币。
  - edge = -29.8% → 绝对不要入串关。
  - 解释: 这个区间的球队被市场高估了——看起来强但实际不强。
  
⚖️ 1.51-2.00 区间 (n=68, 55.9%综合):
  - 市场接近有效, edge ≈ 0。
  - 入串关需严格筛选(偏离+离散+动机三重检查)。
```

### 16.3 Kelly公式升级 (v3.9.0)

```
旧公式: edge = 0.636 - (1/Pin赔率)  ← 误判1.21-1.35区间
新公式: edge = 分箱准确率 - (1/Pin赔率)  ← 查表得准确率

使用规则:
  1. 找到 Pin赔率所在区间 → 查表取 分箱准确率
  2. edge = 分箱准确率 - (1/实际赔率)  [注意: 投注用竞彩赔率]
  3. Kelly_fraction = max(0, edge / (odds - 1)) × 0.5
  4. 仓位硬上限: min(25%, Kelly_fraction)
  5. 单关最低: edge < +5% → ¥0 (仅入串关)
```

### 16.4 跨赛事稳定性

```
赛事         场次   Pin准确率   95%CI
─────────────────────────────────────
WC2018       64    59.4%      [47%-71%]
WC2022       64    53.1%      [41%-65%]
EURO2024     51    51.0%      [37%-65%]
─────────────────────────────────────
综合         179    54.7%      [47%-62%]
标准差        —     4.4pp      —
```

跨赛事波动在可接受范围内 (std 4.4pp)，分箱模式在三个赛事中方向一致：1.21-1.35 区间始终最高。

### 16.5 废除的旧内容

- 63.6% 单一基线 → 废除。替代为 54.7% + 7区间分箱。
- OCI五分位体系 → 已在 v3.7.0 废除，确认不再恢复。
- 单信号命中率表(44场) → 降为历史参考。主力用分箱表。

### 16.5 平局专项

```
Pinnacle 在 44 场中 0 次最低赔率是平局。
13场平局全部来自"强队对弱队但爆冷平"模式。
平局不能用赔率方向预测 → 需要独立模型。

平局触发条件 (暂用Step 9的五条):
  信号来源必须在赔率方向之外 (成交量异常/离散异常/动机冲突)
  触发≥3条 → 平局风险标记, 方向强制为"跳过"而非"D"
```

---

## KB-17: 平局专项模型 + 动机修正 (v3.7.1 WC48场校准)

> **v3.7.1**: 48场世界杯平局分析揭示三种结构模式。Pin 方向无法预测平局(Pin 0次平赔最低)。
> 平局不是"方向问题"，是"Pin 过信问题"。替代为 Pin 深度 + 动机 + 轮次三维分类。

### 17.1 平局三种结构模式 (WC48场实测)

```
类型A: 深盘慢热 (6/13)
  条件: Pin_H < 1.50 AND R1(首轮)
  逻辑: 强队首轮保存实力/磨合阵容, 不一定全力打穿
  案例: 西班牙 0-0 佛得角(Pin=1.11), 葡萄牙 1-1 民主刚果(Pin=1.30)
  平局率: 首轮深盘球队7场中4场平局(57%)

类型B: 深盘动机流失 (3/13)  
  条件: Pin_H < 1.50 AND (主队已出线 OR 主队已淘汰) AND Pin方向方 mot <0.25
  逻辑: Pin方向方的球队没有动力全力争胜。强队轮换, 弱队无欲无求
  案例: 英格兰 0-0 加纳, 比利时 0-0 伊朗

类型C: 均衡对耗 (4/13)
  条件: Pin在 1.80~2.20 AND 双方动机差 <0.15
  逻辑: 实力接近 + 动力相近 → 平局是双方都接受的中间结果
  案例: 荷兰 2-2 日本, 伊朗 2-2 新西兰, 沙特 1-1 乌拉圭
```

### 17.2 动机修正 — 量化执行算法 (v3.9.0 重写)

> **v3.9.0**: 废除 AI 主观定性判断。mot 值从 Step 2 的 ELO 差距 + 小组积分榜 + 剩余赛程 **自动计算**, 四条规则全部可回测。

#### 17.2.1 对阵轮次判定 (R1/R2/R3)

```
判定逻辑:
  如果同组多场比赛在同一日期+时间开球 → R3 (小组末轮)
  否则:
    球队已完成的同组比赛数 = 0 → R1
    球队已完成的同组比赛数 = 1 → R2
    球队已完成的同组比赛数 ≥ 2 → R3

数据源: Liansai API (已含所有场次比分+日期)
```

#### 17.2.2 动机分数计算公式

> **⚠️ 数据源**: base_situation 必须从积分榜字典取值, 禁止 AI 凭记忆编造。
> 积分榜获取: WebFetch `https://liansai.500.com/zuqiu-19476/jifen-26226/`
> 完整协议: `references/fundamentals/standings-protocol.md`

```
mot = base_situation + elo_adjust + rest_adjust

base_situation (从小组积分榜 + 剩余赛程判定, 取最高匹配):

  场景                               base_situation
  ──────────────────────────────────────────────
  R3, 积分=0, 必须赢才能出线         0.90  (生死战)
  R3, 积分=1~2, 赢=出线 平/输=淘汰   0.85  (出线争夺·赢即出线)
  R3, 积分=3~4, 平局=出线            0.40  (平局即出线·保守)
  R3, 积分=4~6, 已锁定出线            0.20  (已出线·可轮换)
  R3, 积分=0~1, 已确定淘汰            0.15  (已淘汰·无动力)
  R2, 积分=0, 输=大概率淘汰           0.85  (背水一战)
  R2, 积分=3, 赢=提前出线             0.80  (赢即出线)
  R2, 积分=0~1, 争出线                0.70  (争夺中)
  R2, 积分=4~6, 基本锁定             0.35  (已安全·可放松)
  R1, 任何积分                        0.70  (首轮等动力)
  淘汰赛阶段                          0.95  (淘汰赛·最高动力)

elo_adjust:
  主队ELO − 客队ELO (从 team_strength.json 查表):
    ELO差 > 100 → 弱队方 mot +0.05 (弱队更有动力证明自己)
    ELO差 ≤ 100 → 0

rest_adjust:
  距上一场比赛间隔 (从 Liansai API 匹配日期计算):
    休息 < 3天 → −0.05 (体能紧张影响动力)
    休息 ≥ 3天 → 0

mot 取值区间: [0.15, 1.00]
两队的 mot 分别独立计算
```

#### 17.2.3 动机判定

```
输入: 主队 mot, 客队 mot
计算: mot_gap = |主队 mot − 客队 mot|
      Pin方向方 = Pin收盘赔率最低的那一方 (H/D/A)

mot 与 Pin 的关系:
  Pin方向方 mot ≥ 0.70 → ✓ 共鸣 (Pin可靠, 不加不减)
  Pin方向方 mot < 0.25 → ✗ 反向冲突
  mot_gap < 0.15 → ~ 中立 (双方动力接近, 不影响 Pin)
  mot_gap > 0.30 → → 动机分化

历史验证 (WC48场):
  mot×Pin 同向 (共鸣): Pin 准确率维持基线 (~54.7%)
  mot×Pin 反向 (冲突): 6场, Pin 方向输 4 场 (33.3%)
  → 冲突是 Pin 方向最强的否定信号
```

#### 17.2.4 四规则 (使用可计算输入)

```
规则1 (深盘慢热 — 首轮):
  Pin_H < 1.50 AND 主队 R1 → draw risk HIGH
  Pin_A < 1.50 AND 客队 R1 → draw risk MEDIUM
  数据: 首轮深盘球队 7 场中 4 场平局 (57%)
  动作: Pin方向标记为"跳过"
  例外 (v3.8.2 O-15 观察项): 
    若同时满足 30家共识≥80% + 离散≤25 + 同向升盘 → 降为"候选"(0.5x), 标记"死亡区间信号豁免"

规则2 (深盘动机流失):
  Pin方赔率 < 1.50 AND Pin方向方 mot < 0.25 → draw risk VERY HIGH
  数据: 动机流失深盘场 3/13 (WC48场), 均在 R3
  动作: 强制"跳过"
  若对手赔率 ≥ 3.0 AND KB-17b 反投条件 1-4 全满足 → 可选反投对手单关 ¥10
  二层验证 (v3.8.2): 
    若竞彩赔率显著低于 Pinnacle (价差>10%) → 不跳过, 降为"候选"(0.5x), 标记"动机待确认"
  注意: 看 Pin方向方的 mot, 不是主队的 mot

规则3 (均衡对耗 — 平局偏向):
  Pin ∈ [1.80, 2.20] AND mot_gap < 0.15 → draw risk MEDIUM
  数据: 均衡对耗 4/13 (WC48场)
  动作: 仓位降 0.5x

规则4 (生死战 — Pin 可靠):
  Pin_H < 1.50 AND 主队 R3 AND 主队 mot ≥ 0.85 → draw risk LOW
  数据: 末轮生死战胜率高于基线 (样本小)
  动作: 正常 Pin 方向, 规则1/2 不触发 (规则4 优先级最高)
```

#### 17.2.5 规则优先级

```
规则触发冲突时的优先级 (从高到低):
  1. 规则4 (生死战覆盖规则1/2)
  2. 规则2 (动机流失 > 规则1 慢热)
  3. 规则1 (深盘慢热)
  4. 规则3 (均衡对耗, 仅降仓不跳过)

同时触发多条时: 取最高优先级的动作
```

### 17.3 平局信号检查 (分级体系, v3.8.1)

> **v3.8.1**: 信号分级替代等权计数。一级信号(相对变化)单条触发即降仓，二级信号(绝对值阈值)维持原有计数逻辑。

```
一级信号 (单条触发即生效 — 相对变化比绝对值更灵敏):
  0. Pinnacle平赔较开盘降幅 ≥ 20%
     逻辑: 平赔大幅下降 = 市场对平局的担忧在急剧上升
     来源: 回测#20260624 英格兰0-0加纳 — 平赔-33%但绝对值5.21>3.20未被原信号1捕获
     动作: 单条触发 → 仓位降0.5x + 该场不得作为"胆"
     触发2条一级信号 → 强制"跳过"

二级信号 (绝对值阈值, 维持原有≥3条计数):
  1. Pinnacle平赔即时<3.20 且 较开盘下降
  2. 30家离散度: 平局离散 ≤ min(主胜离散, 客胜离散)  
  3. 亚盘即时盘口 = 平手盘 (handicap=0)
  4. deVig去抽水后平局概率 > 28%
  5. 必发成交量: draw_pct > 15% 或 draw_PL正值

二级信号触发≥3条 AND 没有规则4(生死战) → 方向"跳过"
一级信号与二级信号独立并行检查, 重叠触发取更严动作
与17.2的四规则独立并行检查
```

### 17.4 废除的DRM规则

- DRM-1/2/3/7 全部废除。替代为 17.1 三种模式 + 17.2 四规则。
- DRM打分体系 → 废除。不再按分计。

---

## KB-17b: 动机计算 + 反投框架 (v3.9.0 更新)

### 动机计算

> **v3.9.0**: mot 计算已升级为可执行算法。见 17.2.2 动机分数计算公式。
> 下文 mot 值直接引用 17.2.2 的输出结果。

```
mot_gap = |主队mot − 客队mot|
mot方向: mot 更高的那一边
```

### 反投触发条件

```
反投 = 不跟Pin + 赌对手方向

需同时满足四个条件 (缺一不可):

  1. Pin方向 ≠ 平局 (赔率最低方向是H或A)
  
  2. 动机-Pin冲突: mot方向 ≠ Pin方向 AND mot_gap > 0.30
     数据: 冲突场次中Pin准确率降至33%(vs 全量基线54.7%)

  3. 偏离信号 ≥ 2条 (KB-19)
     从正常的≥3条降至≥2条 — 动机已提供替代方向, 门槛可降低

  4. 对手赔率在 2.00~6.00 区间
     赔率<2.00 → 市场也认同对手, 不是"反投"
     赔率>6.00 → 概率太低, 风险不可控
     赔率在2.00-6.00 → 中等或偏冷门, 反投有正EV

当前状态: ACTIVE
  可用范围: R3(末轮)且动机分化的比赛
  不可用: R1首轮(双方等动力, 无冲突可检测)


---

## KB-18: 仓位分配 + 串关资格 → 见 betting-sop.md

> **v3.7.0**: 仓位由Pinnacle方向+离散收敛组合决定。详见 betting-sop.md。

## KB-19: 偏离检测 — 否定信号 (v3.7.0 校准)

> **v3.7.0 重写**: 偏离信号不再是冷门翻转的触发器，而是用于**撤销**Pin方向的信号。
> 废除主观赛事标签。全部基于可测量市场数据。

### 19.1 偏离信号 (6条)

```
以下信号出现时, Pin方向可靠性下降:

1. Pin方向热门赔率升水 >5%
2. 必发成交量方向  != Pin方向 (量价背离)
3. Kelly指数 > 1.05 (Pin方向过热)
4. 竞彩-Pinnacle gap > 8% (机构间严重分歧)
5. 30家离散度较开盘上升 >20% (发散)
6. 让球升盘≥0.5球但大小球不动
7. Pin方向离散度绝对值 > 25 (原始值, 非DRI校准值, v3.8.1)
   → 即使较开盘未明显上升, 绝对值偏高 = 30家公司对Pin方向意见分裂
   → 与信号#5(上升>20%)独立计数, 两者可同时触发

触发规则:
  偏离信号 ≥ 3条 → 方向强制为"跳过"
  偏离信号 = 2条 → 仓位降为 0.5x
  偏离信号 ≤ 1条 → 正常
```
  例: 开盘1.50 -> 收盘1.58 = 升水5.3% -> 偏离触发

偏离信号2: 量价背离
  测量: 成交量集中度 vs 赔率方向
  客观数据: touzhu页面必发成交占比
  条件: 某方成交>70% + 该方赔率未降/反升 -> 偏离触发

偏离信号3: 市场分歧
  测量: 30家均值方向 vs Pinnacle方向
  客观数据: 30家closing均值 vs Pinnacle closing
  条件: 均值与Pinnacle方向相反 -> 偏离触发

偏离信号4: 平局偏高
  测量: deVig(平) 绝对值
  客观数据: Pinnacle de-vig概率
  条件: >28% -> 偏离触发 (平局偏向)

偏离信号5: OU线下调
  测量: 大小球线移动
  条件: 6h内OU下调>=0.25 -> 偏离触发 (进球少)
```

### 19.2 综合判断（v3.5.2: 抬高触发门槛）

```
  偏离计数 0-2: 无翻转, 正常执行仓位规则(见betting-sop.md)
    依据: 179场回测中偏离≥2触发翻转仅53.8%, 抬高到≥3减少伪信号

  偏离计数 >=3: 强偏离, 确认冷门翻转
    动作: 反转系统方向 + 仅押单关

  翻转方向判断:
    deVig(平) > 28% + OU下调 -> 押平局
    量价背离 + 升水 -> 押反方向
    市场分歧 + 升水 -> 押反方向
```## KB-20: 跨赛事回测验证 → 用 football-backtest-workflow

> 回测验证框架已统一由 `football-backtest-workflow/` 子技能处理。
> 详见 analyst SKILL.md Step 13 赛后回测触发器。旧版 postmortem.md 已删除。

## KB-20a: 数据聚合层 — 11信号引擎 (v3.8.0 新增)

> **v3.8.0**: 废除零散手工提取，替代为从6页全量JSON计算的10个聚合信号。
> 数据源: ouzhi(30家SPF+凯利+概率)/yazhi(17家AH)/daxiao(18家OU)/touzhu(必发)/rangqiu(16家让球)

### 10信号速查

```
信号1: Kelly共识方向 (ouzhi 30家凯利均值)
  计算: avg(Kelly_h, Kelly_d, Kelly_a) across 30 bookmakers
  最小Kelly均值方向 = 30家共识认为最有价值的方向
  ⚠️ 共识方向准确率仅34.1%, 只用作Pin方向分歧检测, 不替代Pin

信号2: 离散度梯度 (ouzhi 30家CV变化)
  计算: CV_current vs CV_open → converging/diverging/stable
  converging=离散在收窄≈共识形成 → Pin可靠度提升
  diverging=离散在扩大≈分歧加剧 → Pin可靠度下降

信号3: 返还率标准差 (ouzhi 30家return rate)
  计算: stdev(30家return_current_pct)
  标准差>2.5 → 有博彩公司抽额外水 → 市场不健康 → 跳过

信号4: 亚盘共识 (yazhi 17家水位)
  计算: mean(17家home_water, away_water)
  主场水位<客场→机构看好主队, 反之看好客队
  水位std>0.15→机构间分歧大→信号不可靠

信号5: 大小球共识 (daxiao 18家OU水)
  计算: mean(18家over_water, under_water)
  OU水位比=over_w/under_w → <1=高进球预期, >1=低进球预期
  → 比分预测的λ先验输入

信号6: 必发热冷共识 (touzhu hot_cold/pl/volume)
  计算: hot_cold方向 vs pl_index方向
  同向→热度真实, 反向→庄家诱导
  volume_ratio_pct>55%→H方向, <45%→A方向

信号7: 大额交易比 (touzhu large_trade/volume)
  大额/总成交>5%→大户活跃, 方向有参考价值

信号8: 让球深度 (rangqiu 16家handicap)
  计算: mode(16家让球数)
  让球越深(>1.5)→市场越看好Pin方向, 期望净胜球增加
  → 比分预测的λ非对称输入

信号9: 庄家PL暴露 (touzhu bookmaker_pl)
  每方向PL绝对值最大的方向=庄家最不希望的结果
  用作反向参考(有限), 不替代Pin方向

信号10: 公司异常检测 (ouzhi 30家z-score)
  计算: z_h = abs(home_odds - mean) / std
  z>2.0→某家公司独立大幅偏离→标记, 检查其动机
  count≥3→市场操纵风险→强制跳过
```

### 使用规则

```
仅做方向判定时: Pin方向(54.7%全量基线, 分箱见KB-16) + 信号2(离散度) + 信号6(必发方向)
仅做比分预测时: 信号5(OU) + 信号8(让球深度) + 信号6(成交量分布)
仅做反投判断时: 信号1(Kelly共识≠Pin) + 信号3(返还率异常) + 信号9(PL暴露) + 信号11(交易流水)
仅做胆识别时:   Pin方向 + 信号1(同向) + 信号2(收敛) + 信号6(一致)
```

信号11: 模拟盈亏交易流水 (touzhu 页 模拟盈亏 section, v3.8.0)
```
来源: touzhu 页 模拟盈亏表格 — 逐笔买/卖交易记录
  每行: [方向(主/客/平), 买卖(买/卖), 成交量, 交易时间, 比例%]
  买=庄家买入该方向筹码(对冲风险/不看好)
  卖=庄家卖出该方向筹码(承接投注/不担心赔付)

分析方法:
  净流向 = 总买入量 - 总卖出量
  净流向<0(卖出>买入) → 庄家在收筹码 → 不担心该方向赔付 → 反向利好
  净流向>0(买入>卖出) → 庄家在抛筹码 → 想对冲该方向风险 → 庄家担忧

  按方向拆分:
    主胜net<0 + 客平net>0 → 庄家看好主胜
    主胜net>0 + 客胜net<0 → 庄家看好客胜  
    平局net<0 + 主客net>0 → 庄家担心平局赔付

  用途: 与信号9(PL暴露)交叉验证
    PL暴露 + 交易流水同向 → 信号增强
    PL暴露 vs 交易流水反向 → 庄家有操作(可能在诱盘) → 反投条件之一
```

## KB-21: 比分预测引擎 (v3.8.0 新增)

> **v3.8.0**: 废除免责声明式"仅供参考"比分。替代为市场隐含的Poisson+OU+让球三位一体的量化预测。
> 验证: WC48场 Top3命中率25.0%, 精确命中15.9% (3.3x随机基线)

### 四步计算

```
步骤1: 期望总进球 λ_total
  输入: 信号5 OU共识 (over_water/under_water比)
  λ_base = 2.5 + (1 - ratio) × 1.5  (capped [1.2, 4.5])
  
步骤2: 非对称拆分 λ_h, λ_a
  输入: 信号8 让球深度
  depth = |handicap_mode| × 0.2
  λ_h = λ_base × (0.55 + depth/2)
  λ_a = λ_base × (0.45 - depth/2)  
  → 若让球-2: λ_h=65% λ_a=35% (主队更可能进球)

步骤3: Poisson概率矩阵
  对 h, a ∈ [0, 6]:
    P(h,a) = Poisson(λ_h, h) × Poisson(λ_a, a)
  归一化 → Top N 比分按概率排序

步骤4: 必发成交量校准 (可选)
  输入: 信号6 成交量方向
  若 volume_ratio > 60%H → λ_h += 0.1, λ_a -= 0.05
  若 volume_ratio < 40%H → λ_h -= 0.1, λ_a += 0.05
```

### 输出格式

```
比分预测:
  1. X-X  (概率 Y.Y%) ← 最可能比分
  2. X-X  (概率 Y.Y%)
  3. X-X  (概率 Y.Y%)
  
  期望总进球: X.X球  (市场共识: X.X)
  进球倾向: 偏大球/偏小球/中性  (置信度: [基于OU水位差])
  
  校准依据: WC48场 Top3=25.0% / Exact=15.9% / Brier=0.XX
```

