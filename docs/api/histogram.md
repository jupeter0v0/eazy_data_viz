# `histogram` — 直方图

> 把连续数值切成等宽区间并统计频数，用柱高展示分布形状（集中、偏态、双峰、离群）。
> 适合：数值分布、分箱统计、数据质量检查（异常值/长尾）、建模前探索。
> 不适合：类目计数（用 bar）、随时间的分布变化（按时间分面或热力图）、精确到个值的频率。

## 函数签名

```python
eazy_data_viz.histogram(
    data,
    column=None,
    bins=20,
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle="频数",
    fmt="compact",
    height=360,
    theme="light",
    labels=False,
    max_rows=200000,
) -> Chart
```

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源 DataFrame |
| `column` | `str` | `None` | 否 | 要画分布的数值列（可省略） |
| `bins` | `int` | `20` | 否 | 分箱数，默认 20 |
| `title` | `str \| None` | `None` | 否 | 主标题 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `xtitle` | `str \| None` | `None` | 否 | 横轴标题（缺省用列名） |
| `ytitle` | `str \| None` | `'频数'` | 否 | 纵轴标题，默认“频数” |
| `fmt` | `str` | `'compact'` | 否 | 数值格式 |
| `height` | `int` | `360` | 否 | 画布高度（默认 360） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `str` | `'light'` | 否 | light / dark |
| `labels` | `bool` | `False` | 否 | 标签开关（当前前端忽略） |
| `max_rows` | `int` | `200000` | 否 | 最大绘制行数 |

## 参数详解

### `data` — 数据源，图表取数的唯一入口（`pandas.DataFrame | dict | list | Series`，必填）

- **作用**：图表的数据来源。内部由 `frame.ensure_frame()` 统一处理：`DataFrame` 原样使用，`Series` 转成单列 DataFrame，`dict` / `list` 转成 DataFrame（list 每个元素当作一行）。 传入对象不会被原地修改；行数超过 `max_rows` 时内部会做均匀抽样，并把提示写进 `chart.warnings`。 列名允许中文、空格与特殊字符；绘图只需要列名唯一。
- **建议**：优先传现成的 `pandas.DataFrame`；不要在绘图函数里做复杂清洗，先 `df = ...` 准备好再传。 dict / list 只适合快速试验；正式代码建议保持 DataFrame，便于复用与排查。 只有一列数值时可以用 `Series`，例如 `edv.histogram(df["销售额"])`。
- **示例**：`data=df`
- **报错**：`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`；`data=42` → `TypeError: 无法识别 data 类型 'int'，请传入 pandas.DataFrame（或 dict / list）。`

### `column` — 要画分布的数值列（可省略）（`str`，默认 `None`）

- **作用**：直方图的数据列；省略时仅当 DataFrame 恰好只有一个数值列才自动选取，否则要求显式指定。 列里的 NaN 会被过滤掉；非数值列不会自动转换。
- **建议**：默认就用 `column="销售额"` 明确写出，避免数据源变化导致自动选择漂移。
- **示例**：`column="销售额"`
- **报错**：多数值列且未指定 → `ValueError: histogram 需要指定一个数值列，例如 histogram(df, column="销售额")。当前数值列有：销售额, 订单数, 利润, 客户数`；传文本列 → `TypeError: 列 '大区' 需要是数值类型，但当前是文本类型（例如 ['华东', '华东', '华东', '华北', '华北']）。请先用 pd.to_numeric() 清洗，或换一列。`

### `bins` — 分箱数（`int`，默认 `20`）

- **作用**：把数值范围等宽切成 bins 个区间，频数画成柱高。 源码不校验：`bins=0`、`bins=-3`、`bins="8"` 都会通过 Python 校验，但前端行为不可靠（已在自检记录中标注）。
- **建议**：用 10~30 的整数；样本量越大可以适当增加。 想看长尾时先用 `np.log1p` 变换，再画直方图。
- **示例**：`bins=15`

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在画布左上角的主标题；不传时由函数自动生成（例如 `bar` 为「销售额 按 大区」）。 自动标题会附带分组信息：有 `color` 时追加「 · 按 渠道」。
- **建议**：正式报表建议显式写标题，自动标题只适合快速探索。 标题内不要塞入长句；补充说明放 `subtitle`。
- **示例**：`title="各大区销售额"`

### `subtitle` — 副标题（灰字说明）（`str | None`，默认 `None`）

- **作用**：显示在主标题下方的小号灰字，常用于写口径、数据范围或时间区间。 不传时不显示；与 `title` 各自独立，可以只传 subtitle。
- **建议**：写清统计口径，例如「2024 年 1~12 月，含税」。 保持一行，过长会被画布截断。
- **示例**：`subtitle="2024 全年，按订单日期统计"`

### `xtitle` — 横轴标题（缺省用列名）（`str | None`，默认 `None`）

- **作用**：覆盖横轴轴名；不传时自动使用 column 的列名。
- **建议**：需要单位时写在这里，例如「销售额（元）」。 分箱区间标签由前端按 lo~hi 生成。
- **示例**：`xtitle="销售额（元）"`

### `ytitle` — 纵轴标题，默认“频数”（`str | None`，默认 `'频数'`）

- **作用**：直方图纵轴表示频数，默认标题「频数」；可改成「订单数」「记录条数」等业务说法。 若数据已被采样（超过 max_rows），频数是采样后的口径，不是全量。
- **建议**：写清统计口径，例如「记录数（抽样后）」。 横轴标题缺省用数值列名，可用 `xtitle` 覆盖。
- **示例**：`ytitle="订单数"`

### `fmt` — 数值格式（`str`，默认 `'compact'`）

- **作用**：可选：`"compact"`（默认，1.2万 / 1.3亿）、`"thousands"`（12,345）、`"raw"`（原样）、`"percent"`（12.3%）、`"currency"`（¥12,345.67）。 作用于坐标轴刻度、`labels=True` 的标签以及 KPI 读数；不会改变原始数据。 `fmt="percent"` 只是格式化，不做归一化；要做百分比堆叠请用 `percent=True`。
- **建议**：金额用 `currency` 或 `compact`；占比用 `percent`；需要精确数字用 `thousands`。 `gauge` 的 fmt 不做校验（见 gauge 文档）；其余图的 fmt 都会严格校验。
- **示例**：`fmt="currency"`
- **报错**：`fmt="money"` → `ValueError: fmt='money' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素，默认 380）（`int`，默认 `360`）

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

### `labels` — 显示频数标签（当前前端忽略）（`bool`，默认 `False`）

- **作用**：签名保留 labels，但前端 `buildHistogram()` 不读取该字段，打开后柱顶也不会出现频数标签（已在自检记录中标注）。 需要频数请把鼠标悬停看 tooltip，或改用 bar 自己分箱。
- **建议**：当前版本不要依赖该参数。
- **示例**：`labels=True`

### `max_rows` — 最大参与绘制的行数（`int`，默认 `200000`）

- **作用**：默认 200000 行；超过该行数时内部做均匀抽样，而不是简单截断，尽量保留整体分布；提示写入 `chart.warnings`。 传 `None` 表示完全关闭采样，全部行进入图表（数据很大时 HTML 体积和渲染压力都会上升）。 源码没有校验取值范围：传 0 会得到 0 行（图表为空），传负数行为也不受保护（已在自检记录中标注）。 该参数只控制进入图表的行数，不改变原始 DataFrame。
- **建议**：一般保持默认 200000；前端渲染压力大时可降到 5000~10000。 确定要完整数据（例如逐条散点）时传 `max_rows=None`，并注意页面体积。 需要精确汇总时不要在超大数据集上依赖 max_rows 抽样，先自行 groupby 聚合再画。
- **示例**：`max_rows=5000`

## 返回值

所有图表函数都返回 `eazy_data_viz.Chart` 对象：`chart.spec` 是 JSON 可序列化的完整渲染配置，`chart.data` 是实际参与绘图的数据，`chart.warnings` 记录采样/丢列等降级提示；`save()` / `to_html()` / `palette()` / `show()` 的通用用法见 [交互与联动指南](../guides/06-interaction.md)。

本图的 `spec` 额外包含：

- `bins`：分箱数；`roles`：`{"value": column 列名}`；`agg="count"`、`sort="none"` 固定。
- histogram 没有 `color` / `legend` / `drill` / `zoom` / `link` 参数。

## 完整示例

以下示例都基于 `edv.sample_df()`，可直接复制运行（在仓库根目录执行）；所有输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法：销售额分布

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.histogram(df, column="销售额", bins=20)
chart.save("examples/output/histogram_1.html")
```

**输出**：
- 把销售额切成 20 个等宽区间，柱高为落入区间的记录数。
- 自动标题「销售额 分布」，横轴显示区间（如 1.2万~2.1万），纵轴「频数」。
- 默认 `agg="count"`、`sort="none"`，不会按频数排序。

**验证**：`chart.spec["type"] == "histogram"`；`chart.spec["bins"] == 20`；各柱频数之和等于非空销售额行数。

### 示例 2：调整分箱数：bins 对比

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.histogram(
    df, column="销售额", bins=10,
    title="销售额分布（10 箱）", subtitle="箱数少，形状更平滑",
    xtitle="销售额（元）", ytitle="记录数",
)
chart.save("examples/output/histogram_2.html")
```

**输出**：
- 只有 10 根柱子，形态更概括，容易看出单峰/长尾。
- 和 20/40 箱对比可以看到分辨率与噪声的权衡。
- `bins` 必须用整数；非法值当前不会报错但前端行为不可靠。

**验证**：`chart.spec["bins"] == 10`；柱数应为 10。

### 示例 3：省略 column：自动选择唯一数值列

```python
import eazy_data_viz as edv
df = edv.sample_df()

profit = df[["利润"]].copy()
chart = edv.histogram(
    profit, bins=15,
    title="利润分布（自动选列）", subtitle="子表只剩一个数值列，column 可省略",
    height=380,
)
chart.save("examples/output/histogram_3.html")
```

**输出**：
- 子表只有一个数值列时，`column=None` 自动选中「利润」。
- 利润有正有负，分箱会跨过 0，横轴可能出现负区间。
- 在完整 df 上省略 column 会报错（有 4 个数值列），这是源码的保护逻辑。

**验证**：`chart.spec["roles"]["value"] == "利润"`；柱状区间从负值开始。

### 示例 4：深色主题 + 配色

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.histogram(
    df, column="利润", bins=24,
    theme="dark",
    title="利润分布（深色）", subtitle="24 箱，观察长尾",
    xtitle="利润（元）", ytitle="记录数",
)
chart.palette("antd").save("examples/output/histogram_4.html")
```

**输出**：
- 深色背景 + antd 色板，柱子为色板第一个颜色。
- 利润长尾（少数大额利润）在 24 箱下更容易看到。
- histogram 只有单系列，图例无意义，不显示图例。

**验证**：`chart.spec["theme"] == "dark"`；保存文件 > 100KB。

### 示例 5：对数变换后的分布

```python
import eazy_data_viz as edv
df = edv.sample_df()

import numpy as np
log_df = df.assign(对数销售额=np.log1p(df["销售额"]))
chart = edv.histogram(
    log_df, column="对数销售额", bins=20,
    title="销售额的对数分布", subtitle="log1p 变换后更接近对称",
    xtitle="log(1 + 销售额)", ytitle="记录数",
)
chart.save("examples/output/histogram_5.html")
```

**输出**：
- 对数变换把右偏的金额分布拉成更对称的形状，便于看主体区间。
- 横轴是 log 值，读图时要注意不能直接当金额解释。
- `df.assign` 新建列，不改原始 DataFrame。

**验证**：`chart.data` 中有「对数销售额」列；横轴范围约 0~15。

## 常见问题 / 注意事项

- **为什么 bins 传 0 也不报错？** 源码没有校验 bins 的取值范围与类型，`0`、`-3`、`"8"` 都会通过 Python 侧校验；前端可能画不出有效直方图。 这是已知实现问题，写代码时请自行保证传正整数。
- **labels=True 为什么没有频数标签？** 前端 `buildHistogram()` 没有读取 spec.labels，属于当前版本的无效参数。 需要精确频数时用 tooltip，或先用 `pd.cut` 分箱 + `bar` 自己画。
- **直方图和 bar 有什么区别？** 直方图的 x 是连续区间的分箱，柱与柱之间没有间隙，表达分布；bar 的 x 是离散类目，表达比较。 已经分好箱、想控制颜色/堆叠/标签时用 bar 更灵活。

## 相关图表

- `box`：用五数概括并排比较多个分布的箱线图。
- `bar`：已分箱的频数用 bar 画，可控性更强。
- `heatmap`：两个维度上的分布热力。
