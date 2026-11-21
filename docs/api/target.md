# `target` — 目标对比图：实际值柱 + 目标值虚线

> 柱子是实际值，每个类目上方一条虚线标出目标，tooltip 里同时给出达成率；比 `bullet` 更强调“目标是一条线”，适合扫一眼看哪些类目越线。
> 适合：销售额 vs 预算、产量 vs 计划、门店 vs 配额、月度实际 vs 月度目标。
> 不适合：单指标完成率的仪表盘（用 `gauge`）、目标是一根竖线刻度的紧凑布局（用 `bullet`）、看目标的历史走势（用 `line` 双系列）。

## 函数签名

```python
def target(
    data,
    x,
    actual,
    target=None,
    *,
    target_value=None,
    agg="sum",
    sort=None,
    top_n=None,
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    xlim=None,
    ylim=None,
    fmt="compact",
    height=380,
    theme="light",
    legend=True,
    labels=False,
    zoom="auto",
    drill=None,
    link=None,
    max_rows=200000,
) -> "Chart":
    ...
```

> `data` / `x` / `actual` / `target` 是位置参数，其余全部是**关键字限定参数**（`*` 之后必须写成 `参数名=值`）。
> 参数个数 23：4 个位置参数 + 19 个关键字参数。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源，图表取数的唯一入口 |
| `x` | `str` | `—` | 是 | 类目列名（画在横轴） |
| `actual` | `str` | `—` | 是 | 实际值数值列（柱高） |
| `target` | `str \| float` | `None` | 否 | 目标值：列名或一个常数 |
| `target_value` | `float` | `None` | 否 | 目标常数，优先级高于 `target` |
| `agg` | `str` | `'sum'` | 否 | 实际值/目标列的聚合方式 |
| `sort` | `str` | `None` | 否 | 排序：x / asc / desc / none |
| `top_n` | `int` | `None` | 否 | 只保留前 N 项（当前版本不裁剪，见详解） |
| `title` | `str \| None` | `None` | 否 | 主标题，默认自动生成 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题（灰色小字） |
| `xtitle` | `str \| None` | `None` | 否 | 类目轴（横轴）标题 |
| `ytitle` | `str \| None` | `None` | 否 | 数值轴（纵轴）标题 |
| `xlim` | `tuple[float, float]` | `None` | 否 | 类目轴范围（本图不生效） |
| `ylim` | `tuple[float, float]` | `None` | 否 | 数值轴范围 |
| `fmt` | `str` | `'compact'` | 否 | 数值格式：compact / thousands / raw / percent / currency |
| `height` | `int` | `380` | 否 | 画布高度（像素，≥120） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `str` | `'light'` | 否 | light / dark |
| `legend` | `bool` | `True` | 否 | 是否显示图例 |
| `labels` | `bool` | `False` | 否 | 是否在柱顶标数值 |
| `zoom` | `bool \| str` | `'auto'` | 否 | 缩放条（本图不支持） |
| `drill` | `str \| list[str]` | `None` | 否 | 逐级下钻维度 |
| `link` | `str` | `None` | 否 | 联动组名（同组图表互相筛选） |
| `max_rows` | `int` | `200000` | 否 | 最大参与绘制行数（None 不采样） |

## 参数详解

### `data` — 数据源，图表取数的唯一入口（必填）

- **类型 / 默认值**：`pandas.DataFrame`、`dict`、`list`（每项一行）或 `Series` / 无
- **说明**：经 `frame.ensure_frame()` 归一化成 DataFrame；行数超过 `max_rows` 时均匀抽样并提示。
- **取值建议**：实际值与目标值最好在同一张表；如果目标在另一张表，先在 pandas 里 merge 好再传。
- **报错**：`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`；`data=42` → `TypeError: 无法识别 data 类型 'int'，请传入 pandas.DataFrame（或 dict / list）。`

### `x` — 类目列名（必填）

- **类型 / 默认值**：`str` / 无
- **说明**：每根柱子对应一个类目，画在横轴；同一 `x` 的多行先按 `agg` 聚合实际值与目标值。
- **取值建议**：类目 4~12 个最合适；类目多时柱子变细、目标虚线容易看不清。有序类目（月份）配合 `sort="x"` 使用。
- **报错**：不传 → `TypeError: target() missing 1 required positional argument: 'x'`；列名写错 → `KeyError: "x（类目）列 '不存在' 不存在。当前可用的列有：日期, 月份, 大区, 省份, 城市, 产品, 渠道, 销售额, 订单数, 利润, 客户数"`

### `actual` — 实际值数值列（必填）

- **类型 / 默认值**：`str` / 无
- **说明**：柱子的高度来源；与目标值一起决定 tooltip 里的“达成率”（实际 / 目标 × 100%，目标为 0 时不显示）。
- **取值建议**：与目标值同量纲、同口径；可加指标用 `agg="sum"`，比率型指标用 `agg="mean"`。
- **报错**：文本列 → `TypeError: y（数值）列 '产品' 需要是数值类型（当前是文本，例如 ['智能终端', '云服务', '行业软件']）。请先用 pd.to_numeric() 清洗，或换一列。`

### `target` — 目标值：列名或常数

- **类型 / 默认值**：`str` 或 `float`（`int` 也可以） / `None`
- **说明**：只有两种合法用法：
  - 传 **数字**（`int` / `float`，且不是 `bool`）：等价于 `target_value=该数字`，所有类目共用同一个目标；
  - 传 **字符串**：当作列名，按 `agg` 聚合后作为每个类目的目标（可以逐类目不同）。
  - 同时传了 `target` 和 `target_value` 时，**`target_value` 优先**。
- **取值建议**：全公司统一预算用常数；逐区域/逐月目标写在数据列里。注意 `bool` 会被当成列名（`target=True` → `KeyError: target（目标值）列 True 不存在`）。
- **示例**：`target=500000`（所有类目统一 50 万）；`target="目标销售额"`（列名）

### `target_value` — 目标常数（优先级更高）

- **类型 / 默认值**：`float` / `None`
- **说明**：统一目标值。前端在“该行没有目标列取值”时用它兜底，因此当 `target` 传列名、但某些类目缺目标时，缺失项会落到 `target_value`；两者都传时 `target_value` 覆盖列值。非数字字符串会被静默吞成 `None`（图仍能画，目标按 0 处理），不会报错。
- **取值建议**：统一目标用 `target_value=`；逐类目目标用 `target="列名"`，不要同时传两个（否则列值被覆盖）。
- **示例**：`target_value=500000` → `chart.spec["targetValue"] == 500000.0`；`target_value="abc"` → `None`（不报错，需自行校验）

### `agg` — 聚合方式

- **类型 / 默认值**：`str` / `'sum'`
- **说明**：`actual` 与 `target` 列分别按 `x` 聚合，同一个 `agg` 同时作用于两者。可选 `sum` / `mean` / `count` / `max` / `min` / `median`。
- **取值建议**：金额、销量用 `"sum"`；达成率/单价类指标用 `"mean"`，否则求和后达成率会失真。目标列与实际列口径必须一致。
- **报错**：`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median`

### `sort` — 类目顺序

- **类型 / 默认值**：`str` / `None`
- **说明**：`"x"` 按类目本身排序，`"asc"` / `"desc"` 按**实际值**排序，`None` 保持聚合顺序。非法值不报错。
- **取值建议**：看完成情况排行用 `"desc"`；看月度进度用 `sort="x"` 配合有序月份。
- **示例**：`sort="desc"` → 销售额最高的类目排最左

### `top_n` — 只保留前 N 项（当前版本不裁剪）

- **类型 / 默认值**：`int` / `None`
- **说明**：只做合法性校验并写入 `spec["topN"]`。**1.0.0 中目标图的前端构建器不读取 `spec.topN`，本参数不会减少柱子数**。
- **取值建议**：先过滤数据再画。
- **报错**：`top_n=0` → `ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`

### `title` — 主标题

- **类型 / 默认值**：`str` / `None`
- **说明**：不传时自动生成「<actual 列名> 目标对比」；传 `""` 得到空标题（不回落自动）。
- **取值建议**：写清“什么对比什么目标”，例如 `"各月销售额 vs 月度目标"`。
- **示例**：`title=None` → `chart.spec["title"] == "销售额 目标对比"`

### `subtitle` — 副标题

- **类型 / 默认值**：`str` / `None`
- **说明**：标题下方的小字说明，默认没有。
- **取值建议**：注明目标的口径与来源（“预算”“去年同期 ×1.1”）。
- **示例**：`subtitle="目标 = 2024 年度预算（含税）"`

### `xtitle` — 类目轴（横轴）标题

- **类型 / 默认值**：`str` / `None`
- **说明**：不传时用 `x` 列名；传 `""` 隐藏。
- **取值建议**：类目名已自明时传 `""`，给底部标签留空间。
- **示例**：`xtitle="月份"`；`xtitle=""` → 横轴无标题

### `ytitle` — 数值轴（纵轴）标题

- **类型 / 默认值**：`str` / `None`
- **说明**：不传时用 `actual` 列名；传 `""` 隐藏。
- **取值建议**：写上单位，如 `"销售额（元）"`。
- **示例**：`ytitle="销售额（元）"`

### `xlim` — 类目轴范围（本图不生效）

- **类型 / 默认值**：`tuple[float, float]` / `None`
- **说明**：横轴是类目轴，`xlim` 只写入 `spec["xlim"]`，不改变画面；格式错误仍会报错。
- **取值建议**：本图不需要；数值范围请用 `ylim`。
- **报错**：`xlim=(0,)` → `ValueError: xlim 需要是 (最小值, 最大值) 两元组，例如 xlim=(0, 100)`

### `ylim` — 数值轴范围

- **类型 / 默认值**：`tuple[float, float]` / `None`
- **说明**：固定纵轴范围，**本图生效**；内部把 `(lo, hi)` 交换成 `[lo, hi]`。
- **取值建议**：用 `(0, 目标最大值 × 1.1)` 让目标虚线位于柱子上方、留出视觉余量；多图并排时统一 `ylim` 便于比较。
- **示例**：`ylim=(0, 600000)`

### `fmt` — 数值格式

- **类型 / 默认值**：`str` / `'compact'`
- **说明**：作用于纵轴刻度、`labels` 与 tooltip（实际值、目标值）。可选 `compact` / `thousands` / `raw` / `percent` / `currency`；`fmt=None` 按 `compact` 处理。
- **取值建议**：金额用 `"thousands"` 或 `"currency"`；比率场景用 `"percent"`。
- **报错**：`fmt="cn"` → `ValueError: fmt='cn' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）

- **类型 / 默认值**：`int` / `380`
- **说明**：最小 120；传 `None` 回落到 380。
- **取值建议**：类目 4~8 用 380；10 个以上用 460~560。
- **报错**：`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题

- **类型 / 默认值**：`str` / `'light'`
- **说明**：`"light"` / `"dark"`，控制背景、文字、柱色与目标虚线颜色。
- **取值建议**：深色大屏用 `"dark"`；目标虚线在深底下用较亮的副文本色，仍可见。
- **报错**：`theme="night"` → `ValueError: theme 只支持 "light" / "dark"，收到 'night'`

### `legend` — 是否显示图例

- **类型 / 默认值**：`bool` / `True`
- **说明**：**本图生效**，图例显示“实际值（柱）”与“目标值（虚线）”两项；默认开启，因为目标值需要靠图例说明。
- **取值建议**：单图展示且标题已说明时可用 `False` 省空间；多图并排建议保留。
- **示例**：`legend=False` → 图例隐藏

### `labels` — 是否在柱顶标数值

- **类型 / 默认值**：`bool` / `False`
- **说明**：**本图生效**，只标柱子的实际值（目标虚线上不标）。类目多时容易重叠。
- **取值建议**：类目 ≤10 且需要直接读数时开启；否则用 tooltip（tooltip 同时给实际、目标、达成率）。
- **示例**：`labels=True` → 每根柱顶显示实际值

### `zoom` — 缩放条（本图不支持）

- **类型 / 默认值**：`bool` / `str` / `'auto'`
- **说明**：只有核心笛卡尔图消费 `spec.zoom`；**目标图构建器不读取该字段**，`"auto"` 也不会自动加缩放条。
- **取值建议**：类目多时先聚合或截取区间。
- **示例**：`zoom=True` → `chart.spec["zoom"] is True`，画面无缩放条。

### `drill` — 逐级下钻维度

- **类型 / 默认值**：`str` 或 `list[str]` / `None`
- **说明**：点击某根柱子后按该类目名过滤数据并重算（实际柱与目标虚线一起重算）；点「返回」回退。传字符串自动转列表；`drill[0]` 与 `x` 不同时自动把 `x` 插到最前。
- **取值建议**：从粗到细 2~3 层；注意下钻后目标值也跟着变化。
- **报错**：`drill=[]` → `ValueError: drill 不能是空列表；不需要下钻请传 drill=None。`；列名不存在 → `KeyError: "下钻维度列 '不存在' 不存在。……"`

### `link` — 联动组名

- **类型 / 默认值**：`str` / `None`
- **说明**：同 `link` 组的图表互相联动：点击某类目把名字广播给组内其它图，它们按同名列过滤重算。
- **取值建议**：与同页趋势图、明细表统一命名，如 `link="month"`。
- **示例**：`link="month"`；`chart.spec["link"] == "month"`

### `max_rows` — 最大参与绘制行数

- **类型 / 默认值**：`int` / `200000`
- **说明**：超过则等间隔均匀抽样，warning 写入 `chart.warnings["warnings"]`，`chart.data["n_total"]` 保留原始行数；`None` 关闭采样。
- **取值建议**：目标图通常只画聚合后的类目，建议先 `groupby` 再传；明细行抽样会让实际值与目标值一起变动。
- **示例**：`max_rows=100` → `chart.data["n"] == 100`

## 返回值

所有图表函数都返回 `eazy_data_viz.Chart` 对象（`chart = edv.target(df, x="月份", actual="销售额", target_value=140000)`）。

**Chart 的属性**

- `chart.spec`：`dict`，前端 ECharts 配置（JSON 可序列化）。公共键有 `id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`、`roles`、`agg`、`fmt`、`sort`、`topN`、`xtitle`、`ytitle`、`xlim`、`ylim`、`legend`、`labels`、`zoom`、`drill`、`link`，本图额外带 `targetValue`。
- `chart.data`：**`dict`**，不是 DataFrame。含 `cols`、`rows`、`dims` / `measures` / `kinds`、`orders`、`n`、`n_total`。
- `chart.data_ref`：数据引用 id（`d-` + 12 位 sha1）。
- `chart.warnings`：**`dict`**，形如 `{"warnings": [...], "n_total": 1500}`。
- `chart.title`：只读属性，等价于 `chart.spec["title"]`。

**Chart 的方法**

- `chart.save(path, inline=True)`：写出单文件 HTML（约 1.2~1.5 MB），自动建目录，返回绝对路径。
- `chart.to_html(inline=True)`：返回完整 HTML 字符串；`inline=False` 引用外部资源。
- `chart.show(open_browser=None)`：浏览器打开；Jupyter / Streamlit 自动内嵌。
- `chart.palette(name)`：切换配色并返回 `self`；可选 `google`、`antd`、`tableau`、`carbon`、`echarts`、`morandi`、`tailwind`。

**本图 `spec` 的真实结构**

```json
{ "id": "c1", "type": "target", "title": "销售额 目标对比", "subtitle": null, "theme": "light",
  "height": 380, "dataRef": "d9465273f71af", "roles": {"x": "月份", "y": "销售额", "target": null},
  "agg": "sum", "targetValue": 140000.0, "sort": null, "topN": null, "xtitle": null,
  "ytitle": null, "xlim": null, "ylim": null, "fmt": "compact", "legend": true, "labels": false,
  "zoom": "auto", "drill": null, "link": null }
```

**验证返回值的小技巧**

```python
import eazy_data_viz as edv
df = edv.sample_df()
chart = edv.target(df, x="月份", actual="销售额", target_value=140000)
assert chart.spec["type"] == "target"
assert chart.spec["targetValue"] == 140000.0
assert chart.spec["legend"] is True
print(chart.warnings, len(chart.to_html()))
```

## 完整示例

以下示例都基于 `edv.sample_df()`（1500 行 × 11 列），可直接复制运行；输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法：统一月度目标 14 万

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.target(df, x="月份", actual="销售额", target_value=140000)
chart.save("examples/output/target_1.html")
```

**输出**：自动标题「销售额 目标对比」；12 根柱子（月份合计，5 月最高 174,919），一条虚线横在 14 万处；高于虚线的月份是 3 月、4 月、5 月、6 月、7 月等（113,745 的 1 月低于线）。
**验证**：`chart.spec["targetValue"] == 140000.0`、`chart.spec["roles"]["target"] is None`。

### 示例 2：目标写成列：逐月不同目标

```python
import eazy_data_viz as edv
df = edv.sample_df()

df["月度目标"] = 120000
chart = edv.target(
    df, x="月份", actual="销售额", target="月度目标",
    sort="x", fmt="thousands", ytitle="销售额（元）",
    title="月度销售额 vs 月度目标", subtitle="目标 = 12 万 / 月",
)
chart.save("examples/output/target_2.html")
```

**输出**：每个月的目标都是 12 万，虚线在整张图上是一条水平折线；`roles["target"]` 变成列名「月度目标」，`targetValue` 为 `None`。
**验证**：`chart.spec["roles"]["target"] == "月度目标"`、`chart.spec["targetValue"] is None`。

### 示例 3：排序 + 柱标 + 固定上限

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.target(
    df, x="大区", actual="销售额", target_value=500000,
    sort="desc", labels=True, ylim=(0, 650000), fmt="thousands",
    title="大区销售额达成", subtitle="目标 50 万 / 大区",
)
chart.save("examples/output/target_3.html")
```

**输出**：按实际销售额从高到低（华东 582,864 → 华北 → 华南 → 西部）；纵轴固定 0~65 万；华东柱越过 50 万目标线，其余三个大区在目标线以下。
**验证**：`chart.spec["sort"] == "desc"`、`chart.spec["ylim"] == [0.0, 650000.0]`。

### 示例 4：`target` 与 `target_value` 同时传：后者优先

```python
import eazy_data_viz as edv
df = edv.sample_df()

df["目标列"] = 100000
c1 = edv.target(df, x="大区", actual="销售额", target="目标列", target_value=300000)
c2 = edv.target(df, x="大区", actual="销售额", target=500000)
assert c1.spec["targetValue"] == 300000.0    # target_value 覆盖列值
assert c2.spec["targetValue"] == 500000.0    # 数字 target 自动转 target_value
chart = edv.target(df, x="大区", actual="销售额", target="目标列")
chart.save("examples/output/target_4.html")
```

**输出**：`target_value` 优先于 `target` 列；数字形式的 `target` 会被内部转成 `targetValue`；只传 `target="目标列"` 时虚线在 10 万处。
**验证**：三个 `assert` 都通过；`c1.spec["roles"]["target"] == "目标列"`。

### 示例 5：下钻 + 联动

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.target(
    df, x="大区", actual="销售额", target_value=600000,
    drill=["大区", "省份"], link="goal",
    title="大区销售额目标对比（可下钻）",
)
chart.save("examples/output/target_5.html")
```

**输出**：初始 4 个大区；点击柱子按该大区过滤并切到省份维度，实际值与目标线一起重算；同 `link="goal"` 的图表同步过滤。
**验证**：`chart.spec["drill"] == ["大区", "省份"]`、`chart.spec["link"] == "goal"`。

### 示例 6：边界：目标为 0 / 目标列有缺失

```python
import eazy_data_viz as edv
import numpy as np

df = edv.sample_df()
# 目标为 0：tooltip 不显示达成率，图仍可画
c1 = edv.target(df, x="大区", actual="销售额", target_value=0)
# 目标列部分缺失：缺失类目回落到 target_value（若为 None 则按 0 处理）
df["目标列"] = 200000.0
df.loc[df["大区"] == "西部", "目标列"] = np.nan
c2 = edv.target(df, x="大区", actual="销售额", target="目标列", target_value=300000)
chart = edv.target(df, x="大区", actual="销售额", target_value=400000, labels=True)
chart.save("examples/output/target_6.html")
```

**输出**：`target_value=0` 时所有虚线贴在 0 处；目标列缺失的西部回落到 `target_value=300000`，其余大区用列值 200,000。
**验证**：`c1.spec["targetValue"] == 0.0`、`c2.spec["targetValue"] == 300000.0`。

## 常见错误

### 1. 把 `target=True` 当成“统一目标”

```python
import eazy_data_viz as edv
df = edv.sample_df()
# 错误写法：bool 不是数字，会被当成列名
# edv.target(df, x="大区", actual="销售额", target=True)
# → KeyError: "target（目标值）列 True 不存在。当前可用的列有：日期, 月份, 大区, ..."
# 正确写法：用 target_value
chart = edv.target(df, x="大区", actual="销售额", target_value=500000)
```

**修法**：统一目标一律用 `target_value=`；`target=` 只接列名或纯数字（`bool` 会被当成列名）。

### 2. 目标列里混进了文本

```python
import eazy_data_viz as edv
df = edv.sample_df()
# 错误写法：目标列是 "50万" 这类文本
# df["目标"] = "50万"
# edv.target(df, x="大区", actual="销售额", target="目标")
# → TypeError: y（数值）列 '目标' 需要是数值类型……
# 正确写法：转成数字列
df["目标"] = 500000.0
chart = edv.target(df, x="大区", actual="销售额", target="目标")
```

**修法**：`pd.to_numeric(df["目标"], errors="coerce")` 清洗，或直接用数字常量列。

### 3. 指望 `labels` 在目标虚线上也标数值

```python
import eazy_data_viz as edv
df = edv.sample_df()
chart = edv.target(df, x="大区", actual="销售额", target_value=500000, labels=True)
# labels 只作用于柱子（实际值）；目标虚线上没有数字
assert chart.spec["labels"] is True
```

**修法**：目标值靠 tooltip 或图例说明；需要在图上常显目标数字时改用 `bar` 双系列或 `bullet`。

### 4. 用 `xlim` / `zoom` 调整画面

```python
import eazy_data_viz as edv
df = edv.sample_df()
chart = edv.target(df, x="大区", actual="销售额", target_value=500000,
                   xlim=(0, 300000), zoom=True, ylim=(0, 650000))
# 横轴是类目轴：xlim 不生效；zoom 未被构建器读取
assert chart.spec["xlim"] == [0.0, 300000.0]   # 只写进 spec
```

**修法**：数值范围用 `ylim`；类目太多先聚合或下钻。

## 相关图表

- `bullet`：目标是一根竖线刻度、横向布局的紧凑达成图。
- `bar`：不需要目标线、只比较实际值时用它。
- `gauge`：单指标完成率的仪表盘。
- `waterfall`：把“实际与目标的差额”拆成增减项。
- `pareto`：按贡献度排序、找重点类目。
