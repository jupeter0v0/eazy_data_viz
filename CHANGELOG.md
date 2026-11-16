# Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## 1.0.0 — 2026-11-16

首个对外版本，项目正式命名为 **eazy_data_viz**（此前内部名 `pviz`）。

### 图表

- 45 种图表类型、46 个图表函数，覆盖驾驶舱所需的指标、趋势、对比、结构、分布、关系、明细：
  - 基础：`bar` `line` `area` `pie` `scatter` `histogram` `heatmap` `box` `funnel`
    `treemap` `gauge` `kpi` `combo`
  - 指标：`group_kpi` `ring_progress` `progress` `bullet` `target` `tile` `pictorial`
  - 对比：`waterfall` `pareto` `lollipop` `dumbbell` `slope` `bump` `radar` `parallel`
    `bar_pct` `area_pct`
  - 结构：`rose` `pyramid` `sunburst` `tree` `theme_river`
  - 分布/关系：`quadrant` `matrix` `sparkline` `trend` `sankey` `graph`
  - 时间/明细：`calendar` `gantt` `candlestick` `table` `wordcloud`
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

### 画廊（`gallery.html`）

- 64 张卡片 / 45 种图表 / 8 个分区；**每张卡片右上角「代码」可展开生成该图的完整
  Python 代码，并支持一键复制**。
- 配套 Streamlit 版画廊：8 个页面 + 侧栏主题/行数/配色切换。

### 给 AI 的文档

- `docs/AI_GUIDE.md`：使用规则、选图决策表、函数签名 + 可运行示例、错误对照。
- `docs/eazy_catalog.json`：机器可读目录（46 个图表条目的签名/参数/示例）。
- 由 `tools/gen_ai_doc.py` 从 `inspect.signature` 生成，所有示例纳入测试。

### 工程

- 单文件 HTML：ECharts 5.5 与运行时内联，离线可用，数据按 ref 去重只嵌一次。
- Python 只做校验与角色识别，聚合在前端按当前筛选状态实时计算。
- 测试：Python 28 项、前端 54+5 项（headless Chrome 内断言）。
- 支持 Python 3.8 / 3.12 / 3.14（含 pandas 3.x、streamlit 1.67）。
