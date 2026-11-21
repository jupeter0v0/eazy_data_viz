# `tile` — 瓦片图（类目量级色块）

> 把每个类目画成一个方块，用**颜色深浅**而不是长度表达数值大小；一眼就能看出「谁强谁弱、分布是否悬殊」。
> 适合：类目数量中等（5~30 个）、只需要看相对量级而不需要精确读数的场景（大区销售额、门店业绩、渠道贡献）。
> 不适合：需要精确比较（用 `bar`）、看趋势（用 `line` / `area`）、类目非常多且需要下钻（用 `treemap`）、表达占比构成（用 `pie` / `bar_pct`）。

## 函数签名

```python
eazy_data_viz.tile(
    data,
    names=None,
    values=None,
    *,
    agg="sum",
    sort=None,
    top_n=None,
    title=None,
    subtitle=None,
    fmt="compact",
    height=360,
    theme="light",
    link=None,
    max_rows=200000,
) -> Chart
```

签名要点：

- `data` 必填，`names` / `values` 都可以省略：省略 `names` 时自动挑第一个分类列（日期或文本），省略 `values` 时统计记录数。
- `agg`、`sort`、`top_n`、`title`、`subtitle`、`fmt`、`height`、`theme`、`link`、`max_rows` 全部是 keyword-only，必须写 `agg="mean"` 这种形式。
- 没有 `color`（瓦片本身就按类目着色）、没有 `xlim` / `ylim` / `legend` / `labels` / `zoom` / `drill` —— 瓦片图不是坐标轴图。
- 瓦片图是 **HTML 组件**（不是 ECharts 画布），由前端 `EazyViz.htmlBuilders["tile"]` 渲染成方块网格。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list` | `—` | 是 | 数据源 |
| `names` | `str \| None` | `None` | 否 | 类目列名，None 时自动挑分类列 |
| `values` | `str \| None` | `None` | 否 | 数值列名，None 时统计记录数 |
| `agg` | `str` | `"sum"` | 否 | 聚合方式：sum/mean/count/max/min/median |
| `sort` | `str \| None` | `None` | 否 | 排序偏好（当前版本瓦片固定按值降序，见下文） |
| `top_n` | `int \| None` | `None` | 否 | 只保留前 N 个类目（当前版本瓦片不截断，见下文） |
| `title` | `str \| None` | `None` | 否 | 主标题 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `fmt` | `str` | `"compact"` | 否 | 瓦片数值格式 |
| `height` | `int` | `360` | 否 | 画布/卡片高度（≥120） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `str` | `"light"` | 否 | 主题：light / dark |
| `link` | `str \| None` | `None` | 否 | 联动组名 |
| `max_rows` | `int \| None` | `200000` | 否 | 进入绘图的最大行数，None 表示不采样 |

## 参数详解

### `data` — 数据源（必填）

- **类型**：`pandas.DataFrame | dict | list`
- **默认值**：无
- **说明**：由 `frame.ensure_frame()` 统一处理：DataFrame 原样使用，`dict` / `list` 先转 DataFrame；行数超过 `max_rows` 时均匀抽样并把提示写进 `chart.warnings`。只读取 `names` / `values` 两列，但整份数据都会嵌入前端 payload。
- **取值建议**：正式代码用 DataFrame；只需要两列时先 `df = df[["大区", "销售额"]]`，能明显减小页面体积。
- **示例**：`data=df`
- **常见错误**：`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`；`data=42` → `TypeError: 无法识别 data 类型 'int'，请传入 pandas.DataFrame（或 dict / list）。`

### `names` — 类目列名（默认 `None`，自动挑选）

- **类型**：`str | None`
- **默认值**：`None`
- **说明**：每个方块对应的类目，通常是文本列。省略时走 `_pick_dim(df)`：先找第一个分类列（pandas category 或文本列），找不到再找第一个时间列；`edv.sample_df()` 里第一个分类列是「月份」。
- **取值建议**：类目数控制在 5~30 个；用有业务含义的维度（大区、产品、渠道），不要用城市 × 省份这类组合；类目太多时先聚合到上层维度。
- **示例**：`names="大区"`
- **常见错误**：列名写错 → `KeyError: "names（类目）列 '不存在' 不存在。当前可用的列有：..."`；没有分类列且省略 names → `ValueError: tile 需要 names（类目列），例如 tile(df, names="门店", values="销售额")；当前 DataFrame 里没有分类/时间列。`

### `values` — 数值列名（默认 `None`，统计记录数）

- **类型**：`str | None`
- **默认值**：`None`
- **说明**：决定方块颜色深浅的列，必须是数值 dtype；文本列会被拒绝而不是静默转成 0。省略时按 `names` 分组计数，内部把 `agg` 强制改成 `count`，自动标题里的度量名写成「记录数」。
- **取值建议**：可加指标用 `sum`，比率用 `mean` / `median`，关注极值用 `max` / `min`；想看覆盖度（每个类目多少条记录）就省略该参数。
- **示例**：`values="销售额"`
- **常见错误**：`values="大区"` → `TypeError: values（数值）列 '大区' 需要是数值类型（当前是文本，例如 ['华东', '华北', ...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `agg` — 聚合方式（默认 `"sum"`）

- **类型**：`str`
- **默认值**：`"sum"`
- **说明**：同一个类目对应多行时如何合并。合法值只有 `sum` / `mean` / `count` / `max` / `min` / `median`，其它值抛 `ValueError`。聚合在前端做，`chart.data` 里仍是原始行。
- **取值建议**：金额、件数等可加指标用 `sum`；单价、比率用 `mean` 或 `median`；比率列不要直接 `sum`（会得到无意义的和）。
- **示例**：`agg="mean"`
- **常见错误**：`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median`

### `sort` — 排序偏好（默认 `None`）

- **类型**：`str | None`
- **默认值**：`None`
- **说明**：语义上控制方块顺序（`desc` / `asc` 按值，`x` 按类目自身顺序，`none` 保持原序），但**当前瓦片渲染器固定按数值降序**、不读取 `spec.sort`；该参数只会写进 spec，不改变画面。不做取值范围校验。
- **取值建议**：想「最大在前」什么都不用传；需要严格类目顺序时改用 `bar` / `heatmap`。
- **示例**：`sort="asc"`（只影响 `spec.sort`）

### `top_n` — 只保留前 N 个类目（默认 `None`）

- **类型**：`int | None`
- **默认值**：`None`
- **说明**：语义是只展示前 N 项，必须 ≥1（bool 会被拒绝）。但**当前瓦片渲染器不读 `spec.topN`**：所有类目都会画出来，不会合并「其他」；Python 侧也不截断，`chart.data["n"]` 仍是全部行数。
- **取值建议**：要在页面上只显示前 N 项，先在 pandas 里聚合 + 排序 + `head(n)` 再传；不要用 `top_n` 控制方块数量。
- **示例**：`top_n=6`（只写进 spec）
- **常见错误**：`top_n=0` → `ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`

### `title` — 主标题（默认 `None`）

- **类型**：`str | None`
- **默认值**：`None`
- **说明**：`None` 时自动生成「`values` 瓦片图」，`values` 也为 `None` 时是「记录数 瓦片图」；长度建议 ≤24 个汉字，过长会挤压右侧的「代码」按钮。
- **取值建议**：自动标题只说明指标，建议显式写成业务口径，例如「各大区销售额（2024 全年）」。
- **示例**：`title="各大区销售额"`
- **常见错误**：无（任意字符串都接受）

### `subtitle` — 副标题（默认 `None`）

- **类型**：`str | None`
- **默认值**：`None`
- **说明**：标题下方的灰色小字，写口径、时间范围、单位；会让卡片头部从 8px 变成 46px。建议不超过两行。
- **取值建议**：`"2024 全年，含税，单位：元"` 这类一句话说明即可。
- **示例**：`subtitle="2024 全年，含税"`

### `fmt` — 数值格式（默认 `"compact"`）

- **类型**：`str`
- **默认值**：`"compact"`
- **说明**：瓦片数值的显示格式，5 选 1：`compact`（1.2万 / 1.3亿）、`thousands`（千分位）、`raw`（原始值）、`currency`（¥ + 两位小数）、`percent`（只加 `%`，不乘 100）。只影响显示，不影响颜色映射。
- **取值建议**：金额大、格子小用 `compact`；需要精确读数用 `thousands`；0~1 的小数要先把列乘以 100 再配 `percent`。
- **示例**：`fmt="thousands"`
- **常见错误**：`fmt="usd"` → `ValueError: fmt='usd' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素，默认 `360`）

- **类型**：`int`
- **默认值**：`360`
- **说明**：写入 `spec["height"]`；瓦片属于自适应高度组件，页面里以 `min-height: 360px` 渲染，内容按方块数量自然撑开。通用校验要求 ≥120。
- **取值建议**：6~12 个方块保持 360；20 个以上调到 420~480；深色大屏可再加 40~60px。
- **示例**：`height=420`
- **常见错误**：`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题（默认 `"light"`）

- **类型**：`str`
- **默认值**：`"light"`
- **说明**：`light` 浅色热力色阶；`dark` 深色底 + 深色系色阶。方块文字颜色按背景亮度自动切黑/白。
- **取值建议**：与页面其它图统一主题；大屏、夜间模式用 `dark`。
- **示例**：`theme="dark"`
- **常见错误**：`theme="blue"` → `ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `link` — 联动组名（默认 `None`）

- **类型**：`str | None`
- **默认值**：`None`
- **说明**：相同字符串为一组；同组中其它图表被点击时，本图按点击的维度过滤后重算。瓦片是 HTML 组件、**自身不绑定点击**，只能作为接收端；联动是否生效取决于数据里是否有被点击的那一列。
- **取值建议**：用业务含义命名（`link="销售"`），同一页面所有需要联动的图传完全相同的字符串；不要指望点瓦片能触发联动。
- **示例**：`link="销售"`
- **常见错误**：无（不做校验，非法值只会在前端退化为默认行为）

### `max_rows` — 最大参与绘制的行数（默认 `200000`）

- **类型**：`int | None`
- **默认值**：`200000`
- **说明**：超出行数时做**均匀抽样**（不是简单截断），提示写进 `chart.warnings["warnings"]`，`n_total` 保留原始行数；传 `None` 关闭采样。传 `0` 会得到 0 行空图，传负数行为未定义（源码不做范围校验）。
- **取值建议**：瓦片聚合后只有几十个方块，保持默认即可；需要精确的 `mean` 时先自行 groupby，或传 `max_rows=None`。
- **示例**：`max_rows=50000`
- **常见错误**：无（不做取值校验；`max_rows=0` 会得到只有提示没有数据的空图）

## 返回值

返回 `eazy_data_viz.Chart` 对象。

**Chart 的通用属性**

- `chart.spec`：`dict`，前端渲染配置。公共键有 `id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`、`roles`、`agg`、`fmt`、`sort`、`topN`、`xtitle`、`ytitle`、`xlim`、`ylim`、`legend`、`labels`、`zoom`、`drill`、`link`；本图没有专属绘图键，`roles` 里装的是 `names` / `value`。
- `chart.data`：嵌入前端的绘图 payload，不是 DataFrame。结构是 `{"cols": [...列名], "rows": [...], "dims": [...], "measures": [...], "kinds": {...}, "orders": {...}, "n": 行数, "n_total": 原始行数}`；瓦片图只需要其中 `roles.names` / `roles.value` 两列，但整份 payload 都会随页面输出。
- `chart.data_ref`：数据引用 id（`"d" + sha1 前 12 位`），同一次会话里内容相同的数据复用同一个 id。
- `chart.warnings`：`dict`，形如 `{"warnings": ["数据 1500 行，超过 max_rows=30，已均匀采样 30 行用于绘图。"], "n_total": 1500}`；没有降级时是 `{"warnings": [], "n_total": 行数}`。

**Chart 的通用方法**

- `chart.to_html(inline=True)`：返回完整 HTML 字符串（内联约 1.2~1.5MB）。
- `chart.save(path, inline=True)`：写文件、自动建目录、返回绝对路径。
- `chart.show(open_browser=None)`：浏览器打开。
- `chart.palette(name)`：换配色并返回 `self`。
- `chart.title`：只读属性，等于 `spec["title"]`。

**本图 `spec` 的专属事实**

- `roles = {"names": 类目列, "value": 数值列}`（省略时填自动挑选的列名或 `None`）。
- 没有专属绘图键；`sort` / `topN` 会写进 spec，但当前渲染器不读取（见「参数详解」）。
- `labels` / `legend` / `zoom` 固定为 `false`，`drill` / `xlim` / `ylim` 固定为 `null`。

### 本图 `chart.spec` 的真实结构

下面是 `edv.tile(df, names="大区", values="销售额")` 实际生成的 `spec`：

```json
{
  "id": "c1",
  "type": "tile",
  "title": "销售额 瓦片图",
  "subtitle": null,
  "theme": "light",
  "height": 360,
  "dataRef": "d3cae6f6e0275",
  "roles": {
    "names": "大区",
    "value": "销售额"
  },
  "agg": "sum",
  "fmt": "compact",
  "sort": null,
  "topN": null,
  "xtitle": null,
  "ytitle": null,
  "xlim": null,
  "ylim": null,
  "legend": false,
  "labels": false,
  "zoom": false,
  "drill": null,
  "link": null
}
```

**验证返回值的小技巧**

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.tile(df, names="大区", values="销售额")
assert chart.spec["type"] == "tile"
assert chart.spec["roles"] == {"names": "大区", "value": "销售额"}
assert chart.data["n"] == 1500
print(chart.title, chart.data_ref, len(chart.data["rows"]))
```

## 完整示例

以下示例都只依赖 `eazy_data_viz` 与 `pandas`，可直接复制运行。

### 示例 1：最简用法：各大区销售额

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.tile(df, names="大区", values="销售额")

print(chart.title)
print(chart.spec["roles"])
assert chart.spec["type"] == "tile"
```

**输出**：
- `销售额 瓦片图`（默认标题 = 「度量名 + 瓦片图」）。
- `{'names': '大区', 'value': '销售额'}`：角色映射原样写进 spec。
- 页面渲染 4 个方块，颜色从深到浅依次是 华东（58.3 万）> 华北（47.6 万）> 华南（34.7 万）> 西部（22.5 万）。

**验证**：`chart.spec["agg"] == "sum"`；4 个方块按数值降序排列（瓦片图固定行为）。

### 示例 2：省略参数：自动挑类目、自动计数

```python
import eazy_data_viz as edv

df = edv.sample_df()
counts = edv.tile(df, names="大区")   # 省略 values → 计数
auto = edv.tile(df)                    # 两个都省略 → 自动挑类目列

print(counts.title, counts.spec["agg"], counts.spec["roles"]["value"])
print(auto.spec["roles"]["names"])
assert counts.spec["agg"] == "count"
assert auto.spec["roles"]["names"] == "月份"
```

**输出**：
- `记录数 瓦片图 count None`：省略 `values` 时 `agg` 被强制为 `count`，`roles.value` 为 `None`。
- `月份`：两个参数都省略时，自动挑第一个分类列（`sample_df` 里是「月份」）。
- 计数结果：华东 / 华北各 450 条，华南 / 西部各 300 条；按月份则每月 100~150 条。

**验证**：`counts.spec["roles"]["value"] is None`；只含数值列的数据省略 `names` 会抛「需要 names」。

### 示例 3：换聚合方式：各大区平均销售额

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.tile(
    df,
    names="大区",
    values="销售额",
    agg="mean",
    fmt="raw",
    title="各大区平均销售额",
    subtitle="均值易受大单影响，仅供参考",
)

print(chart.spec["agg"], chart.spec["title"], chart.spec["fmt"])
assert chart.spec["agg"] == "mean"
```

**输出**：
- `mean 各大区平均销售额 raw`：聚合方式、标题、格式都写进 spec。
- 4 个方块分别显示平均单笔销售额（约 1087 元/笔，四个大区数值接近，颜色差异很小）。

**验证**：`chart.spec["agg"] == "mean"`；对比示例 1 会看到方块颜色分布完全不同（均值差异远小于求和差异）。

### 示例 4：派生列：各大区利润率

```python
import eazy_data_viz as edv

df = edv.sample_df()
df["利润率"] = df["利润"] / df["销售额"]
chart = edv.tile(
    df,
    names="大区",
    values="利润率",
    agg="mean",
    fmt="percent",
    title="各大区平均利润率",
)

print(round(df["利润率"].mean() * 100, 2))
assert "利润率" in df.columns
```

**输出**：
- `20.0` 左右：`sample_df` 的整体利润率约为 20%。
- 方块显示 `0.2%` 这类数字——`fmt="percent"` 只加百分号、不乘 100，看到 `0.2%` 说明传的是 0~1 的小数；想显示 20% 需要先把派生列乘以 100。

**验证**：`chart.spec["roles"]["value"] == "利润率"`；把 `values` 换成 `"销售额"` 时超大数据会被拒绝（文本列才会报错，数值列正常）。

### 示例 5：主题与高度

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.tile(
    df,
    names="省份",
    values="销售额",
    height=460,
    theme="dark",
    fmt="thousands",
    title="各省份销售额",
    subtitle="10 个省份，2024 全年",
    link="销售",
)

print(chart.spec["height"], chart.spec["theme"], chart.spec["link"])
assert chart.spec["height"] == 460
assert chart.spec["theme"] == "dark"
```

**输出**：
- `460 dark 销售`：高度、主题、联动组名都写入 spec。
- 10 个省份方块按销售额降序排列，深色背景下颜色由暗到亮表示从高到低。
- 联动组名只写进 spec；瓦片自身不响应点击，但同组其它图被点击时本图会被筛选。

**验证**：`chart.spec["link"] == "销售"`；多图放进同一个 `edv.dashboard(...)` 页面后联动才会真正生效。

### 示例 6：大数据采样

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.tile(df, names="渠道", values="销售额", max_rows=100)

print(chart.data["n"], chart.warnings["n_total"])
print(chart.warnings["warnings"])
assert chart.data["n"] == 100
```

**输出**：
- `100 1500`：只有 100 行进入绘图，原始 1500 行记录在 `n_total`。
- 提示文本：`['数据 1500 行，超过 max_rows=100，已均匀采样 100 行用于绘图。']`
- 3 个方块（渠道代理、直销、线上商城）的数值基于抽样后的 100 行，与全量结果略有差异。

**验证**：`len(chart.data["rows"]) == 100`；传 `max_rows=None` 后 `chart.warnings["warnings"] == []`。

## 常见错误

- **`values` 传了文本列**
  - `tile(df, names="大区", values="产品")` → `TypeError: values（数值）列 '产品' 需要是数值类型（当前是文本，例如 ['智能终端', '云服务', '行业软件', '运维服务']）。请先用 pd.to_numeric() 清洗，或换一列。`
  - 数值列里有少量脏值（非数字字符）时，内部会尝试 `pd.to_numeric(errors="coerce")`；如果可转换比例低于 99%，同样抛这个错。先清洗：`df["销售额"] = pd.to_numeric(df["销售额"], errors="coerce").fillna(0)`。

- **以为 `sort` / `top_n` 能控制瓦片顺序和数量**
  - 当前版本瓦片渲染器固定按数值降序、且不截断；`sort` / `top_n` 只会写进 `spec`。
  - 需要只显示前 N 个类目：先在 pandas 里筛选（`df.groupby(...).sum().sort_values().head(n)` 再重建 DataFrame），或改用 `bar` + `top_n`。

- **类目列没传、数据里也没有分类列**
  - 省略 `names` 且几列全是数值 → `ValueError: tile 需要 names（类目列），例如 tile(df, names="门店", values="销售额")；当前 DataFrame 里没有分类/时间列。`
  - 这种数据先把数值列分箱成类目（`pd.cut`），或显式传一个文本列。

- **`fmt` / `theme` / `height` 传了非法值**
  - `fmt` 只能是 compact、thousands、raw、percent、currency；`theme` 只能是 light、dark；`height` 必须 ≥120。
  - `fmt="percent"` 不会把 0.2 显示成 20%，派生比率列要自己乘以 100。

## 相关图表

- `progress`：同样按类目聚合，但用「进度条长度 + 百分比」表达，能读出相对比例，适合排行。
- `treemap`：类目有层级、数量很多时用嵌套矩形；瓦片图是它的「单层、等大方块」简化版。
- `heatmap`：要同时看两个维度（行 × 列）的数值强弱时用热力图，瓦片图只有一个维度。
- `bar`：需要精确比较数值大小时用柱状图，颜色只做强调。
- `group_kpi`：把几个关键数字做成卡片，比瓦片图更强调绝对值和环比。
