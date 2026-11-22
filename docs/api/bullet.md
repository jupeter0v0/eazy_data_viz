# `bullet` — 子弹图：实际值 vs 目标

> 横向条形图的一种变体：每行先画一条浅色“背景槽”，槽内再画一根细的“实际值”条，目标值用一根竖线刻度标出；一眼就能看出“完成了多少、离目标还差多少”。
> 适合：分区域/分团队的 KPI 达成情况、渠道销售 vs 目标、预算执行进度。
> 不适合：比较类目之间的绝对大小（用 `bar`）、看目标随时间的走势（用 `target` 折线或 `line`）、多指标雷达对比（用 `radar`）。

## 函数签名

```python
eazy_data_viz.bullet(
    data,
    x,
    actual,
    target=None,
    *,
    target_value=None,
    agg=None,
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
    theme="light",
    legend=False,
    labels=False,
    zoom=False,
    drill=None,
    link=None,
    max_rows=2000000,
) -> Chart
```

> `data` / `x` / `actual` / `target` 是位置参数，其余全部是**关键字限定参数**（`*` 之后必须写成 `参数名=值`）。
> 参数个数 23：4 个位置参数 + 19 个关键字参数。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源，图表取数的唯一入口 |
| `x` | `str` | `—` | 是 | 类目列名，每行一个类目（画在纵轴） |
| `actual` | `str` | `—` | 是 | 实际值数值列（必填） |
| `target` | `str \| float` | `None` | 否 | 目标值：列名或一个常数 |
| `target_value` | `float` | `None` | 否 | 目标常数，优先级高于 `target` |
| `agg` | `str` | `'sum'` | 否 | 实际值/目标列的聚合方式 |
| `sort` | `str` | `None` | 否 | 排序：x / asc / desc / none |
| `top_n` | `int` | `None` | 否 | 只保留前 N 项（当前版本不裁剪，见详解） |
| `title` | `str \| None` | `None` | 否 | 主标题，默认自动生成 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题（灰色小字） |
| `xtitle` | `str \| None` | `None` | 否 | **数值轴（横轴）**的标题 |
| `ytitle` | `str \| None` | `None` | 否 | **类目轴（纵轴）**的标题 |
| `xlim` | `tuple[float, float]` | `None` | 否 | 数值轴（横轴）范围 |
| `ylim` | `tuple[float, float]` | `None` | 否 | 类目轴范围（本图不生效） |
| `fmt` | `str` | `'compact'` | 否 | 数值格式：compact / thousands / raw / percent / currency |
| `height` | `int` | `380` | 否 | 画布高度（像素，≥120） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `str` | `'light'` | 否 | light / dark |
| `legend` | `bool` | `False` | 否 | 是否显示图例（本图固定不显示） |
| `labels` | `bool` | `False` | 否 | 是否标数值（本图不支持） |
| `zoom` | `bool \| str` | `False` | 否 | 缩放条（本图不支持） |
| `drill` | `str \| list[str]` | `None` | 否 | 逐级下钻维度 |
| `link` | `str` | `None` | 否 | 联动组名（同组图表互相筛选） |
| `max_rows` | `int` | `2000000` | 否 | 最大参与绘制行数（None 不采样） |

## 参数详解

### `data` — 数据源，图表取数的唯一入口（必填）

- **类型 / 默认值**：`pandas.DataFrame`、`dict`、`list`（每项一行）或 `Series` / 无
- **说明**：内部先经 `frame.ensure_frame()` 归一化成 DataFrame 再绘图：`DataFrame` 原样使用，`Series` 变单列，`dict` / `list` 自动转表。传入对象不会被原地修改；行数超过 `max_rows` 时均匀抽样，并把提示写进 `chart.warnings`。
- **取值建议**：正式代码一律传 DataFrame；`dict` / `list` 只用于快速试验。列名允许中文、空格与特殊字符，只要唯一即可。
- **报错**：`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`；`data=42` → `TypeError: 无法识别 data 类型 'int'，请传入 pandas.DataFrame（或 dict / list）。`

### `x` — 类目列名（必填）

- **类型 / 默认值**：`str` / 无
- **说明**：每行一个类目，画在**纵轴**上；因为纵轴 `inverse=true`，聚合顺序里的第一项出现在最上方。同一 `x` 的多行先按 `agg` 聚合，实际值与目标值各自聚合。
- **取值建议**：传真实列名。类目多（>15）时纵向排布会很长，建议先聚合或用 `drill`；类目顺序有明显业务含义时用有序分类保证顺序。
- **报错**：不传 → `TypeError: bullet() missing 1 required positional argument: 'x'`；列名写错 → `KeyError: "x（类目）列 '不存在' 不存在。当前可用的列有：日期, 月份, 大区, 省份, 城市, 产品, 渠道, 销售额, 订单数, 利润, 客户数"`

### `actual` — 实际值数值列（必填）

- **类型 / 默认值**：`str` / 无
- **说明**：每行细条的长度来源；与 `target` 一起决定 tooltip 里的“达成率”（实际 / 目标 × 100%）。目标为 0 时不显示达成率。
- **取值建议**：可加指标（销售额、订单数）用 `agg="sum"`；比率型指标（客单价、转化率）用 `agg="mean"`。累计值和目标值口径必须一致。
- **报错**：文本列 → `TypeError: y（数值）列 '产品' 需要是数值类型（当前是文本，例如 ['智能终端', '云服务', '行业软件']）。请先用 pd.to_numeric() 清洗，或换一列。`

### `target` — 目标值：列名或常数

- **类型 / 默认值**：`str` 或 `float`（`int` 也可以） / `None`
- **说明**：只有两种合法用法：
  - 传 **数字**（`int` / `float`，且不是 `bool`）：等价于 `target_value=该数字`，所有类目共用同一个目标；
  - 传 **字符串**：当作列名，按 `agg` 聚合后作为每个类目的目标（可以逐类目不同）。
  - 同时传了 `target` 和 `target_value` 时，**`target_value` 优先**。
- **取值建议**：全公司统一 KPI 用常数；逐区域/逐人目标写在数据列里。注意 `bool` 会被当成列名（`target=True` → `KeyError: target（目标值）列 True 不存在`）。
- **示例**：`target=500000`（所有类目统一 50 万）；`target="目标销售额"`（列名）

### `target_value` — 目标常数（优先级更高）

- **类型 / 默认值**：`float` / `None`
- **说明**：统一目标值。前端在“该行没有目标列取值”时用它兜底，因此当 `target` 传列名、但某些类目缺目标时，缺失项会落到 `target_value`；两者都传时 `target_value` 覆盖列值。非数字字符串会被静默吞成 `None`（图仍能画，目标按 0 处理），不会报错。
- **取值建议**：统一目标用 `target_value=`；需要逐类目不同目标就用 `target="列名"`，不要同时传两个。
- **示例**：`target_value=500000` → `chart.spec["targetValue"] == 500000.0`；`target_value="abc"` → `None`（不报错，需自行校验）

### `agg` — 聚合方式

- **类型 / 默认值**：`str` / `'sum'`
- **说明**：`actual` 与 `target` 列分别按 `x` 聚合，同一个 `agg` 同时作用于两者。可选 `sum` / `mean` / `count` / `max` / `min` / `median`。
- **取值建议**：金额、销量用 `"sum"`；达成率/单价类指标用 `"mean"`，否则求和后达成率会失真。目标列与 `actual` 列的口径必须一致。
- **报错**：`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, unique, max, min, median`

### `sort` — 类目顺序

- **类型 / 默认值**：`str` / `None`
- **说明**：`"x"` 按类目本身排序，`"asc"` / `"desc"` 按**实际值**排序，`None` 保持聚合顺序（数据中首次出现的顺序）。
- **取值建议**：KPI 排行常用 `"desc"`（完成最好的在最上方，因为纵轴反向）；保持组织结构顺序就用有序分类 + `"x"`。非法值不报错，前端按不排序处理。
- **示例**：`sort="desc"` → 华东（582,864）排第一行

### `top_n` — 只保留前 N 项（当前版本不裁剪）

- **类型 / 默认值**：`int` / `None`
- **说明**：只做合法性校验并写入 `spec["topN"]`。**1.0.0 中子弹图的前端构建器不读取 `spec.topN`，本参数不会减少行数**；需要截断请先过滤数据。
- **取值建议**：先 `df.groupby("大区")["销售额"].sum().nlargest(5)` 再画。
- **报错**：`top_n=0` → `ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`

### `title` — 主标题

- **类型 / 默认值**：`str` / `None`
- **说明**：不传时自动生成「<actual 列名> 达成情况」；传 `""` 得到空标题（不回落自动）。
- **取值建议**：写清“谁的目标 + 时间区间”，例如 `"2024 各大区销售额达成情况"`。
- **示例**：`title=None` → `chart.spec["title"] == "销售额 达成情况"`

### `subtitle` — 副标题

- **类型 / 默认值**：`str` / `None`
- **说明**：标题下方的小字说明，默认没有。
- **取值建议**：写目标口径（税前/含税、是否含退款）与时间范围。
- **示例**：`subtitle="目标 = 2024 年度预算，实际含税"`

### `xtitle` — 数值轴（横轴）标题

- **类型 / 默认值**：`str` / `None`
- **说明**：注意子弹图是**横向**的，所以 `xtitle` 管的是**数值轴（横轴）**，不传时用 `actual` 列名；传 `""` 隐藏。
- **取值建议**：写上单位，如 `"销售额（元）"`。
- **示例**：`xtitle="销售额（元）"`

### `ytitle` — 类目轴（纵轴）标题

- **类型 / 默认值**：`str` / `None`
- **说明**：管**类目轴（纵轴）**，不传时用 `x` 列名；传 `""` 隐藏。因为横向条形图右侧空间紧张，纵轴标题默认靠右留出 24px。
- **取值建议**：类目本身已自明（大区/产品）时可以传 `""`，把空间留给条形。
- **示例**：`ytitle="大区"`；`ytitle=""` → 纵轴无标题

### `xlim` — 数值轴（横轴）范围

- **类型 / 默认值**：`tuple[float, float]` / `None`
- **说明**：给横轴（数值轴）一个固定范围，**本图生效**。内部会把 `(lo, hi)` 交换成 `[lo, hi]` 存储。想固定“满分刻度”（例如 0~100%）时特别有用。
- **取值建议**：达成率场景用 `xlim=(0, 100)`（若数据是百分比数值）；销售额场景给到“最大目标 × 1.1”左右，避免目标刻度顶到边缘。
- **示例**：`xlim=(0, 800000)`；格式错 → `ValueError: xlim 需要是 (最小值, 最大值) 两元组，例如 xlim=(0, 100)`

### `ylim` — 类目轴范围（本图不生效）

- **类型 / 默认值**：`tuple[float, float]` / `None`
- **说明**：子弹图纵轴固定是类目轴，`ylim` 只写入 `spec["ylim"]`，不改变画面；格式不对仍会报错。
- **取值建议**：本图不需要；控制数值范围请用 `xlim`。
- **报错**：`ylim=(0,)` → `ValueError: ylim 需要是 (最小值, 最大值) 两元组，例如 ylim=(0, 100)`

### `fmt` — 数值格式

- **类型 / 默认值**：`str` / `'compact'`
- **说明**：作用于横轴刻度与 tooltip（实际值、目标值、达成率里的数值）。可选 `compact` / `thousands` / `raw` / `percent` / `currency`；`fmt=None` 按 `compact` 处理。
- **取值建议**：金额用 `"thousands"` 或 `"currency"`；比例用 `"percent"`。
- **报错**：`fmt="cn"` → `ValueError: fmt='cn' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）

- **类型 / 默认值**：`int` / `380`
- **说明**：画布高度，最小 120；传 `None` 回落到 380。子弹图每行约占 30~40px，行数多时要相应加高。
- **取值建议**：类目 ≤8 用 380；10 个类目以上用 420~560。
- **报错**：`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题

- **类型 / 默认值**：`str` / `'light'`
- **说明**：`"light"` / `"dark"`，控制背景、文字与背景槽的灰度。
- **取值建议**：深色大屏用 `"dark"`，背景槽用 `surfaceVar`，在深底下仍能看清“槽”和“细条”的对比。
- **报错**：`theme="night"` → `ValueError: theme 只支持 "light" / "dark"，收到 'night'`

### `legend` — 是否显示图例（本图固定不显示）

- **类型 / 默认值**：`bool` / `False`
- **说明**：子弹图固定 `legend: false`，**本参数只写入 `spec["legend"]`，不渲染图例**；实际值 / 目标刻度靠 tooltip 与图形直觉区分。
- **取值建议**：保持默认；需要在图例位置说明“竖线是目标”时，用 `subtitle` 写一句。
- **示例**：`legend=True` → `chart.spec["legend"] is True`，画面无图例。

### `labels` — 是否标数值（本图不支持）

- **类型 / 默认值**：`bool` / `False`
- **说明**：子弹图构建器没有为条形/刻度配置 `label`，**本参数只写入 `spec["labels"]`，不会出现数值标签**；数值请通过 tooltip 查看。
- **取值建议**：需要常显数值时改用 `bar` + `labels=True`，或用 `target` 图。
- **示例**：`labels=True` → `chart.spec["labels"] is True`，画面无变化。

### `zoom` — 缩放条（本图不支持）

- **类型 / 默认值**：`bool` / `str` / `False`
- **说明**：只有核心笛卡尔图（`bar` / `line` / `area` / `combo`）消费 `spec.zoom` 并渲染 dataZoom；**子弹图构建器不读取该字段**。
- **取值建议**：行数太多时先聚合或下钻，不要依赖 `zoom`。
- **示例**：`zoom=True` → `chart.spec["zoom"] is True`，画面无缩放条。

### `drill` — 逐级下钻维度

- **类型 / 默认值**：`str` 或 `list[str]` / `None`
- **说明**：点击某一行后按该类目名过滤数据并重算，点「返回」回退。传字符串自动转列表；`drill[0]` 与 `x` 不同时自动把 `x` 插到最前。只传 `drill` 时 `x` 取 `drill[0]`。
- **取值建议**：从粗到细 2~3 层（大区 → 省份 → 城市）。
- **报错**：`drill=[]` → `ValueError: drill 不能是空列表；不需要下钻请传 drill=None。`；列名不存在 → `KeyError: "下钻维度列 '不存在' 不存在。当前可用的列有：……\n提示：drill 里的每一列都必须是 df 的列名。"`

### `link` — 联动组名

- **类型 / 默认值**：`str` / `None`
- **说明**：同 `link` 组的图表互相联动：点击某行把类目名广播给组内其它图，它们按同名列过滤重算。需要数据里有同名列。
- **取值建议**：看板里与销量趋势、明细表同组时统一命名，如 `link="region"`。
- **示例**：`link="region"`；`chart.spec["link"] == "region"`

### `max_rows` — 最大参与绘制行数

- **类型 / 默认值**：`int` / `200000`
- **说明**：超过则等间隔均匀抽样，warning 写入 `chart.warnings["warnings"]`，`chart.data["n_total"]` 保留原始行数；传 `None` 关闭采样。
- **取值建议**：子弹图通常只画聚合后的类目，建议先在 pandas 里 `groupby` 再传，`max_rows` 只作为兜底。
- **示例**：`max_rows=100` → `chart.data["n"] == 100`；`max_rows=None` → 不抽样

## 返回值

所有图表函数都返回 `eazy_data_viz.Chart` 对象（`chart = edv.bullet(df, x="大区", actual="销售额", target=500000)`）。

**Chart 的属性**

- `chart.spec`：`dict`，前端 ECharts 配置（JSON 可序列化）。公共键有 `id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`、`roles`、`agg`、`fmt`、`sort`、`topN`、`xtitle`、`ytitle`、`xlim`、`ylim`、`legend`、`labels`、`zoom`、`drill`、`link`，本图额外带 `targetValue`。
- `chart.data`：**`dict`**，不是 DataFrame。含 `cols`（列名）、`rows`（实际参与绘图的二维数组）、`dims` / `measures` / `kinds`、`orders`、`n`（参与行数）、`n_total`（原始行数）。
- `chart.data_ref`：数据引用 id（`d-` + 12 位 sha1），同内容数据在同一次会话复用。
- `chart.warnings`：**`dict`**，形如 `{"warnings": ["..."], "n_total": 1500}`；`warnings` 为空表示无降级。
- `chart.title`：只读属性，等价于 `chart.spec["title"]`。

**Chart 的方法**

- `chart.save(path, inline=True)`：写出单文件 HTML（约 1.2~1.5 MB），自动建目录，返回绝对路径。
- `chart.to_html(inline=True)`：返回完整 HTML 字符串；`inline=False` 引用外部资源。
- `chart.show(open_browser=None)`：浏览器打开；Jupyter / Streamlit 自动内嵌。
- `chart.palette(name)`：切换配色并返回 `self`；可选 `google`、`antd`、`tableau`、`carbon`、`echarts`、`morandi`、`tailwind`。

**本图 `spec` 的真实结构**

```json
{ "id": "c1", "type": "bullet", "title": "销售额 达成情况", "subtitle": null, "theme": "light",
  "height": 380, "dataRef": "d9465273f71af", "roles": {"x": "大区", "y": "销售额", "target": null},
  "agg": "sum", "targetValue": 500000.0, "sort": null, "topN": null, "xtitle": null,
  "ytitle": null, "xlim": null, "ylim": null, "fmt": "compact", "legend": false, "labels": false,
  "zoom": false, "drill": null, "link": null }
```

**验证返回值的小技巧**

```python
import eazy_data_viz as edv
df = edv.sample_df()
chart = edv.bullet(df, x="大区", actual="销售额", target=500000)
assert chart.spec["type"] == "bullet"
assert chart.spec["targetValue"] == 500000.0
assert chart.spec["roles"]["target"] is None
print(chart.warnings, len(chart.to_html()))
```

## 完整示例

以下示例都基于 `edv.sample_df()`（1500 行 × 11 列），可直接复制运行；输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法：统一目标 50 万

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.bullet(df, x="大区", actual="销售额", target=500000)
chart.save("examples/output/bullet_1.html")
```

**输出**：自动标题「销售额 达成情况」；4 行从下到上依次是数据顺序（纵轴反向，第一项在顶部）；每行背景槽到本行最大值，细条是实际值，竖线是 50 万目标。
**验证**：`chart.spec["targetValue"] == 500000.0`、`chart.spec["roles"]["target"] is None`。

### 示例 2：目标写成列：逐类目不同目标

```python
import eazy_data_viz as edv
df = edv.sample_df()

df["目标销售额"] = df["销售额"] * 1.15
chart = edv.bullet(
    df, x="大区", actual="销售额", target="目标销售额",
    fmt="thousands", xtitle="销售额（元）", ytitle="大区",
)
chart.save("examples/output/bullet_2.html")
```

**输出**：每个大区的目标 = 自身销售额 × 1.15（按大区求和后同样成立），因此达成率统一为 87.0%；`roles["target"]` 变成列名「目标销售额」。
**验证**：`chart.spec["roles"]["target"] == "目标销售额"`、`chart.spec["targetValue"] is None`。

### 示例 3：排序 + 固定满格刻度

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.bullet(
    df, x="产品", actual="销售额", target_value=500000,
    sort="desc", xlim=(0, 600000), fmt="thousands",
    title="产品销售额达成", subtitle="目标 50 万 / 产品",
)
chart.save("examples/output/bullet_3.html")
```

**输出**：按实际销售额从大到小排列（智能终端 → 行业软件 → 云服务 → 运维服务），横轴固定 0~60 万，目标竖线在 50 万处整齐对齐。
**验证**：`chart.spec["xlim"] == [0.0, 600000.0]`、`chart.spec["sort"] == "desc"`。

### 示例 4：下钻 + 联动

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.bullet(
    df, x="大区", actual="销售额", target_value=600000,
    drill=["大区", "省份"], link="kpi",
    title="销售额达成：可下钻到省份",
)
chart.save("examples/output/bullet_4.html")
```

**输出**：初始 4 行大区；点击某行按该大区过滤并切到省份维度重新计算实际值与达成率；同 `link="kpi"` 的图表同步过滤。
**验证**：`chart.spec["drill"] == ["大区", "省份"]`、`chart.spec["link"] == "kpi"`。

### 示例 5：target 与 target_value 同时传：后者优先

```python
import eazy_data_viz as edv
df = edv.sample_df()

c1 = edv.bullet(df, x="大区", actual="销售额", target="利润", target_value=300000)
c2 = edv.bullet(df, x="大区", actual="销售额", target=500000)
assert c1.spec["targetValue"] == 300000.0   # target_value 覆盖列值
assert c2.spec["targetValue"] == 500000.0   # 数字 target 自动转 target_value
c1.save("examples/output/bullet_5.html")
```

**输出**：`target_value` 优先于 `target` 列，`roles["target"]` 仍记录列名但渲染时以 `targetValue` 为准；数字形式的 `target` 会被内部转成 `targetValue`。
**验证**：两个 `assert` 都通过；`c1.spec["roles"]["target"] == "利润"`。

### 示例 6：边界：目标为 0 / 空目标

```python
import eazy_data_viz as edv
df = edv.sample_df()

# 目标为 0：tooltip 不显示达成率，但图仍能画
c1 = edv.bullet(df, x="大区", actual="销售额", target_value=0)
# 低基数类目（订单数只有 1~4 四个取值）同样可以画
chart = edv.bullet(df, x="订单数", actual="订单数", target_value=2)
chart.save("examples/output/bullet_6.html")
```

**输出**：`target_value=0` 时所有目标刻度贴在 0 处、tooltip 只有实际值与目标值；`x="订单数"` 这类低基数类目也能正常渲染（4 行）。
**验证**：`c1.spec["targetValue"] == 0.0`、`chart.data["n"] == 1500`。

## 常见错误

### 1. 把 `target=True` 当成“统一目标”

```python
import eazy_data_viz as edv
df = edv.sample_df()
# 错误写法：bool 不是数字，会被当成列名
# edv.bullet(df, x="大区", actual="销售额", target=True)
# → KeyError: "target（目标值）列 True 不存在。当前可用的列有：日期, 月份, 大区, ..."
# 正确写法：用 target_value
chart = edv.bullet(df, x="大区", actual="销售额", target_value=500000)
```

**修法**：统一目标一律用 `target_value=`；`target=` 只接列名或纯数字（`bool` 会被当成列名）。

### 2. 目标列里混进了文本

```python
import eazy_data_viz as edv
df = edv.sample_df()
# 错误写法：目标列是文本（如 "50万"）
# df["目标"] = "50万"
# edv.bullet(df, x="大区", actual="销售额", target="目标")
# → TypeError: y（数值）列 '目标' 需要是数值类型（当前是文本，例如 ['50万']）……
# 正确写法：清洗成数字
df["目标"] = 500000.0
chart = edv.bullet(df, x="大区", actual="销售额", target="目标")
```

**修法**：`pd.to_numeric(df["目标"].str.replace("万", "").astype(float) * 10000, errors="coerce")`，或直接把目标写成数字列。

### 3. 轴标题写反了

```python
import eazy_data_viz as edv
df = edv.sample_df()
# 子弹图是横向的：xtitle 是数值轴、ytitle 才是类目轴
chart = edv.bullet(
    df, x="大区", actual="销售额", target_value=500000,
    xtitle="大区",          # 显示在横轴（数值轴）上 —— 名字会误导
    ytitle="销售额（元）",   # 显示在纵轴（类目轴）上
)
chart2 = edv.bullet(
    df, x="大区", actual="销售额", target_value=500000,
    xtitle="销售额（元）", ytitle="大区",
)
```

**修法**：横向图记住“`xtitle` 管数值、`ytitle` 管类目”；不确定时把两个都传 `""`，用 `subtitle` 说明单位。

### 4. 指望 `labels` / `zoom` 生效

```python
import eazy_data_viz as edv
df = edv.sample_df()
# 这两个参数会写进 spec，但本图构建器不消费：画面不会出现标签和缩放条
chart = edv.bullet(df, x="大区", actual="销售额", target_value=500000, labels=True, zoom=True)
assert chart.spec["labels"] is True and chart.spec["zoom"] is True
```

**修法**：常显数值改用 `bar(labels=True)`；数据量大时在 pandas 侧聚合或使用 `drill`。

## 相关图表

- `target`：和子弹图同源，但目标用虚线折线表示，适合看“目标随时间/类目的走势”。
- `bar`：只比较实际值大小时用普通柱状图，信息密度更低但更直观。
- `lollipop`：类目多、只关心单个指标的相对大小时更清爽。
- `gauge`：单个指标完成率（0~100%）的仪表盘表达。
- `waterfall`：想把“实际与目标的差额”拆成增减项时使用。
