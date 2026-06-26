# 小组积分榜获取协议 v2.0

> **P0 铁律**: 任何有小组赛的赛事，必须先获取积分榜才能计算 mot。积分错误 = mot 错误 = 方向判定错误。
> **适用范围**: 世界杯、欧洲杯、非洲杯、亚洲杯、美洲杯、欧冠小组赛、任何含小组赛阶段的赛事。
> **核心原则**: 主源抓取 + 搜索引擎交叉验证 + 四道数学验证。三重保障下才允许 mot 计算。

---

## 一、适用判定

```
执行 Step 0a 时，检查当前赛事是否含小组赛:
  - 世界杯/欧洲杯/非洲杯/亚洲杯/美洲杯 → 必有小组赛
  - Liansai API 返回的 match_list 中含"小组赛"/"分组赛"/"Group"字样 → 必有小组赛
  - 不确定 → 默认按有小组赛处理 (宁可多验证不少验证)

判定为有小组赛 → 强制执行本协议全部步骤
```

---

## 二、主数据源: 500.com 积分页

### 2.1 URL 构造

```
积分页 URL 模式:
  https://liansai.500.com/zuqiu-{sid}/jifen-{jid}/

获取 sid 和 jid:
  方法 A (推荐): 从 Liansai API 返回的 URL 或已知常量取 sid
    世界杯 2026: sid=19476, jid=26226
    其他赛事: 打开 https://liansai.500.com/ → 找到目标赛事 → 从 URL 提取 sid
             然后打开赛事主页 https://liansai.500.com/zuqiu-{sid}/ 
             → 找到"积分榜"链接 → 从 URL 提取 jid

  方法 B (后备): 
    WebFetch https://liansai.500.com/zuqiu-{sid}/
    从页面中提取"积分榜"链接的完整 URL
```

### 2.2 抓取与提取

```
WebFetch https://liansai.500.com/zuqiu-{sid}/jifen-{jid}/

提取每个小组的全部球队的以下字段:
  排名, 球队名, 已赛场数(P), 胜(W), 平(D), 负(L), 
  进球(GF), 失球(GA), 净胜球(GD), 积分(pts)

构建 standings 字典:
{
  "Germany":     {"group": "E", "P": 2, "W": 2, "D": 0, "L": 0, "GF": 9, "GA": 2, "GD": +7, "pts": 6, "rank": 1},
  ...
}
```

---

## 三、数学自检 (所有数据源通用)

```
每支球队逐一验证 (四道):
  □ W + D + L = P              (胜平负和=已赛场次)
  □ GF − GA = GD               (进球差=净胜球)
  □ pts = W × 3 + D × 1        (积分=胜×3+平×1)
  □ 同组 4 队的 P 差 ≤ 1       (全组场次一致或差1场)

全部通过 → 进入交叉验证
任一失败 → STANDINGS_INVALID, 整场 mot 禁止计算
```

---

## 四、搜索引擎交叉验证 (强制)

```
使用 WebSearch 搜索 "[赛事名称] [球队名] group standings points 2026"
或 "[赛事名称] 小组积分榜"

多源对照:
  - Wikipedia 赛事页面 (通常有完整积分榜)
  - FIFA/UEFA/CAF 等官方机构网站
  - ESPN/BBC/Sports Illustrated 等权威体育媒体
  
对照维度:
  □ 每队 pts (积分) — 主源与搜索结果必须一致
  □ 每队 P (已赛场次) — 必须一致
  □ 小组排名顺序 — 如搜索结果含排名，对照

一致场次 ≥ 80% → 通过, 标记 STANDINGS_VERIFIED
一致场次 < 80% → 人工检查, 标记 STANDINGS_DISCREPANCY

⚠️ WebSearch 返回的积分可能与 500.com 有 1 场的延迟
   如发现差异, 以 500.com 为主 (500.com 更新更频繁)
   但记录差异作为"验证标记"
```

---

## 五、缓存策略

```
standings 数据有时效性:
  - 比赛日之内: standings 在每场结束后更新
  - 策略: 每次执行分析时重新抓取 (缓存 ≤ 1h)
  - 抓取时间戳 + 数据源 URL 必须记录
  - 如果抓取失败 (网站不可用), 回退到 WebSearch 结果
```

---

## 六、在 mot 计算中的使用

```
KB-17.2.2 base_situation 的所有判定基于 standings 字典:

  判断"已出线": 
    当前积分 + 剩余可获积分 > 第3名理论最高积分 → 数学锁定
  
  判断"已淘汰":
    当前积分 + 剩余可获积分 < 第2名当前积分 → 数学淘汰
  
  判断"生死战":
    R3 + 赢=出线且输/平=淘汰
  
  判断"平局即出线":
    平局积分 ≥ 第3名理论最高积分且输球积分 < 第3名理论最高积分

  ⚠️ 以上所有判定必须基于 standings 字典的实际数据计算
  ⚠️ 禁止 AI 凭记忆或推理编造积分——只从 standings 字典取值
  ⚠️ standings 未经过四验证 + 交叉验证 → 不得用于 mot 计算
```

---

## 七、常见错误预防

```
错误类型 1: AI 凭比赛结果倒推积分
  ✗ 看到"科特迪瓦 2-0 胜某队"就假设科特迪瓦 3 分
  ✓ 从 standings 字典查: Ivory Coast.pts

错误类型 2: 积分与净胜球混淆
  ✗ 看到德国"进球 9"就推断"肯定小组第一"
  ✓ 从 standings 字典同时查: Germany.pts + Germany.GD + Germany.group 排名

错误类型 3: 忽略同分净胜球
  ✗ 同组两队同分就认为"并列第一"
  ✓ 查 standings 的排名列 (500.com 已按净胜球排好)

错误类型 4: 跨组混淆
  ✗ 把 A 组的积分用到 E 组的比赛
  ✓ 先确认两队的 group 字段一致, 再取组内其他队数据

错误类型 5: 未验证直接使用
  ✗ 抓到了 standings 就直接算 mot
  ✓ 必须先跑四验证 + WebSearch 交叉对照
```

---

## 八、输出格式

```
Step 0a 积分榜验证报告:
  数据源: liansai.500.com/zuqiu-{sid}/jifen-{jid}/ (主)
           WebSearch "[赛事] 小组积分" (交叉)
  四验证: ✅ 全部通过 / ❌ [X/Y/Z] 项失败
  交叉验证: ✅ 一致 / ⚠️ [X] 场差异 [说明] / ❌ 严重不符
  状态: STANDINGS_VERIFIED / STANDINGS_DISCREPANCY / STANDINGS_INVALID
  时间戳: 2026-06-25T20:30+08
```
