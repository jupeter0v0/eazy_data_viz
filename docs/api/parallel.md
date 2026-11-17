# `parallel` — 平行坐标图（多维分布）

> 每行数据一条折线，穿过所有维度轴：用「线的走向」同时看多个数值维度，是发现离群值、聚类、维度相关性的工具。
> 适合：4~10 个数值维度的分布对比（订单的价格/数量/利润/折扣）、按类目分色的多维画像、找异常样本（某条线突然拐弯）。
> 不适合：精确读数（平行坐标只能看趋势）、维度间量级差异极大却不做归一化（线会全部贴着底部）、行数太多（上千条线会糊成一团，见 `max_rows`）。

## 函数签名

```python
eazy_data_viz.parallel(
    data,
    dims,
    *,
    color=None,
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    xlim=None,
    ylim=None,
    fmt="compact",
    height=440,
    theme="light",
    legend=False,
    labels=False,
    zoom=False,
    link=None,
    max_rows=200000,
) -> Chart
```

签名要点：

- `dims` 必填，是**数值列名列表**（也接受单个列名字符串）；日期列会报错，文本列会报错。
- 本图**没有** `agg` / `sort` / `top_n` / `drill` 参数：它是分布图，不做聚合、不排序、不下钻；`spec` 里的 `agg` 固定写 `"sum"`（不参与渲染）。
- `xtitle` / `ytitle` 只写入 spec——平行坐标没有直角坐标轴，轴名来自 `dims` 列名。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list` | `—` | 是 | 数据源 |
| `dims` | `list[str] \| str` | `—` | 是 | 数值维度列名列表 |
| `color` | `str \| None` | `None` | 否 | 分色列名，按取值拆成多个系列 |
| `title` | `str \| None` | `None` | 否 | 主标题 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `xtitle` | `str \| None` | `None` | 否 | X 轴标题（本图不生效） |
| `ytitle` | `str \| None` | `None` | 否 | Y 轴标题（本图不生效） |
| `xlim` | `tuple \| None` | `None` | 否 | X 轴范围（本图不生效） |
| `ylim` | `tuple \| None` | `None` | 否 | Y 轴范围（本图不生效） |
| `fmt` | `str` | `"compact"` | 否 | 数值格式（轴刻度、tooltip） |
| `height` | `int` | `440` | 否 | 图表高度（≥120） |
| `theme` | `str` | `"light"` | 否 | 主题：light / dark |
| `legend` | `bool` | `False` | 否 | 是否显示系列图例 |
| `labels` | `bool` | `False` | 否 | 数值标签（本图不生效） |
| `zoom` | `bool` | `False` | 否 | 缩放（本图不生效） |
| `link` | `str \| None` | `None` | 否 | 联动组名 |
| `max_rows` | `int \| None` | `200000` | 否 | 进入绘图的最大行数 |

## 参数详解

### `data` — 数据源（必填）
- **类型**：`pandas.DataFrame | dict | list`
- **默认值**：无
- **说明**：`frame.ensure_frame()` 统一转换；除 `dims` / `color` 外其余列也会嵌入 payload，但只有 `dims` 里的列会画到轴上。
- **取值建议**：平行坐标对行数敏感——**每行一条折线**，几百条还能看，几千条就是一团。传之前先筛选或采样（`max_rows`）。
- **示例**：`data=df`
- **常见错误**：空表 → `ValueError: 数据为空（0 行），无法绘图。`；`data=42` → `TypeError: 无法识别 data 类型 'int'，请传入 pandas.DataFrame（或 dict / list）。`

### `dims` — 维度列名列表（必填）
- **类型**：`list[str] | str`
- **默认值**：无
- **说明**：每一列对应一根平行轴，轴按列表顺序从左到右排列。必须都是**数值列**：文本列会先 `pd.to_numeric` 尝试，失败抛 `TypeError`；日期时间列直接抛 `TypeError`。列表里的 `None` 会被过滤；空列表等价于没传。
- **取值建议**：4~8 个维度最可读；各维度量纲相差很大时先做 min-max 归一化（见示例 3），否则小量级的轴会把线全压平。
- **示例**：`dims=["销售额", "订单数", "利润", "客户数"]`
- **常见错误**：省略 → `ValueError: parallel 需要 dims（数值列名列表），例如 parallel(df, ["价格", "销量", "利润"])。`；`dims=["日期"]` → `TypeError: dims[0]列 '日期' 需要是数值类型，但当前是日期时间类型。请换一列。`；`dims=["产品"]` → `TypeError: dims[0]列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `color` — 分色列名（默认 `None`，单系列）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：按该列的去重取值把折线分成多个系列，每个系列一种颜色。省略时所有线同色、只有一个系列。该列可以是文本/时间/数值，不参与数值校验。
- **取值建议**：用**基数 2~5** 的维度（大区、渠道、产品）分色；基数太大时颜色无法区分，先聚合或筛选。
- **示例**：`color="大区"`
- **常见错误**：列名不存在 → `KeyError: "color（分组）列 'xxx' 不存在。当前可用的列有：..."`

### `title` — 主标题（默认 `None`）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：`None` 时固定用「平行坐标」——本图的自动标题**不会**拼进维度名。
- **取值建议**：写清看的是什么分布，例如「各渠道订单的多维分布」。
- **示例**：`title="各渠道订单的多维分布"`

### `subtitle` — 副标题（默认 `None`）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：标题下方灰色小字，写样本量、口径、是否归一化。
- **取值建议**：例如 `"随机抽样 300 行，原始量纲"`——样本量对平行坐标的可读性影响很大，值得标注。
- **示例**：`subtitle="随机抽样 300 行"`

### `xtitle` / `ytitle` — 轴标题（默认 `None`，本图不生效）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：平行坐标没有直角坐标轴，两个参数只写入 spec，渲染器不绘制。轴名来自 `dims` 里的列名。
- **取值建议**：不要依赖；需要说明时用 `subtitle`，或把 DataFrame 列重命名成更短的中文再传。
- **示例**：`xtitle="维度"`

### `xlim` / `ylim` — 轴范围（默认 `None`，本图不生效）
- **类型**：`tuple(min, max) | None`
- **默认值**：`None`
- **说明**：只做「(最小值, 最大值) 两元组」格式校验后写入 spec；平行坐标的每根轴各自缩放，渲染器不应用这两个范围。
- **取值建议**：不用传；要控制量纲请先归一化数据。
- **示例**：`xlim=(0, 1)`
- **常见错误**：`xlim=5` → `ValueError: xlim 需要是 (最小值, 最大值) 两元组，例如 xlim=(0, 100)`

### `fmt` — 数值格式（默认 `"compact"`）
- **类型**：`str`
- **默认值**：`"compact"`
- **说明**：轴刻度标签与 tooltip 的数值格式，5 选 1：`compact` / `thousands` / `raw` / `currency` / `percent`（只加 `%`，不乘 100）。
- **取值建议**：金额用 `compact`；归一化后的 0~1 数值用 `raw`，否则会被显示成「1」以外的紧凑格式。
- **示例**：`fmt="raw"`
- **常见错误**：`fmt="usd"` → `ValueError: fmt='usd' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 图表高度（像素，默认 `440`）
- **类型**：`int`
- **默认值**：`440`
- **说明**：写进 `spec["height"]`；平行坐标是 9 个扩展图里默认最高的（440），因为维度多、线多时需要竖向空间。通用校验要求 ≥120。
- **取值建议**：4~6 个维度用 400~440；8 个以上维度或需要放图例时用 480~560。
- **示例**：`height=480`
- **常见错误**：`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `theme` — 主题（默认 `"light"`）
- **类型**：`str`
- **默认值**：`"light"`
- **说明**：`light` 浅色底；`dark` 深色底，轴、文字、折线颜色随主题切换。
- **取值建议**：与同页其它图一致；线多时深色底更不容易糊。
- **示例**：`theme="dark"`
- **常见错误**：`theme="blue"` → `ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `legend` — 图例开关（默认 `False`）
- **类型**：`bool`
- **默认值**：`False`
- **说明**：前端只在「有 `color` 且系列数 > 1」时才决定显示图例，条件是 `useColor && series 数 > 1 && spec.legend !== false`；所以单系列时传 `True` 也没有图例。
- **取值建议**：有 `color` 分组时建议打开（否则读者不知道哪种颜色代表谁）；单系列保持 `False`。
- **示例**：`legend=True`

### `labels` — 数值标签（默认 `False`，本图不生效）
- **类型**：`bool`
- **默认值**：`False`
- **说明**：只写入 spec，渲染器不对每条线标注数值（1500 条线也没法标）。
- **取值建议**：保持 `False`；要看具体值用 tooltip 或配套表格。

### `zoom` — 缩放（默认 `False`，本图不生效）
- **类型**：`bool`
- **默认值**：`False`
- **说明**：只写入 spec；平行坐标没有 dataZoom，传 `True` 也不会出现缩放条。
- **取值建议**：不用传；数据太多请先筛选/采样。

### `link` — 联动组名（默认 `None`）
- **类型**：`str | None`
- **默认值**：`None`
- **说明**：相同字符串的图属于同一联动组，会被同组图表的点击过滤。但平行坐标没有「类目维度」的概念（`currentXDim` 返回 `null`），**自身点击不会发起联动**，只能作为接收端。
- **取值建议**：需要联动时给个组名，但不要指望它作为联动源；下钻/联动源请用 `bar` / `pictorial` / `area_pct`。
- **示例**：`link="销售"`

### `max_rows` — 最大参与绘制的行数（默认 `200000`）
- **类型**：`int | None`
- **默认值**：`200000`
- **说明**：超出行数时**均匀抽样**（保留原始顺序感），提示写入 `chart.warnings["warnings"]`；`None` 关闭采样，`0` 得到空图。本图每行都会画一条折线，所以这个参数直接决定可读性与性能。
- **取值建议**：**强烈建议显式传 200~1000**；先按业务维度筛选再用 100~300 行做分布图。
- **示例**：`max_rows=300`
- **常见错误**：不传时 1500 行全画出来，图会变成一块「带子」，看不出分布。

## 返回值

返回 `eazy_data_viz.Chart` 对象。

**Chart 的通用属性**

- `chart.spec`：`dict`。公共键 `id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`、`roles`、`agg`、`fmt`、`sort`、`topN`、`xtitle`、`ytitle`、`xlim`、`ylim`、`legend`、`labels`、`zoom`、`drill`、`link`；本图额外带 `parallelDims`。
- `chart.data`：嵌入前端的绘图 payload：`{"cols", "rows", "dims", "measures", "kinds", "orders", "n", "n_total"}`；`chart.data_ref` 是引用 id（`"d" + sha1 前 12 位`）。
- `chart.warnings`：`dict`，`{"warnings": [...], "n_total": 原始行数}`。

**Chart 的通用方法**

- `chart.to_html(inline=True)`：完整 HTML 字符串；`chart.save(path, inline=True)`：写文件并返回绝对路径。
- `chart.show(open_browser=None)` / `chart.palette(name)` / `chart.title`。

**本图 `spec` 的专属事实**

- `roles = {"dims": [...], "color": 分色列或 None}`；专属键 `parallelDims` 是同一份维度列表（前端用它建轴）。
- `agg` 固定 `"sum"`、`sort` / `topN` / `drill` 恒为 `null`（本图没有这些参数，也不参与渲染）。
- `xtitle` / `ytitle` / `xlim` / `ylim` / `labels` / `zoom` 均写入但不参与渲染；只有 `color` 分组 > 1 时 `legend` 才真正起作用。

### 本图 `chart.spec` 的真实结构

下面是 `edv.parallel(df, ["销售额", "订单数", "利润"], color="大区", max_rows=300)` 实际生成的 `spec`：

```json
{
  "id": "c1",
  "type": "parallel",
  "title": "平行坐标",
  "subtitle": null,
  "theme": "light",
  "height": 440,
  "dataRef": "d3cae6f6e0275",
  "roles": {"dims": ["销售额", "订单数", "利润"], "color": "大区"},
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
  "link": null,
  "parallelDims": ["销售额", "订单数", "利润"]
}
```

**验证返回值的小技巧**

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.parallel(df, ["销售额", "订单数", "利润"], color="渠道", max_rows=200)
assert chart.spec["type"] == "parallel"
assert chart.spec["parallelDims"] == ["销售额", "订单数", "利润"]
assert chart.spec["agg"] == "sum" and chart.spec["drill"] is None
print(chart.title, chart.data["n"], chart.spec["roles"]["color"])
```

## 完整示例

以下示例都只依赖 `eazy_data_viz`，可直接复制运行。

### 示例 1：最简用法：三个维度
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.parallel(df, ["销售额", "订单数", "利润"], max_rows=300)

print(chart.title, chart.spec["parallelDims"], chart.data["n"])
assert chart.spec["parallelDims"] == ["销售额", "订单数", "利润"]
assert chart.data["n"] == 300
```

**输出**：
- `平行坐标 ['销售额', '订单数', '利润'] 300`：3 根轴、300 条折线。
- 列名直接作为轴名显示在轴的上方；轴顺序就是列表顺序。
- 不传 `color` 时所有线同色，图例不显示。

**验证**：`chart.spec["legend"] is False`；把 `max_rows` 去掉会画出 1500 条线，页面明显变糊。

### 示例 2：按类目分色
```python
import eazy_data_viz as edv

df = edv.sample_df()
sub = df[df["大区"].isin(["华东", "华北"])]

chart = edv.parallel(
    sub,
    ["销售额", "利润", "客户数"],
    color="大区",
    legend=True,
    title="华东 vs 华北：订单多维分布",
)

print(chart.spec["roles"]["color"], chart.spec["legend"], chart.data["n"])
assert chart.spec["roles"]["color"] == "大区"
assert chart.data["n"] == 900
```

**输出**：
- `大区 True 900`：两个大区两个颜色，图例列出华东/华北。
- 900 条线仍偏多但能看出两团的分布差异（华东线整体偏上）。
- 颜色只按 `color` 列分，不按行数据自动聚类。

**验证**：`sub.shape[0] == 900`（华东 450 + 华北 450）；再筛到一个大区时 `legend=True` 也不显示图例。

### 示例 3：量纲差异大时先归一化
```python
import eazy_data_viz as edv

df = edv.sample_df()
dims = ["销售额", "订单数", "利润"]
cols = df[dims].astype(float)
norm = (cols - cols.min()) / (cols.max() - cols.min())

chart = edv.parallel(norm, dims, fmt="raw", max_rows=200, title="归一化后的多维分布")

print(chart.spec["parallelDims"], chart.spec["fmt"], float(norm["销售额"].max()))
assert abs(float(norm["销售额"].max()) - 1.0) < 1e-9
```

**输出**：
- `['销售额', '订单数', '利润'] raw 1.0`：3 根轴都缩放到 0~1，线不会因为某个维度量级大而被压平。
- `fmt="raw"` 让轴刻度显示 `0.2`、`0.4` 这类小数，而不是 compact 的「万」。
- 归一化后各轴可比性增强，但失去了原始单位——角度只代表相对位置。

**验证**：`norm[dims].min().min() == 0.0`、`norm[dims].max().max() == 1.0`。

### 示例 4：多维度 + 大图 + 深色主题
```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.parallel(
    df,
    ["销售额", "订单数", "利润", "客户数"],
    height=520,
    theme="dark",
    subtitle="随机抽样 200 行",
    max_rows=200,
)

print(chart.spec["height"], chart.spec["theme"], chart.spec["roles"]["dims"])
assert chart.spec["height"] == 520
```

**输出**：
- `520 dark ['销售额', '订单数', '利润', '客户数']`：4 根轴、高度 520，深色背景下折线更醒目。
- `subtitle` 标注样本量，提醒读者这不是全量数据。
- 维度只能是数值列——想加「省份」这种文本列作为维度会直接抛 `TypeError`（见常见错误），不要写进 `dims`。

**验证**：`chart.spec["height"] == 520`；`dims` 里混入任何文本列都会在 Python 侧报错。

### 示例 5：只看头部样本（nlargest）
```python
import eazy_data_viz as edv

df = edv.sample_df()
top = df.nlargest(80, "销售额")

chart = edv.parallel(
    top,
    ["销售额", "利润", "客户数"],
    color="产品",
    legend=True,
    title="销售额 TOP 80 订单的多维画像",
    height=460,
)

print(chart.data["n"], top.shape[0])
assert chart.data["n"] == 80
```

**输出**：
- `80 80`：只有 80 条线，几乎每条都能单独追踪，橙色/蓝色/绿色按产品区分。
- 这种「先筛头部再看分布」的用法比直接画 1500 行有效得多。
- `nlargest` 保留的是原始行，不影响其它列。

**验证**：`top["销售额"].min() <= df["销售额"].max()`；换 `nsmallest` 可以看尾部样本的画像。

### 示例 6：边界：日期列不能当维度
```python
import eazy_data_viz as edv

df = edv.sample_df()

try:
    edv.parallel(df, ["日期", "销售额"], max_rows=100)
except TypeError as exc:
    print("TypeError:", str(exc)[:32])

chart = edv.parallel(df, ["销售额", "销售额"], max_rows=100)
print(chart.spec["parallelDims"])
assert chart.spec["parallelDims"] == ["销售额", "销售额"]
```

**输出**：
- `TypeError: dims[0]列 '日期' 需要是数值类型，但当前是日期时间类型`：日期列不能直接当维度，先转成数值（如 `df["日期"].astype("int64")` 或月份序号）。
- `['销售额', '销售额']`：同一列重复传不会报错，会画出两根相同的轴（没有意义，但说明本图不做去重校验）。
- `dims` 传单个字符串 `"销售额"` 等价于 `["销售额"]`。

**验证**：`chart.spec["parallelDims"] == ["销售额", "销售额"]`；真实使用时不要重复列。

## 常见错误

- **`dims` 里混入文本列 / 日期列**
  - 文本列 → `TypeError: dims[0]列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`
  - 日期列 → `TypeError: dims[0]列 '日期' 需要是数值类型，但当前是日期时间类型。请换一列。`
  - 先把要用的列转成数值（`astype(float)` / `pd.to_numeric` / 日期取月份序号）再传。

- **行数太多，图糊成一团**
  - 平行坐标不聚合，**每行一条线**；`sample_df()` 全量 1500 行已经很难读。
  - 显式传 `max_rows=200~500`，或先按业务维度筛选、用 `nlargest` / `sample` 取子集。

- **各维度量纲差异太大**
  - 金额（几十万）和订单数（个位数）放在一起，订单数那根轴的线全压在底部。
  - 先做 min-max 归一化再画；归一化后 `fmt` 建议用 `raw`。

- **想用 `agg` / `sort` / `top_n` / `drill`**
  - 本图没有这些参数（`agg` 固定写 `"sum"` 但不参与渲染）；传了会直接 `TypeError: parallel() got an unexpected keyword argument`。
  - 需要聚合/排序请先 `groupby` 好数据；需要下钻请用 `bar` / `pictorial`。

## 相关图表

- `radar`：同样是多维对比，但对象少、看「形状」；`parallel` 适合对象多、看「分布」。
- `scatter`：两两维度之间的关系；`parallel` 是多维的并排视图。
- `heatmap`：二维矩阵的精确对比。
- `bar`：单维度精确比较，读数比平行坐标准确。
- `box`：看单个维度的分布区间，与平行坐标的「分布」视角互补。
