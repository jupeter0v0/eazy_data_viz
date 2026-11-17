# 地图图表完全指南

eazy_data_viz 内置中国与世界两张地图，提供三个地图函数：`geo_map`（区域填色）、`map_bubble`（区域气泡）、`map_flow`（区域飞线）。它们共用同一套地图资产、区域名归一化与匹配逻辑，切换到 `link` 联动、`drill` 下钻时行为也一致。本指南讲清三张图怎么选、数据怎么准备、交互怎么配、体积怎么控，最后给一个可直接运行的驾驶舱示例。

## 一、地图能做什么

- **区域填色（`geo_map`）**：一个指标 -> 一片颜色，回答「哪里高、哪里低」。适合销售额、订单量、覆盖率这类单指标区域对比。
- **区域气泡（`map_bubble`）**：在区域中心画圆，圆的大小表达第二指标，颜色表达分组，回答「哪里、多大、属于哪类」。适合城市级分布与双指标地图。
- **区域飞线（`map_flow`）**：起点到终点的动态连线，线宽表达流量，回答「从哪里流向哪里」。适合迁徙、物流、调拨、贸易。
- 三张图都支持 **`link` 联动**：点击地图区域，同组其它图自动过滤重绘；`geo_map` / `map_bubble` 还支持 **`drill` 聚焦**：点击区域只看该区域。

地图不是万能的：需要精确数值与排名时柱状图更好，需要层级占比时树图更好，需要点位热力时散点图更好。地图的价值在于「空间直觉」——一眼看出分布与方向。

## 二、三张图怎么选

| 你想表达 | 推荐函数 | 关键参数 | 典型场景 |
| --- | --- | --- | --- |
| 各省销售额高低 | `geo_map` | `region="省份", value="销售额"` | 区域业绩排名、覆盖热力 |
| 各城市销售额 + 订单量 | `map_bubble` | `region="城市", value="销售额", size="订单数"` | 城市运营、门店分布 |
| 城市按渠道拆分 | `map_bubble` | `+ color="渠道"` | 渠道结构、客群分布 |
| 城市间调拨/发货流向 | `map_flow` | `source="起点", target="终点", value="销售额"` | 物流、迁徙、贸易 |
| 单指标对比 + 精确排名 | 柱状图 | `bar(x=..., y=...)` | 排行榜 |
| 地图 + 明细联动 | 地图 + `link` | `link="g1"` 同组 | 驾驶舱 |
| 地图 + 逐级聚焦 | `geo_map` + `drill` | `drill="省份"` | 单区域详情 |

一句话：**颜色看高低、气泡看大小、飞线看方向；两个以上指标上气泡，有方向关系上飞线，其余用填色。**

## 三、数据准备

### 3.1 区域列怎么写

三张图的核心是「列里的值能匹配到地图区域」。匹配时先做归一化：去掉空格、`·`、`-`、`.`、`—` 等符号，再循环剥离 `省`、`市`、`自治区`、`特别行政区`、`自治州`、`地区`、`盟` 等后缀。

| 写法 | 是否支持 | 说明 |
| --- | --- | --- |
| `广东` | ✅ | 短名，推荐 |
| `广东省` | ✅ | 全名，等价短名 |
| `内蒙古` / `内蒙古自治区` | ✅ | 后缀自动剥离 |
| `广西` / `广西壮族自治区` | ✅ | 后缀自动剥离 |
| `内蒙` / `广西省` / `新疆省` | ✅ | 内置别名 |
| `广州` / `广州市` | ✅ | 城市短名/全名等价 |
| `石家庄` / `石家庄市` | ✅ | 城市短名/全名等价 |
| `美国` / `United States` / `USA` | ✅ | 世界图中文名、英文名、英文别名 |
| `华东` / `华南` | ❌ | 不是地图区域，会被跳过 |

内置中国地图有 34 个省级区域（另有 1 个南海诸岛占位）；世界地图有 215 个国家/地区。城市依赖内置城市表：**725 条原始名称，归一化去重后共 369 个可匹配名称**，覆盖地级市。想要城市的自定义名称也能匹配，用 `name_map`（见 3.3）。

### 3.2 用 `sample_df()` 快速上手

```python
import eazy_data_viz as edv

df = edv.sample_df()
print(df.shape)                       # (1500, 11)
print(df["省份"].unique()[:5])        # ['上海' '江苏' '浙江' '北京' '天津']
print(df["城市"].unique()[:5])        # ['上海市' '南京市' '杭州市' '北京市' '天津市']
print(df.columns.tolist())
```

`sample_df()` 的 `省份` 是短名、`城市` 是「广州市」这样的全名，均在地图内置表里，可直接用于三个地图函数。换自己的数据时，只要区域列的值能匹配即可，列名完全自定义。

### 3.3 `name_map`：把业务名称映射成地图名称

数据里的区域名往往不规范（英文缩写、历史命名、业务别名）。`name_map` 的键是数据原值（精确匹配），值是地图区域名：

```python
import eazy_data_viz as edv
import pandas as pd

world = pd.DataFrame({
    "国家": ["USA", "UK", "Germany", "巴西"],
    "订单数": [120, 80, 60, 40],
})
chart = edv.geo_map(
    world, region="国家", value="订单数", map="world",
    name_map={"USA": "United States", "UK": "United Kingdom"},
)
print(chart.spec["nameMap"])
```

- 键必须与数据里完全一致（区分大小写与空格），不经过归一化。
- 值是地图里的区域名：省/国家名；中国地图也接受内置城市名（`geo_map` 会汇总到所属省份）。
- 映射目标不存在时，浏览器控制台会提示「name_map 把「X」映射到了「Y」，但地图里没有这个区域，已忽略该映射。」，然后继续按原值兜底。
- `name_map` 不改变 tooltip 里显示的原值，只影响「落到哪个区域」。

### 3.4 自定义区域列名

`region` / `value` / `size` / `color` / `source` / `target` 都是「列名参数」，可以指向任意列：

```python
import eazy_data_viz as edv
import pandas as pd

raw = pd.DataFrame({
    "发货省": ["广东", "广东", "上海"],
    "收货省": ["北京", "上海", "北京"],
    "发货城市": ["广州市", "广州市", "上海市"],
    "金额": [1200, 800, 500],
})
geo = edv.geo_map(raw, region="发货省", value="金额")
flow = edv.map_flow(raw, source="发货省", target="收货省", value="金额")
bubble = edv.map_bubble(raw, region="发货城市", value="金额")
print(geo.spec["roles"]["region"], flow.spec["roles"]["source"], bubble.spec["roles"]["region"])
```

列名只用于取数，不参与地图匹配。列不存在会抛 `KeyError`（例如 `KeyError: "region（区域列）列 '不存在' 不存在。当前可用的列有：..."`）。

### 3.5 数据规模与聚合

- 三张图都接受明细行，同一区域/同一对起终点的多行由 `agg` 聚合（`sum` / `mean` / `count` / `max` / `min` / `median`，默认 `sum`）。
- 不传 `value` 时按记录数统计（`agg` 自动变成 `count`）。
- 超过 20 万行会均匀抽样，提示写入 `chart.warnings`；`chart.data["n"]` 是实际绘图行数、`n_total` 是原始行数。
- 聚合在前端完成，`chart.data["rows"]` 仍保留全部明细，页面体积随行数增长（见第五节）。

## 四、交互：drill、link、palette、theme

### 4.1 drill：点击区域聚焦

`geo_map` / `map_bubble` 支持 `drill`：点击某个区域后，按该区域过滤数据并重绘。地图只有区域（省/国家）边界，没有市级边界，所以 drill 的实际效果是 **「只看这一个区域」**，不是逐级下钻：

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.geo_map(df, region="省份", value="销售额", drill="省份")
print(chart.spec["drill"])              # ['省份', '省份']
print(chart.spec["roles"]["_extra"])    # ['省份', '省份']
chart.save("examples/output/guide_drill.html")
```

- 传字符串会被复制成两层；传列表时第一层强制为 `region`。
- 地图 drill 不会出现「省 -> 市」两层，第二次点击不会继续推进；需要真正多级下钻请组合不同图表或用 `bar` / `treemap`。
- `map_flow` 没有 `drill` 参数，传了会报 `TypeError: map_flow() got an unexpected keyword argument 'drill'`。

### 4.2 link：联动多张图

同 `link` 组名的一组图共享一次点击过滤：点击地图区域后，组内其它图按「当前维度 + 点击值」精确过滤，源图自身不过滤。地图的当前维度是它的区域列（`geo_map` / `map_bubble` 为 `region`，`map_flow` 为 `source`）。

```python
import eazy_data_viz as edv

df = edv.sample_df()
geo = edv.geo_map(df, region="省份", value="销售额", link="region-link")
bar = edv.bar(df, x="省份", y="销售额", link="region-link")
edv.dashboard([geo, bar], cols=2, title="地图联动柱状图").save("examples/output/guide_link.html")
print(geo.spec["link"], bar.spec["link"])
```

- 联动是字符串精确比较：`广东` 与 `广东省` 不会互相匹配，参与联动的图最好用同一种写法。
- 点击地图的「广东」后，柱状图按 `{"省份": "广东"}` 过滤；地图自身仍显示全国。
- 飞线图只联动起点：点击一条线，其它图按 `source` 列的值过滤，不区分终点。

### 4.3 palette 与 theme

- `palette` 可选 `google`、`antd`、`tableau`、`carbon`、`echarts`、`morandi`、`tailwind`，默认 `google`。地图取主色做高热色，气泡图多分组时按配色序列分配，飞线图取主色做线与箭头颜色。
- `theme` 只有 `light` / `dark`；深色主题会调整背景、文字、描边与色阶过渡。
- 页面级配色可在 `dashboard(palette=...)` 统一设置，单图 `palette=` 或 `chart.palette(name)` 覆盖。

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.geo_map(df, region="省份", value="销售额", palette="tableau", theme="dark")
chart.palette("morandi")
print(chart.spec["palette"], chart.spec["theme"])   # morandi dark
```

注意：先 `palette="tableau"` 再 `chart.palette("morandi")` 会以最后一次为准（示例里 `spec["theme"]` 仍是 `dark`）。

### 4.4 缩放与视角

`zoom` 是「开关」而不是「级别」：只有 `False` 关闭鼠标缩放/平移，`None` / `True` / `'auto'` / `'scale'` / `'move'` 行为一致（都允许）。默认视角：中国 `zoom=1.32`、中心 `[104, 35.5]`；世界 `zoom=1.12`。API 没有暴露视角参数，需要时直接改 `spec`（前端支持 `mapZoom` / `mapCenter`）：

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.geo_map(df, region="省份", value="销售额")
chart.spec["mapZoom"] = 1.6
chart.spec["mapCenter"] = [110, 30]
chart.save("examples/output/guide_view.html")
print(chart.spec["mapZoom"], chart.spec["mapCenter"])
```

### 4.5 提示框（tooltip）

- `geo_map`：区域名、度量值、占比；数据来自城市且一省多城时，额外显示「覆盖城市 N 个」。
- `map_bubble`：区域名、度量值、`size` 列值、`color` 分组、所属省份、占比。
- `map_flow`：`起点 → 终点`、流量值、起点/终点所属省份、占比；城市所属省份为空时（直辖市按省级处理）不显示该字段。

## 五、性能与体积

### 5.1 地图资产有多大

| 资产 | 体积 | 内容 |
| --- | --- | --- |
| `china.json` | 约 0.57 MB（582,522 B） | 34 个省级区域 + 1 个占位 |
| `world.json` | 约 0.96 MB（1,010,239 B） | 215 个国家/地区 |
| `china_cities.json` | 约 39 KB（39,897 B） | 725 条城市名 -> 省份 + 坐标 |

渲染时页面只注入「当前图表用到的地图」：纯中国地图页面不带 `world.json`；世界地图页面两者都不缺。城市表在用到任意地图时都会注入（约 39 KB）。

### 5.2 单文件 HTML 有多大

| 输出 | `inline=True`（默认） | `inline=False` |
| --- | --- | --- |
| 中国地图单图 | 约 2.1 MB（2,121,225 B） | `index.html` 约 0.87 MB + 外部 assets |
| 世界地图单图 | 约 2.4 MB（2,379,065 B） | `index.html` 约 1.12 MB + 外部 assets |
| 三图 dashboard | 约 2.1 MB（2,123,766 B） | 约 0.9 MB + 外部 assets |

`inline=True` 时 ECharts、eazy 运行时、地图 GeoJSON 全部内联，单文件可离线打开、适合发文档；`inline=False` 时只写一个 `index.html`，通过 `<script src="eazy_assets/...">` 引用资源——**这些资源不会复制到输出目录**，需要把包里的 `eazy_data_viz/assets/` 按同名路径部署到页面旁边，否则页面白屏。

### 5.3 体积与性能建议

- 明细行数越多，内联的数据越大：1000 行左右的三图看板仍在 2 MB 级；十万行级别建议先在 pandas 里聚合再画（前端 `agg` 只是方便，不减少传输体积）。
- 只用一个地图时不必引入另一张：`map` 参数按需选择，渲染层只注入用到的地图。
- 世界地图区域多、文字密，建议 `labels=False` 或只给有数据的区域显示标签；气泡图世界分布时设 `min_size=2, max_size=20` 减少压盖。
- 静态报告优先 `inline=False` 并统一部署 assets；单文件分发用默认 `inline=True`。

## 六、常见问题（FAQ）

**Q1：地图整张是空的，或某几个区域不上色？**

先看浏览器控制台有没有 `[eazy_map]` 开头的提示。未匹配区域会被跳过，提示只进 console、不写进 `chart.warnings`。常见原因：区域列用了 `大区` 这类非地图名称、城市名不在内置表里、世界图写了不在别名表里的中文全称、`name_map` 目标不是地图区域。用 `edv.maps.province_centers()` 可拿到 34 个省级短名做自查。

**Q2：所有区域颜色看起来一样？**

可能是数据差异太小，或 `min_value` / `max_value` 被固定在过宽的范围。先不传两端看自动色阶，再按需要固定；也可以换 `palette` 增强区分度。

**Q3：为什么城市填色是按省显示的？**

中国地图只有省级 GeoJSON，没有市级边界。`geo_map` 传城市列会把城市值汇总到所属省份再填色（tooltip 会显示覆盖城市数）。要看城市点位请用 `map_bubble` / `map_flow`。

**Q4：`吉林市`、`海南藏族自治州` 的位置不对？**

这是已知匹配限制：匹配顺序是「省级索引优先、城市兜底」，所以 `吉林市` 会落到吉林省中心、`海南藏族自治州`（属青海）会落到海南省中心。城市级分析请避开与省同名的城市，或改用不冲突的写法。

**Q5：`name_map` 不生效？**

检查三点：键与数据原值是否完全一致（含大小写、空格）、映射目标是否是地图区域（省/国家，或内置城市名）、是否在 `spec` 里看到 `nameMap`。目标不存在时控制台会提示并继续按原值兜底匹配。

**Q6：点击地图没有联动/没有下钻？**

- 联动：确认两张图的 `link` 组名相同、用于联动的列名与取值写法一致（`广东` ≠ `广东省`）。源地图自身不过滤是正常行为。
- 下钻：地图 drill 只有单区域聚焦，不会出现市级第二层；`map_flow` 不支持 drill。

**Q7：世界地图写中文国名匹配不到？**

常用中文国名（约 100 个）会自动转英文，例如 `美国`、`中国`、`德国`、`巴西`、`印度`。不在别名表里的中文全称（如「美利坚合众国」）不会匹配，请改用常用简称或用 `name_map` 指定 GeoJSON 英文名。

**Q8：`zoom=False` 和 `zoom=True` 有什么区别？**

只控制是否允许鼠标缩放/平移：`False` 关闭，其余值等价开启。它不影响默认缩放级别，也不影响坐标轴（地图没有 dataZoom）。

**Q9：数值格式不对 / 想显示单位？**

用 `fmt`：`compact`（1.9万）、`thousands`（19,519）、`raw`（195190.32）、`percent`、`currency`。更细的口径说明写在 `subtitle`。

**Q10：`geo_map` 的 `value` 是文本列为什么不报错，图却是空的？**

`geo_map` 对数值列只做「能转就转」的清洗，转不了不会抛 `TypeError`，前端聚合结果为空就显示「当前条件下没有数据」。`map_bubble` 则会抛 `TypeError` 并提示用 `pd.to_numeric()` 清洗。纯文本列请先清洗。

**Q11：为什么 `chart.warnings` 里没有未匹配区域的提示？**

设计如此：区域匹配发生在浏览器端，未匹配提示只输出到 console。Python 侧要自查，可用 `edv.maps` 的区域名集合与数据值做差集。

**Q12：dashboard 里地图卡片高度不对？**

卡片高度 = `height` + 标题区 + 有 `drill`/`link` 时的工具栏高度。多图并排时统一 `height`（如 480），避免卡片高低不齐。

## 七、完整驾驶舱示例

下面这个 dashboard 同时包含三张地图，并让 `geo_map` 与 `map_bubble` 通过 `link` 联动：点击省份，城市气泡图只显示该省城市；点击城市，省份地图只保留该城市所在省份。

```python
import eazy_data_viz as edv
import pandas as pd

df = edv.sample_df()

flow = pd.DataFrame({
    "起点": ["上海", "上海", "江苏", "北京", "广东"],
    "终点": ["广东", "北京", "广东", "广东", "江苏"],
    "调拨额": [1200, 800, 600, 500, 300],
})

geo = edv.geo_map(
    df, region="省份", value="销售额",
    fmt="compact", palette="google", link="map-link",
    title="各省销售额", subtitle="点击省份联动城市气泡",
)
bubble = edv.map_bubble(
    df, region="城市", value="销售额", size="订单数", color="渠道",
    min_size=4, max_size=24, palette="google", link="map-link",
    title="城市销售额与订单量", subtitle="气泡大小=订单数",
)
flow_chart = edv.map_flow(
    flow, source="起点", target="终点", value="调拨额",
    title="区域调拨流向", subtitle="线宽=调拨额",
)

dash = edv.dashboard(
    [geo, bubble, flow_chart],
    cols=2,
    title="区域销售驾驶舱",
    desc="左：各省销售额；右：城市气泡；下：区域调拨流向",
    theme="light",
    palette="google",
)
path = dash.save("examples/output/map_dashboard.html")
print("saved:", path)
print("geo:", geo.spec["type"], "bubble:", bubble.spec["type"], "flow:", flow_chart.spec["type"])
assert geo.spec["link"] == bubble.spec["link"] == "map-link"
```

**输出**：三张地图一屏展示；点击省份地图的「广东」，城市气泡图过滤为广东的城市；点击气泡「广州市」，省份地图过滤为广东；飞线图展示 5 条区域调拨流向，线宽随「调拨额」变化。

**验证**：

```python
import eazy_data_viz as edv
import pandas as pd

df = edv.sample_df()
geo = edv.geo_map(df, region="省份", value="销售额", link="map-link")
bubble = edv.map_bubble(df, region="城市", value="销售额", link="map-link")
assert geo.spec["link"] == bubble.spec["link"] == "map-link"
assert geo.spec["type"] == "geo_map" and bubble.spec["type"] == "map_bubble"
print("ok", geo.spec["map"], bubble.spec["map"])
```

### 7.1 驾驶舱设计建议

- **一屏只回答一个业务问题**：区域表现用「填色 + 气泡」，流向单列一张图；不要把三张地图都塞进第一屏。
- **统一配色与区域写法**：三张图用同一 `palette`；参与联动的图使用同一种区域写法（都短名或都全名）。
- **给颜色和大小写清口径**：`subtitle` 里写明「颜色=销售额、大小=订单数」，比图例更直接。
- **控制体积**：三图 dashboard 约 2 MB（内联）；日报场景可 `inline=False` 并复用外部 assets。
- **先聚合再画**：大数据量在 pandas 里 `groupby` 到区域粒度，能显著减小 HTML 体积。

### 7.2 从示例到生产

1. 把 `sample_df()` 换成真实 DataFrame，确认区域列写法能匹配（`edv.maps.province_centers()` 自查）。
2. 补齐业务字段：`value`、`size`、`color`、起终点列。
3. 按需加 `name_map`、`fmt`、`min_value/max_value`（`geo_map`）、`min_size/max_size`（`map_bubble`）。
4. 用 `link` 串起地图与排名图，用 `drill` 做单区域聚焦。
5. 用 `chart.save(...)` 输出，或 `edv.dashboard(...)` 组装多图页面。

更多细节见三个函数的 API 文档：[geo_map](../api/geo_map.md)、[map_bubble](../api/map_bubble.md)、[map_flow](../api/map_flow.md)。
