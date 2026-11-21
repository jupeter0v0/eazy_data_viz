# `sankey` — 桑基图（用带宽表达流量大小的多级流向图）

桑基图把流量画成一条条粗细不同的带子，带宽与数值成正比，节点按层级自动从左到右排布。它擅长回答“东西从哪来、到哪去、各占多少”，例如 大区 → 渠道 → 产品 的转化与分摊。

有两种写法（二选一）：

- **两级**（`source` + `target`）：每条记录是一条边，同一对 (source, target) 按 `agg` 聚合。
- **多级**（`path`）：给一串层级列，1.5 起按相邻两级自动画多层（`path[0]→path[1]`、`path[1]→path[2]`…），不需要手工拼边。跨层同名值（例如「华东」既是 `大区` 也是 `渠道`）会当作两个不同节点，不会被合并。

节点总量由流入/流出自动汇总，不需要额外计算。

- **适合**：有明确方向与流量的分层数据：大区→渠道→产品、预算→部门→项目；节点数 5~40、层数 2~4。
- **不适合**：没有方向、或只想看两列交叉计数时用 `matrix`/`heatmap`；只是层级占比（不分流）用 `sunburst`。

> 本页所有示例均可直接复制运行：先 `import eazy_data_viz as edv`，再 `df = edv.sample_df()`。

## 函数签名

```python
eazy_data_viz.sankey(
    data,
    source=None,
    target=None,
    value=None,
    *,
    path=None,
    agg='sum',
    sort=None,
    top_n=None,
    title=None,
    subtitle=None,
    fmt='compact',
    height=420,
    theme='light',
    legend=False,
    labels=True,
    zoom=False,
    link=None,
    max_rows=200000,
) -> Chart
```

`source`/`target` 与 `path` 是**互斥**的两套写法：给了 `path` 就不要再给 `source`/`target`（会报 `ValueError`），反之亦然。参数按签名顺序：`data` → 本图专有参数 → 关键字参数（`*` 之后全部只能按关键字传）。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | pandas.DataFrame（也接受 dict / list，内部会转成 DataFrame） | 无 | 是 | 数据源（DataFrame） |
| `source` | str 或 None | None | 否 | 两级写法的起点列；与 `path` 互斥 |
| `target` | str 或 None | None | 否 | 两级写法的终点列；与 `path` 互斥 |
| `value` | str 或 None | None | 否 | 边的权重列（流量） |
| `path` | list 或 None | None | 否 | 多级写法的层级列，`[一级, 二级, 三级…]` |
| `agg` | str | 'sum' | 否 | 聚合方式（同一对上下级多条记录时如何合并） |
| `sort` | str 或 None | None | 否 | 排序方式（本图不生效） |
| `top_n` | int 或 None | None | 否 | 只保留前 N 项（本图不生效） |
| `title` | str 或 None | None | 否 | 图表主标题 |
| `subtitle` | str 或 None | None | 否 | 副标题（口径/单位/时间范围） |
| `fmt` | str | 'compact' | 否 | 数值格式（tooltip / 标签） |
| `height` | int | 420 | 否 | 画布高度（像素） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | str | 'light' | 否 | 主题（浅色 / 深色） |
| `legend` | bool 或 None | False | 否 | 是否显示图例 |
| `labels` | bool | True | 否 | 是否显示数据标签 |
| `zoom` | bool 或 str | False | 否 | 缩放/漫游（本图不生效，节点本身可拖拽） |
| `link` | str / tuple / dict | None | 否 | 联动分组名（可带方向：双向/单向进/单向出） |
| `max_rows` | int | 200000 | 否 | 嵌入前端的最大行数 |

> 共 18 个参数。签名里 `*` 之后是 keyword-only，必须写参数名；`data` 之前的位置参数（本图专有）可以按位置传。

## 参数详解

### `data` — 数据源（DataFrame）（`pandas.DataFrame`，必填）

- **作用**：图的原始数据。函数会按参数名从里面取列：`data` 既可以是 `pandas.DataFrame`，也可以是 `dict`（列名 → 值序列）或 `list`（记录列表），内部通过 `ensure_frame()` 统一转换。转换后必须至少有 1 行，否则报 `ValueError`。每张图最多嵌入 40 列（`MAX_COLS=40`），超过的部分会被丢弃并写入 `chart.warnings["warnings"]`。
- **建议**：首选 `pandas.DataFrame`；列名建议保持唯一、非空，中文列名可以直接用。 数值列用数值 dtype（`int64/float64`）；文本数字请先 `pd.to_numeric()`。 日期列用 `datetime64[ns]`（或可被 `pd.to_datetime()` 解析的字符串）。
- **示例**：`edv.sankey(data=df, path=["大区", "渠道", "产品"], value="销售额")`
- **报错**：传入空 DataFrame：`ValueError: 数据为空（0 行），无法绘图。`；传入 `None`：`ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`

### `source` — 两级写法的起点列（`str | None`，默认 `None`）

- **作用**：每个取值是一个起始节点；与 `target` 共同构成有向边。缺失值按 `(空)` 处理。只在两级写法里使用，必须和 `target` 一起给。
- **建议**：上游维度：`渠道`、`大区`。 超过两级时改用 `path=[...]`，不要再手工拼边。 `source == target` 的自环会被跳过。
- **示例**：`edv.sankey(df, source="渠道", target="产品", value="销售额")`
- **报错**：只给 `source` 不给 `target`：`ValueError: sankey 需要 path（多级）或 source / target（两级），例如 sankey(df, path=["大区", "渠道", "产品"], value="销售额")。`；与 `path` 同时给：`ValueError: sankey 的 path 与 source/target 不能同时使用：多级流量用 path=["一级", "二级", "三级"]，两级流量用 source= / target=。`；列名写错：`KeyError: "path[0]（第 1 级）列 '不存在' 不存在。当前可用的列有：..."`

### `target` — 两级写法的终点列（`str | None`，默认 `None`）

- **作用**：每个取值是一个到达节点。`source == target` 的自环会被 JS 跳过（不画）。只在两级写法里使用，必须和 `source` 一起给。
- **建议**：下游维度：`产品`、`大区`。 自环、空值、非正数的边会被静默丢弃，作图前建议先检查。 值必须可加总（流量），不要用率值。
- **示例**：`edv.sankey(df, source="渠道", target="产品", value="销售额")`

### `path` — 多级写法的层级列（`list | None`，默认 `None`）

- **作用**：按顺序给出从上游到下游的层级列，例如 `path=["大区", "渠道", "产品"]`。前端按相邻两级自动建边：`大区→渠道`、`渠道→产品`，同一行的值会沿整条路径串起来，所以一条记录会在每一层各贡献一次流量。
- **跨层同名不合并**：节点以「层级 + 值」区分，「华东」作为 `大区` 和作为 `渠道` 是两个独立节点，点击时回传的维度也不同（分别是 `大区` / `渠道`）。
- **建议**：2~4 层最易读；层数越多单层节点越挤，可配合 `height` 放大画布。 列顺序必须是“上游在前、下游在后”，反过来会画出倒流。 需要给节点加上限时先在 Python 里聚合（`groupby`）再传入。
- **示例**：
  ```python
  edv.sankey(df, path=["大区", "渠道", "产品"], value="销售额")
  ```
- **报错**：`path` 少于两级：`ValueError: sankey 至少需要 2 级：path=[一级, 二级]，收到 1 级。`；同一列重复出现：`ValueError: sankey 的 path 里不能有重复列：['渠道', '渠道']。同一列不能同时当两级。`；与 `source`/`target` 同时给：`ValueError: sankey 的 path 与 source/target 不能同时使用：...`

### `value` — 边的权重列（`str | None`，默认 `None`）

- **作用**：决定带子粗细的数值列；不传时 `agg` 被强制为 `count`，粗细=记录条数。同一对上下级的多行按 `agg` 合并，最终值保留 3 位小数。
- **建议**：流量类指标：`销售额`、`订单数`、`客户数`。 非正数会被丢弃：值为 0 或负的边在图上不存在。 不传值时按条数计，适合先看数据是否连成一张网。
- **示例**：`edv.sankey(df, path=["大区", "渠道", "产品"], value="销售额")`
- **报错**：传文本列：`TypeError: value（数值）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `agg` — 聚合方式（同一对上下级多条记录时如何合并）（`str`，默认 `'sum'`）

- **作用**：同一对上下级有多条记录时，把数值列合成一个数的方法。可选：`sum`（默认）、`mean`、`count`、`max`、`min`、`median`。当函数没有拿到数值列（例如没传 `value`）时，内部会把 `agg` 强制为 `count`，按记录条数统计。 本图实现：对每一组相邻层级 `(path[i], path[i+1])` 分别用 `agg` 聚合流量。
- **建议**：金额、订单数用 `sum`；单价、率值用 `mean` 或 `median`。 想看“有多少条记录”就传 `agg="count"`，此时数值列只作存在性检查。
- **示例**：`edv.sankey(df, path=["大区", "渠道"], value="销售额", agg="mean")`
- **报错**：`agg="average"`：`ValueError: agg='average' 不支持，可选：sum, mean, count, unique, max, min, median`

### `sort` — 排序方式（`str | None`，默认 `None`）

- **作用**：控制分类的排列顺序。本库只认 `"asc"`、`"desc"`、`"x"`、`"none"` 四种语义，但**不做枚举校验**：传其他字符串不会报错，会静默按该图默认顺序渲染。 本图实现：**不生效**。流向右左布局由节点层级自动分层，与类目顺序无关。
- **建议**：排行榜用 `asc/desc`；时间序列用 `x`（按列顺序/时间升序）。 需要保持数据原始顺序时传 `sort="none"`。
- **示例**：`edv.sankey(df, path=["大区", "渠道"], value="销售额", sort="asc")`

### `top_n` — 只保留前 N 项（`int | None`，默认 `None`）

- **作用**：按当前排序只保留前 N 个类目，`None`（默认）表示全部保留。必须是 ≥1 的整数（`bool` 不算）。 本图实现：**不生效**。所有层级的所有节点都会绘制。
- **建议**：节点超过 20 个时先在 Python 里 `groupby().nlargest()` 收敛，或把尾部合并成“其他”，否则标签会重叠。

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：不传时自动生成 `"大区 → 渠道 → 产品 流向"`（按 `path` 拼）；两级写法是 `"渠道 → 产品 流向"`。
- **建议**：看板里标题尽量短；口径写在 `subtitle`。

### `subtitle` — 副标题（`str | None`，默认 `None`）

- **作用**：标题下方的小字，适合写口径、单位、时间范围。

### `fmt` — 数值格式（`str`，默认 `'compact'`）

- **作用**：tooltip 与标签里数值的格式。可选 `compact`（万/亿缩写）、`thousands`（千分位）、`raw`（原样）、`percent`、`currency`。
- **示例**：`edv.sankey(df, path=["大区", "渠道"], value="利润", fmt="currency")`

### `height` — 画布高度（`int`，默认 `420`）

- **作用**：卡片里图表的像素高度。层数多或节点多时调大，节点会更舒展。

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题（`light` / `dark`）（`str`，默认 `'light'`）

- **作用**：单图主题；看板里也可用右上角 ◐ 统一切换。

### `legend` — 是否显示图例（`bool | None`，默认 `False`）

- **作用**：本图固定不显示图例（节点本身带标签），传 `True` 也不会出现图例。

### `labels` — 是否显示数据标签（`bool`，默认 `True`）

- **作用**：节点上的文字标签。标签显示的是真实值（不是内部编码）；节点太挤时前端会隐藏重叠标签（`labelLayout.hideOverlap`）。传 `False` 可隐藏，只留 tooltip。

### `zoom` — 缩放/漫游（`bool | str`，默认 `False`）

- **作用**：是否开启缩放。本图实现：**不生效**。节点可拖拽，但不是缩放。

### `link` — 联动分组名与方向（`str | tuple | dict`，默认 `None`）

- **作用**：把多张图放进同一个联动组：点击某张图的节点/类目，同组中包含该维度列的其他图会按该值过滤。三种方向：
  - `link="g1"` 或 `link=("g1", "both")`：**双向**（默认），既能发起也能被联动。
  - `link=("g1", "out")`：**单向出**，只发起联动，自己永远不过滤（适合“总览图/筛选器”）。
  - `link=("g1", "in")`：**单向进**，只接收联动，点它不会改变其它图（适合“明细图”）。
  - 也支持字典写法：`link={"group": "g1", "direction": "out"}`。
  - 本图实现：点击节点按该节点所在**层级列**联动——点 `大区` 层节点回传 `大区=华东`，点 `渠道` 层节点回传 `渠道=线上`；点连线（带子）不触发联动。
- **建议**：总览桑基用 `"out"`，明细表用 `"in"`，避免互相覆盖选中态。 联动维度由点击的节点层级决定，各图尽量共享同一批列。
- **示例**：
  ```python
  sk = edv.sankey(df, path=["大区", "渠道", "产品"], value="销售额", link=("k1", "out"))
  tbl = edv.table(df, groupby={"columns": ["大区"], "value": "销售额"}, link=("k1", "in"))
  edv.dashboard(sk, tbl).save("examples/output/sankey_link.html")
  ```
- **报错**：方向写错：`ValueError: link 的方向只支持 "both"（双向）/ "out"（单向出）/ "in"（单向进），收到 'up'。`；字典键写错：`ValueError: link 字典只支持 group / name / direction / mode 四个键，收到未知键：groupby。`

### `max_rows` — 嵌入前端的最大行数（`int`，默认 `2000000`）

- **作用**：Python 侧只把前 `max_rows` 行数据嵌入 HTML，超过时按均匀间隔抽样，并把提示写入 `chart.warnings["warnings"]`。抽样只发生在“嵌入”阶段。
- **建议**：多级桑基的行数会放大成多份流量，建议先用 Python 聚合成“边表”再传入，可显著减小 HTML 体积。

## 返回值

返回 `eazy_data_viz.Chart` 对象（`chart.spec` 是完整的渲染 spec，`chart.data` 是嵌入前端的数据）。

- 通用方法：`chart.save(path)` 写单文件 HTML、`chart.to_html()` 返回字符串、`chart.palette(name)` 链式换色、`chart.show()` 在浏览器打开；`chart.warnings` 记录采样等降级提示（详见 [交互与联动指南](../guides/06-interaction.md)）。

本图的关键 spec 字段（`chart.spec`）：

| 字段 | 含义 |
| --- | --- |
| `type` | 固定为 `"sankey"`。 |
| `roles` | 多级写法 `{"path": [一级, 二级, …], "value": 权重列或 None}`；两级写法 `{"path": [source, target], "value": …}`。 |
| `link / linkMode` | 联动组名与方向（`both` / `out` / `in`）。 |
| `nodes / links` | 由 JS 在浏览器端按相邻层级聚合出的节点与边数组（不在 spec 中，Python 不预计算）。节点内部用「层级+值」编码，点击时还原成真实的 (维度, 值)。 |
| `agg` | 聚合方式；未传 `value` 时强制 `"count"`。 |
| `labels / legend / sort / top_n / zoom` | 签名保留，但 builder 固定显示节点标签、不显示图例、不排序也不裁剪。 |

## 完整示例

以下示例全部基于 `edv.sample_df()`（1500 行、11 列）；输出文件写到 `examples/output/`。

### 示例 1：最简：渠道 → 产品

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.sankey(df, source="渠道", target="产品", value="销售额")
chart.save("examples/output/sankey_1.html")
```

**输出**：左侧三个渠道节点、右侧四个产品节点，12 条带子按销售额粗细排布；节点颜色按层级取色，悬停带子显示“渠道 → 产品”与金额，悬停节点显示关联总量。

### 示例 2：多级：大区 → 渠道 → 产品（1.5 新写法）

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.sankey(
    df,
    path=["大区", "渠道", "产品"],
    value="销售额",
    height=560,
    title="大区 → 渠道 → 产品 流向",
)
chart.save("examples/output/sankey_2.html")
```

**输出**：三层从左到右展开（4 个大区 → 3 个渠道 → 4 个产品），每条记录沿整条路径贡献 4 + 3 + 4 条带子；同一行的值会从大区一路串到产品，避免“两级写法只能看一段”的断层。

### 示例 3：不传权重，按记录条数

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.sankey(
    df,
    path=["大区", "渠道"],
    title="大区 → 渠道 记录流向",
    height=460,
)
chart.save("examples/output/sankey_3.html")
```

**输出**：带子粗细=记录条数（`agg="count"`），4×3 共 12 条边；由于数据均匀，各带子粗细接近，适合检查数据覆盖。

### 示例 4：深色主题、货币格式与配色

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.sankey(
    df,
    path=["大区", "渠道", "产品"],
    value="利润",
    fmt="currency",
    theme="dark",
)
chart.palette("echarts")
chart.save("examples/output/sankey_4.html")
```

**输出**：深色背景上彩色带子 + 渐变透明；tooltip 中利润为“¥…”格式，节点标签自动转浅色。

### 示例 5：联动：点击任意层级的节点过滤明细

```python
import eazy_data_viz as edv

df = edv.sample_df()
sk = edv.sankey(df, path=["大区", "渠道", "产品"], value="销售额",
                link=("k1", "out"))
tbl = edv.table(df, groupby={"columns": ["大区"], "value": "销售额"}, link=("k1", "in"), limit=40)
edv.dashboard(sk, tbl, title="桑基图联动", cols=2).save("examples/output/sankey_5.html")
```

**输出**：点 `大区` 层节点 → 表格按“大区=该值”汇总；点 `渠道` 层节点 → 表格按“渠道=该值”汇总（汇总会跟着变，但表格本身是单向进，点它不会反向改桑基）。桑基自己用的是单向出，所以永远显示全量。

## 常见问题 / 注意事项

- **桑基图和热力图的区别？** 桑基图表达有向流量且带宽可比，适合看“从哪来到哪去”；热力图只表达两维交叉的强度，没有方向。
- **多级会不会把同一条记录重复计三次？** 会，而且这是预期行为：每一层都统计该记录在该层的流量，所以“大区”层的总量、“渠道”层的总量、“产品”层的总量各自独立，看的是每层的分摊，不是把三层加总。
- **跨层同名值怎么区分？** 节点内部用「层级序号 + 值」编码，因此「华东」作为大区和作为渠道是两个节点；点击回传的维度分别是 `大区` / `渠道`，联动过滤不会串。
- **带宽数值为什么保留 3 位小数？** JS 端对边值做了 `round(3)` 处理，避免浮点尾数导致的 tooltip 噪声；原始精度仍在 Python 数据里。
- **为什么有的边不见了？** 四类边会被丢弃：非数值（NaN）、值 ≤0、端点为空、source==target 的自环。这是业务上的合理过滤，但会静默发生。
- **`top_n` 能只画前 N 条边吗？** 不能。当前 builder 不读取 `top_n`。需要裁剪请先在 Python 里过滤/聚合边，再传入 `sankey`。
- **旧的两级写法还能用吗？** 能，`source=`/`target=` 完全兼容；两者只能二选一。

## 相关图表

| 图表 | 说明 |
| --- | --- |
| [`graph`](graph.md) | 关系图（没有方向、任意多对多关系时用它） |
| [`theme_river`](theme_river.md) | 主题河流图（流量随时间变化时用它） |
| [`sunburst`](sunburst.md) | 旭日图（层级占比而不是流量分摊） |
| [`matrix`](matrix.md) | 相关系数矩阵（数值列之间的相关结构） |

- 回到总览：`docs/EXTRA_CHARTS.md`、`docs/AI_GUIDE.md`
