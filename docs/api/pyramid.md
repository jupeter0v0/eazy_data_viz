# `pyramid` — 金字塔图（用漏斗层宽表达大小，自上而下收窄）

金字塔图用一层层水平条（漏斗）表达各个类目的数值，层宽与数值成正比。它天然带有“从上到下逐级收窄”的视觉隐喻，适合渠道转化、客户分层、预算分配这类单向收敛的场景。

注意：本库的 `pyramid` 实际渲染是一个 `funnel`（漏斗）系列，层与层之间没有连线，只是按数值降序排列。

- **适合**：层级/阶段型的构成对比（渠道占比、客户等级、费用分层），层数 3~8 个、数值为正。
- **不适合**：需要精确比较或排序、含负值、想要经典“人口金字塔”（左右对称双列）时不要用本图——本库没有左右双列版本。

> 本页所有示例均可直接复制运行：先 `import eazy_data_viz as edv`，再 `df = edv.sample_df()`。

## 函数签名

```python
eazy_data_viz.pyramid(
    data,
    names,
    values=None,
    *,
    agg=None,
    sort="asc",
    top_n=None,
    title=None,
    subtitle=None,
    fmt="compact",
    height=380,
    abs_height=False,
    theme="light",
    legend=False,
    labels=True,
    zoom=False,
    link=None,
    max_rows=2000000,
) -> Chart
```

参数按签名顺序：`data` → 本图专有参数 → 关键字参数（`*` 之后全部只能按关键字传）。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | pandas.DataFrame（也接受 dict / list，内部会转成 DataFrame） | 无 | 是 | 数据源（DataFrame） |
| `names` | str | 无 | 是 | 类目列（每层名称） |
| `values` | str 或 None | None | 否 | 数值列（决定每层宽度） |
| `agg` | str | 'sum' | 否 | 聚合方式（同一类目多条记录时如何合并） |
| `sort` | str 或 None | 'asc' | 否 | 排序方式 |
| `top_n` | int 或 None | None | 否 | 只保留前 N 项 |
| `title` | str 或 None | None | 否 | 图表主标题 |
| `subtitle` | str 或 None | None | 否 | 副标题（口径/单位/时间范围） |
| `fmt` | str | 'compact' | 否 | 数值格式（tooltip / 标签） |
| `height` | int | 380 | 否 | 画布高度（像素） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | str | 'light' | 否 | 主题（浅色 / 深色） |
| `legend` | bool 或 None | False | 否 | 是否显示图例 |
| `labels` | bool | True | 否 | 是否显示数据标签 |
| `zoom` | bool 或 str | False | 否 | 缩放/漫游 |
| `link` | str 或 None | None | 否 | 联动分组名 |
| `max_rows` | int | 200000 | 否 | 嵌入前端的最大行数 |

> 共 16 个参数。签名里 `*` 之后是 keyword-only，必须写参数名；`data` 之前的位置参数（本图专有）可以按位置传。

## 参数详解

### `data` — 数据源（DataFrame）（`pandas.DataFrame`，必填）

- **作用**：图的原始数据。函数会按参数名从里面取列：`data` 既可以是 `pandas.DataFrame`，也可以是 `dict`（列名 → 值序列）或 `list`（记录列表），内部通过 `ensure_frame()` 统一转换。转换后必须至少有 1 行，否则报 `ValueError`。每张图最多嵌入 40 列（`MAX_COLS=40`），超过的部分会被丢弃并写入 `chart.warnings["warnings"]`。
- **建议**：首选 `pandas.DataFrame`；列名建议保持唯一、非空，中文列名可以直接用。 数值列用数值 dtype（`int64/float64`）；文本数字请先 `pd.to_numeric()`。 日期列用 `datetime64[ns]`（或可被 `pd.to_datetime()` 解析的字符串）。 作图前先处理空值：不同图对空值的策略不同（见各函数“常见问题”）。
- **示例**：`edv.pyramid(data=df, names="产品", values="订单数")`
- **报错**：传入空 DataFrame：`ValueError: 数据为空（0 行），无法绘图。`；传入 `None`：`ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`

### `names` — 类目列（每层名称）（`str`，必填）

- **作用**：每个不同取值对应一层；层名显示在漏斗内部（`labels=True` 时），也是 tooltip 的标题。
- **建议**：层数控制在 3~8 个：`渠道`（3 层）、`大区`（4 层）都很合适。 有自然顺序的分层（如客户等级）建议先把列转成 `pd.Categorical` 并按业务顺序排序。 高基数列（省份、城市）请先聚合或分档。
- **示例**：`edv.pyramid(df, values="订单数", names="产品")`
- **报错**：列名写错：`KeyError: "names（类目）列 '不存在' 不存在。当前可用的列有：日期, 月份, 大区, 省份, 城市, 产品, 渠道, 销售额, 订单数, 利润, 客户数"`

### `values` — 数值列（决定每层宽度）（`str | None`，默认 `None`）

- **作用**：决定每层宽度的数值列，必须为数值类型。不传时 `agg` 被强制为 `count`，层宽=记录条数。
- **建议**：转化人数/订单数/金额都可以；同一张图只用一个指标。 负值会被漏斗渲染得很奇怪，先过滤或取绝对值。 不传 `values` 时不要再传 `agg="sum"`，内部会忽略。
- **示例**：`edv.pyramid(df, names="产品", values="订单数")`
- **报错**：传文本列：`TypeError: values（数值）列 '产品' 需要是数值类型（当前是文本，例如 ['智能终端', '云服务', '行业软件']）。请先用 pd.to_numeric() 清洗，或换一列。`

### `agg` — 聚合方式（同一类目多条记录时如何合并）（`str`，默认 `'sum'`）

- **作用**：同一分类下有多条记录时，把数值列合成一个数的方法。可选：`sum`（默认）、`mean`、`count`、`max`、`min`、`median`。当函数没有拿到数值列（例如没传 `values`/`value`）时，内部会把 `agg` 强制为 `count`，按记录条数统计。 本图实现：未传 `values` 时 `agg` 被强制为 `count`；传了数值列时按 `agg` 聚合。
- **建议**：金额、订单数用 `sum`；单价、率值用 `mean` 或 `median`。 想看“有多少条记录”就传 `agg="count"`，此时数值列只作存在性检查。 `median` 对极端值更稳健，适合客单价、利润率这类偏态指标。
- **示例**：`edv.pyramid(df, names="产品", values="订单数", agg="mean")`
- **报错**：`agg="average"`：`ValueError: agg='average' 不支持，可选：sum, mean, count, unique, max, min, median`

### `sort` — 排序方式（`str | None`，默认 `'asc'`）

- **作用**：控制分类的排列顺序。本库只认 `"asc"`、`"desc"`、`"x"`、`"none"` 四种语义，但**不做枚举校验**：传其他字符串不会报错，会静默按该图默认顺序渲染。 本图实现：默认 `"asc"`，但 **JS 未读取**，金字塔永远是“底部大、顶部小”的值降序渲染。
- **建议**：排行榜用 `asc/desc`；时间序列用 `x`（按列顺序/时间升序）。 需要保持数据原始顺序时传 `sort="none"`。 分类是 `pd.Categorical`（如 `月份`）时，`x` 会按分类顺序而不是字母序。
- **示例**：`edv.pyramid(df, names="产品", values="订单数", sort="asc")`
- **报错**：不存在的值不报错：`sort="DESC"` 会被忽略并按默认顺序渲染（大小写敏感）。；对不读取 `sort` 的图（如 pyramid/sunburst/sankey）传任何值都不会改变图形。

### `top_n` — 只保留前 N 项（`int | None`，默认 `None`）

- **作用**：按当前排序只保留前 N 个类目，`None`（默认）表示全部保留。必须是 ≥1 的整数（`bool` 不算）。不同函数对“多出来的部分”处理不同：rose 会把剩余项合并成“其他”，wordcloud 直接截断，其余函数多数不读取该字段。 本图实现：**不生效**。`spec.topN` 会被写入，但 JS 不读取。
- **建议**：类目超过 12 个时用 `top_n` 收敛，避免标签重叠。 玫瑰图配 `top_n` 会得到“其他”扇区，其余图不会。 配合 `sort="desc"` 使用才有“前 N 大”的含义。
- **示例**：`edv.pyramid(df, names="产品", values="订单数", top_n=5)`
- **报错**：`top_n=0`：`ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`；`top_n=True`：同样报错（`bool` 被显式拒绝）。

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在卡片顶部的主标题。传 `None` 时使用函数内置的自动标题；传字符串则完全覆盖自动标题。标题只影响展示，不参与数据聚合与排序。
- **建议**：建议 8~18 个汉字，写清“指标 + 维度 + 口径”，例如 `销售额 按 大区`。 时间范围、币种、口径放在 `subtitle`，不要全部堆进标题。 标题是单行布局，过长会被卡片宽度截断，不建议加换行符。
- **示例**：`edv.pyramid(df, names="产品", values="订单数", title="华东区销售构成")`

### `subtitle` — 副标题（口径/单位/时间范围）（`str | None`，默认 `None`）

- **作用**：标题下方的第二行说明，常用于补充统计口径、单位、时间范围或“较上期 +8%”这类结论。默认 `None`，不显示副标题；传空字符串等同于不显示。
- **建议**：写口径而不重复标题，例如 `2024 年 1-12 月 · 含税`。 颜色比标题浅，信息量控制在 30 字以内。 需要换行时直接写 `\n` 不会被解析成 HTML，建议保持单行。
- **示例**：`edv.pyramid(df, names="产品", values="订单数", subtitle="2024 年 1-12 月 · 含税")`

### `fmt` — 数值格式（tooltip / 标签）（`str`，默认 `'compact'`）

- **作用**：控制数值在 tooltip、数据标签、右端读数里的显示格式，不改变原始数据。可选值：`compact`（默认，≥1 亿显示“x.x亿”、≥1 万显示“x.x万”、否则千分位）、`thousands`（千分位，如 `1,234,567`）、`raw`（原样，最多 3 位小数）、`percent`（一位小数加 `%`，如 `12.3%`）、`currency`（`¥` + 千分位 + 两位小数）。 本图实现：控制 tooltip 中的数值与占比；漏斗内标签只显示类目名。
- **建议**：金额大数用 `compact`，表格/财务口径用 `thousands` 或 `currency`。 已经是百分数的列用 `percent`，不要再乘 100。 同一页多张图保持一致的 `fmt`，避免“万/千分位”混排。
- **示例**：`edv.pyramid(df, names="产品", values="订单数", fmt="thousands")`
- **报错**：`fmt="commas"`：`ValueError: fmt='commas' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）（`int`，默认 `380`）

- **作用**：单张图的容器高度，单位像素，最小 120。不同函数的默认高度不同（本函数默认值见参数总览）。高度只影响画布，不改变数据；图例/标题/坐标轴会自动占用内部空间。
- **建议**：普通看板 320~460；层级图/关系图建议 ≥420。 多张图并排时高度取一致，视觉更整齐。 `height` 小于 120 会直接报错，不要用它做“隐藏图”。
- **示例**：`edv.pyramid(df, names="产品", values="订单数", height=520)`
- **报错**：`height=100`：`ValueError: height 至少 120（像素），收到 100`；`height="400"`：同样报错（必须是 `int/float`）。

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题（浅色 / 深色）（`str`，默认 `'light'`）

- **作用**：页面主题，只支持 `"light"`（默认，白底深字）和 `"dark"`（深底浅字）。主题会同时改变背景、文字、坐标轴、tooltip 和默认色板的取色（`theme.palette`）。
- **建议**：常规报表/打印用 `light`；大屏、夜间模式用 `dark`。 多图看板统一主题，不要一张亮一张暗。 深色下避免使用低饱和的 `morandi` 色板，对比度会不够。
- **示例**：`edv.pyramid(df, names="产品", values="订单数", theme="dark")`
- **报错**：`theme="blue"`：`ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `legend` — 是否显示图例（`bool | None`，默认 `False`）

- **作用**：是否显示图例。`None` 表示“按语义自动决定”（有色分组时显示、没有分组时隐藏），`True`/`False` 为强制开关。只有真正用颜色/名称区分系列的函数才会生效。 本图实现：**不生效**。漏斗图没有图例，传 `True` 也不会出现。
- **建议**：类目多且颜色即含义（产品、渠道）时保留图例。 图例项超过 10 个时图例会滚动，建议先 `top_n` 或合并小类。 单系列图关闭图例，把空间留给图形。
- **示例**：`edv.pyramid(df, names="产品", values="订单数", legend=False)`
- **报错**：无校验：传非布尔值会经 `bool()` 转换（非空字符串为 `True`）。

### `labels` — 是否显示数据标签（`bool`，默认 `True`）

- **作用**：是否在图形上直接显示文字标签（类目名/数值/百分比）。默认值因函数而异；有的函数固定显示标签、不支持关闭。 本图实现：默认 `True`，在漏斗内部显示类目名（不显示数值）。
- **建议**：类目 ≤8 个时打开标签，读者不用来回看 tooltip。 数据密集（散点、关系图）时关闭，避免文字糊成一片。 百分比标签通常配合 `fmt="percent"`。
- **示例**：`edv.pyramid(df, names="产品", values="订单数", labels=False)`
- **报错**：无校验：会经 `bool()` 转换，传 `"no"` 也是 `True`。

### `zoom` — 缩放/漫游（`bool | str`，默认 `False`）

- **作用**：是否开启缩放。多数函数接受 `bool`；`candlestick` 默认 `"auto"`，表示分类数超过 30 时自动显示底部缩放条。不支持缩放的图会接受该参数但不产生效果。 本图实现：**不生效**。漏斗图没有缩放。
- **建议**：时间序列很长（>60 点）时用 `zoom=True` 或放到 `candlestick` 的 `"auto"`。 层级/关系图本身可拖拽缩放，不必再开 `zoom`。 截图/打印场景关掉缩放，画面更干净。
- **示例**：`edv.pyramid(df, names="产品", values="订单数", zoom=True)`

### `link` — 联动分组名（`str | None`，默认 `None`）

- **作用**：把多张图放进同一个联动组：点击某张图的类目，同组中包含该维度列的其他图会按该值过滤。同一个组名（如 `"g1"`）即可联动；默认 `None` 不联动。注意：`table`/`wordcloud` 是 HTML 渲染，只能作为**被联动方**，点击它们不会触发联动。 本图实现：点击漏斗层会按 `names` 维度联动同组图表。
- **建议**：同一看板里的明细表用同一个 `link` 组名，点图即可筛表。 联动维度由点击的图决定，各图尽量共享同一列（如 `产品`）。 组名建议用有含义的英文/拼音，不要用随机串。
- **示例**：`edv.pyramid(df, names="产品", values="订单数", link="g1")`
- **报错**：无校验：传数字/对象会原样写入 spec，JS 端作为对象键使用，建议只传字符串。

### `max_rows` — 嵌入前端的最大行数（`int`，默认 `2000000`）

- **作用**：Python 侧只把前 `max_rows` 行（默认 20000）的数据嵌入 HTML，超过时按均匀间隔抽样，并把提示写入 `chart.warnings["warnings"]`。`table` 特殊：默认 200，且最终最多嵌入 200 行。抽样只发生在“嵌入”阶段，不影响函数内已经算好的统计（如相关系数、回归系数）。
- **建议**：前端交互图保持默认 20000 即可；超大表用 `table(max_rows=...)` 控制体积。 需要完整数据时导出 Excel/CSV，不要让 HTML 承担全量数据。 抽样后 tooltip 的明细行数会变少，但聚合图的总量不受影响。
- **示例**：`edv.pyramid(df, names="产品", values="订单数", max_rows=500)`
- **报错**：无校验：传 `0` 或负数会得到空数据（图形空白），建议传正整数。

## 返回值

返回 `eazy_data_viz.Chart` 对象（`chart.spec` 是完整的渲染 spec，`chart.data` 是嵌入前端的数据）。

- 通用方法：`chart.save(path)` 写单文件 HTML、`chart.to_html()` 返回字符串、`chart.palette(name)` 链式换色、`chart.show()` 在浏览器打开；`chart.warnings` 记录采样等降级提示（详见 [交互与联动指南](../guides/06-interaction.md)）。

本图的关键 spec 字段（`chart.spec`）：

| 字段 | 含义 |
| --- | --- |
| `type` | 固定为 `"pyramid"`。 |
| `roles` | `{"names": 类目列, "value": 数值列或 None}`。 |
| `agg` | 聚合方式；未传 `values` 时被强制为 `"count"`。 |
| `labels` | 是否在漏斗层内显示类目名。 |
| `sort` | 会被写入，但 JS 始终按数值降序渲染（`sort` 不生效）。 |
| `topN` | 会被写入，但 JS 不读取（不生效）。 |

## 完整示例

以下示例全部基于 `edv.sample_df()`（1500 行、11 列）或由它派生的小表；输出文件写到 `examples/output/`。

### 示例 1：最简金字塔

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.pyramid(df, names="大区", values="销售额")
chart.save("examples/output/pyramid_1.html")
```

**输出**：四大区按销售额从大到小排成 4 层漏斗，最上面一层最宽；自动标题“大区 金字塔”，层内显示大区名，悬停显示销售额与占比。

### 示例 2：典型：渠道订单分层

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.pyramid(
    df,
    names="渠道",
    values="订单数",
    title="渠道订单分层",
    subtitle="订单数 · 自上而下递减",
    height=400,
)
chart.save("examples/output/pyramid_2.html")
```

**输出**：三条渠道被画成上宽下窄的漏斗，层间距 2px；副标题补充口径，层内只写渠道名，数值放在 tooltip 里。

### 示例 3：进阶：不传数值，按记录条数分层

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.pyramid(df, names="产品", title="各产品线记录条数")
chart.save("examples/output/pyramid_3.html")
```

**输出**：不传 `values` 时每层宽度=该产品线的记录条数（`agg="count"`）；图例/数值标签都不显示，靠 tooltip 读具体条数。

### 示例 4：深色主题与标签开关

```python
import eazy_data_viz as edv

df = edv.sample_df()
on = edv.pyramid(df, names="渠道", values="利润", theme="dark", labels=True)
on.save("examples/output/pyramid_4.html")
off = edv.pyramid(df, names="渠道", values="利润", theme="dark", labels=False)
off.save("examples/output/pyramid_4.html")
```

**输出**：深色底上两层漏斗对比明显；`labels=True` 时层内写渠道名，`labels=False` 时只剩色块与 tooltip。

### 示例 5：联动：点击漏斗层过滤明细

```python
import eazy_data_viz as edv

df = edv.sample_df()
funnel = edv.pyramid(df, names="产品", values="销售额", link="p1")
tbl = edv.table(df, columns=["产品", "渠道", "销售额"], link="p1", limit=30)
edv.dashboard(funnel, tbl, title="产品结构联动", cols=2).save("examples/output/pyramid_5.html")
```

**输出**：点击某一产品层，右侧表格只保留该产品的记录；漏斗层本身保持原样（联动只做过滤，不重算漏斗）。

## 常见问题 / 注意事项

- **金字塔图和漏斗图、玫瑰图怎么选？** 金字塔/漏斗强调“阶段逐级收敛”，层数少、可读性最好；玫瑰图强调占比和排名；如果每层还有子类目，选 `sunburst`。本库 `pyramid` 渲染的就是漏斗系列，没有左右对称的人口金字塔。
- **为什么 `sort="asc"` 没有让漏斗倒过来？** 当前 JS 明确按数值降序排序（宽的在上面），`spec.sort` 未被读取。想要“上升型”表达，请对数据取负值或改用 `bar` 横向条形图。
- **层数太多怎么处理？** 漏斗层数超过 8 层后，每层高度不足 26px，标签会互相压住。先聚合到 4~6 层（例如把渠道代理并入渠道），或改用 `rose` + `top_n`。
- **`top_n` 为什么不起作用？** 本函数签名保留了 `top_n`，但 JS builder 没有读取 `spec.topN`，所有类目都会绘制。需要截断请在传参前先 `df[df["产品"].isin(top5)]`。
- **不传 `values` 时图例/金额去哪了？** 会按记录条数分层（`agg="count"`），tooltip 里显示“记录数”。如果你看到所有层一样宽，通常说明每类记录数确实相近。

## 相关图表

| 图表 | 说明 |
| --- | --- |
| [`rose`](rose.md) | 南丁格尔玫瑰图（同样表达构成，用半径而不是层宽） |
| [`sunburst`](sunburst.md) | 旭日图（需要层级构成时替代金字塔） |
| [`matrix`](matrix.md) | 相关系数矩阵（层级关系之外的另一种“结构”图） |
| [`wordcloud`](wordcloud.md) | 词云（类目很多、只想看大小排序时的轻量替代） |

- 回到总览：`docs/EXTRA_CHARTS.md`、`docs/AI_GUIDE.md`
