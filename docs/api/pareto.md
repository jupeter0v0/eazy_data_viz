# `pareto` — 帕累托图：按贡献排序的柱 + 累计占比线

> 柱子按数值从大到小排列，折线是“累计占比”；利用“二八法则”快速回答“哪几个类目贡献了 80%”。
> 适合：找出贡献最大的头部客户/产品/区域、质量问题归因（80% 的问题来自哪几类原因）、库存 ABC 分类。
> 不适合：比较类目之间的绝对大小（用 `bar`）、看占比构成（用 `pie`）、看时间趋势（用 `line`）。

## 函数签名

```python
def pareto(
    data,
    x,
    y=None,
    *,
    agg="sum",
    top_n=None,
    cum_fmt="percent",
    sort=None,
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    xlim=None,
    ylim=None,
    fmt="compact",
    height=400,
    theme="light",
    legend=False,
    labels=False,
    zoom="auto",
    drill=None,
    link=None,
    max_rows=200000,
) -> "Chart":
    ...
```

> `data` / `x` / `y` 是位置参数，其余全部是**关键字限定参数**（`*` 之后必须写成 `参数名=值`）。
> 参数个数 22：3 个位置参数 + 19 个关键字参数（含帕累托独有的 `cum_fmt`）。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源，图表取数的唯一入口 |
| `x` | `str` | `—` | 是 | 类目列名（画在横轴） |
| `y` | `str` | `None` | 否 | 数值列名；省略则统计记录数 |
| `agg` | `str` | `'sum'` | 否 | 聚合方式 |
| `top_n` | `int` | `None` | 否 | 只保留前 N 项（当前版本不裁剪，见详解） |
| `cum_fmt` | `str` | `'percent'` | 否 | 累计占比（折线/tooltip）的数值格式 |
| `sort` | `str` | `None` | 否 | 排序：x / asc / desc；默认按值降序 |
| `title` | `str \| None` | `None` | 否 | 主标题，默认自动生成 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题（灰色小字） |
| `xtitle` | `str \| None` | `None` | 否 | 类目轴（横轴）标题 |
| `ytitle` | `str \| None` | `None` | 否 | 数值轴（左纵轴）标题 |
| `xlim` | `tuple[float, float]` | `None` | 否 | 类目轴范围（本图不生效） |
| `ylim` | `tuple[float, float]` | `None` | 否 | 左轴（数值）范围 |
| `fmt` | `str` | `'compact'` | 否 | 左轴与柱标签的数值格式 |
| `height` | `int` | `400` | 否 | 画布高度（像素，≥120） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `str` | `'light'` | 否 | light / dark |
| `legend` | `bool` | `False` | 否 | 是否显示图例 |
| `labels` | `bool` | `False` | 否 | 是否在柱顶标数值 |
| `zoom` | `bool \| str` | `'auto'` | 否 | 缩放条（本图不支持） |
| `drill` | `str \| list[str]` | `None` | 否 | 逐级下钻维度 |
| `link` | `str` | `None` | 否 | 联动组名（同组图表互相筛选） |
| `max_rows` | `int` | `200000` | 否 | 最大参与绘制行数（None 不采样） |

## 参数详解

### `data` — 数据源，图表取数的唯一入口（必填）

- **类型 / 默认值**：`pandas.DataFrame`、`dict`、`list`（每项一行）或 `Series` / 无
- **说明**：经 `frame.ensure_frame()` 归一化成 DataFrame：`DataFrame` 原样使用，`Series` 变单列，`dict` / `list` 自动转表。行数超过 `max_rows` 时均匀抽样并提示。
- **取值建议**：帕累托图对“排序”敏感，建议先按 `x` 聚合好再传，避免明细行数影响聚合顺序。列名允许中文、空格与特殊字符。
- **报错**：`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`；`data=42` → `TypeError: 无法识别 data 类型 'int'，请传入 pandas.DataFrame（或 dict / list）。`

### `x` — 类目列名（必填）

- **类型 / 默认值**：`str` / 无
- **说明**：帕累托分析的类目，画在横轴；同一 `x` 的多行先按 `agg` 聚合。
- **取值建议**：类目数建议 5~15；太多会挤在一起，先用 `top_n` 的思路在 pandas 里取头部。类目顺序默认按数值降序，原始顺序不重要。
- **报错**：不传 → `TypeError: pareto() missing 1 required positional argument: 'x'`；列名写错 → `KeyError: "x（类目）列 '不存在' 不存在。当前可用的列有：日期, 月份, 大区, 省份, 城市, 产品, 渠道, 销售额, 订单数, 利润, 客户数"`

### `y` — 数值列名（可省略）

- **类型 / 默认值**：`str` / `None`
- **说明**：柱子高度与累计占比的来源。**省略时**改为“统计记录数”（`agg` 被强制成 `count`），自动标题里的指标名变成「记录数」；此时累计占比 = 记录数占比。
- **取值建议**：金额/次数用数值列；想看“各类目记录数分布”就直接省掉 `y`。
- **报错**：文本列 → `TypeError: y（数值）列 '产品' 需要是数值类型（当前是文本，例如 ['智能终端', '云服务', '行业软件']）。请先用 pd.to_numeric() 清洗，或换一列。`

### `agg` — 聚合方式

- **类型 / 默认值**：`str` / `'sum'`
- **说明**：按 `x` 聚合 `y` 时使用。可选 `sum` / `mean` / `count` / `max` / `min` / `median`；`y=None` 时被强制为 `count`。
- **取值建议**：贡献度分析（金额、缺陷数）用 `"sum"`；注意帕累托的“累计”语义是求和，用 `"mean"` 时柱高不再是可累加的份额，累计占比会失真。
- **报错**：`y` 已给且 `agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median`

### `top_n` — 只保留前 N 项（当前版本不裁剪）

- **类型 / 默认值**：`int` / `None`
- **说明**：只做合法性校验并写入 `spec["topN"]`。**1.0.0 中帕累托图的前端构建器不读取 `spec.topN`，本参数不会减少柱子数**；需要 Top N 请先在 pandas 里过滤。
- **取值建议**：`df.groupby("产品")["销售额"].sum().nlargest(10).reset_index()` 之后再画。
- **报错**：`top_n=0` → `ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`

### `cum_fmt` — 累计占比的数值格式

- **类型 / 默认值**：`str` / `'percent'`
- **说明**：帕累托独有。决定 **tooltip 里「累计」那一行**的格式，取值集合同 `fmt`：`percent` / `compact` / `thousands` / `raw` / `currency`。默认 `"percent"` 时显示为百分比（如 `87.5%`）；改成其它值时显示累计的**原始数值**（如 `1,428,000`）。注意右侧累计轴的刻度固定是 0~100%，不受本参数影响。传 `None` 按 `percent` 处理。
- **取值建议**：几乎总是保持 `"percent"`；只有当你想在 tooltip 里同时看到累计绝对值时改成 `"thousands"`（此时百分比信息消失，需要自己算）。
- **报错**：`cum_fmt="cn"` → `ValueError: fmt='cn' 不支持，可选：compact, thousands, raw, percent, currency`（**提示文案写的是 `fmt=`，这是 1.0.0 的文案瑕疵，实际校验的是 `cum_fmt`**）

### `sort` — 排序方式

- **类型 / 默认值**：`str` / `None`
- **说明**：帕累托图**默认强制按值降序**：
  - `None` / `"desc"` / 其它任意值 → 按值降序（帕累托的标准画法）；
  - `"asc"` → 按值升序；
  - `"x"` → 按类目本身排序（会失去帕累托意义，但方便看时间/有序类目）。
  非法值不会报错，走默认降序分支。
- **取值建议**：除非要做“反向帕累托”（长尾分析），否则保持默认；要看月度累计时用 `sort="x"` 并配合有序分类。
- **示例**：`sort="asc"` → 柱子从小到大排列，折线从低位快速爬升

### `title` — 主标题

- **类型 / 默认值**：`str` / `None`
- **说明**：不传时自动生成「<y 列名> 帕累托分析」（`y=None` 时为「记录数 帕累托分析」）；传 `""` 得到空标题（不回落自动）。
- **取值建议**：写清“谁对什么的贡献”，例如 `"产品销售额帕累托分析（2024）"`。
- **示例**：`title=None` → `chart.spec["title"] == "销售额 帕累托分析"`

### `subtitle` — 副标题

- **类型 / 默认值**：`str` / `None`
- **说明**：标题下方的小字说明，默认没有。
- **取值建议**：写清“80% 线”的口径或数据范围。
- **示例**：`subtitle="累计 80% 线以上的类目为重点关注对象"`

### `xtitle` — 类目轴（横轴）标题

- **类型 / 默认值**：`str` / `None`
- **说明**：不传时用 `x` 列名；传 `""` 隐藏。
- **取值建议**：类目名已自明时传 `""`，给底部标签留空间。
- **示例**：`xtitle="产品"`；`xtitle=""` → 横轴无标题

### `ytitle` — 数值轴（左纵轴）标题

- **类型 / 默认值**：`str` / `None`
- **说明**：左轴（柱子的刻度）标题，同时也是柱系列在图例/tooltip 里的名称；不传时用 `y` 列名；传 `""` 隐藏。
- **取值建议**：写上单位，如 `"销售额（元）"`。右轴的「累计占比」名称是固定的，不用传。
- **示例**：`ytitle="销售额（元）"`

### `xlim` — 类目轴范围（本图不生效）

- **类型 / 默认值**：`tuple[float, float]` / `None`
- **说明**：横轴是类目轴，`xlim` 只写入 `spec["xlim"]`，不改变画面；格式错误仍会报错。
- **取值建议**：本图不需要；左轴范围用 `ylim`。
- **报错**：`xlim=(0,)` → `ValueError: xlim 需要是 (最小值, 最大值) 两元组，例如 xlim=(0, 100)`

### `ylim` — 左轴（数值）范围

- **类型 / 默认值**：`tuple[float, float]` / `None`
- **说明**：只作用于左轴（柱子的数值轴），**本图生效**；右轴累计始终固定 0~100%。内部把 `(lo, hi)` 交换成 `[lo, hi]`。
- **取值建议**：`ylim=(0, 600000)` 这类固定范围可让多张帕累托图对齐；留出顶部空间能避免累计折线被裁切。
- **示例**：`ylim=(0, 600000)`

### `fmt` — 左轴与柱标签的数值格式

- **类型 / 默认值**：`str` / `'compact'`
- **说明**：作用于左轴刻度、`labels` 显示的柱顶数值与 tooltip 里的“数值”行。可选 `compact` / `thousands` / `raw` / `percent` / `currency`；`fmt=None` 按 `compact` 处理。**累计占比的格式由 `cum_fmt` 单独控制**。
- **取值建议**：金额用 `"thousands"`；注意不要用 `"percent"`（除非柱子本身就是百分比）。
- **报错**：`fmt="cn"` → `ValueError: fmt='cn' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）

- **类型 / 默认值**：`int` / `400`
- **说明**：帕累托图默认比其他扩展图高 20px（400），因为要同时容纳柱子和折线；传 `None` 时**回落到 380**（不是 400）。
- **取值建议**：类目多时 460~560；类目少时 400 足够。
- **报错**：`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题

- **类型 / 默认值**：`str` / `'light'`
- **说明**：`"light"` / `"dark"`，控制背景、文字、柱色与累计线颜色。
- **取值建议**：深色大屏用 `"dark"`；累计折线在深底下用高对比色，仍清晰。
- **报错**：`theme="night"` → `ValueError: theme 只支持 "light" / "dark"，收到 'night'`

### `legend` — 是否显示图例

- **类型 / 默认值**：`bool` / `False`
- **说明**：**本图生效**。显示柱系列（名称取自 `ytitle` 或 `y` 列名）与「累计占比」两条图例；默认关闭以节省右侧空间。
- **取值建议**：单图独立展示、标题已说明时保持 `False`；多图并排或需要明确“右轴是累计占比”时开 `True`。
- **示例**：`legend=True` → 图例出现「销售额 / 累计占比」两项

### `labels` — 是否在柱顶标数值

- **类型 / 默认值**：`bool` / `False`
- **说明**：**本图生效**，只标柱子的数值（按 `fmt` 格式化），累计折线上不标。类目多时容易重叠。
- **取值建议**：类目 ≤10 且需要直接读数时开启；否则用 tooltip。
- **示例**：`labels=True` → 每根柱顶显示数值

### `zoom` — 缩放条（本图不支持）

- **类型 / 默认值**：`bool` / `str` / `'auto'`
- **说明**：只有核心笛卡尔图消费 `spec.zoom`；**帕累托图构建器不读取该字段**，`"auto"` 也不会自动加缩放条。
- **取值建议**：类目太多时先聚合或取头部。
- **示例**：`zoom=True` → `chart.spec["zoom"] is True`，画面无缩放条。

### `drill` — 逐级下钻维度

- **类型 / 默认值**：`str` 或 `list[str]` / `None`
- **说明**：点击某根柱子后按该类目名过滤数据并重算（柱子、累计占比全部重算）；点「返回」回退。传字符串自动转列表；`drill[0]` 与 `x` 不同时自动把 `x` 插到最前。
- **取值建议**：从粗到细 2~3 层；下钻后类目数变化，累计占比的含义也随之变化。
- **报错**：`drill=[]` → `ValueError: drill 不能是空列表；不需要下钻请传 drill=None。`；列名不存在 → `KeyError: "下钻维度列 '不存在' 不存在。……"`

### `link` — 联动组名

- **类型 / 默认值**：`str` / `None`
- **说明**：同 `link` 组的图表互相联动：点击某类目把名字广播给组内其它图，它们按同名列过滤重算。
- **取值建议**：与同页趋势图、明细表统一命名，如 `link="product"`。
- **示例**：`link="product"`；`chart.spec["link"] == "product"`

### `max_rows` — 最大参与绘制行数

- **类型 / 默认值**：`int` / `200000`
- **说明**：超过则等间隔均匀抽样，warning 写入 `chart.warnings["warnings"]`，`chart.data["n_total"]` 保留原始行数；`None` 关闭采样。
- **取值建议**：帕累托图应基于完整聚合结果，建议先 `groupby` 再传；`max_rows` 作为兜底。
- **示例**：`max_rows=100` → `chart.data["n"] == 100`

## 返回值

所有图表函数都返回 `eazy_data_viz.Chart` 对象（`chart = edv.pareto(df, x="产品", y="销售额")`）。

**Chart 的属性**

- `chart.spec`：`dict`，前端 ECharts 配置（JSON 可序列化）。公共键有 `id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`、`roles`、`agg`、`fmt`、`sort`、`topN`、`xtitle`、`ytitle`、`xlim`、`ylim`、`legend`、`labels`、`zoom`、`drill`、`link`，本图额外带 `cumFmt`。
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
{ "id": "c1", "type": "pareto", "title": "销售额 帕累托分析", "subtitle": null, "theme": "light",
  "height": 400, "dataRef": "d9465273f71af", "roles": {"x": "产品", "y": "销售额"}, "agg": "sum",
  "cumFmt": "percent", "sort": null, "topN": null, "xtitle": null, "ytitle": null, "xlim": null,
  "ylim": null, "fmt": "compact", "legend": false, "labels": false, "zoom": "auto", "drill": null,
  "link": null }
```

**验证返回值的小技巧**

```python
import eazy_data_viz as edv
df = edv.sample_df()
chart = edv.pareto(df, x="产品", y="销售额")
assert chart.spec["type"] == "pareto"
assert chart.spec["cumFmt"] == "percent"
assert chart.spec["height"] == 400
print(chart.warnings, len(chart.to_html()))
```

## 完整示例

以下示例都基于 `edv.sample_df()`（1500 行 × 11 列），可直接复制运行；输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.pareto(df, x="产品", y="销售额")
chart.save("examples/output/pareto_1.html")
```

**输出**：自动标题「销售额 帕累托分析」；柱子按销售额降序（智能终端 536,604 → 行业软件 450,647 → 云服务 407,997 → 运维服务 235,785），累计占比依次约 32.9% → 60.5% → 85.5% → 100%。
**验证**：`chart.spec["roles"]["y"] == "销售额"`、`chart.spec["cumFmt"] == "percent"`。

### 示例 2：省略 `y`：类目记录数占比

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.pareto(df, x="渠道")
chart.save("examples/output/pareto_2.html")
```

**输出**：自动标题「记录数 帕累托分析」；三个渠道各 500 条记录，柱子等高，累计占比 33.3% → 66.7% → 100%。
**验证**：`chart.spec["agg"] == "count"`、`chart.spec["title"] == "记录数 帕累托分析"`。

### 示例 3：柱标 + 图例 + 千分位

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.pareto(
    df, x="省份", y="销售额",
    labels=True, legend=True, fmt="thousands",
    title="各省销售额帕累托分析", subtitle="累计 80% 以上的省份为重点",
)
chart.save("examples/output/pareto_3.html")
```

**输出**：10 个省份按销售额降序；柱顶显示千分位数值；图例出现「销售额 / 累计占比」；累计线在前 5~6 个省就接近 80%。
**验证**：`chart.spec["labels"] is True`、`chart.spec["legend"] is True`。

### 示例 4：`cum_fmt="thousands"`：tooltip 里看累计绝对值

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.pareto(
    df, x="产品", y="销售额",
    cum_fmt="thousands", ytitle="销售额（元）",
)
chart.save("examples/output/pareto_4.html")
```

**输出**：右轴刻度仍是 0~100%，但 tooltip 的「累计」一行变成累计金额（如 987,251 而不是 60.5%）；左轴刻度仍按 `fmt`（默认 compact）。
**验证**：`chart.spec["cumFmt"] == "thousands"`。

### 示例 5：`sort="asc"` 反向排序

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.pareto(
    df, x="产品", y="销售额", sort="asc",
    labels=True, title="产品销售额帕累托（升序）",
)
chart.save("examples/output/pareto_5.html")
```

**输出**：柱子从小到大（运维服务 → 云服务 → 行业软件 → 智能终端）；累计线从低位一路上升，最后一个点才到 100%。
**验证**：`chart.spec["sort"] == "asc"`。

### 示例 6：下钻 + 联动

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.pareto(
    df, x="大区", y="销售额",
    drill=["大区", "省份", "城市"], link="pareto",
    labels=True, legend=True,
)
chart.save("examples/output/pareto_6.html")
```

**输出**：初始 4 个大区的贡献排序；点击柱子按该大区过滤并切到省份维度，累计占比按过滤后的子集重算；同 `link="pareto"` 的图表同步过滤。
**验证**：`chart.spec["drill"] == ["大区", "省份", "城市"]`、`chart.spec["link"] == "pareto"`。

### 示例 7：边界：只有一个类目

```python
import pandas as pd
import eazy_data_viz as edv

# 只有一根柱子：累计占比恒为 100%，右轴 0~100% 的刻度依旧成立
d1 = pd.DataFrame({"项目": ["唯一项目"], "金额": [100]})
chart = edv.pareto(d1, x="项目", y="金额", legend=True)
chart.save("examples/output/pareto_7.html")
```

**输出**：单根柱子占满左侧数值轴，累计线只有一个点、停在 100%。
**验证**：`chart.data["n"] == 1`、`chart.spec["type"] == "pareto"`。

## 常见错误

### 1. 以为 `top_n` 能只画前 N 个柱子

```python
import eazy_data_viz as edv
df = edv.sample_df()
chart = edv.pareto(df, x="省份", y="销售额", top_n=3)
assert chart.spec["topN"] == 3
# 但仍然是 10 根柱子，累计占比按全部 10 个算
```

**修法**：先 `df.groupby("省份")["销售额"].sum().nlargest(3).reset_index()`；注意截断后累计占比的“100%”只代表这 3 项。

### 2. `cum_fmt` 写错时看到的是 `fmt=` 报错

```python
import eazy_data_viz as edv
df = edv.sample_df()
# edv.pareto(df, x="产品", y="销售额", cum_fmt="cn")
# → ValueError: fmt='cn' 不支持，可选：compact, thousands, raw, percent, currency
# 注意提示里写的是 fmt，但实际校验的是 cum_fmt；改为合法值即可
chart = edv.pareto(df, x="产品", y="销售额", cum_fmt="percent")
```

**修法**：`cum_fmt` 只接受 `compact` / `thousands` / `raw` / `percent` / `currency`（与 `fmt` 同一集合）。

### 3. 用 `ylim` 想同时控制右轴

```python
import eazy_data_viz as edv
df = edv.sample_df()
# ylim 只作用于左轴；右轴累计固定 0~100%，无法通过参数修改
chart = edv.pareto(df, x="产品", y="销售额", ylim=(0, 100))
# 如果想看“左轴百分比”，把数据换成百分比、fmt="percent"
chart2 = edv.pareto(df, x="产品", y="销售额", ylim=(0, 600000), fmt="thousands")
```

**修法**：右轴无需也无法配置；`ylim` 只影响柱子刻度。需要百分比柱时先把数据算成比例再用 `fmt="percent"`。

### 4. 用 `"mean"` 聚合后累计占比不对

```python
import eazy_data_viz as edv
df = edv.sample_df()
# 累计占比是按“各柱求和”算的；用 mean 时柱高不可累加，累计曲线的百分比会失真
chart = edv.pareto(df, x="大区", y="销售额", agg="mean")
# 贡献度分析请用 sum
chart2 = edv.pareto(df, x="大区", y="销售额", agg="sum")
```

**修法**：帕累托图只在 `agg="sum"`（或 `count`）下语义正确；`mean` / `median` 仅当你确认柱子可累加时使用。

## 相关图表

- `bar`：只关心各类目绝对大小、不需要累计线时用它。
- `pie`：看占比构成（但类目多时不如帕累托清晰）。
- `waterfall`：想把“累计过程”拆成增减项时用瀑布图。
- `treemap`：类目层级多、要同时表达占比与结构。
- `lollipop`：排序后的轻量排行替代方案。
