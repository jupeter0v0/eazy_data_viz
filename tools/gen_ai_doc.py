# -*- coding: utf-8 -*-
"""生成给 AI / 人看的组件库文档。

输出：
    docs/eazy_catalog.json   —— 机器可读（函数签名、参数、类型、示例）
    docs/AI_GUIDE.md         —— 给 AI 的说明文档（Markdown）

用法：
    python tools/gen_ai_doc.py
"""
from __future__ import annotations

import inspect
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import eazy_data_viz  # noqa: E402

DOCS = os.path.join(ROOT, "docs")

# 图表分类（顺序即文档顺序）
GROUPS = [
    ("核心指标", ["kpi", "group_kpi", "gauge", "ring_progress", "bullet", "target", "progress"]),
    ("趋势", ["line", "area_pct", "combo", "sparkline", "theme_river", "gantt", "candlestick", "calendar"]),
    ("对比与排名", ["bar", "bar_pct", "waterfall", "pareto", "lollipop", "dumbbell", "slope",
                    "bump", "pictorial", "pyramid"]),
    ("结构与占比", ["pie", "rose", "funnel", "treemap", "sunburst", "tree", "tile"]),
    ("分布与关系", ["scatter", "histogram", "box", "heatmap", "matrix", "radar", "parallel",
                    "quadrant", "sankey", "graph", "trend"]),
    ("地图", ["geo_map", "beijing_map", "map_bubble", "map_flow"]),
    ("明细与文本", ["table", "wordcloud"]),
]

HELPERS = ["show", "dashboard", "Chart", "Dashboard", "sample_df", "help", "gallery",
           "set_palette", "palettes", "streamlit_dashboard", "streamlit_available"]

# 参数名的示例值（用 eazy_data_viz.sample_df() 的列）
EXAMPLE_LITERAL = {
    # 列名（字符串）
    "x": '"月份"', "y": '"销售额"', "y2": '"利润"', "color": '"产品"',
    "size": '"客户数"', "names": '"产品"', "values": '"销售额"', "value": '"销售额"',
    "column": '"销售额"', "source": '"渠道"', "target": '"产品"', "actual": '"销售额"',
    "period": '"期间"', "group": '"产品"', "spark": '"销售额"', "spark_x": '"月份"',
    "bar": '"销售额"', "line": '"利润"', "y1": '"上半年"', "y2_": '"下半年"',
    "date": '"日期"', "start": '"开始"', "end": '"结束"', "task": '"任务"',
    "label": '"全年销售额"', "title": '"我的看板"',
    # 结构 / 数值
    "path": '["大区", "省份"]', "dims": '["销售额", "订单数", "利润"]',
    "columns": '["月份", "大区", "销售额"]',
    "percent": "19.9", "max": "100", "min": "0",
    "agg": "'sum'", "fmt": "'compact'", "theme": "'light'",
    "delta": "0.128", "delta_label": '"同比"', "target_label": '"年度目标"',
    "unit": '"%"', "prefix": '"≈"', "hint": '"2024 全年 · 含税"',
    # 地图
    "region": '"省份"', "map": "'china'", "name_map": '{"广东": "广东省"}',
    "min_value": "0", "max_value": "100000", "zoom": "1.2",
}
COLUMN_PARAMS = set(EXAMPLE_LITERAL) - {"label", "title", "path", "dims", "columns",
                                        "percent", "max", "min", "agg", "fmt", "theme",
                                        "delta", "delta_label", "target_label",
                                        "unit", "prefix", "hint"}
SINGLE_VALUE_FUNCS = {"gauge", "ring_progress"}
POSITIONAL_SKIP = {"self", "cls", "kwargs"}


EXAMPLES = {
    "kpi": 'kpi(df, value="销售额", label="全年销售额", delta=0.128, target=2000000)',
    "group_kpi": 'group_kpi(df, names="大区", values="销售额", title="大区概况")',
    "combo": 'combo(df, x="月份", bar="销售额", line="利润")',
    "heatmap": 'heatmap(df, x="月份", y="大区", value="销售额")',
    "pie": 'pie(df, names="产品", values="销售额", donut=True)',
    "scatter": 'scatter(df, x="订单数", y="销售额", size="客户数")',
    "radar": 'radar(df, x="产品", y="销售额", color="大区")',
    "parallel": 'parallel(df, dims=["销售额", "订单数", "利润"])',
    "matrix": 'matrix(df, columns=["销售额", "订单数", "利润", "客户数"])',
    "table": 'table(df, columns=["月份", "大区", "销售额"], limit=10)',
    "wordcloud": 'wordcloud(df, names="城市", values="销售额", top_n=20)',
    "gauge": 'gauge(19.9, label="利润率", min=0, max=40, fmt="percent")',
    "ring_progress": 'ring_progress(78, label="年度目标达成率")',
    "slope": 'slope(df, x="月份", y="销售额", color="产品")',
    "treemap": 'treemap(df, path=["大区", "省份"], value="销售额")',
    "sunburst": 'sunburst(df, path=["大区", "省份"], value="销售额")',
    "sankey": 'sankey(df, path=["大区", "渠道", "产品"], value="销售额")',
    "column": 'column(金额="sum", 客户名称="unique")',
    "follow": 'follow()',
    "box": 'box(df, x="渠道", y="销售额")',
    "histogram": 'histogram(df, column="销售额", bins=24)',
    "area_pct": 'area_pct(df, x="月份", y="销售额", color="产品")',
    "bar_pct": 'bar_pct(df, x="月份", y="销售额", color="渠道")',
    "bar": 'bar(df, x="大区", y="销售额", color="渠道", stack=True)',
    "line": 'line(df, x="月份", y="销售额", color="产品", smooth=True)',
    "waterfall": 'waterfall(df, x="产品", y="销售额", total=True)',
    "progress": 'progress(df, x="大区", y="销售额")',
    "bullet": 'bullet(df, x="大区", actual="销售额", target_value=500000)',
    "target": 'target(df, x="大区", actual="销售额", target_value=500000)',
    "sparkline": 'sparkline(df, x="月份", y="销售额", group="渠道")',
    "theme_river": 'theme_river(df, x="月份", color="产品", value="销售额")',
    "calendar": 'calendar(df, date="日期", value="销售额")',
    "dumbbell": 'dumbbell(df, x="大区", y1="销售额", y2="利润")',
    "quadrant": 'quadrant(df, x="订单数", y="销售额", color="大区")',
    "trend": 'trend(df, x="客户数", y="利润", color="产品")',
    "geo_map": 'geo_map(df, region="省份", value="销售额")',
    "beijing_map": 'beijing_map(pd.DataFrame({"区": ["朝阳区", "海淀区"], '
                   '"销售额": [128, 142]}), region="区", value="销售额")',
    "map_bubble": 'map_bubble(df, region="城市", value="销售额")',
    "map_flow": 'map_flow(pd.DataFrame({"出发城市": ["北京市", "上海市", "广州市"], '
                '"到达城市": ["广州市", "成都市", "上海市"], "件数": [320, 280, 260]}), '
                'source="出发城市", target="到达城市", value="件数")',
    "gantt": 'gantt(pd.DataFrame({"任务": ["调研", "开发"], "开始": ["2024-01-01", "2024-02-01"], '
             '"结束": ["2024-02-01", "2024-05-01"], "部门": ["产品", "研发"]}), '
             'task="任务", start="开始", end="结束", color="部门")',
    "candlestick": 'candlestick(pd.DataFrame({"日期": ["2024-01-01", "2024-01-02"], '
                   '"开盘": [10.0, 10.6], "最高": [10.9, 11.2], "最低": [9.8, 10.2], '
                   '"收盘": [10.6, 10.7]}), date="日期", open="开盘", high="最高", '
                   'low="最低", close="收盘")',
}


def _example(name, sig):
    if name in EXAMPLES:
        return "eazy_data_viz." + EXAMPLES[name]
    parts = []
    for pname, p in sig.parameters.items():
        if pname in POSITIONAL_SKIP:
            continue
        required = (p.default is p.empty and
                    p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY))
        if pname == "data":
            parts.append("df")
            continue
        if not required:
            continue
        if pname in ("value", "percent") and (name in SINGLE_VALUE_FUNCS or pname == "percent"):
            parts.append("19.9")
            continue
        if pname in EXAMPLE_LITERAL:
            parts.append("%s=%s" % (pname, EXAMPLE_LITERAL[pname]))
            continue
        parts.append("%s=%s" % (pname, '"%s"' % pname if pname in COLUMN_PARAMS else "0"))
    return "eazy_data_viz.%s(%s)" % (name, ", ".join(parts))


def _jsonable_default(d):
    if d is inspect.Parameter.empty:
        return None
    if isinstance(d, (str, int, float, bool)) or d is None:
        return d
    return repr(d)


def describe(fn, name):
    sig = inspect.signature(fn)
    params = []
    for pname, p in sig.parameters.items():
        params.append({
            "name": pname,
            "kind": str(p.kind).replace("Parameter.", "").lower(),
            "default": _jsonable_default(p.default),
            "required": p.default is p.empty and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD),
        })
    doc = (inspect.getdoc(fn) or "").strip()
    summary = doc.split("\n\n")[0].replace("\n", " ") if doc else ""
    return {
        "name": name,
        "signature": "%s%s" % (name, str(sig)),
        "params": params,
        "summary": summary,
        "doc": doc,
        "example": _example(name, sig),
    }


def main():
    os.makedirs(DOCS, exist_ok=True)
    chart_index = {}
    for fname in dir(eazy_data_viz):
        if fname.startswith("_"):
            continue
        obj = getattr(eazy_data_viz, fname)
        if inspect.isfunction(obj) and fname not in HELPERS:
            try:
                chart_index[fname] = describe(obj, fname)
            except (TypeError, ValueError):
                pass

    groups = []
    used = set()
    for gname, names in GROUPS:
        items = [chart_index[n] for n in names if n in chart_index]
        used.update(i["name"] for i in items)
        groups.append({"group": gname, "charts": items})
    rest = [v for k, v in sorted(chart_index.items()) if k not in used]
    if rest:
        groups.append({"group": "其他", "charts": rest})

    helpers = {}
    for hname in HELPERS:
        obj = getattr(eazy_data_viz, hname, None)
        if obj is None:
            continue
        try:
            helpers[hname] = describe(obj, hname)
        except (TypeError, ValueError):
            pass
    palettes = []
    for pname in eazy_data_viz.palette.names():
        p = eazy_data_viz.palette.get(pname)
        palettes.append({k: p[k] for k in ("label", "desc", "best_for", "colors") if k in p})

    catalog = {
        "name": "eazy_data_viz",
        "version": getattr(eazy_data_viz, "__version__", "0"),
        "summary": "pandas → 单文件 HTML 交互图表库（经营驾驶舱场景，Material Design 3，45 种图表，"
                   "客户端下钻/联动，Streamlit 兼容）",
        "install": "pip install -e .   # 或构建 wheel: python -m pip wheel . --no-deps",
        "quickstart": [
            "import eazy_data_viz",
            "df = eazy_data_viz.sample_df()                 # 或你自己的 DataFrame",
            'eazy_data_viz.bar(df, x="大区", y="销售额").show()      # Notebook/脚本',
            'eazy_data_viz.dashboard(*charts, cols=2).save("dash.html")',
        ],
        "conventions": {
            "data": "第一参数永远是 pandas.DataFrame（除 gauge/ring_progress 这类单值图）",
            "columns": "x/y/color/names/values 等参数都传【列名字符串】，不要传 Series 或 JSON",
            "agg": ["sum", "mean", "count", "max", "min", "median"],
            "fmt": ["compact", "thousands", "raw", "percent", "currency"],
            "theme": ["light", "dark"],
            "return": "所有图表函数返回 eazy_data_viz.Chart（.to_html() / .save(path) / .show()）",
            "dashboard": "多图放同一页面才能联动：eazy_data_viz.dashboard(c1, c2, cols=2)",
            "drill": 'drill=["大区","省份"] 点击柱子逐级下钻',
            "link": 'link="g1" 同一组名的图点击后互相筛选',
        },
        "palettes": palettes,
        "default_palette": eazy_data_viz.palette.DEFAULT_PALETTE,
        "groups": groups,
        "helpers": helpers,
        "chart_types": sorted(chart_index),
    }
    jpath = os.path.join(DOCS, "eazy_catalog.json")
    with open(jpath, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=1)
    print("写出", jpath, os.path.getsize(jpath), "bytes")

    md_path = os.path.join(DOCS, "AI_GUIDE.md")
    with open(md_path, "w", encoding="utf-8") as f:
        write_markdown(f, catalog)
    print("写出", md_path, os.path.getsize(md_path), "bytes")


def write_markdown(f, cat):
    w = f.write
    w("# eazy_data_viz 组件库说明书（给 AI 用）\n\n")
    w("> 版本 %s · 机器可读版：`docs/eazy_catalog.json` · 人读版：`README.md`\n\n" % cat["version"])
    w("## 0. 一句话\n\n%s\n\n" % cat["summary"])
    w("## 1. 规则（先读这段，能避免 90% 的错误）\n\n")
    conv = cat["conventions"]
    w("| 事项 | 约定 |\n|---|---|\n")
    rows = [
        ("输入数据", conv["data"]),
        ("列参数", conv["columns"]),
        ("返回值", conv["return"]),
        ("聚合 agg", "`" + "` `".join(conv["agg"]) + "`"),
        ("格式 fmt", "`" + "` `".join(conv["fmt"]) + "`"),
        ("主题", "`light` / `dark`（页面级），配色见 palette"),
        ("多图联动", conv["dashboard"] + "；`link=\"g1\"` 同组联动"),
        ("下钻", conv["drill"]),
        ("配色库", "`Chart.palette('tableau')` 或 `dashboard(..., palette='morandi')`"),
        ("Streamlit", "`eazy_data_viz.dashboard(...).show()` 自动用 `st.components.v1.html`，必须给 height"),
    ]
    for a, b in rows:
        w("| %s | %s |\n" % (a, b.replace("|", "\\|")))
    w("\n")

    w("## 2. 最快上手\n\n```python\n")
    w("import eazy_data_viz\nimport pandas as pd\n\n")
    w("df = eazy_data_viz.sample_df()          # 演示数据；真实场景换成你的 DataFrame\n\n")
    w('# 单图：存成一个 HTML，双击就能看，可交互（缩放/图例/导出 PNG）\n')
    w('eazy_data_viz.bar(df, x="大区", y="销售额", color="渠道", top_n=8).save("bar.html")\n\n')
    w("# 看板：多图同页 → 才能联动\n")
    w('c1 = eazy_data_viz.line(df, x="月份", y="销售额", color="渠道", link="g1")\n')
    w('c2 = eazy_data_viz.bar(df, x="大区", y="销售额", color="产品", link="g1")\n')
    w('eazy_data_viz.dashboard(c1, c2, cols=2, title="经营看板").save("dash.html")\n')
    w("```\n\n")

    w("## 3. 配色库\n\n")
    w("默认 `google`（Material Design 3）。可用：\n\n")
    w("| 名字 | 风格 | 适合 |\n|---|---|---|\n")
    for p in cat["palettes"]:
        w("| `%s` | %s | %s |\n" % (p["label"], p["desc"], p.get("best_for", "")))
    w("\n```python\n")
    w('eazy_data_viz.bar(df, x="大区", y="销售额").palette("tableau").show()   # 单图换色\n')
    w('eazy_data_viz.dashboard(c1, c2, palette="morandi").save("x.html")      # 整页换色\n')
    w('eazy_data_viz.set_palette("carbon")                                     # 改全局默认\n')
    w("```\n\n")

    w("## 4. 图表函数（按场景分组，共 %d 个）\n\n" % len(cat["chart_types"]))
    for g in cat["groups"]:
        w("### %s\n\n" % g["group"])
        w("| 函数 | 签名 | 说明 |\n|---|---|---|\n")
        for c in g["charts"]:
            sig = c["signature"].replace("|", "\\|").replace("\n", " ")
            w("| `%s` | `%s` | %s |\n" % (c["name"], sig, c["summary"].replace("|", "\\|")))
        w("\n")
        for c in g["charts"]:
            if c["doc"] and len(c["doc"]) > 0:
                w("**`%s`** — %s\n\n" % (c["name"], c["doc"].split("\n")[0]))
                w("```python\n%s\n```\n\n" % c["example"])
    w("\n")

    w("## 5. 选图决策表\n\n")
    w("| 你想表达 | 用哪个 |\n|---|---|\n")
    decide = [
        ("一个总数 + 同比", "`kpi`"),
        ("一组总数（4~8 个）", "`group_kpi`"),
        ("完成率 / 目标达成", "`gauge` / `ring_progress` / `bullet` / `target` / `progress`"),
        ("随时间变化", "`line`（可 `area=True` / `step=True`）"),
        ("占比随时间变化", "`area_pct` / `bar_pct` / `theme_river`"),
        ("排名对比", "`bar`（`horizontal=True`） / `pareto` / `lollipop`"),
        ("两个时点变化", "`slope` / `dumbbell`"),
        ("排名随时间变化", "`bump`"),
        ("构成 / 占比", "`pie` / `rose` / `funnel` / `pyramid`"),
        ("层级构成", "`treemap` / `sunburst` / `tree`"),
        ("两变量关系 / 回归", "`scatter` / `trend` / `quadrant`"),
        ("分布", "`histogram` / `box`"),
        ("多变量对比", "`radar` / `parallel` / `heatmap` / `matrix`"),
        ("流转 / 关系", "`sankey` / `graph`"),
        ("项目排期", "`gantt`；股票走势 `candlestick`"),
        ("明细表 / 词云", "`table` / `wordcloud`"),
    ]
    for a, b in decide:
        w("| %s | %s |\n" % (a, b))
    w("\n")

    w("## 6. KPI 卡片\n\n")
    w("```python\n")
    w('eazy_data_viz.kpi(df, value="销售额", label="全年销售额", delta=0.128, delta_label="同比",\n')
    w('         target=2000000, spark="销售额", spark_x="月份", hint="2024 全年 · 含税",\n')
    w('         link="g1").show()\n')
    w("```\n\n")
    w("| 参数 | 作用 |\n|---|---|\n")
    w("| `data` / `value` / `agg` | 传 df + 列名（参与联动过滤）或直接传一个数字 |\n")
    w("| `label` / `hint` | 主标签 / 下方说明 |\n")
    w("| `fmt` / `unit` / `prefix` | 数值格式：compact/thousands/raw/percent/currency |\n")
    w("| `delta` / `delta_label` / `inverse` | 同比环比；`inverse=True` 时下降变绿（成本类指标） |\n")
    w("| `target` / `target_label` | 目标值 → 右上角徽标 + 达成率进度条 |\n")
    w("| `spark` / `spark_x` | 迷你走势线（按 spark_x 聚合 spark 列） |\n")
    w("| `accent` | 强调色序号（取当前配色的第 N 个颜色） |\n\n")

    w("## 7. 交互能力\n\n")
    w("- **下钻**：`drill=[\"大区\",\"省份\",\"城市\"]`，点击柱子/扇区逐级钻取，面包屑可返回；JS 内完成，不回调 Python。\n")
    w("- **联动**：同一 dashboard 内 `link=\"g1\"`，点击任意图的一个类目，其余同组图按该维度过滤，顶部出现筛选 chips，再点一次取消。\n")
    w("- **图例筛选 / 缩放 / 主题切换 / 导出 PNG**：ECharts 内置能力 + 右上角工具箱。\n")
    w("- **注意**：两个独立的 `components.html`（两个 iframe）之间无法联动，必须放在同一个 `dashboard` 页面里。\n\n")

    w("## 8. Streamlit\n\n")
    w("```python\n")
    w('import streamlit as st, eazy_data_viz\n')
    w("df = eazy_data_viz.sample_df()\n")
    w("charts = [eazy_data_viz.line(df, x='月份', y='销售额', link='g1'),\n")
    w("          eazy_data_viz.bar(df, x='大区', y='销售额', link='g1')]\n")
    w("page = eazy_data_viz.dashboard(*charts, cols=2, title='经营看板')\n")
    w("page.show()          # 内部调用 st.components.v1.html(..., height=page_height)\n")
    w("```\n\n")

    w("## 9. 文件结构 / spec 结构（需要深挖时看）\n\n")
    w("```\n")
    w("eazy_data_viz/\n")
    w("  __init__.py      # 对外 API\n")
    w("  chart.py         # 基础 13 种图 + _base_spec（组装 spec）\n")
    w("  charts_extra.py  # 32 种扩展图\n")
    w("  frame.py         # DataFrame → 紧凑记录（去重、采样、有序类目）\n")
    w("  render.py        # Material 3 页面/看板、CSS、脚本内联\n")
    w("  palette.py       # 7 套配色\n")
    w("  assets/eazy.js   # 运行时（聚合、option 构建、下钻/联动）\n")
    w("  assets/eazy_extra_*.js\n")
    w("```\n\n")
    w("页面 HTML 里 `window.EAZY_DATA` 存放去重后的数据（cols/rows/kinds/orders），\n")
    w("每张图只存 spec（type + roles + 样式），聚合在前端做——所以联动过滤是即时的、无需 Python 重算。\n\n")

    w("## 10. 常见错误对照\n\n")
    w("| 报错 | 原因 / 解决 |\n|---|---|\n")
    errs = [
        ("`列 'X' 需要是数值类型`", "该列是字符串但被当成数值角色（y/value/size）。改传数值列，或先 `df['X']=pd.to_numeric(...)`"),
        ("`列 'X' 不存在`", "列名拼写/前后空格；用 `print(df.columns.tolist())` 核对"),
        ("`不支持的下钻层级`", "drill 列表必须都出现在 DataFrame 里，且第一层通常等于 x"),
        ("图是空白", "数值列里有大量 NaN 或全为 0；检查 `df[col].isna().mean()`"),
        ("Streamlit 里图被裁掉", "必须传 height（`.show()` 已自动算，手写 `components.html` 时要自己给）"),
        ("跨图不联动", "两张图在同一个 `dashboard` 页面里且 `link` 相同"),
    ]
    for a, b in errs:
        w("| %s | %s |\n" % (a, b.replace("|", "\\|")))
    w("\n")


if __name__ == "__main__":
    main()
