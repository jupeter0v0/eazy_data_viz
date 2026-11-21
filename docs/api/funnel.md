# `funnel` — 漏斗图

> 用逐层收窄的梯形表示有先后顺序的转化流程，每层宽度对应该阶段的数量。
> 适合：转化漏斗（曝光→访问→加购→下单→支付）、招聘/审批阶段、任何逐级过滤的流程。
> 不适合：没有阶段顺序的类目比较（用 bar）、多组漏斗并排（需自己分面）、占比构成（用 pie）。

## 函数签名

```python
eazy_data_viz.funnel(
    data,
    names,
    values=None,
    agg="sum",
    fmt="compact",
    height=380,
    theme="light",
    title=None,
    subtitle=None,
    labels=True,
    link=None,
    max_rows=200000,
) -> Chart
```

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源 DataFrame |
| `names` | `str` | `—` | 是 | 阶段名称列 |
| `values` | `str` | `None` | 否 | 阶段数值列；省略表示计数 |
| `agg` | `str` | `'sum'` | 否 | 聚合方式，默认 sum |
| `fmt` | `str` | `'compact'` | 否 | 数值格式 |
| `height` | `int` | `380` | 否 | 画布高度（默认 380） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `str` | `'light'` | 否 | light / dark |
| `title` | `str \| None` | `None` | 否 | 主标题 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `labels` | `bool` | `True` | 否 | 显示阶段标签（默认 True） |
| `link` | `str` | `None` | 否 | 联动组名 |
| `max_rows` | `int` | `200000` | 否 | 最大绘制行数 |

## 参数详解

### `data` — 数据源，图表取数的唯一入口（`pandas.DataFrame | dict | list | Series`，必填）

- **作用**：图表的数据来源。内部由 `frame.ensure_frame()` 统一处理：`DataFrame` 原样使用，`Series` 转成单列 DataFrame，`dict` / `list` 转成 DataFrame（list 每个元素当作一行）。 传入对象不会被原地修改；行数超过 `max_rows` 时内部会做均匀抽样，并把提示写进 `chart.warnings`。 列名允许中文、空格与特殊字符；绘图只需要列名唯一。
- **建议**：优先传现成的 `pandas.DataFrame`；不要在绘图函数里做复杂清洗，先 `df = ...` 准备好再传。 dict / list 只适合快速试验；正式代码建议保持 DataFrame，便于复用与排查。 只有一列数值时可以用 `Series`，例如 `edv.histogram(df["销售额"])`。
- **示例**：`data=df`
- **报错**：`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`；`data=42` → `TypeError: 无法识别 data 类型 'int'，请传入 pandas.DataFrame（或 dict / list）。`

### `names` — 阶段名称列（`str`，必填）

- **作用**：漏斗每一层的名称列；每行（聚合后）是一层，顺序按数值降序（前端固定 descending）。 阶段顺序应由数据决定：数值从大到小排列，因此数据里各层数量必须递减才符合漏斗直觉。
- **建议**：按业务流程顺序准备数据；如果业务顺序与数值顺序不一致，漏斗形状会“倒挂”。 阶段数 3~6 最易读。
- **示例**：`names="阶段"`
- **报错**：列名写错 → `KeyError: "列 'XX' 不存在。当前可用的列有：..."`

### `values` — 阶段数值列；省略表示计数（`str`，默认 `None`）

- **作用**：决定每层宽度的数值列；省略时按 names 统计记录数（agg 自动 count）。 必须是数值 dtype；按 names 聚合后交给前端。
- **建议**：转化人数/订单数用 sum；比率类指标不适合直接做漏斗宽度。
- **示例**：`values="人数"`
- **报错**：传文本列 → `TypeError: 列 '产品' 需要是数值类型，但当前是文本类型（例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `agg` — 聚合方式（`str`，默认 `'sum'`）

- **作用**：同一阶段有多行时如何合并；默认 sum。省略 values 时内部自动改为 count。 阶段数通常来自“人数”列，如果每阶段只有一行则 agg 不影响结果。
- **建议**：计数用省略 values 的方式；人数/金额求和用 sum。
- **示例**：`agg="sum"`
- **报错**：`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median`

### `fmt` — 数值格式（`str`，默认 `'compact'`）

- **作用**：可选：`"compact"`（默认，1.2万 / 1.3亿）、`"thousands"`（12,345）、`"raw"`（原样）、`"percent"`（12.3%）、`"currency"`（¥12,345.67）。 作用于坐标轴刻度、`labels=True` 的标签以及 KPI 读数；不会改变原始数据。 `fmt="percent"` 只是格式化，不做归一化；要做百分比堆叠请用 `percent=True`。
- **建议**：金额用 `currency` 或 `compact`；占比用 `percent`；需要精确数字用 `thousands`。 `gauge` 的 fmt 不做校验（见 gauge 文档）；其余图的 fmt 都会严格校验。
- **示例**：`fmt="currency"`
- **报错**：`fmt="money"` → `ValueError: fmt='money' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（`int`，默认 `380`）

- **作用**：默认 380，最小 120；阶段多或标签长时调高。
- **建议**：5 层漏斗用 420~480 较舒展。
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

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在画布左上角的主标题；不传时由函数自动生成（例如 `bar` 为「销售额 按 大区」）。 自动标题会附带分组信息：有 `color` 时追加「 · 按 渠道」。
- **建议**：正式报表建议显式写标题，自动标题只适合快速探索。 标题内不要塞入长句；补充说明放 `subtitle`。
- **示例**：`title="各大区销售额"`

### `subtitle` — 副标题（灰字说明）（`str | None`，默认 `None`）

- **作用**：显示在主标题下方的小号灰字，常用于写口径、数据范围或时间区间。 不传时不显示；与 `title` 各自独立，可以只传 subtitle。
- **建议**：写清统计口径，例如「2024 年 1~12 月，含税」。 保持一行，过长会被画布截断。
- **示例**：`subtitle="2024 全年，按订单日期统计"`

### `labels` — 显示阶段标签（`bool`，默认 `True`）

- **作用**：`True`（默认）时在漏斗内部显示“阶段名 + 数值”（白色文字）；`False` 只保留图形，hover 看 tooltip。 标签在窄层可能放不下，阶段多时建议关闭或加高画布。
- **建议**：汇报图保留标签；小尺寸嵌入时关闭。
- **示例**：`labels=False`

### `link` — 联动组名（`str`，默认 `None`）

- **作用**：点击某一层后按该层名称筛选同组图表；再次点击取消。 只有放进 Dashboard/HTML 页面才生效，单图导出仅记录参数。
- **建议**：同页面图表传相同 link 字符串。
- **示例**：`link="转化"`

### `max_rows` — 最大参与绘制的行数（`int`，默认 `200000`）

- **作用**：默认 200000 行；超过该行数时内部做均匀抽样，而不是简单截断，尽量保留整体分布；提示写入 `chart.warnings`。 传 `None` 表示完全关闭采样，全部行进入图表（数据很大时 HTML 体积和渲染压力都会上升）。 源码没有校验取值范围：传 0 会得到 0 行（图表为空），传负数行为也不受保护（已在自检记录中标注）。 该参数只控制进入图表的行数，不改变原始 DataFrame。
- **建议**：一般保持默认 200000；前端渲染压力大时可降到 5000~10000。 确定要完整数据（例如逐条散点）时传 `max_rows=None`，并注意页面体积。 需要精确汇总时不要在超大数据集上依赖 max_rows 抽样，先自行 groupby 聚合再画。
- **示例**：`max_rows=5000`

## 返回值

所有图表函数都返回 `eazy_data_viz.Chart` 对象：`chart.spec` 是 JSON 可序列化的完整渲染配置，`chart.data` 是实际参与绘图的数据，`chart.warnings` 记录采样/丢列等降级提示；`save()` / `to_html()` / `palette()` / `show()` 的通用用法见 [交互与联动指南](../guides/06-interaction.md)。

本图的 `spec` 额外包含：

- `roles`：`{"name": names 列, "value": values 列或 None}`；漏斗没有 `sort` / `top_n` / `legend` / `drill` 参数。
- 层顺序由前端按数值降序，Python 侧 `spec["sort"]` 恒为 `"desc"`。

## 完整示例

以下示例都基于 `edv.sample_df()`，可直接复制运行（在仓库根目录执行）；所有输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法：转化漏斗

```python
import eazy_data_viz as edv
df = edv.sample_df()

stage = pd.DataFrame({
    "阶段": ["曝光", "访问", "加购", "下单", "支付"],
    "人数": [120000, 48000, 16000, 5200, 3100],
})
chart = edv.funnel(stage, names="阶段", values="人数")
chart.save("examples/output/funnel_1.html")
```

**输出**：
- 5 层漏斗按人数从多到少排列，宽度逐渐收窄。
- 自动标题「人数 漏斗」；默认 `labels=True`，层内显示阶段名与数值。
- 数据由 dict → DataFrame 构造，是漏斗最典型的用法。

**验证**：`chart.spec["type"] == "funnel"`；层数 = 5；`chart.spec["sort"] == "desc"`。

### 示例 2：省略 values：按阶段统计记录数

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.funnel(
    df, names="渠道",
    title="各渠道记录数漏斗", subtitle="values 省略时按 count 统计",
    height=380,
)
chart.save("examples/output/funnel_2.html")
```

**输出**：
- 按渠道统计行数，三个渠道按记录数降序形成漏斗（示例仅演示参数，真实漏斗应有阶段顺序）。
- `agg` 自动变为 count；层内标签显示渠道名与记录数。
- 没有阶段顺序的类目更适合用 bar。

**验证**：`chart.spec["agg"] == "count"`；`chart.spec["roles"]["value"] is None`。

### 示例 3：深色主题 + 配色

```python
import eazy_data_viz as edv
df = edv.sample_df()

stage = pd.DataFrame({
    "阶段": ["曝光", "点击", "下单", "支付"],
    "人数": [98000, 41000, 12000, 7600],
})
chart = edv.funnel(
    stage, names="阶段", values="人数",
    theme="dark", height=440,
    title="广告转化漏斗（深色）",
)
chart.palette("antd").save("examples/output/funnel_3.html")
```

**输出**：
- 深色背景 + antd 色板，层内白字标签自动适配。
- 漏斗层颜色按顺序取自色板，越往下颜色不同。
- 链式 palette 后保存。

**验证**：`chart.spec["theme"] == "dark"`；HTML > 100KB。

### 示例 4：联动：点击层筛选

```python
import eazy_data_viz as edv
df = edv.sample_df()

stage = pd.DataFrame({
    "阶段": ["访问", "注册", "下单", "复购"],
    "人数": [64000, 28000, 9500, 3200],
})
chart = edv.funnel(
    stage, names="阶段", values="人数",
    link="转化联动",
    title="转化漏斗（可联动）", subtitle="点击某层筛选同组图表",
    height=420,
)
chart.save("examples/output/funnel_4.html")
```

**输出**：
- `link="转化联动"` 写入 spec；同页面同组图表会按点击的阶段筛选。
- 单图导出时点击只高亮当前层。
- 联动依据阶段名称，重名会合并。

**验证**：`chart.spec["link"] == "转化联动"`。

### 示例 5：mean 聚合：平均金额漏斗

```python
import eazy_data_viz as edv
df = edv.sample_df()

stage = pd.DataFrame({
    "阶段": ["询价", "报价", "成交"],
    "平均金额": [8600, 12400, 18600],
})
chart = edv.funnel(
    stage, names="阶段", values="平均金额", agg="mean",
    fmt="currency", labels=True,
    title="平均金额漏斗", subtitle="注意：均值漏斗不代表转化率",
)
chart.save("examples/output/funnel_5.html")
```

**输出**：
- 每层一个均值，层宽由均值决定；数值可能不递减，漏斗形状会不规则。
- 漏斗本质是“逐级过滤的数量”，均值类指标只适合展示“每阶段平均客单”这类辅助信息。
- `agg="mean"` 在此数据上等同于原值（每阶段一行）。

**验证**：`chart.spec["agg"] == "mean"`；层宽与均值成比例。

## 常见问题 / 注意事项

- **漏斗能自定义阶段顺序吗？** 不能。前端 ECharts funnel 固定按数值降序排列，`sort` 也没有暴露成参数；阶段顺序由数值大小决定。 要让业务顺序与数值顺序一致，请保证数据本身逐级递减。
- **漏斗层宽是转化率吗？** 不是，层宽对应 values（或记录数）的绝对值；需要转化率请自己计算并写在副标题/标签里。 本库没有内置“相对首层百分比”的漏斗样式。
- **为什么 labels=False 后什么都没有了？** `labels=False` 只关闭层内标签，图形仍在；hover 可以看 tooltip。 如果图形也不可见，检查数据是否为空或 values 全为 0。

## 相关图表

- `bar`：没有阶段顺序的类目比较。
- `pie`：整体构成占比。
- `kpi`：把漏斗的总体转化率做成指标卡。
