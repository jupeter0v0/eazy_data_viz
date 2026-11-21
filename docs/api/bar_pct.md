# `bar_pct` — 百分比堆叠柱状图（构成对比）

> 每根柱子归一化到 100%，用堆叠柱看「各类目内部的构成比例」。
> 适合：3~10 个离散类目的构成对比（各大区销售构成、各渠道产品结构）、类目之间占比差异一眼可见、总和为 100% 的分配场景。
> 不适合：需要看绝对金额（用 `bar` 堆叠）、时间点连续的趋势（用 `area_pct`）、分组超过 6 个（柱子太碎）、类目超过 15 个（柱子挤在一起）。

## 函数签名

```python
eazy_data_viz.bar_pct(
    data,
    x,
    y,
    color=None,
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
    legend=True,
    labels=False,
    zoom="auto",
    drill=None,
    link=None,
    max_rows=200000,
) -> Chart
```

签名要点：

- `x`（类目）、`y`（数值）、`color`（构成分组）三者**都必须传**；`color=None` 有专属报错。
- 本图是 ECharts 的 `bar + stack`（`barMaxWidth=38`、`boundaryGap=True`），适合离散类目；时间趋势请用 `area_pct`。
- 与 `area_pct` 参数完全一致，只有渲染形态不同：本图是柱子，`area_pct` 是面积。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list` | `—` | 是 | 数据源 |
| `x` | `str` | `—` | 是 | 类目列名 |
| `y` | `str` | `—` | 是 | 数值列名 |
| `color` | `str \| None` | `None` | 否 | 构成分组列名（实际必传） |
| `agg` | `str` | `"sum"` | 否 | 聚合方式 |
| `sort` | `str \| None` | `None` | 否 | 类目顺序：None / x / asc / desc |
| `top_n` | `int \| None` | `None` | 否 | 只保留前 N 项（本图不生效） |
| `title` | `str \| None` | `None` | 否 | 主标题 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `xtitle` | `str \| None` | `None` | 否 | X 轴标题 |
| `ytitle` | `str \| None` | `None` | 否 | Y 轴标题 |
| `xlim` | `tuple \| None` | `None` | 否 | X 轴范围（本图不生效） |
| `ylim` | `tuple \| None` | `None` | 否 | Y 轴范围（被 0~100% 覆盖） |
| `fmt` | `str` | `"compact"` | 否 | 数值格式 |
| `height` | `int` | `380` | 否 | 图表高度（≥120） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `str` | `"light"` | 否 | 主题：light / dark |
| `legend` | `bool` | `True` | 否 | 是否显示分组图例 |
| `labels` | `bool` | `False` | 否 | 数值标签（本图不生效） |
| `zoom` | `str` | `"auto"` | 否 | 缩放（本图不生效） |
| `drill` | `str \| list \| None` | `None` | 否 | 下钻维度列 |
| `link` | `str \| None` | `None` | 否 | 联动组名 |
| `max_rows` | `int \| None` | `200000` | 否 | 进入绘图的最大行数 |

## 参数详解

### `data` — 数据源（必填）
- **类型**：`pandas.DataFrame | dict | list`
- **默认值**：无
- **说明**：`frame.ensure_frame()` 统一转换；只读取 `x` / `y` / `color` 三列，整份数据嵌入 payload；超过 `max_rows` 时均匀抽样。
- **取值建议**：类目数控制在 10 以内；类目太多时柱子会变细，堆叠段也看不清。
- **示例**：`data=df`
- **常见错误**：空表 → `ValueError: 数据为空（0 行），无法绘图。`

### `x` — 类目列名（必填）
- **类型**：`str`
- **默认值**：无
- **说明**：每根柱子一个类目，所有 `color` 分组在该类目的值归一化为 100%。X 轴是 category 轴（`boundaryGap=True`），类目间留有空隙。默认按出现顺序排，可用 `sort` 调整。
- **取值建议**：基数 3~10 的离散维度（大区、渠道、产品、门店）；月份这种有序类目也可以，但趋势更推荐 `area_pct`。
- **示例**：`x="产品"`
- **常见错误**：省略 → `ValueError: bar_pct 需要 x / y，例如 bar_pct(df, x="月份", y="销售额", color="产品")。`

### `y` — 数值列名（必填）
- **类型**：`str`
- **默认值**：无
- **说明**：每个 (x, color) 组合按 `agg` 聚合后，再按 x 归一化到 100%（保留 1 位小数）。必须是数值 dtype，文本列会先尝试 `pd.to_numeric`，失败抛 `TypeError`。
- **取值建议**：可加指标（销售额、订单数、客户数）；利润率这类比率不适合堆叠。
- **示例**：`y="销售额"`
- **常见错误**：`y="产品"` → `TypeError: y（数值）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `color` — 构成分组列名（默认 `None`，但实际必传）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：决定堆叠段：每个去重取值一段。省略时**直接抛错**；`color` 与 `x` 同列不会报错，但每根柱子只有一段、恒为 100%（没有对比意义）。
- **取值建议**：基数 2~6 的维度（产品、渠道、大区）；段数太多时建议先合并小段为「其他」。
- **示例**：`color="渠道"`
- **常见错误**：省略 → `ValueError: bar_pct 需要 color（百分比的分组列），例如 bar_pct(df, x="月份", y="销售额", color="产品")。`

### `agg` — 聚合方式（默认 `"sum"`）
- **类型**：`str`
- **默认值**：`"sum"`
- **说明**：同一 (x, color) 多行时的合并方式，合法值 `sum` / `mean` / `count` / `max` / `min` / `median`；归一化发生在聚合之后。
- **取值建议**：金额/数量用 `sum`；想看「平均单笔的构成」用 `mean`。
- **示例**：`agg="mean"`
- **常见错误**：`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, unique, max, min, median`

### `sort` — 类目顺序（默认 `None`）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：`"x"` 按 X 自身顺序；`"asc"` / `"desc"` 按每根柱子的合计值排序；`None` 时若数据带类目顺序则按类目序，否则按出现顺序。排序只改变柱子顺序，不改变占比。
- **取值建议**：排行场景用 `desc`（柱高一致，排序意义在于把「哪一类占比结构不同」放在一起看）；固定业务顺序用 `x`。
- **示例**：`sort="desc"`

### `top_n` — 只保留前 N 项（默认 `None`）
- **类型**：`int | None`
- **默认值**：`None`
- **说明**：写入 `spec["topN"]` 并做 ≥1 整数校验，但**本图不截断类目或分组**。要控制类目数量请先在 Python 侧筛选。
- **取值建议**：保持 `None`，用 `df.nlargest(...)` 或 `groupby` 自己截断。
- **示例**：`top_n=5`（只写 spec，页面不变）
- **常见错误**：`top_n=0` → `ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`

### `title` — 主标题（默认 `None`，自动生成）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：`None` 时自动生成「`y` 百分比构成」；自动标题不含维度，建议手写「各大区销售构成」。
- **示例**：`title="各大区销售构成"`

### `subtitle` — 副标题（默认 `None`）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：标题下方灰色小字，写口径或时间范围，例如 `"2024 全年 · 按销售额占比"`。
- **示例**：`subtitle="2024 全年 · 按销售额占比"`

### `xtitle` — X 轴标题（默认 `None`）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：X 轴下方标题，`None` 时回退成 `x` 列名；类目列名清楚时不用传。
- **示例**：`xtitle="产品线"`

### `ytitle` — Y 轴标题（默认 `None`）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：Y 轴标题，`None` 时回退成「占比」；Y 轴刻度固定 0~100%，默认值一般够用。
- **示例**：`ytitle="销售占比"`

### `xlim` — X 轴范围（默认 `None`，本图不生效）
- **类型**：`tuple(min, max) | None`
- **默认值**：`None`
- **说明**：只做格式校验后写入 spec；category 轴不应用 xlim。
- **取值建议**：不用传；要缩小类目范围请先过滤数据。

### `ylim` — Y 轴范围（默认 `None`，会被 0~100% 覆盖）
- **类型**：`tuple(min, max) | None`
- **默认值**：`None`
- **说明**：格式校验后写入 spec，但本图 Y 轴固定 `min=0`、`max=100`、刻度加 `%`，**ylim 不生效**。
- **取值建议**：不用传；百分比图本来就固定 0~100%。
- **常见错误**：`ylim=5` → `ValueError: ylim 需要是 (最小值, 最大值) 两元组，例如 ylim=(0, 100)`

### `fmt` — 数值格式（默认 `"compact"`）
- **类型**：`str`
- **默认值**：`"compact"`
- **说明**：tooltip 里原始数值的格式（不是占比本身），5 选 1：`compact` / `thousands` / `raw` / `currency` / `percent`；占比固定由渲染器加 `%`。
- **取值建议**：金额用 `compact`；需要原始精度用 `raw`。
- **示例**：`fmt="thousands"`
- **常见错误**：`fmt="usd"` → `ValueError: fmt='usd' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 图表高度（像素，默认 `380`）
- **类型**：`int`
- **默认值**：`380`
- **说明**：写进 `spec["height"]`；柱子高度、图例与 X 轴标签都从这里分配空间，通用校验要求 ≥120；类目少用 360~400，类目多或图例长时用 420~480。
- **示例**：`height=420`
- **常见错误**：`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题（默认 `"light"`）
- **类型**：`str`
- **默认值**：`"light"`
- **说明**：`light` 浅色底；`dark` 深色底，段色与网格线随主题切换，与同页其它图保持一致。
- **示例**：`theme="dark"`
- **常见错误**：`theme="blue"` → `ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `legend` — 图例开关（默认 `True`）
- **类型**：`bool`
- **默认值**：`True`
- **说明**：前端条件是 `spec.legend !== false`；百分比构成必须有图例，否则不知道每段是哪组。
- **取值建议**：保持 `True`；段数少且 `subtitle` 说明颜色含义时可关。
- **示例**：`legend=False`

### `labels` — 数值标签（默认 `False`，本图不生效）
- **类型**：`bool`
- **默认值**：`False`
- **说明**：只写入 spec，堆叠段的标签位置重叠，渲染器不绘制；读数靠 tooltip（显示每段占比）。
- **取值建议**：保持 `False`。

### `zoom` — 缩放（默认 `"auto"`，本图不生效）
- **类型**：`str`
- **默认值**：`"auto"`
- **说明**：只写入 spec；本图没有 dataZoom 逻辑，类目太多请先筛选。
- **取值建议**：不用传。

### `drill` — 下钻维度列（默认 `None`）
- **类型**：`str | list[str] | None`
- **默认值**：`None`
- **说明**：点击柱子按维度逐级下钻，第一层自动作为 `roles.x`；ECharts 画布，点击事件可用。
- **取值建议**：`drill=["大区", "省份"]` 这类两级下钻；列必须真实存在。
- **示例**：`drill=["大区", "省份"]`
- **常见错误**：`drill=[]` → `ValueError: drill 不能是空列表；不需要下钻请传 drill=None。`

### `link` — 联动组名（默认 `None`）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：相同字符串为同一联动组，点击柱子会把类目值广播给同组图表过滤；既能发起也能接收。
- **取值建议**：同页图表用同一个组名（如 `"销售"`）。
- **示例**：`link="销售"`

### `max_rows` — 最大参与绘制的行数（默认 `2000000`）
- **类型**：`int | None`
- **默认值**：`200000`
- **说明**：超出行数时均匀抽样，提示写入 `chart.warnings["warnings"]`；`None` 关闭采样，`0` 得到空图。
- **取值建议**：百分比图对抽样不敏感，默认值即可。
- **示例**：`max_rows=50000`

## 返回值

返回 `eazy_data_viz.Chart` 对象。

**Chart 的通用属性**

- `chart.spec`：`dict`。公共键 `id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`、`roles`、`agg`、`fmt`、`sort`、`topN`、`xtitle`、`ytitle`、`xlim`、`ylim`、`legend`、`labels`、`zoom`、`drill`、`link`；本图额外带 `percent: true`。
- `chart.data`：嵌入前端的绘图 payload（`cols/rows/dims/measures/kinds/orders/n/n_total`），`chart.data_ref` 是引用 id（`"d" + sha1 前 12 位`）。
- `chart.warnings`：`dict`，`{"warnings": [...], "n_total": 原始行数}`。

**Chart 的通用方法**

- `chart.to_html(inline=True)` / `chart.save(path, inline=True)` / `chart.show()` / `chart.palette(name)` / `chart.title`。

**本图 `spec` 的专属事实**

- `roles = {"x", "y", "color"}`；专属键 `percent: true`（前端据此走 `buildPercentStack` 的柱状分支）。
- Y 轴固定 0~100% 并加 `%` → `ylim` 失效；`xlim`/`labels`/`zoom` 不参与渲染、`topN` 不截断；`legend` 默认 `True`、`height` 默认 `380`。

### 本图 `chart.spec` 的真实结构

下面是 `edv.bar_pct(df, x="产品", y="销售额", color="渠道")` 实际生成的 `spec`：

```json
{
  "id": "c1",
  "type": "bar_pct",
  "title": "销售额 百分比构成",
  "subtitle": null,
  "theme": "light",
  "height": 380,
  "dataRef": "d3cae6f6e0275",
  "roles": {"x": "产品", "y": "销售额", "color": "渠道"},
  "agg": "sum",
  "fmt": "compact",
  "sort": null,
  "topN": null,
  "xtitle": null,
  "ytitle": null,
  "xlim": null,
  "ylim": null,
  "legend": true,
  "labels": false,
  "zoom": "auto",
  "drill": null,
  "link": null,
  "percent": true
}
```

**验证返回值的小技巧**

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.bar_pct(df, x="产品", y="销售额", color="渠道")
assert chart.spec["type"] == "bar_pct"
assert chart.spec["percent"] is True
assert chart.spec["legend"] is True
print(chart.title, chart.spec["roles"], chart.data["n"])
```

## 完整示例

以下示例都只依赖 `eazy_data_viz`，可直接复制运行。
### 示例 1：最简用法：各产品的渠道构成
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.bar_pct(df, x="产品", y="销售额", color="渠道")

print(chart.title, chart.spec["percent"], chart.spec["roles"]["color"])
assert chart.spec["type"] == "bar_pct"
assert chart.spec["percent"] is True
```

**输出**：
- `销售额 百分比构成 True 渠道`：4 根柱子（4 个产品），每根由 3 段（渠道）堆叠到 100%。
- Y 轴固定 0~100%、刻度带 `%`；每根柱子的 3 段高度之和等于 100，各产品的渠道结构差异通过段的比例体现（智能终端直销偏多）。

**验证**：`chart.spec["ylim"] is None`；传 `ylim=(20, 80)` 也不会改变 0~100% 的轴。
### 示例 2：各大区的产品构成
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.bar_pct(
    df,
    x="大区",
    y="销售额",
    color="产品",
    title="各大区产品构成",
    subtitle="按销售额占比",
)

print(chart.spec["title"], chart.spec["roles"]["color"], chart.data["n"])
assert chart.spec["roles"]["x"] == "大区"
assert chart.spec["title"] == "各大区产品构成"
```

**输出**：
- 4 根柱子、每根 4 段（产品），4 段合计 100%——柱高相同，比较的是「内部构成」。
- 图例按产品去重顺序列出，`subtitle` 标明口径；这是 `bar_pct` 最典型的用法：类目之间总量不可比时，比结构。

**验证**：`len(df["产品"].unique()) == 4`；分组数越少，每段越厚越好读。
### 示例 3：排序与聚合
```python
import eazy_data_viz as edv

df = edv.sample_df()
mean_chart = edv.bar_pct(df, x="产品", y="销售额", color="渠道", agg="mean")
sorted_chart = edv.bar_pct(df, x="产品", y="销售额", color="渠道", sort="desc")

print(mean_chart.spec["agg"], sorted_chart.spec["sort"])
assert mean_chart.spec["agg"] == "mean"
assert sorted_chart.spec["sort"] == "desc"
```

**输出**：
- `mean desc`：`agg="mean"` 时每段的原始值是均值，归一化后仍是占比（结构形状可能变化）。
- `sort="desc"` 按每根柱子的合计值从高到低排——柱高相同，排序让「量大的类目」靠左；排序只改顺序，不改占比。

**验证**：`sorted_chart.spec["sort"] == "desc"`；`sort="x"` 按类目列自身顺序排。
### 示例 4：深色主题 + 高度 + 关图例
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.bar_pct(
    df,
    x="渠道",
    y="订单数",
    color="产品",
    height=440,
    theme="dark",
    legend=False,
    xtitle="销售渠道",
    ytitle="订单占比",
)

print(chart.spec["height"], chart.spec["theme"], chart.spec["legend"])
assert chart.spec["height"] == 440
assert chart.spec["legend"] is False
```

**输出**：
- `440 dark False`：3 根柱子、每根 4 段，深色底上段色对比更清楚。
- 关掉图例后卡片更紧凑，但读者不知道颜色对应哪个产品——只在 `subtitle` 写清时这样用；`xtitle` / `ytitle` 覆盖默认轴名（默认 y 轴是「占比」）。

**验证**：`chart.spec["xtitle"] == "销售渠道"`；`chart.spec["ytitle"] == "订单占比"`。
### 示例 5：下钻与联动
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.bar_pct(
    df,
    x="大区",
    y="销售额",
    color="产品",
    drill=["大区", "省份"],
    link="销售",
)

print(chart.spec["drill"], chart.spec["roles"]["_extra"], chart.spec["link"])
assert chart.spec["drill"] == ["大区", "省份"]
assert chart.spec["link"] == "销售"
```

**输出**：
- `['大区', '省份'] ['大区', '省份'] 销售`：两级下钻写入 spec，`roles._extra` 记录层级供前端使用。
- 点击某大区会按「大区 → 省份」推进，同组 `link="销售"` 的图跟着过滤，点击「其他」不触发下钻。

**验证**：`drill="省份"` 单字符串等价于 `["省份"]`；`drill=[]` 会抛 `ValueError`。
### 示例 6：分组缺失与同列分组
```python
import eazy_data_viz as edv

df = edv.sample_df()

try:
    edv.bar_pct(df, x="产品", y="销售额")
except ValueError as exc:
    print("ValueError:", str(exc)[:24])

same = edv.bar_pct(df, x="大区", y="销售额", color="大区")
print(same.spec["roles"]["color"], same.spec["roles"]["x"])
assert same.spec["roles"]["color"] == same.spec["roles"]["x"]
```

**输出**：
- `ValueError: bar_pct 需要 color（百分比的分组列）`：省略 `color` 直接报错，错误信息带正确写法示例。
- `大区 大区`：`color` 与 `x` 同列**不报错**，但每根柱子只有一段，恒为 100%——没有对比意义，属于常见误用。
- 正确做法：让 `color` 是另一个维度（产品/渠道/省份）。

**验证**：`chart.spec["percent"] is True`；同列分组时页面上的柱子全是满高。

## 常见错误

- **忘记传 `color`**
  - `bar_pct(df, x="产品", y="销售额")` → `ValueError: bar_pct 需要 color（百分比的分组列），例如 bar_pct(df, x="月份", y="销售额", color="产品")。`
  - 百分比构成必须有分组；只想看总量请用 `bar`。

- **`x` / `y` 缺失或 `y` 不是数值列**
  - 缺 `x` 或 `y` → `ValueError: bar_pct 需要 x / y，例如 bar_pct(df, x="月份", y="销售额", color="产品")。`
  - `y` 是文本列 → `TypeError: y（数值）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。`

- **`color` 与 `x` 传了同一列**
  - 不报错，但每根柱子只有一段、恒为 100%，等于白画。
  - 换一个真正有区分度的分组列（产品、渠道、大区）。

- **以为 `ylim` / `xlim` / `labels` / `zoom` / `top_n` 会生效**
  - 这 5 个参数只写入 spec：Y 轴固定 0~100%（ylim 被覆盖）、X 轴是 category 轴（xlim 不应用）、labels 不绘制、没有 dataZoom、topN 不截断。
  - 要减少分组：先在 Python 侧把占比小的类目合并成「其他」。

## 相关图表

- `area_pct`：同样的百分比构成，但用面积表达——时间连续时更好看。
- `bar`：绝对量柱状图（可堆叠），想看金额时用。
- `pie` / `rose`：单个类目的构成，不比较多个类目。
- `tile`：类目热力图，在一屏里放更多类目。
- `pictorial`：单指标类目对比的视觉化版本。
