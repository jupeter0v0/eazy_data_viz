# `pictorial` — 象形柱图（图形符号填充的柱状图）

> 用重复的图形符号（圆点、方块、菱形……）填满柱子，柱子长度表达数值，图形感强、适合大屏和汇报页。
> 适合：5~12 个类目的「量级对比 + 视觉冲击」（各产品销售额、各大区订单量）、需要摆在大屏首屏的重点图、单个维度即可说清的场景。
> 不适合：需要精确读数的对比（用 `bar`）、多系列分组/堆叠（本图只有一根柱子）、时间趋势（用 `line` / `area`）、类目超过 15 个（符号会挤成一团）。

## 函数签名

```python
eazy_data_viz.pictorial(
    data,
    x,
    y=None,
    *,
    symbol="circle",
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
    labels=True,
    zoom="auto",
    drill=None,
    link=None,
    max_rows=200000,
) -> Chart
```

签名要点：

- `x` 必填（类目列），`y` 可省略——省略时按类目计数，`agg` 被强制为 `count`。
- `symbol` 只接受 `circle` / `rect` / `roundRect` / `diamond` / `triangle` 五种。
- 本图**没有** `color` 参数：一个类目一根柱子，不支持多系列；想按维度拆色请用 `bar` 或 `area_pct`。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list` | `—` | 是 | 数据源 |
| `x` | `str` | `—` | 是 | 类目列名 |
| `y` | `str \| None` | `None` | 否 | 数值列名，None 时统计记录数 |
| `symbol` | `str` | `"circle"` | 否 | 填充符号形状 |
| `agg` | `str` | `"sum"` | 否 | 聚合方式 |
| `sort` | `str \| None` | `None` | 否 | 排序：None / x / asc / desc |
| `top_n` | `int \| None` | `None` | 否 | 只保留前 N 项（仅写入 spec） |
| `title` | `str \| None` | `None` | 否 | 主标题 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `xtitle` | `str \| None` | `None` | 否 | X 轴标题 |
| `ytitle` | `str \| None` | `None` | 否 | Y 轴标题 |
| `xlim` | `tuple \| None` | `None` | 否 | X 轴范围（本图不生效） |
| `ylim` | `tuple \| None` | `None` | 否 | Y 轴范围 |
| `fmt` | `str` | `"compact"` | 否 | 数值格式 |
| `height` | `int` | `380` | 否 | 图表高度（≥120），也决定符号大小 |
| `theme` | `str` | `"light"` | 否 | 主题：light / dark |
| `legend` | `bool` | `False` | 否 | 图例开关（本图不渲染图例） |
| `labels` | `bool` | `True` | 否 | 是否在柱顶显示数值 |
| `zoom` | `str` | `"auto"` | 否 | 缩放开关（本图不生效） |
| `drill` | `str \| list \| None` | `None` | 否 | 下钻维度列 |
| `link` | `str \| None` | `None` | 否 | 联动组名 |
| `max_rows` | `int \| None` | `200000` | 否 | 进入绘图的最大行数 |

## 参数详解

### `data` — 数据源（必填）
- **类型**：`pandas.DataFrame | dict | list`
- **默认值**：无
- **说明**：`frame.ensure_frame()` 统一转换；行数超过 `max_rows` 时均匀抽样，提示写入 `chart.warnings`。只读取 `x` / `y` 两列，但整份数据都会嵌入前端 payload。
- **取值建议**：正式代码传 DataFrame；只需要两列时先 `df[["产品", "销售额"]]`，能显著减小 HTML 体积。
- **示例**：`data=df`
- **常见错误**：`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`；空表 → `ValueError: 数据为空（0 行），无法绘图。`

### `x` — 类目列名（必填）
- **类型**：`str`
- **默认值**：无
- **说明**：每个取值一根柱子，柱子顺序默认按分组首次出现顺序（不排序），显式传 `sort` 才改变顺序。必须存在于 DataFrame，文本列或时间列都可以。
- **取值建议**：基数 5~12 的维度最合适；月份、大区、产品这类业务维度；不要用「城市+产品」组合出的高基数列。
- **示例**：`x="产品"`
- **常见错误**：省略 → `ValueError: pictorial 需要 x（类目列），例如 pictorial(df, x="产品", y="销量")。`；列名写错 → `KeyError: "x（类目）列 '不存在' 不存在。当前可用的列有：..."`

### `y` — 数值列名（默认 `None`，统计记录数）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：柱子长度取这一列聚合后的值，必须是数值 dtype（文本列会先 `pd.to_numeric` 尝试，失败抛 `TypeError`）。省略时按 `x` 计数，`agg` 被强制为 `count`，自动标题里的度量名变成「记录数」。
- **取值建议**：金额、销量、订单量用 `sum`；人均/单价用 `mean`；想看覆盖量就省略该参数。
- **示例**：`y="销售额"`
- **常见错误**：`y="产品"` → `TypeError: y（数值）列 '产品' 需要是数值类型（当前是文本，例如 ['智能终端', ...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `symbol` — 填充符号（默认 `"circle"`）
- **类型**：`str`
- **默认值**：`"circle"`
- **说明**：柱子由重复的符号拼成，符号会被裁切（symbolClip）以精确表达长度。可选值与视觉感受：
  - `circle`：圆点，最通用、最像「象形柱」。
  - `rect`：小方块，密排后接近实心柱子，适合大屏远看。
  - `roundRect`：圆角方块，介于两者之间，偏柔和。
  - `diamond`：菱形，装饰性强，适合强调「排名」。
  - `triangle`：三角形，指向性最强，适合「增长/目标」语境。
- **取值建议**：同一页多张象形柱图用同一种符号；符号越大越花哨，`diamond` / `triangle` 建议配合 `labels=True` 保证可读。
- **示例**：`symbol="roundRect"`
- **常见错误**：`symbol="star"` → `ValueError: symbol='star' 不支持，可选：circle / rect / roundRect / diamond / triangle`

### `agg` — 聚合方式（默认 `"sum"`）
- **类型**：`str`
- **默认值**：`"sum"`
- **说明**：同一类目多行时的合并方式，合法值 `sum` / `mean` / `count` / `max` / `min` / `median`；`y=None` 时被强制为 `count`。聚合在前端完成，Python 只校验取值。
- **取值建议**：总量用 `sum`，客单价/转化率用 `mean`，怕极值用 `median`。
- **示例**：`agg="mean"`
- **常见错误**：`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median`

### `sort` — 排序方式（默认 `None`，保持原始顺序）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：**本图的排序在前端生效**：`"x"` 按类目自身顺序（依赖类目的固定顺序，如月份 1月→12月），`"asc"` / `"desc"` 按柱子数值排序，`None` 保持分组首次出现顺序。不做取值校验，写错会退化为不排序（`sort="x"` 只在类目是有序 category 时才有意义）。
- **取值建议**：排行用 `desc`；月份/季度等有序维度用 `x`；不确定时留 `None`。
- **示例**：`sort="desc"`
- **常见错误**：无（非法值静默退化为不排序）

### `top_n` — 只保留前 N 项（默认 `None`）
- **类型**：`int | None`
- **默认值**：`None`
- **说明**：写入 `spec["topN"]` 并做 ≥1 整数校验，但**本图的渲染器不读取 topN**：不截断、不合并「其他」、不做「TOP N」标注。真正的截断请在 Python 侧完成（`df.nlargest(...)` 或 `groupby` 后取头部）。
- **取值建议**：想要 TOP 10 效果时先自己筛数据再传；本参数留 `None`。
- **示例**：`top_n=5`（只写进 spec，页面不变）
- **常见错误**：`top_n=0` → `ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`

### `title` — 主标题（默认 `None`，自动生成）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：`None` 时自动生成「`y` 按 `x`」，`y=None` 时是「记录数 按 `x`」。
- **取值建议**：自动标题会把列名原样拼进去，列名是英文/缩写时建议手写中文标题。
- **示例**：`title="各产品销售额对比"`

### `subtitle` — 副标题（默认 `None`）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：标题下方灰色小字，写时间范围或口径；会让卡片头部变高。
- **取值建议**：一行以内，例如 `"2024 全年 · 含税"`。
- **示例**：`subtitle="2024 全年 · 含税"`

### `xtitle` — X 轴标题（默认 `None`）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：X 轴下方的轴标题；`None` 时回退成 `x` 列名。
- **取值建议**：列名本身已经清楚时不用传；要写业务口径时再传。
- **示例**：`xtitle="产品线"`

### `ytitle` — Y 轴标题（默认 `None`）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：Y 轴左侧的轴标题；`None` 时回退成 `y` 列名。
- **取值建议**：指标有单位时写进标题，如 `"销售额（万元）"`，避免和 `fmt` 重复。
- **示例**：`ytitle="销售额（万元）"`

### `xlim` — X 轴范围（默认 `None`，本图不生效）
- **类型**：`tuple(min, max) | None`
- **默认值**：`None`
- **说明**：只做格式校验后写入 spec，但**象形柱图的类目轴是 category 轴，渲染器不应用 xlim**，传了也不会改变显示。
- **取值建议**：不用传；需要控制显示范围请先过滤数据。
- **示例**：`xlim=(0, 5)`
- **常见错误**：`xlim=(1, 2, 3)` → `ValueError: xlim 需要是 (最小值, 最大值) 两元组，例如 xlim=(0, 100)`

### `ylim` — Y 轴范围（默认 `None`，本图生效）
- **类型**：`tuple(min, max) | None`
- **默认值**：`None`
- **说明**：数值轴的范围，两个元素都必须是数值或 `None`。**象形柱图会应用 ylim**（`applyLim`），常用于从 0 开始、或压掉异常值。
- **取值建议**：想让柱子从固定起点长起时用 `ylim=(0, 1000000)`；上限要比最大值大一点，留出 `labels` 的空间。
- **示例**：`ylim=(0, 600000)`
- **常见错误**：`ylim=5` → `ValueError: ylim 需要是 (最小值, 最大值) 两元组，例如 ylim=(0, 100)`

### `fmt` — 数值格式（默认 `"compact"`）
- **类型**：`str`
- **默认值**：`"compact"`
- **说明**：Y 轴刻度、柱顶 `labels`、tooltip 的数值格式，5 选 1：`compact` / `thousands` / `raw` / `currency` / `percent`（只加 `%`，不乘 100）。
- **取值建议**：金额大用 `compact`；需要精确读数用 `thousands`；比率先乘 100 再配 `percent`。
- **示例**：`fmt="thousands"`
- **常见错误**：`fmt="usd"` → `ValueError: fmt='usd' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 图表高度（像素，默认 `380`）
- **类型**：`int`
- **默认值**：`380`
- **说明**：写进 `spec["height"]`，同时**决定符号大小**：`symbolSize = clamp(round(height / 26), 7, 18)`。例如 380 → 15px、300 → 12px、260 → 10px、520 → 20 但被夹到 18px。通用校验要求 ≥120。
- **取值建议**：一屏两张图时用 300~340；单张大图 380~480；不需要再单独调符号大小。
- **示例**：`height=300`
- **常见错误**：`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `theme` — 主题（默认 `"light"`）
- **类型**：`str`
- **默认值**：`"light"`
- **说明**：`light` 浅色底；`dark` 深色底，轴、文字、符号颜色随主题切换。
- **取值建议**：与同页其它图一致；大屏用 `dark`。
- **示例**：`theme="dark"`
- **常见错误**：`theme="blue"` → `ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `legend` — 图例开关（默认 `False`）
- **类型**：`bool`
- **默认值**：`False`
- **说明**：只写入 `spec["legend"]`；象形柱图只有一个系列，**渲染器不画图例**，传 `True` 也不会出现图例。
- **取值建议**：保持默认；确实需要图例说明时用 `subtitle` 或轴标题替代。
- **示例**：`legend=True`（写入 spec，页面无图例）

### `labels` — 柱顶数值标签（默认 `True`）
- **类型**：`bool`
- **默认值**：`True`
- **说明**：是否在柱子顶部显示数值文本（按 `fmt` 格式化）。象形柱的符号会占满柱子宽度，标签位置在柱顶上方。
- **取值建议**：类目少、数值差异大时保持 `True`；柱子很密或高度不足时改 `False`，靠 tooltip 读数。
- **示例**：`labels=False`

### `zoom` — 缩放（默认 `"auto"`，本图不生效）
- **类型**：`str`
- **默认值**：`"auto"`
- **说明**：只写入 spec；象形柱图的渲染器**不生成 dataZoom**，传 `True` / `"auto"` 都不会出现缩放条。
- **取值建议**：不用传；类目太多请先过滤数据，而不是依赖缩放。
- **示例**：`zoom="none"`

### `drill` — 下钻维度（默认 `None`）
- **类型**：`str | list[str] | None`
- **默认值**：`None`
- **说明**：点击柱子按维度逐级下钻。可以传单个列名或列名列表，列表里每一层对应一次点击；第一层会自动作为 `roles.x` 使用，点击「其他」不触发。注意本图是 ECharts 画布，**点击事件可用**，与 HTML 类图不同。
- **取值建议**：`drill=["大区", "省份"]` 做两级下钻；列必须是 df 里真实存在的列。
- **示例**：`drill=["大区", "省份"]`
- **常见错误**：`drill=[]` → `ValueError: drill 不能是空列表；不需要下钻请传 drill=None。`；列不存在 → `KeyError: "下钻维度列 '不存在' 不存在。..."`

### `link` — 联动组名（默认 `None`）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：相同字符串的图属于同一联动组；点击本图柱子会把该维度值广播给同组图表做过滤。本图既能发起联动也能接收联动。
- **取值建议**：同一页所有图用同一个组名（如 `"销售"`），页面顶部会出现联动筛选条。
- **示例**：`link="销售"`

### `max_rows` — 最大参与绘制的行数（默认 `200000`）
- **类型**：`int | None`
- **默认值**：`200000`
- **说明**：超出行数时均匀抽样，提示写入 `chart.warnings["warnings"]`，`n_total` 保留原始行数；`None` 关闭采样，`0` 得到空图。
- **取值建议**：聚合类图表用默认值即可；需要精确 `mean` 时先自行 `groupby` 或传 `None`。
- **示例**：`max_rows=50000`

## 返回值

返回 `eazy_data_viz.Chart` 对象。

**Chart 的通用属性**

- `chart.spec`：`dict`。公共键 `id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`、`roles`、`agg`、`fmt`、`sort`、`topN`、`xtitle`、`ytitle`、`xlim`、`ylim`、`legend`、`labels`、`zoom`、`drill`、`link`；本图额外带 `symbol`。
- `chart.data`：嵌入前端的绘图 payload：`{"cols", "rows", "dims", "measures", "kinds", "orders", "n", "n_total"}`；`chart.data_ref` 是数据引用 id（`"d" + sha1 前 12 位`），相同内容复用同一个 id。
- `chart.warnings`：`dict`，形如 `{"warnings": ["数据 1500 行，超过 max_rows=100，已均匀采样 100 行用于绘图。"], "n_total": 1500}`。

**Chart 的通用方法**

- `chart.to_html(inline=True)`：完整 HTML 字符串（内联约 1.2~1.5MB）。
- `chart.save(path, inline=True)`：写文件、自动建目录、返回绝对路径。
- `chart.show(open_browser=None)` / `chart.palette(name)`（换配色并返回 `self`）/ `chart.title`（等于 `spec["title"]`）。

**本图 `spec` 的专属事实**

- `roles = {"x": 类目列, "y": 数值列}`，`y` 省略时为 `None`、此时 `agg` 是 `"count"`。
- 专属键只有 `symbol`；`xlim` 写入但不生效、`ylim` 生效、`topN` 不截断、`zoom` 不生成 dataZoom、`legend` 不画图例；`labels` 默认 `True`、`sort` 默认 `None`、`height` 默认 `380`。

### 本图 `chart.spec` 的真实结构

下面是 `edv.pictorial(df, x="产品", y="销售额")` 实际生成的 `spec`：

```json
{
  "id": "c1",
  "type": "pictorial",
  "title": "销售额 按 产品",
  "subtitle": null,
  "theme": "light",
  "height": 380,
  "dataRef": "d3cae6f6e0275",
  "roles": {"x": "产品", "y": "销售额"},
  "agg": "sum",
  "fmt": "compact",
  "sort": null,
  "topN": null,
  "xtitle": null,
  "ytitle": null,
  "xlim": null,
  "ylim": null,
  "legend": false,
  "labels": true,
  "zoom": "auto",
  "drill": null,
  "link": null,
  "symbol": "circle"
}
```

**验证返回值的小技巧**

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.pictorial(df, x="产品", y="销售额")
assert chart.spec["type"] == "pictorial"
assert chart.spec["roles"] == {"x": "产品", "y": "销售额"}
assert chart.spec["labels"] is True and chart.spec["symbol"] == "circle"
print(chart.title, chart.spec["height"], chart.data["n"])
```

## 完整示例

以下示例都只依赖 `eazy_data_viz`，可直接复制运行。

### 示例 1：最简用法：各产品销售额
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.pictorial(df, x="产品", y="销售额")

print(chart.title, chart.spec["height"])
assert chart.spec["roles"] == {"x": "产品", "y": "销售额"}
assert chart.spec["symbol"] == "circle"
```

**输出**：
- `销售额 按 产品`：自动标题 = 「度量 + 按 + 维度」。
- 4 根柱子：智能终端 53.7万 > 行业软件 45.1万 > 云服务 40.8万 > 运维服务 23.6万，柱顶显示 compact 数值。
- 符号为圆点，尺寸 15px（380 / 26 ≈ 15）。

**验证**：`chart.spec["sort"] is None`——柱子顺序等于分组首次出现顺序，不是数值顺序。

### 示例 2：换符号、关标签、压高度
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.pictorial(
    df,
    x="大区",
    y="订单数",
    symbol="roundRect",
    labels=False,
    height=260,
    fmt="thousands",
)

print(chart.spec["symbol"], chart.spec["height"], chart.spec["labels"])
assert chart.spec["symbol"] == "roundRect"
assert chart.spec["labels"] is False
```

**输出**：
- `roundRect 260 False`：符号换成圆角方块；高度 260 → 符号尺寸 `round(260/26) = 10px`，比默认更小。
- 柱顶不再显示数值，只能通过 tooltip 或轴读数；`fmt="thousands"` 让 Y 轴刻度显示为 `1,000` 这类千分位。

**验证**：把 `height` 改成 520 后 `symbolSize` 被夹到最大值 18px（`min(18, ...)`）。

### 示例 3：省略 y：统计每个类目的记录数
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.pictorial(df, x="大区")

print(chart.title, chart.spec["agg"], chart.spec["roles"])
assert chart.spec["agg"] == "count"
assert chart.spec["roles"]["y"] is None
```

**输出**：
- `记录数 按 大区 count {'x': '大区', 'y': None}`：省略 `y` 时按类目计数，标题里的度量名变成「记录数」。
- 4 根柱子分别是 450、450、300、300，华东/华北一样长。
- 计数模式下 `fmt` 对整数没有可见影响。

**验证**：`chart.spec["title"] == "记录数 按 大区"`；传 `y` 后 `agg` 恢复为默认 `sum`。

### 示例 4：排序：按类目顺序排月份
```python
import eazy_data_viz as edv

df = edv.sample_df()

by_x = edv.pictorial(df, x="月份", y="销售额", sort="x")
by_desc = edv.pictorial(df, x="月份", y="销售额", sort="desc")

print(by_x.spec["sort"], by_desc.spec["sort"])
assert by_x.spec["sort"] == "x"
assert by_desc.spec["sort"] == "desc"
```

**输出**：
- `x desc`：`sort="x"` 时 12 个月按 1月→12月 的固定顺序排（月份是 category 列，顺序有意义）。
- `sort="desc"` 时变成按销售额从高到低，5月（17.5万）排第一；两种排序都只影响显示顺序，`chart.data` 里的行顺序不变。

**验证**：`sort=None`（默认）时保持分组首次出现顺序，通常与数据里月份出现顺序一致。

### 示例 5：标题、轴标题、Y 轴范围与主题
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.pictorial(
    df,
    x="渠道",
    y="销售额",
    title="各渠道销售额",
    subtitle="2024 全年 · 含税",
    xtitle="销售渠道",
    ytitle="销售额（万元）",
    ylim=(0, 700000),
    fmt="compact",
    theme="dark",
    symbol="diamond",
)

print(chart.spec["xtitle"], chart.spec["ytitle"], chart.spec["ylim"])
assert list(chart.spec["ylim"]) == [0, 700000]
assert chart.spec["theme"] == "dark"
```

**输出**：
- `销售渠道 销售额（万元） (0, 700000)`：轴标题与范围写入 spec；Y 轴从 0 起、到 70 万，直销（61.4万）离顶部还有一段距离。
- 深色主题下背景变深、轴与符号颜色变浅；`diamond` 符号让三根柱子带明显的棱角。`xlim` 在本图不生效，所以上面没有传。

**验证**：`chart.spec["ylim"] == (0, 700000)`；把 `ylim` 去掉后 Y 轴上限会自适应到 61.4万附近（spec 里以 `[0, 700000]` 列表形式保存）。

### 示例 6：下钻与联动一起用
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.pictorial(
    df,
    x="大区",
    y="销售额",
    drill=["大区", "省份"],
    link="销售",
)

print(chart.spec["drill"], chart.spec["roles"].get("_extra"))
assert chart.spec["drill"] == ["大区", "省份"]
assert chart.spec["link"] == "销售"
```

**输出**：
- `['大区', '省份'] ['大区', '省份']`：下钻层级写入 spec，`roles` 里同时记录 `_extra` 供前端取层级。
- 点击柱子会按「大区 → 省份」逐级刷新；同一页面里 `link="销售"` 的其它图会跟着过滤。
- 点击类目「其他」不会触发下钻。

**验证**：`chart.spec["roles"]["_extra"] == ["大区", "省份"]`；`drill="省份"` 传单个字符串等价于 `["省份"]`。
