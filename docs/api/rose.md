# `rose` — 南丁格尔玫瑰图（半径表达大小、角度均分的饼图变体）

玫瑰图把每个类目画成一个角度相同、半径不同的扇区：半径越长代表数值越大。它比普通饼图更容易比较相近的数值，也比柱状图更节省横向空间，适合“一个维度下 6~12 个类目”的构成对比。

本质上它仍是“部分与整体”的图：所有扇区共享同一个总数，百分比之和为 100%。

- **适合**：类目数量适中（建议 6~12 个）、想同时表达“占比”和“排名”的场景，例如大区销售构成、产品线订单结构。
- **不适合**：需要精确比较数值、类目超过 15 个、含负值或跨多个维度的场景，请改用 `bar` 或 `sunburst`。

> 本页所有示例均可直接复制运行：先 `import eazy_data_viz as edv`，再 `df = edv.sample_df()`。

## 函数签名

```python
eazy_data_viz.rose(
    data,
    names,
    values=None,
    *,
    donut=False,
    agg='sum',
    sort='desc',
    top_n=None,
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    xlim=None,
    ylim=None,
    fmt='compact',
    height=380,
    theme='light',
    legend=True,
    labels=True,
    zoom=False,
    drill=None,
    link=None,
    max_rows=200000,
) -> Chart
```

参数按签名顺序：`data` → 本图专有参数 → 关键字参数（`*` 之后全部只能按关键字传）。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | pandas.DataFrame（也接受 dict / list，内部会转成 DataFrame） | 无 | 是 | 数据源（DataFrame） |
| `names` | str | 无 | 是 | 类目列（决定扇区名称） |
| `values` | str 或 None | None | 否 | 数值列（决定扇区半径） |
| `donut` | bool | False | 否 | 是否画成环形玫瑰 |
| `agg` | str | 'sum' | 否 | 聚合方式（同一类目多条记录时如何合并） |
| `sort` | str 或 None | 'desc' | 否 | 排序方式 |
| `top_n` | int 或 None | None | 否 | 只保留前 N 项 |
| `title` | str 或 None | None | 否 | 图表主标题 |
| `subtitle` | str 或 None | None | 否 | 副标题（口径/单位/时间范围） |
| `xtitle` | str 或 None | None | 否 | X 轴标题 |
| `ytitle` | str 或 None | None | 否 | Y 轴标题 |
| `xlim` | tuple[float, float] 或 list[float] 或 None | None | 否 | X 轴取值范围 |
| `ylim` | tuple[float, float] 或 list[float] 或 None | None | 否 | Y 轴取值范围 |
| `fmt` | str | 'compact' | 否 | 数值格式（tooltip / 标签） |
| `height` | int | 380 | 否 | 画布高度（像素） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | str | 'light' | 否 | 主题（浅色 / 深色） |
| `legend` | bool 或 None | True | 否 | 是否显示图例 |
| `labels` | bool | True | 否 | 是否显示数据标签 |
| `zoom` | bool 或 str | False | 否 | 缩放/漫游 |
| `drill` | str 或 list[str] 或 None | None | 否 | 下钻维度链 |
| `link` | str 或 None | None | 否 | 联动分组名 |
| `max_rows` | int | 200000 | 否 | 嵌入前端的最大行数 |

> 共 22 个参数。签名里 `*` 之后是 keyword-only，必须写参数名；`data` 之前的位置参数（本图专有）可以按位置传。

## 参数详解

### `data` — 数据源（DataFrame）（`pandas.DataFrame`，必填）

- **作用**：图的原始数据。函数会按参数名从里面取列：`data` 既可以是 `pandas.DataFrame`，也可以是 `dict`（列名 → 值序列）或 `list`（记录列表），内部通过 `ensure_frame()` 统一转换。转换后必须至少有 1 行，否则报 `ValueError`。每张图最多嵌入 40 列（`MAX_COLS=40`），超过的部分会被丢弃并写入 `chart.warnings["warnings"]`。
- **建议**：首选 `pandas.DataFrame`；列名建议保持唯一、非空，中文列名可以直接用。 数值列用数值 dtype（`int64/float64`）；文本数字请先 `pd.to_numeric()`。 日期列用 `datetime64[ns]`（或可被 `pd.to_datetime()` 解析的字符串）。 作图前先处理空值：不同图对空值的策略不同（见各函数“常见问题”）。
- **示例**：`edv.rose(data=df, names="大区", values="销售额")`
- **报错**：传入空 DataFrame：`ValueError: 数据为空（0 行），无法绘图。`；传入 `None`：`ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`

### `names` — 类目列（决定扇区名称）（`str`，必填）

- **作用**：每个不同取值对应一个扇区，扇区名直接显示在标签和 tooltip 中。必须是 `data` 中真实存在的列；缺失值会显示为 `(空)` 并被当作一个独立类目。
- **建议**：选低基数分类列：`大区`、`产品`、`渠道`（4~8 个取值最舒服）。 `省份`、`城市` 这类高基数列请配合 `top_n` 使用。 如果要按数值分档，先 `pd.cut()` 造一列再传进来。
- **示例**：`edv.rose(df, values="销售额", names="大区")`
- **报错**：列名写错：`KeyError: "names（类目）列 '不存在' 不存在。当前可用的列有：日期, 月份, 大区, 省份, 城市, 产品, 渠道, 销售额, 订单数, 利润, 客户数"`

### `values` — 数值列（决定扇区半径）（`str | None`，默认 `None`）

- **作用**：用于计算每个扇区大小的数值列，必须能转成数值（`int/float`，或 ≥99% 可解析的文本数字）。不传（`None`）时函数会把 `agg` 强制为 `count`，扇区大小=该类的记录条数，适合“只看分布不看金额”。
- **建议**：金额/数量类指标：`销售额`、`订单数`、`利润`。 想看记录条数就省略该参数，不要手工造一列 1。 同一张图不要再混入百分比列，占比由图形自动计算。
- **示例**：`edv.rose(df, names="大区", values="销售额")`
- **报错**：传文本列：`TypeError: values（数值）列 '产品' 需要是数值类型（当前是文本，例如 ['智能终端', '云服务', '行业软件']）。请先用 pd.to_numeric() 清洗，或换一列。`；传日期列：`TypeError: values（数值）列 '日期' 需要是数值类型，但当前是日期时间类型。请换一列。`

### `donut` — 是否画成环形玫瑰（`bool`，默认 `False`）

- **作用**：`False`（默认）时扇区从圆心开始（半径 `0%~70%`）；`True` 时挖空中心（半径 `38%~70%`），适合在中心放标题/总计，视觉更轻。
- **建议**：需要展示总数或口径说明时用 `donut=True`（中心留白但不要塞太多字）。 扇区很多时环形会显得更干净。
- **示例**：`edv.rose(df, names="大区", values="销售额", donut=True)`
- **报错**：无校验：任意真值都按环形渲染，`donut="no"` 也会是 `True`。

### `agg` — 聚合方式（同一类目多条记录时如何合并）（`str`，默认 `'sum'`）

- **作用**：同一分类下有多条记录时，把数值列合成一个数的方法。可选：`sum`（默认）、`mean`、`count`、`max`、`min`、`median`。当函数没有拿到数值列（例如没传 `values`/`value`）时，内部会把 `agg` 强制为 `count`，按记录条数统计。 本图实现：未传 `values` 时内部把 `agg` 强制为 `count`（扇区值=记录条数）；传了 `values` 时按 `agg` 聚合。
- **建议**：金额、订单数用 `sum`；单价、率值用 `mean` 或 `median`。 想看“有多少条记录”就传 `agg="count"`，此时数值列只作存在性检查。 `median` 对极端值更稳健，适合客单价、利润率这类偏态指标。
- **示例**：`edv.rose(df, names="大区", values="销售额", agg="mean")`
- **报错**：`agg="average"`：`ValueError: agg='average' 不支持，可选：sum, mean, count, max, min, median`

### `sort` — 排序方式（`str | None`，默认 `'desc'`）

- **作用**：控制分类的排列顺序。本库只认 `"asc"`、`"desc"`、`"x"`、`"none"` 四种语义，但**不做枚举校验**：传其他字符串不会报错，会静默按该图默认顺序渲染。 本图实现：默认 `"desc"`（按扇区值降序）；传 `"asc"` 升序；其他值一律按降序处理。
- **建议**：排行榜用 `asc/desc`；时间序列用 `x`（按列顺序/时间升序）。 需要保持数据原始顺序时传 `sort="none"`。 分类是 `pd.Categorical`（如 `月份`）时，`x` 会按分类顺序而不是字母序。
- **示例**：`edv.rose(df, names="大区", values="销售额", sort="asc")`
- **报错**：不存在的值不报错：`sort="DESC"` 会被忽略并按默认顺序渲染（大小写敏感）。；对不读取 `sort` 的图（如 pyramid/sunburst/sankey）传任何值都不会改变图形。

### `top_n` — 只保留前 N 项（`int | None`，默认 `None`）

- **作用**：按当前排序只保留前 N 个类目，`None`（默认）表示全部保留。必须是 ≥1 的整数（`bool` 不算）。不同函数对“多出来的部分”处理不同：rose 会把剩余项合并成“其他”，wordcloud 直接截断，其余函数多数不读取该字段。 本图实现：生效。保留前 N 个扇区，其余合并为一个名为“其他”的扇区（值=剩余之和）。
- **建议**：类目超过 12 个时用 `top_n` 收敛，避免标签重叠。 玫瑰图配 `top_n` 会得到“其他”扇区，其余图不会。 配合 `sort="desc"` 使用才有“前 N 大”的含义。
- **示例**：`edv.rose(df, names="大区", values="销售额", top_n=5)`
- **报错**：`top_n=0`：`ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`；`top_n=True`：同样报错（`bool` 被显式拒绝）。

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在卡片顶部的主标题。传 `None` 时使用函数内置的自动标题；传字符串则完全覆盖自动标题。标题只影响展示，不参与数据聚合与排序。
- **建议**：建议 8~18 个汉字，写清“指标 + 维度 + 口径”，例如 `销售额 按 大区`。 时间范围、币种、口径放在 `subtitle`，不要全部堆进标题。 标题是单行布局，过长会被卡片宽度截断，不建议加换行符。
- **示例**：`edv.rose(df, names="大区", values="销售额", title="华东区销售构成")`

### `subtitle` — 副标题（口径/单位/时间范围）（`str | None`，默认 `None`）

- **作用**：标题下方的第二行说明，常用于补充统计口径、单位、时间范围或“较上期 +8%”这类结论。默认 `None`，不显示副标题；传空字符串等同于不显示。
- **建议**：写口径而不重复标题，例如 `2024 年 1-12 月 · 含税`。 颜色比标题浅，信息量控制在 30 字以内。 需要换行时直接写 `\n` 不会被解析成 HTML，建议保持单行。
- **示例**：`edv.rose(df, names="大区", values="销售额", subtitle="2024 年 1-12 月 · 含税")`

### `xtitle` — X 轴标题（`str | None`，默认 `None`）

- **作用**：横轴标题。传 `None` 时横轴使用列名作为轴名；传字符串则覆盖。该字段只对直角坐标系有效（玫瑰图/旭日图/树图/关系图等没有 X 轴的图形不会显示）。 本图实现：**不生效**（极坐标没有 X 轴）；`ytitle` 会作为 tooltip 中数值行的标签。
- **建议**：写字段含义而不是字段名，例如 `日期`、`大区`、`广告投入（万元）`。 带单位的量把单位写进轴标题，数值格式交给 `fmt`。 分类轴很短时可以不写轴标题，避免和类目标签重复。
- **示例**：`edv.rose(df, names="大区", values="销售额", xtitle="日期")`

### `ytitle` — Y 轴标题（`str | None`，默认 `None`）

- **作用**：纵轴标题。传 `None` 时纵轴使用数值列名作为轴名；传字符串则覆盖。部分无直角坐标系的图会把 `ytitle` 用在 tooltip 的数值行标签上。 本图实现：生效在 tooltip（数值行标签），不出现在坐标轴上；`None` 时用 `values` 列名，未传值时用“数量”。
- **建议**：带单位，例如 `销售额（元）`、`订单数（单）`。 百分比的图直接写 `占比`，并把 `fmt="percent"`。 与 `xtitle` 风格保持一致。
- **示例**：`edv.rose(df, names="大区", values="销售额", ytitle="销售额（元）")`

### `xlim` — X 轴取值范围（`tuple[float, float] | list[float] | None`，默认 `None`）

- **作用**：把 X 轴限制在 `(最小值, 最大值)`。接受 2 元 `list/tuple`，也接受元素为 `None` 的 2 元组（表示该侧自动）；若 `最小值 > 最大值` 会自动交换。非法长度会报错。 本图实现：**不生效**（极坐标没有轴范围）。
- **建议**：数值散点/回归图用 `xlim` 聚焦重点区间，避免极端值把点压成一团。 分类轴（`x` 是文本/日期）上该参数无效。 先看数据范围（`df["销售额"].min()`）再给范围，不要凭感觉截断。
- **示例**：`edv.rose(df, names="大区", values="销售额", xlim=(0, 3000))`
- **报错**：`xlim=(1, 2, 3)`：`ValueError: xlim 需要是 (最小值, 最大值) 两元组，例如 xlim=(0, 100)`；`xlim="0,100"`（字符串）同样按长度错误报上面这条。

### `ylim` — Y 轴取值范围（`tuple[float, float] | list[float] | None`，默认 `None`）

- **作用**：把 Y 轴限制在 `(最小值, 最大值)`，规则同 `xlim`（2 元组、自动交换、`None` 表示该侧自动）。注意：`ylim` 只裁剪显示范围，不会过滤数据，tooltip 仍显示真实值。 本图实现：**不生效**（极坐标没有轴范围）。
- **建议**：需要强调差异时用 `ylim` 放大局部，但不要把 0 截掉造成误读。 含负值的图（利润、增长）要把负区间留给 `ylim=(..., ...)`。 堆叠/河流图用 `ylim` 固定上界，多张图并排时更可比。
- **示例**：`edv.rose(df, names="大区", values="销售额", ylim=(-500, 2500))`
- **报错**：`ylim=(0, "高")`：`ValueError: ylim 需要是 (最小值, 最大值) 两元组，例如 ylim=(0, 100)`

### `fmt` — 数值格式（tooltip / 标签）（`str`，默认 `'compact'`）

- **作用**：控制数值在 tooltip、数据标签、右端读数里的显示格式，不改变原始数据。可选值：`compact`（默认，≥1 亿显示“x.x亿”、≥1 万显示“x.x万”、否则千分位）、`thousands`（千分位，如 `1,234,567`）、`raw`（原样，最多 3 位小数）、`percent`（一位小数加 `%`，如 `12.3%`）、`currency`（`¥` + 千分位 + 两位小数）。 本图实现：控制 tooltip 中的数值和占比；扇区标签固定显示 `{类目}\n{百分比}%`。
- **建议**：金额大数用 `compact`，表格/财务口径用 `thousands` 或 `currency`。 已经是百分数的列用 `percent`，不要再乘 100。 同一页多张图保持一致的 `fmt`，避免“万/千分位”混排。
- **示例**：`edv.rose(df, names="大区", values="销售额", fmt="thousands")`
- **报错**：`fmt="commas"`：`ValueError: fmt='commas' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）（`int`，默认 `380`）

- **作用**：单张图的容器高度，单位像素，最小 120。不同函数的默认高度不同（本函数默认值见参数总览）。高度只影响画布，不改变数据；图例/标题/坐标轴会自动占用内部空间。
- **建议**：普通看板 320~460；层级图/关系图建议 ≥420。 多张图并排时高度取一致，视觉更整齐。 `height` 小于 120 会直接报错，不要用它做“隐藏图”。
- **示例**：`edv.rose(df, names="大区", values="销售额", height=520)`
- **报错**：`height=100`：`ValueError: height 至少 120（像素），收到 100`；`height="400"`：同样报错（必须是 `int/float`）。

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题（浅色 / 深色）（`str`，默认 `'light'`）

- **作用**：页面主题，只支持 `"light"`（默认，白底深字）和 `"dark"`（深底浅字）。主题会同时改变背景、文字、坐标轴、tooltip 和默认色板的取色（`theme.palette`）。
- **建议**：常规报表/打印用 `light`；大屏、夜间模式用 `dark`。 多图看板统一主题，不要一张亮一张暗。 深色下避免使用低饱和的 `morandi` 色板，对比度会不够。
- **示例**：`edv.rose(df, names="大区", values="销售额", theme="dark")`
- **报错**：`theme="blue"`：`ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `legend` — 是否显示图例（`bool | None`，默认 `True`）

- **作用**：是否显示图例。`None` 表示“按语义自动决定”（有色分组时显示、没有分组时隐藏），`True`/`False` 为强制开关。只有真正用颜色/名称区分系列的函数才会生效。 本图实现：默认 `True`，图例在右侧竖排、可滚动；`False` 关闭图例（扇区仍带标签）。
- **建议**：类目多且颜色即含义（产品、渠道）时保留图例。 图例项超过 10 个时图例会滚动，建议先 `top_n` 或合并小类。 单系列图关闭图例，把空间留给图形。
- **示例**：`edv.rose(df, names="大区", values="销售额", legend=False)`
- **报错**：无校验：传非布尔值会经 `bool()` 转换（非空字符串为 `True`）。

### `labels` — 是否显示数据标签（`bool`，默认 `True`）

- **作用**：是否在图形上直接显示文字标签（类目名/数值/百分比）。默认值因函数而异；有的函数固定显示标签、不支持关闭。 本图实现：默认 `True`，显示“类目名 + 百分比”标签；`False` 关闭标签和引导线。
- **建议**：类目 ≤8 个时打开标签，读者不用来回看 tooltip。 数据密集（散点、关系图）时关闭，避免文字糊成一片。 百分比标签通常配合 `fmt="percent"`。
- **示例**：`edv.rose(df, names="大区", values="销售额", labels=False)`
- **报错**：无校验：会经 `bool()` 转换，传 `"no"` 也是 `True`。

### `zoom` — 缩放/漫游（`bool | str`，默认 `False`）

- **作用**：是否开启缩放。多数函数接受 `bool`；`candlestick` 默认 `"auto"`，表示分类数超过 30 时自动显示底部缩放条。不支持缩放的图会接受该参数但不产生效果。 本图实现：**不生效**。饼/玫瑰图是极坐标图，没有缩放。
- **建议**：时间序列很长（>60 点）时用 `zoom=True` 或放到 `candlestick` 的 `"auto"`。 层级/关系图本身可拖拽缩放，不必再开 `zoom`。 截图/打印场景关掉缩放，画面更干净。
- **示例**：`edv.rose(df, names="大区", values="销售额", zoom=True)`

### `drill` — 下钻维度链（`str | list[str] | None`，默认 `None`）

- **作用**：配置点击下钻：传列名或列名列表（第一层就是当前分类维度）。点击图形后，工具栏会出现面包屑（全部 / 各层取值），其他图表按当前层过滤。默认 `None` 表示不开启。本库只有少数函数暴露该参数（本函数是否支持见参数总览）。 本图实现：唯一暴露 `drill` 的结构图。注意：点击后只有工具栏面包屑和其他图表的过滤在变，玫瑰图本身始终按 `names` 聚合（不会自动切换到下一层维度），属于“部分生效”。
- **建议**：按“大区 → 产品 → 渠道”这类真实层级配置，最多 3 层。 下钻列必须在 `data` 里存在，否则抛 `KeyError`。 下钻是页面内交互，`save()` 出来的 HTML 里同样可用（需在浏览器打开）。
- **示例**：`edv.rose(df, names="大区", values="销售额", drill=["产品"])`
- **报错**：`drill=[]`：`ValueError: drill 不能是空列表；不需要下钻请传 drill=None。`；`drill=["不存在"]`：`KeyError: 下钻维度列 '不存在' 不存在。当前可用的列有：...`

### `link` — 联动分组名（`str | None`，默认 `None`）

- **作用**：把多张图放进同一个联动组：点击某张图的类目，同组中包含该维度列的其他图会按该值过滤。同一个组名（如 `"g1"`）即可联动；默认 `None` 不联动。注意：`table`/`wordcloud` 是 HTML 渲染，只能作为**被联动方**，点击它们不会触发联动。 本图实现：可作为联动发起方（点击扇区），也可被同组其他图过滤。
- **建议**：同一看板里的明细表用同一个 `link` 组名，点图即可筛表。 联动维度由点击的图决定，各图尽量共享同一列（如 `产品`）。 组名建议用有含义的英文/拼音，不要用随机串。
- **示例**：`edv.rose(df, names="大区", values="销售额", link="g1")`
- **报错**：无校验：传数字/对象会原样写入 spec，JS 端作为对象键使用，建议只传字符串。

### `max_rows` — 嵌入前端的最大行数（`int`，默认 `200000`）

- **作用**：Python 侧只把前 `max_rows` 行（默认 20000）的数据嵌入 HTML，超过时按均匀间隔抽样，并把提示写入 `chart.warnings["warnings"]`。`table` 特殊：默认 200，且最终最多嵌入 200 行。抽样只发生在“嵌入”阶段，不影响函数内已经算好的统计（如相关系数、回归系数）。
- **建议**：前端交互图保持默认 20000 即可；超大表用 `table(max_rows=...)` 控制体积。 需要完整数据时导出 Excel/CSV，不要让 HTML 承担全量数据。 抽样后 tooltip 的明细行数会变少，但聚合图的总量不受影响。
- **示例**：`edv.rose(df, names="大区", values="销售额", max_rows=500)`
- **报错**：无校验：传 `0` 或负数会得到空数据（图形空白），建议传正整数。

## 返回值

返回 `eazy_data_viz.Chart` 对象（`chart.spec` 是完整的渲染 spec，`chart.data` 是嵌入前端的数据）。

- 通用方法：`chart.save(path)` 写单文件 HTML、`chart.to_html()` 返回字符串、`chart.palette(name)` 链式换色、`chart.show()` 在浏览器打开；`chart.warnings` 记录采样等降级提示（详见 [交互与联动指南](../guides/06-interaction.md)）。

本图的关键 spec 字段（`chart.spec`）：

| 字段 | 含义 |
| --- | --- |
| `type` | 固定为 `"rose"`。 |
| `roles` | `{"names": 类目列, "value": 数值列或 None}`。 |
| `donut` | 是否环形；`True` 时 JS 用内半径 38%。 |
| `sort` | `"asc"` 升序，其余值一律降序；仅影响扇区排列。 |
| `topN` | 保留的扇区数；溢出项在 JS 端合并为“其他”扇区。 |
| `labels / legend` | 数据标签（类目名+百分比）/ 右侧竖排图例的开关。 |
| `agg` | 聚合方式；未传 `values` 时被强制为 `"count"`。 |
| `fmt` | tooltip 数值格式。 |

## 完整示例

以下示例全部基于 `edv.sample_df()`（1500 行、11 列）或由它派生的小表；输出文件写到 `examples/output/`。

### 示例 1：最简玫瑰图

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.rose(df, names="大区", values="销售额")
chart.save("examples/output/rose_1.html")
```

**输出**：四个大区按销售额画成四个等角扇区，半径由销售额决定；右上角自动标题“销售额 构成”，右侧竖排图例列出四大区，扇区外显示“大区名 + 百分比”。

### 示例 2：典型用法：产品线订单结构

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.rose(
    df,
    names="产品",
    values="订单数",
    title="四大产品线订单结构",
    subtitle="按订单数汇总 · 2024 年",
)
chart.save("examples/output/rose_2.html")
```

**输出**：四条产品线各占约 1/4 角度，半径体现订单数差异；标题与副标题替换了自动标题，tooltip 中订单数按 `compact` 格式显示（如 1.2万）。

### 示例 3：进阶：只保留前 5 名并合并“其他”

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.rose(
    df,
    names="省份",
    values="销售额",
    sort="desc",
    top_n=5,
    labels=False,
)
chart.save("examples/output/rose_3.html")
```

**输出**：原本十几个省份只画 6 个扇区：前 5 大省份 + 一个名为“其他”的灰色汇总扇区；关闭标签后图形更干净，鼠标悬停可在 tooltip 看到每个扇区的精确值。

### 示例 4：深色主题 + 单图配色

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.rose(df, names="产品", values="订单数", theme="dark")
chart.palette("morandi")
chart.save("examples/output/rose_4.html")
```

**输出**：深色背景 + 低饱和莫兰迪色扇区，文字自动变为浅色；`chart.palette()` 只影响这一张图，返回 Chart 因此可以链式调用。

### 示例 5：联动：点击扇区过滤明细表

```python
import eazy_data_viz as edv

df = edv.sample_df()
rose = edv.rose(df, names="大区", values="销售额", link="g1")
tbl = edv.table(df, columns=["大区", "产品", "销售额"], link="g1", limit=50)
edv.dashboard(rose, tbl, title="玫瑰图联动明细", cols=2).save("examples/output/rose_5.html")
```

**输出**：左侧玫瑰图、右侧明细表同属 `g1` 联动组；点击某个大区扇区，右侧表格只显示该大区的记录，再次点击空白可恢复。

## 常见问题 / 注意事项

- **玫瑰图和普通饼图有什么区别？** 普通饼图角度不同、半径相同；玫瑰图（`roseType: "radius"`）反过来——角度均分、半径表达数值。所以玫瑰图比较相近数值更灵敏，但读者不能再用“角度”估占比，适合已经给出百分比标签的场景。
- **怎么让扇区不要挤在一起、标签不重叠？** 三件事：① `top_n=6` 左右收敛类目；② `labels=False` 关掉扇区外标签，只留 tooltip；③ `height=460` 以上并给图例留出右侧空间。扇区少于 4 个时反而不要用玫瑰图，饼图更合适。
- **为什么传了 `ytitle` 却没有坐标轴？** 玫瑰图是极坐标图，没有 X/Y 轴。`ytitle` 只作为 tooltip 里数值行的标签出现，`xtitle`、`xlim`、`ylim` 都不会有任何视觉效果。
- **点击扇区后图形为什么没有切换到下一层？** 这是当前实现的已知差异：`drill` 会把下钻状态传给工具栏和其他联动图表，但玫瑰图 builder 始终按 `roles.names` 聚合，不会自动换成 `drill` 的下一列。需要真正的层级下钻请用 `sunburst` 或 `tree`。
- **不传 `values` 会发生什么？** 函数把 `agg` 强制为 `count`，每个扇区=该类目在 `data` 中的记录条数。此时 `sum/mean` 等设置无效；如果只是想看分布，这比手工造一列 `1` 再求和更准确。

## 相关图表

| 图表 | 说明 |
| --- | --- |
| [`pyramid`](pyramid.md) | 金字塔图（同样是“类目 + 单值”的构成图，但用层宽表达大小、可读性更稳） |
| [`sunburst`](sunburst.md) | 旭日图（需要层级构成与真正的下钻时优先用它） |
| [`tree`](tree.md) | 树图（关心层级结构和父子关系而不是占比时用它） |
| [`theme_river`](theme_river.md) | 主题河流图（想看构成随时间变化时用它） |

- 回到总览：`docs/EXTRA_CHARTS.md`、`docs/AI_GUIDE.md`
