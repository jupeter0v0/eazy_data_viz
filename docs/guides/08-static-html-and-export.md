# 08 · 静态 HTML 与导出：一个文件，哪里都能开

eazy_data_viz 的交付物本质上就是**一个自包含的 HTML 文件**：ECharts、运行时代码、
数据、样式全部内联，双击就能看，不依赖 CDN、不需要 Python 环境。
这一篇讲清它由什么构成、`to_html/save/show` 的差异、怎么把体积压下去，
以及嵌进现有网页/报表系统/Notebook 的正确姿势。

- **适用人群**：需要把看板交付给业务方、嵌进内部系统、或归档留存的工程师/分析师。
- **前置条件**：读过 [02 · 五分钟上手](02-quickstart.md)；本篇数字在 Python 3.8.10 +
  pandas 2.0.3 + eazy_data_viz 1.0.0 上实测。

## 0. 三个 API，一张表

| API | 返回 | 用途 | 是否落盘 |
| --- | --- | --- | --- |
| `chart.to_html()` / `page.to_html()` | `str`（完整 HTML 文档） | 交给 Web 框架、写自己的响应、做字符串处理 | 否 |
| `chart.save(path)` / `page.save(path)` | 绝对路径 `str` | 交付文件、归档 | 是 |
| `chart.show()` / `page.show()` | 自身 | 交互式环境自适应显示 | 脚本分支会写临时文件 |

```python
import os
import eazy_data_viz as edv

os.makedirs("examples/output", exist_ok=True)
df = edv.sample_df()
chart = edv.bar(df, x="大区", y="销售额")

html = chart.to_html()                      # str，可直接 len()
path = chart.save("examples/output/one.html")
print(type(html).__name__, len(html))
print(path, os.path.exists(path), os.path.getsize(path))
```

```text
str 1382003
F:\deepseek\eazy_data_viz\examples\output\one.html True 1442994
```

**`len(html)` 与 `os.path.getsize(path)` 不相等是正常的**：`to_html()` 返回的是字符数，
`save()` 按 UTF-8 写盘，中文字符占 3 字节，文件通常比字符数大 4%~5%。

### `show()` 到底做了什么

```python
chart.show(open_browser=False)
```

在普通脚本里输出：

```text
[eazy_data_viz] 已生成图表：C:\Users\<你>\AppData\Local\Temp\eazy_xxxx\chart.html
```

`show()` 按运行环境自动分流：

| 环境 | 行为 |
| --- | --- |
| Streamlit | `st.components.v1.html(html, height=page_height(...), scrolling=False)` |
| Jupyter / IPython | `IPython.display.HTML(html)` |
| 普通脚本 | 写临时 HTML 并打印路径；标准输出是 tty 时自动开浏览器 |

**交付/归档永远用 `save()`，不要用 `show()` 的临时文件**——它在系统临时目录里，会被清理。

## 1. 单文件里装了什么

以“2 图 + 标题”的页面为例（实测字符数）：

| 组成 | 字符量 | 说明 |
| --- | --- | --- |
| `echarts.min.js` | 1,030,855 | ECharts 5 运行时，固定成本，约占 75% |
| `eazy.js` | 67,014 | 渲染、下钻、联动、主题核心 |
| `eazy_map.js` | 43,274 | 地图扩展（按需加载进页面） |
| `eazy_extra_a.js` | 50,717 | 扩展图 A 组 builder |
| `eazy_extra_b.js` | 38,888 | 扩展图 B 组 builder |
| `eazy_extra_main.js` | 8,908 | 扩展图入口 |
| `eazy_extra_html.js` | 9,209 | KPI/表格/进度等 HTML 组件 |
| CSS | 12,160 | Material Design 3 变量与卡片样式 |
| 数据 JSON | 约 110,847 | 1500 行 × 11 列（紧凑 JSON） |
| 页面 spec JSON | 约 863 | 每张图的配置 |
| **合计** | **约 1,382,970 字符** | 写盘约 1,437,964 字节；gzip 后约 412 KB |

关键结论：

- **固定成本 ≈ 1.24 MB**（ECharts + 全部 JS），无论画 1 张还是 20 张图都要付；
- **增量成本很小**：第二张图起只增加 spec 与（同数据源的）零行数据；
- 数据只嵌**一次**：所有图共用同一个 `dataRef` 时，`window.EAZY_DATA` 里只有一份；
- 页面里没有 CDN/外链字体：`<script src="http...">` 数为 0，
  HTML 中出现的少量 `http://` 是 ECharts 的 Apache License 注释与 XML 命名空间，不会发起网络请求。

```python
# 自查：是不是真的没有外链脚本
import re
html = chart.to_html()
print("外部脚本:", re.findall(r'<script[^>]+src="https?://', html))   # []
print("内联 ECharts:", "Apache License" in html and "echarts" in html[:200000].lower())
```

```text
外部脚本: []
内联 ECharts: True
```

## 2. `to_html()`：拿字符串自己处理

`to_html()` 返回完整文档（`<!DOCTYPE html>...`），适合：

- Flask/FastAPI 直接返回：`return HTMLResponse(page.to_html())`；
- 写进模板变量、对象的 `__str__`；
- 二次字符串处理（注意：这是**不推荐但可行**的定制方式）。

```python
from eazy_data_viz import render as edv_render

page = edv.dashboard(
    edv.bar(df, x="大区", y="销售额"),
    edv.pie(df, names="产品", values="销售额"),
    cols=2, title="销售总览",
)
raw = page.to_html()
print("文档开头:", raw[:60].replace("\n", " "))
print("字符数:", len(raw), "| 图表数:", len(page.charts))
print("页面高度估算:", edv_render.page_height(page.charts, cols=2, has_header=True))
```

```text
文档开头: <!DOCTYPE html> <html lang="zh-CN" data-theme="light" data-palette="google">
字符数: 1383357 | 图表数: 2
页面高度估算: 540
```

`inline` 参数只在需要拆分资源时传：`page.to_html(inline=False)` 生成的 HTML 只含
`<script src="eazy_assets/xxx.js">`，**不会自动复制资源文件**——复制是 `save()` 的事。

## 3. `save()`：正确交付文件

```python
p1 = page.save("examples/output/report/sales.html")
print(p1, os.path.getsize(p1))
```

- 自动创建不存在的目录（`report/` 不用提前建）；
- 固定 UTF-8 编码，文件里 `<meta charset="utf-8">`；
- 返回**绝对路径**，方便日志打印或后续打开；
- 同名覆盖，不做备份。

### 3.1 `inline=False`：拆出公共资源

当你要交付**很多个页面**时，每个页面重复 1.24 MB JS 很浪费。`inline=False` 把 JS 拆到
同目录的 `eazy_assets/`，HTML 只剩样式+数据+卡片：

```python
p2 = page.save("examples/output/report_split/page.html", inline=False)
print("HTML 大小:", os.path.getsize(p2))
print("资源目录:", sorted(os.listdir("examples/output/report_split/eazy_assets")))
```

```text
HTML 大小: 142646
资源目录: ['eazy.js', 'eazy_extra_a.js', 'eazy_extra_b.js', 'eazy_extra_html.js',
          'eazy_extra_main.js', 'eazy_map.js', 'echarts.min.js', 'maps']
```

代价：

| 方式 | 单页体积 | 交付形态 | 适用 |
| --- | --- | --- | --- |
| `inline=True`（默认） | 1.3~1.5 MB | **单文件**，可单独发走 | 邮件附件以外的任何场景首选 |
| `inline=False` | 约 140 KB + 公共资源 | **目录**，必须整体拷贝/部署 | 多页站点、内网静态服务器 |

**`inline=False` 的页面离开 `eazy_assets/` 目录就白屏**（控制台会报 404/`EazyViz is not defined`）。
部署到 Nginx 时把 `eazy_assets/` 放在 HTML 同级即可；不要只发 HTML 文件。

### 3.2 目录交付示例

```python
import shutil

target = "examples/output/deliver"
shutil.rmtree(target, ignore_errors=True)
p = page.save(os.path.join(target, "index.html"))
print("交付文件:", os.path.relpath(p))
```

单文件方式下 `deliver/` 里只有 `index.html`，压缩成 zip 发给业务方即可。

## 4. 数据去重：为什么 20 张图不重复存 20 份数据

`Chart` 在 Python 侧就把 DataFrame 变成了 `(columns, rows, kinds)` 结构，并算出指纹：

```text
data_ref = "d" + sha1(cols+rows+orders)[:12]
```

`build_page()` 遍历所有图，**同一 `data_ref` 只嵌入一次**：

```python
import re

c1 = edv.bar(df, x="大区", y="销售额")
c2 = edv.line(df, x="日期", y="销售额")     # 同一个 df，列顺序一致 → 同 ref
c3 = edv.pie(df[df["大区"] == "华东"], names="产品", values="销售额")  # 不同数据 → 不同 ref

page = edv.dashboard(c1, c2, c3, cols=2)
html = page.to_html()
refs = set(re.findall(r'"(d[0-9a-f]{12})"', html))
print("c1 与 c2 同 ref:", c1.data_ref == c2.data_ref)
print("c1 与 c3 同 ref:", c1.data_ref == c3.data_ref)
print("页面内嵌数据份数:", len(refs))
```

```text
c1 与 c2 同 ref: True
c1 与 c3 同 ref: False
页面内嵌数据份数: 2
```

注意两点：

1. **列顺序参与指纹**。同一个 df 先 `df[["日期","销售额","大区"]]` 再画图，ref 会不同，
   数据会再嵌一份；多图共用数据时保持列顺序一致。
2. **每张图各自采样**。某张图 `max_rows=500` 时它自己那份数据是 500 行，
   和别的图不再共享 ref，属于预期。

```python
# 反例：同一份数据换了列顺序 → 多嵌一份
c4 = edv.bar(df[["大区", "销售额", "产品"]], x="大区", y="销售额")
print("ref 是否相同:", c1.data_ref == c4.data_ref)   # False
```

## 5. 体积优化：从 1.4 MB 到多少

按收益从大到小：

| 手段 | 效果 | 代价 |
| --- | --- | --- |
| 用 `inline=False` 拆公共 JS | 每页从 ~1.4 MB 降到 ~140 KB（多页场景总量大降） | 必须连目录一起交付 |
| 开 gzip / brotli（服务器或反代） | 约 412 KB → 再压缩到 ~100 KB 级 | 需要服务端支持；`file://` 打开无效 |
| 降 `max_rows` | 数据 JSON 线性下降（1500 行≈110 KB，占总量 8%） | 图表可能被采样，精度下降 |
| 减少图表数 / 拆页 | 每图只加 spec（约几百字节） | 信息密度下降 |
| `table(limit=...)` 控制行数 | 表格最多嵌 200 行 | 明细变少 |
| 预聚合后再画 | 常是最大收益：100 万行明细聚成 500 行 | 丢失明细，需在 Python 侧先聚合 |

```python
big = edv.sample_df(rows=30000)
small = edv.sample_df()
p_big = edv.dashboard(edv.bar(big, x="日期", y="销售额"), cols=1, title="3 万行")
p_small = edv.dashboard(edv.bar(small, x="日期", y="销售额"), cols=1, title="1500 行")
print("3 万行:", len(p_big.to_html()), "| 1500 行:", len(p_small.to_html()))
```

```text
3 万行: 1512xxx | 1500 行: 1381xxx
```

（`max_rows` 默认 200000，3 万行全部嵌入，所以差异是真实数据量；
超过 20 万行会被自动均匀采样，体积不再线性增长。）

**压缩前先问一句：这份 HTML 是给人看，还是给机器归档？**
给人看：单文件 + 内网 gzip 足够；给归档：`save()` 一份单文件最省心。

## 6. 嵌进现有网页 / 报表系统

### 6.1 推荐：`<iframe>`

静态 HTML 是完整文档，直接塞进 `<div>` 会因为 `innerHTML` 不执行 `<script>` 而白屏。
正确做法是 iframe：

```html
<iframe src="/reports/sales.html"
        style="width:100%;height:800px;border:0;border-radius:8px"
        title="销售看板"></iframe>
```

- `height` 必须给足：iframe 不会自动长高，给少了会出内部滚动条；
  用 Python 侧 `page_height(...)` 算出来再写死，或前端按固定比例；
- 同源策略：iframe 内的下钻/联动在自己的文档里工作，**不要跨 iframe 期待联动**（06 篇第 8 节）；
- `file://` 打开本机 HTML 可以，但被嵌进**远程页面**时浏览器会拦 `file://`，需走 Web 服务器。

### 6.2 服务端直接返回 HTML

```python
# Flask 示例（伪代码，按你项目框架调整）
from flask import Response

@app.route("/sales")
def sales():
    return Response(page.to_html(), mimetype="text/html")
```

这样浏览器地址栏就是一个独立页面，交互、缩放、PNG 导出全部可用，最省事。

### 6.3 报表系统 / 低代码平台

| 平台能力 | 做法 |
| --- | --- |
| 支持 iframe / 外链页面 | 挂 HTML 的 URL（推荐） |
| 只支持上传 HTML 附件 | 上传 `inline=True` 单文件 |
| 支持自定义 HTML 片段 | 用 iframe 包裹，不要直接内联 script |
| 只支持图片 | 浏览器里点“保存图片”，或改用 PNG 交付 |

### 6.4 邮件：基本不要指望

邮件客户端普遍**禁用 JavaScript**、剥离 `script/style`，把 HTML 看板塞进正文必然降级。
要发邮件就附 **PNG 截图**，或附 HTML 文件让收件人用浏览器打开（多数客户端能当附件）。

## 7. 在 Notebook 里显示

`Chart`/`Dashboard` 都实现了 `_repr_html_`，Jupyter 里直接写变量名就会尝试渲染：

```python
chart = edv.bar(df, x="大区", y="销售额")
chart            # 触发 _repr_html_
```

也可以显式：

```python
from IPython.display import display

display(edv.HTML(page.to_html()))   # 等价于 page.show() 的 Notebook 分支
```

注意：

- 渲染依赖执行内联 `<script>`。**JupyterLab / 部分 VS Code Notebook 会出于安全限制不执行
  HTML 输出里的脚本**，表现为空白或只有标题；这是前端限制，不是图表库报错。
- 遇到空白：改用 `page.save("tmp.html")` 后浏览器打开；或用 `IPython.display.IFrame`
  指向保存好的文件路径（需要环境允许 `file://`）。
- Notebook 适合探索，不适合交付；正式交付用 `save()`。

## 8. 一次导出多页

常见需求：“每个大区一份 HTML”。循环即可，注意**每页都是独立完整文档**：

```python
import os

out = "examples/output/by_region"
os.makedirs(out, exist_ok=True)
for region in sorted(df["大区"].unique()):
    sub = df[df["大区"] == region]
    page = edv.dashboard(
        edv.kpi(sub, value="销售额", label="销售额合计"),
        edv.bar(sub, x="省份", y="销售额"),
        edv.line(sub, x="日期", y="销售额"),
        edv.pie(sub, names="产品", values="销售额"),
        cols=2, title="%s · 销售看板" % region,
    )
    path = page.save(os.path.join(out, "%s.html" % region))
    print(region, os.path.getsize(path), "bytes")
```

```text
华东 1440xxx bytes
华北 1438xxx bytes
华南 1439xxx bytes
西南 1441xxx bytes
```

多页场景建议 `inline=False` + 公共 `eazy_assets/`，否则每个文件都背 1.24 MB JS。

如果只是“一页里分多个区域”，不要拆文件，用 `section` 分区即可（03 篇）：

```python
cards = []
for region in sorted(df["大区"].unique()):
    sub = df[df["大区"] == region]
    c = edv.bar(sub, x="省份", y="销售额", title="%s 省份销售额" % region)
    c.spec["section"] = region        # 非 bar/line/kpi 的图用这种方式补分区
    cards.append(c)
edv.dashboard(cards, cols=2, title="各大区对比").save("examples/output/regions.html")
```

## 9. 常见问题

**Q1：发给别人打开是空白？**
按顺序排查：文件是否完整（大小 >1 MB 的才是内联版）；控制台是否有 `EazyViz is not defined`
（多半是 `inline=False` 丢了 `eazy_assets/`）；页面里是否有 `#eazy-js-error`
（JS 初始化异常，见 12 篇）。

**Q2：能去掉右下角/右上角的按钮吗？**
工具箱是 ECharts 配置的一部分，当前没有 Python 开关；如需定制走 14 篇的 JS 扩展。

**Q3：HTML 里能看到我的原始数据吗？**
能。数据是明文 JSON 内嵌的，**不要交付含敏感字段的数据**。正确做法是在 Python 里
只保留需要的列（`df[cols]`）再画图。

**Q4：为什么 gzip 后小这么多？**
JS 与 JSON 的重复度极高，gzip 压缩比通常 3~4 倍。生产环境务必开 gzip/brotli。

**Q5：`to_html()` 的字符串能直接写进数据库/邮件模板吗？**
技术上可以，但要保证接收端执行脚本；SQL 字段长度和邮件模板都会截断，不推荐。

## 下一篇

数据是图表的地基。列类型、排序、缺失值、聚合方式任何一样不对，
图要么报错要么“看起来对但其实错”：[09 · 数据准备](09-data-preparation.md)。
