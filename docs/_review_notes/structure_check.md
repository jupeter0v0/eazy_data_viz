# 结构一致性检查：16 个「结构 / 分布 / 关系 / 时间 / 明细」图表

> 检查对象：`rose`、`pyramid`、`sunburst`、`tree`、`theme_river`、`quadrant`、`matrix`、`sparkline`、`trend`、`sankey`、`graph`、`calendar`、`gantt`、`candlestick`、`table`、`wordcloud`
> 检查范围：Python 实现 `eazy_data_viz/charts_extra.py`、JS builder `eazy_data_viz/assets/eazy_extra_a.js` / `eazy_extra_b.js` / `eazy_extra_html.js`、核心 `eazy.js`，以及 `docs/api/*.md` 与 `examples/charts/*.py`。
> 结论：**16/16 文档参数与 `inspect.signature` 完全一致、无缺漏**；**16/16 示例脚本实跑通过**；静态核对出 **56 个“签名接受但 JS builder 从不读取”的参数**、**7 个 JS 支持但 Python 不暴露的 spec 字段**、若干渲染与联动缺陷（详见下文）。本检查**只记录问题，未修改任何源码**。

## 1. 检查方法与证据

1. **签名基线**：对 16 个函数逐个执行 `inspect.signature(edv.<fn>)`，以运行时签名为唯一事实来源；`docs/api/<fn>.md` 的「函数签名 / 参数总览 / 参数详解」均由同一份签名生成，故参数名、顺序、默认值、keyword-only 位置天然一致。
2. **文档覆盖校验**：脚本比对「签名参数名 ⊆ 参数详解 `### \`名\`` 标题 ⊆ 参数总览表行」，并检查 7 个必需章节、示例数 ≥6、每例 `**输出**：` 与 `.save("examples/output/...")`。
3. **“是否真的生效”静态扫描**：按 builder 注册行切分 `eazy_extra_a.js` / `eazy_extra_b.js` 中各函数函数体，正则收集 `spec.<key>` 读取（`spec.labels` 等），再与 Python 签名交叉比对；JS 未读取 = 该参数只写入 spec，不改变渲染。
4. **联动/下钻链路核对**：读 `eazy.js` 的 `currentXDim()`（`eazy.js:249`）、`filteredRows()`（`eazy.js:276`）、`onChartClick()`（`eazy.js:1475`）、`setLink()`（`eazy.js:1508`），确认点击能否产生 `p.name` 与联动维度。
5. **运行验证**：在仓库根目录逐个执行 16 个示例脚本，记录 exit code 与产物大小；本次全部 `exit=0`、每个 HTML ≥ 1.2 MB。

复现命令（仓库根目录）：

```bash
PYTHONPATH=. PYTHONIOENCODING=utf-8 python - <<'EOF'
import inspect, eazy_data_viz as edv
for fn in ("rose pyramid sunburst tree theme_river quadrant matrix sparkline trend "
           "sankey graph calendar gantt candlestick table wordcloud").split():
    print(fn, list(inspect.signature(getattr(edv, fn)).parameters))
EOF
```

## 2. 逐函数对照总表

参数数 = `inspect.signature` 参数个数（含 `data`）；文档覆盖全部通过。builder 行号指 JS 中 `B['<name>'] = function ...` 的注册行。

| 函数 | Python 实现 | 签名参数 | 文档覆盖 | JS builder | 签名接受但 JS 不读取（不生效） | 其它问题 |
| --- | --- | --- | --- | --- | --- | --- |
| `rose` | `charts_extra.py:920` | 22 | 22/22 | `eazy_extra_a.js:595` | `xtitle`、`xlim`、`ylim`、`zoom` | `drill` 只是逐级筛选，扇区维度不切换（见 §4.3） |
| `pyramid` | `charts_extra.py:2088` | 16 | 16/16 | `eazy_extra_b.js:946` | `sort`、`top_n`、`legend`、`zoom` | 永远按 value 降序 + funnel 升序布局，`sort="asc"` 默认值有误导性 |
| `sunburst` | `charts_extra.py:1556` | 18 | 18/18 | `eazy_extra_b.js:204` | `sort`、`top_n`、`labels`、`legend`、`zoom`、`xtitle`、`ytitle` | 标签恒显示；环半径固定 4 层 |
| `tree` | `charts_extra.py:1621` | 18 | 18/18 | `eazy_extra_b.js:256` | `sort`、`top_n`、`labels`、`legend`、`zoom`、`xtitle`、`ytitle` | 标签恒显示；默认只展开 3 层 |
| `theme_river` | `charts_extra.py:1810` | 17 | 17/17 | `eazy_extra_b.js:524` | `legend`、`labels`、`zoom`、`top_n` | 图例恒显示；JS 读取的 `xtitle/ytitle/ylim` 无 Python 参数（见 §4.2） |
| `quadrant` | `charts_extra.py:1290` | 20 | 20/20 | `eazy_extra_a.js:962` | `labels`、`zoom` | 无 `agg/sort/top_n`；`link` 维度是 x 列（见 §4.3） |
| `matrix` | `charts_extra.py:1383` | 8 | 8/8 | `eazy_extra_a.js:1075` | `fmt` | 单元格文本固定 2 位小数，`spec.values` 4 位；无坐标轴标题参数；不能作联动源 |
| `sparkline` | `charts_extra.py:1451` | 11 | 11/11 | `eazy_extra_a.js:1141` | 无（全部生效） | 最多画 12 组，超出静默丢弃；无 `link/drill` |
| `trend` | `charts_extra.py:1201` | 18 | 18/18 | `eazy_extra_a.js:873` | `labels`、`zoom` | 回归线只有一条（不按 `color` 分组分别拟合）；R² 是右上角 graphic 文本 |
| `sankey` | `charts_extra.py:1684` | 17 | 17/17 | `eazy_extra_b.js:333` | `labels`、`legend`、`sort`、`top_n`、`zoom` | 标签恒显示；value≤0 的自环/负值静默丢弃 |
| `graph` | `charts_extra.py:1747` | 17 | 17/17 | `eazy_extra_b.js:415` | `labels`、`legend`、`sort`、`top_n`、`zoom` | 力导向布局每次刷新位置不同；同上丢弃规则 |
| `calendar` | `charts_extra.py:1874` | 16 | 16/16 | `eazy_extra_b.js:603` | `sort`、`top_n`、`labels`、`legend`、`zoom` | `currentXDim=null`，不能作联动源；visualMap 用实际 min/max |
| `gantt` | `charts_extra.py:1934` | 18 | 18/18 | `eazy_extra_b.js:690` | `agg`、`sort`、`top_n`、`zoom`、`fmt` | JS 读取的 `xtitle/ytitle` 无 Python 参数；end<start 被 JS 静默交换 |
| `candlestick` | `charts_extra.py:2010` | 20 | 20/20 | `eazy_extra_b.js:858` | `labels`、`legend`、`xlim` | `xlim` 无效（类目轴）；红涨绿跌不可配；缺 OHLC 的行跳过 |
| `table` | `charts_extra.py:2407` | 10 | 10/10 | `eazy_extra_html.js:112` | 无（全部生效） | `limit`/`max_rows` 双 200 上限；时间截断到 16 字符；不能作联动源 |
| `wordcloud` | `charts_extra.py:2470` | 13 | 13/13 | `eazy_extra_html.js:147` | `sort`、`fmt` | 永远按 value 降序；value≤0 丢弃；不能作联动源 |

合计：签名参数 **259** 个（含跨函数重复），文档逐参数覆盖 **259/259**；静态确认不生效 **56** 个。

## 3. 逐函数详情与证据

### 3.1 `rose` — 玫瑰图（`eazy_extra_a.js:595`）
- **生效**：`names`、`values`（→ `roles.names` / `roles.value`）、`agg`、`sort`（仅 `asc` 升序，其余一律降序）、`top_n`（尾部合并为「其他」）、`labels`、`legend`、`donut`、`fmt`、`ytitle`（tooltip 数值标题）、`height`、`title/subtitle`、`theme`、`link`、`drill`。
- **不生效**：`xtitle`、`xlim`、`ylim`、`zoom` —— builder 只读 `spec.ytitle`（`eazy_extra_a.js:595-660` 中无 `spec.xtitle/xlim/ylim/zoom`）。
- **`drill` 语义偏差**：`_base_spec` 在 `roles.x is None` 时把 `roles.x = drill[0]`（`chart.py:211` 附近），且 `roles._extra = drill`；但 rose builder 始终 `groupBy(rows, [roles.names])`，点击只会经 `filteredRows` 过滤行（`eazy.js:276`），**不会切换到下一层维度重新分组**。若 `drill[0]` 与 `names` 不是同一列，`currentXDim` 与扇区名对不上，点击后过滤为空图。
- **「其他」扇区不可点**：`onChartClick` 对 `p.name === '其他'` 直接 return（`eazy.js:1481`）。
- 文档已按上述行为写明：`xtitle/xlim/ylim/zoom` 一节给出“参数被接受但不改变画面”的说明，示例中未把它们当作有效功能使用。

### 3.2 `pyramid` — 金字塔图（`eazy_extra_b.js:946`）
- **生效**：`names`、`values`、`agg`、`fmt`、`labels`、`title/subtitle`、`height`、`theme`、`link`（维度 = `roles.names`）。
- **不生效**：`sort`（Python 默认 `"asc"`，builder 永远 `items.sort(desc)` 后按 funnel `sort:'ascending'` 画，视觉固定“下宽上窄”）、`top_n`、`legend`（funnel 无图例）、`zoom`。
- **渲染**：`minSize:'18%'`、`maxSize:'100%'`，小占比类目仍占 18% 最小高度；标签仅名称不带数值（`show: spec.labels !== false`），数值只在 tooltip。
- 文档把 `sort` 的默认值原样列出，并在参数详解中说明“实际渲染顺序固定为降序”。

### 3.3 `sunburst` — 旭日图（`eazy_extra_b.js:204`）
- **生效**：`path`、`value`、`agg`、`fmt`、`title/subtitle`、`height`、`theme`、`link`（维度 = `path[min(drillDepth, len-1)]`，通常 `path[0]`）。
- **不生效**：`sort`（ECharts 配置 `sort: null`）、`top_n`、`labels`（label 恒显示，`fontSize:11`）、`legend`、`zoom`、`xtitle`、`ytitle`。
- **渲染限制**：`levels` 只配置了 4 层半径（12%/42%/72%/90%），`path` 超过 4 层时更深层退回 ECharts 默认样式；窄扇区标签会重叠。
- **联动**：只有第 0 层节点点击后过滤有意义（`currentXDim=path[0]`）；点深层节点会用深层名称去过滤 `path[0]` 列，通常得到空结果。

### 3.4 `tree` — 树图（`eazy_extra_b.js:256`）
- **生效**：`path`、`value`、`agg`、`fmt`、`title/subtitle`、`height`、`theme`、`link`（同 sunburst）。
- **不生效**：`sort`、`top_n`、`labels`（label 恒显示：内部节点在左、叶子在右）、`legend`、`zoom`。
- **渲染限制**：`roam:true` 可原生拖拽/缩放（`zoom` 参数无效）；`initialTreeDepth: min(path长度, 3)`，超过 3 层默认折叠；右侧预留 140px 给叶子标签，超长名称会溢出/截断依赖浏览器。
- **`xtitle`/`ytitle`**：签名有，但 JS 完全未读取（`eazy_extra_b.js:256-332` 无对应 `spec.` 读取）。

### 3.5 `theme_river` — 主题河流图（`eazy_extra_b.js:524`）
- **生效**：`x`、`color`、`value`、`agg`、`sort`（`'x'/'asc'/'desc'`，或横轴像日期时自动排序）、`fmt`、`title/subtitle`、`height`、`theme`、`link`（维度 = `roles.x`）。
- **不生效**：`legend`（`U.makeLegend(..., true)` 恒显示）、`labels`、`zoom`、`top_n`（色带数量不被裁剪）。
- **字段名不一致（未暴露）**：JS 读取 `spec.xtitle`、`spec.ytitle`、`spec.ylim`（`eazy_extra_b.js:524-602`），但 Python 签名里**没有**这三个参数，`_ext` 也不会写入 → 这三个能力只能改 JS 才能用。
- **实现与命名不符**：注释已说明“ECharts themeRiver 组件需要真实 time 轴，月份/类目会空白”，实际用 `line + stack:'river' + smooth + areaStyle` 手绘，属已知取舍；负值被 JS 截断为 0。
- **渲染**：横轴是 category 轴。用 `x="日期"`（1500 个不同日期）时刻度极密，示例已提示“适合看整体趋势”。

### 3.6 `quadrant` — 四象限散点（`eazy_extra_a.js:962`）
- **生效**：`x`、`y`、`size`、`color`、`quad_labels`（`spec.quadrantLabels`，四角文本）、`xtitle/ytitle`、`xlim/ylim`、`fmt`、`legend`（仅 `color` 时出现）、`title/subtitle`、`height`、`theme`、`link`。
- **不生效**：`labels`、`zoom`（builder 无 `spec.labels/spec.zoom` 读取；散点本身无“数据标签”能力）。
- **`quad_labels` 顺序**：`["高值·高值","低值·高值","低值·低值","高值·低值"]` 对应 **左上、右上、左下、右下**（`eazy_extra_a.js` 四角 graphic 的排布），文档已明确写出，避免用户按“顺时针”误解。
- **联动**：`currentXDim = roles.x`，而点击散点的 `p.name = catName(x 值)`（`n: U.catName(r[xcol])`）→ 联动按 **x 列的原始数值字符串精确匹配行**；浮点值经 `catName` 格式化后可能与原值不一致，匹配不到时会表现为“点了没反应/表格空”。文档按“按 x 值过滤”描述，未夸大为类目联动。
- **`agg` 不存在**：签名无此参数，调用会 `TypeError`；示例已避免。

### 3.7 `matrix` — 相关系数矩阵（`eazy_extra_a.js:1075`）
- **生效**：`data`、`columns`、`max_cols`、`title/subtitle`、`height`、`theme`。Python 端完成 Pearson 相关与 4 位小数舍入，JS 只画 `spec.labels` + `spec.values`。
- **不生效**：`fmt`（单元格文本固定 `toFixed(2)`、tooltip 固定 `toFixed(2)`、visualMap 固定 `toFixed(1)`，均不读 `spec.fmt`）。
- **字段名不一致（同名不同义）**：`matrix` 的 `spec.labels` 是**标签字符串数组**（不是其他图里的布尔“显示标签”开关），JS 用 `spec.labels !== false` 判断，数组永远为真 → 单元格数值恒定显示，无法关闭。
- **未暴露字段**：JS 支持 `spec.xtitle` / `spec.ytitle`（`U.setAxisName(..., 30/12)`），但 Python 签名没有这两个参数，轴标题恒为空。
- **渲染**：`visualMap` 固定 `min:-1, max:1`、竖向右侧；配色 `[palette[3], bg, palette[0]]`；单元格文本 2 位小数与 `spec.values` 的 4 位精度不一致（复制 `chart.spec["values"]` 得到的数字比图上更细）。
- **联动**：`currentXDim = null`（`eazy.js:267`），点击无法联动/下钻；`link` 参数不存在。

### 3.8 `sparkline` — 迷你走势（`eazy_extra_a.js:1141`）
- **生效**：`x`、`y`、`group`（→ `roles.color`）、`agg`、`fmt`、`title/subtitle`、`height`、`theme`、`max_rows`。
- **全部签名参数均生效**；但注意：
  - JS 有 `spec.series / spec.sparkData` 预计算分支（`eazy_extra_a.js:1141-1249`），**Python 从不写入**这两个字段（`docs/EXTRA_CHARTS.md` 3.16 的“Python 预计算 series”描述与代码不符），永远走回退聚合。
  - 最多 12 组：`if (groups.length > 12) groups = groups.slice(0, 12);`（`eazy_extra_a.js:1195`）→ 第 13 个及以后的分组静默丢弃，无警告。
  - 横轴顺序取“首次出现顺序”，Python 不写 `spec.sort`（签名里也没有 `sort`）→ 想按时间顺序请先 `df.sort_values()` 或把 x 设为有序分类。
  - 无 `link/drill` 参数；`currentXDim` 虽是 `roles.x`，但没有联动入口。

### 3.9 `trend` — 趋势回归（`eazy_extra_a.js:873`）
- **生效**：`x`、`y`、`color`、`xtitle/ytitle`、`xlim/ylim`、`fmt`、`legend`（仅 `color` 时）、`title/subtitle`、`height`、`theme`、`link`（同 quadrant 的 x 数值匹配）。
- **不生效**：`labels`、`zoom`（builder 无读取）。
- **回归线**：Python 在 `spec.fit` 中写入 `{slope, intercept, r2, xmin, xmax}`（`charts_extra.py:1201` 起）；JS 用 `fit.slope/intercept` 画**唯一一条**虚线，**不按 `color` 分组分别拟合**——`color` 只影响散点着色。R² 显示为右上角 graphic 文本 `"R² = <3位小数>"`（不是副标题），`r2` 为 `None`（x 全等/ss_tot≤0）时不显示。
- **边界**：有效点 <2 时 Python 直接 `ValueError: trend 需要至少 2 个有效的 (x, y) 数值点才能拟合回归线。`；x 全等时 JS 把 `[minX, maxX]` 各扩 0.5 以画出垂直线段的近似直线。

### 3.10 `sankey` — 桑基图（`eazy_extra_b.js:333`）
- **生效**：`source`、`target`、`value`（→ `roles.source/target/value`）、`agg`、`fmt`、`title/subtitle`、`height`、`theme`、`link`（维度 = `roles.source`）、`max_rows`。
- **不生效**：`labels`（节点 label 恒显示）、`legend`（桑基无图例）、`sort`、`top_n`、`zoom`。
- **静默丢弃**：`!isFinite(v) || v <= 0 || s === t` 的边被跳过（负值、0、自环），无警告；全部被丢弃时返回空图（`U.emptyOption`）。
- **数值处理**：边值 `Math.round(v*1000)/1000`（3 位小数）；节点对象不带 `value`，由 ECharts 从边推导；内部节点 tooltip“关联总量”把流入+流出相加，**中间节点会被重复计数**（不是净流量）。
- **联动**：点节点 `p.name` = 节点名，`currentXDim = roles.source`；点**源侧**节点可过滤出以它为 source 的行，点**汇侧**节点按 source 列匹配通常为空。文档将此写为“按 source 列过滤”。

### 3.11 `graph` — 关系图（`eazy_extra_b.js:415`）
- **生效**：`source`、`target`、`value`、`agg`、`fmt`、`title/subtitle`、`height`、`theme`、`link`（维度 = `roles.source`）、`max_rows`。
- **不生效**：`labels`（节点 label 恒显示在右侧）、`legend`、`sort`、`top_n`、`zoom`。
- **渲染**：`layout:'force'`，`repulsion:230`、`edgeLength:[50,140]`、`gravity:0.1`；**每次打开页面节点位置不同**（力导向无固定初始坐标），做截图对比时需注意。
- **节点/边尺寸**：节点 `symbolSize = 10 + 26*sqrt((total-tmin)/span)`（全部相等时 18）；边宽 `round((1+4*sqrt(v/maxLink))*10)/10`，边值同样 3 位小数、非正/自环丢弃。
- **联动**：同 sankey。

### 3.12 `calendar` — 日历热力图（`eazy_extra_b.js:603`）
- **生效**：`date`、`value`、`agg`、`fmt`、`title/subtitle`、`height`、`theme`、`max_rows`。
- **不生效**：`sort`（JS 自己对日期排序，`compareCatX`）、`top_n`、`labels`、`legend`、`zoom`。
- **渲染**：`cellSize:['auto',14]`（格高固定 14px，`height` 太小会挤压）；year range 为单年字符串或 `[y0-01-01, y1-12-31]`；`visualMap` 用**实际数据 min/max**（不是 0 起点）→ 只有一天或数据极均匀时颜色对比很弱；tooltip 用 `fmt` 格式化数值。
- **不能作联动源**：`currentXDim = null`（`eazy.js:267`）；即便有 `link` 参数，点击也不会触发 `setLink`。但仍可作为**被过滤方**接收其他图的联动。

### 3.13 `gantt` — 甘特图（`eazy_extra_b.js:690`）
- **生效**：`task`、`start`、`end`、`color`、`labels`（条宽 ≥26px 时在条内写任务名）、`legend`（仅 `color` 时）、`title/subtitle`、`height`、`theme`、`link`（维度 = `roles.x` 即 task）、`max_rows`。
- **不生效**：`agg`、`sort`、`top_n`、`zoom`、`fmt`（tooltip 只用 `fmtDay` 与“工期 N 天”，不读 `spec.fmt`）。
- **未暴露字段**：JS 支持 `spec.xtitle` / `spec.ytitle`（横/纵轴名，缺省回退到 start 列名 / task 列名），但 Python 签名没有这两个参数。
- **end < start**：Python 端追加 warning `gantt 有 N 行结束日期早于开始日期，这些条会显示异常，建议先清洗数据。`，但 JS 会**静默交换** start/end（`eazy_extra_b.js` 内 `if (end < start) swap`）→ warning 文案（“显示异常”）与实际行为（自动纠正）不完全一致。
- **聚合**：同一 task 多行时取 `start=min`、`end=max`，任务按开始时间升序、y 轴 inverse 使最早任务在最上方。
- **xlim/ylim**：签名没有这两个参数，文档未列为可用参数。

### 3.14 `candlestick` — K 线图（`eazy_extra_b.js:858`）
- **生效**：`date`、`open/high/low/close`、`xtitle`（横轴名）、`ytitle`（纵轴名）、`ylim`、`fmt`（tooltip 数值）、`zoom`、`title/subtitle`、`height`、`theme`、`link`（维度 = `roles.x` 日期）。
- **不生效**：`labels`、`legend`（K 线无图例/标签）、`xlim`（横轴是类目轴，xlim 不参与）。
- **颜色不可配**：固定 `color: palette[3]`（涨红）、`color0: palette[1]`（跌绿），中国习惯；换配色库只改色值不改红涨绿跌语义。
- **数据清洗**：Python 按日期 `mergesort` 排序；任一行 OHLC 有非数值/缺失则整行跳过（`U.num` 判空）。`zoom='auto'`：蜡烛 >30 根时出现底部 `dataZoom`（inside+slider），初始窗口保留最后约 60 根。
- **`agg` 不存在**：OHLC 由数据给出，不聚合；示例中的边界演示已修正为仅用真实存在的参数。

### 3.15 `table` — 明细表（`eazy_extra_html.js:112`）
- **生效**：`columns`（默认前 12 列）、`limit`、`fmt`、`title/subtitle`、`height`、`theme`、`link`（只能作为**被过滤方**）、`max_rows`。
- **双重 200 上限**：Python `show_limit = min(limit, 200)` 写入 `spec.limit`；同时 `embed_rows = min(max_rows, 200)`（默认 `max_rows=200`）→ 即使 `limit=999`，页面上最多也只有 200 行，且 JS 再取 `min(spec.limit, 500)`。控制台会提示采样 warning。
- **时间显示**：时间单元格 `String(catName(...)).slice(0, 16)`，即 `YYYY-MM-DD HH:MM`，**秒与时区被截掉**。
- **数值格式**：`spec.fmt === 'compact'` 时单元格改用 `thousands`（千分位），其余沿用 `fmt`；`raw/percent/currency` 与 tooltip 一致。
- **不能作联动源**：HTML 类 builder 不注册 ECharts `click`，点击无事件（工具栏也不显示联动提示），只能接收其他图的过滤。

### 3.16 `wordcloud` — 词云（`eazy_extra_html.js:147`）
- **生效**：`names`（默认 `_pick_dim`：首个分类列，否则首个时间列）、`values`、`agg`、`top_n`（默认 30）、`title/subtitle`、`height`、`theme`、`link`（只能作为被过滤方）、`max_rows`。
- **不生效**：`sort`（JS 永远按聚合值降序）、`fmt`（词云不显示数字）。
- **边界**：`value <= 0` 的词被过滤；字号 `13 + round(t*17)px`（最小 13px）、透明度 `0.72 + t*0.28`；无数据时显示占位文案“当前条件下没有数据”。
- **不能作联动源**：同 table（纯 HTML 渲染）。

## 4. 跨函数共性问题

### 4.1 `section` / `palette` 不是这 16 个函数的参数
- `section` 只存在于基础图表（如 `bar/line/pie` 等）的签名与 `spec["section"]`；`render.build_page` 只在页面卡片前插入 `<div class="eazy-section">`。本组 16 个函数**没有** `section` 参数，文档已明确说明，示例也未使用。
- `palette` 同样不是函数参数；配色只能通过链式方法 `chart.palette("antd")`（或全局 `edv.set_palette`）设置，写入 `spec["palette"]`。16 篇文档均在返回值/注意事项里给出该用法。

### 4.2 JS 支持但 Python 未暴露的 spec 字段（7 个）
| spec 字段 | JS 位置 | 本应出现的函数 | 后果 |
| --- | --- | --- | --- |
| `spec.xtitle` | `eazy_extra_b.js:524-602`（theme_river） | `theme_river` | 无法设置横轴标题 |
| `spec.ytitle` | 同上 | `theme_river` | 无法设置纵轴标题 |
| `spec.ylim` | 同上 | `theme_river` | 无法限制纵轴范围（当前固定从 0 起） |
| `spec.xtitle` | `eazy_extra_b.js:690-857`（gantt） | `gantt` | 轴标题只能用默认列名 |
| `spec.ytitle` | 同上 | `gantt` | 同上 |
| `spec.xtitle` | `eazy_extra_a.js:1075`（matrix） | `matrix` | 轴标题恒空 |
| `spec.ytitle` | 同上 | `matrix` | 轴标题恒空 |

另有 `sparkline` 的 `spec.series` / `spec.sparkData`（`eazy_extra_a.js:1141`）：JS 有预计算分支，Python 从不写入，永远走回退聚合；`docs/EXTRA_CHARTS.md` 3.16 声称“Python 预计算 series”，与实现不符。

### 4.3 联动 / 下钻（`link`、`drill`）的适用边界
- 联动的前提是 `currentXDim(spec, state)` 非空且点击事件带 `p.name`（`eazy.js:1475-1481`）。逐个函数：
  - **可作联动源**：`pyramid`（维度 names）、`theme_river`（x）、`gantt`（task）、`candlestick`（date）、`rose`（仅当给出 `drill` 使 `roles.x` 存在）、`sunburst`/`tree`（维度 `path[min(depth,last)]`，深层点击通常匹配不到）、`sankey`/`graph`（维度 source，点源侧节点才有意义）、`quadrant`/`trend`（维度 x，按 x 数值字符串精确匹配）。
  - **不能作联动源**：`calendar`、`matrix`（`currentXDim=null`）；`table`、`wordcloud`（HTML 类无 click 事件）。
- **`drill` 只有 `rose` 一个函数支持**，且不是“切换下钻维度”，而是“把点击值作为筛选条件叠加”：扇区仍按 `roles.names` 分组，只是数据被 `filteredRows` 过滤。`drill[0]` 必须与 `names` 同列，否则点击后过滤为空；「其他」扇区点击被忽略。
- 联动高亮：`rose`/散点类会通过 `U.sourceSelection` 把非选中的数据项降低透明度（`opacity 0.3 / 0.84`），其余图表只是过滤行。

### 4.4 默认值与文档一致性
- 16 篇文档的签名与默认值从运行时 `inspect.signature` 生成，与源码逐字一致（含 `max_rows=200000`；`table` 例外为 `max_rows=200`）。
- 但“默认值存在”不等于“默认行为直观”，以下默认值有误导性，文档已在参数详解中补充实际行为：
  - `pyramid.sort='asc'`：默认值存在，JS 从不读取，视觉顺序固定。
  - `theme_river.legend=True`：JS 恒显示图例，传 `False` 也无法隐藏。
  - `quadrant/trend/gantt.legend=None`：`None` 是“按是否传 color 自动决定”的哨兵值，非布尔；文档已写清。
  - `calendar.sort='x'`：JS 自己排序，该参数不影响结果。
  - `table.limit=100`：真实上限还受 `max_rows=200` 与 `min(limit,200)` 双重截断。
  - `sunburst/tree.labels` 默认 `True` 但传 `False` 也无效（builder 恒显示标签）。

### 4.5 契约文档 `docs/EXTRA_CHARTS.md` 与实现漂移（只记录，未改文档）
- 3.16 称 Python 预计算 `spec.series`（sparkline）：实现未写入。
- 3.22 称主题河流使用 ECharts `themeRiver` 组件：实际为 `line + stack + areaStyle` 手绘。
- 若干 builder 细节（`other` 合并、`levels` 固定 4 层、`max_rows=200000` 默认值等）未在契约文档更新。`docs/api/*.md` 以源码为准，不受该漂移影响。

### 4.6 示例目录的模块遮蔽问题（运行阻塞，已绕过）
- `examples/charts/calendar.py` 与标准库 `calendar` 同名。以 `python examples/charts/<fn>.py` 方式运行时 `sys.path[0]` 就是 `examples/charts`，`import pandas` 链路里的 `_strptime` 执行 `import calendar` 会命中本目录的示例脚本，导致**该目录下所有脚本**在导入 pandas 阶段崩溃：
  `AttributeError: module 'calendar' has no attribute 'day_abbr'`（`_strptime.py:83`）。
- 本任务的 16 个示例脚本统一在 `import pandas` 之前加了 `sys.path` 清理 shim（把脚本自身目录移除），因此在仓库根目录按验收命令可直接运行；**该问题与具体函数无关，同目录其他示例脚本若未加 shim 同样会失败**。
- 建议（不在本任务修改范围）：把 `calendar.py` 改名/移出该目录，或统一用 `python -m examples.charts.<fn>` 启动（此时 `sys.path[0]` 是仓库根目录，标准库优先）。本检查未改任何源码与脚本。

## 5. 文档与示例验收结果

- **文档**：16/16 存在；每篇均含「函数签名 / 参数总览 / 参数详解 / 返回值 / 完整示例 / 常见问题 / 相关图表」7 节；参数详解标题与签名参数 **259/259 一一对应、无遗漏无多余**；每篇示例 7~10 个（均 ≥6），每个示例都有 `.save("examples/output/...")` 与 `**输出**：` 说明；常见错误均给出真实异常文本（已实测的 `ValueError/TypeError/KeyError`）。
- **示例**：16/16 脚本 `exit=0` 并打印 `OK <fn>`；共生成 150+ 个 HTML，按函数抽检最小文件 **≥ 1233 KB**（inline ECharts 保证 >100KB）。
- **参数总数**：16 函数合计 259 个签名参数（跨函数重复计），其中静态确认 **203 个真正影响渲染**、**56 个被签名接受但 JS 从不读取**（清单见 §2 总表）；另有 **7 个 JS 能力没有 Python 入口**（§4.2）。

## 6. 问题清单汇总（按严重度）

| 级别 | 问题 | 涉及函数 | 证据 |
| --- | --- | --- | --- |
| P0（运行阻塞） | 示例目录 `calendar.py` 遮蔽标准库，导致同目录脚本全部无法导入 pandas | 运行环境（所有示例） | `_strptime.py:83` 报错；已用 sys.path shim 绕过 |
| P1（功能误导） | 签名接受但 JS 不读取的参数共 56 个，静默无效 | 除 `sparkline`、`table` 外全部 | §2 总表「不生效」列 |
| P1（功能误导） | `rose.drill` 是逐级筛选而非维度下钻；`drill[0]` 与 `names` 不同列时点击后为空图 | `rose` | `eazy_extra_a.js:595` 始终按 roles.names 分组；`eazy.js:1475` |
| P1（功能误导） | JS 支持的 `xtitle/ytitle/ylim` 无 Python 参数，无法设置主题河流/甘特/矩阵轴标题 | `theme_river`、`gantt`、`matrix` | §4.2 |
| P2（渲染异常） | `sunburst/tree` 标签恒显示、超过 4 层无半径配置；窄扇区/深树标签重叠 | `sunburst`、`tree` | `eazy_extra_b.js:204/256` |
| P2（渲染异常） | `sparkline` 第 13 个分组起静默丢弃，无警告 | `sparkline` | `eazy_extra_a.js:1195` |
| P2（渲染异常） | `graph` 力导向布局每次刷新位置不同，截图不可复现 | `graph` | `layout:'force'`，无固定坐标 |
| P2（数据口径） | `sankey`/`graph` 静默丢弃 value≤0、自环；sankey 中间节点“关联总量”重复计数 | `sankey`、`graph` | `eazy_extra_b.js:333/415` |
| P2（数据口径） | `gantt` Python warning 说“显示异常”，JS 实际静默交换 end/start，二者不一致 | `gantt` | `charts_extra.py:1934`；`eazy_extra_b.js:690` |
| P2（数据口径） | `table` 时间截断到 16 字符（丢秒/时区）、`limit` 与 `max_rows` 双 200 上限、`compact` 被改成 `thousands` | `table` | `eazy_extra_html.js:112` |
| P2（数据口径） | `wordcloud` 永远降序、`fmt` 无效、value≤0 词静默丢弃 | `wordcloud` | `eazy_extra_html.js:147` |
| P3（精度/展示） | `matrix` 单元格 2 位小数 vs `spec.values` 4 位小数；`fmt` 无效；`spec.labels` 同名不同义（数组 vs 布尔） | `matrix` | `eazy_extra_a.js:1075` |
| P3（联动限制） | `calendar`/`matrix` 不能作联动源；`table`/`wordcloud` 纯 HTML 不能作联动源；深层 `sunburst/tree`、汇侧 `sankey/graph`、散点按 x 数值匹配的联动命中率低 | 多函数 | `eazy.js:249/1475` |
| P3（契约漂移） | `docs/EXTRA_CHARTS.md` 与实现不一致（sparkline 预计算、themeRiver 组件等） | 契约文档 | 见 §4.5 |

## 7. 声明

- 本次检查**未修改** `eazy_data_viz/**` 任何 Python/JS 资源、`README.md`、其他 docs、tests，也未执行 `git commit`。
- 写入范围仅限本任务约定的 16 个 `docs/api/*.md`、16 个 `examples/charts/*.py` 与本文件。
- 文档中所有“不生效/边界/联动”描述均以上述源码行号为证据；示例脚本已全部实跑验证。
