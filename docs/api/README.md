# API 索引

53 个图表函数 + `Chart` 对象 + `dashboard()`。每页固定包含：函数签名、参数总览、逐参数详解、完整示例、常见问题、相关图表。本页只讲**跨函数的公共约定**，单个参数的细节请点进对应函数页。

签名与默认值的权威来源（文档与代码不一致时以它们为准）：

* [`docs/eazy_catalog.json`](../eazy_catalog.json)：机器可读的完整签名与参数元数据；
* `python -c "import eazy_data_viz as e; e.help()"`：终端里的速查；
* `python -c "import inspect, eazy_data_viz as e; print(inspect.signature(e.bar))"`：运行时真实签名。

## 通用返回对象 `Chart`

所有图表函数都返回同一个对象，Python 侧只做校验与数据打包，交互全部在前端完成：

| 方法 / 属性 | 说明 |
| --- | --- |
| `to_html(inline=True)` | 返回完整 HTML 字符串。`inline=False` 时改为引用 `eazy_assets/` 外链资产（需部署资产目录） |
| `save(path, inline=True)` | 写文件并返回绝对路径；目录不存在会自动创建；编码 UTF-8 |
| `show(open_browser=None)` | 自动判断环境：Streamlit 用 `components.html` 并按图表高度撑开 iframe；Jupyter 用 `IPython.display.HTML`；普通脚本写临时文件并打印路径（`open_browser=True` 时再调浏览器） |
| `palette(name)` | 单图覆盖配色（google / antd / tableau / carbon / echarts / morandi / tailwind），返回自身可链式调用 |
| `.spec` / `.data` / `.data_ref` / `.warnings` | 序列化后的图表配置、嵌入数据、数据指纹、告警（如采样、丢列）。调试与二次开发用 |
| `.title` | 图表标题（未显式传 `title` 时为自动生成的标题） |

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.bar(df, x="大区", y="销售额", color="渠道", stack=True)
print(chart.title)                       # 销售额 按 大区
chart.palette("tableau").save("examples/output/api-chart.html")
```

## 公共参数

下表是大多数图表共有的参数。**不是每个函数都有全部参数**（例如 `pie` 没有 `xlim`，`box` 没有 `link`，`matrix` 只有 8 个参数）；某函数到底支持哪些参数，以该函数页的「函数签名 / 参数总览」为准。

| 参数 | 含义 | 默认值 |
| --- | --- | --- |
| `data` | 第一个位置参数，`pandas.DataFrame`（也接受 Series / dict / list）；`gauge` / `ring_progress` 这类单值图不需要 | 必填（单值图除外） |
| `x` / `y` | 列名字符串：`x` 是维度（分类或时间），`y` 是度量；`y=None` 时按 `count` 统计行数 | `bar`/`line` 的 `x` 必填；`y` 可省略 |
| `color` | 分组列名，多个系列/多条线/堆叠色 | `None` |
| `size` | 气泡/散点大小列名（`scatter`、`map_bubble`） | `None` |
| `title` / `subtitle` | 标题 / 副标题；不传时按图表类型自动生成，如「销售额 按 大区」「销售额 趋势」 | `None`（自动） |
| `xtitle` / `ytitle` | 横轴 / 纵轴标题；不传取列名，传 `""` 隐藏 | `None` |
| `xlim` / `ylim` | 轴范围 `(最小值, 最大值)`，list/tuple 皆可；`lo > hi` 自动交换；传 `None` 表示不限制 | `None` |
| `fmt` | 数值格式：`compact`（1.2万）/ `thousands`（12,345）/ `raw`（12345）/ `percent`（12.3%，只加 % 不乘 100）/ `currency`（¥12,345.00） | `"compact"` |
| `agg` | 聚合方式：`sum` / `mean` / `count` / `max` / `min` / `median` | `"sum"`（`radar` 为 `"mean"`） |
| `sort` | 排序：`desc` / `asc` / `none` / `x`；不传时按图表类型自动（时间轴 `x`、`bar` 降序） | `None`（自动） |
| `top_n` | 只保留前 N 项，其余合并为「其他」（「其他」不可点击下钻） | `None` |
| `height` | 图表高度（像素），最小 120 | `380`（各图不同：KPI 150、gauge 260、calendar 300、pie/histogram 360、heatmap/combo/table 400、treemap 420、gantt/candlestick 420、sunburst/tree 460、地图 460） |
| `abs_height` | `True` 时 `height` 变成**整个组件外框**的高度（含标题、副标题、联动工具条），正文自适应剩余空间——同一行里标题长短不一时框底能对齐 | `False`（`height` 只算正文） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `light` / `dark`。看板内以第一张图的主题为准，页面右上角可运行时切换 | `"light"` |
| `legend` | 是否显示图例；图例可点选过滤系列 | `True`（部分图为 `False`，如 `waterfall`、`bullet`） |
| `labels` | 是否在图形上直接显示数值标签 | `False`（`pie`/`funnel`/`gantt`/`geo_map` 等默认 `True`） |
| `zoom` | 数据缩放条：`"auto"`（类目/数据点多时出现）/ `True` / `False` | `"auto"`（部分图为 `False`） |
| `palette` | 单图配色库名，覆盖页面默认配色（地图函数暴露此参数） | `None`（跟随页面） |
| `drill` | 下钻层级列名列表，如 `drill=["大区", "省份", "城市"]`；点击图形逐级下钻，面包屑返回 | `None` |
| `link` | 联动组名与方向：`"g1"`（双向）/ `("g1", "out")`（单向出）/ `("g1", "in")`（单向进）/ `{"group": "g1", "direction": "out"}`；同一页内相同组名的图互相筛选，要求组内使用同名维度列 | `None` |
| `section` | 看板分区标题：`dashboard()` 在连续图表前插入分区，用于把页面切成几段 | `None` |
| `max_rows` | 嵌入数据前最多保留多少行；超过时按行位置**均匀采样**（`np.linspace`），`None` 表示不采样；`table` 默认 200 | `200000` |

两个高频约定：

* **`fmt="percent"` 只加百分号不乘 100**：利润率要传 `利润 / 销售额 * 100`，传 `0.128` 会显示 `0.1%`。
* **`top_n` 合并出的「其他」不可点击**：它不对应任何原始行，下钻/联动需要完整覆盖时请先在 DataFrame 里过滤。

## 图表函数（按 7 组）

### 核心指标（7）

| 函数 | 一句话用途 |
| --- | --- |
| [`kpi`](kpi.md) | 单指标 KPI 卡：同比/环比、目标达成、迷你走势，可随联动重算 |
| [`group_kpi`](group_kpi.md) | 一组 KPI 卡（2–6 个）并排，适合指标区 |
| [`gauge`](gauge.md) | 仪表盘：单值 + 区间，完成率/健康度 |
| [`ring_progress`](ring_progress.md) | 环形进度：紧凑的百分比指标位 |
| [`bullet`](bullet.md) | 子弹图：横向实际条 + 目标刻度线 |
| [`target`](target.md) | 目标图：柱=实际、虚线=目标，按类目对比 |
| [`progress`](progress.md) | 进度条列表：名称 + 数值 + 横条，Top N 完成率 |

### 趋势（8）

| 函数 | 一句话用途 |
| --- | --- |
| [`line`](line.md) | 折线/面积趋势：多系列、平滑、阶梯、百分比 |
| [`area_pct`](area_pct.md) | 百分比堆叠面积：看结构随时间的占比变化 |
| [`combo`](combo.md) | 柱线双轴组合：柱看体量、线看率值 |
| [`sparkline`](sparkline.md) | 迷你走势：一图多行，适合指标看板 |
| [`theme_river`](theme_river.md) | 主题河流：多类别占比随时间的连续分布 |
| [`gantt`](gantt.md) | 甘特图：任务开始/结束/负责人排期 |
| [`candlestick`](candlestick.md) | K 线：OHLC 价格走势 |
| [`calendar`](calendar.md) | 日历热力：每天一格的活跃/金额规律 |

### 对比与排名（10）

| 函数 | 一句话用途 |
| --- | --- |
| [`bar`](bar.md) | 柱/条形图：分组、堆叠、横向、Top N 的全能选手 |
| [`bar_pct`](bar_pct.md) | 百分比堆叠柱：每个类目内部占比 100% |
| [`waterfall`](waterfall.md) | 瀑布图：正负增量逐段累加，看增减来源 |
| [`pareto`](pareto.md) | 帕累托图：柱 + 累计曲线，定位 80/20 |
| [`lollipop`](lollipop.md) | 棒棒糖图：比柱更轻的排名表达 |
| [`dumbbell`](dumbbell.md) | 哑铃图：两期/两组数值并排看差距 |
| [`slope`](slope.md) | 斜率图：两期之间的大小/名次变化 |
| [`bump`](bump.md) | 排名变化图：多期名次交叉 |
| [`pictorial`](pictorial.md) | 象形柱：用图标单位表达数量 |
| [`pyramid`](pyramid.md) | 金字塔：层级从下到上的结构对比 |

### 结构与占比（7）

| 函数 | 一句话用途 |
| --- | --- |
| [`pie`](pie.md) | 饼图/环图：≤6 个类目的占比 |
| [`rose`](rose.md) | 玫瑰图：多类目占比，扇区半径/角度编码 |
| [`funnel`](funnel.md) | 漏斗图：环节转化与流失 |
| [`treemap`](treemap.md) | 矩形树图：多层级占比，面积编码 |
| [`sunburst`](sunburst.md) | 旭日图：径向层级构成 |
| [`tree`](tree.md) | 树图：层级结构展开与折叠 |
| [`tile`](tile.md) | 瓦片图：方块矩阵，每块一个数值 |

### 分布与关系（11）

| 函数 | 一句话用途 |
| --- | --- |
| [`scatter`](scatter.md) | 散点图：两变量关系，可带大小/颜色 |
| [`histogram`](histogram.md) | 直方图：单变量分布与分箱 |
| [`box`](box.md) | 箱线图：分布、四分位与离群值 |
| [`heatmap`](heatmap.md) | 热力图：两个类目交叉的数值强弱 |
| [`matrix`](matrix.md) | 相关系数矩阵：数值列的 Pearson 相关 |
| [`radar`](radar.md) | 雷达图：多维评分对比 |
| [`parallel`](parallel.md) | 平行坐标：多指标个体比较 |
| [`quadrant`](quadrant.md) | 四象限散点：按中位数找重点客户 |
| [`sankey`](sankey.md) | 桑基图：节点间流向与转化 |
| [`graph`](graph.md) | 关系网络图：节点与边的关系 |
| [`trend`](trend.md) | 趋势回归图：散点 + 拟合线 + R² |

### 明细与文本（2）

| 函数 | 一句话用途 |
| --- | --- |
| [`table`](table.md) | 明细表：限行展示，可随联动过滤 |
| [`wordcloud`](wordcloud.md) | 词云：按数值大小排布的文本 |

### 地图与其它（4）

| 函数 | 一句话用途 |
| --- | --- |
| [`beijing_map`](beijing_map.md) | 北京区级填色地图：16 个市辖区（`geo_map` 的便捷封装） |
| [`geo_map`](geo_map.md) | 区域填色地图：颜色表达指标高低（中国/世界/北京） |
| [`map_bubble`](map_bubble.md) | 气泡地图：位置 + 气泡大小/颜色表达双指标 |
| [`map_flow`](map_flow.md) | 飞线地图：起点到终点的流量方向 |
| [`area`](area.md) | 面积图：`line(area=True)` 的简写 |

地图的完整用法（区域名归一化、城市回退、下钻聚焦、体积）见 [地图图表完全指南](../guides/map.md)。

## 多图页面：`dashboard()` 与 `show()`

只有放进**同一个页面**的图才能互相联动（`link`）和共享数据（同 `dataRef` 只嵌一次）：

```python
import eazy_data_viz as edv

df = edv.sample_df()
k = edv.kpi(df, value="销售额", label="销售额", link="g1")
trend = edv.line(df, x="日期", y="销售额", color="渠道", link="g1")
region = edv.bar(df, x="大区", y="销售额", link="g1", section="区域")
detail = edv.table(df, columns=["日期", "大区", "产品", "销售额"], link="g1")

edv.dashboard(k, trend, region, detail, cols=2, title="经营驾驶舱",
              desc="2024 全年").save("examples/output/api-dashboard.html")
```

* 函数：`edv.dashboard(*charts, cols=2, title=None, desc=None, theme=None, palette=None)`，返回 `Dashboard`，同样有 `to_html()` / `save()` / `show()`；也可以传一个图表列表。
* 简写：`edv.show(*charts, cols=2, ...)`；只有一张图时等同于 `Chart.show()`。
* `cols` 为栅格列数（1–6）；带 `title`/`desc` 时出现页头、配色下拉、深色切换与「重置联动」按钮。
* 看板主题取第一张图的 `theme`，可在页头运行时切换；`palette` 参数指定整页配色。
* 每张图可用 `section="分区名"` 分组，页面按图表顺序插入分区标题。
* Streamlit 中 `Dashboard.show()` 会自动按 `page_height()` 计算 iframe 高度；若手动 `components.html(dash.to_html(), height=...)`，高度不足会出现裁剪（见 [12 · 常见问题](../guides/12-troubleshooting.md)）。

## 数据与列类型

图表函数只接受列名，不接受 Series 表达式；进函数前请把数据整理成「一列一个角色」的长表（见 [09 · 数据准备](../guides/09-data-preparation.md)）：

* 数值列：`int/float`（可空数值类型），用于 `y` / `value` / `size`；
* 时间列：`datetime64`，用于 `x` / `date` / `start` / `end`（`calendar` / `gantt` / `candlestick` 会自动 `pd.to_datetime`）；
* 分类列：`object/string/category`，用于 `x` / `names` / `color` / `drill`；有序 `Categorical` 会保留类别顺序；
* 布尔列：显示为「是 / 否」；混入 `None` 后退化为分类列。

## 相关

* [教程总目录](../guides/README.md) · [文档总入口](../README.md)
* [AI_GUIDE.md](../AI_GUIDE.md)（给 AI 的紧凑契约）· [EXTRA_CHARTS.md](../EXTRA_CHARTS.md)（Python ⇄ JS 实现契约）
* 遇到报错先查 [12 · 常见问题与错误对照](../guides/12-troubleshooting.md)。
