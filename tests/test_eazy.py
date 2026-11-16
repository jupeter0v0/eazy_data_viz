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

    import eazy_data_viz.streamlit_v2 as v2

    # 无 Streamlit 时 is_available() 必须返回 False，而不是抛 ImportError
    assert v2.is_available() in (True, False)
    assert hasattr(eazy_data_viz, "streamlit_dashboard")
    assert "streamlit_dashboard" in eazy_data_viz.__all__
    assert "streamlit_available" in eazy_data_viz.__all__


for name, fn in sorted((k[2:], v) for k, v in list(globals().items()) if k.startswith("t_")):
    check(name, fn)

print("PASS %d" % len(PASS))
if FAIL:
    print("FAIL %d" % len(FAIL))
    for name, tb in FAIL:
        print("\n--- %s ---\n%s" % (name, tb))
    sys.exit(1)
print("ALL OK:", ", ".join(PASS))
