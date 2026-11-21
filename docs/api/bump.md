# `bump` — 排名图：多期排名变化的平滑折线

> 每个时间点把各分组按数值从高到低排名，纵轴是名次（1 在最上面），每个分组一条平滑折线；线的交叉就是名次互换。
> 适合：月度/季度排名变化（产品销量榜、门店排行）、多期竞赛追赶、名次稳定性分析。
> 不适合：看绝对数值趋势（用 `line`）、只有两期（用 `slope`）、需要精确数值对比（用 `bar`）。

## 函数签名

```python
def bump(
    data,
    x,
    y,
    *,
    group,
    agg="sum",
    sort=None,
    top_n=None,
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    xlim=None,
    ylim=None,
    fmt="compact",
    height=420,
    theme="light",
    legend=True,
    labels=False,
    zoom="auto",
    drill=None,
    link=None,
    max_rows=200000,
) -> "Chart":
    ...
```

> `data` / `x` / `y` 是位置参数；`group` 是**必填的关键字参数**（`*` 之后的第一个），其余都是关键字限定参数。
> 参数个数 22：3 个位置参数 + 19 个关键字参数（含必填的 `group`）。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `data` | `pandas.DataFrame \| dict \| list \| Series` | `—` | 是 | 数据源，图表取数的唯一入口 |
| `x` | `str` | `—` | 是 | 时间/期别列名（横轴） |
| `y` | `str` | `—` | 是 | 排名依据的数值列 |
| `group` | `str` | `—` | 是 | 参与排名的分组列（每个取值一条线） |
| `agg` | `str` | `'sum'` | 否 | 聚合方式 |
| `sort` | `str` | `None` | 否 | 排序：x（按时间排序） |
| `top_n` | `int` | `None` | 否 | 只保留前 N 项（当前版本不裁剪，见详解） |
| `title` | `str \| None` | `None` | 否 | 主标题，默认自动生成 |
| `subtitle` | `str \| None` | `None` | 否 | 副标题（灰色小字） |
| `xtitle` | `str \| None` | `None` | 否 | 时间轴（横轴）标题 |
| `ytitle` | `str \| None` | `None` | 否 | 数值名称（只影响 tooltip，纵轴固定「排名」） |
| `xlim` | `tuple[float, float]` | `None` | 否 | 时间轴范围（本图不生效） |
| `ylim` | `tuple[float, float]` | `None` | 否 | 数值范围（本图为排名轴，不生效） |
| `fmt` | `str` | `'compact'` | 否 | 数值格式：compact / thousands / raw / percent / currency |
| `height` | `int` | `420` | 否 | 画布高度（像素，≥120） |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `str` | `'light'` | 否 | light / dark |
| `legend` | `bool` | `True` | 否 | 是否显示图例 |
| `labels` | `bool` | `False` | 否 | 是否在点上标**实际值**（不是名次） |
| `zoom` | `bool \| str` | `'auto'` | 否 | 缩放条（本图不支持） |
| `drill` | `str \| list[str]` | `None` | 否 | 逐级下钻维度 |
| `link` | `str` | `None` | 否 | 联动组名（同组图表互相筛选） |
| `max_rows` | `int` | `200000` | 否 | 最大参与绘制行数（None 不采样） |

## 参数详解

### `data` — 数据源，图表取数的唯一入口（必填）

- **类型 / 默认值**：`pandas.DataFrame`、`dict`、`list`（每项一行）或 `Series` / 无
- **说明**：经 `frame.ensure_frame()` 归一化成 DataFrame；行数超过 `max_rows` 时均匀抽样并提示。
- **取值建议**：长表结构（一行 = 一个时间点 × 一个分组 × 数值）最合适；宽表请先 `melt`。
- **报错**：`data=None` → `ValueError: data 不能为空，请传入 pandas.DataFrame（或 dict / list）。`；`data=42` → `TypeError: 无法识别 data 类型 'int'，请传入 pandas.DataFrame（或 dict / list）。`

### `x` — 时间/期别列名（必填）

- **类型 / 默认值**：`str` / 无
- **说明**：横轴的每个位置对应 `x` 的一个取值（按期去重），在每个位置内部对各分组按值排名。类目顺序默认按数据中首次出现顺序；`sort="x"` 时按 `x` 值排序（月份这类有序分类能正确排成 1 月→12 月）。
- **取值建议**：期别数 3~12 最合适；`x` 是有序分类（如 `月份`）时强烈建议 `sort="x"`，否则顺序可能乱。
- **报错**：不传 → `TypeError: bump() missing 1 required positional argument: 'x'`；列名写错 → `KeyError: "x（类目）列 '不存在' 不存在。当前可用的列有：日期, 月份, 大区, 省份, 城市, 产品, 渠道, 销售额, 订单数, 利润, 客户数"`

### `y` — 排名依据的数值列（必填）

- **类型 / 默认值**：`str` / 无
- **说明**：数值越大名次越靠前（名次 1 在最上方）。tooltip 里同时显示数值与名次；`labels=True` 时点旁标的是**数值**不是名次。
- **取值建议**：同一 `x` 位置内各分组必须都有值（缺值的分组该期不参与排名，线会断开）；量纲不一致的分组不要放在同一张图。
- **报错**：文本列 → `TypeError: y（数值）列 '产品' 需要是数值类型……`

### `group` — 参与排名的分组列（必填，关键字参数）

- **类型 / 默认值**：`str` / 无
- **说明**：`group` 的每个取值画一条线，每个时间点内按 `y` 降序给出名次（1、2、3…）。纵轴范围自动取 `1 ~ max(2, 分组数)`。`group` 必须用关键字传（`group="产品"`），不能按位置传。
- **取值建议**：分组数 3~10（多了线会缠在一起）；组名要短，图例才不占地方。
- **报错**：省略 → `TypeError: bump() missing 1 required keyword-only argument: 'group'`；列名不存在 → `KeyError: "group（分组）列 '不存在' 不存在。当前可用的列有：……"`；显式传 `group=None` 不报错，但会画出空图。

### `agg` — 聚合方式

- **类型 / 默认值**：`str` / `'sum'`
- **说明**：按 (`x`, `group`) 聚合 `y` 后再排名。可选 `sum` / `mean` / `count` / `max` / `min` / `median`。
- **取值建议**：销量/金额用 `"sum"`；比率/得分用 `"mean"`；排名对聚合方式很敏感，口径要统一。
- **报错**：`agg="avg"` → `ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median`

### `sort` — 排序方式

- **类型 / 默认值**：`str` / `None`
- **说明**：本图只对**时间轴**有意义：`"x"` 按期别值排序，其它取值（含 `"asc"` / `"desc"`）不改变时间顺序（排名本身由数值决定，不需要额外排序）。
- **取值建议**：期别是月份/季度这类有序分类时用 `"x"`；其它情况保持 `None` 即可。
- **示例**：`sort="x"` → 1 月 → 12 月顺序排列

### `top_n` — 只保留前 N 项（当前版本不裁剪）

- **类型 / 默认值**：`int` / `None`
- **说明**：只做合法性校验并写入 `spec["topN"]`。**1.0.0 中排名图的前端构建器不读取 `spec.topN`，本参数不会减少分组或期别**。
- **取值建议**：先过滤数据（如只保留 Top 5 产品）再画。
- **报错**：`top_n=0` → `ValueError: top_n 需要是 >=1 的整数（只显示前 N 项），收到 0`

### `title` — 主标题

- **类型 / 默认值**：`str` / `None`
- **说明**：不传时自动生成「<y 列名> 排名变化」；传 `""` 得到空标题（不回落自动）。
- **取值建议**：写清“谁在排什么名”，例如 `"产品月度销售额排名变化"`。
- **示例**：`title=None` → `chart.spec["title"] == "销售额 排名变化"`

### `subtitle` — 副标题

- **类型 / 默认值**：`str` / `None`
- **说明**：标题下方的小字说明，默认没有。
- **取值建议**：注明排名规则（如“按月销售额合计，1 名为最高”）。
- **示例**：`subtitle="按月销售额合计排名，1 = 最高"`

### `xtitle` — 时间轴（横轴）标题

- **类型 / 默认值**：`str` / `None`
- **说明**：不传时用 `x` 列名；传 `""` 隐藏。
- **取值建议**：期别标签已自明时可传 `""`。
- **示例**：`xtitle="月份"`；`xtitle=""` → 横轴无标题

### `ytitle` — 数值名称（只影响 tooltip）

- **类型 / 默认值**：`str` / `None`
- **说明**：注意本图纵轴是**排名轴**，轴名固定为「排名」，`ytitle` 不改变轴名；它只作为 tooltip 里数值那一行的标签（不传时用 `y` 列名）。传 `""` 时 tooltip 不显示该标签。
- **取值建议**：写上业务含义（如“销售额”），方便看 tooltip 时区分数值与名次。
- **示例**：`ytitle="销售额（元）"` → 轴名仍是「排名」，tooltip 里显示“销售额（元）: 174,919”

### `xlim` — 时间轴范围（本图不生效）

- **类型 / 默认值**：`tuple[float, float]` / `None`
- **说明**：时间轴由 `x` 的取值决定，`xlim` 只写入 `spec["xlim"]`，不改变画面；格式错误仍会报错。
- **取值建议**：本图不需要。
- **报错**：`xlim=(0,)` → `ValueError: xlim 需要是 (最小值, 最大值) 两元组，例如 xlim=(0, 100)`

### `ylim` — 数值范围（本图为排名轴，不生效）

- **类型 / 默认值**：`tuple[float, float]` / `None`
- **说明**：纵轴被固定在 `1 ~ max(2, 分组数)` 的排名刻度上，`ylim` 只写入 `spec["ylim"]`，不改变画面。
- **取值建议**：本图不需要；分组数变化时纵轴会自动伸缩。
- **示例**：`ylim=(1, 5)` → `chart.spec["ylim"] == [1.0, 5.0]`，画面不变

### `fmt` — 数值格式

- **类型 / 默认值**：`str` / `'compact'`
- **说明**：作用于 `labels` 显示的实际值与 tooltip 里的数值。可选 `compact` / `thousands` / `raw` / `percent` / `currency`；`fmt=None` 按 `compact` 处理。
- **取值建议**：金额用 `"thousands"`；排名轴本身是整数，不受影响。
- **报错**：`fmt="cn"` → `ValueError: fmt='cn' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素）

- **类型 / 默认值**：`int` / `420`
- **说明**：排名图默认比其他扩展图高 40px（420），给线间交叉留出空间；传 `None` 时**回落到 380**（不是 420）。
- **取值建议**：分组 4~6 用 420；7 个以上用 480~560。
- **报错**：`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题

- **类型 / 默认值**：`str` / `'light'`
- **说明**：`"light"` / `"dark"`，控制背景、文字、网格与线条颜色。
- **取值建议**：深色大屏用 `"dark"`；排名图线条多，深底下建议同时关闭 `labels` 避免拥挤。
- **报错**：`theme="night"` → `ValueError: theme 只支持 "light" / "dark"，收到 'night'`

### `legend` — 是否显示图例

- **类型 / 默认值**：`bool` / `True`
- **说明**：**本图生效**，图例列出每个分组（`group` 的取值），是识别线条的主要手段。
- **取值建议**：分组名短时保持 `True`；分组 >8 时图例占空间，可考虑关掉并用 `labels` 辅助。
- **示例**：`legend=False` → 图例隐藏

### `labels` — 是否在点上标实际值

- **类型 / 默认值**：`bool` / `False`
- **说明**：**本图生效**，标的是**实际数值**（按 `fmt` 格式化），不是名次；每期 × 每个分组都有标签，容易重叠。
- **取值建议**：期别 ≤6 且分组 ≤4 时开启；否则用 tooltip（tooltip 同时给数值和名次）。
- **示例**：`labels=True` → 每个点上显示实际销售额

### `zoom` — 缩放条（本图不支持）

- **类型 / 默认值**：`bool` / `str` / `'auto'`
- **说明**：只有核心笛卡尔图消费 `spec.zoom`；**排名图构建器不读取该字段**，`"auto"` 也不会自动加缩放条。
- **取值建议**：期别太多时截取区间，不要依赖缩放。
- **示例**：`zoom=True` → `chart.spec["zoom"] is True`，画面无缩放条。

### `drill` — 逐级下钻维度

- **类型 / 默认值**：`str` 或 `list[str]` / `None`
- **说明**：点击某个期别/分组后按类目名过滤数据并重算排名；点「返回」回退。传字符串自动转列表；`drill[0]` 与 `x` 不同时自动把 `x` 插到最前。
- **取值建议**：下钻后分组集合会变（排名跟着重算），注意别把“过滤后的第 1 名”误读成全量第 1 名。
- **报错**：`drill=[]` → `ValueError: drill 不能是空列表；不需要下钻请传 drill=None。`；列名不存在 → `KeyError: "下钻维度列 '不存在' 不存在。……"`

### `link` — 联动组名

- **类型 / 默认值**：`str` / `None`
- **说明**：同 `link` 组的图表互相联动：点击后把类目名广播给组内其它图，它们按同名列过滤重算。
- **取值建议**：与同页趋势图、明细表统一命名，如 `link="product"`。
- **示例**：`link="product"`；`chart.spec["link"] == "product"`

### `max_rows` — 最大参与绘制行数

- **类型 / 默认值**：`int` / `200000`
- **说明**：超过则等间隔均匀抽样，warning 写入 `chart.warnings["warnings"]`，`chart.data["n_total"]` 保留原始行数；`None` 关闭采样。
- **取值建议**：排名图先 `groupby(["月份","产品"])` 聚合再传；抽样会改变名次。
- **示例**：`max_rows=100` → `chart.data["n"] == 100`

## 返回值

所有图表函数都返回 `eazy_data_viz.Chart` 对象（`chart = edv.bump(df, x="月份", y="销售额", group="产品")`）。

**Chart 的属性**

- `chart.spec`：`dict`，前端 ECharts 配置（JSON 可序列化）。公共键有 `id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`、`roles`、`agg`、`fmt`、`sort`、`topN`、`xtitle`、`ytitle`、`xlim`、`ylim`、`legend`、`labels`、`zoom`、`drill`、`link`；本图没有额外键（`group` 记在 `roles["color"]` 里）。
- `chart.data`：**`dict`**，不是 DataFrame。含 `cols`、`rows`、`dims` / `measures` / `kinds`、`orders`、`n`、`n_total`。
- `chart.data_ref`：数据引用 id（`d-` + 12 位 sha1）。
- `chart.warnings`：**`dict`**，形如 `{"warnings": [...], "n_total": 1500}`。
- `chart.title`：只读属性，等价于 `chart.spec["title"]`。

**Chart 的方法**

- `chart.save(path, inline=True)`：写出单文件 HTML（约 1.2~1.5 MB），自动建目录，返回绝对路径。
- `chart.to_html(inline=True)`：返回完整 HTML 字符串；`inline=False` 引用外部资源。
- `chart.show(open_browser=None)`：浏览器打开；Jupyter / Streamlit 自动内嵌。
- `chart.palette(name)`：切换配色并返回 `self`；可选 `google`、`antd`、`tableau`、`carbon`、`echarts`、`morandi`、`tailwind`。

**本图 `spec` 的真实结构**

```json
{ "id": "c1", "type": "bump", "title": "销售额 排名变化", "subtitle": null, "theme": "light",
  "height": 420, "dataRef": "d9465273f71af", "roles": {"x": "月份", "y": "销售额", "color": "产品"},
  "agg": "sum", "sort": null, "topN": null, "xtitle": null, "ytitle": null, "xlim": null,
  "ylim": null, "fmt": "compact", "legend": true, "labels": false, "zoom": "auto", "drill": null,
  "link": null }
```

**验证返回值的小技巧**

```python
import eazy_data_viz as edv
df = edv.sample_df()
chart = edv.bump(df, x="月份", y="销售额", group="产品")
assert chart.spec["type"] == "bump"
assert chart.spec["roles"] == {"x": "月份", "y": "销售额", "color": "产品"}
assert chart.spec["height"] == 420
print(chart.warnings, len(chart.to_html()))
```

## 完整示例

以下示例都基于 `edv.sample_df()`（1500 行 × 11 列），可直接复制运行；输出文件写到 `examples/output/`（该目录已 gitignore）。

### 示例 1：最简用法：产品月度排名

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.bump(df, x="月份", y="销售额", group="产品")
chart.save("examples/output/bump_1.html")
```

**输出**：自动标题「销售额 排名变化」；横轴 12 个月（按数据首次出现顺序），4 条线分别代表 4 个产品；纵轴为 1~4 名，名次最高的线在上方。
**验证**：`chart.spec["roles"]["color"] == "产品"`、`chart.spec["height"] == 420`。

### 示例 2：按时间排序 + 数值标签

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.bump(
    df, x="月份", y="销售额", group="产品",
    sort="x", labels=True, fmt="thousands",
    title="产品销售额月度排名", subtitle="按月合计排名，1 = 最高",
)
chart.save("examples/output/bump_2.html")
```

**输出**：横轴按 1 月 → 12 月排列（月份是有序分类）；每个点上标实际销售额（千分位），不是名次。
**验证**：`chart.spec["sort"] == "x"`、`chart.spec["labels"] is True`。

### 示例 3：3 个渠道的排名变化

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.bump(
    df, x="月份", y="销售额", group="渠道",
    sort="x", theme="dark", height=480, legend=True,
    subtitle="深色主题，3 条线",
)
chart.save("examples/output/bump_3.html")
```

**输出**：3 条线（直销 / 渠道代理 / 线上商城）在 12 个月内的名次变化；纵轴范围 1~3；深色主题下线条与文字对比清晰。
**验证**：`chart.spec["theme"] == "dark"`、`chart.spec["legend"] is True`。

### 示例 4：`ytitle` 只影响 tooltip

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.bump(
    df, x="月份", y="销售额", group="产品", sort="x",
    ytitle="销售额（元）", xtitle="月份", fmt="thousands",
)
chart.save("examples/output/bump_4.html")
```

**输出**：纵轴轴名仍是固定的「排名」；`ytitle` 只出现在 tooltip 里，形式如“销售额（元）: 174,919”，与“名次: 1”并列。
**验证**：`chart.spec["ytitle"] == "销售额（元）"`（画面轴名不变）。

### 示例 5：下钻 + 联动

```python
import eazy_data_viz as edv
df = edv.sample_df()

chart = edv.bump(
    df, x="月份", y="销售额", group="产品",
    sort="x", drill=["月份", "大区"], link="rank",
    title="产品排名变化（可下钻）",
)
chart.save("examples/output/bump_5.html")
```

**输出**：初始按月份展示 4 条产品线；点击后按该位置过滤并切到大区维度，重新形成排名线；同 `link="rank"` 的图表同步过滤。
**验证**：`chart.spec["drill"] == ["月份", "大区"]`、`chart.spec["link"] == "rank"`。

### 示例 6：边界：分组只有 1 个取值

```python
import eazy_data_viz as edv
df = edv.sample_df()

sub = df[df["大区"] == "华东"]
chart = edv.bump(sub, x="月份", y="销售额", group="产品", sort="x")
# 纵轴范围自动取 1 ~ max(2, 4) = 1~4（4 个产品仍是 4 条线）
print(chart.spec["roles"])
chart.save("examples/output/bump_6.html")
```

**输出**：只剩华东的数据参与计算，名次会重排；纵轴范围由分组数决定（此处 4 个产品 → 1~4），不会因为只有 1 行数据而塌缩。
**验证**：`chart.data["n_total"] == len(sub)`（约 375 行）。

## 常见错误

### 1. 忘了传 `group`

```python
import eazy_data_viz as edv
df = edv.sample_df()
# edv.bump(df, x="月份", y="销售额")
# → TypeError: bump() missing 1 required keyword-only argument: 'group'
chart = edv.bump(df, x="月份", y="销售额", group="产品")
```

**修法**：`group` 是必填关键字参数，必须写 `group="列名"`；同时确认这一列是**分组**（每期都会出现），不是期别本身。

### 2. `group` 传了唯一值列（选错列）

```python
import eazy_data_viz as edv
df = edv.sample_df()
# 错误：用“城市”当分组（10 条线，太密）；或者用常量列（只有 1 条线，无排名意义）
chart = edv.bump(df, x="月份", y="销售额", group="产品")     # 4 条线，合适
chart2 = edv.bump(df.head(50), x="月份", y="销售额", group="城市")
```

**修法**：分组列应有 3~10 个取值，且几乎每期都有数据；先用 `df["产品"].nunique()` 检查基数。

### 3. 期别顺序错乱

```python
import eazy_data_viz as edv
df = edv.sample_df()
# 不排序：横轴按数据首次出现顺序，可能不是 1 月→12 月
chart = edv.bump(df, x="月份", y="销售额", group="产品")
# 正确：月份是有序分类，用 sort="x" 保证时间顺序
chart2 = edv.bump(df, x="月份", y="销售额", group="产品", sort="x")
```

**修法**：`x` 是有序分类/日期时加 `sort="x"`；字符串型期别（"Q1"…"Q4"）建议先改成有序分类。

### 4. 想用 `ylim` / `zoom` 调整画面

```python
import eazy_data_viz as edv
df = edv.sample_df()
chart = edv.bump(df, x="月份", y="销售额", group="产品",
                 ylim=(0, 100), zoom=True, xlim=(0, 12))
# 纵轴是排名轴，固定 1~分组数；ylim / xlim / zoom 只写进 spec，不改变画面
assert chart.spec["ylim"] == [0.0, 100.0]
```

**修法**：名次轴由分组数决定，无法配置；期别太多时截取时间区间。

## 相关图表

- `slope`：只有两期的排名/数值变化。
- `line`：看绝对数值走势而不是名次。
- `bar`：某一期的排名快照（单期柱状图）。
- `dumbbell`：两期数值差值的另一种表达。
- `trend`：单指标随时间变化的趋势线（无多组排名）。
