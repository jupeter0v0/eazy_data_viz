# -*- coding: utf-8 -*-
"""eazy_data_viz 冒烟单测（不依赖 pytest，直接 python tests/test_eazy_data_viz.py）。"""
import os
import tempfile
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import eazy_data_viz  # noqa: E402
from eazy_data_viz import chart as pchart  # noqa: E402

DF = eazy_data_viz.sample_df(rows=600, seed=7)
PASS, FAIL = [], []


def check(name, fn):
    try:
        fn()
        PASS.append(name)
    except Exception:
        FAIL.append((name, traceback.format_exc()))


def _spec(chart):
    return chart.spec


def _has_data(spec):
    assert spec["dataRef"], "dataRef 为空"
    assert spec["type"], "type 为空"


# ---------------------------------------------------------------- 14 种图
def t_bar():
    s = _spec(eazy_data_viz.bar(DF, x="大区", y="销售额"))
    _has_data(s)
    assert s["roles"]["x"] == "大区" and s["roles"]["y"] == "销售额"
    assert s["sort"] == "desc"
    assert eazy_data_viz.bar(DF, x="大区").spec["roles"]["y"] is None  # 只给 x → 计数


def t_bar_horizontal():
    s = _spec(eazy_data_viz.bar(DF, x="产品", y="销售额", horizontal=True, stack="季度" if "季度" in DF else None))
    assert s["horizontal"] is True


def t_line():
    s = _spec(eazy_data_viz.line(DF, x="月份", y="销售额"))
    assert s["sort"] == "x", "有序类目 / 时间列应按时序排"
    assert _spec(eazy_data_viz.line(DF, x="大区", y="销售额", smooth=True, area=False))["smooth"] is True


def t_area():
    s = _spec(eazy_data_viz.area(DF, x="月份", y="订单数"))
    assert s["area"] is True and s["type"] == "line"


def t_pie():
    s = _spec(eazy_data_viz.pie(DF, names="产品", values="销售额"))
    assert s["type"] == "pie" and s["sort"] == "desc"
    assert _spec(eazy_data_viz.pie(DF, names="渠道"))["roles"]["value"] is None  # 计数饼图


def t_scatter():
    s = _spec(eazy_data_viz.scatter(DF, x="订单数", y="销售额", size="客户数"))
    assert s["roles"]["size"] == "客户数"


def t_histogram():
    s = _spec(eazy_data_viz.histogram(DF, column="销售额", bins=20))
    assert s["bins"] == 20


def t_heatmap():
    s = _spec(eazy_data_viz.heatmap(DF, x="月份", y="大区", value="销售额"))
    assert s["labels"] is False
    assert _spec(eazy_data_viz.heatmap(DF, x="月份", y="大区", value="销售额", labels=True))["labels"] is True


def t_box():
    s = _spec(eazy_data_viz.box(DF, y="销售额"))
    assert s["type"] == "box"
    _spec(eazy_data_viz.box(DF, x="渠道", y="销售额"))


def t_funnel():
    s = _spec(eazy_data_viz.funnel(DF, names="渠道", values="销售额"))
    assert s["type"] == "funnel"


def t_treemap():
    s = _spec(eazy_data_viz.treemap(DF, path=["大区", "产品"], value="销售额"))
    assert s["roles"]["path"] == ["大区", "产品"]


def t_gauge():
    s = _spec(eazy_data_viz.gauge(72.5, label="完成率", max=100, unit="%"))
    assert s["type"] == "gauge" and s["max"] == 100


def t_kpi():
    s = _spec(eazy_data_viz.kpi(DF, value="销售额", agg="sum", label="总销售额"))
    assert s["type"] == "kpi"


def t_combo():
    s = _spec(eazy_data_viz.combo(DF, x="月份", bar="销售额", line="利润"))
    assert s["roles"]["y"] == "销售额" and s["roles"]["y2"] == "利润"


# ------------------------------------------------------- 下钻 / 联动参数
def t_drill():
    s = _spec(eazy_data_viz.bar(DF, x="大区", y="销售额", drill=["产品", "渠道"]))
    assert s["drill"] == ["大区", "产品", "渠道"], "x 应被自动补为下钻第一层"
    s2 = _spec(eazy_data_viz.line(DF, x="大区", y="销售额", drill=["大区", "省份"]))
    assert s2["drill"] == ["大区", "省份"]


def t_link():
    a = eazy_data_viz.bar(DF, x="大区", y="销售额", link="d1")
    b = eazy_data_viz.line(DF, x="月份", y="销售额", link="d1")
    assert a.spec["link"] == "d1" and b.spec["link"] == "d1"
    page = eazy_data_viz.dashboard([a, b], cols=2, title="联动")
    html = page.to_html()
    assert html.count('"link": "d1"') >= 2


# ------------------------------------------------------------ 参数校验
def t_errors():
    for fn, exc in [
        (lambda: eazy_data_viz.bar(DF, x="不存在的列"), KeyError),
        (lambda: eazy_data_viz.bar(DF, x="大区", y="产品"), TypeError),
        (lambda: eazy_data_viz.bar(DF, x="大区", y="销售额", agg="avg"), ValueError),
        (lambda: eazy_data_viz.bar(DF, x="大区", y="销售额", fmt="usd"), ValueError),
        (lambda: eazy_data_viz.bar(DF, x="大区", y="销售额", theme="blue"), ValueError),
        (lambda: eazy_data_viz.bar(DF, x="大区", y="销售额", top_n=-1), ValueError),
    ]:
        try:
            fn()
        except exc:
            continue
        raise AssertionError("期望 %s，未抛出" % exc.__name__)


# ------------------------------------------------ 输出 HTML / 元数据
def t_html():
    html = eazy_data_viz.bar(DF, x="大区", y="销售额").to_html()
    for token in ("<!DOCTYPE html>", "eazy-grid", "EAZY_DATA", "EAZY_PAGE", "EazyViz.init", "echarts"):
        assert token in html, "缺少 %s" % token
    assert len(html) > 200000  # ECharts 内联


def t_save(tmpdir=None):
    if tmpdir is None:
        tmpdir = os.path.join(tempfile.gettempdir(), "eazy_data_viz_test")
    os.makedirs(tmpdir, exist_ok=True)
    p = os.path.join(tmpdir, "unit_single.html")
    eazy_data_viz.bar(DF, x="大区", y="销售额").save(p)
    assert os.path.getsize(p) > 200000


def t_dashboard_orders():
    page = eazy_data_viz.dashboard([eazy_data_viz.line(DF, x="月份", y="销售额")], cols=1, title="t")
    html = page.to_html()
    assert "orders" in html, "有序类目顺序未写入页面"


def t_dashboard_reset_buttons():
    """顶栏回退入口：有 link 或 drill 就渲染，「重置下钻」按钮总在其中。"""
    HDR = '<header class="eazy-appbar'
    bar = eazy_data_viz.bar(DF, x="大区" if "大区" in DF.columns else "月份", y="销售额")
    only_bar = eazy_data_viz.dashboard(bar).to_html()
    assert HDR not in only_bar, "既无联动也无下钻时不该渲染顶栏"
    linked = eazy_data_viz.dashboard(
        eazy_data_viz.bar(DF, x="大区" if "大区" in DF.columns else "月份", y="销售额", link="g9"),
    ).to_html()
    assert HDR in linked, "有 link 就该渲染顶栏（否则没有回退入口）"
    assert 'data-eazy-reset-drill' in linked, "缺少重置下钻按钮"
    assert 'data-eazy-reset-drill title=' in linked or 'data-eazy-reset-drill ' in linked
    assert HDR + ' is-plain"' in linked, "没有标题时应使用紧凑工具条样式"
    drill_only = eazy_data_viz.dashboard(
        eazy_data_viz.bar(DF, x="大区" if "大区" in DF.columns else "月份", y="销售额",
                          drill=["大区", "月份"] if "大区" in DF.columns else ["月份"]),
    ).to_html()
    assert 'data-eazy-reset-drill' in drill_only, "只有 drill 的看板也要有重置下钻按钮"
    titled = eazy_data_viz.dashboard(
        eazy_data_viz.bar(DF, x="大区" if "大区" in DF.columns else "月份", y="销售额", link="g9"),
        title="有标题",
    ).to_html()
    assert HDR in titled and HDR + ' is-plain"' not in titled


def t_empty_df():
    import pandas as pd
    empty = pd.DataFrame({"a": [], "b": []})
    try:
        eazy_data_viz.bar(empty, x="a")
    except ValueError:
        return
    raise AssertionError("空 DataFrame 应给出明确错误")


def t_show_api():
    assert callable(eazy_data_viz.show) and callable(eazy_data_viz.dashboard) and callable(eazy_data_viz.help)



def t_kpi_card():
    c = eazy_data_viz.kpi(DF, value="销售额", label="全年销售额", delta=0.128,
                 delta_label="同比", target=2000000, spark="销售额", spark_x="月份",
                 hint="2024 全年", link="g1")
    spec = c.spec
    assert spec["type"] == "kpi"
    assert spec["target"] == 2000000
    assert spec["delta"] == 0.128 and spec["deltaLabel"] == "同比"
    assert spec["spark"]["x"] == "月份" and spec["spark"]["y"] == "销售额"
    assert spec["hint"] == "2024 全年" and spec["link"] == "g1"
    assert c.data_ref, "KPI 需要 dataRef 才能参与联动过滤"
    assert spec.get("title") is None, "KPI 默认不再回退卡片标题（避免和 label 重复）"
    html = c.to_html()
    assert "eazy-kpi-value" in html or "EAZY_DATA" in html


def t_kpi_static_and_inverse():
    c = eazy_data_viz.kpi(19.9, label="利润率", fmt="percent", target=25, inverse=True)
    assert c.data_ref is None
    assert abs(c.spec["target"] - 25) < 1e-9 and c.spec["inverse"] is True
    # 参数校验
    for bad in (dict(spark="销售额"), dict(accent=-1), dict(target="abc")):
        try:
            eazy_data_viz.kpi(DF, value="销售额", label="x", **bad)
        except (ValueError, TypeError):
            continue
        raise AssertionError("非法 KPI 参数未报错: %r" % (bad,))


def t_palette_api():
    names = eazy_data_viz.palette.names()
    assert len(names) >= 7 and "google" in names and "tableau" in names, names
    for n in names:
        p = eazy_data_viz.palette.get(n)
        assert len(p["colors"]) >= 10 and p["label"], n
        assert all(len(c) == 7 and c[0] == "#" for c in p["colors"]), n
    try:
        eazy_data_viz.palette.check("nope")
    except ValueError:
        pass
    else:
        raise AssertionError("未知配色名应报错")


def t_chart_palette():
    c = eazy_data_viz.bar(DF, x="大区", y="销售额")
    out = c.palette("tableau")
    assert out is c and c.spec["palette"] == "tableau"
    c2 = eazy_data_viz.line(DF, x="月份", y="销售额").palette("morandi")
    assert c2.spec["palette"] == "morandi"
    try:
        c.palette("nope")
    except ValueError:
        pass
    else:
        raise AssertionError("未知配色名应报错")


def t_dashboard_palette():
    page = eazy_data_viz.dashboard(
        eazy_data_viz.bar(DF, x="大区", y="销售额"),
        eazy_data_viz.line(DF, x="月份", y="销售额").palette("tableau"),
        cols=1, title="t", palette="morandi")
    html = page.to_html()
    assert "data-eazy-palette" in html and '"palette": "morandi"' in html
    assert '"palette": "tableau"' in html
    assert "配色" in html


def t_max_rows_default():
    """默认 max_rows 必须是 20 万（用户数据 45622 行不能被采样）。"""
    import pandas as _pd
    from eazy_data_viz import frame as _frame
    assert _frame.MAX_ROWS == 200000, _frame.MAX_ROWS
    df = _pd.DataFrame({"x": ["a"] * 45622, "y": list(range(45622))})
    ch = eazy_data_viz.bar(df, x="x", y="y")
    assert len(ch.data["rows"]) == 45622, len(ch.data["rows"])
    assert not ch.warnings["warnings"], ch.warnings
    # 超过上限才采样
    df2 = _pd.DataFrame({"x": ["a"] * 250000, "y": list(range(250000))})
    ch2 = eazy_data_viz.bar(df2, x="x", y="y")
    assert len(ch2.data["rows"]) == 200000, len(ch2.data["rows"])
    assert ch2.warnings["warnings"] and "采样" in ch2.warnings["warnings"][0], ch2.warnings
    # max_rows=None 不采样
    ch3 = eazy_data_viz.bar(df2, x="x", y="y", max_rows=None)
    assert len(ch3.data["rows"]) == 250000, len(ch3.data["rows"])
    assert not ch3.warnings["warnings"], ch3.warnings
    # 显式 max_rows 生效
    ch4 = eazy_data_viz.bar(df, x="x", y="y", max_rows=1000)
    assert len(ch4.data["rows"]) == 1000, len(ch4.data["rows"])
    # 非法 max_rows 给出明确报错（而不是底层 TypeError）
    for bad, exc in ((100.5, TypeError), ("abc", TypeError), (0, ValueError), (-1, ValueError), (True, TypeError)):
        try:
            eazy_data_viz.bar(df, x="x", y="y", max_rows=bad)
        except exc as err:
            assert "max_rows" in str(err), (bad, str(err))
        else:
            raise AssertionError("max_rows=%r 应该报错" % (bad,))


def t_extra_param_checks():
    """扩展图表的关键字参数校验：target_value 非数字要报错，pareto 的 cum_fmt 报错文案要正确。"""
    df = DF.groupby("大区", as_index=False).agg(销售额=("销售额", "sum"), 利润=("利润", "sum"))
    for fn, kw in ((eazy_data_viz.bullet, {"target_value": "abc"}),
                   (eazy_data_viz.target, {"target_value": "abc"})):
        try:
            fn(df, x="大区", actual="销售额", **kw)
        except ValueError as err:
            assert "target_value" in str(err), (fn.__name__, str(err))
        else:
            raise AssertionError("%s(target_value='abc') 应该报 ValueError" % fn.__name__)
    try:
        eazy_data_viz.pareto(df, x="大区", y="销售额", cum_fmt="cn")
    except ValueError as err:
        assert "cum_fmt" in str(err), str(err)
    else:
        raise AssertionError("pareto(cum_fmt='cn') 应该报 ValueError")
    # radar 允许不传 y（按记录数画）
    ch = eazy_data_viz.radar(DF, x="渠道")
    assert ch.spec["type"] == "radar"


def t_maps():
    """地图：函数导出 / spec 字段 / 页面注入 EAZY_MAPS + EAZY_CITIES / 未知地图报错。"""
    import eazy_data_viz
    from eazy_data_viz import maps as ec_maps

    for fn in ("geo_map", "map_bubble", "map_flow"):
        assert fn in eazy_data_viz.__all__, "缺少导出 %s" % fn
        assert callable(getattr(eazy_data_viz, fn))

    reg = DF.groupby("省份", as_index=False)["销售额"].sum()
    ch = eazy_data_viz.geo_map(reg, region="省份", value="销售额")
    assert ch.spec["type"] == "geo_map" and ch.spec["map"] == "china"
    assert ch.spec["roles"]["region"] == "省份"

    world = __import__("pandas").DataFrame({"国家": ["中国", "美国"], "销售额": [10, 5]})
    chw = eazy_data_viz.geo_map(world, region="国家", value="销售额", map="world")
    assert chw.spec["map"] == "world"

    try:
        eazy_data_viz.geo_map(reg, region="省份", map="mars")
    except ValueError as exc:
        assert ("未知地图" in str(exc)) or ("只支持" in str(exc)), str(exc)
    else:
        raise AssertionError("未知地图应当报错")

    cities = DF.groupby("城市", as_index=False)["销售额"].sum()
    chb = eazy_data_viz.map_bubble(cities, region="城市", value="销售额")
    assert chb.spec["type"] == "map_bubble"
    html = eazy_data_viz.dashboard(ch, chb, cols=1).to_html()
    assert "window.EAZY_MAPS = {" in html and '"china"' in html
    assert "window.EAZY_CITIES = {" in html and "广州市" in html
    assert "eazy_map.js" in html or "地图类图表运行时" in html

    # 所有地图都支持公共参数
    ch2 = eazy_data_viz.map_bubble(cities, region="城市", value="销售额", fmt="compact",
                                   height=420, palette="tableau", link="g1")
    assert ch2.spec["height"] == 420 and ch2.spec["palette"] == "tableau"
    assert ch2.spec["link"] == "g1"


def t_doc_examples():
    """docs/eazy_catalog.json 里每个示例都必须能跑通（给 AI 的文档不能带坏例子）。"""
    import json
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "docs", "eazy_catalog.json")
    if not os.path.exists(path):
        return
    cat = json.load(open(path, encoding="utf-8"))
    assert cat["chart_types"], "目录为空"
    ns = {"eazy_data_viz": eazy_data_viz, "df": DF, "pd": __import__("pandas")}
    bad = []
    for g in cat["groups"]:
        for c in g["charts"]:
            try:
                eval(c["example"], ns)
            except Exception as exc:
                bad.append("%s: %s (%s)" % (c["name"], exc, c["example"]))
    assert not bad, "示例执行失败:\n" + "\n".join(bad)


def t_streamlit_v2():
    """components v2 渲染层：片段作用域化、可选依赖不报错、包入口导出。"""
    from eazy_data_viz import render as _render

    frag = _render.build_fragment([eazy_data_viz.bar(DF, x="大区", y="销售额"),
                                   eazy_data_viz.kpi(DF, value="销售额")])
    for key in ("html", "css", "page", "data_store", "maps", "cities", "cols"):
        assert key in frag, "build_fragment 缺少 " + key
    assert frag["html"].strip(), "片段 html 为空"
    assert "<script" not in frag["html"] and "<html" not in frag["html"]
    assert ":host" in frag["css"], "CSS 没有作用域化为 :host"
    assert "html[data-theme" not in frag["css"], "CSS 仍带全局选择器"
    assert frag["page"]["charts"], "片段缺少图表 spec"
    # 稳定 id：Chart 构造时是自增 id，渲染层必须按位置覆盖；否则 v2 每次 rerun
    # 都会因 data 变化重挂整块看板，联动/下钻状态被清空。
    import json as _json
    a = _render.build_fragment([eazy_data_viz.bar(DF, x="大区", y="销售额"),
                                eazy_data_viz.kpi(DF, value="销售额")])
    b = _render.build_fragment([eazy_data_viz.bar(DF, x="大区", y="销售额"),
                                eazy_data_viz.kpi(DF, value="销售额")])
    _ids = [c["id"] for c in a["page"]["charts"]]
    # 形如 eazy-<看板指纹>-<位置>：同一看板稳定，不同看板不撞车
    assert all(_i.startswith("eazy-") for _i in _ids), _ids
    assert len(set(_ids)) == 2, _ids
    assert _ids[0] != _ids[1]

    # 不同看板（同一页面挂多个 streamlit_dashboard）的 id 不能重复
    other = _render.build_fragment([eazy_data_viz.bar(DF, x="大区", y="销售额", title="另一个看板")])
    other_ids = [c["id"] for c in other["page"]["charts"]]
    assert not (set(_ids) & set(other_ids)), (_ids, other_ids)
    assert _json.dumps(a["page"], sort_keys=True) == _json.dumps(b["page"], sort_keys=True), \
        "同一批数据两次构建的 page 不一致：v2 会判定 data 变化并重挂组件"

    import eazy_data_viz.streamlit_v2 as v2

    # 无 Streamlit 时 is_available() 必须返回 False，而不是抛 ImportError
    assert v2.is_available() in (True, False)
    assert hasattr(eazy_data_viz, "streamlit_dashboard")
    assert "streamlit_dashboard" in eazy_data_viz.__all__
    assert "streamlit_available" in eazy_data_viz.__all__

    # 1.3.0：只有传 on_select 才挂 trigger；默认点击不 rerun。
    assert "payload.trigger" in v2._JS_TEMPLATE

    # v2 必须把所有运行时资源都喂给前端：手写清单漏掉 eazy_map.js 时，
    # geo_map / map_bubble / map_flow 会报「不支持的图表类型」。
    assert set(v2._sources()) == set(_render.ALL_JS), "v2 资源清单与 ALL_JS 不一致"
    assert "B.geo_map" in v2._sources()["eazy_map.js"]
    assert "window.EazyViz.onSelect = null" in v2._JS_TEMPLATE
    if v2.is_available():
        captured = {}

        class _FakeComp(object):
            def __call__(self, **kw):
                captured.clear(); captured.update(kw)
                return type("R", (), {"select": None})()

        frag = {"html": "<div></div>", "page": {"charts": []}, "data_store": {},
                "maps": {}, "cities": {}, "css": "", "cols": 1}
        old_frag, old_comp = v2._render.build_fragment, v2._component
        try:
            v2._render.build_fragment = lambda *a, **k: dict(frag)
            v2._component = lambda: _FakeComp()
            v2.render_dashboard([eazy_data_viz.bar(DF, x="大区", y="销售额")])
            assert captured["data"]["trigger"] is False
            assert "on_select_change" not in captured
            v2.render_dashboard([eazy_data_viz.bar(DF, x="大区", y="销售额")],
                                on_select=lambda: None)
            assert captured["data"]["trigger"] is True
            assert "on_select_change" in captured
        finally:
            v2._render.build_fragment, v2._component = old_frag, old_comp


def t_responsive():
    from eazy_data_viz import render as _render

    # 窄屏 / 窄容器自适应：网格列数走 CSS 变量（内联 repeat 写死时媒体查询盖不住），
    # 响应式断点、KPI 数字自动缩放、图例按容器宽度排版都在样式/脚本里。
    html = eazy_data_viz.dashboard([eazy_data_viz.bar(DF, x="大区", y="销售额")],
                                   cols=2, title="响应式").to_html()
    assert 'style="--eazy-cols:2"' in html
    assert "grid-template-columns:repeat(var(--eazy-cols,2)" in html
    assert "@media (max-width: 720px)" in html
    assert "--eazy-cols:2!important" in html
    js = _render._read_asset("eazy.js")
    for token in ("function fitTexts", "function fitResponsiveHeights",
                  "var activeWidth", "function legendItemPx", "function layoutLegend"):
        assert token in js, token
def t_layout():
    """自由排列：flow（列/行分配）、span（格子占位）、报错与页面标记。"""
    import pandas as _pd
    from eazy_data_viz import layout as L
    from eazy_data_viz import render as _render

    assert L.normalize_direction(None) == "h"
    for alias in ("h", "horizontal", "lr", "从左到右", "col"):
        assert L.normalize_direction(alias) == "h", alias
    for alias in ("v", "vertical", "tb", "从上到下", "row"):
        assert L.normalize_direction(alias) == "v", alias
    try:
        L.normalize_direction("diagonal")
    except ValueError as exc:
        assert "direction 只支持" in str(exc), str(exc)
    else:
        raise AssertionError("未知 direction 应当报错")

    plan = L.parse_layout(4, layout=[1, 3], direction="h")
    assert plan["mode"] == "flow" and plan["cols"] == 2 and plan["rows"] == 3
    assert plan["cells"] == [(0, 0, 1, 1), (0, 1, 1, 1), (1, 1, 1, 1), (2, 1, 1, 1)], plan["cells"]
    plan_v = L.parse_layout(3, layout=[1, 2], direction="v")
    assert plan_v["cells"] == [(0, 0, 1, 1), (1, 0, 1, 1), (1, 1, 1, 1)], plan_v["cells"]
    assert plan_v["cols"] == 2 and plan_v["rows"] == 2

    plan_s = L.parse_layout(2, layout=[[2, 2], [1, 1]], grid=(3, 3))
    assert plan_s["mode"] == "span" and plan_s["grid"] == (3, 3)
    # 第二张图落在 2×2 的右上角
    assert plan_s["cells"] == [(0, 0, 2, 2), (0, 2, 1, 1)], plan_s["cells"]
    assert L.parse_layout(2, layout=[[1, 1], [1, 1]], grid="2x2")["cols"] == 2

    for bad, msg in (
        (lambda: L.parse_layout(4, layout=[1, 2], direction="h"), "只提供了 3 个位置"),
        (lambda: L.parse_layout(2, grid=(2, 2)), "grid 需要配合 layout"),
        (lambda: L.parse_layout(4, layout=[[2, 2]], grid=(2, 2)), "收到 1 个占位声明"),
        (lambda: L.parse_layout(2, layout=[[3, 1], [1, 1]], grid=(2, 2)), "超过网格"),
        (lambda: L.parse_layout(2, layout=[[1, 1, 1]], grid=(2, 2)), "需要统一是整数"),
    ):
        try:
            bad()
        except ValueError as exc:
            assert msg in str(exc), "期望含 %r，实际 %s" % (msg, exc)
        else:
            raise AssertionError("应当报错：%s" % msg)

    cols_specs = [eazy_data_viz.bar(DF, x="大区", y="销售额") for _ in range(4)]
    html = _render.build_page(cols_specs, inline=False, layout=[1, 3], direction="h")
    assert "eazy-flow" in html and html.count("eazy-flow-col") >= 2, "缺少分列容器"
    html_v = _render.build_page(cols_specs, inline=False, layout=[1, 2, 1], direction="v")
    assert html_v.count("eazy-flow-row") >= 2, "缺少分行容器"
    html_s = _render.build_page(cols_specs[:2], inline=False,
                                layout=[[2, 2], [1, 1]], grid=(3, 3))
    assert "eazy-grid-free" in html_s and "grid-column:1 / span 2" in html_s, html_s[:400]

    frag = _render.build_fragment(cols_specs, layout=[1, 3], direction="h")
    assert frag["page"]["layout"]["mode"] == "flow", frag["page"]["layout"]
    assert "eazy-flow-col" in frag["html"]

    h_flow = _render.page_height(cols_specs, cols=2, layout=[1, 3], direction="h")
    assert h_flow > 0
    assert _render.page_height(cols_specs, cols=2) > 0

    # 自由排列与 section 分节互斥
    sec = [eazy_data_viz.bar(DF, x="大区", y="销售额", section="一"),
           eazy_data_viz.bar(DF, x="产品", y="销售额")]
    try:
        _render.build_page(sec, inline=False, layout=[1, 1], direction="h")
    except ValueError as exc:
        assert "不支持 section" in str(exc), str(exc)
    else:
        raise AssertionError("layout + section 应当报错")

    # 汇总文本可读
    assert "第1列 1 张" in L.layout_summary(plan), L.layout_summary(plan)


def t_table_groupby():
    """table(groupby=...)：显示层汇总、与 columns 互斥、参数校验。"""
    spec = eazy_data_viz.table(DF, groupby={"columns": ["大区"], "value": "销售额"}).spec
    assert spec["type"] == "table"
    assert spec["groupby"] == {"columns": ["大区"], "value": "销售额", "agg": "sum"}, spec["groupby"]
    assert spec["columns"] == ["大区", "销售额"], spec["columns"]
    assert spec["agg"] == "sum"
    assert spec["title"] == "汇总数据", spec["title"]

    cnt = eazy_data_viz.table(DF, groupby={"columns": ["大区", "渠道"]}).spec
    assert cnt["groupby"]["agg"] == "count" and cnt["groupby"]["value"] is None
    assert cnt["columns"] == ["大区", "渠道"], cnt["columns"]

    detail = eazy_data_viz.table(DF, columns=["日期", "大区", "销售额"]).spec
    assert detail["groupby"] is None and detail["columns"] == ["日期", "大区", "销售额"]
    assert detail["title"] == "明细数据"

    for kwargs, msg in (
        (dict(columns=["大区"], groupby={"columns": ["大区"]}), "已由 groupby 取代"),
        (dict(groupby={"columns": ["大区"], "agg_func": "sum"}), "未知键"),
        (dict(groupby={"columns": []}), "不能为空"),
        (dict(groupby={"columns": ["大区"], "value": ["销售额", "利润"]}), "只能是一列"),
        (dict(groupby={"columns": ["大区"], "value": "大区"}), "不能同时出现在 columns"),
        (dict(groupby={"columns": ["大区"], "value": "销售额", "agg": "avg"}), "不支持"),
        (dict(groupby={"columns": ["大区"], "agg": "sum"}), "只能是"),
        (dict(groupby=["大区"]), "需要是字典"),
    ):
        try:
            eazy_data_viz.table(DF, **kwargs)
        except ValueError as exc:
            assert msg in str(exc), "期望含 %r，实际 %s" % (msg, exc)
        else:
            raise AssertionError("应当报错：%s" % msg)

    html = eazy_data_viz.dashboard(eazy_data_viz.table(
        DF, groupby={"columns": ["大区"], "value": "销售额"})).to_html()
    assert '"groupby"' in html and "大区" in html


def t_sankey_path():
    """多级桑基：path 相邻层成边、默认标题、两级兼容、参数互斥。"""
    s = eazy_data_viz.sankey(DF, path=["大区", "渠道", "产品"], value="销售额").spec
    assert s["type"] == "sankey"
    assert s["roles"]["path"] == ["大区", "渠道", "产品"], s["roles"]
    assert s["roles"]["value"] == "销售额"
    assert s["title"] == "大区 → 渠道 → 产品 流向", s["title"]
    assert s["agg"] == "sum"

    legacy = eazy_data_viz.sankey(DF, source="渠道", target="产品", value="销售额").spec
    assert legacy["roles"]["path"] == ["渠道", "产品"], legacy["roles"]
    assert legacy["roles"]["value"] == "销售额"

    counted = eazy_data_viz.sankey(DF, source="渠道", target="产品").spec
    assert counted["agg"] == "count", counted["agg"]

    for kwargs, msg in (
        (dict(path=["大区", "渠道"], source="大区", target="渠道"), "不能同时使用"),
        (dict(value="销售额"), "需要 path"),
        (dict(path=["大区"]), "至少需要 2 级"),
        (dict(path=["大区", "大区"]), "不能有重复列"),
    ):
        try:
            eazy_data_viz.sankey(DF, **kwargs)
        except ValueError as exc:
            assert msg in str(exc), "期望含 %r，实际 %s" % (msg, exc)
        else:
            raise AssertionError("应当报错：%s" % msg)


def t_bar_yoy():
    """同比：两个取值时标注本期/上期，多于两个退化并提示，缺 color 报错。"""
    import pandas as _pd

    yy = _pd.DataFrame({
        "月份": ["1月", "1月", "2月", "2月"],
        "年份": ["2026", "2025", "2026", "2025"],
        "销售额": [130, 100, 90, 120],
    })
    ch = eazy_data_viz.bar(yy, x="月份", y="销售额", color="年份", yoy=True)
    assert ch.spec["yoy"] == {"dim": "年份"}, ch.spec["yoy"]

    plain = eazy_data_viz.bar(yy, x="月份", y="销售额", color="年份")
    assert plain.spec["yoy"] is None, plain.spec["yoy"]

    many = eazy_data_viz.bar(DF, x="大区", y="销售额", color="渠道", yoy=True)
    assert many.spec["yoy"] is None
    warns = " ".join(many.warnings.get("warnings") or [])
    assert "只有恰好 2 个取值" in warns, many.warnings

    try:
        eazy_data_viz.bar(yy, x="月份", y="销售额", yoy=True)
    except ValueError as exc:
        assert "需要 color 参数" in str(exc), str(exc)
    else:
        raise AssertionError("yoy 缺 color 应当报错")


def t_link_modes():
    """联动方向：both / out / in 的三种写法与校验。"""
    g = lambda **kw: eazy_data_viz.bar(DF, x="大区", y="销售额", **kw).spec
    assert g(link="g1")["link"] == "g1" and g(link="g1")["linkMode"] == "both"
    assert g(link=("g1", "out"))["linkMode"] == "out"
    assert g(link=["g1", "in"])["linkMode"] == "in"
    assert g(link={"group": "g1", "direction": "out"})["linkMode"] == "out"
    assert g(link={"group": "g1"})["linkMode"] == "both"
    assert g(link=("g1", "单向出"))["linkMode"] == "out"
    assert g(link=("g1", "单向进"))["linkMode"] == "in"
    assert g(link=("g1", "双向"))["linkMode"] == "both"
    assert g(link=("g1", "接收"))["linkMode"] == "in"

    # KPI / 手工 spec 也走同一套解析
    assert eazy_data_viz.kpi(DF, value="销售额", link=("k", "out")).spec["linkMode"] == "out"
    assert eazy_data_viz.table(DF, link=("t", "in")).spec["linkMode"] == "in"

    for bad, msg in (
        (dict(link=("a", "out", "x")), "最多两个元素"),
        (dict(link=()), "不能是空元组"),
        (dict(link={"group": "g", "mode": "out", "extra": 1}), "未知键"),
        (dict(link={"direction": "out"}), "需要 group 键"),
        (dict(link=123), "需要是字符串"),
        (dict(link=""), "不能为空"),
        (dict(link=("g", "up")), "方向只支持"),
    ):
        try:
            eazy_data_viz.bar(DF, x="大区", y="销售额", **bad)
        except ValueError as exc:
            assert msg in str(exc), "期望含 %r，实际 %s" % (msg, exc)
        else:
            raise AssertionError("应当报错：%s" % msg)


def t_abs_height():
    """绝对高度：height 指整个组件外框；网格拼成矩形、方向模式各列等高。"""
    import pandas as _pd
    from eazy_data_viz import layout as L
    from eazy_data_viz import render as _render

    plain = _spec(eazy_data_viz.bar(DF, x="大区", y="销售额", height=320))
    assert plain["absHeight"] is False and plain["height"] == 320
    assert _render._card_height(plain) > 320  # 默认 height 只算正文

    boxed = _spec(eazy_data_viz.bar(DF, x="大区", y="销售额", height=320, abs_height=True))
    assert boxed["absHeight"] is True and boxed["height"] == 320
    assert _render._card_height(boxed) == 320
    # 标题很长、还带联动工具条，框高依旧是 320
    tall = _spec(
        eazy_data_viz.bar(DF, x="大区", y="销售额", title="很长" * 30, subtitle="副标题",
                          link="g1", height=320, abs_height=True)
    )
    assert _render._card_height(tall) == 320, _render._card_height(tall)

    # 非 bar 的实现（手工 spec / 地图）也认这个参数
    assert eazy_data_viz.kpi(DF, value="销售额", height=200, abs_height=True).spec["absHeight"] is True
    assert eazy_data_viz.table(DF, height=360, abs_height=True).spec["absHeight"] is True
    assert eazy_data_viz.gauge(62, height=260, abs_height=True).spec["absHeight"] is True

    html = eazy_data_viz.dashboard(
        eazy_data_viz.bar(DF, x="大区", y="销售额", title="销售额", height=320, abs_height=True),
        eazy_data_viz.pie(DF, names="大区", values="销售额", height=320, abs_height=True),
        cols=2,
    ).to_html()
    assert "eazy-card-fill" in html and "height:320px" in html
    assert "eazy-fill" in html

    # 模式 B：行高只增不减，跨行卡片吃满格子 → 整块网格是一个矩形
    plan = L.parse_layout(4, layout=[[2, 2], [1, 1], [1, 1], [1, 1]], grid=(3, 3))
    rows, boxes = L.grid_row_heights(plan, [700, 300, 300, 300])
    assert len(rows) == 3, rows
    for i in range(3):
        assert rows[i] >= 300, (i, rows)
    assert int(round(boxes[0])) == int(round(rows[0] + rows[1] + L.GAP)) == 700
    assert L.layout_height(plan, [700, 300, 300, 300]) == sum(rows) + 2 * L.GAP

    grid_html = _render.build_page(
        [eazy_data_viz.bar(DF, x="大区", y="销售额") for _ in range(4)],
        inline=False, layout=[[2, 2], [1, 1], [1, 1], [1, 1]], grid=(3, 3),
    )
    assert "grid-template-rows:" in grid_html and "eazy-grid-free" in grid_html
    # 模式 A：各列高度一致（列容器带 px 高度，卡片 fill）
    flow_html = _render.build_page(
        [eazy_data_viz.bar(DF, x="大区", y="销售额") for _ in range(3)],
        inline=False, layout=[1, 2], direction="h",
    )
    assert '<div class="eazy-flow-col" style="height:' in flow_html
    assert "eazy-card-fill" in flow_html


def t_wordcloud_shape():
    """词云形状：内置形状名 / 本地图片 → spec.shape；非法输入报中文错误。"""
    import base64
    import io as _io
    import tempfile

    import pandas as _pd
    df = _pd.DataFrame({"关键词": ["华东", "华南", "华北"], "次数": [120, 80, 40]})

    c = eazy_data_viz.wordcloud(df, names="关键词", values="次数", shape="heart")
    assert c.spec["shape"] == {"type": "builtin", "name": "heart"}, c.spec["shape"]
    c = eazy_data_viz.wordcloud(df, names="关键词", values="次数", shape="star")
    assert c.spec["shape"]["name"] == "star", c.spec["shape"]
    c = eazy_data_viz.wordcloud(df, names="关键词", values="次数")
    assert c.spec.get("shape") is None, c.spec.get("shape")

    tmp = tempfile.mkdtemp(prefix="eazy_wc_")
    img = os.path.join(tmp, "shape.png")
    _io.open(img, "wb").write(base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="))
    c = eazy_data_viz.wordcloud(df, names="关键词", values="次数", shape=img)
    sh = c.spec["shape"]
    assert sh["type"] == "image", sh
    assert sh["src"].startswith("data:image/png;base64,"), sh["src"][:40]
    assert sh["name"] == "shape.png", sh

    for bad in ("nope", "", 5):
        try:
            eazy_data_viz.wordcloud(df, names="关键词", values="次数", shape=bad)
        except ValueError as exc:
            assert "shape" in str(exc), str(exc)
        else:
            raise AssertionError("shape=%r 应当报错" % (bad,))

    bad_ext = os.path.join(tmp, "shape.tiff")
    _io.open(bad_ext, "wb").write(b"x")
    try:
        eazy_data_viz.wordcloud(df, names="关键词", values="次数", shape=bad_ext)
    except ValueError as exc:
        assert "只支持" in str(exc), str(exc)
    else:
        raise AssertionError("不支持的图片扩展名应当报错")

    big = os.path.join(tmp, "big.png")
    _io.open(big, "wb").write(b"x" * (3 * 1024 * 1024))
    try:
        eazy_data_viz.wordcloud(df, names="关键词", values="次数", shape=big)
    except ValueError as exc:
        assert "2 MB" in str(exc), str(exc)
    else:
        raise AssertionError("超过 2MB 的图片应当报错")


def t_type_hints():
    """公开 API 全带类型注解（IDE 悬浮不再显示 Unknown）。"""
    import ast as _ast
    import inspect as _inspect

    import io as _io2
    from eazy_data_viz import chart as _chart, charts_extra as _extra, maps as _maps
    missing = []
    for mod in (_chart, _extra, _maps):
        src = _io2.open(_inspect.getsourcefile(mod), encoding="utf-8").read()
        for node in _ast.parse(src).body:
            if not isinstance(node, _ast.FunctionDef) or node.name.startswith("_"):
                continue
            args = node.args.args + node.args.kwonlyargs
            if any(a.annotation is None for a in args) or node.returns is None:
                missing.append("%s.%s" % (mod.__name__.rsplit(".", 1)[-1], node.name))
    assert not missing, "缺类型注解: %s" % ", ".join(missing[:8])
    sig = str(_inspect.signature(eazy_data_viz.table))
    assert "pd.DataFrame" in sig and "groupby" in sig, sig


for name, fn in sorted((k[2:], v) for k, v in list(globals().items()) if k.startswith("t_")):
    check(name, fn)

print("PASS %d" % len(PASS))
if FAIL:
    print("FAIL %d" % len(FAIL))
    for name, tb in FAIL:
        print("\n--- %s ---\n%s" % (name, tb))
    sys.exit(1)
print("ALL OK:", ", ".join(PASS))
