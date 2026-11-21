## 1.5.7 — 2026-11-22

### 性能：prepare 向量化（10~12 倍）

- `frame.prepare()` 不再用逐元素 `Series.map(lambda)`：数值走 `to_numpy() + np.round().tolist()`、
  时间走 `pd.to_datetime + dt.strftime`、布尔走 `np.where`、文本走 `astype(str).tolist()`，
  只有超长文本（>120 字符）才逐条截断。
- 实测 8 图看板：2,000 行 0.18 s → **0.04 s**；20,000 行 0.97 s → **0.08 s**；80,000 行 3.88 s → **0.34 s**。
- 采样提前到转换之前：`max_rows` 生效时只转换采样后的行，不再先转全量。

### 性能：整列缓存

- 同一份 df 画多张图时，从第二张起复用已转换好的列（键含 `id(df)`、行数、`max_rows`、列名、
  首尾行指纹；`weakref` 防 id 复用）。
- 新增 `edv.clear_cache()` / `edv.cache_info()` / `edv.use_cache(False)`；`EAZY_NO_CACHE=1` 可全局关闭。

### Streamlit：先显示再加载

- `streamlit_dashboard()` 先画**骨架屏**（转圈 + 灰色卡片）再算数据，避免长时间空白。
- 新增 **payload 复用**：按「spec + 数据指纹 + 页面参数」签名缓存 `build_fragment()` 的结果，
  签名不变时跳过重新打包（8 图 6 行数据 0.4 s → 0.06 s）。
- v1 回退路径（`components.v1.html`）也套了 `st.spinner`。

### 新增 `edv.cached`

- `@edv.cached` 一行给「读数据」函数加缓存：Streamlit 里等价 `st.cache_data`，
  否则退回 `functools.lru_cache`。

### 多核结论

- 没有引入多线程 / 多进程 prepare：实测 6 线程 0.35 s vs 单线程 0.21 s（GIL + `astype(str)`），
  多进程还要 pickle 整份 df。并行收益留在「读数据」层（`@edv.cached`、SQL 侧聚合）。

### 测试

- `tests/test_eazy.py` 新增 `t_prepare_cache()`、`t_cached_helper()`（PASS 51）。

# Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## 1.5.6 — 2026-11-21

以「少占地方、看得清」为目标的界面瘦身，7 项：

### 页头 / 页脚

- 页头只留标题与副标题：配色下拉、主题按钮、两个重置按钮全部从页头移走。
- 页脚新增一条工具条，只放 **◐ 主题** 与 **重置** 两个控件（合并了原来分开的「重置联动」与「重置下钻」）；
  重置现在一次清掉：全部联动条件 + 每张图的下钻层级 + 旭日图放大。
- 要去换整页配色请用 `palette=` 参数，页面上不再提供配色下拉。

### 操作提示小字

- 「点击图形下钻到「…」」「点击单元格可按该列联动同组图表」「点击图形可联动同组图表（双向）」这些提示默认**不显示**；
  KPI 卡片自动生成的「联动组 g1 · 点同组图表筛选」也一起隐藏（用户自己传的 `hint=` 仍然显示）。
- 需要时按 `hints=True` 打开：`edv.dashboard(a, b, c, d, hints=True)`。

### KPI 迷你曲线

- `spark_x` 传月份时按自然顺序排（`1月, 2月, … 10月, 11月, 12月`）：`compareCatX` 改成「数字优先」比较，
  不再出现 `10月` 排在 `2月` 前面。
- 曲线改为 Catmull-Rom 平滑贝塞尔 + 渐变面积填充，末端点用 CSS 圆点（`preserveAspectRatio="none"` 下也不会被拉成椭圆）。

### 手机端

- 新增 `@media (max-width: 820px)`：自由排列（模式 B）的多列网格自动折成单列、
  `grid-column`/`grid-row`/固定高度全部让位；模式 A 的 `eazy-flow` 竖排；
  页脚与页头内边距收紧。之前手机上会挤成一团的问题解决。

### `card_style`：卡片外框样式

- 新增参数 `card_style`（`dashboard()` / `show()` / `streamlit_dashboard()` 都支持）：
  `"default"` 实心白卡（默认），`"glass"` 液态玻璃（半透明渐变 + `backdrop-filter: blur(22px) saturate(180%)` + 白色高光边）。
- 换页面底色时白色卡片会压住背景，用 `card_style="glass"` 让底色透上来；深色主题另有一套更暗的玻璃层。
- 传错值报错：`ValueError: card_style 只支持 "default"（实心卡片）或 "glass"（液态玻璃），收到 'x'。`
- 教程：[16 · 自由排列](../docs/guides/16-layout.md) 第 7 节。

## 1.5.5 — 2026-11-21

### 新增：多级联动条件（下钻 / 旭日 / 树图一次带多层）

以前一条联动只装「一个维度 = 一个值」：`bar(drill=["渠道", "品牌系列"], link="q1")`
点完“1月”再点“直销”后，联动条件只剩 `渠道 = 直销`，第一层的 `1月` 丢了，
下游图又被放大回全时间范围。

- 现在联动条件是一个**数组**：点一次带一层，钻几层就带几层。
  `bar(x="月", drill=["渠道", "品牌系列"], link="q1")` 点完两次后是
  `月 = 1月 · 渠道 = 直销`，下游按两条条件同时过滤；数据里没有的列自动跳过。
- 旭日图 / 树图点击深层节点时，从根到该节点的整条路径进联动：
  点第三层产品 → `大区 = 华东 · 渠道 = 直销 · 产品 = A`。
- 发起方自己仍然不过滤、只高亮；明细表 / 汇总表按“所有能对上的条件”标黄命中行。
- 兼容：`linkMode`、`onSelect` 不变；联动对象新增 `conds` 数组，`dim` / `value`
  仍等于最深一级，旧代码照常工作。

## 1.5.4 — 2026-11-21

### 新增：`agg="unique"`（去重计数）
- `agg` 新增第 7 种取值 `unique`，数的是**不重复的值有几个**，相当于 `pandas.Series.nunique()`。
  和第 1.5.3 的 `count` 不同：`count` 数行数，`unique` 数不同的值（`A / A / B` → count 3、unique 2）。
- 与 `count` 一样，度量列可以是**文本列**（客户名称、SKU、订单号……），不会被强制转数值：

```python
edv.kpi(df, value="客户名称", label="客户数", agg="unique")          # 多少家不同客户
edv.bar(df, x="大区", y="客户名称", agg="unique")                     # 每个大区几个不同客户
edv.table(df, groupby={"columns": ["大区"], "value": "客户名称", "agg": "unique"})
edv.wordcloud(df, names="客户名称", agg="unique")                     # 也支持
```

- 覆盖范围与 `count` 一致：`kpi`（含 `spark` 迷你趋势）、`bar` / `line` / `area` / `pie` / `funnel` /
  `sunburst` / `sankey` / `tree` / `treemap` / `group_kpi` / `wordcloud` / `waterfall` / `pareto` 等 30 多个函数，
  以及 `table(groupby={"agg": "unique"})`（表头显示「去重数」）。
- `agg="unique"` 必须指定要计数的列：`bar(df, x="大区", agg="unique")` 会报
  `ValueError: agg="unique"（去重计数）需要指定要计数的列…只数行数请用 agg="count"`；
  `table(groupby={"columns": [...], "agg": "unique"})` 缺 `value` 时同样提示改用 `count`。
- 忽略 `None` / `NaN` / 空串，与 `nunique()` 口径一致。
- `sum` / `mean` / `max` / `min` / `median` 仍然要求数值列，不受影响。

## 1.5.3 — 2026-11-21

### 修复：`agg="count"` 不再要求 measure 列是数值
- `kpi(df, value="客户名称", agg="count", spark="客户名称", spark_x="月")` 这类「数客户数」的写法，此前会抛
  `TypeError: 列 '客户名称' 需要是数值类型`。现在 `agg="count"` 统计的是行数，`value` / `spark` 可以是文本列。
- 同类问题一并修好：`bar` / `line` / `area` / `pie` / `funnel` / `sunburst` / `sankey` / `tree` / `treemap` /
  `group_kpi` / `wordcloud` / `waterfall` / `pareto` 等 30 多个函数，以及 `table(groupby={"agg": "count"})`。
- `sum` / `mean` / `max` / `min` / `median` 仍然要求数值列，报错文案不变（`TypeError: ... 需要是数值类型 ... 请先用 pd.to_numeric() 清洗`）。

### 修复：汇总表（`groupby`）默认嵌入完整数据
- `table` 的 `max_rows` 默认值改为 `None`（自动）：**明细表**仍嵌 200 行；**汇总表**嵌入全部行。
  原因是汇总必须在完整数据上算才和 `df.groupby(...).agg(...)` 对得上——此前硬截断到 200 行，
  大表上的 `sum` / `count` 会明显偏小（例如 480 行只按 200 行汇总）。
- 汇总表超过 5 万行时在 `chart.warnings` 里提示页面体积，并建议先预聚合或显式 `max_rows=20000`。
- `docs/api/table.md`、`docs/api/kpi.md` 同步更新。

## 1.5.2 — 2026-11-21

这一版全是「数字对不上」类的修复，来自真实看板的反馈。

### 修复：KPI 卡片数字和 pandas 的合计不一样

`kpi()` 的 `fmt` 默认是 `compact`，`4112275.31` 会被显示成 **411万**——数值本身没错，
但和 `df['金额'].sum()` 一比就像是算错了。

- KPI 卡片默认改成 `thousands`：直接显示 `4,112,275.31`，逐个数字对得上；
- 想紧凑仍可显式 `fmt="compact"`（411万）、`fmt="raw"`、`fmt="currency"`；
- 其它图表（坐标轴、tooltip、表格）的默认格式不变。

### 修复：柱状图同比方向可能反了

`yoy=True` 用「color 值大的算本期」：两个颜色值都是纯数字（`2025` / `2026`）时没问题，
但写成 `2025年` / `2026年` 时数字解析失败，会退化成「合计大的算本期」——
如果 2026 只统计到 8 月，2026 合计更小，同比就变成了「2025 对比 2026」。

- 现在先从系列名里抽数字（`2026年` → 2026、`第2季度` → 2），数字大的算本期；
- 抽不出数字（`华东` / `华南`）才回退到「合计大的算本期」。

### 新增：`sort` 可以传一列列名

横轴是「1月…12月」这类文本时，`sort="desc"` 会按金额排、`sort="x"` 按字符串排，都不对。
现在 `sort` 可以传一列列名，按这一列在每个类目下的最小值排序：

```python
edv.bar(df, x="月", y="金额", color="年", sort="年-月", yoy=True)   # 1月 → 12月
```

- `sort="desc" / "asc" / "x" / "none"` 四个保留取值不变；
- 传了不存在或无法组合的列会给出中文报错 / 警告，不再静默按原顺序画。

### 调整：`max_rows` 默认 200000 → 2000000

- 单图默认最多嵌入 200 万行（超出仍是按行位置均匀采样，并写入 `chart.warnings`）；
- `max_rows=None` 依旧表示完全不采样；
- 体积按约 120 B/行线性增长（200 万行 ≈ 230 MB），折线/柱状这类只看趋势的图
  建议仍显式传 `max_rows=5000~50000`，见 13 · 性能与体积。

## 1.5.1 — 2026-11-21

### 修复：汇总表（`table(groupby=...)`）不能联动

1.5.0 的汇总表只渲染了数字，单元格上没有挂联动的钩子，点了没反应。

- 分组列单元格现在和明细表一样带 `data-eazy-cell` / `data-eazy-val`，点一次发联动、再点取消；
- 命中当前联动时整行高亮（`eazy-row-hit`），汇总值按过滤后的数据重算，但底层 `data.rows` 不变。

### 修复：旭日图「放大」与「联动」冲突

点节点后只联动、不放大：联动会重画图表，而重画会把 ECharts 的视图根（`rootToNode` 放大的状态）重置回根。

- 点击时记下**名字路径**（`c.zoomPath`），重画后按路径在树里找回节点，再 `dispatchAction({type:'sunburstRootToNode', targetNode: 节点对象})`；
- 名字路径在重画前后稳定（用节点 id 会变），因此放大状态可以跨联动保留；
- 「重置联动」同时把旭日图退回根层；
- 没有放大请求的重画（换筛选条件、切主题、重置）会显式把视图根退到整棵树，不会卡在某个圈里。

### 新增：词云形状 `wordcloud(shape=...)`

`shape` 支持 8 种内置形状（`circle` / `cardioid` / `diamond` / `triangle` / `square` / `star` / `pentagon` / `heart`）
或一张本地图片（`.png` / `.jpg` / `.jpeg` / `.webp` / `.gif` / `.bmp` / `.svg`，≤ 2 MB，会内联成 data URI）：

- 传了 `shape` 才切到 `<canvas>` 引擎：形状掩膜 + 阿基米德螺旋装箱 + 词框互不重叠，字号按词频开方分配；
- 不传 `shape` 仍是原来那套纯 HTML/CSS 排版，行为与 1.5.0 完全一致；
- 形状会以 10% 透明度铺一层底影，词铺不满的尖角也能看出形状；
- 图片按「非白色像素」判定形状，白底 PNG/JPG 直接可用。

### 新增：公开 API 类型注解

`chart.py` / `charts_extra.py` / `maps.py` / `render.py` / `__init__.py` 的公开函数与 `Chart` / `Dashboard` 方法
都补上了参数与返回值注解（`data: pd.DataFrame`、`height: int`、`link: str | tuple | dict | None` …），
IDE 悬浮和自动补全不再显示 `Unknown`。

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
- 新增教程 [16 · 自由排列](docs/guides/16-layout.md)。

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

- 新增 [16 · 自由排列](docs/guides/16-layout.md)；[06 · 交互与联动](docs/guides/06-interaction.md) 增加 2.4 联动方向；
  `docs/api/` 的 `bar` / `table` / `sankey` 补全新参数与示例，全部图表补 `abs_height` 参数说明，
  公共参数表补 `linkMode`、`yoy`、`groupby`、`abs_height`。

## 1.4.1 — 2026-11-19

### 新增：北京区级地图（`map="beijing"` / `edv.beijing_map`）

- 内置北京 16 个市辖区行政区划 GeoJSON（`assets/maps/beijing.json`，约 0.10 MB），
  `MAPS` 从 `("china", "world")` 扩展为 `("china", "world", "beijing")`。
- 新增便捷函数 `edv.beijing_map(data, region="区", value=..., **kwargs)`，
  等价于 `geo_map(..., map="beijing")`，一行出图。也支持
  `map_bubble` / `map_flow` 在区级质心上打点、画线。
- 区名短名 / 全名都能匹配：`"朝阳"` 与 `"朝阳区"` 等价（行政区后缀表新增 `区` / `县`，
  Python 与前端两份表保持同步）。
- 前端 `initialView`：未知地图（如 beijing）不再强行套用中国视角，
  改为交给 ECharts 按 GeoJSON 包围盒自动缩放居中，地图不再跑偏。
- 渲染层：`_map_payload` 只在真正用到中国地图时才注入 39 KB 的城市表
  （`window.EAZY_CITIES`），北京 / 世界地图页面更轻。
- 匹配告警文案通用化：`区 列有 N 个区域名没匹配到内置北京地图…`，
  未匹配区域被静默跳过（不参与色阶与总计），北京地图也做匹配检查。
- 文档：`docs/api/geo_map.md`、`map_bubble.md`、`map_flow.md`、`guides/map.md`
  补充北京地图说明与示例；新增 `examples/beijing_map_demo.py`。
- 测试：新增 `t_geojson_beijing`、`t_beijing_map` 等，`tests/test_maps.py`
  断言更新为 `MAPS == ("china", "world", "beijing")`。

## 1.4.0 — 2026-11-18

### 表格 ↔ 图表 双向筛选联动

- 之前 `table(link="G")` 只能**接收**联动：点图筛表可以，点表没反应。
- 现在表格也能当**联动源**：`link` 已设置时，表里的维度列（文本/日期列）渲染成可点单元格
  （手型光标 + hover 提示），点一下把 `{dim: 列名, value: 单元格值, sourceId: 表格}` 写进
  联动组，同组 ECharts 图立刻按该条件过滤；点同一格再次取消。
- 表格自己作为 source 时不筛行，而是把命中的行高亮（首列主色竖条 + 半透明蒙层，
  `inset box-shadow` 叠在数据条之上，深浅色主题都生效），和图表「自己不过滤、只高亮」一致。
- 点单元格同样触发 `on_select`（`type: "table"`，带 `dim` / `value`），
  Streamlit 里传了 `on_select` 才会回传 Python，不传则完全在浏览器内完成，0 rerun。
- 数值列（含数据条列）不可点；没有 `link` 的表格行为完全不变。
- `combo()` 新增 `link` 参数（之前 spec 里已经会写 `link: None`，但函数签名没暴露），现在双轴图也能参与联动被动过滤。
"
"- 附：`eazy.js` 新增 `EazyViz.chartOfEl(el)`（按 DOM 归属反查图表，单元格点击没有 chart index）。

### 修复：同一页面挂多个看板时「图表 id 跳组件撞车」

- 现象：Streamlit 页面里挂了 KPI / 6 张图 / 明细表三个 `streamlit_dashboard()`，点明细表单元格后，chip 出现了、表里命中行也高亮了，但上方图表一张都没被筛。
- 原因：1.2.0 把图表 id 按**位置**固定为 `eazy-0`、`eazy-1`…，但每个看板组件都从 `eazy-0` 开始编号，一个页面挂多个看板时 id 就撞车了。表格发出的 `sourceId` 恰好等于另一个看板里某张图的 id，那张图就会误以为「自己是发起者」而不过滤（联动里「自己不过滤」是有意的，但不能把别人当成自己）。
- 修复：`render.py` 的 `_assign_ids()` 改为「看板内容指纹 + 位置」，id 形如 `eazy-<6 位指纹>-<位置>`。同一看板 rerun 前后指纹不变（不重挂、状态不丢），不同看板之间几乎不可能一致。
- 验证：`sales_demo` 里点明细表「大区 = 西南大区」单元格，月度趋势 / 大区×产品线 / 省份地图 / TOP10 / 饼图同步只剩西南大区；`tests/test_eazy.py` 新增「不同看板 id 不重复」回归。

### 新增：窄屏 / 窄容器自适应

- **栅格变量化**：`.eazy-grid` 从内联写死的 `repeat(N,minmax(0,1fr))` 改成
  `repeat(var(--eazy-cols,2),minmax(0,1fr))`，`build_page` / `build_fragment` 输出
  `style="--eazy-cols:N"`；`≤720px` 断点把变量压成 2 并按卡片类型排：KPI / 指标卡每行两张，
  图表卡与表格卡用 `grid-column:1/-1` 占满整行（之前内联写死的 `repeat()` 媒体查询根本盖不住）。
- **KPI 数字不再被裁**：手机上 `cols=4` 的指标卡只有 ~150px 宽，`47,771,40…` 会被切掉。
  新增 `fitTexts()`，用 `scrollWidth > 父节点 clientWidth` 判断溢出，每次 -2px（下限 13px）
  缩到放得下为止，完整数字读得出来。
- **图例按容器实际宽度排版**：`legendItemPx()` 按中日韩字符 1em、西文 0.56em 估算宽度
  （旧算法「字符数 × 7」把中文严重低估，行数算少、图例压到轴名上）；`legendRowInfo()`
  改用容器实际宽度算行数，`<720px` 允许 4 行、`<270px` 改成底部可滚动单行图例。
  饼图 / 漏斗的竖排图例有 `__legendFixed` 保护，不会被改成顶部横排。
- **饼图窄屏**：组件宽 `<430px` 时自动关掉外置标签（等同 `labels=False`）、图例移到底部，
  环径放大（donut 内径 30% / 外径 62%），手机上不再标签压环、图例挤成一团。
- **高度自适应**：`fitResponsiveHeights()` 在组件内栅格 `<720px` 时把 `--eazy-cols` 兜底成 1
  （给「宽视口 + 窄侧栏」用，视口 `≤720px` 时由 CSS 断点覆盖）；并按视口收高度——
  图取 `max(210, min(原高度, innerWidth*0.8))`，表格取 `innerHeight*0.6`，
  卡片最小高度同步（原值存在 `data-eazy-h` / `data-eazy-mh`，宽屏自动还原）。

实测 390px 宽的手机上 Streamlit 页面横向溢出从 54px 降到 0（KPI 2×2、每张约 177px，图表卡 366px 整行、
KPI 数字无裁切），375px 同理；768px 平板与 1440px 桌面仍是两列。**桌面端外观不变。**

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
