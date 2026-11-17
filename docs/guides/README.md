# 教程目录

从安装到扩展的 15 篇教程，按编号顺序读即可；已会 pandas 的可以直接跳到 09。

| 编号 | 标题 | 学完能做什么 |
| --- | --- | --- |
| 01 | [安装与环境矩阵](01-installation.md) | 在 Python 3.8–3.14 / pandas 1.3–3.x 上装好本库，确认 Streamlit、Notebook 附加依赖，跑通第一张图 |
| 02 | [五分钟上手](02-quickstart.md) | 掌握「DataFrame + 列名」的调用方式，理解 `Chart` 的 `to_html()` / `save()` / `show()`，独立画出 3–5 张图 |
| 03 | [从零搭一个经营驾驶舱](03-cockpit-tutorial.md) | 用 KPI + 趋势 + 结构 + 明细拼出可交付驾驶舱，会用 `dashboard()`、`cols`、`section`、`link` |
| 04 | [KPI 卡片全参数详解](04-kpi-cards.md) | 把 `kpi` / `group_kpi` / `gauge` / `ring_progress` / `progress` 的同比、目标、迷你走势、联动全部用对 |
| 05 | [配色与主题](05-palette-and-theme.md) | 7 套配色与深浅主题的选择、单图覆盖与整页覆盖，知道品牌色怎么换 |
| 06 | [交互总览：下钻、联动、缩放与导出](06-interaction.md) | 配置 `drill` 逐级下钻、`link` 多图联动、`zoom` 缩放、图例过滤与工具箱导出 PNG，理解前端交互不触发 Python 重算 |
| 07 | [Streamlit 集成](07-streamlit.md) | 把看板嵌入 Streamlit：`components.html` 高度、缓存、多图与联动、部署注意事项 |
| 08 | [静态 HTML 与导出](08-static-html-and-export.md) | 生成单文件离线 HTML、外链资产模式、批量导出与体积控制，交给业务方直接打开 |
| 09 | [数据准备](09-data-preparation.md) | 列类型、缺失值、重复值、日期、分类顺序、长宽表、派生列、`max_rows` 采样、多图复用同一份 `df` 全部处理好 |
| 10 | [选图决策指南](10-chart-selection.md) | 按「要回答的问题」在 49 个图表函数里做选择，避开饼图切太碎、折线画无序类目等常见误用 |
| 11 | [常用配方（Cookbook）](11-cookbook.md) | 20 个拿来即用的配方：Top N、同环比、目标达成、瀑布、帕累托、四象限、下钻、地图、明细导出等 |
| 12 | [常见问题与错误对照](12-troubleshooting.md) | 按「现象 → 原因 → 解决」定位乱码、空白图、类型报错、Streamlit 裁剪、地图不匹配、体积过大等问题 |
| 13 | [性能与体积](13-performance.md) | 用实测数据估算 HTML 体积与首屏耗时，会采样、预聚合、数据去重和 iframe 数量控制 |
| 14 | [扩展图表](14-extend-charts.md) | 从 Python 函数到 JS builder 新增一种图表，并补齐测试、API 文档、示例与 gallery 卡片 |
| 地图 | [地图图表完全指南](map.md) | 三张地图（`geo_map` / `map_bubble` / `map_flow`）的选型、区域名匹配、下钻联动与体积控制 |

## 推荐阅读路径

| 你的情况 | 建议顺序 |
| --- | --- |
| 第一次用，想先看到图 | 01 → 02 → 10（选图） |
| 要给老板做经营驾驶舱 | 02 → 03 → 04 → 05 → 06 → 11 |
| 手上数据很脏 | 09 → 10 → 12 |
| 要嵌到 Streamlit / 部署 | 02 → 07 → 08 → 13 |
| 遇到报错或图不对 | 12 → 09 |
| 要加一种新图表 | 02 → 14 → `docs/EXTRA_CHARTS.md` |

## 教程约定

* 所有代码都在仓库根目录直接运行：`import eazy_data_viz as edv`、`df = edv.sample_df()`。
* 需要写文件时统一写到 `examples/output/`（已在 `.gitignore` 中）。
* 文中代码已逐块执行验证；输出示例可能因机器与版本略有差异。
* 函数名、参数与默认值的权威来源是 [API 索引](../api/README.md) 与 [`docs/eazy_catalog.json`](../eazy_catalog.json)。

## 其它文档

* [API 索引](../api/README.md)：49 个图表函数的签名与参数详解入口。
* [文档总入口](../README.md)：按「我想……」导航全部文档。
* [`docs/AI_GUIDE.md`](../AI_GUIDE.md)：给 AI 助手/代码生成用的精简契约。
* [`docs/EXTRA_CHARTS.md`](../EXTRA_CHARTS.md)：Python 与 JS 的图表实现契约，扩展图表前必读。
