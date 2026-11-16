# `bar` — 分组 / 堆叠柱状图

> 用柱子的长度比较不同类目的数值大小；多个系列并排就是分组柱，堆叠起来就是堆叠柱，横向排布则适合长类目名。
> 适合：类目对比（各大区销售额）、结构占比（渠道构成）、总量 + 结构（产品 × 渠道堆叠）。
> 不适合：连续时间趋势（用 line）、两个数值变量的相关性（用 scatter）、超过 ~30 个类目的精细比较（先 top_n 或横向）。

## 函数签名

```python
eazy_data_viz.bar(
    data,
    x,
    y=None,
    color=None,
    agg="sum",
    stack=False,
    horizontal=False,
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
    percent=False,
    section=None,
) -> Chart
```

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源 DataFrame |
| `x` | `str` | `—` | 是 | 类目轴列名 |
| `y` | `str` | `None` | 否 | 数值列；省略表示统计记录数 |
| `color` | `str` | `None` | 否 | 分组列，拆成多系列 |
| `agg` | `str` | `'sum'` | 否 | 聚合方式，默认 sum |
| `stack` | `bool` | `False` | 否 | 多系列堆叠到同一根柱 |
| `horizontal` | `bool` | `False` | 否 | 横向柱状图 |
| `sort` | `str` | `None` | 否 | 排序：desc / asc / x / none |
| `top_n` | `int` | `None` | 否 | 只保留前 N 项，其余合并“其他” |
| `title` | `str \| None` | `None` | 否 | 主标题 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `xtitle` | `str \| None` | `None` | 否 | 横轴标题 |
| `ytitle` | `str \| None` | `None` | 否 | 纵轴标题 |
| `xlim` | `tuple[float, float]` | `None` | 否 | 数值轴范围元组 |
| `ylim` | `tuple[float, float]` | `None` | 否 | 数值轴范围元组 |
| `fmt` | `str` | `'compact'` | 否 | 刻度/标签数值格式 |
| `height` | `int` | `380` | 否 | 画布高度（≥120） |
| `theme` | `str` | `'light'` | 否 | light / dark |
| `drill` | `str \| list[str]` | `None` | 否 | 逐级下钻维度列表 |
| `link` | `str` | `None` | 否 | 联动组名 |
| `legend` | `bool` | `True` | 否 | 是否显示图例 |
| `labels` | `bool` | `False` | 否 | 柱顶显示数值 |
| `zoom` | `bool \| str` | `'auto'` | 否 | 类目轴缩放条 auto/True/False |
| `max_rows` | `int` | `200000` | 否 | 最大绘制行数（None 不采样） |
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

### `y` — 数值列；None 表示统计记录数（`str`，默认 `None`）

- **作用**：柱高对应的数值列；省略时 `bar` 会按 x 统计每个类目的行数，内部把 `agg` 自动改为 `count`，自动标题里的度量名写成「记录数」。 传了 y 时会先按 `x`（以及 `color`）用 `agg` 聚合再画；数值列必须是数值 dtype。 `y` 与 `x` 不能是同一列；同一列既分类又度量没有意义。
- **建议**：比较销售额/订单数等可加指标用 `sum`，比较单价用 `mean`。 想看每类记录条数就省略 y，例如 `edv.bar(df, x="大区")`。
- **示例**：`y="销售额"`
- **报错**：数值列传文本列 → `TypeError: 列 '产品' 需要是数值类型，但当前是文本类型（例如 ['智能终端', '云服务', '行业软件', '运维服务', '智能终端']）。请先用 pd.to_numeric() 清洗，或换一列。`

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

### `stack` — 是否堆叠（bar 专用）（`bool`，默认 `False`）

- **作用**：`True` 时把 `color` 的各个系列堆叠到同一根柱子上，柱高代表合计值；默认 `False` 为并排分组柱。 只影响绘制，不改变聚合结果；与 `percent=True` 同时使用时先堆叠再归一化为百分比。 未传 `color` 时堆叠没有可堆叠的系列，等同于普通柱状图。
- **建议**：看“总量 + 结构”用堆叠；只看各类别数值大小用并排（默认）。 堆叠后中间系列难以精确读数，需要精确值时打开 `labels=True`。
- **示例**：`stack=True`

### `horizontal` — 是否横向柱状图（`bool`，默认 `False`）

- **作用**：`True` 时交换坐标轴：类目（x）画在纵轴，数值（y）画在横轴，长标签更易读。 坐标轴参数随之交换：`xlim`/`xtitle` 作用于数值轴，`ylim`/`ytitle` 作用于类目轴。
- **建议**：类目名称较长（例如省份全称）时优先用横向柱；类目很多时横向也更易排布。 横向模式下想按数值从大到小从上往下排，用 `sort="desc"`；需要从下往上则 `sort="asc"`。
- **示例**：`horizontal=True`

### `sort` — 排序方式，默认按类目自适应（`str`，默认 `None`）

- **作用**：`"desc"` 按柱高降序、`"asc"` 升序、`"x"` 按 x 列原值排序、`"none"` 保持数据出现顺序。 默认 `None` 时：x 是日期/数值/有序分类 → `"x"`；普通文本类目 → `"desc"`（销售报表通常希望从大到小）。 排序在聚合之后、`top_n` 截断之前进行；源码不校验非法值，传 `"rank"` 会静默变成不排序。
- **建议**：省份/城市排名用默认 `desc`；月份、年份等时间类目显式写 `sort="x"`。 需要业务自定义顺序（例如 华东→华北→华南→西部）时用 `sort="none"` 并调整 DataFrame 行顺序。
- **示例**：`sort="asc"`

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

### `xlim` — 横向柱的数值轴范围；纵向柱用于类目轴（`tuple[float, float]`，默认 `None`）

- **作用**：`horizontal=False`（默认纵向柱）时数值轴是 y，xlim 约束的是**类目轴**，通常不需要设置。 `horizontal=True` 时数值轴变成横轴，`xlim=(0, 4000000)` 才能控制柱子长度范围。 两元组，min>max 会自动交换；非数字会抛 ValueError。
- **建议**：横向柱需要从 0 起画时用 `xlim=(0, 上限)`；纵向柱的数值范围请用 `ylim`。
- **示例**：`xlim=(0, 4000000)`
- **报错**：`xlim=5` → `ValueError: xlim 需要是 (最小值, 最大值) 两元组，例如 xlim=(0, 100)`

### `ylim` — 纵向柱的数值轴范围（`tuple[float, float]`，默认 `None`）

- **作用**：默认纵向柱时 `ylim` 控制柱高的数值范围；`horizontal=True` 时纵轴变成类目轴，此时 ylim 约束类目范围，一般不设。 两元组、数字可转换；min>max 自动交换。
- **建议**：纵向柱建议 `ylim=(0, 上限)` 保证柱子从 0 起画；需要截断对比时才用非 0 下限。
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

### `max_rows` — 最大参与绘制的行数（`int`，默认 `200000`）

- **作用**：默认 200000 行；超过该行数时内部做均匀抽样，而不是简单截断，尽量保留整体分布；提示写入 `chart.warnings`。 传 `None` 表示完全关闭采样，全部行进入图表（数据很大时 HTML 体积和渲染压力都会上升）。 源码没有校验取值范围：传 0 会得到 0 行（图表为空），传负数行为也不受保护（已在自检记录中标注）。 该参数只控制进入图表的行数，不改变原始 DataFrame。
- **建议**：一般保持默认 200000；前端渲染压力大时可降到 5000~10000。 确定要完整数据（例如逐条散点）时传 `max_rows=None`，并注意页面体积。 需要精确汇总时不要在超大数据集上依赖 max_rows 抽样，先自行 groupby 聚合再画。
- **示例**：`max_rows=5000`

### `percent` — 百分比堆叠/百分比柱（`bool`，默认 `False`）

- **作用**：`True` 时把每个 x 类目内的柱高除以该类目合计，换算成 0~100% 的份额；数值轴固定为 0~100 且按百分比格式化。 与 `stack=True` 同时用是百分比堆叠柱；不堆叠时每根柱都归一化到 100%，视觉上只剩结构。 类目合计为 0 时按 0 处理，不会除零报错。
- **建议**：比较“各渠道占比”用 `percent=True, stack=True`；比较绝对金额用默认 False。
- **示例**：`percent=True`

### `section` — 看板分区标题（`str | None`，默认 `None`）

- **作用**：在 Dashboard 中把图表归入某个分区，分区标题渲染在图表上方；单图导出时只写入 spec。
- **建议**：同一看板内分区名保持一致，例如「销售概况」「区域明细」。
- **示例**：`section="销售概况"`

## 返回值

所有图表函数都返回 `eazy_data_viz.Chart` 对象：`chart.spec` 是 JSON 可序列化的完整渲染配置，`chart.data` 是实际参与绘图的数据，`chart.warnings` 记录采样/丢列等降级提示；`save()` / `to_html()` / `palette()` / `show()` 的通用用法见 [交互与联动指南](../guides/06-interaction.md)。

本图的 `spec` 额外包含：

- `stack` / `horizontal` / `percent` / `section`：柱状图的绘制方式与看板分区。
- `roles`：`{"x": 类目列, "y": 数值列, "color": 分组列或 None}`。
- `sort` / `topN`：最终排序策略与截断数量（未传 top_n 时为 None）。

## 完整示例

以下示例都基于 `edv.sample_df()`，可直接复制运行（在仓库根目录执行）；所有输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法：各大区销售额

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.bar(df, x="大区", y="销售额")
chart.save("examples/output/bar_1.html")
```

**输出**：
- 自动标题「销售额 按 大区」，纵轴按 `fmt="compact"` 显示 1.2万 / 1.3亿 这类缩写。
- 默认 `sort="desc"`：柱子从高到低排列，图例不显示（没有 color），tooltip 显示精确值。
- `chart.spec["type"] == "bar"`，`chart.spec["sort"] == "desc"`。

**验证**：打开 HTML 能看到 4 根柱子；`print(chart.spec["roles"])` 应得到 `{'x': '大区', 'y': '销售额'}` 这类角色映射。

### 示例 2：按类目聚合 + 排序 + top_n：省份销售额前 8

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.bar(
    df, x="省份", y="销售额",
    agg="sum", sort="desc", top_n=8,
    fmt="currency", labels=True,
    title="销售额 TOP 8 省份", subtitle="2024 全年，含税",
    xtitle="省份", ytitle="销售额（元）",
)
chart.save("examples/output/bar_2.html")
```

**输出**：
- 先按省份聚合销售额，再降序取前 8，其余省份合并为「其他」一根柱。
- `labels=True` 在每根柱顶写格式化后的金额（¥ 前缀 + 千分位），`fmt="currency"` 同时作用于 y 轴刻度。
- 8 个类目不会触发缩放条（阈值是 >15 类）。

**验证**：`len(chart.spec["data"]["rows"])` 检查最终行数；图上应恰好 8 根柱（含「其他」）。

### 示例 3：分组堆叠：产品 × 渠道

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.bar(
    df, x="产品", y="销售额", color="渠道",
    stack=True, sort="x",
    title="各产品渠道构成", subtitle="堆叠显示合计",
    xtitle="产品", ytitle="销售额（元）",
)
chart.save("examples/output/bar_3.html")
```

**输出**：
- 每个产品一根柱子，柱内按渠道（直销/渠道代理/线上商城）分三段堆叠，柱高=该产品合计销售额。
- 自动标题会追加分组信息：「销售额 按 产品 · 按 渠道」。
- 底部出现图例，点击图例项可隐藏/恢复对应渠道（前端行为）。

**验证**：`chart.spec["stack"] is True`；堆叠后每根柱各段之和应等于 `df.groupby("产品")["销售额"].sum()`。

### 示例 4：下钻 + 联动：大区 → 省份 → 城市

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.bar(
    df, x="大区", y="销售额",
    drill=["大区", "省份", "城市"],
    link="销售", sort="desc",
    title="销售额下钻", subtitle="点击柱子逐级查看，联动组“销售”",
    xtitle="大区", ytitle="销售额（元）",
)
chart.save("examples/output/bar_4.html")
```

**输出**：
- 首层显示 4 个大区；点击某根柱后按省份重算，页面顶部出现面包屑「全部 › 华东」与返回按钮。
- `link="销售"` 记录到 spec：同一看板里其他 `link="销售"` 的图会跟随筛选。
- 下钻层级列必须是 df 的列名；点击“其他”不会下钻。

**验证**：`chart.spec["drill"] == ["大区", "省份", "城市"]`；点击柱子后图表标题维度应变为省份。

## 常见问题 / 注意事项

- **bar 的 y 能不能不传？** 可以，`edv.bar(df, x="大区")` 会统计每个大区的记录数，自动标题写成「记录数 按 大区」。 此时 `chart.spec["agg"] == "count"`；如果同一次调用还传了 y=None 又想用别的聚合，count 是唯一合理选择。
- **堆叠柱里某一段特别小，读不出来怎么办？** 打开 `labels=True` 直接标数值，或改成 `horizontal=True` 给每段更多长度。 缩放条（`zoom=True`）只解决类目过密，不解决单段过小；必要时把低频类别先合并。
- **横向柱的排序方向为什么反了？** 横向柱的类目轴是纵轴，`sort="desc"` 会让最大值排在最下面（ECharts 类目轴从下往上）。 需要最大值在最上面时用 `sort="asc"`，或先用 `sort="none"` 控制行顺序。

## 相关图表

- `line`：看随时间变化的趋势而不是类目之间的高低。
- `area`：既看趋势又强调累计量级，用填充面积。
- `combo`：同一张图里同时表达“总量柱 + 率折线”。
- `treemap`：类目很多、还要看层级构成时，用嵌套矩形替代密集柱状图。
