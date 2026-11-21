# eazy_data_viz 组件库说明书（给 AI 用）

> 版本 1.5.0 · 机器可读版：`docs/eazy_catalog.json` · 人读版：`README.md`

## 0. 一句话

pandas → 单文件 HTML 交互图表库（经营驾驶舱场景，Material Design 3，45 种图表，客户端下钻/联动，Streamlit 兼容）

## 1. 规则（先读这段，能避免 90% 的错误）

| 事项 | 约定 |
|---|---|
| 输入数据 | 第一参数永远是 pandas.DataFrame（除 gauge/ring_progress 这类单值图） |
| 列参数 | x/y/color/names/values 等参数都传【列名字符串】，不要传 Series 或 JSON |
| 返回值 | 所有图表函数返回 eazy_data_viz.Chart（.to_html() / .save(path) / .show()） |
| 聚合 agg | `sum` `mean` `count` `max` `min` `median` |
| 格式 fmt | `compact` `thousands` `raw` `percent` `currency` |
| 主题 | `light` / `dark`（页面级），配色见 palette |
| 多图联动 | 多图放同一页面才能联动：eazy_data_viz.dashboard(c1, c2, cols=2)；`link="g1"` 同组联动 |
| 下钻 | drill=["大区","省份"] 点击柱子逐级下钻 |
| 配色库 | `Chart.palette('tableau')` 或 `dashboard(..., palette='morandi')` |
| Streamlit | `eazy_data_viz.dashboard(...).show()` 自动用 `st.components.v1.html`，必须给 height |

## 2. 最快上手

```python
import eazy_data_viz
import pandas as pd

df = eazy_data_viz.sample_df()          # 演示数据；真实场景换成你的 DataFrame

# 单图：存成一个 HTML，双击就能看，可交互（缩放/图例/导出 PNG）
eazy_data_viz.bar(df, x="大区", y="销售额", color="渠道", top_n=8).save("bar.html")

# 看板：多图同页 → 才能联动
c1 = eazy_data_viz.line(df, x="月份", y="销售额", color="渠道", link="g1")
c2 = eazy_data_viz.bar(df, x="大区", y="销售额", color="产品", link="g1")
eazy_data_viz.dashboard(c1, c2, cols=2, title="经营看板").save("dash.html")
```

## 3. 配色库

默认 `google`（Material Design 3）。可用：

| 名字 | 风格 | 适合 |
|---|---|---|
| `Google Material 3` | 谷歌产品线配色（Google Blue 为主），干净、品牌感强，适合大多数经营看板。 | 通用 / 公司经营驾驶舱默认 |
| `Ant Design` | 蚂蚁 Ant Design 5 的默认色板，蓝紫为主、饱和度略高，企业后台最常见。 | 中后台 / 业务报表 |
| `Tableau 10` | Tableau 默认十色，明度层次分明，多系列折线/散点分组可读性极好。 | 多系列对比 / BI 分析图 |
| `IBM Carbon` | IBM Carbon Design 的分类色，冷色偏多、对比强，适合深色大屏与数据密集型看板。 | 深色大屏 / 技术运营 |
| `ECharts 默认` | ECharts 官方默认色板，国内报表里认知度最高，几乎不用解释。 | 兼容既有 ECharts 报表 |
| `莫兰迪（低饱和）` | 低饱和灰调色板，柔和、彼此不抢眼，适合给老板看的汇报型看板。 | 汇报 / 印刷 / 弱对比大屏 |
| `Tailwind / Flowbite` | 现代 Web 产品常用的 Tailwind 色板，明亮活泼，适合面向 C 端的增长看板。 | 产品增长 / 运营看板 |

```python
eazy_data_viz.bar(df, x="大区", y="销售额").palette("tableau").show()   # 单图换色
eazy_data_viz.dashboard(c1, c2, palette="morandi").save("x.html")      # 整页换色
eazy_data_viz.set_palette("carbon")                                     # 改全局默认
```

## 4. 图表函数（按场景分组，共 50 个）

### 核心指标

| 函数 | 签名 | 说明 |
|---|---|---|
| `kpi` | `kpi(data=None, value=None, *, agg='sum', label=None, fmt=None, delta=None, delta_label=None, inverse=False, target=None, target_label=None, spark=None, spark_x=None, hint=None, unit=None, prefix=None, accent=0, height=150, abs_height=False, theme='light', title=None, subtitle=None, link=None, section=None)` | KPI 数字卡片（驾驶舱指标头，可跟随联动筛选自动重算）。 |
| `group_kpi` | `group_kpi(data=None, names=None, values=None, *, items=None, agg='sum', sort='desc', top_n=6, unit=None, delta=None, fmt='compact', title=None, subtitle=None, height=140, abs_height=False, theme='light')` | KPI 卡片组（HTML 渲染）：一排指标卡片。 |
| `gauge` | `gauge(value, *, label=None, min=0, max=100, fmt='raw', unit=None, height=260, abs_height=False, theme='light', title=None, subtitle=None)` | 仪表盘（单个数值）。 |
| `ring_progress` | `ring_progress(percent, *, label=None, max=100, fmt=None, height=None, abs_height=False, theme='light', title=None)` | 环形进度：一个百分比/完成值画成圆环，中心显示数值（不接 DataFrame）。 |
| `bullet` | `bullet(data, x, actual, target=None, *, target_value=None, agg='sum', sort=None, top_n=None, title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=380, abs_height=False, theme='light', legend=False, labels=False, zoom=False, drill=None, link=None, max_rows=200000)` | 子弹图：每类一个实际值，对比目标值（横向，目标用刻度线表示）。 |
| `target` | `target(data, x, actual, target=None, *, target_value=None, agg='sum', sort=None, top_n=None, title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=380, abs_height=False, theme='light', legend=True, labels=False, zoom='auto', drill=None, link=None, max_rows=200000)` | 目标对比图：实际值柱子 + 目标值折线（虚线）。 |
| `progress` | `progress(data, x=None, y=None, *, max=None, agg='sum', sort='desc', top_n=10, title=None, subtitle=None, fmt='compact', height=340, abs_height=False, theme='light', link=None, max_rows=200000)` | 进度条列表（HTML 渲染）：每类一条「名称 + 数值 + 进度条」。 |

**`kpi`** — KPI 数字卡片（驾驶舱指标头，可跟随联动筛选自动重算）。

```python
eazy_data_viz.kpi(df, value="销售额", label="全年销售额", delta=0.128, target=2000000)
```

**`group_kpi`** — KPI 卡片组（HTML 渲染）：一排指标卡片。

```python
eazy_data_viz.group_kpi(df, names="大区", values="销售额", title="大区概况")
```

**`gauge`** — 仪表盘（单个数值）。

```python
eazy_data_viz.gauge(19.9, label="利润率", min=0, max=40, fmt="percent")
```

**`ring_progress`** — 环形进度：一个百分比/完成值画成圆环，中心显示数值（不接 DataFrame）。

```python
eazy_data_viz.ring_progress(78, label="年度目标达成率")
```

**`bullet`** — 子弹图：每类一个实际值，对比目标值（横向，目标用刻度线表示）。

```python
eazy_data_viz.bullet(df, x="大区", actual="销售额", target_value=500000)
```

**`target`** — 目标对比图：实际值柱子 + 目标值折线（虚线）。

```python
eazy_data_viz.target(df, x="大区", actual="销售额", target_value=500000)
```

**`progress`** — 进度条列表（HTML 渲染）：每类一条「名称 + 数值 + 进度条」。

```python
eazy_data_viz.progress(df, x="大区", y="销售额")
```

### 趋势

| 函数 | 签名 | 说明 |
|---|---|---|
| `line` | `line(data, x, y, color=None, *, agg='sum', smooth=True, area=False, markers=None, sort=None, top_n=None, title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=380, abs_height=False, theme='light', drill=None, link=None, legend=True, labels=False, zoom='auto', max_rows=200000, step=False, percent=False, section=None)` | 折线图 / 面积图 / 阶梯图。 |
| `area_pct` | `area_pct(data, x, y, color=None, *, agg='sum', sort=None, top_n=None, title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=380, abs_height=False, theme='light', legend=True, labels=False, zoom='auto', drill=None, link=None, max_rows=200000)` | 百分比堆叠面积图：每个 x 归一化到 100%，看各 color 的占比变化。 |
| `combo` | `combo(data, x, bar=None, line=None, *, agg='sum', title=None, subtitle=None, xtitle=None, ytitle=None, fmt='compact', height=400, abs_height=False, theme='light', zoom='auto', link=None, max_rows=200000)` | 柱线混合图（一根柱子 + 一条折线，双坐标轴）。 |
| `sparkline` | `sparkline(data, x, y, *, group, agg='sum', title=None, subtitle=None, fmt='compact', height=260, abs_height=False, theme='light', max_rows=200000)` | 迷你走势（sparkline）：每个 group 一张无坐标轴小折线，最多 12 个。 |
| `theme_river` | `theme_river(data, x, color, value=None, *, agg='sum', sort=None, top_n=None, title=None, subtitle=None, fmt='compact', height=380, abs_height=False, theme='light', legend=True, labels=False, zoom='auto', link=None, max_rows=200000)` | 主题河流图：各类目随时间的体量变化，像河流一样堆叠流动。 |
| `gantt` | `gantt(data, task, start, end, *, color=None, agg='sum', sort=None, top_n=None, title=None, subtitle=None, fmt='compact', height=420, abs_height=False, theme='light', legend=None, labels=True, zoom=False, link=None, max_rows=200000)` | 甘特图：横向时间条，展示每个任务的起止时间。 |
| `candlestick` | `candlestick(data, date, open, high, low, close, *, title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=420, abs_height=False, theme='light', legend=False, labels=False, zoom='auto', link=None, max_rows=200000)` | K 线图（红涨绿跌）：需要日期 + 开 / 高 / 低 / 收 四列。 |
| `calendar` | `calendar(data, date, value=None, *, agg='sum', sort='x', top_n=None, title=None, subtitle=None, fmt='compact', height=300, abs_height=False, theme='light', legend=False, labels=False, zoom=False, link=None, max_rows=200000)` | 日历热力图：按天显示数值深浅（日期列会在 Python 侧转成 YYYY-MM-DD）。 |

**`line`** — 折线图 / 面积图 / 阶梯图。

```python
eazy_data_viz.line(df, x="月份", y="销售额", color="产品", smooth=True)
```

**`area_pct`** — 百分比堆叠面积图：每个 x 归一化到 100%，看各 color 的占比变化。

```python
eazy_data_viz.area_pct(df, x="月份", y="销售额", color="产品")
```

**`combo`** — 柱线混合图（一根柱子 + 一条折线，双坐标轴）。

```python
eazy_data_viz.combo(df, x="月份", bar="销售额", line="利润")
```

**`sparkline`** — 迷你走势（sparkline）：每个 group 一张无坐标轴小折线，最多 12 个。

```python
eazy_data_viz.sparkline(df, x="月份", y="销售额", group="渠道")
```

**`theme_river`** — 主题河流图：各类目随时间的体量变化，像河流一样堆叠流动。

```python
eazy_data_viz.theme_river(df, x="月份", color="产品", value="销售额")
```

**`gantt`** — 甘特图：横向时间条，展示每个任务的起止时间。

```python
eazy_data_viz.gantt(pd.DataFrame({"任务": ["调研", "开发"], "开始": ["2024-01-01", "2024-02-01"], "结束": ["2024-02-01", "2024-05-01"], "部门": ["产品", "研发"]}), task="任务", start="开始", end="结束", color="部门")
```

**`candlestick`** — K 线图（红涨绿跌）：需要日期 + 开 / 高 / 低 / 收 四列。

```python
eazy_data_viz.candlestick(pd.DataFrame({"日期": ["2024-01-01", "2024-01-02"], "开盘": [10.0, 10.6], "最高": [10.9, 11.2], "最低": [9.8, 10.2], "收盘": [10.6, 10.7]}), date="日期", open="开盘", high="最高", low="最低", close="收盘")
```

**`calendar`** — 日历热力图：按天显示数值深浅（日期列会在 Python 侧转成 YYYY-MM-DD）。

```python
eazy_data_viz.calendar(df, date="日期", value="销售额")
```

### 对比与排名

| 函数 | 签名 | 说明 |
|---|---|---|
| `bar` | `bar(data, x, y=None, color=None, *, agg='sum', stack=False, horizontal=False, sort=None, top_n=None, title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=380, abs_height=False, theme='light', drill=None, link=None, legend=True, labels=False, zoom='auto', max_rows=200000, percent=False, yoy=False, section=None)` | 柱状图 / 条形图（支持分组、堆叠、百分比、同比、下钻、联动）。 |
| `bar_pct` | `bar_pct(data, x, y, color=None, *, agg='sum', sort=None, top_n=None, title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=380, abs_height=False, theme='light', legend=True, labels=False, zoom='auto', drill=None, link=None, max_rows=200000)` | 百分比堆叠柱图：每个 x 归一化到 100%，看各 color 的占比。 |
| `waterfall` | `waterfall(data, x, y=None, *, agg='sum', total=None, sort=None, top_n=None, title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=380, abs_height=False, theme='light', legend=False, labels=False, zoom='auto', drill=None, link=None, max_rows=200000)` | 瀑布图：各分项正负增量逐段累加，直观看到「从哪来、累计到多少」。 |
| `pareto` | `pareto(data, x, y=None, *, agg='sum', top_n=None, cum_fmt='percent', sort=None, title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=400, abs_height=False, theme='light', legend=False, labels=False, zoom='auto', drill=None, link=None, max_rows=200000)` | 帕累托图：按数值降序的柱 + 累计占比折线（右轴 0~100%）。 |
| `lollipop` | `lollipop(data, x, y=None, *, agg='sum', sort=None, top_n=None, title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=380, abs_height=False, theme='light', legend=False, labels=False, zoom='auto', drill=None, link=None, max_rows=200000)` | 棒棒糖图：细柱 + 顶端圆点，比柱状图更清爽的排行榜。 |
| `dumbbell` | `dumbbell(data, x, y1, y2, *, labels=None, series_names=None, agg='sum', sort=None, top_n=None, title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=380, abs_height=False, theme='light', legend=True, zoom='auto', drill=None, link=None, max_rows=200000)` | 哑铃图：同一类目两个数值（如两期、两组）之间的差距对比。 |
| `slope` | `slope(data, x, y, color=None, *, group=None, period=None, agg='sum', sort=None, top_n=None, title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=380, abs_height=False, theme='light', legend=True, labels=False, zoom=False, drill=None, link=None, max_rows=200000)` | 斜率图：同一类目在两个「期」之间的变化（两点连线，斜率即变化）。 |
| `bump` | `bump(data, x, y, *, group, agg='sum', sort=None, top_n=None, title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=420, abs_height=False, theme='light', legend=True, labels=False, zoom='auto', drill=None, link=None, max_rows=200000)` | 排名变化图（bump chart）：每个 group 一条折线，y 轴是排名。 |
| `pictorial` | `pictorial(data, x, y=None, *, symbol='circle', agg='sum', sort=None, top_n=None, title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=380, abs_height=False, theme='light', legend=False, labels=True, zoom='auto', drill=None, link=None, max_rows=200000)` | 象形柱图：用重复的小图形（circle / rect / roundRect / diamond / triangle）堆出柱子。 |
| `pyramid` | `pyramid(data, names, values=None, *, agg='sum', sort='asc', top_n=None, title=None, subtitle=None, fmt='compact', height=380, abs_height=False, theme='light', legend=False, labels=True, zoom=False, link=None, max_rows=200000)` | 金字塔图：漏斗图上下翻转（下宽上窄），常用于层级/转化结构。 |

**`bar`** — 柱状图 / 条形图（支持分组、堆叠、百分比、同比、下钻、联动）。

```python
eazy_data_viz.bar(df, x="大区", y="销售额", color="渠道", stack=True)
```

**`bar_pct`** — 百分比堆叠柱图：每个 x 归一化到 100%，看各 color 的占比。

```python
eazy_data_viz.bar_pct(df, x="月份", y="销售额", color="渠道")
```

**`waterfall`** — 瀑布图：各分项正负增量逐段累加，直观看到「从哪来、累计到多少」。

```python
eazy_data_viz.waterfall(df, x="产品", y="销售额", total=True)
```

**`pareto`** — 帕累托图：按数值降序的柱 + 累计占比折线（右轴 0~100%）。

```python
eazy_data_viz.pareto(df, x="月份")
```

**`lollipop`** — 棒棒糖图：细柱 + 顶端圆点，比柱状图更清爽的排行榜。

```python
eazy_data_viz.lollipop(df, x="月份")
```

**`dumbbell`** — 哑铃图：同一类目两个数值（如两期、两组）之间的差距对比。

```python
eazy_data_viz.dumbbell(df, x="大区", y1="销售额", y2="利润")
```

**`slope`** — 斜率图：同一类目在两个「期」之间的变化（两点连线，斜率即变化）。

```python
eazy_data_viz.slope(df, x="月份", y="销售额", color="产品")
```

**`bump`** — 排名变化图（bump chart）：每个 group 一条折线，y 轴是排名。

```python
eazy_data_viz.bump(df, x="月份", y="销售额", group="产品")
```

**`pictorial`** — 象形柱图：用重复的小图形（circle / rect / roundRect / diamond / triangle）堆出柱子。

```python
eazy_data_viz.pictorial(df, x="月份")
```

**`pyramid`** — 金字塔图：漏斗图上下翻转（下宽上窄），常用于层级/转化结构。

```python
eazy_data_viz.pyramid(df, names="产品")
```

### 结构与占比

| 函数 | 签名 | 说明 |
|---|---|---|
| `pie` | `pie(data, names, values=None, *, donut=False, agg='sum', sort='desc', top_n=None, title=None, subtitle=None, fmt='compact', height=360, abs_height=False, theme='light', labels=True, link=None, max_rows=200000)` | 饼图 / 环图。 |
| `rose` | `rose(data, names, values=None, *, donut=False, agg='sum', sort='desc', top_n=None, title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=380, abs_height=False, theme='light', legend=True, labels=True, zoom=False, drill=None, link=None, max_rows=200000)` | 南丁格尔玫瑰图：用半径表达数值的饼图。 |
| `funnel` | `funnel(data, names, values=None, *, agg='sum', fmt='compact', height=380, abs_height=False, theme='light', title=None, subtitle=None, labels=True, link=None, max_rows=200000)` | 漏斗图（转化/流程）。 |
| `treemap` | `treemap(data, path, value, *, agg='sum', title=None, subtitle=None, fmt='compact', height=420, abs_height=False, theme='light', max_rows=200000)` | 矩形树图（多层级构成）。 |
| `sunburst` | `sunburst(data, path, value=None, *, agg='sum', sort='desc', top_n=None, title=None, subtitle=None, xtitle=None, ytitle=None, fmt='compact', height=460, abs_height=False, theme='light', legend=False, labels=True, zoom=False, link=None, max_rows=200000)` | 旭日图：多层级构成的同心圆环。 |
| `tree` | `tree(data, path, value=None, *, agg='sum', sort='desc', top_n=None, title=None, subtitle=None, xtitle=None, ytitle=None, fmt='compact', height=460, abs_height=False, theme='light', legend=False, labels=True, zoom=False, link=None, max_rows=200000)` | 树图：从左到右的层级结构（树状），节点大小可反映数值。 |
| `tile` | `tile(data, names=None, values=None, *, agg='sum', sort=None, top_n=None, title=None, subtitle=None, fmt='compact', height=360, abs_height=False, theme='light', link=None, max_rows=200000)` | 瓦片图（HTML 渲染）：每个类目一个方块，颜色深浅表示数值大小。 |

**`pie`** — 饼图 / 环图。

```python
eazy_data_viz.pie(df, names="产品", values="销售额", donut=True)
```

**`rose`** — 南丁格尔玫瑰图：用半径表达数值的饼图。

```python
eazy_data_viz.rose(df, names="产品")
```

**`funnel`** — 漏斗图（转化/流程）。

```python
eazy_data_viz.funnel(df, names="产品")
```

**`treemap`** — 矩形树图（多层级构成）。

```python
eazy_data_viz.treemap(df, path=["大区", "省份"], value="销售额")
```

**`sunburst`** — 旭日图：多层级构成的同心圆环。

```python
eazy_data_viz.sunburst(df, path=["大区", "省份"], value="销售额")
```

**`tree`** — 树图：从左到右的层级结构（树状），节点大小可反映数值。

```python
eazy_data_viz.tree(df, path=["大区", "省份"])
```

**`tile`** — 瓦片图（HTML 渲染）：每个类目一个方块，颜色深浅表示数值大小。

```python
eazy_data_viz.tile(df)
```

### 分布与关系

| 函数 | 签名 | 说明 |
|---|---|---|
| `scatter` | `scatter(data, x, y, color=None, size=None, *, agg='sum', title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=380, abs_height=False, theme='light', link=None, legend=True, max_rows=200000)` | 散点图（x / y 都必须是数值列，可选气泡大小）。 |
| `histogram` | `histogram(data, column=None, *, bins=20, title=None, subtitle=None, xtitle=None, ytitle='频数', fmt='compact', height=360, abs_height=False, theme='light', labels=False, max_rows=200000)` | 直方图（数值分布）。 |
| `box` | `box(data, x=None, y=None, *, title=None, subtitle=None, ytitle=None, fmt='compact', height=380, abs_height=False, theme='light', max_rows=200000)` | 箱线图（按类目展示数值分布）。 |
| `heatmap` | `heatmap(data, x, y, value, *, agg='sum', sort=None, title=None, subtitle=None, xtitle=None, ytitle=None, fmt='compact', height=400, abs_height=False, theme='light', labels=False, max_rows=200000, link=None)` | 热力图（x × y 的数值矩阵）。 |
| `matrix` | `matrix(data, columns=None, *, max_cols=12, title=None, subtitle=None, fmt='compact', height=460, abs_height=False, theme='light')` | 相关系数矩阵（Pearson）：热力图 + 格子里两位小数的 r 值。 |
| `radar` | `radar(data, x, y=None, color=None, *, max=None, agg='mean', sort=None, top_n=None, title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=400, abs_height=False, theme='light', legend=True, labels=False, zoom=False, drill=None, link=None, max_rows=200000)` | 雷达图：每个 color 组一条闭合折线，指标是 x 的各个类目。 |
| `parallel` | `parallel(data, dims, *, color=None, title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=440, abs_height=False, theme='light', legend=False, labels=False, zoom=False, link=None, max_rows=200000)` | 平行坐标：每一行是一条折线，每个维度一根纵轴，用来看多维分布/聚类。 |
| `quadrant` | `quadrant(data, x, y, size=None, color=None, *, quad_labels=None, title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=400, abs_height=False, theme='light', legend=None, labels=False, zoom=False, link=None, max_rows=200000)` | 四象限散点图：用 x / y 的中位数把平面切成四块，看对象落在哪个象限。 |
| `sankey` | `sankey(data, source=None, target=None, value=None, *, path=None, agg='sum', sort=None, top_n=None, title=None, subtitle=None, fmt='compact', height=420, abs_height=False, theme='light', legend=False, labels=True, zoom=False, link=None, max_rows=200000)` | 桑基图：展示流量在多层「来源 → 去向」之间的流转及大小。 |
| `graph` | `graph(data, source, target, value=None, *, agg='sum', sort=None, top_n=None, title=None, subtitle=None, fmt='compact', height=420, abs_height=False, theme='light', legend=False, labels=True, zoom=False, link=None, max_rows=200000)` | 关系图：力导向网络图，节点大小/边宽反映数值。 |
| `trend` | `trend(data, x, y, color=None, *, title=None, subtitle=None, xtitle=None, ytitle=None, xlim=None, ylim=None, fmt='compact', height=400, abs_height=False, theme='light', legend=None, labels=False, zoom=False, link=None, max_rows=200000)` | 趋势散点图：散点 + 最小二乘回归线，图例/副标题带 R²。 |

**`scatter`** — 散点图（x / y 都必须是数值列，可选气泡大小）。

```python
eazy_data_viz.scatter(df, x="订单数", y="销售额", size="客户数")
```

**`histogram`** — 直方图（数值分布）。

```python
eazy_data_viz.histogram(df, column="销售额", bins=24)
```

**`box`** — 箱线图（按类目展示数值分布）。

```python
eazy_data_viz.box(df, x="渠道", y="销售额")
```

**`heatmap`** — 热力图（x × y 的数值矩阵）。

```python
eazy_data_viz.heatmap(df, x="月份", y="大区", value="销售额")
```

**`matrix`** — 相关系数矩阵（Pearson）：热力图 + 格子里两位小数的 r 值。

```python
eazy_data_viz.matrix(df, columns=["销售额", "订单数", "利润", "客户数"])
```

**`radar`** — 雷达图：每个 color 组一条闭合折线，指标是 x 的各个类目。

```python
eazy_data_viz.radar(df, x="产品", y="销售额", color="大区")
```

**`parallel`** — 平行坐标：每一行是一条折线，每个维度一根纵轴，用来看多维分布/聚类。

```python
eazy_data_viz.parallel(df, dims=["销售额", "订单数", "利润"])
```

**`quadrant`** — 四象限散点图：用 x / y 的中位数把平面切成四块，看对象落在哪个象限。

```python
eazy_data_viz.quadrant(df, x="订单数", y="销售额", color="大区")
```

**`sankey`** — 桑基图：展示流量在多层「来源 → 去向」之间的流转及大小。

```python
eazy_data_viz.sankey(df, path=["大区", "渠道", "产品"], value="销售额")
```

**`graph`** — 关系图：力导向网络图，节点大小/边宽反映数值。

```python
eazy_data_viz.graph(df, source="渠道", target="产品")
```

**`trend`** — 趋势散点图：散点 + 最小二乘回归线，图例/副标题带 R²。

```python
eazy_data_viz.trend(df, x="客户数", y="利润", color="产品")
```

### 地图

| 函数 | 签名 | 说明 |
|---|---|---|
| `geo_map` | `geo_map(data, region, value=None, *, map='china', agg='sum', fmt='compact', labels=True, min_value=None, max_value=None, name_map=None, zoom=None, palette=None, height=460, abs_height=False, theme='light', title=None, subtitle=None, drill=None, link=None, legend=True, section=None)` | 区域填色地图：用颜色深浅表达一个指标在各省 / 各国 / 北京各区上的高低。 |
| `beijing_map` | `beijing_map(data, region='区', value=None, **kwargs)` | 北京 16 个市辖区的区级填色地图。 |
| `map_bubble` | `map_bubble(data, region, value=None, *, map='china', agg='sum', size=None, color=None, fmt='compact', min_size=4, max_size=28, name_map=None, zoom=None, palette=None, height=460, abs_height=False, theme='light', title=None, subtitle=None, drill=None, link=None, legend=True, section=None)` | 气泡地图：在省份 / 国家中心点画气泡，气泡大小和颜色可以再编码两个指标。 |
| `map_flow` | `map_flow(data, source, target, value=None, *, map='china', agg='sum', fmt='compact', name_map=None, zoom=None, palette=None, height=460, abs_height=False, theme='light', title=None, subtitle=None, link=None, legend=True, section=None)` | 飞线地图：把一条数据当作「source → target」的流量，在地图上画动态飞线。 |

**`geo_map`** — 区域填色地图：用颜色深浅表达一个指标在各省 / 各国 / 北京各区上的高低。

```python
eazy_data_viz.geo_map(df, region="省份", value="销售额")
```

**`beijing_map`** — 北京 16 个市辖区的区级填色地图。

```python
eazy_data_viz.beijing_map(pd.DataFrame({"区": ["朝阳区", "海淀区"], "销售额": [128, 142]}), region="区", value="销售额")
```

**`map_bubble`** — 气泡地图：在省份 / 国家中心点画气泡，气泡大小和颜色可以再编码两个指标。

```python
eazy_data_viz.map_bubble(df, region="城市", value="销售额")
```

**`map_flow`** — 飞线地图：把一条数据当作「source → target」的流量，在地图上画动态飞线。

```python
eazy_data_viz.map_flow(pd.DataFrame({"出发城市": ["北京市", "上海市", "广州市"], "到达城市": ["广州市", "成都市", "上海市"], "件数": [320, 280, 260]}), source="出发城市", target="到达城市", value="件数")
```

### 明细与文本

| 函数 | 签名 | 说明 |
|---|---|---|
| `table` | `table(data, columns=None, *, groupby=None, limit=100, title=None, subtitle=None, fmt='compact', height=400, abs_height=False, theme='light', link=None, max_rows=200, total=False, index=False, bar=None, stripe=True)` | 表格（HTML 渲染）：明细表，或按 groupby 汇总后的汇总表。 |
| `wordcloud` | `wordcloud(data, names=None, values=None, *, agg='sum', sort=None, top_n=30, title=None, subtitle=None, fmt='compact', height=360, abs_height=False, theme='light', link=None, max_rows=200000)` | 词云（HTML/CSS 渲染）：每个类目一个词，字号随数值变化，最多 30 个。 |

**`table`** — 表格（HTML 渲染）：明细表，或按 groupby 汇总后的汇总表。

```python
eazy_data_viz.table(df, columns=["月份", "大区", "销售额"], limit=10)
```

**`wordcloud`** — 词云（HTML/CSS 渲染）：每个类目一个词，字号随数值变化，最多 30 个。

```python
eazy_data_viz.wordcloud(df, names="城市", values="销售额", top_n=20)
```

### 其他

| 函数 | 签名 | 说明 |
|---|---|---|
| `area` | `area(data, x, y, color=None, **kwargs)` | 面积图 = ``line(..., area=True)``。 |

**`area`** — 面积图 = ``line(..., area=True)``。

```python
eazy_data_viz.area(df, x="月份", y="销售额")
```


## 5. 选图决策表

| 你想表达 | 用哪个 |
|---|---|
| 一个总数 + 同比 | `kpi` |
| 一组总数（4~8 个） | `group_kpi` |
| 完成率 / 目标达成 | `gauge` / `ring_progress` / `bullet` / `target` / `progress` |
| 随时间变化 | `line`（可 `area=True` / `step=True`） |
| 占比随时间变化 | `area_pct` / `bar_pct` / `theme_river` |
| 排名对比 | `bar`（`horizontal=True`） / `pareto` / `lollipop` |
| 两个时点变化 | `slope` / `dumbbell` |
| 排名随时间变化 | `bump` |
| 构成 / 占比 | `pie` / `rose` / `funnel` / `pyramid` |
| 层级构成 | `treemap` / `sunburst` / `tree` |
| 两变量关系 / 回归 | `scatter` / `trend` / `quadrant` |
| 分布 | `histogram` / `box` |
| 多变量对比 | `radar` / `parallel` / `heatmap` / `matrix` |
| 流转 / 关系 | `sankey` / `graph` |
| 项目排期 | `gantt`；股票走势 `candlestick` |
| 明细表 / 词云 | `table` / `wordcloud` |

## 6. KPI 卡片

```python
eazy_data_viz.kpi(df, value="销售额", label="全年销售额", delta=0.128, delta_label="同比",
         target=2000000, spark="销售额", spark_x="月份", hint="2024 全年 · 含税",
         link="g1").show()
```

| 参数 | 作用 |
|---|---|
| `data` / `value` / `agg` | 传 df + 列名（参与联动过滤）或直接传一个数字 |
| `label` / `hint` | 主标签 / 下方说明 |
| `fmt` / `unit` / `prefix` | 数值格式：compact/thousands/raw/percent/currency |
| `delta` / `delta_label` / `inverse` | 同比环比；`inverse=True` 时下降变绿（成本类指标） |
| `target` / `target_label` | 目标值 → 右上角徽标 + 达成率进度条 |
| `spark` / `spark_x` | 迷你走势线（按 spark_x 聚合 spark 列） |
| `accent` | 强调色序号（取当前配色的第 N 个颜色） |

## 7. 交互能力

- **下钻**：`drill=["大区","省份","城市"]`，点击柱子/扇区逐级钻取，面包屑可返回；JS 内完成，不回调 Python。
- **联动**：同一 dashboard 内 `link="g1"`，点击任意图的一个类目，其余同组图按该维度过滤，顶部出现筛选 chips，再点一次取消。
- **图例筛选 / 缩放 / 主题切换 / 导出 PNG**：ECharts 内置能力 + 右上角工具箱。
- **注意**：两个独立的 `components.html`（两个 iframe）之间无法联动，必须放在同一个 `dashboard` 页面里。

## 8. Streamlit

```python
import streamlit as st, eazy_data_viz
df = eazy_data_viz.sample_df()
charts = [eazy_data_viz.line(df, x='月份', y='销售额', link='g1'),
          eazy_data_viz.bar(df, x='大区', y='销售额', link='g1')]
page = eazy_data_viz.dashboard(*charts, cols=2, title='经营看板')
page.show()          # 内部调用 st.components.v1.html(..., height=page_height)
```

## 9. 文件结构 / spec 结构（需要深挖时看）

```
eazy_data_viz/
  __init__.py      # 对外 API
  chart.py         # 基础 13 种图 + _base_spec（组装 spec）
  charts_extra.py  # 32 种扩展图
  frame.py         # DataFrame → 紧凑记录（去重、采样、有序类目）
  render.py        # Material 3 页面/看板、CSS、脚本内联
  palette.py       # 7 套配色
  assets/eazy.js   # 运行时（聚合、option 构建、下钻/联动）
  assets/eazy_extra_*.js
```

页面 HTML 里 `window.EAZY_DATA` 存放去重后的数据（cols/rows/kinds/orders），
每张图只存 spec（type + roles + 样式），聚合在前端做——所以联动过滤是即时的、无需 Python 重算。

## 10. 常见错误对照

| 报错 | 原因 / 解决 |
|---|---|
| `列 'X' 需要是数值类型` | 该列是字符串但被当成数值角色（y/value/size）。改传数值列，或先 `df['X']=pd.to_numeric(...)` |
| `列 'X' 不存在` | 列名拼写/前后空格；用 `print(df.columns.tolist())` 核对 |
| `不支持的下钻层级` | drill 列表必须都出现在 DataFrame 里，且第一层通常等于 x |
| 图是空白 | 数值列里有大量 NaN 或全为 0；检查 `df[col].isna().mean()` |
| Streamlit 里图被裁掉 | 必须传 height（`.show()` 已自动算，手写 `components.html` 时要自己给） |
| 跨图不联动 | 两张图在同一个 `dashboard` 页面里且 `link` 相同 |

