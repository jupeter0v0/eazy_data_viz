# `slope` — 斜率图：两个期别之间的变化

> 横轴只有两个位置（两个期别），每个类目是一条从左到右的折线；线的升降表示涨跌，线的交叉表示排名变化。
> 适合：期别对比（今年 vs 去年、上半年 vs 下半年）、排名变化、AB 两组的指标差异。
> 不适合：三个以上期别（用 `line` 或 `bump`）、连续时间序列（用 `line`）、精确数值对比（用 `dumbbell`）。

## 函数签名

```python
def slope(
    data,
    x,
    y,
    color=None,
    *,
    group=None,
    period=None,
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
    zoom=False,
    drill=None,
    link=None,
    max_rows=200000,
) -> "Chart":
    ...
```

> `data` / `x` / `y` / `color` 是位置参数，其余全部是**关键字限定参数**（`*` 之后必须写成 `参数名=值`）。
> 参数个数 24：4 个位置参数 + 20 个关键字参数。`color` 可以省略，但必须用 `group=` 补上（两者等价）。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源，图表取数的唯一入口 |
| `x` | `str` | `—` | 是 | 类目列名（每个类目一条折线） |
| `y` | `str` | `—` | 是 | 数值列名（必填，不能为 None） |
| `color` | `str` | `None` | 否 | 期别列名（决定横轴的两个位置） |
| `group` | `str` | `None` | 否 | `color` 的别名；`color` 优先 |
| `period` | `str \| list[str]` | `None` | 否 | 显式指定两个期别的名称 |
| `agg` | `str` | `'sum'` | 否 | 聚合方式 |
| `sort` | `str` | `None` | 否 | 排序：x / asc / desc（按第二期值） |
| `top_n` | `int` | `None` | 否 | 只保留前 N 项（当前版本不裁剪，见详解） |
| `title` | `str \| None` | `None` | 否 | 主标题，默认自动生成 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题（灰色小字） |
| `xtitle` | `str \| None` | `None` | 否 | 期别轴（横轴）标题 |
| `ytitle` | `str \| None` | `None` | 否 | 数值轴（纵轴）标题 |
| `xlim` | `tuple[float, float]` | `None` | 否 | 期别轴范围（本图不生效） |
| `ylim` | `tuple[float, float]` | `None` | 否 | 数值轴范围 |
| `fmt` | `str` | `'compact'` | 否 | 数值格式：compact / thousands / raw / percent / currency |
| `height` | `int` | `380` | 否 | 画布高度（像素，≥120） |
| `theme` | `str` | `'light'` | 否 | light / dark |
| `legend` | `bool` | `True` | 否 | 是否显示图例（类目 >6 时自动隐藏） |
| `labels` | `bool` | `False` | 否 | 是否在两个端点标数值 |
| `zoom` | `bool \| str` | `False` | 否 | 缩放条（本图不支持） |
| `drill` | `str \| list[str]` | `None` | 否 | 逐级下钻维度 |
| `link` | `str` | `None` | 否 | 联动组名（同组图表互相筛选） |
| `max_rows` | `int` | `200000` | 否 | 最大参与绘制行数（None 不采样） |

## 参数详解

### `data` — 数据源，图表取数的唯一入口（必填）

- **类型 / 默认值**：`pandas.DataFrame`、`dict`、`list`（每项一行）或 `Series` / 无
- **说明**：经 `frame.ensure_frame()` 归一化成 DataFrame；行数超过 `max_rows` 时均匀抽样并提示。
- **取值建议**：斜率图要求同一张表里同时有“类目列”“期别列”“数值列”，通常需要先 `groupby([x, color])` 聚合再传，或直接把明细表传进来让库内聚合。
- **报错**：`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`；`data=42` → `TypeError: 无法识别 data 类型 'int'，请传入 pandas.DataFrame（或 dict / list）。`

### `x` — 类目列名（必填）

- **类型 / 默认值**：`str` / 无
- **说明**：**每个 `x` 取值是一条折线**（一个类目一条线，从左侧期别连到右侧期别）。注意：横轴画的不是 `x` 列，而是两个期别；`x` 是折线的颜色/图例身份。
- **取值建议**：类目 2~6 个最好（折线多了会乱）；超过 6 个时图例自动隐藏。类目要有业务含义（大区、产品、渠道）。
- **报错**：不传 → `TypeError: slope() missing 1 required positional argument: 'x'`；列名写错 → `KeyError: "x（类目）列 '不存在' 不存在。当前可用的列有：日期, 月份, 大区, 省份, 城市, 产品, 渠道, 销售额, 订单数, 利润, 客户数"`

### `y` — 数值列名（必填）

- **类型 / 默认值**：`str` / 无（不能为 `None`）
- **说明**：折线端点的高度。与其它扩展图不同，斜率图的 `y` **不是可选的**：不传会直接报错。
- **取值建议**：同量纲、同口径；两个期别的数值必须来自同一列（用 `color` 区分期别），而不是两列。
- **报错**：`y=None` → `ValueError: slope 需要 y（数值列），例如 slope(df, x="门店", y="销售额", color="年份")。`；文本列 → `TypeError: y（数值）列 '产品' 需要是数值类型……`

### `color` — 期别列名（决定横轴两个位置）

- **类型 / 默认值**：`str` / `None`
- **说明**：**这是斜率图的“横轴”来源**：该列的不同取值就是折线端点的两个位置（期别）。内部按出现顺序去重取**前两个**取值作为左右两端。可以省略，但必须用 `group=` 补上；同时传时 `color` 优先。
- **取值建议**：期别列最好只有 2 个取值（如“上半年/下半年”“2023/2024”）；有 3 个及以上时只取前两个并在 `chart.warnings` 里提示。
- **报错**：`color`/`group` 都不传 → `ValueError: slope 需要 color（两期对比列，如年份/期别），也可以用 group= 传入。`；列名不存在 → `KeyError: "color（期别）列 '不存在' 不存在。当前可用的列有：……"`

### `group` — `color` 的别名

- **类型 / 默认值**：`str` / `None`
- **说明**：与 `color` 完全等价（`color is None` 时用它顶上）；`color` 与 `group` 同时传时 `color` 生效。语义上 `group` 更像“分组列”，但斜率图里它就是期别列。
- **取值建议**：只在不能改动位置参数位置时用；正常写法直接传 `color=`。
- **示例**：`group="渠道"` → `chart.spec["roles"]["color"] == "渠道"`

### `period` — 显式指定两个期别的名称

- **类型 / 默认值**：`str` 或 `list[str]` / `None`
- **说明**：不传时从 `color` 列的取值里自动取前两个；传了就按你给的名称作为横轴两个标签（单值会自动变成 1 个期别）。**名称必须与 `color` 列的真实取值一致**，否则按 (类目, 期别) 找不到数据，图上没有折线。
- **取值建议**：数据里期别叫“H1/H2”但想显示“上半年/下半年”时，要么先 `df["期别"] = df["期别"].map({...})` 改写数据，要么让 `period` 与数据取值一致。
- **示例**：`period=["上半年", "下半年"]`；`period=["A", "B", "C"]` → 只取 `["A","B"]`

### `agg` — 聚合方式

- **类型 / 默认值**：`str` / `'sum'`
- **说明**：按 (`x`, 期别) 聚合 `y`。可选 `sum` / `mean` / `count` / `max` / `min` / `median`。
- **取值建议**：金额/销量用 `"sum"`；比率类（转化率、客单价）用 `"mean"`。
- **报错**：`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median`

### `sort` — 排序方式

- **类型 / 默认值**：`str` / `None`
- **说明**：`"x"` 按类目本身排序；`"asc"` / `"desc"` 按**第二期（右侧端点）的聚合值**排序；`None` 保持聚合顺序。非法值不报错。
- **取值建议**：想突出“期末谁领先”用 `"desc"`；类目有固定业务顺序用 `"x"`。
- **示例**：`sort="desc"` → 按下半年销售额从高到低排列折线

### `top_n` — 只保留前 N 项（当前版本不裁剪）

- **类型 / 默认值**：`int` / `None`
- **说明**：只做合法性校验并写入 `spec["topN"]`。**1.0.0 中斜率图的前端构建器不读取 `spec.topN`，本参数不会减少折线条数**。
- **取值建议**：先过滤数据再画。
- **报错**：`top_n=0` → `ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`

### `title` — 主标题

- **类型 / 默认值**：`str` / `None`
- **说明**：不传时自动生成「<y 列名> 变化」；传 `""` 得到空标题（不回落自动）。
- **取值建议**：写清两期与口径，例如 `"各大区销售额：下半年 vs 上半年"`。
- **示例**：`title=None` → `chart.spec["title"] == "销售额 变化"`

### `subtitle` — 副标题

- **类型 / 默认值**：`str` / `None`
- **说明**：标题下方的小字说明，默认没有。
- **取值建议**：注明两期的时间范围与口径。
- **示例**：`subtitle="上半年 1-6 月 / 下半年 7-12 月"`

### `xtitle` — 期别轴（横轴）标题

- **类型 / 默认值**：`str` / `None`
- **说明**：横轴是期别轴（两个端点），`xtitle` 标在它下面；不传时用期别列名；传 `""` 隐藏。
- **取值建议**：两个标签本身已自明（上半年/下半年）时可传 `""`。
- **示例**：`xtitle="期别"`

### `ytitle` — 数值轴（纵轴）标题

- **类型 / 默认值**：`str` / `None`
- **说明**：纵轴（数值）标题，不传时用 `y` 列名；传 `""` 隐藏。
- **取值建议**：写上单位，如 `"销售额（元）"`。
- **示例**：`ytitle="销售额（元）"`

### `xlim` — 期别轴范围（本图不生效）

- **类型 / 默认值**：`tuple[float, float]` / `None`
- **说明**：横轴固定只有两个位置，`xlim` 只写入 `spec["xlim"]`，不改变画面；格式错误仍会报错。
- **取值建议**：本图不需要；数值范围请用 `ylim`。
- **报错**：`xlim=(0,)` → `ValueError: xlim 需要是 (最小值, 最大值) 两元组，例如 xlim=(0, 100)`

### `ylim` — 数值轴范围

- **类型 / 默认值**：`tuple[float, float]` / `None`
- **说明**：固定纵轴范围，**本图生效**；内部把 `(lo, hi)` 交换成 `[lo, hi]`。
- **取值建议**：多张斜率图并排时统一 `ylim`，否则“陡峭程度”不可横向比较；从 0 起画能弱化视觉夸张。
- **示例**：`ylim=(0, 350000)`

### `fmt` — 数值格式

- **类型 / 默认值**：`str` / `'compact'`
- **说明**：作用于纵轴刻度、`labels` 与 tooltip。可选 `compact` / `thousands` / `raw` / `percent` / `currency`；`fmt=None` 按 `compact` 处理。
- **取值建议**：金额用 `"thousands"`；变化率场景（数据已是百分比）用 `"percent"`。
- **报错**：`fmt="cn"` → `ValueError: fmt='cn' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）

- **类型 / 默认值**：`int` / `380`
- **说明**：最小 120；传 `None` 回落到 380。斜率图只有两个横坐标，高度主要影响纵向拉伸（线的陡峭感）。
- **取值建议**：380~460；线多时加高减少重叠。
- **报错**：`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `theme` — 主题

- **类型 / 默认值**：`str` / `'light'`
- **说明**：`"light"` / `"dark"`，控制背景、文字与线条颜色（每个类目取一个调色板颜色）。
- **取值建议**：深色大屏用 `"dark"`；类目多时留意相近色。
- **报错**：`theme="night"` → `ValueError: theme 只支持 "light" / "dark"，收到 'night'`

### `legend` — 是否显示图例（类目 >6 时自动隐藏）

- **类型 / 默认值**：`bool` / `True`
- **说明**：**本图生效**，但图例只在类目数 ≤6 时显示；超过 6 条线即使传 `True` 也会被隐藏（`g.legendMany` 抑制）。
- **取值建议**：类目多时用 `labels=True` 或 `subtitle` 辅助识别；单图展示可以关掉图例省空间。
- **示例**：`legend=False` → 图例隐藏（`chart.spec["legend"] is False`）

### `labels` — 是否在端点标数值

- **类型 / 默认值**：`bool` / `False`
- **说明**：**本图生效**，左右两个端点都显示按 `fmt` 格式化的数值；线多时会互相重叠。
- **取值建议**：类目 2~4 个且数值需要直接读时开启；否则用 tooltip（tooltip 还会给出变化率）。
- **示例**：`labels=True` → 每条线两端显示数值

### `zoom` — 缩放条（本图不支持）

- **类型 / 默认值**：`bool` / `False`
- **说明**：只有核心笛卡尔图消费 `spec.zoom`；**斜率图构建器不读取该字段**。
- **取值建议**：本图横轴只有两个位置，缩放没有意义。
- **示例**：`zoom=True` → `chart.spec["zoom"] is True`，画面无变化。

### `drill` — 逐级下钻维度

- **类型 / 默认值**：`str` 或 `list[str]` / `None`
- **说明**：点击某条折线（其实是点击该系列）后按类目名过滤数据并重算所有线；点「返回」回退。传字符串自动转列表；`drill[0]` 与 `x` 不同时自动把 `x` 插到最前。
- **取值建议**：注意下钻后类目集合变化，折线数量可能变少。
- **报错**：`drill=[]` → `ValueError: drill 不能是空列表；不需要下钻请传 drill=None。`；列名不存在 → `KeyError: "下钻维度列 '不存在' 不存在。……"`

### `link` — 联动组名

- **类型 / 默认值**：`str` / `None`
- **说明**：同 `link` 组的图表互相联动：点击某个类目把名字广播给组内其它图，它们按同名列过滤重算。
- **取值建议**：与同页的趋势图、明细表统一命名，如 `link="region"`。
- **示例**：`link="region"`；`chart.spec["link"] == "region"`

### `max_rows` — 最大参与绘制行数

- **类型 / 默认值**：`int` / `200000`
- **说明**：超过则等间隔均匀抽样，warning 写入 `chart.warnings["warnings"]`，`chart.data["n_total"]` 保留原始行数；`None` 关闭采样。
- **取值建议**：斜率先 `groupby(["类目","期别"])` 聚合再传；明细行抽样会显著改变两端数值。
- **示例**：`max_rows=100` → `chart.data["n"] == 100`

## 返回值

所有图表函数都返回 `eazy_data_viz.Chart` 对象（`chart = edv.slope(df, x="大区", y="销售额", color="半年")`）。

**Chart 的属性**

- `chart.spec`：`dict`，前端 ECharts 配置（JSON 可序列化）。公共键有 `id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`、`roles`、`agg`、`fmt`、`sort`、`topN`、`xtitle`、`ytitle`、`xlim`、`ylim`、`legend`、`labels`、`zoom`、`drill`、`link`，本图额外带 `arms`（两个期别名）。
- `chart.data`：**`dict`**，不是 DataFrame。含 `cols`、`rows`、`dims` / `measures` / `kinds`、`orders`、`n`、`n_total`。
- `chart.data_ref`：数据引用 id（`d-` + 12 位 sha1）。
- `chart.warnings`：**`dict`**，形如 `{"warnings": ["slope 的 color 列 …"], "n_total": 1500}`。
- `chart.title`：只读属性，等价于 `chart.spec["title"]`。

**Chart 的方法**

- `chart.save(path, inline=True)`：写出单文件 HTML（约 1.2~1.5 MB），自动建目录，返回绝对路径。
- `chart.to_html(inline=True)`：返回完整 HTML 字符串；`inline=False` 引用外部资源。
- `chart.show(open_browser=None)`：浏览器打开；Jupyter / Streamlit 自动内嵌。
- `chart.palette(name)`：切换配色并返回 `self`；可选 `google`、`antd`、`tableau`、`carbon`、`echarts`、`morandi`、`tailwind`。

**本图 `spec` 的真实结构**

```json
{ "id": "c1", "type": "slope", "title": "销售额 变化", "subtitle": null, "theme": "light",
  "height": 380, "dataRef": "d9465273f71af", "roles": {"x": "大区", "y": "销售额", "color": "半年"},
  "arms": ["上半年", "下半年"], "agg": "sum", "sort": null, "topN": null, "xtitle": null, "ytitle": null,
  "xlim": null, "ylim": null, "fmt": "compact", "legend": true, "labels": false, "zoom": false,
  "drill": null, "link": null }
```

**验证返回值的小技巧**

```python
import eazy_data_viz as edv
import numpy as np
df = edv.sample_df()
df["半年"] = np.where(df["日期"].dt.month <= 6, "上半年", "下半年")
chart = edv.slope(df, x="大区", y="销售额", color="半年")
assert chart.spec["type"] == "slope"
assert chart.spec["arms"] == ["上半年", "下半年"]
assert chart.spec["roles"]["color"] == "半年"
print(chart.warnings, len(chart.to_html()))
```

## 完整示例

以下示例都基于 `edv.sample_df()`（1500 行 × 11 列），可直接复制运行；输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法：上半年 vs 下半年

```python
import numpy as np
import eazy_data_viz as edv

df = edv.sample_df()
df["半年"] = np.where(df["日期"].dt.month <= 6, "上半年", "下半年")

chart = edv.slope(df, x="大区", y="销售额", color="半年")
chart.save("examples/output/slope_1.html")
```

**输出**：自动标题「销售额 变化」；横轴只有“上半年 / 下半年”两个位置；4 条线分别从 294,384 → 288,479（华东）、241,758 → 234,290（华北）等，全部略微下降（下半年 < 上半年）。
**验证**：`chart.spec["arms"] == ["上半年", "下半年"]`、`chart.spec["roles"] == {"x": "大区", "y": "销售额", "color": "半年"}`。

### 示例 2：用 `group=` 代替 `color=`

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.slope(df, x="大区", y="销售额", group="渠道")
chart.save("examples/output/slope_2.html")
```

**输出**：`group` 等价于 `color`，`roles["color"]` 变成「渠道」；渠道有 3 个取值，只取前两个（直销 / 渠道代理），`chart.warnings` 里出现「slope 的 color 列 '渠道' 有 3 个取值，只取前两个：直销 / 渠道代理。如需对比其它期别，请先过滤数据。」
**验证**：`chart.spec["roles"]["color"] == "渠道"`、`chart.spec["arms"] == ["直销", "渠道代理"]`。

### 示例 3：显式 `period=` 指定期别名

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.slope(
    df, x="大区", y="销售额", color="渠道",
    period=["直销", "渠道代理"],
    title="大区销售额：直销 vs 渠道代理",
    labels=True, fmt="thousands",
)
chart.save("examples/output/slope_3.html")
```

**输出**：横轴两个标签固定为“直销 / 渠道代理”；每条线两端标千分位数值；若 `period` 里的名字与数据取值不一致，画面将没有折线。
**验证**：`chart.spec["arms"] == ["直销", "渠道代理"]`、`chart.spec["labels"] is True`。

### 示例 4：排序 + 固定数值轴 + 深色主题

```python
import numpy as np
import eazy_data_viz as edv

df = edv.sample_df()
df["半年"] = np.where(df["日期"].dt.month <= 6, "上半年", "下半年")

chart = edv.slope(
    df, x="大区", y="销售额", color="半年",
    sort="desc", ylim=(260000, 300000), theme="dark", height=440,
    fmt="thousands", ytitle="销售额（元）", xtitle="期别", labels=True,
)
chart.save("examples/output/slope_4.html")
```

**输出**：按下半年销售额从大到小排列（华东 → 华北 → 华南 → 西部）；纵轴固定 26 万~30 万，四条线都呈现下降。
**验证**：`chart.spec["sort"] == "desc"`、`chart.spec["ylim"] == [260000.0, 300000.0]`。

### 示例 5：下钻 + 联动

```python
import numpy as np
import eazy_data_viz as edv

df = edv.sample_df()
df["半年"] = np.where(df["日期"].dt.month <= 6, "上半年", "下半年")

chart = edv.slope(
    df, x="大区", y="销售额", color="半年",
    drill=["大区", "省份"], link="trend",
    title="大区销售额变化（可下钻到省份）",
)
chart.save("examples/output/slope_5.html")
```

**输出**：初始 4 条线；点击某条线按该大区过滤并切到省份维度，线的数量与两端数值一起重算；同 `link="trend"` 的图表同步过滤。
**验证**：`chart.spec["drill"] == ["大区", "省份"]`、`chart.spec["link"] == "trend"`。

### 示例 6：边界：只有 1 个期别

```python
import eazy_data_viz as edv

df = edv.sample_df()
# 只给一个期别：图能生成，但只有单个端点，斜率无意义
chart = edv.slope(df, x="大区", y="销售额", color="渠道", period=["直销"])
print(chart.spec["arms"])
chart.save("examples/output/slope_6.html")
```

**输出**：`spec["arms"] == ["直销"]`，画面只有左侧一列点、没有连线；这种输入不报错也不产生 warning，需要自己保证两期。
**验证**：`len(chart.spec["arms"]) == 1`。

## 常见错误

### 1. 忘了传 `color`（或 `group`）

```python
import eazy_data_viz as edv
df = edv.sample_df()
# edv.slope(df, x="大区", y="销售额")
# → ValueError: slope 需要 color（两期对比列，如年份/期别），也可以用 group= 传入。
chart = edv.slope(df, x="大区", y="销售额", color="渠道")
```

**修法**：斜率图必须有“两期”的来源；没有期别列就先派生一列（如按月份切上半年/下半年）。

### 2. `period` 与 `color` 列的取值不一致

```python
import eazy_data_viz as edv
df = edv.sample_df()
# 数据里期别取值是“直销/渠道代理/线上商城”，period 却给“上半年/下半年”
chart = edv.slope(df, x="大区", y="销售额", color="渠道", period=["上半年", "下半年"])
# 图能生成，但按 (类目, 期别) 找不到数据 → 没有折线
chart2 = edv.slope(df, x="大区", y="销售额", color="渠道", period=["直销", "渠道代理"])
```

**修法**：`period` 只是横轴标签，必须与数据里 `color` 的真实取值一一对应；要换显示名请先 `df["期别"] = df["期别"].map(...)`。

### 3. 以为横轴画的是 `x` 列

```python
import numpy as np
import eazy_data_viz as edv
df = edv.sample_df()
df["半年"] = np.where(df["日期"].dt.month <= 6, "上半年", "下半年")
# 错误期待：横轴是“大区”。实际横轴是两期（上半年/下半年），大区是每条线的身份
chart = edv.slope(df, x="大区", y="销售额", color="半年")
# 想把类目放横轴、两期当分组：用 dumbbell 或 line
```

**修法**：斜率图的横轴只容纳两个期别；要按类目排开比较两期，用 `dumbbell`（两值同行）或 `bar`（分组柱）。

## 相关图表

- `bump`：三个及以上期别的排名变化，平滑折线版。
- `dumbbell`：两期对比但按类目排开，差值更直观。
- `line`：连续时间序列的趋势。
- `bar`：两期数值的分组柱状对比。
- `target`：把其中一期换成“目标值”虚线展示达成情况。
