# 13 · 性能与体积

> 目标：知道一张图为什么大、大在哪里、怎么在 3 分钟内把 20 MB 的页面压到 2 MB，并且不牺牲可读性。
> 先读 [09 · 数据准备](09-data-preparation.md) 的「大数据量」一节，本篇只谈测量与取舍。

## 1. 三个常数

| 常数 | 实测值 | 含义 |
| --- | --- | --- |
| 空页面基线 | **1.205 MB**（126 万字符） | ECharts 5.5.1 + 运行库 + 样式全部内联，页面再小也这么大 |
| 数据体积 | **约 99 B/行**（11 列） | 每行 JSON 的列名只出现一次，行是纯值数组 |
| 单图额外开销 | **约 1–3 KB** | 图只嵌 spec 和 dataRef，不重复嵌入数据 |

结论：HTML 体积 ≈ 1.2 MB + 行数 × 列数 × 约 9 B。与图的数量几乎无关，与**嵌入的行数 × 列数**直接相关。

## 2. 数据量 vs 文件体积（实测）

环境：Python 3.8.10 / pandas 2.0.3，11 列 `edv.sample_df()`，单张 `bar`，`to_html()` 生成的 UTF-8 文件。

| 数据行数 | 实际嵌入行数 | HTML 体积 | 其中数据 JSON | Python 生成耗时 |
| --- | --- | --- | --- | --- |
| 0（只有 KPI） | 0 | 1.205 MB | 0 | 0.00 s |
| 1,000 | 1,000 | 1.316 MB | 0.099 MB | 0.01 s |
| 5,000 | 5,000 | 1.755 MB | 0.496 MB | 0.01 s |
| 50,000 | 50,000 | 6.693 MB | 4.963 MB | 0.09 s |
| 200,000 | 200,000 | 23.154 MB | 19.850 MB | 0.38 s |

`max_rows` 对 20 万行数据的削减效果：

| max_rows | 嵌入行数 | HTML 体积 | 提示 |
| --- | --- | --- | --- |
| `1000` | 1,000 | 1.316 MB | 有采样警告 |
| `10000` | 10,000 | 2.303 MB | 有采样警告 |
| `200000` | 200,000 | 23.154 MB | 无 |
| `None`（30 万行） | 300,000 | 34.128 MB | 无，且 0.67 s |

同样 5,000 行，**只保留用到的 2 列** 是 1.303 MB；预聚合到「大区 × 月份」这类 40 行汇总表后压到 **1.206 MB**——数据部分几乎归零。

### 默认值调整（1.5.2）

`max_rows` 默认由 200000 提到 **2000000**。体积按上表线性估算：约 120 B/行，
即 200 万行 ≈ **230 MB** 的 HTML。所以：

* 折线 / 柱状 / 饼图这类只看趋势和汇总的图，仍然建议显式传 `max_rows=5000~50000`；
* 散点、箱线、明细表要看原始点分布时，默认值已经足够放下百万级数据；
* 真要到百万行还嫌大，先 `groupby` 预聚合最有效（见下一节）。

## 3. 体积从哪里来

```python
import eazy_data_viz as edv
df = edv.sample_df(rows=5000)

# 11 列全嵌入
big = edv.bar(df, x="大区", y="销售额")
# 只取 2 列，dataRef 和体积都更小
small = edv.bar(df[["大区", "销售额"]], x="大区", y="销售额")
print(len(big.to_html()) / 1024 / 1024)     # 1.755
print(len(small.to_html()) / 1024 / 1024)   # 1.303
print(big.data["n"], len(big.data["cols"]))  # 5000 11
```

嵌入的是 `df` 的全部列（不超过 40 列时），不是只有 `x/y`。所以「先 `df[需要的列]` 再画图」是最省事的一刀；超过 40 列时库会优先保留角色列并打印警告。

## 4. max_rows：默认采样，不是截断

默认 `max_rows=2000000`（1.5.2 起；1.5.1 及以前是 200000）。超过时用 `np.linspace(0, n-1, max_rows)` 取**按行位置的均匀样本**（不是取前 20 万行，也不是随机抽样），并给出警告：

```python
import eazy_data_viz as edv
df = edv.sample_df(rows=5000)
c = edv.line(df, x="日期", y="销售额", max_rows=100)
print(c.data["n"], c.data["n_total"])   # 100 5000
print(c.warnings["warnings"][0])
# 数据 5000 行，超过 max_rows=100，已均匀采样 100 行用于绘图。
```

什么时候用 `max_rows=None`：需要看原始点分布（散点、箱线、明细表 `table`）且行数在万级以内。什么时候不要：折线/柱状只关心趋势和汇总，直接 `max_rows=5000` 甚至先 `groupby` 预聚合，文件从 20 MB 降到 1–2 MB。

均匀采样会保留整体形状和异常值密度，但会稀释「某个具体的极端点」；对箱线图的四分位影响很小，对 Top N 排名影响较大，排名类请先聚合。

## 5. 浏览器侧聚合：Python 只校验和打包

数据流是这样的：

1. `prepare()`：校验列、转 JSON 类型、按 `max_rows` 采样、把行数组塞进 `window.EAZY_DATA[dataRef]`；
2. 浏览器 `EazyViz.init()`：每张图用 `spec.roles` 声明「按哪列分组、聚合哪列、怎么聚合」，初始化时 `groupBy` 一次；
3. 点图例、下钻、联动：**只重跑前端 `groupBy`**，不会回头调用 Python；
4. 聚合结果交给 ECharts 画图。

因此「Python 生成快」不代表「打开快」：Python 只做 0.01–0.35 s 的打包（1.5.7 起向量化）；浏览器要解析 JSON 并对每张图各扫一遍数据。20 张图 × 20 万行 ≈ 400 万次行访问，第一次打开会明显卡；10 万行以上建议降到 10–20 张图或预聚合。

### 5.1 1.5.7：prepare 向量化（10~12 倍）+ 列缓存

1.5.6 及以前，`prepare()` 是**逐元素 Python lambda**（`Series.map(...)`）把每列转成
JSON 友好的 list；一列文本就是几十万次 Python 函数调用。1.5.7 改成整列向量化：

| 数据类型 | 现在怎么做 |
| --- | --- |
| 数值 | `Series.to_numpy()` + `np.round(vals, 4).tolist()`，NaN 用 `np.flatnonzero` 定位后置 `None` |
| 时间 | `pd.to_datetime` → `dt.strftime` → `pd.isna` 统一置 `None` |
| 布尔 | `np.where(filled, "是", "否")` |
| 分类文本 | `astype(str).tolist()`（只有出现超长文本 >120 字符时才逐条截断） |

同一份数据、同一个 8 图看板：

| 行数 | 1.5.6 build | 1.5.7 build | 提速 |
| --- | --- | --- | --- |
| 2,000 | 0.18 s | **0.04 s** | 4.5× |
| 20,000 | 0.97 s | **0.08 s** | 12× |
| 80,000 | 3.88 s | **0.34 s** | 11× |

另外加了**整列缓存**：同一份 df 在同一个进程里被画多张图时，第二张起直接复用
上一次转换好的列（键 = `id(df)` + 行数 + `max_rows` + 用到的列 + 首尾行指纹），
所以 `bar` + `line` + `sunburst` 共用一份 df 时只转一次。原地 `df["x"] = ...`
会被首尾行指纹发现并自动失效；也可以 `edv.clear_cache()` 手动清。

```python
print(edv.cache_info())      # {'entries': 3, 'cells': 22000}
edv.clear_cache()            # {'entries': 0, 'cells': 0}
```

**没有做多线程 / 多进程**：实测 6 线程 prepare 0.35 s，单线程反而 0.21 s（`astype(str)`
持有 GIL、线程调度纯亏）；多进程还要把整份 DataFrame pickle 过去，比它省下的时间更贵。
真正的并行加速在「读数据」那一层——用 `@edv.cached` 缓存，或把聚合下推到数据库。

## 6. 多图共用 df：dataRef 去重

`dataRef` 是「列 + 行 + 分类顺序」的 sha1，**同样内容只嵌一次**。同一个 df 画 12 张图，只多出 12 份 spec：

```python
import eazy_data_viz as edv
df = edv.sample_df(rows=1500)
c1 = edv.bar(df, x="大区", y="销售额")
c2 = edv.line(df, x="日期", y="利润")
print(c1.data_ref == c2.data_ref)   # True
print(c1.data_ref == df.copy().pipe(lambda d: edv.bar(d, x="大区", y="销售额")).data_ref)  # True
print(len(edv.dashboard(c1, c2).to_html()) / 1024 / 1024)  # 约 1.37，数据只嵌一次
```

实测：1500 行单图 1.370 MB；同 df 4 张图 1.373 MB；同 df 12 张图 1.379 MB；4 张图各自用不同 `sample_df(seed=...)` 生成 4 份数据时 1.868 MB。

想按维度拆图时，不要 `df[df.渠道=="直销"]` 复制 4 份再画（4 个 dataRef，数据被嵌 4 次），而是共用一份 df、用 `color="渠道"` 或 `filter` 列在图表内区分。

## 7. 单图 vs 页面首屏（实测）

本机 headless Chrome，`file://` 本地打开，计时到 `EazyViz.charts.length` 达标（含 ECharts 初始化）。冷启动 / 热启动各测一次，取范围：

| 页面 | 首次可用时间 |
| --- | --- |
| 单图，1,500 行 | 80–310 ms |
| 单图，5,000 行 | 240–260 ms |
| 看板 12 图，1,500 行 | 285–470 ms |
| 单图，200,000 行 | 0.8–1.1 s |

页面体积 1–2 MB 时首屏主要花在解析 JS 和数据；200k 行时数据解析占大头。深色模式切换会 `dispose()` 全部图表再重建，12 图页面实测 **约 122 ms**，图越多越慢——深色模式不是 CSS 换色，请当成一次全量重绘。

## 8. Streamlit：iframe 数量与高度

`Chart.show()` / `Dashboard.show()` 在 Streamlit 里就是一次 `st.components.v1.html(...)`，**每次调用产生一个 iframe**：

- 一个 Dashboard = 一个 iframe：所有联动、下钻、主题切换都在 iframe 内工作；
- 每张图单独 `.show()` = 多个 iframe：彼此看不到，联动必然失效，且每个 iframe 都内联一份 1.2 MB 运行库，页面会「重一次」。

高度由库自动计算（`render.page_height`）：单图 480 px、2×2 看板 936 px、带标题的 2×2 996 px、3 列 12 图 1908 px。自动高度不含 Streamlit 自己的 padding，通常不用手写。

```python
import eazy_data_viz as edv

df = edv.sample_df(rows=1500)
dash = edv.dashboard(
    edv.bar(df, x="大区", y="销售额"),
    edv.line(df, x="日期", y="销售额"),
    cols=2, title="经营看板",
)
dash.show()   # Streamlit 里自动用 components.html，高度自适应
```

如果一定要手写 `st.components.v1.html(dash.to_html(), height=996, scrolling=False)`，请用第 7 节的方法估算高度：每行卡片约 480 px、行间距 16 px、页头约 60 px。

## 9. 导出 PNG 与静态 HTML

- 单图右上角工具箱「保存为图片」由 ECharts 画布直接导出 PNG：不经过 Python、不重新请求数据，导出的是**当前筛选/下钻后的画面**。画质取决于浏览器 `devicePixelRatio`，高分屏更清晰。
- 想导出整页（含多个图表卡片），用浏览器打印/截图，或 `to_html()` 后交给无头浏览器截长图；库里没有「整页 PNG」接口。
- 发给别人离线看：`.save("a.html")` 默认 `inline=True` 全部内联；`inline=False` 会生成 `eazy_assets/` 目录，体积更小但必须连同目录一起拷贝。

## 10. 优化清单

| 动作 | 典型收益 |
| --- | --- |
| 只保留用到的列 | 11 列 → 2 列，5,000 行下 1.755 → 1.303 MB |
| 先 `groupby` 再画图 | 5,000 行 → 40 行，1.755 → 1.206 MB |
| `max_rows=5000`（或不传，别设 `None`） | 200k 行 23.2 MB → 1.75 MB |
| 排名类用 `top_n=10` | 类目从数百降到 10，前端聚合也更快 |
| 少画图：20 张变 4–6 张 | 首屏从数百 ms 降到百 ms 级；深色切换更快 |
| 共用 df + `color`/`link` | 避免同一批数据被嵌多份 |
| Streamlit 只放一个 Dashboard | iframe 从 N 个降到 1 个，运行库只加载一次 |
| 大屏明细用 `table(limit=100)` | 明细表最多嵌入 200 行 |

## 11. 复现测量

```python
import time
import eazy_data_viz as edv

for n in (1000, 5000, 50000, 200000):
    df = edv.sample_df(rows=n)
    t0 = time.time()
    html = edv.bar(df, x="大区", y="销售额").to_html()
    print("%7d 行  %6.3f MB  %.2fs" % (n, len(html) / 1024 / 1024, time.time() - t0))
```

同一段代码在不同机器上会因 CPU、Python 版本、浏览器而不同，看相对关系即可。

## 12. 相关阅读

- [09 · 数据准备](09-data-preparation.md) —— `max_rows`、采样、预聚合
- [12 · 常见问题](12-troubleshooting.md) —— 页面太大、首屏慢
- [14 · 扩展图表](14-extend-charts.md) —— 自定义图表也要遵守 `groupBy` 的代价模型
