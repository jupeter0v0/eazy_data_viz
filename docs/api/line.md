# `line` — 折线 / 趋势图

> 用折线连接有序数据点，表达指标随时间的走势、季节性与拐点；多条线可对比多个系列。
> 适合：时间序列（月度销售）、连续变量的趋势对比、阈值/异常点观察。
> 不适合：无序类目的大小比较（用 bar）、两个数值变量的相关关系（用 scatter）、占比结构（用 pie 或百分比堆叠柱）。

## 函数签名

```python
eazy_data_viz.line(
    data,
    x,
    y,
    color=None,
    agg="sum",
    smooth=True,
    area=False,
    markers=None,
    sort=None,
    top_n=None,
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    xlim=None,
    ylim=None,
    fmt="compact",
    height=380,
    theme="light",
    drill=None,
    link=None,
    legend=True,
    labels=False,
    zoom="auto",
    max_rows=200000,
    step=False,
    percent=False,
    section=None,
) -> Chart
```

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源 DataFrame |
| `x` | `str` | `—` | 是 | 横轴列（通常是时间或有序类目） |
| `y` | `str` | `—` | 是 | 数值列 |
| `color` | `str` | `None` | 否 | 分组列，拆成多条线 |
| `agg` | `str` | `'sum'` | 否 | 聚合方式，默认 sum |
| `smooth` | `bool` | `True` | 否 | 是否平滑曲线，默认 True |
| `area` | `bool` | `False` | 否 | 折线下方填充 |
| `markers` | `bool` | `None` | 否 | 数据点标记（当前版本无效） |
| `sort` | `str` | `None` | 否 | 排序：x / none / desc / asc |
| `top_n` | `int` | `None` | 否 | 只保留前 N 个类目 |
| `title` | `str \| None` | `None` | 否 | 主标题 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `xtitle` | `str \| None` | `None` | 否 | 横轴标题 |
| `ytitle` | `str \| None` | `None` | 否 | 纵轴标题 |
| `xlim` | `tuple[float, float]` | `None` | 否 | 数值轴范围元组 |
| `ylim` | `tuple[float, float]` | `None` | 否 | 数值轴范围元组 |
| `fmt` | `str` | `'compact'` | 否 | 刻度/标签数值格式 |
| `height` | `int` | `380` | 否 | 画布高度（≥120） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `str` | `'light'` | 否 | light / dark |
| `drill` | `str \| list[str]` | `None` | 否 | 逐级下钻维度列表 |
| `link` | `str` | `None` | 否 | 联动组名 |
| `legend` | `bool` | `True` | 否 | 是否显示图例 |
| `labels` | `bool` | `False` | 否 | 数据点显示数值 |
| `zoom` | `bool \| str` | `'auto'` | 否 | 类目轴缩放条 auto/True/False |
| `max_rows` | `int` | `2000000` | 否 | 最大绘制行数（None 不采样） |
| `step` | `bool` | `False` | 否 | 阶梯折线 |
| `percent` | `bool` | `False` | 否 | 按 x 类目归一化为百分比 |
| `section` | `str \| None` | `None` | 否 | 看板分区标题 |

## 参数详解

### `data` — 数据源，图表取数的唯一入口（`pandas.DataFrame | dict | list | Series`，必填）

- **作用**：图表的数据来源。内部由 `frame.ensure_frame()` 统一处理：`DataFrame` 原样使用，`Series` 转成单列 DataFrame，`dict` / `list` 转成 DataFrame（list 每个元素当作一行）。 传入对象不会被原地修改；行数超过 `max_rows` 时内部会做均匀抽样，并把提示写进 `chart.warnings`。 列名允许中文、空格与特殊字符；绘图只需要列名唯一。
- **建议**：优先传现成的 `pandas.DataFrame`；不要在绘图函数里做复杂清洗，先 `df = ...` 准备好再传。 dict / list 只适合快速试验；正式代码建议保持 DataFrame，便于复用与排查。 只有一列数值时可以用 `Series`，例如 `edv.histogram(df["销售额"])`。
- **示例**：`data=df`
- **报错**：`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`；`data=42` → `TypeError: 无法识别 data 类型 'int'，请传入 pandas.DataFrame（或 dict / list）。`

### `x` — 横轴 / 类目列名（`str`，必填）

- **作用**：指定横轴使用的列名。列可以是文本分类、时间或数值；图表类型决定它的角色（类目轴或数值轴）。 它同时决定默认排序：x 是日期、数值或有序分类时，柱状图默认按 x 升序（`sort='x'`）；普通文本列则柱状图默认按数值降序（`sort='desc'`）、折线图默认保持原始顺序（`sort='none'`）。 使用 `drill` 下钻时，第一层维度必须就是 x；若 `drill[0]` 与 x 不同，内部会自动把 x 插到最前面。
- **建议**：传 `df.columns` 里的真实列名，不能传列序号或表达式。 时间列先 `pd.to_datetime()`；像“月份”这种有固定顺序的分类，用 `pd.Categorical(df["月份"], categories=[...], ordered=True)` 可保证 1月→12月 的正确顺序。 分类过多（>15 类）时柱状图会自动出现缩放条，或改用 `top_n` 只保留前 N 项。
- **示例**：`x="大区"`
- **报错**：不传 → `TypeError: bar() missing 1 required positional argument: 'x'`；显式 `x=None` → `ValueError: 缺少 x：请用 x="列名" 指定横轴（分类/时间）列。`；列名写错 → `KeyError: "列 '不存在' 不存在。当前可用的列有：日期, 月份, 大区, 省份, 城市, 产品, 渠道, 销售额, 订单数, 利润, 客户数"`

### `y` — 纵轴数值列（`str`，必填）

- **作用**：折线的数值列，必填；按 x（以及 color）用 agg 聚合后连线。 同一条 line 只能有一个 y；要对比多个指标时用 color 或画多条 line。
- **建议**：时间序列建议先用 `df.groupby("月份", observed=True)["销售额"].sum().reset_index()` 聚合成“每个时间点一行”，折线更干净。 金额类指标注意 `agg="sum"` 与 `agg="mean"` 的业务口径差异。
- **示例**：`y="销售额"`
- **报错**：不传 → `TypeError: line() missing 1 required positional argument: 'y'`；传文本列 → `TypeError: 列 '产品' 需要是数值类型，但当前是文本类型（例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `color` — 分组/系列列名（`str`，默认 `None`）

- **作用**：按该列的取值把数据拆成多个系列：柱状图变成分组柱或（配合 `stack=True`）堆叠柱，折线图变成多条线，散点图按类别着色。 同时会参与聚合：每个 (x, color) 组合先按 `agg` 聚合再绘制。 传入的列会变成图例；`legend=False` 可隐藏图例（但系列依然按 color 拆分）。
- **建议**：分类基数不宜过大：超过 10 个类别时颜色会难以区分，建议先合并低频类别。 `color` 与 `x` 不能是同一列（同一列分组没有意义）。 需要固定配色时用 `chart.palette("tableau")` 或全局 `edv.set_palette(...)`。
- **示例**：`color="渠道"`
- **报错**：列名写错 → `KeyError: "列 'XX' 不存在。当前可用的列有：..."`

### `agg` — 聚合方式（`str`，默认 `'sum'`）

- **作用**：同一个类目下有多行记录时的聚合函数，全部可选值：`"sum"`、`"mean"`、`"count"`、`"max"`、`"min"`、`"median"`。 聚合在 `x`（以及 `color`）分组上进行；`top_n` 截断是在聚合之后做的。 部分图表会强制固定 agg：`box` 固定 `median`、`histogram` 固定 `count`，此时传入值不生效。
- **建议**：销售额/订单数等可加指标用 `sum`；单价、评分等不可加指标用 `mean` 或 `median`。 想看“每个类目出现多少条记录”时用 `count`，同时可省略 y。
- **示例**：`agg="mean"`
- **报错**：`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median`

### `smooth` — 是否平滑曲线，默认 True（`bool`，默认 `True`）

- **作用**：默认 `True` 画平滑曲线；显式 `False` 才画折线段（前端判断 `smooth !== false`）。 平滑只是视觉插值，不改变数据点；相邻点之间会被“圆滑”过去，可能在视觉上夸大波动。
- **建议**：月/季度趋势可保持平滑；日粒度或需要精确读数时用 `smooth=False`。
- **示例**：`smooth=False`

### `area` — 折线下方是否填充（line）（`bool`，默认 `False`）

- **作用**：`True` 时折线下方填充半透明色块，形成面积图。 `edv.area()` 是 `line(..., area=True)` 的快捷封装；它的包装会把该值强制为 True，所以传 `area=False` 不会生效。
- **建议**：单条/少条趋势适合填充；多条线重叠时填充会互相遮挡，建议只填充合计线或改用堆叠面积。 面积图默认不堆叠，各系列从 0 起画，会遮住下方曲线。
- **示例**：`area=True`

### `markers` — 数据点标记（当前版本无视觉效果）（`bool`，默认 `None`）

- **作用**：源码把 `markers` 写入 spec，前端只创建空的 markPoint，当前版本视觉上看不到点标记。 需要显示每个点的数值时用 `labels=True` 临时替代。
- **建议**：该参数保留在签名中，等待后续版本修复；不要依赖它做展示。
- **示例**：`markers=True`

### `sort` — 排序方式，默认 none 或 x（`str`，默认 `None`）

- **作用**：默认 `None` 时：x 是日期/数值/有序分类 → `"x"`；普通文本 → `"none"`（保持数据顺序）。 折线图不应随意按 y 排序，否则连线会来回穿插，失去时间意义。 源码不校验非法值，`"rank"` 会被静默忽略。
- **建议**：时间序列一律确保按时间升序；数据本身乱序时用 `sort="x"`。
- **示例**：`sort="x"`

### `top_n` — 只保留前 N 个类目，其余合并为“其他”（`int`，默认 `None`）

- **作用**：按当前排序取前 N 个类目，剩余类目合并成一个名为“其他”的项，避免图表过密。 必须传 ≥1 的正整数（bool 会被拒绝）；合并发生在聚合之后。 前端对“其他”这一项不触发联动/下钻（点击它会提示或无效果），因此需要逐项交互时请直接改数据源。
- **建议**：类目 10 个以上时考虑 `top_n=8` 或 `top_n=10`；保留“其他”能让总量仍然正确。 需要看完整类目就不要用 top_n，改用 `zoom=True` 或横向柱。
- **示例**：`top_n=8`
- **报错**：`top_n=0` → `ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`；`top_n=True` → 同上，收到 True

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在画布左上角的主标题；不传时由函数自动生成（例如 `bar` 为「销售额 按 大区」）。 自动标题会附带分组信息：有 `color` 时追加「 · 按 渠道」。
- **建议**：正式报表建议显式写标题，自动标题只适合快速探索。 标题内不要塞入长句；补充说明放 `subtitle`。
- **示例**：`title="各大区销售额"`

### `subtitle` — 副标题（灰字说明）（`str | None`，默认 `None`）

- **作用**：显示在主标题下方的小号灰字，常用于写口径、数据范围或时间区间。 不传时不显示；与 `title` 各自独立，可以只传 subtitle。
- **建议**：写清统计口径，例如「2024 年 1~12 月，含税」。 保持一行，过长会被画布截断。
- **示例**：`subtitle="2024 全年，按订单日期统计"`

### `xtitle` — 横轴标题（`str | None`，默认 `None`）

- **作用**：覆盖横轴的轴名；不传时后端按角色回退（bar 用 x 列名，histogram 用数值列名，heatmap 用 x 列名）。 `horizontal=True` 时横轴是数值轴，`xtitle` 相应地描述数值。
- **建议**：需要写单位时放在这里，例如「销售额（万元）」。 轴名能自解释时可以省略，保持画面干净。
- **示例**：`xtitle="大区"`

### `ytitle` — 纵轴标题（`str | None`，默认 `None`）

- **作用**：覆盖纵轴的轴名；不传时回退（bar/line 用 y 列名，histogram 默认「频数」，heatmap 用 y 列名）。 `box` 只有 `ytitle`，没有 `xtitle`，因为纵轴才是数值轴。
- **建议**：多系列/堆叠时写清度量与单位，例如「销售额（元）」。 横向柱状图里纵轴是类目轴，`ytitle` 描述类目。
- **示例**：`ytitle="销售额（元）"`

### `xlim` — 数值轴范围（横向维度）（`tuple[float, float]`，默认 `None`）

- **作用**：折线图 x 通常是类目/时间轴，xlim 一般用于 x 为数值列的情形；两元组，min>max 自动交换。
- **建议**：x 为数值（例如价格、年龄）时才需要；时间轴请用类目缩放（zoom）。
- **示例**：`xlim=(0, 12)`

### `ylim` — 纵轴数值范围（`tuple[float, float]`，默认 `None`）

- **作用**：控制 y 轴上下限，两元组；传入后折线可能被截断在画面外。
- **建议**：需要固定对比基线时用 `ylim=(0, 上限)`；观察小幅波动时不要从 0 起。
- **示例**：`ylim=(0, 4000000)`

### `fmt` — 数值格式（`str`，默认 `'compact'`）

- **作用**：可选：`"compact"`（默认，1.2万 / 1.3亿）、`"thousands"`（12,345）、`"raw"`（原样）、`"percent"`（12.3%）、`"currency"`（¥12,345.67）。 作用于坐标轴刻度、`labels=True` 的标签以及 KPI 读数；不会改变原始数据。 `fmt="percent"` 只是格式化，不做归一化；要做百分比堆叠请用 `percent=True`。
- **建议**：金额用 `currency` 或 `compact`；占比用 `percent`；需要精确数字用 `thousands`。 `gauge` 的 fmt 不做校验（见 gauge 文档）；其余图的 fmt 都会严格校验。
- **示例**：`fmt="currency"`
- **报错**：`fmt="money"` → `ValueError: fmt='money' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素，默认 380）（`int`，默认 `380`）

- **作用**：只控制图表画布高度（CSS px），不控制宽度；最小 120，小于 120 会报错。 不同图默认高度不同：bar/line/scatter/box/funnel 380、pie/histogram 360、heatmap 400、treemap 420、combo 400、gauge 260、kpi 150。
- **建议**：信息密集的图（热力图、堆叠柱）建议 420~520；KPI 卡片保持 150 左右。 嵌入窄容器时保留 300 以上，否则标题和坐标轴会挤压。
- **示例**：`height=480`
- **报错**：`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题（light / dark）（`str`，默认 `'light'`）

- **作用**：`"light"`（默认）浅色背景；`"dark"` 深色背景，坐标轴、文字、图例颜色自动反转。 主题只影响配色与背景，不改变图表结构；与其他图混排时建议统一主题。
- **建议**：大屏/深色看板用 `dark`；报告导出用 `light`。 自定义色板（`chart.palette(...)`）在两种主题下都会生效。
- **示例**：`theme="dark"`
- **报错**：`theme="blue"` → `ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `drill` — 下钻维度列表（逐级点击）（`str | list[str]`，默认 `None`）

- **作用**：传列名或列名列表，图表点击某类目后会按下一层维度重新聚合；页面出现面包屑「全部 › 华东 › 江苏」和返回按钮。 字符串会自动转成单元素列表；列表不能为空。第一层必须是当前的 x（内部会自动把 x 插到最前）。 下钻后的聚合沿用 `agg`，数据仍然是同一份 DataFrame，只改变维度。
- **建议**：层级列应有包含关系，例如 `["大区", "省份", "城市"]`；无序组合不要用 drill。 下钻与 `link` 可同时使用，但联动图表也会跟随下钻维度重算。
- **示例**：`drill=["大区", "省份", "城市"]`
- **报错**：`drill=[]` → `ValueError: drill 不能是空列表；不需要下钻请传 drill=None。`；列名写错 → `KeyError: "下钻维度列 'XX' 不存在。当前可用的列有：..."`

### `link` — 联动组名（同组图表互相筛选）（`str`，默认 `None`）

- **作用**：把多个图表放进同一个联动组：点击某图的类目后，同组其它图表按该维度过滤并重算；再次点击同一类目取消筛选。 联动依据是点击项的名称（x 类目）；点“其他”不触发联动。 需要在 Dashboard/HTML 页面里才真正生效，单独导出单个图表时只记录参数。
- **建议**：同一页面里所有要联动的图必须传完全相同的字符串，例如都写 `link="销售"`。 散点/热力图的点击联动依赖数据点名称，当前版本可能不生效（已在自检记录中标注）。
- **示例**：`link="销售"`

### `legend` — 是否显示图例（`bool`，默认 `True`）

- **作用**：控制图例显隐；图例项来自 `color` 分组，没有 `color` 时通常不显示图例。 图例本身可点击以隐藏/恢复系列（前端行为，与 `legend=False` 的“完全不显示”不同）。
- **建议**：多系列必须保留图例；单系列可以关掉让画面更干净。 手机窄屏下多系列图例占空间，可考虑关闭并改用标签。
- **示例**：`legend=False`

### `labels` — 是否在图形上直接标数值（`bool`，默认 `False`）

- **作用**：`True` 时在柱子顶部/右侧、扇区外或热力格内直接显示数值，省去对照坐标轴。 标签文本会经过 `fmt` 格式化；点数很多时标签会重叠，此时建议关闭。 各图支持情况不同：`histogram` 的 labels 当前被前端忽略；`heatmap` 仅在格子数 ≤60 时显示。
- **建议**：演示、汇报截图建议打开；密集数据保持关闭，用 tooltip 查看。 与 `percent=True` 组合时标签显示百分比。
- **示例**：`labels=True`

### `zoom` — 类目轴缩放条（auto/True/False）（`bool | str`，默认 `'auto'`）

- **作用**：`"auto"`（默认）在类目数超过 15 时自动出现缩放条；`True` 强制显示，`False` 关闭。 缩放条可在浏览器里拖动查看密集类目，与 `top_n` 的“直接截断”是两种策略。
- **建议**：类目很多又需要全量查看时用 `zoom=True`；类目少时保持默认即可。 导出静态截图时缩放条只显示初始窗口，读图者看不到其余类目，此时更适合 `top_n`。
- **示例**：`zoom=True`

### `max_rows` — 最大参与绘制的行数（`int`，默认 `2000000`）

- **作用**：默认 2000000 行（200 万）；超过该行数时内部做均匀抽样，而不是简单截断，尽量保留整体分布；提示写入 `chart.warnings`。 传 `None` 表示完全关闭采样，全部行进入图表（数据很大时 HTML 体积和渲染压力都会上升）。 源码没有校验取值范围：传 0 会得到 0 行（图表为空），传负数行为也不受保护（已在自检记录中标注）。 该参数只控制进入图表的行数，不改变原始 DataFrame。
- **建议**：一般保持默认 2000000；前端渲染压力大时可降到 5000~10000。 确定要完整数据（例如逐条散点）时传 `max_rows=None`，并注意页面体积。 需要精确汇总时不要在超大数据集上依赖 max_rows 抽样，先自行 groupby 聚合再画。
- **示例**：`max_rows=5000`

### `step` — 阶梯折线（line）（`bool`，默认 `False`）

- **作用**：`True` 时折线变成阶梯线（ECharts `step: 'middle'`），适合表示“状态在区间内保持不变”的指标，例如库存、阶梯价。 与 `smooth=True` 同时使用时前端以 step 为准，平滑被覆盖。
- **建议**：状态型/累计台阶型数据用 `step=True`；连续趋势不要用阶梯线。 阶梯图和 `area=True` 可组合，但视觉较密，建议调高 `height`。
- **示例**：`step=True`

### `percent` — 份额折线（百分比归一化）（`bool`，默认 `False`）

- **作用**：`True` 时每个 x 时间点内各系列除以该点合计，显示份额走势；y 轴固定 0~100%。 多系列时才有意义；单系列恒为 100%。
- **建议**：看“渠道份额随时间变化”用 `percent=True, color="渠道"`。
- **示例**：`percent=True`

### `section` — 看板分区标题（`str | None`，默认 `None`）

- **作用**：在 Dashboard 中把折线图归入某个分区；单图导出时只写入 spec。
- **建议**：与同看板的 bar/kpi 使用一致的分区名。
- **示例**：`section="趋势分析"`

## 返回值

所有图表函数都返回 `eazy_data_viz.Chart` 对象：`chart.spec` 是 JSON 可序列化的完整渲染配置，`chart.data` 是实际参与绘图的数据，`chart.warnings` 记录采样/丢列等降级提示；`save()` / `to_html()` / `palette()` / `show()` 的通用用法见 [交互与联动指南](../guides/06-interaction.md)。

本图的 `spec` 额外包含：

- `smooth` / `area` / `markers` / `step` / `percent` / `section`：折线样式与看板分区。
- `roles`：`{"x": 横轴列, "y": 数值列, "color": 分组列或 None}`。

## 完整示例

以下示例都基于 `edv.sample_df()`，可直接复制运行（在仓库根目录执行）；所有输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法：销售额趋势

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.line(df, x="日期", y="销售额")
chart.save("examples/output/line_1.html")
```

**输出**：
- x=日期 是 datetime，默认 `sort="x"`，折线按日期升序连接。
- 自动标题「销售额 趋势」，默认平滑曲线（`smooth=True`）。
- 1500 条日级记录会按日期聚合（agg=sum），同一天多行先求和。

**验证**：`chart.spec["smooth"] is True`；`chart.spec["sort"] == "x"`。

### 示例 2：按月聚合：12 个月的销售额

```python
import eazy_data_viz as edv
df = edv.sample_df()

month = df.groupby("月份", observed=True)["销售额"].sum().reset_index()
chart = edv.line(
    month, x="月份", y="销售额", sort="x",
    title="月度销售额趋势", subtitle="按订单月份汇总",
    xtitle="月份", ytitle="销售额（元）",
)
chart.save("examples/output/line_2.html")
```

**输出**：
- 先在 pandas 里聚合成 12 行，折线点更干净，也避免同一月份重复采样。
- 月份是有序分类，`sort="x"` 保证 1月→12月 而不是字符串顺序。
- 标题、轴名由参数覆盖，自动标题不再生效。

**验证**：`len(chart.data) == 12`；图上应有 12 个拐点，x 轴从 1月 到 12月。

### 示例 3：坐标范围 + 标题：固定 y 轴上限

```python
import eazy_data_viz as edv
df = edv.sample_df()

month = df.groupby("月份", observed=True)["销售额"].sum().reset_index()
chart = edv.line(
    month, x="月份", y="销售额", sort="x",
    ylim=(0, 4000000), xlim=(0, 12),
    title="月度销售额（固定坐标范围）",
    subtitle="y 轴 0~400万，便于多图对比",
    xtitle="月份", ytitle="销售额（元）", fmt="thousands",
)
chart.save("examples/output/line_3.html")
```

**输出**：
- `ylim=(0, 4000000)` 固定纵轴范围，多张图并排时高度可直接比较。
- `xlim=(0, 12)` 只在 x 为数值时生效；这里的月份是分类，设置了也仅写入 spec。
- `fmt="thousands"` 让刻度显示 2,500,000 这类千分位。

**验证**：`chart.spec["ylim"] == [0.0, 4000000.0]`；y 轴刻度从 0 开始。

### 示例 4：下钻 + 联动：日期 → 大区 → 产品

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.line(
    df, x="日期", y="销售额",
    drill=["日期", "大区", "产品"], link="趋势",
    title="销售额趋势下钻", subtitle="点击数据点进入下一层维度",
    xtitle="日期", ytitle="销售额（元）",
)
chart.save("examples/output/line_4.html")
```

**输出**：
- 首层按日期画趋势；点击折线上的点后按大区重新汇总，再点进入产品层。
- `link="趋势"` 让同组图表跟随筛选；面包屑显示当前层级。
- 下钻维度顺序必须与业务层级一致，否则点击后维度没有意义。

**验证**：`chart.spec["drill"] == ["日期", "大区", "产品"]`；`chart.spec["link"] == "趋势"`。

## 常见问题 / 注意事项

- **为什么没有 stack 参数？** 本库的 `line` 没有堆叠参数，签名里也没有 `stack`；需要堆叠面积时请用 `area` 并自行把数据按 x 累加。 百分比堆叠折线用 `percent=True`，它做的是份额归一化，不是堆叠。
- **markers 为什么看不到点？** 当前版本前端只根据 markers 创建了一个空的 markPoint，没有实际数据点渲染，属于待修复参数。 需要逐点读数时用 `labels=True`，或改用 `scatter`。
- **多条线颜色太像怎么办？** 先 `chart.palette("tableau")` 或全局 `edv.set_palette("antd")` 换色板；再不行就减少系列数（top_n 或合并低频类）。 深色主题下 morandi 色板对比度较低，建议用 echarts/carbon。

## 相关图表

- `bar`：类目之间比大小，而不是连续趋势。
- `area`：折线 + 填充，强调累计量级。
- `combo`：柱 + 线双轴，同时表达体量与比率。
- `scatter`：两个数值变量的相关关系，而不是随时间变化。
