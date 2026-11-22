# 17 · KPI 对比与指标切换

> 适用版本：1.6.0+　｜　相关：`kpi`、`switch`、`bar` 的 `yoy`、[06 多图联动](06-interaction.md)

一张经营看板通常要回答三个问题：**现在多少**、**比去年好还是差**、**换个口径（销售额/销量/应收）怎么样**。
1.6 之前这三件事分别要靠：先筛数据再画 KPI、手填 `delta=`、给每种口径单独做一页。1.6 把三件事都做成参数。

---

## 1. 动态同比：`compare=`

### 1.1 最小可用

```python
import pandas as pd
import eazy_data_viz as edv

df = pd.DataFrame({
    "年": ["2026年", "2026年", "2026年", "2025年", "2025年", "2025年"],
    "月": ["1月", "2月", "3月", "1月", "2月", "3月"],
    "金额": [130, 90, 96, 100, 120, 80],
})

chart = edv.kpi(df, value="金额", label="销售额", spark="金额", spark_x="月",
                compare={"年": ["2026年", "2025年"]})
print(chart.spec["compare"]["static"])
# {'cur': 316.0, 'base': 300.0, 'rate': 0.0533…, 'mom': {'cur': 96.0, 'base': 90.0, 'rate': 0.0666…}}
```

卡片上会出现：

```
销售额
316        ▲ +5.3% 同比
[2026年 316] [2025年 300] [环比]
▁▂▃▅▆▇   ← 迷你走势
```

* 点 `2025年` → 主数字换成基期（300），chips 里高亮跟着换；
* 点 `环比` → 增长率换成「最后一期 vs 上一期」（96 vs 90）；
* 再点一次回到默认。

### 1.2 字典里的四个键

| 键 | 取值 | 默认 | 说明 |
|---|---|---|---|
| 列名 | `["本期取值", "基期取值"]` | 必填 | 例如 `"年": ["2026年", "2025年"]` |
| `show` | `"value"` / `"rate"` / `"both"` | `"both"` | 主数字显示数值还是增长率 |
| `mode` | `"yoy"` / `"mom"` | `"yoy"` | 同比（两组取值）/ 环比（最后两期） |
| `period` | 列名 | 取 `spark_x` | 同期对齐与环比分期都用它 |
| `base_label` | 字符串 | 基期取值本身 | 基期 chip 上显示的名字 |

### 1.3 「同期对齐」为什么重要

2026 年只有 1–8 月的数据，2025 年有整年。直接比总量，2026 永远输。`compare` 只比**本期已有的期**：

```python
df["月"] = pd.Categorical(df["月"], ["1月", "2月", "3月"])
chart = edv.kpi(df, value="金额", spark_x="月", compare={"年": ["2026年", "2025年"]})
print(chart.spec["compare"]["static"]["base"])   # 只累计 1–3 月 → 300，而不是整年
```

### 1.4 去年为空 / 为 0 / 为负

| 情况 | 显示 | 为什么 |
|---|---|---|
| 基期没有数据 | 「新增」 | 从 0 到有，增长率没有意义 |
| 基期 = 0，本期 > 0 | 「新增」 | 同上（除零） |
| 基期 = 0，本期 = 0 | `—` | 没有信息 |
| 基期 < 0（例如利润 -100 → -50） | `+50%` | 分母取绝对值，方向不会反 |

### 1.5 联动之后会重算

这是把数字交给前端算的核心好处：点别的图筛选「渠道 = 直销」，KPI 会拿**过滤后的行**重算本期、基期、同比、环比四个数。
以前「先 `df[df["年"]=="2026年"]` 再画 KPI」的做法，联动一变，卡片还停在没筛过的静态值上。

### 1.6 和 `delta=` 的关系

`compare` 与 `delta` 同时传时**以 compare 为准**，并在 `chart.warnings["warnings"]` 里提示一句。
静态数字（`kpi(42)`）不能配 compare，会直接报错。

---

## 2. 指标切换：`edv.switch(...)`

### 2.1 一个 switch，全看板跟着切

```python
amount = edv.switch(sale="金额", qty="数量", balance="余额")

edv.show(
    edv.kpi(df, value=amount, label="销售额", metric="sale", spark="金额", spark_x="月"),
    edv.bar(df, x="月", y=amount),
    edv.pie(df, names="大区", values=amount),
    cols=3, title="经营看板", card_style="glass")
```

点第一张卡片上的「数量」chip：三张图一起换成数量口径。**纯前端**，不触发 Python 重跑。

### 2.2 哪些参数能接

任何列名角色：`x` / `y` / `y2` / `color` / `size` / `names` / `values` / `value` / `path`（单个）/ `source` / `target` / `spark` …

```python
edv.bar(df, x="月", y=edv.switch(sale="金额", qty="数量"))
edv.pie(df, names="大区", values=edv.switch(sale="金额", qty="数量"))
edv.kpi(df, value=edv.switch(cust="客户名称", order="订单号"), agg="unique", spark_x="月")
```

### 2.3 想固定某张图

那张图别传 switch，传具体列名即可 —— 它就不会跟着切。

### 2.4 类型要一致

同组 switch 的列要同类（都数值或都文本）。数值图切到文本列会画不出来；文本类指标配 `agg="count"` / `"unique"`。

---

## 3. 卡片外框：`card_style`

1.6 起默认 `"plain"`（透明、无边框），把页面底色让出来。

```python
edv.show(a, b, c, card_style="card")    # 旧样式：实心白卡
edv.show(a, b, c, card_style="glass")   # 液态玻璃：半透明 + 背景模糊
```

| 取值 | 别名 | 效果 |
|---|---|---|
| `"plain"`（默认） | `transparent` / `透明` / `无框` | 透明，页面底色直接透上来 |
| `"card"` | `default` / `solid` / `实心` | 实心白卡 |
| `"glass"` | `liquid` / `液态玻璃` / `玻璃` | 半透明渐变 + 毛玻璃 + 高光边 |

---

## 4. 完整例子（Streamlit）

```python
import streamlit as st
import eazy_data_viz as edv

@edv.cached
def read_data():
    ...  # 返回 年/月/组织名称/渠道/物料名称/金额/数量/余额 的明细

df = read_data()
amount = edv.switch(sale="金额", qty="数量", balance="余额")

st.plotly = None  # 占位，忽略
edv.streamlit_dashboard(
    edv.kpi(df, value=amount, label="销售额", metric="sale", spark="金额", spark_x="月",
            compare={"年": ["2026年", "2025年"]}, abs_height=110, link="q1"),
    edv.kpi(df, value=amount, label="应收余额", metric="balance", link="q1"),
    edv.bar(df, x="月", y=amount, color="年", link="q1", sort="年-月"),
    edv.sunburst(df, path=["渠道", "年"], value=amount, link="q1"),
    cols=2, card_style="glass", palette="tableau")
```

点柱状图的「1月」→ 两张 KPI 的同比、环比、基期全部按 1 月重算。

---

## 5. 常见问题

**Q1. 为什么同比方向反了？**

老版本 `yoy=True` 靠「系列合计大者为本期」判断，年份不完整时会反。1.6 的 `compare` 直接指定本期/基期，没有这个问题；
`bar(yoy=True)` 也已按「名字里的数字」判断（2026 > 2025）。

**Q2. `compare` 和「先筛数据」冲突吗？**

冲突。传 compare 时**不要**把数据筛到本期，否则基期是空的。把完整数据交给它。

**Q3. 环比只有一个期怎么办？**

不足两期时不出「环比」chip，主数字仍是本期值。

**Q4. 指标切换后联动还在吗？**

在。切换只换「用哪一列」，联动过滤、下钻路径、compare 全都不受影响。

**Q5. 能不能只让一张 KPI 跟着切换？**

可以，只在那张卡上写 `metric=`；其它图不传 switch 就不会动。

---

下一篇：[12 图表选型速查](10-chart-selection.md)　｜　上一篇：[16 自由排列](16-layout.md)
