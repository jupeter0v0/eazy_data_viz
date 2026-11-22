# 17 · KPI 对比、卡片选择器与指标跟随

> 适用版本：1.6.1+　｜　相关：`kpi` 的 `compare=` / `metric=`、`follow()`、`column()`、
>`bar` 的 `yoy`、[06 多图联动](06-interaction.md)

做经营看板时常见的三个诉求：

1. **同比 / 环比要现算**，而且要跟着联动一起变——不能每次先在 pandas 里筛好再传进来；
2. **一张 KPI 卡片就是一个按钮**：点「销售额」全看板看金额，点「客户数」全看板看去重客户数；
3. **每列怎么汇总，最好只声明一次**，不要每张图都写 `agg=`。

这三件事分别由 `compare=`、`metric=` + `edv.follow()`、`edv.column(...)` 负责。

---

## 1. 动态同比：`compare=`

### 1.1 最小写法

```python
edv.kpi(
    df, value="金额", label="销售额",
    spark="金额", spark_x="月",
    compare={"年": ["2026年", "2025年"]},
)
```

含义：在 `年` 这一列里，`2026年` 是本期、`2025年` **是上期**；卡片主数字显示本期合计，
旁边标注同比增速。上下期是**同期对齐**的：本期只有 1–8 月，上期也只取 1–8 月，
不会拿「8 个月的 2026」去比「12 个月的 2025」。

### 1.2 完整参数

| 键 | 取值 | 默认 | 说明 |
|---|---|---|---|
| `列名` | `[本期值, 上期值]` | — | 必填；只能用**一个**数据列做对比 |
| `show` | `"value"` / `"rate"` / `"both"` | `"both"` | 显示本期值、增速，还是两个都显示 |
| `mode` | `"yoy"` / `"mom"` | `"yoy"` | 同比（本期 vs 上期）或环比（最后一期 vs 上一期） |
| `period` | 列名 | 有 `spark_x` 就用 `spark_x` | 判断「期」的列，决定同期对齐与环比 |
| `base_label` | 字符串 | 上期取值本身 | 上期的显示名，例如 `"去年同期"` |
| `label` | 字符串 | `"同比"` / `"环比"` | 增速标签 |

```python
edv.kpi(df, value="金额", compare={"年": ["2026年", "2025年"], "show": "rate", "mode": "yoy"})
edv.kpi(df, value="金额", compare={"年": ["2026年", "2025年"], "mode": "mom", "period": "月"})
```

### 1.3 上期为空 / 为 0 / 为负数的规则

| 情况 | 显示 | 说明 |
|---|---|---|
| 上期没有数据 | `新增`（本期 > 0）或 `—` | 不显示无穷大，也不显示 100% |
| 上期为 0 | `—`，本期 > 0 时显示 `新增` | 0 做分母没有意义，直接不给数字 |
| 上期为负 | 照常算，分母取绝对值 | 例如上期 -100 → 本期 -50，显示 `+50.0%`（减亏一半） |
| 本期为空 | `—` | 没有本期就没有增速 |
| 不足两期（环比） | 不显示环比 | 数据只有一期时无法环比 |

### 1.4 联动之后会重算吗

会。`compare` 的数值是在**浏览器里**用当前筛选结果现算的：点了别的图的某个类目，
KPI 卡片上的本期值、上期值、增速会一起重算，不需要 Python 重跑。

### 1.5 不要提前筛数据

```python
# ✗ 错：基期被你筛掉了，compare 永远算不出同比
edv.kpi(df[df["年"] == "2026年"], value="金额", compare={"年": ["2026年", "2025年"]})

# ✓ 对：传完整数据，compare 自己切本期 / 上期
edv.kpi(df, value="金额", compare={"年": ["2026年", "2025年"]})
```

报错里也会提示这句：「如果你已经把数据筛到本期，请改传未筛选的完整数据——compare 会自己切本期/基期。」

---

## 2. 卡片 = 选择器：`metric=` + `edv.follow()`

### 2.1 思路

KPI 卡片本身就是个按钮。给它一个标识 `metric="sale"`，点它就等于「选中销售额这个口径」；
其它图表在度量位置写 `edv.follow()`，表示「我的这根柱子跟着选中的卡走」。

```python
edv.column(金额="sum", 客户名称="unique")   # 可选：声明每列怎么汇总

edv.show(
    edv.kpi(df, value="金额", metric="sale", label="销售额", spark="金额", spark_x="月"),
    edv.kpi(df, value="客户名称", metric="cust", label="客户数"),
    edv.kpi(df, value="余额", metric="bal", label="应收余额"),
    edv.bar(df, x="月", y=edv.follow()),
    edv.pie(df, names="大区", values=edv.follow()),
    edv.table(df, groupby={"columns": ["大区"], "value": edv.follow()}),
    cols=2,
)
```

- 页面初始选中第一张带 `metric=` 的卡片（这里就是「销售额」）；
- 点「客户数」→ 柱状图换成按客户名称去重计数、饼图同理、汇总表也换成去重数；
- 再点一次同一张 → 取消选中，图回到 `follow(default)` 的列；
- 选中的卡片会有高亮描边，方便知道现在看的是哪个口径。

### 2.2 `follow()` 的默认列

```python
edv.bar(df, x="月", y=edv.follow("金额"))   # 没选中时先看金额
edv.bar(df, x="月", y=edv.follow())         # 不写就等用户点卡片
```

### 2.3 哪些角色能接

度量角色都可以：`y`、`y2`、`value`、`values`、`size`、`names`、`spark`。
维度角色（`x`、`color`、`path`）不能接，会直接报错——那会把整张图的结构换掉。

```python
edv.combo(df, x="月", bar=edv.follow(), line="数量")
edv.scatter(df, x="订单数", y=edv.follow(), size=edv.follow())
```

### 2.4 不写 `follow()` 的图

完全不动。所以一个看板里可以混着「固定看金额」的图和「跟着切」的图。

### 2.5 为什么不用 rerun

选中状态只存在前端 `EazyViz.selection` 里，切换时只重画相关的图；不重新读数据、
不重新序列化 payload，所以是毫秒级。Streamlit 里也不会 `st.rerun()`。

---

## 3. 每列怎么汇总：`edv.column(...)`

### 3.1 一次声明，整页生效

```python
edv.column(
    金额="sum",
    客户名称="unique",        # 去重计数
    订单数="count",           # 行数
    订单均价="金额/订单数",    # 表达式列，默认按 mean
)
```

之后：

```python
edv.bar(df, x="月", y="客户名称")   # 自动 unique
edv.bar(df, x="月", y="订单均价")   # 自动 mean
edv.table(df, groupby={"columns": ["大区"], "value": "客户名称"})   # 汇总表也去重计数
```

### 3.2 表达式列

支持 `+ - * /`，可以嵌套引用别的登记项：

```python
edv.column(毛利额="金额-成本", 毛利率=("毛利额/金额", "mean"))
```

表达式列**只在被引用时才计算**，不会凭空增加页面体积；分母为 0 或空值的那一行记为缺失。

### 3.3 优先级

显式传的 `agg=` > `edv.column(...)` 登记值 > 默认 `sum`。

```python
edv.column(金额="sum")
edv.bar(df, x="月", y="金额")             # sum（登记值）
edv.bar(df, x="月", y="金额", agg="mean") # mean（显式覆盖）
```

---

## 4. 卡片外框：`card_style`

`show()` / `dashboard()` 的 `card_style` 三档（1.6 起默认透明）：

| 取值 | 效果 | 适合 |
|---|---|---|
| `"plain"`（默认） | 无边框、无底色、无阴影 | 白底/浅色页面上让图表「浮」着，最省视觉噪音 |
| `"card"` | 实心卡片（旧样式：白底 + 边框 + 阴影） | 需要明确分区、深色背景 |
| `"glass"` | 液态玻璃：半透明 + 磨砂 + 高光边 | 有渐变/图片背景，想让底色透上来 |

```python
edv.show(*charts, card_style="glass", cols=3)
```

别名：`transparent`/`透明`/`无框` → plain；`default`/`solid`/`实心` → card；`liquid`/`液态玻璃` → glass。

---

## 5. 完整例子（Streamlit）

```python
import streamlit as st
import eazy_data_viz as edv

@edv.cached
def read_data():
    ...  # 返回已 groupby 汇总过的多维数据

df = read_data()

edv.column(金额="sum", 数量="sum", 客户名称="unique", 余额="sum", 订单数="count")

edv.streamlit_dashboard(
    edv.kpi(df, value="金额", metric="sale", label="销售额", spark="金额", spark_x="月",
            compare={"年": ["2026年", "2025年"]}, abs_height=100, fmt="compact"),
    edv.kpi(df, value="数量", metric="qty", label="销售量", abs_height=100),
    edv.kpi(df, value="余额", metric="bal", label="应收余额", abs_height=100),
    edv.kpi(df, value="客户名称", metric="cust", label="客户数", agg="unique", abs_height=100),
    edv.bar(df, x="月", y=edv.follow(), drill=["渠道", "品牌系列"],
            color="年", link="q1", sort="年-月", yoy=True),
    edv.sunburst(df, path=["渠道", "年"], value=edv.follow(), link="q1"),
    edv.sankey(df, path=["组织名称", "渠道"], value=edv.follow(), link="q1"),
    edv.table(df, groupby={"columns": ["年", "月", "组织名称"], "value": "数量"}, link="q1"),
    palette="tableau", card_style="glass",
    grid=(4, 4), layout=[[1, 1], [1, 1], [1, 1], [1, 1], [1, 3], [1, 1], [2, 3], [2, 1]],
)
```

点任意一张 KPI 卡片，柱状图 / 旭日 / 桑基 / 汇总表一起换口径；点图里的类目，四张卡片一起重算同比。

---

## 6. 常见问题

**Q1. `compare` 和 `bar(yoy=True)` 有什么区别？**

`bar(yoy=True)` 只是给柱状图在**两个 color 系列**之间标增长率；`compare=` 是 KPI 卡片的
动态对比引擎，支持同期对齐、环比、上期为空/为 0/为负的规则，而且跟着联动重算。

**Q2. 卡片上的两排 chip 去哪了？**

1.6.1 起去掉了。卡片只显示「本期数值 + 同比/环比」，切换用「点卡片选指标」的方式，
界面更安静，也不会挤占卡片高度。

**Q3. 切换指标会不会影响联动条件？**

不会。联动条件（`link`）与指标选择是两件事：先按联动筛行，再按当前指标算值。

**Q4. 只有一张卡片也能当选择器吗？**

能。点它是选中，再点是取消；取消后图回到 `follow(default)`。

**Q5. `follow()` 能用于 `table` 的 `groupby.value` 吗？**

能。`table(df, groupby={"columns": ["大区"], "value": edv.follow()})` 会跟着选中卡片换汇总列。

**Q6. 为什么 `agg` 的默认值变成 `None` 了？**

为了区分「用户没传」和「用户显式传了 sum」。没传时才会去查 `edv.column(...)` 的登记值；
显式传了就以你写的为准。

---

下一篇：[16 自由排列](16-layout.md)　｜　上一篇：[15 中文与本地化约定](15-chinese-format.md)　｜　回到 [教程索引](README.md)
