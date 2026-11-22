# `radar` — 雷达图（多指标画像）

> 每个类目一根轴，把多个指标摊在一个多边形里：一眼看出「谁哪一项强、形状像不像」。
> 适合：3~8 个指标的横向画像（产品能力对比、员工/门店多维评分、区域综合表现）、同一对象在不同系列下的形状对比。
> 不适合：精确数值比较（用 `bar` / `table`）、指标之间没有共同量纲时硬凑（雷达图不适合把金额和比率放一起）、指标超过 10 个（轴太密）、只有 1~2 个指标（用柱状图更清楚）。

## 函数签名

```python
eazy_data_viz.radar(
    data,
    x,
    y=None,
    color=None,
    *,
    max=None,
    agg=None,
    sort=None,
    top_n=None,
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    xlim=None,
    ylim=None,
    fmt="compact",
    height=400,
    abs_height=False,
    theme="light",
    legend=True,
    labels=False,
    zoom=False,
    drill=None,
    link=None,
    max_rows=2000000,
) -> Chart
```

签名要点：

- `y` 在签名里可省略，**但雷达图必须传 `y`**：渲染器要求同时有指标列和数值列，`y=None` 时不会报错，只会渲染成空白图。
- 指标轴 = `x` 列的去重取值，系列 = `color` 列的去重取值；省略 `color` 时只有一个系列。
- `agg` 默认 `"mean"`（与其它图的 `"sum"` 不同），因为雷达图通常画「平均值/评分」。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list` | `—` | 是 | 数据源 |
| `x` | `str` | `—` | 是 | 指标轴列名（每个取值一根轴） |
| `y` | `str \| None` | `None` | 否 | 数值列名（实际必传） |
| `color` | `str \| None` | `None` | 否 | 系列列名，一个取值一个多边形 |
| `max` | `float \| None` | `None` | 否 | 所有轴的统一上限 |
| `agg` | `str` | `"mean"` | 否 | 聚合方式 |
| `sort` | `str \| None` | `None` | 否 | 轴顺序：None / x / asc / desc |
| `top_n` | `int \| None` | `None` | 否 | 只保留前 N 项（本图不生效） |
| `title` | `str \| None` | `None` | 否 | 主标题 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `xtitle` | `str \| None` | `None` | 否 | X 轴标题（本图不生效） |
| `ytitle` | `str \| None` | `None` | 否 | Y 轴标题（本图不生效） |
| `xlim` | `tuple \| None` | `None` | 否 | X 轴范围（本图不生效） |
| `ylim` | `tuple \| None` | `None` | 否 | Y 轴范围（本图不生效） |
| `fmt` | `str` | `"compact"` | 否 | 数值格式 |
| `height` | `int` | `400` | 否 | 图表高度（≥120） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `str` | `"light"` | 否 | 主题：light / dark |
| `legend` | `bool` | `True` | 否 | 是否显示系列图例 |
| `labels` | `bool` | `False` | 否 | 数值标签（本图不生效） |
| `zoom` | `bool` | `False` | 否 | 缩放（本图不生效） |
| `drill` | `str \| list \| None` | `None` | 否 | 下钻维度列 |
| `link` | `str \| None` | `None` | 否 | 联动组名 |
| `max_rows` | `int \| None` | `200000` | 否 | 进入绘图的最大行数 |

## 参数详解

### `data` — 数据源（必填）
- **类型**：`pandas.DataFrame | dict | list`
- **默认值**：无
- **说明**：`frame.ensure_frame()` 统一转换；只读取 `x` / `color` / `y` 三列，但整份数据都会嵌入 payload；超过 `max_rows` 时均匀抽样并写 `warnings`。
- **取值建议**：多指标对比时数据通常是「长表」（指标列 + 数值列），不要传宽表——宽表请先 `melt` 成长表。
- **示例**：`data=df`

### `x` — 指标轴列名（必填）
- **类型**：`str`
- **默认值**：无
- **说明**：每个去重取值对应一根雷达轴（indicator），轴名超过 12 个字会被截断。轴的顺序默认按数据出现顺序，可用 `sort` 调整。缺失值会归到「—」轴。
- **取值建议**：3~8 个指标最合适；指标名要短（「满意度」「响应速度」），长句会被截断。
- **示例**：`x="产品"`
- **常见错误**：省略 → `ValueError: radar 需要 x（指标项），例如 radar(df, x="能力项", y="得分", color="对象")。`

### `y` — 数值列名（默认 `None`，但实际必传）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：每个轴上的值，必须是数值 dtype。**省略时不会报错**，而是 `agg` 被强制成 `count`、`roles.y` 为 `None`，前端渲染器检测到没有数值列直接返回空图（画布空白，不是报错）。
- **取值建议**：永远显式传 `y`；同一张雷达图的各指标最好同量纲（都是 0~100 的评分，或都是金额），必要时用 `max` 统一上限。
- **示例**：`y="销售额"`
- **常见错误**：`y="产品"` → `TypeError: y（数值）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `color` — 系列列名（默认 `None`，单系列）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：每个去重取值画一个多边形（一个 `type:"radar"` 系列）。省略时只有一个系列，不画图例。**注意**：`color` 的取值不是「每个指标一色」，而是「每个对象一个多边形」。
- **取值建议**：对比 2~5 个对象（大区、产品线、渠道）；超过 5 个系列会互相遮挡。
- **示例**：`color="大区"`
- **常见错误**：`color` 列名不存在 → `KeyError: "color（分组）列 'xxx' 不存在。当前可用的列有：..."`

### `max` — 所有轴的统一上限（默认 `None`，自动计算）
- **类型**：`int | float | None`
- **默认值**：`None`
- **说明**：写入 `spec["maxValue"]`，所有 indicator 共用这个最大值，用来统一量纲。不传时每个轴各算一个上限：`ceil(该轴最大系列值 × 1.1 × 10) / 10`（向上取整留 10% 留白），没有正值时用 1。传非数值会被静默忽略（按 `None` 处理）。
- **取值建议**：指标量纲不同（金额 vs 比率）时先做归一化，否则雷达图会失真；只有各轴量级接近时才直接用自动上限。
- **示例**：`max=200000`

### `agg` — 聚合方式（默认 `"mean"`）
- **类型**：`str`
- **默认值**：`"mean"`
- **说明**：同一 (指标, 系列) 多行时的合并方式，合法值 `sum` / `mean` / `count` / `max` / `min` / `median`，默认 `mean`（与 `bar` 的 `sum` 不同）。`y=None` 时被强制为 `count`。
- **取值建议**：评分/比率用 `mean`；总量对比用 `sum`；想看最大单笔用 `max`。混用 `sum` 时注意各指标量级会被放大。
- **示例**：`agg="sum"`
- **常见错误**：`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, unique, max, min, median`

### `sort` — 轴顺序（默认 `None`，按数据出现顺序）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：本图的排序在前端生效**：`"x"` 按指标自身顺序（类目有固定顺序时最有用），`"asc"` / `"desc"` 按各指标全部系列合计值排序，`None` 保持数据出现顺序。非法值静默退化为不排序。
- **取值建议**：想固定指标顺序（例如「销售额、利润、订单数、客户数」的业务顺序）时，把 `x` 列设为 category 并传 `sort="x"`；想按重要性排行用 `desc`。
- **示例**：`sort="desc"`

### `top_n` — 只保留前 N 项（默认 `None`）
- **类型**：`int | None`
- **默认值**：`None`
- **说明**：写入 `spec["topN"]` 并做 ≥1 整数校验，但**雷达图渲染器不读取 topN**：指标轴与系列都不会被截断。要限制指标数量请在 Python 侧筛选 `x` 的取值。
- **取值建议**：保持 `None`，自己控制指标数量（3~8 个）。
- **示例**：`top_n=5`（只写 spec，页面不变）
- **常见错误**：`top_n=0` → `ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`

### `title` — 主标题（默认 `None`，自动生成）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：`None` 时自动生成「`y` 雷达图」，`y=None` 时是「记录数 雷达图」。
- **取值建议**：自动标题只含度量名，建议手写「2024 各产品综合能力对比」这类业务标题。
- **示例**：`title="各产品综合能力对比"`

### `subtitle` — 副标题（默认 `None`）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：标题下方灰色小字，写口径或时间范围。
- **取值建议**：例如 `"5 分制评分，均值口径"`。
- **示例**：`subtitle="5 分制评分，均值口径"`

### `xtitle` / `ytitle` — 轴标题（默认 `None`，本图不生效）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：雷达图没有直角坐标轴，两个参数只写入 spec，渲染器不绘制轴标题。
- **取值建议**：不要依赖；需要说明时用 `subtitle`。
- **示例**：`xtitle="指标"`

### `xlim` / `ylim` — 轴范围（默认 `None`，本图不生效）
- **类型**：`tuple(min, max) | None`
- **默认值**：`None`
- **说明**：只做「(最小值, 最大值) 两元组」格式校验后写入 spec；雷达图没有线性轴，渲染器不应用。控制量纲请用 `max`。
- **取值建议**：不用传；要统一上限用 `max`。
- **示例**：`xlim=(0, 5)`
- **常见错误**：`xlim=(1, 2, 3)` → `ValueError: xlim 需要是 (最小值, 最大值) 两元组，例如 xlim=(0, 100)`

### `fmt` — 数值格式（默认 `"compact"`）
- **类型**：`str`
- **默认值**：`"compact"`
- **说明**：tooltip 里各指标值的格式，5 选 1：`compact` / `thousands` / `raw` / `currency` / `percent`（只加 `%`，不乘 100）。不影响轴上限的计算。
- **取值建议**：金额用 `compact`；评分用 `raw`（保留小数），避免 `compact` 把 4.5 分显示成「4.5」以外的形式。
- **示例**：`fmt="raw"`
- **常见错误**：`fmt="usd"` → `ValueError: fmt='usd' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 图表高度（像素，默认 `400`）
- **类型**：`int`
- **默认值**：`400`
- **说明**：写进 `spec["height"]`，同时决定雷达图的可用画布大小；通用校验要求 ≥120。雷达图比其它图更吃高度，太矮时轴名会重叠。
- **取值建议**：3~5 个指标用 360~400；6~8 个指标建议 420~480。
- **示例**：`height=460`
- **常见错误**：`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题（默认 `"light"`）
- **类型**：`str`
- **默认值**：`"light"`
- **说明**：`light` 浅色底；`dark` 深色底，网格线、轴名、系列色随主题切换。
- **取值建议**：与同页其它图一致；深色大屏用 `dark`。
- **示例**：`theme="dark"`
- **常见错误**：`theme="blue"` → `ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `legend` — 图例开关（默认 `True`）
- **类型**：`bool`
- **默认值**：`True`
- **说明**：多个 `color` 系列时图例是必需的（否则分不清哪个多边形是谁）；单系列时图例无意义但也不占太多空间。前端条件是 `spec.legend !== false`。
- **取值建议**：≥2 个系列保持 `True`；单系列且空间紧张时传 `False`。
- **示例**：`legend=False`

### `labels` — 数值标签（默认 `False`，本图不生效）
- **类型**：`bool`
- **默认值**：`False`
- **说明**：只写入 spec，雷达图渲染器不绘制数值标签；读数靠 tooltip。
- **取值建议**：保持 `False`，看数值用 tooltip 或配套表格。
- **示例**：`labels=True`（写入 spec，页面无变化）

### `zoom` — 缩放（默认 `False`，本图不生效）
- **类型**：`bool`
- **默认值**：`False`
- **说明**：只写入 spec；雷达图没有 dataZoom，传 `True` 也不会出现缩放条。
- **取值建议**：不用传。

### `drill` — 下钻维度列（默认 `None`）
- **类型**：`str | list[str] | None`
- **默认值**：`None`
- **说明**：写入 spec 并参与前端点击下钻。但雷达图的点击对象是**系列**（`color` 组），前端会把系列名当作类目值去过滤 `roles.x`，语义和柱状图不同，效果通常不符合预期。
- **取值建议**：需要逐级下钻请用 `pictorial` / `bar` / `area_pct`；雷达图用于静态画像。
- **示例**：`drill=["大区", "省份"]`
- **常见错误**：`drill=[]` → `ValueError: drill 不能是空列表；不需要下钻请传 drill=None。`

### `link` — 联动组名（默认 `None`）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：相同字符串为同一联动组；雷达图点击返回系列名，广播的维度同样是系列名，联动效果需按业务验证。
- **取值建议**：同上，静态画像图一般不加联动。
- **示例**：`link="销售"`

### `max_rows` — 最大参与绘制的行数（默认 `2000000`）
- **类型**：`int | None`
- **默认值**：`200000`
- **说明**：超出行数时均匀抽样，提示写入 `chart.warnings["warnings"]`；`None` 关闭采样，`0` 得到空图。聚合后指标轴只有几个，采样对 `mean` 影响较小。
- **取值建议**：需要精确均值时先自行 `groupby`，或传 `None`。
- **示例**：`max_rows=50000`

## 返回值

返回 `eazy_data_viz.Chart` 对象。

**Chart 的通用属性**

- `chart.spec`：`dict`。公共键 `id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`、`roles`、`agg`、`fmt`、`sort`、`topN`、`xtitle`、`ytitle`、`xlim`、`ylim`、`legend`、`labels`、`zoom`、`drill`、`link`；本图额外带 `maxValue`。
- `chart.data`：嵌入前端的绘图 payload：`{"cols", "rows", "dims", "measures", "kinds", "orders", "n", "n_total"}`；`chart.data_ref` 是引用 id（`"d" + sha1 前 12 位`）。
- `chart.warnings`：`dict`，`{"warnings": [...], "n_total": 原始行数}`。

**Chart 的通用方法**

- `chart.to_html(inline=True)`：完整 HTML 字符串；`chart.save(path, inline=True)`：写文件并返回绝对路径。
- `chart.show(open_browser=None)` / `chart.palette(name)` / `chart.title`。

**本图 `spec` 的专属事实**

- `roles = {"x": 指标列, "y": 数值列, "color": 系列列}`；`y` 省略时为 `None`（页面空白）。
- 专属键只有 `maxValue`（未传 `max` 时为 `null`）；`xtitle` / `ytitle` 写入但不绘制，`xlim` / `ylim` / `labels` / `zoom` / `topN` 均不参与渲染。
- `agg` 默认 `"mean"`、`legend` 默认 `True`、`height` 默认 `400`。

### 本图 `chart.spec` 的真实结构

下面是 `edv.radar(df, x="产品", y="销售额", color="大区")` 实际生成的 `spec`（`maxValue` 未传，为 `null`）：

```json
{
  "id": "c1",
  "type": "radar",
  "title": "销售额 雷达图",
  "subtitle": null,
  "theme": "light",
  "height": 400,
  "dataRef": "d3cae6f6e0275",
  "roles": {"x": "产品", "y": "销售额", "color": "大区"},
  "agg": "mean",
  "fmt": "compact",
  "sort": null,
  "topN": null,
  "xtitle": null,
  "ytitle": null,
  "xlim": null,
  "ylim": null,
  "legend": true,
  "labels": false,
  "zoom": false,
  "drill": null,
  "link": null,
  "maxValue": null
}
```

**验证返回值的小技巧**

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.radar(df, x="产品", y="销售额", color="大区", max=200000)
assert chart.spec["type"] == "radar"
assert chart.spec["agg"] == "mean"
assert chart.spec["maxValue"] == 200000.0
print(chart.title, chart.spec["roles"], chart.data["n"])
```

## 完整示例

以下示例都只依赖 `eazy_data_viz`，可直接复制运行。
### 示例 1：最简用法：单系列雷达
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.radar(df, x="产品", y="销售额")

print(chart.title, chart.spec["roles"], chart.spec["legend"])
assert chart.spec["roles"]["color"] is None
assert chart.spec["agg"] == "mean"
```

**输出**：
- `销售额 雷达图 {'x': '产品', 'y': '销售额', 'color': None} True`：4 个产品作为 4 根轴。
- 只有一个多边形，图例仍保留（单系列只有一个条目）；每个轴的值是各产品销售额的**均值**（默认 `agg="mean"`），量级都在 1000 上下，形状接近正多边形。

**验证**：`chart.spec["maxValue"] is None`——每根轴各自按「最大值×1.1」自适应。
### 示例 2：多系列对比：4 个大区 × 4 个产品
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.radar(
    df,
    x="产品",
    y="销售额",
    color="大区",
    title="各大区产品结构对比",
    subtitle="均值口径",
    max=200000,
)

print(chart.spec["roles"]["color"], chart.spec["maxValue"])
assert chart.spec["roles"]["color"] == "大区"
assert chart.spec["title"] == "各大区产品结构对比"
```

**输出**：
- `大区 200000.0`：4 个大区 = 4 个多边形，统一上限 20 万，四条形状可直接比较「哪块凸出」。
- 图例列出 华东 / 华北 / 华南 / 西部，颜色与多边形一一对应；tooltip 悬停时按指标列出该系列的值（compact 格式）。

**验证**：`len(chart.data["rows"]) == 1500`；去掉 `max` 后每个轴的半径会按各轴自己的最大值缩放。
### 示例 3：sum 与 mean 的区别
```python
import eazy_data_viz as edv

df = edv.sample_df()
mean_chart = edv.radar(df, x="产品", y="销售额", color="大区")
sum_chart = edv.radar(df, x="产品", y="销售额", color="大区", agg="sum")

print(mean_chart.spec["agg"], sum_chart.spec["agg"])
assert mean_chart.spec["agg"] == "mean"
assert sum_chart.spec["agg"] == "sum"
```

**输出**：
- `mean sum`：同一个图换聚合方式，`spec["agg"]` 跟着变，前端按该方式合并。
- `mean` 下各轴约 1000，`sum` 下升到 10 万级；如果没传 `max`，两者的轴上限会自动跟着量级变。
- 混用不同聚合方式的两张图不要放在同一组联动里比较。

**验证**：`chart.spec["agg"] == "sum"`；`agg` 非法值时抛 `ValueError`。
### 示例 4：排序与数值格式
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.radar(
    df,
    x="月份",
    y="销售额",
    sort="desc",
    fmt="thousands",
    height=460,
    legend=False,
)

print(chart.spec["sort"], chart.spec["height"], chart.spec["fmt"])
assert chart.spec["sort"] == "desc"
assert chart.spec["legend"] is False
```

**输出**：
- `desc 460 thousands`：12 根轴按「各月销售额合计」降序重排；高度 460 让 12 个轴名不至于挤在一起。
- `sort="x"` 时月份按 1月→12月 的固定顺序排；`sort=None` 时按数据出现顺序。
- `fmt="thousands"` 让 tooltip 显示 `113,744.8` 这类千分位。

**验证**：12 个指标已接近雷达图可读上限，实际使用建议不超过 8 根轴。
### 示例 5：省略 y 的后果（页面空白）
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.radar(df, x="产品", title="只有指标没有数值")

print(chart.spec["roles"]["y"], chart.spec["agg"], chart.title)
assert chart.spec["roles"]["y"] is None
assert chart.spec["agg"] == "count"
```

**输出**：
- `None count 只有指标没有数值`：Python 侧不报错，`agg` 被强制成 `count`。
- 但前端渲染器检测到 `roles.y` 为空，直接返回空 option——**页面是一块空白画布**，不是报错；`y` 虽然不是必填参数，实际必须传。

**验证**：补上 `y="销售额"` 后同一份数据就能正常画出雷达图。
### 示例 6：深色主题 + 大图 + 联动参数
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.radar(
    df,
    x="产品",
    y="利润",
    color="渠道",
    theme="dark",
    height=480,
    link="销售",
)

print(chart.spec["theme"], chart.spec["height"], chart.spec["link"])
assert chart.spec["theme"] == "dark"
assert chart.spec["height"] == 480
```

**输出**：
- `dark 480 销售`：3 个渠道 = 3 个多边形，深色底上系列色更亮。
- 高度 480 让轴名与图例都不易重叠。
- `link` 写入 spec；但雷达图点击广播的是系列名，联动效果要按业务验证。

**验证**：`chart.spec["link"] == "销售"`；同组其它图需要存在同一个 `link` 值才会联动。

## 常见错误

- **省略 `y` 得到空白图**
  - `radar(df, x="产品")` 不报错，但页面空白（`roles.y is None`，渲染器直接返回空图）；补上 `y` 即可——这是签名「可选」与渲染「必填」的不一致点。

- **把宽表当成长表传**
  - 雷达图需要「指标列 + 数值列」的长表；宽表（每个指标一列）会被当成一个指标列，画出来只有一根轴。
  - 正确做法：`df.melt(id_vars=["对象"], value_vars=["指标A", "指标B"], var_name="指标", value_name="得分")`。

- **`x` 缺失或 `y` 是文本列**
  - 省略 `x` → `ValueError: radar 需要 x（指标项），例如 radar(df, x="能力项", y="得分", color="对象")。`
  - `y` 文本列 → `TypeError: y（数值）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。`

- **期待 `top_n` / `xlim` / `ylim` / `labels` / `zoom` 生效**
  - 这几个参数只写入 spec，雷达图渲染器不读取：指标不截断、轴范围不应用、数值标签不绘制、没有 dataZoom。
  - 想限制指标数量请先筛 `x` 的取值；想统一轴范围用 `max`。
## 相关图表

- `parallel`：同样是多维对比，但每个对象一条折线，能容纳更多维度、更适合看「分布」。
- `bar` / `heatmap`：单指标或二维矩阵的精确比较，雷达图不适合读具体数值。
- `pictorial`：一维类目对比的视觉化版本。
- `parallel` 与 `radar` 的选择：对象多、维度多、想看分布 → `parallel`；对象少、维度少、想看「形状」 → `radar`。
