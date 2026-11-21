# `box` — 箱线图

> 用一组箱子概括数值分布：中位数、上下四分位与极值，便于并排比较多个分组的离散程度与偏态。
> 适合：多组分布对比（各大区销售额分布）、找异常区间、比较中位数而不是均值。
> 不适合：需要看每个数据点（用 scatter/strip）、精确频数分布（用 histogram）、类别很少且样本极小时。

## 函数签名

```python
eazy_data_viz.box(
    data,
    x=None,
    y=None,
    title=None,
    subtitle=None,
    ytitle=None,
    fmt="compact",
    height=380,
    theme="light",
    max_rows=200000,
) -> Chart
```

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源 DataFrame |
| `x` | `str` | `None` | 否 | 分组维度列（可省略） |
| `y` | `str` | `None` | 否 | 数值列（可省略，仅单数值列时自动） |
| `title` | `str \| None` | `None` | 否 | 主标题 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `ytitle` | `str \| None` | `None` | 否 | 纵轴标题 |
| `fmt` | `str` | `'compact'` | 否 | 数值格式 |
| `height` | `int` | `380` | 否 | 画布高度（默认 380） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `str` | `'light'` | 否 | light / dark |
| `max_rows` | `int` | `200000` | 否 | 最大绘制行数 |

## 参数详解

### `data` — 数据源，图表取数的唯一入口（`pandas.DataFrame | dict | list | Series`，必填）

- **作用**：图表的数据来源。内部由 `frame.ensure_frame()` 统一处理：`DataFrame` 原样使用，`Series` 转成单列 DataFrame，`dict` / `list` 转成 DataFrame（list 每个元素当作一行）。 传入对象不会被原地修改；行数超过 `max_rows` 时内部会做均匀抽样，并把提示写进 `chart.warnings`。 列名允许中文、空格与特殊字符；绘图只需要列名唯一。
- **建议**：优先传现成的 `pandas.DataFrame`；不要在绘图函数里做复杂清洗，先 `df = ...` 准备好再传。 dict / list 只适合快速试验；正式代码建议保持 DataFrame，便于复用与排查。 只有一列数值时可以用 `Series`，例如 `edv.histogram(df["销售额"])`。
- **示例**：`data=df`
- **报错**：`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`；`data=42` → `TypeError: 无法识别 data 类型 'int'，请传入 pandas.DataFrame（或 dict / list）。`

### `x` — 分组维度列（可省略）（`str`，默认 `None`）

- **作用**：按该列分组，每个取值画一个箱子；省略（`x=None`）时所有数据合成一个箱子，前端 key 为「全部」。 x 可以是文本、日期或有序分类；它决定横轴的分组标签。 box 没有 sort 参数，箱子顺序由前端按数据出现顺序决定。
- **建议**：分组数建议 2~15；过多箱子会挤在一起，可先筛选或合并。 需要“整体分布”时不传 x。
- **示例**：`x="大区"`
- **报错**：列名写错 → `KeyError: "列 'XX' 不存在。当前可用的列有：..."`

### `y` — 数值列（可省略，仅单数值列时自动）（`str`，默认 `None`）

- **作用**：箱体对应的数值列；省略时仅当 DataFrame 恰好只有一个数值列才自动选取，否则要求显式指定。 用 min / Q1 / 中位数 / Q3 / max 五数概括绘制，不计算离群点（没有单独的异常点标记）。 必须数值 dtype；文本列会抛 TypeError。
- **建议**：明确写出 `y="销售额"` 最稳妥；单列子表可省略。 需要看均值时把 `agg` 理解为固定 median —— box 的统计量固定，不接受 agg 参数。
- **示例**：`y="销售额"`
- **报错**：多数值列且 `y=None` → `ValueError: box 需要指定数值列 y，例如 box(df, x="地区", y="销售额")。当前数值列有：销售额, 订单数, 利润, 客户数`；传文本列 → `TypeError: 列 '产品' 需要是数值类型，但当前是文本类型（例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在画布左上角的主标题；不传时由函数自动生成（例如 `bar` 为「销售额 按 大区」）。 自动标题会附带分组信息：有 `color` 时追加「 · 按 渠道」。
- **建议**：正式报表建议显式写标题，自动标题只适合快速探索。 标题内不要塞入长句；补充说明放 `subtitle`。
- **示例**：`title="各大区销售额"`

### `subtitle` — 副标题（灰字说明）（`str | None`，默认 `None`）

- **作用**：显示在主标题下方的小号灰字，常用于写口径、数据范围或时间区间。 不传时不显示；与 `title` 各自独立，可以只传 subtitle。
- **建议**：写清统计口径，例如「2024 年 1~12 月，含税」。 保持一行，过长会被画布截断。
- **示例**：`subtitle="2024 全年，按订单日期统计"`

### `ytitle` — 纵轴标题（唯一轴名参数）（`str | None`，默认 `None`）

- **作用**：box 只有 `ytitle`，没有 `xtitle`：纵轴是数值轴，横轴是分组标签（前端缺省用 x 列名）。 不传时回退为 y 列名。
- **建议**：需要单位时写「销售额（万元）」；分组含义由 x 列名自动显示。
- **示例**：`ytitle="销售额（万元）"`

### `fmt` — 数值格式（`str`，默认 `'compact'`）

- **作用**：可选：`"compact"`（默认，1.2万 / 1.3亿）、`"thousands"`（12,345）、`"raw"`（原样）、`"percent"`（12.3%）、`"currency"`（¥12,345.67）。 作用于坐标轴刻度、`labels=True` 的标签以及 KPI 读数；不会改变原始数据。 `fmt="percent"` 只是格式化，不做归一化；要做百分比堆叠请用 `percent=True`。
- **建议**：金额用 `currency` 或 `compact`；占比用 `percent`；需要精确数字用 `thousands`。 `gauge` 的 fmt 不做校验（见 gauge 文档）；其余图的 fmt 都会严格校验。
- **示例**：`fmt="currency"`
- **报错**：`fmt="money"` → `ValueError: fmt='money' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（`int`，默认 `380`）

- **作用**：默认 380，最小 120；箱子多时加高避免箱体被压扁。
- **建议**：2~5 组用默认；10 组以上用 460~520。
- **示例**：`height=460`
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

### `max_rows` — 最大参与绘制的行数（`int`，默认 `200000`）

- **作用**：默认 200000 行；超过该行数时内部做均匀抽样，而不是简单截断，尽量保留整体分布；提示写入 `chart.warnings`。 传 `None` 表示完全关闭采样，全部行进入图表（数据很大时 HTML 体积和渲染压力都会上升）。 源码没有校验取值范围：传 0 会得到 0 行（图表为空），传负数行为也不受保护（已在自检记录中标注）。 该参数只控制进入图表的行数，不改变原始 DataFrame。
- **建议**：一般保持默认 200000；前端渲染压力大时可降到 5000~10000。 确定要完整数据（例如逐条散点）时传 `max_rows=None`，并注意页面体积。 需要精确汇总时不要在超大数据集上依赖 max_rows 抽样，先自行 groupby 聚合再画。
- **示例**：`max_rows=5000`

## 返回值

所有图表函数都返回 `eazy_data_viz.Chart` 对象：`chart.spec` 是 JSON 可序列化的完整渲染配置，`chart.data` 是实际参与绘图的数据，`chart.warnings` 记录采样/丢列等降级提示；`save()` / `to_html()` / `palette()` / `show()` 的通用用法见 [交互与联动指南](../guides/06-interaction.md)。

本图的 `spec` 额外包含：

- `roles`：`{"x": 分组列或 None, "y": 数值列}`；`agg="median"`、`sort="none"` 固定。
- box 没有 `color` / `legend` / `labels` / `zoom` / `drill` / `link` / `xlim` / `ylim` 参数。

## 完整示例

以下示例都基于 `edv.sample_df()`，可直接复制运行（在仓库根目录执行）；所有输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法：各大区销售额分布

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.box(df, x="大区", y="销售额")
chart.save("examples/output/box_1.html")
```

**输出**：
- 每个大区一个箱子，箱体是 Q1~Q3，箱内横线是中位数，须线延伸到 min/max。
- 自动标题「销售额 分布」，`agg` 固定为 median、`sort` 固定 none。
- 不画离群点；须线端点就是数据的最小/最大值。

**验证**：`chart.spec["type"] == "box"`；`chart.spec["agg"] == "median"`；箱子数 = 大区数（4）。

### 示例 2：只给 y：整体分布单箱

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.box(
    df, y="销售额",
    title="销售额整体分布", subtitle="不分组时只画一个箱子",
    ytitle="销售额（元）",
)
chart.save("examples/output/box_2.html")
```

**输出**：
- 不传 x 时所有记录合成一个箱子，横轴标签为「全部」。
- 适合先看整体分布，再决定按哪个维度分组。
- 箱体宽度由前端固定，不表示样本量。

**验证**：`chart.spec["roles"]["x"] is None`；只有一个箱子。

### 示例 3：分组对比：产品利润分布

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.box(
    df, x="产品", y="利润",
    title="各产品利润分布", subtitle="利润有负值，须线会跨过 0",
    ytitle="利润（元）", fmt="currency",
)
chart.save("examples/output/box_3.html")
```

**输出**：
- 4 个产品并排；中位数位置可看出哪个产品典型利润更高。
- 利润含负值时须线跨过 0 基线，箱体位置也相应下移。
- `fmt="currency"` 让轴刻度与 tooltip 显示 ¥。

**验证**：`chart.spec["fmt"] == "currency"`；箱体数与产品数一致。

### 示例 4：按月份分组（有序分类）

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.box(
    df, x="月份", y="销售额",
    height=480,
    title="月度销售额分布", subtitle="12 个箱子按月排列",
    ytitle="销售额（元）", fmt="compact",
)
chart.save("examples/output/box_4.html")
```

**输出**：
- 12 个箱子按月份顺序排列，可比较各月离散程度与中位数。
- box 没有 sort 参数，顺序取决于前端对有序分类的处理（月份为 ordered Categorical）。
- `height=480` 给 12 个箱子足够宽度。

**验证**：`chart.spec["height"] == 480`；横轴出现 12 个分组。

### 示例 5：深色主题 + 配色

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.box(
    df, x="大区", y="利润",
    theme="dark", height=440,
    title="各大区利润分布（深色）",
    ytitle="利润（元）",
)
chart.palette("tableau").save("examples/output/box_5.html")
```

**输出**：
- 深色主题下箱体与须线颜色自动适配为亮色。
- tableau 色板用于区分不同大区的箱子。
- 链式 palette 后保存。

**验证**：`chart.spec["theme"] == "dark"`；文件 > 100KB。

## 常见问题 / 注意事项

- **box 能画离群点吗？** 当前版本不绘制离群点，须线直接延伸到 min/max；需要识别异常值请自己用 IQR 规则在 pandas 侧计算。 需要逐个点查看时用 `scatter`，或对数据做 strip 图。
- **box 的 agg 为什么不能改？** 签名里没有 agg 参数：箱线图固定使用中位数/四分位数统计，`chart.spec["agg"]` 恒为 `"median"`。 需要均值对比请用 `bar` + `agg="mean"`。
- **箱子代表样本量吗？** 不代表。箱体宽度由前端布局决定，与记录数无关；样本量差异大时解读分位数要谨慎。 可以先 `df.groupby(...).size()` 检查每组样本量。
- **为什么没有 xtitle？** box 的横轴是分组标签，轴名由后端固定为 x 列名（或「全部」），签名只提供 `ytitle`。 需要自定义横轴说明时写在副标题里。

## 相关图表

- `histogram`：看单个分布的完整形状与频数。
- `scatter`：查看每个数据点与异常值。
- `bar`：比较均值/合计而不是分位数。
