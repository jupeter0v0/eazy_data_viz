# eazy_data_viz 文档

`eazy_data_viz` 把 pandas DataFrame 变成可交互的单文件 HTML 图表与经营驾驶舱：49 个图表函数、7 套配色、客户端下钻/联动、Streamlit 兼容，图表运行时完全内联，离线可开。

## 60 秒出第一张图

```python
import eazy_data_viz as edv

df = edv.sample_df()
edv.bar(df, x="大区", y="销售额", color="渠道", stack=True).save("examples/output/quickstart.html")
```

`edv.sample_df()` 是一份 1500 行的模拟销售数据（日期 / 大区 / 省份 / 城市 / 产品 / 渠道 / 销售额 / 订单数 / 利润 / 客户数），用于把文档里的例子直接跑起来。换成你自己的 DataFrame 即可，第一参数永远是 `df`，其余参数传**列名字符串**。

## 我想……

| 我想…… | 去哪 |
| --- | --- |
| 第一次安装、确认版本兼容 | [01 · 安装与环境矩阵](guides/01-installation.md) |
| 5 分钟学会画图 | [02 · 五分钟上手](guides/02-quickstart.md) |
| 知道某个问题该用什么图 | [10 · 选图决策指南](guides/10-chart-selection.md) |
| 搭一个经营驾驶舱 | [03 · 从零搭一个经营驾驶舱](guides/03-cockpit-tutorial.md) |
| 把 KPI 卡片做到位 | [04 · KPI 卡片全参数详解](guides/04-kpi-cards.md) |
| 换配色 / 深色主题 | [05 · 配色与主题](guides/05-palette-and-theme.md) |
| 配下钻、联动、缩放、导出 PNG | [06 · 交互总览](guides/06-interaction.md) |
| 放进 Streamlit | [07 · Streamlit 集成](guides/07-streamlit.md) |
| 交付一个离线 HTML 文件 | [08 · 静态 HTML 与导出](guides/08-static-html-and-export.md) |
| 清洗数据 / 处理日期和缺失值 | [09 · 数据准备](guides/09-data-preparation.md) |
| 直接抄一个常用配方 | [11 · 常用配方（Cookbook）](guides/11-cookbook.md) |
| 图不对 / 报错了 | [12 · 常见问题与错误对照](guides/12-troubleshooting.md) |
| 文件太大 / 首屏太慢 | [13 · 性能与体积](guides/13-performance.md) |
| 加一种新图表类型 | [14 · 扩展图表](guides/14-extend-charts.md) |
| 做省份 / 城市地图 | [地图图表完全指南](guides/map.md) |
| 查某个函数的全部参数 | [API 索引](api/README.md) |
| 让 AI 帮我写代码 | [AI_GUIDE.md](AI_GUIDE.md) |

## 文档地图

### 教程（guides）

| 篇 | 主题 |
| --- | --- |
| 01 | [安装与环境矩阵](guides/01-installation.md) |
| 02 | [五分钟上手](guides/02-quickstart.md) |
| 03 | [从零搭一个经营驾驶舱](guides/03-cockpit-tutorial.md) |
| 04 | [KPI 卡片全参数详解](guides/04-kpi-cards.md) |
| 05 | [配色与主题](guides/05-palette-and-theme.md) |
| 06 | [交互总览：下钻、联动、缩放与导出](guides/06-interaction.md) |
| 07 | [Streamlit 集成](guides/07-streamlit.md) |
| 08 | [静态 HTML 与导出](guides/08-static-html-and-export.md) |
| 09 | [数据准备](guides/09-data-preparation.md) |
| 10 | [选图决策指南](guides/10-chart-selection.md) |
| 11 | [常用配方（Cookbook）](guides/11-cookbook.md) |
| 12 | [常见问题与错误对照](guides/12-troubleshooting.md) |
| 13 | [性能与体积](guides/13-performance.md) |
| 14 | [扩展图表](guides/14-extend-charts.md) |
| 专题 | [地图图表完全指南](guides/map.md) |

完整目录与推荐阅读路径见 [guides/README.md](guides/README.md)。

### API 参考（api）

49 个图表函数按 7 组组织：核心指标、趋势、对比与排名、结构与占比、分布与关系、明细与文本、地图/其它；每个函数都有独立的签名、参数详解、完整示例与常见问题页：

| 组 | 函数 |
| --- | --- |
| 核心指标 7 | `kpi` `group_kpi` `gauge` `ring_progress` `bullet` `target` `progress` |
| 趋势 8 | `line` `area_pct` `combo` `sparkline` `theme_river` `gantt` `candlestick` `calendar` |
| 对比与排名 10 | `bar` `bar_pct` `waterfall` `pareto` `lollipop` `dumbbell` `slope` `bump` `pictorial` `pyramid` |
| 结构与占比 7 | `pie` `rose` `funnel` `treemap` `sunburst` `tree` `tile` |
| 分布与关系 11 | `scatter` `histogram` `box` `heatmap` `matrix` `radar` `parallel` `quadrant` `sankey` `graph` `trend` |
| 明细与文本 2 | `table` `wordcloud` |
| 地图/其它 4 | `area` `geo_map` `map_bubble` `map_flow` |

入口：[docs/api/README.md](api/README.md)（含公共参数、`Chart` 方法与 `dashboard()` 用法）。机器可读的完整签名在 [`docs/eazy_catalog.json`](eazy_catalog.json)，终端里也可以运行：

```bash
python -c "import eazy_data_viz as e; e.help()"
```

### 其它文档

* [AI_GUIDE.md](AI_GUIDE.md)：给 AI 助手/代码生成模型的紧凑契约（调用方式、参数枚举、常见组合）。
* [EXTRA_CHARTS.md](EXTRA_CHARTS.md)：Python ⇄ JS 的图表实现契约，新增图表前必读。
* [eazy_catalog.json](eazy_catalog.json)：函数签名、参数元数据、配色与分组，供工具与 AI 读取。

## 环境矩阵

| Python | pandas | streamlit | 状态 |
| --- | --- | --- | --- |
| 3.8.10 | 2.0.3 | 1.27.1 | 已验证（本项目主力环境） |
| 3.12.14 | 2.x | 1.67.0 | 已验证 |
| 3.14.10 | 3.1.1 | 1.67.0 | 已验证 |

最低要求：Python ≥ 3.8、pandas ≥ 1.3。Streamlit 是可选依赖（`pip install "eazy_data_viz[streamlit]"`，≥ 1.10）；Jupyter 展示需要 IPython（`[notebook]` 附加）。浏览器需支持 ES5 与 Canvas（Chrome / Edge / Firefox / Safari 近十年版本均可）。详细安装步骤见 [01 · 安装与环境矩阵](guides/01-installation.md)。

## 核心概念

* **图表函数 → `Chart`**：每个函数返回 `Chart`，三个方法：`to_html()` 拿完整 HTML 字符串、`save(path)` 写文件、`show()` 按环境自动显示（Streamlit / Jupyter / 脚本）。
* **列名驱动**：`x` / `y` / `color` / `names` / `values` 等参数都传**列名字符串**，不传 Series。
* **前端聚合**：Python 只做列校验、数据打包与少量预计算，分组聚合、下钻、联动、缩放全部在浏览器里完成，交互不触发 Python 重算。
* **多图联动**：同组图传相同 `link="组名"`，并且使用同名列作为维度；只有放进同一个 `dashboard()` / `show()` 页面才能联动。
* **单文件交付**：默认把 ECharts 与地图资产内联进 HTML，约 1.2 MB 固定开销，之后按数据行数增长；体积与性能见 [13 · 性能与体积](guides/13-performance.md)。

## 仓库结构

```
eazy_data_viz/          Python 包（chart.py / charts_extra.py / maps.py / frame.py / render.py + assets/）
docs/                   本文档
  guides/               15 篇教程
  api/                  49 个函数参考 + 公共参数
  eazy_catalog.json     机器可读目录
examples/               charts/ 单图示例、cockpit/ 看板、output/ 运行产物（gitignored）
tools/                  gen_ai_doc / build_gallery / check_docs 等维护脚本
tests/                  Python 冒烟测试与无头浏览器 JS 测试
```

## 文档约定

* 代码统一 `import eazy_data_viz as edv`，示例数据统一 `df = edv.sample_df()`；需要写文件时写到 `examples/output/`。
* 文中代码已逐块执行验证；示例输出为示意，数值随 pandas / 浏览器版本可能略有差异。
* 教程按「先解决问题、再解释参数」组织；单函数全参数请查 [API 索引](api/README.md)。
* 发现文档与代码不一致，以 `docs/eazy_catalog.json` 与运行时 `inspect.signature` 为准，并欢迎提 issue。
