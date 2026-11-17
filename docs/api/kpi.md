# `kpi` — KPI 数字卡片

> 把单个聚合指标做成卡片：大号数值 + 指标名 + 环比/同比 + 目标达成 + 迷你走势，是驾驶舱顶部的指标头。
> 适合：看板核心指标、同比环比、目标达成率、需要随联动筛选自动重算的汇总数。
> 不适合：多值比较（用 bar）、趋势细节（用 line）、单个完成度仪表（用 gauge）。

## 函数签名

```python
eazy_data_viz.kpi(
    data=None,
    value=None,
    agg="sum",
    label=None,
    fmt=None,
    delta=None,
    delta_label=None,
    inverse=False,
    target=None,
    target_label=None,
    spark=None,
    spark_x=None,
    hint=None,
    unit=None,
    prefix=None,
    accent=0,
    height=150,
    theme="light",
    title=None,
    subtitle=None,
    link=None,
    section=None,
) -> Chart
```

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `None` | 否 | DataFrame 或直接传数值 |
| `value` | `str \| float` | `None` | 否 | 要聚合的数值列 |
| `agg` | `str` | `'sum'` | 否 | 聚合方式，默认 sum |
| `label` | `str` | `None` | 否 | 指标名 |
| `fmt` | `str` | `None` | 否 | 数字格式，默认 compact |
| `delta` | `float \| None` | `None` | 否 | 涨跌幅（比例或绝对值） |
| `delta_label` | `str \| None` | `None` | 否 | 涨跌幅口径，如同比/环比 |
| `inverse` | `bool` | `False` | 否 | 越小越好时下降显绿 |
| `target` | `float \| None` | `None` | 否 | 目标值，显示达成率与进度条 |
| `target_label` | `str \| None` | `None` | 否 | 目标标签，默认“目标” |
| `spark` | `str \| None` | `None` | 否 | 迷你走势数值列 |
| `spark_x` | `str \| None` | `None` | 否 | 迷你走势横轴列 |
| `hint` | `str \| None` | `None` | 否 | 底部说明小字 |
| `unit` | `str` | `None` | 否 | 数值后缀 |
| `prefix` | `str \| None` | `None` | 否 | 数值前缀 |
| `accent` | `int` | `0` | 否 | 强调色序号 |
| `height` | `int` | `150` | 否 | 卡片高度（默认 150） |
| `theme` | `str` | `'light'` | 否 | light / dark |
| `title` | `str \| None` | `None` | 否 | 标题（静态数值时兼作 label 回退） |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `link` | `str` | `None` | 否 | 联动组名，筛选时重算 |
| `section` | `str \| None` | `None` | 否 | 看板分区标题 |

## 参数详解

### `data` — DataFrame 或直接传数值（`pandas.DataFrame | dict | list | Series`，默认 `None`）

- **作用**：两种形态：传 DataFrame 时配合 `value` 聚合出指标；传 int/float 时直接作为静态值（此时 `value` 必须为 None，且不做数据管线）。 布尔值不算数值；传 `True` 会走 DataFrame 分支并报类型错误。 静态数值模式下 `spark`/`spark_x` 没有数据可用于走势，即使传了也不会画线。
- **建议**：看板联动重算用 DataFrame；固定展示的历史数字用静态值。 静态数值建议配 label/fmt/delta/target 使用。
- **示例**：`kpi(df, value="销售额") 或 kpi(1630000, label="销售额")`
- **报错**：`kpi()` → `ValueError: kpi 需要数据：kpi(df, value="销售额") 或 kpi(1630000, label="销售额")。`；传 bool → `TypeError: 无法识别 data 类型 'bool'，请传入 pandas.DataFrame（或 dict / list）。`

### `value` — 要聚合的数值列（`str | float`，默认 `None`）

- **作用**：从 DataFrame 取数时，按 agg 聚合该列得到卡片数值。 省略时仅当 DataFrame 恰好只有一个数值列才自动选用，否则报错要求显式传。 列不存在抛 KeyError；文本列会在 prepare 阶段转数值或报错。
- **建议**：多指标页面每个 kpi 传不同 value；列名用反引号或原始中文列名。
- **示例**：`value="销售额"`
- **报错**：`value=None` 且多数值列 → `ValueError: kpi 需要指定 value 列，例如 kpi(df, value="销售额")。`；列名错 → `KeyError: "value列 'XX' 不存在。当前可用的列有：..."`

### `agg` — 聚合方式（`str`，默认 `'sum'`）

- **作用**：同一筛选范围内把 value 聚合成一个数：sum 合计、mean 均值、count 计数、max/min/median 等。 count 会统计非空记录数；与 value 一起用时按 value 列的非空值计数。 联动筛选后，KPI 会按当前筛选范围用同一 agg 重算。
- **建议**：金额/数量用 sum；比率/客单价用 mean；记录量用 count。
- **示例**：`agg="mean"`
- **报错**：`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median`

### `label` — 指标名（显示在数值上方）（`str`，默认 `None`）

- **作用**：卡片主标签，通常是指标中文名。 静态数值（data 为数字）且未传 label 时，会用 `title` 作为 label。
- **建议**：6~10 个字；口径说明放 hint 或 delta_label。
- **示例**：`label="全年销售额"`

### `fmt` — 数字格式（`str`，默认 `None`）

- **作用**：`None` 时按 compact 处理；可选 compact（163万）、thousands（1,630,000）、raw、percent（12.8%）、currency（¥1,630,000.00）。 percent 只加 % 号不乘 100；currency 固定两位小数。 传入非法值会报错（kpi 会校验 fmt，但仅在非 None 时）。
- **建议**：金额用 currency 或 compact；百分比指标用 percent。 需要完整数字用 thousands。
- **示例**：`fmt="currency"`
- **报错**：`fmt="money"` → `ValueError: fmt='money' 不支持，可选：compact, thousands, raw, percent, currency`

### `delta` — 涨跌幅（比例或绝对值）（`float | None`，默认 `None`）

- **作用**：传 -1~1 之间的小数时按比例显示：0.128 → ▲12.8%；传 12.8 这类绝对值时按原样显示。 正数显示向上箭头，负数向下；配合 `inverse=True` 反转颜色语义。 delta 只影响展示，不会自动计算同比——需要自己算好再传。
- **建议**：同比/环比用小数比例；没有比较基准时不要硬编。
- **示例**：`delta=0.128`

### `delta_label` — 涨跌幅口径说明（`str | None`，默认 `None`）

- **作用**：显示在涨跌幅旁边的文字，例如「同比」「环比」「较上月」。默认不显示说明。
- **建议**：明确口径，避免“涨了 12.8%”被误解为绝对值。
- **示例**：`delta_label="同比"`

### `inverse` — 越小越好时下降显绿（`bool`，默认 `False`）

- **作用**：默认上升红/下降绿；`inverse=True` 反转为上升绿/下降红，适合成本、退货率、投诉率等逆向指标。 只改颜色，不改数值或箭头方向。
- **建议**：成本、时长、缺陷率类指标打开。
- **示例**：`inverse=True`

### `target` — 目标值（显示达成率与进度条）（`float | None`，默认 `None`）

- **作用**：传入数字后，卡片右上角显示达成率百分比，底部显示进度条；`target_label` 控制标签文字。 target 必须是 int/float；字符串（如 "200万"）会报错。 达成率 = 当前值 / target × 100%（前端计算，target 为 0 时需自行避免）。
- **建议**：目标与 value 同量纲；target 大于 0。
- **示例**：`target=2000000`
- **报错**：`target="200万"` → `ValueError: target 需要是数字（目标值），收到 '200万'`

### `target_label` — 目标标签（`str | None`，默认 `None`）

- **作用**：目标徽标上的文字，例如「年度目标」「预算」。不传时前端显示「目标」。
- **建议**：短词；与 target 一起使用。
- **示例**：`target_label="年度目标"`

### `spark` — 迷你走势数值列（`str | None`，默认 `None`）

- **作用**：在卡片右下角画一条无坐标轴的走势线，帮助看指标随时间的形状；必须同时给 `spark_x`。 spark 与 value 可以相同（看该指标自身的走势），也可以不同（例如主指标销售额、走势客单价）。 静态数值模式没有数据行，spark 不会生效。
- **建议**：spark_x 用月份/日期等有序列；类别太多时先聚合。
- **示例**：`spark="销售额"`
- **报错**：只传 spark 不传 spark_x → `ValueError: 带迷你走势的 KPI 需要 spark_x（横轴列），例如 kpi(df, value="销售额", spark="销售额", spark_x="月份")。`

### `spark_x` — 迷你走势横轴列（`str | None`，默认 `None`）

- **作用**：走势线的横轴列；按它分组后用 agg 聚合 spark，形成迷你折线。 必须是 df 的列；不存在会报 KeyError。
- **建议**：月份、日期等有序维度；建议去重后 6~20 个点。
- **示例**：`spark_x="月份"`
- **报错**：列名错 → `KeyError: "spark_x列 'XX' 不存在。当前可用的列有：..."`

### `hint` — 底部说明小字（`str | None`，默认 `None`）

- **作用**：卡片底部一行灰色小字，常用于写口径、时间范围、备注。
- **建议**：一行短句，例如「2024 全年 · 含税」。
- **示例**：`hint="2024 全年 · 含税"`

### `unit` — 数值后缀（`str`，默认 `None`）

- **作用**：拼在格式化数值后面的单位，例如 %、人、单；与 fmt 的 %/¥ 不冲突但注意不要重复。
- **建议**：1~2 个字符；百分比指标若 fmt=percent 就不要再加 %。
- **示例**：`unit="人"`

### `prefix` — 数值前缀（`str | None`，默认 `None`）

- **作用**：拼在数值前面的符号或文字，例如 ≈、≥、约。
- **建议**：用于强调近似值或下限。
- **示例**：`prefix="≈"`

### `accent` — 强调色序号（0 起）（`int`，默认 `0`）

- **作用**：取当前配色库中第 accent 个颜色用于走势线/进度条等强调元素；默认 0。 必须是 >=0 的整数（bool 与负数报错）；超过色板长度时前端取模。
- **建议**：一屏多卡时用不同 accent 区分，但主色仍建议统一。
- **示例**：`accent=2`
- **报错**：`accent=-1` → `ValueError: accent 需要是 >=0 的整数（配色序号），收到 -1`

### `height` — 卡片高度（`int`，默认 `150`）

- **作用**：默认 150，最小 120；有 spark/target/hint 时建议 170~200。
- **建议**：驾驶舱一行多卡用 150~170；单独大卡用 200。
- **示例**：`height=180`
- **报错**：`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `theme` — 主题（light / dark）（`str`，默认 `'light'`）

- **作用**：`"light"`（默认）浅色背景；`"dark"` 深色背景，坐标轴、文字、图例颜色自动反转。 主题只影响配色与背景，不改变图表结构；与其他图混排时建议统一主题。
- **建议**：大屏/深色看板用 `dark`；报告导出用 `light`。 自定义色板（`chart.palette(...)`）在两种主题下都会生效。
- **示例**：`theme="dark"`
- **报错**：`theme="blue"` → `ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `title` — 标题（静态数值时兼作 label 回退）（`str | None`，默认 `None`）

- **作用**：卡片标题；静态数值模式下若没传 label，会用 title 当 label。 与 label 同时存在时分别显示。
- **建议**：通常留空，让 label 承担指标名；需要大标题时再传。
- **示例**：`title="核心指标"`

### `subtitle` — 副标题（灰字说明）（`str | None`，默认 `None`）

- **作用**：显示在主标题下方的小号灰字，常用于写口径、数据范围或时间区间。 不传时不显示；与 `title` 各自独立，可以只传 subtitle。
- **建议**：写清统计口径，例如「2024 年 1~12 月，含税」。 保持一行，过长会被画布截断。
- **示例**：`subtitle="2024 全年，按订单日期统计"`

### `link` — 联动组名（同组图表互相筛选）（`str`，默认 `None`）

- **作用**：把多个图表放进同一个联动组：点击某图的类目后，同组其它图表按该维度过滤并重算；再次点击同一类目取消筛选。 联动依据是点击项的名称（x 类目）；点“其他”不触发联动。 需要在 Dashboard/HTML 页面里才真正生效，单独导出单个图表时只记录参数。
- **建议**：同一页面里所有要联动的图必须传完全相同的字符串，例如都写 `link="销售"`。 散点/热力图的点击联动依赖数据点名称，当前版本可能不生效（已在自检记录中标注）。
- **示例**：`link="销售"`

### `section` — 看板分区标题（`str | None`，默认 `None`）

- **作用**：仅 dashboard 使用：把 KPI 归入某个分区，页面按 section 分组显示。 单独保存 HTML 时该字段只是写进 spec。
- **建议**：与同页图表使用一致的分区名。
- **示例**：`section="总览"`

## 返回值

所有图表函数都返回 `eazy_data_viz.Chart` 对象：`chart.spec` 是 JSON 可序列化的完整渲染配置，`chart.data` 是实际参与绘图的数据，`chart.warnings` 记录采样/丢列等降级提示；`save()` / `to_html()` / `palette()` / `show()` 的通用用法见 [交互与联动指南](../guides/06-interaction.md)。

本图的 `spec` 额外包含：

- `roles`：`{"value": value 列}`（静态数值模式为 `{}`）；`xtitle`/`ytitle`/`xlim`/`ylim`/`legend`/`labels`/`zoom` 均固定为 None/False。
- `spec` 额外包含：`value`（静态值或 None）、`label`、`delta`、`deltaLabel`、`inverse`、`target`、`targetLabel`、`spark`、`hint`、`unit`、`prefix`、`accent`、`section`。
- kpi 没有 `max_rows` 参数（固定使用公共 MAX_ROWS），也没有 `xlim`/`ylim`/`labels`/`zoom`/`drill`。

## 完整示例

以下示例都基于 `edv.sample_df()`，可直接复制运行（在仓库根目录执行）；所有输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法：聚合销售额

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.kpi(df, value="销售额")
chart.save("examples/output/kpi_1.html")
```

**输出**：
- 卡片显示 1500 行销售额的 sum（compact 格式，例如 163万）。
- 默认 `agg="sum"`、`fmt="compact"`、`height=150`；无 label 时数值上方为空。
- `spec["rows"]` 为 1500（DataFrame 模式走数据管线），link 为空不可联动。

**验证**：卡片数值 == `df["销售额"].sum()`；`chart.spec["agg"] == "sum"`。

### 示例 2：指标名 + 金额格式

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.kpi(
    df, value="销售额",
    label="全年销售额", fmt="currency",
    hint="2024 全年 · 含税",
)
chart.save("examples/output/kpi_2.html")
```

**输出**：
- 卡片上方显示「全年销售额」，数值显示 ¥1,630,000.00 这类两位小数金额。
- 底部 hint 显示口径小字。
- `fmt="currency"` 使用 ¥ 符号与千分位。

**验证**：`chart.spec["label"] == "全年销售额"`；`chart.spec["fmt"] == "currency"`。

### 示例 3：同比涨跌：delta + delta_label

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.kpi(
    df, value="销售额",
    label="销售额", fmt="compact",
    delta=0.128, delta_label="同比",
    hint="较去年同期",
)
chart.save("examples/output/kpi_3.html")
```

**输出**：
- 数值旁显示 ▲12.8% 与「同比」。
- delta 传小数比例时按 ×100% 显示；正数向上、颜色默认红。
- 卡片高度默认 150 即可容纳数值与涨跌。

**验证**：`chart.spec["delta"] == 0.128`；`deltaLabel == "同比"`。

### 示例 4：强调色 + 分区 + 联动

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.kpi(
    df, value="订单数", agg="sum",
    label="总订单数", fmt="thousands", unit=" 单",
    accent=2, section="总览", link="销售",
    hint="联动组：销售",
)
chart.save("examples/output/kpi_4.html")
```

**输出**：
- 数值千分位显示并带「单」后缀；强调色取色板第 3 个颜色。
- `section="总览"` 供 dashboard 分区；`link="销售"` 让 KPI 跟随同组图表筛选重算。
- 单图保存时 link 只写入 spec。

**验证**：`chart.spec["accent"] == 2`；`chart.spec["section"] == "总览"`；`link == "销售"`。

### 示例 5：深色主题 + 标题 + 高度

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.kpi(
    df, value="客户数", agg="sum",
    label="累计客户数", unit=" 人", fmt="thousands",
    title="客户规模", subtitle="截至 2024-12-31",
    theme="dark", height=190, accent=1,
)
chart.save("examples/output/kpi_5.html")
```

**输出**：
- 深色卡片，数值与标题切换为浅色文字。
- `title` 与 `label` 同时存在时都有显示，适合分组标题 + 指标名。
- `height=190` 比默认更高，适合单独强调。

**验证**：`chart.spec["theme"] == "dark"`；`height == 190`。

## 常见问题 / 注意事项

- **kpi 的数值是怎么算出来的？** DataFrame 模式下：先按联动/筛选条件取子集，再对 value 列执行 agg（默认 sum）得到一个数；静态数值模式下直接用传入的数。 卡片下方的 tooltip/副标题不会自动带出口径，请用 hint 写清。
- **为什么 spark 没画出来？** 常见原因：只传了 spark 没传 spark_x（会直接报错）；或 data 是静态数值，没有数据行；或 spark_x 不是有序列导致走势无意义。 另外 min/max 范围内的数值太少时前端会退化为空白，检查 `chart.data["rows"]`。
- **delta 会自动计算同比吗？** 不会。delta 是展示参数，需要先用 pandas 算好同比/环比再传入。 传 0.128 显示 12.8%，传 12.8 显示 12.8%（按绝对值处理）。
- **target 达成率怎么算？** 前端按「当前值 / target」计算并格式化为百分比；target=0 时会异常，请保证目标为正数。 如果 value 是逆向指标，达成率语义要自己确认（目标越低越好时不要用 target 进度条）。
- **一个页面多个 KPI 如何对齐？** 用 `edv.dashboard(kpi1, kpi2, bar, cols=3)` 组合；每张卡的 height 保持一致，accent 可取不同序号。 所有 KPI 的 fmt/unit 口径要统一，否则数字大小无法横向比较。

## 相关图表

- `gauge`：单个完成度的仪表盘可视化。
- `bar`：拆解 KPI 由哪些类目构成。
- `line`：看 KPI 的时间趋势细节。
- `combo`：柱线混合展示两个相关指标。
