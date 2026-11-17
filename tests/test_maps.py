# -*- coding: utf-8 -*-
"""地图图表冒烟单测（不依赖 pytest，直接 ``python tests/test_maps.py``）。

覆盖四块内容：

1. 内置 GeoJSON（china.json / world.json）的合法性、feature 数、关键区域名；
2. ``geo_map`` / ``map_bubble`` / ``map_flow`` 的 spec 组装（type / roles /
   map / dataRef / 标题 / 下钻 / 配色等）；
3. 静态参数校验的中文报错（列不存在、map 非法、min_value >= max_value、
   source == target、min_size >= max_size、配色 / 主题 / 聚合非法……）；
4. 真实 HTML 产物：``to_html()`` / ``save()`` 里确实注入了
   ``window.EAZY_MAPS`` 并加载了 ``eazy_map.js``（地图能渲染的前提）。
"""
import io
import json
import os
import sys
import tempfile
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

import eazy_data_viz  # noqa: E402
import eazy_data_viz.maps as maps  # noqa: E402
from eazy_data_viz.maps import (  # noqa: E402
    MAPS,
    geo_map,
    map_bubble,
    map_flow,
    normalize_region,
    province_centers,
    region_centers,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS_DIR = os.path.join(ROOT, "eazy_data_viz", "assets", "maps")

DF = eazy_data_viz.sample_df(rows=600, seed=7)

# 飞线用的数据：起点 / 终点都是省份短名，能匹配中国地图
FLOW = pd.DataFrame(
    {
        "起点": ["北京", "广东", "上海", "江苏", "浙江", "四川"],
        "终点": ["上海", "北京", "广东", "浙江", "北京", "陕西"],
        "货量": [120, 80, 60, 45, 90, 30],
    }
)

# 世界地图数据：中文国名（前端有别名表，同时也支持英文原名）
WORLD = pd.DataFrame(
    {
        "国家": ["美国", "中国", "德国", "巴西", "印度", "澳大利亚"],
        "GDP": [100, 90, 70, 60, 55, 40],
    }
)

PASS, FAIL = [], []


def check(name, fn):
    try:
        fn()
        PASS.append(name)
    except Exception:
        FAIL.append((name, traceback.format_exc()))


# ---------------------------------------------------------------- 小工具
def _spec(chart):
    return chart.spec


def _has_data(spec):
    assert spec["dataRef"], "dataRef 为空"
    assert str(spec["dataRef"]).startswith("d"), "dataRef 应以 d 开头：%r" % (spec["dataRef"],)
    assert spec["type"], "type 为空"


def raises(exc_type, fn, *args, **kwargs):
    """断言调用必然抛出 exc_type，返回异常文本（供断言中文关键字用）。"""
    try:
        fn(*args, **kwargs)
    except exc_type as exc:
        return str(exc)
    except Exception as exc:  # noqa: BLE001 - 测试里要报告「抛错了类型」
        raise AssertionError(
            "期望 %s，实际抛出 %s：%s" % (exc_type.__name__, type(exc).__name__, exc)
        )
    raise AssertionError("期望 %s，但调用没有报错。" % exc_type.__name__)


def _load_geo(name):
    path = os.path.join(MAPS_DIR, name + ".json")
    assert os.path.isfile(path), "缺少地图文件：%s" % path
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------- GeoJSON
def t_geojson_china():
    geo = _load_geo("china")
    assert geo["type"] == "FeatureCollection"
    features = geo["features"]
    assert len(features) == 35, "china.json 应有 35 个 feature，实际 %d" % len(features)
    names = [f.get("properties", {}).get("name") or "" for f in features]
    assert names.count("") == 1, "应有且只有 1 个空名称占位 feature（南海诸岛）"
    for key in ("北京市", "广东省", "内蒙古自治区", "广西壮族自治区",
                "新疆维吾尔自治区", "西藏自治区", "香港特别行政区", "澳门特别行政区",
                "台湾省"):
        assert key in names, "china.json 缺少区域：%s" % key
    # 所有 geometry 都是 Polygon / MultiPolygon，且坐标是数字对
    empty_ok = 0
    for f in features:
        geom = f.get("geometry") or {}
        assert geom.get("type") in ("Polygon", "MultiPolygon"), geom.get("type")
        coords = geom.get("coordinates")
        assert isinstance(coords, list) and coords, "coordinates 为空：%r" % f.get(
            "properties", {}
        )
        # 取第一层第一个点做冒烟检查
        point = coords[0][0] if geom["type"] == "Polygon" else coords[0][0][0]
        lng, lat = float(point[0]), float(point[1])
        assert -180 <= lng <= 180 and -90 <= lat <= 90, "坐标越界：%r" % (point,)
        if not (f.get("properties") or {}).get("name"):
            empty_ok += 1
    assert empty_ok == 1
    # properties.center 也要是合法经纬度（气泡图质心会优先用它）
    for f in features:
        center = (f.get("properties") or {}).get("center")
        if center:
            assert -180 <= float(center[0]) <= 180
            assert -90 <= float(center[1]) <= 90


def t_geojson_world():
    geo = _load_geo("world")
    assert geo["type"] == "FeatureCollection"
    features = geo["features"]
    assert len(features) == 217, "world.json 应有 217 个 feature，实际 %d" % len(features)
    names = [(f.get("properties") or {}).get("name") or "" for f in features]
    assert names.count("") == 2, "world.json 应有 2 个空名称 feature（南极洲碎片）"
    for key in ("China", "United States", "Russia", "United Kingdom", "Korea",
                "W. Sahara", "Central African Rep.", "Czech Rep."):
        assert key in names, "world.json 缺少国家：%s" % key
    for f in features:
        geom = f.get("geometry") or {}
        assert geom.get("type") in ("Polygon", "MultiPolygon"), geom.get("type")
        cp = (f.get("properties") or {}).get("cp")
        if cp:
            assert -180 <= float(cp[0]) <= 180, "cp 经度越界：%r" % (cp,)
            assert -90 <= float(cp[1]) <= 90, "cp 纬度越界：%r" % (cp,)


# ---------------------------------------------------------------- 名称归一化
def t_normalize_region():
    cases = {
        "广东省": "广东",
        "广西壮族自治区": "广西",
        "内蒙古自治区": "内蒙古",
        "宁夏回族自治区": "宁夏",
        "新疆维吾尔自治区": "新疆",
        "西藏自治区": "西藏",
        "香港特别行政区": "香港",
        "澳门特别行政区": "澳门",
        "北京市": "北京",
        "上海市": "上海",
        "浙江省": "浙江",
        "广东": "广东",
        " 广东 ": "广东",
        "W. Sahara": "WSahara",
        "United States": "UnitedStates",
    }
    for raw, want in cases.items():
        got = normalize_region(raw)
        assert got == want, "normalize_region(%r) 应为 %r，实际 %r" % (raw, want, got)
    assert normalize_region(None) == ""
    # 归一化是幂等的：短名再归一化还是自己
    for short in ("广东", "内蒙古", "广西", "香港", "新疆"):
        assert normalize_region(short) == short
    # 与前端共享的约定：python 接口必须暴露
    assert callable(maps.normalize_region)


def t_maps_constant():
    assert MAPS == ("china", "world")
    assert maps.__all__ and "geo_map" in maps.__all__


# ---------------------------------------------------------------- 中心点
def t_province_centers():
    centers = province_centers()
    assert isinstance(centers, dict)
    assert len(centers) >= 34, "省级中心点数量应 >= 34，实际 %d" % len(centers)
    for key in ("北京", "上海", "广东", "江苏", "浙江", "四川", "内蒙古",
                "广西", "新疆", "西藏", "香港", "澳门", "台湾"):
        assert key in centers, "缺少省级中心点：%s" % key
        point = centers[key]
        assert isinstance(point, list) and len(point) == 2, point
        lng, lat = float(point[0]), float(point[1])
        assert 70 <= lng <= 140, "%s 经度异常：%r" % (key, point)
        assert 0 <= lat <= 60, "%s 纬度异常：%r" % (key, point)
    # 返回值是副本，修改不影响内部缓存
    centers["广东"][0] = 0
    assert province_centers()["广东"][0] != 0


def t_region_centers():
    china = region_centers("china")
    assert "广东省" in china and "北京市" in china
    world = region_centers("world")
    assert len(world) >= 200
    assert "United States" in world and "China" in world
    # 非法地图名给中文报错
    msg = raises(ValueError, region_centers, "mars")
    assert "china" in msg and "world" in msg


# ---------------------------------------------------------------- geo_map
def t_geo_map_spec():
    chart = geo_map(DF, "省份", "销售额")
    spec = _spec(chart)
    _has_data(spec)
    assert spec["type"] == "geo_map"
    assert spec["map"] == "china"
    assert spec["roles"]["region"] == "省份"
    assert spec["roles"]["value"] == "销售额"
    assert spec["roles"]["x"] == "省份", "roles.x 必须是区域列，联动/下钻依赖它"
    assert spec["agg"] == "sum"
    assert spec["fmt"] == "compact"
    assert spec["height"] == 460
    assert spec["theme"] == "light"
    assert spec["labels"] is True
    assert spec["legend"] is True
    assert spec["title"] == "销售额 · 中国地图"
    assert spec["minValue"] is None and spec["maxValue"] is None
    assert len(chart.data["rows"]) > 0


def t_geo_map_options():
    chart = geo_map(
        DF,
        "省份",
        "订单数",
        map="china",
        agg="mean",
        fmt="thousands",
        labels=False,
        legend=False,
        min_value=0,
        max_value=1000,
        name_map={"广东": "广东省", "北京": "北京市"},
        zoom=False,
        palette="carbon",
        height=520,
        theme="dark",
        title="自定义标题",
        subtitle="副标题",
        link="省份",
        section="地图区",
    )
    spec = _spec(chart)
    assert spec["agg"] == "mean"
    assert spec["fmt"] == "thousands"
    assert spec["labels"] is False
    assert spec["legend"] is False
    assert spec["minValue"] == 0.0 and spec["maxValue"] == 1000.0
    assert spec["nameMap"] == {"广东": "广东省", "北京": "北京市"}
    assert spec["zoom"] is False
    assert spec["palette"] == "carbon"
    assert spec["height"] == 520
    assert spec["theme"] == "dark"
    assert spec["title"] == "自定义标题"
    assert spec["subtitle"] == "副标题"
    assert spec["link"] == "省份"
    assert spec["section"] == "地图区"


def t_geo_map_count():
    # 不传 value：按记录数聚合，标题自动用「记录数」
    chart = geo_map(DF, "省份")
    spec = _spec(chart)
    assert spec["roles"]["value"] is None
    assert spec["agg"] == "count"
    assert spec["title"] == "记录数 · 中国地图"


def t_geo_map_drill():
    chart = geo_map(DF, "省份", "销售额", drill="城市")
    spec = _spec(chart)
    assert spec["drill"] == ["省份", "城市"], spec["drill"]
    # 只给一层地图维度时，自动补一层 region 让点击聚焦生效
    assert _spec(geo_map(DF, "省份", "销售额", drill="省份"))["drill"] == ["省份", "省份"]
    # 下钻维度不以 region 开头时自动前置
    assert _spec(geo_map(DF, "省份", "销售额", drill=["城市"]))["drill"] == ["省份", "城市"]
    # 不传 drill 时是 None
    assert _spec(geo_map(DF, "省份", "销售额"))["drill"] is None
    # 下钻列不存在 → 中文 KeyError
    msg = raises(KeyError, geo_map, DF, "省份", "销售额", drill=["不存在的列"])
    assert "不存在" in msg


def t_geo_map_full_names():
    # 数据里写全名也能用：Python 不做名称匹配，原样交给前端归一化
    df = pd.DataFrame(
        {
            "区域": ["广东省", "北京市", "内蒙古自治区", "香港特别行政区"],
            "销售额": ["1200", "980", "760", "640"],  # 文本数字应被自动清洗
        }
    )
    spec = _spec(geo_map(df, "区域", "销售额"))
    assert spec["map"] == "china"
    rows = geo_map(df, "区域", "销售额").data["rows"]
    assert rows[0][0] == "广东省"  # 原值原样保留（点击联动靠它精确匹配）
    assert isinstance(rows[0][1], (int, float)), "文本数字应被转成数值：%r" % (rows[0],)


def t_geo_map_errors():
    # region 列不存在
    msg = raises(KeyError, geo_map, DF, "不存在的省份", "销售额")
    assert "region" in msg and "不存在" in msg
    # value 列不存在
    msg = raises(KeyError, geo_map, DF, "省份", "不存在的指标")
    assert "value" in msg and "不存在" in msg
    # map 非法
    msg = raises(ValueError, geo_map, DF, "省份", "销售额", map="europe")
    assert 'map 只支持 "china"' in msg
    # min_value >= max_value
    msg = raises(ValueError, geo_map, DF, "省份", "销售额", min_value=10, max_value=10)
    assert "min_value 必须小于 max_value" in msg
    # 只固定一端是允许的
    spec = _spec(geo_map(DF, "省份", "销售额", min_value=0))
    assert spec["minValue"] == 0.0 and spec["maxValue"] is None
    spec = _spec(geo_map(DF, "省份", "销售额", max_value=200000))
    assert spec["maxValue"] == 200000.0
    # 参数类型错误
    assert "region" in raises(ValueError, geo_map, DF, "", "销售额")
    assert "数字" in raises(ValueError, geo_map, DF, "省份", "销售额", min_value="abc")
    assert "name_map 需要是 dict" in raises(TypeError, geo_map, DF, "省份", "销售额",
                                            name_map=[("广东", "广东省")])
    assert "zoom 只支持" in raises(ValueError, geo_map, DF, "省份", "销售额", zoom="big")
    assert "配色" in raises(ValueError, geo_map, DF, "省份", "销售额", palette="rainbow")
    assert "height 至少 120" in raises(ValueError, geo_map, DF, "省份", "销售额", height=100)
    assert "theme 只支持" in raises(ValueError, geo_map, DF, "省份", "销售额", theme="blue")
    assert "agg" in raises(ValueError, geo_map, DF, "省份", "销售额", agg="avg")
    assert "fmt" in raises(ValueError, geo_map, DF, "省份", "销售额", fmt="usd")


# ---------------------------------------------------------------- map_bubble
def t_map_bubble_spec():
    chart = map_bubble(DF, "省份", "销售额")
    spec = _spec(chart)
    _has_data(spec)
    assert spec["type"] == "map_bubble"
    assert spec["map"] == "china"
    assert spec["roles"]["region"] == "省份"
    assert spec["roles"]["value"] == "销售额"
    assert spec["roles"]["size"] is None and spec["roles"]["color"] is None
    assert spec["labels"] is False, "气泡默认不显示标签，避免和省份名重叠"
    assert spec["minSize"] == 4.0 and spec["maxSize"] == 28.0
    assert spec["title"] == "销售额 · 省份气泡地图"
    assert spec["agg"] == "sum"


def t_map_bubble_options():
    chart = map_bubble(
        DF,
        "省份",
        "销售额",
        size="订单数",
        color="大区",
        min_size=6,
        max_size=40,
        agg="mean",
        legend=False,
        link="省份",
        drill="城市",
        palette="tableau",
        subtitle="按大区着色",
    )
    spec = _spec(chart)
    assert spec["roles"]["size"] == "订单数"
    assert spec["roles"]["color"] == "大区"
    assert spec["minSize"] == 6.0 and spec["maxSize"] == 40.0
    assert spec["agg"] == "mean"
    assert spec["legend"] is False
    assert spec["link"] == "省份"
    assert spec["drill"] == ["省份", "城市"]
    assert spec["palette"] == "tableau"
    assert spec["subtitle"] == "按大区着色"


def t_map_bubble_count():
    # 只给 size：气泡大小用 size，值仍按记录数计
    spec = _spec(map_bubble(DF, "省份", size="订单数"))
    assert spec["roles"]["value"] is None
    assert spec["roles"]["size"] == "订单数"
    assert spec["agg"] == "count"
    assert spec["title"] == "记录数 · 省份气泡地图"


def t_map_bubble_text_numeric():
    df = pd.DataFrame(
        {
            "省份": ["广东", "浙江", "江苏", "四川"],
            "销售额": ["1200", "980", "760", "640"],
            "订单数": ["10", "20", "30", "40"],
        }
    )
    rows = map_bubble(df, "省份", "销售额", size="订单数").data["rows"]
    assert isinstance(rows[0][1], (int, float)), rows
    assert isinstance(rows[0][2], (int, float)), rows
    # 完全不是数字的文本列 → TypeError（而不是静默画一张空图）
    bad = pd.DataFrame({"省份": ["广东", "浙江"], "销售额": ["很多", "未知"]})
    msg = raises(TypeError, map_bubble, bad, "省份", "销售额")
    assert "数值" in msg
    msg = raises(TypeError, map_bubble, bad, "省份", size="销售额")
    assert "数值" in msg


def t_map_bubble_errors():
    msg = raises(KeyError, map_bubble, DF, "省份", "销售额", size="不存在的列")
    assert "size" in msg and "不存在" in msg
    msg = raises(KeyError, map_bubble, DF, "省份", "销售额", color="不存在的列")
    assert "color" in msg and "不存在" in msg
    msg = raises(ValueError, map_bubble, DF, "省份", "销售额", min_size=30, max_size=10)
    assert "min_size 必须小于 max_size" in msg
    msg = raises(ValueError, map_bubble, DF, "省份", "销售额", min_size=0)
    assert "min_size / max_size 需要大于 0" in msg
    msg = raises(ValueError, map_bubble, DF, "省份", size="省份")
    assert "size 不能与 region 是同一列" in msg
    msg = raises(ValueError, map_bubble, DF, "省份", color="省份")
    assert "color 不能与 region 是同一列" in msg
    msg = raises(ValueError, map_bubble, DF, "省份", map="europe")
    assert 'map 只支持 "china"' in msg


def t_map_bubble_no_value():
    # value / size / color 全不传：退化为「各省记录数」气泡图
    chart = map_bubble(DF, "省份")
    spec = _spec(chart)
    assert spec["roles"]["value"] is None
    assert spec["agg"] == "count"
    assert len(chart.data["rows"]) > 0


# ---------------------------------------------------------------- map_flow
def t_map_flow_spec():
    chart = map_flow(FLOW, "起点", "终点", "货量")
    spec = _spec(chart)
    _has_data(spec)
    assert spec["type"] == "map_flow"
    assert spec["map"] == "china"
    assert spec["roles"]["source"] == "起点"
    assert spec["roles"]["target"] == "终点"
    assert spec["roles"]["value"] == "货量"
    assert spec["roles"]["x"] == "起点", "roles.x 用起点列，联动过滤按起点维度走"
    assert spec["title"] == "起点 → 终点 流向"
    assert spec["drill"] is None, "飞线图没有下钻，显式置空"
    assert spec["height"] == 460


def t_map_flow_options():
    chart = map_flow(
        FLOW,
        "起点",
        "终点",
        "货量",
        map="china",
        agg="max",
        fmt="thousands",
        name_map={"北京": "北京市"},
        zoom="scale",
        palette="antd",
        height=480,
        theme="dark",
        title="调拨",
        subtitle="按最大值聚合",
        legend=False,
        link="起点",
        section="流向",
    )
    spec = _spec(chart)
    assert spec["agg"] == "max"
    assert spec["fmt"] == "thousands"
    assert spec["nameMap"] == {"北京": "北京市"}
    assert spec["zoom"] == "scale"
    assert spec["palette"] == "antd"
    assert spec["height"] == 480
    assert spec["theme"] == "dark"
    assert spec["title"] == "调拨"
    assert spec["subtitle"] == "按最大值聚合"
    assert spec["legend"] is False
    assert spec["link"] == "起点"
    assert spec["section"] == "流向"


def t_map_flow_count():
    spec = _spec(map_flow(FLOW, "起点", "终点"))
    assert spec["roles"]["value"] is None
    assert spec["agg"] == "count"
    assert spec["title"] == "起点 → 终点 流向"


def t_map_flow_text_numeric():
    df = pd.DataFrame(
        {"起点": ["北京", "广东"], "终点": ["上海", "北京"], "货量": ["100", "200"]}
    )
    rows = map_flow(df, "起点", "终点", "货量").data["rows"]
    assert isinstance(rows[0][2], (int, float)), rows


def t_map_flow_errors():
    msg = raises(ValueError, map_flow, FLOW, "起点", "起点", "货量")
    assert "source 和 target 不能是同一列" in msg
    msg = raises(KeyError, map_flow, FLOW, "不存在的起点", "终点", "货量")
    assert "source" in msg and "不存在" in msg
    msg = raises(KeyError, map_flow, FLOW, "起点", "不存在的终点")
    assert "target" in msg and "不存在" in msg
    msg = raises(KeyError, map_flow, FLOW, "起点", "终点", "不存在的值")
    assert "value" in msg and "不存在" in msg
    msg = raises(ValueError, map_flow, FLOW, "起点", "终点", map="europe")
    assert 'map 只支持 "china"' in msg


# ---------------------------------------------------------------- 世界地图
def t_world_map():
    spec = _spec(geo_map(WORLD, "国家", "GDP", map="world"))
    assert spec["map"] == "world"
    assert _spec(map_bubble(WORLD, "国家", "GDP", map="world"))["map"] == "world"
    flow = pd.DataFrame({"起点": ["中国", "美国"], "终点": ["美国", "中国"], "值": [1, 2]})
    assert _spec(map_flow(flow, "起点", "终点", "值", map="world"))["map"] == "world"
    # 世界地图的中文国名在前端有别名表；Python 侧原样保留
    rows = geo_map(WORLD, "国家", "GDP", map="world").data["rows"]
    assert rows[0][0] == "美国"


# ---------------------------------------------------------------- HTML 产物
def t_chart_html():
    html = geo_map(DF, "省份", "销售额").to_html()
    assert len(html) > 1_000_000, "内联 HTML 应包含 echarts / eazy.js，实际 %d 字节" % len(html)
    assert "window.EAZY_MAPS" in html, "页面必须注入 window.EAZY_MAPS"
    assert '"china"' in html, "中国地图 GeoJSON 应被注入"
    assert "eazy_map.js" in html, "地图运行时 eazy_map.js 应被内联/引入"
    assert "registerMap" in html, "运行时需要调用 echarts.registerMap"
    # 世界地图页只注入 world 也要能工作
    html_world = geo_map(WORLD, "国家", "GDP", map="world").to_html()
    assert "window.EAZY_MAPS" in html_world and '"world"' in html_world
    assert '"china"' not in html_world.split("window.EAZY_DATA")[0], "未使用的地图不应注入"


def t_chart_save():
    chart = geo_map(DF, "省份", "销售额")
    tmpdir = tempfile.mkdtemp(prefix="eazy_map_save_")
    path = chart.save(os.path.join(tmpdir, "map.html"))
    assert os.path.isfile(path), path
    assert os.path.getsize(path) > 1_000_000
    with io.open(path, encoding="utf-8") as fh:
        html = fh.read()
    assert "<html" in html.lower()
    assert "window.EAZY_MAPS" in html, "save() 产物也必须注入地图数据"


def t_dashboard():
    page = eazy_data_viz.dashboard(
        [
            geo_map(DF, "省份", "销售额", title="区域填色"),
            map_bubble(DF, "省份", "销售额", size="订单数", title="气泡"),
            map_flow(FLOW, "起点", "终点", "货量", title="飞线"),
            geo_map(WORLD, "国家", "GDP", map="world", title="世界"),
        ],
        cols=2,
        title="地图看板",
    )
    tmpdir = tempfile.mkdtemp(prefix="eazy_map_dash_")
    path = page.save(os.path.join(tmpdir, "dash.html"))
    assert os.path.isfile(path)
    assert os.path.getsize(path) > 1_500_000
    with io.open(path, encoding="utf-8") as fh:
        html = fh.read()
    assert '"china"' in html and '"world"' in html, "看板里两种地图的 GeoJSON 都应注入"
    assert html.count("eazy-chart") >= 4, "看板应有 4 个图表格子"


def t_region_warning():
    """没匹配到的区域名要进 chart.warnings，而不是只在控制台里消失。"""
    df = DF.copy()
    df.loc[df.index[0], "省份"] = "火星省"
    ch = geo_map(df, "省份", "销售额")
    msgs = ch.warnings["warnings"]
    assert any("火星省" in m for m in msgs), msgs
    clean = geo_map(DF, "省份", "销售额")
    assert not [m for m in clean.warnings["warnings"] if "没匹配到内置中国地图" in m], clean.warnings


def t_known_region_keys():
    """known_region_keys() 要覆盖省份短名与城市名。"""
    keys = maps.known_region_keys("china")
    assert isinstance(keys, set)
    assert "广东" in keys and "内蒙古" in keys, "应包含省份短名"
    assert "吉林" in keys, "应包含省份/城市短名"
    assert "广州" in keys or "广东" in keys, "应包含城市或省份短名"
    assert len(keys) > 300, len(keys)
    world = maps.known_region_keys("world")
    assert len(world) > 100, len(world)


def t_geo_map_text_value_error():
    """文本 value 统一报中文 TypeError（此前 geo_map 会静默出空图）。"""
    bad = pd.DataFrame({"省份": ["广东省", "江苏省"], "销售额": ["a", "b"]})
    try:
        geo_map(bad, "省份", "销售额")
    except TypeError as err:
        assert "数值" in str(err), str(err)
    else:
        raise AssertionError("geo_map 用文本列应当报 TypeError")
    ok = pd.DataFrame({"省份": ["广东省", "江苏省"], "销售额": ["12", "34"]})
    geo_map(ok, "省份", "销售额")  # 纯数字文本可以自动转换，不报错


def t_map_flow_warning():
    """飞线的起点/终点没匹配上时，两条列都要有提示。"""
    flow = pd.DataFrame({"起点": ["北京", "火星市"], "终点": ["上海", "月宫市"], "货量": [1, 2]})
    ch = map_flow(flow, "起点", "终点", "货量")
    msgs = " ".join(ch.warnings["warnings"])
    assert "火星市" in msgs and "月宫市" in msgs, msgs


# ---------------------------------------------------------------- 运行
for _name, _fn in sorted((k[2:], v) for k, v in list(globals().items()) if k.startswith("t_")):
    check(_name, _fn)

print("PASS %d" % len(PASS))
if FAIL:
    print("FAIL %d" % len(FAIL))
    for _name, _tb in FAIL:
        print("\n--- %s ---\n%s" % (_name, _tb))
    sys.exit(1)
print("ALL OK:", ", ".join(PASS))
