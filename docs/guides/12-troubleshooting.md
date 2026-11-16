# 12 · 常见问题与错误对照

> 目标：遇到报错别猜，按「现象 → 原因 → 解决」对照表直接定位。所有修复代码都可直接运行。

## 快速定位

| 现象 | 先看这里 |
| --- | --- |
| 图是空白 / 只有卡片没有图形 | [2](#2-图表空白只有卡片没有图形)、[12](#12-离线或拷走-html-后图表空白) |
| 中文变成 `????` 或乱码 | [1](#1-中文乱码)、[15](#15-windows-路径与编码) |
| 列名相关异常 | [3](#3-typeerror列-x-需要是数值类型)、[4](#4-keyerror-列-y-不存在) |
| 时间/日期图报错 | [5](#5-不支持的时间类型) |
| 参数校验异常 | [6](#6-agg-只支持--)、[7](#7-fmt-只支持--)、[8](#8-xlim--ylim-用法错误) |
| 在 Streamlit / Jupyter 里显示不对 | [9](#9-streamlit-高度裁剪联动失效)、[10](#10-jupyter-不显示) |
| 文件太大 / 打开卡 | [11](#11-导出-html-体积大)、[16](#16-首屏慢行数过多) |
| 地图没颜色 / 区域没匹配 | [13](#13-地图区域没匹配上)、[14](#14-keyerror-maps) |

## 1. 中文乱码

**现象**：控制台打印 `UnicodeEncodeError`；或读 CSV 后列名/内容变成 `????`；或 Excel 打开导出的 CSV 乱码。
**原因**：CSV 的编码是 `gbk` 却按 UTF-8 读；Windows 控制台默认代码页不是 UTF-8。HTML 输出本身固定 UTF-8（`<meta charset="utf-8">`），不会因保存路径而乱码。

```python
csv = "examples/output/12-gbk.csv"
df.to_csv(csv, index=False, encoding="gbk")        # 给旧版 Excel 的 CSV
back = pd.read_csv(csv, encoding="gbk")            # 读回时必须指定同一编码
print(back.shape, back.columns[:3].tolist())
edv.bar(back, x="大区", y="销售额").save("examples/output/12-utf8.html")
```

控制台报错则在命令前加 `PYTHONIOENCODING=utf-8`（Windows CMD 用 `set PYTHONIOENCODING=utf-8`）。

## 2. 图表空白（只有卡片没有图形）

**现象**：HTML 能打开，卡片标题在、图形区一片白；或点选后图消失。
**原因**：① 筛选后 `0` 行；② `inline=False` 导致外部脚本 404；③ 数据里有 NaN 但全是空行；④ 浏览器 JS 报错（页面底部会显示红色 `INIT ERROR:`）。

```python
subset = df[df["大区"] == "华东"]        # 模拟联动/筛选后的数据
if subset.empty:
    subset = df.copy()
c = edv.bar(subset, x="大区", y="销售额")
print("嵌入行数", c.data["n"], "| dataRef", c.data_ref)
print("dataRef 已写入页面", c.data_ref in c.to_html())
```

若第二行打印 `False`，说明页面被二次加工过（手动拼 HTML 或 `inline=False`），改用 `to_html(inline=True)` 整页输出。

## 3. TypeError：列 'x' 需要是数值类型

**现象**：`TypeError: 列 '销售额文本' 需要是数值类型，但当前是文本类型（例如 '1,234.5'）。请先用 pd.to_numeric() 清洗，或换一列。`
**原因**：该参数在图表里承担数值角色（`y`、`value`、`size` 等），但列是 object/文本。含千分位逗号、单位、`￥` 的列不会自动转换。

```python
bad = df.assign(销售额文本=df["销售额"].round(2).astype(str))
try:
    edv.bar(bad, x="大区", y="销售额文本")
except TypeError as err:
    print(err)
clean = bad.assign(销售额=pd.to_numeric(bad["销售额文本"], errors="coerce"))
edv.bar(clean, x="大区", y="销售额").save("examples/output/12-numeric.html")
```

先 `str.replace` 去掉 `,`、`￥`、`%` 再做 `pd.to_numeric(errors="coerce")`；`coerce` 产生 NaN 的行会被数值聚合跳过。

## 4. KeyError：列 'y' 不存在

**现象**：`KeyError: "列 '销售' 不存在。当前可用的列有：日期, 月份, 大区, …"`
**原因**：列名拼错、多了空格、大小写不一致，或对 DataFrame 做过滤/透视后列名变了。

```python
print([c for c in df.columns if "销售" in c])
fixed = df.rename(columns=lambda c: str(c).strip())
try:
    edv.bar(fixed, x="大区", y="销售 额")
except KeyError as err:
    print(err)
edv.bar(fixed, x="大区", y="销售额").to_html()
```

透视之后记得 `reset_index()`，否则 `大区` 在索引里而不是列里。

## 5. 不支持的时间类型

**现象**：`TypeError: start（开始日期）列 '订单数' 需要是日期/时间类型，但当前是数值类型。请换一列。` 或 `ValueError: … 存在无法解析为日期的值`。
**原因**：`gantt` / `calendar` / `candlestick` 需要真实日期；Excel 常见的 `20240101` 整数、`2024/13/01` 非法值都会失败。`bar` / `line` 不会自动把日期字符串转成时间，只是当类别画。

```python
tasks = pd.DataFrame({
    "任务": ["A", "B"],
    "开始": [20240101, 20240105],        # Excel 常见的 8 位数字日期
    "结束": [20240103, 20240109],
})
for col in ("开始", "结束"):
    tasks[col] = pd.to_datetime(tasks[col].astype(str), format="%Y%m%d")
print(edv.gantt(tasks, task="任务", start="开始", end="结束").warnings)
```

清洗用 `pd.to_datetime(col, errors="coerce")`，再 `df[col].notna()` 过滤掉解析失败的行。

## 6. agg 只支持 ...

**现象**：`ValueError: agg='avg' 不支持，可选：sum, mean, count, max, min, median`（旧版提示为「agg 只支持 …」）。
**原因**：写成了 SQL 习惯的 `avg`、`average`；聚合方式只有 6 种。

```python
try:
    edv.bar(df, x="大区", y="销售额", agg="avg")
except ValueError as err:
    print(err)
g = df.groupby("大区", as_index=False)["销售额"].mean()   # 特殊口径先在 pandas 里算好
edv.bar(g, x="大区", y="销售额", agg="sum").to_html()
```

`count` 不需要数值列，常用来「按行数/订单数计数」；`median` 用于抗极值。

## 7. fmt 只支持 ...

**现象**：`ValueError: fmt='money' 不支持，可选：compact, thousands, raw, percent, currency`（旧版提示为「fmt 只支持 …」）。
**原因**：只接受 5 种格式键。`percent` 只是给数字加 `%`，不会乘 100；比率列请自己 `* 100`。

```python
try:
    edv.pie(df, names="渠道", values="销售额", fmt="money")
except ValueError as err:
    print(err)
print(edv.FORMATS)
edv.pie(df, names="渠道", values="销售额", fmt="thousands").to_html()
```

## 8. xlim / ylim 用法错误

**现象**：`ValueError: ylim 需要是 (最小值, 最大值) 两元组，例如 ylim=(0, 100)`。
**原因**：传了单个数字、三个元素，或字符串 `"0,100"`。允许列表、允许 `None` 占位（只限一端），写反了会自动交换。

```python
c = edv.bar(df, x="大区", y="销售额", ylim=(0, 300000))
print(c.spec["ylim"])
print(edv.bar(df, x="大区", y="销售额", xlim=(2, 0)).spec["xlim"])  # 写反自动交换
print(edv.bar(df, x="大区", y="销售额", ylim=(None, 300000)).spec["ylim"])
```

## 9. Streamlit 高度裁剪、联动失效

**现象**：图只显示上半截，需要滚动；或几组图点选后互不影响。
**原因**：`st.components.v1.html` 的 iframe 高度是写死的，不会自适应；每调一次 `components.html` 就是一个独立 iframe，iframe 之间无法联动。解决办法是**所有要联动的图放进同一个 dashboard，一次渲染**。

```python
import streamlit.components.v1 as components
import eazy_data_viz as edv

def render(dash):
    html = dash.to_html(inline=True)
    components.html(html, height=900, scrolling=False)   # 高度显式给足

cards = [edv.kpi(df, value="销售额", link="g1"),
         edv.bar(df, x="大区", y="销售额", link="g1"),
         edv.line(df, x="日期", y="销售额", link="g1")]
render(edv.dashboard(*cards, cols=2, title="经营看板"))
```

高度可按图数估算：单图约 `480`，`cols=2` 每行约 `460`，再加上头部 60；或直接用 `eazy_data_viz.render.page_height(cards, cols=2, has_header=True)`。

## 10. Jupyter 不显示

**现象**：Notebook 里只输出了 `<eazy_data_viz.Chart …>` 或什么都没有。
**原因**：Chart 只在作为**单元格最后一个表达式**时通过 `_repr_html_` 渲染；赋给变量后不会自动显示。

```python
c = edv.bar(df, x="大区", y="销售额")
try:
    from IPython.display import display
    display(c)              # Notebook：单元格内显式渲染
except ImportError:
    print(c.show())         # 纯脚本：临时 HTML + 打印路径
```

Notebook 里图表太大被裁剪时，可在单元格里直接 `c.show()`；它走 `IPython.display.HTML`，不受 iframe 高度限制。

## 11. 导出 HTML 体积大

**现象**：单图 20 MB+，微信/邮件发不出去。
**原因**：数据行全部内联。基线约 1.2 MB（ECharts 已内联），之后每 1 万行 11 列约 +0.5–1 MB；20 万行约 23 MB。

```python
big = edv.sample_df(rows=50000)
c = edv.bar(big, x="日期", y="销售额", max_rows=10000)   # 只嵌 1 万行（均匀采样）
print(c.warnings)
print("HTML %.2f MB" % (len(c.to_html()) / 1024.0 / 1024.0))
```

再配合只保留需要的列（`big[["日期", "销售额", "大区"]]`）或先在 pandas 里聚合，通常能压到 2 MB 内。

## 12. 离线或拷走 HTML 后图表空白

**现象**：本机正常，发给别人/open 到内网后空白；浏览器 Network 面板里脚本 404。
**原因**：用了 `to_html(inline=False)`，页面引用 `eazy_assets/xxx.js` 相对路径，但只拷了 HTML 没拷资产。默认 `inline=True` 会把 ECharts、地图 GeoJSON 全部内联，完全离线可用。

```python
c = edv.bar(df, x="大区", y="销售额")
html = c.to_html(inline=True)       # 默认就是内联；显式写出来避免误改
print("内联 ECharts：", "echarts" in html.lower(),
      "| 体积 %.2f MB" % (len(html) / 1024.0 / 1024.0))
```

必须用外链模式时，把包内 `eazy_data_viz/assets/` 一起发布，并让 `eazy_assets/` 与 HTML 同级。

## 13. 地图区域没匹配上

**现象**：省份地图大部分是灰色「无数据」，只有个别省份着色；城市气泡不出现。
**原因**：区域名与内置 GeoJSON 的 `properties.name` 不一致（如「广东省」对「广东」），或把城市名传给了省级地图。`geo_map` / `map_bubble` 会自动去后缀，但不会把城市升格成省。

```python
from eazy_data_viz.maps import normalize_region
print(normalize_region("广东省"), normalize_region("内蒙古自治区"))
alias = df.assign(区域=df["省份"].map({"上海": "上海市"}))
edv.geo_map(alias, region="区域", value="销售额",
            name_map={"沪": "上海"}).save("examples/output/12-map.html")
```

城市级用 `map_bubble(region="城市")`（走内置城市坐标表），省级用 `geo_map`；业务别名统一走 `name_map`。自定义 GeoJSON 当前不支持。

## 14. KeyError: 'maps'

**现象**：旧版本页面初始化报 `KeyError: 'maps'`，整页图表不渲染。
**原因**：0.x 早期版本在**没有地图**的页面上仍去读地图配置键。1.0.0 已修复：`render._map_payload()` 只收集实际用到的地图，没有地图时返回 `{}`，前端用 `window.EAZY_MAPS || {}` 兜底。若升级后仍报，通常是手改过页面脚本或用了旧的 `gallery.html` 缓存。

```python
c = edv.geo_map(df, region="省份", value="销售额")
html = c.to_html()
print("地图：", c.spec["map"], "| GeoJSON 已内联：", "window.EAZY_MAPS" in html)
```

升级到 1.0.0 后重新 `save()` 生成页面即可；不要在新页面上手工删 `window.EAZY_MAPS` 那行。

## 15. Windows 路径与编码

**现象**：`save(r"C:\new\table.html")` 报目录不存在，或文件写到奇怪的位置；中文文件名打不开。
**原因**：`\n`、`\t` 被 Python 当转义符；`save()` 会自动建目录，但不会猜你想要的目录。HTML 内部始终 UTF-8，文件名建议中文 + `.html` 没问题。

```python
path = r"examples\output\12-windows.html"     # 原始字符串：避免 \t \n 转义
edv.bar(df, x="大区", y="销售额").save(path)
print(path)
print(edv.bar(df, x="大区", y="销售额").save("examples/output/12-forward.html"))
```

路径统一用 `/`（Windows 也认）或 `r"..."`；从 Excel 复制的路径常带不可见空格，先 `.strip()`。

## 16. 首屏慢、行数过多

**现象**：浏览器打开要等好几秒，拖动/悬浮卡顿；Python 侧 `to_html()` 也要 1–3 秒。
**原因**：200k 行 × 多列全部内联，前端每次交互都对全量行聚合；一页放几十上百张图也会拖慢初始化。

```python
c = edv.bar(df, x="大区", y="销售额", max_rows=2000)   # 最多嵌 2000 行（均匀采样）
dash = edv.dashboard(edv.kpi(df, value="销售额"), c, cols=2)
html = dash.to_html()
print(c.warnings, "| %.2f MB" % (len(html) / 1024.0 / 1024.0))
```

优化顺序：**先聚合（pandas groupby 后再画）→ 减少列（只保留用到的）→ 设 `max_rows` → 一页不超过 20 张图**。数据量大时优先在 Python 里把明细聚合到「图表需要的粒度」，而不是把 20 万行明细塞进浏览器。
