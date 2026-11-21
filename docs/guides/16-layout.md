# 16 · 自由排列：让看板按你要的形状拼

默认看板是**等宽网格**：`cols=2` 就是每行两张、每行等高。真实汇报里经常不是这个形状——
“左上放一张大趋势，右边竖排三张小卡片”、“先给 KPI 一条通栏，下面 2×2 四张明细”。
1.5 起 `show()` / `dashboard()` 支持**自由排列**，两种模式：

| 模式 | 参数 | 一句话 |
| --- | --- | --- |
| A. 方向 + 数量 | `direction=` + `layout=[1, 3]` | 每列（或每行）放几张图 |
| B. 网格 + 占位 | `grid=(3, 3)` + `layout=[[2, 2], [1, 1], …]` | 先申请网格，再让每张图占若干格 |

- **适用人群**：已经会用 `dashboard()` / `cols`，想让页面更像“设计过的报表”的人。
- **前置条件**：读完 [02 · 五分钟上手](02-quickstart.md)；知道 `dashboard(*charts, cols=…)`。
- **不需要写 CSS**：排列全部由 Python 参数生成，导出的单文件 HTML 里直接生效。

## 0. 先跑起来

```python
import os

import eazy_data_viz as edv

OUT = os.path.join("examples", "output")
os.makedirs(OUT, exist_ok=True)
df = edv.sample_df()

cards = [
    edv.kpi(df, value="销售额", label="销售额", delta=0.128),
    edv.line(df, x="日期", y="销售额", title="日趋势"),
    edv.bar(df, x="大区", y="销售额", title="大区对比"),
    edv.pie(df, names="产品", values="销售额", title="产品结构"),
]

page = edv.dashboard(*cards, layout=[1, 3], direction="h",
                     title="左边一列，右边三行")
path = os.path.join(OUT, "guide15_flow.html")
page.save(path)
print("已生成", path, os.path.getsize(path), "bytes")
```

预期效果：**左列一张 KPI，右列从上到下三张图**。打开 HTML 源码能直接看到结构：

```html
<div class="eazy-flow">
  <div class="eazy-flow-col" style="height:1172px">…KPI…</div>
  <div class="eazy-flow-col" style="height:1172px">…趋势…</div>
  <div class="eazy-flow-col" style="height:1172px">…柱图…</div>
</div>
```

> 三列带同一个 `height` 是「列等高」的实现方式：列内卡片用 `flex` 按自然高度比例分摊，
> 于是最矮的一列也会被拉到最高列的高度，底边齐平。

## 1. 模式 A：方向 + 每行/列图表数

### 1.1 两个参数怎么分工

- `direction`：**描述方向**，决定“数量列表”是按列还是按行数。
  - `"h"` / `"horizontal"` / `"lr"` / `"从左到右"` → 从左到右排，`layout` 表示**每一列**有几张图。
  - `"v"` / `"vertical"` / `"tb"` / `"从上到下"` → 从上到下排，`layout` 表示**每一行**有几张图。
- `layout`：一串正整数，第 i 个数是第 i 列（或第 i 行）的图表数。

### 1.2 从左到右（`direction="h"`）

```python
# 第一列 1 张，第二列 3 张 —— 共 4 张图
edv.dashboard(c1, c2, c3, c4, layout=[1, 3], direction="h")
```

```text
┌─────┬─────┐
│ c1  │ c2  │
│     ├─────┤
│     │ c3  │
│     ├─────┤
│     │ c4  │
└─────┴─────┘
```

### 1.3 从上到下（`direction="v"`）

```python
# 第一行 1 张，第二行 2 张 —— 共 3 张图
edv.dashboard(a, b, c, layout=[1, 2], direction="v")
```

```text
┌───────────┐
│     a     │
├─────┬─────┤
│  b  │  c  │
└─────┴─────┘
```

### 1.4 数量可以多给，不能用少

`sum(layout)` 必须 **≥ 图数**，多出来的格子留空；少了直接报错：

```python
edv.dashboard(c1, c2, c3, c4, layout=[1, 2], direction="h")
# ValueError: layout=[1, 2] 只提供了 3 个位置，但有 4 张图。
```

```python
edv.dashboard(c1, c2, c3, layout=[2, 2], direction="h")   # 4 个位置、3 张图：最后一格空着
```

`direction` 只写了 `layout` 没写时默认 `"h"`（从左到右）；只写 `direction` 不写 `layout` 会报错：

```text
ValueError: direction 需要配合 layout 一起使用：layout=[每列/行图表数]，例如 layout=[1, 3], direction="h"。
```

### 1.5 模式 A 的高度怎么算（各列底边对齐）

同列内的卡片按各自高度**依次堆叠**，整页高度取最高的一列，并且让所有列都拉到这个高度：

```text
列高 = max(各列卡片高度之和 + 列内间距)
页高 = 列高 + 页内边距
```

多出来的空间会按各卡片的自然高度等比分摊（`flex: 1 1 <自然高度>`），
所以 `layout=[1, 3]` 时左列那张 KPI 会被拉高到和右侧三张图的总高一样，**两列底边齐平**，
不会出现「左边短、右边长」的缺口。

## 2. 模式 B：先申请网格，再按顺序占位

### 2.1 两个参数怎么分工

- `grid`：先声明网格行列，例如 `(3, 3)`（也接受 `[3, 3]`、`"3x3"`、`3`）。
- `layout`：**每张图一个 `[行, 列]`**（行数, 列数），第 i 个描述第 i 张图要占的格子。

占位顺序固定为「**从左到右、从上到下** 找第一个放得下的空位」，所以不用手工写坐标。

### 2.2 用户最关心的例子

```python
# 3×3 网格；先占 2×2，再占 1×1
edv.dashboard(big, small, grid=(3, 3), layout=[[2, 2], [1, 1]])
```

```text
┌─────┬─────┬─────┐
│     │     │ small│
│ big │ big ├─────┤
│     │     │ 空   │
├─────┴─────┴─────┤
│        空        │
└──────────────────┘
```

`[1,1]` 会自动落在 2×2 的**右上角**（第 1 行第 3 列），因为它是扫描时第一个能放下的位置。

### 2.3 一个更像报表的例子

```python
page = edv.dashboard(
    edv.line(df, x="日期", y="销售额", title="趋势（通栏）"),
    edv.bar(df, x="大区", y="销售额", title="大区"),
    edv.pie(df, names="产品", values="销售额", title="产品"),
    edv.table(df, groupby={"columns": ["大区"], "value": "销售额"}, title="汇总"),
    grid=(3, 2),
    layout=[[1, 2], [1, 1], [1, 1], [1, 2]],
    title="销售看板（自由排列）",
)
page.save("examples/output/guide15_span.html")
```

```text
┌───────────┬───────────┐
│      趋势（1×2）       │
├───────────┼───────────┤
│   大区    │   产品    │
├───────────┴───────────┤
│      汇总表（1×2）     │
└───────────────────────┘
```

### 2.4 模式 B 的三条硬规则

1. **占位声明数量必须等于图数**（模式 A 可以多给，模式 B 不行）：

   ```python
   edv.dashboard(a, b, c, d, grid=(2, 2), layout=[[2, 2]])
   # ValueError: 网格排列需要为每张图声明 [行, 列] 占用：共 4 张图，收到 1 个占位声明。
   ```

2. **单张图不能超过网格**：

   ```python
   edv.dashboard(a, grid=(2, 2), layout=[[3, 1]])
   # ValueError: 第 1 张图申请 3×1 的空间，超过网格 2×2。
   ```

3. **放不下就报错**（不会静默挪位或裁切）：

   ```python
   edv.dashboard(a, b, c, grid=(2, 2), layout=[[2, 2], [2, 1], [1, 1]])
   # ValueError: 第 2 张图申请 2×1 的空间放不下：2×2 网格已经占用了 4 格，剩下的空位放不下这个尺寸。
   ```

### 2.5 模式 B 的高度怎么算（拼成严丝合缝的矩形）

先按每张卡片的自然高度算出**每一行该有多高**，再让每张卡正好吃满它占的那几格：

```text
1) 单行卡片：把它的自然高度写进所在行；
2) 跨行卡片：如果「自然高度 > 已占行高之和 + 跨行间距」，把差额加到它跨的最后一行；
3) 重复第 2 步直到稳定（行高只增不减）；
4) 每张卡的高度 = 它跨的各行高度之和 + 行间距 × (跨行数 - 1)。
```

结果就是整块网格是**一个完整的矩形**：`grid=(3, 3)` + `layout=[[2,2],[1,1],[1,1],[1,1]]` 时，
左边 2×2 的大图底边、右边两张 1×1 的底边都落在同一水平线上。
相同逻辑也用于 `page_height()`（Streamlit 的 iframe 高度），所以不会有内容被裁。

自查：

```python
from eazy_data_viz import layout

plan = layout.parse_layout(4, layout=[[2, 2], [1, 2], [1, 1], [2, 1]], grid=(3, 3))
rows, boxes = layout.grid_row_heights(plan, [420, 380, 360, 340])
print([int(r) for r in rows])    # [360, 44, 380] —— 第二行被上面的 2×2 撑起来
print([int(b) for b in boxes])   # [420, 380, 360, 440] —— 每张卡正好吃满自己占的格子
```

## 3. 四种入口都支持

| 入口 | 用法 |
| --- | --- |
| 看板 | `edv.dashboard(*charts, layout=…, direction=…, grid=…)` |
| 快捷函数 | `edv.show(*charts, layout=…, direction=…, grid=…)` |
| 单图 | `edv.show(c, layout=[1])` 会走看板渲染，1 张图看不出排列差异，等价于单图直接展示 |
| Streamlit | `edv.streamlit_dashboard(charts, layout=…, direction=…, grid=…)`（v2 与 v1 回退都支持） |

`Dashboard.to_html()` 分页高度也按自由排列计算（`render.page_height(..., layout=…)`），
所以 Streamlit 里不会出现“内容被裁掉一半”的情况。

## 4. 和 `section` 的关系

`section` 是“整行分区标题”，自由排列下没有行/列的统一语义，因此**两者不能同时用**：

```python
c = edv.bar(df, x="大区", y="销售额", section="一、销售")
edv.dashboard(c, layout=[1], direction="h")
# ValueError: 自定义排列（layout / direction / grid）暂不支持 section 分节：
# 第 1 张图设置了 section='一'。请改用 title / subtitle 区分，或去掉自由排列参数。
```

要用自由排列就改用 `title` / `subtitle` 标注分组；要分区标题就回到 `cols` 等宽网格。

## 5. 怎么自查排出来的结果（不用打开浏览器）

排列是纯 Python 计算，可以直接检查每张图落在哪一格：

```python
from eazy_data_viz import layout

plan = layout.parse_layout(4, layout=[1, 3], direction="h")
print(plan["mode"], plan["cols"], plan["rows"], plan["cells"])
print(layout.layout_summary(plan))
```

```text
flow 2 3 [(0, 0, 1, 1), (0, 1, 1, 1), (1, 1, 1, 1), (2, 1, 1, 1)]
从左到右：第1列 1 张、第2列 3 张
```

```python
plan = layout.parse_layout(2, layout=[[2, 2], [1, 1]], grid=(3, 3))
print(plan["cells"])
print(layout.layout_summary(plan))
```

```text
[(0, 0, 2, 2), (0, 2, 1, 1)]
网格 3×3：#1 (1,1) 2×2；#2 (1,3) 1×1
```

`cells` 里每一格是 `(行, 列, 跨行, 跨列)`，行列都从 0 开始；对照上表就能确认“谁是右上角”。

## 6. 让框与框对齐：`abs_height`

自由排列只决定**谁在哪一格**，格子里的卡片高度仍由各图自己决定：

- 默认 `height` 只算图表正文，卡片会再加上标题（约 46px）、联动工具条（约 30px）等，
  于是「带长标题的图」和「带工具条的图」框高不同，同一行并排时底边就歪了。
- 想让同一行的框严格等高，给每张图加 `abs_height=True`：
  这时 `height` 表示**整个组件外框**（内边距、标题、副标题、工具条都算在里面），正文用 flex 自适应剩余空间。

```python
cards = [
    edv.bar(df, x="月份", y="销售额", title="月度销售额",
            height=320, abs_height=True),
    edv.line(df, x="月份", y="销售额", title="月度销售额（折线）", subtitle="单位：万元",
             height=320, abs_height=True),
    edv.pie(df, names="大区", values="销售额", skip_zero=True,
            height=320, abs_height=True),
]
edv.dashboard(*cards, direction="h", layout=[1, 2])
```

三张卡的标题长度、有无副标题都不一样，但框高都是 320px、底边齐平。

两种「对齐」的分工：

| 想要的效果 | 用哪个 |
| --- | --- |
| 整块网格/各列拼成严丝合缝的矩形 | 自由排列自带（模式 A 列等高、模式 B 行高铺满），不用额外参数 |
| 同一格里、或普通 `cols` 网格里，卡片框严格等高 | `abs_height=True`（外框高度），建议同一行传同一个 `height` |

优先级：**模式 B（`grid`）里格子高度优先**——整块要先拼成矩形，所以卡片会被拉伸到格子大小；
**模式 A（`direction`）与普通 `cols` 网格里 `abs_height` 优先**——给了固定框高的卡片不会再被拉伸，
其余卡片照常拉伸填满所在列/行。

> `abs_height` 也适用于普通 `cols` 等宽看板：`edv.dashboard(a, b, c, cols=3)` 里给三张图都设
> `height=320, abs_height=True`，同样能消掉标题/工具条带来的高度差。

## 7. 常见问题

**Q1. 为什么我的页面右边突然空了？**
模式 A 里 `sum(layout)` 大于图数时，多出来的格子会留空。把 `layout` 的数量改成和图的分布一致即可。

**Q2. 能不能一张图跨两列、另一张正常排？**
用模式 B（`grid` + `[[1, 2], [1, 1]]`），模式 A 只能整列/整行计数。

**Q3. 手机窄屏会不会挤坏？**
`eazy-flow` 与网格都按比例分配宽度，窄屏会等比例缩小、不会溢出；卡片内部图表自身会自适应宽度。

**Q4. `cols` 还需要传吗？**
不需要，自由排列模式下 `cols` 会被覆盖（`build_page` 用 `plan["cols"]`）。留着也不影响。

**Q5. 为什么报错信息里说“第 N 张图”？**
N 是**传参顺序**（从 1 开始），不是布局里的格子序号。

**Q6. 能只排某几张图、其余自动流式吗？**
不能。一个看板只能选一种模式：要么全 `cols` 等宽，要么全自由排列。

## 下一篇

- 想理解联动的方向（双向/单向进/单向出）：[06 · 交互总览](06-interaction.md)
- 想先搭一个完整驾驶舱：[03 · 从零搭一个经营驾驶舱](03-cockpit-tutorial.md)
- 想调色与主题：[05 · 配色与主题](05-palette-and-theme.md)
