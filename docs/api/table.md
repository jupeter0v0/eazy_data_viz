# `table` — 明细表（把指定列渲染成可筛选的 HTML 表格）

明细表把 DataFrame 的指定列渲染成一张 HTML 表格：数值列右对齐、时间列只显示到分钟，超过显示上限时底部提示总行数。它常作为看板里的“核对明细”，也是联动过滤的接收方。

表格是纯 HTML（不经过 ECharts），因此在导出的单文件页面里同样可以打开；它不能作为联动的点击源，但可以被其它图表联动过滤。

1.2.0 起支持中国式报表的常用能力：`total` 表尾合计、`index` 序号列、`bar` 单元格数据条、
`stripe` 斑马纹（默认开启），观感对齐帆软 FineReport 明细表与观远 BI 表格。

- **适合**：需要逐行核对数值、或作为其它图表的联动明细；行数 ≤200、列数 ≤12。
- **不适合**：需要排序/分页/导出时不要用；请导出 CSV 或用专业表格组件。行数很多时考虑先聚合。

> 本页所有示例均可直接复制运行：先 `import eazy_data_viz as edv`，再 `df = edv.sample_df()`。

## 函数签名

```python
eazy_data_viz.table(
    data,
    columns=None,
    *,
    groupby=None,
    limit=100,
    title=None,
    subtitle=None,
    fmt='compact',
    height=400,
    theme='light',
    link=None,
    max_rows=None,
    total=False,
    index=False,
    bar=None,
    stripe=True,
) -> Chart
```

参数按签名顺序：`data` → 本图专有参数 → 关键字参数（`*` 之后全部只能按关键字传）。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | pandas.DataFrame（也接受 dict / list，内部会转成 DataFrame） | 无 | 是 | 数据源（DataFrame） |
| `columns` | list[str] 或 None | None | 否 | 明细模式要显示的列（默认前 12 列）；与 `groupby` 互斥 |
| `groupby` | dict 或 None | None | 否 | 汇总模式：`{"columns": [...], "value": "...", "agg": "sum"}` |
| `limit` | int | 100 | 否 | 最多显示的行数 |
| `title` | str 或 None | None | 否 | 图表主标题 |
| `subtitle` | str 或 None | None | 否 | 副标题（口径/单位/时间范围） |
| `fmt` | str | 'compact' | 否 | 数值格式（tooltip / 标签） |
| `height` | int | 400 | 否 | 画布高度（像素） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | str | 'light' | 否 | 主题（浅色 / 深色） |
| `link` | str 或 None | None | 否 | 联动分组名 |
| `max_rows` | int 或 None | `None`（自动） | 否 | 嵌入前端的行数：明细表默认 200 行，汇总表默认全部行 |
| `total` | `bool` | `False` | 否 | 表尾合计行 |
| `index` | `bool` | `False` | 否 | 最左侧序号列 |
| `bar` | `bool \| str \| list[str] \| None` | `None` | 否 | 单元格数据条 |
| `stripe` | `bool` | `True` | 否 | 斑马纹 |

> 共 15 个参数。签名里 `*` 之后是 keyword-only，必须写参数名；`data` 之前的位置参数（本图专有）可以按位置传。

## 参数详解

### `data` — 数据源（DataFrame）（`pandas.DataFrame`，必填）

- **作用**：图的原始数据。函数会按参数名从里面取列：`data` 既可以是 `pandas.DataFrame`，也可以是 `dict`（列名 → 值序列）或 `list`（记录列表），内部通过 `ensure_frame()` 统一转换。转换后必须至少有 1 行，否则报 `ValueError`。每张图最多嵌入 40 列（`MAX_COLS=40`），超过的部分会被丢弃并写入 `chart.warnings["warnings"]`。
- **建议**：首选 `pandas.DataFrame`；列名建议保持唯一、非空，中文列名可以直接用。 数值列用数值 dtype（`int64/float64`）；文本数字请先 `pd.to_numeric()`。 日期列用 `datetime64[ns]`（或可被 `pd.to_datetime()` 解析的字符串）。 作图前先处理空值：不同图对空值的策略不同（见各函数“常见问题”）。
- **示例**：`edv.table(data=df, columns=["大区", "销售额"], limit=20)`
- **报错**：传入空 DataFrame：`ValueError: 数据为空（0 行），无法绘图。`；传入 `None`：`ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`

### `columns` — 要显示的列（`list[str] | None`，默认 `None`）

- **作用**：按传入顺序显示；不传时取 `data.columns` 的前 12 列。每一列都必须存在于 `data`。列名写错会直接报错，不会静默跳过。
- **建议**：只放关键列（4~8 列），列太多在卡片里会横向溢出。 把最常核对的列放前面，顺序就是展示顺序。 时间列会显示到分钟（`YYYY-MM-DD HH:MM`），日期列只显示日期。
- **示例**：`edv.table(df, limit=20, columns=["日期", "大区", "产品", "销售额"])`
- **互斥**：要汇总就改用 `groupby`，两个参数同时传会报错：`ValueError: table 的 columns 参数已由 groupby 取代：要明细就只传 columns，要汇总就只传 groupby={...}，不要同时传。`
- **报错**：列不存在：`KeyError: "columns[1]列 '不存在' 不存在。当前可用的列有：..."`；`columns=[]`：`ValueError: table 需要至少 1 列，例如 table(df, columns=["月份", "销售额"])。`

### `groupby` — 汇总模式（`dict | None`，默认 `None`）

- **作用**：把表格从“逐行明细”换成“按维度分组汇总”。字典只有三个键：

  | 键 | 是否必填 | 含义 |
  | --- | --- | --- |
  | `columns` | 是 | 分组维度列，1 列或多列（分组键） |
  | `value` | 否 | 要汇总的数值列；不给则按组计数 |
  | `agg` | 否 | 聚合方式：`sum`（有 value 时默认）/ `mean` / `count` / `max` / `min` / `median` |

  渲染时按 `value` 降序排列；表头显示“`value（求和）`”这类“列名（聚合名）”，没有 `value` 时显示“记录数”；底部提示“共 N 行，汇总为 M 组”。
- **只影响显示**：分组/聚合发生在浏览器端对**筛选后数据**的计算上，不会改动嵌入页面的原始数据，也不会改变其它图表收到的联动值。所以“点某个大区 → 这张表显示该大区的汇总”是安全的。
- **建议**：分组列用低基数字段（大区、渠道、产品，5~20 个取值）；维度太多先用 `top_n` 思路在 Python 里裁剪。 需要“明细 + 汇总”两张表时，用同一个 `link` 组名各建一张。 汇总表同样支持 `link=("g", "in")` 单向进，避免点表影响别的图。
- **示例**：
  ```python
  edv.table(df, groupby={"columns": ["大区"], "value": "销售额", "agg": "sum"})
  edv.table(df, groupby={"columns": ["大区", "渠道"]})          # 按组计数
  edv.table(df, groupby={"columns": ["产品"], "value": "利润", "agg": "mean"})
  ```
- **报错**：不是字典：`ValueError: groupby 需要是字典，例如 groupby={"columns": ["大区"], "value": "销售额", "agg": "sum"}。`；未知键：`ValueError: groupby 只支持 columns / value / agg 三个键，收到未知键：agg_func。`；没有 `columns`：`ValueError: groupby 需要 columns（按哪些列分组），例如 groupby={"columns": ["大区"], "value": "销售额"}。`；`columns` 为空：`ValueError: groupby 的 columns 不能为空：至少指定 1 个分组列。`；`value` 传了多列：`ValueError: groupby 的 value 只能是一列（汇总哪一列数值），收到 2 列。`；`value` 同时出现在 `columns` 里：`ValueError: groupby 的 value（'大区'）不能同时出现在 columns 里：同一列不能既分组又求和。`；`agg` 不认识：`ValueError: groupby 的 agg='avg' 不支持，可选：sum、mean、count、max、min、median。`；没给 `value` 却传了其它 `agg`：`ValueError: groupby 没给 value 时 agg 只能是 "count"（按组计数），收到 agg='sum'。`

### `limit` — 最多显示的行数（`int`，默认 `100`）

- **作用**：正整数，默认 100。Python 会把上限截到 200（`min(limit, 200)`），JS 端再截到 500；超过时表格底部提示“共 N 行，仅显示前 limit 行”。
- **建议**：看板里 20~50 行最合适，`limit=100` 已经需要滚动。 要展示更多行请改用其它方式（导出 CSV），而不是把 `limit` 调到 1000。 `limit` 只影响显示，不影响数据嵌入：`max_rows` 才控制嵌入行数（明细表默认 200 行，汇总表默认全部行）。
- **示例**：`edv.table(df, columns=["大区", "销售额"], limit=30)`
- **报错**：`limit=0`：`ValueError: limit 需要是 >=1 的整数（最多显示多少行），收到 0`

### `title` — 图表主标题（`str | None`，默认 `None`）

- **作用**：显示在卡片顶部的主标题。传 `None` 时使用函数内置的自动标题；传字符串则完全覆盖自动标题。标题只影响展示，不参与数据聚合与排序。
- **建议**：建议 8~18 个汉字，写清“指标 + 维度 + 口径”，例如 `销售额 按 大区`。 时间范围、币种、口径放在 `subtitle`，不要全部堆进标题。 标题是单行布局，过长会被卡片宽度截断，不建议加换行符。
- **示例**：`edv.table(df, columns=["大区", "销售额"], limit=20, title="华东区销售构成")`

### `subtitle` — 副标题（口径/单位/时间范围）（`str | None`，默认 `None`）

- **作用**：标题下方的第二行说明，常用于补充统计口径、单位、时间范围或“较上期 +8%”这类结论。默认 `None`，不显示副标题；传空字符串等同于不显示。
- **建议**：写口径而不重复标题，例如 `2024 年 1-12 月 · 含税`。 颜色比标题浅，信息量控制在 30 字以内。 需要换行时直接写 `\n` 不会被解析成 HTML，建议保持单行。
- **示例**：`edv.table(df, columns=["大区", "销售额"], limit=20, subtitle="2024 年 1-12 月 · 含税")`

### `fmt` — 数值格式（tooltip / 标签）（`str`，默认 `'compact'`）

- **作用**：控制数值在 tooltip、数据标签、右端读数里的显示格式，不改变原始数据。可选值：`compact`（默认，≥1 亿显示“x.x亿”、≥1 万显示“x.x万”、否则千分位）、`thousands`（千分位，如 `1,234,567`）、`raw`（原样，最多 3 位小数）、`percent`（一位小数加 `%`，如 `12.3%`）、`currency`（`¥` + 千分位 + 两位小数）。 本图实现：作用于数值单元格；注意 `compact` 在这里被降级为千分位（不会显示“万/亿”）。
- **建议**：金额大数用 `compact`，表格/财务口径用 `thousands` 或 `currency`。 已经是百分数的列用 `percent`，不要再乘 100。 同一页多张图保持一致的 `fmt`，避免“万/千分位”混排。
- **示例**：`edv.table(df, columns=["大区", "销售额"], limit=20, fmt="thousands")`
- **报错**：`fmt="commas"`：`ValueError: fmt='commas' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）（`int`，默认 `400`）

- **作用**：单张图的容器高度，单位像素，最小 120。不同函数的默认高度不同（本函数默认值见参数总览）。高度只影响画布，不改变数据；图例/标题/坐标轴会自动占用内部空间。
- **建议**：普通看板 320~460；层级图/关系图建议 ≥420。 多张图并排时高度取一致，视觉更整齐。 `height` 小于 120 会直接报错，不要用它做“隐藏图”。
- **示例**：`edv.table(df, columns=["大区", "销售额"], limit=20, height=520)`
- **报错**：`height=100`：`ValueError: height 至少 120（像素），收到 100`；`height="400"`：同样报错（必须是 `int/float`）。

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题（浅色 / 深色）（`str`，默认 `'light'`）

- **作用**：页面主题，只支持 `"light"`（默认，白底深字）和 `"dark"`（深底浅字）。主题会同时改变背景、文字、坐标轴、tooltip 和默认色板的取色（`theme.palette`）。
- **建议**：常规报表/打印用 `light`；大屏、夜间模式用 `dark`。 多图看板统一主题，不要一张亮一张暗。 深色下避免使用低饱和的 `morandi` 色板，对比度会不够。
- **示例**：`edv.table(df, columns=["大区", "销售额"], limit=20, theme="dark")`
- **报错**：`theme="blue"`：`ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `link` — 联动分组名（`str | None`，默认 `None`）

- **作用**：把多张图放进同一个联动组：点击某张图的类目，同组中包含该维度列的其他图会按该值过滤。同一个组名（如 `"g1"`）即可联动；默认 `None` 不联动。注意：`table`/`wordcloud` 是 HTML 渲染，只能作为**被联动方**，点击它们不会触发联动。 本图实现：只能作为被联动方（点击行不会触发联动）。
- **建议**：同一看板里的明细表用同一个 `link` 组名，点图即可筛表。 联动维度由点击的图决定，各图尽量共享同一列（如 `产品`）。 组名建议用有含义的英文/拼音，不要用随机串。
- **示例**：`edv.table(df, columns=["大区", "销售额"], limit=20, link="g1")`
- **双向**：设了 `link` 之后表格不只是「接收方」——表里的维度列（文本/日期列）会变成
  可点单元格，点一下就把 `列 = 该格的值` 写进联动组，同组图表立刻被筛；表格自己不过滤，
  而是把命中的行高亮（左侧主色竖条 + 浅色蒙层）。再点同一格取消。数值列不可点。
  1.4.0 起生效。
- **报错**：无校验：传数字/对象会原样写入 spec，JS 端作为对象键使用，建议只传字符串。

### `max_rows` — 嵌入前端的行数（`int` 或 `None`，默认 `None` = 自动）

- **作用**：Python 侧把 `max_rows` 行数据嵌入 HTML，超过时按均匀间隔抽样，并把提示写入 `chart.warnings["warnings"]`。`table` 的默认值是 `None`（自动）：**明细表**（`columns=`）嵌 200 行，**汇总表**（`groupby=`）嵌全部行——因为汇总必须在完整数据上算，只嵌 200 行时 `sum` / `count` 的数字会和 pandas 对不上。`limit` 只控制显示行数，`max_rows` 控制嵌入行数。
- **建议**：汇总表数据量很大（几十万行）时，先 `df.groupby(...).sum()` 预聚合再传 `table`，或显式传 `max_rows=20000`（注意此时汇总是按嵌入的行算的）。需要完整数据时导出 Excel/CSV，不要让 HTML 承担全量数据。
- **示例**：`edv.table(df, columns=["大区", "销售额"], limit=20, max_rows=500)`；汇总表默认嵌全量：`edv.table(df, groupby={"columns": ["大区"], "value": "销售额"}, max_rows=20000)` 可限制为前 20000 行。
- **报错**：无校验：传 `0` 或负数会得到空数据（图形空白），建议传正整数。

### `total` — 表尾合计行（`bool`，默认 `False`）

- **作用**：`True` 时在表尾增加一行「合计」，对**数值列**求和，并按单元格同样的格式显示（如 `7,735.98`）；文本列、时间列留空，0 行时不画合计行。
- **统计范围**：只统计 `limit` 内**实际渲染**的行，与底部「共 N 行，仅显示前 M 行」的提示一致，不是整表求和。要合计全量数据，请先用 `df.groupby(...).sum()` 聚合，或把 `limit` 调大。
- **位置**：没有 `index` 时，「合计」二字占第一列（通常是维度列）；
  `index=True` 时占序号列。若第一列本身就是数值列（例如只选了 `["销售额", "利润"]`），
  「合计」会与该列合计同格显示（`合计 6,044.28`），不会吞掉这一列的合计。
- **格式**：跟随 `fmt`（`currency` → `¥…`、`thousands` → 千分位）；与 `.unit("万")` 同用时先按单位换算再显示。
- **样式**：加粗、顶部 4px 双线 + 浅底色；表头 sticky 时合计行仍随表格可见。
- **示例**：`edv.table(df, columns=["大区", "销售额", "利润"], limit=12, total=True)`
- **报错**：非布尔值：`ValueError: total 需要是 bool（True / False），收到 'yes'`

### `index` — 序号列（`bool`，默认 `False`）

- **作用**：`True` 时在最左侧增加「序号」列，从 1 开始编号，一直编到当前显示的最后一行。
- **样式**：居中、定宽 48px、文字比正文浅；横向滚动时固定在左侧，不随内容滚走。
- **注意**：序号是**显示序号**（1..N），不是 DataFrame 的 index；原始索引不会显示。联动/下钻过滤后，序号按过滤后的结果重新从 1 开始。
- **与 total 的关系**：`total=True` 且 `index=True` 时，「合计」写在序号列，维度列保持为空。
- **示例**：`edv.table(df, columns=["日期", "大区", "销售额"], limit=15, index=True)`
- **报错**：非布尔值：`ValueError: index 需要是 bool（True / False），收到 1`

### `bar` — 单元格数据条（`bool | str | list[str] | None`，默认 `None`）

- **取值**：`True` 自动取 `columns` 里第一个数值列；`"列名"` 指定一列；`["列1", "列2"]` 指定多列（按主题调色板依次取色）；`None` / `False` 不画。
- **行为**：条宽 = `|值| / 该列绝对值最大`，只按 `limit` 内实际渲染的行计算；数值文字压在色条上层，仍保持右对齐。浅色主题 alpha 0.22、深色 0.34，颜色取自当前主题调色板。
- **与 columns 的关系**：`bar` 指定的列必须同时出现在 `columns` 里（不显示的列不画条）；重复列名会自动去重。
- **组合**：可以和 `total=True` 一起用——合计行只显示数字，不画数据条。
- **示例**：`edv.table(df, columns=["大区", "销售额", "利润"], limit=20, bar=["销售额", "利润"])`
- **报错**：列不在 `columns`：`ValueError: bar 指定的列 '毛利率' 不在 columns 里；当前可用的列有：...`；非数值列：`ValueError: bar 只能用于数值列，'大区' 是文本列；请改用 total=True 求和或去掉 bar。`；空列表：`ValueError: bar 不能是空列表；不需要数据条请传 bar=None。`

### `stripe` — 斑马纹（`bool`，默认 `True`）

- **作用**：`True`（默认）时给偶数行加一层极浅底色，长表横向阅读时不容易串行。这是 1.2.0 起的默认外观，旧图会多一层很浅的斑马纹；想还原旧观感传 `stripe=False`。
- **配套默认样式**（无需额外参数）：表头 sticky、首列（有序号时是序号列）横向滚动固定、合计行 4px 双线 + 底色、空单元格统一显示「−」。
- **深色主题**：斑马纹底色由主题自动生成，`theme="dark"` 下不会变成刺眼的浅灰。
- **示例**：`edv.table(df, columns=["大区", "销售额"], limit=20, stripe=False)`
- **报错**：非布尔值：`ValueError: stripe 需要是 bool（True / False），收到 'on'`

## 返回值

返回 `eazy_data_viz.Chart` 对象（`chart.spec` 是完整的渲染 spec，`chart.data` 是嵌入前端的数据）。

- 通用方法：`chart.save(path)` 写单文件 HTML、`chart.to_html()` 返回字符串、`chart.palette(name)` 链式换色、`chart.show()` 在浏览器打开；`chart.warnings` 记录采样等降级提示（详见 [交互与联动指南](../guides/06-interaction.md)）。

本图的关键 spec 字段（`chart.spec`）：

| 字段 | 含义 |
| --- | --- |
| `type` | 固定为 `"table"`。 |
| `columns` | 字符串列表，决定表头与列顺序。 |
| `limit` | 显示行数上限（Python 已截到 ≤200）。 |
| `roles` | 明细 `{"columns": [...], "value": None}`；汇总 `{"columns": [...], "value": "销售额"}`。 |
| `groupby` | 汇总模式的三键字典；明细模式为 `None`。 |
| `fmt` | 数值格式：`compact` 在表格里按千分位显示，`percent`/`currency` 按对应格式，`raw` 原样。 |
| `max_rows` | 嵌入页面的行数：`None`（默认）时明细表 200 行、汇总表全部行；传整数则按该行数。 |
| `total` | 是否绘制表尾合计行。 |
| `index` | 是否显示序号列。 |
| `bar` | 数据条列名数组（`None` 表示不画）。 |
| `stripe` | 是否显示斑马纹。 |

## 完整示例

以下示例全部基于 `edv.sample_df()`（1500 行、11 列）或由它派生的小表；输出文件写到 `examples/output/`。

### 示例 1：最简：默认取全部列

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.table(df)
chart.save("examples/output/table_1.html")
```

**输出**：渲染 sample 数据前 100 行、全部 11 列；数值列右对齐，日期列显示到天，月份显示“1月”等；页面标题自动为“明细数据”。

### 示例 2：典型：指定列与行数

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.table(
    df,
    columns=["日期", "大区", "产品", "渠道", "销售额", "利润"],
    limit=30,
    title="重点字段明细",
    subtitle="仅展示前 30 行",
)
chart.save("examples/output/table_2.html")
```

**输出**：只出现指定的 6 列，顺序与传入一致；显示 30 行后若数据更多，底部出现“共 1500 行，仅显示前 30 行”的提示。

### 示例 3：进阶：数值格式与深色主题

```python
import eazy_data_viz as edv

df = edv.sample_df()
a = edv.table(df, columns=["大区", "销售额", "利润"], limit=20, fmt="currency")
a.save("examples/output/table_3.html")
b = edv.table(df, columns=["大区", "销售额", "利润"], limit=20, theme="dark")
b.save("examples/output/table_3.html")
```

**输出**：`currency` 版本销售额显示为“¥…”；深色主题下表格背景、边框、文字全部切换为深色，数值仍右对齐。

### 示例 4：边界：先筛选再展示（避免空表）

```python
import eazy_data_viz as edv

df = edv.sample_df()
east = df[df["大区"] == "华东"]
chart = edv.table(east, columns=["日期", "产品", "销售额"], limit=15, title="华东明细")
chart.save("examples/output/table_4.html")

empty = df[df["大区"] == "不存在的区域"]
try:
    edv.table(empty, columns=["日期", "销售额"], title="空结果")
except ValueError as exc:
    print("空数据会直接报错，符合预期：", exc)
```

**输出**：第一张表只显示华东记录；第二张表因为 0 行，在 Python 端抛出 `ValueError: 数据为空（0 行），无法绘图。`——空表必须在传参前自己过滤，不能交给 table。

### 示例 5：联动：作为被过滤的明细表

```python
import eazy_data_viz as edv

df = edv.sample_df()
rose = edv.rose(df, names="大区", values="销售额", link="tb1")
tbl = edv.table(df, columns=["大区", "产品", "销售额"], link="tb1", limit=40)
edv.dashboard(rose, tbl, title="玫瑰图 → 明细表", cols=2).save("examples/output/table_5.html")
```

**输出**：点击左侧玫瑰图的某个大区，右侧表格只剩该大区记录；表格自身不能点击触发联动（HTML 表格不是 ECharts 系列）。

### 示例 6：中国式报表（序号 + 合计 + 数据条）

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.table(
    df,
    columns=["大区", "产品", "销售额", "利润"],
    limit=12,
    index=True,
    total=True,
    bar="销售额",
    title="重点明细（含合计）",
    subtitle="合计只统计当前显示的 12 行",
)
chart.save("examples/output/table_6.html")
```

**输出**：最左侧出现 1–12 的「序号」列，横向滚动时固定；「销售额」单元格带浅色数据条，「利润」不带；表尾一行「合计」，销售额/利润按千分位显示（如 `7,735.98`），大区/产品列留空；底部仍提示「共 1500 行，仅显示前 12 行」。

### 示例 6：汇总表：只显示汇总，不影响后台联动（1.5 新参数）

```python
import eazy_data_viz as edv

df = edv.sample_df()
bar = edv.bar(df, x="大区", y="销售额", link=("s1", "out"))
summary = edv.table(
    df,
    groupby={"columns": ["大区"], "value": "销售额", "agg": "sum"},
    link=("s1", "in"),
    limit=20,
    title="大区销售汇总",
)
edv.dashboard(bar, summary, title="汇总表联动", cols=2).save("examples/output/table_6.html")
```

**输出**：表格一进页面就显示 4 行汇总（华东/华北/华南/西南 + 求和列）；点击柱状图的某个大区后，表格变成 **1 行**——该大区的汇总值，而不是把明细行过滤出来。后台数据没被改写，其它图表照常收到原来的联动值。

**验证**：`chart.spec["groupby"] == {"columns": ["大区"], "value": "销售额", "agg": "sum"}`；`chart.data.rows` 仍是原始行（汇总只在前端算）。

## 常见问题 / 注意事项

### Q1. 表格能排序、分页、搜索吗？

不能。它是静态 HTML 表格，只做展示与联动过滤；`limit` 控制显示行数，超出部分不会渲染。需要交互表格请用专业组件。

### Q2. 为什么只显示了 200 行，明明 `limit` 更大？

两层限制：`limit` 被 Python 截到 ≤200，且嵌入行数由 `max_rows` 决定（明细表默认 200 行；汇总表默认全部行，因为它要算准）。即使 `limit=999`，最多也是 200 行。

### Q3. 时间列为什么只显示到分钟？

表格对时间列固定 `slice(0, 16)`，即 `YYYY-MM-DD HH:MM`；日期列只到天。需要秒级精度请先把列转成字符串再传入。

### Q4. 数值列为什么没有千分位？

`fmt="compact"` 在表格里等价于千分位（`thousands`）；`raw` 原样输出。`percent`/`currency` 分别加 `%`/`¥`。

### Q5. 表格能作为联动源吗？

不能。HTML 表格没有注册点击事件，工具栏也不会显示联动提示；但它能被其它图表联动过滤（这是最常用的组合）。

### Q6. 合计为什么只算显示的行？

`total` 与页面上看到的内容保持一致：只对 `limit` 内实际渲染的行求和，避免「屏幕上是 12 行、合计却是 1500 行」的误读。需要全量合计请先用 `df.groupby(...).sum()` 聚合，或把 `limit` 调大（上限 200）。合计的数字格式跟随 `fmt`：`currency` 会带 `¥`，`unit("万")` 会先换算再显示。

### Q7. `bar="销售额"` 为什么直接报错？

数据条只画在**已经显示**的数值列上：列必须同时出现在 `columns` 里，且必须是数值列。文本列/时间列不能画条；想强调文本列请改用 `total`，或先把该列转成数值。

### Q8. 升级后表格多了一层浅色条纹？

1.2.0 起 `stripe` 默认 `True`（中国式报表的斑马纹）。传 `stripe=False` 即可回到 1.1.x 的纯白底；表头 sticky、首列固定、空值「−」这些配套样式仍保留。

## 相关图表

| 图表 | 说明 |
| --- | --- |
| [`wordcloud`](wordcloud.md) | 词云（类目的视觉化汇总） |
| [`matrix`](matrix.md) | 相关系数矩阵（数值列之间的相关性） |
| [`calendar`](calendar.md) | 日历热力图（按天看密度） |
| [`rose`](rose.md) | 南丁格尔玫瑰图（构成占比的图形表达） |

- 回到总览：`docs/EXTRA_CHARTS.md`、`docs/AI_GUIDE.md`
