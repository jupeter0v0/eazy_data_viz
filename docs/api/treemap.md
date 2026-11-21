# `treemap` — 矩形树图

> 用嵌套矩形面积表达数值大小，矩形按层级分组，一层套一层，适合类别多且带父子关系的构成分析。
> 适合：层级构成（大区→产品→渠道）、面积占比、类别很多时的整体分布。
> 不适合：精确比较相近数值（用 bar）、时间趋势（用 line）、没有层级关系的单层类别（用 pie/bar）。

## 函数签名

```python
eazy_data_viz.treemap(
    data,
    path,
    value,
    agg="sum",
    title=None,
    subtitle=None,
    fmt="compact",
    height=420,
    theme="light",
    max_rows=200000,
) -> Chart
```

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源 DataFrame |
| `path` | `str \| list[str]` | `—` | 是 | 层级维度列表（从外到内） |
| `value` | `str \| float` | `—` | 是 | 矩形面积的数值列 |
| `agg` | `str` | `'sum'` | 否 | 聚合方式，默认 sum |
| `title` | `str \| None` | `None` | 否 | 主标题 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `fmt` | `str` | `'compact'` | 否 | 数值格式 |
| `height` | `int` | `420` | 否 | 画布高度（默认 420） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `str` | `'light'` | 否 | light / dark |
| `max_rows` | `int` | `200000` | 否 | 最大绘制行数 |

## 参数详解

### `data` — 数据源，图表取数的唯一入口（`pandas.DataFrame | dict | list | Series`，必填）

- **作用**：图表的数据来源。内部由 `frame.ensure_frame()` 统一处理：`DataFrame` 原样使用，`Series` 转成单列 DataFrame，`dict` / `list` 转成 DataFrame（list 每个元素当作一行）。 传入对象不会被原地修改；行数超过 `max_rows` 时内部会做均匀抽样，并把提示写进 `chart.warnings`。 列名允许中文、空格与特殊字符；绘图只需要列名唯一。
- **建议**：优先传现成的 `pandas.DataFrame`；不要在绘图函数里做复杂清洗，先 `df = ...` 准备好再传。 dict / list 只适合快速试验；正式代码建议保持 DataFrame，便于复用与排查。 只有一列数值时可以用 `Series`，例如 `edv.histogram(df["销售额"])`。
- **示例**：`data=df`
- **报错**：`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`；`data=42` → `TypeError: 无法识别 data 类型 'int'，请传入 pandas.DataFrame（或 dict / list）。`

### `path` — 层级维度列表（从外到内）（`str | list[str]`，必填）

- **作用**：层级路径：`"大区"` 等价于 `["大区"]`；`["大区", "产品", "渠道"]` 表示先按大区分块、块内按产品、再按渠道。 列表顺序即层级顺序；每层矩形面积由该层聚合后的 value 决定。 点击子节点会放大（zoomToNode）该层；再次点击空白区域返回。
- **建议**：2~3 层最易读；超过 3 层矩形会很小。 层级列必须存在且最好是有包含关系的维度。
- **示例**：`path=["大区", "产品"]`
- **报错**：`path=[]` → `ValueError: treemap 的 path 不能为空，例如 path=["大区", "品类"]。`；列名写错 → `KeyError: "列 'XX' 不存在。当前可用的列有：..."`

### `value` — 矩形面积的数值列（`str | float`，必填）

- **作用**：决定每个矩形面积的度量列；按 path 的层级逐级聚合（默认 sum）。 必须是数值 dtype；负值在树图里没有面积语义，建议先过滤或取绝对值。
- **建议**：面积是可加指标时用 sum；均值/率类指标用 mean 但面积比较会失真。
- **示例**：`value="销售额"`
- **报错**：传文本列 → `TypeError: 列 '渠道' 需要是数值类型，但当前是文本类型（例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

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

### `fmt` — 数值格式（`str`，默认 `'compact'`）

- **作用**：可选：`"compact"`（默认，1.2万 / 1.3亿）、`"thousands"`（12,345）、`"raw"`（原样）、`"percent"`（12.3%）、`"currency"`（¥12,345.67）。 作用于坐标轴刻度、`labels=True` 的标签以及 KPI 读数；不会改变原始数据。 `fmt="percent"` 只是格式化，不做归一化；要做百分比堆叠请用 `percent=True`。
- **建议**：金额用 `currency` 或 `compact`；占比用 `percent`；需要精确数字用 `thousands`。 `gauge` 的 fmt 不做校验（见 gauge 文档）；其余图的 fmt 都会严格校验。
- **示例**：`fmt="currency"`
- **报错**：`fmt="money"` → `ValueError: fmt='money' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（`int`，默认 `420`）

- **作用**：树图默认 420，最小 120；层级多、矩形密时加高。
- **建议**：两层用 420~480；三层用 520 以上。
- **示例**：`height=520`
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

- `path`：层级列表；`roles`：`{"path": [...], "value": 数值列}`；`sort="desc"` 固定写入。
- treemap 没有 `labels` / `legend` / `link` / `drill` / `top_n` 参数，标签恒显示（放得下时）。

## 完整示例

以下示例都基于 `edv.sample_df()`，可直接复制运行（在仓库根目录执行）；所有输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法：单层树图

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.treemap(df, path="大区", value="销售额")
chart.save("examples/output/treemap_1.html")
```

**输出**：
- 4 个大区各占一块矩形，面积与销售额成正比。
- 自动标题「销售额 层级构成」；矩形上显示大区名与数值。
- 点击矩形会放大该大区（单层时仅聚焦显示）。

**验证**：`chart.spec["type"] == "treemap"`；顶级节点数 = 大区数（4）。

### 示例 2：两层：大区 → 产品

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.treemap(
    df, path=["大区", "产品"], value="销售额",
    height=480,
    title="大区 × 产品销售额树图", subtitle="外层大区，内层产品",
    fmt="compact",
)
chart.save("examples/output/treemap_2.html")
```

**输出**：
- 先按大区分块，每块内部再按产品切分矩形；面积仍按销售额。
- `height=480` 让两层矩形都有足够面积显示标签。
- 点击产品矩形会放大到该产品所在块。

**验证**：`chart.spec["path"] == ["大区", "产品"]`；二级节点数 = 大区 × 产品的有效组合数。

### 示例 3：三层：大区 → 产品 → 渠道

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.treemap(
    df, path=["大区", "产品", "渠道"], value="销售额",
    height=560, fmt="compact",
    title="三层销售构成", subtitle="大区 → 产品 → 渠道",
)
chart.save("examples/output/treemap_3.html")
```

**输出**：
- 三层嵌套，最内层是渠道；面积 = 对应组合的销售额。
- 三层时矩形较小，`height=560` 尽量保证标签可读。
- 点击可逐层放大，空白处点击返回上层。

**验证**：`chart.spec["path"]` 长度 3；最内层节点总数 ≤ 4×4×3。

### 示例 4：深色主题 + 配色

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.treemap(
    df, path=["产品", "渠道"], value="利润",
    theme="dark", height=480, fmt="compact",
    title="产品 × 渠道利润（深色）",
)
chart.palette("echarts").save("examples/output/treemap_4.html")
```

**输出**：
- 深色主题 + echarts 色板；矩形标签与边框自动适配。
- 利润有负值时面积语义不严谨，本示例仅用于演示主题与配色。
- 链式 palette 后保存。

**验证**：`chart.spec["theme"] == "dark"`；文件 > 100KB。

### 示例 5：mean 聚合：平均销售额树图

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.treemap(
    df, path=["大区", "产品"], value="销售额",
    agg="mean", height=460, fmt="compact",
    title="平均销售额树图", subtitle="agg=mean，面积代表均值",
)
chart.save("examples/output/treemap_5.html")
```

**输出**：
- 按 (大区, 产品) 求均值后决定面积；与 sum 图的大小关系可能不同。
- 均值类指标用面积表达会让人误以为“总量”，业务解释要写清。
- `agg="mean"` 会逐级影响父子面积。

**验证**：`chart.spec["agg"] == "mean"`；面积比例与均值一致。

## 常见问题 / 注意事项

- **treemap 能下钻吗？** 没有 drill 参数；交互是点击矩形 zoomToNode 放大该层，再点空白返回，不是数据维度重算。 需要按维度逐级重算请用 bar/line 的 drill。
- **treemap 的 sort 为什么没用？** Python 侧固定写 `sort="desc"`，但前端构建树时没有读取该字段，矩形顺序由数据出现顺序决定。 需要控制顺序请先 `df.sort_values(...)` 再传。
- **矩形太小/标签不显示怎么办？** 减少层级（2 层最稳）、减少类别（先 top_n 式过滤）、加高画布（height 520+）。 前端自动隐藏放不下的标签，hover 可查看完整名称与数值。
- **为什么面积和数值不成比例？** 树图按层级逐级布局，父级矩形大小受层级 padding 与子节点数量影响，看起来不完全线性。 精确比例请用 bar；树图适合快速看构成与量级。

## 相关图表

- `pie`：单层构成占比，类别少时更直观。
- `bar`：精确比较各类目数值。
- `heatmap`：二维交叉的强度，而不是层级面积。
