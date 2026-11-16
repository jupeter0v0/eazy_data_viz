# eazy_data_viz 扩展图表契约（Python ⇄ JS）

本文档是 `eazy_data_viz/charts_extra.py`（Python API）与 `eazy_data_viz/assets/eazy_extra_*.js`（前端 ECharts 构建器）
之间的唯一契约。两边必须严格按此实现，字段名不得改动。

---

## 0. 总体分工

- **Python**：只做「列名校验 + 角色声明 + 数据结构化」，把用户 DataFrame 转成 records，
  并生成 spec 里少量**只读元信息**（如 target 列名、link 的 source/target 列名）。
  **聚合（sum/mean/count…）一律在前端做**，这样联动过滤、下钻后能自动重算。
- **JS**：注册 `EazyViz.extraBuilders['<type>'] = function (spec, data, state, theme) { return optionObject; }`，
  用 `U = EazyViz.core.util` 里的工具从 `data.rows` 现算数据并返回 ECharts option。
- 每张新图都必须支持：`U.filteredRows(spec, data, state)` 过滤 + `U.groupBy` 聚合 + tooltip + 主题色。
- 图表类型名（`spec.type`，也是注册键）与 Python 函数名一致，例如 `waterfall` / `pareto`。

---

## 1. 可用的前端工具（`U = EazyViz.core.util`）

| 工具 | 说明 |
|---|---|
| `U.rowsOf(data)` | `[{列名: 值}]` 数组（已缓存，勿修改返回对象） |
| `U.hasCol(data, name)` | 列是否存在 |
| `U.filteredRows(spec, data, state)` | 应用 state.filters + state.drill 后的行 |
| `U.groupBy(rows, dims, measure, how)` | → `[{key, keys:[...], value, cnt}]`；how = sum/mean/count/max/min/median；dims 是列名数组 |
| `U.currentXDim(spec, state)` | 当前横轴维度（下钻后自动变） |
| `U.fmtValue(v, fmt)` / `U.fmtValue(v)` | 数值格式化（compact 万/亿、thousands、percent、currency） |
| `U.catName(v)` | 值 → 类目字符串（null → "—"） |
| `U.makeGrid(theme, {legend, zoom, rightExtra, top, bottom})` | grid 配置（返回对象，可直接用或改字段） |
| `U.makeLegend(theme, selected, show)` | 图例 |
| `U.makeToolbox(theme)` | 右上角「另存为图片」 |
| `U.makeCategoryAxis(spec, cats, theme)` | 类目轴（自动抽稀标签、轴名 `spec.xtitle`） |
| `U.makeValueAxis(spec, theme, lim)` | 数值轴（`lim` 例如 `spec.ylim`；轴名需另调用 `U.setAxisName`） |
| `U.setAxisName(axis, name, theme, isX, gap)` | 设置轴标题 |
| `U.axisTooltip(spec, theme, stacked)` / `U.tooltipBox(theme)` | tooltip 配置 |
| `U.catRanker(data, dim)` | 返回排序函数（尊重 pd.Categorical 顺序），无顺序时返回 null |
| `U.compareCatX(a, b)` | 类目比较函数（数字优先） |
| `U.THEME.light` / `U.THEME.dark` | 主题：`text/subtext/axis/split/border/bg/tooltipBg/tooltipBorder/palette[]/heat[]/primary/error/success/surface/surfaceVar/outline` |
| `U.emptyOption(theme)` | 无数据占位 option |
| `U.FONT` | 字体栈 |
| `U.dimItem(spec, name)` | 类目值 → `{name, value, itemStyle:{...}}`，用于给图形加数据项 |

HTML 类图表（不用 ECharts，直接返回 HTML 字符串）注册到：
```js
EazyViz.htmlBuilders['progress'] = function (spec, data, state, theme) { return '<div ...>'; };
```
注意：HTML 类里所有用户数据必须用 `U.esc()` 转义。

---

## 2. spec 通用字段（全部图表都有）

```json
{
  "id": "eazy-3", "type": "pareto", "title": "...", "subtitle": null,
  "theme": "light", "height": 380, "dataRef": "sha1",
  "roles": {"x": "月份", "y": "销售额", "color": "渠道", "names": null, "value": null, "y2": null, "target": null, "size": null},
  "agg": "sum", "fmt": "compact", "sort": "none", "topN": null,
  "xtitle": null, "ytitle": null, "xlim": null, "ylim": null,
  "legend": true, "labels": false, "zoom": false, "drill": null, "link": null,
  "... 各图自己的字段 ...": "..."
}
```
- `roles.x` / `roles.color` 等是**列名**；`data.cols` 里存的也是列名。
- 下钻：`spec.drill` 是维度列名数组，`state.drill = [{dim, value}, ...]`；
  `U.currentXDim(spec, state)` 已封装，直接用即可。
- 联动：点击图形时 `onChartClick` 会对 `p.name` 调 `setLink(spec.link, U.currentXDim(...), p.name, chart)`，
  所以**系列数据项的 `name` 必须等于当前横轴类目值**，否则联动会错。

---

## 3. 每个图表的字段与行为

> 约定：`records` 指 `data.rows` 的行对象；`agg` 默认 `spec.agg`；`fmt` 默认 `spec.fmt`。

### 3.1 `waterfall` 瀑布图（文件 A）
- Python: `waterfall(data, x, y=None, *, agg="sum", total=None, sort=None, ...)`；roles `{x, y}`；额外字段 `total: bool`（末尾加"合计"）。
- 行为：按 x 聚合出增量值 → 累加得到每一段的起点/终点 → 透明堆叠柱 + 可见柱；上涨用 palette[3]（红）不合适 →
  **上涨用 `theme.palette[1]`（绿 #188038），下降用 `theme.palette[3]`（红 #d93025），合计柱用 `theme.palette[0]`**。
- 标签：`spec.labels` 为真时在柱顶显示 `fmtValue(v)`；tooltip 显示「增量 / 累计」两项。
- 排序：`spec.sort` 为 `desc/asc` 时按增量值排序；为 `x` 时按类目顺序（用 `U.catRanker`）。
- 返回：`xAxis` 类目轴 + 数值轴 + 2 个 bar series（透明底、可见段，`stack:'wf'`）+ tooltip。

### 3.2 `bullet` 子弹图（文件 A）
- Python: `bullet(data, x, actual, target=None, *, agg="sum", ...)`；roles `{x, y=actual, target}`；
  若 `target` 为 None 则用 `spec.targetValue`（Python 传一个常数，字段 `targetValue`）。
- 行为：**横向** bar：每类一个"背景条"（灰色 `theme.surfaceVar`，宽度取 max(actual, target)）、
  一个实际值条（palette[0]，细）、一个目标刻度（用第三个 bar 系列宽度 2 的短竖条，或 scatter symbol 'rect'）。
  推荐实现：`yAxis` 类目（反向，第一项在顶部）+ `xAxis` 数值 + 3 个 `bar` 系列 `stack:'b'`：
  ① 透明 `[0,0]` 不用；简化做法：
  - series1 = 背景 bar（`itemStyle.color = theme.surfaceVar`，`barWidth` 大，`data = [[0, maxVal]]` 用数值轴两个值不支持）→
  **改用横向 bar 的 `data = [maxVal]` + `showBackground:true` + `backgroundStyle`**；
  - series2 = actual bar（`barWidth: 8`，`barGap:'-100%'`）；
  - series3 = target tick（`type:'scatter'`，`symbol:'rect'`，`symbolSize:[2,16]`，颜色 theme.text）。
- tooltip：实际 / 目标 / 达成率。

### 3.3 `lollipop` 棒棒糖图（文件 A）
- Python: `lollipop(data, x, y=None, *, agg="sum", sort=None, ...)`；roles `{x,y}`。
- 行为：每类一根细柱（`barWidth: 2`，颜色 palette[0]）+ 顶端散点（`symbolSize: 9`）；
  tooltip 显示值；`spec.labels` 时右侧显示数值。

### 3.4 `dumbbell` 哑铃图（文件 A）
- Python: `dumbbell(data, x, y1, y2, *, labels=None, agg="sum", sort=None, ...)`；
  roles `{x, y: y1, y2: y2}`；额外 `seriesNames: [y1名, y2名]`。
- 行为：每类一条连接线（`type:'line'` + `data:[[a,b]]` 不行）→ 用 **custom series** 或
  `series: bar(transparent stacked base) + bar(细差分) + scatter(a) + scatter(b)`。
  推荐：`bar` 透明底 `stack:'d'`，`bar` 差分 `barWidth:3, stack:'d'`，两个 scatter 端点。
- 图例显示两期名称；tooltip 显示两值 + 差值。

### 3.5 `pareto` 帕累托图（文件 A）
- Python: `pareto(data, x, y=None, *, agg="sum", top_n=None, ...)`；roles `{x,y}`；额外 `cumFmt`（默认 "percent"）。
- 行为：按值降序 → 柱 + 累计占比折线（`yAxisIndex:1`，右轴 0~100%，`fmt:"percent"`）；
  左轴数值；**累计线的数据项 name 同柱**；tooltip 显示 值 + 累计占比。

### 3.6 `slope` 斜率图（文件 A）
- Python: `slope(data, x, y, *, group=None, agg="sum", period=None, ...)`；
  roles `{x: 类目, y: 数值, color: 对比维度}`，额外 `seriesNames` 两期名称（来自 color 列的两个取值）。
  若 `group` 提供则 x=group 的分类，y 两列? —— **简化契约**：`slope(data, x, y, color)`，
  color 列必须恰好 2 个取值，Python 在 spec 写 `arms: [v1, v2]`。
- 行为：`xAxis` 为类目 `['期初','期末']`（或 spec.arms），每个 x 类目一条 line series（`data:[a,b]`），
  颜色 palette 轮转；tooltip 显示起止值和变化率。

### 3.7 `bump` 排名变化图（文件 A）
- Python: `bump(data, x, y, *, group, agg="sum", ...)`；roles `{x: 时间, y: 数值, color: group}`。
- 行为：按 x 分组 → 每个 (x, group) 聚合 → 每个 x 内按值排名 → 每个 group 一条 line（y 轴为排名，逆向）；
  `yAxis: {type:'value', inverse:true, min:1, max:组数}`；标签显示值；tooltip 显示值 + 排名。

### 3.8 `radar` 雷达图（文件 A）
- Python: `radar(data, x, y=None, *, color=None, agg="mean", max=None, ...)`；roles `{x,y,color}`。
- 行为：`radar.indicator` = 每个 x 类目（`max` 取 `spec.maxValue` 或各指标最大值上浮 10%）；
  每个 color 组一条 `radar` series（`data:[{name, value:[...]}]`）。

### 3.9 `rose` 南丁格尔玫瑰图（文件 A）
- Python: `rose(data, names, values=None, *, agg="sum", donut=False, ...)`；roles `{names, value}`。
- 行为：pie `roseType:'radius'`；图例；tooltip 值 + 占比；不用额外字段。

### 3.10 `parallel` 平行坐标（文件 A）
- Python: `parallel(data, dims, *, color=None, ...)`；`dims` 是数值列名列表 → spec `parallelDims`；
  roles `{color}`（可选，用于分组着色）。
- 行为：`parallelAxis` 每维一个（`name` 列名，`dim` 序号），`series:[{type:'parallel', data: rows.map(...)}]`，
  color 分组时用 `visualMap` 或 `lineStyle.color` 函数。

### 3.11 `pictorial` 象形柱图（文件 A）
- Python: `pictorial(data, x, y=None, *, symbol="circle", agg="sum", ...)`；roles `{x,y}`；额外 `symbol`。
- 行为：`type:'pictorialBar'`，`symbol: spec.symbol`（circle/rect/roundRect/diamond/triangle），
  `symbolRepeat:true`，`symbolSize` 随图高自适应，颜色 palette[0]，带数值标签。

### 3.12 `target` 目标对比图（文件 A）
- Python: `target(data, x, actual, target=None, *, agg="sum", ...)`；roles `{x,y:actual,target}`，额外 `targetValue`。
- 行为：柱（实际值）+ 目标线（`markLine` 逐项？）→ 用 line series 画目标值（`symbol:'none'`，虚线，颜色 theme.subtext），
  tooltip 实际 / 目标 / 达成率。

### 3.13 `trend` 趋势散点（文件 A）
- Python: `trend(data, x, y, *, color=None, ...)`；roles `{x,y,color}`；x/y 必须是数值列；
  Python 计算回归线并写 `fit: {slope, intercept, r2}`（用 numpy.polyfit）。
- 行为：散点 series + 回归线 `line`（数据用 `fit` 在 [minX,maxX] 两点算）；tooltip 显示点值；标题下方/图例带 R²。

### 3.14 `quadrant` 四象限散点（文件 A）
- Python: `quadrant(data, x, y, *, size=None, color=None, ...)`；roles `{x,y,size,color}`；额外 `xmid`/`ymid`（中位数）。
- 行为：`scatter` + `markLine` 两条中线（虚线，`theme.subtext`）+ 四角 `graphic` 文本（如「高值-高值」用 spec 的 `quadrantLabels`）。

### 3.15 `matrix` 相关系数矩阵（文件 A）
- Python: `matrix(data, columns=None, * )` → 计算 Pearson 相关 → spec `labels:[...]`, `values:[[r,...],...]`。
- 行为：heatmap（`xAxis`/`yAxis` 都是 labels，`data:[[i,j,v]]`）+ `visualMap`（`min:-1,max:1`，颜色 palette 两端），
  格子里显示两位小数（`labels` 默认开）；**不参与联动/过滤**（数据已预计算）。

### 3.16 `sparkline` 迷你走势（文件 A）
- Python: `sparkline(data, x, y, *, group, agg="sum")`；roles `{x,y,color:group}`。
- 行为：多个小图 grid 拼在一张 ECharts 里：每个 group 一个 grid + line series（无坐标轴、无 tooltip 轴）；
  左侧显示 group 名称（graphic text），右侧显示最新值。最多 12 个。

### 3.17 `ring_progress` 环形进度（文件 A）
- Python: `ring_progress(percent, *, label=None, max=100, ...)`（不接 df）；spec `percentValue`, `label`。
- 行为：`pie` 两个数据项（进度 / 余量），`startAngle:90`，`itemStyle.borderRadius: 50%`，
  中心 `graphic` 文本显示 `XX%`（用 spec.fmt）。

### 3.18 `sunburst` 旭日图（文件 B）
- Python: `sunburst(data, path, value=None, *, agg="sum", ...)`；roles `{path, value}`；path 是列名列表。
- 行为：用 `U.rowsOf` + `U.groupBy` 建树（参考 eazy.js 里 `buildTreemapTree` 思路，层级递归），
  `series:[{type:'sunburst', data: tree, radius:['12%','90%'], label:{...}}]`。

### 3.19 `tree` 树图（文件 B）
- Python: `tree(data, path, value=None, *, agg="sum", ...)`；roles 同上。
- 行为：建同样的树，`series:[{type:'tree', layout:'orthogonal', orient:'LR', data:[tree]}]`，`symbolSize` 按值。

### 3.20 `sankey` 桑基图（文件 B）
- Python: `sankey(data, source, target, value=None, *, agg="sum", ...)`；roles `{source, target, value}`。
- 行为：`series:[{type:'sankey', data: nodes, links: links}]`；节点名 = 列值，颜色按层轮转 palette。

### 3.21 `graph` 关系图（文件 B）
- Python: `graph(data, source, target, value=None, *, agg="sum", ...)`；roles 同 sankey。
- 行为：`force` 布局，节点大小按连接总值（`symbolSize`），边宽按值；`label.show:true`。

### 3.22 `theme_river` 主题河流图（文件 B）
- Python: `theme_river(data, x, color, value=None, *, agg="sum", ...)`；roles `{x, color, value}`。
- 行为：`series:[{type:'themeRiver', data:[[x, value, color], ...]}]`，`singleAxis` 为类目或时间轴。

### 3.23 `calendar` 日历热力图（文件 B）
- Python: `calendar(data, date, value=None, *, agg="sum", ...)`；roles `{x: date, value}`；日期列在 Python 侧转 `YYYY-MM-DD`。
- 行为：`calendar` 配置（`range: 年份`，`cellSize:['auto',14]`）+ `heatmap` series（`coordinateSystem:'calendar'`）+ `visualMap`。

### 3.24 `gantt` 甘特图（文件 B）
- Python: `gantt(data, task, start, end, *, color=None, ...)`；roles `{x: task, start, end, color}`。
- 行为：用 **custom series**（`renderItem` 画圆角矩形），x 轴为时间轴（`type:'time'`）；
  颜色按 color 分组；tooltip 显示起止。

### 3.25 `candlestick` K 线图（文件 B）
- Python: `candlestick(data, date, open, high, low, close)`；roles `{x:date, open, high, low, close}`；
  records 已按日期升序。
- 行为：`xAxis` 类目 + `series:[{type:'candlestick', data:[[open,close,low,high],...]}]`；
  `itemStyle: {color: theme.palette[3], color0: theme.palette[1], borderColor:...}`（中国习惯红涨绿跌）；
  可选 `zoom`。

### 3.26 `pyramid` 金字塔图（文件 B）
- Python: `pyramid(data, names, values=None, *, agg="sum", ...)`；roles `{names, value}`。
- 行为：漏斗图 `funnel` 的 `sort:'ascending'`（下宽上窄）+ `gap:2`；其余同 funnel。

### 3.27 `area_pct` / `bar_pct` 百分比堆叠（文件 B）
- Python: `area_pct(data, x, y, *, color, agg="sum", ...)` / `bar_pct(...)`；roles `{x,y,color}`；
  spec `percent: true`，`type` 分别为 `area_pct` / `bar_pct`。
- 行为：按 x 分组聚合后，把每个 x 的各类目值归一化为 100%，堆叠面积/柱；
  数值轴 `max:100`，`axisLabel` 显示 `%`；tooltip 显示百分比。

---

## 4. 文件与注册约定

- 文件 A：`eazy_data_viz/assets/eazy_extra_a.js`（本节 3.1–3.17 + HTML 类 progress/tile/table/wordcloud/group_kpi 由主控写）
- 文件 B：`eazy_data_viz/assets/eazy_extra_b.js`（本节 3.18–3.27）
- 每个文件结构：
```js
(function () {
  'use strict';
  if (typeof window === 'undefined' || !window.EazyViz) return;
  var EazyViz = window.EazyViz, U = EazyViz.core.util;
  var B = EazyViz.extraBuilders, H = EazyViz.htmlBuilders;
  B['waterfall'] = function (spec, data, state, theme) { ... };
  ...
})();
```
- 代码风格：ES5（`var` + `function`），不要用箭头函数/模板字符串（与现有 eazy.js 一致）。
- 中文注释；不要 `console.log`。
