# 02 · 五分钟上手

> 目标：不读任何其它文档，从零到「一张图 → 一个可发给同事的 HTML → 一个能联动的驾驶舱 → 一次主题切换」。
> 每一节都给出可直接复制运行的代码，以及你应该看到的输出。

## 适用人群与前置条件

| 项 | 要求 |
| --- | --- |
| 读者 | 会写 `for` 循环、知道 DataFrame 是什么即可 |
| 环境 | 已按 [01 · 安装与环境矩阵](01-installation.md) 装好 `eazy_data_viz` |
| 时间 | 5~15 分钟（含等浏览器打开） |
| 产物目录 | 本文统一写 `examples/output/`，该目录已在 `.gitignore` 中 |

先把三件事说清楚，后面所有例子都基于它们：

```python
import eazy_data_viz as edv

df = edv.sample_df()        # 内置示例数据，1500 行 × 11 列
print(df.shape)             # (1500, 11)
print(list(df.columns))
```

```text
(1500, 11)
['日期', '月份', '大区', '省份', '城市', '产品', '渠道', '销售额', '订单数', '利润', '客户数']
```

### 示例数据的列结构

`sample_df()` 生成的是一张「订单明细」形状的长表：一行是一笔订单聚合记录，
时间是 2024 年全年，覆盖 6 个大区、12 个省份/城市、4 个产品、3 个渠道。

| 列 | dtype | 角色 | 说明 |
| --- | --- | --- | --- |
| `日期` | `datetime64[ns]` | 时间 | 2024-01-01 起，逐日 |
| `月份` | `category`（有序） | 时间/有序类目 | `1月`…`12月`，**已是有序 Categorical**，折线图按自然月排序 |
| `大区` `省份` `城市` | `object` | 类目 | 层级：大区 → 省份 → 城市，可直接做下钻 |
| `产品` `渠道` | `object` | 类目 | 4 个产品 / 3 个渠道 |
| `销售额` `利润` | `float64` | 数值 | 金额，含小数 |
| `订单数` `客户数` | `int64` | 数值 | 计数 |

> **重要结论**：库不会猜你的意图，但会**按 dtype 猜列的角色**——数值列才能求和，
> 时间列才会按时间轴排序，`pd.Categorical(ordered=True)` 才会按你指定的顺序排。
> 详见 [09 · 数据准备](09-data-preparation.md)。

## 第 1 步：画第一张图（1 分钟）

```python
import eazy_data_viz as edv

df = edv.sample_df()
chart = edv.bar(df, x="大区", y="销售额", color="产品", stack=True)
chart.show()
```

发生了什么：

1. `edv.bar(...)` 返回一个 `Chart` 对象，**此时还没有生成 HTML**，只做了列校验和 spec 组装；
2. `.show()` 根据运行环境自动选择展示方式：

| 运行环境 | `.show()` 的行为 |
| --- | --- |
| 普通脚本 / 终端 | 写入临时 HTML，打印路径；有图形界面时自动打开浏览器 |
| Jupyter Notebook | 用 `IPython.display.HTML` 内联到输出单元 |
| Streamlit | 用 `st.components.v1.html` 嵌成组件，并自动算高度 |

在 Git Bash / CI 这类非交互终端里，你会看到类似输出（路径随系统不同）：

```text
[已生成图表] C:\Users\you\AppData\Local\Temp\eazy_2f3a1c.html
```

如果浏览器没自动打开，复制打印的路径手动打开即可——**能双击打开的 HTML 就是最终产物**。

### 1.1 换一种图只需要换函数名

```python
edv.line(df, x="月份", y="销售额", color="渠道", smooth=True).show()
edv.pie(df, names="产品", values="销售额", donut=True).show()
edv.heatmap(df, x="月份", y="大区", value="销售额").show()
edv.kpi(df, value="销售额", label="全年销售额", delta=0.128, target=2_000_000).show()
```

四个函数、同一个 `df`、只写列名。**没有一个 JSON、没有一个配置字典**。

### 1.2 想确认它到底生成了什么

```python
chart = edv.bar(df, x="大区", y="销售额", color="产品", stack=True)
print(chart.spec["type"])          # bar
print(chart.spec["roles"])         # {'x': '大区', 'y': '销售额', 'color': '产品'}
print(chart.spec["agg"])           # sum
print(chart.spec["sort"])          # desc（分类轴默认按数值降序）
print(chart.data_ref)              # d3f2a9c1b7e4（数据指纹，12 位）
print(chart.warnings)              # {'warnings': [], 'n_total': 1500}（采样警告在 warnings 列表里）
print(len(chart.to_html()))        # 1342749（约 1.3 MB，含内联 ECharts）
```

`chart.spec` 是「图怎么画」，`chart.data` 是「数据长什么样」，两者分离是本库的核心设计——
同一份 `df` 画 20 张图时，数据只会被序列化一次（见 [13 · 性能与体积](13-performance.md)）。

## 第 2 步：保存成独立 HTML（1 分钟）

```python
import os
os.makedirs("examples/output", exist_ok=True)

chart = edv.bar(df, x="大区", y="销售额", color="产品", stack=True,
                title="各大区销售额", subtitle="按产品堆叠 · 2024 全年")
path = chart.save("examples/output/quickstart_bar.html")
print(path)
```

`save()` 返回**绝对路径**，并会自动创建不存在的父目录。产物特性：

| 特性 | 说明 |
| --- | --- |
| 单文件 | 一个 `.html` 含 ECharts、运行时、数据，约 1.3 MB |
| 离线可用 | 断网、无 CDN、无服务器也能交互 |
| 可分享 | 微信/邮件/OSS/内网静态服务器，双击即用 |
| 可嵌入 | 也可放进 iframe 或后端模板（见 [08 · 静态 HTML 与导出](08-static-html-and-export.md)） |

浏览器打开后依次试：**悬停看 tooltip → 点图例隐藏一组 → 滚轮缩放 → 右上角截图下载 PNG**。
这些不需要写任何代码。

### 2.1 `.show()` 和 `.save()` 的关系

```python
chart.to_html()                 # 返回 HTML 字符串（自己塞模板时用）
chart.save("out.html")          # 写文件（最常用）
chart.show()                    # 按环境展示（脚本里 = 临时文件 + 打开）
```

三者用的是同一个渲染器，**体积和效果完全一致**；区别只是「给谁」。

## 第 3 步：拼一个驾驶舱（2 分钟）

单图只能看一个切面。多张图放进 `edv.dashboard(...)` 或 `edv.show(...)` 才会出现
「点击一张图，其它图跟着筛选」的联动能力。

```python
import eazy_data_viz as edv

df = edv.sample_df()

dash = edv.dashboard(
    edv.group_kpi(
        names=None,
        items=[
            {"label": "总销售额", "value": float(df["销售额"].sum()), "fmt": "compact", "delta": 0.128},
            {"label": "总利润", "value": float(df["利润"].sum()), "fmt": "compact", "delta": 0.086},
            {"label": "订单数", "value": int(df["订单数"].sum()), "fmt": "raw"},
            {"label": "客户数", "value": int(df["客户数"].sum()), "fmt": "raw"},
        ],
    ),
    edv.line(df, x="月份", y="销售额", color="渠道", link="经营", title="销售额趋势"),
    edv.bar(df, x="大区", y="销售额", color="产品", stack=True, link="经营", title="大区构成"),
    edv.pie(df, names="产品", values="销售额", donut=True, link="经营", title="产品占比"),
    edv.heatmap(df, x="月份", y="大区", value="利润", title="利润热力"),
    cols=2,
    title="经营驾驶舱（最小版）",
    desc="点击任意一张有联动的图，其余带 link 的图会交叉筛选",
)
dash.save("examples/output/quickstart_dashboard.html")
```

要点：

1. **`link` 分组**：上面三张图都写了 `link="经营"`，点任意一张的柱子/折线点，
   另外两张会按点击的类目筛选；再点一次同一项取消筛选。
2. **`edv.dashboard(...)` 接受任意张图**，`cols=2` 表示两列网格；宽度按视口自适应。
3. **`edv.show(...)` 就是 `edv.dashboard(...).show()`**，脚本里等价：

```python
edv.show(
    edv.line(df, x="月份", y="销售额"),
    edv.bar(df, x="大区", y="销售额"),
    cols=2,
    title="最简看板",
).save("examples/output/quickstart_show.html")
```

> **重要结论**：联动、下钻、主题切换这些“全局能力”只有在 Dashboard 里才生效；
> 单图 `.save()` 出去只有该图自己的交互（缩放、图例、tooltip、PNG）。

## 第 4 步：主题与配色（1 分钟）

### 4.1 单图切深色

```python
edv.line(df, x="月份", y="销售额", color="产品",
         theme="dark", title="深色主题").save("examples/output/quickstart_dark.html")
```

`theme` 只有两个合法值：`"light"` / `"dark"`，非法值会立刻抛
`ValueError('theme 只支持 "light" / "dark"，收到 ...')`。

### 4.2 整页切深色

```python
dash_dark = edv.dashboard(
    edv.bar(df, x="大区", y="销售额"),
    edv.pie(df, names="渠道", values="订单数"),
    cols=2, theme="dark", title="深色驾驶舱",
)
dash_dark.save("examples/output/quickstart_dark_dashboard.html")
```

### 4.3 换配色

```python
import eazy_data_viz as edv

edv.palettes()                      # 打印 7 套配色 + 目前默认
edv.set_palette("tableau")         # 改全局默认（影响之后创建的所有图）
print(edv.palette.current())        # tableau

# 单图覆盖（不改变全局）
edv.bar(df, x="大区", y="销售额", color="产品").palette("morandi").save(
    "examples/output/quickstart_morandi.html")

# 整页覆盖
edv.dashboard(
    edv.bar(df, x="大区", y="销售额", color="产品"),
    edv.line(df, x="月份", y="销售额"),
    palette="carbon", cols=2, title="Carbon 配色",
).save("examples/output/quickstart_carbon.html")

edv.set_palette("google")           # 用完记得复位，避免影响后续例子
```

三层优先级从高到低：**单图 `.palette()` > 整页 `dashboard(palette=)` > 全局 `set_palette()`**。
浏览器里打开带标题的 Dashboard，右上角还会出现配色下拉框和明暗切换按钮，观众可以自己切。

## 第 5 步：把示例数据换成你的数据

只有三件事要注意：

```python
import pandas as pd
import eazy_data_viz as edv

# 1) 读进来：列名保留中文没问题；日期列要真日期类型
df = pd.read_excel("经营数据.xlsx", parse_dates=["日期"])
# df = pd.read_csv("经营数据.csv", encoding="utf-8-sig", parse_dates=["日期"])

# 2) 数值列被当成文本时，显式转换（金额里带逗号/￥时先清洗）
df["销售额"] = pd.to_numeric(df["销售额"], errors="coerce").fillna(0)

# 3) 分类排序想自定义时，用有序 Categorical
df["月份"] = pd.Categorical(
    df["月份"], categories=[f"{i}月" for i in range(1, 13)], ordered=True
)

edv.line(df, x="日期", y="销售额", color="渠道", smooth=True,
         title="我的第一个真实图表").save("examples/output/quickstart_my.html")
```

三个最常见的数据坑（报错原文见 [12 · 常见错误](12-troubleshooting.md)）：

| 现象 | 原因 | 一行修法 |
| --- | --- | --- |
| 图是空的 / 只有 1 根柱 | 数值列其实是 `object`（含 `¥`、逗号、空串） | `pd.to_numeric(s, errors="coerce")` |
| 月序乱了（10月 在 2月 前） | 月份是字符串 | `pd.Categorical(..., ordered=True)` |
| `KeyError: x列 '销售额' 不存在` | 列名有空格/全角 | `print(df.columns.tolist())` 对照 |

## 第 6 步：完整可运行脚本

把下面文件存为 `my_first_dashboard.py`，在仓库根目录执行：

```bash
PYTHONIOENCODING=utf-8 python my_first_dashboard.py
```

```python
# -*- coding: utf-8 -*-
"""五分钟上手完整脚本：单图 → HTML → 驾驶舱 → 深色 → 配色。"""
import os
import eazy_data_viz as edv

OUT = "examples/output"
os.makedirs(OUT, exist_ok=True)

df = edv.sample_df()
print("数据:", df.shape)

# 1) 单图落盘
p1 = edv.bar(df, x="大区", y="销售额", color="产品", stack=True,
             title="各大区销售额").save(os.path.join(OUT, "q_bar.html"))
print("单图:", p1)

# 2) 驾驶舱（4 张图联动 + KPI）
dash = edv.dashboard(
    edv.group_kpi(items=[
        {"label": "总销售额", "value": float(df["销售额"].sum()), "fmt": "compact", "delta": 0.128},
        {"label": "利润率", "value": float(df["利润"].sum() / df["销售额"].sum()), "fmt": "percent", "delta": 0.021},
        {"label": "订单数", "value": int(df["订单数"].sum()), "fmt": "raw"},
        {"label": "客户数", "value": int(df["客户数"].sum()), "fmt": "raw"},
    ]),
    edv.line(df, x="月份", y="销售额", color="渠道", link="g1", title="趋势"),
    edv.bar(df, x="省份", y="销售额", color="产品", stack=True, link="g1", title="省份构成"),
    edv.pie(df, names="产品", values="利润", donut=True, link="g1", title="利润占比"),
    cols=2, title="经营驾驶舱", desc="点击带 link 的图，其余联动筛选",
)
p2 = dash.save(os.path.join(OUT, "q_dashboard.html"))
print("驾驶舱:", p2, os.path.getsize(p2), "字节")

# 3) 深色 + 指定配色
p3 = edv.dashboard(
    edv.bar(df, x="大区", y="销售额", color="渠道"),
    edv.line(df, x="月份", y="利润"),
    cols=2, theme="dark", palette="morandi", title="深色莫兰迪",
).save(os.path.join(OUT, "q_dark.html"))
print("深色:", p3)

# 4) 自检
print("warnings:", [c.warnings for c in dash.charts])
```

预期输出（路径与字节数随机器不同）：

```text
数据: (1500, 11)
单图: F:\deepseek\eazy_data_viz\examples\output\q_bar.html
驾驶舱: F:\deepseek\eazy_data_viz\examples\output\q_dashboard.html 1401102 字节
深色: F:\deepseek\eazy_data_viz\examples\output\q_dark.html
warnings: [{}, {'warnings': [], 'n_total': 1500}, {'warnings': [], 'n_total': 1500}, {'warnings': [], 'n_total': 1500}]
```

打开 `q_dashboard.html`，按顺序验证四件事：

1. 顶部 4 张 KPI 卡、下面 3 张图 + 1 个空位（`cols=2`，共 4 张图）；
2. 点「趋势」里的某个渠道 → 「省份构成」和「利润占比」自动按该渠道筛选 → 顶部出现筛选 chip；
3. 再点同一个点 → 筛选取消；点右上角「重置联动」也能清空；
4. 点右上角 ◐ → 整页切深色；配色下拉框切到 `tableau` → 所有图重上色。

## 常见问题（新手最常卡住的 6 个）

**Q1：`.show()` 什么都没发生，也没打印东西？**
在无图形界面的服务器上，浏览器不会弹；但文件已经写到临时目录。用 `.save("x.html")` 拿到确定路径。
Jupyter 里则应该内联显示，若显示成一串文字，检查是否装了 `ipython`。

**Q2：`AttributeError: 'DataFrame' object has no attribute 'show'`？**
你调用的是 `df.show()`，不是 `edv.xxx(df, ...).show()`。本库不修改 pandas。

**Q3：图里中文是方框/乱码？**
HTML 内部已声明 UTF-8；乱码通常发生在**终端打印**。Windows 终端执行前设置
`set PYTHONIOENCODING=utf-8`（CMD）或 `export PYTHONIOENCODING=utf-8`（Git Bash）。

**Q4：KPI 卡显示 `¥1.2万` 还是 `12000`？看不明白 `fmt`。**
`fmt` 有 5 个值：`compact`（万/亿缩写）、`thousands`（千分位）、`raw`（原样）、
`percent`（0.128 → 12.8%）、`currency`（带 ¥）。默认 `compact`。

**Q5：`sort` 到底是什么默认值？**
分类轴且是 `bar` 默认按值降序；折线/面积默认不排序（保持数据顺序）；
横轴是时间/数值/有序 Categorical 时默认按 x 升序。不确定就显式写 `sort="none"`。

**Q6：图里只有 20 万行？**
`max_rows` 默认 200000（20 万行），超了会均匀采样并在 `chart.warnings` 里告诉你；
传 `max_rows=None` 可关闭采样（体积会明显变大）。
这是体积保护，不是 bug，见 [13 · 性能与体积](13-performance.md)。

## 下一篇

已经能出图了，接下来从零搭一个真正能用的经营驾驶舱：
[03 · 从零搭建经营驾驶舱](03-cockpit-tutorial.md)。
