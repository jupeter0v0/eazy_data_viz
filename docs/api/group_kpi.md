# `group_kpi` — KPI 指标卡片组

> 把一组关键数字排成一排卡片：大号数值 + 单位 + 环比箭头 + 一行小字备注，适合放在看板最上方。
> 适合：Dashboard 顶部的「总销售额 / 订单数 / 利润 / 客户数」、按大区或渠道拆开的核心指标、需要人工指定数值与环比的场景。
> 不适合：需要趋势或对比的数值（用 `bar` / `line`）、单个指标的达成率圆环（用 `ring_progress`）、多行明细（用 `table`）、需要排名的进度条列表（用 `progress`）。

## 函数签名

```python
eazy_data_viz.group_kpi(
    data=None,
    names=None,
    values=None,
    *,
    items=None,
    agg="sum",
    sort="desc",
    top_n=6,
    unit=None,
    delta=None,
    fmt="compact",
    title=None,
    subtitle=None,
    height=140,
    theme="light",
) -> Chart
```

签名要点：

- `data`、`names`、`values` 是位置参数，但有默认值 `None`，因此三种用法都能省略——`group_kpi(df)`、`group_kpi(df, "大区", "销售额")`、`group_kpi(items=[...])`。
- `items` 优先级最高：传了 `items` 就**完全忽略** `data` / `names` / `values` / `sort` / `top_n` / `unit`（详见下文）。
- 没有 `max_rows` / `link` / `drill` / `legend` / `labels` / `zoom` / `xtitle` / `ytitle` / `xlim` / `ylim`；本图是 **HTML 组件**，前端 `EazyViz.htmlBuilders["group_kpi"]` 直接渲染 `spec["items"]`。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| None` | `None` | 否 | 数据源；用 `items` 时可省略 |
| `names` | `str \| None` | `None` | 否 | 分组列名，每个类目一张卡 |
| `values` | `str \| None` | `None` | 否 | 数值列名，None 时按类目计数 |
| `items` | `list[dict] \| dict \| None` | `None` | 否 | 手工指定卡片，优先级最高 |
| `agg` | `str` | `"sum"` | 否 | 聚合方式：sum/mean/count/max/min/median |
| `sort` | `str` | `"desc"` | 否 | 卡片顺序：desc / asc / 其它（保序） |
| `top_n` | `int` | `6` | 否 | 最多几张卡 |
| `unit` | `str \| None` | `None` | 否 | 数值后缀单位（如「万元」） |
| `delta` | `float \| list \| None` | `None` | 否 | 同比/环比变化的小数比例（0.128 = 12.8%），标量给第 1 张、列表逐张 |
| `fmt` | `str` | `"compact"` | 否 | 数值格式 |
| `title` | `str \| None` | `None` | 否 | 主标题 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `height` | `int` | `140` | 否 | 卡片最小高度（≥120） |
| `theme` | `str` | `"light"` | 否 | 主题：light / dark |

## 参数详解

### `data` — 数据源（默认 `None`）

- **类型**：`pandas.DataFrame | dict | list | None`
- **默认值**：`None`
- **说明**：由 `frame.ensure_frame()` 转成 DataFrame。传了 `items` 时该参数被完全忽略；`data` 与 `items` 都没传会抛 `ValueError`。
- **取值建议**：从明细表直接传整份 DataFrame 即可，本图只读 `names` / `values` 两列；想减小页面体积可先 `df[["大区", "销售额"]]`。
- **示例**：`data=df`
- **常见错误**：`group_kpi()` → `ValueError: group_kpi 需要 data（DataFrame）或 items=[...]，例如 group_kpi(df, names="大区", values="销售额")。`；`group_kpi(pd.DataFrame())` → `ValueError: 数据为空（0 行），无法绘图。`

### `names` — 分组列名（默认 `None`，自动挑选）

- **类型**：`str | None`
- **默认值**：`None`
- **说明**：每个不同取值生成一张卡片，标签就是该取值。与 `values` 同时为 `None` 时走「每个数值列一张卡」模式；只给 `names` 时省略 `values`，卡片数值是**该组行数**。
  - `names=None` 但 `values` 有值时，自动用 `_pick_dim(df)` 挑第一个分类列（`sample_df` 里是「月份」）。
  - 缺失值（NaN）会被归到标签 `—` 的卡片里。
- **取值建议**：基数 3~8 个的维度最合适（大区、渠道、产品）；基数太大时先用 `top_n` 截断。
- **示例**：`names="大区"`
- **常见错误**：列名写错 → `KeyError: "names（分组）列 '不存在' 不存在。当前可用的列有：..."`；数据没有分类列 → `ValueError: group_kpi 需要 names（分组列），例如 group_kpi(df, names="大区", values="销售额")。`

### `values` — 数值列名（默认 `None`，按组计数）

- **类型**：`str | None`
- **默认值**：`None`
- **说明**：决定卡片上的数值。必须是数值列（文本列会先被 `pd.to_numeric(errors="coerce")` 尝试转换，失败则抛 `TypeError`）。省略时按组计数（每行记 1.0），`agg` 的默认 `sum` 正好等于条数。
- **取值建议**：金额用 `sum`；客单价、转化率用 `mean`；想看覆盖量就省略该参数。
- **示例**：`values="销售额"`
- **常见错误**：`values="产品"` → `TypeError: values（数值）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `items` — 手工指定卡片（默认 `None`，优先级最高）

- **类型**：`list[dict] | dict | None`
- **默认值**：`None`
- **说明**：完全绕过 DataFrame，直接给卡片数据；单个 dict 会被包成 `[dict]`。每项支持的键：
  - `label`（str）：卡片标题，缺省为 `""`（显示空白）。
  - `value`（number，**必填**）：卡片大号数值，必须能转成数值。
  - `delta`（number | None）：同比/环比变化的小数比例，前端显示为 `▲ 8.2%` / `▼ 3.4%`（见 `delta` 参数）。
  - `unit`（str | None）：该卡的数值后缀单位，**会覆盖全局 `unit`**（items 模式下全局 `unit` 不生效）。
  - `fmt`（str | None）：该卡数值格式，缺省继承全局 `fmt`。
  - `hint`（str | None）：卡片第三行灰色小字，写口径或备注。
  - 传了 `items` 后 `data` / `names` / `values` / `sort` / `top_n` **全部不生效**：不排序、不截断、不做列校验。
- **取值建议**：指标来自多张表、或多个口径时用 `items`；把单位写进 `unit`、口径写进 `hint`，卡片才自解释。
- **示例**：`items=[{"label": "总销售额", "value": 1631033.57, "unit": "元"}]`
- **常见错误**：非 dict → `TypeError: items[0] 需要是 dict，例如 {"label": "总销售额", "value": 123}，收到 'str'`；缺 `value` 或非数值 → `ValueError: items[0] 缺少可用的数值 value，收到 None`；`items=[]` → `ValueError: group_kpi 没有可展示的指标。`

### `agg` — 聚合方式（默认 `"sum"`）

- **类型**：`str`
- **默认值**：`"sum"`
- **说明**：同一分组多行时的合并方式，合法值 `sum` / `mean` / `count` / `max` / `min` / `median`。该值只影响 Python 侧算出的卡片数值，也会写进 `spec["agg"]`；`items` 模式下不参与计算（仅原样写入 spec）。
- **取值建议**：总量用 `sum`；客单价、平均利润用 `mean`；担心极值用 `median`；想显式计数用 `count`。
- **示例**：`agg="mean"`
- **常见错误**：`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median`

### `sort` — 卡片顺序（默认 `"desc"`）

- **类型**：`str`
- **默认值**：`"desc"`
- **说明**：**只在 `names` 模式生效**，且只影响 Python 侧生成的 `items` 顺序：
  - `"desc"`：按数值从大到小；`"asc"`：从小到大；其它值（含 `"none"`）：保持分组首次出现顺序。
  - 该参数**不会写进 spec**（`spec["sort"]` 恒为 `null`），排序结果体现在 `chart.spec["items"]` 的数组顺序上。
  - `items` 模式与「每个数值列一张卡」模式都不排序（后者按 DataFrame 列顺序）。
- **取值建议**：排行用 `desc`；「短木板」看板用 `asc`；想保持业务固定顺序（如东→西）用 `"none"` 并自己排好 DataFrame。
- **示例**：`sort="asc"`

### `top_n` — 最多几张卡（默认 `6`）

- **类型**：`int`
- **默认值**：`6`
- **说明**：
  - `names` 模式：排序后截断到前 N 个类目，**不合并「其他」**。
  - 每数值列一卡模式：取 DataFrame 里前 N 个数值列。
  - `items` 模式：**不生效**（手工指定的卡片全部显示）。
  - 必须 ≥1 的整数（bool 会被拒绝）。
- **取值建议**：卡片每行最多 4 张，6~8 张是两行最舒服；超过 8 张建议拆成两个图或先聚合。
- **示例**：`top_n=4`
- **常见错误**：`top_n=0` → `ValueError: top_n 需要是 >=1 的整数，收到 0`

### `unit` — 数值单位后缀（默认 `None`）

- **类型**：`str | None`
- **默认值**：`None`
- **说明**：拼在卡片数值后面的小字，例如 `"万元"`、`"单"`、`"人"`。**只在 DataFrame 模式生效**；`items` 模式下要用每项自己的 `unit`。
- **取值建议**：数值本身已是「万」为单位时写 `"万元"`；不要和 `fmt="currency"` 的 `¥` 重复表达。
- **示例**：`unit="万元"`

### `delta` — 同比/环比变化（默认 `None`）

- **类型**：`float | list[float] | None`
- **默认值**：`None`
- **说明**：写入每张卡片的 `items[i]["delta"]`，前端渲染成 `▲/▼ + abs(delta * 100).toFixed(1) + '%'`：
  - **delta 是「小数比例」，与 `kpi()` 一致**：`delta=0.082` 显示 `▲ 8.2%`，`delta=-0.034` 显示 `▼ 3.4%`；传 `8.2` 会显示成 `▲ 820.0%`。
  - 标量：只写第 1 张卡（`items[0]`），其余卡片没有箭头。
  - list / tuple：按顺序逐张写入，长度不足的部分保持 `None`，超长部分被忽略。
  - 非数值会被 `_num_or_none` 转成 `None`（不报错）；`None` 表示不显示环比。
- **取值建议**：百分点数据先除以 100（`8.2 → 0.082`）；零增长传 `0.0` 会显示 `▲ 0.0%`。
- **示例**：`delta=[0.082, -0.034, 0.011, 0.0]`

### `fmt` — 数值格式（默认 `"compact"`）

- **类型**：`str`
- **默认值**：`"compact"`
- **说明**：卡片数值的格式，5 选 1：`compact`（163.1万 / 1.3亿）、`thousands`（1,631,034）、`raw`（1631033.57）、`currency`（¥1,631,033.57，两位小数）、`percent`（只加 `%`，不乘 100）。`items` 每项可用自己的 `fmt` 覆盖。
- **取值建议**：大额金额用 `compact`；需要精确读数用 `thousands`；比率类（同比增长）先把数值存成百分数（12.4）再配 `percent`。
- **示例**：`fmt="thousands"`
- **常见错误**：`fmt="usd"` → `ValueError: fmt='usd' 不支持，可选：compact, thousands, raw, percent, currency`

### `title` — 主标题（默认 `None`）

- **类型**：`str | None`
- **默认值**：`None`
- **说明**：`None` 时自动用「关键指标」。标题不影响布局，但会占用卡片头部。
- **取值建议**：一排放两组 KPI 时用标题区分口径，例如「2024 全年 · 全渠道」。
- **示例**：`title="2024 全年核心指标"`

### `subtitle` — 副标题（默认 `None`）

- **类型**：`str | None`
- **默认值**：`None`
- **说明**：标题下的灰色小字，写时间范围、口径、数据更新时间。
- **取值建议**：一行以内，例如 `"同比口径：2023 全年"`。
- **示例**：`subtitle="同比口径：2023 全年"`

### `height` — 卡片最小高度（像素，默认 `140`）

- **类型**：`int`
- **默认值**：`140`
- **说明**：写入 `spec["height"]`，页面里作为 `min-height` 使用；**卡片组的真实高度由卡片数量决定**（前端布局每行 4 张、每行约 62px，`_card_height` 不读 `spec.height`），所以调大 `height` 不会让卡片变高，只会让容器底部留白。
- **取值建议**：保持 140；确实需要更多留白时再调大。
- **示例**：`height=160`
- **常见错误**：`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `theme` — 主题（默认 `"light"`）

- **类型**：`str`
- **默认值**：`"light"`
- **说明**：`light` 浅色底 + 深色数值；`dark` 深色底 + 浅色数值，上涨/下跌箭头的颜色随主题调整。
- **取值建议**：与同页其它图一致；大屏、夜间看板用 `dark`。
- **示例**：`theme="dark"`
- **常见错误**：`theme="blue"` → `ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

## 返回值

返回 `eazy_data_viz.Chart` 对象。

**Chart 的通用属性**

- `chart.spec`：`dict`。公共键 `id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`（本图为 `None`）、`roles`（本图为 `{}`）、`agg`、`fmt`、`sort`（本图为 `None`）、`topN`、`xtitle`、`ytitle`、`xlim`、`ylim`、`legend`、`labels`、`zoom`、`drill`、`link`；本图额外带 `items`。
- `chart.data`：手工图不接 DataFrame，恒为 `{"cols": [], "rows": [], "n": 0}`。
- `chart.data_ref`：`None`。
- `chart.warnings`：`{}`（手工图不做采样提示）。

**Chart 的通用方法**

- `chart.to_html(inline=True)` / `chart.save(path, inline=True)`：导出完整 HTML（save 会写文件、自动建目录、返回绝对路径）。
- `chart.show(open_browser=None)`：浏览器打开。
- `chart.palette(name)`：换配色并返回 `self`。
- `chart.title`：只读属性，等于 `spec["title"]`。

**本图 `spec` 的专属事实**

- `spec["items"]` 是**已经算好的卡片数组**，前端不做任何聚合、排序或截断，只按顺序画。
- 每项固定 6 个键：`label`、`value`、`delta`、`unit`、`fmt`、`hint`，缺省值为 `""` / 数值 / `None` / `None` / `"compact"` / `None`。
- `sort` 只影响数组顺序，所以 `spec["sort"]` 恒为 `null`；`top_n` 会写进 `spec["topN"]`，但 items 模式下它只是记录，不影响数组长度。

### 本图 `chart.spec` 的真实结构

下面是 `edv.group_kpi(df, names="大区", values="销售额", delta=[8.2, -3.4, 1.1, 0.0])` 实际生成的 `spec`：

```json
{
  "id": "c1",
  "type": "group_kpi",
  "title": "关键指标",
  "subtitle": null,
  "theme": "light",
  "height": 140,
  "dataRef": null,
  "roles": {},
  "agg": "sum",
  "fmt": "compact",
  "sort": null,
  "topN": 6,
  "xtitle": null,
  "ytitle": null,
  "xlim": null,
  "ylim": null,
  "legend": false,
  "labels": false,
  "zoom": false,
  "drill": null,
  "link": null,
  "items": [
    {"label": "华东", "value": 582863.53, "delta": 8.2, "unit": null, "fmt": "compact", "hint": null},
    {"label": "华北", "value": 476047.98, "delta": -3.4, "unit": null, "fmt": "compact", "hint": null},
    {"label": "华南", "value": 347045.62, "delta": 1.1, "unit": null, "fmt": "compact", "hint": null},
    {"label": "西部", "value": 225076.44, "delta": 0.0, "unit": null, "fmt": "compact", "hint": null}
  ]
}
```

**验证返回值的小技巧**

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.group_kpi(df, names="大区", values="销售额")
items = chart.spec["items"]
assert len(items) == 4
assert items[0]["label"] == "华东"
assert items[0]["value"] == 582863.53
assert chart.spec["dataRef"] is None and chart.data["n"] == 0
print(len(items), items[0], chart.title)
```

## 完整示例

以下示例都只依赖 `eazy_data_viz`，可直接复制运行。

### 示例 1：最简用法：每个数值列一张卡

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.group_kpi(df)

print([(it["label"], round(it["value"], 2)) for it in chart.spec["items"]])
assert [it["label"] for it in chart.spec["items"]] == ["销售额", "订单数", "利润", "客户数"]
```

**输出**：
- `销售额 1631033.57` / `订单数 2568.0` / `利润 325738.59` / `客户数 1922.0`：4 个数值列各一张卡，默认 `agg="sum"`。
- 页面显示为 `163.1万`、`2568`、`32.6万`、`1922`（compact 格式）。
- 卡片顺序与 DataFrame 列顺序一致，不排序。

**验证**：`len(chart.spec["items"]) == 4`；`top_n=2` 时只保留前三列中的前两列（销售额、订单数）。

### 示例 2：按类目拆卡：各大区销售额

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.group_kpi(
    df,
    names="大区",
    values="销售额",
    title="各大区销售额",
    subtitle="2024 全年",
    unit="元",
)

print([(it["label"], round(it["value"], 1)) for it in chart.spec["items"]])
assert chart.spec["items"][0]["label"] == "华东"
assert chart.spec["items"][0]["unit"] == "元"
```

**输出**：
- `[('华东', 582863.5), ('华北', 476048.0), ('华南', 347045.6), ('西部', 225076.4)]`：每类目一张卡，默认按值降序。
- 页面上数值后缀带「元」：`58.3万 元`。
- 省略 `values` 时改为按类目计数：4 个大区分别是 450 / 450 / 300 / 300 行。

**验证**：`chart.spec["topN"] == 6`；把 `sort` 改成 `"asc"` 后顺序变成 西部 → 华南 → 华北 → 华东。

### 示例 3：items 手工模式：多口径指标 + 环比

```python
import eazy_data_viz as edv

chart = edv.group_kpi(
    items=[
        {"label": "总销售额", "value": 1631033.57, "unit": "元", "hint": "全渠道合计"},
        {"label": "平均客单价", "value": 1087.36, "fmt": "thousands", "hint": "销售额/订单数"},
        {"label": "同比增长", "value": 12.4, "fmt": "percent", "delta": 0.124},
        {"label": "覆盖客户", "value": 1922, "unit": "人"},
    ],
    title="关键指标",
    subtitle="数据截至 2024-12-31",
)

print(len(chart.spec["items"]), chart.spec["items"][2]["fmt"])
assert chart.data == {"cols": [], "rows": [], "n": 0}
```

**输出**：
- `4 percent`：4 张卡全部显示；第 3 张卡 `fmt="percent"` 显示 `12.4%`。
- 每张卡：`总销售额 / 平均客单价 / 同比增长 / 覆盖客户`，带各自的单位或备注。
- `chart.data` 是空 payload——手工模式不嵌入任何数据行。

**验证**：`chart.spec["dataRef"] is None`；`chart.spec["items"][0]["unit"] == "元"`。

### 示例 4：delta 的两种写法

```python
import eazy_data_viz as edv

df = edv.sample_df()

scalar = edv.group_kpi(df, names="大区", values="销售额", delta=0.125)
print([(it["label"], it["delta"]) for it in scalar.spec["items"]])

listed = edv.group_kpi(df, names="大区", values="销售额", delta=[0.082, -0.034, 0.011, 0.0])
print([(it["label"], it["delta"]) for it in listed.spec["items"]])

assert scalar.spec["items"][0]["delta"] == 0.125
assert [it["delta"] for it in scalar.spec["items"][1:]] == [None, None, None]
assert listed.spec["items"][1]["delta"] == -0.034
```

**输出**：
- `[('华东', 0.125), ('华北', None), ('华南', None), ('西部', None)]`：标量只作用于第 1 张卡；前端显示 `▲ 12.5%`。
- `[('华东', 8.2), ('华北', -3.4), ('华南', 1.1), ('西部', 0.0)]`：列表逐张写入。
- 页面上分别显示 `▲ 8.2%`、`▼ 3.4%`、`▲ 1.1%`、`▲ 0.0%`（负值自动换箭头与颜色）。

**验证**：`delta=0.12` 会显示 `▲ 0.1%`，可以确认 delta 是百分点数值而不是小数比例。

### 示例 5：排序与截断

```python
import eazy_data_viz as edv

df = edv.sample_df()
desc = edv.group_kpi(df, names="渠道", values="销售额", top_n=2)
asc = edv.group_kpi(df, names="渠道", values="销售额", sort="asc", top_n=2)

print([(it["label"], round(it["value"], 1)) for it in desc.spec["items"]])
print([(it["label"], round(it["value"], 1)) for it in asc.spec["items"]])
assert desc.spec["topN"] == 2 and len(desc.spec["items"]) == 2
```

**输出**：
- `[('直销', 613719.3), ('渠道代理', 528777.8)]`：默认按值降序取前 2。
- `[('线上商城', 488536.5), ('渠道代理', 528777.8)]`：升序取前 2，顺序反过来。
- 3 个渠道里被截掉的 1 个不会合并成「其他」，直接不显示。

**验证**：`chart.spec["sort"] is None`——排序只体现在 items 数组顺序里。

### 示例 6：聚合方式与深色主题

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.group_kpi(
    df,
    names="产品",
    values="销售额",
    agg="mean",
    top_n=4,
    fmt="thousands",
    title="各产品平均单笔销售额",
    theme="dark",
)

print([(it["label"], round(it["value"], 2)) for it in chart.spec["items"]])
assert chart.spec["agg"] == "mean"
assert chart.spec["theme"] == "dark"
```

**输出**：
- `[('智能终端', 1430.94), ('行业软件', 1201.73), ('云服务', 1085.1), ('运维服务', 630.44)]`：`mean` 是平均单笔销售额，量级从 `sum` 的几十万变成一千上下。
- `fmt="thousands"` 显示为 `1,430.94` 这类千分位；深色主题下卡片底色、文字色与箭头颜色自动反转。
- 4 张卡排成一行，卡片高度由数量决定，不受 `height` 影响。

**验证**：`chart.spec["agg"] == "mean"`；换成默认 `sum` 会看到 53.7万 / 45.1万 / 40.8万 / 23.6万 的总量口径。

## 常见错误

- **在 items 模式下期待 `top_n` / `sort` / `unit` 生效**
  - `items` 优先且完全绕过 DataFrame 逻辑：`sort` 不排序、`top_n` 不截断、全局 `unit` 不生效（会被每项的 `unit` 覆盖）。
  - 想截断就自己在 Python 侧切片，想排序就自己排好列表顺序。

- **把 delta 当成小数比例传入**
  - 前端按百分点渲染：`delta=0.082` 显示 `▲ 0.1%`，不是 `8.2%`。
  - 接口返回比例时先 `delta * 100`；百分比为 `None` 的卡片不要传 `0`（会显示 `▲ 0.0%`）。

- **`values` 用了文本列 / 列名写错**
  - `values="产品"` → `TypeError: values（数值）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`
  - `names="不存在的列"` → `KeyError: "names（分组）列 '不存在的列' 不存在。当前可用的列有：..."`

- **少传了数据和 items**
  - `group_kpi()` → `ValueError: group_kpi 需要 data（DataFrame）或 items=[...]，例如 group_kpi(df, names="大区", values="销售额")。`
  - `group_kpi(pd.DataFrame({"a": ["x"]}))` → `ValueError: group_kpi 需要至少 1 个数值列（或直接传 items=[...]）；当前 DataFrame 里没有数值列。`
  - `items=[]` 或空 DataFrame → `ValueError: group_kpi 没有可展示的指标。` / `ValueError: 数据为空（0 行），无法绘图。`

## 相关图表

- `kpi`：单值指标卡（带图标/背景），适合只强调一个数字；`group_kpi` 是一排数字的版本。
- `ring_progress`：单个指标的达成率圆环，比卡片更有「进度」语义。
- `progress`：多类目进度条排行，数值大小 + 百分比一起看。
- `tile`：多类目方块热力图，用颜色表达量级，不显示数值细节。
- `bar`：需要精确比较各维度数值大小时用柱状图。
