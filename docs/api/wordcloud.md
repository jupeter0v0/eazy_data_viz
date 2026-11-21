# `wordcloud` — 词云（用字号大小表达类目数值的文本云）

词云把类目名按数值大小映射成不同字号，铺排成一团文本云：字越大，值越高。它牺牲精确比较，换取“一眼抓住重点词”的视觉冲击，适合放在汇报首页或看板角落。

默认是纯 HTML/CSS 渲染（传了 `shape` 才切到 canvas，见下文 `shape`），字号按 `13 + 17 * 归一化值` 计算，颜色从调色板循环取。

- **适合**：类目 10~30 个、只想表达“谁更重要”，且这些名字本身就是可读的中文词。
- **不适合**：需要精确比较、类目超过 40 个、或名称很长时不要用；改用 `bar` 或 `table`。

> 本页所有示例均可直接复制运行：先 `import eazy_data_viz as edv`，再 `df = edv.sample_df()`。

## 函数签名

```python
eazy_data_viz.wordcloud(
    data,
    names=None,
    values=None,
    *,
    agg='sum',
    sort=None,
    top_n=30,
    title=None,
    subtitle=None,
    fmt='compact',
    height=360,
    abs_height=False,
    theme='light',
    link=None,
    shape=None,
    max_rows=200000,
) -> Chart
```

参数按签名顺序：`data` → 本图专有参数 → 关键字参数（`*` 之后全部只能按关键字传）。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | pandas.DataFrame（也接受 dict / list，内部会转成 DataFrame） | 无 | 是 | 数据源（DataFrame） |
| `names` | str 或 None | None | 否 | 词/类目列（决定文本内容） |
| `values` | str 或 None | None | 否 | 字号权重列 |
| `agg` | str | 'sum' | 否 | 聚合方式（同一类目多条记录时如何合并） |
| `sort` | str 或 None | None | 否 | 排序方式 |
| `top_n` | int 或 None | 30 | 否 | 只保留前 N 项 |
| `title` | str 或 None | None | 否 | 图表主标题 |
| `subtitle` | str 或 None | None | 否 | 副标题（口径/单位/时间范围） |
| `fmt` | str | 'compact' | 否 | 数值格式（tooltip / 标签） |
| `height` | int | 360 | 否 | 画布高度（像素） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `shape` | str 或 None | None | 否 | 词云形状：内置形状名（circle / cardioid / diamond / triangle / square / star / pentagon / heart）或本地图片路径 |
| `theme` | str | 'light' | 否 | 主题（浅色 / 深色） |
| `link` | str 或 None | None | 否 | 联动分组名 |
| `max_rows` | int | 200000 | 否 | 嵌入前端的最大行数 |

> 共 13 个参数。签名里 `*` 之后是 keyword-only，必须写参数名；`data` 之前的位置参数（本图专有）可以按位置传。

## 参数详解

### `data` — 数据源（DataFrame）（`pandas.DataFrame`，必填）

- **作用**：图的原始数据。函数会按参数名从里面取列：`data` 既可以是 `pandas.DataFrame`，也可以是 `dict`（列名 → 值序列）或 `list`（记录列表），内部通过 `ensure_frame()` 统一转换。转换后必须至少有 1 行，否则报 `ValueError`。每张图最多嵌入 40 列（`MAX_COLS=40`），超过的部分会被丢弃并写入 `chart.warnings["warnings"]`。
- **建议**：首选 `pandas.DataFrame`；列名建议保持唯一、非空，中文列名可以直接用。 数值列用数值 dtype（`int64/float64`）；文本数字请先 `pd.to_numeric()`。 日期列用 `datetime64[ns]`（或可被 `pd.to_datetime()` 解析的字符串）。 作图前先处理空值：不同图对空值的策略不同（见各函数“常见问题”）。
- **示例**：`edv.wordcloud(data=df, names="产品", values="销售额")`
- **报错**：传入空 DataFrame：`ValueError: 数据为空（0 行），无法绘图。`；传入 `None`：`ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`

### `names` — 词/类目列（决定文本内容）（`str | None`，默认 `None`）

- **作用**：每个不同取值是一个词，值决定字号。不传时会自动选 `data` 里第一个分类列（没有则第一个时间列）；如果数据里既无分类也无时间列且未传 `names`，会报错。
- **建议**：低基数、短文本列：`产品`、`大区`、`渠道`。 `城市` 有十几个取值，也适合做词云；再把长名字映射成简称。 不要传连续数值列——每个取值都会成为一个“词”。
- **示例**：`edv.wordcloud(df, values="销售额", names="产品")`
- **报错**：数据里没有分类/时间列且不传 `names`：`ValueError: wordcloud 需要 names（词/类目列），例如 wordcloud(df, names="关键词", values="次数")；当前 DataFrame 里没有分类/时间列。`；列名写错：`KeyError: "names（词/类目）列 '不存在' 不存在。当前可用的列有：..."`

### `values` — 字号权重列（`str | None`，默认 `None`）

- **作用**：数值列；每个词的字号 = 该词聚合值归一化后映射到 13~30px。不传时按记录条数计（`agg="count"`）。只有值 >0 的词会被渲染。
- **建议**：用金额/数量：`销售额`、`订单数`、`客户数`。 极值差距过大时字号会被拉开，必要时先 `np.log1p` 或截断。 值 ≤0 的词直接不显示（负值/零值）。
- **示例**：`edv.wordcloud(df, names="产品", values="销售额")`
- **报错**：传文本列：`TypeError: values（数值）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `agg` — 聚合方式（同一类目多条记录时如何合并）（`str`，默认 `'sum'`）

- **作用**：同一分类下有多条记录时，把数值列合成一个数的方法。可选：`sum`（默认）、`mean`、`count`、`max`、`min`、`median`。当函数没有拿到数值列（例如没传 `values`/`value`）时，内部会把 `agg` 强制为 `count`，按记录条数统计。 本图实现：未传 `values` 时 `agg` 被强制为 `count`（词频=记录条数）；传了数值列时按 `agg` 聚合。
- **建议**：金额、订单数用 `sum`；单价、率值用 `mean` 或 `median`。 想看“有多少条记录”就传 `agg="count"`，此时数值列只作存在性检查。 `median` 对极端值更稳健，适合客单价、利润率这类偏态指标。
- **示例**：`edv.wordcloud(df, names="产品", values="销售额", agg="mean")`
- **报错**：`agg="average"`：`ValueError: agg='average' 不支持，可选：sum, mean, count, unique, max, min, median`

### `sort` — 排序方式（`str | None`，默认 `None`）

- **作用**：控制分类的排列顺序。本库只认 `"asc"`、`"desc"`、`"x"`、`"none"` 四种语义，但**不做枚举校验**：传其他字符串不会报错，会静默按该图默认顺序渲染。 本图实现：**不生效**。词云永远按词值从大到小排布。
- **建议**：排行榜用 `asc/desc`；时间序列用 `x`（按列顺序/时间升序）。 需要保持数据原始顺序时传 `sort="none"`。 分类是 `pd.Categorical`（如 `月份`）时，`x` 会按分类顺序而不是字母序。
- **示例**：`edv.wordcloud(df, names="产品", values="销售额", sort="asc")`
- **报错**：不存在的值不报错：`sort="DESC"` 会被忽略并按默认顺序渲染（大小写敏感）。；对不读取 `sort` 的图（如 pyramid/sunburst/sankey）传任何值都不会改变图形。

### `top_n` — 只保留前 N 项（`int | None`，默认 `30`）

- **作用**：按当前排序只保留前 N 个类目，`None`（默认）表示全部保留。必须是 ≥1 的整数（`bool` 不算）。不同函数对“多出来的部分”处理不同：rose 会把剩余项合并成“其他”，wordcloud 直接截断，其余函数多数不读取该字段。 本图实现：生效。按词值降序只保留前 `top_n` 个词（默认 30）。
- **建议**：类目超过 12 个时用 `top_n` 收敛，避免标签重叠。 玫瑰图配 `top_n` 会得到“其他”扇区，其余图不会。 配合 `sort="desc"` 使用才有“前 N 大”的含义。
- **示例**：`edv.wordcloud(df, names="产品", values="销售额", top_n=5)`
- **报错**：`top_n=0`：`ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`；`top_n=True`：同样报错（`bool` 被显式拒绝）。

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在卡片顶部的主标题。传 `None` 时使用函数内置的自动标题；传字符串则完全覆盖自动标题。标题只影响展示，不参与数据聚合与排序。
- **建议**：建议 8~18 个汉字，写清“指标 + 维度 + 口径”，例如 `销售额 按 大区`。 时间范围、币种、口径放在 `subtitle`，不要全部堆进标题。 标题是单行布局，过长会被卡片宽度截断，不建议加换行符。
- **示例**：`edv.wordcloud(df, names="产品", values="销售额", title="华东区销售构成")`

### `subtitle` — 副标题（口径/单位/时间范围）（`str | None`，默认 `None`）

- **作用**：标题下方的第二行说明，常用于补充统计口径、单位、时间范围或“较上期 +8%”这类结论。默认 `None`，不显示副标题；传空字符串等同于不显示。
- **建议**：写口径而不重复标题，例如 `2024 年 1-12 月 · 含税`。 颜色比标题浅，信息量控制在 30 字以内。 需要换行时直接写 `\n` 不会被解析成 HTML，建议保持单行。
- **示例**：`edv.wordcloud(df, names="产品", values="销售额", subtitle="2024 年 1-12 月 · 含税")`

### `fmt` — 数值格式（tooltip / 标签）（`str`，默认 `'compact'`）

- **作用**：控制数值在 tooltip、数据标签、右端读数里的显示格式，不改变原始数据。可选值：`compact`（默认，≥1 亿显示“x.x亿”、≥1 万显示“x.x万”、否则千分位）、`thousands`（千分位，如 `1,234,567`）、`raw`（原样，最多 3 位小数）、`percent`（一位小数加 `%`，如 `12.3%`）、`currency`（`¥` + 千分位 + 两位小数）。 本图实现：**不生效**。词云只按数值映射字号/透明度，不显示数值文本。
- **建议**：金额大数用 `compact`，表格/财务口径用 `thousands` 或 `currency`。 已经是百分数的列用 `percent`，不要再乘 100。 同一页多张图保持一致的 `fmt`，避免“万/千分位”混排。
- **示例**：`edv.wordcloud(df, names="产品", values="销售额", fmt="thousands")`
- **报错**：`fmt="commas"`：`ValueError: fmt='commas' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）（`int`，默认 `360`）

- **作用**：单张图的容器高度，单位像素，最小 120。不同函数的默认高度不同（本函数默认值见参数总览）。高度只影响画布，不改变数据；图例/标题/坐标轴会自动占用内部空间。
- **建议**：普通看板 320~460；层级图/关系图建议 ≥420。 多张图并排时高度取一致，视觉更整齐。 `height` 小于 120 会直接报错，不要用它做“隐藏图”。
- **示例**：`edv.wordcloud(df, names="产品", values="销售额", height=520)`
- **报错**：`height=100`：`ValueError: height 至少 120（像素），收到 100`；`height="400"`：同样报错（必须是 `int/float`）。

### `shape` — 词云形状（内置形状名或图片路径）（`str | None`，默认 `None`）

- **作用**：不传时是原来的 CSS 词云（铺满卡片、轻量）；传了之后改用 canvas 渲染，词会按形状的轮廓螺旋排布，看上去就像「这些词组成了这个形状」。
- **取值**：内置形状 `circle`、`cardioid`、`diamond`、`triangle`、`square`、`star`、`pentagon`、`heart`（会自动拉伸铺满卡片）；或者一张本地图片的路径（`png` / `jpg` / `jpeg` / `webp` / `gif` / `bmp` / `svg`，≤ 2 MB）——图片会转成 data URI 内联进 HTML，所以别放太大的图。
- **预览**：形状区域会铺一层 7% 透明度的淡淡底影，词铺不满的尖角也能看出轮廓。
- **建议**：词数 25~60 个时效果最好（`top_n` 调大些）；词太少（< 8 个）或名称太长会显得空。窄卡片里建议 `height=320` 以上，形状才展开得开。
- **报错**：`ValueError: wordcloud 的 shape='nope' 既不是内置形状（circle、cardioid、diamond、triangle、square、star、pentagon、heart），也不是存在的图片文件。` / `ValueError: wordcloud 的 shape 图片只支持 .bmp、.gif、.jpeg、.jpg、.png、.svg、.webp，收到 .tiff。` / `ValueError: wordcloud 的 shape 图片不能超过 2 MB（当前 3.4 MB）：图片会整段内联进 HTML。`
- **示例**：`shape="star"`、`shape="heart"`、`shape="assets/logo.png"`

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题（浅色 / 深色）（`str`，默认 `'light'`）

- **作用**：页面主题，只支持 `"light"`（默认，白底深字）和 `"dark"`（深底浅字）。主题会同时改变背景、文字、坐标轴、tooltip 和默认色板的取色（`theme.palette`）。
- **建议**：常规报表/打印用 `light`；大屏、夜间模式用 `dark`。 多图看板统一主题，不要一张亮一张暗。 深色下避免使用低饱和的 `morandi` 色板，对比度会不够。
- **示例**：`edv.wordcloud(df, names="产品", values="销售额", theme="dark")`
- **报错**：`theme="blue"`：`ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `link` — 联动分组名（`str | None`，默认 `None`）

- **作用**：把多张图放进同一个联动组：点击某张图的类目，同组中包含该维度列的其他图会按该值过滤。同一个组名（如 `"g1"`）即可联动；默认 `None` 不联动。注意：`table`/`wordcloud` 是 HTML 渲染，只能作为**被联动方**，点击它们不会触发联动。 本图实现：只能作为被联动方（点击词语不会触发联动）。
- **建议**：同一看板里的明细表用同一个 `link` 组名，点图即可筛表。 联动维度由点击的图决定，各图尽量共享同一列（如 `产品`）。 组名建议用有含义的英文/拼音，不要用随机串。
- **示例**：`edv.wordcloud(df, names="产品", values="销售额", link="g1")`
- **报错**：无校验：传数字/对象会原样写入 spec，JS 端作为对象键使用，建议只传字符串。

### `max_rows` — 嵌入前端的最大行数（`int`，默认 `2000000`）

- **作用**：Python 侧只把前 `max_rows` 行（默认 20000）的数据嵌入 HTML，超过时按均匀间隔抽样，并把提示写入 `chart.warnings["warnings"]`。`table` 特殊：默认 200，且最终最多嵌入 200 行。抽样只发生在“嵌入”阶段，不影响函数内已经算好的统计（如相关系数、回归系数）。
- **建议**：前端交互图保持默认 20000 即可；超大表用 `table(max_rows=...)` 控制体积。 需要完整数据时导出 Excel/CSV，不要让 HTML 承担全量数据。 抽样后 tooltip 的明细行数会变少，但聚合图的总量不受影响。
- **示例**：`edv.wordcloud(df, names="产品", values="销售额", max_rows=500)`
- **报错**：无校验：传 `0` 或负数会得到空数据（图形空白），建议传正整数。

## 返回值

返回 `eazy_data_viz.Chart` 对象（`chart.spec` 是完整的渲染 spec，`chart.data` 是嵌入前端的数据）。

- 通用方法：`chart.save(path)` 写单文件 HTML、`chart.to_html()` 返回字符串、`chart.palette(name)` 链式换色、`chart.show()` 在浏览器打开；`chart.warnings` 记录采样等降级提示（详见 [交互与联动指南](../guides/06-interaction.md)）。

本图的关键 spec 字段（`chart.spec`）：

| 字段 | 含义 |
| --- | --- |
| `type` | 固定为 `"wordcloud"`。 |
| `roles` | `{"names": 词列, "value": 权重列或 None}`。 |
| `topN` | 最多显示多少个词（默认 30；超过部分按值排序后截断）。 |
| `agg` | 同一个词的聚合方式；未传 `values` 时为 `"count"`。 |
| `sort` | 签名保留，但 JS 始终按值降序取前 N 个（排序结果不受该参数影响）。 |
| `fmt` | 签名保留，但词云不显示数值（数值只影响字号），`fmt` 无实际作用。 |

## 完整示例

以下示例全部基于 `edv.sample_df()`（1500 行、11 列）或由它派生的小表；输出文件写到 `examples/output/`。

### 示例 1：最简：产品销售额词云

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.wordcloud(df, names="产品", values="销售额")
chart.save("examples/output/wordcloud_1.html")
```

**输出**：四个产品名按销售额大小显示为不同字号，颜色循环取色板；自动标题“产品 词云”，没有坐标轴与图例。

### 示例 2：典型：城市维度与记录数

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.wordcloud(df, names="城市", title="城市记录热度", height=420)
chart.save("examples/output/wordcloud_2.html")
```

**输出**：不传 `values` 时字号=该城市的记录条数（`agg="count"`）；十几个城市名随机铺排，字号差异反映记录量差异。

### 示例 3：深色主题与配色

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.wordcloud(df, names="渠道", values="客户数", theme="dark")
chart.palette("morandi")
chart.save("examples/output/wordcloud_3.html")
```

**输出**：深色背景上低饱和莫兰迪色文字；文字透明度随数值增大（0.72~1.0），大词更实。

### 示例 4：先聚合再画：两列组合成词

```python
import eazy_data_viz as edv

df = edv.sample_df()
combo = df.copy()
combo["标签"] = combo["大区"] + "·" + combo["渠道"]
chart = edv.wordcloud(combo, names="标签", values="利润", top_n=20, height=460)
chart.save("examples/output/wordcloud_4.html")
```

**输出**：12 个“大区·渠道”组合变成词云；这是词云最实用的进阶用法——把多列拼成有业务含义的短标签。

### 示例 5：联动：词云作为被过滤方

```python
import eazy_data_viz as edv

df = edv.sample_df()
cal = edv.calendar(df, date="日期", value="订单数", link="wc1")
wc = edv.wordcloud(df, names="产品", values="销售额", link="wc1", top_n=4)
edv.dashboard(cal, wc, title="日历 → 词云", cols=2).save("examples/output/wordcloud_5.html")
```

**输出**：日历图点击无法传值（calendar 不支持作为联动源），所以实际不会过滤；但词云可以接收来自其它 ECharts 图表的联动过滤，过滤后字号按剩余数据重算。

> 以上示例对应的可运行脚本见 `examples/charts/wordcloud.py`，运行 `PYTHONPATH=. python examples/charts/wordcloud.py` 会一次性生成全部 HTML。

### 示例 6：按形状排（1.5 新参数）

```python
import eazy_data_viz as edv
import eazy_data_viz.charts_extra as px

df = edv.sample_df()
px.wordcloud(df, names="产品", values="销售额", shape="star", height=340, top_n=30)

# 用一张本地图片当轮廓（logo、素材图都行，≤ 2 MB）
px.wordcloud(df, names="产品", values="销售额", shape="assets/logo.png", height=340)
```

不传 `shape` 时行为完全不变（CSS 排版），所以老代码不用动。

## 常见问题 / 注意事项

- **词云能显示具体数值吗？** 不能。数值只映射为字号，页面上没有数字与 tooltip；需要精确值请用 `table`/`bar`。
- **字号是怎么算的？** `font-size = 13 + round(t * 17)`，其中 `t = (值 - 最小值) / (最大值 - 最小值)`，所以范围是 13~30px；所有词值相同时 `t=0`，全部 13px。
- **为什么有些词不见了？** 三种原因：① 值 ≤0 被过滤；② 超过 `top_n`（默认 30）被截断；③ 聚合后为空。先 print 聚合结果排查。
- **`sort` 能改变词的顺序吗？** 不能。JS 固定按值降序取前 `top_n`，`sort` 未生效；词的位置由 CSS 流式布局决定，不是排序结果。
- **词云能作为联动源吗？** 不能。词云是纯 HTML 渲染，没有注册点击事件；它可以作为被过滤方接收联动，但点击不会触发联动。

## 相关图表

| 图表 | 说明 |
| --- | --- |
| [`table`](table.md) | 明细表（需要精确数值时用它） |
| [`rose`](rose.md) | 南丁格尔玫瑰图（同样表达构成，但有精确比例） |
| [`sunburst`](sunburst.md) | 旭日图（层级构成的占比表达） |
| [`matrix`](matrix.md) | 相关系数矩阵（数值指标之间的关系） |

- 回到总览：`docs/EXTRA_CHARTS.md`、`docs/AI_GUIDE.md`
