# `graph` — 关系图（力导向网络）（用节点大小和连线粗细表达任意多对多关系）

关系图把 `source` 与 `target` 看成网络中的两个节点，边权决定连线粗细，节点大小由它的连接总量决定；布局用力导向算法自动散开，适合发现“谁是中心、哪些群体抱团”。

和桑基图不同：关系图没有层级和方向，节点可以任意互相连接，适合组织关系、商品共现、客户-产品网络。

- **适合**：实体之间是多对多关系、想找中心节点/社群；节点 5~50、边 10~100。
- **不适合**：有明确上下游方向（用 `sankey`）、或只需要两列交叉计数（用 `matrix`）时不要用；节点上百时力导向图会变成毛线团。

> 本页所有示例均可直接复制运行：先 `import eazy_data_viz as edv`，再 `df = edv.sample_df()`。

## 函数签名

```python
eazy_data_viz.graph(
    data,
    source,
    target,
    value=None,
    *,
    agg='sum',
    sort=None,
    top_n=None,
    title=None,
    subtitle=None,
    fmt='compact',
    height=420,
    theme='light',
    legend=False,
    labels=True,
    zoom=False,
    link=None,
    max_rows=200000,
) -> Chart
```

参数按签名顺序：`data` → 本图专有参数 → 关键字参数（`*` 之后全部只能按关键字传）。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | pandas.DataFrame（也接受 dict / list，内部会转成 DataFrame） | 无 | 是 | 数据源（DataFrame） |
| `source` | str | 无 | 是 | 关系的一端 |
| `target` | str | 无 | 是 | 关系的另一端 |
| `value` | str 或 None | None | 否 | 边权列（决定连线粗细与节点大小） |
| `agg` | str | 'sum' | 否 | 聚合方式（同一类目多条记录时如何合并） |
| `sort` | str 或 None | None | 否 | 排序方式 |
| `top_n` | int 或 None | None | 否 | 只保留前 N 项 |
| `title` | str 或 None | None | 否 | 图表主标题 |
| `subtitle` | str 或 None | None | 否 | 副标题（口径/单位/时间范围） |
| `fmt` | str | 'compact' | 否 | 数值格式（tooltip / 标签） |
| `height` | int | 420 | 否 | 画布高度（像素） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | str | 'light' | 否 | 主题（浅色 / 深色） |
| `legend` | bool 或 None | False | 否 | 是否显示图例 |
| `labels` | bool | True | 否 | 是否显示数据标签 |
| `zoom` | bool 或 str | False | 否 | 缩放/漫游 |
| `link` | str 或 None | None | 否 | 联动分组名 |
| `max_rows` | int | 200000 | 否 | 嵌入前端的最大行数 |

> 共 17 个参数。签名里 `*` 之后是 keyword-only，必须写参数名；`data` 之前的位置参数（本图专有）可以按位置传。

## 参数详解

### `data` — 数据源（DataFrame）（`pandas.DataFrame`，必填）

- **作用**：图的原始数据。函数会按参数名从里面取列：`data` 既可以是 `pandas.DataFrame`，也可以是 `dict`（列名 → 值序列）或 `list`（记录列表），内部通过 `ensure_frame()` 统一转换。转换后必须至少有 1 行，否则报 `ValueError`。每张图最多嵌入 40 列（`MAX_COLS=40`），超过的部分会被丢弃并写入 `chart.warnings["warnings"]`。
- **建议**：首选 `pandas.DataFrame`；列名建议保持唯一、非空，中文列名可以直接用。 数值列用数值 dtype（`int64/float64`）；文本数字请先 `pd.to_numeric()`。 日期列用 `datetime64[ns]`（或可被 `pd.to_datetime()` 解析的字符串）。 作图前先处理空值：不同图对空值的策略不同（见各函数“常见问题”）。
- **示例**：`edv.graph(data=df, source="大区", target="产品", value="订单数")`
- **报错**：传入空 DataFrame：`ValueError: 数据为空（0 行），无法绘图。`；传入 `None`：`ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`

### `source` — 关系的一端（`str`，必填）

- **作用**：与 `target` 组合成无向边（渲染上不画箭头）。同一实体在任意行的 source/target 中出现，都会合并为同一个节点。
- **建议**：一侧是“主体”、另一侧是“属性”时，主体列更适合放 source（自动标题也取 source）；例如 `source="大区"`、`target="产品"`。 两张表拼边时确保节点名不重名（“华东”大区和“华东”产品会被当成同一节点）。 缺失值归为 `(空)` 节点，最好先清洗。
- **示例**：`edv.graph(df, target="产品", value="订单数", source="大区")`
- **报错**：不传：`TypeError: graph() missing 1 required positional argument: 'target'`；列名写错：`KeyError: "source列 '不存在' 不存在。当前可用的列有：..."`

### `target` — 关系的另一端（`str`，必填）

- **作用**：每个取值是一个节点。`source == target` 的自环被跳过；同一对节点多次出现会按 `agg` 合并成一条边。
- **建议**：节点名尽量短，力导向布局中长名字会互相遮挡。 用低基数列（产品、渠道、大区），不要用订单号/客户 ID。 把节点名统一大小写与空格，避免出现“华东”“华东 ”两个节点。
- **示例**：`edv.graph(df, source="大区", value="订单数", target="产品")`
- **报错**：列名写错：`KeyError: "target列 '不存在' 不存在。当前可用的列有：..."`

### `value` — 边权列（决定连线粗细与节点大小）（`str | None`，默认 `None`）

- **作用**：数值列；同一对节点的多行按 `agg` 合并。节点总连接量 = 它所有边的权重之和，用于映射节点大小。不传时 `agg` 强制为 `count`，权重=共现次数。
- **建议**：共现次数/金额：`订单数`、`客户数`、`销售额`。 非正数边会被丢弃，只保留 v>0 的连线。 节点大小是开方缩放，极端中心节点不会完全吞掉其他节点。
- **示例**：`edv.graph(df, source="大区", target="产品", value="订单数")`
- **报错**：传文本列：`TypeError: value（数值）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `agg` — 聚合方式（同一类目多条记录时如何合并）（`str`，默认 `'sum'`）

- **作用**：同一分类下有多条记录时，把数值列合成一个数的方法。可选：`sum`（默认）、`mean`、`count`、`max`、`min`、`median`。当函数没有拿到数值列（例如没传 `values`/`value`）时，内部会把 `agg` 强制为 `count`，按记录条数统计。 本图实现：按 `(source, target)` 分组后用 `agg` 聚合连线权重；未传 `value` 时按记录数 `count`。
- **建议**：金额、订单数用 `sum`；单价、率值用 `mean` 或 `median`。 想看“有多少条记录”就传 `agg="count"`，此时数值列只作存在性检查。 `median` 对极端值更稳健，适合客单价、利润率这类偏态指标。
- **示例**：`edv.graph(df, source="大区", target="产品", value="订单数", agg="mean")`
- **报错**：`agg="average"`：`ValueError: agg='average' 不支持，可选：sum, mean, count, max, min, median`

### `sort` — 排序方式（`str | None`，默认 `None`）

- **作用**：控制分类的排列顺序。本库只认 `"asc"`、`"desc"`、`"x"`、`"none"` 四种语义，但**不做枚举校验**：传其他字符串不会报错，会静默按该图默认顺序渲染。 本图实现：**不生效**。力导向布局每次运行位置略有不同，与 `sort` 无关。
- **建议**：排行榜用 `asc/desc`；时间序列用 `x`（按列顺序/时间升序）。 需要保持数据原始顺序时传 `sort="none"`。 分类是 `pd.Categorical`（如 `月份`）时，`x` 会按分类顺序而不是字母序。
- **示例**：`edv.graph(df, source="大区", target="产品", value="订单数", sort="asc")`
- **报错**：不存在的值不报错：`sort="DESC"` 会被忽略并按默认顺序渲染（大小写敏感）。；对不读取 `sort` 的图（如 pyramid/sunburst/sankey）传任何值都不会改变图形。

### `top_n` — 只保留前 N 项（`int | None`，默认 `None`）

- **作用**：按当前排序只保留前 N 个类目，`None`（默认）表示全部保留。必须是 ≥1 的整数（`bool` 不算）。不同函数对“多出来的部分”处理不同：rose 会把剩余项合并成“其他”，wordcloud 直接截断，其余函数多数不读取该字段。 本图实现：**不生效**。所有节点和边都会绘制。
- **建议**：类目超过 12 个时用 `top_n` 收敛，避免标签重叠。 玫瑰图配 `top_n` 会得到“其他”扇区，其余图不会。 配合 `sort="desc"` 使用才有“前 N 大”的含义。
- **示例**：`edv.graph(df, source="大区", target="产品", value="订单数", top_n=5)`
- **报错**：`top_n=0`：`ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`；`top_n=True`：同样报错（`bool` 被显式拒绝）。

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在卡片顶部的主标题。传 `None` 时使用函数内置的自动标题；传字符串则完全覆盖自动标题。标题只影响展示，不参与数据聚合与排序。
- **建议**：建议 8~18 个汉字，写清“指标 + 维度 + 口径”，例如 `销售额 按 大区`。 时间范围、币种、口径放在 `subtitle`，不要全部堆进标题。 标题是单行布局，过长会被卡片宽度截断，不建议加换行符。
- **示例**：`edv.graph(df, source="大区", target="产品", value="订单数", title="华东区销售构成")`

### `subtitle` — 副标题（口径/单位/时间范围）（`str | None`，默认 `None`）

- **作用**：标题下方的第二行说明，常用于补充统计口径、单位、时间范围或“较上期 +8%”这类结论。默认 `None`，不显示副标题；传空字符串等同于不显示。
- **建议**：写口径而不重复标题，例如 `2024 年 1-12 月 · 含税`。 颜色比标题浅，信息量控制在 30 字以内。 需要换行时直接写 `\n` 不会被解析成 HTML，建议保持单行。
- **示例**：`edv.graph(df, source="大区", target="产品", value="订单数", subtitle="2024 年 1-12 月 · 含税")`

### `fmt` — 数值格式（tooltip / 标签）（`str`，默认 `'compact'`）

- **作用**：控制数值在 tooltip、数据标签、右端读数里的显示格式，不改变原始数据。可选值：`compact`（默认，≥1 亿显示“x.x亿”、≥1 万显示“x.x万”、否则千分位）、`thousands`（千分位，如 `1,234,567`）、`raw`（原样，最多 3 位小数）、`percent`（一位小数加 `%`，如 `12.3%`）、`currency`（`¥` + 千分位 + 两位小数）。 本图实现：控制连线 tooltip 中的权重、节点 tooltip 中的连接总值。
- **建议**：金额大数用 `compact`，表格/财务口径用 `thousands` 或 `currency`。 已经是百分数的列用 `percent`，不要再乘 100。 同一页多张图保持一致的 `fmt`，避免“万/千分位”混排。
- **示例**：`edv.graph(df, source="大区", target="产品", value="订单数", fmt="thousands")`
- **报错**：`fmt="commas"`：`ValueError: fmt='commas' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）（`int`，默认 `420`）

- **作用**：单张图的容器高度，单位像素，最小 120。不同函数的默认高度不同（本函数默认值见参数总览）。高度只影响画布，不改变数据；图例/标题/坐标轴会自动占用内部空间。
- **建议**：普通看板 320~460；层级图/关系图建议 ≥420。 多张图并排时高度取一致，视觉更整齐。 `height` 小于 120 会直接报错，不要用它做“隐藏图”。
- **示例**：`edv.graph(df, source="大区", target="产品", value="订单数", height=520)`
- **报错**：`height=100`：`ValueError: height 至少 120（像素），收到 100`；`height="400"`：同样报错（必须是 `int/float`）。

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题（浅色 / 深色）（`str`，默认 `'light'`）

- **作用**：页面主题，只支持 `"light"`（默认，白底深字）和 `"dark"`（深底浅字）。主题会同时改变背景、文字、坐标轴、tooltip 和默认色板的取色（`theme.palette`）。
- **建议**：常规报表/打印用 `light`；大屏、夜间模式用 `dark`。 多图看板统一主题，不要一张亮一张暗。 深色下避免使用低饱和的 `morandi` 色板，对比度会不够。
- **示例**：`edv.graph(df, source="大区", target="产品", value="订单数", theme="dark")`
- **报错**：`theme="blue"`：`ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `legend` — 是否显示图例（`bool | None`，默认 `False`）

- **作用**：是否显示图例。`None` 表示“按语义自动决定”（有色分组时显示、没有分组时隐藏），`True`/`False` 为强制开关。只有真正用颜色/名称区分系列的函数才会生效。 本图实现：**不生效**。关系图不带图例。
- **建议**：类目多且颜色即含义（产品、渠道）时保留图例。 图例项超过 10 个时图例会滚动，建议先 `top_n` 或合并小类。 单系列图关闭图例，把空间留给图形。
- **示例**：`edv.graph(df, source="大区", target="产品", value="订单数", legend=False)`
- **报错**：无校验：传非布尔值会经 `bool()` 转换（非空字符串为 `True`）。

### `labels` — 是否显示数据标签（`bool`，默认 `True`）

- **作用**：是否在图形上直接显示文字标签（类目名/数值/百分比）。默认值因函数而异；有的函数固定显示标签、不支持关闭。 本图实现：**不生效**。节点标签始终显示在节点右侧。
- **建议**：类目 ≤8 个时打开标签，读者不用来回看 tooltip。 数据密集（散点、关系图）时关闭，避免文字糊成一片。 百分比标签通常配合 `fmt="percent"`。
- **示例**：`edv.graph(df, source="大区", target="产品", value="订单数", labels=False)`
- **报错**：无校验：会经 `bool()` 转换，传 `"no"` 也是 `True`。

### `zoom` — 缩放/漫游（`bool | str`，默认 `False`）

- **作用**：是否开启缩放。多数函数接受 `bool`；`candlestick` 默认 `"auto"`，表示分类数超过 30 时自动显示底部缩放条。不支持缩放的图会接受该参数但不产生效果。 本图实现：**不生效**。力导向图默认支持拖拽/滚轮漫游。
- **建议**：时间序列很长（>60 点）时用 `zoom=True` 或放到 `candlestick` 的 `"auto"`。 层级/关系图本身可拖拽缩放，不必再开 `zoom`。 截图/打印场景关掉缩放，画面更干净。
- **示例**：`edv.graph(df, source="大区", target="产品", value="订单数", zoom=True)`

### `link` — 联动分组名（`str | None`，默认 `None`）

- **作用**：把多张图放进同一个联动组：点击某张图的类目，同组中包含该维度列的其他图会按该值过滤。同一个组名（如 `"g1"`）即可联动；默认 `None` 不联动。注意：`table`/`wordcloud` 是 HTML 渲染，只能作为**被联动方**，点击它们不会触发联动。 本图实现：点击节点会按 `source` 维度联动。
- **建议**：同一看板里的明细表用同一个 `link` 组名，点图即可筛表。 联动维度由点击的图决定，各图尽量共享同一列（如 `产品`）。 组名建议用有含义的英文/拼音，不要用随机串。
- **示例**：`edv.graph(df, source="大区", target="产品", value="订单数", link="g1")`
- **报错**：无校验：传数字/对象会原样写入 spec，JS 端作为对象键使用，建议只传字符串。

### `max_rows` — 嵌入前端的最大行数（`int`，默认 `2000000`）

- **作用**：Python 侧只把前 `max_rows` 行（默认 20000）的数据嵌入 HTML，超过时按均匀间隔抽样，并把提示写入 `chart.warnings["warnings"]`。`table` 特殊：默认 200，且最终最多嵌入 200 行。抽样只发生在“嵌入”阶段，不影响函数内已经算好的统计（如相关系数、回归系数）。
- **建议**：前端交互图保持默认 20000 即可；超大表用 `table(max_rows=...)` 控制体积。 需要完整数据时导出 Excel/CSV，不要让 HTML 承担全量数据。 抽样后 tooltip 的明细行数会变少，但聚合图的总量不受影响。
- **示例**：`edv.graph(df, source="大区", target="产品", value="订单数", max_rows=500)`
- **报错**：无校验：传 `0` 或负数会得到空数据（图形空白），建议传正整数。

## 返回值

返回 `eazy_data_viz.Chart` 对象（`chart.spec` 是完整的渲染 spec，`chart.data` 是嵌入前端的数据）。

- 通用方法：`chart.save(path)` 写单文件 HTML、`chart.to_html()` 返回字符串、`chart.palette(name)` 链式换色、`chart.show()` 在浏览器打开；`chart.warnings` 记录采样等降级提示（详见 [交互与联动指南](../guides/06-interaction.md)）。

本图的关键 spec 字段（`chart.spec`）：

| 字段 | 含义 |
| --- | --- |
| `type` | 固定为 `"graph"`。 |
| `roles` | `{"source": 一列, "target": 另一列, "value": 权重列或 None}`。 |
| `nodes / links` | JS 端聚合出的节点与边（节点值=连接总量，边值=聚合权重）；Python 不预计算。 |
| `agg` | 同一对节点的合并方式；未传 `value` 时强制 `"count"`。 |
| `labels / legend / sort / top_n / zoom` | 签名保留，但节点标签固定显示、无图例、无排序与缩放。 |

## 完整示例

以下示例全部基于 `edv.sample_df()`（1500 行、11 列）或由它派生的小表；输出文件写到 `examples/output/`。

### 示例 1：最简：大区 × 产品网络

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.graph(df, source="大区", target="产品", value="订单数")
chart.save("examples/output/graph_1.html")
```

**输出**：4 个大区节点 + 4 个产品节点，力导向布局把它们拉开；连线粗细=订单数，节点大小=连接总量，悬停显示“大区 — 产品”与数值。

### 示例 2：典型：不传权重，按共现次数

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.graph(
    df,
    source="渠道",
    target="产品",
    title="渠道与产品的共现网络",
    height=460,
)
chart.save("examples/output/graph_2.html")
```

**输出**：边粗=同一渠道-产品组合的记录条数，节点大小=该实体的记录总量；数据均匀时图近似一个 3×4 的二分网络。

### 示例 3：进阶：拼出产品共现网络

```python
import eazy_data_viz as edv
import pandas as pd

df = edv.sample_df()
pairs = df.groupby(["大区", "渠道"], as_index=False)["订单数"].sum()
pairs.columns = ["source", "target", "value"]
chart = edv.graph(pairs, source="source", target="target", value="value", height=520)
chart.save("examples/output/graph_3.html")
```

**输出**：4 个大区 × 3 个渠道共 12 条边，力导向让连接多的大区靠近中心；点与边均支持拖拽（节点可手动挪位）。

### 示例 4：深色主题与自定义配色

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.graph(df, source="产品", target="渠道", value="销售额", theme="dark")
chart.palette("morandi")
chart.save("examples/output/graph_4.html")
```

**输出**：深色背景 + 莫兰迪色节点，连线透明度 0.55；文字与 tooltip 自动适配深色。

### 示例 5：联动：点击节点过滤明细

```python
import eazy_data_viz as edv

df = edv.sample_df()
g = edv.graph(df, source="大区", target="产品", value="订单数", link="g1")
tbl = edv.table(df, columns=["大区", "产品", "订单数"], link="g1", limit=40)
edv.dashboard(g, tbl, title="关系图联动", cols=2).save("examples/output/graph_5.html")
```

**输出**：点击任意节点，右侧表格按“source=该节点”过滤（联动维度固定为 source 列）；点击别的节点会切换过滤值。

## 常见问题 / 注意事项

- **关系图和桑基图怎么选？** 桑基图有明确层级与方向，带宽=流量；关系图无方向、力导向布局，适合多对多网络。两者都读 `source/target/value`，但语义不同：同一份数据换图会得到完全不同的阅读方式。
- **节点位置为什么每次打开都不一样？** 力导向布局从随机初始位置迭代，每次渲染的坐标可能略有差异；这是 ECharts 的默认行为，不是数据问题。
- **节点大小是怎么算的？** 节点值 = 该实体所有边的权重之和（同一条边如果 source/target 都指向它会被累计）；节点直径按 `10 + 26 * sqrt(归一化值)` 映射，`span=0` 时固定 18px。
- **边的粗细怎么映射？** `lineWidth = round((1 + 4*sqrt(边值/最大边值))*10)/10`，最粗 5px、最细接近 1px；所有边透明度 0.55。
- **能只画某个子图吗？** 本函数没有过滤参数。请在传参前先筛选 `data`（例如只保留华东相关行），或聚合掉低频节点。

## 相关图表

| 图表 | 说明 |
| --- | --- |
| [`sankey`](sankey.md) | 桑基图（有方向、有层级的流量） |
| [`sunburst`](sunburst.md) | 旭日图（严格的层级结构） |
| [`quadrant`](quadrant.md) | 四象限散点图（对象定位到二维空间） |
| [`matrix`](matrix.md) | 相关系数矩阵（数值指标之间的关系强度） |

- 回到总览：`docs/EXTRA_CHARTS.md`、`docs/AI_GUIDE.md`
