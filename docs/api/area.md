# `area` — 面积图

> 折线下方填充颜色的图，本质是 `line(..., area=True)` 的快捷封装；适合强调累计量级或整体趋势。
> 适合：总量随时间的累积变化、单系列/少系列趋势、占比随时间的粗略对比。
> 不适合：多系列互相遮挡时精确读数、无序类目比较；需要严格堆叠时本库未提供 stack 参数。

## 函数签名

```python
eazy_data_viz.area(
    data,
    x,
    y,
    color=None,
) -> Chart
```

`area` 是 `line(..., area=True)` 的薄封装：正式签名只有 `data / x / y / color` 四个参数，其余参数全部经 `**kwargs` 透传给 `line`（下方“参数总览”把可透传的参数逐行列全）。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源 DataFrame |
| `x` | `str` | `—` | 是 | 横轴列 |
| `y` | `str` | `—` | 是 | 数值列 |
| `color` | `str` | `None` | 否 | 分组列，拆成多条面积 |
| `**kwargs` | `dict` | — | 否 | 透传给 line 的其余参数 |
| `agg` | `str` | `'sum'` | 否 | 聚合方式，默认 sum |
| `smooth` | `bool` | `True` | 否 | 是否平滑，默认 True |
| `markers` | `bool` | `None` | 否 | 数据点标记（当前版本无效） |
| `sort` | `str` | `None` | 否 | 排序：x / none / desc / asc |
| `top_n` | `int` | `None` | 否 | 只保留前 N 个类目 |
| `title` | `str \| None` | `None` | 否 | 主标题 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `xtitle` | `str \| None` | `None` | 否 | 横轴标题 |
| `ytitle` | `str \| None` | `None` | 否 | 纵轴标题 |
| `xlim` | `tuple[float, float]` | `None` | 否 | 数值轴范围元组 |
| `ylim` | `tuple[float, float]` | `None` | 否 | 数值轴范围元组 |
| `fmt` | `str` | `'compact'` | 否 | 数值格式 |
| `height` | `int` | `380` | 否 | 画布高度（≥120） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `str` | `'light'` | 否 | light / dark |
| `drill` | `str \| list[str]` | `None` | 否 | 逐级下钻维度列表 |
| `link` | `str` | `None` | 否 | 联动组名 |
| `legend` | `bool` | `True` | 否 | 是否显示图例 |
| `labels` | `bool` | `False` | 否 | 数据点显示数值 |
| `zoom` | `bool \| str` | `'auto'` | 否 | 类目轴缩放条 |
| `max_rows` | `int` | `2000000` | 否 | 最大绘制行数 |
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

### `y` — 数值（度量）列名（`str`，必填）

- **作用**：纵轴的数值列。`bar` 的 `y=None` 合法：表示不指定度量，直接按 x 统计记录数（此时 `agg` 变为 `count`）。 内部会用 `pd.api.types.is_numeric_dtype` 校验数值角色列；文本列不会自动转数字，以免悄悄丢失数据。 聚合方式由 `agg` 决定（默认 `sum`）；同一个 x 下有多行记录时会先按 x（以及 `color`）聚合再画。
- **建议**：必须是数值 dtype；文本数字先 `pd.to_numeric(df["销售额"], errors="coerce")` 清洗并处理 NaN。 要对比多个度量时，用 `color` 指定分组列，不要在一个图里堆叠传多个 y。 需要“每类多少条记录”时直接省略 y（`bar` 支持，`line` 不支持）。
- **示例**：`y="销售额"`
- **报错**：数值角色传文本列 → `TypeError: 列 '产品' 需要是数值类型，但当前是文本类型（例如 ['智能终端', '云服务', '行业软件', '运维服务', '智能终端']）。请先用 pd.to_numeric() 清洗，或换一列。`

### `color` — 分组/系列列名（`str`，默认 `None`）

- **作用**：按该列的取值把数据拆成多个系列：柱状图变成分组柱或（配合 `stack=True`）堆叠柱，折线图变成多条线，散点图按类别着色。 同时会参与聚合：每个 (x, color) 组合先按 `agg` 聚合再绘制。 传入的列会变成图例；`legend=False` 可隐藏图例（但系列依然按 color 拆分）。
- **建议**：分类基数不宜过大：超过 10 个类别时颜色会难以区分，建议先合并低频类别。 `color` 与 `x` 不能是同一列（同一列分组没有意义）。 需要固定配色时用 `chart.palette("tableau")` 或全局 `edv.set_palette(...)`。 想只给某一条线换色（而不是整体换配色），用 `line` 的同名参数 `colors={"系列名": "#d93025"}`——`area` 是 `line(..., area=True)` 的包装，`line` 的关键字参数都原样透传。
- **示例**：`color="渠道"`
- **报错**：列名写错 → `KeyError: "列 'XX' 不存在。当前可用的列有：..."`

### `**kwargs` — 透传给 `line` 的其余参数（`dict`，必填）

- **作用**：`area` 本身没有为每个参数单独声明形参，所有 `line` 支持的参数都可以通过 `**kwargs` 传入，例如 `sort`、`top_n`、`xlim`、`theme`、`drill`。唯一会被内部覆盖的是 `area`：包装函数固定写入 `kwargs["area"] = True`，因此 `area=False` 也会被改成 True。
- **建议**：按下方逐个参数说明使用即可；不确定某参数是否支持时，以 `inspect.signature(edv.line)` 为准。
- **示例**：`edv.area(df, x="月份", y="销售额", stack=False, height=420)`
- **报错**：传了 `line` 不支持的参数（例如 `bar`、`donut`）会被 Python 以 `TypeError: line() got an unexpected keyword argument 'donut'` 拒绝。

### `agg` — 聚合方式（`str`，默认 `'sum'`）

- **作用**：同一个类目下有多行记录时的聚合函数，全部可选值：`"sum"`、`"mean"`、`"count"`、`"unique"`、`"max"`、`"min"`、`"median"`。 聚合在 `x`（以及 `color`）分组上进行；`top_n` 截断是在聚合之后做的。 部分图表会强制固定 agg：`box` 固定 `median`、`histogram` 固定 `count`，此时传入值不生效。
- **建议**：销售额/订单数等可加指标用 `sum`；单价、评分等不可加指标用 `mean` 或 `median`。 想看“每个类目出现多少条记录”时用 `count`，同时可省略 y。
- **示例**：`agg="mean"`
- **报错**：`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, unique, max, min, median`

### `smooth` — 折线是否平滑（`bool`，默认 `True`）

- **作用**：`True`（默认）时折线用平滑曲线；`False` 才是折线段。前端判断条件是 `smooth !== false`，因此只有显式 `False` 才关闭。 平滑只改变视觉，不改变数据点与聚合结果。
- **建议**：趋势类监控图常用平滑；需要精确对齐每个数据点时用 `smooth=False` + `markers=True`。 点数很少（<5）时平滑会造成“凭空多出拐点”的观感，建议关闭。
- **示例**：`smooth=False`

### `markers` — 是否显示数据点标记（line）（`bool`，默认 `None`）

- **作用**：源码会把 `markers` 写进 spec，前端只创建了一个空的 `markPoint`，**当前版本视觉上看不到任何标记**，属于待修复参数。 需要看清每个点时，暂时用 `labels=True` 显示数值，或改用 `scatter`。
- **建议**：该参数目前不产生可见效果；文档保留它是因为签名里有，修复后语义应为“显示数据点”。 如果只是为了强调关键点，可以用 `labels=True` 临时替代。
- **示例**：`markers=True`

### `sort` — 排序方式（`str`，默认 `None`）

- **作用**：`"desc"` 降序、`"asc"` 升序、`"x"` 按横轴原值排序、`"none"` 保持数据出现顺序。 默认值 `None` 表示自动：x 是日期/数值/有序分类时用 `"x"`；否则柱状图用 `"desc"`，折线/组合图用 `"none"`。 源码对 sort 不做合法性校验：传入 `"rank"` 这类非法值不会报错，而是退化为不排序（已在自检记录中标注）。
- **建议**：类目柱状图默认降序已经足够；时间序列显式写 `sort="x"` 最稳。 需要保持业务自定义顺序时用 `sort="none"`，并让 DataFrame 的行顺序正确。
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

### `xlim` — 数值轴范围（最小值, 最大值）（`tuple[float, float]`，默认 `None`）

- **作用**：只对数值轴生效；传 `(min, max)` 两元组，且两端都是数字或可转成数字的字符串。 若传反了（min > max），内部会自动交换两端；字符串无法转数字时抛 ValueError。 `bar` 的 `horizontal=True` 时数值轴是横轴，因此 `xlim` 控制横向长度。
- **建议**：想让柱子从固定基线开始时用 `ylim=(0, ...)`（纵向柱）；横向柱用 `xlim=(0, ...)`。 只写一端做不到，必须给完整两元组；不需要限制就不要传。
- **示例**：`xlim=(0, 2000000)`
- **报错**：`xlim=5` → `ValueError: xlim 需要是 (最小值, 最大值) 两元组，例如 xlim=(0, 100)`；`xlim=("a","b")` → `ValueError: could not convert string to float: 'a'`

### `ylim` — 数值轴范围（最小值, 最大值）（`tuple[float, float]`，默认 `None`）

- **作用**：只对数值轴生效；纵向柱/折线/散点时控制纵轴，`horizontal=True` 时控制类目轴（横轴）。 两元组、数字可转换；min > max 自动交换，非法字符串抛 ValueError。
- **建议**：从 0 开始的柱状图建议 `ylim=(0, None)` 不支持，直接给上限即可：`ylim=(0, 2000000)`。 需要保留负值显示时不要把下限设成 0。
- **示例**：`ylim=(0, 2000000)`
- **报错**：格式不对 → `ValueError: ylim 需要是 (最小值, 最大值) 两元组，例如 ylim=(0, 100)`

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

### `percent` — 百分比归一化（bar / line）（`bool`，默认 `False`）

- **作用**：`True` 时把每个 x 类目内的数值换算成占该类目合计的百分比（0~100%），数值轴上限固定为 100，刻度按百分比格式化。 与 `stack=True` 一起用就是百分比堆叠柱；多系列折线则变成“份额走势”。 单个类目合计为 0 时该组份额按 0 处理，不会出现除零报错。
- **建议**：比较结构占比用 `percent=True`；比较绝对量用默认 `percent=False`。 百分比堆叠时数据里不要混入负数，否则份额会扭曲。
- **示例**：`percent=True`

### `section` — 看板分区标题（仅 bar/line/kpi）（`str | None`，默认 `None`）

- **作用**：在 Dashboard 页面里把图表归入某个分区，分区标题会渲染在图表上方。 只对 `bar`、`line`、`kpi` 有效；其它图表没有这个参数。
- **建议**：同一个 Dashboard 里的分区名保持一致，例如「销售概况」「区域明细」。 单图导出时该字段只写入 spec，不影响画面。
- **示例**：`section="销售概况"`

## 返回值

所有图表函数都返回 `eazy_data_viz.Chart` 对象：`chart.spec` 是 JSON 可序列化的完整渲染配置，`chart.data` 是实际参与绘图的数据，`chart.warnings` 记录采样/丢列等降级提示；`save()` / `to_html()` / `palette()` / `show()` 的通用用法见 [交互与联动指南](../guides/06-interaction.md)。

本图的 `spec` 额外包含：

- `area`：恒为 True（包装函数强制写入）；`smooth` / `step` / `percent` 与 line 一致。
- `chart.spec["type"]` 为 `"line"`，前端按折线图渲染。

## 完整示例

以下示例都基于 `edv.sample_df()`，可直接复制运行（在仓库根目录执行）；所有输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法：日期销售额面积图

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.area(df, x="日期", y="销售额")
chart.save("examples/output/area_1.html")
```

**输出**：
- 与 `edv.line(..., area=True)` 完全等价：折线下方填充。
- 自动标题「销售额 趋势」，默认平滑；日期按升序连接。
- `chart.spec["area"] is True` 是包装函数强制写入的。

**验证**：`chart.spec["type"] == "line"`（面积图复用 line 的渲染类型）；`chart.spec["area"] is True`。

### 示例 2：按月聚合的面积趋势

```python
import eazy_data_viz as edv
df = edv.sample_df()

month = df.groupby("月份", observed=True)["销售额"].sum().reset_index()
chart = edv.area(
    month, x="月份", y="销售额", sort="x",
    title="月度销售额面积图", subtitle="面积强调累计量级",
    xtitle="月份", ytitle="销售额（元）",
)
chart.save("examples/output/area_2.html")
```

**输出**：
- 12 个有序月份，折线平滑、下方填充半透明色块。
- 聚合在 pandas 侧完成，图表只负责展示；`sort="x"` 保证月份顺序。
- 轴名被显式覆盖，自动标题不再显示。

**验证**：`len(chart.data) == 12`；面积从 0 基线填充到折线。

### 示例 3：下钻 + 联动

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.area(
    df, x="日期", y="销售额",
    drill=["日期", "大区", "产品"], link="面积联动",
    title="销售额面积下钻", subtitle="点击图形逐级下钻",
    xtitle="日期", ytitle="销售额（元）",
)
chart.save("examples/output/area_3.html")
```

**输出**：
- 首层按日期显示趋势，点击后按大区重算，再到产品层。
- `link="面积联动"` 把图加入联动组，同组图表跟随筛选。
- 下钻与面积填充不冲突，层级切换后面板重新绘制。

**验证**：`chart.spec["drill"]` 与 `chart.spec["link"]` 均已写入。

### 示例 4：主题 / 配色 / 导出

```python
import eazy_data_viz as edv
df = edv.sample_df()

month = df.groupby("月份", observed=True)["利润"].sum().reset_index()
chart = edv.area(
    month, x="月份", y="利润", sort="x",
    theme="dark", title="月度利润（深色）", labels=False,
)
chart.palette("echarts").save("examples/output/area_4.html")
```

**输出**：
- echarts 色板 + 深色主题；利润有负值时面积会跨过 0 基线。
- `chart.palette("echarts")` 返回 chart，链式保存。
- HTML 内联资源，离线可打开。

**验证**：`chart.spec["theme"] == "dark"`；文件 > 100KB。

### 示例 5：百分比份额面积（percent）

```python
import eazy_data_viz as edv
df = edv.sample_df()

month_ch = df.groupby(["月份", "渠道"], observed=True)["销售额"].sum().reset_index()
chart = edv.area(
    month_ch, x="月份", y="销售额", color="渠道",
    sort="x", percent=True, height=420,
    title="渠道份额走势", subtitle="每个时间点归一化为 100%",
    xtitle="月份", ytitle="份额",
)
chart.save("examples/output/area_5.html")
```

**输出**：
- `percent=True` 把每个月各渠道的销售额换算成份额，y 轴 0~100%。
- 多系列份额面积仍然各自从 0 起画、互相遮挡；它表达的是“份额趋势”，不是堆叠面积。
- 要严格堆叠面积请先自行累计，或改用百分比堆叠柱（bar + stack + percent）。

**验证**：`chart.spec["percent"] is True`；y 轴刻度为百分比。

## 常见问题 / 注意事项

- **area 和 line(area=True) 有什么区别？** 没有区别：`area` 的源码就是给 `kwargs["area"] = True` 后调用 `line`，签名只是少写了 line 的那一长串参数。 `chart.spec["type"]` 仍然是 `"line"`，所以基本检查脚本按 line 的规则校验它。
- **为什么传 area=False 还是填充？** 包装函数固定写入 `kwargs["area"] = True`，会覆盖你传的值；这是源码实现，当前版本无法关闭填充。 需要不填充时直接用 `edv.line(...)`。
- **多条面积互相遮挡怎么办？** 减少系列数，或点击图例只保留一两条；也可以改用 `bar`（堆叠柱）表达结构。 本库 line/area 没有 stack 参数，不能画真正的堆叠面积图。

## 相关图表

- `line`：不需要填充的纯趋势线。
- `bar`：类目对比或堆叠结构，比面积图更精确。
- `combo`：柱线双轴，同时看体量与比率。
