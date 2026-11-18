# Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## 1.3.2 — 2026-11-18

### Streamlit 多组件页面：面包屑 / 返回 / 联动 chip 不刷新

- 现象：一个页面里挂多个 `streamlit_dashboard()` 时（例如 KPI + 图表 + 明细表），点图下钻后
  数据确实变了，但图表顶部的面包屑一直停在「全部」、不出现「返回」按钮、联动 chip 也不更新；
  单文件 `to_html()` 导出没有这个问题。
- 原因：`EazyViz.scope` 只指向**最后挂载**的组件（components v2 各自一个 ShadowRoot），
  `renderToolbar()` / `syncFilterBar()` 用 `findOne()` 在 scope 里找
  `[data-eazy-toolbar]` / `#eazy-filters`，找的是别的组件，自然找不到就直接返回了。
- 修复：新增 `rootOfChart(c)` / `chartRoots()`，工具条按图形自己的根节点（`c.el.getRootNode()`）
  查找；筛选条改为遍历页面上所有看板根节点各刷新一遍。
- 顺带：`syncFilterBar()` 在没有联动时也会把各看板的筛选条正确隐藏。

## 1.3.1 — 2026-11-18

### 下钻 / 联动交互修复

- **下钻层级显示不准（少一级）**：下钻判定条件用了 `drill.length < drill.length - 1`，
  导致最后一级维度永远无法下钻、层级显示少一级。改为 `< drill.length`，现在可下钻到最末级。
- **顶栏面包屑改为「维度:值」并置于图表顶部**：每一级显示为 `地区:北京`、`渠道:超市`，
  完整呈现 `全部 › 地区:北京 › 渠道:超市`；点击任意一级即回到该层级。
- **「返回」按钮失效 / 回退多级**：Streamlit 组件在同一 ShadowRoot 上重复 `init()` 会重复
  绑定全局点击监听，一次返回被处理多次。现在每个挂载点只绑定一次（`__eazyGlobalBound` 守卫），
  返回稳定只回退一级。
- **下钻 + 联动的图回退后残留旧条件**：`handleCrumb` / `handleBack` 只在回到顶层时清理联动，
  部分回退时仍残留更深一层条件。新增 `applyDrillLink` / `afterDrillChange`，让本图发出的联动
  始终等于「当前最深一级的下钻条件」，回退时同步更新。
- **一页多个看板时点错图**：各看板 chart index 都从 0 开始，新增 `chartFor(el, idx)` 按被点击
  看板的根节点定位图表，面包屑 / 返回不再指向另一块看板。

## 1.3.0 — 2026-11-17

### Streamlit v2：默认不再因点击图表而 rerun

- **行为变更**：`streamlit_dashboard()` / `.show()` 只有在显式传入 `on_select` 时，才把
  图表点击通过 components v2 的 trigger 回传 Python；不传时前端 `EazyViz.onSelect`
  为 `null`，点击、联动、下钻、图例开关全部在浏览器内完成，**脚本 0 次 rerun**，
  此时返回值的 `select` 恒为 `None`。
- 需要「点图 → Python 重算」时传 `on_select`（点击触发一次 rerun）；既要回调又不想
  整页重跑时，把看板包进 `@st.fragment`。
- 兼容性：旧代码若依赖「不传 `on_select` 也能读到 `result.select`」，
  需显式传 `on_select`。
- 元件数据里新增 `trigger` 开关；`eazy_data_viz/streamlit_v2.py` 的前端模板
  按它决定是否挂 `setTriggerValue`。

### Streamlit v2：补齐地图脚本，地图不再报「不支持的图表类型」

- v2 的脚本清单原来是手写的，漏了 `eazy_map.js`，`geo_map` / 省份地图在 v2 下会报
  `不支持的图表类型: geo_map` 并且整块看板只画出前两张图。现在 `_sources()` 直接
  按 `render.ALL_JS` 取资源，v1 / v2 用同一份清单，以后新增脚本不会再漏。

### 图表排版：图例不再压字、不再被截断

- 图例改按内容排：项目少时（1–2 行放得下）用自动换行，项目多时用分页，并给图例
  写死宽度（`width: 92%`），修掉「最后一项被卡片边缘截断成 `1/2`」的问题。
- `grid.top` 按图例实际行数下推（`46 + 行数 × 20`），图例不再压住纵轴名。
- 横向条形图的类目在 Y 轴上，强制不旋转（原来会按文字长度斜 30°）。
- 图例字号 11 → 10、间距 12 → 8，6 个大区 / 5 条产品线这种常见分组可以排在一行。
- 跨年的月度时间轴（例如 17 个月）把「2025年3月」拆成两行「2025年 / 3月」，
  抽稀到 6 个标签，并把 x 轴名与 grid 底部一起下让，不再互相重叠、不压轴名。

### 一个页面挂多个看板时，联动 / 下钻不生效

- 每个 `streamlit_dashboard()` 都是一个 components v2 实例，它们共享 `window.EazyViz`，
  而 `EazyViz.init()` 本来每次都会把 `charts` / `links` 清空：前一个看板的图就从注册表
  里消失了，点柱子时只剩最后一个看板会重绘，联动 / 下钻看起来「没反应」。
  现在 init 只剔除已从 DOM 上摘掉的图（rerun 换 innerHTML），并按挂载点作用域查找
  `data-chart` 对应的图，同一页面上的几个看板能各自联动、互不串号。

### 新增「重置下钻」按钮：下钻之后一定回得去

- 顶栏新增 `重置下钻`（`data-eazy-reset-drill` / `EazyViz.resetDrill(el)`）：所有图的下钻
  层级一次清空、回到第一层，并顺手清掉「下钻那次点击」产生的联动。
- 修掉一个真回不去的情况：图同时有 `drill` 和 `link` 时，点柱子既下钻又 `setLink`，
  这条联动会反过来过滤源图自己；点「全部」面包屑只清了 drill，图仍被自己的联动过滤，
  只剩一根柱子。现在清下钻时连带 `sourceId` 是自己的联动组一起删。
- 顶栏渲染条件放宽：1.3.0 起只要页面里有 `link` 或 `drill` 就渲染顶栏（没有标题时是
  紧凑工具条，只有按钮），不再要求 `title=` / `desc=`，否则没有标题的看板连回退入口都没有。

### 新增示例：销售经营分析看板

- `examples/streamlit_sales_demo/`：把「全是主键」的 ERP 销售明细翻译成可读中文名，
  做出一套完整看板（KPI、趋势、堆叠下钻、中国地图、TOP 客户、回款双轴、订单类型、
  中国式报表），附 `prepare_data.py` 与数据说明。

## 1.2.0 — 2026-11-17

### 中文本地化：数字单位、日期轴、中国式报表表格

- 新增 `Chart.unit(unit)`：给整张图统一数值单位，接受 `"千"` / `"万"` / `"百万"` / `"亿"`，
  或等价的 `1e3` / `1e4` / `1e6` / `1e8`（也接受 `"1e6"` 这类字符串）。坐标轴刻度、tooltip、
  数据标签、饼图/漏斗/仪表盘/KPI 与明细表统一按「值 ÷ 倍数」展示，最多 2 位小数；
  `fmt` 为 `raw` / `percent` / `thousands` / `currency` 时以 `fmt` 为准（表格的 `thousands`
  例外，仍按单位换算）。
- `table()` 新增 4 个中国式报表参数（参考 FineReport 明细表、观远 BI 表格）：
  `total` 表尾合计行（只统计 `limit` 内实际渲染的行）、`index` 序号列（横向滚动固定）、
  `bar` 单元格数据条（`True` / 列名 / 多列）、`stripe` 斑马纹（默认开启，旧图外观会略有变化）。
- 日期类目轴自动中文化：`2024-03-01` → `3月1日`，跨年补年份 → `2024年3月1日`，
  `2024-03` → `3月`，带时间保留 `09:30`；支持 `-` / `/` 分隔与 `HH:MM[:SS]`。
  只改坐标轴显示，tooltip、导出与下钻仍用原始日期。

### Streamlit v2：rerun 后图表状态保留

- 修复 v2 每次 rerun 时图表 id 漂移（自增计数器）导致整个看板 HTML 被重挂、
  联动筛选条 / 下钻 / 图例状态被清零的问题：id 改为按位置固定（`eazy-0`、`eazy-1`…），
  rerun 后状态保留。
- 注意：v2 点击图表仍会触发一次脚本 rerun（事件回传 Python 的机制不变）；需要零 rerun
  请用 v1（`st.components.v1.html`）或 `@st.fragment`，详见 `docs/guides/07-streamlit.md`。

### 文档

- 新增 `docs/guides/15-cn-conventions.md`：中文单位、日期轴、中国式报表表格。
- `docs/guides/07-streamlit.md` 新增「点击图表会不会 rerun？」小节。
- `docs/api/table.md` 补齐 `total` / `index` / `bar` / `stripe` 四个参数与示例 6。

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
