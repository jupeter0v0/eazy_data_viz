# `gauge` — 仪表盘

> 用指针在刻度盘上的位置展示单个数值相对目标区间的完成度，适合大屏/看板上的核心指标。
> 适合：完成率、满意度、健康分、温度等单值指标；一屏多个 gauge 并列。
> 不适合：多值对比（用 bar）、趋势（用 line/kpi+spark）、需要精确读数的报表（用 kpi）。

## 函数签名

```python
eazy_data_viz.gauge(
    value,
    *,
    label=None,
    min=0,
    max=100,
    fmt="raw",
    unit=None,
    height=260,
    abs_height=False,
    theme="light",
    title=None,
    subtitle=None,
) -> Chart
```

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `value` | `str \| float` | `—` | 是 | 要展示的单个数值 |
| `label` | `str` | `None` | 否 | 读数旁的名称 |
| `min` | `float` | `0` | 否 | 刻度下限，默认 0 |
| `max` | `float` | `100` | 否 | 刻度上限，默认 100 |
| `fmt` | `str` | `'raw'` | 否 | 数值格式，默认 raw |
| `unit` | `str` | `None` | 否 | 单位后缀 |
| `height` | `int` | `260` | 否 | 画布高度（默认 260） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `str` | `'light'` | 否 | light / dark |
| `title` | `str \| None` | `None` | 否 | 主标题（缺省回退 label） |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |

## 参数详解

### `value` — 要展示的单个数值（`str | float`，必填）

- **作用**：gauge 只接受单个数值：int/float 或可被 `float()` 转换的字符串；不能传 DataFrame/Series。 数值超出 [min, max] 时指针顶格，但读数仍显示原值。 需要从 DataFrame 聚合出单个值请用 `kpi(df, value="销售额")`，它有卡片样式与更多能力。
- **建议**：先自己算好聚合值再传，例如 `df["销售额"].sum()`。 百分比类指标直接传 87.5 这类 0~100 的数，配合 `fmt="percent"`。
- **示例**：`edv.gauge(df["销售额"].sum() / 1e6, label="销售额（百万元）", max=20)`
- **报错**：传 DataFrame → `TypeError: gauge 接受单个数值，例如 eazy_data_viz.gauge(87.5)。如果要聚合 DataFrame，请用 eazy_data_viz.kpi(df, value="销售额")。`

### `label` — 读数旁的名称（可省略）（`str`，默认 `None`）

- **作用**：显示在仪表盘中央读数旁边的名称；不传时标题区为空。 `title` 不传时 gauge 会回退用 label 作为标题（见源码）。
- **建议**：短名词，例如「完成率」「满意度」。 长说明放 subtitle。
- **示例**：`label="完成率"`

### `min` — 刻度下限（`float`，默认 `0`）

- **作用**：仪表盘刻度起点；必须严格小于 max，否则报错。 负值可用于温差、同比变化等场景。
- **建议**：完成率/满意度保持 0；差值类指标可用负数。
- **示例**：`min=-10`
- **报错**：`max <= min` → `ValueError: gauge 的 max 必须大于 min。`

### `max` — 刻度上限（`float`，默认 `100`）

- **作用**：仪表盘刻度终点；value 超过它也照常显示读数，只是指针顶格。 内部只校验 max > min，不校验 value 是否在区间内。
- **建议**：百分比用 100；金额类按业务上限设，例如 20（百万元）。
- **示例**：`max=200`
- **报错**：`max <= min` → `ValueError: gauge 的 max 必须大于 min。`

### `fmt` — 数值格式（`str`，默认 `'raw'`）

- **作用**：对中央读数做格式化：`raw` 原样、`compact` 1.2万、`thousands` 千分位、`percent` 加 %、`currency` ¥。 注意：`percent` 只是加 `%` 号，不乘 100；value=87.5 会显示 87.5%。 gauge 不走统一参数校验，非法 fmt（如 `"money"`）不会报错而是按 compact 处理（已在自检记录中标注）。
- **建议**：百分比用 `percent` 且 value 已经是 0~100 的数。 金额用 `currency` 或 `compact`。
- **示例**：`fmt="percent"`

### `unit` — 单位后缀（`str`，默认 `None`）

- **作用**：拼在格式化读数后面的单位文本，例如「单」「℃」；fmt=percent 时仍会拼接。 gauge 不做单位换算，只做后缀。
- **建议**：1~2 个字符；不要与 fmt 自带的 %/¥ 重复。
- **示例**：`unit="单"`

### `height` — 画布高度（`int`，默认 `260`）

- **作用**：gauge 默认 260；与其它图不同，gauge 的 height 不经过最小 120 校验，传 80 也不会报错（已在自检记录中标注）。 高度太小时刻度与读数会挤在一起。
- **建议**：大屏单个 gauge 用 260~360；并排小卡用 200~240。
- **示例**：`height=320`

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — light / dark（不校验）（`str`，默认 `'light'`）

- **作用**：gauge 的 theme 同样不经过统一校验，传非法字符串不会报错，前端按 light 处理（已在自检记录中标注）。
- **建议**：只用 `light` / `dark`。
- **示例**：`theme="dark"`

### `title` — 主标题（缺省回退 label）（`str | None`，默认 `None`）

- **作用**：主标题；不传时 gauge 会回退使用 `label`（源码行为），因此只传 label 也会出现在标题区。
- **建议**：需要同时显示标题与读数名称时分别传 title 和 label。
- **示例**：`title="年度目标完成率"`

### `subtitle` — 副标题（`str | None`，默认 `None`）

- **作用**：标题下方的灰字说明，可用于写口径与时间范围。
- **建议**：一行短句，说明数据口径。
- **示例**：`subtitle="截至 2024-12-31"`

## 返回值

所有图表函数都返回 `eazy_data_viz.Chart` 对象：`chart.spec` 是 JSON 可序列化的完整渲染配置，`chart.data` 是实际参与绘图的数据，`chart.warnings` 记录采样/丢列等降级提示；`save()` / `to_html()` / `palette()` / `show()` 的通用用法见 [交互与联动指南](../guides/06-interaction.md)。

本图的 `spec` 额外包含：

- `spec` 直接包含 `value`、`min`、`max`、`label`、`unit`、`fmt`、`title`、`subtitle`，没有 `dataRef`/`roles`。
- gauge 没有 `legend` / `labels` / `drill` / `link` / `max_rows` 参数。

## 完整示例

以下示例都基于 `edv.sample_df()`，可直接复制运行（在仓库根目录执行）；所有输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法：单个百分比

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.gauge(87.5)
chart.save("examples/output/gauge_1.html")
```

**输出**：
- 默认刻度 0~100，指针停在 87.5；中央读数显示 87.5。
- `fmt="raw"` 原样输出，无标题、无单位。
- `chart.spec["type"] == "gauge"`，rows=1。

**验证**：`chart.spec["value"] == 87.5`；`chart.spec["min"] == 0`、`max == 100`。

### 示例 2：百分比格式：fmt=percent

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.gauge(
    87.5, fmt="percent",
    label="目标达成", unit=None,
    title="目标达成率", subtitle="percent 只加 %，不乘 100",
)
chart.save("examples/output/gauge_2.html")
```

**输出**：
- 读数显示 87.5%（而不是 8750%）。
- `fmt="percent"` 只拼接 %；value 本身应已经是 0~100 的百分数。
- 标题与 label 分开，副标题说明口径。

**验证**：读数文本应为 87.5%；`chart.spec["fmt"] == "percent"`。

### 示例 3：负数区间：温度

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.gauge(
    -4.5, label="当前温度", min=-20, max=45,
    fmt="raw", unit="℃",
    title="室外温度", subtitle="min=-20, max=45",
    height=300,
)
chart.save("examples/output/gauge_3.html")
```

**输出**：
- 刻度从 -20 到 45，指针在负温区；读数显示「-4.5℃」。
- min 为负数时刻度标签也带负号。
- value 必须在业务上落在区间内，否则指针顶格。

**验证**：`chart.spec["min"] == -20`；`max == 45`；读数含 ℃。

### 示例 4：深色主题

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.gauge(
    68, label="健康分", theme="dark",
    title="设备健康分（深色）", height=300,
)
chart.save("examples/output/gauge_4.html")
```

**输出**：
- 深色背景，刻度条与文字切换为浅色。
- gauge 的 theme 不做校验，但传 light/dark 会正常生效。
- 适合放在深色大屏上。

**验证**：`chart.spec["theme"] == "dark"`。

### 示例 5：聚合后传入：由 DataFrame 算出单值

```python
import eazy_data_viz as edv
df = edv.sample_df()

total = df["销售额"].sum() / 1e6  # 换算成百万元
chart = edv.gauge(
    total, label="累计销售额（百万元）",
    min=0, max=20, fmt="raw", unit=" 百万",
    title="全年销售额完成度", subtitle="目标 2000 万",
    height=320,
)
chart.save("examples/output/gauge_5.html")
```

**输出**：
- 先把 DataFrame 聚合成单个数值（百万元），再交给 gauge。
- gauge 不接受 DataFrame，聚合要在 pandas 侧完成（或用 kpi 的数字样式）。
- 读数直接显示数值 + 单位后缀。

**验证**：`chart.spec["rows"]` 不存在（gauge 不走 data 管线），但 `chart.spec["value"]` 与计算值一致。

## 常见问题 / 注意事项

- **gauge 能直接传 DataFrame 吗？** 不能。gauge 只接受单个数值，传 DataFrame 会报「gauge 接受单个数值…」的 TypeError。 先聚合：`value=df["销售额"].sum()`；需要卡片样式和 delta/target/spark 时用 `kpi(df, value=...)`。
- **为什么 gauge 的 fmt/theme/height 非法值不报错？** gauge 不走 `_base_spec` 公共校验，参数直接写入 spec，前端对未知值退化为默认行为。 这是已知的实现不一致，写代码时请自行保证取值合法。
- **如何显示完成率百分比？** 自己算「实际/目标×100」后传入，并 `fmt="percent"`；`percent` 只加 % 号，不乘 100。 不要直接传 0.87 再指望显示 87%，那样会显示 0.87%。
- **一个页面放多个 gauge 怎么排？** 用 Dashboard 组合，或自己写 HTML 布局；gauge 的 height 建议统一为 240~300。 多个 gauge 的 min/max 口径要一致，否则视觉上不可比。

## 相关图表

- `kpi`：数字卡片，可带 delta/target/迷你走势，比 gauge 信息更密。
- `bar`：多个指标之间的精确对比。
- `line`：指标随时间的变化趋势。
