# `sankey` — 桑基图（用带宽表达流量大小的有向流向图）

桑基图把 `source → target` 的流量画成一条条粗细不同的带子，带宽与数值成正比，节点按层级自动排布。它擅长回答“东西从哪来、到哪去、各占多少”，例如渠道 → 产品 → 大区的转化与分摊。

每条记录是一条边；同一对 (source, target) 会按 `agg` 聚合。节点总量由流入/流出自动汇总，不需要额外计算。

- **适合**：有明确的方向与流量：渠道→产品、地区→渠道、预算→部门；边数 5~40，节点数 5~30。
- **不适合**：没有方向、或只想看两列交叉计数时用 `matrix`/`heatmap`；层级超过 2 跳时需要手工拼边（见示例 3）。

> 本页所有示例均可直接复制运行：先 `import eazy_data_viz as edv`，再 `df = edv.sample_df()`。

## 函数签名

```python
eazy_data_viz.sankey(
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
| `source` | str | 无 | 是 | 起点列（边的出发节点） |
| `target` | str | 无 | 是 | 终点列（边的到达节点） |
| `value` | str 或 None | None | 否 | 边的权重列 |
| `agg` | str | 'sum' | 否 | 聚合方式（同一类目多条记录时如何合并） |
| `sort` | str 或 None | None | 否 | 排序方式 |
| `top_n` | int 或 None | None | 否 | 只保留前 N 项 |
| `title` | str 或 None | None | 否 | 图表主标题 |
| `subtitle` | str 或 None | None | 否 | 副标题（口径/单位/时间范围） |
| `fmt` | str | 'compact' | 否 | 数值格式（tooltip / 标签） |
| `height` | int | 420 | 否 | 画布高度（像素） |
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
- **示例**：`edv.sankey(data=df, source="渠道", target="产品", value="销售额")`
- **报错**：传入空 DataFrame：`ValueError: 数据为空（0 行），无法绘图。`；传入 `None`：`ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`

### `source` — 起点列（边的出发节点）（`str`，必填）

- **作用**：每个取值是一个起始节点；与 `target` 共同构成有向边。缺失值按 `(空)` 处理。
- **建议**：上游维度：`渠道`、`大区`。 同一列里不要混入下游节点名，否则节点会被合并成一个。 多跳流向需要额外的中间层列（见示例 3 的拼边方法）。
- **示例**：`edv.sankey(df, target="产品", value="销售额", source="渠道")`
- **报错**：不传：`TypeError: sankey() missing 1 required positional argument: 'target'`（source/target 都是必填）；列名写错：`KeyError: "source列 '不存在' 不存在。当前可用的列有：..."`

### `target` — 终点列（边的到达节点）（`str`，必填）

- **作用**：每个取值是一个到达节点。`source == target` 的自环会被 JS 跳过（不画）。
- **建议**：下游维度：`产品`、`大区`。 自环、空值、非正数的边会被静默丢弃，作图前建议先检查。 值必须可加总（流量），不要用率值。
- **示例**：`edv.sankey(df, source="渠道", value="销售额", target="产品")`
- **报错**：列名写错：`KeyError: "target列 '不存在' 不存在。当前可用的列有：..."`

### `value` — 边的权重列（`str | None`，默认 `None`）

- **作用**：决定带子粗细的数值列；不传时 `agg` 被强制为 `count`，粗细=记录条数。同一 (source, target) 的多行按 `agg` 合并，最终值保留 3 位小数。
- **建议**：流量类指标：`销售额`、`订单数`、`客户数`。 非正数会被丢弃：值为 0 或负的边在图上不存在。 不传值时按条数计，适合先看数据是否连成一张网。
- **示例**：`edv.sankey(df, source="渠道", target="产品", value="销售额")`
- **报错**：传文本列：`TypeError: value（数值）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `agg` — 聚合方式（同一类目多条记录时如何合并）（`str`，默认 `'sum'`）

- **作用**：同一分类下有多条记录时，把数值列合成一个数的方法。可选：`sum`（默认）、`mean`、`count`、`max`、`min`、`median`。当函数没有拿到数值列（例如没传 `values`/`value`）时，内部会把 `agg` 强制为 `count`，按记录条数统计。 本图实现：按 `(source, target)` 分组后用 `agg` 聚合流量；未传 `value` 时按记录数 `count`。
- **建议**：金额、订单数用 `sum`；单价、率值用 `mean` 或 `median`。 想看“有多少条记录”就传 `agg="count"`，此时数值列只作存在性检查。 `median` 对极端值更稳健，适合客单价、利润率这类偏态指标。
- **示例**：`edv.sankey(df, source="渠道", target="产品", value="销售额", agg="mean")`
- **报错**：`agg="average"`：`ValueError: agg='average' 不支持，可选：sum, mean, count, max, min, median`

### `sort` — 排序方式（`str | None`，默认 `None`）

- **作用**：控制分类的排列顺序。本库只认 `"asc"`、`"desc"`、`"x"`、`"none"` 四种语义，但**不做枚举校验**：传其他字符串不会报错，会静默按该图默认顺序渲染。 本图实现：**不生效**。流向右左布局由节点层级自动分层，与类目顺序无关。
- **建议**：排行榜用 `asc/desc`；时间序列用 `x`（按列顺序/时间升序）。 需要保持数据原始顺序时传 `sort="none"`。 分类是 `pd.Categorical`（如 `月份`）时，`x` 会按分类顺序而不是字母序。
- **示例**：`edv.sankey(df, source="渠道", target="产品", value="销售额", sort="asc")`
- **报错**：不存在的值不报错：`sort="DESC"` 会被忽略并按默认顺序渲染（大小写敏感）。；对不读取 `sort` 的图（如 pyramid/sunburst/sankey）传任何值都不会改变图形。

### `top_n` — 只保留前 N 项（`int | None`，默认 `None`）

- **作用**：按当前排序只保留前 N 个类目，`None`（默认）表示全部保留。必须是 ≥1 的整数（`bool` 不算）。不同函数对“多出来的部分”处理不同：rose 会把剩余项合并成“其他”，wordcloud 直接截断，其余函数多数不读取该字段。 本图实现：**不生效**。所有 source/target 节点都会绘制。
- **建议**：类目超过 12 个时用 `top_n` 收敛，避免标签重叠。 玫瑰图配 `top_n` 会得到“其他”扇区，其余图不会。 配合 `sort="desc"` 使用才有“前 N 大”的含义。
- **示例**：`edv.sankey(df, source="渠道", target="产品", value="销售额", top_n=5)`
- **报错**：`top_n=0`：`ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`；`top_n=True`：同样报错（`bool` 被显式拒绝）。

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在卡片顶部的主标题。传 `None` 时使用函数内置的自动标题；传字符串则完全覆盖自动标题。标题只影响展示，不参与数据聚合与排序。
- **建议**：建议 8~18 个汉字，写清“指标 + 维度 + 口径”，例如 `销售额 按 大区`。 时间范围、币种、口径放在 `subtitle`，不要全部堆进标题。 标题是单行布局，过长会被卡片宽度截断，不建议加换行符。
- **示例**：`edv.sankey(df, source="渠道", target="产品", value="销售额", title="华东区销售构成")`

### `subtitle` — 副标题（口径/单位/时间范围）（`str | None`，默认 `None`）

- **作用**：标题下方的第二行说明，常用于补充统计口径、单位、时间范围或“较上期 +8%”这类结论。默认 `None`，不显示副标题；传空字符串等同于不显示。
- **建议**：写口径而不重复标题，例如 `2024 年 1-12 月 · 含税`。 颜色比标题浅，信息量控制在 30 字以内。 需要换行时直接写 `\n` 不会被解析成 HTML，建议保持单行。
- **示例**：`edv.sankey(df, source="渠道", target="产品", value="销售额", subtitle="2024 年 1-12 月 · 含税")`

### `fmt` — 数值格式（tooltip / 标签）（`str`，默认 `'compact'`）

- **作用**：控制数值在 tooltip、数据标签、右端读数里的显示格式，不改变原始数据。可选值：`compact`（默认，≥1 亿显示“x.x亿”、≥1 万显示“x.x万”、否则千分位）、`thousands`（千分位，如 `1,234,567`）、`raw`（原样，最多 3 位小数）、`percent`（一位小数加 `%`，如 `12.3%`）、`currency`（`¥` + 千分位 + 两位小数）。 本图实现：控制连线 tooltip 中的流量、节点 tooltip 中的关联总量。
- **建议**：金额大数用 `compact`，表格/财务口径用 `thousands` 或 `currency`。 已经是百分数的列用 `percent`，不要再乘 100。 同一页多张图保持一致的 `fmt`，避免“万/千分位”混排。
- **示例**：`edv.sankey(df, source="渠道", target="产品", value="销售额", fmt="thousands")`
- **报错**：`fmt="commas"`：`ValueError: fmt='commas' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）（`int`，默认 `420`）

- **作用**：单张图的容器高度，单位像素，最小 120。不同函数的默认高度不同（本函数默认值见参数总览）。高度只影响画布，不改变数据；图例/标题/坐标轴会自动占用内部空间。
- **建议**：普通看板 320~460；层级图/关系图建议 ≥420。 多张图并排时高度取一致，视觉更整齐。 `height` 小于 120 会直接报错，不要用它做“隐藏图”。
- **示例**：`edv.sankey(df, source="渠道", target="产品", value="销售额", height=520)`
- **报错**：`height=100`：`ValueError: height 至少 120（像素），收到 100`；`height="400"`：同样报错（必须是 `int/float`）。

### `theme` — 主题（浅色 / 深色）（`str`，默认 `'light'`）

- **作用**：页面主题，只支持 `"light"`（默认，白底深字）和 `"dark"`（深底浅字）。主题会同时改变背景、文字、坐标轴、tooltip 和默认色板的取色（`theme.palette`）。
- **建议**：常规报表/打印用 `light`；大屏、夜间模式用 `dark`。 多图看板统一主题，不要一张亮一张暗。 深色下避免使用低饱和的 `morandi` 色板，对比度会不够。
- **示例**：`edv.sankey(df, source="渠道", target="产品", value="销售额", theme="dark")`
- **报错**：`theme="blue"`：`ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `legend` — 是否显示图例（`bool | None`，默认 `False`）

- **作用**：是否显示图例。`None` 表示“按语义自动决定”（有色分组时显示、没有分组时隐藏），`True`/`False` 为强制开关。只有真正用颜色/名称区分系列的函数才会生效。 本图实现：**不生效**。桑基图不带图例（节点颜色表示层级）。
- **建议**：类目多且颜色即含义（产品、渠道）时保留图例。 图例项超过 10 个时图例会滚动，建议先 `top_n` 或合并小类。 单系列图关闭图例，把空间留给图形。
- **示例**：`edv.sankey(df, source="渠道", target="产品", value="销售额", legend=False)`
- **报错**：无校验：传非布尔值会经 `bool()` 转换（非空字符串为 `True`）。

### `labels` — 是否显示数据标签（`bool`，默认 `True`）

- **作用**：是否在图形上直接显示文字标签（类目名/数值/百分比）。默认值因函数而异；有的函数固定显示标签、不支持关闭。 本图实现：**不生效**。节点标签始终显示。
- **建议**：类目 ≤8 个时打开标签，读者不用来回看 tooltip。 数据密集（散点、关系图）时关闭，避免文字糊成一片。 百分比标签通常配合 `fmt="percent"`。
- **示例**：`edv.sankey(df, source="渠道", target="产品", value="销售额", labels=False)`
- **报错**：无校验：会经 `bool()` 转换，传 `"no"` 也是 `True`。

### `zoom` — 缩放/漫游（`bool | str`，默认 `False`）

- **作用**：是否开启缩放。多数函数接受 `bool`；`candlestick` 默认 `"auto"`，表示分类数超过 30 时自动显示底部缩放条。不支持缩放的图会接受该参数但不产生效果。 本图实现：**不生效**。节点可拖拽，但不是缩放。
- **建议**：时间序列很长（>60 点）时用 `zoom=True` 或放到 `candlestick` 的 `"auto"`。 层级/关系图本身可拖拽缩放，不必再开 `zoom`。 截图/打印场景关掉缩放，画面更干净。
- **示例**：`edv.sankey(df, source="渠道", target="产品", value="销售额", zoom=True)`

### `link` — 联动分组名（`str | None`，默认 `None`）

- **作用**：把多张图放进同一个联动组：点击某张图的类目，同组中包含该维度列的其他图会按该值过滤。同一个组名（如 `"g1"`）即可联动；默认 `None` 不联动。注意：`table`/`wordcloud` 是 HTML 渲染，只能作为**被联动方**，点击它们不会触发联动。 本图实现：点击节点会按 `source` 维度联动。
- **建议**：同一看板里的明细表用同一个 `link` 组名，点图即可筛表。 联动维度由点击的图决定，各图尽量共享同一列（如 `产品`）。 组名建议用有含义的英文/拼音，不要用随机串。
- **示例**：`edv.sankey(df, source="渠道", target="产品", value="销售额", link="g1")`
- **报错**：无校验：传数字/对象会原样写入 spec，JS 端作为对象键使用，建议只传字符串。

### `max_rows` — 嵌入前端的最大行数（`int`，默认 `200000`）

- **作用**：Python 侧只把前 `max_rows` 行（默认 20000）的数据嵌入 HTML，超过时按均匀间隔抽样，并把提示写入 `chart.warnings["warnings"]`。`table` 特殊：默认 200，且最终最多嵌入 200 行。抽样只发生在“嵌入”阶段，不影响函数内已经算好的统计（如相关系数、回归系数）。
- **建议**：前端交互图保持默认 20000 即可；超大表用 `table(max_rows=...)` 控制体积。 需要完整数据时导出 Excel/CSV，不要让 HTML 承担全量数据。 抽样后 tooltip 的明细行数会变少，但聚合图的总量不受影响。
- **示例**：`edv.sankey(df, source="渠道", target="产品", value="销售额", max_rows=500)`
- **报错**：无校验：传 `0` 或负数会得到空数据（图形空白），建议传正整数。

## 返回值

返回 `eazy_data_viz.Chart` 对象（`chart.spec` 是完整的渲染 spec，`chart.data` 是嵌入前端的数据）。

- 通用方法：`chart.save(path)` 写单文件 HTML、`chart.to_html()` 返回字符串、`chart.palette(name)` 链式换色、`chart.show()` 在浏览器打开；`chart.warnings` 记录采样等降级提示（详见 [交互与联动指南](../guides/06-interaction.md)）。

本图的关键 spec 字段（`chart.spec`）：

| 字段 | 含义 |
| --- | --- |
| `type` | 固定为 `"sankey"`。 |
| `roles` | `{"source": 起点列, "target": 终点列, "value": 权重列或 None}`。 |
| `nodes / links` | 由 JS 在浏览器端聚合出的节点与边数组（不在 spec 中，Python 不预计算）。 |
| `agg` | 同一对 (source, target) 的聚合方式；未传 `value` 时强制 `"count"`。 |
| `labels / legend / sort / top_n / zoom` | 签名保留，但当前 builder 固定显示节点标签、不显示图例、不排序也不裁剪。 |

## 完整示例

以下示例全部基于 `edv.sample_df()`（1500 行、11 列）或由它派生的小表；输出文件写到 `examples/output/`。

### 示例 1：最简：渠道 → 产品

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.sankey(df, source="渠道", target="产品", value="销售额")
chart.save("examples/output/sankey_1.html")
```

**输出**：左侧三个渠道节点、右侧四个产品节点，12 条带子按销售额粗细排布；节点颜色按层级取色，悬停带子显示“渠道 → 产品”与金额，悬停节点显示关联总量。

### 示例 2：典型：不传权重，按记录条数

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.sankey(
    df,
    source="大区",
    target="渠道",
    title="大区 → 渠道 记录流向",
    height=460,
)
chart.save("examples/output/sankey_2.html")
```

**输出**：带子粗细=记录条数（`agg="count"`），4×3 共 12 条边；由于数据均匀，各带子粗细接近，适合检查数据覆盖。

### 示例 3：进阶：拼出三层流向（大区 → 产品 → 渠道）

```python
import eazy_data_viz as edv
import pandas as pd

df = edv.sample_df()
e1 = df.groupby(["大区", "产品"], as_index=False)["销售额"].sum()
e1.columns = ["source", "target", "value"]
e2 = df.groupby(["产品", "渠道"], as_index=False)["销售额"].sum()
e2.columns = ["source", "target", "value"]
edges = pd.concat([e1, e2], ignore_index=True)
chart = edv.sankey(edges, source="source", target="target", value="value", height=560)
chart.save("examples/output/sankey_3.html")
```

**输出**：三个层级依次展开：大区 → 产品 → 渠道；“产品”在同名节点上汇合，带宽自动衔接，能看出每个产品再分流到哪些渠道。

### 示例 4：深色主题、货币格式与配色

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.sankey(
    df,
    source="渠道",
    target="产品",
    value="利润",
    fmt="currency",
    theme="dark",
)
chart.palette("echarts")
chart.save("examples/output/sankey_4.html")
```

**输出**：深色背景上彩色带子 + 渐变透明；tooltip 中利润为“¥…”格式，节点标签自动转浅色。

### 示例 5：联动：点击节点过滤明细

```python
import eazy_data_viz as edv

df = edv.sample_df()
sk = edv.sankey(df, source="渠道", target="产品", value="销售额", link="k1")
tbl = edv.table(df, columns=["渠道", "产品", "销售额"], link="k1", limit=40)
edv.dashboard(sk, tbl, title="桑基图联动", cols=2).save("examples/output/sankey_5.html")
```

**输出**：点击某个渠道节点，右侧表格按“渠道=该值”过滤；点击已选中节点可取消。联动维度固定为 `source` 列。

## 常见问题 / 注意事项

- **桑基图和热力图的区别？** 桑基图表达有向流量且带宽可比，适合看“从哪来到哪去”；热力图只表达两维交叉的强度，没有方向。两列交叉计数既可用 sankey 也可用基础 heatmap，后者更紧凑。
- **节点顺序可以手动指定吗？** 不能。JS 使用最长路径分层（入度 0 的层为第 0 层）+ 布局算法自动排布，`sort` 参数未生效。需要固定顺序只能靠数据本身的结构。
- **带宽数值为什么保留 3 位小数？** JS 端对边值做了 `round(3)` 处理，避免浮点尾数导致的 tooltip 噪声；原始精度仍在 Python 数据里。
- **为什么有的边不见了？** 四类边会被丢弃：非数值（NaN）、值 ≤0、source 为空、source==target 的自环。这是业务上的合理过滤，但会静默发生。
- **`top_n` 能只画前 N 条边吗？** 不能。当前 builder 不读取 `top_n`。需要裁剪请先在 Python 里过滤/聚合边，再传入 `sankey`。

## 相关图表

| 图表 | 说明 |
| --- | --- |
| [`graph`](graph.md) | 关系图（没有方向、任意多对多关系时用它） |
| [`theme_river`](theme_river.md) | 主题河流图（流量随时间变化时用它） |
| [`sunburst`](sunburst.md) | 旭日图（层级占比而不是流量分摊） |
| [`matrix`](matrix.md) | 相关系数矩阵（数值列之间的相关结构） |

- 回到总览：`docs/EXTRA_CHARTS.md`、`docs/AI_GUIDE.md`
