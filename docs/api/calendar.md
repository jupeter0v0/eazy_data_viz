# `calendar` — 日历热力图（按天铺开的年度热力日历）

日历热力图把一整年（或多��）铺成 GitHub 贡献图那样的格式：每个格子是一天，颜色深浅代表当天聚合值。它能一眼看出“哪几天/哪个月特别忙、有没有周期性”，特别适合日粒度的运营数据。

日期列会在 Python 端被标准化为 `YYYY-MM-DD` 字符串，JS 再解析成日粒度；因此像 `2024-03-05 14:22` 这样的时间戳会按“天”归并，不会爆出几千个格子。

- **适合**：日粒度、跨度 1~2 年、想看密度分布（订单量、活跃用户、故障数）。
- **不适合**：数据跨度只有几天、或需要精确比较每天数值时用 `bar`/`line`；跨度超过 2 年格子会变小、可读性下降。

> 本页所有示例均可直接复制运行：先 `import eazy_data_viz as edv`，再 `df = edv.sample_df()`。

## 函数签名

```python
eazy_data_viz.calendar(
    data,
    date,
    value=None,
    *,
    agg='sum',
    sort='x',
    top_n=None,
    title=None,
    subtitle=None,
    fmt='compact',
    height=300,
    theme='light',
    legend=False,
    labels=False,
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
| `date` | str | 无 | 是 | 日期列 |
| `value` | str 或 None | None | 否 | 每天聚合的数值列 |
| `agg` | str | 'sum' | 否 | 聚合方式（同一类目多条记录时如何合并） |
| `sort` | str 或 None | 'x' | 否 | 排序方式 |
| `top_n` | int 或 None | None | 否 | 只保留前 N 项 |
| `title` | str 或 None | None | 否 | 图表主标题 |
| `subtitle` | str 或 None | None | 否 | 副标题（口径/单位/时间范围） |
| `fmt` | str | 'compact' | 否 | 数值格式（tooltip / 标签） |
| `height` | int | 300 | 否 | 画布高度（像素） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | str | 'light' | 否 | 主题（浅色 / 深色） |
| `legend` | bool 或 None | False | 否 | 是否显示图例 |
| `labels` | bool | False | 否 | 是否显示数据标签 |
| `zoom` | bool 或 str | False | 否 | 缩放/漫游 |
| `link` | str 或 None | None | 否 | 联动分组名 |
| `max_rows` | int | 200000 | 否 | 嵌入前端的最大行数 |

> 共 16 个参数。签名里 `*` 之后是 keyword-only，必须写参数名；`data` 之前的位置参数（本图专有）可以按位置传。

## 参数详解

### `data` — 数据源（DataFrame）（`pandas.DataFrame`，必填）

- **作用**：图的原始数据。函数会按参数名从里面取列：`data` 既可以是 `pandas.DataFrame`，也可以是 `dict`（列名 → 值序列）或 `list`（记录列表），内部通过 `ensure_frame()` 统一转换。转换后必须至少有 1 行，否则报 `ValueError`。每张图最多嵌入 40 列（`MAX_COLS=40`），超过的部分会被丢弃并写入 `chart.warnings["warnings"]`。
- **建议**：首选 `pandas.DataFrame`；列名建议保持唯一、非空，中文列名可以直接用。 数值列用数值 dtype（`int64/float64`）；文本数字请先 `pd.to_numeric()`。 日期列用 `datetime64[ns]`（或可被 `pd.to_datetime()` 解析的字符串）。 作图前先处理空值：不同图对空值的策略不同（见各函数“常见问题”）。
- **示例**：`edv.calendar(data=df, date="日期", value="订单数")`
- **报错**：传入空 DataFrame：`ValueError: 数据为空（0 行），无法绘图。`；传入 `None`：`ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`

### `date` — 日期列（`str`，必填）

- **作用**：必须是日期/时间类型，或能被 `pd.to_datetime` 解析的文本；数值列会被拒绝。带时间的值按天截断，同一时刻的多行按 `agg` 合并。
- **建议**：`date="日期"`（sample 数据是 datetime64）。 文本日期（`2024-03-05`）可直接传，函数会统一格式。 多行同一天是常态：用 `agg="sum"`（默认）或 `mean` 控制合并口径。
- **示例**：`edv.calendar(df, value="订单数", date="日期")`
- **报错**：传数值列：`TypeError: date（日期）列 '销售额' 需要是日期/时间类型，但当前是数值类型。请换一列。`；存在无法解析的值：`ValueError: date（日期）列 '日期' 存在无法解析为日期的值（例如 '不是日期'），请先清洗。`

### `value` — 每天聚合的数值列（`str | None`，默认 `None`）

- **作用**：决定格子颜色的指标；不传时按记录条数计（`agg="count"`），颜色范围取实际最小值~最大值（不是 0 起）。
- **建议**：计数/金额类：`订单数`、`销售额`、`客户数`。 同一天多行的合并方式由 `agg` 控制：金额用 `sum`，客单价用 `mean`。 负值会让色阶失去意义，含负值请先取绝对值或换指标。
- **示例**：`edv.calendar(df, date="日期", value="订单数")`
- **报错**：传文本列：`TypeError: value（数值）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `agg` — 聚合方式（同一类目多条记录时如何合并）（`str`，默认 `'sum'`）

- **作用**：同一分类下有多条记录时，把数值列合成一个数的方法。可选：`sum`（默认）、`mean`、`count`、`max`、`min`、`median`。当函数没有拿到数值列（例如没传 `values`/`value`）时，内部会把 `agg` 强制为 `count`，按记录条数统计。 本图实现：按日期分组后用 `agg` 聚合；未传 `value` 时按记录数 `count`。
- **建议**：金额、订单数用 `sum`；单价、率值用 `mean` 或 `median`。 想看“有多少条记录”就传 `agg="count"`，此时数值列只作存在性检查。 `median` 对极端值更稳健，适合客单价、利润率这类偏态指标。
- **示例**：`edv.calendar(df, date="日期", value="订单数", agg="mean")`
- **报错**：`agg="average"`：`ValueError: agg='average' 不支持，可选：sum, mean, count, unique, max, min, median`

### `sort` — 排序方式（`str | None`，默认 `'x'`）

- **作用**：控制分类的排列顺序。本库只认 `"asc"`、`"desc"`、`"x"`、`"none"` 四种语义，但**不做枚举校验**：传其他字符串不会报错，会静默按该图默认顺序渲染。 本图实现：**不生效**。日历格子固定按日期排序。
- **建议**：排行榜用 `asc/desc`；时间序列用 `x`（按列顺序/时间升序）。 需要保持数据原始顺序时传 `sort="none"`。 分类是 `pd.Categorical`（如 `月份`）时，`x` 会按分类顺序而不是字母序。
- **示例**：`edv.calendar(df, date="日期", value="订单数", sort="asc")`
- **报错**：不存在的值不报错：`sort="DESC"` 会被忽略并按默认顺序渲染（大小写敏感）。；对不读取 `sort` 的图（如 pyramid/sunburst/sankey）传任何值都不会改变图形。

### `top_n` — 只保留前 N 项（`int | None`，默认 `None`）

- **作用**：按当前排序只保留前 N 个类目，`None`（默认）表示全部保留。必须是 ≥1 的整数（`bool` 不算）。不同函数对“多出来的部分”处理不同：rose 会把剩余项合并成“其他”，wordcloud 直接截断，其余函数多数不读取该字段。 本图实现：**不生效**。所有日期格子都会绘制。
- **建议**：类目超过 12 个时用 `top_n` 收敛，避免标签重叠。 玫瑰图配 `top_n` 会得到“其他”扇区，其余图不会。 配合 `sort="desc"` 使用才有“前 N 大”的含义。
- **示例**：`edv.calendar(df, date="日期", value="订单数", top_n=5)`
- **报错**：`top_n=0`：`ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`；`top_n=True`：同样报错（`bool` 被显式拒绝）。

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在卡片顶部的主标题。传 `None` 时使用函数内置的自动标题；传字符串则完全覆盖自动标题。标题只影响展示，不参与数据聚合与排序。
- **建议**：建议 8~18 个汉字，写清“指标 + 维度 + 口径”，例如 `销售额 按 大区`。 时间范围、币种、口径放在 `subtitle`，不要全部堆进标题。 标题是单行布局，过长会被卡片宽度截断，不建议加换行符。
- **示例**：`edv.calendar(df, date="日期", value="订单数", title="华东区销售构成")`

### `subtitle` — 副标题（口径/单位/时间范围）（`str | None`，默认 `None`）

- **作用**：标题下方的第二行说明，常用于补充统计口径、单位、时间范围或“较上期 +8%”这类结论。默认 `None`，不显示副标题；传空字符串等同于不显示。
- **建议**：写口径而不重复标题，例如 `2024 年 1-12 月 · 含税`。 颜色比标题浅，信息量控制在 30 字以内。 需要换行时直接写 `\n` 不会被解析成 HTML，建议保持单行。
- **示例**：`edv.calendar(df, date="日期", value="订单数", subtitle="2024 年 1-12 月 · 含税")`

### `fmt` — 数值格式（tooltip / 标签）（`str`，默认 `'compact'`）

- **作用**：控制数值在 tooltip、数据标签、右端读数里的显示格式，不改变原始数据。可选值：`compact`（默认，≥1 亿显示“x.x亿”、≥1 万显示“x.x万”、否则千分位）、`thousands`（千分位，如 `1,234,567`）、`raw`（原样，最多 3 位小数）、`percent`（一位小数加 `%`，如 `12.3%`）、`currency`（`¥` + 千分位 + 两位小数）。 本图实现：控制 tooltip 数值和日历下方色阶的刻度文本。
- **建议**：金额大数用 `compact`，表格/财务口径用 `thousands` 或 `currency`。 已经是百分数的列用 `percent`，不要再乘 100。 同一页多张图保持一致的 `fmt`，避免“万/千分位”混排。
- **示例**：`edv.calendar(df, date="日期", value="订单数", fmt="thousands")`
- **报错**：`fmt="commas"`：`ValueError: fmt='commas' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）（`int`，默认 `300`）

- **作用**：单张图的容器高度，单位像素，最小 120。不同函数的默认高度不同（本函数默认值见参数总览）。高度只影响画布，不改变数据；图例/标题/坐标轴会自动占用内部空间。
- **建议**：普通看板 320~460；层级图/关系图建议 ≥420。 多张图并排时高度取一致，视觉更整齐。 `height` 小于 120 会直接报错，不要用它做“隐藏图”。
- **示例**：`edv.calendar(df, date="日期", value="订单数", height=520)`
- **报错**：`height=100`：`ValueError: height 至少 120（像素），收到 100`；`height="400"`：同样报错（必须是 `int/float`）。

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题（浅色 / 深色）（`str`，默认 `'light'`）

- **作用**：页面主题，只支持 `"light"`（默认，白底深字）和 `"dark"`（深底浅字）。主题会同时改变背景、文字、坐标轴、tooltip 和默认色板的取色（`theme.palette`）。
- **建议**：常规报表/打印用 `light`；大屏、夜间模式用 `dark`。 多图看板统一主题，不要一张亮一张暗。 深色下避免使用低饱和的 `morandi` 色板，对比度会不够。
- **示例**：`edv.calendar(df, date="日期", value="订单数", theme="dark")`
- **报错**：`theme="blue"`：`ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `legend` — 是否显示图例（`bool | None`，默认 `False`）

- **作用**：是否显示图例。`None` 表示“按语义自动决定”（有色分组时显示、没有分组时隐藏），`True`/`False` 为强制开关。只有真正用颜色/名称区分系列的函数才会生效。 本图实现：**不生效**。热力日历用可视化色阶代替图例。
- **建议**：类目多且颜色即含义（产品、渠道）时保留图例。 图例项超过 10 个时图例会滚动，建议先 `top_n` 或合并小类。 单系列图关闭图例，把空间留给图形。
- **示例**：`edv.calendar(df, date="日期", value="订单数", legend=False)`
- **报错**：无校验：传非布尔值会经 `bool()` 转换（非空字符串为 `True`）。

### `labels` — 是否显示数据标签（`bool`，默认 `False`）

- **作用**：是否在图形上直接显示文字标签（类目名/数值/百分比）。默认值因函数而异；有的函数固定显示标签、不支持关闭。 本图实现：**不生效**。格子内不显示数值，只靠颜色和 tooltip。
- **建议**：类目 ≤8 个时打开标签，读者不用来回看 tooltip。 数据密集（散点、关系图）时关闭，避免文字糊成一片。 百分比标签通常配合 `fmt="percent"`。
- **示例**：`edv.calendar(df, date="日期", value="订单数", labels=False)`
- **报错**：无校验：会经 `bool()` 转换，传 `"no"` 也是 `True`。

### `zoom` — 缩放/漫游（`bool | str`，默认 `False`）

- **作用**：是否开启缩放。多数函数接受 `bool`；`candlestick` 默认 `"auto"`，表示分类数超过 30 时自动显示底部缩放条。不支持缩放的图会接受该参数但不产生效果。 本图实现：**不生效**。日历没有缩放。
- **建议**：时间序列很长（>60 点）时用 `zoom=True` 或放到 `candlestick` 的 `"auto"`。 层级/关系图本身可拖拽缩放，不必再开 `zoom`。 截图/打印场景关掉缩放，画面更干净。
- **示例**：`edv.calendar(df, date="日期", value="订单数", zoom=True)`

### `link` — 联动分组名（`str | None`，默认 `None`）

- **作用**：把多张图放进同一个联动组：点击某张图的类目，同组中包含该维度列的其他图会按该值过滤。同一个组名（如 `"g1"`）即可联动；默认 `None` 不联动。注意：`table`/`wordcloud` 是 HTML 渲染，只能作为**被联动方**，点击它们不会触发联动。 本图实现：当前点击日期格没有稳定的类目名，联动通常不触发（可作为被联动方）。
- **建议**：同一看板里的明细表用同一个 `link` 组名，点图即可筛表。 联动维度由点击的图决定，各图尽量共享同一列（如 `产品`）。 组名建议用有含义的英文/拼音，不要用随机串。
- **示例**：`edv.calendar(df, date="日期", value="订单数", link="g1")`
- **报错**：无校验：传数字/对象会原样写入 spec，JS 端作为对象键使用，建议只传字符串。

### `max_rows` — 嵌入前端的最大行数（`int`，默认 `2000000`）

- **作用**：Python 侧只把前 `max_rows` 行（默认 20000）的数据嵌入 HTML，超过时按均匀间隔抽样，并把提示写入 `chart.warnings["warnings"]`。`table` 特殊：默认 200，且最终最多嵌入 200 行。抽样只发生在“嵌入”阶段，不影响函数内已经算好的统计（如相关系数、回归系数）。
- **建议**：前端交互图保持默认 20000 即可；超大表用 `table(max_rows=...)` 控制体积。 需要完整数据时导出 Excel/CSV，不要让 HTML 承担全量数据。 抽样后 tooltip 的明细行数会变少，但聚合图的总量不受影响。
- **示例**：`edv.calendar(df, date="日期", value="订单数", max_rows=500)`
- **报错**：无校验：传 `0` 或负数会得到空数据（图形空白），建议传正整数。

## 返回值

返回 `eazy_data_viz.Chart` 对象（`chart.spec` 是完整的渲染 spec，`chart.data` 是嵌入前端的数据）。

- 通用方法：`chart.save(path)` 写单文件 HTML、`chart.to_html()` 返回字符串、`chart.palette(name)` 链式换色、`chart.show()` 在浏览器打开；`chart.warnings` 记录采样等降级提示（详见 [交互与联动指南](../guides/06-interaction.md)）。

本图的关键 spec 字段（`chart.spec`）：

| 字段 | 含义 |
| --- | --- |
| `type` | 固定为 `"calendar"`。 |
| `roles` | `{"x": 日期列, "value": 数值列或 None}`（日期放在 `x` 角色里）。 |
| `agg` | 同一天多行的聚合方式；未传 `value` 时为 `"count"`。 |
| `sort` | 默认 `"x"`，仅写入；JS 按日期值自行排序。 |
| `labels / legend / zoom / top_n` | 签名保留，但日历图没有图例/缩放，`labels` 与 `top_n` 未被读取。 |
| `visualMap` | 由 JS 根据实际 min/max 生成，颜色取主题 heat 色阶。 |

## 完整示例

以下示例全部基于 `edv.sample_df()`（1500 行、11 列）或由它派生的小表；输出文件写到 `examples/output/`。

### 示例 1：最简：全年订单热力

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.calendar(df, date="日期", value="订单数")
chart.save("examples/output/calendar_1.html")
```

**输出**：一整年的日历按月份分行、星期分列铺开，格子颜色从浅到深对应当天订单数；底部横向 visualMap 显示最小值~最大值，悬停格子显示日期与数值。

### 示例 2：典型：按记录条数着色

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.calendar(df, date="日期", title="每日记录条数", height=320)
chart.save("examples/output/calendar_2.html")
```

**输出**：不传 `value` 时颜色=当天记录条数（`agg="count"`）；sample 数据每天记录数不均，能看到明显的深浅差异。

### 示例 3：进阶：先聚合再画 + 数值格式

```python
import eazy_data_viz as edv

df = edv.sample_df()
daily = (
    df.groupby("日期", as_index=False)
      .agg(销售额=("销售额", "sum"))
)
chart = edv.calendar(
    daily,
    date="日期",
    value="销售额",
    fmt="thousands",
    title="每日销售额",
    height=340,
)
chart.save("examples/output/calendar_3.html")
```

**输出**：Python 端先按天汇总，前端只负责着色；tooltip 中销售额带千分位，visualMap 的刻度也用同一格式。

### 示例 4：深色主题与配色

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.calendar(df, date="日期", value="客户数", theme="dark")
chart.palette("carbon")
chart.save("examples/output/calendar_4.html")
```

**输出**：深色背景上热力色阶更醒目，月份/星期标签自动转浅色；深色模式下格子边框几乎不可见，整体更像一张发光的地图。

### 示例 5：看板：日历 + 明细表

```python
import eazy_data_viz as edv

df = edv.sample_df()
cal = edv.calendar(df, date="日期", value="订单数", title="每日订单")
top = df.nlargest(30, "订单数")[["日期", "大区", "产品", "订单数"]]
tbl = edv.table(top, columns=["日期", "大区", "产品", "订单数"], limit=30)
edv.dashboard(cal, tbl, title="日历看板", cols=1).save("examples/output/calendar_5.html")
```

**输出**：上排是全年日历、下排是订单数最高的 30 条明细（单列布局）；日历本身不能作为联动源，但可作为被过滤方接收其它图的联动。

> 以上示例对应的可运行脚本见 `examples/charts/calendar_chart.py`，运行 `PYTHONPATH=. python examples/charts/calendar_chart.py` 会一次性生成全部 HTML。

## 常见问题 / 注意事项

- **日历热力图能不能按周/月聚合？** 不能，日历本身就是“日”粒度。要看月粒度请用 `bar` 或 `theme_river`；要按周看可先把日期截断到周一再传入。
- **同一天有多行会怎样？** 按 `agg` 合并成一天的值：默认 `sum`；`agg="mean"` 取均值、`count` 数条数。日历的深浅只反映合并后的值。
- **`calendar` 能作为联动源吗？** 不能。JS 的 `currentXDim` 对 calendar 返回 `null`，点击格子不会向外传联动条件；但它能作为被过滤方接收其它图表的联动。
- **日期跨度只有几个月会怎样？** 仍然按整年铺格子，没有数据的月份留空；视觉上会有一大片空白，建议配合标题说明时间段，或改用 `bar`。
- **`top_n` 能只显示部分日期吗？** 不能。`top_n` 未生效；需要只展示某段日期，请在传参前筛选 `data`。

## 相关图表

| 图表 | 说明 |
| --- | --- |
| [`gantt`](gantt.md) | 甘特图（按任务看起止时间） |
| [`sparkline`](sparkline.md) | 迷你走势图（按时间看多条走势） |
| [`theme_river`](theme_river.md) | 主题河流图（按时间看构成变化） |
| [`table`](table.md) | 明细表（需要精确到天的数值列表时用它） |

- 回到总览：`docs/EXTRA_CHARTS.md`、`docs/AI_GUIDE.md`
