# `waterfall` — 瀑布图：把增减项逐级累加

> 用一串“悬浮柱”表达从起点到终点的累计变化：每根柱从上一个累计值画到当前累计值，上涨一种颜色、下降另一种颜色，还可以在末尾补一根“合计”柱。
> 适合：利润/收入的增减拆解（哪个产品贡献了多少）、预算执行差异、用户数环比变化的归因。
> 不适合：单纯比较类目大小（用 `bar`）、看连续时间趋势（用 `line`）、看结构占比（用 `pie` / `treemap`）。

## 函数签名

```python
eazy_data_viz.waterfall(
    data,
    x,
    y=None,
    *,
    agg=None,
    total=None,
    sort=None,
    top_n=None,
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    xlim=None,
    ylim=None,
    fmt="compact",
    height=380,
    abs_height=False,
    colors=None,
    theme="light",
    legend=False,
    labels=False,
    zoom="auto",
    drill=None,
    link=None,
    max_rows=2000000,
) -> Chart
```

> `data` / `x` / `y` 是位置参数，其余全部是**关键字限定参数**（`*` 之后必须写成 `参数名=值`）。
> 参数个数 22：3 个位置参数 + 19 个关键字参数。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源，图表取数的唯一入口 |
| `x` | `str` | `—` | 是 | 类目轴列名，每个类目一根柱 |
| `y` | `str` | `None` | 否 | 增量数值列；省略表示统计记录数 |
| `agg` | `str` | `'sum'` | 否 | 同一类目多行时的聚合方式 |
| `total` | `bool` | `None` | 否 | 是否在末尾追加“合计”柱 |
| `sort` | `str` | `None` | 否 | 排序：x / asc / desc / none |
| `top_n` | `int` | `None` | 否 | 只保留前 N 项（当前版本不裁剪，见详解） |
| `title` | `str \| None` | `None` | 否 | 主标题，默认自动生成 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题（灰色小字） |
| `xtitle` | `str \| None` | `None` | 否 | 横轴（类目轴）标题 |
| `ytitle` | `str \| None` | `None` | 否 | 纵轴（数值轴）标题 |
| `xlim` | `tuple[float, float]` | `None` | 否 | 横轴范围（类目轴，本图不生效） |
| `ylim` | `tuple[float, float]` | `None` | 否 | 纵轴数值范围 |
| `fmt` | `str` | `'compact'` | 否 | 数值格式：compact / thousands / raw / percent / currency |
| `height` | `int` | `380` | 否 | 画布高度（像素，≥120） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `colors` | `dict \| None` | `None` | 否 | 给特定类目/系列指定颜色 |
| `theme` | `str` | `'light'` | 否 | light / dark |
| `legend` | `bool` | `False` | 否 | 是否显示图例（本图固定不显示） |
| `labels` | `bool` | `False` | 否 | 是否在柱顶标注增量数值 |
| `zoom` | `bool \| str` | `'auto'` | 否 | 类目轴缩放条（本图不支持） |
| `drill` | `str \| list[str]` | `None` | 否 | 逐级下钻维度 |
| `link` | `str` | `None` | 否 | 联动组名（同组图表互相筛选） |
| `max_rows` | `int` | `2000000` | 否 | 最大参与绘制行数（None 不采样） |

## 参数详解

### `data` — 数据源，图表取数的唯一入口（必填）

- **类型 / 默认值**：`pandas.DataFrame`、`dict`、`list`（每项一行）或 `Series` / 无
- **说明**：内部先经 `frame.ensure_frame()` 归一化成 DataFrame 再绘图：`DataFrame` 原样使用，`Series` 变单列，`dict` / `list` 自动转表。传入对象不会被原地修改；行数超过 `max_rows` 时均匀抽样，并把提示写进 `chart.warnings`。
- **取值建议**：正式代码一律传 DataFrame；`dict` / `list` 只用于快速试验。列名允许中文、空格与特殊字符，只要唯一即可。
- **报错**：`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`；`data=42` → `TypeError: 无法识别 data 类型 'int'，请传入 pandas.DataFrame（或 dict / list）。`

### `x` — 类目轴列名（必填）

- **类型 / 默认值**：`str` / 无
- **说明**：决定每根柱叫什么。同一 `x` 的多行会先按 `agg` 聚合成一个增量。它同时是下钻第一层：若 `drill[0]` 与 `x` 不同，内部会自动把 `x` 插到 `drill` 最前面。
- **取值建议**：传真实列名，不能是列序号或表达式。像“月份”这种有固定顺序的分类，先 `pd.Categorical(df["月份"], categories=[...], ordered=True)`，否则顺序取决于数据里首次出现的先后。
- **报错**：不传 → `TypeError: waterfall() missing 1 required positional argument: 'x'`；列名写错 → `KeyError: "x（类目）列 '不存在' 不存在。当前可用的列有：日期, 月份, 大区, 省份, 城市, 产品, 渠道, 销售额, 订单数, 利润, 客户数"`

### `y` — 增量数值列；None 表示统计记录数

- **类型 / 默认值**：`str` / `None`
- **说明**：每根柱的高度来自 `y` 的聚合值，正数向上累加、负数向下累加。省略 `y` 时改为统计每个类目的记录条数（内部把 `agg` 强制成 `count`），自动标题里的度量名变成「记录数」。
- **取值建议**：讲“增减归因”就传数值列；讲“各类目有多少条记录”就省略，例如 `waterfall(df, x="产品")`。
- **报错**：文本列 → `TypeError: y（数值）列 '产品' 需要是数值类型（当前是文本，例如 ['智能终端', '云服务', '行业软件']）。请先用 pd.to_numeric() 清洗，或换一列。`；日期列 → `TypeError: y（数值）列 '日期' 需要是数值类型，但当前是日期时间类型。请换一列。`

### `agg` — 同一类目多行的聚合方式

- **类型 / 默认值**：`str` / `'sum'`
- **说明**：`x` 相同的行先按 `agg` 折成一个数，再作为该段增量。可选 `sum` / `mean` / `count` / `max` / `min` / `median`。
- **取值建议**：金额、销量等可加指标用 `"sum"`；单价、转化率、客单价用 `"mean"`；想数条数用 `"count"`（等价于省略 `y`）。注意 `y=None` 时 `agg` 会被强制改成 `count`，此时传非法值**不会**报错。
- **报错**：`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, unique, max, min, median`

### `total` — 是否追加“合计”柱

- **类型 / 默认值**：`bool` / `None`
- **说明**：为真时在末尾追加一根「合计」柱，高度等于所有增量之和，颜色取调色板第 0 号（`palette[0]`）；该柱 tooltip 只显示累计值。内部按 `bool(total)` 处理，因此 `1`、`"yes"` 之类的真值都等价于 `True`。
- **取值建议**：汇报、月度经营分析一般传 `True`，让读者一眼看到净值；纯拆解、不关心总额时省略。
- **示例**：`total=True` → `chart.spec["total"] is True` 且末尾类目名为「合计」；`total=None` / `total=False` → `chart.spec["total"] is False`。

### `sort` — 类目顺序

- **类型 / 默认值**：`str` / `None`
- **说明**：`"x"` 按类目本身排序（日期、数值、有序分类按自然顺序），`"asc"` / `"desc"` 按增量大小排序，`None` 保持聚合顺序（即数据中 `x` 首次出现的顺序）。
- **取值建议**：**瀑布图的累计关系依赖顺序**，用 `"desc"` 会把累计曲线打乱成“从大到小依次累加”，通常没有业务含义；推荐保持 `None`，只有时间/有序分类才用 `"x"`。非法值（如 `"weird"`）不会报错，会原样写进 `spec` 并在前端按“不排序”处理。
- **示例**：`sort="x"`（月份 1月→12月）；`sort=None`（按数据顺序）

### `top_n` — 只保留前 N 项（当前版本不裁剪）

- **类型 / 默认值**：`int` / `None`
- **说明**：只做合法性校验（`>=1` 的整数）并写入 `spec["topN"]`。**1.0.0 中瀑布图的前端构建器不读取 `spec.topN`，因此本参数不会减少柱子数量**；需要截断请先自己过滤数据。
- **取值建议**：不要依赖它做截断。正确做法是先聚合再取前几项，例如 `d = df.groupby("大区")["销售额"].sum().nlargest(3).reset_index()`，再把 `d` 传进图里。
- **报错**：`top_n=0` → `ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`

### `title` — 主标题

- **类型 / 默认值**：`str` / `None`
- **说明**：不传时自动生成：传了 `y` 是「<y 列名> 瀑布图」，没传 `y` 是「记录数 瀑布图」。传 `""` 会得到空标题（不会回落到自动标题）。
- **取值建议**：写成“看什么 + 口径”，例如 `"2024 各大区销售额累计"`；单位统一放在 `ytitle` 或 `subtitle` 里。
- **示例**：`title="2024 各大区销售额累计"`；`title=None` → `chart.spec["title"] == "销售额 瀑布图"`

### `subtitle` — 副标题

- **类型 / 默认值**：`str` / `None`
- **说明**：标题下方的小字说明，默认没有；传了才占位。
- **取值建议**：放时间范围、数据口径、单位换算说明。
- **示例**：`subtitle="2024-01-01 ~ 2024-12-30，单位：元"`

### `xtitle` — 横轴（类目轴）标题

- **类型 / 默认值**：`str` / `None`
- **说明**：类目轴标题。不传时用 `roles.x` 的列名，传 `""` 可以隐藏轴标题（类目名本身已经很明确时有用）。
- **取值建议**：类目是“大区/产品/渠道”这类自明维度时可以直接传 `""`。
- **示例**：`xtitle="大区"`；`xtitle=""` → 轴标题区留空

### `ytitle` — 纵轴（数值轴）标题

- **类型 / 默认值**：`str` / `None`
- **说明**：数值轴标题。不传时用 `roles.y` 的列名（`y=None` 时为空）。
- **取值建议**：带单位时写进标题，例如 `"销售额（万元）"`，避免读者误读量级。
- **示例**：`ytitle="销售额（元）"`

### `xlim` — 横轴范围（本图不生效）

- **类型 / 默认值**：`tuple[float, float]` / `None`
- **说明**：瀑布图横轴固定是**类目轴**，`xlim` 只写入 `spec["xlim"]`，不会改变画面；但格式不对仍会报错。内部会把 `(lo, hi)` 交换成 `[lo, hi]` 存储。
- **取值建议**：本图不需要。要控制显示范围请用 `ylim`。
- **报错**：`xlim=(0,)` → `ValueError: xlim 需要是 (最小值, 最大值) 两元组，例如 xlim=(0, 100)`

### `ylim` — 纵轴数值范围

- **类型 / 默认值**：`tuple[float, float]` / `None`
- **说明**：给数值轴一个固定范围，生效。有负数增量时可以把下界压到 0 以下，避免柱子被截断。
- **取值建议**：全为正向增量时 `(0, 上限)`；有下降项时用 `(下限, 上限)`，两个边界都留约 5% 余量。
- **示例**：`ylim=(0, 2000000)`；写成 `[0, 100000]` 也可；`ylim=(0, 100, 200)` → `ValueError: ylim 需要是 (最小值, 最大值) 两元组，例如 ylim=(0, 100)`

### `fmt` — 数值格式

- **类型 / 默认值**：`str` / `'compact'`
- **说明**：同时作用于轴刻度、tooltip 与柱顶标签。可选 `compact`（1.2万 / 1.3亿）、`thousands`（1,234,567）、`raw`（1234567）、`percent`（12.3%）、`currency`（¥1,234）。`fmt=None` 合法，按 `compact` 处理。
- **取值建议**：金额用 `"thousands"` 或 `"currency"`；比率/占比用 `"percent"`；大屏演示用 `"compact"` 更省空间。
- **报错**：`fmt="cn"` → `ValueError: fmt='cn' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）

- **类型 / 默认值**：`int` / `380`
- **说明**：图表区域高度，最小 120。传 `None` 时回落到 380；传数字字符串会报错（不会隐式转换）。
- **取值建议**：类目不超过 8 个用 380；类目多、或需要容纳多行标题时用 460~560。
- **报错**：`height=100` → `ValueError: height 至少 120（像素），收到 100`；`height="380"` → `ValueError: height 至少 120（像素），收到 '380'`

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `colors` — 给特定类目指定颜色（`dict`，默认 `None`）

- **作用**：`{"类目名": "颜色"}` 的字典，命中的类目用你给的颜色，其余仍走主题调色板。 颜色可以写 `#d93025`、`red`、`rgb(217,48,37)`、`rgba(...)`。键是**横轴类目名**。默认按增量正负自动取色（涨绿跌红），配了 `colors` 的类目优先。 键匹配不上不会报错（只是那一条不生效），方便同一段代码复用到不同数据集。
- **建议**：把某个关键驱动项单独标记；「合计」柱仍用主题第一色。 要整体换配色请用 `edv.set_palette()`，不要用它逐个类目硬编码。
- **示例**：`waterfall(df, "项目", "变动额", total=True, colors={"退款": "#d93025"})`

### `theme` — 主题

- **类型 / 默认值**：`str` / `'light'`
- **说明**：只支持 `"light"` / `"dark"`，决定背景、文字、网格线与调色板明暗。`theme=None` 不合法。
- **取值建议**：浅色报表用 `"light"`；深色大屏用 `"dark"`，淡色柱在深底上对比更强。
- **报错**：`theme="night"` → `ValueError: theme 只支持 "light" / "dark"，收到 'night'`

### `legend` — 是否显示图例（本图固定不显示）

- **类型 / 默认值**：`bool` / `False`
- **说明**：瀑布图只有一个“增量”系列，前端构建器固定 `legend: false`，**本参数只写入 `spec["legend"]`，不会显示图例**。颜色语义（涨/跌/合计）靠 tooltip 与直觉传达。
- **取值建议**：保持默认即可；需要解释颜色含义时用 `subtitle` 写一句“绿色为增长、橙色为下降”。
- **示例**：`legend=True` → `chart.spec["legend"] is True`，但画面上依然没有图例。

### `labels` — 是否在柱顶标注数值

- **类型 / 默认值**：`bool` / `False`
- **说明**：开启后在每根增量柱顶部标出**该段增量**（不是累计值），文字受 `fmt` 影响、颜色取次要文字色。合计柱也会标出合计增量。
- **取值建议**：类目少（≤8）且需要精确读数时开启；类目多、或同时开了 `subtitle` 时会显得拥挤。
- **示例**：`labels=True`（配合 `fmt="thousands"` 显示 582,864 这类数字）

### `zoom` — 类目轴缩放条（本图不支持）

- **类型 / 默认值**：`bool` / `str` / `'auto'`
- **说明**：只有核心 `bar` / `line` / `area` / `combo` 等笛卡尔图会消费该字段并渲染 dataZoom 滑条；**瀑布图构建器不读取 `spec.zoom`，传什么都不会出现缩放条**。
- **取值建议**：类目太多时先聚合或使用 `drill` 下钻；不要指望 `zoom` 解决拥挤问题。
- **示例**：`zoom=True` → `chart.spec["zoom"] is True`，画面无变化。

### `drill` — 逐级下钻维度

- **类型 / 默认值**：`str` 或 `list[str]` / `None`
- **说明**：点击某根柱后，按该柱的类目名过滤数据并重算图表，点「返回」逐级回退。传字符串会自动转成单元素列表；若 `drill[0]` 与 `x` 不同，内部会自动把 `x` 插到最前面（如 `x="大区", drill=["省份"]` → `["大区", "省份"]`）。也可以只传 `drill` 不传 `x`，此时 `x` 取 `drill[0]`。
- **取值建议**：维度顺序从粗到细（大区 → 省份 → 城市）；下钻层级不宜超过 3 层，否则用户容易迷路。
- **报错**：`drill=[]` → `ValueError: drill 不能是空列表；不需要下钻请传 drill=None。`；列名不存在 → `KeyError: "下钻维度列 '不存在' 不存在。当前可用的列有：……\n提示：drill 里的每一列都必须是 df 的列名。"`

### `link` — 联动组名

- **类型 / 默认值**：`str` / `None`
- **说明**：同一个 `link` 组内的图表互相联动：点击某根柱，会把该柱的类目名广播给组内其它图，它们按同名列过滤后重算。只有当数据里存在同名列时过滤才有意义。
- **取值建议**：同一看板里“大区 × 产品”这类交叉分析用同一个组名，例如 `link="region"`；不参与联动的图不要传。
- **示例**：`link="sales"`；`chart.spec["link"] == "sales"`

### `max_rows` — 最大参与绘制行数

- **类型 / 默认值**：`int` / `200000`
- **说明**：超过该行数时按等间隔**均匀抽样**，并把提示写进 `chart.warnings`（如「数据 1500 行，超过 max_rows=100，已均匀采样 100 行用于绘图。」），`chart.data["n_total"]` 保留原始行数。传 `None` 关闭采样。列数超过 40 时还有一条“多余列未嵌入”的提示。
- **取值建议**：交互大屏建议 5 万以内；离线静态导出可以放宽到 20 万。`0` 会得到空图，负数/浮点会抛底层异常，别传。
- **示例**：`max_rows=100` → `chart.data["n"] == 100`、`chart.data["n_total"] == 1500`；`max_rows=None` → 不抽样

## 返回值

所有图表函数都返回 `eazy_data_viz.Chart` 对象（`chart = edv.waterfall(df, x="大区", y="销售额")`）。

**Chart 的属性**

- `chart.spec`：`dict`，交给前端 ECharts 的完整配置（JSON 可序列化）。公共键有 `id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`、`roles`、`agg`、`fmt`、`sort`、`topN`、`xtitle`、`ytitle`、`xlim`、`ylim`、`legend`、`labels`、`zoom`、`drill`、`link`，本图额外带 `total`。
- `chart.data`：**`dict`**，不是 DataFrame。包含 `cols`（列名）、`rows`（实际参与绘图的二维数组）、`dims` / `measures` / `kinds`（列角色与类型）、`orders`（有序分类的取值顺序，如月份）、`n`（参与行数）、`n_total`（原始行数）。
- `chart.data_ref`：数据引用 id（`d-` + 12 位 sha1），内容相同的数据在同一次会话里复用同一引用。
- `chart.warnings`：**`dict`**，形如 `{"warnings": ["..."], "n_total": 1500}`；`warnings` 为空表示没有发生采样/丢列降级。
- `chart.title`：只读属性，等价于 `chart.spec["title"]`。

**Chart 的方法**

- `chart.save(path, inline=True)`：写出单文件 HTML，自动创建父目录，返回绝对路径（约 1.2~1.5 MB，可离线打开）。
- `chart.to_html(inline=True)`：返回完整 HTML 字符串；`inline=False` 时引用外部资源，体积小但需要联网/同目录资产。
- `chart.show(open_browser=None)`：在浏览器中打开；Jupyter / Streamlit 下自动内嵌。
- `chart.palette(name)`：切换配色并返回 `self`，支持链式调用；可选 `google`、`antd`、`tableau`、`carbon`、`echarts`、`morandi`、`tailwind`。

**本图 `spec` 的真实结构**

```json
{ "id": "c1", "type": "waterfall", "title": "销售额 瀑布图", "subtitle": null, "theme": "light",
  "height": 380, "dataRef": "d9465273f71af", "roles": {"x": "大区", "y": "销售额"}, "agg": "sum",
  "total": false, "sort": null, "topN": null, "xtitle": null, "ytitle": null, "xlim": null,
  "ylim": null, "fmt": "compact", "legend": false, "labels": false, "zoom": "auto", "drill": null,
  "link": null }
```

## 完整示例

以下示例都基于 `edv.sample_df()`（1500 行 × 11 列），可直接复制运行；输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法：各大区销售额累计

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.waterfall(df, x="大区", y="销售额")
chart.save("examples/output/waterfall_1.html")
```

**输出**：自动标题「销售额 瀑布图」，4 段增量依次累加：华东 582,864 → 华北 476,048 → 华南 347,046 → 西部 225,076，最终累计 1,631,034；全部为正，柱子都是上涨色。
**验证**：`chart.spec["roles"] == {"x": "大区", "y": "销售额"}`，`chart.spec["total"] is False`。

### 示例 2：合计柱 + 数值标签 + 千分位

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.waterfall(
    df, x="产品", y="销售额",
    total=True, labels=True, fmt="thousands",
    title="各产品销售额贡献", subtitle="2024 全年，单位：元",
)
chart.save("examples/output/waterfall_2.html")
```

**输出**：产品顺序为数据中首次出现的顺序（智能终端 → 云服务 → 行业软件 → 运维服务），末尾追加「合计」柱=1,631,034；柱顶标注每段增量，数字带千分位逗号。
**验证**：`chart.spec["total"] is True`、`chart.spec["labels"] is True`、`chart.spec["fmt"] == "thousands"`。

### 示例 3：按月累加 + 轴范围 + 轴标题

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.waterfall(
    df, x="月份", y="销售额",
    sort="x", total=True,
    xtitle="月份", ytitle="销售额（元）",
    ylim=(0, 2200000), height=460,
)
chart.save("examples/output/waterfall_3.html")
```

**输出**：`月份` 是有序分类，`sort="x"` 保证 1月→12月 的累计顺序；12 月累计 1,631,034，与「合计」柱等高；纵轴固定到 220 万，头顶留出标签空间。
**验证**：`chart.spec["ylim"] == [0.0, 2200000.0]`，`chart.spec["sort"] == "x"`。

### 示例 4：含下降项：季度利润增减

```python
import pandas as pd
import eazy_data_viz as edv

df = pd.DataFrame({
    "季度": ["Q1", "Q2", "Q3", "Q4"],
    "利润": [120000, -35000, 68000, -12000],
})

chart = edv.waterfall(
    df, x="季度", y="利润", total=True, labels=True,
    fmt="thousands", ytitle="利润（元）",
    title="2024 季度利润变化",
    subtitle="Q2、Q4 为负贡献",
)
chart.save("examples/output/waterfall_4.html")
```

**输出**：Q1 从 0 涨到 120,000；Q2 向下落到 85,000（下降色）；Q3 回到 153,000；Q4 落到 141,000；「合计」柱=141,000。tooltip 同时给出该段增量与累计值。
**验证**：`chart.spec["total"] is True`；`chart.data["n"] == 4`。

### 示例 5：不传 y：统计各类目记录条数 + 深色主题

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.waterfall(
    df, x="渠道", theme="dark", height=420,
    labels=True, total=True,
    title="各渠道记录条数累计",
)
chart.save("examples/output/waterfall_5.html")
```

**输出**：`y` 省略后自动按记录数统计（`agg="count"`），三个渠道各 500 条，累计 1500；自动标题变成「记录数 瀑布图」。
**验证**：`chart.spec["agg"] == "count"`、`chart.spec["roles"]["y"] is None`、`chart.spec["theme"] == "dark"`。

### 示例 6：下钻 + 联动

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.waterfall(
    df, x="大区", y="销售额",
    drill=["大区", "省份", "城市"], link="sales",
    title="销售额下钻：大区 → 省份 → 城市",
)
chart.save("examples/output/waterfall_6.html")
```

**输出**：初始按大区累计；点击某根柱后按该大区过滤、类目自动切成省份并重新累加；再点一次切到城市。同 `link="sales"` 的其它图表会同步过滤。
**验证**：`chart.spec["drill"] == ["大区", "省份", "城市"]`；`chart.data["dims"]` 里包含这些列。

### 示例 7：边界：只有一个类目

```python
import pandas as pd
import eazy_data_viz as edv

# 只有一根增量柱：累计值就是它本身，加 total 后会多出一根「合计」柱
d1 = pd.DataFrame({"阶段": ["首月"], "增量": [1200]})
chart = edv.waterfall(d1, x="阶段", y="增量", total=True, labels=True)
chart.save("examples/output/waterfall_7.html")
```

**输出**：两根柱（「首月」+「合计」）、高度相同；累计轴从 0 直接跳到 1200。
**验证**：`chart.data["n"] == 1`、`chart.spec["total"] is True`。

## 常见错误

### 1. 把文本列当成了增量列

```python
# 错误写法：y 传了文本列
# edv.waterfall(df, x="大区", y="产品")
# → TypeError: y（数值）列 '产品' 需要是数值类型（当前是文本，例如 ['智能终端', '云服务', '行业软件']）。
#   请先用 pd.to_numeric() 清洗，或换一列。
# 正确写法：换成真正的数值列
import eazy_data_viz as edv
df = edv.sample_df()
chart = edv.waterfall(df, x="大区", y="利润")
```

**修法**：确认 `y` 列的 dtype 是数值（`print(df.dtypes)`）；如果是“¥1,234”这类脏文本，先 `pd.to_numeric(df["列"].str.replace(",", ""), errors="coerce")`。

### 2. 列名拼错 / 用了不存在的列

```python
# 错误写法：列名不存在
# edv.waterfall(df, x="region", y="销售额")
# → KeyError: "x（类目）列 'region' 不存在。当前可用的列有：日期, 月份, 大区, ..."
# 正确写法：用真实列名
import eazy_data_viz as edv
df = edv.sample_df()
chart = edv.waterfall(df, x="大区", y="销售额")
```

**修法**：先 `print(list(df.columns))` 核对；中文列名注意全角/半角与前后空格。

### 3. `sort="desc"` 打乱了累计含义

```python
import eazy_data_viz as edv
df = edv.sample_df()
# 增量按从大到小重排后再累加：曲线形状会变，累计值失去“按时间发生”的含义
chart_desc = edv.waterfall(df, x="产品", y="销售额", sort="desc", total=True)
chart_keep = edv.waterfall(df, x="产品", y="销售额", sort=None, total=True)
```

**修法**：瀑布图只在“类目本身有顺序”（时间、阶段、优先级）时用 `sort="x"`；按大小排序请改用 `bar`。

### 4. 以为 `top_n` 会裁剪类目

```python
import eazy_data_viz as edv
df = edv.sample_df()
chart = edv.waterfall(df, x="大区", y="销售额", top_n=2)
# chart.spec["topN"] == 2，但画面上仍然是 4 根柱：本图前端不消费 topN
d = df.groupby("大区")["销售额"].sum().nlargest(2).reset_index()
chart2 = edv.waterfall(d, x="大区", y="销售额")
```

**修法**：先在 pandas 里 `nlargest` / `sort_values` 截断再画，不要依赖 `top_n`。

## 相关图表

- `bar`：只比较类目大小、不关心累计过程时用分组/堆叠柱。
- `bullet`：看“实际 vs 目标”与达成率，比瀑布图更直接。
- `pareto`：既看类目排序又看累计占比（帕累托 80/20）。
- `lollipop`：类目较多时用更轻量的“棒棒糖”代替柱。
- `line`：关心时间趋势而非增减归因时改用折线。
