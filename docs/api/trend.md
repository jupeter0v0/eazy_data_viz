# `trend` — 趋势图（散点 + 线性拟合）（散点图上叠加最小二乘回归线与 R²）

趋势图把每一行画成一个散点，并在 Python 端用最小二乘法拟合一条直线，把斜率、截距、R² 一起写进 spec，前端画出虚线回归线并在右上角标出 R²。它回答的是“两个数值指标之间有没有线性关系、关系有多强”。

和 `quadrant` 的区别：四象限只划分区域，趋势图会真的算回归；和基础 `scatter` 的区别：这里自带回归线与 R²。

- **适合**：两个连续数值变量、样本量几十以上、想量化线性关系强度（销售额 vs 利润、投入 vs 产出）。
- **不适合**：关系明显非线性、含大量离群点、或 x 是时间序列（应改用 `line`/`trend` 的时间轴用法）时不要用；R² 低不代表没关系，只代表线性关系弱。

> 本页所有示例均可直接复制运行：先 `import eazy_data_viz as edv`，再 `df = edv.sample_df()`。

## 函数签名

```python
eazy_data_viz.trend(
    data,
    x,
    y,
    color=None,
    *,
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    xlim=None,
    ylim=None,
    fmt="compact",
    height=400,
    abs_height=False,
    theme="light",
    legend=None,
    labels=False,
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
| `x` | str | 无 | 是 | 自变量列（横轴） |
| `y` | str | 无 | 是 | 因变量列（纵轴） |
| `color` | str 或 None | None | 否 | 分组列（按颜色拆成多个散点系列） |
| `title` | str 或 None | None | 否 | 图表主标题 |
| `subtitle` | str 或 None | None | 否 | 副标题（口径/单位/时间范围） |
| `xtitle` | str 或 None | None | 否 | X 轴标题 |
| `ytitle` | str 或 None | None | 否 | Y 轴标题 |
| `xlim` | tuple[float, float] 或 list[float] 或 None | None | 否 | X 轴取值范围 |
| `ylim` | tuple[float, float] 或 list[float] 或 None | None | 否 | Y 轴取值范围 |
| `fmt` | str | 'compact' | 否 | 数值格式（tooltip / 标签） |
| `height` | int | 400 | 否 | 画布高度（像素） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | str | 'light' | 否 | 主题（浅色 / 深色） |
| `legend` | bool 或 None | None | 否 | 是否显示图例 |
| `labels` | bool | False | 否 | 是否显示数据标签 |
| `zoom` | bool 或 str | False | 否 | 缩放/漫游 |
| `link` | str 或 None | None | 否 | 联动分组名 |
| `max_rows` | int | 200000 | 否 | 嵌入前端的最大行数 |

> 共 18 个参数。签名里 `*` 之后是 keyword-only，必须写参数名；`data` 之前的位置参数（本图专有）可以按位置传。

## 参数详解

### `data` — 数据源（DataFrame）（`pandas.DataFrame`，必填）

- **作用**：图的原始数据。函数会按参数名从里面取列：`data` 既可以是 `pandas.DataFrame`，也可以是 `dict`（列名 → 值序列）或 `list`（记录列表），内部通过 `ensure_frame()` 统一转换。转换后必须至少有 1 行，否则报 `ValueError`。每张图最多嵌入 40 列（`MAX_COLS=40`），超过的部分会被丢弃并写入 `chart.warnings["warnings"]`。
- **建议**：首选 `pandas.DataFrame`；列名建议保持唯一、非空，中文列名可以直接用。 数值列用数值 dtype（`int64/float64`）；文本数字请先 `pd.to_numeric()`。 日期列用 `datetime64[ns]`（或可被 `pd.to_datetime()` 解析的字符串）。 作图前先处理空值：不同图对空值的策略不同（见各函数“常见问题”）。
- **示例**：`edv.trend(data=df, x="销售额", y="利润")`
- **报错**：传入空 DataFrame：`ValueError: 数据为空（0 行），无法绘图。`；传入 `None`：`ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`

### `x` — 自变量列（横轴）（`str`，必填）

- **作用**：必须是数值列（或 ≥99% 可解析为数字的文本列）；日期列会被拒绝。空值行会被剔除后再拟合，不会以 0 参与计算。
- **建议**：用“投入/规模”类指标：`销售额`、`客户数`、`订单数`。 若 x 是时间，请把日期转成序号或直接用 `line`，否则 R² 没有业务意义。 x 只有单一取值（所有点同一 x）时斜率为 0、R² 为空。
- **示例**：`edv.trend(df, y="利润", x="销售额")`
- **报错**：传文本列：`TypeError: x（横轴）列 '大区' 需要是数值类型（当前是文本，例如 ['华东', '华北']）。请先用 pd.to_numeric() 清洗，或换一列。`；传日期列：`TypeError: x（横轴）列 '日期' 需要是数值类型，但当前是日期时间类型。请换一列。`

### `y` — 因变量列（纵轴）（`str`，必填）

- **作用**：必须是数值列。拟合的是 `y = slope * x + intercept`，因此 x、y 的角色不能随意互换——R² 对称，但斜率的业务解释不对称。
- **建议**：用“结果”类指标：`利润`、`订单数`、`客户数`。 与 x 量纲不同没关系，斜率单位是“y 单位 / x 单位”。 y 为空的行同样被剔除；有效点少于 2 个会直接报错。
- **示例**：`edv.trend(df, x="销售额", y="利润")`
- **报错**：传文本列：`TypeError: y（纵轴）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`；有效点 <2：`ValueError: trend 需要至少 2 个有效的 (x, y) 数值点才能拟合回归线。`

### `color` — 分组列（按颜色拆成多个散点系列）（`str | None`，默认 `None`）

- **作用**：每个取值一个散点系列，颜色从调色板取；回归线仍然只有一条，基于**全量**数据拟合，不会按分组各拟合一条。分组后图例默认显示。
- **建议**：低基数列：`大区`、`产品`、`渠道`，可用于看“分组是否各自聚簇”。 分组后仍建议看整体 R²：分组只影响点的颜色，不影响拟合结果。 需要分组分别拟合时，请分别调用 `trend()` 生成多张图。
- **示例**：`edv.trend(df, x="销售额", y="利润", color="大区")`
- **报错**：列名写错：`KeyError: "color列 '不存在' 不存在。当前可用的列有：..."`

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在卡片顶部的主标题。传 `None` 时使用函数内置的自动标题；传字符串则完全覆盖自动标题。标题只影响展示，不参与数据聚合与排序。
- **建议**：建议 8~18 个汉字，写清“指标 + 维度 + 口径”，例如 `销售额 按 大区`。 时间范围、币种、口径放在 `subtitle`，不要全部堆进标题。 标题是单行布局，过长会被卡片宽度截断，不建议加换行符。
- **示例**：`edv.trend(df, x="销售额", y="利润", title="华东区销售构成")`

### `subtitle` — 副标题（口径/单位/时间范围）（`str | None`，默认 `None`）

- **作用**：标题下方的第二行说明，常用于补充统计口径、单位、时间范围或“较上期 +8%”这类结论。默认 `None`，不显示副标题；传空字符串等同于不显示。
- **建议**：写口径而不重复标题，例如 `2024 年 1-12 月 · 含税`。 颜色比标题浅，信息量控制在 30 字以内。 需要换行时直接写 `\n` 不会被解析成 HTML，建议保持单行。
- **示例**：`edv.trend(df, x="销售额", y="利润", subtitle="2024 年 1-12 月 · 含税")`

### `xtitle` — X 轴标题（`str | None`，默认 `None`）

- **作用**：横轴标题。传 `None` 时横轴使用列名作为轴名；传字符串则覆盖。该字段只对直角坐标系有效（玫瑰图/旭日图/树图/关系图等没有 X 轴的图形不会显示）。 本图实现：生效，作为横轴标题，`None` 时回退为 `x` 列名。
- **建议**：写字段含义而不是字段名，例如 `日期`、`大区`、`广告投入（万元）`。 带单位的量把单位写进轴标题，数值格式交给 `fmt`。 分类轴很短时可以不写轴标题，避免和类目标签重复。
- **示例**：`edv.trend(df, x="销售额", y="利润", xtitle="日期")`

### `ytitle` — Y 轴标题（`str | None`，默认 `None`）

- **作用**：纵轴标题。传 `None` 时纵轴使用数值列名作为轴名；传字符串则覆盖。部分无直角坐标系的图会把 `ytitle` 用在 tooltip 的数值行标签上。 本图实现：生效，作为纵轴标题，`None` 时回退为 `y` 列名。
- **建议**：带单位，例如 `销售额（元）`、`订单数（单）`。 百分比的图直接写 `占比`，并把 `fmt="percent"`。 与 `xtitle` 风格保持一致。
- **示例**：`edv.trend(df, x="销售额", y="利润", ytitle="销售额（元）")`

### `xlim` — X 轴取值范围（`tuple[float, float] | list[float] | None`，默认 `None`）

- **作用**：把 X 轴限制在 `(最小值, 最大值)`。接受 2 元 `list/tuple`，也接受元素为 `None` 的 2 元组（表示该侧自动）；若 `最小值 > 最大值` 会自动交换。非法长度会报错。 本图实现：生效，限制横轴显示范围（不过滤数据、不影响回归系数）。
- **建议**：数值散点/回归图用 `xlim` 聚焦重点区间，避免极端值把点压成一团。 分类轴（`x` 是文本/日期）上该参数无效。 先看数据范围（`df["销售额"].min()`）再给范围，不要凭感觉截断。
- **示例**：`edv.trend(df, x="销售额", y="利润", xlim=(0, 3000))`
- **报错**：`xlim=(1, 2, 3)`：`ValueError: xlim 需要是 (最小值, 最大值) 两元组，例如 xlim=(0, 100)`；`xlim="0,100"`（字符串）同样按长度错误报上面这条。

### `ylim` — Y 轴取值范围（`tuple[float, float] | list[float] | None`，默认 `None`）

- **作用**：把 Y 轴限制在 `(最小值, 最大值)`，规则同 `xlim`（2 元组、自动交换、`None` 表示该侧自动）。注意：`ylim` 只裁剪显示范围，不会过滤数据，tooltip 仍显示真实值。 本图实现：生效，限制纵轴显示范围。
- **建议**：需要强调差异时用 `ylim` 放大局部，但不要把 0 截掉造成误读。 含负值的图（利润、增长）要把负区间留给 `ylim=(..., ...)`。 堆叠/河流图用 `ylim` 固定上界，多张图并排时更可比。
- **示例**：`edv.trend(df, x="销售额", y="利润", ylim=(-500, 2500))`
- **报错**：`ylim=(0, "高")`：`ValueError: ylim 需要是 (最小值, 最大值) 两元组，例如 ylim=(0, 100)`

### `fmt` — 数值格式（tooltip / 标签）（`str`，默认 `'compact'`）

- **作用**：控制数值在 tooltip、数据标签、右端读数里的显示格式，不改变原始数据。可选值：`compact`（默认，≥1 亿显示“x.x亿”、≥1 万显示“x.x万”、否则千分位）、`thousands`（千分位，如 `1,234,567`）、`raw`（原样，最多 3 位小数）、`percent`（一位小数加 `%`，如 `12.3%`）、`currency`（`¥` + 千分位 + 两位小数）。 本图实现：控制散点 tooltip 中的 x/y 数值与回归线方程。
- **建议**：金额大数用 `compact`，表格/财务口径用 `thousands` 或 `currency`。 已经是百分数的列用 `percent`，不要再乘 100。 同一页多张图保持一致的 `fmt`，避免“万/千分位”混排。
- **示例**：`edv.trend(df, x="销售额", y="利润", fmt="thousands")`
- **报错**：`fmt="commas"`：`ValueError: fmt='commas' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）（`int`，默认 `400`）

- **作用**：单张图的容器高度，单位像素，最小 120。不同函数的默认高度不同（本函数默认值见参数总览）。高度只影响画布，不改变数据；图例/标题/坐标轴会自动占用内部空间。
- **建议**：普通看板 320~460；层级图/关系图建议 ≥420。 多张图并排时高度取一致，视觉更整齐。 `height` 小于 120 会直接报错，不要用它做“隐藏图”。
- **示例**：`edv.trend(df, x="销售额", y="利润", height=520)`
- **报错**：`height=100`：`ValueError: height 至少 120（像素），收到 100`；`height="400"`：同样报错（必须是 `int/float`）。

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题（浅色 / 深色）（`str`，默认 `'light'`）

- **作用**：页面主题，只支持 `"light"`（默认，白底深字）和 `"dark"`（深底浅字）。主题会同时改变背景、文字、坐标轴、tooltip 和默认色板的取色（`theme.palette`）。
- **建议**：常规报表/打印用 `light`；大屏、夜间模式用 `dark`。 多图看板统一主题，不要一张亮一张暗。 深色下避免使用低饱和的 `morandi` 色板，对比度会不够。
- **示例**：`edv.trend(df, x="销售额", y="利润", theme="dark")`
- **报错**：`theme="blue"`：`ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `legend` — 是否显示图例（`bool | None`，默认 `None`）

- **作用**：是否显示图例。`None` 表示“按语义自动决定”（有色分组时显示、没有分组时隐藏），`True`/`False` 为强制开关。只有真正用颜色/名称区分系列的函数才会生效。 本图实现：默认 `None`（=有 `color` 才显示回归系列图例）；单系列不显示。
- **建议**：类目多且颜色即含义（产品、渠道）时保留图例。 图例项超过 10 个时图例会滚动，建议先 `top_n` 或合并小类。 单系列图关闭图例，把空间留给图形。
- **示例**：`edv.trend(df, x="销售额", y="利润", legend=False)`
- **报错**：无校验：传非布尔值会经 `bool()` 转换（非空字符串为 `True`）。

### `labels` — 是否显示数据标签（`bool`，默认 `False`）

- **作用**：是否在图形上直接显示文字标签（类目名/数值/百分比）。默认值因函数而异；有的函数固定显示标签、不支持关闭。 本图实现：**不生效**。散点没有标签，`spec.labels` 被 JS 忽略。
- **建议**：类目 ≤8 个时打开标签，读者不用来回看 tooltip。 数据密集（散点、关系图）时关闭，避免文字糊成一片。 百分比标签通常配合 `fmt="percent"`。
- **示例**：`edv.trend(df, x="销售额", y="利润", labels=False)`
- **报错**：无校验：会经 `bool()` 转换，传 `"no"` 也是 `True`。

### `zoom` — 缩放/漫游（`bool | str`，默认 `False`）

- **作用**：是否开启缩放。多数函数接受 `bool`；`candlestick` 默认 `"auto"`，表示分类数超过 30 时自动显示底部缩放条。不支持缩放的图会接受该参数但不产生效果。 本图实现：**不生效**。散点不提供 dataZoom。
- **建议**：时间序列很长（>60 点）时用 `zoom=True` 或放到 `candlestick` 的 `"auto"`。 层级/关系图本身可拖拽缩放，不必再开 `zoom`。 截图/打印场景关掉缩放，画面更干净。
- **示例**：`edv.trend(df, x="销售额", y="利润", zoom=True)`

### `link` — 联动分组名（`str | None`，默认 `None`）

- **作用**：把多张图放进同一个联动组：点击某张图的类目，同组中包含该维度列的其他图会按该值过滤。同一个组名（如 `"g1"`）即可联动；默认 `None` 不联动。注意：`table`/`wordcloud` 是 HTML 渲染，只能作为**被联动方**，点击它们不会触发联动。 本图实现：点击散点会按 `x` 值联动；回归线本身不参与联动。
- **建议**：同一看板里的明细表用同一个 `link` 组名，点图即可筛表。 联动维度由点击的图决定，各图尽量共享同一列（如 `产品`）。 组名建议用有含义的英文/拼音，不要用随机串。
- **示例**：`edv.trend(df, x="销售额", y="利润", link="g1")`
- **报错**：无校验：传数字/对象会原样写入 spec，JS 端作为对象键使用，建议只传字符串。

### `max_rows` — 嵌入前端的最大行数（`int`，默认 `2000000`）

- **作用**：Python 侧只把前 `max_rows` 行（默认 20000）的数据嵌入 HTML，超过时按均匀间隔抽样，并把提示写入 `chart.warnings["warnings"]`。`table` 特殊：默认 200，且最终最多嵌入 200 行。抽样只发生在“嵌入”阶段，不影响函数内已经算好的统计（如相关系数、回归系数）。
- **建议**：前端交互图保持默认 20000 即可；超大表用 `table(max_rows=...)` 控制体积。 需要完整数据时导出 Excel/CSV，不要让 HTML 承担全量数据。 抽样后 tooltip 的明细行数会变少，但聚合图的总量不受影响。
- **示例**：`edv.trend(df, x="销售额", y="利润", max_rows=500)`
- **报错**：无校验：传 `0` 或负数会得到空数据（图形空白），建议传正整数。

## 返回值

返回 `eazy_data_viz.Chart` 对象（`chart.spec` 是完整的渲染 spec，`chart.data` 是嵌入前端的数据）。

- 通用方法：`chart.save(path)` 写单文件 HTML、`chart.to_html()` 返回字符串、`chart.palette(name)` 链式换色、`chart.show()` 在浏览器打开；`chart.warnings` 记录采样等降级提示（详见 [交互与联动指南](../guides/06-interaction.md)）。

本图的关键 spec 字段（`chart.spec`）：

| 字段 | 含义 |
| --- | --- |
| `type` | 固定为 `"trend"`。 |
| `roles` | `{"x": 自变量列, "y": 因变量列, "color": 分组列或 None}`。 |
| `fit` | `{"slope", "intercept", "r2", "xmin", "xmax"}`：Python 端最小二乘结果，R² 可能为 `null`。 |
| `legend` | 默认 `color is not None`；有分组时显示图例。 |
| `xlim / ylim` | 两轴显示范围；回归线仍按全量数据计算。 |
| `labels / zoom` | 签名保留，但当前 builder 不读取（无点标签、无缩放）。 |

## 完整示例

以下示例全部基于 `edv.sample_df()`（1500 行、11 列）或由它派生的小表；输出文件写到 `examples/output/`。

### 示例 1：最简：销售额 vs 利润

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.trend(df, x="销售额", y="利润")
chart.save("examples/output/trend_1.html")
```

**输出**：1500 个散点 + 一条虚线回归线，右上角显示“R² = 0.61”（示例数据实测 0.6095）；自动标题“利润 与 销售额 趋势”。

### 示例 2：典型：按大区分组着色

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.trend(
    df,
    x="销售额",
    y="利润",
    color="大区",
    title="销售额与利润的线性关系",
    subtitle="颜色=大区 · 回归线基于全量数据",
    height=440,
)
chart.save("examples/output/trend_2.html")
```

**输出**：四个大区各一色散点，图例显示在顶部；回归线只有一条且颜色固定为调色板第 4 色，R² 仍是全量口径。

### 示例 3：格式化与深色主题

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.trend(df, x="客户数", y="销售额", fmt="thousands", theme="dark")
chart.palette("tableau")
chart.save("examples/output/trend_3.html")
```

**输出**：深色背景 + Tableau 配色；tooltip 中客户数与销售额都带千分位，右上角 R² 文字自动转浅色。

### 示例 4：先聚合再拟合：大区层面

```python
import eazy_data_viz as edv

df = edv.sample_df()
agg = df.groupby("大区", as_index=False).agg(
    销售额=("销售额", "sum"),
    利润=("利润", "sum"),
)
chart = edv.trend(agg, x="销售额", y="利润", color="大区", height=380)
chart.save("examples/output/trend_4.html")
```

**输出**：只有 4 个点，回归线几乎穿过所有点，R² 会很高——这是“聚合后的关系”，与逐行关系的含义不同，解读时要说明粒度。

### 示例 5：联动：点击分组点过滤明细

```python
import eazy_data_viz as edv

df = edv.sample_df()
tr = edv.trend(df, x="销售额", y="利润", color="大区", link="tr1")
tbl = edv.table(df, columns=["大区", "销售额", "利润"], link="tr1", limit=40)
edv.dashboard(tr, tbl, title="趋势图联动", cols=2).save("examples/output/trend_5.html")
```

**输出**：点击某个散点，右侧表格按该点所属大区过滤；回归线与 R² 不随联动变化。

## 常见问题 / 注意事项

- **R² 是怎么算的？显示在哪？** Python 用 `np.polyfit(x, y, 1)` 得到斜率/截距，再用 `1 - SS_res / SS_tot` 算 R²（`SS_tot<=0` 时为 `None`）。前端把它画成右上角的 graphic 文本“R² = 0.xxx”，不是副标题。
- **R² 为 `None` 是什么意思？** 当 y 完全没有波动（`SS_tot<=0`）或 x 只有一个取值时，R² 没有定义，`spec.fit.r2` 为 `None`，页面不显示 R² 文本。
- **回归线能按分组分别拟合吗？** 不能。`color` 只改变散点颜色与图例，回归线永远基于全部有效点。需要分组拟合请对每个分组分别调用 `trend()`，再把多张图放进 `dashboard`。
- **为什么斜率和我想的方向相反？** 检查 `x`/`y` 是否传反：拟合的是 `y = slope*x + intercept`，交换两列后斜率变成倒数关系，R² 不变但业务解释完全不同。
- **`labels=True` 为什么没有效果？** 当前 trend builder 没有读取 `spec.labels`，散点标签恒为关闭。该参数只写入 spec，属于已知差异。

## 相关图表

| 图表 | 说明 |
| --- | --- |
| [`quadrant`](quadrant.md) | 四象限散点图（不拟合、只划分区域，更适合汇报定位） |
| [`matrix`](matrix.md) | 相关系数矩阵（多变量两两相关性的总览） |
| [`sparkline`](sparkline.md) | 迷你走势图（时间维度上的走势） |
| [`theme_river`](theme_river.md) | 主题河流图（构成随时间的变化） |

- 回到总览：`docs/EXTRA_CHARTS.md`、`docs/AI_GUIDE.md`
