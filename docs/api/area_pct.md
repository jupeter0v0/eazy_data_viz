# `area_pct` — 百分比堆叠面积图（构成随时间变化）

> 每个时间点所有分组归一化到 100%，用堆叠面积看「构成比例」怎么随时间演变。
> 适合：6~15 个时间点的构成占比（各产品月份销售占比、各渠道流量结构）、总和为 100% 的业务分配场景、想看「份额变化」而不是「绝对量」。
> 不适合：需要看绝对金额（用 `area`）、只看一个时间点（用 `pie` / `rose`）、分组超过 6 个（颜色难分、面积太碎）、时间点太少（<5 个点画不出趋势）。

## 函数签名

```python
eazy_data_viz.area_pct(
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

- `x`（时间/类目）、`y`（数值）、`color`（构成分组）三者**都必须传**；`color=None` 有专属报错，因为百分比构成没有分组就没有意义。
- 本图是 ECharts 的 `line + stack`（带 smooth），X 轴 `boundaryGap=False`，适合时间轴；离散类目请用 `bar_pct`。
- `ylim` / `xlim` / `labels` / `zoom` / `top_n` 只写入 spec，渲染器不应用（Y 轴被固定成 0~100%）。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list` | `—` | 是 | 数据源 |
| `x` | `str` | `—` | 是 | 时间/类目列名 |
| `y` | `str` | `—` | 是 | 数值列名 |
| `color` | `str \| None` | `None` | 否 | 构成分组列名（实际必传） |
| `agg` | `str` | `"sum"` | 否 | 聚合方式 |
| `sort` | `str \| None` | `None` | 否 | X 轴顺序：None / x / asc / desc |
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
- **取值建议**：`x` 是时间维时按天数据会有几百个点，建议先按月聚合再传，面积图 12~24 个点最好看。
- **示例**：`data=df`
- **常见错误**：空表 → `ValueError: 数据为空（0 行），无法绘图。`

### `x` — 时间/类目列名（必填）
- **类型**：`str`
- **默认值**：无
- **说明**：横轴，每个去重取值一个点；所有 `color` 分组在该点的值加起来归一化为 100%。X 轴是 category 轴（`boundaryGap=False`），时间字符串会按出现顺序排，除非 `x` 列是有序 category 或传 `sort="x"`。
- **取值建议**：`月份` / `日期` 这类时间维度；点之间最好等距，否则面积形状会失真。
- **示例**：`x="月份"`
- **常见错误**：省略 → `ValueError: area_pct 需要 x / y，例如 area_pct(df, x="日期", y="销售额", color="产品")。`

### `y` — 数值列名（必填）
- **类型**：`str`
- **默认值**：无
- **说明**：每个 (x, color) 组合聚合后的值，先按 `agg` 合并，再按 x 归一化到 100%（保留 1 位小数）。必须是数值 dtype，文本列先尝试 `pd.to_numeric`，失败抛 `TypeError`。
- **取值建议**：用**可加**的指标（销售额、订单数、客户数）；比率类指标（利润率）加总没有意义，应改用 `line`。
- **示例**：`y="销售额"`
- **常见错误**：`y="产品"` → `TypeError: y（数值）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `color` — 构成分组列名（默认 `None`，但实际必传）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：决定堆叠的层：每个去重取值一层。省略时**直接抛错**（本图没有分组的百分比没有意义），错误信息里带示例。
- **取值建议**：基数 2~6 的维度（产品、渠道、大区）；超过 6 层面积会很碎，建议先合并成「其他」。
- **示例**：`color="产品"`
- **常见错误**：省略 → `ValueError: area_pct 需要 color（百分比的分组列），例如 area_pct(df, x="日期", y="销售额", color="产品")。`

### `agg` — 聚合方式（默认 `"sum"`）
- **类型**：`str`
- **默认值**：`"sum"`
- **说明**：同一 (x, color) 多行时的合并方式，合法值 `sum` / `mean` / `count` / `max` / `min` / `median`。注意：百分比归一化发生在聚合之后，所以 `mean` 改变的是「每层的原始值」，最终仍会被归一化成占比。
- **取值建议**：销售额/订单数用 `sum`；想看「平均每单」的构成时用 `mean`（但结论会变成「按均值占比」）。
- **示例**：`agg="mean"`
- **常见错误**：`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, unique, max, min, median`

### `sort` — X 轴顺序（默认 `None`）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：`"x"` 按 X 自身顺序（类目有固定顺序时最有用，如 1月→12月）；`"asc"` / `"desc"` 按每个 x 的合计值排序；`None` 时若数据带类目顺序则按类目序，否则按出现顺序。时间序列一般不要排序，否则趋势线会来回折。
- **取值建议**：时间轴保持 `None`（配合 category 列的自然顺序）；想按业务量排行时刻意用 `desc`（此时横轴不再是时间）。
- **示例**：`sort="desc"`

### `top_n` — 只保留前 N 项（默认 `None`）
- **类型**：`int | None`
- **默认值**：`None`
- **说明**：写入 `spec["topN"]` 并做 ≥1 整数校验，但**本图不截断分组**：所有颜色层都会画出来。要减少层数请先在 Python 侧合并小分组。
- **取值建议**：保持 `None`；用 `df["产品"].where(df["产品"].isin(top), "其他")` 之类的方式合并。
- **示例**：`top_n=4`（只写 spec，页面不变）
- **常见错误**：`top_n=0` → `ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`

### `title` — 主标题（默认 `None`，自动生成）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：`None` 时自动生成「`y` 百分比构成」。
- **取值建议**：自动标题没有时间范围，建议手写「2024 各月销售构成」。
- **示例**：`title="2024 各月销售构成"`

### `subtitle` — 副标题（默认 `None`）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：标题下方灰色小字，写口径（是否含税、是否含退货）。
- **取值建议**：例如 `"按销售额占比，含税"`。
- **示例**：`subtitle="按销售额占比"`

### `xtitle` — X 轴标题（默认 `None`）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：X 轴下方标题，`None` 时回退成 `x` 列名。
- **取值建议**：列名已清楚时不用传。

### `ytitle` — Y 轴标题（默认 `None`）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：Y 轴标题，`None` 时回退成「占比」。Y 轴刻度固定为 0~100%。
- **取值建议**：默认「占比」已经贴切，一般不用改。
- **示例**：`ytitle="销售占比"`

### `xlim` — X 轴范围（默认 `None`，本图不生效）
- **类型**：`tuple(min, max) | None`
- **默认值**：`None`
- **说明**：只做格式校验后写入 spec；面积图的 X 轴是 category 轴，渲染器不应用 xlim。
- **取值建议**：不用传；要缩小时间窗口请先过滤数据。
- **常见错误**：`xlim=(1, 2, 3)` → `ValueError: xlim 需要是 (最小值, 最大值) 两元组，例如 xlim=(0, 100)`

### `ylim` — Y 轴范围（默认 `None`，会被 0~100% 覆盖）
- **类型**：`tuple(min, max) | None`
- **默认值**：`None`
- **说明**：格式校验后写入 spec，但**本图渲染器把 Y 轴固定成 `min=0`、`max=100`、刻度加 `%`**，所以 ylim 不会生效；这一点与 `pictorial` 等图不同。
- **取值建议**：不用传；百分比图本来就该固定 0~100%。
- **常见错误**：`ylim=5` → `ValueError: ylim 需要是 (最小值, 最大值) 两元组，例如 ylim=(0, 100)`

### `fmt` — 数值格式（默认 `"compact"`）
- **类型**：`str`
- **默认值**：`"compact"`
- **说明**：tooltip 里原始数值的格式（不是百分比本身），5 选 1：`compact` / `thousands` / `raw` / `currency` / `percent`。占比数字由渲染器统一加 `%`。
- **取值建议**：金额用 `compact`；想看原始小数用 `raw`。
- **示例**：`fmt="thousands"`
- **常见错误**：`fmt="usd"` → `ValueError: fmt='usd' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 图表高度（像素，默认 `380`）
- **类型**：`int`
- **默认值**：`380`
- **说明**：写进 `spec["height"]`；面积图高度太小时层与层之间的差异会被压扁，通用校验要求 ≥120。
- **取值建议**：12 个时间点用 360~400；24 个点或层数多时用 420~480。
- **示例**：`height=420`
- **常见错误**：`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题（默认 `"light"`）
- **类型**：`str`
- **默认值**：`"light"`
- **说明**：`light` 浅色底；`dark` 深色底，层色与网格线随主题切换。
- **取值建议**：与同页其它图一致。
- **示例**：`theme="dark"`
- **常见错误**：`theme="blue"` → `ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `legend` — 图例开关（默认 `True`）
- **类型**：`bool`
- **默认值**：`True`
- **说明**：前端条件是 `spec.legend !== false`；百分比构成必须有图例，否则不知道哪层是哪组。
- **取值建议**：保持 `True`；除非层数少且 `subtitle` 里写清了颜色含义。
- **示例**：`legend=False`

### `labels` — 数值标签（默认 `False`，本图不生效）
- **类型**：`bool`
- **默认值**：`False`
- **说明**：只写入 spec，面积叠加后每层数值位置重叠，渲染器不绘制标签；读数靠 tooltip（显示每层占比）。
- **取值建议**：保持 `False`。

### `zoom` — 缩放（默认 `"auto"`，本图不生效）
- **类型**：`str`
- **默认值**：`"auto"`
- **说明**：只写入 spec；本图没有 dataZoom 逻辑，时间点太多请先聚合而不是依赖缩放。
- **取值建议**：不用传。

### `drill` — 下钻维度列（默认 `None`）
- **类型**：`str | list[str] | None`
- **默认值**：`None`
- **说明**：点击面积图的 X 类目按维度逐级下钻，第一层自动作为 `roles.x`；本图是 ECharts 画布，点击事件可用。
- **取值建议**：`drill=["月份", "产品"]` 这类时间→细分类目的两级下钻；列必须真实存在。
- **示例**：`drill=["大区", "省份"]`
- **常见错误**：`drill=[]` → `ValueError: drill 不能是空列表；不需要下钻请传 drill=None。`

### `link` — 联动组名（默认 `None`）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：相同字符串为同一联动组，点击某个 x 类目会把该维度值广播给同组图表过滤；本条图既能发起也能接收。
- **取值建议**：同页图表用同一个组名（如 `"销售"`）。
- **示例**：`link="销售"`

### `max_rows` — 最大参与绘制的行数（默认 `2000000`）
- **类型**：`int | None`
- **默认值**：`200000`
- **说明**：超出行数时均匀抽样，提示写入 `chart.warnings["warnings"]`；`None` 关闭采样，`0` 得到空图。
- **取值建议**：百分比图对抽样不敏感（比例基本不变），默认值即可。
- **示例**：`max_rows=50000`

## 返回值

返回 `eazy_data_viz.Chart` 对象。

**Chart 的通用属性**

- `chart.spec`：`dict`。公共键 `id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`、`roles`、`agg`、`fmt`、`sort`、`topN`、`xtitle`、`ytitle`、`xlim`、`ylim`、`legend`、`labels`、`zoom`、`drill`、`link`；本图额外带 `percent: true`。
- `chart.data`：嵌入前端的绘图 payload（`cols/rows/dims/measures/kinds/orders/n/n_total`），`chart.data_ref` 是引用 id（`"d" + sha1 前 12 位`）。
- `chart.warnings`：`dict`，`{"warnings": [...], "n_total": 原始行数}`。

**Chart 的通用方法**

- `chart.to_html(inline=True)` / `chart.save(path, inline=True)`：导出完整 HTML（save 会写文件并返回绝对路径）；`chart.show(open_browser=None)` / `chart.palette(name)` / `chart.title`。

**本图 `spec` 的专属事实**

- `roles = {"x", "y", "color"}`；专属键 `percent: true`（前端据此走 `buildPercentStack`）。
- Y 轴固定 0~100% 并加 `%` → `ylim` 失效；`xlim`/`labels`/`zoom` 不参与渲染、`topN` 不截断；`legend` 默认 `True`、`height` 默认 `380`。

### 本图 `chart.spec` 的真实结构

下面是 `edv.area_pct(df, x="月份", y="销售额", color="产品")` 实际生成的 `spec`：

```json
{
  "id": "c1",
  "type": "area_pct",
  "title": "销售额 百分比构成",
  "subtitle": null,
  "theme": "light",
  "height": 380,
  "dataRef": "d3cae6f6e0275",
  "roles": {"x": "月份", "y": "销售额", "color": "产品"},
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
chart = edv.area_pct(df, x="月份", y="销售额", color="渠道")
assert chart.spec["type"] == "area_pct"
assert chart.spec["percent"] is True
assert chart.spec["legend"] is True
print(chart.title, chart.spec["roles"], chart.data["n"])
```

## 完整示例

以下示例都只依赖 `eazy_data_viz`，可直接复制运行。
### 示例 1：最简用法：各月销售构成
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.area_pct(df, x="月份", y="销售额", color="产品")

print(chart.title, chart.spec["percent"], chart.spec["roles"]["color"])
assert chart.spec["type"] == "area_pct"
assert chart.spec["percent"] is True
```

**输出**：
- `销售额 百分比构成 True 产品`：12 个月 × 4 个产品，每个月 4 层加起来都是 100%；Y 轴固定 0~100% 且刻度带 `%`，一层约 25% 上下浮动，份额变化通过层与层的宽度变化体现。

**验证**：`chart.spec["ylim"] is None`；即使传 `ylim=(20, 80)`，Y 轴仍是 0~100%。
### 示例 2：按渠道看结构变化
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.area_pct(
    df,
    x="月份",
    y="销售额",
    color="渠道",
    title="2024 各月渠道销售构成",
    subtitle="按销售额占比",
)

print(chart.spec["title"], len(chart.spec["roles"]))
assert chart.spec["roles"]["color"] == "渠道"
assert chart.spec["title"] == "2024 各月渠道销售构成"
```

**输出**：
- 3 层（直销 / 渠道代理 / 线上商城）叠加到 100%，每层约 30% 上下。
- 图例按渠道去重顺序列出，面积图从左到右是月份顺序；`subtitle` 说明口径，避免读者误以为是绝对金额。

**验证**：`len(df["渠道"].unique()) == 3`；分组数越少，层越厚越好读。
### 示例 3：排序、聚合与数值格式
```python
import eazy_data_viz as edv

df = edv.sample_df()
mean_chart = edv.area_pct(df, x="月份", y="销售额", color="产品", agg="mean")
sorted_chart = edv.area_pct(df, x="月份", y="销售额", color="产品", sort="desc")

print(mean_chart.spec["agg"], sorted_chart.spec["sort"])
assert mean_chart.spec["agg"] == "mean"
assert sorted_chart.spec["sort"] == "desc"
```

**输出**：
- `mean desc`：`agg` 换成 `mean` 后每层归一化的仍是占比，只是层内的原始均值不同；`sort="desc"` 会把月份按当月销售额合计从高到低排——**时间轴会被打乱**，一般不要对时间用排序。

**验证**：`sorted_chart.spec["sort"] == "desc"`；`sort="x"` 时按月份列固定顺序排。
### 示例 4：深色主题 + 高度 + 关图例
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.area_pct(
    df,
    x="月份",
    y="订单数",
    color="渠道",
    height=440,
    theme="dark",
    legend=False,
    xtitle="月份",
    ytitle="订单占比",
)

print(chart.spec["height"], chart.spec["theme"], chart.spec["legend"])
assert chart.spec["height"] == 440
assert chart.spec["legend"] is False
```

**输出**：
- `440 dark False`：深色底 + 440 高度，层与网格线对比更明显。
- 关掉图例后卡片更紧凑，但读者不知道颜色对应哪个渠道——只在 `subtitle` 写清时这样用；`ytitle` 覆盖默认的「占比」，`xtitle` 覆盖默认列名。

**验证**：`chart.spec["xtitle"] == "月份"`；`chart.spec["ytitle"] == "订单占比"`。
### 示例 5：下钻与联动
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.area_pct(
    df,
    x="月份",
    y="销售额",
    color="产品",
    drill=["月份", "产品"],
    link="销售",
)

print(chart.spec["drill"], chart.spec["roles"]["_extra"], chart.spec["link"])
assert chart.spec["drill"] == ["月份", "产品"]
assert chart.spec["link"] == "销售"
```

**输出**：
- `['月份', '产品'] ['月份', '产品'] 销售`：两级下钻写入 spec，`roles` 里记录 `_extra` 供前端取层级；点击某月会按「月份 → 产品」推进，同组 `link="销售"` 的图跟着过滤，点击「其他」不触发下钻。

**验证**：`drill="产品"` 单字符串等价于 `["产品"]`；`drill=[]` 会抛 `ValueError`。
### 示例 6：分组缺失时的专属报错
```python
import eazy_data_viz as edv

df = edv.sample_df()

try:
    edv.area_pct(df, x="月份", y="销售额")
except ValueError as exc:
    print("ValueError:", str(exc)[:26])

chart = edv.area_pct(df, x="月份", y="销售额", color="产品", max_rows=120)
print(chart.data["n"], chart.data["n_total"], bool(chart.warnings["warnings"]))
```

**输出**：
- `ValueError: area_pct 需要 color（百分比的分组列）`：省略 `color` 直接报错，错误信息里带正确写法示例。
- `120 1500 True`：`max_rows=120` 时只嵌入 120 行并写入采样提示（抽样对占比影响很小）；补上 `color` 即可正常出图。

**验证**：`chart.warnings["n_total"] == 1500`；`max_rows=None` 时 1500 行全部嵌入。

## 常见错误

- **忘记传 `color`**
  - `area_pct(df, x="月份", y="销售额")` → `ValueError: area_pct 需要 color（百分比的分组列），例如 area_pct(df, x="日期", y="销售额", color="产品")。`
  - 百分比构成必须有分组；只想看总量趋势请用 `area`。

- **`x` / `y` 缺失或 `y` 不是数值列**
  - 缺 `x` 或 `y` → `ValueError: area_pct 需要 x / y，例如 area_pct(df, x="日期", y="销售额", color="产品")。`
  - `y` 是文本列 → `TypeError: y（数值）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。`

- **以为 `ylim` / `xlim` / `labels` / `zoom` / `top_n` 会生效**
  - 这 5 个参数只写入 spec：Y 轴固定 0~100%（ylim 被覆盖）、X 轴是 category 轴（xlim 不应用）、labels 不绘制、没有 dataZoom、topN 不截断分组。
  - 要合并小组：`df["产品"] = df["产品"].where(df["产品"].isin(top3), "其他")`。

- **对时间轴用了 `sort="desc"` / `"asc"`**
  - 会把月份/日期按合计值重排，趋势线变成锯齿，看起来像数据错误。
  - 时间轴保持 `sort=None`（或 `sort="x"` 配合有序 category 列）。
## 相关图表

- `bar_pct`：同样的百分比构成，但用堆叠柱而不是面积——离散类目（大区/渠道）更清楚。
- `area`：绝对量堆叠/折线，想看金额而不是占比时用。
- `pie` / `rose`：单个时间点的构成。
- `line`：多个指标的趋势，不做归一化。
- `tile` / `bar`：类目量级对比，读数更准。
