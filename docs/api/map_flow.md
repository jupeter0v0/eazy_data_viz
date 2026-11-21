# `map_flow` — 区域飞线图

> 用动态飞线表达「从哪里流向哪里」，线宽表示流量大小，适合迁徙、物流、调拨、贸易等方向性数据。
> 适合：城市间流量（发货地 → 收货地）、区域调拨、全球贸易流向、枢纽辐射分析。
> 不适合：单个区域的数值对比（用 geo_map）、只要点位与规模（用 map_bubble）、无方向关系的分类数据（用 bar）。

## 函数签名

```python
eazy_data_viz.map_flow(
    data, source, target, value=None, *,
    map="china", agg="sum", fmt="compact", name_map=None,
    zoom=None, palette=None, height=460, theme="light",
    title=None, subtitle=None, link=None, legend=True, section=None,
) -> Chart
```

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源 DataFrame |
| `source` | `str` | `—` | 是 | 起点区域列 |
| `target` | `str` | `—` | 是 | 终点区域列 |
| `value` | `str` | `None` | 否 | 流量数值列；省略表示统计记录数 |
| `map` | `str` | `'china'` | 否 | 内置地图：`china` / `world` |
| `agg` | `str` | `'sum'` | 否 | 同一对起终点多行时的聚合方式 |
| `fmt` | `str` | `'compact'` | 否 | tooltip 数值格式 |
| `name_map` | `dict \| None` | `None` | 否 | 数据区域值 → 地图区域名的映射（起点、终点都生效） |
| `zoom` | `bool \| str \| None` | `None` | 否 | 是否允许鼠标缩放、平移 |
| `palette` | `str \| None` | `None` | 否 | 配色方案名 |
| `height` | `int` | `460` | 否 | 画布高度（≥120） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `str` | `'light'` | 否 | `light` / `dark` |
| `title` | `str \| None` | `None` | 否 | 主标题；省略自动生成 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题 |
| `link` | `str \| None` | `None` | 否 | 联动组名（点击飞线按起点过滤同组图） |
| `legend` | `bool` | `True` | 否 | 是否显示流量色阶图例 |
| `section` | `str \| None` | `None` | 否 | 看板分区标题 |

## 参数详解

### `data` — 数据源（必填）

- **作用**：图表取数的唯一入口；`Series` 转单列、`dict` / `list` 转 DataFrame。超过 20 万行会均匀抽样并写进 `chart.warnings`。`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`
- **取值建议 / 示例**：每行代表一条流量记录，例如 `{"起点": "上海", "终点": "广东", "销售额": 1200}`；传 `DataFrame` 最直接。

### `source` — 起点区域列（必填）

- **作用**：飞线起点。支持省份短名/全名、城市短名/全名、世界国家名；城市用内置城市表定位坐标。与 `target` 不能是同一列。
- **取值建议 / 示例**：`source="起点"`。列名写错 → `KeyError: "source（起点列）列 '不存在' 不存在。当前可用的列有：..."`；`source` 与 `target` 相同 → `ValueError: source 和 target 不能是同一列：飞线图需要「起点 → 终点」两个不同的区域列。`

### `target` — 终点区域列（必填）

- **作用**：飞线终点，匹配规则与 `source` 完全一致；两端都匹配成功才会画出这条线，任一端失败整条线跳过。
- **取值建议 / 示例**：`target="终点"`；终点写法建议与起点统一（例如都用城市全名），便于阅读与联动。

### `value` — 流量数值列

- **类型 / 默认值**：`str`；`None`。
- **作用**：决定线的宽度与颜色深浅（线宽 `1 + 2 × |值| / 最大值`，最大 3 像素）；省略时按每对起终点统计记录数（`agg` 内部改成 `count`），每对区域默认流量为 1。文本型数字自动转数值；纯文本列不会抛错，但聚合后流量为空、线宽接近 1。
- **取值建议 / 示例**：销量、单量、人数都可以，例如 `value="销售额"`；无金额字段可省略 `value` 看连接关系。

### `map` — 使用哪张内置地图

- **类型 / 默认值**：`str`；`'china'`。
- **作用**：`china` 有 34 个省级区域，`world` 有 215 个国家/地区。飞线不受行政区层级限制，起点/终点可以是任意可匹配区域（如城市 → 省份、城市 → 国家不行，跨国必须用 `world`）。
- **取值建议 / 示例**：国内流向用默认值；跨国贸易用 `map="world"`。`map="usa"` → `ValueError: map 只支持 "china"（中国）/ "world"（世界），收到 'usa'。`

### `agg` — 聚合方式

- **类型 / 默认值**：`str`；`'sum'`。
- **作用**：同一对 `(source, target)` 有多行时先聚合，可选 `sum`、`mean`、`count`、`max`、`min`、`median`；`value=None` 时强制 `count`。
- **取值建议 / 示例**：总额用 `sum`、平均单笔用 `mean`，例如 `agg="mean"`。`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median`

### `fmt` — 数值格式

- **类型 / 默认值**：`str`；`'compact'`。
- **作用**：控制 tooltip 与色阶刻度格式，可选 `compact`、`thousands`、`raw`、`percent`、`currency`。
- **取值建议 / 示例**：`fmt="thousands"` 便于核对精确流量。`fmt="wan"` → `ValueError: fmt='wan' 不支持，可选：compact, thousands, raw, percent, currency`

### `name_map` — 区域名映射

- **类型 / 默认值**：`dict | None`；`None`。
- **作用**：键是数据原值（精确匹配），值是地图区域名；对起点和终点同时生效，常用于英文缩写、历史命名。映射目标不存在时浏览器控制台提示后忽略，继续按原值兜底。
- **取值建议 / 示例**：`name_map={"USA": "United States", "UK": "United Kingdom"}`。传 `list` → `TypeError: name_map 需要是 dict，例如 name_map={'USA': 'United States'}，收到 'list'。`

### `zoom` — 是否允许鼠标缩放与平移

- **类型 / 默认值**：`bool | str | None`；`None`。
- **作用**：开关语义：只有 `False` 关闭缩放/平移，`None`、`True`、`'auto'`、`'scale'`、`'move'` 行为一致（都允许）。默认视角固定，自定义视角可改 `chart.spec["mapZoom"]` / `chart.spec["mapCenter"]`。
- **取值建议 / 示例**：嵌入小卡片时设 `zoom=False`。`zoom=2` → `ValueError: zoom 只支持 None / True / False / 'auto'（地图里表示是否允许鼠标缩放和平移），收到 2。`

### `palette` — 配色方案

- **类型 / 默认值**：`str | None`；`None`（页面默认，初始 `google`）。
- **作用**：可选 `google`、`antd`、`tableau`、`carbon`、`echarts`、`morandi`、`tailwind`；取配色主色作为飞线与箭头颜色，并生成流量色阶。
- **取值建议 / 示例**：`palette="echarts"`；未知配色 → `ValueError: 未知配色 'foo'，可选：google、antd、tableau、carbon、echarts、morandi、tailwind`

### `height` — 画布高度

- **类型 / 默认值**：`int`；`460`（像素，最小 120）。
- **作用**：画布高度；放进 `dashboard` 后卡片还会加标题与工具栏高度。
- **取值建议 / 示例**：线多时用 520～600，例如 `height=560`。`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题

- **类型 / 默认值**：`str`；`'light'`。
- **作用**：只支持 `light` / `dark`，影响背景、文字、地图底色与飞线色阶。
- **取值建议 / 示例**：深色看板用 `theme="dark"`。`theme="blue"` → `ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `title` — 主标题

- **类型 / 默认值**：`str | None`；`None`（自动生成 `"<source 列名> → <target 列名> 流向"`，例如「起点 → 省份 流向」）。
- **作用**：显示在画布顶部的主标题。
- **取值建议 / 示例**：写成业务语言，例如 `title="全国调拨流向"`。

### `subtitle` — 副标题

- **类型 / 默认值**：`str | None`；`None`。
- **作用**：主标题下方的小字，常写口径与时间范围。
- **取值建议 / 示例**：`subtitle="2024 年，按发货单统计"`。

### `link` — 联动组名

- **类型 / 默认值**：`str | None`；`None`。
- **作用**：同组图表共享点击过滤。飞线图的当前维度是 `source` 列：点击某条线时，同组其它图按「起点列 + 起点值」精确过滤并重绘；源图自身不过滤。只能联动起点，不能联动终点。
- **取值建议 / 示例**：`link="flow-link"`，与以 `起点` 为 x 轴的柱状图联动；点击无变化时检查组名、起点列名与取值写法。

### `legend` — 是否显示图例

- **类型 / 默认值**：`bool`；`True`。
- **作用**：`False` 时隐藏流量色阶条（`visualMap.show=false`），飞线颜色仍按流量映射。
- **取值建议 / 示例**：小卡片里设 `legend=False`。

### `section` — 看板分区标题

- **类型 / 默认值**：`str | None`；`None`。
- **作用**：仅在 `dashboard` 中生效，把卡片归入同名分区；单图只写进 `spec.section`。
- **取值建议 / 示例**：`section="流转效率"`。

## 地图数据与区域名

### 内置地图与端点匹配

| 地图 | `map` | 匹配对象 | 说明 |
| --- | --- | --- | --- |
| 中国 | `'china'` | 34 个省级区域 + 内置城市表 | 同一条线两端可分别是城市与省份 |
| 世界 | `'world'` | 215 个国家/地区 | 起点、终点都必须是国家名 |

```python
import eazy_data_viz as edv

print(edv.maps.MAPS)   # ('china', 'world')
print(len(edv.maps.region_centers("china")))  # 34
```

### 端点写法

- 省份：短名/全名等价（`广东` / `广东省`），别名 `内蒙`、`广西省`、`新疆省`、`西藏省`、`宁夏省` 也支持。
- 城市：`广州` / `广州市` 等价；内置城市表 725 条原始记录、去重后 **369 个可匹配名称**，坐标取城市表中心。
- 世界：常用中文国名（约 100 个，如 `美国`、`中国`、`德国`）自动转英文名；也支持 `USA`、`UK`、`United States` 等英文写法。
- **同名坑**：`吉林市` 会落到吉林省中心、`海南藏族自治州`（属青海）会落到海南省中心——匹配顺序是「省级索引优先、城市兜底」。做城市级流向时避开与省同名的城市。
- 直辖市（北京/上海/天津/重庆）按省级区域处理，tooltip 中「起点省份 / 终点省份」为空。

### name_map 用法

`name_map` 对起点和终点都生效，适合历史命名与英文缩写：

```python
import eazy_data_viz as edv
import pandas as pd

trade = pd.DataFrame({
    "出口国": ["USA", "USA", "Germany"],
    "进口国": ["China", "Germany", "China"],
    "金额": [500, 200, 300],
})
chart = edv.map_flow(
    trade, source="出口国", target="进口国", value="金额", map="world",
    name_map={"USA": "United States"},
)
chart.save("examples/output/map_flow_namemap.html")
```

- 键必须与数据原值完全一致（区分大小写、空格），值必须是地图里存在的区域名。
- 映射目标不存在时会提示并忽略该映射，继续按原值走普通匹配；`name_map` 不改变 tooltip 显示的原值。

### 匹配不到时会怎样

- 任意一端匹配失败：整条飞线被跳过，其余线照常绘制。
- 全部失败：整张图退化为空图，页面显示「当前条件下没有数据」。
- 自环（起点与终点解析到同一区域）会被静默跳过，不报错。
- 提示只输出到浏览器控制台（`[eazy_map]` 前缀，每图一次），不会写进 `chart.warnings`：

```
[eazy_map] 以下区域没有匹配到地图（对应的飞线已跳过）：火星市 → 北京市。可统一改名，或用 name_map 指定映射。
```

### 自定义区域列名

`source` / `target` / `value` 接受任意列名，例如数据里叫 `发货省` / `收货省`，直接 `edv.map_flow(df, source="发货省", target="收货省", value="销售额")`；列名不参与匹配，列里的值能匹配地图区域即可。

## 返回值

`map_flow` 返回 `eazy_data_viz.Chart` 对象（`chart = edv.map_flow(df, source="起点", target="终点", value="销售额")`）。

**Chart 的属性**

- `chart.spec`：前端 ECharts 配置。公共键：`id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`、`roles`、`agg`、`fmt`、`sort`、`topN`、`legend`、`labels`、`zoom`、`drill`、`link`；地图专属：`map`、`minValue`、`maxValue`、`nameMap`。
- `chart.data`：注入页面的数据仓库（`dict`），键 `cols` / `rows` / `dims` / `measures` / `kinds` / `orders` / `n` / `n_total`；`rows` 是原始明细行。
- `chart.data_ref`：数据引用 id（`data-<12 位 sha1>`），同内容数据复用。
- `chart.warnings`：`dict`，形如 `{"warnings": [], "n_total": 120}`；区域未匹配不属于 warnings。
- `chart.title`：可读标题。

**Chart 的方法**

- `chart.to_html(inline=True)`：返回完整 HTML；内联中国地图单图约 2.1 MB。
- `chart.save(path, inline=True)`：写 HTML 文件并返回绝对路径。
- `chart.show(open_browser=None)`：在浏览器中打开。
- `chart.palette(name)`：切换配色并返回 `self`。

**本图 `spec` 的真实结构**

用起点/终点/销售额三列数据生成的 `spec`（未使用的公共键已省略；飞线图没有 `drill` 参数，`drill` 恒为 `null`）：

```json
{
  "id": "c3",
  "type": "map_flow",
  "title": "起点 → 省份 流向",
  "subtitle": null,
  "theme": "light",
  "height": 460,
  "dataRef": "d776b33833e99",
  "roles": {"source": "起点", "target": "省份", "value": "销售额", "x": "起点"},
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
import pandas as pd

df = pd.DataFrame({"起点": ["上海", "北京"], "终点": ["广东", "广东"], "销售额": [1200, 800]})
chart = edv.map_flow(df, source="起点", target="终点", value="销售额")
assert chart.spec["type"] == "map_flow"
assert chart.spec["roles"]["source"] == "起点"
assert chart.spec["drill"] is None
print(chart.title, chart.data["n"])
```

## 完整示例

以下示例可直接复制运行；输出写到 `examples/output/`（已 gitignore），图表数据尽量小而全。

### 示例 1：省份枢纽飞线

```python
import eazy_data_viz as edv
import pandas as pd

flow = pd.DataFrame({
    "起点": ["上海", "上海", "上海", "北京", "广东"],
    "终点": ["广东", "北京", "江苏", "广东", "江苏"],
    "销售额": [1200, 800, 600, 500, 300],
})
chart = edv.map_flow(flow, source="起点", target="终点", value="销售额")
chart.save("examples/output/map_flow_1.html")
print(chart.spec["type"], chart.title)
```

**输出**：自动标题「起点 → 终点 流向」，5 条飞线从上海/北京/广东出发，线宽按销售额变化，箭头循环动画。

**验证**：`chart.spec["roles"]["source"] == "起点"`；前端 `series[0].type === "lines"`、`series[0].data.length === 5`、`geo` 存在。

### 示例 2：城市间飞线

```python
import eazy_data_viz as edv
import pandas as pd

flow = pd.DataFrame({
    "起点": ["广州市", "广州市", "北京市", "成都市"],
    "终点": ["北京市", "上海市", "深圳市", "杭州市"],
    "订单数": [320, 280, 210, 160],
})
chart = edv.map_flow(flow, source="起点", target="终点", value="订单数", height=560)
chart.save("examples/output/map_flow_2.html")
print(chart.spec["roles"])
```

**输出**：城市表坐标定位，飞线从一个城市中心连到另一个城市中心；`广州市` / `广州` 混写也能匹配。

**验证**：`chart.spec["roles"]["value"] == "订单数"`；前端每条 `data[i].coords` 是 `[[lng1, lat1], [lng2, lat2]]` 两段城市坐标。

### 示例 3：不传 value，按记录数计算流量

```python
import eazy_data_viz as edv
import pandas as pd

flow = pd.DataFrame({
    "起点": ["上海", "上海", "北京", "北京"],
    "终点": ["广东", "广东", "广东", "上海"],
})
chart = edv.map_flow(flow, source="起点", target="终点")
chart.save("examples/output/map_flow_3.html")
print(chart.spec["agg"], chart.title)
```

**输出**：上海 → 广东 有 2 条记录，聚合后流量为 2、线更粗；其余每对为 1。自动标题使用列名而非度量名。

**验证**：`chart.spec["agg"] == "count"`；前端上海 → 广东的 `value === 2`，线宽按最大流量 2 归一化。

### 示例 4：世界贸易流向

```python
import eazy_data_viz as edv
import pandas as pd

trade = pd.DataFrame({
    "出口国": ["中国", "中国", "美国", "德国", "巴西"],
    "进口国": ["美国", "德国", "德国", "法国", "中国"],
    "金额": [520, 380, 240, 160, 90],
})
chart = edv.map_flow(trade, source="出口国", target="进口国", value="金额", map="world")
chart.save("examples/output/map_flow_4.html")
print(chart.spec["map"], chart.title)
```

**输出**：5 条跨国飞线；中文国名经别名表转英文后定位，世界图默认视角更远。

**验证**：`chart.spec["map"] == "world"`；前端 `series[0].data.length === 5`，`geo.zoom === 1.12`。

### 示例 5：name_map 修正起终点名称

```python
import eazy_data_viz as edv
import pandas as pd

trade = pd.DataFrame({
    "出口国": ["USA", "USA", "Germany"],
    "进口国": ["China", "Germany", "China"],
    "金额": [500, 200, 300],
})
chart = edv.map_flow(
    trade, source="出口国", target="进口国", value="金额", map="world",
    name_map={"USA": "United States", "Germany": "Germany", "China": "China"},
)
chart.save("examples/output/map_flow_5.html")
print(chart.spec["nameMap"])
```

**输出**：`USA` 通过 `name_map` 映射到 `United States` 后正常出线；`USA → China` 与 `USA → Germany` 两条线可见。

**验证**：`chart.spec["nameMap"]["USA"] == "United States"`；前端 3 条飞线全部保留。

### 示例 6：固定视角 + 隐藏色阶

```python
import eazy_data_viz as edv
import pandas as pd

flow = pd.DataFrame({
    "起点": ["上海", "北京", "广东"],
    "终点": ["广东", "上海", "北京"],
    "销售额": [900, 700, 500],
})
chart = edv.map_flow(
    flow, source="起点", target="终点", value="销售额",
    zoom=False, legend=False, theme="dark", palette="echarts",
    title="三地互发流向", subtitle="单位：元",
)
chart.save("examples/output/map_flow_6.html")
print(chart.spec["zoom"], chart.spec["legend"])
```

**输出**：深色主题，鼠标无法缩放/平移，流量色阶隐藏；三条互发线形成环状。

**验证**：`chart.spec["zoom"] is False`、`chart.spec["legend"] is False`；前端 `geo.roam === false`、`visualMap[0].show === false`。

### 示例 7：link 联动飞线与柱状图

```python
import eazy_data_viz as edv
import pandas as pd

flow = pd.DataFrame({
    "起点": ["上海", "上海", "北京"],
    "终点": ["广东", "北京", "广东"],
    "销售额": [1200, 800, 500],
})
chart = edv.map_flow(flow, source="起点", target="终点", value="销售额", link="flow-link")
bar = edv.bar(flow, x="起点", y="销售额", link="flow-link")
dash = edv.dashboard([chart, bar], cols=2, title="流向联动")
dash.save("examples/output/map_flow_7.html")
print(chart.spec["link"], bar.spec["link"])
```

**输出**：点击地图上从「上海」出发的任意一条线，右侧柱状图只显示起点为上海的流量；飞线图自身保持全貌。联动只按起点列过滤，不区分具体终点。

**验证**：两张图的 `spec["link"]` 都是 `"flow-link"`；点击后柱状图 `state.filters == {"起点": "上海"}`。

## 常见错误

**必填参数 / 列不存在 / 起终点同列**

```
TypeError: map_flow() missing 2 required positional arguments: 'source' and 'target'
KeyError: "source（起点列）列 '不存在' 不存在。当前可用的列有：..."
KeyError: "target（终点列）列 '不存在' 不存在。当前可用的列有：..."
ValueError: source 和 target 不能是同一列：飞线图需要「起点 → 终点」两个不同的区域列。
```

**地图 / 配色 / 主题等取值非法**

```
ValueError: map 只支持 "china"（中国）/ "world"（世界），收到 'usa'。
ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median
ValueError: fmt='wan' 不支持，可选：compact, thousands, raw, percent, currency
TypeError: name_map 需要是 dict，例如 name_map={'USA': 'United States'}，收到 'list'。
ValueError: theme 只支持 "light" / "dark"，收到 'blue'
ValueError: height 至少 120（像素），收到 100
ValueError: 未知配色 'foo'，可选：google、antd、tableau、carbon、echarts、morandi、tailwind
```

**传了不存在的参数**

```
TypeError: map_flow() got an unexpected keyword argument 'drill'
TypeError: map_flow() got an unexpected keyword argument 'labels'
```

飞线图没有 `drill` / `labels` 参数；下钻与标签请改用 `geo_map` / `map_bubble`。

**纯文本 `value` 不报错，但线宽异常**

`map_flow` 对数值列只做「能转就转」的清洗，转不了不会抛 `TypeError`；聚合后流量为空，所有线宽都接近 1 像素。排查 `df["销售额"].dtype`，或用 `pd.to_numeric(df["销售额"], errors="coerce")` 清洗。

**飞线不显示 / 少了若干条**

常见原因：起点或终点写法不在内置区域/城市表里、使用了 `大区` 这类非地图名称、世界图里写了不在别名表里的中文全称、起点终点解析到同一区域（自环）。提示只在浏览器控制台（`[eazy_map]` 前缀），Python 侧 `chart.warnings` 为空。

## 相关图表

- [geo_map](./geo_map.md)：区域填色，看「哪里多」。
- [map_bubble](./map_bubble.md)：区域气泡，看「哪里多大」。
- [bar](./bar.md)：起终点排名，常与飞线图 `link` 联动。
- [地图教程](../guides/map.md)：地图选型、数据准备与驾驶舱实战。
