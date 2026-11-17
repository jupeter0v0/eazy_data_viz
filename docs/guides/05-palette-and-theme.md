# 05 · 配色与主题

> 适用人群：要让图表符合公司 VI、需要在深浅色之间切换、或者单纯觉得默认颜色不好看的人。
> 前置条件：`import eazy_data_viz as edv`，`df = edv.sample_df()`。
> 读完你会：在 7 套配色里选对一套，用三层机制精确控制颜色，做出深色驾驶舱，并注入品牌色。

配色系统只有两个概念：

- **配色库（palette）**：一组 10 个分类色，决定“第 1 个系列什么颜色、第 2 个什么颜色……”；
- **主题（theme）**：`light` / `dark`，决定背景、文字、网格线；深色主题下的分类色会自动提亮 20%。

两者正交：任何配色 × 任何主题都能组合。

## 1. 七套配色，各自适合什么

先看一眼全部配色：

```python
import eazy_data_viz as edv

edv.palettes()          # 打印名字 / 标签 / 适用场景 / 色值 / 当前默认，返回名字列表
```

| 名字 | 标签 | 适用场景（`best_for`） | 主色 |
| --- | --- | --- | --- |
| `google` | Google Material 3 | 通用 / 公司经营驾驶舱默认 | `#1a73e8` 蓝 |
| `antd` | Ant Design | 中后台 / 业务报表 | `#1677ff` 蓝 |
| `tableau` | Tableau 10 | 多系列对比 / BI 分析图 | `#4e79a7` 灰蓝 |
| `carbon` | IBM Carbon | 深色大屏 / 技术运营 | `#6929c4` 紫 |
| `echarts` | ECharts 默认 | 兼容既有 ECharts 报表 | `#5470c6` 蓝紫 |
| `morandi` | 莫兰迪（低饱和） | 汇报 / 印刷 / 弱对比大屏 | `#8fa3b0` 灰 |
| `tailwind` | Tailwind / Flowbite | 产品增长 / 运营看板 | `#3f83f8` 亮蓝 |

选择建议（按优先级）：

1. **要跟已有报表长得一样** → `echarts`；
2. **多系列折线、散点分组** → `tableau`，十色明度差最大，最容易区分；
3. **给老板汇报、投屏** → `morandi`，低饱和不刺眼；
4. **深色大屏** → `carbon`（冷色多、对比强）；
5. **对外产品/官网风格** → `tailwind`；
6. **不知道选什么** → 默认 `google`。

```python
from eazy_data_viz import palette as pl

pl.get("tableau")
# {'name': 'tableau', 'label': 'Tableau 10',
#  'desc': '...', 'best_for': '多系列对比 / BI 分析图', 'colors': ['#4e79a7', ...]}

pl.names()      # ['google', 'antd', 'tableau', 'carbon', 'echarts', 'morandi', 'tailwind']
pl.listing()    # 给界面用的完整清单（含 desc / best_for / colors）
pl.current()    # 当前进程默认配色名，初始 "google"
```

## 2. 三层切换机制

| 层级 | API | 作用范围 | 优先级 |
| --- | --- | --- | --- |
| 全局默认 | `edv.set_palette("tableau")` | 当前 Python 进程，**之后构建的** Dashboard | 最低 |
| 整页 | `edv.dashboard(..., palette="carbon")` | 这一页所有没单独指定配色的图 | 中 |
| 单图 | `chart.palette("morandi")` | 这一张图，页面切换配色也不变 | 最高 |

### 2.1 全局默认

```python
import eazy_data_viz as edv

df = edv.sample_df()
edv.set_palette("tableau")          # 进程级默认
page = edv.dashboard(
    edv.bar(df, x="大区", y="销售额"),
    edv.line(df, x="月份", y="销售额", color="渠道"),
    cols=2, title="全局 tableau")
page.save("examples/output/palette_global.html")

edv.set_palette("google")           # 用完记得还原，避免影响同进程其它页面
```

**生效时机**：`set_palette` 影响的是 `dashboard(...)` 构建时读取的默认值。
图对象自己不会存“全局配色”，所以先建图、后 `set_palette`、再 `dashboard(...)` 也是新配色。

### 2.2 单图覆盖

`Chart.palette()` 是链式方法，返回图本身：

```python
c = edv.bar(df, x="大区", y="销售额", title="我会一直是 morandi").palette("morandi")
c.spec["palette"]     # 'morandi'

page = edv.dashboard(
    edv.bar(df, x="大区", y="销售额", title="跟随整页"),
    c,
    cols=2, title="单图覆盖演示", palette="carbon")
```

打开页面：第一张图用 carbon，第二张图用 morandi。**右上角配色下拉切换时，第二张图不变**——
因为它的 `spec.palette` 固定了。

```python
# 想恢复跟随整页：把 spec 里的 palette 去掉
c.spec.pop("palette", None)
```

### 2.3 整页覆盖

```python
page = edv.dashboard(
    edv.bar(df, x="大区", y="销售额"),
    edv.pie(df, names="渠道", values="销售额", donut=True),
    cols=2, title="整页 antd", palette="antd")
```

`dashboard(palette=...)` 不合法时抛 `ValueError`：

```python
edv.dashboard(edv.bar(df, x="大区", y="销售额"), palette="brand")
# ValueError: 未知配色 'brand'，可选：google、antd、tableau、carbon、echarts、morandi、tailwind
```

`palette.check(None)` / 空串返回当前默认值，所以不传等同于用全局默认。

## 3. 深色主题

主题同样三层：单图 `theme="dark"`、整页 `dashboard(theme="dark")`，以及页面右上角的 ◐ 按钮
（运行时切换，不重新加载）。

```python
page = edv.dashboard(
    edv.bar(df, x="大区", y="销售额", color="产品", stack=True, title="深色示例"),
    edv.line(df, x="月份", y="销售额", color="渠道", title="深色折线"),
    edv.kpi(df, value="销售额", label="销售额", target=2_000_000),
    cols=2, title="深色驾驶舱", theme="dark", palette="carbon")
page.save("examples/output/theme_dark.html")
```

深色模式的实现（`themeFor(mode, paletteName)`）：

- 背景 / 文字 / 网格线来自 Material 3 的深色基础色；
- 分类色统一向白色混合 20%（`mixColor(color, "#fff", 0.2)`）提亮，保证深底上可读；
- 热力图色阶由**首色**派生：浅色模式从 8% 首色到 100% 首色，深色模式反向；
- 主题对象按 `mode|palette` 缓存，切换开销很小。

运行时 ◐ 按钮做的事：给 `<html data-theme>` 和 `<body data-theme>` 设值、重建每个图的主题、
`dispose()` 旧 ECharts 实例后重绘。**联动筛选状态会保留**，不会因为切主题而清空。

单图混用深浅色（不推荐，仅特殊版面）：

```python
dark_card = edv.bar(df, x="大区", y="销售额", theme="dark", title="单独深色卡片")
```

## 4. 运行时配色下拉框

只要 Dashboard 有 `title` 或 `desc`，顶栏就会出现：

- 配色 `<select data-eazy-palette>`（7 个内置选项）；
- ◐ 主题按钮；
- 有 `link` 或有 `drill` 时会出现顶栏按钮：`重置联动`、`重置下钻`；`link` 还会有筛选 chips。

选择下拉项调用前端 `setPalette(name)`：

1. 更新 `EazyViz.page.palette`；
2. 对每张图：`chart.paletteName = spec.palette || 选中的名字`（**单图固定配色优先**）；
3. dispose 后重绘，联动状态保留。

**没有标题就没有顶栏**——这是“下拉框不出现”最常见的原因。

```python
# 没有顶栏，没有下拉框
edv.dashboard(edv.bar(df, x="大区", y="销售额"), cols=2)

# 有顶栏：title 或 desc 至少给一个
edv.dashboard(edv.bar(df, x="大区", y="销售额"), title="有顶栏")
```

## 5. 品牌色自定义

### 5.1 先试最省事的：内置库 + accent

大多数“品牌色”需求其实是“强调色一致”。用 `accent` 把 KPI/进度条固定到某个色号即可：

```python
edv.kpi(df, value="销售额", label="销售额", accent=0)   # 取当前配色的第 0 色
```

如果公司主色恰好接近某套内置色板的第 1 色，直接换那套配色最省事：

| 公司主色 | 最接近的内置配色 |
| --- | --- |
| 蓝 `#1677ff` | `antd` |
| 谷歌蓝 `#1a73e8` | `google` |
| 亮蓝 `#3f83f8` | `tailwind` |
| 紫 `#6929c4` | `carbon` |

### 5.2 真·品牌色：Python 注册 + HTML 注入

内置 7 套是**前端 JS 里写死**的（`EazyViz.PALETTES`）。要加自己的色板，需要两步：

**第一步，Python 侧注册**，让 `dashboard(palette=...)` 校验通过、顶栏下拉框出现你的选项：

```python
from eazy_data_viz import palette as pl

BRAND = ["#0057B8", "#00A3E0", "#F2A900", "#D64545", "#6F42C1",
         "#20B2AA", "#FF7F50", "#C71585", "#5A5A5A", "#8B6F47"]

pl.COLOR_PALETTES["brand"] = {
    "label": "企业品牌蓝",
    "desc": "公司 VI 色板（示例）",
    "best_for": "对外品牌报表",
    "colors": list(BRAND),
}
```

**第二步，生成 HTML 后注入前端色板**，放在 `EazyViz.init()` 之后：

```python
page = edv.dashboard(
    edv.bar(df, x="大区", y="销售额", title="品牌色柱图"),
    edv.pie(df, names="渠道", values="销售额", donut=True),
    cols=2, title="品牌色示例", palette="brand")

html = page.to_html()
inject = (
    'EazyViz.init(window.EAZY_PAGE);'
    'EazyViz.PALETTES.brand={label:"企业品牌蓝",colors:%r};'
    'EazyViz.setPalette("brand");'
) % (BRAND,)
inject = inject.replace("'", '"')          # JS 里用双引号

html = html.replace("EazyViz.init(window.EAZY_PAGE);", inject, 1)
open("examples/output/palette_brand.html", "w", encoding="utf-8").write(html)
```

打开 `examples/output/palette_brand.html`：图表用品牌色，下拉框里也能选回其它内置配色
（切走再选“企业品牌蓝”仍然有效，因为 `EazyViz.PALETTES.brand` 已在页面里注册）。

注意事项：

- `EazyViz.init(...)` 这行是模板固定输出，**首次出现即替换一次**；注入必须放在它之后，
  因为 `init` 要先读到 `window.EAZY_PAGE`；
- `palette="brand"` 在 init 时 JS 还不认识，会先回退 `google`，紧接着 `setPalette("brand")`
  修正——所以会有一次极短的重绘，无感知；
- 注入后的 HTML 仍是单文件，可离线分发；但这是**运行时扩展**，不是官方 API，
  升级库后模板若改了 init 调用形式，需要同步调整替换字符串；
- 不要直接改 `site-packages/eazy_data_viz/assets/eazy.js`——升级会丢，且无法在 Streamlit
  部署环境里持久化。

### 5.3 Streamlit 里同样可用

```python
import streamlit as st
import streamlit.components.v1 as components
from eazy_data_viz import render as edv_render

html = page.to_html().replace("EazyViz.init(window.EAZY_PAGE);", inject, 1)
h = edv_render.page_height(page.charts, cols=2, has_header=True)
components.html(html, height=h + 20, scrolling=False)
```

`page_height` 从 `eazy_data_viz.render` 导入（它不在顶层 `__all__` 里）。

## 6. 常见问题

| 现象 | 原因 | 修法 |
| --- | --- | --- |
| `ValueError: 未知配色 'xxx'，可选：…` | 拼错名字或用了未注册的自定义名 | 用 `pl.names()` 里的名字；自定义先注册 |
| 顶栏没有配色下拉框 | Dashboard 没 `title`/`desc` | 给标题或副标题 |
| 切换下拉框，某张图不变 | 该图用了 `.palette()` 固定 | 去掉 `spec["palette"]` 或接受 |
| 切主题后颜色发灰 | 深色模式按 20% 白提亮，低饱和色板（morandi）更明显 | 深色场景换 `carbon` / `tableau` |
| `set_palette` 后旧图没变 | 全局默认只在 `dashboard()` 构建时读取 | 在构建页面前调用 |
| 品牌色注入了但没效果 | `EazyViz.setPalette` 执行时 `EazyViz` 还没初始化 / 替换没命中 | 确认替换字符串 `EazyViz.init(window.EAZY_PAGE);` 存在，且注入在它之后 |
| Streamlit 里配色下拉无效 | iframe 内页面自己重绘正常，但父页面没有联动 | 下拉框只在 iframe 内部生效，正常现象 |
| 深色下导出 PNG 背景是白的 | PNG 导出取当前画布，主题是深色时背景也深 | 不需要额外处理；要白底就切回 light 再导出 |

两个容易混淆的点：

1. **配色和主题互不影响**：`palette` 管分类色，`theme` 管背景文字；深色不是“另一套配色”；
2. **跨 iframe 的状态不同步**：Streamlit 里每个组件是独立 iframe，各自的主题/配色下拉
   只作用于自己，父页面没法帮它同步（见 [07 · Streamlit](07-streamlit.md)）。

## 下一篇

- 交互（下钻 / 联动 / 图例 / 缩放 / 导出 PNG）：[06 · 交互总览](06-interaction.md)
- 单文件 HTML 的体积与拆资源：[08 · 静态 HTML 与导出](08-static-html-and-export.md)
- 配色与 KPI 强调色：[04 · KPI 卡片](04-kpi-cards.md)
