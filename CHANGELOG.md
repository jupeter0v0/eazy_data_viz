# Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

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
