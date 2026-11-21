# `theme_river` — 主题河流图（用堆叠面积流表达各分组占比随时间的变化）

主题河流图沿着时间（或有序类目）轴画出多条堆叠的平滑色带，每条色带的厚度代表该分组在当期的数值，整体轮廓则随总量起伏。它特别适合看“结构如何随时间漂移”：某产品线越吃越多、某渠道逐渐萎缩，一眼就能看出来。

注意：本库的 `theme_river` 不是 ECharts 自带的 themeRiver 组件，而是用“堆叠面积 + 类目轴”实现的同款效果，因此 `x` 可以是日期，也可以是月份、季度这类有序类目，不会出现空白。

- **适合**：时间/有序类目 × 分组 × 数值的三元数据，想看分组构成的演化趋势；分组 3~6 个、周期 10~30 个。
- **不适合**：只需要看总量趋势用 line/area；需要看精确数值对比用 bar；分组超过 8 个时色带会细到无法分辨，先用 `top_n` 或合并小类。

> 本页所有示例均可直接复制运行：先 `import eazy_data_viz as edv`，再 `df = edv.sample_df()`。

## 函数签名

```python
eazy_data_viz.theme_river(
    data,
    x,
    color,
    value=None,
    *,
    agg='sum',
    sort=None,
    top_n=None,
    title=None,
    subtitle=None,
    fmt='compact',
    height=380,
    theme='light',
    legend=True,
    labels=False,
    zoom='auto',
    link=None,
    max_rows=200000,
) -> Chart
```

参数按签名顺序：`data` → 本图专有参数 → 关键字参数（`*` 之后全部只能按关键字传）。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | pandas.DataFrame（也接受 dict / list，内部会转成 DataFrame） | 无 | 是 | 数据源（DataFrame） |
| `x` | str | 无 | 是 | 横轴列（时间或有序类目） |
| `color` | str | 无 | 是 | 分组列（决定色带数量） |
| `value` | str 或 None | None | 否 | 数值列（决定色带厚度） |
| `agg` | str | 'sum' | 否 | 聚合方式（同一类目多条记录时如何合并） |
| `sort` | str 或 None | None | 否 | 排序方式 |
| `top_n` | int 或 None | None | 否 | 只保留前 N 项 |
| `title` | str 或 None | None | 否 | 图表主标题 |
| `subtitle` | str 或 None | None | 否 | 副标题（口径/单位/时间范围） |
| `fmt` | str | 'compact' | 否 | 数值格式（tooltip / 标签） |
| `height` | int | 380 | 否 | 画布高度（像素） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | str | 'light' | 否 | 主题（浅色 / 深色） |
| `legend` | bool 或 None | True | 否 | 是否显示图例 |
| `labels` | bool | False | 否 | 是否显示数据标签 |
| `zoom` | bool 或 str | 'auto' | 否 | 缩放/漫游 |
| `link` | str 或 None | None | 否 | 联动分组名 |
| `max_rows` | int | 200000 | 否 | 嵌入前端的最大行数 |

> 共 17 个参数。签名里 `*` 之后是 keyword-only，必须写参数名；`data` 之前的位置参数（本图专有）可以按位置传。

## 参数详解

### `data` — 数据源（DataFrame）（`pandas.DataFrame`，必填）

- **作用**：图的原始数据。函数会按参数名从里面取列：`data` 既可以是 `pandas.DataFrame`，也可以是 `dict`（列名 → 值序列）或 `list`（记录列表），内部通过 `ensure_frame()` 统一转换。转换后必须至少有 1 行，否则报 `ValueError`。每张图最多嵌入 40 列（`MAX_COLS=40`），超过的部分会被丢弃并写入 `chart.warnings["warnings"]`。
- **建议**：首选 `pandas.DataFrame`；列名建议保持唯一、非空，中文列名可以直接用。 数值列用数值 dtype（`int64/float64`）；文本数字请先 `pd.to_numeric()`。 日期列用 `datetime64[ns]`（或可被 `pd.to_datetime()` 解析的字符串）。 作图前先处理空值：不同图对空值的策略不同（见各函数“常见问题”）。
- **示例**：`edv.theme_river(data=df, x="日期", color="产品", value="销售额")`
- **报错**：传入空 DataFrame：`ValueError: 数据为空（0 行），无法绘图。`；传入 `None`：`ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`

### `x` — 横轴列（时间或有序类目）（`str`，必填）

- **作用**：必须是 `data` 中存在的列。数值列会经 `_coerce_numeric`、日期列会经 `_coerce_time` 处理成可读文本，类目列直接按取值。JS 端按“首次出现顺序”排列，若值是日期样式或 `sort` 指定了 `x`，则按值排序。
- **建议**：日期列：`x="日期"`（1500 行逐日数据会得到很密的色带，建议先按周/月聚合）。 有序类目：`x="月份"`（`月份` 是有序分类，排序可靠）。 不要传高基数无序文本列（城市名），横轴会变成几十个无法阅读的刻度。
- **示例**：`edv.theme_river(df, color="产品", value="销售额", x="月份")`
- **报错**：列名写错：`KeyError: "x列 '不存在' 不存在。当前可用的列有：..."`；传日期列但函数期望数值（不适用于本参数）：`TypeError: x 列 '日期' ...`（本函数会自动处理日期，不会触发）

### `color` — 分组列（决定色带数量）（`str`，必填）

- **作用**：每个不同取值对应一条色带，色带颜色按分组顺序从调色板依次取。缺失值会归为 `(空)` 分组。
- **建议**：低基数列：`产品`（4）、`渠道`（3）、`大区`（4）。 分组超过 8 个时先把小类合并成“其他”，否则色带无法辨认。 不要用数值列做 `color`，展会变成几十条细线。
- **示例**：`edv.theme_river(df, x="日期", value="销售额", color="产品")`
- **报错**：列名写错：`KeyError: "color列 '不存在' 不存在。当前可用的列有：..."`

### `value` — 数值列（决定色带厚度）（`str | None`，默认 `None`）

- **作用**：决定每条色带在每期的厚度。不传时 `agg` 被强制为 `count`，厚度=记录条数。同一期里所有分组的数值会堆叠，纵轴是累计值。
- **建议**：可加总指标：`销售额`、`订单数`、`客户数`。 负值会被截断为 0（JS 端 `value<0 → 0`），含负值的指标（利润）请先加偏移或改用其它图。 不传值时不要再传 `agg="sum"`，会被忽略。
- **示例**：`edv.theme_river(df, x="日期", color="产品", value="销售额")`
- **报错**：传文本列：`TypeError: value（数值）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `agg` — 聚合方式（同一类目多条记录时如何合并）（`str`，默认 `'sum'`）

- **作用**：同一分类下有多条记录时，把数值列合成一个数的方法。可选：`sum`（默认）、`mean`、`count`、`max`、`min`、`median`。当函数没有拿到数值列（例如没传 `values`/`value`）时，内部会把 `agg` 强制为 `count`，按记录条数统计。 本图实现：按 `(x, color)` 分组后用 `agg` 聚合；未传 `value` 时强制 `count`。
- **建议**：金额、订单数用 `sum`；单价、率值用 `mean` 或 `median`。 想看“有多少条记录”就传 `agg="count"`，此时数值列只作存在性检查。 `median` 对极端值更稳健，适合客单价、利润率这类偏态指标。
- **示例**：`edv.theme_river(df, x="日期", color="产品", value="销售额", agg="mean")`
- **报错**：`agg="average"`：`ValueError: agg='average' 不支持，可选：sum, mean, count, max, min, median`

### `sort` — 排序方式（`str | None`，默认 `None`）

- **作用**：控制分类的排列顺序。本库只认 `"asc"`、`"desc"`、`"x"`、`"none"` 四种语义，但**不做枚举校验**：传其他字符串不会报错，会静默按该图默认顺序渲染。 本图实现：传 `"x"`/`"asc"`/`"desc"` 会对横轴类目排序；日期型类目会自动按时间升序。
- **建议**：排行榜用 `asc/desc`；时间序列用 `x`（按列顺序/时间升序）。 需要保持数据原始顺序时传 `sort="none"`。 分类是 `pd.Categorical`（如 `月份`）时，`x` 会按分类顺序而不是字母序。
- **示例**：`edv.theme_river(df, x="日期", color="产品", value="销售额", sort="asc")`
- **报错**：不存在的值不报错：`sort="DESC"` 会被忽略并按默认顺序渲染（大小写敏感）。；对不读取 `sort` 的图（如 pyramid/sunburst/sankey）传任何值都不会改变图形。

### `top_n` — 只保留前 N 项（`int | None`，默认 `None`）

- **作用**：按当前排序只保留前 N 个类目，`None`（默认）表示全部保留。必须是 ≥1 的整数（`bool` 不算）。不同函数对“多出来的部分”处理不同：rose 会把剩余项合并成“其他”，wordcloud 直接截断，其余函数多数不读取该字段。 本图实现：**不生效**。所有分组系列都会绘制。
- **建议**：类目超过 12 个时用 `top_n` 收敛，避免标签重叠。 玫瑰图配 `top_n` 会得到“其他”扇区，其余图不会。 配合 `sort="desc"` 使用才有“前 N 大”的含义。
- **示例**：`edv.theme_river(df, x="日期", color="产品", value="销售额", top_n=5)`
- **报错**：`top_n=0`：`ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`；`top_n=True`：同样报错（`bool` 被显式拒绝）。

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在卡片顶部的主标题。传 `None` 时使用函数内置的自动标题；传字符串则完全覆盖自动标题。标题只影响展示，不参与数据聚合与排序。
- **建议**：建议 8~18 个汉字，写清“指标 + 维度 + 口径”，例如 `销售额 按 大区`。 时间范围、币种、口径放在 `subtitle`，不要全部堆进标题。 标题是单行布局，过长会被卡片宽度截断，不建议加换行符。
- **示例**：`edv.theme_river(df, x="日期", color="产品", value="销售额", title="华东区销售构成")`

### `subtitle` — 副标题（口径/单位/时间范围）（`str | None`，默认 `None`）

- **作用**：标题下方的第二行说明，常用于补充统计口径、单位、时间范围或“较上期 +8%”这类结论。默认 `None`，不显示副标题；传空字符串等同于不显示。
- **建议**：写口径而不重复标题，例如 `2024 年 1-12 月 · 含税`。 颜色比标题浅，信息量控制在 30 字以内。 需要换行时直接写 `\n` 不会被解析成 HTML，建议保持单行。
- **示例**：`edv.theme_river(df, x="日期", color="产品", value="销售额", subtitle="2024 年 1-12 月 · 含税")`

### `fmt` — 数值格式（tooltip / 标签）（`str`，默认 `'compact'`）

- **作用**：控制数值在 tooltip、数据标签、右端读数里的显示格式，不改变原始数据。可选值：`compact`（默认，≥1 亿显示“x.x亿”、≥1 万显示“x.x万”、否则千分位）、`thousands`（千分位，如 `1,234,567`）、`raw`（原样，最多 3 位小数）、`percent`（一位小数加 `%`，如 `12.3%`）、`currency`（`¥` + 千分位 + 两位小数）。 本图实现：控制 Y 轴刻度和 tooltip 中的数值。
- **建议**：金额大数用 `compact`，表格/财务口径用 `thousands` 或 `currency`。 已经是百分数的列用 `percent`，不要再乘 100。 同一页多张图保持一致的 `fmt`，避免“万/千分位”混排。
- **示例**：`edv.theme_river(df, x="日期", color="产品", value="销售额", fmt="thousands")`
- **报错**：`fmt="commas"`：`ValueError: fmt='commas' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）（`int`，默认 `380`）

- **作用**：单张图的容器高度，单位像素，最小 120。不同函数的默认高度不同（本函数默认值见参数总览）。高度只影响画布，不改变数据；图例/标题/坐标轴会自动占用内部空间。
- **建议**：普通看板 320~460；层级图/关系图建议 ≥420。 多张图并排时高度取一致，视觉更整齐。 `height` 小于 120 会直接报错，不要用它做“隐藏图”。
- **示例**：`edv.theme_river(df, x="日期", color="产品", value="销售额", height=520)`
- **报错**：`height=100`：`ValueError: height 至少 120（像素），收到 100`；`height="400"`：同样报错（必须是 `int/float`）。

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题（浅色 / 深色）（`str`，默认 `'light'`）

- **作用**：页面主题，只支持 `"light"`（默认，白底深字）和 `"dark"`（深底浅字）。主题会同时改变背景、文字、坐标轴、tooltip 和默认色板的取色（`theme.palette`）。
- **建议**：常规报表/打印用 `light`；大屏、夜间模式用 `dark`。 多图看板统一主题，不要一张亮一张暗。 深色下避免使用低饱和的 `morandi` 色板，对比度会不够。
- **示例**：`edv.theme_river(df, x="日期", color="产品", value="销售额", theme="dark")`
- **报错**：`theme="blue"`：`ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `legend` — 是否显示图例（`bool | None`，默认 `True`）

- **作用**：是否显示图例。`None` 表示“按语义自动决定”（有色分组时显示、没有分组时隐藏），`True`/`False` 为强制开关。只有真正用颜色/名称区分系列的函数才会生效。 本图实现：**不生效**。河流图固定显示顶部图例，无法关闭。
- **建议**：类目多且颜色即含义（产品、渠道）时保留图例。 图例项超过 10 个时图例会滚动，建议先 `top_n` 或合并小类。 单系列图关闭图例，把空间留给图形。
- **示例**：`edv.theme_river(df, x="日期", color="产品", value="销售额", legend=False)`
- **报错**：无校验：传非布尔值会经 `bool()` 转换（非空字符串为 `True`）。

### `labels` — 是否显示数据标签（`bool`，默认 `False`）

- **作用**：是否在图形上直接显示文字标签（类目名/数值/百分比）。默认值因函数而异；有的函数固定显示标签、不支持关闭。 本图实现：**不生效**。河流图不显示数据标签。
- **建议**：类目 ≤8 个时打开标签，读者不用来回看 tooltip。 数据密集（散点、关系图）时关闭，避免文字糊成一片。 百分比标签通常配合 `fmt="percent"`。
- **示例**：`edv.theme_river(df, x="日期", color="产品", value="销售额", labels=False)`
- **报错**：无校验：会经 `bool()` 转换，传 `"no"` 也是 `True`。

### `zoom` — 缩放/漫游（`bool | str`，默认 `'auto'`）

- **作用**：是否开启缩放。多数函数接受 `bool`；`candlestick` 默认 `"auto"`，表示分类数超过 30 时自动显示底部缩放条。不支持缩放的图会接受该参数但不产生效果。 本图实现：**不生效**。横轴是分类轴，没有 dataZoom。
- **建议**：时间序列很长（>60 点）时用 `zoom=True` 或放到 `candlestick` 的 `"auto"`。 层级/关系图本身可拖拽缩放，不必再开 `zoom`。 截图/打印场景关掉缩放，画面更干净。
- **示例**：`edv.theme_river(df, x="日期", color="产品", value="销售额", zoom=True)`

### `link` — 联动分组名（`str | None`，默认 `None`）

- **作用**：把多张图放进同一个联动组：点击某张图的类目，同组中包含该维度列的其他图会按该值过滤。同一个组名（如 `"g1"`）即可联动；默认 `None` 不联动。注意：`table`/`wordcloud` 是 HTML 渲染，只能作为**被联动方**，点击它们不会触发联动。 本图实现：点击面积块（类目）会按 `x` 维度联动。
- **建议**：同一看板里的明细表用同一个 `link` 组名，点图即可筛表。 联动维度由点击的图决定，各图尽量共享同一列（如 `产品`）。 组名建议用有含义的英文/拼音，不要用随机串。
- **示例**：`edv.theme_river(df, x="日期", color="产品", value="销售额", link="g1")`
- **报错**：无校验：传数字/对象会原样写入 spec，JS 端作为对象键使用，建议只传字符串。

### `max_rows` — 嵌入前端的最大行数（`int`，默认 `200000`）

- **作用**：Python 侧只把前 `max_rows` 行（默认 20000）的数据嵌入 HTML，超过时按均匀间隔抽样，并把提示写入 `chart.warnings["warnings"]`。`table` 特殊：默认 200，且最终最多嵌入 200 行。抽样只发生在“嵌入”阶段，不影响函数内已经算好的统计（如相关系数、回归系数）。
- **建议**：前端交互图保持默认 20000 即可；超大表用 `table(max_rows=...)` 控制体积。 需要完整数据时导出 Excel/CSV，不要让 HTML 承担全量数据。 抽样后 tooltip 的明细行数会变少，但聚合图的总量不受影响。
- **示例**：`edv.theme_river(df, x="日期", color="产品", value="销售额", max_rows=500)`
- **报错**：无校验：传 `0` 或负数会得到空数据（图形空白），建议传正整数。

## 返回值

返回 `eazy_data_viz.Chart` 对象（`chart.spec` 是完整的渲染 spec，`chart.data` 是嵌入前端的数据）。

- 通用方法：`chart.save(path)` 写单文件 HTML、`chart.to_html()` 返回字符串、`chart.palette(name)` 链式换色、`chart.show()` 在浏览器打开；`chart.warnings` 记录采样等降级提示（详见 [交互与联动指南](../guides/06-interaction.md)）。

本图的关键 spec 字段（`chart.spec`）：

| 字段 | 含义 |
| --- | --- |
| `type` | 固定为 `"theme_river"`。 |
| `roles` | `{"x": 横轴列, "color": 分组列, "value": 数值列或 None}`。 |
| `sort` | `"x"`/`"asc"`/`"desc"` 或日期样式横轴时，JS 端会对横轴类目排序；`None` 保持首次出现顺序。 |
| `agg` | 聚合方式；未传 `value` 时为 `"count"`。 |
| `legend / labels / zoom / top_n` | 签名保留，但当前 builder 固定显示图例、不显示数据标签、不支持缩放，`top_n` 也不裁剪色带。 |

## 完整示例

以下示例全部基于 `edv.sample_df()`（1500 行、11 列）或由它派生的小表；输出文件写到 `examples/output/`。

### 示例 1：最简河流图：月份 × 产品

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.theme_river(df, x="月份", color="产品", value="销售额")
chart.save("examples/output/theme_river_1.html")
```

**输出**：横轴是 1 月~12 月，四块平滑色带上下堆叠、整体轮廓随销售额起伏；图例固定显示在顶部，悬停某月会列出四产品的当期值与累计纵轴。

### 示例 2：典型：按日期看渠道结构漂移

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.theme_river(
    df,
    x="日期",
    color="渠道",
    value="订单数",
    title="订单渠道结构演化",
    subtitle="2024 全年 · 逐日",
    height=420,
)
chart.save("examples/output/theme_river_2.html")
```

**输出**：横轴是被压缩成日期标签的时间轴，三条渠道色带随时间交替变厚；由于是逐日数据，刻度较密，适合看整体趋势而不是单日精确值。

### 示例 3：进阶：排序 + 数值格式 + 高度

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.theme_river(
    df,
    x="月份",
    color="产品",
    value="销售额",
    sort="x",
    fmt="thousands",
    height=460,
)
chart.save("examples/output/theme_river_3.html")
```

**输出**：横轴按月份类目顺序 1 月→12 月排列（`sort='x'` 触发 JS 端排序），tooltip 数值带千分位，画布更高、四条色带更舒展。

### 示例 4：深色主题与配色

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.theme_river(df, x="月份", color="大区", value="客户数", theme="dark")
chart.palette("morandi")
chart.save("examples/output/theme_river_4.html")
```

**输出**：深色背景上四条低饱和莫兰迪色带，网格与图例自动适配为浅色文字；面积透明度 0.9，重叠处不会过暗。

### 示例 5：联动：点击色带过滤明细

```python
import eazy_data_viz as edv

df = edv.sample_df()
river = edv.theme_river(df, x="月份", color="产品", value="销售额", link="r1")
tbl = edv.table(df, columns=["月份", "产品", "销售额"], link="r1", limit=30)
edv.dashboard(river, tbl, title="河流图联动", cols=2).save("examples/output/theme_river_5.html")
```

**输出**：点击某个横轴刻度（月份）后，右侧表格按月份过滤；点击色带本身不会传值，因为堆叠面积系列的点击语义按横轴类目走。

> 以上示例对应的可运行脚本见 `examples/charts/theme_river.py`，运行 `PYTHONPATH=. python examples/charts/theme_river.py` 会一次性生成全部 HTML。

## 常见问题 / 注意事项

- **主题河流图和堆叠面积图有什么区别？** 数据表达几乎一样，区别在视觉：河流图用平滑、无描边的色带强调“流动感”，适合对外汇报；严格来说本库的实现就是“堆叠平滑面积”，所以 `line/area` 能做的它几乎都能做，反之亦然。
- **为什么 `legend=False` 图例还在？** 当前 builder 无条件调用图例配置，不读取 `spec.legend`。如果图例遮挡内容，可增大 `height` 或减少分组数量。
- **横轴日期太密怎么办？** 先把 `data` 聚合到周/月再画，例如 `df.groupby(["月", "产品"], as_index=False)["销售额"].sum()`；或者直接用 `月份` 做横轴。类目轴会自动抽样显示刻度，但色带仍按原始粒度绘制。
- **`sort` 到底排什么？** 排的是横轴类目顺序（`catOrder`），不是图例顺序。传 `"desc"` 会让月份按数值大小重排，通常只在“x 是类目而非时间”时才有意义。
- **`top_n` 能只显示前 N 个分组吗？** 不能。当前 builder 不读取 `top_n`，所有 `color` 取值都会画。请先在数据里合并小类：把低频分组替换成“其他”。

## 相关图表

| 图表 | 说明 |
| --- | --- |
| [`rose`](rose.md) | 南丁格尔玫瑰图（只看一个时点的构成） |
| [`sunburst`](sunburst.md) | 旭日图（层级构成而不是时间演化） |
| [`trend`](trend.md) | 趋势图（关心总量趋势和拟合线时用它） |
| [`sparkline`](sparkline.md) | 迷你走势图（多组时间序列的紧凑对比） |

- 回到总览：`docs/EXTRA_CHARTS.md`、`docs/AI_GUIDE.md`
