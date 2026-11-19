# `map_bubble` — 区域气泡地图

> 在区域中心画气泡，用气泡大小表达一个指标、用颜色区分分组，适合同时看「在哪、多大、属于哪类」。
> 适合：城市级分布（各城市销售额 + 订单数）、双指标地图（气泡大小 + 颜色分组）、世界市场对比。
> 不适合：只要深浅对比（用 geo_map）、点与点之间的流向（用 map_flow）、精确排名（用 bar）。

## 函数签名

```python
eazy_data_viz.map_bubble(
    data, region, value=None, *,
    map="china", agg="sum", size=None, color=None,
    fmt="compact", min_size=4, max_size=28, name_map=None,
    zoom=None, palette=None, height=460, theme="light",
    title=None, subtitle=None, drill=None, link=None,
    legend=True, section=None,
) -> Chart
```

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源 DataFrame |
| `region` | `str` | `—` | 是 | 区域列：城市 / 省份 / 国家名 |
| `value` | `str` | `None` | 否 | 气泡数值列（tooltip 与颜色/大小映射的基准） |
| `map` | `str` | `'china'` | 否 | 内置地图：`china` / `world` / `beijing` |
| `agg` | `str` | `'sum'` | 否 | 同一区域多行时的聚合方式 |
| `size` | `str` | `None` | 否 | 气泡大小指标列；省略时用 `value` 映射半径 |
| `color` | `str` | `None` | 否 | 分组列，每个取值一组气泡并进入图例 |
| `fmt` | `str` | `'compact'` | 否 | tooltip 与数值格式 |
| `min_size` | `int \| float` | `4` | 否 | 最小气泡半径（像素） |
| `max_size` | `int \| float` | `28` | 否 | 最大气泡半径（像素） |
| `name_map` | `dict \| None` | `None` | 否 | 数据区域值 → 地图区域名的映射 |
| `zoom` | `bool \| str \| None` | `None` | 否 | 是否允许鼠标缩放、平移 |
| `palette` | `str \| None` | `None` | 否 | 配色方案名 |
| `height` | `int` | `460` | 否 | 画布高度（≥120） |
| `theme` | `str` | `'light'` | 否 | `light` / `dark` |
| `title` | `str \| None` | `None` | 否 | 主标题；省略自动生成 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `drill` | `str \| list[str]` | `None` | 否 | 点击区域后聚焦该区域 |
| `link` | `str \| None` | `None` | 否 | 联动组名 |
| `legend` | `bool` | `True` | 否 | 是否显示图例（有 `color` 分组时才有图例） |
| `section` | `str \| None` | `None` | 否 | 看板分区标题 |

## 参数详解

### `data` — 数据源（必填）

- **作用**：图表取数的唯一入口；`Series` 转单列、`dict` / `list` 转 DataFrame。超过 20 万行会均匀抽样并写进 `chart.warnings`。`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`
- **取值建议 / 示例**：传清洗好的 `DataFrame`，例如 `data=df`；聚合与匹配都在前端完成，原始明细行会完整注入页面。

### `region` — 区域列名（必填）

- **作用**：气泡落点的区域列。城市支持 `广州` / `广州市`、省份支持 `广东` / `广东省`、世界图用国家名（中文常用国名或 GeoJSON 英文名）。气泡直接画在城市坐标上，**不会**汇总到省份（这一点与 `geo_map` 不同）。
- **取值建议 / 示例**：城市级分析用 `region="城市"`；省级气泡用 `region="省份"`。列名写错 → `KeyError: "region（区域列）列 '不存在' 不存在。当前可用的列有：..."`；传空串 → `ValueError: region（区域列） 需要是非空字符串，收到 '  '。`

### `value` — 气泡数值列

- **类型 / 默认值**：`str`；`None`。
- **作用**：tooltip 主数值；未传 `size` 时也用于映射气泡半径；省略时按区域统计记录数（`agg` 内部改成 `count`，标题度量名写成「记录数」）。文本型数字自动转数值；纯文本列会抛 `TypeError`（与 `geo_map` 的静默空图不同）。
- **取值建议 / 示例**：销售额用 `value="销售额"`；想同时表达规模与数量时再配合 `size`。`value="省份"` → `ValueError: value 不能与 region 是同一列：region 是区域名，value 是数值。`

### `map` — 使用哪张内置地图

- **类型 / 默认值**：`str`；`'china'`。
- **作用**：`china` 有 34 个省级区域，`world` 有 215 个国家/地区。选 `world` 时 `region` 必须是国家名；用省份名会全部匹配不到，整张图变空。
- **取值建议 / 示例**：中国城市用默认值；国家列用 `map="world"`。`map="usa"` → `ValueError: map 只支持 "china"（中国）/ "world"（世界），收到 'usa'。`

### `agg` — 聚合方式

- **类型 / 默认值**：`str`；`'sum'`。
- **作用**：同一区域（且同一分组）有多行时先聚合，可选 `sum`、`mean`、`count`、`max`、`min`、`median`；`value=None` 时强制 `count`。
- **取值建议 / 示例**：销售额用 `sum`、客单价用 `mean`，例如 `agg="mean"`。`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median`

### `size` — 气泡大小指标列

- **类型 / 默认值**：`str`；`None`（所有气泡同样大小）。
- **作用**：控制气泡半径，按 `sqrt` 缩放到 `min_size ~ max_size` 像素之间（面积与数值近似成正比，避免大值视觉爆炸）。**省略时用 `value` 作为大小映射**；只传 `size` 不传 `value` 时内部按记录数聚合，`size` 列实际不生效。与 `region` 同名列会报错。
- **取值建议 / 示例**：用订单数放大销售额高的城市，例如 `value="销售额", size="订单数"`。`size="城市"` → `ValueError: size 不能与 region 是同一列：region 是区域名，size 是数值。`

### `color` — 分组列

- **类型 / 默认值**：`str`；`None`（全部气泡同色）。
- **作用**：按该列的每个取值生成一个 `scatter` 系列，自动配色并生成图例；同一区域出现在多个分组时，气泡会围绕区域中心散开，避免完全重叠。与 `region` 同名列会报错。
- **取值建议 / 示例**：按渠道分组看结构，例如 `color="渠道"`；分组不要超过 6 个取值，否则图例过长、颜色难辨。`color="城市"` → `ValueError: color 不能与 region 是同一列：region 是区域名，color 是分组列。`

### `fmt` — 数值格式

- **类型 / 默认值**：`str`；`'compact'`。
- **作用**：控制 tooltip 与度量数值的格式，可选 `compact`（1.9万）、`thousands`（19,519）、`raw`（195190.32）、`percent`、`currency`。
- **取值建议 / 示例**：默认 `compact`；核对数字用 `fmt="thousands"`。`fmt="wan"` → `ValueError: fmt='wan' 不支持，可选：compact, thousands, raw, percent, currency`

### `min_size` — 最小气泡半径

- **类型 / 默认值**：`int | float`；`4`（像素）。
- **作用**：气泡半径下界；`size=None` 时半径由 `value` 映射，`min_size` / `max_size` 仍是这条映射的上下界。必须大于 0 且小于 `max_size`。
- **取值建议 / 示例**：点多、地图密时调到 2～4，例如 `min_size=2`。`min_size=0` → `ValueError: min_size / max_size 需要大于 0，收到 min_size=0、max_size=28。`

### `max_size` — 最大气泡半径

- **类型 / 默认值**：`int | float`；`28`（像素）。
- **作用**：气泡半径上界；世界地图气泡容易压盖，通常调小到 18～24。必须大于 `min_size`。
- **取值建议 / 示例**：`min_size=2, max_size=20`。`min_size=30, max_size=10` → `ValueError: min_size 必须小于 max_size，收到 min_size=30、max_size=10。`

### `name_map` — 区域名映射

- **类型 / 默认值**：`dict | None`；`None`。
- **作用**：键是数据原值（精确匹配），值是地图区域名。城市映射目标必须在内置城市表里（369 个可匹配名称），省份/国家映射目标必须是地图区域；映射目标不存在时浏览器控制台提示后忽略，继续按原值兜底。
- **取值建议 / 示例**：把业务缩写映射成标准名，例如 `name_map={"USA": "United States", "UK": "United Kingdom"}`。传 `list` → `TypeError: name_map 需要是 dict，例如 name_map={'USA': 'United States'}，收到 'list'。`

### `zoom` — 是否允许鼠标缩放与平移

- **类型 / 默认值**：`bool | str | None`；`None`。
- **作用**：开关语义：只有 `False` 关闭缩放/平移，`None`、`True`、`'auto'`、`'scale'`、`'move'` 行为一致（都允许）。默认视角固定（中国中心 `[104, 35.5]`、世界 `zoom=1.12`）；自定义视角可改 `chart.spec["mapZoom"]` / `chart.spec["mapCenter"]`。
- **取值建议 / 示例**：静态看板设 `zoom=False`。`zoom=2` → `ValueError: zoom 只支持 None / True / False / 'auto'（地图里表示是否允许鼠标缩放和平移），收到 2。`

### `palette` — 配色方案

- **类型 / 默认值**：`str | None`；`None`（页面默认，初始 `google`）。
- **作用**：可选 `google`、`antd`、`tableau`、`carbon`、`echarts`、`morandi`、`tailwind`。单组气泡取主色，多组按配色序列分配、并影响图例色块。
- **取值建议 / 示例**：`palette="tableau"`；未知配色 → `ValueError: 未知配色 'foo'，可选：google、antd、tableau、carbon、echarts、morandi、tailwind`

### `height` — 画布高度

- **类型 / 默认值**：`int`；`460`（像素，最小 120）。
- **作用**：画布高度；放进 `dashboard` 后卡片还会加标题与工具栏高度。
- **取值建议 / 示例**：城市点多时用 520～600，例如 `height=560`。`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `theme` — 主题

- **类型 / 默认值**：`str`；`'light'`。
- **作用**：只支持 `light` / `dark`，影响背景、文字、描边与配色。
- **取值建议 / 示例**：深色看板用 `theme="dark"`。`theme="blue"` → `ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `title` — 主标题

- **类型 / 默认值**：`str | None`；`None`（自动生成 `"<度量> · <区域列>气泡地图"`，例如「销售额 · 城市气泡地图」）。注意自动标题使用 `region` 列名，而不是「中国/世界」。
- **作用**：显示在画布顶部的主标题。
- **取值建议 / 示例**：`title="城市销售额与订单量"`。

### `subtitle` — 副标题

- **类型 / 默认值**：`str | None`；`None`。
- **作用**：主标题下方的小字，常写口径与单位。
- **取值建议 / 示例**：`subtitle="气泡大小=订单数，单位：元"`。

### `drill` — 点击区域后聚焦该区域

- **类型 / 默认值**：`str | list[str]`；`None`。
- **作用**：点击气泡后按该区域过滤数据并重绘，效果是「只看这一个区域」；地图没有市级边界，不存在第二层下钻。字符串会被复制成两层（`["城市", "城市"]`），列表第一层强制为 `region`；多级列表不会逐级推进。
- **取值建议 / 示例**：`drill="城市"`。`drill=["不存在"]` → `KeyError: "下钻维度列 '不存在' 不存在。..."`

### `link` — 联动组名

- **类型 / 默认值**：`str | None`；`None`。
- **作用**：同组图表共享点击过滤；点击气泡后，同组其它图按「当前维度（`region`）+ 点击值」精确过滤，源图自身不过滤。字符串精确比较，`广州` 与 `广州市` 不互相匹配。
- **取值建议 / 示例**：与柱状图联动都用 `link="city-link"`；点击后无变化时检查列名与取值写法。

### `legend` — 是否显示图例

- **类型 / 默认值**：`bool`；`True`。
- **作用**：没有 `color` 分组时不显示图例；有分组且 `legend=True` 时显示分组图例。
- **取值建议 / 示例**：副标题已说明分组时设 `legend=False`。

### `section` — 看板分区标题

- **类型 / 默认值**：`str | None`；`None`。
- **作用**：仅在 `dashboard` 中生效，把卡片归入同名分区；单图只写进 `spec.section`。
- **取值建议 / 示例**：`section="城市表现"`。

## 地图数据与区域名

### 内置地图与匹配范围

| 地图 | `map` | 匹配对象 | 说明 |
| --- | --- | --- | --- |
| 中国 | `'china'` | 34 个省级区域 + 内置城市表 | 城市用 725 条城市表定位坐标 |
| 世界 | `'world'` | 215 个国家/地区 | 中文常用国名（约 100 个）自动转英文名 |

```python
import eazy_data_viz as edv

print(edv.maps.MAPS)   # ('china', 'world', 'beijing')
print(len(edv.maps.province_centers()))  # 34
```

### 城市写法与坐标

- 城市短名、全名等价：`广州` / `广州市`、`石家庄` / `石家庄市`；`sample_df` 的 `城市` 列就是 `广州市`、`石家庄市` 这种全名。
- 内置城市表 725 条原始记录，按归一化去重后共有 **369 个可匹配名称**；匹配顺序是「省级索引优先、城市兜底」。
- **同名坑**：`吉林市` 会落到吉林省中心（真实坐标 `[126.553, 43.8436]`）、`海南藏族自治州`（属青海）会落到海南省中心；直辖市（北京/上海/天津/重庆）按省级区域处理，tooltip 里「所属省份」为空。城市级分析要避开与省级同名的名称。
- 城市不在内置表里时该点被跳过，提示只出现在浏览器控制台（`[eazy_map]` 前缀，每图一次）：

```
[eazy_map] 以下区域没有匹配到地图（已跳过）：火星市。可统一改名、用 name_map 指定映射，或检查城市名是否在内置城市表里。
```

### 省份 / 世界写法

- 省份支持短名与全名（`广东` / `广东省`、`内蒙古` / `内蒙古自治区`），别名 `内蒙`、`广西省`、`新疆省`、`西藏省`、`宁夏省` 也支持。
- 世界地图可直接写常用中文国名（`美国`、`中国`、`德国`、`巴西`…）；也支持 GeoJSON 英文名与常见英文别名（`USA`、`UK`、`South Korea`）。不在别名表里的中文全称不会自动匹配，请用 `name_map`。
- `name_map` 的键要与数据原值完全一致（区分大小写、空格），值必须是地图里存在的区域名；它只影响匹配，不改变 tooltip 中显示的原值。

### 匹配不到时会怎样

单个区域失败只跳过该气泡，其余照常绘制；全部失败时整图退化为空图，页面显示「当前条件下没有数据」。提示只进浏览器控制台，**不会**写入 `chart.warnings`。想提前自查可对照内置区域名：

```python
import eazy_data_viz as edv

df = edv.sample_df()
regions = set(edv.maps.province_centers())
print(sorted(set(df["城市"]) - {"广州市"}))  # 其余城市名，用于确认数据写法
```

### 自定义区域列名

`region` / `value` / `size` / `color` 接受任意列名，例如数据里叫 `发货城市`，直接 `edv.map_bubble(df, region="发货城市", value="销售额")`；列名不参与匹配，列里的值能匹配地图区域即可。

## 返回值

`map_bubble` 返回 `eazy_data_viz.Chart` 对象（`chart = edv.map_bubble(df, region="城市", value="销售额")`）。

**Chart 的属性**

- `chart.spec`：前端 ECharts 配置。公共键：`id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`、`roles`、`agg`、`fmt`、`sort`、`topN`、`legend`、`labels`、`zoom`、`drill`、`link`；地图专属：`map`、`minValue`、`maxValue`、`nameMap`、`minSize`、`maxSize`。
- `chart.data`：注入页面的数据仓库（`dict`），键 `cols` / `rows` / `dims` / `measures` / `kinds` / `orders` / `n` / `n_total`；`rows` 是原始明细行。
- `chart.data_ref`：数据引用 id（`data-<12 位 sha1>`），同内容数据复用。
- `chart.warnings`：`dict`，形如 `{"warnings": [], "n_total": 1500}`；区域未匹配不属于 warnings。
- `chart.title`：可读标题。

**Chart 的方法**

- `chart.to_html(inline=True)`：返回完整 HTML；内联中国地图单图约 2.1 MB。
- `chart.save(path, inline=True)`：写 HTML 文件并返回绝对路径。
- `chart.show(open_browser=None)`：在浏览器中打开。
- `chart.palette(name)`：切换配色并返回 `self`。

**本图 `spec` 的真实结构**

用 `edv.map_bubble(df, region="城市", value="销售额", size="订单数", color="渠道")` 生成的 `spec`（未使用的公共键已省略；`labels` 固定为 `false`）：

```json
{
  "id": "c2",
  "type": "map_bubble",
  "title": "销售额 · 城市气泡地图",
  "subtitle": null,
  "theme": "light",
  "height": 460,
  "dataRef": "d3cae6f6e0275",
  "roles": {"region": "城市", "value": "销售额", "size": "订单数", "color": "渠道", "x": "城市"},
  "agg": "sum",
  "fmt": "compact",
  "sort": null,
  "legend": true,
  "labels": false,
  "zoom": null,
  "drill": null,
  "link": null,
  "map": "china",
  "minValue": null,
  "maxValue": null,
  "nameMap": null,
  "minSize": 4.0,
  "maxSize": 28.0
}
```

**验证返回值的小技巧**

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.map_bubble(df, region="城市", value="销售额")
assert chart.spec["type"] == "map_bubble"
assert chart.spec["labels"] is False
assert chart.data["n"] == len(df)
print(chart.title, chart.warnings["n_total"])
```

## 完整示例

以下示例都基于 `edv.sample_df()`，可直接复制运行；输出写到 `examples/output/`（已 gitignore）。

### 示例 1：最简城市气泡

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.map_bubble(df, region="城市", value="销售额")
chart.save("examples/output/map_bubble_1.html")
print(chart.spec["type"], chart.title)
```

**输出**：自动标题「销售额 · 城市气泡地图」，10 个城市各一个同色气泡，半径默认按销售额在 4～28 像素间映射（未传 `size` 时用 `value` 映射大小）。

**验证**：`chart.spec["roles"]["value"] == "销售额"`；前端 `series[0].type === "scatter"`、`series[0].data.length === 10`。

### 示例 2：省份气泡 + size

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.map_bubble(df, region="省份", value="销售额", size="订单数")
chart.save("examples/output/map_bubble_2.html")
print(chart.spec["roles"])
```

**输出**：每省一个气泡，半径随订单数在 4～28 像素间变化；tooltip 同时显示销售额与订单数。

**验证**：`chart.spec["roles"]["size"] == "订单数"`；前端气泡 `value` 前四位为 `[lng, lat, 订单数, 销售额]`。

### 示例 3：size + color 分组

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.map_bubble(
    df, region="城市", value="销售额", size="订单数", color="渠道",
    height=560, title="城市销售额：按渠道分组",
)
chart.save("examples/output/map_bubble_3.html")
print(chart.spec["roles"]["color"], chart.spec["minSize"], chart.spec["maxSize"])
```

**输出**：按 3 个渠道生成 3 个系列（3 种颜色 + 图例），共 30 个气泡（10 城市 × 3 渠道）；同一城市的三个气泡围绕城市中心散开。

**验证**：`chart.spec["roles"]["color"] == "渠道"`；前端 `series.length === 3`、`legend.show === true`，`series[0].data.length === 10`。

### 示例 4：世界地图气泡

```python
import eazy_data_viz as edv
import pandas as pd

world = pd.DataFrame({
    "国家": ["美国", "中国", "德国", "巴西", "印度", "澳大利亚"],
    "销售额": [180, 260, 120, 90, 140, 70],
})
chart = edv.map_bubble(world, region="国家", value="销售额", map="world")
chart.save("examples/output/map_bubble_4.html")
print(chart.spec["map"], chart.title)
```

**输出**：6 个国家按销售额画出气泡，中文国名经别名表转英文名后定位；世界图默认视角比中国图更远。

**验证**：`chart.spec["map"] == "world"`；前端 `series[0].data.length === 6`，`geo.zoom === 1.12`。

### 示例 5：name_map 修正区域名

```python
import eazy_data_viz as edv
import pandas as pd

world = pd.DataFrame({"国家": ["USA", "UK", "Germany", "巴西"], "订单数": [120, 80, 60, 40]})
chart = edv.map_bubble(
    world, region="国家", value="订单数", map="world",
    name_map={"USA": "United States", "UK": "United Kingdom"},
)
chart.save("examples/output/map_bubble_5.html")
print(chart.spec["nameMap"])
```

**输出**：四个国家全部出泡；去掉 `name_map` 后 `USA` / `UK` 会被跳过。

**验证**：`chart.spec["nameMap"] == {"USA": "United States", "UK": "United Kingdom"}`。

### 示例 6：drill 点击城市聚焦

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.map_bubble(df, region="城市", value="销售额", drill="城市")
chart.save("examples/output/map_bubble_6.html")
print(chart.spec["drill"], chart.spec["roles"]["_extra"])
```

**输出**：点击「广州市」后只保留该城市数据；地图没有市级边界，drill 的效果是单点聚焦而非逐级下钻。

**验证**：`chart.spec["drill"] == ["城市", "城市"]`；模拟点击后 `state.drill == [{"dim": "城市", "value": "广州市"}]`。

### 示例 7：link 联动气泡与柱状图

```python
import eazy_data_viz as edv

df = edv.sample_df()
bubble = edv.map_bubble(df, region="城市", value="销售额", link="city-link")
bar = edv.bar(df, x="城市", y="销售额", link="city-link")
dash = edv.dashboard([bubble, bar], cols=2, title="城市联动")
dash.save("examples/output/map_bubble_7.html")
print(bubble.spec["link"], bar.spec["link"])
```

**输出**：点击气泡「广州市」，右侧柱状图自动过滤为广州市；气泡图自身保持全貌。

**验证**：两张图的 `spec["link"]` 都是 `"city-link"`；点击后柱状图 `state.filters == {"城市": "广州市"}`。

## 常见错误

**必填参数 / 列不存在**

```
TypeError: map_bubble() missing 1 required positional argument: 'region'
KeyError: "region（区域列）列 '不存在' 不存在。当前可用的列有：日期, 月份, 大区, 省份, 城市, 产品, 渠道, 销售额, 订单数, 利润, 客户数"
KeyError: "value（数值列）列 '不存在' 不存在。当前可用的列有：..."
```

**列之间冲突、文本列未清洗**

```
ValueError: value 不能与 region 是同一列：region 是区域名，value 是数值。
ValueError: size 不能与 region 是同一列：region 是区域名，size 是数值。
ValueError: color 不能与 region 是同一列：region 是区域名，color 是分组列。
TypeError: value（数值列） '销售额' 需要是数值类型（当前是文本，例如 ['abc', 'abc', 'abc']）。请先用 pd.to_numeric() 清洗，或换一列。
```

**地图 / 气泡尺寸 / 配色 / 主题等取值非法**

```
ValueError: map 只支持 "china"（中国）/ "world"（世界），收到 'usa'。
ValueError: min_size / max_size 需要大于 0，收到 min_size=0、max_size=28。
ValueError: min_size 必须小于 max_size，收到 min_size=30、max_size=10。
TypeError: name_map 需要是 dict，例如 name_map={'USA': 'United States'}，收到 'list'。
ValueError: theme 只支持 "light" / "dark"，收到 'blue'
ValueError: height 至少 120（像素），收到 100
ValueError: 未知配色 'foo'，可选：google、antd、tableau、carbon、echarts、morandi、tailwind
```

**传了不存在的参数**

```
TypeError: map_bubble() got an unexpected keyword argument 'labels'
TypeError: map_bubble() got an unexpected keyword argument 'min_value'
```

气泡图没有 `labels`、`min_value` / `max_value` 参数；想固定视觉范围请用 `min_size` / `max_size`。

**只传 `size` 不传 `value`**

不会报错，但度量变成记录数、`size` 列实际不生效（半径改由记录数映射）。请同时传 `value`。

**区域名匹配不到**

没有 Python 异常：该气泡被跳过，提示在浏览器控制台（`[eazy_map]` 前缀）；全部失败时页面显示「当前条件下没有数据」。常见原因：城市名不在 369 个可匹配名称里、世界图写了不在别名表里的中文全称、`name_map` 目标不是地图区域。

## 相关图表

- [geo_map](./geo_map.md)：区域填色，适合单指标全省/全国对比。
- [map_flow](./map_flow.md)：`source → target` 的飞线流向图。
- [bar](./bar.md)：城市精确排名，常与气泡图 `link` 联动。
- [地图教程](../guides/map.md)：地图选型、数据准备与驾驶舱实战。
