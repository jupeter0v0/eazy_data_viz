# Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## 1.5.0 — 2026-11-21

### 看板自由排列：`layout` / `direction` / `grid`

`dashboard()` / `show()` / `streamlit_dashboard()` 新增三个参数，让看板不再只能是等宽网格：

- **按列/按行分配**：`direction="h"` 时 `layout=[1, 3]` 表示第一列 1 张、第二列 3 张；
  `direction="v"` 时按行算，`layout=[1, 2]` 是第一行 1 张、第二行 2 张。`sum(layout)` 必须 ≥ 图数。
- **格子占位**：`grid=(3, 3)` 先申请 3×3 网格，`layout` 换成每张图的 `[行, 列]` 占用，
  按从左到右、从上到下依次找第一个放得下的空位；`[[2, 2], [1, 1]]` 的第二张会落在 2×2 的右上角。
  尺寸超网格、位置放不下、占位声明数量与图数不一致都直接 `ValueError` 并说明原因。
- 新增 `eazy_data_viz/layout.py`：`parse_layout()` / `layout_height()` / `layout_summary()` 可在画图前自查排布结果。
- `page_height()` 按自由排列实际形状估算高度（Streamlit 不再裁剪）；模式 B 跨行卡片自动补足高度。
- **方方正正**：模式 B 会先算好每一行的高度（`layout.grid_row_heights()`，行高只增不减），
  再让每张卡正好吃满它占的格子，2×2 + 右侧两张 1×1 也能拼成严丝合缝的矩形，不会「左短右长」；
  模式 A 的各列底边同样对齐（每列取最高列的目标高，卡片按比例分摊剩余空间）。
- 自由排列目前与 `section` 分节互斥（显式报错），避免分区标题把网格切开。
- 新增教程 [15 · 自由排列](docs/guides/15-layout.md)。

### `abs_height`：绝对高度，框与框对齐

- 默认 `height` 只算图表正文，标题、副标题、联动工具条会把卡片额外撑高，
  同一行里「带长标题的图」和「带工具条的图」底边就对不齐。
- 所有图表（含 KPI、gauge、地图）新增 `abs_height=True`：此时 `height` 是**整个组件外框**的高度
  （内边距、标题、工具条都算在里面），正文用 flex 自适应剩余空间，框高严格等于 `height`。
- 例：`ev.bar(df, x="大区", y="销售额", height=320, abs_height=True)` 与
  `ev.pie(df, names="大区", values="销售额", height=320, abs_height=True)` 无论标题多长，卡片都是 320px 高。

### `table()`：`groupby` 汇总表（只影响显示，不影响联动数据）

- `table(data, groupby={"columns": ["大区"], "value": "销售额", "agg": "sum"})`：
  前端在 `filteredRows` 之后做 `groupBy`，所以**联动过滤会重算汇总，但后台明细行不变**，
  同页其它图仍拿到原始行。
- `columns` 与 `groupby` 互斥：要明细传 `columns`，要汇总传 `groupby`，同时传会报错。
  老写法 `table(df, columns=[...])` 行为不变。
- `agg` 支持 `sum / mean / count / max / min / median`；不给 `value` 时默认 `count`（按组计数）。
  未知键、`value` 与 `columns` 重叠、`agg` 拼错等都有明确中文提示。

### `sankey()`：`path=` 多级桑基

- `sankey(df, path=["大区", "渠道", "产品"], value="销售额")`：相邻两级自动成边，
  不再需要手工拼「A→B、B→C」两张表再合并。
- 节点名按层级编码（`层号 + 列值`），**不同层的同名值不会被合并**；label / tooltip 仍显示原始值。
- 点击回传真实「第几级维度 + 该级的值」：多级桑基与旭日图传给联动的维度一致，
  跨图联动不会再拿到一个不存在的列名。
- 两级旧写法 `sankey(df, source=..., target=...)` 保留；`path` 与 `source`/`target` 互斥。

### `bar()`：`yoy=True` 同比

- `bar(df, x="月份", y="销售额", color="年份", yoy=True)`：color 只有两个取值时，
  **值大的作为本期对比值小的**（2026 对 2025），在本期柱顶标注增长率、tooltip 追加同比行。
- 系列名都是数字时按数字大小定本期与上期，否则按系列合计大小判定；上期为 0 或空不计算。
- 取值多于两个不报错，退化为普通分组柱状图，并在 `chart.warnings["warnings"]` 里提示。
  `yoy=True` 但没传 `color` 会直接报错。

### 联动方向：双向 / 单向进 / 单向出

- `link` 支持三种写法：`link="g1"`（双向，默认）、`link=("g1", "out")`（单向出：只推不接）、
  `link=("g1", "in")`（单向进：只接不推），也接受 `{"group": "g1", "direction": "out"}`。
- 单向出被点击时只影响同组其它图、自己保持全量；单向进只接收，点击不会改变同组图表。
- 工具栏提示按方向区分（「单向出：点击图形联动到同组其他图表」等）；
  `EazyViz.onSelect` 回传的事件里带 `linkMode` / `canSend`。

### 修复：桑基图 / 旭日图 / 联动的传参

- 桑基图（含多级）与旭日图点击时按节点真实层级回传维度列与列值；连线/边点击不再误触发联动。
- 旭日图节点自带 `nodeDim` / `nodeLayer` / `nodeValue`：点开一层（`nodeClick: 'rootToNode'`）后
  图表根节点会变、`treePathInfo` 变短，之前的实现照路径长度推维度会推错，现在不再受影响。
- 旭日图标签改为「环内 + 外层切向 + 占比过小不画」：文字不再被挤到环外糊成一团，外圈沿弧线排列，
  最外环占比 < 3.5%、倒数第二环 < 3%、更内层 < 1.5% 不画名字（悬停仍看得到）；
  环半径按层级均分，`path` 给到 4、5 级也不会画到画布外。
- `_NUMERIC_ROLE_KEYS` 补上 `sankey` / `sunburst` / `tree` / `graph` / `theme_river` / `table` 的
  `value` 角色，这几类图的 `value` 列不再被当作维度处理（`sum` / `mean` 等聚合恢复正常）。
- 联动只作用于同名列：目标图没有该列时不会写入无效筛选（行为保持，补测试覆盖）。

### 文档

- 新增 [15 · 自由排列](docs/guides/15-layout.md)；[06 · 交互与联动](docs/guides/06-interaction.md) 增加 2.4 联动方向；
  `docs/api/` 的 `bar` / `table` / `sankey` 补全新参数与示例，全部图表补 `abs_height` 参数说明，
  公共参数表补 `linkMode`、`yoy`、`groupby`、`abs_height`。

## 1.1.0 — 2026-11-16

### Streamlit：迁移到 `st.components.v2`

`st.components.v1.html` 已官宣 2026-06-01 后移除，本版把 Streamlit 渲染层换成 v2，
并保留旧版自动回退。

- 新增 `edv.streamlit_dashboard(charts, ..., on_select=...)`：一行渲染看板，
  无 iframe、高度按内容自适应、**点击图表可把事件回传给 Python**（`result.select`）。
- `Chart.show()` / `Dashboard.show()` / `edv.set_palette()` 在 Streamlit 中自动优先 v2，
  检测不到 v2 时自动回退 `components.v1.html`（行为与 1.0.x 一致）。
- 运行时 `eazy.js` 支持作用域化：查询与事件监听都收敛到组件根节点（Shadow DOM），
  多个看板可共存于同一页面而互不干扰；新增 `EazyViz.onSelect` 钩子。
- 新增 `edv.streamlit_available()` 检测当前环境是否支持 v2。
- Streamlit 画廊新增「v2 双向事件」页；文档 §9 重写，`docs/guides/07-streamlit.md` 增补 v2 用法。

## 1.0.0 — 2026-11-16

首个对外版本，项目正式命名为 **eazy_data_viz**（此前内部名 `pviz`）。

### 图表

- **48 种图表类型、49 个图表函数**（含 3 种地图），覆盖驾驶舱所需的指标、趋势、对比、结构、分布、关系、明细、地理：
  - 基础：`bar` `line` `area` `pie` `scatter` `histogram` `heatmap` `box` `funnel`
    `treemap` `gauge` `kpi` `combo`
  - 指标：`group_kpi` `ring_progress` `progress` `bullet` `target` `tile` `pictorial`
  - 对比：`waterfall` `pareto` `lollipop` `dumbbell` `slope` `bump` `radar` `parallel`
    `bar_pct` `area_pct`
  - 结构：`rose` `pyramid` `sunburst` `tree` `theme_river`
  - 分布/关系：`quadrant` `matrix` `sparkline` `trend` `sankey` `graph`
  - 时间/明细：`calendar` `gantt` `candlestick` `table` `wordcloud`
- **地图**：`geo_map`（区域填色）、`map_bubble`（气泡）、`map_flow`（飞线）；
  内置中国与**世界地图** GeoJSON（本地文件、离线可用、不依赖 CDN）、725 条城市名与坐标映射；
  `region` 支持「广东 / 广东省」「广州 / 广州市」两种写法，城市值可自动聚合到省份。
- 所有图表共用同一套公共参数：`title` / `subtitle` / `xtitle` / `ytitle` /
  `xlim` / `ylim` / `fmt` / `height` / `theme` / `legend` / `labels` / `zoom` /
  `palette` / `drill` / `link` / `section`。

### 交互（全部在浏览器内完成，不触发 Python 重算）

- 下钻：`drill=["大区", "省份", "城市"]`，面包屑可逐级返回。
- 联动：多图同一个 `link`，点击交叉筛选；KPI 卡随筛选实时重算。
- 图例点选过滤、数据缩放、tooltip、PNG 导出、深浅色主题、一键重置联动。

### KPI 卡片

- 目标徽标 + 达成率进度条、迷你走势线、同比/环比（`inverse=True` 支持反向指标）、
  单位/前缀/口径提示、可参与联动重算、卡片高度可调。

### 配色

- 7 套配色库：`google`（默认，Material 3）/ `antd` / `tableau` / `carbon` /
  `echarts` / `morandi` / `tailwind`，深浅主题自动适配。
- 三种切换方式：`set_palette()` 全局、`Chart.palette()` 单图、`dashboard(palette=)` 整页；
  页面顶栏下拉框可在运行时实时换肤。

### 视觉

- 全站 Material Design 3：Roboto/Google Sans、Google Blue `#1a73e8`、
  卡片 12px 圆角 + elevation、MD3 chips 与按钮、sticky 顶栏。

### 数据规模

- `max_rows` 默认 **200000 行**（超出才自动均匀采样；5 万~20 万行看板可整表传入），
  传 `max_rows=None` 完全不采样。单文件 HTML 约每万行 0.5MB（200k × 6 列 ≈ 10MB）。

### 文档与用例

- `docs/api/<函数>.md`：**每个图表函数一篇**，含完整签名、参数总览、逐个参数详解
  （类型 / 默认值 / 取值建议 / 示例 / 真实报错）、返回值与 `chart.spec` 片段、可运行示例、常见错误。
- `examples/charts/*.py`：每个函数一个可运行脚本（输出到 `examples/output/`）。
- `docs/guides/`：安装、快速上手、驾驶舱教程、KPI、配色、交互、Streamlit、静态导出、地图等教程。

### 画廊（`gallery.html`）

- 68 张卡片 / 48 种图表 / 9 个分区（含地图可视化）；**每张卡片右上角「代码」可展开
  生成该图的完整 Python 代码，并支持一键复制**。
- 配套 Streamlit 版画廊：9 个页面 + 侧栏主题/行数/配色切换。

### 给 AI 的文档

- `docs/AI_GUIDE.md`：使用规则、选图决策表、函数签名 + 可运行示例、错误对照。
- `docs/eazy_catalog.json`：机器可读目录（49 个图表条目的签名/参数/示例）。
- 由 `tools/gen_ai_doc.py` 从 `inspect.signature` 生成，所有示例纳入测试。

### 工程

- 单文件 HTML：ECharts 5.5 与运行时内联，离线可用，数据按 ref 去重只嵌一次。
- Python 只做校验与角色识别，聚合在前端按当前筛选状态实时计算。
- 测试：Python 30 项、前端 71 项（headless Chrome 内断言）。
- 支持 Python 3.8 / 3.12 / 3.14（含 pandas 3.x、streamlit 1.67）。
