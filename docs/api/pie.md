# `pie` — 饼图 / 环形图

> 用扇区角度表示各部分占整体的比例，只适合“一个整体、若干部分”的构成分析。
> 适合：≤6 个类别的占比（渠道构成、产品收入占比）、环形图中心可放说明。
> 不适合：类别过多、需要精确比较相近比例、多组占比对比；这些场景用 bar 或百分比堆叠柱。

## 函数签名

```python
eazy_data_viz.pie(
    data,
    names,
    values=None,
    donut=False,
    agg="sum",
    sort="desc",
    top_n=None,
    title=None,
    subtitle=None,
    fmt="compact",
    height=360,
    theme="light",
    labels=True,
    link=None,
    max_rows=200000,
) -> Chart
```

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源 DataFrame |
| `names` | `str` | `—` | 是 | 类目名称列 |
| `values` | `str` | `None` | 否 | 数值列；省略表示统计记录数 |
| `donut` | `bool` | `False` | 否 | 环形图 |
| `agg` | `str` | `'sum'` | 否 | 聚合方式，默认 sum |
| `sort` | `str` | `'desc'` | 否 | 排序参数（当前前端恒按数值降序） |
| `top_n` | `int` | `None` | 否 | 只保留前 N 项，其余合并“其他” |
| `title` | `str \| None` | `None` | 否 | 主标题 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `fmt` | `str` | `'compact'` | 否 | 数值格式 |
| `height` | `int` | `360` | 否 | 画布高度（≥120） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `str` | `'light'` | 否 | light / dark |
| `labels` | `bool` | `True` | 否 | 显示扇区标签与引导线 |
| `link` | `str` | `None` | 否 | 联动组名 |
| `max_rows` | `int` | `200000` | 否 | 最大绘制行数 |

## 参数详解

### `data` — 数据源，图表取数的唯一入口（`pandas.DataFrame | dict | list | Series`，必填）

- **作用**：图表的数据来源。内部由 `frame.ensure_frame()` 统一处理：`DataFrame` 原样使用，`Series` 转成单列 DataFrame，`dict` / `list` 转成 DataFrame（list 每个元素当作一行）。 传入对象不会被原地修改；行数超过 `max_rows` 时内部会做均匀抽样，并把提示写进 `chart.warnings`。 列名允许中文、空格与特殊字符；绘图只需要列名唯一。
- **建议**：优先传现成的 `pandas.DataFrame`；不要在绘图函数里做复杂清洗，先 `df = ...` 准备好再传。 dict / list 只适合快速试验；正式代码建议保持 DataFrame，便于复用与排查。 只有一列数值时可以用 `Series`，例如 `edv.histogram(df["销售额"])`。
- **示例**：`data=df`
- **报错**：`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`；`data=42` → `TypeError: 无法识别 data 类型 'int'，请传入 pandas.DataFrame（或 dict / list）。`

### `names` — 类目（名称）列名（`str`，必填）

- **作用**：饼图/漏斗图的名称列，每一行（聚合后）代表一个扇区或一层。 配合 `values=None` 时表示按 names 统计记录数（此时 `agg` 变为 `count`）。
- **建议**：名称列应是分类文本或可读标签；类别过多时用 `top_n` 截断，其余合并为“其他”。 名称重复的行会按 `agg` 聚合到同一个扇区。
- **示例**：`names="产品"`
- **报错**：列名写错 → `KeyError: "列 '不存在' 不存在。当前可用的列有：..."`

### `values` — 扇区大小的数值列；省略表示计数（`str`，默认 `None`）

- **作用**：决定每个扇区大小的数值列；省略时按 names 统计记录数，`agg` 自动变为 `count`。 内部按 names 聚合（默认 sum）再交给前端；数值必须是数值 dtype。
- **建议**：占比类需求用 `sum`；想看“每类多少条”时省略 values。
- **示例**：`values="销售额"`
- **报错**：传文本列 → `TypeError: 列 '渠道' 需要是数值类型，但当前是文本类型（例如 ['直销', '渠道代理', '线上商城', '直销', '渠道代理']）。请先用 pd.to_numeric() 清洗，或换一列。`

### `donut` — 环形图（中心挖空）（`bool`，默认 `False`）

- **作用**：`True` 时半径从约 45% 到 70%，中心留白；默认实心饼图。 环形图不自动在中心写数字，需要强调中心值时用 `title`/`subtitle` 辅助。
- **建议**：类别较多或需要更清爽的视觉时用 `donut=True`。
- **示例**：`donut=True`

### `agg` — 聚合方式（`str`，默认 `'sum'`）

- **作用**：同一个类目下有多行记录时的聚合函数，全部可选值：`"sum"`、`"mean"`、`"count"`、`"max"`、`"min"`、`"median"`。 聚合在 `x`（以及 `color`）分组上进行；`top_n` 截断是在聚合之后做的。 部分图表会强制固定 agg：`box` 固定 `median`、`histogram` 固定 `count`，此时传入值不生效。
- **建议**：销售额/订单数等可加指标用 `sum`；单价、评分等不可加指标用 `mean` 或 `median`。 想看“每个类目出现多少条记录”时用 `count`，同时可省略 y。
- **示例**：`agg="mean"`
- **报错**：`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median`

### `sort` — 排序参数（当前版本不生效）（`str`，默认 `'desc'`）

- **作用**：签名默认 `sort="desc"`，但前端 `buildPie()` 恒定按数值降序绘制，传 `"asc"` 或 `"none"` 不会改变扇区顺序（已在自检记录中标注）。 需要自定义顺序时，前端不支持，只能自行接受降序结果。
- **建议**：保持默认即可；不要依赖该参数控制顺序。
- **示例**：`sort="desc"`

### `top_n` — 保留前 N 个扇区（`int`，默认 `None`）

- **作用**：按数值降序取前 N 项，其余合并为「其他」；默认不截断。 必须 ≥1 的正整数；合并后总量不变（其他项仍占一个扇区）。
- **建议**：饼图类别建议 ≤6，超过时 `top_n=5` 或 `top_n=6`。
- **示例**：`top_n=5`
- **报错**：`top_n=0` → `ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在画布左上角的主标题；不传时由函数自动生成（例如 `bar` 为「销售额 按 大区」）。 自动标题会附带分组信息：有 `color` 时追加「 · 按 渠道」。
- **建议**：正式报表建议显式写标题，自动标题只适合快速探索。 标题内不要塞入长句；补充说明放 `subtitle`。
- **示例**：`title="各大区销售额"`

### `subtitle` — 副标题（灰字说明）（`str | None`，默认 `None`）

- **作用**：显示在主标题下方的小号灰字，常用于写口径、数据范围或时间区间。 不传时不显示；与 `title` 各自独立，可以只传 subtitle。
- **建议**：写清统计口径，例如「2024 年 1~12 月，含税」。 保持一行，过长会被画布截断。
- **示例**：`subtitle="2024 全年，按订单日期统计"`

### `fmt` — 数值格式（`str`，默认 `'compact'`）

- **作用**：可选：`"compact"`（默认，1.2万 / 1.3亿）、`"thousands"`（12,345）、`"raw"`（原样）、`"percent"`（12.3%）、`"currency"`（¥12,345.67）。 作用于坐标轴刻度、`labels=True` 的标签以及 KPI 读数；不会改变原始数据。 `fmt="percent"` 只是格式化，不做归一化；要做百分比堆叠请用 `percent=True`。
- **建议**：金额用 `currency` 或 `compact`；占比用 `percent`；需要精确数字用 `thousands`。 `gauge` 的 fmt 不做校验（见 gauge 文档）；其余图的 fmt 都会严格校验。
- **示例**：`fmt="currency"`
- **报错**：`fmt="money"` → `ValueError: fmt='money' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（`int`，默认 `360`）

- **作用**：饼图默认高度 360，最小 120；环形图中心留白时适当加高。
- **建议**：清单/仪表盘里 300~380 较合适。
- **示例**：`height=380`
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

### `labels` — 显示扇区标签（`bool`，默认 `True`）

- **作用**：`True`（默认）时在扇区外显示“名称 + 数值”并画引导线；`False` 只保留图形，hover 才显示 tooltip。 标签会经过 `fmt` 格式化；扇区太小标签会重叠，此时建议关闭或先 top_n。
- **建议**：汇报截图保留标签；小屏/多类别时 `labels=False` 更干净。 卡片很矮时（例如 `height=320, abs_height=True`）外置标签容易顶出卡片边界，此时用 `labels=False` 或 `donut=True` 更稳。
- **示例**：`labels=False`

### `link` — 联动组名（`str`，默认 `None`）

- **作用**：点击扇区后按该名称筛选同组图表；再次点击同一扇区取消。 只有放在 Dashboard/HTML 页面里才生效，单图导出仅记录参数。
- **建议**：同页面所有要联动的图传相同字符串。
- **示例**：`link="产品"`

### `max_rows` — 最大参与绘制的行数（`int`，默认 `200000`）

- **作用**：默认 200000 行；超过该行数时内部做均匀抽样，而不是简单截断，尽量保留整体分布；提示写入 `chart.warnings`。 传 `None` 表示完全关闭采样，全部行进入图表（数据很大时 HTML 体积和渲染压力都会上升）。 源码没有校验取值范围：传 0 会得到 0 行（图表为空），传负数行为也不受保护（已在自检记录中标注）。 该参数只控制进入图表的行数，不改变原始 DataFrame。
- **建议**：一般保持默认 200000；前端渲染压力大时可降到 5000~10000。 确定要完整数据（例如逐条散点）时传 `max_rows=None`，并注意页面体积。 需要精确汇总时不要在超大数据集上依赖 max_rows 抽样，先自行 groupby 聚合再画。
- **示例**：`max_rows=5000`

## 返回值

所有图表函数都返回 `eazy_data_viz.Chart` 对象：`chart.spec` 是 JSON 可序列化的完整渲染配置，`chart.data` 是实际参与绘图的数据，`chart.warnings` 记录采样/丢列等降级提示；`save()` / `to_html()` / `palette()` / `show()` 的通用用法见 [交互与联动指南](../guides/06-interaction.md)。

本图的 `spec` 额外包含：

- `donut`：环形开关；`roles`：`{"name": names 列, "value": values 列或 None}`。
- 饼图没有 `legend` / `zoom` / `drill` 参数，图例恒显示。

## 完整示例

以下示例都基于 `edv.sample_df()`，可直接复制运行（在仓库根目录执行）；所有输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法：产品销售额占比

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.pie(df, names="产品", values="销售额")
chart.save("examples/output/pie_1.html")
```

**输出**：
- 按产品聚合销售额，扇区按数值降序排列，自动标题「销售额 构成」。
- 默认显示标签（名称 + 格式化数值）与引导线，`fmt="compact"` 使标签显示 1.2万/1.3亿。
- 图例恒显示（pie 没有 legend 参数）。

**验证**：`chart.spec["type"] == "pie"`；四个扇区之和 ≈ `df["销售额"].sum()`。

### 示例 2：计数值饼图：各渠道订单条数

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.pie(
    df, names="渠道",
    title="各渠道订单条数占比", subtitle="values 省略时按记录数统计",
    fmt="thousands",
)
chart.save("examples/output/pie_2.html")
```

**输出**：
- 省略 `values` 后按渠道统计行数，`agg` 自动变为 `count`。
- 标题与副标题显式覆盖；`fmt="thousands"` 让标签用千分位。
- 三个渠道的扇区比例等于各自记录条数占比。

**验证**：`chart.spec["agg"] == "count"`；`chart.spec["roles"]["value"] is None`。

### 示例 3：环形图（donut）

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.pie(
    df, names="大区", values="利润",
    donut=True, labels=True,
    title="各大区利润占比", subtitle="环形图，中心留白",
    height=400,
)
chart.save("examples/output/pie_3.html")
```

**输出**：
- 中心挖空的环形图，扇区宽度表达利润占比。
- `height=400` 让环形更舒展；标签与引导线仍显示在外侧。
- 利润若为负数，占比语义不成立，应先过滤或取绝对值。

**验证**：打开 HTML 能看到中心镂空；`chart.spec["donut"] is True`。

### 示例 4：格式 + 高度 + 暗色主题

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.pie(
    df, names="产品", values="订单数",
    theme="dark", fmt="thousands", labels=True,
    height=420, title="产品订单数（深色）",
)
chart.save("examples/output/pie_4.html")
```

**输出**：
- 深色背景 + 千分位标签，标签文字颜色自动适配为浅色。
- `labels=True` 显示名称和数值；扇区较小时标签可能重叠。
- `height=420` 给了标签更多画布空间。

**验证**：`chart.spec["theme"] == "dark"`；HTML 正常打开且资源内联。

### 示例 5：联动：点击扇区筛选同组图表

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.pie(
    df, names="渠道", values="销售额",
    link="渠道联动",
    title="渠道销售额占比", subtitle="点击扇区可筛选同组图表",
)
chart.save("examples/output/pie_5.html")
```

**输出**：
- 点击某渠道扇区后，同页面 `link="渠道联动"` 的图表按该渠道过滤重算；再点取消。
- 单图导出时点击只高亮，不产生跨图效应。
- 联动依据扇区名称，名称重复会合并后再联动。

**验证**：`chart.spec["link"] == "渠道联动"`。

## 常见问题 / 注意事项

- **为什么 sort 参数不起作用？** 当前前端 `buildPie()` 固定按数值降序排序，Python 侧写入的 sort 会被忽略；这是已知实现与参数语义不一致。 需要固定顺序时只能改数据或等版本修复；不要依赖 `sort="asc"`。
- **饼图的百分比为什么和 labels 里的数值不一致？** labels 显示的是原始数值（经过 fmt 格式化），不是自动百分比；tooltip 也显示数值。 要看百分比请自己算占比列，或在 `values` 里传已归一化的列。
- **多组占比怎么比较？** 饼图不适合并排比较；用 `bar` + `stack=True` + `percent=True` 画百分比堆叠柱，或分面多张图。

## 相关图表

- `bar`：类目精确对比；百分比堆叠柱可替代多组饼图。
- `funnel`：有阶段转化关系时用漏斗而不是饼图。
- `treemap`：类别多、还带层级时用矩形树图表达占比。
