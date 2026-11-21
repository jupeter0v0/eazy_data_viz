# `ring_progress` — 圆环进度图（单值达成率）

> 用一个圆环把「已完成量 / 目标量」的比值画出来，环内大字显示百分比，副文字说明这是哪个指标。
> 适合：单个核心指标的达成率（完成率、预算消耗率、目标达成度），大屏顶部或 Dashboard 里的「一眼看数」位置。
> 不适合：多个类目的横向对比（用 `progress` 或 `tile`）、随时间变化的趋势（用 `line` / `area`）、需要精确比较的数值（圆环面积不精确，用 `bar` / `kpi`）。

## 函数签名

```python
eazy_data_viz.ring_progress(
    percent,
    *,
    label=None,
    max=100,
    fmt=None,
    height=None,
    theme="light",
    title=None,
) -> Chart
```

签名要点：

- `percent` 是唯一的位置参数，其余参数全部是 keyword-only（`*` 之后），必须写 `max=2000`，不能写 `ring_progress(1280, 2000)`。
- 函数只接**一个数值**，不接 DataFrame；没有 `data` / `agg` / `sort` / `top_n` / `legend` / `drill` / `link` / `max_rows` 参数。
- 需要从 DataFrame 里算出一个比值时，先自己聚合（`df["销售额"].sum()`），再把结果传进来。
- 返回的是普通的 `eazy_data_viz.Chart` 对象，属性与方法与其它图表一致。

## 参数总览

| 参数 | 类型 | 默认值 | 必填 | 一句话说明 |
| --- | --- | --- | --- | --- |
| `percent` | `int \| float` | `—` | 是 | 已完成量（分子），渲染时换算成百分比 |
| `label` | `str \| None` | `None` | 否 | 环内副文字，也作为默认标题的兜底 |
| `max` | `int \| float` | `100` | 否 | 目标量（分母），必须大于 0 |
| `fmt` | `str \| None` | `None` | 否 | 中心数字与 tooltip 的数值格式，None 等价 `"raw"` |
| `height` | `int \| None` | `None` | 否 | 画布高度，None 等价 260，且必须 ≥120 |
| `abs_height` | `bool` | `False` | 否 | 绝对高度：`height` 当整个组件外框（含标题 / 工具条） |
| `theme` | `str` | `"light"` | 否 | 主题：`light` / `dark` |
| `title` | `str \| None` | `None` | 否 | 主标题，None 时用 `label`，再兜底「进度」 |

## 参数详解

### `percent` — 已完成量（分子，必填）

- **类型**：`int | float`（能被 `float()` 转换的数值）
- **默认值**：无
- **说明**：
  - 达成率的分子。函数内部先 `float(percent)`，再把结果原样写进 `spec["percentValue"]`。
  - 渲染时才计算占比：`pct = percentValue / max * 100`，并夹取到 `[0, 100]` 区间。所以 `percent=150` 不报错，但环画满、中心显示 `100%`；`percent=-5` 同样不报错，显示 `0%`。
  - 数值必须是**有限**值：`NaN`、`inf` 会直接抛 `ValueError`，而不是静默画成空图。
  - 这里传的是「已完成量」而不是「百分比小数」：传 `0.72` 配 `max=100` 会显示 `0.7%`，想要 72% 请传 `72` 或 `72.5`。
- **取值建议**：
  - 与 `max` 保持同一量纲。百分比直接 `percent=72.5`（默认 `max=100`）；金额/件数用 `percent=已完成金额, max=目标金额`。
  - 监控类指标允许溢出时保留真实值（例如 `128` / `100`），让读者从「100%」+ tooltip 里看出是超额完成。
  - 需要展示小数点后一位就传浮点（`72.5`），需要整数就传整数（`72`）。
- **示例**：`ring_progress(72.5)`；`ring_progress(1280, max=2000)`
- **常见错误**：
  - `ring_progress(None)` → `TypeError: ring_progress 接受单个数值，例如 ring_progress(72.5, label="完成率")。如果要画 DataFrame，请用 eazy_data_viz.charts_extra.progress(df, x=..., y=...)。`
  - `ring_progress(float("nan"))` → `ValueError: ring_progress 的 percent 必须是有限数值，收到 nan`

### `label` — 环内副文字

- **类型**：`str | None`
- **默认值**：`None`
- **说明**：
  - 在圆环中心、百分比大字的下一行显示一行灰色小字（位置在半径 60% 处，左对齐居中），用来解释这个百分比是什么。
  - 该值原样写进 `spec["label"]`；`None` 时不渲染第二行文字。
  - 同时是默认标题的兜底：`title=None` 时，标题取 `label`；`label` 也为 `None` 时标题是「进度」。
- **取值建议**：
  - 4~8 个字最合适，例如「Q3 完成率」「库存周转」「预算消耗」。
  - 已经有 `title` 描述指标时，`label` 可以放时间范围或统计口径（「2024 全年」「含税」）。
  - 不要在 `label` 里重复百分比数字，中心大字已经显示了占比。
- **示例**：`label="完成率"`
- **常见错误**：无（不做校验，非字符串会原样进 `spec`；建议统一传 `str`）

### `max` — 目标量（分母，默认 100）

- **类型**：`int | float`
- **默认值**：`100`
- **说明**：
  - 达成率的分母。内部转成 `float` 后同时写进 `spec["max"]` 与 `spec["maxValue"]`（后者是给前端取数用的别名）。
  - 取值必须**大于 0 且有限**，否则抛 `ValueError`；传字符串数字（`"2000"`）会被 `float` 转成功，但建议直接传数值。
  - 默认 100 表示「`percent` 本身就是百分数」，这是最常用的用法；只有目标不是 100 时才需要显式传。
  - 前端还有一层兜底：如果 `spec["max"]` 缺失或不大于 0，按 100 计算——但 Python 侧已经挡住了非法值，正常走不到这一步。
- **取值建议**：
  - 目标金额/目标件数直接写目标值，例如 `max=2000000`。
  - 想表达「超出目标」不必把 `max` 调大，保留真实目标更诚实，超出部分会被夹到 100%，tooltip 里仍能看到真实完成量。
  - 不要把 `max` 和 `percent` 写成不同量纲（一个元、一个万元），否则占比会错得离谱。
- **示例**：`ring_progress(1280, max=2000)` → 占比 64%
- **常见错误**：
  - `ring_progress(50, max=0)` → `ValueError: ring_progress 的 max 必须大于 0，收到 0`
  - `ring_progress(50, max=-1)` → `ValueError: ring_progress 的 max 必须大于 0，收到 -1`
  - `ring_progress(50, max="一百")` → `TypeError: ring_progress 的 max 需要是数值，例如 max=100，收到 '一百'`

### `fmt` — 中心数字与 tooltip 的数值格式（默认 `None` → `"raw"`）

- **类型**：`str | None`
- **默认值**：`None`（等价 `"raw"`）
- **说明**：
  - 写入 `spec["fmt"]`。`None` 时函数内部替换为 `"raw"`，不是「不格式化」。
  - 合法值只有 5 个：`compact`、`thousands`、`raw`、`percent`、`currency`；传其它值抛 `ValueError`。
  - 渲染时这个格式作用于两个位置：
    1. 中心大字：先算出占比 `pct`，再用 `fmtValue(pct, fmt)` 格式化；如果结果里没有 `%`，前端会**自动补一个 `%`**。
    2. tooltip 的「完成」项：用同一个 `fmt` 格式化 `percentValue`。
  - 因此 `fmt="raw"`（默认）时中心显示 `72.5%`；`fmt="thousands"` 时中心仍是 `72.5%`，但 tooltip 的完成量显示 `1,280`；`fmt="percent"` 时 tooltip 的完成量会显示成 `1280.0%`（percent 格式不乘 100，只是加百分号）。
- **取值建议**：
  - 只关心百分比、不想被格式化干扰：保持默认（`raw`）或显式 `fmt="percent"`。
  - 完成量是金额且希望 tooltip 里带千分位：`fmt="thousands"`。
  - 不建议 `currency`：中心大字会变成「¥64.00%」这种混合文本，语义混乱。
- **示例**：`ring_progress(1280, max=2000, fmt="thousands")`
- **常见错误**：`fmt="usd"` → `ValueError: fmt='usd' 不支持，可选：compact, thousands, raw, percent, currency`

### `height` — 画布高度（像素，默认 `None` → 260）

- **类型**：`int | None`
- **默认值**：`None`（内部取 260）
- **说明**：
  - `None` 表示用本图默认高度 260；传数值时写入 `spec["height"]`，页面按这个高度固定渲染 ECharts 容器（圆环本身不在自适应高度名单里，`height` 直接决定画布大小）。
  - 通用校验要求 `height ≥ 120`，否则抛 `ValueError`。圆环图低于 200 时中心文字和环会明显拥挤。
- **取值建议**：
  - 大屏主指标 260~320；并排卡片 220~260；嵌在窄卡片里不要低于 200。
  - 和其它图混排时，让同一行的卡片高度接近，避免页面出现高低不齐的台阶。
- **示例**：`ring_progress(72.5, height=300)`
- **常见错误**：`height=100` → `ValueError: height 至少 120（像素），收到 100`

### `abs_height` — 绝对高度：`height` 就是整个组件外框（`bool`，默认 `False`）

- **作用**：默认 `height` 只算图表正文，标题 / 副标题 / 联动工具条会把卡片额外撑高，同一行里一张带长标题、一张带工具条的卡片底边就对不齐。打开 `abs_height=True` 后 `height` 表示**整个组件外框**（内边距、标题、工具条都算在里面），正文用剩余空间自适应。
- **建议**：在 `dashboard` / `show` 里要「框和框严格对齐」时打开；单图导出或不在意卡片底边时保持默认。
- **示例**：`abs_height=True, height=320`（配合 `dashboard(..., cols=2)` 看两张卡的底边）

### `theme` — 主题（默认 `"light"`）

- **类型**：`str`
- **默认值**：`"light"`
- **说明**：
  - `"light"` 浅色背景、深色文字；`"dark"` 深色背景、浅色文字，圆环余量段的灰色也会跟着反转。
  - 只影响配色与背景，不改变占比计算与布局。
- **取值建议**：
  - 报告/网页默认 `light`；大屏、夜间看板用 `dark`。
  - 同一个页面的所有图保持同一主题，否则圆环和旁边图表的底色会明显割裂。
- **示例**：`ring_progress(72.5, theme="dark")`
- **常见错误**：`theme="blue"` → `ValueError: theme 只支持 "light" / "dark"，收到 'blue'`

### `title` — 主标题（默认 `None`）

- **类型**：`str | None`
- **默认值**：`None`
- **说明**：
  - 卡片顶部标题。优先级是 `title` → `label` → 固定字符串「进度」，三者都不是 `None` 时以 `title` 为准。
  - 写进 `spec["title"]`，同时参与页面高度估算（有标题时卡片头部占 46px）。
  - 传空字符串 `""` 会被当成「有 title 但内容为空」，不会回退到 `label`；需要回退就传 `None`。
- **取值建议**：
  - 标题负责说明「这个数字是什么」，例如「2024 Q3 销售完成率」；`label` 负责说明口径。
  - 单图嵌在已经有大标题的区块里时，可以把 `title` 设成指标名、把区块说明放在外层。
- **示例**：`title="2024 Q3 完成率"`
- **常见错误**：无（任意字符串都接受）

## 返回值

返回 `eazy_data_viz.Chart` 对象，与其它图表函数一致。

**Chart 的通用属性**

- `chart.spec`：`dict`，前端 ECharts 的完整配置，JSON 可序列化。公共键有 `id`、`type`、`title`、`subtitle`、`theme`、`height`、`dataRef`、`roles`、`agg`、`fmt`、`sort`、`topN`、`xtitle`、`ytitle`、`xlim`、`ylim`、`legend`、`labels`、`zoom`、`drill`、`link`。
- `chart.data`：本图不接 DataFrame，所以是一个空 payload：`{"cols": [], "rows": [], "n": 0}`。
- `chart.data_ref`：`None`（没有内嵌数据，不需要引用 id）。
- `chart.warnings`：`{}`（空 dict；手工 spec 类图不做行数采样，也不产生提示）。

**Chart 的通用方法**

- `chart.to_html(inline=True)`：返回完整 HTML 字符串；`inline=True` 会把 ECharts 运行时内联进去，单图约 1.2~1.5MB，可离线打开。
- `chart.save(path, inline=True)`：写出 HTML 文件，自动创建父目录，返回绝对路径。
- `chart.show(open_browser=None)`：在浏览器打开；Jupyter / Streamlit 下自动适配。
- `chart.palette(name)`：切换配色并返回 `self`（可链式），可选 google、antd、tableau、carbon、echarts、morandi、tailwind。
- `chart.title`：只读属性，等于 `spec["title"]`。

**本图 `spec` 的专属键**

- `percentValue`：`float`，已完成量（`percent` 原值转 float）。
- `max` / `maxValue`：`float`，目标量，两个键同值（`max` 给渲染器、`maxValue` 是统一命名）。
- `label`：`str | None`，环内副文字。
- 固定值：`type="ring_progress"`、`dataRef=None`、`roles={}`、`agg="sum"`、`labels=True`、`legend=False`、`zoom=False`、`drill=None`、`link=None`。
- `fmt="raw"`、`height=260` 是 `None` 默认值被替换后的结果，不是调用方写死的。

### 本图 `chart.spec` 的真实结构

下面是 `edv.ring_progress(72.5, label="完成率")` 实际生成的 `spec`（大图对象，字段与上面一一对应）：

```json
{
  "id": "c1",
  "type": "ring_progress",
  "title": "完成率",
  "subtitle": null,
  "theme": "light",
  "height": 260,
  "dataRef": null,
  "roles": {},
  "agg": "sum",
  "fmt": "raw",
  "sort": null,
  "topN": null,
  "xtitle": null,
  "ytitle": null,
  "xlim": null,
  "ylim": null,
  "legend": false,
  "labels": true,
  "zoom": false,
  "drill": null,
  "link": null,
  "percentValue": 72.5,
  "max": 100.0,
  "maxValue": 100.0,
  "label": "完成率"
}
```

**验证返回值的小技巧**

```python
import eazy_data_viz as edv

chart = edv.ring_progress(1280, max=2000, label="销售额")
assert chart.spec["type"] == "ring_progress"
assert chart.spec["percentValue"] == 1280.0
assert chart.spec["max"] == 2000.0
assert chart.data_ref is None
print(chart.title, chart.spec["label"])
```

## 完整示例

以下示例都只依赖 `eazy_data_viz` 本身，可直接复制运行（在仓库根目录执行）。

### 示例 1：最简用法

```python
import eazy_data_viz as edv

chart = edv.ring_progress(72.5)
print(chart.title)
print(chart.spec["percentValue"], chart.spec["max"], chart.spec["fmt"])
assert chart.spec["type"] == "ring_progress"
```

**输出**：
- `进度`（没有传 `label` / `title`，标题兜底为「进度」）。
- `72.5 100.0 raw`：`max` 被转成 float，`fmt` 的 `None` 被替换成 `raw`。

**验证**：`chart.spec["title"] == "进度"`；`chart.spec["height"] == 260`。

### 示例 2：加说明文字与标题

```python
import eazy_data_viz as edv

chart = edv.ring_progress(72.5, label="完成率", title="2024 Q3 销售完成率")
print(chart.title)
print(chart.spec["label"])
assert chart.spec["title"] == "2024 Q3 销售完成率"
assert chart.spec["label"] == "完成率"
```

**输出**：
- `2024 Q3 销售完成率`（`title` 显式传入，不再用 `label` 兜底）。
- `完成率`（环内第二行灰字）。

**验证**：注释掉 `title` 再运行，`chart.title` 会变成 `完成率`。

### 示例 3：目标不是 100：金额达成率

```python
import eazy_data_viz as edv

# 完成 1280 元，目标 2000 元 → 环画 64%
chart = edv.ring_progress(1280, max=2000, label="销售额", fmt="thousands")
pct = chart.spec["percentValue"] / chart.spec["max"] * 100
print(chart.title, round(pct, 1))
assert abs(pct - 64.0) < 1e-9
```

**输出**：
- `销售额 64.0`：标题取 `label`，占比 `1280 / 2000 = 64%`。
- tooltip 的「完成」项按 `thousands` 显示 `1,280`，中心大字仍是 `64%`。

**验证**：`chart.spec["max"] == 2000.0`；把 `max` 改成 100 后占比会变成 1280%。

### 示例 4：fmt 对中心文本与 tooltip 的影响

```python
import eazy_data_viz as edv

raw = edv.ring_progress(72.5)
thousands = edv.ring_progress(72.5, fmt="thousands")
percent = edv.ring_progress(72.5, fmt="percent")

print(raw.spec["fmt"], thousands.spec["fmt"], percent.spec["fmt"])
print(round(raw.spec["percentValue"], 1))
assert raw.spec["fmt"] == "raw"
assert thousands.spec["fmt"] == "thousands"
```

**输出**：
- `raw thousands percent`：`fmt` 原样写进 spec。
- `72.5`：`percentValue` 不随 `fmt` 改变，格式化只发生在渲染阶段。

**验证**：三种写法打印的 `percentValue` 完全相同，只有 HTML 里的展示文本不同。

### 示例 5：尺寸与深色主题

```python
import eazy_data_viz as edv

chart = edv.ring_progress(
    63,
    label="预算消耗",
    height=300,
    theme="dark",
    title="2024 年度预算执行",
)
print(chart.spec["height"], chart.spec["theme"])
assert chart.spec["height"] == 300
assert chart.spec["theme"] == "dark"
```

**输出**：
- `300 dark`：高度与主题都写进了 spec。
- 页面里卡片高度按 300px 分配，环内文字自动换成浅色。

**验证**：`chart.spec["height"] == 300`；把 `theme` 改回默认应得到 `light`。

### 示例 6：从 DataFrame 计算达成率再绘图

```python
import eazy_data_viz as edv

df = edv.sample_df()
done = df["销售额"].sum()
target = 2000000.0
rate = done / target * 100
print(round(done, 2), round(rate, 1))

chart = edv.ring_progress(
    round(rate, 1),
    max=100,
    label="销售目标达成",
    title="2024 销售目标（200 万）",
)
assert chart.spec["percentValue"] == round(rate, 1)
```

**输出**：
- `1631033.57 81.6`：`sample_df` 的销售额合计约 163.1 万，对 200 万目标约 81.6%。
- 环画到 81.6%，中心显示 `81.6%`，`label` 说明这是目标达成率。

**验证**：`chart.spec["percentValue"] == 81.6`；把 `target` 改成 1631033.57 应得到 100%。

### 示例 7：边界值：0、100、超 100

```python
import eazy_data_viz as edv

zero = edv.ring_progress(0, label="零进度")
full = edv.ring_progress(100, label="已完成")
over = edv.ring_progress(150, label="超额")

for name, chart in (("zero", zero), ("full", full), ("over", over)):
    print(name, chart.spec["percentValue"], chart.spec["max"])
assert over.spec["percentValue"] == 150.0
```

**输出**：
- `zero 0.0 100.0` / `full 100.0 100.0` / `over 150.0 100.0`。
- 渲染时占比依次是 0%、100%、100%（超 100 被夹取），但 `spec` 里保留真实值 150，tooltip 仍能看到「完成 150」。

**验证**：`over.spec["percentValue"] == 150.0`；负数同理（`ring_progress(-20)` 在 spec 里保留 -20，渲染为 0%）。

## 常见错误

- **把 DataFrame 当 `percent` 传进来**
  - `edv.ring_progress(df)` 会抛 `TypeError: ring_progress 接受单个数值，例如 ring_progress(72.5, label="完成率")。如果要画 DataFrame，请用 eazy_data_viz.charts_extra.progress(df, x=..., y=...)。`
  - 本图是单值图，不做聚合：先 `df["销售额"].sum()` 或 `df.groupby(...)` 算出结果，再传数值。

- **达成率算成了小数**
  - `ring_progress(0.725)` 配默认 `max=100` 会显示 `0.7%`，不是 72.5%。
  - 传百分数点位（`72.5`），或传「完成量 + 目标量」两个真实数值（`percent=725, max=1000`）。

- **`max` 传了 0 / 负数 / 非数值**
  - `max=0` 与 `max=-1` → `ValueError: ring_progress 的 max 必须大于 0，收到 0`。
  - `max="一百"` → `TypeError: ring_progress 的 max 需要是数值，例如 max=100，收到 '一百'`。
  - `max=None` 不是「用默认值」，会走 `TypeError`；要默认 100 就省略该参数。

- **`fmt` 与 `theme` / `height` 传了非法值**
  - `fmt` 只能是 compact、thousands、raw、percent、currency，否则 `ValueError: fmt='usd' 不支持，可选：compact, thousands, raw, percent, currency`。
  - `theme` 只能是 light / dark；`height` 必须 ≥120（`height=None` 表示用 260）。
  - `NaN` / `inf` 作为 `percent` 会抛 `ValueError: ring_progress 的 percent 必须是有限数值，收到 nan`。

## 相关图表

- `progress`：多个类目的完成度排行（列表 + 进度条），本图的「多值」版本。
- `kpi`：只显示数字与环比，不带圆环；需要更紧凑的指标卡时用它。
- `gauge`：需要指针式仪表盘（带刻度与区间）时用它，强调「落在哪个区间」而不是「完成多少」。
- `tile`：用色块颜色表达类目量级，适合一眼看强弱分布。
- `group_kpi`：一行多张指标卡，适合把「完成率 + 绝对值 + 环比」并排展示。
