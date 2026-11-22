> **已废弃（1.6.1）**：`edv.switch()` 与 `Switch` 已从公开 API 移除，改由
> [`edv.follow()`](../api/follow.md)（度量跟随选中的 KPI 卡片）与
> [`edv.column()`](../api/column.md)（每列汇总登记）承担。
> 这份文档仅作历史参考保留。

# `switch` — 指标切换映射（1.6）

## 函数签名

```python
eazy_data_viz.switch(**kwargs)
```

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 说明 |
|---|---|---|---|---|
| `**kwargs` | `str` | — | 是 | 指标名 = 列名，例如 `switch(sale="金额", qty="数量")`；第一个是默认指标 |

> 共 1 个参数（可变关键字参数）；指标名不能为空，列名必须是字符串。

## 参数详解

### `**kwargs` — 指标名 → 列名（`str`）

**作用**：声明「同一个角色可以映射到多列」，把它传给任何接受列名的角色参数（`y` / `value` / `size` / `names` / `spark` …）。第一次出现的指标是默认指标，Python 侧先用它出图；浏览器里点 KPI 卡片上的指标 chip（或 `kpi(metric=...)` 指定的那张卡）会把这个看板里所有用到同一个 switch 的图表切到对应列，**不触发 Python 重算**。

**建议**：

* 一个 switch 里的列要**同一类**（都数值或都文本），否则切换后类型对不上（数值图切到文本列会画不出来）；
* 数据准备时 switch 的所有列都会一起带上，所以切换是纯前端的；
* 用 `metric=` 指定默认指标时，必须出现在 switch 里。

**示例**：

```python
amount = eazy_data_viz.switch(sale="金额", qty="数量", balance="余额")
eazy_data_viz.show(
    eazy_data_viz.kpi(df, value=amount, label="销售额", metric="sale", spark="金额", spark_x="月"),
    eazy_data_viz.bar(df, x="月", y=amount),
    eazy_data_viz.pie(df, names="大区", values=amount),
)
```

**报错**：

* `ValueError: edv.switch 至少需要一个指标，例如 edv.switch(sale="金额", qty="数量")。`
* `ValueError: edv.switch 的指标名不能是空字符串。`
* `ValueError: edv.switch['sale'] 需要是列名字符串，收到 ''。`
* `ValueError: 角色参数只能传一个 switch，或者传普通列名。`（多列参数里混入 switch 时）

## 返回值

`Switch` —— 一个有序字典（`dict` 子类），带这些只读属性：

| 属性 | 说明 |
|---|---|
| `default_name` | 默认指标名（第一个键） |
| `default_column` | 默认指标对应的列名 |
| `names` | 全部指标名 |
| `columns` | 全部列名（去重、按声明顺序） |

## 完整示例

### 示例 1：销售额 / 销售量 / 应收余额 一键切换

```python
import pandas as pd
import eazy_data_viz

df = pd.DataFrame({"月": ["1月", "2月", "3月"],
                   "金额": [100, 200, 300],
                   "数量": [10, 20, 30],
                   "余额": [1000, 2000, 3000]})
amount = eazy_data_viz.switch(sale="金额", qty="数量", bal="余额")

k = eazy_data_viz.kpi(df, value=amount, label="指标", metric="sale", spark="金额", spark_x="月")
print(k.spec["switch"])      # {'value': {'sale': '金额', 'qty': '数量', 'bal': '余额'}}
print(k.spec["roles"])       # {'value': '金额'}   ← Python 侧先用默认指标

b = eazy_data_viz.bar(df, x="月", y=amount)
print(b.spec["switch"])      # {'y': {'sale': '金额', …}}
```

### 示例 2：文本类指标（客户数 / 订单数）

```python
who = eazy_data_viz.switch(cust="客户名称", order="订单号")
eazy_data_viz.kpi(df, value=who, label="数量", agg="unique", spark_x="月")
```

## 常见问题 / 注意事项

### Q1. 切换时 Python 会重跑吗？

不会。所有列在建看板时就嵌进 `dataStore` 了，切换只是改 `spec.roles[角色]` 之后重绘。

### Q2. 联动会失效吗？

不会。指标切换只换「用哪一列」，联动过滤、下钻、对比引擎都照旧。

### Q3. 想让某张图不跟着切？

那张图别传 `switch`，继续用具体列名即可。

## 相关图表

* [`kpi`](kpi.md) —— `metric=` 指定默认指标、卡片上的指标 chip
* [`bar`](bar.md) / [`line`](line.md) / [`pie`](pie.md) —— 任何角色参数都可以接 switch
