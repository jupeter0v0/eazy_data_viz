# `geo_map` — 区域填色地图

> 用颜色深浅表达一个指标在各省 / 各国上的高低，一眼看出「哪里高、哪里低」。
> 适合：区域对比（各省销售额）、地理分布（各国订单量）、配合下钻/联动做区域分析。
> 不适合：精确数值与排名（用 bar）、多点位置与双指标（用 map_bubble）、流向关系（用 map_flow）。

## 函数签名

```python
eazy_data_viz.geo_map(
    data, region, value=None, *,
    map="china", agg="sum", fmt="compact", labels=True,
    min_value=None, max_value=None, name_map=None,
    zoom=None, palette=None, height=460, theme="light",
    title=None, subtitle=None, drill=None, link=None,
    legend=True, section=None,
) -> Chart
```

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源 DataFrame |
| `region` | `str` | `—` | 是 | 区域列：省份 / 城市 / 国家名 |
| `value` | `str` | `None` | 否 | 填色数值列；省略表示统计记录数 |
| `map` | `str` | `'china'` | 否 | 内置地图：`china` / `world` / `beijing` |
| `agg` | `str` | `'sum'` | 否 | 同一区域多行时的聚合方式 |
| `fmt` | `str` | `'compact'` | 否 | 色阶刻度与 tooltip 数值格式 |
| `labels` | `bool` | `True` | 否 | 是否在区域上显示名称 |
| `min_value` | `float \| None` | `None` | 否 | 色阶下限（固定配色范围） |
| `max_value` | `float \| None` | `None` | 否 | 色阶上限（固定配色范围） |
| `name_map` | `dict \| None` | `None` | 否 | 数据区域值 → 地图区域名的映射 |
| `zoom` | `bool \| str \| None` | `None` | 否 | 是否允许鼠标缩放、平移 |
| `palette` | `str \| None` | `None` | 否 | 配色方案名 |
| `height` | `int` | `460` | 否 | 画布高度（≥120） |
| `theme` | `str` | `'light'` | 否 | `light` / `dark` |
| `title` | `str \| None` | `None` | 否 | 主标题；省略自动生成 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `drill` | `str \| list[str]` | `None` | 否 | 点击区域后聚焦该区域 |
| `link` | `str \| None` | `None` | 否 | 联动组名 |
| `legend` | `bool` | `True` | 否 | 是否显示右侧色阶图例 |
| `section` | `str \| None` | `None` | 否 | 看板分区标题 |

## 参数详解

### `data` — 数据源（必填）

- **作用**：图表取数的唯一入口。`Series` 转单列、`dict` / `list` 转 DataFrame（list 每个元素一行）；超过 20 万行会均匀抽样，提示写进 `chart.warnings`。
- **取值建议 / 示例**：优先传清洗好的 `DataFrame`，例如 `data=df`；不要在绘图调用里做复杂变换。`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`

### `region` — 区域列名（必填）

- **作用**：指定「颜色属于哪个区域」的列。省份支持短名（`广东`）与全名（`广东省`）；城市支持 `广州` / `广州市`，`geo_map` 会把城市值汇总到所属省份再填色。同省多种写法会合并，显示名取第一次出现的写法。
- **取值建议 / 示例**：省级填色用 `region="省份"`；想按城市看也直接传 `城市`，但地图没有市级边界，最终仍是按省汇总。列名写错 → `KeyError: "region（区域列）列 '不存在' 不存在。当前可用的列有：..."`；传空串 → `ValueError: region（区域列） 需要是非空字符串，收到 '  '。`

### `value` — 填色数值列

- **作用**：决定区域颜色的指标列；省略时按区域统计行数（`agg` 内部改成 `count`，标题度量名写成「记录数」）。先按 `region` 用 `agg` 聚合，再由连续色阶上色。文本型数字（`"1234"`、`"1,234"`）会自动转数值；纯文本列不报错，只会得到一张空图。
- **取值建议 / 示例**：销售额用 `sum`、比率用 `mean`，例如 `value="销售额"`；只看覆盖情况可省略 `value`。纯文本列先用 `pd.to_numeric(df["列"], errors="coerce")` 清洗。

### `map` — 使用哪张内置地图

- **作用**：内置 `china`（34 个省级区域 + 南海诸岛占位）、`world`（215 个国家/地区）与 `beijing`（北京 16 个市辖区，区级）三张。GeoJSON 随页面注入，`china` 约 0.57 MB、`world` 约 0.96 MB、`beijing` 约 0.10 MB；选 `world` 时 `region` 必须是国家名，用省份名会全部匹配不到；选 `beijing` 时 `region` 传区名即可（`"朝阳"` / `"朝阳区"` 都能匹配）。
- **取值建议 / 示例**：中国省级用默认值；国家列用 `map="world"`；北京区级用 `map="beijing"`（或直接用便捷函数 `edv.beijing_map(df, region="区", value="销售额")`）。`map="usa"` → `ValueError: map 只支持 "china"（中国）/ "world"（世界）/ "beijing"（北京），收到 'usa'。`

### `agg` — 聚合方式

- **作用**：同一区域有多行时先聚合再上色，可选 `sum`、`mean`、`count`、`max`、`min`、`median`；`value=None` 时强制 `count`。聚合在前端完成，`chart.data` 仍保留原始明细行。
- **取值建议 / 示例**：销售额用 `sum`、客单价用 `mean`，例如 `agg="mean"`；统计记录数就省略 `value`。`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median`

### `fmt` — 数值格式

- **作用**：控制色阶刻度与 tooltip 格式，可选 `compact`（1.9万）、`thousands`（19,519）、`raw`（195190.32）、`percent`、`currency`。
- **取值建议 / 示例**：看板默认 `compact`；核对数字用 `fmt="thousands"`。`fmt="wan"` → `ValueError: fmt='wan' 不支持，可选：compact, thousands, raw, percent, currency`

### `labels` — 是否显示区域名称

- **作用**：在区域上叠加名称文本。中国地图区域少、会全部显示；世界地图区域多时只显示有数据的区域，避免文字压盖。标签文本是数据里的原始写法（`广东` 而非 `广东省`）。
- **取值建议 / 示例**：中国地图保持默认；世界地图区域多时设 `labels=False`，靠 tooltip 看国家名。非布尔值按真值处理、不报错但不推荐（`labels="no"` 仍会显示）。

### `min_value` — 色阶下限

- **作用**：只影响 `visualMap` 的颜色映射范围，不裁剪数据；可以只固定一端。多张地图并排时固定同一范围，颜色才可横向比较。
- **取值建议 / 示例**：需要对比时同时固定两端，例如 `min_value=0, max_value=250000`。写反 → `ValueError: min_value 必须小于 max_value，收到 min_value=100、max_value=10。（如果只想固定一端，另一端请传 None）`

### `max_value` — 色阶上限

- **作用**：与 `min_value` 对称，只影响配色范围，不影响 tooltip 的真实数值；数据里有极端大值时用它压住色阶，避免其它区域被「压平」。
- **取值建议 / 示例**：`max_value=250000`；两端顺序写反时同上报 `min_value 必须小于 max_value`。

### `name_map` — 区域名映射

- **作用**：键是数据里的原始值（精确匹配、不归一化），值是地图区域名：中国可用省名短名/全名（也接受内置城市名，会汇总到所属省份），世界必须是 GeoJSON 英文名或常用国家名。命中后优先按映射目标匹配；目标不存在时浏览器控制台提示「name_map 把「X」映射到了「Y」，但地图里没有这个区域，已忽略该映射。」并继续按原值兜底。映射目标只能是省/国家，不能把任意值映射到城市。
- **取值建议 / 示例**：世界数据用 `name_map={"USA": "United States", "UK": "United Kingdom"}`；国内历史写法用它兜底，而不是改原始数据。传 `list` → `TypeError: name_map 需要是 dict，例如 name_map={'USA': 'United States'}，收到 'list'。`

### `zoom` — 是否允许鼠标缩放与平移

- **作用**：这是「开关」而不是「级别」：只有 `False` 会关闭缩放/平移，`None`、`True`、`'auto'`、`'scale'`、`'move'` 都表示允许且行为一致。默认视角固定（中国 `zoom=1.32`、中心 `[104, 35.5]`；世界 `zoom=1.12`）；API 没有暴露视角参数，需要自定义可改 `chart.spec["mapZoom"]` / `chart.spec["mapCenter"]`。
- **取值建议 / 示例**：看板里不做交互时设 `zoom=False`，避免移动端误触。`zoom=2` → `ValueError: zoom 只支持 None / True / False / 'auto'（地图里表示是否允许鼠标缩放和平移），收到 2。`

### `palette` — 配色方案

- **作用**：可选 `google`、`antd`、`tableau`、`carbon`、`echarts`、`morandi`、`tailwind`；地图取该配色主色作为「高热色」，再与主题背景混出 5 级渐变。
- **取值建议 / 示例**：同一看板统一配色，例如 `palette="tableau"`；也可链式 `chart.palette("tableau")`。未知配色 → `ValueError: 未知配色 'foo'，可选：google、antd、tableau、carbon、echarts、morandi、tailwind`

### `height` — 画布高度

- **作用**：地图画布高度；放进 `dashboard` 后卡片还会加上标题与工具栏高度。
- **取值建议 / 示例**：单图 460～520、驾驶舱 420～480，例如 `height=520`。`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `theme` — 主题

- **作用**：只支持 `light` / `dark`，影响背景、文字、区域描边与色阶过渡色。
- **取值建议 / 示例**：深色看板用 `theme="dark"`，搭配 `palette="morandi"` 或 `"carbon"`。`theme="blue"` → `ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `title` — 主标题

- **作用**：显示在画布顶部的主标题；`None` / 空串都会触发自动标题。
- **取值建议 / 示例**：驾驶舱里写业务标题，例如 `title="各省销售额分布"`。

### `subtitle` — 副标题

- **作用**：主标题下方的小字，常用来写数据口径与单位。
- **取值建议 / 示例**：`subtitle="单位：元，口径：含税"`。

### `drill` — 点击区域后聚焦该区域

- **作用**：地图的区域层永远按 `region` 聚合，所以效果是「点击某区域 → 过滤出该区域的行 → 重绘只剩该区域的地图」，不会出现市级边界。传单个字符串会被复制成两层（`["省份", "省份"]`）；传列表时第一层强制为 `region`（不一致会插到最前）。只有点击值与当前层维度一致才触发；多级列表不会逐级钻取（第二次点击不推进）。
- **取值建议 / 示例**：`drill="省份"`；真正多级分析请用 `bar` / `treemap` 等图。`drill=["不存在"]` → `KeyError: "下钻维度列 '不存在' 不存在。..."`；`drill=["城市"]` 而 `region="省份"` 时，点击后按城市过滤通常得到空图。

### `link` — 联动组名

- **作用**：同一 `link` 组共享一次点击过滤：点击地图区域后，同组其它图按「当前维度 + 点击值」精确过滤并重绘。地图当前维度是 `region` 列（点击 `广东` 会以 `{"省份": "广东"}` 过滤同组图）；源地图自身不过滤，保留全貌。联动是字符串精确比较，`广东` 与 `广东省` 不会互相匹配。
- **取值建议 / 示例**：与柱状图联动时让两者使用同一种区域列，例如都 `link="region-link"`；点击后无变化时先检查组名、列名与取值写法。

### `legend` — 是否显示色阶图例

- **作用**：`False` 时隐藏右侧连续色阶条（`visualMap.show=false`），但区域颜色仍按数据映射。
- **取值建议 / 示例**：小卡片或副标题已说明口径时设 `legend=False`。

### `section` — 看板分区标题

- **作用**：仅在 `dashboard` 中生效：把卡片归入同名分区，分区标题显示在卡片组上方；单图只写进 `spec.section`。
- **取值建议 / 示例**：驾驶舱按业务域分区，例如 `section="区域表现"`。

## 地图数据与区域名

### 内置地图

| 地图 | `map` | 区域数 | GeoJSON 体积 | 适用数据 |
| --- | --- | --- | --- | --- |
| 中国 | `'china'` | 34 个省级区域（另有 1 个南海诸岛占位） | 约 0.57 MB | 省份、城市列 |
| 世界 | `'world'` | 215 个国家/地区 | 约 0.96 MB | 国家列 |
| 北京 | `'beijing'` | 16 个市辖区（区级） | 约 0.10 MB | 北京各区列 |

```python
import eazy_data_viz as edv

print(edv.maps.MAPS)                          # ('china', 'world', 'beijing')
print(len(edv.maps.province_centers()))       # 34
print(len(edv.maps.region_centers("world")))  # 215
print(len(edv.maps.region_centers("beijing")))  # 16
```

### 北京区级地图

```python
bj = pd.DataFrame({
    "区": ["东城区", "西城区", "朝阳区", "海淀区", "大兴区"],
    "销售额": [52, 68, 128, 142, 63],
})
# 两种写法等价：
chart = edv.beijing_map(bj, region="区", value="销售额")
chart = edv.geo_map(bj, region="区", value="销售额", map="beijing")
chart.save("beijing_map.html")
```

### 省级区域写法

- 短名、全名都可以：`广东` / `广东省`、`内蒙古` / `内蒙古自治区`、`广西` / `广西壮族自治区`、`香港` / `香港特别行政区`。
- 归一化会去掉空格、`·`、`-`、`.` 等符号，并循环剥离 `省`、`市`、`自治区`、`特别行政区`、`自治州`、`地区`、`盟` 等后缀，两种写法等价。
- 常见别名也支持：`内蒙` → `内蒙古`、`广西省` → `广西`、`新疆省` → `新疆`、`西藏省` → `西藏`、`宁夏省` → `宁夏`。
- 建议数据里统一用短名（`sample_df` 的 `省份` 列就是 `广东`、`上海` 这种短名）。

### 城市列写法

- `geo_map` 也接受城市列（`region="城市"`）：先匹配内置城市表、再汇总到所属省份填色；`广州` 与 `广州市` 等价。
- 内置城市表共 725 条原始记录，按归一化去重后是 **369 个可匹配名称**；覆盖地级市。直辖市（北京/上海/天津/重庆）在省级索引里先命中，按省级区域处理。
- 城市没有独立 GeoJSON 边界，所以填色永远是「按省」的效果；看城市点位请用 `map_bubble` / `map_flow`。
- **同名坑**：匹配顺序是「省级索引优先、城市兜底」，所以 `吉林市` 会落到吉林省中心、`海南藏族自治州`（属青海）会落到海南省中心。城市级分析优先用 `map_bubble` / `map_flow`，并避免与省同名的城市名。
- 想确认城市是否在内置表里，可在浏览器控制台执行 `EazyViz.mapUtil.resolveCity("广州市")`；Python 侧没有城市表接口。

### 世界地图写法

- 常用中文国名可直接用（约 100 个）：`美国`、`中国`、`俄罗斯`、`英国`、`法国`、`德国`、`日本`、`韩国`、`印度`、`巴西`、`澳大利亚` 等。
- 也支持 GeoJSON 英文原名：`United States`、`United Kingdom`、`Korea`、`W. Sahara`、`Czech Rep.` 等。
- 常见英文别名会归一化：`USA` → `United States`、`UK` → `United Kingdom`、`South Korea` → `Korea`。
- 不在别名表里的中文全称（如「美利坚合众国」）不会自动匹配，请改用常用简称或 `name_map`。

### `name_map` 用法

`name_map` 是「数据原值 → 地图区域名」的字典，适合历史遗留命名、英文缩写、业务自定义名称：

```python
import eazy_data_viz as edv
import pandas as pd

world = pd.DataFrame({"国家": ["USA", "UK", "Germany", "巴西"], "订单数": [120, 80, 60, 40]})
chart = edv.geo_map(
    world, region="国家", value="订单数", map="world",
    name_map={"USA": "United States", "UK": "United Kingdom"},
)
```

- 键必须与数据原值完全一致（区分大小写、空格），不经过归一化；值是地图里的区域名（省份/国家，中国地图也接受内置城市名）。
- 映射目标不存在时会提示并忽略该映射，继续按原值走普通匹配。
- `name_map` 只影响「匹配区域」，不修改数据、也不改变 tooltip 里显示的名字。

### 匹配不到时会怎样

- 单个区域失败：该区域被跳过（填色图里保持无数据的灰色），不报错。
- 全部区域失败：整张图退化为空图，页面显示「当前条件下没有数据」。
- 提示只输出到浏览器控制台（`[eazy_map]` 前缀，每个图表只提醒一次），不会写进 `chart.warnings`：

```
[eazy_map] 以下区域没有匹配到地图（已跳过）：华东、华北、华南、西部。可统一改名，或用 name_map 指定映射；城市名需在内置城市表（window.EAZY_CITIES）里。
```

- 想在 Python 侧提前自查，可拿数据值与内置区域名集合比对：

```python
import eazy_data_viz as edv

df = edv.sample_df()
regions = set(edv.maps.province_centers())   # {'北京', '广东', ...}
print(sorted(set(df["大区"]) - regions))      # ['华东', '华北', '华南', '西部']
```

### 自定义区域列名

`region` / `value` 接受任意列名，不需要改成固定名字。例如数据里叫 `发货省`，直接 `edv.geo_map(df, region="发货省", value="销售额")` 即可；列名不参与匹配，列里的值能匹配地图区域就行。

## 返回值

`geo_map` 返回 `eazy_data_viz.Chart` 对象（`chart = edv.geo_map(df, region="省份", value="销售额")`）。

**Chart 的属性**

- `chart.spec`：交给前端 ECharts 的完整配置（JSON 可序列化）。公共键有 `id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`、`roles`、`agg`、`fmt`、`sort`、`topN`、`legend`、`labels`、`zoom`、`drill`、`link`；地图专属键有 `map`、`minValue`、`maxValue`、`nameMap`。
- `chart.data`：注入页面的数据仓库（`dict`），键为 `cols` / `rows` / `dims` / `measures` / `kinds` / `orders` / `n` / `n_total`；`rows` 是原始明细行（聚合在前端完成）。
- `chart.data_ref`：数据引用 id（`data-<12 位 sha1>`），同内容数据复用同一引用。
- `chart.warnings`：`dict`，形如 `{"warnings": [], "n_total": 1500}`；只有采样、丢列等提示。**区域未匹配不属于 warnings**，只进浏览器控制台。
- `chart.title`：可读标题（读 `spec["title"]`）。

**Chart 的方法**

- `chart.to_html(inline=True)`：返回完整 HTML 字符串；`inline=True` 时把 ECharts、运行时、地图 GeoJSON 全部内联（中国地图单图约 2.1 MB，可离线打开）。
- `chart.save(path, inline=True)`：写出 HTML 文件，自动创建父目录，返回绝对路径。
- `chart.show(open_browser=None)`：在浏览器中打开。
- `chart.palette(name)`：切换配色并返回 `self`，支持链式调用。

**本图 `spec` 的真实结构**

用 `edv.geo_map(df, region="省份", value="销售额")` 实际生成的 `spec`（GeoJSON 与数据在页面注入的 payload 里，未使用的 `xtitle` / `ytitle` / `xlim` / `ylim` / `topN` 等公共键已省略）：

```json
{
  "id": "c1",
  "type": "geo_map",
  "title": "销售额 · 中国地图",
  "subtitle": null,
  "theme": "light",
  "height": 460,
  "dataRef": "d3cae6f6e0275",
  "roles": {"region": "省份", "value": "销售额", "x": "省份"},
  "agg": "sum",
  "fmt": "compact",
  "sort": null,
  "legend": true,
  "labels": true,
  "zoom": null,
  "drill": null,
  "link": null,
  "map": "china",
  "minValue": null,
  "maxValue": null,
  "nameMap": null
}
```

**验证返回值的小技巧**

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.geo_map(df, region="省份", value="销售额")
assert chart.spec["type"] == "geo_map"
assert chart.spec["map"] == "china"
assert chart.data["n"] == len(df)
print(chart.title, chart.data["n"], chart.warnings)
```

## 完整示例

以下示例都基于 `edv.sample_df()`，可直接复制运行（在仓库根目录执行）；输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简中国省级填色

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.geo_map(df, region="省份", value="销售额")
chart.save("examples/output/geo_map_1.html")
print(chart.spec["type"], chart.spec["map"], chart.title)
```

**输出**：自动标题「销售额 · 中国地图」，10 个省份按销售额深浅着色，右侧连续色阶约「11.2万 ~ 19.5万」。

**验证**：`chart.spec["roles"]["region"] == "省份"`；浏览器里 `series[0].type === "map"`、`series[0].data.length === 10`，`visualMap[0].min/max` 等于数据极值。

### 示例 2：城市列自动汇总到省

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.geo_map(df, region="城市", value="销售额")
chart.save("examples/output/geo_map_2.html")
print(chart.spec["roles"]["region"], chart.title)
```

**输出**：城市值按所属省份汇总后填色，tooltip 里标注「覆盖城市 N 个」；`sample_df` 每省只有一个城市，效果与示例 1 接近。

**验证**：`chart.spec["roles"]["region"] == "城市"`；前端 `series[0].data` 仍是 10 条（按省合并），每条带 `cities` 计数。

### 示例 3：世界地图（中文国名）

```python
import eazy_data_viz as edv
import pandas as pd

world = pd.DataFrame({
    "国家": ["美国", "中国", "德国", "巴西", "印度", "澳大利亚"],
    "销售额": [180, 260, 120, 90, 140, 70],
})
chart = edv.geo_map(world, region="国家", value="销售额", map="world")
chart.save("examples/output/geo_map_3.html")
print(chart.spec["map"], chart.title)
```

**输出**：自动标题「销售额 · 世界地图」，6 个国家着色；中文国名经内置别名表转成 GeoJSON 英文名后再匹配。

**验证**：`chart.spec["map"] == "world"`；前端 `series[0].data` 的 `name` 保留中文原值，`geo.nameMap` 把英文区域名改写成中文显示。

### 示例 4：固定色阶 + 深色主题 + 隐藏图例

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.geo_map(
    df, region="省份", value="销售额",
    min_value=0, max_value=250000, labels=False, legend=False,
    theme="dark", palette="tableau", height=560,
    title="各省销售额分布", subtitle="单位：元，口径：含税",
)
chart.save("examples/output/geo_map_4.html")
print(chart.spec["minValue"], chart.spec["maxValue"], chart.spec["height"])
```

**输出**：深色背景 + tableau 主色渐变，色阶固定 0 ~ 250000，右侧图例隐藏、区域名称不显示；多张地图并排时可横向比较颜色深浅。

**验证**：`chart.spec["minValue"] == 0`、`chart.spec["maxValue"] == 250000`、`chart.spec["labels"] is False`、`chart.spec["legend"] is False`。

### 示例 5：用 name_map 修正区域名

```python
import eazy_data_viz as edv
import pandas as pd

world = pd.DataFrame({"国家": ["USA", "UK", "Germany", "巴西"], "订单数": [120, 80, 60, 40]})
chart = edv.geo_map(
    world, region="国家", value="订单数", map="world",
    name_map={"USA": "United States", "UK": "United Kingdom"},
)
chart.save("examples/output/geo_map_5.html")
print(chart.spec["nameMap"])
```

**输出**：`USA` / `UK` 通过 `name_map` 映射到 GeoJSON 的 `United States` / `United Kingdom`，四个国家全部着色；去掉 `name_map` 后这两个值会被跳过。

**验证**：`chart.spec["nameMap"] == {"USA": "United States", "UK": "United Kingdom"}`；前端 `series[0].data.length === 4`。

### 示例 6：drill 点击区域聚焦

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.geo_map(df, region="省份", value="销售额", drill="省份")
chart.save("examples/output/geo_map_6.html")
print(chart.spec["drill"], chart.spec["roles"]["_extra"])
```

**输出**：鼠标移入区域出现 `cursor: pointer`；点击「广东」后地图只保留广东数据，顶部出现下钻面包屑 / 返回按钮。地图的 drill 只有单区域聚焦效果，不会出现市级边界。

**验证**：`chart.spec["drill"] == ["省份", "省份"]`；模拟点击后 `state.drill == [{"dim": "省份", "value": "广东"}]`，过滤后 150 行，重绘只剩 1 条区域数据。

### 示例 7：link 联动地图与柱状图

```python
import eazy_data_viz as edv

df = edv.sample_df()
geo = edv.geo_map(df, region="省份", value="销售额", link="region-link")
bar = edv.bar(df, x="省份", y="销售额", link="region-link")
dash = edv.dashboard([geo, bar], cols=2, title="地图联动")
dash.save("examples/output/geo_map_7.html")
print(geo.spec["link"], bar.spec["link"])
```

**输出**：点击地图上的「广东」，右侧柱状图自动过滤为广东并重绘；地图本身保持全国全貌（源图不过滤）。再次点击同一区域可取消联动。

**验证**：两张图的 `spec["link"]` 都是 `"region-link"`；点击后柱状图 `state.filters == {"省份": "广东"}`、过滤后 150 行。

### 示例 8：排查未匹配区域

```python
import eazy_data_viz as edv

df = edv.sample_df()
regions = set(edv.maps.province_centers())
print("未匹配区域：", sorted(set(df["大区"]) - regions))

chart = edv.geo_map(df, region="大区", value="销售额")
chart.save("examples/output/geo_map_8.html")
print(chart.spec["type"], chart.warnings)
```

**输出**：`未匹配区域： ['华东', '华北', '华南', '西部']`；因为 `大区` 不是地图区域，页面显示空图「当前条件下没有数据」。提示只出现在浏览器控制台，`chart.warnings` 里没有相关记录——这是最容易踩的坑。

**验证**：`chart.warnings["warnings"] == []`；浏览器控制台有 `[eazy_map] 以下区域没有匹配到地图（已跳过）：...`。

## 常见错误

**`map` 写错、列不存在、区域列为空**

```
ValueError: map 只支持 "china"（中国）/ "world"（世界），收到 'usa'。
KeyError: "region（区域列）列 '不存在' 不存在。当前可用的列有：日期, 月份, 大区, 省份, 城市, 产品, 渠道, 销售额, 订单数, 利润, 客户数"
KeyError: "value（数值列）列 '不存在' 不存在。当前可用的列有：..."
ValueError: region（区域列） 需要是非空字符串，收到 '  '。
```

**色阶 / name_map / zoom / theme / height / fmt / agg / palette 取值非法**

```
ValueError: min_value 必须小于 max_value，收到 min_value=100、max_value=10。（如果只想固定一端，另一端请传 None）
TypeError: name_map 需要是 dict，例如 name_map={'USA': 'United States'}，收到 'list'。
ValueError: zoom 只支持 None / True / False / 'auto'（地图里表示是否允许鼠标缩放和平移），收到 2。
ValueError: theme 只支持 "light" / "dark"，收到 'blue'
ValueError: height 至少 120（像素），收到 100
ValueError: fmt='wan' 不支持，可选：compact, thousands, raw, percent, currency
ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median
ValueError: 未知配色 'foo'，可选：google、antd、tableau、carbon、echarts、morandi、tailwind
```

**`drill` 列不存在**

```
KeyError: "下钻维度列 '不存在' 不存在。当前可用的列有：... \n提示：drill 里的每一列都必须是 df 的列名。"
```

**纯文本 `value` 不报错，但图是空的**

`geo_map` 对数值列只做「能转就转」的清洗，转不了不会抛 `TypeError`，而是让前端聚合结果为空，最终显示「当前条件下没有数据」。排查：`df["销售额"].dtype` 是否为数值、`pd.to_numeric(df["销售额"], errors="coerce").notna().mean()` 是否接近 1。

**区域名匹配不到**

没有 Python 异常：地图上该区域保持灰色、气泡/飞线被跳过；提示在浏览器控制台（`[eazy_map]` 前缀）。常见原因：用了 `大区` 这类非地图名称、世界地图里写了中文全称、城市名不在 725 条内置表里。

## 相关图表

- [map_bubble](./map_bubble.md)：在区域中心画气泡，可再加 `size` / `color` 两个指标。
- [map_flow](./map_flow.md)：把 `source → target` 的流量画成动态飞线。
- [bar](./bar.md)：区域数值精确比较与排序，常与地图做 `link` 联动。
- [地图教程](../guides/map.md)：地图选型、数据准备与驾驶舱实战。
