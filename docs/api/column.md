# `column` — 声明每列的汇总方式（1.6.1）

## 函数签名

```python
eazy_data_viz.column(**specs)
```

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 说明 |
|---|---|---|---|---|
| `**specs` | `str` 或 `tuple` | — | 是 | `列名=聚合方式`，或 `列名="表达式"`，或 `列名=("表达式", "聚合方式")` |

> 共 1 个参数（可变关键字参数）。登记是**全局**的：登记之后新建的图都用这套规则，直到 `reset_columns()`。

## 参数详解

### `**specs` — 列名 → 汇总规则（`str` 或 `tuple`）

**作用**：一次性声明「这列怎么汇总」，之后画图就不用每张都写 `agg=`：

```python
edv.column(
    金额="sum",            # 求和
    客户名称="unique",      # 去重计数（文本列也合法）
    订单数="count",         # 计数（行数）
    订单均价="金额/订单数",  # 表达式列：建图前用 pandas 算出来
)
edv.bar(df, x="月", y="客户名称")   # 自动按 unique 汇总
```

三种写法：

| 写法 | 含义 | 默认聚合 |
|---|---|---|
| `列名="sum"` | 直接指定聚合方式 | 就是写的那个 |
| `列名="金额/订单数"` | 表达式：用其它列算出新列 | 含 `/` 用 `mean`，否则 `sum` |
| `列名=("金额/订单数", "mean")` | 表达式 + 显式聚合 | 以第二个元素为准 |

支持的聚合方式：`sum`、`mean`、`count`、`unique`、`max`、`min`、`median`。

**建议**：

* 只登记**需要改默认行为**的列，没登记的列仍然按 `sum`；
* 表达式只支持 `+ - * /`（四则运算），列名可以带中文；分母为 0 或空值的那一行结果记为缺失，不会画出 `inf`；
* 表达式列**用到才计算**：没有图引用它时不会出现在数据里，不增加页面体积；
* 同一个名字重复登记会覆盖旧规则，`reset_columns()` 可清空。

**示例**：

```python
edv.column(金额="sum", 数量="sum", 客户名称="unique", 订单数="count")
edv.column(订单均价="金额/订单数")
edv.column(客单价=("金额/客户名称", "mean"))
```

**报错**：

* `ValueError: edv.column 至少需要一列，例如 edv.column(金额="sum", 客户名称="unique")。`
* `ValueError: edv.column 的列名不能是空字符串。`
* `ValueError: edv.column['金额'] 的聚合方式 'avg' 不支持，可选：sum、mean、count、unique、max、min、median；要写表达式请用 + - * / ，例如 订单均价="金额/订单数"。`
* `ValueError: edv.column['金额'] 需要是字符串（聚合方式或表达式），收到 123。`
* `ValueError: edv.column['订单均价'] 的取值只能是聚合方式、表达式，或 (表达式, 聚合方式)。`
* `ValueError: edv.column 的表达式 '金额/单价' 里用到列 '单价'，但数据里没有这一列，也没有在 edv.column(...) 里登记过。`（建图时才校验）

## 返回值

`dict` —— 当前登记表的副本：`{列名: {"agg": 聚合方式或 None, "expr": 表达式或 None}}`，方便自查。

另有三个辅助函数：

| 函数 | 说明 |
|---|---|
| `column_table()` | 同返回值，看当前登记了什么 |
| `reset_columns()` | 清空登记表，回到「全部按 sum」的旧行为 |
| `column_spec(name)` | 查单列的登记项（没有则 `None`） |

## 与图表参数的关系

优先级从高到低：

1. 显式传的 `agg=`（例如 `bar(..., agg="mean")`）；
2. `edv.column(...)` 里登记的值；
3. 内置默认 `sum`（没有度量列时按 `count`）。

`agg` 的默认值在 1.6.1 起是 `None`，就是为了区分「没传」和「显式传了 sum」。

## 完整示例

### 示例 1：一份登记，整页生效

```python
import eazy_data_viz as edv

edv.column(
    金额="sum",
    数量="sum",
    客户名称="unique",
    订单数="count",
    订单均价="金额/订单数",
)

edv.show(
    edv.bar(df, x="月", y="金额"),            # sum
    edv.bar(df, x="大区", y="客户名称"),      # unique（去重计数）
    edv.bar(df, x="大区", y="订单数"),        # count
    edv.bar(df, x="月", y="订单均价"),        # mean（表达式列）
    cols=2,
)
```

### 示例 2：表达式列只算被引用的

```python
edv.column(订单均价="金额/订单数")
c = edv.bar(df, x="月", y="订单均价")
print("订单均价" in c.data["cols"])   # True

c2 = edv.bar(df, x="月", y="金额")
print("订单均价" in c2.data["cols"])  # False —— 没被引用就不计算
```

### 示例 3：和 follow() 一起用

```python
edv.column(金额="sum", 客户名称="unique")

edv.show(
    edv.kpi(df, value="金额", metric="sale", label="销售额"),
    edv.kpi(df, value="客户名称", metric="cust", label="客户数"),
    edv.bar(df, x="月", y=edv.follow()),   # 卡片选谁就用谁的列 + 登记聚合
    cols=2,
)
```

## 常见问题

### Q1. 为什么不用每张图写 `agg=`？

一张看板里同一个指标往往被 5 张图用到，逐张写既啰嗦又容易写漏。登记一次，之后新建的图自动对齐口径。

### Q2. 表达式列能参与联动 / 下钻吗？

能。它在建 spec 时就变成了真实的一列，联动筛选、下钻、汇总表都用它。

### Q3. 登记表是全局的，会不会影响别人的图？

只影响**登记之后**新建的图。多页/多用例里想隔离，先用 `reset_columns()` 再登记。

### Q4. `count` 和 `unique` 有什么区别？

`count` 数**非空行数**；`unique` 数**不重复的值个数**。例如「客户名称」列有 100 行、其中 30 个不同客户：`count` 是 100，`unique` 是 30。

## 相关图表

* [`follow`](follow.md) —— 度量跟着选中的 KPI 卡片走
* [`kpi`](kpi.md) —— 卡片 / 选择器
* [`table`](table.md) —— 汇总表的 `groupby.agg` 与这里同源

## 表达式列的细节

支持的运算：`+ - * /`，按普通四则运算优先级（先乘除后加减），不支持括号与函数调用。
每个片段要么是数据里已有的列，要么是别的登记项（可以嵌套引用）。

```python
edv.column(订单均价="金额/订单数", 单均成本="成本/订单数")
edv.column(毛利额="金额-成本", 毛利率=("毛利额/金额", "mean"))
```

计算规则：

| 情况 | 结果 |
|---|---|
| 分母为 0 | 该行记为缺失（`null`），不画 `inf` |
| 任一操作数是空值 | 该行记为缺失 |
| 操作数是文本 | 先按数值转换，转不动的当缺失 |
| 目标列名已存在 | 用算出来的列覆盖原列 |

## 与汇总表 / 联动的关系

* `table(groupby={"columns": [...], "value": "客户名称"})` 的 `agg` 默认也走这里——登记成 `unique` 之后，汇总表自动是去重计数，不用再写 `"agg": "unique"`；
* 联动筛选（`link`）在算聚合**之前**发生，所以汇总数字永远是「当前筛选结果」的；
* 表达式列参与联动筛选时，按它的值筛（和普通数值列一样）。

## 调试

```python
edv.column(金额="sum", 客户名称="unique")
print(edv.column_table())
# {'金额': {'agg': 'sum', 'expr': None}, '客户名称': {'agg': 'unique', 'expr': None}}

print(edv.column_spec("客户名称"))   # {'agg': 'unique', 'expr': None}
edv.reset_columns()                  # 清空
```

看图实际用了什么：

```python
c = edv.bar(df, x="大区", y="客户名称")
print(c.spec["agg"])        # 'unique'
print(c.spec["roles"])      # {'x': '大区', 'y': '客户名称'}
```

## 版本说明

| 版本 | 变化 |
|---|---|
| 1.6.1 | 新增；同时把 `agg` 的默认值从 `"sum"` 改成 `None`，用来区分「没传」与「显式传了 sum」 |
