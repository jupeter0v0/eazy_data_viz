# 基础图表文档自检记录（basic_check）

本文件由脚本 `F:\deepseek\_ds_scratch\check_docs.py` 自动生成（2026-11-16），逐函数对比 **`docs/api/<函数>.md` 的「参数总览」表** 与 **`inspect.signature`**，并记录阅读源码/前端 `eazy_data_viz/assets/eazy.js` 时发现的实现疑点。仅记录，不修改任何代码。

## 检查方法

1. 用 `inspect.signature(edv.<函数>)` 取参数名、默认值、是否必填；`area` 特殊：正式签名只有 `data / x / y / color / **kwargs`，有效参数集按 `inspect.signature(edv.line)` 展开（去掉 `area`）。
2. 解析文档「参数总览」表的每一行（参数 / 类型 / 默认值 / 必填），与签名逐项比对。
3. 解析「函数签名」下的 python 代码块，逐参数核对是否保留默认值（`title=None`、`fmt="compact"` 等）。
4. 同时检查 7 个顶层章节是否齐全、`## 完整示例` 下 `### 示例 N` 数量是否 ≥4。
5. 运行 `examples/charts/<函数>.py` 验证示例可执行、生成 HTML > 100_000 字节。

## 总览

| 函数 | 签名参数数（含 **kwargs） | 文档覆盖数 | 缺失 | 多写 | 默认值不符 | 必填标记不符 | 签名块 | 7 章节 | 示例数 | 文档行数 | 示例脚本行数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `bar` | 26 | 26 | 0 | 0 | 0 | 0 | OK | 7/7 | 10 | 781 | 159 |
| `line` | 28 | 28 | 0 | 0 | 0 | 0 | OK | 7/7 | 10 | 805 | 162 |
| `area` | 28 | 28 | 0 | 0 | 0 | 0 | OK | 7/7 | 10 | 789 | 158 |
| `pie` | 15 | 15 | 0 | 0 | 0 | 0 | OK | 7/7 | 11 | 604 | 159 |
| `scatter` | 18 | 18 | 0 | 0 | 0 | 0 | OK | 7/7 | 10 | 646 | 165 |
| `histogram` | 12 | 12 | 0 | 0 | 0 | 0 | OK | 7/7 | 10 | 551 | 158 |
| `heatmap` | 16 | 16 | 0 | 0 | 0 | 0 | OK | 7/7 | 10 | 618 | 161 |
| `box` | 10 | 10 | 0 | 0 | 0 | 0 | OK | 7/7 | 10 | 515 | 157 |
| `funnel` | 12 | 12 | 0 | 0 | 0 | 0 | OK | 7/7 | 10 | 569 | 185 |
| `treemap` | 10 | 10 | 0 | 0 | 0 | 0 | OK | 7/7 | 10 | 514 | 153 |
| `gauge` | 10 | 10 | 0 | 0 | 0 | 0 | OK | 7/7 | 11 | 502 | 154 |
| `kpi` | 22 | 22 | 0 | 0 | 0 | 0 | OK | 7/7 | 10 | 698 | 158 |
| `combo` | 14 | 14 | 0 | 0 | 0 | 0 | OK | 7/7 | 12 | 615 | 166 |

**结论：13 个函数的参数集合、默认值、必填标记、签名代码块、7 个章节全部一致，0 处不一致。**

## 示例运行结果

| 函数 | 退出码 | 输出 HTML 数 | 最小 HTML 字节 | 最大 HTML 字节 | 末尾标记 |
| --- | --- | --- | --- | --- | --- |
| `bar` | 0 | 10 | 1442994 | 1443326 | `OK bar` |
| `line` | 0 | 10 | 1270527 | 1443337 | `OK line` |
| `area` | 0 | 10 | 1270434 | 1443318 | `OK area` |
| `pie` | 0 | 11 | 1442922 | 1443162 | `OK pie` |
| `scatter` | 0 | 10 | 1270483 | 1443252 | `OK scatter` |
| `histogram` | 0 | 10 | 1284812 | 1454966 | `OK histogram` |
| `heatmap` | 0 | 10 | 1322218 | 1443228 | `OK heatmap` |
| `box` | 0 | 10 | 1304980 | 1443025 | `OK box` |
| `funnel` | 0 | 10 | 1270026 | 1443016 | `OK funnel` |
| `treemap` | 0 | 10 | 1270741 | 1443087 | `OK treemap` |
| `gauge` | 0 | 11 | 1269740 | 1269976 | `OK gauge` |
| `kpi` | 0 | 10 | 1269923 | 1443269 | `OK kpi` |
| `combo` | 0 | 12 | 1339643 | 1443071 | `OK combo` |

> 运行方式：`cd F:\deepseek\eazy_data_viz && PYTHONPATH=. PYTHONIOENCODING=utf-8 python examples/charts/<函数>.py`；13 个脚本均实际执行通过，输出目录 `examples/output/`（已 gitignore）。注意：`examples/charts/` 下还有其它图表脚本（例如 `calendar.py`），直接运行时会因脚本目录排在 `sys.path` 首位而遮蔽标准库 `calendar`，导致 `import pandas` 失败；本组 13 个示例已在模板里先移除脚本目录再 import，规避了该问题。

## 参数说明中已核对的环境事实

- `max_rows` 默认值已由主控从 20000 调整为 **200000**（`eazy_data_viz/frame.py:21 MAX_ROWS = 200000`），传 `None` 表示不采样（`frame.py:206-209`）；本文档按新默认值生成。
- 超过 `max_rows` 时使用 `numpy.linspace` 均匀抽样，`prepare()` 返回的 `truncated` 标记与 `chart.warnings` 会提示；抽样不修改原始 DataFrame。
- `Chart.save()` 返回绝对路径并自动建目录；单图 HTML 约 1.2~1.4MB（ECharts 与数据内联）。
- 真实报错文本均通过运行触发采集（`F:\deepseek\_ds_scratch\probe.py` / `probe_out.txt`），未编造。

## 源码/前端可疑实现清单（建议主控评估）

1. **pie 的 sort 参数不生效**
   - 位置：`eazy_data_viz/assets/eazy.js` 的 `buildPie()`（约 771 行）；`eazy_data_viz/chart.py:533` 仍暴露 `sort="desc"`
   - 现象：`spec.sort` 虽然写入页面，但前端始终按 value 降序绘制；传 `sort="asc"` 与 `"desc"` 画面一致。
   - 建议：前端读取 `spec.sort` 后决定排序方向；或在修复前把 `sort` 标记为“预留参数”。文档已如实说明。

2. **scatter 的 agg 参数不生效**
   - 位置：`assets/eazy.js` 的 `buildScatter()`（约 829 行）；`chart.py:591`
   - 现象：`agg` 会写入 spec，但散点图前端没有 groupBy 聚合逻辑，逐行画点，传 `agg="mean"` 与 `sum` 结果相同。
   - 建议：若希望散点先聚合，应在 Python 侧聚合后再画；或前端补聚合分支。文档已注明。

3. **line/area 的 markers 参数几乎无效**
   - 位置：`assets/eazy.js` 的 `buildCartesian()` 中对 `spec.markers` 的处理；`chart.py:458`
   - 现象：目前只设置空的 `markPoint`（`data: []`、`symbolSize: 0`），肉眼看不到标记点，传 `markers=True` 与默认无差别。
   - 建议：实现 `markPoint: {symbolSize: 8}` 或直接移除该参数。文档写为“预留/效果有限”。

4. **histogram 的 labels 参数不生效**
   - 位置：`assets/eazy.js` 的 `buildHistogram()`（约 902 行）；`chart.py:648`
   - 现象：`labels` 写入 spec，但直方图前端不读取它，柱顶不显示数值。
   - 建议：前端补 `label.show` 逻辑或移除参数。文档已注明。

5. **treemap 的 sort 参数不生效**
   - 位置：`assets/eazy.js` 的 `buildTreemapTree()` / `buildTreemap()`（约 1157 行）；`chart.py:861`
   - 现象：Python 侧 spec 写入 `sort="desc"`，但前端构建树时不排序，节点顺序取决于数据出现顺序。
   - 建议：前端按 value 排序或在 Python 侧排序后传入。文档已注明。

6. **heatmap 的 labels 只在格子 ≤60 时显示**
   - 位置：`assets/eazy.js` 的 `buildHeatmap()`（约 965 行）
   - 现象：前端条件为 `showLabel = !!spec.labels && 格子数 <= 60`，格子多时静默隐藏标签，用户会以为参数失效。
   - 建议：把阈值写进文档（已写）或改为按需抽样显示。

7. **gauge 完全不校验 theme / height / fmt**
   - 位置：`chart.py:916-973` 的 `gauge()` 未调用 `_base_spec`
   - 现象：`gauge(87, fmt="money")`、`gauge(87, theme="blue")`、`gauge(87, height=80)` 都不报错，非法值直接进入 spec；`gauge(True)` 会被 `float(True)` 转成 1.0。
   - 建议：复用公共参数校验（theme/fmt/height）并对 bool 显式拒绝。

8. **max_rows 缺少取值校验**
   - 位置：`eazy_data_viz/frame.py:206-209`；`chart.py` 各函数默认 `_frame.MAX_ROWS`
   - 现象：`max_rows=0` 会得到 0 行图表（页面显示“当前条件下没有数据”），负数行为未定义；`max_rows=None` 才是关闭采样。
   - 建议：在 `prepare()` 或 `_base_spec()` 校验 `max_rows is None or (int 且 >0)`；文档已说明。

9. **sort / labels / zoom 等布尔与枚举参数缺少类型校验**
   - 位置：`chart.py` 的 `_base_spec`（约 92-175 行）与各函数
   - 现象：`sort="rank"`、`labels="yes"`、`zoom="nope"` 都被静默接受：非法 sort 等价不排序，labels 走 truthy，zoom 非法值前端当 false。
   - 建议：对 sort 做枚举/方向校验，对 labels/zoom 做 bool 校验并报中文错误。

10. **scatter / heatmap 的 link 联动可能失效**
   - 位置：`assets/eazy.js` 的联动逻辑依赖点击事件里的 `p.name`；`buildScatter()` / `buildHeatmap()` 的数据项未设置 `name`
   - 现象：点击散点或热力图格子时可能拿不到类目值，导致联动组其它图不刷新或刷新为空。
   - 建议：前端给 data item 增加 `name`（类目值）后再触发联动；文档写为“可用但需验证”。

11. **area 通过 **kwargs 隐藏了全部参数，且 area=False 会被覆盖**
   - 位置：`eazy_data_viz/chart.py:527-531`
   - 现象：`area(df, x, y, area=False)` 内部固定 `kwargs["area"] = True`，无法画“关闭填充”的面积图；IDE/签名提示也看不到 sort、theme 等参数。
   - 建议：把 line 的参数显式列出，或至少文档说明（已说明）；若允许 `area=False`，改成 `kwargs.setdefault("area", True)`。

12. **pie 没有 legend 参数但图例恒显示**
   - 位置：`chart.py:533` 的签名；`assets/eazy.js` 的 `buildPie()`
   - 现象：用户无法关闭饼图图例；`legend` 也不在 spec 中。
   - 建议：增加 `legend=True` 参数并透传前端。文档已注明“图例始终显示”。

13. **line/area 未暴露 stack 参数**
   - 位置：`chart.py:458` 的 line 签名；`assets/eazy.js` 的 `buildCartesian()` 支持 `spec.stack`
   - 现象：前端支持堆叠线/面积，但 API 没有 `stack`，用户只能画重叠面积。
   - 建议：增加 `stack=False` 参数（bar 已有同名参数，语义一致）。

14. **combo 右轴标题固定为 line 列名，ytitle 只作用左轴**
   - 位置：`chart.py:1152-1200`；`assets/eazy.js` 的 `buildCombo()`（约 729 行）
   - 现象：无法单独给右轴设置标题；用户传 `ytitle` 误以为两轴都改。
   - 建议：增加 `ytitle2`/`line_ytitle` 参数，或文档明确（已写）。

15. **box 无 xtitle 参数，且不绘制离群点**
   - 位置：`chart.py:757-812`；`assets/eazy.js` 的 `buildBox()`（约 1041 行）
   - 现象：箱线图只有 min/Q1/中位数/Q3/max 五数，没有离群点（1.5 IQR 之外的点不单独绘制）；类目轴标题只能回退列名。
   - 建议：补离群点计算与 `xtitle` 参数；文档已说明口径，避免用户误读。

16. **histogram column=None 的自动选择很窄**
   - 位置：`chart.py:648-702`
   - 现象：仅当 DataFrame 恰好只有 1 个数值列时才自动选列，否则直接报错并列出数值列；多列数据必须显式传 column。
   - 建议：行为合理，但错误提示可给“默认取第一数值列”的选项；文档已说明。

17. **kpi 静态数值模式下 spark 无法渲染**
   - 位置：`chart.py:975-1150` 的静态分支
   - 现象：当 `data` 直接传数值（如 `kpi(1630000, label="销售额", spark=..., spark_x=...)`）时 rows=0，迷你走势没有数据不会渲染；且仍会因缺 `spark_x` 报错。
   - 建议：静态模式下忽略 spark 参数（或直接报“静态 KPI 不支持 spark”）；文档已说明。

18. **kpi 的 bool 数据未被明确拒绝**
   - 位置：`chart.py:975` 的 `isinstance(data, (int, float)) and not isinstance(data, bool)` 分支
   - 现象：`kpi(True)` 既不进入静态数值分支，也不是 DataFrame/Series/dict/list，随后走 `ensure_frame` 报类型错误，错误信息与“缺数据”混淆。
   - 建议：在入口处显式拒绝 bool 并给出中文提示。

19. **bar/line/kpi 的 section 只在 Dashboard 生效**
   - 位置：`chart.py` 的 `section` 参数；`render.py:523` 的 `Dashboard`
   - 现象：单图 `save()/to_html()` 时 section 仅写入 spec，不会显示分区标题；用户可能以为参数无效。
   - 建议：文档已说明；也可在单图页脚提示“该参数仅在 Dashboard 中生效”。

20. **top_n 合并出的“其他”类目不参与联动**
   - 位置：`assets/eazy.js` 的联动点击处理
   - 现象：点击“其他”柱/扇区时联动被忽略（避免把多个类目混为一谈），但用户会以为联动坏了。
   - 建议：前端对“其他”给出 tooltip 说明，或在文档强调（已写）。

21. **zoom 的 `"auto"` 阈值固定为 15 个类目**
   - 位置：`assets/eazy.js` 的 `buildCartesian()`
   - 现象：类目 >15 自动出现缩放条，≤15 不出现；该阈值不可配置。
   - 建议：可增加 `zoom_min_categories` 参数；文档已写清阈值。

22. **`_ensure_numeric` 对文本列直接报错，不会尝试自动转换**
   - 位置：`chart.py:1207-1220`；`eazy_data_viz/frame.py` 的类型处理
   - 现象：散点 x 等数值角色遇到文本列会抛中文 TypeError 并给示例值，但不会尝试 `pd.to_numeric`；数据里混入“暂无”等脏值时整图失败。
   - 建议：保持显式报错是合理的；文档已给清洗示例。

23. **min/max 等数值型参数对非数字输入缺少统一错误**
   - 位置：`chart.py` 的 `gauge()` / `kpi()`
   - 现象：`gauge(min="a")` 会在 `float()` 处抛原生 `ValueError: could not convert string to float: 'a'`，与其它中文错误风格不一致。
   - 建议：统一用中文错误包装（文档已如实给出原生报错）。

## 备注

- 本组文档不追求行数指标（lead 已说明用户关注的是绘图数据行数上限 `max_rows`，不是文档行数）；内容按参数与示例的实际需要组织。
- 文档中所有“常见错误”均为运行后复制的真实异常文本；`Warnings`（抽样、丢列）不是异常，写作注意事项。
- 前端行为（排序、标签、缩放、联动）通过阅读 `eazy_data_viz/assets/eazy.js` 对应 build 函数确认，文件行号见上表。
