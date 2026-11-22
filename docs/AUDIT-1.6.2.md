# eazy_data_viz 1.6.2 全项目审计与修复记录

> 审计目标：在框架继续长大之前「排雷」——把**代码、文档、逻辑、显示**四类问题一次性摊开，
> 该修的修，修不了的写清楚原因，避免以后在错误的地基上加功能。
>
> 设计理念（用户原话）：「最简洁的方式（代码和交互）让用户构建起丰富、自洽的分析图表组，页面也需要好看、现代。」
> 这篇文档的每一节都会回到这句话：**修掉的问题，是否让「写一行代码」更接近「得到一个可信的图」**。

---

## 1. 方法与范围

| 项 | 说明 |
| --- | --- |
| 审计对象 | `origin/master` @ `1060d6d`（1.6.1），在 `F:\deepseek\audit` 只读检出 |
| 方式 | 12 个领域并行审计：每个领域「先通读实现 → 再逐条复现」，复现不了的直接判 refuted |
| 领域 | chart-core / charts-extra-a / charts-extra-b / frame-maps / render-layout / metric-compare / js-core / js-render / js-extra / js-html-map / docs-consistency / visual-ux |
| 结果 | 提交 128 条，确认 127 条（1 条判 refuted 后按文档口径改写） |
| 修复 | 1.6.2 修掉 30 条；其余按「现在不做 / 需要设计变更」分类记录在第 4 节 |
| 回归 | `test_eazy` 54 / `test_maps` 33 / `js_test` 137 / `js_test_15` 173 / `e2e_test` 42 / 浏览器探针 14 |

审计只做三件事：**能不能画出正确的图**（数值、坐标、聚合）、**错误是不是可发现的**（报错 / `chart.warnings` / 控制台）、**文档与实现对得上吗**。

---

## 2. 已修复（30 条）

### 2.1 数值与几何（display 错误，用户最容易被骗的地方）

| # | 问题 | 位置 | 修法 |
| --- | --- | --- | --- |
| 1 | `percent=True` 但没给 `color` 时所有柱子变成 0（分母只在有 color 时累加） | `assets/eazy.js` percent 分支 | Python 侧直接报错：`percent=True（百分比堆叠）需要 color 参数…想看单系列的构成请用 pie()/funnel()/treemap()`；JS 侧兜底 `val = ct ? val/ct*100 : val` |
| 2 | `top_n` 的「其他」在没有 color 时恒为 0 / 柱状断线 | `assets/eazy.js` | 取值键改为 `otherCats[k] + SEP + (cdim ? sname : '')` |
| 3 | 瀑布图负增量向上画，柱子与断口错位 | `assets/eazy_extra_main.js` | `bases.push(Math.min(cum, cum + d))` |
| 4 | 瀑布图「合计」柱标签恒为 0 | 同上 | 单独维护 `vals` 数组，label 用真实值 |
| 5 | 哑铃图下降项连接条浮在端点外 | `assets/eazy_extra_a.js` | `bases.push(Math.min(a, b))` |
| 6 | slope 图的 arms 用 `str(v)` 生成类目（`2024-01-01 00:00:00` / `2023.0`），与 records 的字符串对不上 → 整图无线 | `charts_extra.py` slope | 改用 `_frame.column_values()` 生成与数据一致的类目字符串 |
| 7 | 桑基图用「值相等」判断自环，丢掉相邻层同名节点（华东→华东 300 消失） | `assets/eazy_extra_b.js` | 节点按 `层 + 分隔符 + 值` 唯一命名，相邻层同名本就不同节点 → 删掉自环判断，只过滤非有限/非正值 |
| 8 | graph 图不写 `nodeDim`、不注册 `nodeMaps` → `link` 完全失效 | `assets/eazy.js` graph builder | 节点写 `nodeDim/nodeLayer/nodeValue` 并注册 `EazyViz.nodeMaps` |
| 9 | 树图点「全部」根节点会把同组图筛成空 | `assets/eazy_extra_b.js` + `eazy.js` | 合成根写 `nodeDim: null`；`nodeInfoOf` 遇到显式 `null` 直接返回 null，不再落到 `treePathInfo` 兜底 |
| 10 | 时间列格式化成 `%Y-%m-%d %H:%M` 丢秒，同分钟多行被前端合并求和；一个 NaT 还会把整列拉回 `00:00` | `frame.py::column_values` | 按数据实际内容选择 `%Y-%m-%d` / `%H:%M` / `%H:%M:%S`，用 `notna()` 过滤 NaT |
| 11 | 数值列含 ±inf 时 `to_json(allow_nan=False)` 抛错、整页白屏 | `frame.py::column_values` | 非有限值统一转 `None`（前端按缺失处理） |
| 12 | 极小数（`1.23456e-05`）被固定 4 位小数舍成 0 | 同上 | `<1` 的数保留 6 位，其余 4 位 |
| 13 | 重名列导致 `AttributeError: 'DataFrame' object has no attribute 'tolist'` | `frame.py::ensure_frame` | 提前报错：`数据里有重复的列名… df.loc[:, ~df.columns.duplicated()]` |

### 2.2 可发现性（错要错得明白）

| # | 问题 | 修法 |
| --- | --- | --- |
| 14 | 全空/全文本数值列报「当前是文本，例如 []」 | 改报「列 X 里没有可用的数值（整列为空或全是文本）…」 |
| 15 | `combo(df, None, …)` 生成标题「按 None」和单类目 `(空)` | 缺 x 校验列表加入 `combo` |
| 16 | `combo(bar=[a, b])` 抛 `TypeError: cannot use 'list' as a set element` | 注解改 `str | None`，并显式报错「combo 的 bar 只能是一列」 |
| 17 | `Chart.show()` 不打印 `chart.warnings`（只有 `Dashboard.show` 打印） | 写文件后逐条打印，前缀 `[eazy_data_viz 提示]` |
| 18 | 汇总表模式下 `total/index/bar` 被静默忽略 | `table()` 追加 warning 说明 |
| 19 | 旭日/树忽略 `sort`/`top_n` 却什么都不说 | 追加 warning「要控制顺序请先聚合排序」 |
| 20 | `spark: bool` 注解与实现（列名）不符 | 改 `str | None` |
| 21 | `table(index: str | None = False)` 注解不实 | 改 `bool` |
| 22 | `group_kpi` docstring 说「每个数值列一张」，实际默认只取 6 项 | docstring 补 `top_n` 说明 |
| 23 | `table` docstring 没写「`total=True` 只累加当前显示的行」 | 补上 |
| 24 | `kpi` docstring 还在教已下架的 `edv.switch()` | 改为 `metric=` + `edv.follow()` |

### 2.3 交互与联动

| # | 问题 | 修法 |
| --- | --- | --- |
| 25 | drill 列表已含 x 时又前置一次，出现 `[月, 地区, 月]` | 对比后再前置 + 保序去重；地图类型豁免（`maps._drill_dims()` 故意复制 region 以支持单层聚焦） |
| 26 | `sort="订单均价"`（`edv.column` 表达式列）报「不是数据里的一列」 | sort_rank 阶段按需 `materialize()` 表达式列 |
| 27 | trend 回归线/R²、quadrant 中线在联动过滤后仍按全量计算 | 用当前可见点重拟合，退化时回落到全量 |
| 28 | 常数列的相关系数显示 `0.00`（误导为「无关」） | 显示「—（该列为常量）」 |
| 29 | target/bullet 目标缺失时按 0 画线并显示「目标 0」 | 缺失目标不再画线，tooltip 显示「—」 |
| 30 | 棒棒糖图 tooltip 里柱与点同名同值，各出一行 | 自定义 formatter 只输出一行 |

### 2.4 文档与视觉

| # | 问题 | 修法 |
| --- | --- | --- |
| 31 | README / `docs/api/geo_map.md` 仍写默认 `max_rows=200000`（实际 200 万），还建议「调大到 300000」 | 全量更正为 `2000000`，并给出「明细 5k–50k / 聚合类大值」的建议 |
| 32 | `geo_map` 文档说未匹配区域「不进 `chart.warnings`」，实际会进 | 文档与验证段同步改正 |
| 33 | `palette` 的 carbon 最深两色对比度 1.84 / 2.40:1（WCAG 下限 3:1），却标「适合深色大屏」 | 提亮为 `#b2453f` / `#4589ff` |
| 34 | 「内蒙」报未匹配（前端别名表有、Python 没有） | `maps._REGION_ALIASES` 补齐 内蒙/广西省/新疆省/西藏省/宁夏省 |
| 35 | 世界地图「老挝」映射到 `Laos`，而 `world.json` 里是 `Lao PDR` | 修正映射 |
| 36 | 词云用白色/浅色 logo 做形状时画布空白 | 掩膜识别三态：透明底看 alpha、白底看暗像素、浅色 logo 看亮像素 |

---

## 3. 设计中「看起来像 bug 但其实是约定」的（已补文档）

- **明细表 `total=True` 只累加显示中的行**：`table` 为了控制页面体积默认只嵌 100 行，合计按显示行算是刻意的（否则数字与看到的表格不符）。已在 docstring 与 `docs/api/table.md` 写明。
- **`max_rows` 默认 200 万**：1.5.2 起从 20 万提到 200 万（用户要求），代价是页面体积 ≈ 230 MB/百万行，`guides/13` 已给出「明细图显式 5k–50k」的建议。

---

## 4. 已知问题 / 本次未做（附原因）

| 项 | 现状 | 为什么现在不做 |
| --- | --- | --- |
| 旭日 / 树不支持 `sort` / `top_n` | 现在会 warning | 需要改 `buildTree` 的建树与布局（排序影响扇区顺序与角度），属功能而非修 bug，留到下个小版本 |
| 汇总表支持 `total` / `index` / `bar` | 现在会 warning | 汇总表每行已是一个分组，加合计行/序号/迷你柱需要新的渲染分支 |
| `chart.py` 的通用参数文档段落没有复用 `_COMMON_DOC` | 各函数 docstring 已逐条写全（`check_docs` 53/55 全覆盖） | 纯重构，收益是少几十行文本，会动 40+ 个 docstring，风险 > 收益 |
| 明细表 footer 在 `limit=1000` 时消失 | 已补「共 N 行」提示 | 极端大表下 footer 位置会挤压表格，需要布局方案 |
| 词云形状图完全透明（全透明 PNG）时退化成矩形 | 已尽力（三态识别） | 全透明图没有可采样像素，属输入问题 |

---

## 5. 回归矩阵（1.6.2）

```
tests/test_eazy.py     PASS 54   （新增 t_audit_162：12 组断言覆盖本次修复）
tests/test_maps.py     PASS 33
tests/js_test.py       JS PASS 137
tests/js_test_15.py    JS PASS 173
tests/e2e_test.py      E2E PASS 42
_scratch/probe162.py   PASS 14   （瀑布/哑铃/桑基/树/关系/TopN/percent 的浏览器复现）
tools/check_docs.py    55 完整 / 0 不完整 / 0 缺失
```

`t_audit_162` 的断言就是这次审计的「防复发疫苗」：percent 必须报错、±inf 必须变缺失、时间列必须保留秒、极小数不能被舍成 0、`sort` 必须能用表达式列、drill 不能重复、combo 必须报缺 x、静态 KPI 不能复制标题、缓存改中间行必须失效。

---

## 6. 给下一位维护者

1. **改 `assets/*.js` 之前先看行尾**：仓库里 `.py` / `.js` / `.md` 混合 CRLF / LF，脚本必须按原文件行尾写回，否则 `git diff` 会从几十行涨到几千行（这次审计就踩过）。
2. **新增图表要同时补三处**：`_NUMERIC_ROLE_KEYS`（哪些角色是数值）、`currentXDim`（点击回传哪个维度）、`nodeInfoOf`（节点→(维度, 值) 的映射）。漏掉后两者，联动会「点了没反应」。
3. **任何「静默忽略参数」都要换成 warning**：本次 1/4 的问题都是「参数传了但没生效」，用户无法察觉。
4. **跑探针再交付**：`_scratch/probe*.py` 是浏览器里真点一遍，`pytest` 抓不到 `percent` 归零这类显示错误。
