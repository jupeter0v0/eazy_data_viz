# `gantt` — 甘特图（按任务行展示起止时间的水平时间条）

甘特图把每个任务画成一条水平时间条：横轴是时间，纵轴是任务，条的长度就是任务的起止区间。它适合展示项目排期、活动周期、任务依赖之外的时间安排（依赖关系请用其它图）。

同一个任务出现多行时，函数取最早开始、最晚结束合并成一条。`color` 可以把任务按分组着色，并自动生成图例。

- **适合**：5~30 个任务、有明确起止时间、需要看排期或周期重叠。
- **不适合**：只有单点时间（没有结束时间）用 `bar`/`scatter`；任务超过 30 个时行高会被压扁，建议先分组或筛选。

> 本页所有示例均可直接复制运行：先 `import eazy_data_viz as edv`，再 `df = edv.sample_df()`。

## 函数签名

```python
eazy_data_viz.gantt(
    data,
    task,
    start,
    end,
    *,
    color=None,
    agg='sum',
    sort=None,
    top_n=None,
    title=None,
    subtitle=None,
    fmt='compact',
    height=420,
    theme='light',
    legend=None,
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
| `task` | str | 无 | 是 | 任务列（纵轴类目） |
| `start` | str | 无 | 是 | 开始日期列 |
| `end` | str | 无 | 是 | 结束日期列 |
| `color` | str 或 None | None | 否 | 分组列（决定时间条颜色与图例） |
| `agg` | str | 'sum' | 否 | 聚合方式（同一类目多条记录时如何合并） |
| `sort` | str 或 None | None | 否 | 排序方式 |
| `top_n` | int 或 None | None | 否 | 只保留前 N 项 |
| `title` | str 或 None | None | 否 | 图表主标题 |
| `subtitle` | str 或 None | None | 否 | 副标题（口径/单位/时间范围） |
| `fmt` | str | 'compact' | 否 | 数值格式（tooltip / 标签） |
| `height` | int | 420 | 否 | 画布高度（像素） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | str | 'light' | 否 | 主题（浅色 / 深色） |
| `legend` | bool 或 None | None | 否 | 是否显示图例 |
| `labels` | bool | True | 否 | 是否显示数据标签 |
| `zoom` | bool 或 str | False | 否 | 缩放/漫游 |
| `link` | str 或 None | None | 否 | 联动分组名 |
| `max_rows` | int | 200000 | 否 | 嵌入前端的最大行数 |

> 共 18 个参数。签名里 `*` 之后是 keyword-only，必须写参数名；`data` 之前的位置参数（本图专有）可以按位置传。

## 参数详解

### `data` — 数据源（DataFrame）（`pandas.DataFrame`，必填）

- **作用**：图的原始数据。函数会按参数名从里面取列：`data` 既可以是 `pandas.DataFrame`，也可以是 `dict`（列名 → 值序列）或 `list`（记录列表），内部通过 `ensure_frame()` 统一转换。转换后必须至少有 1 行，否则报 `ValueError`。每张图最多嵌入 40 列（`MAX_COLS=40`），超过的部分会被丢弃并写入 `chart.warnings["warnings"]`。
- **建议**：首选 `pandas.DataFrame`；列名建议保持唯一、非空，中文列名可以直接用。 数值列用数值 dtype（`int64/float64`）；文本数字请先 `pd.to_numeric()`。 日期列用 `datetime64[ns]`（或可被 `pd.to_datetime()` 解析的字符串）。 作图前先处理空值：不同图对空值的策略不同（见各函数“常见问题”）。
- **报错**：传入空 DataFrame：`ValueError: 数据为空（0 行），无法绘图。`；传入 `None`：`ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`

### `task` — 任务列（纵轴类目）（`str`，必填）

- **作用**：每个不同取值对应一行时间条；同一任务的多行会被合并（开始取 min、结束取 max）。缺失值归为 `(空)`。行顺序按开始时间升序，第一行在顶部。
- **建议**：用任务名/项目名/活动名，控制 5~20 行。 如果任务名重复但需要分开画，请先加唯一后缀。 任务名过长会被截断到 16 个字符，建议 ≤12 字。
- **示例**：`edv.gantt(tasks, start="开始", end="结束", task="任务")`
- **报错**：不传：`TypeError: gantt() missing 3 required positional arguments: 'start', 'end', ...`；列名写错：`KeyError: "task（任务）列 '不存在' 不存在。当前可用的列有：..."`

### `start` — 开始日期列（`str`，必填）

- **作用**：必须是日期/时间类型或可解析文本；数值列会被拒绝。空值行会被跳过（不画该任务）。
- **建议**：与 `end` 使用同一精度（都到天或都到秒），否则工期计算会差一天。 先确保 start ≤ end；反了的数据 Python 会给 warning，JS 会静默交换。 时间戳带时区时建议先 `pd.to_datetime(...).dt.tz_localize(None)`。
- **示例**：`edv.gantt(tasks, task="任务", end="结束", start="开始")`
- **报错**：传数值列：`TypeError: start（开始日期）列 '销售额' 需要是日期/时间类型，但当前是数值类型。请换一列。（例如 gantt(df, task="任务", start=start_col, end=end_col)）`

### `end` — 结束日期列（`str`，必填）

- **作用**：同 `start`。若某行 `end < start`，Python 会在 `chart.warnings` 里提示“gantt 有 N 行结束日期早于开始日期”，JS 端会交换两者继续绘制（不会报错）。
- **建议**：结束日期通常用“最后一天”（含）语义；工期显示为天数差。 超过 1 年的任务条会占满整行，注意拆分阶段。 空结束日期的行会被直接跳过。
- **示例**：`edv.gantt(tasks, task="任务", start="开始", end="结束")`
- **报错**：传数值列：`TypeError: end（结束日期）列 '利润' 需要是日期/时间类型，但当前是数值类型。请换一列。`

### `color` — 分组列（决定时间条颜色与图例）（`str | None`，默认 `None`）

- **作用**：每个取值一种颜色，同一任务只取第一次出现时的分组；有 `color` 时图例默认显示（`legend=None` 自动）。不传时所有条同色、无图例。
- **建议**：用负责人/团队/阶段 `大区` 等低基数列。 分组别超过 6 个，否则颜色难区分且图例占空间。 图例可用 `legend=False` 关闭，但颜色仍按分组区分。
- **示例**：`edv.gantt(tasks, task="任务", start="开始", end="结束", color="负责人")`
- **报错**：列名写错：`KeyError: "color列 '不存在' 不存在。当前可用的列有：..."`

### `agg` — 聚合方式（同一类目多条记录时如何合并）（`str`，默认 `'sum'`）

- **作用**：同一分类下有多条记录时，把数值列合成一个数的方法。可选：`sum`（默认）、`mean`、`count`、`max`、`min`、`median`。当函数没有拿到数值列（例如没传 `values`/`value`）时，内部会把 `agg` 强制为 `count`，按记录条数统计。 本图实现：每条记录画一条任务条，`agg` 不参与计算（传什么都一样）。
- **建议**：金额、订单数用 `sum`；单价、率值用 `mean` 或 `median`。 想看“有多少条记录”就传 `agg="count"`，此时数值列只作存在性检查。 `median` 对极端值更稳健，适合客单价、利润率这类偏态指标。
- **示例**：`edv.gantt(tasks, task="任务", start="开始", end="结束", agg="mean")`
- **报错**：`agg="average"`：`ValueError: agg='average' 不支持，可选：sum, mean, count, unique, max, min, median`

### `sort` — 排序方式（`str | None`，默认 `None`）

- **作用**：控制分类的排列顺序。本库只认 `"asc"`、`"desc"`、`"x"`、`"none"` 四种语义，但**不做枚举校验**：传其他字符串不会报错，会静默按该图默认顺序渲染。 本图实现：**不生效**。任务条固定按开始时间升序排列（最早的在上）。
- **建议**：排行榜用 `asc/desc`；时间序列用 `x`（按列顺序/时间升序）。 需要保持数据原始顺序时传 `sort="none"`。 分类是 `pd.Categorical`（如 `月份`）时，`x` 会按分类顺序而不是字母序。
- **示例**：`edv.gantt(tasks, task="任务", start="开始", end="结束", sort="asc")`
- **报错**：不存在的值不报错：`sort="DESC"` 会被忽略并按默认顺序渲染（大小写敏感）。；对不读取 `sort` 的图（如 pyramid/sunburst/sankey）传任何值都不会改变图形。

### `top_n` — 只保留前 N 项（`int | None`，默认 `None`）

- **作用**：按当前排序只保留前 N 个类目，`None`（默认）表示全部保留。必须是 ≥1 的整数（`bool` 不算）。不同函数对“多出来的部分”处理不同：rose 会把剩余项合并成“其他”，wordcloud 直接截断，其余函数多数不读取该字段。 本图实现：**不生效**。所有任务都会绘制。
- **建议**：类目超过 12 个时用 `top_n` 收敛，避免标签重叠。 玫瑰图配 `top_n` 会得到“其他”扇区，其余图不会。 配合 `sort="desc"` 使用才有“前 N 大”的含义。
- **示例**：`edv.gantt(tasks, task="任务", start="开始", end="结束", top_n=5)`
- **报错**：`top_n=0`：`ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`；`top_n=True`：同样报错（`bool` 被显式拒绝）。

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在卡片顶部的主标题。传 `None` 时使用函数内置的自动标题；传字符串则完全覆盖自动标题。标题只影响展示，不参与数据聚合与排序。
- **建议**：建议 8~18 个汉字，写清“指标 + 维度 + 口径”，例如 `销售额 按 大区`。 时间范围、币种、口径放在 `subtitle`，不要全部堆进标题。 标题是单行布局，过长会被卡片宽度截断，不建议加换行符。
- **示例**：`edv.gantt(tasks, task="任务", start="开始", end="结束", title="华东区销售构成")`

### `subtitle` — 副标题（口径/单位/时间范围）（`str | None`，默认 `None`）

- **作用**：标题下方的第二行说明，常用于补充统计口径、单位、时间范围或“较上期 +8%”这类结论。默认 `None`，不显示副标题；传空字符串等同于不显示。
- **建议**：写口径而不重复标题，例如 `2024 年 1-12 月 · 含税`。 颜色比标题浅，信息量控制在 30 字以内。 需要换行时直接写 `\n` 不会被解析成 HTML，建议保持单行。
- **示例**：`edv.gantt(tasks, task="任务", start="开始", end="结束", subtitle="2024 年 1-12 月 · 含税")`

### `fmt` — 数值格式（tooltip / 标签）（`str`，默认 `'compact'`）

- **作用**：控制数值在 tooltip、数据标签、右端读数里的显示格式，不改变原始数据。可选值：`compact`（默认，≥1 亿显示“x.x亿”、≥1 万显示“x.x万”、否则千分位）、`thousands`（千分位，如 `1,234,567`）、`raw`（原样，最多 3 位小数）、`percent`（一位小数加 `%`，如 `12.3%`）、`currency`（`¥` + 千分位 + 两位小数）。 本图实现：**不生效**。tooltip 里的日期固定 `YYYY-MM-DD`，工期固定 1 位小数。
- **建议**：金额大数用 `compact`，表格/财务口径用 `thousands` 或 `currency`。 已经是百分数的列用 `percent`，不要再乘 100。 同一页多张图保持一致的 `fmt`，避免“万/千分位”混排。
- **示例**：`edv.gantt(tasks, task="任务", start="开始", end="结束", fmt="thousands")`
- **报错**：`fmt="commas"`：`ValueError: fmt='commas' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）（`int`，默认 `420`）

- **作用**：单张图的容器高度，单位像素，最小 120。不同函数的默认高度不同（本函数默认值见参数总览）。高度只影响画布，不改变数据；图例/标题/坐标轴会自动占用内部空间。
- **建议**：普通看板 320~460；层级图/关系图建议 ≥420。 多张图并排时高度取一致，视觉更整齐。 `height` 小于 120 会直接报错，不要用它做“隐藏图”。
- **示例**：`edv.gantt(tasks, task="任务", start="开始", end="结束", height=520)`
- **报错**：`height=100`：`ValueError: height 至少 120（像素），收到 100`；`height="400"`：同样报错（必须是 `int/float`）。

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题（浅色 / 深色）（`str`，默认 `'light'`）

- **作用**：页面主题，只支持 `"light"`（默认，白底深字）和 `"dark"`（深底浅字）。主题会同时改变背景、文字、坐标轴、tooltip 和默认色板的取色（`theme.palette`）。
- **建议**：常规报表/打印用 `light`；大屏、夜间模式用 `dark`。 多图看板统一主题，不要一张亮一张暗。 深色下避免使用低饱和的 `morandi` 色板，对比度会不够。
- **示例**：`edv.gantt(tasks, task="任务", start="开始", end="结束", theme="dark")`
- **报错**：`theme="blue"`：`ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `legend` — 是否显示图例（`bool | None`，默认 `None`）

- **作用**：是否显示图例。`None` 表示“按语义自动决定”（有色分组时显示、没有分组时隐藏），`True`/`False` 为强制开关。只有真正用颜色/名称区分系列的函数才会生效。 本图实现：默认 `None`（=传了 `color` 才显示）；颜色即分组含义，建议保留。
- **建议**：类目多且颜色即含义（产品、渠道）时保留图例。 图例项超过 10 个时图例会滚动，建议先 `top_n` 或合并小类。 单系列图关闭图例，把空间留给图形。
- **示例**：`edv.gantt(tasks, task="任务", start="开始", end="结束", legend=False)`
- **报错**：无校验：传非布尔值会经 `bool()` 转换（非空字符串为 `True`）。

### `labels` — 是否显示数据标签（`bool`，默认 `True`）

- **作用**：是否在图形上直接显示文字标签（类目名/数值/百分比）。默认值因函数而异；有的函数固定显示标签、不支持关闭。 本图实现：生效。条形宽度 ≥26px 时在条内写任务名；空间不够则自动省略。
- **建议**：类目 ≤8 个时打开标签，读者不用来回看 tooltip。 数据密集（散点、关系图）时关闭，避免文字糊成一片。 百分比标签通常配合 `fmt="percent"`。
- **示例**：`edv.gantt(tasks, task="任务", start="开始", end="结束", labels=False)`
- **报错**：无校验：会经 `bool()` 转换，传 `"no"` 也是 `True`。

### `zoom` — 缩放/漫游（`bool | str`，默认 `False`）

- **作用**：是否开启缩放。多数函数接受 `bool`；`candlestick` 默认 `"auto"`，表示分类数超过 30 时自动显示底部缩放条。不支持缩放的图会接受该参数但不产生效果。 本图实现：**不生效**。甘特图当前版本没有 dataZoom。
- **建议**：时间序列很长（>60 点）时用 `zoom=True` 或放到 `candlestick` 的 `"auto"`。 层级/关系图本身可拖拽缩放，不必再开 `zoom`。 截图/打印场景关掉缩放，画面更干净。
- **示例**：`edv.gantt(tasks, task="任务", start="开始", end="结束", zoom=True)`

### `link` — 联动分组名（`str | None`，默认 `None`）

- **作用**：把多张图放进同一个联动组：点击某张图的类目，同组中包含该维度列的其他图会按该值过滤。同一个组名（如 `"g1"`）即可联动；默认 `None` 不联动。注意：`table`/`wordcloud` 是 HTML 渲染，只能作为**被联动方**，点击它们不会触发联动。 本图实现：点击任务条会按 `task` 维度联动。
- **建议**：同一看板里的明细表用同一个 `link` 组名，点图即可筛表。 联动维度由点击的图决定，各图尽量共享同一列（如 `产品`）。 组名建议用有含义的英文/拼音，不要用随机串。
- **示例**：`edv.gantt(tasks, task="任务", start="开始", end="结束", link="g1")`
- **报错**：无校验：传数字/对象会原样写入 spec，JS 端作为对象键使用，建议只传字符串。

### `max_rows` — 嵌入前端的最大行数（`int`，默认 `2000000`）

- **作用**：Python 侧只把前 `max_rows` 行（默认 20000）的数据嵌入 HTML，超过时按均匀间隔抽样，并把提示写入 `chart.warnings["warnings"]`。`table` 特殊：默认 200，且最终最多嵌入 200 行。抽样只发生在“嵌入”阶段，不影响函数内已经算好的统计（如相关系数、回归系数）。
- **建议**：前端交互图保持默认 20000 即可；超大表用 `table(max_rows=...)` 控制体积。 需要完整数据时导出 Excel/CSV，不要让 HTML 承担全量数据。 抽样后 tooltip 的明细行数会变少，但聚合图的总量不受影响。
- **示例**：`edv.gantt(tasks, task="任务", start="开始", end="结束", max_rows=500)`
- **报错**：无校验：传 `0` 或负数会得到空数据（图形空白），建议传正整数。

## 返回值

返回 `eazy_data_viz.Chart` 对象（`chart.spec` 是完整的渲染 spec，`chart.data` 是嵌入前端的数据）。

- 通用方法：`chart.save(path)` 写单文件 HTML、`chart.to_html()` 返回字符串、`chart.palette(name)` 链式换色、`chart.show()` 在浏览器打开；`chart.warnings` 记录采样等降级提示（详见 [交互与联动指南](../guides/06-interaction.md)）。

本图的关键 spec 字段（`chart.spec`）：

| 字段 | 含义 |
| --- | --- |
| `type` | 固定为 `"gantt"`。 |
| `roles` | `{"x": 任务列, "start": 开始列, "end": 结束列, "color": 分组列或 None}`。 |
| `legend` | 默认 `color is not None`；有效时显示分组图例。 |
| `labels` | `True` 时在足够宽（≥26px）的条内写任务名，文字颜色为背景色。 |
| `agg / sort / top_n / zoom` | 签名保留，但当前 builder 不读取（任务顺序固定按开始时间）。 |

## 完整示例

以下示例全部基于 `edv.sample_df()`（1500 行、11 列）或由它派生的小表；输出文件写到 `examples/output/`。

### 示例 1：最简：手工任务表

```python
import eazy_data_viz as edv
import pandas as pd

tasks = pd.DataFrame({
    "任务": ["数据清洗", "指标对齐", "图表开发", "联调", "上线"],
    "开始": pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-15", "2024-02-01", "2024-02-12"]),
    "结束": pd.to_datetime(["2024-01-12", "2024-01-20", "2024-02-05", "2024-02-14", "2024-02-20"]),
})
chart = edv.gantt(tasks, task="任务", start="开始", end="结束")
chart.save("examples/output/gantt_1.html")
```

**输出**：5 行时间条按开始日期从上到下排列，横轴为时间轴；自动标题“任务甘特图”，默认不在条内写文字（条太窄），悬停显示开始/结束/工期。

### 示例 2：典型：按负责人分组着色

```python
import eazy_data_viz as edv
import pandas as pd

tasks = pd.DataFrame({
    "任务": ["数据清洗", "指标对齐", "图表开发", "联调", "上线"],
    "开始": pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-15", "2024-02-01", "2024-02-12"]),
    "结束": pd.to_datetime(["2024-01-12", "2024-01-20", "2024-02-05", "2024-02-14", "2024-02-20"]),
    "负责人": ["张三", "李四", "张三", "王五", "王五"],
})
chart = edv.gantt(
    tasks,
    task="任务",
    start="开始",
    end="结束",
    color="负责人",
    title="项目排期",
    height=420,
)
chart.save("examples/output/gantt_2.html")
```

**输出**：三种颜色区分三位负责人，右上角出现图例；条宽足够时条内显示任务名（背景色文字），较窄的条只显示色块。

### 示例 3：进阶：从明细数据汇总任务区间

```python
import eazy_data_viz as edv

df = edv.sample_df()
tasks = (
    df.groupby(["大区", "产品"], as_index=False)
      .agg(开始=("日期", "min"), 结束=("日期", "max"))
      .rename(columns={"产品": "任务"})
)
chart = edv.gantt(tasks, task="任务", start="开始", end="结束", color="大区", height=520)
chart.save("examples/output/gantt_3.html")
```

**输出**：16 个“大区-产品”组合变成 16 行，颜色按大区区分；由于 sample 数据覆盖整个时间范围，大部分条几乎等长——这是数据特性，不是 bug。

### 示例 4：深色主题、货币/时间格式与标签开关

```python
import eazy_data_viz as edv
import pandas as pd

tasks = pd.DataFrame({
    "任务": ["需求评审", "设计", "开发", "测试", "发布"],
    "开始": pd.to_datetime(["2024-03-01", "2024-03-05", "2024-03-12", "2024-04-01", "2024-04-15"]),
    "结束": pd.to_datetime(["2024-03-06", "2024-03-14", "2024-04-02", "2024-04-16", "2024-04-20"]),
    "阶段": ["前期", "前期", "中期", "后期", "后期"],
})
a = edv.gantt(tasks, task="任务", start="开始", end="结束", color="阶段",
              theme="dark", labels=True)
a.save("examples/output/gantt_4.html")
b = edv.gantt(tasks, task="任务", start="开始", end="结束", color="阶段",
              theme="dark", labels=False)
b.save("examples/output/gantt_4.html")
```

**输出**：深色主题下两种标签设置对比：`labels=True` 在条内写任务名，`labels=False` 只留彩色条；两者 tooltip 内容一致（开始、结束、工期）。

### 示例 5：联动：点击时间条过滤明细

```python
import eazy_data_viz as edv
import pandas as pd

tasks = pd.DataFrame({
    "任务": ["数据清洗", "指标对齐", "图表开发", "联调", "上线"],
    "开始": pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-15", "2024-02-01", "2024-02-12"]),
    "结束": pd.to_datetime(["2024-01-12", "2024-01-20", "2024-02-05", "2024-02-14", "2024-02-20"]),
    "负责人": ["张三", "李四", "张三", "王五", "王五"],
})
g = edv.gantt(tasks, task="任务", start="开始", end="结束", color="负责人", link="gt1")
tbl = edv.table(tasks, columns=["任务", "负责人", "开始", "结束"], link="gt1", limit=20)
edv.dashboard(g, tbl, title="甘特图联动", cols=2).save("examples/output/gantt_5.html")
```

**输出**：点击某条时间条，右侧表格按“任务=该任务名”过滤；联动维度为 `task` 列，与 `color` 分组无关。

## 常见问题 / 注意事项

- **甘特图的横轴能从“按天”改成“按周/月”吗？** 不能。横轴固定为时间轴（毫秒刻度），格式为 `YYYY-MM-DD`；但你可以先把开始/结束日期截断到周一或月初再传入，视觉上就变成周/月粒度。
- **结束日期早于开始日期会怎样？** Python 不报错，只在 `chart.warnings` 里提示“gantt 有 N 行结束日期早于开始日期”；JS 端会把两者交换后照常绘制。建议作图前清洗，否则工期与业务口径会对不上。
- **条内的文字能换成日期或工期吗？** 不能。`labels=True` 时条内只写任务名（截断 18 字），且只有条宽 ≥26px 才显示；开始/结束/工期在 tooltip 里。
- **能设置横轴/纵轴的标题吗？** 不能。`gantt` 的签名里没有 `xtitle`/`ytitle`，轴名固定取列名：横轴=开始列名，纵轴=任务列名。（JS 其实支持 `spec.xtitle`/`spec.ytitle`，但 Python 没有暴露这两个参数。）
- **任务顺序能自定义吗？** 不能。任务固定按开始时间升序，第一项在顶部（category 轴 inverse）；`sort` 参数未生效。需要自定义顺序请给任务加序号前缀（如 `01-需求`），让名称排序接近你想要的顺序——但仍以开始时间为主键。

## 相关图表

| 图表 | 说明 |
| --- | --- |
| [`calendar`](calendar.md) | 日历热力图（按天看密度而不是任务区间） |
| [`sparkline`](sparkline.md) | 迷你走势图（多组时间趋势的紧凑对比） |
| [`table`](table.md) | 明细表（需要精确列出起止时间时用它） |
| [`timeline`](timeline.md) | 时间线（基础图表中按事件排布的时间线） |

- 回到总览：`docs/EXTRA_CHARTS.md`、`docs/AI_GUIDE.md`
