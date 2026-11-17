# `matrix` — 相关系数矩阵（用热力图展示多个数值列之间的皮尔逊相关系数）

相关系数矩阵把多个数值列两两之间的皮尔逊相关系数画成一张热力图：红色越深正相关越强，蓝色越深负相关越强，对角线恒为 1。它是做特征筛选、发现共线性的第一步。

计算完全在 Python 端完成（`DataFrame.corr(method="pearson")`，保留 4 位小数），JS 只负责把`labels` + `values` 画成对称热力图，因此不依赖浏览器里的原始数据。

- **适合**：3~12 个数值列、想快速找出“谁和谁一起动”的探索性分析。
- **不适合**：列里有大量缺失值（相关系数基于成对完整观测，样本量不一致）、非线性关系、或分类变量时不要直接用它。

> 本页所有示例均可直接复制运行：先 `import eazy_data_viz as edv`，再 `df = edv.sample_df()`。

## 函数签名

```python
eazy_data_viz.matrix(
    data,
    columns=None,
    *,
    max_cols=12,
    title=None,
    subtitle=None,
    fmt='compact',
    height=460,
    theme='light',
) -> Chart
```

参数按签名顺序：`data` → 本图专有参数 → 关键字参数（`*` 之后全部只能按关键字传）。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | pandas.DataFrame（也接受 dict / list，内部会转成 DataFrame） | 无 | 是 | 数据源（DataFrame） |
| `columns` | list[str] 或 None | None | 否 | 参与计算的数值列（默认全部数值列） |
| `max_cols` | int | 12 | 否 | 自动取列时的最大列数 |
| `title` | str 或 None | None | 否 | 图表主标题 |
| `subtitle` | str 或 None | None | 否 | 副标题（口径/单位/时间范围） |
| `fmt` | str | 'compact' | 否 | 数值格式（tooltip / 标签） |
| `height` | int | 460 | 否 | 画布高度（像素） |
| `theme` | str | 'light' | 否 | 主题（浅色 / 深色） |

> 共 8 个参数。签名里 `*` 之后是 keyword-only，必须写参数名；`data` 之前的位置参数（本图专有）可以按位置传。

## 参数详解

### `data` — 数据源（DataFrame）（`pandas.DataFrame`，必填）

- **作用**：图的原始数据。函数会按参数名从里面取列：`data` 既可以是 `pandas.DataFrame`，也可以是 `dict`（列名 → 值序列）或 `list`（记录列表），内部通过 `ensure_frame()` 统一转换。转换后必须至少有 1 行，否则报 `ValueError`。每张图最多嵌入 40 列（`MAX_COLS=40`），超过的部分会被丢弃并写入 `chart.warnings["warnings"]`。
- **建议**：首选 `pandas.DataFrame`；列名建议保持唯一、非空，中文列名可以直接用。 数值列用数值 dtype（`int64/float64`）；文本数字请先 `pd.to_numeric()`。 日期列用 `datetime64[ns]`（或可被 `pd.to_datetime()` 解析的字符串）。 作图前先处理空值：不同图对空值的策略不同（见各函数“常见问题”）。
- **示例**：`edv.matrix(data=df, columns=["销售额", "订单数", "利润", "客户数"])`
- **报错**：传入空 DataFrame：`ValueError: 数据为空（0 行），无法绘图。`；传入 `None`：`ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`

### `columns` — 参与计算的数值列（`list[str] | None`，默认 `None`）

- **作用**：不传时自动取 `data` 中所有数值列（按 DataFrame 列顺序），最多 `max_cols` 个。显式传入时按传入顺序排列，且每一列都必须是数值类型。
- **建议**：显式传入可以控制顺序与选集，例如 `["销售额", "订单数", "利润", "客户数"]`。 只放真正想比较的指标，4~8 个最易读。 不要把 ID、编码这类名义数值列混进来——它们的相关系数没有意义。
- **示例**：`edv.matrix(df, columns=["销售额", "订单数", "利润", "客户数"])`
- **报错**：列不存在：`KeyError: "columns[0]列 '不存在' 不存在。当前可用的列有：..."`；传文本列：`TypeError: columns[0] 列 '大区' 需要是数值类型（相关系数矩阵只能用数值列）。`

### `max_cols` — 自动取列时的最大列数（`int`，默认 `12`）

- **作用**：只有 `columns=None` 时生效：从数值列中截取前 `max_cols` 列。显式传 `columns` 时该参数被忽略。
- **建议**：默认 12，一般不用改；列很多时调小到 6~8 保持格子可读。 需要特定列请直接传 `columns`，不要靠 `max_cols` 截断。 传 `max_cols=0` 会得到 0 列并触发“至少 2 个数值列”报错。
- **示例**：`edv.matrix(df, columns=["销售额", "订单数", "利润", "客户数"], max_cols=6)`
- **报错**：`max_cols=1` 时只剩 1 列：`ValueError: matrix 至少需要 2 个数值列才能计算相关系数（当前 1 个）。请先检查 DataFrame 的数值列，或用 columns= 指定。`

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在卡片顶部的主标题。传 `None` 时使用函数内置的自动标题；传字符串则完全覆盖自动标题。标题只影响展示，不参与数据聚合与排序。
- **建议**：建议 8~18 个汉字，写清“指标 + 维度 + 口径”，例如 `销售额 按 大区`。 时间范围、币种、口径放在 `subtitle`，不要全部堆进标题。 标题是单行布局，过长会被卡片宽度截断，不建议加换行符。
- **示例**：`edv.matrix(df, columns=["销售额", "订单数", "利润", "客户数"], title="华东区销售构成")`

### `subtitle` — 副标题（口径/单位/时间范围）（`str | None`，默认 `None`）

- **作用**：标题下方的第二行说明，常用于补充统计口径、单位、时间范围或“较上期 +8%”这类结论。默认 `None`，不显示副标题；传空字符串等同于不显示。
- **建议**：写口径而不重复标题，例如 `2024 年 1-12 月 · 含税`。 颜色比标题浅，信息量控制在 30 字以内。 需要换行时直接写 `\n` 不会被解析成 HTML，建议保持单行。
- **示例**：`edv.matrix(df, columns=["销售额", "订单数", "利润", "客户数"], subtitle="2024 年 1-12 月 · 含税")`

### `fmt` — 数值格式（tooltip / 标签）（`str`，默认 `'compact'`）

- **作用**：控制数值在 tooltip、数据标签、右端读数里的显示格式，不改变原始数据。可选值：`compact`（默认，≥1 亿显示“x.x亿”、≥1 万显示“x.x万”、否则千分位）、`thousands`（千分位，如 `1,234,567`）、`raw`（原样，最多 3 位小数）、`percent`（一位小数加 `%`，如 `12.3%`）、`currency`（`¥` + 千分位 + 两位小数）。 本图实现：**不生效**。相关系数单元格固定保留 2 位小数，可视映射也固定两位小数。
- **建议**：金额大数用 `compact`，表格/财务口径用 `thousands` 或 `currency`。 已经是百分数的列用 `percent`，不要再乘 100。 同一页多张图保持一致的 `fmt`，避免“万/千分位”混排。
- **示例**：`edv.matrix(df, columns=["销售额", "订单数", "利润", "客户数"], fmt="thousands")`
- **报错**：`fmt="commas"`：`ValueError: fmt='commas' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）（`int`，默认 `460`）

- **作用**：单张图的容器高度，单位像素，最小 120。不同函数的默认高度不同（本函数默认值见参数总览）。高度只影响画布，不改变数据；图例/标题/坐标轴会自动占用内部空间。
- **建议**：普通看板 320~460；层级图/关系图建议 ≥420。 多张图并排时高度取一致，视觉更整齐。 `height` 小于 120 会直接报错，不要用它做“隐藏图”。
- **示例**：`edv.matrix(df, columns=["销售额", "订单数", "利润", "客户数"], height=520)`
- **报错**：`height=100`：`ValueError: height 至少 120（像素），收到 100`；`height="400"`：同样报错（必须是 `int/float`）。

### `theme` — 主题（浅色 / 深色）（`str`，默认 `'light'`）

- **作用**：页面主题，只支持 `"light"`（默认，白底深字）和 `"dark"`（深底浅字）。主题会同时改变背景、文字、坐标轴、tooltip 和默认色板的取色（`theme.palette`）。
- **建议**：常规报表/打印用 `light`；大屏、夜间模式用 `dark`。 多图看板统一主题，不要一张亮一张暗。 深色下避免使用低饱和的 `morandi` 色板，对比度会不够。
- **示例**：`edv.matrix(df, columns=["销售额", "订单数", "利润", "客户数"], theme="dark")`
- **报错**：`theme="blue"`：`ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

## 返回值

返回 `eazy_data_viz.Chart` 对象（`chart.spec` 是完整的渲染 spec，`chart.data` 是嵌入前端的数据）。

- 通用方法：`chart.save(path)` 写单文件 HTML、`chart.to_html()` 返回字符串、`chart.palette(name)` 链式换色、`chart.show()` 在浏览器打开；`chart.warnings` 记录采样等降级提示（详见 [交互与联动指南](../guides/06-interaction.md)）。

本图的关键 spec 字段（`chart.spec`）：

| 字段 | 含义 |
| --- | --- |
| `type` | 固定为 `"matrix"`。 |
| `labels` | 参与计算的列名（字符串列表），JS 用作两轴刻度。 |
| `values` | 二维相关系数矩阵（JSON），已四舍五入到 4 位，NaN 转为 `null`。 |
| `dataRef` | 固定为 `None`：矩阵数据已经算好，不再携带原始行。 |
| `roles` | 固定为 `{}`；本函数不使用角色映射。 |
| `fmt / legend / labels / zoom 等` | 签名保留的部分不参与渲染：单元格数字固定 `toFixed(2)`，图例/缩放不存在。 |

## 完整示例

以下示例全部基于 `edv.sample_df()`（1500 行、11 列）或由它派生的小表；输出文件写到 `examples/output/`。

### 示例 1：最简：自动选全部数值列

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.matrix(df)
chart.save("examples/output/matrix_1.html")
```

**输出**：4×4 对称热力图（销售额、订单数、利润、客户数），对角线深红为 1，格子里显示两位小数的相关系数；右侧竖向 visualMap 从 -1 到 1。

### 示例 2：典型：显式指定指标与顺序

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.matrix(
    df,
    columns=["销售额", "订单数", "利润", "客户数"],
    title="核心指标相关性",
    subtitle="Pearson · 保留两位小数",
)
chart.save("examples/output/matrix_2.html")
```

**输出**：列顺序与传入一致；标题/副标题替换默认的“相关系数矩阵”，格子文字为两位小数（如 0.87），悬停显示完整列名与系数。

### 示例 3：进阶：只保留 3 个指标

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.matrix(df, columns=["销售额", "利润", "客户数"], height=380)
chart.save("examples/output/matrix_3.html")
```

**输出**：3×3 热力图，格子更大更易读；高度降到 380 后格子变成扁矩形，但仍可正常悬停。

### 示例 4：自动截断：`max_cols` 限制列数

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.matrix(df, max_cols=3, title="只取前 3 个数值列")
chart.save("examples/output/matrix_4.html")
```

**输出**：只画 DataFrame 中前 3 个数值列（销售额、订单数、利润）；列顺序来自原始 DataFrame，不是按相关性排序。

### 示例 5：深色主题与配色

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.matrix(df, theme="dark")
chart.palette("tableau")
chart.save("examples/output/matrix_5.html")
```

**输出**：深色背景上格子颜色从 Tableau 蓝到浅色渐变，文字自动转白；visualMap 与坐标轴标签同步适配深色。

## 常见问题 / 注意事项

### Q1. 为什么对角线全是 1、矩阵是对称的？

每个变量与自己的相关系数恒为 1；皮尔逊相关系数满足 r(a,b)=r(b,a)，所以矩阵一定对称。本库会把上下三角都画出来，不做遮罩。

### Q2. 相关系数多大才算“强”？

经验值：|r|≥0.7 强、0.4~0.7 中等、<0.4 弱。但相关不等于因果，还要结合业务判断；样本量小或异常值多时 r 会不稳定。

### Q3. 有缺失值会怎样？

`DataFrame.corr()` 默认按成对完整观测计算，每个格子的样本量可能不同，导致矩阵不再严格对称一致。建议先 `df.dropna(subset=[...])` 或用中位数填充后再算。

### Q4. `fmt` 为什么不起作用？

matrix 使用 `_manual_spec` 手工构 spec，JS 对单元格固定 `toFixed(2)` 且 visualMap 用原始值，`spec.fmt` 没有被读取。

### Q5. 能改坐标轴标题吗？

不能。matrix 的函数签名里没有 `xtitle`/`ytitle`，JS 虽然支持读取这两个字段，但 Python 永远不会写入。

## 相关图表

| 图表 | 说明 |
| --- | --- |
| [`quadrant`](quadrant.md) | 四象限散点图（相关性确认后，把两个指标放进四象限看对象） |
| [`trend`](trend.md) | 趋势图（两个连续变量之间的回归关系与 R²） |
| [`table`](table.md) | 明细表（需要逐行核对原始数值时用它） |
| [`theme_river`](theme_river.md) | 主题河流图（时间维度上的结构变化） |

- 回到总览：`docs/EXTRA_CHARTS.md`、`docs/AI_GUIDE.md`
