# 06 · 交互总览：下钻、联动、缩放与导出

本篇把 eazy_data_viz 的所有浏览器端交互一次讲清：哪些交互是**声明式**的（Python 传参即开启）、
点击后到底发生了什么、状态存在哪里、以及最常见的“为什么没生效”。

- **适用人群**：已经能用 `dashboard()` 出静态页面，想让看板“能点”的工程师/分析师。
- **前置条件**：读完 [02 · 五分钟上手](02-quickstart.md)，本地能打开生成的 HTML。
- **本篇不需要 Python 回调**：所有交互都在浏览器里完成，Python 只负责生成一次 HTML。

## 0. 先跑起来：一个可点的页面

把下面代码存成 `interaction_demo.py`，放在仓库根目录运行。
会生成 `examples/output/guide06_full.html`（约 1.46 MB，内含 ECharts，可离线打开）。

```python
import os

import eazy_data_viz as edv

OUT = os.path.join("examples", "output")
os.makedirs(OUT, exist_ok=True)
df = edv.sample_df()

# 表格是 HTML 组件，没有 section 形参；需要分区时直接写 spec（见 03 篇）
table = edv.table(df, columns=["日期", "大区", "销售额"], limit=20, link="G")
table.spec["section"] = "三、表格"

cards = [
    edv.kpi(df, value="销售额", link="G", section="一、指标"),
    edv.kpi(df, value="订单数", link="G", section="一、指标"),
    # 下钻三级 + 联动：点击柱形先下钻，同时把“当前维度=值”同步给同组图表
    edv.bar(df, x="大区", y="销售额", drill=["大区", "省份", "城市"],
            link="G", section="二、明细"),
    edv.pie(df, names="产品", values="销售额", link="G"),
    table,
]

page = edv.dashboard(cards, cols=2, title="交互演示", desc="下钻 / 联动 / 主题 / 导出 PNG")
path = os.path.join(OUT, "guide06_full.html")
page.save(path)
print("已生成", path, os.path.getsize(path), "bytes")
```

预期输出（字节数会随后续版本微调，量级一致）：

```text
已生成 examples\output\guide06_full.html 1463150 bytes
```

用浏览器打开后按下面清单逐项验证：

| 操作 | 预期现象 |
| --- | --- |
| 点柱状图的某根柱子 | 柱图换成该大区下各省份；上方出现“全部 › 华东”面包屑；其它同组图被筛到该大区 |
| 再点某根省份柱 | 面包屑变成“全部 › 华东 › 江苏省”；联动筛选 chip 变成 `省份 = 江苏省` |
| 点饼图某块 | 同组图按当前饼图类目（产品）过滤；饼图自身保持全量并高亮该块 |
| 再点同一块饼 | 取消联动（同图、同维度、同值再点 = 取消） |
| 点“重置联动” | 所有联动 chip 清空，各图回到全量；**下钻层级不会回退** |
| 点“重置下钻” | 所有图的下钻层级清空、回到第一层；下钻那次点击顺带产生的联动也一起清掉 |
| 点 ◐ | 深色/浅色切换，筛选与下钻状态保留 |
| 右上角“保存图片”图标 | 下载当前图为 PNG（2 倍像素） |

> **重要**：`重置联动`、`重置下钻`、配色下拉、◐ 主题按钮都长在**顶栏**里。
> 1.3.0 起，只要页面里**有联动（`link`）或有下钻（`drill`）**，即使不传标题也会渲染顶栏
> （没有标题时是紧凑工具条：只有按钮、没有标题行）。既没有联动也没有下钻的页面不需要回退入口，
> 顶栏就不渲染了。

```python
# 验证“有没有顶栏按钮”：两个页面对比
h1 = edv.dashboard(edv.bar(df, x="大区", y="销售额", link="G"),
                   edv.pie(df, names="产品", values="销售额", link="G")).to_html()
h2 = edv.dashboard(edv.bar(df, x="大区", y="销售额", link="G"),
                   edv.pie(df, names="产品", values="销售额", link="G"),
                   title="有顶栏").to_html()
print("无标题含重置按钮:", "data-eazy-reset title=" in h1)   # True（有 link 就会渲染）
print("有标题含重置按钮:", "data-eazy-reset title=" in h2)   # True
print("两者都有 chips 容器:", 'id="eazy-filters"' in h1, 'id="eazy-filters"' in h2)
```

```text
无标题含重置按钮: True
有标题含重置按钮: True
两者都有 chips 容器: True True
```

> 既没有 `link` 也没有 `drill`、又没给标题的看板，顶栏不会渲染（没有需要回退的状态）。

## 1. 下钻（drill）：点击图形逐级换维度

下钻 = 点击 A 维度上的某个值后，同一张图**换成以 B 维度为横轴**、且只保留该值范围内的数据。
它只需要一个参数：`drill=["大区", "省份", "城市"]`（顺序就是从粗到细）。

```python
chart = edv.bar(df, x="大区", y="销售额", drill=["大区", "省份", "城市"])
print("drill 声明:", chart.spec["drill"])
print("当前横轴  :", chart.spec["roles"]["x"])
```

```text
drill 声明: ['大区', '省份', '城市']
当前横轴  : 大区
```

### 1.1 运行时到底发生了什么

浏览器端相关源码在 `eazy_data_viz/assets/eazy.js` 的 `onChartClick`（约 1475 行）：

1. 只处理 `componentType === "series"` 的点击，也就是**图形本体**；点坐标轴、卡片空白处不会触发。
2. 用 `currentXDim(spec, state)` 算“当前横轴维度”：
   有 `drill` 时取 `drill[min(当前层数, len(drill)-1)]`，否则取 `roles.x`。
3. 如果 `drill` 还有下一级、且**下一级维度正好等于当前横轴**，就
   `state.drill.push({dim, value})`，然后重绘。
4. 达到最后一层后不再下钻（`state.drill.length < len(drill)-1` 不成立）。

由此得到几条**硬规则**：

| 规则 | 说明 |
| --- | --- |
| `x` 必须是 `drill` 当前层维度 | 初始 `x` 要等于 `drill[0]`，否则点击值对不上维度，只会联动、不会下钻 |
| 维度列必须存在于 DataFrame | 列名写错会在 Python 侧就报 `KeyError`（见 12 篇） |
| 层数上限 = `len(drill)` | 最后一层点击不再变化；想回到上层用面包屑或“↰ 返回” |
| `top_n` 合并出的“其他”不可点 | 前端显式忽略 `value === "其他"`，避免把合并项当成真实类目 |
| 饼图/漏斗不支持下钻 | 它们的“横轴”是 `names` 类目，不是 `drill` 当前层；点击只会联动 |
| 每张图的状态独立 | 两张柱图都声明了 `drill`，各点各的，互不影响 |

`x` 与 `drill[0]` 不一致时的真实现象（不会报错，但只联动不下钻）：

```python
c = edv.bar(df, x="省份", y="销售额", drill=["大区", "省份"], link="G")
# 点“江苏省”时：当前横轴是“省份”，而下一级要的是“大区”，条件不成立 → 只 setLink
print(c.spec["drill"], c.spec["roles"]["x"])
```

### 1.2 面包屑与返回

声明了 `drill` 的卡片，标题下方会自动出现工具栏：

- 初始只显示一个 `全部` 按钮和提示“点击图形逐级下钻”；
- 进入下钻后变成 `全部 › 华东 › 江苏省`，每一段都可点，点第 N 段 = 截断到第 N 层；
- 已在下钻层内时额外出现 `↰ 返回`，等于弹出最后一层。

```python
one = edv.bar(df, x="大区", y="销售额", drill=["大区", "省份"])
html = edv.dashboard(one, cols=1, title="下钻演示").to_html()
# 工具栏是浏览器端用 JS 拼出来的，HTML 里只有容器，没有“全部/返回”按钮文本
print("有 drill 工具栏容器:", 'data-eazy-toolbar="0"' in html)   # True
```

> **常见误会**：导出的 HTML 里搜不到“全部/返回”字样是正常的——面包屑由 `eazy.js`
> 在运行时渲染；同理，导出的 HTML 永远只包含**初始状态**。

### 1.3 drill 和 link 一起用的顺序

同一张图同时有 `drill` 和 `link` 时，一次点击做两件事：

1. 满足条件就先 `push` 下钻状态；
2. 只要有 `link`，就 `setLink(组, 当前维度, 值)`，然后**整组重绘**（包括自己）。

所以效果是：“柱图切到省级视图，同时把其它图筛到该大区”。
注意联动记录的是**点击当时的维度**：在省级视图里点“江苏省”，chip 从 `大区 = 华东`
变成 `省份 = 江苏省`，下游图表会按省份过滤（前提是它们的数据里有 `省份` 列）。

## 2. 联动（link）：同组图表互相筛选

联动 = 给若干张图同一个组名 `link="G"`。点其中任意一张图的图形，同组其它图按
**当前维度 = 被点类目**过滤；再次点同一张图的同一个类目则取消。

```python
c_bar = edv.bar(df, x="产品", y="销售额", link="S1")
c_line = edv.line(df, x="日期", y="销售额", link="S1")
c_pie = edv.pie(df, names="渠道", values="销售额", link="S1")
page = edv.dashboard(c_bar, c_line, c_pie, cols=2, title="纯联动", desc="点任意图形试试")
print([c.spec["link"] for c in (c_bar, c_line, c_pie)])
```

```text
['S1', 'S1', 'S1']
```

### 2.1 联动语义表

| 行为 | 结果 |
| --- | --- |
| 点某图（source）的类目 | `EazyViz.links[组] = {dim, value, sourceId}`，整组 `reRenderGroup` |
| source 自己 | **不过滤**，保持全量并高亮选中项（避免一点就把自己缩成一根柱子） |
| 同组其它图 | 仅当数据里有 `dim` 这一列时过滤（`hasCol(c.data, dim)`），否则原样显示 |
| 再点同图同类目 | 删除该组联动 = 取消 |
| 点同组另一张图的类目 | 替换联动内容（不是叠加） |
| 不同组名 | 互不影响；`重置联动` 会清空所有组 |
| 点图例 | 不是联动，只做本图的系列显隐（见第 3 节） |

“目标图没变”的第一嫌疑永远是：**它的数据里没有这个维度列**。
比如用 `edv.table(df, columns=["日期","销售额"])` 只会嵌入这两列，
点“大区”柱形时它就没有 `大区` 可过滤。

```python
# 反例：table 只保留两列，点击大区时它不会过滤
t = edv.table(df, columns=["日期", "销售额"], limit=10, link="G")
print("table 嵌入的列:", t.spec["roles"])
```

```text
table 嵌入的列: {'columns': ['日期', '销售额']}
```

### 2.2 筛选 chips 与重置

只要页面里**存在任一 `link`**，HTML 就会输出一个筛选栏容器：

```html
<div class="eazy-filters" id="eazy-filters" style="display:none">…</div>
```

有联动时它变为可见，内容形如：

```text
联动筛选  大区 = 华东 ×    产品 = 平板 ×
```

- 每个 chip 的 `×` 只清掉该组；
- 顶栏的 `重置联动`（`data-eazy-reset`）清空所有组；
- 顶栏的 `重置下钻`（`data-eazy-reset-drill`）把所有图的下钻层级清空，并顺手清掉这些图自己发出的联动；
- 清联动**不会**回退任何图的下钻层级；
- 反过来，面包屑/返回也只动下钻，不会清联动——两套状态完全独立。

### 2.3 谁能发起联动，谁只能接收

这是最容易踩的一条：

| 图型 | 发起联动 | 接收联动过滤 |
| --- | --- | --- |
| ECharts 系列（bar/line/pie/scatter/treemap/…） | ✅ 点图形 | ✅ |
| 明细表 `table`（1.4.0 起） | ✅ 点单元格 | ✅ 只留命中的行 |
| HTML 组件（kpi/progress/tile/wordcloud/group_kpi） | ❌ 点击无反应 | ✅（KPI 会按筛选后数据重算） |
| 图例区域 | ❌（只显隐系列） | — |

验证方式：`kpi(link="G")` 作为接收方时，值会从全量合计变成“某大区合计”；
但点击 KPI 卡片本身不会触发任何联动（`eazy_extra_html.js` 里没有 click 绑定）。

```python
# KPI 作为接收方：页面里放一个可点的柱图 + 两个 KPI
p = edv.dashboard(
    edv.bar(df, x="产品", y="销售额", link="G"),
    edv.kpi(df, value="销售额", label="销售额合计", link="G"),
    edv.kpi(df, value="订单数", label="订单数合计", link="G"),
    cols=2, title="KPI 联动重算",
)
print("KPI 是否记录了 link:", [c.spec.get("link") for c in p.charts])
```

```text
KPI 是否记录了 link: ['G', 'G', 'G']
```

`dashboard.charts` 顺序与传参一致：柱图在第一个，两张 KPI 在后，三者都记录了 `link="G"`。
浏览器里点“平板”柱形，两张 KPI 的数字会立即变成平板品类的合计。

### 2.4 表格也能当联动源（1.4.0 起）

给 `table(link="G")` 之后，表里的**维度列**（文本/日期列，数值列不算）会变成可点单元格：
鼠标移上去是手型，点一下就把「列 = 该格的值」写进联动组，同组图表立刻被筛。

```python
tbl = edv.table(df, columns=["大区", "产品", "销售额"], limit=20,
                index=True, total=True, bar="销售额", link="G")
page = edv.dashboard(
    edv.bar(df, x="大区", y="销售额", link="G"),
    edv.line(df, x="月份", y="销售额", link="G"),
    tbl, cols=2, title="表格 ↔ 图表 双向联动",
)
print("表格 link:", tbl.spec.get("link"))
```

```text
表格 link: G
```

点表格里某个「大区」单元格之后：

- 同组的柱图/折线按 `大区 = 华东` 过滤；
- 表格**自己不过滤**，而是把命中的行高亮（左侧主色竖条 + 浅色蒙层），
  方便你接着看「这几行是怎么构成的」；
- 顶栏筛选条出现 `大区 = 华东 ×`，再点同一格或点 `×` 即取消；
- 反过来点柱图，表格就只留该大区的行，底部提示会变成 `共 80 行，仅显示前 20 行`。

要点：

- 只有 `link` 已设置、且列是维度列时单元格才可点；数值列（含数据条列）不可点。
- 点单元格同样会触发 `on_select`（`type` 为 `"table"`、带 `dim` / `value`），
  Streamlit 里想把它回传 Python 才需要传 `on_select`。
- 表格行的过滤发生在浏览器端，不会因为点单元格就 rerun 整个脚本。

### 2.5 联动方向：双向 / 单向进 / 单向出（1.5 起）

只给组名时是**双向**：既能发起也能接收。1.5 起可以再指定方向：

```python
edv.bar(df, x="大区", y="销售额", link="G")                # 双向（默认）
edv.bar(df, x="大区", y="销售额", link=("G", "out"))       # 单向出：只发起
edv.table(df, columns=["大区", "销售额"], link=("G", "in"))  # 单向进：只接收
edv.pie(df, names="产品", values="销售额",
        link={"group": "G", "direction": "out"})           # 字典写法
```

| 方向 | 写法 | 点它会不会改别的图 | 别的图点它会不会被过滤 | 典型用途 |
| --- | --- | --- | --- | --- |
| 双向 | `link="G"` / `("G", "both")` | ✅ | ✅ | 平级图表互筛 |
| 单向出 | `("G", "out")` / `"发起"` / `"出"` | ✅ | ❌ **自己永不过滤** | 总览图、筛选器：始终显示全量，只把选中值广播出去 |
| 单向进 | `("G", "in")` / `"接收"` / `"进"` | ❌ **点了不发起** | ✅ | 明细表、详情图：只跟着变，点它不会污染全局选中态 |

语义细节（前端实现，`spec.linkMode`）：

- 发起前先看 `canSendLink()`：方向是 `in` 的图**不发起**，点它只会做下钻（如果有 `drill`）。
- 接收前先看 `canRecvLink()`：方向是 `out` 的图**不接收**，`EazyViz.links` 里有值也不会过滤它自身。
- 高亮（`sourceSelection`）只给“发起方且没有过滤自己”的图，所以单向出的图点完仍显示全量并高亮选中项。
- 工具栏会按方向给出不同提示：`单向出：点击图形联动到同组其他图表` / `单向进：本图只接收联动，点其他图会过滤本图` / `点击图形可联动同组图表（双向）`。
- 方向不影响筛选 chips 与 `重置联动`：任何一张图点的选中值都能被一键清掉。

验证方式（不需要浏览器）：

```python
a = edv.bar(df, x="大区", y="销售额", link=("G", "out"))
b = edv.bar(df, x="大区", y="销售额", link=("G", "both"))
c = edv.table(df, columns=["大区", "销售额"], link=("G", "in"))
print([(x.spec["link"], x.spec["linkMode"]) for x in (a, b, c)])
```

```text
[('G', 'out'), ('G', 'both'), ('G', 'in')]
```

> 组名相同才会联动，方向不同没关系：`out` / `both` / `in` 三张图可以同组共存，
> 这正是“总览图 → 明细表”的推荐组合。

## 3. 图例点选：只影响自己

有 `color` 维度或多系列时，图例默认出现（`legend=True`）。点图例项：

- ECharts 隐藏/显示对应系列，**不产生筛选、不影响同组其它图**；
- 选择状态记录在 `c.state.legendSel`，联动重绘、主题切换后仍保留；
- 没有 Python 侧 API 指定“默认隐藏哪个系列”，要默认隐藏请在数据准备阶段过滤。

```python
c = edv.bar(df, x="大区", y="销售额", color="渠道")
print("legend:", c.spec["legend"], "| color 维度:", c.spec["roles"]["color"])
```

```text
legend: True | color 维度: 渠道
```

## 4. 缩放：类目多了自动出现

`zoom` 只有三个合法值：`"auto"`（默认）、`True`、`False`。规则（`eazy.js` 约 622 行）：

```js
needZoom = (spec.zoom === true) || (spec.zoom !== false && cats.length > 15)
```

含义：

| 取值 | 行为 |
| --- | --- |
| `"auto"` | 类目数 > 15 时自动加 `inside`（滚轮/拖拽）+ 底部 `slider` 数据缩放条 |
| `True` | 无论多少类目都强制出现 |
| `False` | 强制关闭（适合类目少、想省高度的图） |

```python
print("默认:", edv.bar(df, x="日期", y="销售额").spec["zoom"])          # auto
print("强制:", edv.line(df, x="日期", y="销售额", zoom=True).spec["zoom"])  # True
print("关闭:", edv.bar(df, x="日期", y="销售额", zoom=False).spec["zoom"])  # False
```

```text
默认: auto
强制: True
关闭: False
```

**当前实现里缩放只对柱/线/面积这类直角坐标系图生效**；其它图型虽然签名上也接受
`zoom`，但浏览器端不会渲染缩放条（不要指望用 `zoom` 给饼图/地图加缩放）。

抽样观察：`sample_df()` 的“日期”有 150 个类目，`x="日期"` 的柱图必然自动带缩放条；
而 `x="大区"` 只有 4 个类目，不会出现。

## 5. tooltip：悬停看明细

- 直角坐标系图（bar/line/area/combo/scatter…）用**轴触发** tooltip：悬停某个 x 位置，
  显示该位置所有系列的数值，按 `fmt` 格式化（`compact`/`thousands`/`currency`…）。
- 饼图/漏斗/树图等用**项触发**：悬停单个扇区/节点显示名称、数值、占比。
- `percent=True` 的图（`bar_pct`/`area_pct`/`percent=True`）tooltip 和坐标轴都带 `%`。
- 目前没有 Python 参数自定义 tooltip 内容；需要自定义格式请走第 14 篇的扩展方式。

```python
c = edv.bar(df, x="大区", y="销售额", fmt="currency")
print("fmt:", c.spec["fmt"])
```

```text
fmt: currency
```

## 6. 导出 PNG

每张 ECharts 图右上角有工具箱，内含“保存图片”按钮（源码 `makeToolbox`，约 386 行）：

```js
saveAsImage: { title: "保存图片", pixelRatio: 2, name: "eazy-chart" }
```

- 下载文件名固定为 `eazy-chart.png`（多张图连续保存会得到 `eazy-chart (1).png` 等）；
- 2 倍像素，适合放进 PPT/报表；
- **HTML 组件（KPI/表格/进度/词云/tile）没有工具箱**，截不了 PNG；整页截图请用浏览器插件；
- 想要“一键导出整页”，更稳的做法是 `page.save("xx.html")` 交付 HTML 本身（见 08 篇）。

## 7. 主题与配色切换：运行时也能换

顶栏（有标题时才存在）右侧有三个控件：

| 控件 | 作用 |
| --- | --- |
| 配色下拉（`data-eazy-palette`） | 在 7 套内置配色间切换，纯前端重绘 |
| ◐（`data-eazy-theme`） | 浅色/深色切换，`data-theme` 挂到 `<html>`/`<body>` |
| 重置联动（`data-eazy-reset`） | 清空所有联动组 |
| 重置下钻（`data-eazy-reset-drill`） | 所有图 `state.drill = []`，并清掉 `sourceId` 是这些图的联动组 |

切换主题会重算颜色并重绘所有图，但**保留** filters 和 drill 状态。
初始主题/配色在 Python 侧决定：`dashboard(..., theme="dark", palette="carbon")`；
单图 `.palette()` 的优先级高于整页（细节见 05 篇）。

## 8. 为什么跨 iframe 联动不生效

很多人会在 Streamlit 里放两个 `st.components.v1.html`，然后抱怨“A 点一下 B 不动”。
这不是 bug，而是浏览器安全模型的必然结果：

1. 每个 iframe 有**独立的 `window`**，各自加载一份 `eazy.js`；
2. 联动状态保存在 `EazyViz.links`（该 window 内的普通对象），互相看不见；
3. eazy.js 没有注册任何 `postMessage` 监听，父页面也没有桥接；
4. 就算有桥接，两边数据/图表实例也不同，需要双方协议同步。

所以能力边界是：

| 场景 | 联动是否生效 |
| --- | --- |
| 一个 `dashboard()` → 一个 HTML → 一个 iframe（或多图同页） | ✅ 完整生效 |
| 多个 `components.html()` / 多个 iframe | ❌ 默认不生效 |

可行的替代方案（按推荐度排序）：

1. **合并成一个页面**：把想联动的图放进同一个 `Dashboard`，一次 `components.html` 输出
   （07 篇给完整写法）。这是唯一“零成本真联动”的路径。
2. **Streamlit 侧联动**：把筛选做成 sidebar 控件，用 `st.session_state` + `st.rerun()`
   重建整页。这是“服务端联动”，会触发重算和重绘，不是客户端即时联动。
3. **自写 postMessage 桥**：在 HTML 里注入一段 JS，把 `EazyViz.links` 变化发到父页面，
   父页面再分发给其它 iframe。属于定制开发，需要同时改两边页面。
4. **接受独立**：每个组件只服务自己的分析目标，不做跨组件联动。

## 9. 交互状态存在哪里（以及“分享链接”的真相）

- 下钻层级：各图 `c.state.drill = [{dim, value}, …]`
- 联动：`EazyViz.links = { 组名: {dim, value, sourceId} }`
- 图例显隐：各图 `c.state.legendSel`
- 只存在**当前浏览器内存**里：刷新页面全部重置；不写 localStorage、不进 URL；
- 因此 `save()` 出来的 HTML 永远展示初始状态，适合作为“可交互的静态报表”，
  但无法把“我钻到江苏省”这个状态分享给别人；
- 需要固定某个筛选结果给别人看，正确做法是**在 Python 里先过滤数据再出图**：

```python
hz = df[df["大区"] == "华东"]
page = edv.dashboard(edv.bar(hz, x="省份", y="销售额"), cols=1,
                     title="华东 · 省份销售额（固定筛选版）")
print("行数:", len(hz))
```

```text
行数: 450
```

## 10. 常见问题

**Q1：点了柱子没有任何反应？**
先看该图有没有 `drill` 或 `link`；再确认点的是**图形本体**而不是图例/坐标轴；
最后确认 `x` 与 `drill` 当前层一致（第 1.1 节）。

**Q2：联动只高亮、别的图不动？**
目标图数据里没有该维度列（table 限定了 columns、或预聚合数据只有汇总列）。
让目标图的数据包含该列，或改 list 联动维度。

**Q3：点击后 chip 出现了，但目标图数值没变？**
目标图是**数据里没有这个类目值**（例如筛选值不在该图数据范围内）——
`filteredRows` 过滤后为空，图会显示空状态；检查是否用了不同的数据子集。

**Q4：为什么重置按钮找不到？**
`dashboard()` 没有 `title`/`desc`。加标题即出现（第 0 节）。

**Q5：能不能点 KPI 卡片触发联动？**
不能。KPI/table 等 HTML 组件只能作为接收方；发起方必须是 ECharts 图形。

**Q6：下钻后导出的 HTML 会保留当前层级吗？**
不会。导出发生在 Python 侧，浏览器状态不参与。

## 下一篇

交互都通了，接下来把它塞进 Streamlit，并解决高度、缓存和 iframe 隔离：
[07 · Streamlit 集成](07-streamlit.md)。
