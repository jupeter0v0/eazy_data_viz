# `scatter` — 散点 / 气泡图

> 用点的位置表达两个数值变量的关系，可加颜色分组和气泡大小表达第三、第四维。
> 适合：相关性/离群点（客单价 vs 销量）、分布聚类、气泡图（再加一个度量）。
> 不适合：时间趋势（用 line）、类目精确比较（用 bar）；数据量大时点会重叠，需要抽样或聚合。

## 函数签名

```python
eazy_data_viz.scatter(
    data,
    x,
    y,
    color=None,
    size=None,
    agg="sum",
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    xlim=None,
    ylim=None,
    fmt="compact",
    height=380,
    theme="light",
    link=None,
    legend=True,
    max_rows=200000,
) -> Chart
```

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源 DataFrame |
| `x` | `str` | `—` | 是 | 横轴数值列（必填） |
| `y` | `str` | `—` | 是 | 纵轴数值列（必填） |
| `color` | `str` | `None` | 否 | 分组着色列 |
| `size` | `str` | `None` | 否 | 气泡大小数值列 |
| `agg` | `str` | `'sum'` | 否 | 聚合方式（当前前端未使用） |
| `title` | `str \| None` | `None` | 否 | 主标题 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `xtitle` | `str \| None` | `None` | 否 | 横轴标题 |
| `ytitle` | `str \| None` | `None` | 否 | 纵轴标题 |
| `xlim` | `tuple[float, float]` | `None` | 否 | 横轴范围元组 |
| `ylim` | `tuple[float, float]` | `None` | 否 | 纵轴范围元组 |
| `fmt` | `str` | `'compact'` | 否 | 数值格式 |
| `height` | `int` | `380` | 否 | 画布高度（≥120） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `str` | `'light'` | 否 | light / dark |
| `link` | `str` | `None` | 否 | 联动组名 |
| `legend` | `bool` | `True` | 否 | 是否显示图例 |
| `max_rows` | `int` | `2000000` | 否 | 最大绘制行数 |

## 参数详解

### `data` — 数据源，图表取数的唯一入口（`pandas.DataFrame | dict | list | Series`，必填）

- **作用**：图表的数据来源。内部由 `frame.ensure_frame()` 统一处理：`DataFrame` 原样使用，`Series` 转成单列 DataFrame，`dict` / `list` 转成 DataFrame（list 每个元素当作一行）。 传入对象不会被原地修改；行数超过 `max_rows` 时内部会做均匀抽样，并把提示写进 `chart.warnings`。 列名允许中文、空格与特殊字符；绘图只需要列名唯一。
- **建议**：优先传现成的 `pandas.DataFrame`；不要在绘图函数里做复杂清洗，先 `df = ...` 准备好再传。 dict / list 只适合快速试验；正式代码建议保持 DataFrame，便于复用与排查。 只有一列数值时可以用 `Series`，例如 `edv.histogram(df["销售额"])`。
- **示例**：`data=df`
- **报错**：`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`；`data=42` → `TypeError: 无法识别 data 类型 'int'，请传入 pandas.DataFrame（或 dict / list）。`

### `x` — 横轴数值列（`str`，必填）

- **作用**：散点图横轴必须是数值列；源码用 `_ensure_numeric` 校验，文本列不会自动转换。 与 y 一起构成二维平面；两个变量都应是连续/可比较的数值。
- **建议**：使用业务上可解释的数值对，例如「客单价 vs 订单数」「价格 vs 销量」。
- **示例**：`x="销售额"`
- **报错**：传文本列 → `TypeError: x 列 '大区' 需要是数值类型（当前为 文本，示例值 '华北'）。请先用 pd.to_numeric() 转换，或换一列。`

### `y` — 纵轴数值列（`str`，必填）

- **作用**：散点图纵轴数值列；与 x 一起决定点的位置，必须是数值 dtype。
- **建议**：y 的量级与 x 差异大时，注意坐标轴单位说明。
- **示例**：`y="订单数"`
- **报错**：传文本列 → `TypeError: 列 '产品' 需要是数值类型，但当前是文本类型（例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `color` — 分组/系列列名（`str`，默认 `None`）

- **作用**：按该列的取值把数据拆成多个系列：柱状图变成分组柱或（配合 `stack=True`）堆叠柱，折线图变成多条线，散点图按类别着色。 同时会参与聚合：每个 (x, color) 组合先按 `agg` 聚合再绘制。 传入的列会变成图例；`legend=False` 可隐藏图例（但系列依然按 color 拆分）。
- **建议**：分类基数不宜过大：超过 10 个类别时颜色会难以区分，建议先合并低频类别。 `color` 与 `x` 不能是同一列（同一列分组没有意义）。 需要固定配色时用 `chart.palette("tableau")` 或全局 `edv.set_palette(...)`。
- **示例**：`color="渠道"`
- **报错**：列名写错 → `KeyError: "列 'XX' 不存在。当前可用的列有：..."`

### `size` — 气泡大小列的数值（`str`，默认 `None`）

- **作用**：按该列数值决定点的大小：内部 sqrt 后线性映射到 6~28 像素。 大小不与图例关联，需要在 title/subtitle 中说明气泡含义。
- **建议**：取非负数值；量级差异很大时先做归一化或取对数。
- **示例**：`size="客户数"`
- **报错**：传文本列 → `TypeError: 列 '产品' 需要是数值类型，但当前是文本类型（例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `agg` — 聚合方式（当前前端不生效）（`str`，默认 `'sum'`）

- **作用**：签名保留 `agg`，但前端 `buildScatter()` 不做分组聚合，直接把每行画成一个点，因此该参数当前不改变图形（已在自检记录中标注）。 需要聚合时先在 pandas 里 `groupby(...).agg(...)`，再把结果传给 scatter。
- **建议**：不要依赖它；预先聚合更可控。
- **示例**：`agg="mean"`

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

### `link` — 联动组名（当前可能不生效）（`str`，默认 `None`）

- **作用**：点击散点后按点的名称联动同组图表；但散点的 data item 当前没有设置 `name`，点击联动依赖 `p.name`，实际可能无法触发（已在自检记录中标注）。 单图导出时只记录参数，不产生跨图效果。
- **建议**：需要稳定联动时优先用 bar/pie；散点联动需等待版本修复。
- **示例**：`link="客户"`

### `legend` — 是否显示图例（仅 color 时有效）（`bool`，默认 `True`）

- **作用**：只有传了 color 才会产生图例；没有 color 时 legend 取任何值都不显示图例。
- **建议**：按类别着色时保留图例；单色散点关闭。
- **示例**：`legend=False`

### `max_rows` — 最大参与绘制的行数（`int`，默认 `2000000`）

- **作用**：默认 2000000 行（200 万）；超过该行数时内部做均匀抽样，而不是简单截断，尽量保留整体分布；提示写入 `chart.warnings`。 传 `None` 表示完全关闭采样，全部行进入图表（数据很大时 HTML 体积和渲染压力都会上升）。 源码没有校验取值范围：传 0 会得到 0 行（图表为空），传负数行为也不受保护（已在自检记录中标注）。 该参数只控制进入图表的行数，不改变原始 DataFrame。
- **建议**：一般保持默认 2000000；前端渲染压力大时可降到 5000~10000。 确定要完整数据（例如逐条散点）时传 `max_rows=None`，并注意页面体积。 需要精确汇总时不要在超大数据集上依赖 max_rows 抽样，先自行 groupby 聚合再画。
- **示例**：`max_rows=5000`

## 返回值

所有图表函数都返回 `eazy_data_viz.Chart` 对象：`chart.spec` 是 JSON 可序列化的完整渲染配置，`chart.data` 是实际参与绘图的数据，`chart.warnings` 记录采样/丢列等降级提示；`save()` / `to_html()` / `palette()` / `show()` 的通用用法见 [交互与联动指南](../guides/06-interaction.md)。

本图的 `spec` 额外包含：

- `roles`：`{"x": 横轴数值列, "y": 纵轴数值列, "color": 分组列或 None, "size": 大小列或 None}`。
- 散点没有 `sort` / `top_n` / `drill` / `labels` / `zoom` 参数。

## 完整示例

以下示例都基于 `edv.sample_df()`，可直接复制运行（在仓库根目录执行）；所有输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法：销售额与订单数

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.scatter(df, x="销售额", y="订单数")
chart.save("examples/output/scatter_1.html")
```

**输出**：
- 1500 行数据画成 1500 个点（未聚合），横轴销售额、纵轴订单数。
- 自动标题「订单数 与 销售额」；默认固定点大小、单色。
- 点会大量重叠，真实分析前建议先聚合或抽样。

**验证**：`chart.spec["roles"]["x"] == "销售额"`；`chart.spec["roles"]["y"] == "订单数"`。

### 示例 2：气泡图：size 表达第三维

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.scatter(
    df, x="销售额", y="订单数", size="客户数",
    title="销售额 / 订单数 / 客户数", subtitle="气泡大小 = 客户数",
    xtitle="销售额（元）", ytitle="订单数",
    height=420,
)
chart.save("examples/output/scatter_2.html")
```

**输出**：
- 点的大小按客户数 sqrt 映射到 6~28 像素，形成气泡图。
- 气泡不进入图例，标题/副标题需说明大小含义。
- 仍然逐行绘制，点重叠时气泡会互相覆盖。

**验证**：`chart.spec["roles"]["size"] == "客户数"`；不同点的半径肉眼可见不同。

### 示例 3：按类别着色：产品分组

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.scatter(
    df, x="销售额", y="利润", color="产品",
    title="销售额与利润（按产品着色）",
    subtitle="不同颜色代表不同产品",
    xtitle="销售额（元）", ytitle="利润（元）",
)
chart.save("examples/output/scatter_3.html")
```

**输出**：
- 4 个产品各自一种颜色，图例显示产品名；点击图例可隐藏某类。
- 颜色只用于区分类别，不改变点位；同一产品内仍逐行绘制。
- `legend=False` 可以隐藏图例，但类别颜色仍保留。

**验证**：图例 4 项；`chart.spec["legend"] is True`。

### 示例 4：先聚合再画：城市级散点

```python
import eazy_data_viz as edv
df = edv.sample_df()

city = df.groupby("城市", observed=True).agg(
    销售额=("销售额", "sum"), 订单数=("订单数", "sum"),
).reset_index()
chart = edv.scatter(
    city, x="销售额", y="订单数", color="城市",
    title="城市级销售额 vs 订单数", subtitle="先在 pandas 聚合，避免点重叠",
    xtitle="销售额（元）", ytitle="订单数", legend=False,
)
chart.save("examples/output/scatter_4.html")
```

**输出**：
- 先按城市聚合成少量行，点更少、每个点代表一个城市。
- `color="城市"` 让每个城市颜色不同；`legend=False` 避免图例过长。
- 说明 scatter 的 agg 参数当前不生效，聚合需要在 pandas 侧完成。

**验证**：`len(chart.data) == df["城市"].nunique()`。

### 示例 5：配色 / 深色 / 导出

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.scatter(
    df, x="订单数", y="利润", color="产品", size="客户数",
    theme="dark",
    title="订单数 / 利润 / 客户数（深色气泡）",
    height=460,
)
chart.palette("carbon").save("examples/output/scatter_5.html")
```

**输出**：
- carbon 色板 + 深色主题，气泡半透明叠色。
- 链式 `palette("carbon")` 后直接保存。
- 点数多时深色背景下重叠更明显，可先聚合。

**验证**：`chart.spec["theme"] == "dark"`；HTML > 100KB。

## 常见问题 / 注意事项

- **scatter 的 agg 为什么没效果？** 前端 `buildScatter()` 没有 groupBy，直接把每行画成一个点；`agg` 当前是保留参数（已知问题）。 需要聚合时先在 pandas 侧 `groupby`，再把聚合结果传给 scatter。
- **点太多看不清怎么办？** 先聚合（城市/产品级）或 `df.sample(n)` 抽样；也可以调小 `max_rows`。 气泡图再叠加 size 会让重叠更严重，必要时去掉 size。
- **散点能连成线吗？** 不能，scatter 只画点；需要趋势线请先用 `line`，或对数据做拟合后自己加一条 line 图。

## 相关图表

- `line`：x 是有序时间时的趋势表达。
- `bar`：类目之间的精确比较。
- `heatmap`：两个维度 + 一个度量的密度/强度矩阵。
