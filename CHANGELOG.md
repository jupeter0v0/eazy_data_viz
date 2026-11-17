# Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

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
