# `candlestick` — K 线图（用 OHLC 四价展示每期涨跌）

K 线图把每期的开盘、最高、最低、收盘四个价格画成一根蜡烛：实体是开盘到收盘，上下影线是最高/最低。涨用红色、跌用绿色（中国习惯），配合缩放可以快速看趋势与波动。

本库不做任何 OHLC 计算，四列必须由你提供；日期列会在 Python 端排序，保证蜡烛按时间从左到右排列。

- **适合**：有真实 OHLC 数据（股票、期货、汇率、日销售额的最高/最低/收盘）的时间序列。
- **不适合**：只有单一数值（如每日销售额）时不要硬造 OHLC，改用 `line`/`bar`；数据点少于 5 个时 K 线意义不大。

> 本页所有示例均可直接复制运行：先 `import eazy_data_viz as edv`，再 `df = edv.sample_df()`。

## 函数签名

```python
eazy_data_viz.candlestick(
    data,
    date,
    open,
    high,
    low,
    close,
    *,
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    xlim=None,
    ylim=None,
    fmt='compact',
    height=420,
    theme='light',
    legend=False,
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
| `date` | str | 无 | 是 | 日期/周期列（横轴） |
| `open` | str | 无 | 是 | 开盘价列 |
| `high` | str | 无 | 是 | 最高价列 |
| `low` | str | 无 | 是 | 最低价列 |
| `close` | str | 无 | 是 | 收盘价列 |
| `title` | str 或 None | None | 否 | 图表主标题 |
| `subtitle` | str 或 None | None | 否 | 副标题（口径/单位/时间范围） |
| `xtitle` | str 或 None | None | 否 | X 轴标题 |
| `ytitle` | str 或 None | None | 否 | Y 轴标题 |
| `xlim` | tuple[float, float] 或 list[float] 或 None | None | 否 | X 轴取值范围 |
| `ylim` | tuple[float, float] 或 list[float] 或 None | None | 否 | Y 轴取值范围 |
| `fmt` | str | 'compact' | 否 | 数值格式（tooltip / 标签） |
| `height` | int | 420 | 否 | 画布高度（像素） |
| `theme` | str | 'light' | 否 | 主题（浅色 / 深色） |
| `legend` | bool 或 None | False | 否 | 是否显示图例 |
| `labels` | bool | False | 否 | 是否显示数据标签 |
| `zoom` | bool 或 str | 'auto' | 否 | 缩放/漫游 |
| `link` | str 或 None | None | 否 | 联动分组名 |
| `max_rows` | int | 200000 | 否 | 嵌入前端的最大行数 |

> 共 20 个参数。签名里 `*` 之后是 keyword-only，必须写参数名；`data` 之前的位置参数（本图专有）可以按位置传。

## 参数详解

### `data` — 数据源（DataFrame）（`pandas.DataFrame`，必填）

- **作用**：图的原始数据。函数会按参数名从里面取列：`data` 既可以是 `pandas.DataFrame`，也可以是 `dict`（列名 → 值序列）或 `list`（记录列表），内部通过 `ensure_frame()` 统一转换。转换后必须至少有 1 行，否则报 `ValueError`。每张图最多嵌入 40 列（`MAX_COLS=40`），超过的部分会被丢弃并写入 `chart.warnings["warnings"]`。
- **建议**：首选 `pandas.DataFrame`；列名建议保持唯一、非空，中文列名可以直接用。 数值列用数值 dtype（`int64/float64`）；文本数字请先 `pd.to_numeric()`。 日期列用 `datetime64[ns]`（或可被 `pd.to_datetime()` 解析的字符串）。 作图前先处理空值：不同图对空值的策略不同（见各函数“常见问题”）。
- **报错**：传入空 DataFrame：`ValueError: 数据为空（0 行），无法绘图。`；传入 `None`：`ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`

### `date` — 日期/周期列（横轴）（`str`，必填）

- **作用**：必须是日期/时间类型或可解析文本；Python 会按该列稳定排序后再嵌入数据，因此乱序输入也能正确绘制。每个取值是一根蜡烛，重复日期会各画一根。
- **建议**：日线用交易日；周线/月线请先 `resample` 聚合再传入。 同一日期不要重复（除非你确实要画多根）。 时间戳带时分秒时，横轴标签只显示日期。
- **示例**：`edv.candlestick(ohlc, open="开盘", high="最高", low="最低", close="收盘", date="日期")`
- **报错**：传数值列：`TypeError: date（日期）列 '销售额' 需要是日期/时间类型，但当前是数值类型。请换一列。`

### `open` — 开盘价列（`str`，必填）

- **作用**：数值列；与 close 共同决定实体颜色（close≥open 为红）。
- **建议**：周线/月线的 open 取区间第一个值，close 取最后一个值。 四列必须同一量纲，否则蜡烛比例失真。
- **示例**：`edv.candlestick(ohlc, date="日期", high="最高", low="最低", close="收盘", open="开盘")`
- **报错**：传文本列：`TypeError: open（开盘价）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `high` — 最高价列（`str`，必填）

- **作用**：数值列，画成上影线；应满足 `high >= max(open, close)`，函数不校验这一约束。
- **建议**：聚合时用 `max`。 若 high < open，蜡烛会画得很奇怪（影线穿进实体），请先清洗。
- **示例**：`edv.candlestick(ohlc, date="日期", open="开盘", low="最低", close="收盘", high="最高")`
- **报错**：传文本列：`TypeError: high（最高价）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `low` — 最低价列（`str`，必填）

- **作用**：数值列，画成下影线；应满足 `low <= min(open, close)`。
- **建议**：聚合时用 `min`。 价格含 0 或负数时影线比例会失真，建议先确认数据口径。
- **示例**：`edv.candlestick(ohlc, date="日期", open="开盘", high="最高", close="收盘", low="最低")`
- **报错**：传文本列：`TypeError: low（最低价）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `close` — 收盘价列（`str`，必填）

- **作用**：数值列；close≥open 画红（涨），否则画绿（跌）。tooltip 中收盘价加粗并按涨跌着色。
- **建议**：聚合时用区间最后一个值。 K 线的“最新状态”通常看 close，可在其它图里复用。
- **示例**：`edv.candlestick(ohlc, date="日期", open="开盘", high="最高", low="最低", close="收盘")`
- **报错**：传文本列：`TypeError: close（收盘价）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在卡片顶部的主标题。传 `None` 时使用函数内置的自动标题；传字符串则完全覆盖自动标题。标题只影响展示，不参与数据聚合与排序。
- **建议**：建议 8~18 个汉字，写清“指标 + 维度 + 口径”，例如 `销售额 按 大区`。 时间范围、币种、口径放在 `subtitle`，不要全部堆进标题。 标题是单行布局，过长会被卡片宽度截断，不建议加换行符。
- **示例**：`edv.candlestick(ohlc, date="日期", open="开盘", high="最高", low="最低", close="收盘", title="华东区销售构成")`

### `subtitle` — 副标题（口径/单位/时间范围）（`str | None`，默认 `None`）

- **作用**：标题下方的第二行说明，常用于补充统计口径、单位、时间范围或“较上期 +8%”这类结论。默认 `None`，不显示副标题；传空字符串等同于不显示。
- **建议**：写口径而不重复标题，例如 `2024 年 1-12 月 · 含税`。 颜色比标题浅，信息量控制在 30 字以内。 需要换行时直接写 `\n` 不会被解析成 HTML，建议保持单行。
- **示例**：`edv.candlestick(ohlc, date="日期", open="开盘", high="最高", low="最低", close="收盘", subtitle="2024 年 1-12 月 · 含税")`

### `xtitle` — X 轴标题（`str | None`，默认 `None`）

- **作用**：横轴标题。传 `None` 时横轴使用列名作为轴名；传字符串则覆盖。该字段只对直角坐标系有效（玫瑰图/旭日图/树图/关系图等没有 X 轴的图形不会显示）。 本图实现：生效，作为日期分类轴标题，`None` 时回退为 `date` 列名。
- **建议**：写字段含义而不是字段名，例如 `日期`、`大区`、`广告投入（万元）`。 带单位的量把单位写进轴标题，数值格式交给 `fmt`。 分类轴很短时可以不写轴标题，避免和类目标签重复。
- **示例**：`edv.candlestick(ohlc, date="日期", open="开盘", high="最高", low="最低", close="收盘", xtitle="日期")`

### `ytitle` — Y 轴标题（`str | None`，默认 `None`）

- **作用**：纵轴标题。传 `None` 时纵轴使用数值列名作为轴名；传字符串则覆盖。部分无直角坐标系的图会把 `ytitle` 用在 tooltip 的数值行标签上。 本图实现：生效，作为价格轴标题，`None` 时回退为 `close` 列名。
- **建议**：带单位，例如 `销售额（元）`、`订单数（单）`。 百分比的图直接写 `占比`，并把 `fmt="percent"`。 与 `xtitle` 风格保持一致。
- **示例**：`edv.candlestick(ohlc, date="日期", open="开盘", high="最高", low="最低", close="收盘", ytitle="销售额（元）")`

### `xlim` — X 轴取值范围（`tuple[float, float] | list[float] | None`，默认 `None`）

- **作用**：把 X 轴限制在 `(最小值, 最大值)`。接受 2 元 `list/tuple`，也接受元素为 `None` 的 2 元组（表示该侧自动）；若 `最小值 > 最大值` 会自动交换。非法长度会报错。 本图实现：**不生效**。日期轴是分类轴，`xlim` 不会裁剪 K 线。
- **建议**：数值散点/回归图用 `xlim` 聚焦重点区间，避免极端值把点压成一团。 分类轴（`x` 是文本/日期）上该参数无效。 先看数据范围（`df["销售额"].min()`）再给范围，不要凭感觉截断。
- **示例**：`edv.candlestick(ohlc, date="日期", open="开盘", high="最高", low="最低", close="收盘", xlim=(0, 3000))`
- **报错**：`xlim=(1, 2, 3)`：`ValueError: xlim 需要是 (最小值, 最大值) 两元组，例如 xlim=(0, 100)`；`xlim="0,100"`（字符串）同样按长度错误报上面这条。

### `ylim` — Y 轴取值范围（`tuple[float, float] | list[float] | None`，默认 `None`）

- **作用**：把 Y 轴限制在 `(最小值, 最大值)`，规则同 `xlim`（2 元组、自动交换、`None` 表示该侧自动）。注意：`ylim` 只裁剪显示范围，不会过滤数据，tooltip 仍显示真实值。 本图实现：生效，限制价格轴范围。
- **建议**：需要强调差异时用 `ylim` 放大局部，但不要把 0 截掉造成误读。 含负值的图（利润、增长）要把负区间留给 `ylim=(..., ...)`。 堆叠/河流图用 `ylim` 固定上界，多张图并排时更可比。
- **示例**：`edv.candlestick(ohlc, date="日期", open="开盘", high="最高", low="最低", close="收盘", ylim=(-500, 2500))`
- **报错**：`ylim=(0, "高")`：`ValueError: ylim 需要是 (最小值, 最大值) 两元组，例如 ylim=(0, 100)`

### `fmt` — 数值格式（tooltip / 标签）（`str`，默认 `'compact'`）

- **作用**：控制数值在 tooltip、数据标签、右端读数里的显示格式，不改变原始数据。可选值：`compact`（默认，≥1 亿显示“x.x亿”、≥1 万显示“x.x万”、否则千分位）、`thousands`（千分位，如 `1,234,567`）、`raw`（原样，最多 3 位小数）、`percent`（一位小数加 `%`，如 `12.3%`）、`currency`（`¥` + 千分位 + 两位小数）。 本图实现：控制 tooltip 中开/高/低/收四个价格的显示格式。
- **建议**：金额大数用 `compact`，表格/财务口径用 `thousands` 或 `currency`。 已经是百分数的列用 `percent`，不要再乘 100。 同一页多张图保持一致的 `fmt`，避免“万/千分位”混排。
- **示例**：`edv.candlestick(ohlc, date="日期", open="开盘", high="最高", low="最低", close="收盘", fmt="thousands")`
- **报错**：`fmt="commas"`：`ValueError: fmt='commas' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）（`int`，默认 `420`）

- **作用**：单张图的容器高度，单位像素，最小 120。不同函数的默认高度不同（本函数默认值见参数总览）。高度只影响画布，不改变数据；图例/标题/坐标轴会自动占用内部空间。
- **建议**：普通看板 320~460；层级图/关系图建议 ≥420。 多张图并排时高度取一致，视觉更整齐。 `height` 小于 120 会直接报错，不要用它做“隐藏图”。
- **示例**：`edv.candlestick(ohlc, date="日期", open="开盘", high="最高", low="最低", close="收盘", height=520)`
- **报错**：`height=100`：`ValueError: height 至少 120（像素），收到 100`；`height="400"`：同样报错（必须是 `int/float`）。

### `theme` — 主题（浅色 / 深色）（`str`，默认 `'light'`）

- **作用**：页面主题，只支持 `"light"`（默认，白底深字）和 `"dark"`（深底浅字）。主题会同时改变背景、文字、坐标轴、tooltip 和默认色板的取色（`theme.palette`）。
- **建议**：常规报表/打印用 `light`；大屏、夜间模式用 `dark`。 多图看板统一主题，不要一张亮一张暗。 深色下避免使用低饱和的 `morandi` 色板，对比度会不够。
- **示例**：`edv.candlestick(ohlc, date="日期", open="开盘", high="最高", low="最低", close="收盘", theme="dark")`
- **报错**：`theme="blue"`：`ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `legend` — 是否显示图例（`bool | None`，默认 `False`）

- **作用**：是否显示图例。`None` 表示“按语义自动决定”（有色分组时显示、没有分组时隐藏），`True`/`False` 为强制开关。只有真正用颜色/名称区分系列的函数才会生效。 本图实现：**不生效**。K 线图只有一个系列，不显示图例。
- **建议**：类目多且颜色即含义（产品、渠道）时保留图例。 图例项超过 10 个时图例会滚动，建议先 `top_n` 或合并小类。 单系列图关闭图例，把空间留给图形。
- **示例**：`edv.candlestick(ohlc, date="日期", open="开盘", high="最高", low="最低", close="收盘", legend=False)`
- **报错**：无校验：传非布尔值会经 `bool()` 转换（非空字符串为 `True`）。

### `labels` — 是否显示数据标签（`bool`，默认 `False`）

- **作用**：是否在图形上直接显示文字标签（类目名/数值/百分比）。默认值因函数而异；有的函数固定显示标签、不支持关闭。 本图实现：**不生效**。K 线不显示数据标签。
- **建议**：类目 ≤8 个时打开标签，读者不用来回看 tooltip。 数据密集（散点、关系图）时关闭，避免文字糊成一片。 百分比标签通常配合 `fmt="percent"`。
- **示例**：`edv.candlestick(ohlc, date="日期", open="开盘", high="最高", low="最低", close="收盘", labels=False)`
- **报错**：无校验：会经 `bool()` 转换，传 `"no"` 也是 `True`。

### `zoom` — 缩放/漫游（`bool | str`，默认 `'auto'`）

- **作用**：是否开启缩放。多数函数接受 `bool`；`candlestick` 默认 `"auto"`，表示分类数超过 30 时自动显示底部缩放条。不支持缩放的图会接受该参数但不产生效果。 本图实现：生效。默认 `"auto"`：分类数 >30 时自动出现内部缩放 + 底部滑块；`False` 关闭。
- **建议**：时间序列很长（>60 点）时用 `zoom=True` 或放到 `candlestick` 的 `"auto"`。 层级/关系图本身可拖拽缩放，不必再开 `zoom`。 截图/打印场景关掉缩放，画面更干净。
- **示例**：`edv.candlestick(ohlc, date="日期", open="开盘", high="最高", low="最低", close="收盘", zoom=True)`

### `link` — 联动分组名（`str | None`，默认 `None`）

- **作用**：把多张图放进同一个联动组：点击某张图的类目，同组中包含该维度列的其他图会按该值过滤。同一个组名（如 `"g1"`）即可联动；默认 `None` 不联动。注意：`table`/`wordcloud` 是 HTML 渲染，只能作为**被联动方**，点击它们不会触发联动。 本图实现：点击 K 线会按 `date` 维度联动。
- **建议**：同一看板里的明细表用同一个 `link` 组名，点图即可筛表。 联动维度由点击的图决定，各图尽量共享同一列（如 `产品`）。 组名建议用有含义的英文/拼音，不要用随机串。
- **示例**：`edv.candlestick(ohlc, date="日期", open="开盘", high="最高", low="最低", close="收盘", link="g1")`
- **报错**：无校验：传数字/对象会原样写入 spec，JS 端作为对象键使用，建议只传字符串。

### `max_rows` — 嵌入前端的最大行数（`int`，默认 `200000`）

- **作用**：Python 侧只把前 `max_rows` 行（默认 20000）的数据嵌入 HTML，超过时按均匀间隔抽样，并把提示写入 `chart.warnings["warnings"]`。`table` 特殊：默认 200，且最终最多嵌入 200 行。抽样只发生在“嵌入”阶段，不影响函数内已经算好的统计（如相关系数、回归系数）。
- **建议**：前端交互图保持默认 20000 即可；超大表用 `table(max_rows=...)` 控制体积。 需要完整数据时导出 Excel/CSV，不要让 HTML 承担全量数据。 抽样后 tooltip 的明细行数会变少，但聚合图的总量不受影响。
- **示例**：`edv.candlestick(ohlc, date="日期", open="开盘", high="最高", low="最低", close="收盘", max_rows=500)`
- **报错**：无校验：传 `0` 或负数会得到空数据（图形空白），建议传正整数。

## 返回值

返回 `eazy_data_viz.Chart` 对象（`chart.spec` 是完整的渲染 spec，`chart.data` 是嵌入前端的数据）。

- 通用方法：`chart.save(path)` 写单文件 HTML、`chart.to_html()` 返回字符串、`chart.palette(name)` 链式换色、`chart.show()` 在浏览器打开；`chart.warnings` 记录采样等降级提示（详见 [交互与联动指南](../guides/06-interaction.md)）。

本图的关键 spec 字段（`chart.spec`）：

| 字段 | 含义 |
| --- | --- |
| `type` | 固定为 `"candlestick"`。 |
| `roles` | `{"x": 日期列, "open": 开盘列, "high": 最高列, "low": 最低列, "close": 收盘列}`。 |
| `sort` | 固定为 `"x"`，Python 已按日期排序，JS 按数据顺序绘制。 |
| `zoom` | `"auto"`（默认）：蜡烛 >30 根时自动加缩放条，否则不加；`True` 强制加，`False` 强制不加。 |
| `xtitle / ytitle / ylim` | 横轴/纵轴名称与纵轴范围；`xlim` 对类目轴无效。 |
| `labels / legend / agg` | 签名保留，但 K 线无数据标签与图例，`agg` 也不参与价格计算。 |

## 完整示例

以下示例全部基于 `edv.sample_df()`（1500 行、11 列）或由它派生的小表；输出文件写到 `examples/output/`。

### 示例 1：最简：周线 OHLC

```python
import eazy_data_viz as edv

df = edv.sample_df()
ohlc = (
    df.set_index("日期")["销售额"]
      .resample("W")
      .agg(["first", "max", "min", "last"])
      .dropna()
      .reset_index()
)
ohlc.columns = ["日期", "开盘", "最高", "最低", "收盘"]
chart = edv.candlestick(
    ohlc,
    date="日期",
    open="开盘",
    high="最高",
    low="最低",
    close="收盘",
)
chart.save("examples/output/candlestick_1.html")
```

**输出**：每周一根蜡烛：实体为周初到周末的销售额，上下影线为周内最高/最低；涨红跌绿，纵轴按销售额范围自适应，默认自动显示最近一段并带缩放条。

### 示例 2：典型：手工构造 5 期 OHLC

```python
import eazy_data_viz as edv
import pandas as pd

data = pd.DataFrame({
    "日期": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]),
    "开盘": [100, 103, 101, 105, 104],
    "最高": [104, 106, 104, 108, 106],
    "最低": [99, 100, 98, 103, 101],
    "收盘": [103, 101, 104, 104, 102],
})
chart = edv.candlestick(
    data,
    date="日期",
    open="开盘",
    high="最高",
    low="最低",
    close="收盘",
    title="5 日 K 线",
    height=380,
)
chart.save("examples/output/candlestick_2.html")
```

**输出**：5 根蜡烛：1/1 与 1/4 收涨（红），1/2、1/5 收跌（绿）；影线长度与 high/low 一致；数据点少所以没有自动缩放条。

### 示例 3：进阶：强制缩放 + 轴标题 + 纵轴范围

```python
import eazy_data_viz as edv

df = edv.sample_df()
ohlc = (
    df.set_index("日期")["订单数"]
      .resample("MS")
      .agg(["first", "max", "min", "last"])
      .dropna()
      .reset_index()
)
ohlc.columns = ["日期", "开盘", "最高", "最低", "收盘"]
chart = edv.candlestick(
    ohlc,
    date="日期",
    open="开盘",
    high="最高",
    low="最低",
    close="收盘",
    xtitle="月份",
    ytitle="订单数",
    ylim=(0, 300),
    zoom=True,
    title="月度订单 K 线",
)
chart.save("examples/output/candlestick_3.html")
```

**输出**：月线蜡烛 + 横轴名“月份”、纵轴名“订单数”；纵轴被限制在 0~300，超出部分裁掉；`zoom=True` 强制出现底部缩放条。

### 示例 4：边界：数据量 >30 自动缩放，只显示最后一段

```python
import eazy_data_viz as edv

df = edv.sample_df()
ohlc = (
    df.set_index("日期")["客户数"]
      .resample("D")
      .agg(["first", "max", "min", "last"])
      .dropna()
      .reset_index()
)
ohlc.columns = ["日期", "开盘", "最高", "最低", "收盘"]
chart = edv.candlestick(ohlc, date="日期", open="开盘", high="最高", low="最低", close="收盘",
                        title="日线（自动缩放）")
chart.save("examples/output/candlestick_4.html")
```

**输出**：日线蜡烛超过 30 根，自动出现底部 `dataZoom`，初始窗口显示最后约 60 根；拖动滑块可回看更早的蜡烛。

## 常见问题 / 注意事项

- **红涨绿跌能改成绿涨红跌吗？** 不能。颜色固定为 `color=palette[3]`、`color0=palette[1]`（红涨绿跌，中国习惯）；更换 `palette` 会改变具体色值，但涨跌的红绿语义不变。
- **能画均线、成交量吗？** 不能。本函数只画 K 线主体，没有 MA/成交量叠加；需要均线请自己算好后用 `line`/`dashboard` 组合展示。
- **缩放条能关掉吗？** 可以：`zoom=False` 强制关闭；`zoom="auto"`（默认）在蜡烛 >30 根时自动开启；`zoom=True` 强制开启。
- **为什么打开时只看到最后一段？** 自动缩放会把初始窗口设为最后约 60 根（若总数 >60），拖动底部滑块可以回看更早的数据；这是默认交互。
- **OHLC 有缺失值会怎样？** 四列中任意一列为空，该行会被跳过，不画蜡烛；不会用 0 或前值填充。请先清洗再作图。

## 相关图表

| 图表 | 说明 |
| --- | --- |
| [`calendar`](calendar.md) | 日历热力图（按天看密度分布） |
| [`sparkline`](sparkline.md) | 迷你走势图（多组走势的紧凑对比） |
| [`trend`](trend.md) | 趋势图（两个指标之间的线性关系） |
| [`gantt`](gantt.md) | 甘特图（按任务看起止时间） |

- 回到总览：`docs/EXTRA_CHARTS.md`、`docs/AI_GUIDE.md`
