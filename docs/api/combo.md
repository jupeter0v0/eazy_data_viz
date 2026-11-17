# `combo` — 柱线混合图

> 同一张图里用柱子表示一个指标、折线表示另一个指标，双 y 轴，适合两个量纲不同但相关的指标联动观察。
> 适合：销售额（柱）与利润率（线）、订单量（柱）与客单价（线）、规模与效率的对照。
> 不适合：两个指标量纲相同（用 line 双系列）、需要堆叠（用 bar stack）、指标超过两个（拆图）。

## 函数签名

```python
eazy_data_viz.combo(
    data,
    x,
    bar=None,
    line=None,
    agg="sum",
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    fmt="compact",
    height=400,
    theme="light",
    zoom="auto",
    max_rows=200000,
) -> Chart
```

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源 DataFrame |
| `x` | `str` | `—` | 是 | 类目/时间轴列 |
| `bar` | `str` | `None` | 否 | 柱子的数值列 |
| `line` | `str` | `None` | 否 | 折线的数值列 |
| `agg` | `str` | `'sum'` | 否 | 聚合方式，默认 sum |
| `title` | `str \| None` | `None` | 否 | 主标题 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `xtitle` | `str \| None` | `None` | 否 | 横轴标题 |
| `ytitle` | `str \| None` | `None` | 否 | 左轴标题（柱子） |
| `fmt` | `str` | `'compact'` | 否 | 数值格式 |
| `height` | `int` | `400` | 否 | 画布高度（默认 400） |
| `theme` | `str` | `'light'` | 否 | light / dark |
| `zoom` | `bool \| str` | `'auto'` | 否 | 类目多时缩放条 |
| `max_rows` | `int` | `200000` | 否 | 最大绘制行数 |

## 参数详解

### `data` — 数据源，图表取数的唯一入口（`pandas.DataFrame | dict | list | Series`，必填）

- **作用**：图表的数据来源。内部由 `frame.ensure_frame()` 统一处理：`DataFrame` 原样使用，`Series` 转成单列 DataFrame，`dict` / `list` 转成 DataFrame（list 每个元素当作一行）。 传入对象不会被原地修改；行数超过 `max_rows` 时内部会做均匀抽样，并把提示写进 `chart.warnings`。 列名允许中文、空格与特殊字符；绘图只需要列名唯一。
- **建议**：优先传现成的 `pandas.DataFrame`；不要在绘图函数里做复杂清洗，先 `df = ...` 准备好再传。 dict / list 只适合快速试验；正式代码建议保持 DataFrame，便于复用与排查。 只有一列数值时可以用 `Series`，例如 `edv.histogram(df["销售额"])`。
- **示例**：`data=df`
- **报错**：`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`；`data=42` → `TypeError: 无法识别 data 类型 'int'，请传入 pandas.DataFrame（或 dict / list）。`

### `x` — 类目/时间轴列（`str`，必填）

- **作用**：横轴维度；bar 与 line 都按该列分组聚合。 x 为日期/数值/有序分类时默认 `sort="x"`，否则保持出现顺序；combo 没有 sort 参数。 x 的基数决定 zoom 是否自动开启。
- **建议**：月份、日期、大区等低基数维度；类目>15 时建议检查 zoom 是否开启。
- **示例**：`x="月份"`
- **报错**：缺 x → `ValueError: 缺少 x：请用 x="列名" 指定横轴（分类/时间）列。`；列名错 → `KeyError`

### `bar` — 柱子的数值列（`str`，默认 `None`）

- **作用**：柱系列对应的数值列，画在左 y 轴；`ytitle` 只作用于这根轴。 必须与 line 同时提供，否则直接报错。 文本列会抛 TypeError（combo 的数值列强制校验）。
- **建议**：放“量”的指标：销售额、订单数、客户数。 同量纲的柱子用 bar 更合适。
- **示例**：`bar="销售额"`
- **报错**：只给 bar 不给 line → `ValueError: combo 需要同时指定 bar="数值列" 和 line="数值列"。`；传文本列 → `TypeError: bar 列 '产品' 需要是数值类型（当前为 文本，示例值 '智能终端'）。请先用 pd.to_numeric() 转换，或换一列。`

### `line` — 折线的数值列（`str`，默认 `None`）

- **作用**：折线系列对应的数值列，画在右 y 轴；右轴名称固定为 line 列名（不读 ytitle）。 折线默认 smooth=True、带圆点 symbol；与柱子共用横轴类目。 必须与 bar 同时提供。
- **建议**：放“率/均值”的指标：利润率、客单价、转化率。 量纲与柱不同也没关系，双轴已分开。
- **示例**：`line="利润"`
- **报错**：只给 line 不给 bar → 同上 ValueError；文本列 → `TypeError: line 列 ... 需要是数值类型 ...`

### `agg` — 聚合方式（`str`，默认 `'sum'`）

- **作用**：同一个类目下有多行记录时的聚合函数，全部可选值：`"sum"`、`"mean"`、`"count"`、`"max"`、`"min"`、`"median"`。 聚合在 `x`（以及 `color`）分组上进行；`top_n` 截断是在聚合之后做的。 部分图表会强制固定 agg：`box` 固定 `median`、`histogram` 固定 `count`，此时传入值不生效。
- **建议**：销售额/订单数等可加指标用 `sum`；单价、评分等不可加指标用 `mean` 或 `median`。 想看“每个类目出现多少条记录”时用 `count`，同时可省略 y。
- **示例**：`agg="mean"`
- **报错**：`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median`

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

### `ytitle` — 左轴标题（柱子）（`str | None`，默认 `None`）

- **作用**：只作用于左轴（bar 列）；右轴标题固定为 line 列名。 不传时左轴回退 bar 列名。
- **建议**：写柱子指标的名称与单位；折线含义靠右轴列名。
- **示例**：`ytitle="销售额（元）"`

### `fmt` — 数值格式（`str`，默认 `'compact'`）

- **作用**：可选：`"compact"`（默认，1.2万 / 1.3亿）、`"thousands"`（12,345）、`"raw"`（原样）、`"percent"`（12.3%）、`"currency"`（¥12,345.67）。 作用于坐标轴刻度、`labels=True` 的标签以及 KPI 读数；不会改变原始数据。 `fmt="percent"` 只是格式化，不做归一化；要做百分比堆叠请用 `percent=True`。
- **建议**：金额用 `currency` 或 `compact`；占比用 `percent`；需要精确数字用 `thousands`。 `gauge` 的 fmt 不做校验（见 gauge 文档）；其余图的 fmt 都会严格校验。
- **示例**：`fmt="currency"`
- **报错**：`fmt="money"` → `ValueError: fmt='money' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（`int`，默认 `400`）

- **作用**：默认 400，最小 120；双轴 + 图例 + 缩放条时建议 ≥420。
- **建议**：常规看板用 400~480。
- **示例**：`height=480`
- **报错**：`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `theme` — 主题（light / dark）（`str`，默认 `'light'`）

- **作用**：`"light"`（默认）浅色背景；`"dark"` 深色背景，坐标轴、文字、图例颜色自动反转。 主题只影响配色与背景，不改变图表结构；与其他图混排时建议统一主题。
- **建议**：大屏/深色看板用 `dark`；报告导出用 `light`。 自定义色板（`chart.palette(...)`）在两种主题下都会生效。
- **示例**：`theme="dark"`
- **报错**：`theme="blue"` → `ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `zoom` — 类目多时缩放条（`bool | str`，默认 `'auto'`）

- **作用**：`"auto"`：类目数 >15 时自动开启 dataZoom；`True` 强制开启；`False` 关闭。 缩放条作用于横轴，方便类目多时拖拽查看。 combo 没有 drill/link 参数。
- **建议**：月份 12 个默认不开启；城市/省份多时保持 auto。
- **示例**：`zoom=True`

### `max_rows` — 最大参与绘制的行数（`int`，默认 `200000`）

- **作用**：默认 200000 行；超过该行数时内部做均匀抽样，而不是简单截断，尽量保留整体分布；提示写入 `chart.warnings`。 传 `None` 表示完全关闭采样，全部行进入图表（数据很大时 HTML 体积和渲染压力都会上升）。 源码没有校验取值范围：传 0 会得到 0 行（图表为空），传负数行为也不受保护（已在自检记录中标注）。 该参数只控制进入图表的行数，不改变原始 DataFrame。
- **建议**：一般保持默认 200000；前端渲染压力大时可降到 5000~10000。 确定要完整数据（例如逐条散点）时传 `max_rows=None`，并注意页面体积。 需要精确汇总时不要在超大数据集上依赖 max_rows 抽样，先自行 groupby 聚合再画。
- **示例**：`max_rows=5000`

## 返回值

所有图表函数都返回 `eazy_data_viz.Chart` 对象：`chart.spec` 是 JSON 可序列化的完整渲染配置，`chart.data` 是实际参与绘图的数据，`chart.warnings` 记录采样/丢列等降级提示；`save()` / `to_html()` / `palette()` / `show()` 的通用用法见 [交互与联动指南](../guides/06-interaction.md)。

本图的 `spec` 额外包含：

- `roles`：`{"x": x, "y": bar, "y2": line}`；`legend=True`、`labels=False`、`drill=None`、`link=None`。
- combo 没有 `color` / `stack` / `horizontal` / `percent` / `sort` / `top_n` / `xlim` / `ylim` / `drill` / `link` / `section` 参数。
- 右轴标题固定为 line 列名；`ytitle` 只写左轴。

## 完整示例

以下示例都基于 `edv.sample_df()`，可直接复制运行（在仓库根目录执行）；所有输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法：销售额柱 + 订单数线

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.combo(df, x="月份", bar="销售额", line="订单数")
chart.save("examples/output/combo_1.html")
```

**输出**：
- 12 个月：柱子是销售额（左轴），折线是订单数（右轴）。
- 自动标题「销售额 / 订单数 按 月份」；双轴分别缩放。
- 折线 smooth=True 且带圆点；图例可点击隐藏某系列。

**验证**：`chart.spec["type"] == "combo"`；`roles == {"x": "月份", "y": "销售额", "y2": "订单数"}`。

### 示例 2：按大区：柱=销售额，线=利润

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.combo(
    df, x="大区", bar="销售额", line="利润",
    title="各大区销售额与利润", subtitle="柱=销售额（左轴），线=利润（右轴）",
)
chart.save("examples/output/combo_2.html")
```

**输出**：
- 4 个大区并排：柱高为销售额，折线点为利润。
- 利润可能为负，折线会落到 0 轴下方（右轴范围自动包含负值）。
- 左轴标题回退为「销售额」，右轴标题为「利润」。

**验证**：`chart.spec["roles"]["y2"] == "利润"`；折线含负值。

### 示例 3：mean 聚合：平均客单价

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.combo(
    df, x="产品", bar="销售额", line="利润", agg="mean",
    title="产品平均销售额与平均利润", subtitle="agg=mean 口径",
    fmt="currency", height=420,
)
chart.save("examples/output/combo_3.html")
```

**输出**：
- 按产品对销售额与利润分别求均值后绘图。
- `agg` 同时作用于柱和线，口径必须一致。
- `fmt="currency"` 让双轴刻度带 ¥。

**验证**：`chart.spec["agg"] == "mean"`；柱高等于分组均值。

### 示例 4：深色主题 + 配色

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.combo(
    df, x="渠道", bar="订单数", line="利润",
    theme="dark", height=440,
    title="渠道订单数与利润（深色）",
)
chart.palette("echarts").save("examples/output/combo_4.html")
```

**输出**：
- 深色背景，柱子与折线分别取 echarts 色板前两色。
- 图例、轴标签自动切换为浅色。
- 链式 palette 后保存。

**验证**：`chart.spec["theme"] == "dark"`；文件 > 100KB。

### 示例 5：count 聚合：记录数柱 + 客户数线

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.combo(
    df, x="渠道", bar="订单数", line="客户数", agg="count",
    fmt="thousands", height=440,
    title="渠道记录数对照", subtitle="agg=count 统计非空记录数",
)
chart.save("examples/output/combo_5.html")
```

**输出**：
- 柱与线都按 count 聚合：每个渠道的记录条数（订单数/客户数均无缺失时相同）。
- `agg` 对两个系列同时生效，口径必须一致。
- count 结果与 sum 的语义不同，汇报时注意。

**验证**：`chart.spec["agg"] == "count"`；两系列数值相等（无缺失时）。

## 常见问题 / 注意事项

- **combo 为什么没有第二个 y 轴标题参数？** `ytitle` 只作用于左轴（bar 列）；右轴标题固定读取 line 列名，无法单独改。 需要自定义右轴名称时，把 line 列名改成想要的名称（再在数据里对应）。
- **两个指标量级差很多怎么办？** 双轴本来就是各自缩放，视觉高度不具可比性；请在副标题里写清“左轴=…，右轴=…”。 若两个指标量纲相同，直接用 line 双系列更诚实。
- **combo 能堆叠柱子吗？** 不能。combo 固定一根柱 + 一条线，没有 stack 参数。 需要堆叠柱 + 折线请用 dashboard 组合 bar(stack=True) 与 line。
- **combo 能联动/下钻吗？** 签名没有 drill 与 link 参数；需要联动请把 combo 与其它图放进 dashboard，或改用 bar/line。

## 相关图表

- `line`：两个同量纲指标的趋势对比。
- `bar`：堆叠/分组柱状图。
- `kpi`：把柱线里的总体值做成指标卡。
