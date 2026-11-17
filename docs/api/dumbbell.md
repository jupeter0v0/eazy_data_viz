# `dumbbell` — 哑铃图：同一类目的两值对比

> 每个类目一行，两个数值各画一个圆点，中间用一根短杆连起来，杆的长度就是“差值”；比双柱状图更紧凑，差值一眼可见。
> 适合：本期 vs 上期、实际 vs 目标、两个渠道的同一指标对比、男女/新老客对比。
> 不适合：三个以上数值同时对比（用 `bar` 分组）、需要堆叠分解（用 `waterfall`）、看目标的连续走势（用 `target`）。

## 函数签名

```python
def dumbbell(
    data,
    x,
    y1,
    y2,
    *,
    labels=None,
    series_names=None,
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
    zoom="auto",
    drill=None,
    link=None,
    max_rows=200000,
) -> "Chart":
    ...
```

> `data` / `x` / `y1` / `y2` 是位置参数，其余全部是**关键字限定参数**（`*` 之后必须写成 `参数名=值`）。
> 参数个数 23：4 个位置参数 + 19 个关键字参数。`labels` 与 `series_names` 都在 `*` 之后。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源，图表取数的唯一入口 |
| `x` | `str` | `—` | 是 | 类目列名（画在纵轴） |
| `y1` | `str` | `—` | 是 | 第一个数值列（默认左侧/主色圆点） |
| `y2` | `str` | `—` | 是 | 第二个数值列（默认右侧/对比色圆点） |
| `labels` | `bool \| list[str]` | `None` | 否 | `True` 标数值；传 list 等价于 `series_names` |
| `series_names` | `list[str]` | `None` | 否 | 两个系列的名称（图例与 tooltip） |
| `agg` | `str` | `'sum'` | 否 | 两个数值列的聚合方式 |
| `sort` | `str` | `None` | 否 | 排序：x / asc / desc / none（按 `y1`） |
| `top_n` | `int` | `None` | 否 | 只保留前 N 项（当前版本不裁剪，见详解） |
| `title` | `str \| None` | `None` | 否 | 主标题，默认自动生成 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题（灰色小字） |
| `xtitle` | `str \| None` | `None` | 否 | 类目轴（纵轴）标题 |
| `ytitle` | `str \| None` | `None` | 否 | 数值轴（横轴）标题 |
| `xlim` | `tuple[float, float]` | `None` | 否 | 类目轴范围（本图不生效） |
| `ylim` | `tuple[float, float]` | `None` | 否 | 数值轴范围 |
| `fmt` | `str` | `'compact'` | 否 | 数值格式：compact / thousands / raw / percent / currency |
| `height` | `int` | `380` | 否 | 画布高度（像素，≥120） |
| `theme` | `str` | `'light'` | 否 | light / dark |
| `legend` | `bool` | `True` | 否 | 是否显示图例 |
| `zoom` | `bool \| str` | `'auto'` | 否 | 缩放条（本图不支持） |
| `drill` | `str \| list[str]` | `None` | 否 | 逐级下钻维度 |
| `link` | `str` | `None` | 否 | 联动组名（同组图表互相筛选） |
| `max_rows` | `int` | `200000` | 否 | 最大参与绘制行数（None 不采样） |

## 参数详解

### `data` — 数据源，图表取数的唯一入口（必填）

- **类型 / 默认值**：`pandas.DataFrame`、`dict`、`list`（每项一行）或 `Series` / 无
- **说明**：经 `frame.ensure_frame()` 归一化成 DataFrame：`DataFrame` 原样使用，`Series` 变单列，`dict` / `list` 自动转表。行数超过 `max_rows` 时均匀抽样并提示。
- **取值建议**：两个数值列必须在同一张表里（同一行代表同一类目的一次观测），否则先在 pandas 里 merge/join 好再传。
- **报错**：`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`；`data=42` → `TypeError: 无法识别 data 类型 'int'，请传入 pandas.DataFrame（或 dict / list）。`

### `x` — 类目列名（必填）

- **类型 / 默认值**：`str` / 无
- **说明**：每行一个类目（一条哑铃），画在**纵轴**上。同一 `x` 的多行先按 `agg` 聚合两个数值列。
- **取值建议**：类目 5~20 个最合适；类目太多时纵向会很长，可先聚合或用 `drill`。
- **报错**：不传 → `TypeError: dumbbell() missing 1 required positional argument: 'x'`；列名写错 → `KeyError: "x（类目）列 '不存在' 不存在。当前可用的列有：日期, 月份, 大区, 省份, 城市, 产品, 渠道, 销售额, 订单数, 利润, 客户数"`

### `y1` — 第一个数值列（必填）

- **类型 / 默认值**：`str` / 无
- **说明**：第一个圆点的位置，同时是默认排序依据（`sort="asc"` / `"desc"` 按 `y1` 排）与差值基准（tooltip 里的差值 = `y2 - y1`，变化率 = 差值 / `y1`）。
- **取值建议**：把“基数/上期/现状”放在 `y1`，把“本期/目标”放在 `y2`，差值方向与文案才一致。
- **报错**：文本列 → `TypeError: y1（第一个数值）列 '产品' 需要是数值类型（当前是文本，例如 ['智能终端', '云服务', '行业软件']）。请先用 pd.to_numeric() 清洗，或换一列。`

### `y2` — 第二个数值列（必填）

- **类型 / 默认值**：`str` / 无
- **说明**：第二个圆点的位置。`y1` 与 `y2` 都缺值的类目会被**整行丢弃**（不会画成 0）。
- **取值建议**：与 `y1` 同量纲、同口径；比率和金额不要混在一张哑铃图里。
- **报错**：列名不存在 → `KeyError: "y2（第二个数值）列 '不存在' 不存在。当前可用的列有：……"`；文本列 → `TypeError: y2（第二个数值）列 '……' 需要是数值类型……`

### `labels` — 数值标签 / 系列名的双重身份

- **类型 / 默认值**：`bool` 或 `list[str]` / `None`
- **说明**：行为随类型变化：
  - `True`：在两个圆点旁显示数值标签（`y1` 在点下方、`y2` 在点上方）；
  - `False` / `None`：不显示标签；
  - **传 `list`**：不会被当作开关，而是**当作 `series_names`**（只取前两个元素，多余元素被忽略且不报错）。
- **取值建议**：只想显示数值用 `True`，想改系列名用 `series_names=`（更明确）；两者同时需要时用 `series_names=` + `labels=True`。
- **示例**：`labels=True` → `chart.spec["labels"] is True`；`labels=["A", "B"]` → `chart.spec["seriesNames"] == ["A", "B"]`、`spec["labels"] is False`

### `series_names` — 两个系列的名称

- **类型 / 默认值**：`list[str]`（长度 2） / `None`（回落到 `[y1, y2]`）
- **说明**：决定图例文字与 tooltip 里两行的名称。显式传入时优先于 `labels` 的 list 形式。长度不足 2 时缺失项回落到列名；长度超过 2 时多余项被忽略（不报错）。
- **取值建议**：用业务语言命名，如 `["上期销售额", "本期销售额"]`；不要与列名重复时产生歧义。
- **示例**：`series_names=["上期", "本期"]` → `chart.spec["seriesNames"] == ["上期", "本期"]`

### `agg` — 聚合方式

- **类型 / 默认值**：`str` / `'sum'`
- **说明**：`y1`、`y2` 各自按 `x` 聚合，同一个 `agg` 同时作用于两者。可选 `sum` / `mean` / `count` / `max` / `min` / `median`。
- **取值建议**：金额、销量用 `"sum"`；单价、转化率用 `"mean"`，否则求和后差值失真。
- **报错**：`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median`

### `sort` — 类目顺序（按 `y1`）

- **类型 / 默认值**：`str` / `None`
- **说明**：`"x"` 按类目本身排序；`"asc"` / `"desc"` 按**`y1`** 的聚合值排序；`None` 保持聚合顺序。非法值不报错。
- **取值建议**：想看“谁涨得最多”时可先按差值排序再画（pandas 里算差值列排序），`sort` 只按 `y1`。
- **示例**：`sort="desc"` → 按上期（`y1`）销售额从大到小排列

### `top_n` — 只保留前 N 项（当前版本不裁剪）

- **类型 / 默认值**：`int` / `None`
- **说明**：只做合法性校验并写入 `spec["topN"]`。**1.0.0 中哑铃图的前端构建器不读取 `spec.topN`，本参数不会减少行数**。
- **取值建议**：先过滤数据再画。
- **报错**：`top_n=0` → `ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`

### `title` — 主标题

- **类型 / 默认值**：`str` / `None`
- **说明**：不传时自动生成「<y1> / <y2> 对比」；传 `""` 得到空标题（不回落自动）。
- **取值建议**：写清“哪两期/哪两个口径”，例如 `"各大区上期 vs 本期销售额"`。
- **示例**：`title=None` → `chart.spec["title"] == "销售额 / 利润 对比"`

### `subtitle` — 副标题

- **类型 / 默认值**：`str` / `None`
- **说明**：标题下方的小字说明，默认没有。
- **取值建议**：注明“上期 = 去年同期”“本期含税”等口径说明。
- **示例**：`subtitle="上期 = 去年同期，本期含税"`

### `xtitle` — 类目轴（纵轴）标题

- **类型 / 默认值**：`str` / `None`
- **说明**：哑铃是**横向**图，类目在纵轴，所以 `xtitle` 管**类目轴**（纵轴）；不传时用 `x` 列名；传 `""` 隐藏。
- **取值建议**：类目名已自明时传 `""`，给数值轴留空间。
- **示例**：`xtitle="大区"`；`xtitle=""` → 纵轴无标题

### `ytitle` — 数值轴（横轴）标题

- **类型 / 默认值**：`str` / `None`
- **说明**：管**数值轴（横轴）**，不传时用 `y1` 列名；传 `""` 隐藏。
- **取值建议**：注明单位与口径，如 `"销售额（元）"`。
- **示例**：`ytitle="销售额（元）"`

### `xlim` — 类目轴范围（本图不生效）

- **类型 / 默认值**：`tuple[float, float]` / `None`
- **说明**：哑铃图纵轴是类目轴，`xlim` 只写入 `spec["xlim"]`，不改变画面；格式错误仍会报错。
- **取值建议**：本图不需要；控制数值范围请用 `ylim`。
- **报错**：`xlim=(0,)` → `ValueError: xlim 需要是 (最小值, 最大值) 两元组，例如 xlim=(0, 100)`

### `ylim` — 数值轴范围

- **类型 / 默认值**：`tuple[float, float]` / `None`
- **说明**：固定数值轴（横轴）范围，**本图生效**；内部把 `(lo, hi)` 交换成 `[lo, hi]`。
- **取值建议**：多张哑铃图并排时统一 `ylim` 便于横向比较；差值很小的场景可以从 0 起画，避免夸大差异。
- **示例**：`ylim=(0, 600000)`

### `fmt` — 数值格式

- **类型 / 默认值**：`str` / `'compact'`
- **说明**：作用于数值轴刻度、`labels` 数值与 tooltip。可选 `compact` / `thousands` / `raw` / `percent` / `currency`；`fmt=None` 按 `compact` 处理。
- **取值建议**：金额用 `"thousands"`；比率用 `"percent"`；差值很小、需要看清个位时用 `"raw"`。
- **报错**：`fmt="cn"` → `ValueError: fmt='cn' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）

- **类型 / 默认值**：`int` / `380`
- **说明**：最小 120；传 `None` 回落到 380。每行哑铃约占 30~40px。
- **取值建议**：4~8 个类目用 380；10 个以上用 460~560。
- **报错**：`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `theme` — 主题

- **类型 / 默认值**：`str` / `'light'`
- **说明**：`"light"` / `"dark"`，控制背景、文字与连接杆颜色。
- **取值建议**：深色大屏用 `"dark"`；连接杆在深底下用 `theme.axis` 色，仍可辨识。
- **报错**：`theme="night"` → `ValueError: theme 只支持 "light" / "dark"，收到 'night'`

### `legend` — 是否显示图例

- **类型 / 默认值**：`bool` / `True`
- **说明**：**本图生效**。图例显示 `series_names` 里的两个名称；`legend=False` 时隐藏（此时两个圆点的含义要靠 `subtitle` 或标题说明）。
- **取值建议**：两个系列名不自明时保持 `True`；单图独立展示、标题已说明时可用 `False` 省空间。
- **示例**：`legend=False` → `chart.spec["legend"] is False`，图例隐藏

### `zoom` — 缩放条（本图不支持）

- **类型 / 默认值**：`bool` / `str` / `'auto'`
- **说明**：只有核心笛卡尔图消费 `spec.zoom`；**哑铃图构建器不读取该字段**，`"auto"` 也不会自动加缩放条。
- **取值建议**：类目多时先聚合或下钻。
- **示例**：`zoom=True` → `chart.spec["zoom"] is True`，画面无缩放条。

### `drill` — 逐级下钻维度

- **类型 / 默认值**：`str` 或 `list[str]` / `None`
- **说明**：点击某一行后按该类目名过滤数据并重算，`y1` / `y2` 一起重算；点「返回」回退。传字符串自动转列表；`drill[0]` 与 `x` 不同时自动把 `x` 插到最前。
- **取值建议**：从粗到细 2~3 层；下钻后类目变多，记得同步调大 `height`。
- **报错**：`drill=[]` → `ValueError: drill 不能是空列表；不需要下钻请传 drill=None。`；列名不存在 → `KeyError: "下钻维度列 '不存在' 不存在。……"`

### `link` — 联动组名

- **类型 / 默认值**：`str` / `None`
- **说明**：同 `link` 组的图表互相联动：点击某行把类目名广播给组内其它图，它们按同名列过滤重算。
- **取值建议**：与同页的趋势图、明细表统一命名，如 `link="region"`。
- **示例**：`link="region"`；`chart.spec["link"] == "region"`

### `max_rows` — 最大参与绘制行数

- **类型 / 默认值**：`int` / `200000`
- **说明**：超过则等间隔均匀抽样，warning 写入 `chart.warnings["warnings"]`，`chart.data["n_total"]` 保留原始行数；`None` 关闭采样。
- **取值建议**：哑铃图只画聚合结果，建议先 `groupby` 再传。
- **示例**：`max_rows=100` → `chart.data["n"] == 100`

## 返回值

所有图表函数都返回 `eazy_data_viz.Chart` 对象（`chart = edv.dumbbell(df, x="大区", y1="上期销售额", y2="本期销售额")`）。

**Chart 的属性**

- `chart.spec`：`dict`，前端 ECharts 配置（JSON 可序列化）。公共键有 `id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`、`roles`、`agg`、`fmt`、`sort`、`topN`、`xtitle`、`ytitle`、`xlim`、`ylim`、`legend`、`labels`、`zoom`、`drill`、`link`，本图额外带 `seriesNames`。
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
{ "id": "c1", "type": "dumbbell", "title": "上期销售额 / 本期销售额 对比", "subtitle": null, "theme": "light",
  "height": 380, "dataRef": "d9465273f71af", "roles": {"x": "大区", "y": "上期销售额", "y2": "本期销售额"},
  "agg": "sum", "seriesNames": ["上期销售额", "本期销售额"], "sort": null, "topN": null, "xtitle": null,
  "ytitle": null, "xlim": null, "ylim": null, "fmt": "compact", "legend": true, "labels": false,
  "zoom": "auto", "drill": null, "link": null }
```

**验证返回值的小技巧**

```python
import eazy_data_viz as edv
df = edv.sample_df()
df["上期销售额"] = df["销售额"] * 0.85
df["本期销售额"] = df["销售额"]
chart = edv.dumbbell(df, x="大区", y1="上期销售额", y2="本期销售额")
assert chart.spec["type"] == "dumbbell"
assert chart.spec["seriesNames"] == ["上期销售额", "本期销售额"]
print(chart.warnings, len(chart.to_html()))
```

## 完整示例

以下示例都基于 `edv.sample_df()`（1500 行 × 11 列），可直接复制运行；输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法：上期 vs 本期

```python
import eazy_data_viz as edv
df = edv.sample_df()
df["上期销售额"] = df["销售额"] * 0.85
df["本期销售额"] = df["销售额"]

chart = edv.dumbbell(df, x="大区", y1="上期销售额", y2="本期销售额")
chart.save("examples/output/dumbbell_1.html")
```

**输出**：自动标题「上期销售额 / 本期销售额 对比」；4 行哑铃，本期圆点（582,864 等）都在上期（495,434 等）右侧，差额为 +15%。
**验证**：`chart.spec["roles"] == {"x": "大区", "y": "上期销售额", "y2": "本期销售额"}`、`chart.spec["legend"] is True`。

### 示例 2：显式系列名 + 数值标签

```python
import eazy_data_viz as edv
df = edv.sample_df()
df["上期销售额"] = df["销售额"] * 0.85
df["本期销售额"] = df["销售额"]

chart = edv.dumbbell(
    df, x="大区", y1="上期销售额", y2="本期销售额",
    series_names=["上期", "本期"], labels=True, fmt="thousands",
    title="大区销售环比", subtitle="上期 = 销售额 × 0.85 的模拟口径",
)
chart.save("examples/output/dumbbell_2.html")
```

**输出**：图例显示“上期 / 本期”；每个圆点旁标千分位数值；tooltip 里同时给出差值与变化率（+15.0%）。
**验证**：`chart.spec["seriesNames"] == ["上期", "本期"]`、`chart.spec["labels"] is True`。

### 示例 3：用 `labels` 的 list 形式改系列名

```python
import eazy_data_viz as edv
df = edv.sample_df()
df["上期销售额"] = df["销售额"] * 0.85
df["本期销售额"] = df["销售额"]

chart = edv.dumbbell(
    df, x="产品", y1="上期销售额", y2="本期销售额",
    labels=["上期", "本期"],   # list 会被当作 series_names
)
chart.save("examples/output/dumbbell_3.html")
```

**输出**：系列名变为“上期 / 本期”，但**没有数值标签**（list 形式不会开启 `labels`）；想看数值需同时传 `labels=True` 与 `series_names=[...]`。
**验证**：`chart.spec["seriesNames"] == ["上期", "本期"]`、`chart.spec["labels"] is False`。

### 示例 4：排序 + 固定数值轴 + 深色主题

```python
import eazy_data_viz as edv
df = edv.sample_df()
df["上期销售额"] = df["销售额"] * 0.85
df["本期销售额"] = df["销售额"]

chart = edv.dumbbell(
    df, x="大区", y1="上期销售额", y2="本期销售额",
    sort="desc", ylim=(0, 700000), theme="dark", height=440,
    fmt="thousands", ytitle="销售额（元）", xtitle="",
)
chart.save("examples/output/dumbbell_4.html")
```

**输出**：按上期值从大到小排列（华东 → 华北 → 华南 → 西部）；数值轴固定 0~70 万，四行差值长度可直接横向比较。
**验证**：`chart.spec["ylim"] == [0.0, 700000.0]`、`chart.spec["theme"] == "dark"`。

### 示例 5：缺值类目被整行丢弃

```python
import eazy_data_viz as edv
import numpy as np

df = edv.sample_df()
df["上期销售额"] = df["销售额"] * 0.85
df["本期销售额"] = df["销售额"]
# 让西部大区的“本期”缺值：该行会整条消失
df.loc[df["大区"] == "西部", "本期销售额"] = np.nan

chart = edv.dumbbell(df, x="大区", y1="上期销售额", y2="本期销售额")
chart.save("examples/output/dumbbell_5.html")
```

**输出**：只剩 3 条哑铃（华东 / 华北 / 华南），西部不显示（`y1`、`y2` 任一缺值都丢弃该行）。
**验证**：`chart.spec["roles"]["x"] == "大区"`；图中类目数 3（通过 HTML 内容或目视确认）。

### 示例 6：下钻 + 联动

```python
import eazy_data_viz as edv
df = edv.sample_df()
df["上期销售额"] = df["销售额"] * 0.85
df["本期销售额"] = df["销售额"]

chart = edv.dumbbell(
    df, x="大区", y1="上期销售额", y2="本期销售额",
    drill=["大区", "省份"], link="compare",
    title="大区销售环比（可下钻到省份）",
)
chart.save("examples/output/dumbbell_6.html")
```

**输出**：初始 4 行；点击某行按该大区过滤并切到省份维度，`y1`/`y2` 一起重算；同 `link="compare"` 的图表同步过滤。
**验证**：`chart.spec["drill"] == ["大区", "省份"]`、`chart.spec["link"] == "compare"`。

## 常见错误

### 1. `y2` 列名写错

```python
import eazy_data_viz as edv
df = edv.sample_df()
# edv.dumbbell(df, x="大区", y1="销售额", y2="不存在")
# → KeyError: "y2（第二个数值）列 '不存在' 不存在。当前可用的列有：日期, 月份, 大区, ..."
chart = edv.dumbbell(df, x="大区", y1="销售额", y2="利润")
```

**修法**：先用 `list(df.columns)` 核对；派生列（上期/本期）要先在 df 上赋好列再传。

### 2. 两个数值列量纲差太多

```python
import eazy_data_viz as edv
df = edv.sample_df()
# 销售额（几十万）和订单数（1~4）放一张哑铃图，订单数圆点会挤在最左端
chart = edv.dumbbell(df, x="大区", y1="销售额", y2="订单数", series_names=["销售额", "订单数"])
# 更好的做法：同量纲对比，或分别画两张图
chart2 = edv.dumbbell(df, x="大区", y1="销售额", y2="利润", series_names=["销售额", "利润"])
```

**修法**：同一张哑铃图只放同量纲的两个指标；量纲不同就拆图或换成百分比/指数。

### 3. 用 `labels=["上期","本期"]` 想同时开数值标签

```python
import eazy_data_viz as edv
df = edv.sample_df()
df["上期销售额"] = df["销售额"] * 0.85
df["本期销售额"] = df["销售额"]
chart = edv.dumbbell(
    df, x="大区", y1="上期销售额", y2="本期销售额", labels=["上期", "本期"],
)
assert chart.spec["seriesNames"] == ["上期", "本期"]
assert chart.spec["labels"] is False   # list 不会开启数值标签
```

**修法**：`labels` 传 list 只等价于 `series_names`；要“改名 + 显示数值”就写 `series_names=["上期","本期"], labels=True`。

## 相关图表

- `target`：目标值用虚线折线表达，适合“实际 vs 目标”且要看趋势。
- `bullet`：横向 KPI 达成图，目标是一根竖线刻度，单值更紧凑。
- `slope`：两个期别之间的变化用斜线表示，强调“排名/趋势的移动”。
- `bar`：需要三组以上数值、或要堆叠时用分组柱状图。
- `lollipop`：只有一个数值时的轻量替代。
