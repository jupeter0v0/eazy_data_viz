# `sparkline` — 迷你走势图（按分组纵向堆叠的小型面积折线，用于紧凑对比走势）

迷你走势图把每个分组画成一行没有坐标轴的小折线（带淡淡面积），左侧写分组名，右侧写最新值。它牺牲精确刻度，换取“一屏对比多条走势”的信息密度，适合放在报表或看板的角落。

每一行共享同一横轴类目（按首次出现顺序或 `sort="x"` 排序），纵轴各自独立缩放（每一行按自己的 dataMin/dataMax 自适应）。

- **适合**：3~10 个分组、时间点 10~60 个，想快速看谁在涨谁在跌；高度 200~400 的小卡片。
- **不适合**：需要精确读数值、分组超过 12 个、或时间点非常多时不要用；请改用 `trend`、`line` 或 `theme_river`。

> 本页所有示例均可直接复制运行：先 `import eazy_data_viz as edv`，再 `df = edv.sample_df()`。

## 函数签名

```python
eazy_data_viz.sparkline(
    data,
    x,
    y,
    *,
    group,
    agg='sum',
    title=None,
    subtitle=None,
    fmt='compact',
    height=260,
    theme='light',
    max_rows=200000,
) -> Chart
```

参数按签名顺序：`data` → 本图专有参数 → 关键字参数（`*` 之后全部只能按关键字传）。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | pandas.DataFrame（也接受 dict / list，内部会转成 DataFrame） | 无 | 是 | 数据源（DataFrame） |
| `x` | str | 无 | 是 | 横轴列（通常是时间或有序类目） |
| `y` | str | 无 | 是 | 纵轴数值列 |
| `group` | str | 无 | 是 | 分组列（每行一个分组） |
| `agg` | str | 'sum' | 否 | 聚合方式（同一类目多条记录时如何合并） |
| `title` | str 或 None | None | 否 | 图表主标题 |
| `subtitle` | str 或 None | None | 否 | 副标题（口径/单位/时间范围） |
| `fmt` | str | 'compact' | 否 | 数值格式（tooltip / 标签） |
| `height` | int | 260 | 否 | 画布高度（像素） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | str | 'light' | 否 | 主题（浅色 / 深色） |
| `max_rows` | int | 200000 | 否 | 嵌入前端的最大行数 |

> 共 11 个参数。签名里 `*` 之后是 keyword-only，必须写参数名；`data` 之前的位置参数（本图专有）可以按位置传。

## 参数详解

### `data` — 数据源（DataFrame）（`pandas.DataFrame`，必填）

- **作用**：图的原始数据。函数会按参数名从里面取列：`data` 既可以是 `pandas.DataFrame`，也可以是 `dict`（列名 → 值序列）或 `list`（记录列表），内部通过 `ensure_frame()` 统一转换。转换后必须至少有 1 行，否则报 `ValueError`。每张图最多嵌入 40 列（`MAX_COLS=40`），超过的部分会被丢弃并写入 `chart.warnings["warnings"]`。
- **建议**：首选 `pandas.DataFrame`；列名建议保持唯一、非空，中文列名可以直接用。 数值列用数值 dtype（`int64/float64`）；文本数字请先 `pd.to_numeric()`。 日期列用 `datetime64[ns]`（或可被 `pd.to_datetime()` 解析的字符串）。 作图前先处理空值：不同图对空值的策略不同（见各函数“常见问题”）。
- **示例**：`edv.sparkline(data=df, x="月份", y="销售额", group="产品")`
- **报错**：传入空 DataFrame：`ValueError: 数据为空（0 行），无法绘图。`；传入 `None`：`ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`

### `x` — 横轴列（通常是时间或有序类目）（`str`，必填）

- **作用**：每个不同取值对应折线上的一个点。类目顺序按数据中首次出现顺序；如果值是日期样式，JS 会用日期比较函数排序，因此乱序数据也能正确排列。
- **建议**：`月份`（有序分类）最稳：顺序天然正确。 `日期`（1500 行逐日）会得到 1500 个点，折线噪声大，建议先聚合到周/月。 避免无序文本类目（城市名），横轴顺序会没有意义。
- **示例**：`edv.sparkline(df, y="销售额", group="产品", x="月份")`
- **报错**：列名写错：`KeyError: "x列 '不存在' 不存在。当前可用的列有：..."`

### `y` — 纵轴数值列（`str`，必填）

- **作用**：必须是数值列；每一行分组在该列上的聚合值构成折线。空值会被跳过，不影响同组其它点。
- **建议**：可加总/可平均的指标：`销售额`、`订单数`、`利润`。 不同分组的量级差异很大也 OK——每行独立缩放，但读者无法跨行比较绝对大小，需在标题里说明。 含大量空值时折线会断开，建议先填补或过滤。
- **示例**：`edv.sparkline(df, x="月份", group="产品", y="销售额")`
- **报错**：传文本列：`TypeError: y（数值）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `group` — 分组列（每行一个分组）（`str`，必填）

- **作用**：必填（keyword-only，无默认值）。每个不同取值渲染成一行迷你折线，最多显示 12 行（超出部分被截断）。分组名会截断到 12 个字符显示在左侧。
- **建议**：低基数列：`产品`（4）、`大区`（4）、`渠道`（3）。 分组超过 12 个请先合并/筛选，否则后面的分组不会画出来。 不要传日期列做分组——会变成几百行。
- **示例**：`edv.sparkline(df, x="月份", y="销售额", group="产品")`
- **报错**：不传 `group`：`TypeError: sparkline() missing 1 required keyword-only argument: 'group'`；列名写错：`KeyError: "group（分组）列 '不存在' 不存在。当前可用的列有：..."`

### `agg` — 聚合方式（同一类目多条记录时如何合并）（`str`，默认 `'sum'`）

- **作用**：同一分类下有多条记录时，把数值列合成一个数的方法。可选：`sum`（默认）、`mean`、`count`、`max`、`min`、`median`。当函数没有拿到数值列（例如没传 `values`/`value`）时，内部会把 `agg` 强制为 `count`，按记录条数统计。 本图实现：按 `(x, group)` 分组后用 `agg` 聚合，是真正影响走势的聚合参数。
- **建议**：金额、订单数用 `sum`；单价、率值用 `mean` 或 `median`。 想看“有多少条记录”就传 `agg="count"`，此时数值列只作存在性检查。 `median` 对极端值更稳健，适合客单价、利润率这类偏态指标。
- **示例**：`edv.sparkline(df, x="月份", y="销售额", group="产品", agg="mean")`
- **报错**：`agg="average"`：`ValueError: agg='average' 不支持，可选：sum, mean, count, max, min, median`

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在卡片顶部的主标题。传 `None` 时使用函数内置的自动标题；传字符串则完全覆盖自动标题。标题只影响展示，不参与数据聚合与排序。
- **建议**：建议 8~18 个汉字，写清“指标 + 维度 + 口径”，例如 `销售额 按 大区`。 时间范围、币种、口径放在 `subtitle`，不要全部堆进标题。 标题是单行布局，过长会被卡片宽度截断，不建议加换行符。
- **示例**：`edv.sparkline(df, x="月份", y="销售额", group="产品", title="华东区销售构成")`

### `subtitle` — 副标题（口径/单位/时间范围）（`str | None`，默认 `None`）

- **作用**：标题下方的第二行说明，常用于补充统计口径、单位、时间范围或“较上期 +8%”这类结论。默认 `None`，不显示副标题；传空字符串等同于不显示。
- **建议**：写口径而不重复标题，例如 `2024 年 1-12 月 · 含税`。 颜色比标题浅，信息量控制在 30 字以内。 需要换行时直接写 `\n` 不会被解析成 HTML，建议保持单行。
- **示例**：`edv.sparkline(df, x="月份", y="销售额", group="产品", subtitle="2024 年 1-12 月 · 含税")`

### `fmt` — 数值格式（tooltip / 标签）（`str`，默认 `'compact'`）

- **作用**：控制数值在 tooltip、数据标签、右端读数里的显示格式，不改变原始数据。可选值：`compact`（默认，≥1 亿显示“x.x亿”、≥1 万显示“x.x万”、否则千分位）、`thousands`（千分位，如 `1,234,567`）、`raw`（原样，最多 3 位小数）、`percent`（一位小数加 `%`，如 `12.3%`）、`currency`（`¥` + 千分位 + 两位小数）。 本图实现：控制每行右侧“最新值”读数和 tooltip 数值。
- **建议**：金额大数用 `compact`，表格/财务口径用 `thousands` 或 `currency`。 已经是百分数的列用 `percent`，不要再乘 100。 同一页多张图保持一致的 `fmt`，避免“万/千分位”混排。
- **示例**：`edv.sparkline(df, x="月份", y="销售额", group="产品", fmt="thousands")`
- **报错**：`fmt="commas"`：`ValueError: fmt='commas' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）（`int`，默认 `260`）

- **作用**：单张图的容器高度，单位像素，最小 120。不同函数的默认高度不同（本函数默认值见参数总览）。高度只影响画布，不改变数据；图例/标题/坐标轴会自动占用内部空间。
- **建议**：普通看板 320~460；层级图/关系图建议 ≥420。 多张图并排时高度取一致，视觉更整齐。 `height` 小于 120 会直接报错，不要用它做“隐藏图”。
- **示例**：`edv.sparkline(df, x="月份", y="销售额", group="产品", height=520)`
- **报错**：`height=100`：`ValueError: height 至少 120（像素），收到 100`；`height="400"`：同样报错（必须是 `int/float`）。

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题（浅色 / 深色）（`str`，默认 `'light'`）

- **作用**：页面主题，只支持 `"light"`（默认，白底深字）和 `"dark"`（深底浅字）。主题会同时改变背景、文字、坐标轴、tooltip 和默认色板的取色（`theme.palette`）。
- **建议**：常规报表/打印用 `light`；大屏、夜间模式用 `dark`。 多图看板统一主题，不要一张亮一张暗。 深色下避免使用低饱和的 `morandi` 色板，对比度会不够。
- **示例**：`edv.sparkline(df, x="月份", y="销售额", group="产品", theme="dark")`
- **报错**：`theme="blue"`：`ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `max_rows` — 嵌入前端的最大行数（`int`，默认 `200000`）

- **作用**：Python 侧只把前 `max_rows` 行（默认 20000）的数据嵌入 HTML，超过时按均匀间隔抽样，并把提示写入 `chart.warnings["warnings"]`。`table` 特殊：默认 200，且最终最多嵌入 200 行。抽样只发生在“嵌入”阶段，不影响函数内已经算好的统计（如相关系数、回归系数）。
- **建议**：前端交互图保持默认 20000 即可；超大表用 `table(max_rows=...)` 控制体积。 需要完整数据时导出 Excel/CSV，不要让 HTML 承担全量数据。 抽样后 tooltip 的明细行数会变少，但聚合图的总量不受影响。
- **示例**：`edv.sparkline(df, x="月份", y="销售额", group="产品", max_rows=500)`
- **报错**：无校验：传 `0` 或负数会得到空数据（图形空白），建议传正整数。

## 返回值

返回 `eazy_data_viz.Chart` 对象（`chart.spec` 是完整的渲染 spec，`chart.data` 是嵌入前端的数据）。

- 通用方法：`chart.save(path)` 写单文件 HTML、`chart.to_html()` 返回字符串、`chart.palette(name)` 链式换色、`chart.show()` 在浏览器打开；`chart.warnings` 记录采样等降级提示（详见 [交互与联动指南](../guides/06-interaction.md)）。

本图的关键 spec 字段（`chart.spec`）：

| 字段 | 含义 |
| --- | --- |
| `type` | 固定为 `"sparkline"`。 |
| `roles` | `{"x": 横轴列, "y": 数值列, "color": 分组列}`（分组写在 `color` 角色里）。 |
| `series / sparkData` | 预留的“Python 预计算系列”字段；当前 Python 不写入，JS 走数据回退分支自行聚合。 |
| `agg` | 每个 (横轴, 分组) 单元格的聚合方式，默认 `sum`。 |
| `fmt` | 右侧最新值与前缀数值的格式。 |
| `无 legend / labels / zoom / xtitle / ytitle` | 本函数的签名里没有这些参数；迷你图本身不画坐标轴与图例，也不能缩放。 |

## 完整示例

以下示例全部基于 `edv.sample_df()`（1500 行、11 列）或由它派生的小表；输出文件写到 `examples/output/`。

### 示例 1：最简：产品 × 月份

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.sparkline(df, x="月份", y="销售额", group="产品")
chart.save("examples/output/sparkline_1.html")
```

**输出**：四行迷你折线（四条产品线），每行左侧是产品名、右侧是 12 月最新值；没有坐标轴与网格，只有淡淡的面积填充，自动标题“销售额 走势”。

### 示例 2：典型：大区销售走势对比

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.sparkline(
    df,
    x="月份",
    y="订单数",
    group="大区",
    title="各大区订单走势",
    height=300,
)
chart.save("examples/output/sparkline_2.html")
```

**输出**：四行大区折线纵向堆叠；`height=300` 时每行约 75px，折线与面积都还清晰，适合放在看板卡片里。

### 示例 3：先聚合再画：按月汇总更清晰

```python
import eazy_data_viz as edv

df = edv.sample_df()
monthly = (
    df.groupby(["月份", "产品"], as_index=False, observed=True)["销售额"]
      .sum()
)
chart = edv.sparkline(monthly, x="月份", y="销售额", group="产品", height=360)
chart.save("examples/output/sparkline_3.html")
```

**输出**：数据已经聚合到“月份 × 产品”，迷你图只做渲染，曲线更平滑；这也是推荐的用法——Python 先算好，前端少算。

### 示例 4：深色主题与配色

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.sparkline(df, x="月份", y="利润", group="产品", theme="dark")
chart.palette("carbon")
chart.save("examples/output/sparkline_4.html")
```

**输出**：深色背景上四行浅色折线 + 低透明度面积；左侧分组名与右侧数值自动使用浅色文字。

### 示例 5：多图拼看板

```python
import eazy_data_viz as edv

df = edv.sample_df()
sales = edv.sparkline(df, x="月份", y="销售额", group="产品", title="销售额走势")
orders = edv.sparkline(df, x="月份", y="订单数", group="大区", title="订单数走势")
edv.dashboard(sales, orders, title="走势看板", cols=2).save("examples/output/sparkline_5.html")
```

**输出**：两张迷你图并排放在同一看板的两个卡片里，共用标题“走势看板”；迷你图没��图例，靠左侧分组名区分。

> 以上示例对应的可运行脚本见 `examples/charts/sparkline.py`，运行 `PYTHONPATH=. python examples/charts/sparkline.py` 会一次性生成全部 HTML。

## 常见问题 / 注意事项

### Q1. 迷你走势图和普通折线图的区别？

迷你图没有坐标轴、刻度、网格与图例，每行独立缩放，只回答“走势形状”；折线图有统一坐标轴，能精确比较绝对值。把迷你图当“一眼看趋势”的缩略图，而不是精确图表。

### Q2. 为什么每一行的数值范围不一样？

JS 对每一行单独设置 yAxis 的 `dataMin/dataMax`，所以每行都被拉满高度。好处是小分组也看得见，代价是不能跨行比较绝对大小；需要跨行比较请用 `theme_river` 或基础 `line`。

### Q3. 横轴顺序为什么和我想的不一样？

默认按分组数据中类目的首次出现顺序。数据没排序时顺序会乱；本函数的签名没有 `sort` 参数，请先在 Python 里排序（例如按 `日期` 升序）或直接传有序的 `月份`。

### Q4. 最多能画多少行？

12 行。超过 12 个分组时后面的分组会被静默丢弃（`groups.slice(0, 12)`），不会报错。

### Q5. 右侧的数值是总和还是最新值？

是该分组最后一个横轴类目的聚合值（按排序后的最后一点），不是总和。要看总和请用 `bar` 或 `table`。

## 相关图表

| 图表 | 说明 |
| --- | --- |
| [`theme_river`](theme_river.md) | 主题河流图（需要看占比演化而不是单行走势） |
| [`trend`](trend.md) | 趋势图（需要拟合线与 R² 时用它） |
| [`table`](table.md) | 明细表（需要精确数值时用它） |
| [`calendar`](calendar.md) | 日历热力图（按天看密度而不是走势） |

- 回到总览：`docs/EXTRA_CHARTS.md`、`docs/AI_GUIDE.md`
