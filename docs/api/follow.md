# `follow` — 度量跟随「选中的 KPI 卡片」（1.6.1）

## 函数签名

```python
eazy_data_viz.follow(
    default=None,
) -> Chart
```

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 说明 |
|---|---|---|---|---|
| `default` | `str` 或 `None` | `None` | 否 | 还没选中任何卡片时先用的列名；给 `None` 时该角色先空着，等用户点卡片再填 |

> 共 1 个参数。返回值是 `Follow` 占位符，只该出现在**度量角色**（`y` / `y2` / `value` / `values` / `size` / `names` / `spark`）上。

## 参数详解

### `default` — 未选中时的默认列（`str` 或 `None`）

**作用**：页面刚打开、用户还没点任何 KPI 卡片时，这个角色先用 `default` 这一列；一旦用户点了某张卡片，它立刻换成那张卡片声明的列，聚合方式也跟着换成那张卡片的登记值。

**建议**：

* 不确定就先别给 `default`——`follow()` 空着也安全，页面初始选中会自动取第一张 `metric=` 卡片；
* `default` 列要和卡片的列**同量纲**，否则切换时坐标轴/数值范围会跳得很大；
* `follow()` 只在度量角色上有效，给 `x` / `color` / `path` 这类维度角色会直接报错。

**示例**：

```python
eazy_data_viz.bar(df, x="月", y=eazy_data_viz.follow())          # 完全跟随
eazy_data_viz.bar(df, x="月", y=eazy_data_viz.follow("金额"))    # 没选卡片时先看金额
```

**报错**：

* `ValueError: follow 的 default 需要是列名字符串，收到 123。`
* `ValueError: follow 的 default 不能是空字符串。`
* `ValueError: follow() 只能用在度量角色（y / y2 / value / values / names / size / spark），不能给 'x' 这类维度用。`

## 返回值

`Follow` —— 一个轻量占位对象（不是字符串），只在 Python 侧被 `_base_spec` 摘出来、写成 spec 里的 `follow` 映射：

```json
{"y": {"default": null, "agg": "sum"}}
```

浏览器里 `EazyViz.selection` 一变，同一页所有带 `follow` 的图会重画成新列 + 新聚合，**不触发 Python 重算**。

| 字段 | 说明 |
|---|---|
| `default` | 未选中时用的列（可能为 `null`） |
| `agg` | 建图时解析出的聚合方式（来自 `edv.column` 登记表，没登记按 `sum`） |

## 工作原理（为什么值会跟着卡片走）

1. Python 建 spec 时把 `follow()` 从 `roles` 里摘掉，该角色暂时是 `None`，同时在 spec 里写下 `follow` 映射；
2. 页面渲染时，前端把「第一张带 `metric=` 的 KPI 卡片」设为初始选中（`selection = {name, column, agg, label, id}`）；
3. `renderChart()` 开头调用 `applyFollow(spec)`：拿当前选中的列写回 `spec.roles[role]`，拿选中的聚合写回 `spec.agg`；
4. 用户点某张卡片 → 只更新 `EazyViz.selection` 并重画相关图表（含卡片高亮），Python 完全不参与；
5. 再点同一张卡片 → 取消选中，图回到 `follow(default)` 的列。

## 类目顺序会变吗（1.6.4）

不会。`y=follow()` 的图默认把**类目顺序钉住**：页面第一次渲染时按当时选中指标
（没选中则按 `follow(default)`）的合计降序排一次，之后切卡片只换数值、不重排左右
位置，柱子的位置在切换过程中保持稳定，方便对比同一批类目的不同指标。

```python
edv.bar(df, "大区", edv.follow("销售额"))              # 顺序固定（按销售额排一次）
edv.bar(df, "大区", edv.follow("销售额"), sort="desc")  # 每次都按当前指标重排
edv.bar(df, "大区", edv.follow("销售额"), sort="none")  # 完全按 df 里的出现顺序
```

分组柱（带 `color`）的**图例顺序**也一起钉住；显式写 `sort=` 时以你为准。

## 完整示例

### 示例 1：一张 KPI 卡当「按钮」，两个图跟着换口径

```python
import eazy_data_viz as edv

edv.column(金额="sum", 数量="sum", 客户名称="unique")

edv.show(
    edv.kpi(df, value="金额", metric="sale", label="销售额", spark="金额", spark_x="月"),
    edv.kpi(df, value="客户名称", metric="cust", label="客户数"),
    edv.bar(df, x="月", y=edv.follow()),
    edv.pie(df, names="大区", values=edv.follow()),
    cols=2,
)
```

点「销售额」卡片：柱状图的 `y` = `金额`、聚合 `sum`；饼图的 `values` 同样变成 `金额`。
点「客户数」卡片：两张图一起变成「按客户名称去重计数」。

### 示例 2：给每个跟随的角色一个默认列

```python
edv.bar(df, x="月", y=edv.follow("金额"), color="大区")
edv.line(df, x="月", y=edv.follow("金额"), link="g1")
```

用户还没点卡片时先看金额；点了「客户数」卡片后，两张图都切成去重计数，`color` / `link` 不受影响。

### 示例 3：所有图表都能接

```python
edv.show(
    edv.kpi(df, value="金额", metric="sale", label="销售额"),
    edv.line(df, x="月", y=edv.follow()),
    edv.area(df, x="月", y=edv.follow()),
    edv.pie(df, names="大区", values=edv.follow()),
    edv.rose(df, names="大区", values=edv.follow()),
    edv.heatmap(df, x="月", y="大区", value=edv.follow()),
    edv.treemap(df, path=["大区", "渠道"], value=edv.follow()),
    edv.sunburst(df, path=["大区", "渠道"], value=edv.follow()),
    edv.sankey(df, path=["大区", "渠道"], value=edv.follow()),
    edv.wordcloud(df, names="客户名称", values=edv.follow()),
    edv.table(df, groupby={"columns": ["大区"], "value": edv.follow()}),
    edv.combo(df, x="月", bar=edv.follow(), line="数量"),
    cols=3,
)
```

## 常见问题

### Q1. `follow()` 和 `edv.column(...)` 什么关系？

`edv.column(...)` 决定「某一列怎么汇总」；`follow()` 决定「这个角色用哪一列」。两者叠加：选中卡片后，列来自卡片，聚合来自该列的登记值（没登记就 `sum`）。

### Q2. 能不能跟随多个角色？

可以，每个角色各写一次：

```python
edv.bar(df, x="月", y=edv.follow(), y2=edv.follow())
```

两个角色都跟着同一张卡片走；如果想分别跟随不同卡片，用两页 / 两个 selection 更清楚。

### Q3. 不写 `follow()` 的图会变吗？

不会。没写 `follow()` 的图完全保持自己的列名与聚合，卡片点击对它是无操作。

### Q4. 联动（`link`）还生效吗？

生效，而且顺序是：先按联动条件筛行，再算选中指标的数值。也就是说「华东 + 客户数」和「华北 + 金额」是两个独立结果，互不干扰。

### Q5. Streamlit 里会 rerun 吗？

不会。选择状态存在前端 `EazyViz.selection`，点卡片只重画浏览器里的图；只有你改动图表的 Python 参数时才会 rerun。

## 相关图表

* [`kpi`](kpi.md) —— 卡片本身（`metric=` 让它变成选择器）
* [`column`](column.md) —— 每列的汇总登记
* [`bar`](bar.md) / [`line`](line.md) / [`pie`](pie.md) —— 常见的跟随对象

## 与联动 / 下钻 / 同比一起用

`follow()` 只影响「用哪一列、怎么聚合」，其它交互各管各的：

| 能力 | 和 follow 的关系 |
|---|---|
| `link="g1"` 联动 | 先按联动条件筛行，再算当前选中指标的数值；换卡片不会清掉联动 |
| `drill=["大区", "渠道"]` 下钻 | 维度不变，下钻路径照旧；切换指标只换度量 |
| `compare={...}` 同比 | 对比是在**选中列**上算的：选了客户数就是「客户数同比」 |
| `sort` / `top_n` | 按新列重排，不需要重新传参 |
| `agg="unique"` | 选中的列如果登记成 unique，切换后自动用去重计数 |

### 为什么不会 rerun Python

`follow()` 在 Python 侧只是把角色留空 + 写一份映射，列与聚合都在浏览器里换。
所以点卡片是毫秒级的：不会重新读数据、不会重新序列化 payload。

## 调试

```python
c = edv.bar(df, x="月", y=edv.follow())
print(c.spec["roles"]["y"])   # None —— Python 侧不落列
print(c.spec["follow"])       # {'y': {'default': None, 'agg': 'sum'}}
```

浏览器里看当前选中：

```javascript
EazyViz.selection        // {name, column, agg, label, id} 或 null
EazyViz.charts[i].spec.roles.y   // 已经换成选中列
```

页面第一次渲染时的初始选中，可以在 `page` 里看到：

```python
page = edv.dashboard(edv.kpi(df, value="金额", metric="sale"), edv.bar(df, x="月", y=edv.follow()))
page.specs if hasattr(page, "specs") else None   # 或从 to_html() 的内联 JSON 里搜 "selection"
```

## 版本说明

| 版本 | 变化 |
|---|---|
| 1.6.0 | 先做成 `edv.switch()`（一张卡带一排指标 chip） |
| 1.6.1 | 改成「卡片 = 按钮 + `follow()`」；卡片上的 chip 全部去掉，只留本期数值 + 同比 |

旧写法已废弃，`docs/_deprecated/switch.md` 只作历史参考。

## 常见坑

### 1. 把 `follow()` 当成列名用

```python
edv.bar(df, x="月", y="edv.follow()")   # ✗ 字符串，会被当成一个叫 edv.follow() 的列
edv.bar(df, x="月", y=edv.follow())     # ✓ 传对象
```

### 2. 给维度角色写 `follow()`

```python
edv.bar(df, x=edv.follow(), y="金额")   # ✗ 直接报错：只能用在度量角色
```

维度（`x` / `color` / `path` / `names` 之外的类目轴）跟着卡片走会把整张图的结构
换掉，所以框架在 Python 侧就拦住了。

### 3. 卡片没有 `metric=`

```python
edv.kpi(df, value="金额")                 # 普通卡片，点了不会切换别人
edv.kpi(df, value="金额", metric="sale")  # 选择器卡片
```

只有带 `metric=` 的卡片才参与选择。
