# `progress` — 进度条列表（类目完成度排行）

> 每个类目一行：名称 + 数值 + 百分比 + 一条填充进度条，按数值排序，可以一眼看出「谁快完成了、谁差得远」。
> 适合：多个类目的完成度/占比排行（各大区销售目标完成率、各渠道预算消耗、各门店任务进度），类目数量 3~20 个时最舒服。
> 不适合：随时间变化的趋势（用 `line` / `area`）、单个指标的达成率（用 `ring_progress`）、需要精确比较数值大小（用 `bar`）、二维交叉对比（用 `heatmap`）。

## 函数签名

```python
eazy_data_viz.progress(
    data,
    x=None,
    y=None,
    *,
    max=None,
    agg="sum",
    sort="desc",
    top_n=10,
    title=None,
    subtitle=None,
    fmt="compact",
    height=340,
    theme="light",
    link=None,
    max_rows=200000,
) -> Chart
```

签名要点：

- `x` / `y` 都可以省略：省略 `x` 时自动挑第一个分类列（找不到再挑时间列），省略 `y` 时统计记录数。
- `max`、`agg`、`sort`、`top_n`、`title`、`subtitle`、`fmt`、`height`、`theme`、`link`、`max_rows` 是 keyword-only。
- 没有 `xtitle` / `ytitle` / `xlim` / `ylim` / `legend` / `labels` / `zoom` / `drill` —— 本图没有坐标轴、没有图例，也不能逐级下钻。
- 本图是 **HTML 组件**（不是 ECharts 画布），由前端 `EazyViz.htmlBuilders["progress"]` 渲染成列表。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list` | `—` | 是 | 数据源 |
| `x` | `str \| None` | `None` | 否 | 类目列名，None 时自动挑分类列 |
| `y` | `str \| None` | `None` | 否 | 数值列名，None 时统计记录数 |
| `max` | `float \| None` | `None` | 否 | 进度条满格对应的数值，None 时用当前最大值 |
| `agg` | `str` | `"sum"` | 否 | 聚合方式：sum/mean/count/max/min/median |
| `sort` | `str` | `"desc"` | 否 | 排序：desc / asc / x / none |
| `top_n` | `int` | `10` | 否 | 最多显示多少行 |
| `title` | `str \| None` | `None` | 否 | 主标题 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `fmt` | `str` | `"compact"` | 否 | 数值格式 |
| `height` | `int` | `340` | 否 | 卡片最小高度（≥120） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `str` | `"light"` | 否 | 主题：light / dark |
| `link` | `str \| None` | `None` | 否 | 联动组名 |
| `max_rows` | `int \| None` | `200000` | 否 | 进入绘图的最大行数，None 表示不采样 |

## 参数详解

### `data` — 数据源（必填）

- **类型**：`pandas.DataFrame | dict | list`
- **默认值**：无
- **说明**：由 `frame.ensure_frame()` 统一处理：DataFrame 原样使用，`dict` / `list` 先转 DataFrame。行数超过 `max_rows` 时均匀抽样，提示写进 `chart.warnings`。只读取 `x` / `y` 两列，但整份数据都会被嵌入前端 payload。
- **取值建议**：正式代码用 DataFrame；只需要两列时先 `df = df[["渠道", "销售额"]]`，能减小页面体积。
- **示例**：`data=df`
- **常见错误**：`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`；`data=42` → `TypeError: 无法识别 data 类型 'int'，请传入 pandas.DataFrame（或 dict / list）。`

### `x` — 类目列名（默认 `None`，自动挑选）

- **类型**：`str | None`
- **默认值**：`None`
- **说明**：每一行对应的类目，通常是文本列。省略时走 `_pick_dim(df)`：先找第一个分类列（pandas category 或文本列），找不到再找第一个时间列；`edv.sample_df()` 里第一个分类列是「月份」。
- **取值建议**：类目数 3~20 个最合适；用业务维度（渠道、大区、门店），不要用高基数列（城市 × 产品组合）。
- **示例**：`x="渠道"`
- **常见错误**：列名写错 → `KeyError: "x（类目）列 '不存在' 不存在。当前可用的列有：..."`；没有分类/时间列且省略 x → `ValueError: progress 需要 x（类目列），例如 progress(df, x="渠道", y="完成量")；当前 DataFrame 里没有分类/时间列。`

### `y` — 数值列名（默认 `None`，统计记录数）

- **类型**：`str | None`
- **默认值**：`None`
- **说明**：进度条数值取自这一列，必须是数值 dtype。省略时按 `x` 分组计数：`agg` 被强制改成 `count`，自动标题里的度量名写成「记录数」。
- **取值建议**：完成量、金额、订单数用 `sum`；人均/单价类用 `mean`；想看每个类目的记录条数就省略该参数。
- **示例**：`y="销售额"`
- **常见错误**：`y="产品"` → `TypeError: y（数值）列 '产品' 需要是数值类型（当前是文本，例如 ['智能终端', '云服务', ...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `max` — 进度条满格值（默认 `None`，用当前最大值）

- **类型**：`int | float | None`
- **默认值**：`None`
- **说明**：写入 `spec["maxValue"]`。传了数值时，每行百分比 = `值 / max * 100`；不传（或传入非数值）时，用**当前类目里的最大值**作为满格，于是排名第一的行总是 100%。
  - 百分比会被夹取到 `[0, 100]`：超过 `max` 的显示 100%，负数显示 0%，但数值文本本身仍然显示真实值。
  - `max` 不参与 Python 侧校验，`max="abc"` 会被静默忽略（按 `None` 处理）。
- **取值建议**：
  - 目标是「相对排名」：省略 `max`，第一名 100%，读起来像进度。
  - 目标是「对照目标」：传 `max=目标值`，例如 `max=600000`，这样 30 万的行只显示 50%。
  - `max` 要和 `y` 同量纲；目标高于所有实际值时所有行都不会满格，这是正常的。
- **示例**：`max=600000`
- **常见错误**：无（非数值会被静默忽略；负数 max 会让所有行都显示 0%，请自行避免）

### `agg` — 聚合方式（默认 `"sum"`）

- **类型**：`str`
- **默认值**：`"sum"`
- **说明**：同一类目多行时的合并方式。合法值只有 `sum` / `mean` / `count` / `max` / `min` / `median`，其它值抛 `ValueError`。`y=None` 时该参数被忽略（强制 `count`）。
- **取值建议**：金额、件数用 `sum`；客单价、转化率用 `mean`；担心极值用 `median`。
- **示例**：`agg="mean"`
- **常见错误**：`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median`

### `sort` — 排序方式（默认 `"desc"`）

- **类型**：`str`
- **默认值**：`"desc"`
- **说明**：控制行的顺序，本图的前端渲染器**真的会排序**（与 `tile` 不同）：
  - `"desc"`（默认）：按数值从大到小，第一名在最上面。
  - `"asc"`：按数值从小到大，适合「短板清单」。
  - `"x"`：按类目自身顺序排（依赖 `data.orders` / `catRanker`，`sample_df` 的「月份」是 category 列，会按 1月→12月）。
  - `"none"` 或其它值：保持聚合后的原始顺序。
  - 该参数不做取值校验，写错不会报错，只会退化成不排序。
- **取值建议**：排行用 `desc`；进度落后清单用 `asc`；时间/有序类目用 `x`。
- **示例**：`sort="x"`
- **常见错误**：无（非法值静默退化为不排序）

### `top_n` — 最多显示多少行（默认 `10`）

- **类型**：`int`
- **默认值**：`10`
- **说明**：写入 `spec["topN"]`，前端 `limit = spec.topN || 10`；排序后只保留前 N 行，**不合并「其他」**，被截掉的行直接不显示。
  - 必须 ≥1 的整数（bool 会被拒绝）；传 `None` 时前端回退到 10。
  - Python 侧不截断数据，`chart.data["n"]` 仍是全部行数。
- **取值建议**：类目 ≤10 个时保持默认；类目多时调大（每行约 40px，会撑高卡片）或先用 `top_n` 聚焦头部。
- **示例**：`top_n=5`
- **常见错误**：`top_n=0` → `ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`

### `title` — 主标题（默认 `None`）

- **类型**：`str | None`
- **默认值**：`None`
- **说明**：`None` 时自动生成「`y` 进度」，`y` 也为 `None` 时是「记录数 进度」。
- **取值建议**：自动标题只说明指标，建议写成业务口径，例如「各大区销售目标完成度」。
- **示例**：`title="各大区销售目标完成度"`
- **常见错误**：无（任意字符串都接受）

### `subtitle` — 副标题（默认 `None`）

- **类型**：`str | None`
- **默认值**：`None`
- **说明**：标题下方的灰色小字，写口径、目标值、时间范围；会让卡片头部从 8px 变成 46px。
- **取值建议**：`"目标 60 万，2024 全年"` 这类一句话；两行以内。
- **示例**：`subtitle="目标 60 万，2024 全年"`

### `fmt` — 数值格式（默认 `"compact"`）

- **类型**：`str`
- **默认值**：`"compact"`
- **说明**：行首数值文本的格式，5 选 1：`compact`（1.2万 / 1.3亿）、`thousands`（千分位）、`raw`（原始值）、`currency`（¥ + 两位小数）、`percent`（只加 `%`，不乘 100）。百分比列固定是整数百分比（`toFixed(0)`），不受 `fmt` 影响。
- **取值建议**：金额大用 `compact`；需要精确读数用 `thousands`；比率列先乘以 100 再配 `percent`。
- **示例**：`fmt="thousands"`
- **常见错误**：`fmt="usd"` → `ValueError: fmt='usd' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 卡片最小高度（像素，默认 `340`）

- **类型**：`int`
- **默认值**：`340`
- **说明**：写入 `spec["height"]`；进度条列表属于自适应高度组件，页面里以 `min-height: 340px` 渲染，真实高度由行数撑开。通用校验要求 ≥120。
- **取值建议**：5 行左右保持 340；10 行以上建议 420~480，否则行会显得很挤。
- **示例**：`height=420`
- **常见错误**：`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题（默认 `"light"`）

- **类型**：`str`
- **默认值**：`"light"`
- **说明**：`light` 浅色底 + 深色文字；`dark` 深色底 + 浅色文字。每行的进度条颜色按主题色板轮换取色。
- **取值建议**：与页面其它图统一；大屏、夜间看板用 `dark`。
- **示例**：`theme="dark"`
- **常见错误**：`theme="blue"` → `ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `link` — 联动组名（默认 `None`）

- **类型**：`str | None`
- **默认值**：`None`
- **说明**：把本图加入某个联动组（相同字符串为一组）。同组其它图表被点击时，本图按点击的维度过滤后重算。
  - 进度条列表是 HTML 组件，**自身不绑定点击事件**，所以只能作为联动接收端，不能作为发起者。
  - 联动是否生效取决于本图数据里是否有被点击的那一列；没有该列就不会过滤。
- **取值建议**：用业务含义命名（`link="销售"`）；不要把本图当作唯一的联动源。
- **示例**：`link="销售"`
- **常见错误**：无（不做校验，非法值只会在前端退化为默认行为）

### `max_rows` — 最大参与绘制的行数（默认 `2000000`）

- **类型**：`int | None`
- **默认值**：`200000`
- **说明**：超出行数时做**均匀抽样**（不是简单截断），提示写进 `chart.warnings["warnings"]`，`n_total` 保留原始行数；传 `None` 关闭采样。传 `0` 会得到 0 行空图，传负数行为未定义（源码不做范围校验）。
- **取值建议**：进度条聚合后只有十几行，抽样对结果影响很小；需要精确 `mean` 时先自行 `groupby` 或传 `max_rows=None`。
- **示例**：`max_rows=50000`
- **常见错误**：无（不做取值校验；`max_rows=0` 会得到空图）

## 返回值

返回 `eazy_data_viz.Chart` 对象。

**Chart 的通用属性**

- `chart.spec`：`dict`，前端渲染配置。公共键有 `id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`、`roles`、`agg`、`fmt`、`sort`、`topN`、`xtitle`、`ytitle`、`xlim`、`ylim`、`legend`、`labels`、`zoom`、`drill`、`link`；本图额外带 `maxValue`。
- `chart.data`：嵌入前端的绘图 payload（不是 DataFrame）：`{"cols": [...], "rows": [...], "dims": [...], "measures": [...], "kinds": {...}, "orders": {...}, "n": 行数, "n_total": 原始行数}`。
- `chart.data_ref`：数据引用 id（`"d" + sha1 前 12 位`），内容相同的数据复用同一个 id。
- `chart.warnings`：`dict`，形如 `{"warnings": ["数据 1500 行，超过 max_rows=30，已均匀采样 30 行用于绘图。"], "n_total": 1500}`；没有降级时是 `{"warnings": [], "n_total": 行数}`。

**Chart 的通用方法**

- `chart.to_html(inline=True)`：返回完整 HTML 字符串（内联约 1.2~1.5MB）。
- `chart.save(path, inline=True)`：写文件、自动建目录、返回绝对路径。
- `chart.show(open_browser=None)`：浏览器打开。
- `chart.palette(name)`：换配色并返回 `self`。
- `chart.title`：只读属性，等于 `spec["title"]`。

**本图 `spec` 的专属事实**

- `roles = {"x": 类目列, "y": 数值列}`；`maxValue` 是进度条满格值（未传 `max` 时为 `null`）。
- `sort` 默认 `"desc"`、`topN` 默认 `10`（与 `tile` 不同，这两个参数在本图**会真正生效**）。
- `xtitle` / `ytitle` / `xlim` / `ylim` 恒为 `null`，`legend` / `labels` / `zoom` 恒为 `false`，`drill` 恒为 `null`。

### 本图 `chart.spec` 的真实结构

下面是 `edv.progress(df, x="渠道", y="销售额", max=200000)` 实际生成的 `spec`：

```json
{
  "id": "c1",
  "type": "progress",
  "title": "销售额 进度",
  "subtitle": null,
  "theme": "light",
  "height": 340,
  "dataRef": "d3cae6f6e0275",
  "roles": {
    "x": "渠道",
    "y": "销售额"
  },
  "agg": "sum",
  "fmt": "compact",
  "sort": "desc",
  "topN": 10,
  "xtitle": null,
  "ytitle": null,
  "xlim": null,
  "ylim": null,
  "legend": false,
  "labels": false,
  "zoom": false,
  "drill": null,
  "link": null,
  "maxValue": 200000.0
}
```

**验证返回值的小技巧**

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.progress(df, x="渠道", y="销售额", max=600000)
assert chart.spec["type"] == "progress"
assert chart.spec["roles"] == {"x": "渠道", "y": "销售额"}
assert chart.spec["maxValue"] == 600000.0
print(chart.title, chart.spec["sort"], chart.spec["topN"], chart.data["n"])
```

## 完整示例

以下示例都只依赖 `eazy_data_viz`，可直接复制运行。
### 示例 1：最简用法：各渠道销售额

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.progress(df, x="渠道", y="销售额")

print(chart.title)
print(chart.spec["roles"], chart.spec["maxValue"])
assert chart.spec["type"] == "progress"
```

**输出**：
- `销售额 进度`：默认标题 = 「度量名 + 进度」。
- `{'x': '渠道', 'y': '销售额'} None`：没传 `max`，`maxValue` 为 `None`，前端用当前最大值（直销 61.4 万）作满格，于是直销 100%、渠道代理 52.9 万、线上商城 48.9 万。

**验证**：`chart.spec["sort"] == "desc"`；页面里第一行的进度条是满的，后两行分别约占 86% / 80%。
### 示例 2：指定目标值：让百分比对照目标

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.progress(
    df,
    x="渠道",
    y="销售额",
    max=600000,
    fmt="thousands",
    title="各渠道销售目标完成度",
    subtitle="目标 60 万，2024 全年",
)

print(chart.spec["maxValue"], chart.spec["fmt"])
assert chart.spec["maxValue"] == 600000.0
```

**输出**：
- `600000.0 thousands`：满格值写进 spec，数值改为千分位显示；直销 61.4 万 → 100%（102.3% 被夹到 100%），渠道代理 52.9 万 → 88%，线上商城 48.9 万 → 81%。
- 百分比列固定显示整数（`toFixed(0)`），不受 `fmt` 影响。

**验证**：`chart.spec["maxValue"] == 600000.0`；把 `max` 去掉后三行百分比会变成 100% / 86% / 80%。
### 示例 3：省略 y：统计每个类目的记录数

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.progress(df, x="大区")

print(chart.title, chart.spec["agg"], chart.spec["roles"])
assert chart.spec["agg"] == "count"
```

**输出**：
- `记录数 进度 count {'x': '大区', 'y': None}`：省略 `y` 时按类目计数，`agg` 被强制为 `count`；4 行是华东 450、华北 450、华南 300、西部 300，其中前两行同为 450，都会是 100%。

**验证**：`chart.spec["roles"]["y"] is None`；`chart.spec["title"] == "记录数 进度"`。
### 示例 4：省略 x：自动挑类目列

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.progress(df, y="销售额", sort="x")

print(chart.spec["roles"]["x"], chart.spec["sort"])
assert chart.spec["roles"]["x"] == "月份"
```

**输出**：
- `月份 x`：`sample_df` 里第一个分类列是「月份」，自动按 12 个月分行；`sort="x"` 让月份按 1月→12月 排列（依赖 category 列的固定顺序），而不是按销售额高低。
- 12 行超过默认 `top_n=10`，只会显示前 10 行。

**验证**：`chart.spec["roles"]["x"] == "月份"`；把 `sort` 改回默认 `desc` 会变成按销售额降序。
### 示例 5：top_n 与 asc：只看落后清单

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.progress(
    df,
    x="省份",
    y="销售额",
    sort="asc",
    top_n=5,
    title="销售额后 5 名省份",
)

print(chart.spec["sort"], chart.spec["topN"])
assert chart.spec["sort"] == "asc"
assert chart.spec["topN"] == 5
```

**输出**：
- `asc 5`：按销售额升序、只保留前 5 行（即最低的 5 个省）。
- 页面显示 5 行；10 个省份里被截掉的 5 行不会合并成「其他」，直接不显示。

**验证**：`chart.spec["topN"] == 5`；把 `sort` 改成 `desc` 会变成销售额最高的 5 个省。
### 示例 6：聚合方式与深色主题

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.progress(
    df,
    x="产品",
    y="销售额",
    agg="mean",
    fmt="raw",
    height=300,
    theme="dark",
    title="各产品平均单笔销售额",
)

print(chart.spec["agg"], chart.spec["height"], chart.spec["theme"])
assert chart.spec["agg"] == "mean"
assert chart.spec["height"] == 300
```

**输出**：
- `mean 300 dark`：聚合、高度、主题写入 spec。
- 4 个产品的平均单笔销售额是 1430.94 / 1201.73 / 1085.10 / 630.44——`mean` 是平均单笔口径，与 `sum` 的总量口径不同，排序与长度都会变。
- 深色主题下文字变浅、进度条换成深色系色板。

**验证**：`chart.spec["agg"] == "mean"`；对比示例 1 的 `sum` 可见各产品差距大得多。
### 示例 7：大数据采样与联动参数

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.progress(
    df,
    x="渠道",
    y="销售额",
    max_rows=100,
    link="销售",
)

print(chart.data["n"], chart.warnings["n_total"])
print(chart.spec["link"])
assert chart.data["n"] == 100
assert chart.spec["link"] == "销售"
```

**输出**：
- `100 1500`：只有 100 行进入绘图，原始行数在 `n_total`。
- 提示：`['数据 1500 行，超过 max_rows=100，已均匀采样 100 行用于绘图。']`；`销售` 是联动组名，进度条列表自身不响应点击，但可被同组图表筛选。

**验证**：`len(chart.data["rows"]) == 100`；传 `max_rows=None` 后 `chart.warnings["warnings"] == []`。

## 常见错误

- **`y` 传了文本列**
  - `progress(df, x="大区", y="产品")` → `TypeError: y（数值）列 '产品' 需要是数值类型（当前是文本，例如 ['智能终端', '云服务', ...]）。请先用 pd.to_numeric() 清洗，或换一列。`
  - 数值列里混有 `"12.3万"` 这类带单位文本时同样会报错：先去掉单位再转数字，或 `pd.to_numeric(errors="coerce")` 后决定 `dropna()` / `fillna(0)`。

- **以为 `max` 会自动算成 100% 以外的比例**
  - 不传 `max` 时满格是当前最大值，第一名永远 100%；传了 `max=目标值` 才是「对照目标」的完成度。
  - `max` 与 `y` 必须同量纲；`max` 传非数值会被静默忽略（不会报错，容易误以为是 bug）。

- **省略 `x` 但数据里没有分类列**
  - 全是数值列时 → `ValueError: progress 需要 x（类目列），例如 progress(df, x="渠道", y="完成量")；当前 DataFrame 里没有分类/时间列。`
  - 先把数值列分箱（`pd.cut`），或显式传一个文本列。

- **`sort` / `top_n` / `height` / `fmt` 传了非法值**
  - `sort` 不做校验，写错会退化为不排序；`top_n` 必须 ≥1，否则 `ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`。
  - `fmt` 只能是 compact、thousands、raw、percent、currency；`theme` 只能是 light、dark；`height` 必须 ≥120。

## 相关图表

- `ring_progress`：单个指标的达成率圆环，本图是它的「多类目列表版」。
- `tile`：同样按类目聚合，用方块颜色表达量级；不需要读百分比时更省空间。
- `group_kpi`：把几个关键数字做成卡片，强调绝对值与环比，不做进度条。
- `bar`：需要精确比较数值大小时用柱状图；本图的条形只是视觉辅助，不是精确刻度。
- `kpi`：单值指标卡，带环比箭头，适合 Dashboard 顶部。
