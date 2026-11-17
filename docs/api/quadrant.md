# `quadrant` — 四象限散点图（用两条中位数线把散点分成四个象限）

四象限图在普通散点图的基础上，用 x 中位数和 y 中位数各画一条虚线，把平面切成四个象限，并在四角标注含义。它适合快速定位“高价值/低价值”对象：哪些点又大又赚钱、哪些点规模大但利润低。

中位数来自 Python（`spec.xmid`/`spec.ymid`），不是均值，所以少数极端点不会把分割线拉偏。

- **适合**：两个数值指标 + 一批对象（产品、门店、客户），想在汇报里直接点出“重点对象”。
- **不适合**：指标之间没有可比性/方向不一致、点数超过几百（重叠严重）、或需要精确回归时不要用；后者用 `trend` 或 `scatter`。

> 本页所有示例均可直接复制运行：先 `import eazy_data_viz as edv`，再 `df = edv.sample_df()`。

## 函数签名

```python
eazy_data_viz.quadrant(
    data,
    x,
    y,
    size=None,
    color=None,
    *,
    quad_labels=None,
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    xlim=None,
    ylim=None,
    fmt='compact',
    height=400,
    theme='light',
    legend=None,
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
| `x` | str | 无 | 是 | 横轴数值列 |
| `y` | str | 无 | 是 | 纵轴数值列 |
| `size` | str 或 None | None | 否 | 气泡大小列 |
| `color` | str 或 None | None | 否 | 分组列（按颜色拆成多个系列） |
| `quad_labels` | list[str] 或 None | None | 否 | 四角说明文字（顺序：左上、右上、左下、右下） |
| `title` | str 或 None | None | 否 | 图表主标题 |
| `subtitle` | str 或 None | None | 否 | 副标题（口径/单位/时间范围） |
| `xtitle` | str 或 None | None | 否 | X 轴标题 |
| `ytitle` | str 或 None | None | 否 | Y 轴标题 |
| `xlim` | tuple[float, float] 或 list[float] 或 None | None | 否 | X 轴取值范围 |
| `ylim` | tuple[float, float] 或 list[float] 或 None | None | 否 | Y 轴取值范围 |
| `fmt` | str | 'compact' | 否 | 数值格式（tooltip / 标签） |
| `height` | int | 400 | 否 | 画布高度（像素） |
| `theme` | str | 'light' | 否 | 主题（浅色 / 深色） |
| `legend` | bool 或 None | None | 否 | 是否显示图例 |
| `labels` | bool | False | 否 | 是否显示数据标签 |
| `zoom` | bool 或 str | False | 否 | 缩放/漫游 |
| `link` | str 或 None | None | 否 | 联动分组名 |
| `max_rows` | int | 200000 | 否 | 嵌入前端的最大行数 |

> 共 20 个参数。签名里 `*` 之后是 keyword-only，必须写参数名；`data` 之前的位置参数（本图专有）可以按位置传。

## 参数详解

### `data` — 数据源（DataFrame）（`pandas.DataFrame`，必填）

- **作用**：图的原始数据。函数会按参数名从里面取列：`data` 既可以是 `pandas.DataFrame`，也可以是 `dict`（列名 → 值序列）或 `list`（记录列表），内部通过 `ensure_frame()` 统一转换。转换后必须至少有 1 行，否则报 `ValueError`。每张图最多嵌入 40 列（`MAX_COLS=40`），超过的部分会被丢弃并写入 `chart.warnings["warnings"]`。
- **建议**：首选 `pandas.DataFrame`；列名建议保持唯一、非空，中文列名可以直接用。 数值列用数值 dtype（`int64/float64`）；文本数字请先 `pd.to_numeric()`。 日期列用 `datetime64[ns]`（或可被 `pd.to_datetime()` 解析的字符串）。 作图前先处理空值：不同图对空值的策略不同（见各函数“常见问题”）。
- **示例**：`edv.quadrant(data=df, x="销售额", y="利润")`
- **报错**：传入空 DataFrame：`ValueError: 数据为空（0 行），无法绘图。`；传入 `None`：`ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`

### `x` — 横轴数值列（`str`，必填）

- **作用**：必须是数值列（或 ≥99% 可解析为数字的文本列）；日期列会报错。所有行都按该值定位横坐标。
- **建议**：选“规模/投入”类指标：`销售额`、`订单数`、`客户数`。 两个轴最好都是“越大越好”或“越小越好”，避免象限含义冲突。 x 全是 NaN 时中位数按 0 处理并给出 warning。
- **示例**：`edv.quadrant(df, y="利润", x="销售额")`
- **报错**：传文本列：`TypeError: x（横轴）列 '大区' 需要是数值类型（当前是文本，例如 ['华东', '华北']）。请先用 pd.to_numeric() 清洗，或换一列。`；传日期列：`TypeError: x（横轴）列 '日期' 需要是数值类型，但当前是日期时间类型。请换一列。`

### `y` — 纵轴数值列（`str`，必填）

- **作用**：同 `x`，必须是数值列。y 的中位数决定水平分割线位置。
- **建议**：选“结果/效率”类指标：`利润`、`利润率`。 与 x 量纲不同没关系，两轴各自独立缩放。 如果 y 含大量 0，象限会挤在一条线上，建议先过滤或换指标。
- **示例**：`edv.quadrant(df, x="销售额", y="利润")`
- **报错**：传文本列：`TypeError: y（纵轴）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `size` — 气泡大小列（`str | None`，默认 `None`）

- **作用**：数值列，用于把点画成大小不同的气泡：会在该列最小值~最大值之间线性映射到符号尺寸。不传时所有点大小相同（9px 左右）。
- **建议**：用第三个可加总指标：`订单数`、`客户数`。 极端值会让气泡大小失衡，必要时先 `clip` 或取对数。 `size` 含空值的点会按最小尺寸绘制。
- **示例**：`edv.quadrant(df, x="销售额", y="利润", size="订单数")`
- **报错**：传文本列：`TypeError: size（气泡大小）列 '渠道' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `color` — 分组列（按颜色拆成多个系列）（`str | None`，默认 `None`）

- **作用**：每个不同取值一个系列，颜色从调色板依次取；分组后图例自动出现。缺失值归为 `(空)`。不传时所有点同色，图例默认关闭。
- **建议**：低基数列：`大区`（4）、`产品`（4）、`渠道`（3）。 分组超过 6 个时颜色难区分，改用 `size` 或先筛选。 分组后每组的中位线仍使用全量数据的 xmid/ymid，不会分组重算。
- **示例**：`edv.quadrant(df, x="销售额", y="利润", color="大区")`
- **报错**：列名写错：`KeyError: "color列 '不存在' 不存在。当前可用的列有：..."`

### `quad_labels` — 四角说明文字（顺序：左上、右上、左下、右下）（`list[str] | None`，默认 `None`）

- **作用**：必须正好 4 个字符串，依次对应：左上、右上、左下、右下。默认 `["高值·高值", "低值·高值", "低值·低值", "高值·低值"]`。注意顺序是“左上/右上/左下/右下”，不是顺时针。
- **建议**：用业务语言替换默认值，例如 `["低销高利", "高销高利", "低销低利", "高销低利"]`。 文字尽量 ≤6 个汉字，四角空间有限。 只传 3 个会直接报错，不会自动补齐。
- **示例**：`edv.quadrant(df, x="销售额", y="利润", quad_labels=["低销高利", "高销高利", "低销低利", "高销低利"])`
- **报错**：`quad_labels=["a", "b", "c"]`：`ValueError: quad_labels 需要 4 个文本（四角说明），例如 quad_labels=["高增长高利润", "低增长高利润", "低增长低利润", "高增长低利润"]，收到 ['a', 'b', 'c']`

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在卡片顶部的主标题。传 `None` 时使用函数内置的自动标题；传字符串则完全覆盖自动标题。标题只影响展示，不参与数据聚合与排序。
- **建议**：建议 8~18 个汉字，写清“指标 + 维度 + 口径”，例如 `销售额 按 大区`。 时间范围、币种、口径放在 `subtitle`，不要全部堆进标题。 标题是单行布局，过长会被卡片宽度截断，不建议加换行符。
- **示例**：`edv.quadrant(df, x="销售额", y="利润", title="华东区销售构成")`

### `subtitle` — 副标题（口径/单位/时间范围）（`str | None`，默认 `None`）

- **作用**：标题下方的第二行说明，常用于补充统计口径、单位、时间范围或“较上期 +8%”这类结论。默认 `None`，不显示副标题；传空字符串等同于不显示。
- **建议**：写口径而不重复标题，例如 `2024 年 1-12 月 · 含税`。 颜色比标题浅，信息量控制在 30 字以内。 需要换行时直接写 `\n` 不会被解析成 HTML，建议保持单行。
- **示例**：`edv.quadrant(df, x="销售额", y="利润", subtitle="2024 年 1-12 月 · 含税")`

### `xtitle` — X 轴标题（`str | None`，默认 `None`）

- **作用**：横轴标题。传 `None` 时横轴使用列名作为轴名；传字符串则覆盖。该字段只对直角坐标系有效（玫瑰图/旭日图/树图/关系图等没有 X 轴的图形不会显示）。 本图实现：生效，作为横轴（数值轴）标题，`None` 时回退为 `x` 列名。
- **建议**：写字段含义而不是字段名，例如 `日期`、`大区`、`广告投入（万元）`。 带单位的量把单位写进轴标题，数值格式交给 `fmt`。 分类轴很短时可以不写轴标题，避免和类目标签重复。
- **示例**：`edv.quadrant(df, x="销售额", y="利润", xtitle="日期")`

### `ytitle` — Y 轴标题（`str | None`，默认 `None`）

- **作用**：纵轴标题。传 `None` 时纵轴使用数值列名作为轴名；传字符串则覆盖。部分无直角坐标系的图会把 `ytitle` 用在 tooltip 的数值行标签上。 本图实现：生效，作为纵轴标题，`None` 时回退为 `y` 列名。
- **建议**：带单位，例如 `销售额（元）`、`订单数（单）`。 百分比的图直接写 `占比`，并把 `fmt="percent"`。 与 `xtitle` 风格保持一致。
- **示例**：`edv.quadrant(df, x="销售额", y="利润", ytitle="销售额（元）")`

### `xlim` — X 轴取值范围（`tuple[float, float] | list[float] | None`，默认 `None`）

- **作用**：把 X 轴限制在 `(最小值, 最大值)`。接受 2 元 `list/tuple`，也接受元素为 `None` 的 2 元组（表示该侧自动）；若 `最小值 > 最大值` 会自动交换。非法长度会报错。 本图实现：生效，限制横轴显示范围（不过滤数据）。
- **建议**：数值散点/回归图用 `xlim` 聚焦重点区间，避免极端值把点压成一团。 分类轴（`x` 是文本/日期）上该参数无效。 先看数据范围（`df["销售额"].min()`）再给范围，不要凭感觉截断。
- **示例**：`edv.quadrant(df, x="销售额", y="利润", xlim=(0, 3000))`
- **报错**：`xlim=(1, 2, 3)`：`ValueError: xlim 需要是 (最小值, 最大值) 两元组，例如 xlim=(0, 100)`；`xlim="0,100"`（字符串）同样按长度错误报上面这条。

### `ylim` — Y 轴取值范围（`tuple[float, float] | list[float] | None`，默认 `None`）

- **作用**：把 Y 轴限制在 `(最小值, 最大值)`，规则同 `xlim`（2 元组、自动交换、`None` 表示该侧自动）。注意：`ylim` 只裁剪显示范围，不会过滤数据，tooltip 仍显示真实值。 本图实现：生效，限制纵轴显示范围。
- **建议**：需要强调差异时用 `ylim` 放大局部，但不要把 0 截掉造成误读。 含负值的图（利润、增长）要把负区间留给 `ylim=(..., ...)`。 堆叠/河流图用 `ylim` 固定上界，多张图并排时更可比。
- **示例**：`edv.quadrant(df, x="销售额", y="利润", ylim=(-500, 2500))`
- **报错**：`ylim=(0, "高")`：`ValueError: ylim 需要是 (最小值, 最大值) 两元组，例如 ylim=(0, 100)`

### `fmt` — 数值格式（tooltip / 标签）（`str`，默认 `'compact'`）

- **作用**：控制数值在 tooltip、数据标签、右端读数里的显示格式，不改变原始数据。可选值：`compact`（默认，≥1 亿显示“x.x亿”、≥1 万显示“x.x万”、否则千分位）、`thousands`（千分位，如 `1,234,567`）、`raw`（原样，最多 3 位小数）、`percent`（一位小数加 `%`，如 `12.3%`）、`currency`（`¥` + 千分位 + 两位小数）。 本图实现：控制 tooltip 中的 x、y、size 数值，不改变坐标轴刻度。
- **建议**：金额大数用 `compact`，表格/财务口径用 `thousands` 或 `currency`。 已经是百分数的列用 `percent`，不要再乘 100。 同一页多张图保持一致的 `fmt`，避免“万/千分位”混排。
- **示例**：`edv.quadrant(df, x="销售额", y="利润", fmt="thousands")`
- **报错**：`fmt="commas"`：`ValueError: fmt='commas' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）（`int`，默认 `400`）

- **作用**：单张图的容器高度，单位像素，最小 120。不同函数的默认高度不同（本函数默认值见参数总览）。高度只影响画布，不改变数据；图例/标题/坐标轴会自动占用内部空间。
- **建议**：普通看板 320~460；层级图/关系图建议 ≥420。 多张图并排时高度取一致，视觉更整齐。 `height` 小于 120 会直接报错，不要用它做“隐藏图”。
- **示例**：`edv.quadrant(df, x="销售额", y="利润", height=520)`
- **报错**：`height=100`：`ValueError: height 至少 120（像素），收到 100`；`height="400"`：同样报错（必须是 `int/float`）。

### `theme` — 主题（浅色 / 深色）（`str`，默认 `'light'`）

- **作用**：页面主题，只支持 `"light"`（默认，白底深字）和 `"dark"`（深底浅字）。主题会同时改变背景、文字、坐标轴、tooltip 和默认色板的取色（`theme.palette`）。
- **建议**：常规报表/打印用 `light`；大屏、夜间模式用 `dark`。 多图看板统一主题，不要一张亮一张暗。 深色下避免使用低饱和的 `morandi` 色板，对比度会不够。
- **示例**：`edv.quadrant(df, x="销售额", y="利润", theme="dark")`
- **报错**：`theme="blue"`：`ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `legend` — 是否显示图例（`bool | None`，默认 `None`）

- **作用**：是否显示图例。`None` 表示“按语义自动决定”（有色分组时显示、没有分组时隐藏），`True`/`False` 为强制开关。只有真正用颜色/名称区分系列的函数才会生效。 本图实现：默认 `None`（=有 `color` 才显示）。传 `True` 可显示，`False` 关闭。
- **建议**：类目多且颜色即含义（产品、渠道）时保留图例。 图例项超过 10 个时图例会滚动，建议先 `top_n` 或合并小类。 单系列图关闭图例，把空间留给图形。
- **示例**：`edv.quadrant(df, x="销售额", y="利润", legend=False)`
- **报错**：无校验：传非布尔值会经 `bool()` 转换（非空字符串为 `True`）。

### `labels` — 是否显示数据标签（`bool`，默认 `False`）

- **作用**：是否在图形上直接显示文字标签（类目名/数值/百分比）。默认值因函数而异；有的函数固定显示标签、不支持关闭。 本图实现：**不生效**。散点没有内置标签（可读 tooltip）。
- **建议**：类目 ≤8 个时打开标签，读者不用来回看 tooltip。 数据密集（散点、关系图）时关闭，避免文字糊成一片。 百分比标签通常配合 `fmt="percent"`。
- **示例**：`edv.quadrant(df, x="销售额", y="利润", labels=False)`
- **报错**：无校验：会经 `bool()` 转换，传 `"no"` 也是 `True`。

### `zoom` — 缩放/漫游（`bool | str`，默认 `False`）

- **作用**：是否开启缩放。多数函数接受 `bool`；`candlestick` 默认 `"auto"`，表示分类数超过 30 时自动显示底部缩放条。不支持缩放的图会接受该参数但不产生效果。 本图实现：**不生效**。散点不提供 dataZoom。
- **建议**：时间序列很长（>60 点）时用 `zoom=True` 或放到 `candlestick` 的 `"auto"`。 层级/关系图本身可拖拽缩放，不必再开 `zoom`。 截图/打印场景关掉缩放，画面更干净。
- **示例**：`edv.quadrant(df, x="销售额", y="利润", zoom=True)`

### `link` — 联动分组名（`str | None`，默认 `None`）

- **作用**：把多张图放进同一个联动组：点击某张图的类目，同组中包含该维度列的其他图会按该值过滤。同一个组名（如 `"g1"`）即可联动；默认 `None` 不联动。注意：`table`/`wordcloud` 是 HTML 渲染，只能作为**被联动方**，点击它们不会触发联动。 本图实现：点击散点会按 `x` 维度的取值联动（联动的粒度是 x 值）。
- **建议**：同一看板里的明细表用同一个 `link` 组名，点图即可筛表。 联动维度由点击的图决定，各图尽量共享同一列（如 `产品`）。 组名建议用有含义的英文/拼音，不要用随机串。
- **示例**：`edv.quadrant(df, x="销售额", y="利润", link="g1")`
- **报错**：无校验：传数字/对象会原样写入 spec，JS 端作为对象键使用，建议只传字符串。

### `max_rows` — 嵌入前端的最大行数（`int`，默认 `200000`）

- **作用**：Python 侧只把前 `max_rows` 行（默认 20000）的数据嵌入 HTML，超过时按均匀间隔抽样，并把提示写入 `chart.warnings["warnings"]`。`table` 特殊：默认 200，且最终最多嵌入 200 行。抽样只发生在“嵌入”阶段，不影响函数内已经算好的统计（如相关系数、回归系数）。
- **建议**：前端交互图保持默认 20000 即可；超大表用 `table(max_rows=...)` 控制体积。 需要完整数据时导出 Excel/CSV，不要让 HTML 承担全量数据。 抽样后 tooltip 的明细行数会变少，但聚合图的总量不受影响。
- **示例**：`edv.quadrant(df, x="销售额", y="利润", max_rows=500)`
- **报错**：无校验：传 `0` 或负数会得到空数据（图形空白），建议传正整数。

## 返回值

返回 `eazy_data_viz.Chart` 对象（`chart.spec` 是完整的渲染 spec，`chart.data` 是嵌入前端的数据）。

- 通用方法：`chart.save(path)` 写单文件 HTML、`chart.to_html()` 返回字符串、`chart.palette(name)` 链式换色、`chart.show()` 在浏览器打开；`chart.warnings` 记录采样等降级提示（详见 [交互与联动指南](../guides/06-interaction.md)）。

本图的关键 spec 字段（`chart.spec`）：

| 字段 | 含义 |
| --- | --- |
| `type` | 固定为 `"quadrant"`。 |
| `roles` | `{"x": 横轴列, "y": 纵轴列, "size": 气泡列或 None, "color": 分组列或 None}`。 |
| `xmid / ymid` | Python 预先算好的 x/y 中位数，JS 据此画两条虚线（缺失时 JS 兜底重算中位数）。 |
| `quadrantLabels` | 四角说明文字数组，顺序 `[左上, 右上, 左下, 右下]`。 |
| `xlim / ylim` | 两轴显示范围，`(min, max)` 两元组。 |
| `legend` | 默认 `color is not None`；分组时显示图例。 |

## 完整示例

以下示例全部基于 `edv.sample_df()`（1500 行、11 列）或由它派生的小表；输出文件写到 `examples/output/`。

### 示例 1：最简四象限

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.quadrant(df, x="销售额", y="利润")
chart.save("examples/output/quadrant_1.html")
```

**输出**：一堆散点被 x=销售额中位数、y=利润中位数两条虚线切成四块，四角显示“高值·高值”等默认文字；自动标题“利润 与 销售额 四象限”。

### 示例 2：典型：颜色分组 + 气泡大小

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.quadrant(
    df,
    x="销售额",
    y="客户数",
    size="订单数",
    color="大区",
    title="销售额 × 客户数",
    subtitle="气泡大小=订单数 · 颜色=大区",
)
chart.save("examples/output/quadrant_2.html")
```

**输出**：四个大区各用一种颜色，点的大小按订单数缩放；右上角（高销售、高客户）集中了主力市场，悬停可看三项指标。

### 示例 3：深色主题与配色

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.quadrant(df, x="销售额", y="利润", color="渠道", theme="dark")
chart.palette("antd")
chart.save("examples/output/quadrant_3.html")
```

**输出**：深色背景 + Ant Design 色板，三条渠道三色区分；虚线中位线与四角文字自动变为浅色。

### 示例 4：联动：点击气泡过滤明细

```python
import eazy_data_viz as edv

df = edv.sample_df()
q = edv.quadrant(df, x="销售额", y="利润", color="大区", link="q1")
tbl = edv.table(df, columns=["大区", "产品", "销售额", "利润"], link="q1", limit=40)
edv.dashboard(q, tbl, title="四象限联动", cols=2).save("examples/output/quadrant_4.html")
```

**输出**：点击某一气泡，右侧表格按该点所属分组过滤（联动维度取 `color` 列，未传 `color` 时按 `x` 列）；其余点变淡作为高亮。

### 示例 5：按产品分组：四个产品各自的位置

```python
import eazy_data_viz as edv

df = edv.sample_df()
# 先聚合到「产品」粒度，再放入四象限，避免 1500 个点重叠
agg = df.groupby("产品", as_index=False).agg(
    销售额=("销售额", "sum"),
    利润=("利润", "sum"),
    订单数=("订单数", "sum"),
)
chart = edv.quadrant(
    agg,
    x="销售额",
    y="利润",
    size="订单数",
    color="产品",
    quad_labels=["低销高利", "高销高利", "低销低利", "高销低利"],
)
chart.save("examples/output/quadrant_5.html")
```

**输出**：只有 4 个气泡，每个气泡是一个产品；这是把四象限当“战略矩阵”用的正确姿势——先聚合到对象粒度，再比较对象。

> 以上示例对应的可运行脚本见 `examples/charts/quadrant.py`，运行 `PYTHONPATH=. python examples/charts/quadrant.py` 会一次性生成全部 HTML。

## 常见问题 / 注意事项

- **中位线为什么不是平均值？** 四象限要的是“把对象相对地分成两半”，中位数对极端值更稳健；均值会被少数大客户拉偏，导致大部分点落在同一象限。中位数由 Python 计算并写入 `spec.xmid`/`spec.ymid`，无法通过参数改成均值。
- **点太多挤成一团怎么办？** ① 先聚合到对象粒度（见示例 9）；② 用 `xlim`/`ylim` 放大重点区域；③ 加 `color` 分组并配合图例筛选；④ 点数上千时改用 `matrix` 或基础 `scatter` 的采样。
- **`labels=True` 会显示点名称吗？** 不会。当前 JS 不读取 `spec.labels`，四象限图没有点的数据标签；需要知道点的身份只能悬停 tooltip 或先聚合（每个点变成一个对象）。
- **`quad_labels` 的顺序容易搞错，怎么记？** 顺序是页面视觉顺序：先上排从左到右（左上、右上），再下排（左下、右下）。默认值就是按这个顺序定义的。
- **为什么图例开关是 `None` 而不是布尔？** `legend=None` 表示“自动”：传了 `color` 就显示图例，没传就不显示。显式传 `True`/`False` 可以强制开关。

## 相关图表

| 图表 | 说明 |
| --- | --- |
| [`trend`](trend.md) | 趋势图（需要拟合线和 R² 时用它） |
| [`matrix`](matrix.md) | 相关系数矩阵（先看指标之间是否真的相关，再决定四象限轴） |
| [`graph`](graph.md) | 关系图（对象之间有多对多关系时用它） |
| [`rose`](rose.md) | 南丁格尔玫瑰图（只看单一指标构成时更简单） |

- 回到总览：`docs/EXTRA_CHARTS.md`、`docs/AI_GUIDE.md`
