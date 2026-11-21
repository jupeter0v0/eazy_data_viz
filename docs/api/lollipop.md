# `lollipop` — 棒棒糖图：一根细杆 + 一个圆点

> 用“细杆 + 端点圆点”代替整根柱子表达单个数值，比柱状图更轻、更透气，适合类目较多的排行类场景。
> 适合：区域/产品销售额排行、渠道订单量对比、Top N 榜单（类目 10 个以上时尤其清爽）。
> 不适合：需要精确比较细微差异（用 `bar`）、需要堆叠/分组（用 `bar`）、要表现占比（用 `pie` / `pareto`）。

## 函数签名

```python
def lollipop(
    data,
    x,
    y=None,
    *,
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
> 参数个数 21：3 个位置参数 + 18 个关键字参数。`y` 可以省略——省了就按“记录数”计数。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源，图表取数的唯一入口 |
| `x` | `str` | `—` | 是 | 类目列名（画在纵轴） |
| `y` | `str` | `None` | 否 | 数值列名；省略则统计记录数 |
| `agg` | `str` | `'sum'` | 否 | 聚合方式 |
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
| `legend` | `bool` | `False` | 否 | 是否显示图例（本图固定不显示） |
| `labels` | `bool` | `False` | 否 | 是否在圆点上方标数值 |
| `zoom` | `bool \| str` | `'auto'` | 否 | 缩放条（本图不支持） |
| `drill` | `str \| list[str]` | `None` | 否 | 逐级下钻维度 |
| `link` | `str` | `None` | 否 | 联动组名（同组图表互相筛选） |
| `max_rows` | `int` | `2000000` | 否 | 最大参与绘制行数（None 不采样） |

## 参数详解

### `data` — 数据源，图表取数的唯一入口（必填）

- **类型 / 默认值**：`pandas.DataFrame`、`dict`、`list`（每项一行）或 `Series` / 无
- **说明**：经 `frame.ensure_frame()` 归一化成 DataFrame：`DataFrame` 原样使用，`Series` 变单列，`dict` / `list` 自动转表。行数超过 `max_rows` 时均匀抽样，提示写入 `chart.warnings`。
- **取值建议**：正式代码一律传 DataFrame；`dict` / `list` 只用于快速试验。列名允许中文、空格与特殊字符。
- **报错**：`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`；`data=42` → `TypeError: 无法识别 data 类型 'int'，请传入 pandas.DataFrame（或 dict / list）。`

### `x` — 类目列名（必填）

- **类型 / 默认值**：`str` / 无
- **说明**：每根棒棒糖对应一个类目，画在**横轴**上；同一 `x` 的多行先按 `agg` 聚合。
- **取值建议**：类目标签较长时（如省份全称）用横向布局要留意底部标签重叠；棒棒糖图本身最适合 6~20 个类目。类目有明显业务顺序时用有序分类 + `sort="x"`。
- **报错**：不传 → `TypeError: lollipop() missing 1 required positional argument: 'x'`；列名写错 → `KeyError: "x（类目）列 '不存在' 不存在。当前可用的列有：日期, 月份, 大区, 省份, 城市, 产品, 渠道, 销售额, 订单数, 利润, 客户数"`

### `y` — 数值列名（可省略）

- **类型 / 默认值**：`str` / `None`
- **说明**：棒棒糖端点高低的来源。**省略时**自动改为“统计记录数”（`agg` 被强制成 `count`），此时自动标题里的指标名变成「记录数」。
- **取值建议**：想看“每个类目有多少条记录”就直接省掉 `y`；想看金额/数量就传数值列。`y` 省略时传非法 `agg` 不会报错（会被 `count` 覆盖）。
- **报错**：传文本列 → `TypeError: y（数值）列 '产品' 需要是数值类型（当前是文本，例如 ['智能终端', '云服务', '行业软件']）。请先用 pd.to_numeric() 清洗，或换一列。`；传日期列 → `TypeError: y（数值）列 '日期' 需要是数值类型，但当前是日期时间类型。请换一列。`

### `agg` — 聚合方式

- **类型 / 默认值**：`str` / `'sum'`
- **说明**：按 `x` 聚合 `y` 时使用。可选 `sum` / `mean` / `count` / `max` / `min` / `median`；`y=None` 时被强制为 `count`。
- **取值建议**：金额、销量用 `"sum"`；单价、转化率、客单价等比率型指标用 `"mean"`；`"count"` 可直接统计每个类目的记录数。
- **报错**：`y` 已给且 `agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median`

### `sort` — 类目顺序

- **类型 / 默认值**：`str` / `None`
- **说明**：`"x"` 按类目本身排序，`"asc"` / `"desc"` 按数值排序，`None` 保持聚合顺序（数据中首次出现顺序）。
- **取值建议**：排行榜用 `"desc"`；时间/有序类目用 `"x"`。注意非法值不会报错，前端按不排序处理。
- **示例**：`sort="desc"` → 华东（582,864）排最左（或最右，取决于轴方向）

### `top_n` — 只保留前 N 项（当前版本不裁剪）

- **类型 / 默认值**：`int` / `None`
- **说明**：只做合法性校验并写入 `spec["topN"]`。**1.0.0 中棒棒糖图的前端构建器不读取 `spec.topN`，本参数不会减少类目数**；需要 Top N 请先在 pandas 里过滤。
- **取值建议**：`df.groupby("省份")["销售额"].sum().nlargest(10).reset_index()` 之后再画。
- **报错**：`top_n=0` → `ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`

### `title` — 主标题

- **类型 / 默认值**：`str` / `None`
- **说明**：不传时自动生成「<y 列名> 按 <x 列名>」（`y=None` 时为「记录数 按 <x 列名>」）；传 `""` 得到空标题（不回落自动）。
- **取值建议**：写清指标 + 口径，例如 `"各省销售额（2024 全年，含税）"`。
- **示例**：`title=None` → `chart.spec["title"] == "销售额 按 大区"`

### `subtitle` — 副标题

- **类型 / 默认值**：`str` / `None`
- **说明**：标题下方的小字说明，默认没有。
- **取值建议**：写时间范围、数据口径或“已剔除退款”。
- **示例**：`subtitle="数据区间 2024-01-01 ~ 2024-12-30"`

### `xtitle` — 类目轴（横轴）标题

- **类型 / 默认值**：`str` / `None`
- **说明**：不传时用 `x` 列名；传 `""` 隐藏。
- **取值建议**：类目名已自明（大区/产品）时可传 `""`，把空间让给类目标签。
- **示例**：`xtitle="大区"`；`xtitle=""` → 横轴无标题

### `ytitle` — 数值轴（纵轴）标题

- **类型 / 默认值**：`str` / `None`
- **说明**：不传时用 `y` 列名（`y=None` 时为「记录数」）；传 `""` 隐藏。
- **取值建议**：写上单位，如 `"销售额（元）"`。
- **示例**：`ytitle="销售额（元）"`

### `xlim` — 类目轴范围（本图不生效）

- **类型 / 默认值**：`tuple[float, float]` / `None`
- **说明**：棒棒糖图横轴是类目轴，`xlim` 只写入 `spec["xlim"]`，不改变画面；格式错误仍会报错。
- **取值建议**：本图不需要；要控制显示范围请用 `ylim`（数值轴）。
- **报错**：`xlim=(0,)` → `ValueError: xlim 需要是 (最小值, 最大值) 两元组，例如 xlim=(0, 100)`

### `ylim` — 数值轴范围

- **类型 / 默认值**：`tuple[float, float]` / `None`
- **说明**：固定纵轴范围，**本图生效**；内部把 `(lo, hi)` 交换成 `[lo, hi]` 后写入 `spec["ylim"]`。
- **取值建议**：需要在多张图之间对齐尺度时固定它，例如 `ylim=(0, 300000)`；从 0 起画能避免“细杆长度误导”。
- **示例**：`ylim=(0, 250000)`

### `fmt` — 数值格式

- **类型 / 默认值**：`str` / `'compact'`
- **说明**：作用于纵轴刻度、圆点标签与 tooltip。可选 `compact` / `thousands` / `raw` / `percent` / `currency`；`fmt=None` 按 `compact` 处理。
- **取值建议**：金额用 `"thousands"`；比例用 `"percent"`；需要完整数字（不缩写）用 `"raw"`。
- **报错**：`fmt="cn"` → `ValueError: fmt='cn' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）

- **类型 / 默认值**：`int` / `380`
- **说明**：最小 120；传 `None` 回落到 380。
- **取值建议**：类目多时加高避免横轴标签挤在一起；纵向留白比柱状图更敏感，380~460 是舒适区。
- **报错**：`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题

- **类型 / 默认值**：`str` / `'light'`
- **说明**：`"light"` / `"dark"`，控制背景、文字、轴线与圆点高亮色。
- **取值建议**：深色大屏用 `"dark"`；浅色圆点在深底下对比更强。
- **报错**：`theme="night"` → `ValueError: theme 只支持 "light" / "dark"，收到 'night'`

### `legend` — 是否显示图例（本图固定不显示）

- **类型 / 默认值**：`bool` / `False`
- **说明**：棒棒糖图只有一个系列，构建器 `legend: false` 硬编码，**本参数只写入 `spec["legend"]`，不渲染图例**。
- **取值建议**：保持默认；需要说明“圆点是数值”时写在 `subtitle`。
- **示例**：`legend=True` → `chart.spec["legend"] is True`，画面无图例。

### `labels` — 是否在圆点上方标数值

- **类型 / 默认值**：`bool` / `False`
- **说明**：开启后每个圆点上方显示按 `fmt` 格式化的数值，**本图生效**。类目多时标签会拥挤，建议与 `height` 一起调整。
- **取值建议**：类目 ≤12 且数值不看仔细也能比时开启；否则交给 tooltip。
- **示例**：`labels=True` → 华东圆点上方显示 `582,864`（`fmt="thousands"` 时）

### `zoom` — 缩放条（本图不支持）

- **类型 / 默认值**：`bool` / `str` / `'auto'`
- **说明**：只有核心笛卡尔图（`bar` / `line` / `area` / `combo`）消费 `spec.zoom` 并渲染 dataZoom；**棒棒糖图构建器不读取该字段**，`"auto"` 也不会在类目多时自动加缩放条。
- **取值建议**：类目过多时先聚合或截断，不要依赖 `zoom`。
- **示例**：`zoom=True` → `chart.spec["zoom"] is True`，画面无缩放条。

### `drill` — 逐级下钻维度

- **类型 / 默认值**：`str` 或 `list[str]` / `None`
- **说明**：点击某个类目后按该值过滤数据并重算；点「返回」回退。传字符串自动转列表；`drill[0]` 与 `x` 不同时自动把 `x` 插到最前；只传 `drill` 时 `x` 取 `drill[0]`。
- **取值建议**：从粗到细 2~3 层（大区 → 省份 → 城市）。
- **报错**：`drill=[]` → `ValueError: drill 不能是空列表；不需要下钻请传 drill=None。`；列名不存在 → `KeyError: "下钻维度列 '不存在' 不存在。当前可用的列有：……\n提示：drill 里的每一列都必须是 df 的列名。"`

### `link` — 联动组名

- **类型 / 默认值**：`str` / `None`
- **说明**：同 `link` 组的图表互相联动：点击某类目把名字广播给组内其它图，它们按同名列过滤重算。需要数据里有同名列。
- **取值建议**：看板里与趋势图、明细表同组时统一命名，如 `link="region"`。
- **示例**：`link="region"`；`chart.spec["link"] == "region"`

### `max_rows` — 最大参与绘制行数

- **类型 / 默认值**：`int` / `200000`
- **说明**：超过则等间隔均匀抽样，warning 写入 `chart.warnings["warnings"]`，`chart.data["n_total"]` 保留原始行数；传 `None` 关闭采样。
- **取值建议**：棒棒糖图只画聚合结果，建议先 `groupby` 再传；`max_rows` 作为兜底防止误传明细表。
- **示例**：`max_rows=100` → `chart.data["n"] == 100`；`max_rows=None` → 不抽样

## 返回值

所有图表函数都返回 `eazy_data_viz.Chart` 对象（`chart = edv.lollipop(df, x="大区", y="销售额")`）。

**Chart 的属性**

- `chart.spec`：`dict`，前端 ECharts 配置（JSON 可序列化）。公共键有 `id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`、`roles`、`agg`、`fmt`、`sort`、`topN`、`xtitle`、`ytitle`、`xlim`、`ylim`、`legend`、`labels`、`zoom`、`drill`、`link`；本图没有额外键。
- `chart.data`：**`dict`**，不是 DataFrame。含 `cols`（列名）、`rows`（实际参与绘图的二维数组）、`dims` / `measures` / `kinds`、`orders`、`n`（参与行数）、`n_total`（原始行数）。
- `chart.data_ref`：数据引用 id（`d-` + 12 位 sha1）。
- `chart.warnings`：**`dict`**，形如 `{"warnings": ["..."], "n_total": 1500}`；空表示无降级。
- `chart.title`：只读属性，等价于 `chart.spec["title"]`。

**Chart 的方法**

- `chart.save(path, inline=True)`：写出单文件 HTML（约 1.2~1.5 MB），自动建目录，返回绝对路径。
- `chart.to_html(inline=True)`：返回完整 HTML 字符串；`inline=False` 引用外部资源。
- `chart.show(open_browser=None)`：浏览器打开；Jupyter / Streamlit 自动内嵌。
- `chart.palette(name)`：切换配色并返回 `self`；可选 `google`、`antd`、`tableau`、`carbon`、`echarts`、`morandi`、`tailwind`。

**本图 `spec` 的真实结构**

```json
{ "id": "c1", "type": "lollipop", "title": "销售额 按 大区", "subtitle": null, "theme": "light",
  "height": 380, "dataRef": "d9465273f71af", "roles": {"x": "大区", "y": "销售额"}, "agg": "sum",
  "sort": null, "topN": null, "xtitle": null, "ytitle": null, "xlim": null, "ylim": null,
  "fmt": "compact", "legend": false, "labels": false, "zoom": "auto", "drill": null, "link": null }
```

**验证返回值的小技巧**

```python
import eazy_data_viz as edv
df = edv.sample_df()
chart = edv.lollipop(df, x="大区", y="销售额")
assert chart.spec["type"] == "lollipop"
assert chart.spec["roles"] == {"x": "大区", "y": "销售额"}
print(chart.warnings, len(chart.to_html()))
```

## 完整示例

以下示例都基于 `edv.sample_df()`（1500 行 × 11 列），可直接复制运行；输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.lollipop(df, x="大区", y="销售额")
chart.save("examples/output/lollipop_1.html")
```

**输出**：自动标题「销售额 按 大区」；4 根棒棒糖高度依次为 582,864 / 476,048 / 347,046 / 225,076（按数据首次出现顺序）。
**验证**：`chart.spec["roles"]["y"] == "销售额"`、`chart.spec["agg"] == "sum"`。

### 示例 2：排行榜：降序 + 数值标签

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.lollipop(
    df, x="大区", y="销售额",
    sort="desc", labels=True, fmt="thousands",
    title="大区销售额排行", subtitle="2024 全年，含税",
)
chart.save("examples/output/lollipop_2.html")
```

**输出**：从高到低 华东 → 华北 → 华南 → 西部；每个圆点上方显示千分位数值。
**验证**：`chart.spec["sort"] == "desc"`、`chart.spec["labels"] is True`。

### 示例 3：省略 `y`：统计记录数

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.lollipop(df, x="渠道")
chart.save("examples/output/lollipop_3.html")
```

**输出**：自动标题变成「记录数 按 渠道」；三个渠道各 500 条记录，四根棒棒糖等高（`agg` 被强制为 `count`）。
**验证**：`chart.spec["agg"] == "count"`、`chart.spec["title"] == "记录数 按 渠道"`。

### 示例 4：固定数值轴 + 类目排序

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.lollipop(
    df, x="月份", y="销售额",
    agg="sum", sort="x", ylim=(0, 200000), fmt="thousands",
    xtitle="", ytitle="销售额（元）", height=420,
)
chart.save("examples/output/lollipop_4.html")
```

**输出**：12 个月按 1 月 → 12 月排列（月份是有序分类）；纵轴固定 0~20 万，最高月（5 月 174,919）接近顶部。
**验证**：`chart.spec["ylim"] == [0.0, 200000.0]`、`chart.spec["xtitle"] == ""`。

### 示例 5：下钻 + 联动

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.lollipop(
    df, x="大区", y="销售额",
    drill=["大区", "省份"], link="sales",
    title="销售额（可下钻到省份）",
)
chart.save("examples/output/lollipop_5.html")
```

**输出**：初始 4 个类目；点击某根棒棒糖按该大区过滤并切到省份维度；同 `link="sales"` 的图表同步过滤。
**验证**：`chart.spec["drill"] == ["大区", "省份"]`、`chart.spec["link"] == "sales"`。

### 示例 6：边界：单类目 / 空数值列

```python
import eazy_data_viz as edv
import pandas as pd

df = edv.sample_df()
# 只有 1 个类目：图仍可渲染，但看不出“比较”意义
one = edv.lollipop(df[df["大区"] == "华东"], x="大区", y="销售额")
# 全 NaN 数值列：聚合后为 0/空，棒棒糖贴底
df["空列"] = pd.NA
try:
    edv.lollipop(df, x="大区", y="空列")
except (TypeError, ValueError) as exc:
    print(type(exc).__name__, exc)
chart = edv.lollipop(df, x="产品", y="利润", sort="desc", labels=True)
chart.save("examples/output/lollipop_6.html")
```

**输出**：单类目图正常生成；空数值列可能抛类型错误或画成全 0；产品利润排序为 云服务 → 行业软件 → 智能终端 → 运维服务。
**验证**：`one.data["n_total"] == 500`、`chart.spec["sort"] == "desc"`。

## 常见错误

### 1. `y` 传了文本列

```python
import eazy_data_viz as edv
df = edv.sample_df()
# 错误写法：y="产品" 是文本列
# edv.lollipop(df, x="大区", y="产品")
# → TypeError: y（数值）列 '产品' 需要是数值类型（当前是文本，例如 ['智能终端', '云服务', '行业软件']）……
# 正确写法：换成数值列
chart = edv.lollipop(df, x="大区", y="销售额")
```

**修法**：`aggregate` 前先用 `pd.to_numeric(df["产品"])` 清洗，或改用数值列；需要按产品计数就省略 `y`。

### 2. 以为 `top_n` 会裁剪类目

```python
import eazy_data_viz as edv
df = edv.sample_df()
chart = edv.lollipop(df, x="省份", y="销售额", top_n=3)
assert chart.spec["topN"] == 3
# 但类目仍是 10 个 —— 前端不读 topN
print(chart.data["n_total"])
```

**修法**：在 pandas 里先取 Top N：`df.groupby("省份")["销售额"].sum().nlargest(3).reset_index()`。

### 3. 想用 `xlim` 控制数值范围

```python
import eazy_data_viz as edv
df = edv.sample_df()
# 棒棒糖图的横轴是类目轴，xlim 不生效
chart = edv.lollipop(df, x="大区", y="销售额", xlim=(0, 300000))
# 要固定数值轴请用 ylim
chart2 = edv.lollipop(df, x="大区", y="销售额", ylim=(0, 600000))
```

**修法**：棒棒糖是竖着的“棒”——类目在横轴、数值在纵轴，所以数值范围要用 `ylim`。

### 4. `drill` 传了空列表或错误列名

```python
import eazy_data_viz as edv
df = edv.sample_df()
# edv.lollipop(df, x="大区", y="销售额", drill=[])
# → ValueError: drill 不能是空列表；不需要下钻请传 drill=None。
# edv.lollipop(df, x="大区", y="销售额", drill=["不存在"])
# → KeyError: "下钻维度列 '不存在' 不存在。当前可用的列有：……"
chart = edv.lollipop(df, x="大区", y="销售额")  # 不需要下钻就别传
```

**修法**：不需要下钻就省略 `drill`（或传 `None`）；传的每一列都必须是真实列名。

## 相关图表

- `bar`：需要更粗的视觉份量、或要堆叠/分组时用它。
- `dumbbell`：两个数值（本期 vs 上期）在同一行对比时看差值。
- `pareto`：棒棒糖排序后还想看“累计占比”时换成帕累托图。
- `target`：除了相对大小还关心是否达成目标时用它。
- `waterfall`：想看类目累计过程（增减项）而不是并列大小。
