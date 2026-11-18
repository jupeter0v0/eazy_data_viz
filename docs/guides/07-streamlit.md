# 07 · Streamlit 集成：把看板变成数据应用

eazy_data_viz 和 Streamlit 是“天生一对”：库负责把 DataFrame 变成**单文件可交互 HTML**，
Streamlit 负责控件、布局和状态。这一篇讲清集成方式、高度计算、缓存、页面组织，以及
所有会让人卡半天的坑。

- **适用人群**：已经会写基础 Streamlit 脚本，想把图表库接进内部数据应用。
- **前置条件**：读过 [02 · 五分钟上手](02-quickstart.md) 与 [06 · 交互](06-interaction.md)；
  环境里装了 Streamlit（`pip install ".[streamlit]"` 或 `pip install streamlit>=1.10`）。
- **本篇验证环境**：Python 3.8.10 + pandas 2.0.3 + Streamlit 1.27.1（v1 路径）；
  Python 3.14.10 + pandas 3.1.1 + Streamlit 1.67.0（v2 路径）。

> **新版优先：`st.components.v2`（Streamlit ≥ 1.50）**
>
> `st.components.v1.html` 已被官方标记为 2026-06-01 后移除。eazy_data_viz 1.1.0 起，
> `.show()` / `edv.dashboard(...).show()` 在 Streamlit 里会**自动优先走 v2**：没有 iframe、
> 高度按内容自适应，点击图表还能回传 Python。想手动控制时用一行 API：
>
> ```python
> import streamlit as st
> import eazy_data_viz as edv
>
> df = edv.sample_df()
> charts = [edv.kpi(df, value="销售额", label="销售额"),
>           edv.bar(df, x="大区", y="销售额", link="g1"),
>           edv.line(df, x="月份", y="销售额", link="g1")]
>
> result = edv.streamlit_dashboard(charts, cols=2, title="经营驾驶舱")  # 默认零 rerun
> # 需要 Python 感知点击时才传回调：on_select=...
> if result.select:                 # 传了 on_select 才有值
>     st.write(result.select)       # {chart, title, type, dim, value, drill, link}
> ```
>
> 兼容性：`edv.streamlit_available()` 返回当前环境是否支持 v2；
> 不支持时 `streamlit_dashboard` 会抛错，而 `.show()` 会自动回退到下面的 v1 写法。
> 下文 `## 1`~`## 9` 讲的仍是 v1 的 iframe 方式——在旧版 Streamlit 上依然有效，
> 也是理解「为什么必须自己算 height」的最好材料。

## 点击图表会不会 rerun？（v2 必读）

**默认不会。** 1.3.0 起，`streamlit_dashboard()` 只有显式传了 `on_select` 才把图表点击
通过 trigger 回传给 Python；不传时前端 `EazyViz.onSelect` 为 `null`，点击、联动、下钻、
图例开关全部在浏览器内完成，**脚本一次都不 rerun**，此时返回值的 `result.select` 恒为
`None`。

- **浏览器内交互（默认）**：联动筛选条、下钻、图例开关都只改 DOM / ECharts，不碰 Python。
  图表 id 从 1.2.0 起稳定化（1.4.0 起形如 `eazy-<6 位看板指纹>-<位置>`，如 `eazy-044861-0`），即使侧栏控件改动导致脚本重跑，
  组件 `data` 也不变、组件不会重挂，交互状态照常保留。
- **需要感知点击**：传 `on_select`，点击会 trigger 一次，Streamlit 重跑整个脚本（右上角
  出现计算态）。6 张图重算通常 200–300ms；20 图 / 2 万行约 3.6s、payload 约 3.2MB（见 §6）。
- **要回调又不想整页重跑**：把看板包进 `@st.fragment`（Streamlit ≥ 1.37），trigger 自带
  `fragmentId`，只重跑这个 fragment。

```python
# 默认：零 rerun，点图 / 联动 / 下钻全在浏览器里处理
result = edv.streamlit_dashboard(charts, cols=2, title="经营驾驶舱")

# 需要 Python 侧响应点击：传回调（此时点击会触发一次 rerun）
def on_click():
    st.toast("图表被点击了")

result = edv.streamlit_dashboard(charts, cols=2, on_select=on_click)
if result.select:
    st.write(result.select)   # {chart, title, type, dim, value, drill, link}
```

对照：v1 路径点击图表 0 次 rerun；v2 默认 0 次、传 `on_select` 时 1 次且联动状态保留。

## 0. 最小可运行应用

新建 `app.py`（放在仓库根目录，保证 `import eazy_data_viz` 能找到包）：

```python
import streamlit as st
import streamlit.components.v1 as components

import eazy_data_viz as edv
from eazy_data_viz import render as edv_render

st.set_page_config(page_title="销售看板", layout="wide")
st.title("销售经营看板")

df = edv.sample_df()

bar = edv.bar(df, x="大区", y="销售额", drill=["大区", "省份", "城市"], link="G")
pie = edv.pie(df, names="产品", values="销售额", link="G")
kpi_sales = edv.kpi(df, value="销售额", label="销售额合计", link="G")
kpi_orders = edv.kpi(df, value="订单数", label="订单数合计", link="G")

page = edv.dashboard(kpi_sales, kpi_orders, bar, pie, cols=2,
                     title="销售经营看板", desc="点柱形下钻，点图联动")
html = page.to_html()
height = edv_render.page_height(page.charts, cols=2, has_header=True, has_filters=True)
components.html(html, height=height, scrolling=False)
```

```bash
streamlit run app.py
```

预期：浏览器自动打开 `http://localhost:8501`，前端是一整块 dashboard，高 **806px**
（`page_height(page.charts, cols=2, has_header=True, has_filters=True)` 的实测值），
能下钻、能联动、能切主题。

**这段代码里最重要的一行是 `height=...`**——不是可选项，下面解释原因。

## 1. 为什么必须自己传 height

`st.components.v1.html()` 的 iframe 高度由参数决定，**默认只有 150px**。
图表页真实高度通常 200~1500px，150px 的结果就是“只露出标题和一条边”。

```python
# 高度完全由参数决定：同一个 HTML，180px 与 800px 的显示效果天差地别
components.html(html, height=180, scrolling=False)   # 被裁掉大半
components.html(html, height=800, scrolling=True)    # 出现内部滚动条
```

手动传高度有两种方式：

### 方式 A：用 `page_height()` 算（推荐）

`page_height()` 在 `eazy_data_viz/render.py`，签名：

```python
page_height(charts, cols=None, has_header=False, has_filters=False) -> int
```

公式（与 `_card_height` 对应）：

| 组成 | 数值 |
| --- | --- |
| 每张卡片 | KPI：`height+24`；表格/进度/词云/tile：`height+head+10`；普通图：`height+head+toolbar+14` |
| 卡片头 | 有标题/副标题 46，否则 8 |
| 卡片工具栏 | 有 `drill` 或 `link` 时 30，否则 0 |
| 行间距 | 每行之间 `16` |
| body padding | `40` |
| 顶栏（`has_header`） | `60` |
| 联动筛选条（`has_filters`） | `46` |

实测值（Python 3.8 + 默认 `height`）：

| 布局 | `page_height(...)` |
| --- | --- |
| 单张 KPI，`cols=1` | `214` |
| 4 张 KPI，`cols=2` | `404` |
| 4 张 KPI，`cols=4` | `214` |
| 单张柱图，`cols=1` | `480` |
| 单张柱图 + 顶栏 | `540` |
| 单张表格，`cols=1` | `496` |
| 4 图 + 标题 + 联动，`cols=2` | `1102` |
| 空列表 | `200` |

```python
import eazy_data_viz as edv
from eazy_data_viz import render as edv_render

df = edv.sample_df()
kpis = [edv.kpi(df, value=c) for c in ("销售额", "订单数", "利润", "客户数")]
print("4 KPI cols=2:", edv_render.page_height(kpis, cols=2))   # 404
print("4 KPI cols=4:", edv_render.page_height(kpis, cols=4))   # 214
one = edv.bar(df, x="大区", y="销售额")
print("单柱图:", edv_render.page_height([one], cols=1))         # 480
print("单柱图+顶栏:", edv_render.page_height([one], cols=1, has_header=True))  # 540
```

```text
4 KPI cols=2: 404
4 KPI cols=4: 214
单柱图: 480
单柱图+顶栏: 540
```

注意 `has_header` / `has_filters` 是**手动告诉函数**的：传了 `title`/`desc` 才加 60，
有任意 `link` 才加 46。偷懒可以再多留 20px 余量（官方示例 `examples/streamlit_app.py`
就是 `height + 20`），代价是底部多一条空白。

### 方式 B：让 Dashboard 自己算（最省事）

在 Streamlit 里直接 `page.show()`，库会自己调用 `components.html` 并算好高度：

```python
page.show()          # Streamlit 分支：components.html(html, height=page_height(...), scrolling=False)
```

`Dashboard.show()` 自动使用 `self.cols`、`has_header=bool(title or desc)`、
`has_filters=any(link)`；单图 `chart.show()` 则按 `page_height([self], cols=1)` 算。
**只有需要自己套 `components.html`（比如加额外样式、放进 `st.container`）时才手算。**

### 不要用 `st.html()` / `unsafe_allow_html`

- `st.html()` 不会执行 `<script>`，页面一片空白；
- `st.markdown(html, unsafe_allow_html=True)` 会过滤/转义，同样点不动；
- 唯一正确通道是 `st.components.v1.html`（内部是 iframe，脚本能跑）。

## 2. 一个最容易踩的 Streamlit 语义：控件一改，整页重跑

Streamlit 的模型是“脚本从头再执行一次”。这意味着：

| 事件 | 发生什么 |
| --- | --- |
| 拖动 slider / 改 selectbox | 整个脚本重跑 → `to_html()` 重新生成 → iframe 被替换 |
| 在 iframe 里下钻/联动 | 只改浏览器内存，**不触发** Streamlit 重跑 |
| 触发重跑后 | 之前的下钻/联动状态**全部丢失**（iframe 重建） |

所以交互状态和 Streamlit 控件是两套系统：

- **浏览器内状态**（drill/link/legend/主题）：只在当前 iframe 内，重跑即重置；
- **Streamlit 状态**（`st.session_state`、控件值）：脚本重跑后保留，但影响的是**生成什么图**。

设计应用时把“需要跨重跑保留的筛选”做成**数据层的参数**（先过滤 df 再画），
而不是指望 iframe 状态；把“探索式下钻”留在浏览器里就够了。

```python
# 反模式：每次改控件都重建整页，探索状态必然丢
region = st.sidebar.selectbox("大区", ["全部"] + sorted(df["大区"].unique()))
view = df if region == "全部" else df[df["大区"] == region]
edv.bar(view, x="省份", y="销售额").show()
```

## 3. 侧栏：主题、配色、列数、Top N

典型控制面板（全部是普通 Streamlit 控件，和图表库没有耦合）：

```python
import streamlit as st

theme = st.sidebar.radio("主题", ["light", "dark"], horizontal=True)
palette = st.sidebar.selectbox("配色库", edv.palettes(verbose=False))
cols = st.sidebar.slider("每行列数", 1, 3, 2)
top_n = st.sidebar.slider("Top N", 3, 15, 8)

page = edv.dashboard(
    edv.kpi(df, value="销售额", label="销售额"),
    edv.kpi(df, value="订单数", label="订单数"),
    edv.bar(df, x="城市", y="销售额", top_n=top_n),
    edv.line(df, x="日期", y="销售额"),
    cols=cols, theme=theme, palette=palette,
    title="可配置看板",
)
page.show()
```

几个注意点：

- `edv.palettes(verbose=False)` 返回名字列表（7 项），非常适合直接喂给 `selectbox`；
  `verbose=True`（默认）会在控制台打印每套配色的说明。
- `theme` 只接受 `"light"` / `"dark"`，其它值 Python 侧直接 `ValueError`。
- `cols` 改变会改变 `page_height`，用 `page.show()` 时库会自动重算；
  自己 `components.html` 时必须同步重算高度。
- 控件放 `sidebar` 是习惯问题，不影响渲染；`st.form` 可以把多个控件合并成一次重跑，
  但提交后同样会重建 iframe。

## 4. `@st.cache_data`：别在每次重跑时重算数据

`sample_df()` 很快，真实业务查询/聚合往往很慢。用 `st.cache_data` 缓存**数据准备**和
**HTML 生成**这两层：

```python
import streamlit as st
import eazy_data_viz as edv

@st.cache_data(show_spinner="加载数据…")
def load_data() -> "pd.DataFrame":
    # 真实场景：SQL / API / Excel，参数作为缓存 key
    return edv.sample_df()

@st.cache_data(show_spinner="生成看板…")
def build_html(theme: str, palette: str, top_n: int) -> str:
    df = load_data()
    page = edv.dashboard(
        edv.bar(df, x="产品", y="销售额", top_n=top_n, theme=theme),
        edv.pie(df, names="渠道", values="销售额", theme=theme),
        cols=2, theme=theme, palette=palette,
        title="缓存示例",
    )
    return page.to_html()
```

要点：

- `cache_data` 的缓存 key 是**函数参数**，所以把 `theme/palette/top_n` 都显式传进来；
- 返回 `str`（HTML）最安全：`Dashboard` 对象也能缓存，但含可变 dict，容易被后续调用改掉；
- 不要在缓存函数里读 `st.session_state` 或全局变量——缓存不会感知它们的变化；
- 数据变了用 `load_data.clear()` 或调整参数（如传入日期区间）主动失效；
- 长 TTL 场景可加 `ttl=3600`。

```python
h1 = build_html("light", "google", 8)
h2 = build_html("light", "google", 8)   # 第二次直接命中缓存，不重新构建
print("长度:", len(h1), len(h2))
```

```text
长度: 1382469 1382469
```

两次长度相同，但**不要用 `h1 == h2` 判断是否命中缓存**：卡片 id 由「看板内容指纹 + 位置」生成
（`eazy-<6 位指纹>-<i>`），指纹里包含数据、列名、标题等，任一项变化都会拿到不同 id 的 HTML。
判断缓存是否生效请看首次调用的耗时，而不是比较字节。

## 5. 页面组织方式

### 5.1 单页 + `st.columns`/容器

一块 dashboard 已经自带网格（`cols=1/2/3`），通常不需要再套 `st.columns`：

```python
st.set_page_config(page_title="经营驾驶舱", layout="wide")
st.title("经营驾驶舱")
page.show()
```

`layout="wide"` 让主区域更宽，图表可读性更好；`page.show()` 的 iframe 默认撑满可用宽度。

### 5.2 多页应用（`pages/` 目录）

Streamlit 原生多页：入口 `app.py` + `pages/1_总览.py`、`pages/2_明细.py`。
每个页面各自生成自己的 dashboard 即可；**不同页面之间天然不联动**（各自独立 iframe/会话）。

```
app.py
pages/
  1_总览.py
  2_明细.py
  3_关于.py
```

### 5.3 混合排版：图表 + 表格 + 控件

```python
left, right = st.columns([2, 1])
with left:
    edv.line(df, x="日期", y="销售额", height=320).show()
with right:
    st.metric("销售额合计", f"{df['销售额'].sum():,.0f}")
    st.metric("订单数", f"{df['订单数'].sum():,}")
```

`chart.show()` 会根据自身高度算 iframe 高度，`st.metric` 是原生组件，互不干扰。
但注意**不要期望 `st.metric` 和 iframe 里的图联动**——跨 iframe 不通信（见 06 篇第 8 节）。

## 6. 性能与体积

| 关注点 | 事实 | 建议 |
| --- | --- | --- |
| 单次传输 | 一个 dashboard HTML 约 1.3~1.5 MB（ECharts 已内联 + 数据一份） | 生产内网可接受；公网加 gzip 反代后约 300~400 KB |
| 每次重跑 | 控件变化会重新生成并下发整块 HTML | 用 `cache_data` 缓存 `to_html()`；把控件分组降低频率 |
| 图表数量 | 每多一张图只加"卡片 + spec"，数据按 `dataRef` 去重 | 一页 12~20 张是合理区间；50 张以上考虑拆页 |
| 数据行数 | 默认最多嵌入 20 万行/图，超过自动均匀采样 | 用预聚合把行数压到几千，图表更轻 |
| 交互状态 | 重跑即丢 | 接受它，或把筛选做成数据层参数 |

```python
# 体积自查：同一批数据，图多图少差多少
import eazy_data_viz as edv
from eazy_data_viz import render as edv_render

df = edv.sample_df()
small = edv.dashboard(edv.bar(df, x="大区", y="销售额")).to_html()
big = edv.dashboard(
    *[edv.bar(df, x="大区", y=c) for c in ("销售额", "订单数", "利润", "客户数")],
    edv.line(df, x="日期", y="销售额"),
    edv.pie(df, names="产品", values="销售额"),
    edv.table(df, limit=50),
    cols=2, title="多图看板",
).to_html()
print("1 图:", len(small), "| 6 图:", len(big), "| 差额:", len(big) - len(small))
```

```text
1 图: 1380518 | 6 图: 1402854 | 差额: 22336
```

（绝对字节随版本浮动，但结论稳定：**ECharts 本体约 1.3 MB 是固定成本，第二张图起只加几 KB 到几十 KB**。）

## 7. 常见坑速查

| 现象 | 原因 | 修法 |
| --- | --- | --- |
| 只显示一小条 / 图表被拦腰截断 | `components.html` 默认 height=150 | 传 `height=page_height(...)` 或用 `page.show()` |
| 页面下方出现滚动条 | height 给小了 | +20~40 余量，或用实际布局参数重算 |
| 图表空白，浏览器控制台报 `EazyViz is not defined` | 用了 `st.html`/markdown，脚本没执行 | 改用 `st.components.v1.html` |
| 图表空白且页面里有 `#eazy-js-error` | 数据/图表配置 JS 报错 | 打开 iframe 控制台看具体异常；对照 12 篇 |
| 修改了库源码，刷新 Streamlit 没变化 | Streamlit 只监控入口脚本，不监控包依赖 | 重启 `streamlit run`（或 `--server.runOnSave true` 下改 app.py 触发） |
| 两个组件之间联动不生效 | iframe 隔离 | 合并成一个 Dashboard（06 篇第 8 节） |
| 重跑后下钻/联动没了 | iframe 重建 | 预期行为；需要保留就做成数据层筛选 |
| `ImportError: No module named streamlit` | 没装 extra | `pip install ".[streamlit]"` |
| 深浅色和 Streamlit 主题不一致 | 两者独立 | 用 sidebar 控件把 `theme` 传给 `dashboard()` |
| `st.cache_data` 没生效 | 参数里有可变对象/全局状态 | 只传不可变参数；必要时 `clear()` |

## 8. 完整示例：带侧栏的驾驶舱应用

把本篇素材拼起来就是一个可用的内部应用（`examples/streamlit_app.py` 是仓库自带版本）：

```python
import streamlit as st
import streamlit.components.v1 as components

import eazy_data_viz as edv
from eazy_data_viz import render as edv_render

st.set_page_config(page_title="销售驾驶舱", layout="wide")

@st.cache_data(show_spinner="准备数据…")
def load_data():
    return edv.sample_df()

@st.cache_data(show_spinner="生成看板…")
def build(theme: str, palette: str, top_n: int, cols: int) -> tuple:
    df = load_data()
    cards = [
        edv.kpi(df, value="销售额", label="销售额合计", theme=theme, section="一、核心指标"),
        edv.kpi(df, value="订单数", label="订单数合计", theme=theme, section="一、核心指标"),
        edv.kpi(df, value="利润", label="利润合计", theme=theme, section="一、核心指标"),
        edv.kpi(df, value="客户数", label="客户数", theme=theme, section="一、核心指标"),
        edv.line(df, x="日期", y="销售额", theme=theme, section="二、趋势"),
        edv.bar(df, x="大区", y="销售额", drill=["大区", "省份", "城市"],
                link="G", theme=theme, section="三、结构"),
        edv.pie(df, names="产品", values="销售额", link="G", theme=theme),
        edv.bar(df, x="城市", y="销售额", top_n=top_n, theme=theme, section="四、排名"),
        edv.table(df, columns=["日期", "大区", "城市", "产品", "销售额"],
                  limit=20, link="G", theme=theme),
    ]
    page = edv.dashboard(cards, cols=cols, title="销售经营驾驶舱",
                         desc="下钻/联动/主题切换全部可用", theme=theme, palette=palette)
    height = edv_render.page_height(
        page.charts, cols=cols, has_header=True, has_filters=True
    ) + 20
    return page.to_html(), height

theme = st.sidebar.radio("主题", ["light", "dark"], horizontal=True)
palette = st.sidebar.selectbox("配色", edv.palettes(verbose=False))
cols = st.sidebar.radio("列数", [1, 2, 3], index=1, horizontal=True)
top_n = st.sidebar.slider("城市 Top N", 3, 15, 8)

html, height = build(theme, palette, top_n, cols)
components.html(html, height=height, scrolling=False)
```

```bash
streamlit run app.py
```

验收清单：

1. 首屏高度合适，没有内部滚动条；
2. 侧栏切 `dark` / 换配色 → 整块看板换肤；
3. 改 Top N → 排名图变化；
4. 在 iframe 里下钻、联动 → 流畅；再改侧栏 → 状态重置（预期）。

## 9. 常见问题

**Q1：能不能不传 height，让 iframe 自动撑高？**
不能可靠做到：跨文档测量需要父页面脚本配合，而 `components.html` 没有暴露这个能力。
`page_height` 就是为此提供的估算函数。

**Q2：`page.show()` 和手写 `components.html` 怎么选？**
只放一张 dashboard 且不套容器 → `page.show()`；需要自定义高度/放进 columns/加额外 HTML → 手写。

**Q3：为什么我的回调（按钮）改了数据，图没变？**
Streamlit 是重跑模型，图表每次重跑会重新构建；如果没变，检查控件值是否真的参与了
`to_html()` 的生成，以及 `cache_data` 的 key 是否包含了该参数。

**Q4：`st.experimental_rerun` / `st.rerun` 会把 iframe 搞坏吗？**
会重建 iframe（等价于刷新），交互状态重置；这是 Streamlit 的设计，不是库的问题。

**Q5：能在一个页面里放两个 dashboard 并让它们联动吗？**
不能。两个 `components.html` 是两个 iframe，各有一份 `EazyViz`。合并成一个 Dashboard 即可。

## 下一篇

有时候你不需要 Streamlit，只需要一个能发给别人的单文件 HTML：
[08 · 静态 HTML 与导出](08-static-html-and-export.md)。
