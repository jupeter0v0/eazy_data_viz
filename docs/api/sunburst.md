# `sunburst` — 旭日图（用同心环表达层级占比）

旭日图把多层分类画成同心圆环：最内圈是第一层，向外依次是下一层，每个扇区的角度代表它在父节点中的占比。它能在同一张图里同时展示“层级结构”和“每层占比”，点击节点还能聚焦到某个分支。

适合 3 层以内、每层 3~10 个类目的组织结构/商品类目/地区层级；层数太深或叶子过多会变成一圈细线。

- **适合**：需要同时看层级与占比（大区 → 省份 → 城市、品类 → 子品类），且总节点数在几十到一两百之间。
- **不适合**：只需要总排名、或层级很浅（一层）时不要用；叶子节点上千时也不要——环会碎成无法点击的细缝。

> 本页所有示例均可直接复制运行：先 `import eazy_data_viz as edv`，再 `df = edv.sample_df()`。

## 函数签名

```python
eazy_data_viz.sunburst(
    data,
    path,
    value=None,
    *,
    agg='sum',
    sort='desc',
    top_n=None,
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    fmt='compact',
    height=460,
    theme='light',
    legend=False,
    labels=True,
    zoom=False,
    link=None,
    max_rows=200000,
) -> Chart
```

参数按签名顺序：`data` → 本图专有参数 → 关键字参数（`*` 之后全部只能按关键字传）。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | pandas.DataFrame（也接受 dict / list，内部会转成 DataFrame） | 无 | 是 | 数据源（DataFrame） |
| `path` | str 或 list[str] | 无 | 是 | 层级列名列表（由内到外） |
| `value` | str 或 None | None | 否 | 数值列（决定扇区角度） |
| `agg` | str | 'sum' | 否 | 聚合方式（同一类目多条记录时如何合并） |
| `sort` | str 或 None | 'desc' | 否 | 排序方式 |
| `top_n` | int 或 None | None | 否 | 只保留前 N 项 |
| `title` | str 或 None | None | 否 | 图表主标题 |
| `subtitle` | str 或 None | None | 否 | 副标题（口径/单位/时间范围） |
| `xtitle` | str 或 None | None | 否 | X 轴标题 |
| `ytitle` | str 或 None | None | 否 | Y 轴标题 |
| `fmt` | str | 'compact' | 否 | 数值格式（tooltip / 标签） |
| `height` | int | 460 | 否 | 画布高度（像素） |
| `theme` | str | 'light' | 否 | 主题（浅色 / 深色） |
| `legend` | bool 或 None | False | 否 | 是否显示图例 |
| `labels` | bool | True | 否 | 是否显示数据标签 |
| `zoom` | bool 或 str | False | 否 | 缩放/漫游 |
| `link` | str 或 None | None | 否 | 联动分组名 |
| `max_rows` | int | 200000 | 否 | 嵌入前端的最大行数 |

> 共 18 个参数。签名里 `*` 之后是 keyword-only，必须写参数名；`data` 之前的位置参数（本图专有）可以按位置传。

## 参数详解

### `data` — 数据源（DataFrame）（`pandas.DataFrame`，必填）

- **作用**：图的原始数据。函数会按参数名从里面取列：`data` 既可以是 `pandas.DataFrame`，也可以是 `dict`（列名 → 值序列）或 `list`（记录列表），内部通过 `ensure_frame()` 统一转换。转换后必须至少有 1 行，否则报 `ValueError`。每张图最多嵌入 40 列（`MAX_COLS=40`），超过的部分会被丢弃并写入 `chart.warnings["warnings"]`。
- **建议**：首选 `pandas.DataFrame`；列名建议保持唯一、非空，中文列名可以直接用。 数值列用数值 dtype（`int64/float64`）；文本数字请先 `pd.to_numeric()`。 日期列用 `datetime64[ns]`（或可被 `pd.to_datetime()` 解析的字符串）。 作图前先处理空值：不同图对空值的策略不同（见各函数“常见问题”）。
- **示例**：`edv.sunburst(data=df, path=["大区", "省份"], value="销售额")`
- **报错**：传入空 DataFrame：`ValueError: 数据为空（0 行），无法绘图。`；传入 `None`：`ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`

### `path` — 层级列名列表（由内到外）（`str | list[str]`，必填）

- **作用**：按从内圈到外圈的顺序给出列名。传单个字符串等价于一层。列表不能为空，且每一列都必须在 `data` 中存在。层与层之间是“父 → 子”的包含关系：同一父节点下的子节点共享一段角度。
- **建议**：2~3 层最易读：`["大区", "省份"]`、`["产品", "渠道"]`。 第一层基数控制在 3~8，第二层每父节点 3~10。 不要超过 4 层；第 4 层开始环宽不足 10px。
- **示例**：`edv.sunburst(df, value="销售额", path=["大区", "省份"])`
- **报错**：`path=[]`：`ValueError: sunburst 需要 path（层级列名列表），例如 sunburst(df, ["大区", "品类"], value="销售额")。`；`path=["大区", "不存在"]`：`KeyError: "path[1]列 '不存在' 不存在。当前可用的列有：..."`

### `value` — 数值列（决定扇区角度）（`str | None`，默认 `None`）

- **作用**：用于计算每个节点大小的数值列。每个节点角度 ∝ 该节点聚合值 / 父节点聚合值。不传时按记录条数计（`agg="count"`）。
- **建议**：用可加总的指标（销售额、订单数），不要用率值（利润率、转化率）——层级求和没有意义。 想表达“记录条数”就省略 `value`。 含负值会破坏“占比”语义，先确保数值 ≥0。
- **示例**：`edv.sunburst(df, path=["大区", "省份"], value="销售额")`
- **报错**：传文本列：`TypeError: value（数值）列 '产品' 需要是数值类型（当前是文本，例如 [...]）。请先用 pd.to_numeric() 清洗，或换一列。`

### `agg` — 聚合方式（同一类目多条记录时如何合并）（`str`，默认 `'sum'`）

- **作用**：同一分类下有多条记录时，把数值列合成一个数的方法。可选：`sum`（默认）、`mean`、`count`、`max`、`min`、`median`。当函数没有拿到数值列（例如没传 `values`/`value`）时，内部会把 `agg` 强制为 `count`，按记录条数统计。 本图实现：逐层构建树，每层节点值由 `agg` 聚合；未传 `value` 时强制 `count`。
- **建议**：金额、订单数用 `sum`；单价、率值用 `mean` 或 `median`。 想看“有多少条记录”就传 `agg="count"`，此时数值列只作存在性检查。 `median` 对极端值更稳健，适合客单价、利润率这类偏态指标。
- **示例**：`edv.sunburst(df, path=["大区", "省份"], value="销售额", agg="mean")`
- **报错**：`agg="average"`：`ValueError: agg='average' 不支持，可选：sum, mean, count, max, min, median`

### `sort` — 排序方式（`str | None`，默认 `'desc'`）

- **作用**：控制分类的排列顺序。本库只认 `"asc"`、`"desc"`、`"x"`、`"none"` 四种语义，但**不做枚举校验**：传其他字符串不会报错，会静默按该图默认顺序渲染。 本图实现：**不生效**。层级节点按数据首次出现顺序构建，传 `asc/desc` 不会改变顺序。
- **建议**：排行榜用 `asc/desc`；时间序列用 `x`（按列顺序/时间升序）。 需要保持数据原始顺序时传 `sort="none"`。 分类是 `pd.Categorical`（如 `月份`）时，`x` 会按分类顺序而不是字母序。
- **示例**：`edv.sunburst(df, path=["大区", "省份"], value="销售额", sort="asc")`
- **报错**：不存在的值不报错：`sort="DESC"` 会被忽略并按默认顺序渲染（大小写敏感）。；对不读取 `sort` 的图（如 pyramid/sunburst/sankey）传任何值都不会改变图形。

### `top_n` — 只保留前 N 项（`int | None`，默认 `None`）

- **作用**：按当前排序只保留前 N 个类目，`None`（默认）表示全部保留。必须是 ≥1 的整数（`bool` 不算）。不同函数对“多出来的部分”处理不同：rose 会把剩余项合并成“其他”，wordcloud 直接截断，其余函数多数不读取该字段。 本图实现：**不生效**。层级树始终完整构建。
- **建议**：类目超过 12 个时用 `top_n` 收敛，避免标签重叠。 玫瑰图配 `top_n` 会得到“其他”扇区，其余图不会。 配合 `sort="desc"` 使用才有“前 N 大”的含义。
- **示例**：`edv.sunburst(df, path=["大区", "省份"], value="销售额", top_n=5)`
- **报错**：`top_n=0`：`ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`；`top_n=True`：同样报错（`bool` 被显式拒绝）。

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在卡片顶部的主标题。传 `None` 时使用函数内置的自动标题；传字符串则完全覆盖自动标题。标题只影响展示，不参与数据聚合与排序。
- **建议**：建议 8~18 个汉字，写清“指标 + 维度 + 口径”，例如 `销售额 按 大区`。 时间范围、币种、口径放在 `subtitle`，不要全部堆进标题。 标题是单行布局，过长会被卡片宽度截断，不建议加换行符。
- **示例**：`edv.sunburst(df, path=["大区", "省份"], value="销售额", title="华东区销售构成")`

### `subtitle` — 副标题（口径/单位/时间范围）（`str | None`，默认 `None`）

- **作用**：标题下方的第二行说明，常用于补充统计口径、单位、时间范围或“较上期 +8%”这类结论。默认 `None`，不显示副标题；传空字符串等同于不显示。
- **建议**：写口径而不重复标题，例如 `2024 年 1-12 月 · 含税`。 颜色比标题浅，信息量控制在 30 字以内。 需要换行时直接写 `\n` 不会被解析成 HTML，建议保持单行。
- **示例**：`edv.sunburst(df, path=["大区", "省份"], value="销售额", subtitle="2024 年 1-12 月 · 含税")`

### `xtitle` — X 轴标题（`str | None`，默认 `None`）

- **作用**：横轴标题。传 `None` 时横轴使用列名作为轴名；传字符串则覆盖。该字段只对直角坐标系有效（玫瑰图/旭日图/树图/关系图等没有 X 轴的图形不会显示）。 本图实现：**不生效**（旭日图没有坐标轴）。
- **建议**：写字段含义而不是字段名，例如 `日期`、`大区`、`广告投入（万元）`。 带单位的量把单位写进轴标题，数值格式交给 `fmt`。 分类轴很短时可以不写轴标题，避免和类目标签重复。
- **示例**：`edv.sunburst(df, path=["大区", "省份"], value="销售额", xtitle="日期")`

### `ytitle` — Y 轴标题（`str | None`，默认 `None`）

- **作用**：纵轴标题。传 `None` 时纵轴使用数值列名作为轴名；传字符串则覆盖。部分无直角坐标系的图会把 `ytitle` 用在 tooltip 的数值行标签上。 本图实现：**不生效**（旭日图没有坐标轴）。
- **建议**：带单位，例如 `销售额（元）`、`订单数（单）`。 百分比的图直接写 `占比`，并把 `fmt="percent"`。 与 `xtitle` 风格保持一致。
- **示例**：`edv.sunburst(df, path=["大区", "省份"], value="销售额", ytitle="销售额（元）")`

### `fmt` — 数值格式（tooltip / 标签）（`str`，默认 `'compact'`）

- **作用**：控制数值在 tooltip、数据标签、右端读数里的显示格式，不改变原始数据。可选值：`compact`（默认，≥1 亿显示“x.x亿”、≥1 万显示“x.x万”、否则千分位）、`thousands`（千分位，如 `1,234,567`）、`raw`（原样，最多 3 位小数）、`percent`（一位小数加 `%`，如 `12.3%`）、`currency`（`¥` + 千分位 + 两位小数）。 本图实现：控制 tooltip 中的数值；节点标签固定显示类目名。
- **建议**：金额大数用 `compact`，表格/财务口径用 `thousands` 或 `currency`。 已经是百分数的列用 `percent`，不要再乘 100。 同一页多张图保持一致的 `fmt`，避免“万/千分位”混排。
- **示例**：`edv.sunburst(df, path=["大区", "省份"], value="销售额", fmt="thousands")`
- **报错**：`fmt="commas"`：`ValueError: fmt='commas' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）（`int`，默认 `460`）

- **作用**：单张图的容器高度，单位像素，最小 120。不同函数的默认高度不同（本函数默认值见参数总览）。高度只影响画布，不改变数据；图例/标题/坐标轴会自动占用内部空间。
- **建议**：普通看板 320~460；层级图/关系图建议 ≥420。 多张图并排时高度取一致，视觉更整齐。 `height` 小于 120 会直接报错，不要用它做“隐藏图”。
- **示例**：`edv.sunburst(df, path=["大区", "省份"], value="销售额", height=520)`
- **报错**：`height=100`：`ValueError: height 至少 120（像素），收到 100`；`height="400"`：同样报错（必须是 `int/float`）。

### `theme` — 主题（浅色 / 深色）（`str`，默认 `'light'`）

- **作用**：页面主题，只支持 `"light"`（默认，白底深字）和 `"dark"`（深底浅字）。主题会同时改变背景、文字、坐标轴、tooltip 和默认色板的取色（`theme.palette`）。
- **建议**：常规报表/打印用 `light`；大屏、夜间模式用 `dark`。 多图看板统一主题，不要一张亮一张暗。 深色下避免使用低饱和的 `morandi` 色板，对比度会不够。
- **示例**：`edv.sunburst(df, path=["大区", "省份"], value="销售额", theme="dark")`
- **报错**：`theme="blue"`：`ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `legend` — 是否显示图例（`bool | None`，默认 `False`）

- **作用**：是否显示图例。`None` 表示“按语义自动决定”（有色分组时显示、没有分组时隐藏），`True`/`False` 为强制开关。只有真正用颜色/名称区分系列的函数才会生效。 本图实现：**不生效**。旭日图不带图例，颜色只用于区分同级节点。
- **建议**：类目多且颜色即含义（产品、渠道）时保留图例。 图例项超过 10 个时图例会滚动，建议先 `top_n` 或合并小类。 单系列图关闭图例，把空间留给图形。
- **示例**：`edv.sunburst(df, path=["大区", "省份"], value="销售额", legend=False)`
- **报错**：无校验：传非布尔值会经 `bool()` 转换（非空字符串为 `True`）。

### `labels` — 是否显示数据标签（`bool`，默认 `True`）

- **作用**：是否在图形上直接显示文字标签（类目名/数值/百分比）。默认值因函数而异；有的函数固定显示标签、不支持关闭。 本图实现：**不生效**。节点标签始终显示，无法关闭。
- **建议**：类目 ≤8 个时打开标签，读者不用来回看 tooltip。 数据密集（散点、关系图）时关闭，避免文字糊成一片。 百分比标签通常配合 `fmt="percent"`。
- **示例**：`edv.sunburst(df, path=["大区", "省份"], value="销售额", labels=False)`
- **报错**：无校验：会经 `bool()` 转换，传 `"no"` 也是 `True`。

### `zoom` — 缩放/漫游（`bool | str`，默认 `False`）

- **作用**：是否开启缩放。多数函数接受 `bool`；`candlestick` 默认 `"auto"`，表示分类数超过 30 时自动显示底部缩放条。不支持缩放的图会接受该参数但不产生效果。 本图实现：**不生效**。旭日图点击的是下钻/高亮，不是缩放；需要缩放请用 `roam`（未暴露）。
- **建议**：时间序列很长（>60 点）时用 `zoom=True` 或放到 `candlestick` 的 `"auto"`。 层级/关系图本身可拖拽缩放，不必再开 `zoom`。 截图/打印场景关掉缩放，画面更干净。
- **示例**：`edv.sunburst(df, path=["大区", "省份"], value="销售额", zoom=True)`

### `link` — 联动分组名（`str | None`，默认 `None`）

- **作用**：把多张图放进同一个联动组：点击某张图的类目，同组中包含该维度列的其他图会按该值过滤。同一个组名（如 `"g1"`）即可联动；默认 `None` 不联动。注意：`table`/`wordcloud` 是 HTML 渲染，只能作为**被联动方**，点击它们不会触发联动。 本图实现：点击某个层级节点会按当前层维度联动（`link` 组内其他图过滤）。
- **建议**：同一看板里的明细表用同一个 `link` 组名，点图即可筛表。 联动维度由点击的图决定，各图尽量共享同一列（如 `产品`）。 组名建议用有含义的英文/拼音，不要用随机串。
- **示例**：`edv.sunburst(df, path=["大区", "省份"], value="销售额", link="g1")`
- **报错**：无校验：传数字/对象会原样写入 spec，JS 端作为对象键使用，建议只传字符串。

### `max_rows` — 嵌入前端的最大行数（`int`，默认 `200000`）

- **作用**：Python 侧只把前 `max_rows` 行（默认 20000）的数据嵌入 HTML，超过时按均匀间隔抽样，并把提示写入 `chart.warnings["warnings"]`。`table` 特殊：默认 200，且最终最多嵌入 200 行。抽样只发生在“嵌入”阶段，不影响函数内已经算好的统计（如相关系数、回归系数）。
- **建议**：前端交互图保持默认 20000 即可；超大表用 `table(max_rows=...)` 控制体积。 需要完整数据时导出 Excel/CSV，不要让 HTML 承担全量数据。 抽样后 tooltip 的明细行数会变少，但聚合图的总量不受影响。
- **示例**：`edv.sunburst(df, path=["大区", "省份"], value="销售额", max_rows=500)`
- **报错**：无校验：传 `0` 或负数会得到空数据（图形空白），建议传正整数。

## 返回值

返回 `eazy_data_viz.Chart` 对象（`chart.spec` 是完整的渲染 spec，`chart.data` 是嵌入前端的数据）。

- 通用方法：`chart.save(path)` 写单文件 HTML、`chart.to_html()` 返回字符串、`chart.palette(name)` 链式换色、`chart.show()` 在浏览器打开；`chart.warnings` 记录采样等降级提示（详见 [交互与联动指南](../guides/06-interaction.md)）。

本图的关键 spec 字段（`chart.spec`）：

| 字段 | 含义 |
| --- | --- |
| `type` | 固定为 `"sunburst"`。 |
| `roles` | `{"path": [层级列...], "value": 数值列或 None}`。 |
| `agg` | 每层节点的聚合方式；未传 `value` 时为 `"count"`。 |
| `labels / legend / sort / topN / zoom` | 签名保留，但当前 builder 均不读取（节点标签固定显示）。 |
| `xtitle / ytitle / xlim / ylim` | 签名保留，但旭日图无坐标轴，不生效。 |

## 完整示例

以下示例全部基于 `edv.sample_df()`（1500 行、11 列）或由它派生的小表；输出文件写到 `examples/output/`。

### 示例 1：最简两层旭日图

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.sunburst(df, path=["大区", "省份"], value="销售额")
chart.save("examples/output/sunburst_1.html")
```

**输出**：内圈四个大区、外圈是各大区下的省份；扇区角度按销售额分配，悬停显示“大区 / 省份”完整路径与数值；自动标题“销售额 层级构成”。

### 示例 2：典型：产品 → 渠道三层结构

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.sunburst(
    df,
    path=["产品", "渠道"],
    value="订单数",
    title="产品 × 渠道 层级占比",
    height=520,
)
chart.save("examples/output/sunburst_2.html")
```

**输出**：内圈四大产品线、外圈对应渠道；高度 520px 让三层环（内圈 12%~42%，中环 42%~72%）都清晰可点，标签只在外环切向显示。

### 示例 3：进阶：三层下钻到城市

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.sunburst(
    df,
    path=["大区", "省份", "城市"],
    value="销售额",
    title="大区 → 省份 → 城市",
    height=620,
)
chart.save("examples/output/sunburst_3.html")
```

**输出**：三层同心环由内向外展开；由于浏览器可点击，点内圈某个大区会以它为根重新布局（ECharts 的 `rootToNode`），点中心可返回全量。

### 示例 4：不传数值：按记录条数决定角度

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.sunburst(df, path=["渠道", "产品"], title="渠道 × 产品 记录结构")
chart.save("examples/output/sunburst_4.html")
```

**输出**：角度由记录条数决定（每类约 1/4）；tooltip 显示“记录数”而不是金额；适合先看数据覆盖是否均衡。

### 示例 5：深色主题 + 自定义配色

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.sunburst(df, path=["大区", "产品"], value="销售额", theme="dark")
chart.palette("echarts")
chart.save("examples/output/sunburst_5.html")
```

**输出**：深色背景上同心环使用 ECharts 默认色，颜色按第一层节点分配、子节点继承父色并降低透明度，层级越深越淡。

## 常见问题 / 注意事项

- **旭日图和树图、矩形树图（treemap）怎么选？** 旭日图用角度表达占比、适合看“每层占父级多少”；树图用连线表达层级、适合看“结构关系”；treemap 用面积表达大小、适合叶子很多的情况。本库三者的入口分别是 `sunburst`、`tree`，其中 treemap 属于基础图表。
- **为什么节点标签关不掉？** 当前 JS 的 `label.show` 恒为 `true`，没有读取 `spec.labels`。如果标签太密，只能减少层级/类目数量，或把图放大（`height=620`）。
- **点击节点后怎么返回上一层？** ECharts 旭日图点击节点会以该节点为根重新布局，点击圆心（root）即可回到全量视图；这是 ECharts 自带交互，不需要额外参数。
- **能显示具体数值而不是只有类目名吗？** 节点标签固定显示类目名；数值在 tooltip 里。需要常驻数值请用 `bar` 或 `treemap`（基础图表）。
- **`top_n` 能只保留前 N 个分支吗？** 不能。本函数的 `top_n` 不会生效，层级树始终完整构建。需要裁剪请先过滤 `data`：例如只保留销售额前 6 的省份。

## 相关图表

| 图表 | 说明 |
| --- | --- |
| [`tree`](tree.md) | 树图（更强调父子层级结构、可折叠展开） |
| [`rose`](rose.md) | 南丁格尔玫瑰图（只有一层构成、想强调排名时用它） |
| [`pyramid`](pyramid.md) | 金字塔图（阶段收敛型的构成对比） |
| [`sankey`](sankey.md) | 桑基图（看层级之间的流量去向而不是占比时用它） |

- 回到总览：`docs/EXTRA_CHARTS.md`、`docs/AI_GUIDE.md`
