# 已知限制与行为差异（Known Issues）

这份文档记录 **当前版本已确认、但尚未修改** 的行为差异，以及各图表的「参数生效范围」。
写作原则：**宁可写清楚限制，也不假装参数一定生效。** 每条都给出规避方式。

> 版本：1.0.0 · 最后更新：2026-11-16
> 文中 `spec` 指图表对象内部的 `chart.spec`（调试时可用 `chart.spec` 查看）。

---

## 1. 已修复（保留记录）

| 问题 | 版本 | 处理 |
| --- | --- | --- |
| `examples/charts/calendar.py` 与标准库 `calendar` 同名，导致该目录下所有示例脚本在 `import pandas` 阶段崩溃 | 1.0.0 | 文件已更名为 `calendar_chart.py`；脚本内保留 `sys.path` 兼容垫片 |
| `geo_map` 的数值列是文本时静默出空图 | 1.0.0 | 三个地图函数统一走 `_coerce_numeric()`：纯数字文本自动转换，转不了抛中文 `TypeError` |
| 区域名没匹配上地图时只在浏览器 console 报警 | 1.0.0 | 改为同时写入 `chart.warnings`（`geo_map`/`map_bubble`/`map_flow`） |
| `吉林市` 被 `normalize_region` 剥成 `吉林` 而命中吉林省中心 | 1.0.0 | 前端 `resolveAny` 对带「市/地区/盟/自治州/自治县/旗」后缀的名字优先查城市表 |
| `group_kpi` 的 `delta=0.12` 显示成 `0.1%`（KPI 卡是 `12.0%`） | 1.0.0 | 统一按小数比例渲染，`delta` 语义与 `kpi()` 一致 |
| `radar` 不传 `y` 时渲染空白 | 1.0.0 | 自动退化为「按 `x` 计数」（`agg="count"`，序列名「记录数」） |
| `pareto(cum_fmt="cn")` 报错文案错写成 `fmt=` | 1.0.0 | 改为 `ValueError('cum_fmt 只支持 "percent" / "raw" / "compact"，收到 …')` |
| `target_value` 传非数字字符串被静默忽略 | 1.0.0 | `bullet`/`target` 统一经 `_num_param()` 校验并抛中文 `ValueError` |
| `max_rows=100.5 / "abc" / -1` 抛原始异常 | 1.0.0 | `_frame.prepare()` 统一校验：非整数抛 `TypeError`，`<1` 抛 `ValueError`，`None` 表示不采样 |
| `height=None` 时所有图都落到 380 | 1.0.0 | 按图表类型取默认高度（`_HEIGHT_DEFAULTS`，如 `gauge=260`、`bump=420`） |

---

## 2. 参数生效范围（重要）

公共参数里有几个是「**部分图表生效**」的，调用前请先看下表。
（`✓` 生效 · `△` 部分生效 · `—` 不生效但仍会被接受）

| 图表 | `top_n` | `sort` | `zoom` | `labels` | `xlim/ylim` | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| `bar` `line` `area` `combo` `histogram` `heatmap` | ✓ | ✓ | ✓ | ✓ | ✓ | 完整支持 |
| `pie` `funnel` `treemap` | ✓ | ✓ | — | ✓ | — | 饼类无坐标轴 |
| `scatter` | △ | — | ✓ | △ | ✓ | `top_n` 只保留前 N 行数据 |
| `waterfall` | — | △ | — | ✓ | △ | `xlim` 对类目轴无意义；`legend` 恒不显示 |
| `bullet` `lollipop` | — | ✓ | — | △ | △ | `bullet` 无 `labels`；`lollipop` 标签只标数值 |
| `dumbbell` `slope` `target` `pareto` | — | △ | — | ✓ | △ | `xlim` 作用在数值轴，类目轴请用 `top_n + sort` |
| `bump` | — | ✓ | — | ✓ | △ | `ytitle` 只用于 tooltip |
| `pictorial` | △ | ✓ | — | ✓ | △ | `top_n`/`zoom` 只写 spec 不参与渲染 |
| `tile` `progress` | △ | ✓ | — | — | — | `tile` 的 `sort/top_n` 只写 spec；均为 HTML 组件 |
| `group_kpi` | ✓ | ✓ | — | — | — | `sort` 在 Python 侧排序后传入；`height` 由卡片布局接管 |
| `area_pct` `bar_pct` | △ | ✓ | — | △ | — | `ylim` 被固定为 0–100%，`xlim/labels/zoom` 不生效 |
| `parallel` | — | — | — | △ | — | `agg` 固定 `sum`（每行是原始记录），轴标题不生效 |
| `radar` | — | ✓ | — | ✓ | — | 维度轴范围由 `max` 控制 |
| `sparkline` | — | △ | — | — | — | 最多画 12 个分组，第 13 个起静默丢弃 |
| `matrix` `calendar` `theme_river` `gantt` `sankey` `graph` `sunburst` `tree` `funnel` `wordcloud` `table` | — | △ | — | △ | — | 见下一节逐条说明 |

**通用建议**：拿不准时用 `chart.spec` 检查参数是否真的写进去了；如果某个参数只写进 `spec` 却没渲染，以本表为准。

---

## 3. 逐图限制

### 3.1 结构与层级

- **`rose`**：`drill` 是「筛选式下钻」而非层级重构——点击扇区后面包屑和其他联动图表按当前层过滤，
  但玫瑰图本身始终按 `names` 聚合，不会切换成下一层维度。需要真正的层级下钻请用 `sunburst`/`tree`。
  （1.0.0 起 `drill[0]` 会自动补成 `names` 列，避免点第一层时过滤为空图。）
- **`sunburst` / `tree`**：标签恒定显示，超过 4 层没有半径/高度配置，窄扇区/深树会重叠。
- **`sankey` / `graph`**：`value <= 0` 的边与自环会被静默丢弃；全部被丢弃时返回空图。
  Sankey 中间节点的「关联总量」会被重复计数，看流量占比时请以源侧数值为准。
- **`graph`**：力导向布局每次渲染位置不同，截图不可复现；需要固定版式请导出后手动摆放。
- **`matrix`**：单元格显示 2 位小数，而 `spec.values` 保留 4 位；`fmt` 参数暂不生效。
  `spec.labels` 在 `matrix` 里存的是列名数组（与其它图的布尔 `labels` 不同义）。

### 3.2 时间与明细

- **`gantt`**：`end < start` 的行会在 JS 端自动交换（Python 会在 `chart.warnings` 里提示行数）。
- **`calendar`**：只画有数据的日期，缺失日期留白；不能作为联动源（点击不派发筛选）。
- **`table`**：
  - 时间列截断到 16 字符（秒/时区会丢）；
  - `limit` 与 `max_rows` 双重限制，页面上最多 200 行；
  - `fmt="compact"` 会被改成千分位显示。
- **`wordcloud`**：始终按词频降序，`fmt` 不生效，`value <= 0` 的词被丢弃。

### 3.3 交互与联动

- **HTML 组件类**（`kpi` `group_kpi` `progress` `tile` `table` `wordcloud`）是纯 HTML，
  **不能作为联动/下钻的来源**（点了没有筛选事件）；但可以作为**接收端**随其它图表联动变化
  （`kpi` 已支持：带 `link` 时数值会随过滤重算）。
- **`calendar` / `matrix`** 不能作为联动源；`sankey`/`graph` 的汇侧节点、`sunburst`/`tree` 的深层节点、
  按 x 数值匹配的散点，联动命中率较低。
- 联动只在**同一个 `dashboard()` 页面**内有效；多个 `st.components.v1.html` 是独立 iframe，无法互联。

### 3.4 数据与环境

- `max_rows` 默认 **200000**；超出会均匀采样并写入 `chart.warnings`。`max_rows=None` 表示不采样。
  体积参考：约 **每万行 ≈ 0.5MB** HTML（200k × 6 列 ≈ 10MB，首次打开需要几秒）。
- 页面是单文件：ECharts 与运行时全部内联，离线可用；因此每个 HTML 至少约 1.2MB。
- 浏览器端聚合发生在当前筛选状态下，所以联动/下钻后数值会自动重算；
  **不要在 Python 里先聚合再期望联动**（那样只会联动到聚合后的结果）。

---

## 4. 如何反馈

发现新的不一致，或希望上面某条变成「已支持」：

1. 用 `chart.spec` 确认参数确实写入了；
2. 提供最小复现（DataFrame 几行数据 + 一行调用）；
3. 提交到仓库 Issues，标题格式建议：`[chart] rose: drill 未切换层级`。

我们优先修「参数写了没效果」这类误导性问题（P1），其次是渲染异常（P2）。
