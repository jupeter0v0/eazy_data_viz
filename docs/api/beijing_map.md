# `beijing_map` — 北京区级填色地图

> 北京 16 个市辖区的区级填色地图，是 [`geo_map`](geo_map.md) 的便捷封装（内部固定 `map="beijing"`）。
> 适合：北京各区销售额 / 订单量 / 门店数的区域对比，配合下钻、联动做区级分析。
> 不适合：精确排名（用 `bar`）、点位与双指标（用 `map_bubble`）、跨省或全国数据（用 `geo_map` 的 `china`）。

## 函数签名

```python
eazy_data_viz.beijing_map(
    data,
    region="区",
    value=None,
) -> Chart
```

等价于：

```python
eazy_data_viz.geo_map(data, region, value, map="beijing", **kwargs)
```

`region` 默认就是 `"区"`，所以最常见的写法只需要传三个位置参数：数据、区名列、数值列。
除 `map` 外，`geo_map` 的所有参数（`agg` / `fmt` / `labels` / `min_value` / `max_value` /
`name_map` / `zoom` / `palette` / `height` / `theme` / `title` / `subtitle` /
`drill` / `link` / `legend` / `section`）都通过 `**kwargs` 原样透传。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源 DataFrame |
| `region` | `str` | `'区'` | 否 | 区名列；短名（`朝阳`）与全名（`朝阳区`）都能匹配 |
| `value` | `str` | `None` | 否 | 填色数值列；省略表示统计记录数 |
| `**kwargs` | `—` | `—` | 否 | 透传给 `geo_map`：`map` 会被忽略并强制为 `beijing` |

## 参数详解

### `data` — 数据源（必填）

- **作用**：图表取数的唯一入口。`Series` 转单列、`dict` / `list` 转 DataFrame（list 每个元素一行）；超过 20 万行会均匀抽样，提示写进 `chart.warnings`。
- **取值建议 / 示例**：优先传清洗好的 `DataFrame`，例如 `data=df`；不要在绘图调用里做复杂变换。`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`

### `region` — 区名列

- **作用**：指定「颜色属于哪个区」的列，默认 `"区"`。北京地图只认 16 个市辖区：
  东城区、西城区、朝阳区、丰台区、石景山区、海淀区、门头沟区、房山区、通州区、顺义区、
  昌平区、大兴区、怀柔区、平谷区、密云区、延庆区。匹配前会做名称归一化（去掉空格、`·`、`.`，
  再循环剥离 `省 / 市 / 地区 / 盟 / 区 / 县` 等后缀），所以 `朝阳` 与 `朝阳区` 等价。
- **取值建议 / 示例**：数据列名不叫「区」时显式传入，例如 `region="所属区县"`。列名写错 → `KeyError: "region（区域列）列 '不存在' 不存在。当前可用的列有：..."`；传空串 → `ValueError: region（区域列） 需要是非空字符串，收到 '  '。`

### `value` — 填色数值列

- **作用**：决定区域颜色的指标列；省略时按区统计行数（`agg` 内部改成 `count`，标题度量名写成「记录数」）。先按 `region` 用 `agg` 聚合，再由连续色阶上色。文本型数字（`"1234"`、`"1,234"`）会自动转数值。
- **取值建议 / 示例**：销售额用 `sum`、单店均值用 `mean`，例如 `value="销售额"`；只看覆盖情况可省略 `value`。

### 其余参数（`**kwargs` 透传）

- **作用**：`beijing_map` 只固定了 `map`，其余参数与 [`geo_map`](geo_map.md) 完全一致，全部透传：
  `agg`（聚合方式）、`fmt`（数值格式）、`labels`（区名标签）、`min_value` / `max_value`（色阶范围）、
  `name_map`（区名映射）、`zoom`（是否允许缩放平移）、`palette`（配色）、`height`（画布高度）、
  `theme`（`light` / `dark`）、`title` / `subtitle`、`drill`、`link`、`legend`、`section`。
- **取值建议 / 示例**：想看同一量级的地图横向对比，固定色阶 `min_value=0, max_value=200`；
  不需要右侧色阶条设 `legend=False`。误传 `map="china"` 不会报错，会被忽略并仍然画北京地图
  （`beijing_map` 内部会 `kwargs.pop("map", None)`）。

## 完整示例

```python
import pandas as pd
import eazy_data_viz as edv

bj = pd.DataFrame({
    "区": ["东城区", "西城区", "朝阳区", "丰台区", "石景山区", "海淀区",
           "门头沟区", "房山区", "通州区", "顺义区", "昌平区", "大兴区",
           "怀柔区", "平谷区", "密云区", "延庆区"],
    "销售额": [52, 68, 128, 74, 31, 142, 18, 45, 63, 57, 88, 76, 25, 22, 25, 18],
    "订单数": [620, 720, 1180, 810, 360, 1260, 210, 480, 690, 640, 860, 790, 280, 240, 260, 200],
})

# 1) 最简用法：区名 + 销售额
chart = edv.beijing_map(bj, "区", "销售额", title="北京各区销售额")
chart.save("beijing_sales.html")

# 2) 固定色阶，方便多张地图横向比较
edv.beijing_map(bj, "区", "订单数", min_value=0, max_value=1300,
                palette="tableau", title="北京各区订单数").save("beijing_orders.html")

# 3) 参与联动：点击某个区，同组图表按「区 = 该区」过滤
kpi = edv.kpi(bj, value="销售额", label="总销售额", link="bj")
m = edv.beijing_map(bj, "区", "销售额", link="bj")
edv.dashboard(kpi, m, cols=2).save("beijing_dash.html")
```

## 北京地图与区域匹配

### 16 个市辖区

| 区名 | adcode | 区名 | adcode |
| --- | --- | --- | --- |
| 东城区 | 110101 | 通州区 | 110112 |
| 西城区 | 110102 | 顺义区 | 110113 |
| 朝阳区 | 110105 | 昌平区 | 110114 |
| 丰台区 | 110106 | 大兴区 | 110115 |
| 石景山区 | 110107 | 怀柔区 | 110116 |
| 海淀区 | 110108 | 平谷区 | 110117 |
| 门头沟区 | 110109 | 密云区 | 110118 |
| 房山区 | 110111 | 延庆区 | 110119 |

### 非北京 / 匹配不到的数据怎么处理

- **会被静默跳过**：不参与色阶、不参与总计与 tooltip 占比，图上不画。只有匹配到的区上色。
- **提示位置**：Python 侧写进 `chart.warnings`，`save()` / `to_html()` 时打印
  `[eazy_data_viz 提示] 区 列有 N 个区域名没匹配到内置北京地图…`；浏览器控制台另有一条
  `[eazy_map] 以下区域没有匹配到地图（已跳过）：…`。**Streamlit 界面不会弹提示条**。
- **全是外地数据**：系列为空 → 图上显示空状态「当前条件下没有数据」，不报错。
- **同名坑**：`朝阳区`（长春也有）、`通州区`（南通也有）只有短名时会被当成北京对应区；
  传全名 `长春市朝阳区`（归一化为 `长春朝阳`）可避免误判。
- **自查与过滤**：

```python
known = edv.maps.known_region_keys("beijing")          # 16 个归一化 key
bad = [v for v in bj["区"].dropna().unique()
       if edv.maps.normalize_region(v) not in known]
print("非北京数据：", bad)

# 过滤掉外地行，或把某个值改名映射到北京某区
bj_ok = bj[~bj["区"].isin(bad)]
edv.beijing_map(bj, "区", "销售额", name_map={"北京朝阳": "朝阳区"})
```

### `map_bubble` / `map_flow` 也能用北京地图

```python
edv.map_bubble(bj, region="区", value="销售额", map="beijing")
edv.map_flow(flow, source="起点区", target="终点区", value="件数", map="beijing")
```

只会落在 16 个区的质心上；对不上的区域同样跳过。

## 常见问题

- **和 `geo_map(..., map="beijing")` 有什么区别？** 没有任何渲染差异，只是 `map` 固定、`region` 默认 `"区"`，少写两个参数。
- **能下钻吗？** 地图的区域层永远按 `region` 聚合，`drill` 的效果是「点击某区 → 过滤该区的行 → 重绘」，不会出现街道边界。
- **色阶被一个特别大的值拉爆了？** 用 `max_value` 压住上限；`min_value` / `max_value` 只影响配色，不裁剪数据。
- **想显示全部 16 个区的名称？** 默认 `labels=True` 就会显示；区数只有 16，不存在世界地图那种标签糊成一片的问题。

## 透传参数速查

| 参数 | 作用 | 默认 | 常用取值 |
| --- | --- | --- | --- |
| `agg` | 同一区多行时的聚合方式 | `'sum'` | `sum` / `mean` / `count` / `max` / `min` / `median` |
| `fmt` | 色阶刻度与 tooltip 的数值格式 | `'compact'` | `compact` / `thousands` / `raw` / `percent` / `currency` |
| `labels` | 是否在区域上显示区名 | `True` | `True` / `False` |
| `min_value` | 色阶下限（只影响配色） | `None` | 如 `0` |
| `max_value` | 色阶上限（只影响配色） | `None` | 如 `200` |
| `name_map` | 数据原值 → 地图区名的映射 | `None` | `{"北京朝阳": "朝阳区"}` |
| `zoom` | 是否允许鼠标缩放 / 平移 | `None` | `True` / `False` |
| `palette` | 配色方案 | `None` | `google` / `antd` / `tableau` / `carbon` / `echarts` / `morandi` / `tailwind` |
| `height` | 画布高度（≥120） | `460` | `420`～`520` |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | 主题 | `'light'` | `light` / `dark` |
| `title` / `subtitle` | 标题 / 副标题 | 自动 | 任意字符串 |
| `drill` | 点击区域后聚焦该区域 | `None` | `"区"` |
| `link` | 联动组名 | `None` | 与其它图相同的组名 |
| `legend` | 是否显示右侧色阶条 | `True` | `True` / `False` |
| `section` | 看板分区标题（仅 dashboard 生效） | `None` | 任意字符串 |

## 主题与配色

```python
# 深色主题 + morandi 配色，适合大屏
edv.beijing_map(bj, "区", "销售额", theme="dark", palette="morandi")

# 只要图不要色阶条，卡片更干净
edv.beijing_map(bj, "区", "销售额", legend=False)
```

- 看板内主题以第一张图为准，页面右上角可运行时切换 `light` / `dark`。
- 地图取所选配色的主色作为「高热色」，再与主题背景混出 5 级渐变；同一看板建议统一配色。

## 在 Streamlit 里用

```python
import streamlit as st
import eazy_data_viz as edv

st.set_page_config(layout="wide")

# 与其它图表一样参与联动；不传 on_select 时点击/联动全部在浏览器内完成，0 rerun
edv.streamlit_dashboard([
    edv.kpi(bj, value="销售额", label="总销售额", link="bj"),
    edv.beijing_map(bj, "区", "销售额", link="bj", height=460),
], cols=2)
```

注意：数据里的非北京区域会被静默跳过，而 Streamlit 界面不会弹出告警条；
需要严格校验时，请在 Python 侧先用 `edv.maps.known_region_keys("beijing")` 过滤。

## 性能与体积

- 北京 GeoJSON 只有约 **0.10 MB**（16 个多边形），比世界地图（约 0.96 MB）小得多，页面打开很快。
- 渲染层只在用到中国地图时才注入 39 KB 的城市表（`window.EAZY_CITIES`）；
  只用北京地图的页面不会带这份数据。
- 单文件 HTML 至少约 1.2 MB（ECharts 与运行时内联），与普通图表页面一致。
- 16 个区的标签默认全部显示，不存在世界地图那种「区域太多标签糊成一片」的问题。

## 版本与兼容

- `beijing_map` 与 `map="beijing"` 自 **1.4.1** 起提供；在此之前的版本调用会
  报 `ValueError: map 只支持 "china"（中国）/ "world"（世界）…`。
- 升级：`pip install -U` 重新安装该库，或在仓库根目录 `pip install -e .`。
- `beijing_map` 是 `geo_map` 的薄封装，二者共用同一套渲染与匹配逻辑，升级后无需改代码。

## 相关图表

- [`geo_map`](geo_map.md) — 区域填色地图（中国 / 世界 / 北京三张内置地图）
- [`map_bubble`](map_bubble.md) — 气泡地图：位置 + 大小/颜色双指标
- [`map_flow`](map_flow.md) — 飞线地图：起点到终点的流量
- [`bar`](bar.md) — 排序与精确数值对比
