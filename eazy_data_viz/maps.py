# -*- coding: utf-8 -*-
"""eazy_data_viz 地图图表 API：区域填色 / 气泡地图 / 飞线地图。

本模块只**新增**函数，不修改 ``eazy_data_viz.chart`` / ``frame`` / ``render`` /
``__init__``。所有函数最终都返回 :class:`eazy_data_viz.chart.Chart`；前端按
``spec["type"]``（= 函数名）在 ``EazyViz.extraBuilders`` 里查找构建器，
地图 GeoJSON 由 ``render.py`` 注入到页面的 ``window.EAZY_MAPS``。

分工约定（与 ``charts_extra.py`` 完全一致）：

* Python 只做「列名校验 + 角色声明 + 参数校验」，**聚合在前端完成**，
  这样联动过滤 / 下钻之后地图会自动按过滤后的数据重算；
* 图表类型名 = 函数名；
* 所有列名参数都用 :func:`frame.require_column` 校验，错误信息为中文并指明参数名；
* 区域名称的匹配（短名「广东」 ⇄ 全名「广东省」）在前端完成，规则写在
  ``assets/eazy_map.js`` 的 ``normalizeRegion`` 里，Python 侧的
  :func:`normalize_region` 与之保持同一套规则，方便用户预处理数据。

三个函数的分工：

===============  ==========================================================
函数              适合表达
===============  ==========================================================
``geo_map``       单指标在区域上的高低分布（填色热力），最常用
``map_bubble``    单/双指标的大小对比，或按颜色分组对比（一省多组时并排）
``map_flow``      两个区域之间的流向与流量（需要 source / target 两列）
===============  ==========================================================

用法示例::

    import eazy_data_viz as edv
    from eazy_data_viz.maps import geo_map, map_bubble, map_flow

    df = edv.sample_df()
    geo_map(df, region="省份", value="销售额", title="销售额区域分布")
    map_bubble(df, region="省份", value="销售额", size="订单数")
    map_flow(df, source="渠道", target="产品", value="销售额")
"""
from __future__ import annotations

import io
import json
import math
import os

from . import frame as _frame
from . import palette as _palette
from .chart import Chart, _base_spec, _check_agg

__all__ = [
    "geo_map",
    "map_bubble",
    "map_flow",
    "MAPS",
    "province_centers",
    "normalize_region",
]

# 内置地图名（与 assets/maps/<name>.json 一一对应）
MAPS = ("china", "world")

# 地图显示名，用于自动标题 / 报错提示
_MAP_LABELS = {"china": "中国", "world": "世界"}

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_MAPS_DIR = os.path.join(_ASSETS_DIR, "maps")

# GeoJSON / 质心缓存（进程级，避免反复读 1MB 的 world.json）
_GEO_CACHE = {}
_CENTERS_CACHE = {}

# 中国行政区全名后缀（按「从长到短」顺序匹配，循环剥离直到稳定）。
# 注意：这份列表与 assets/eazy_map.js 的 SUFFIXES 必须保持一致。
_ADMIN_SUFFIXES = (
    "特别行政区",
    "维吾尔自治区",
    "壮族自治区",
    "回族自治区",
    "自治区",
    "自治州",
    "自治县",
    "自治旗",
    "土家族",
    "苗族",
    "侗族",
    "瑶族",
    "彝族",
    "藏族",
    "羌族",
    "白族",
    "傣族",
    "哈尼族",
    "景颇族",
    "傈僳族",
    "拉祜族",
    "佤族",
    "纳西族",
    "朝鲜族",
    "满族",
    "水族",
    "仡佬族",
    "布依族",
    "黎族",
    "畲族",
    "仫佬族",
    "毛南族",
    "京族",
    "省",
    "市",
    "地区",
    "盟",
    "林区",
    "矿区",
    "维吾尔",
    "壮族",
    "回族",
    "蒙古族",
)

# 需要从名称里直接抹掉的空白 / 间隔符号（中英文混排时避免 "W. Sahara" 匹配不上）
_SPACES = ("\u3000", " ", "\t", "\r", "\n", "·", "・", ".", "。", "—", "-")


# ==========================================================================
# 内部：参数校验
# ==========================================================================
def _check_map(map_name):
    """校验 map 参数，返回规范化后的地图名。"""
    if map_name is None:
        return "china"
    if not isinstance(map_name, str):
        raise ValueError(
            'map 只支持 "china"（中国）/ "world"（世界），收到 %r。' % (map_name,)
        )
    name = map_name.strip().lower()
    if name not in MAPS:
        raise ValueError(
            'map 只支持 "china"（中国）/ "world"（世界），收到 %r。' % (map_name,)
        )
    return name


def _check_str(value, name, allow_none=True):
    """校验字符串参数（列名之类）。"""
    if value is None:
        if allow_none:
            return None
        raise ValueError("%s 不能为空。" % name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s 需要是非空字符串，收到 %r。" % (name, value))
    return value


def _check_number(value, name, *, positive=False):
    """校验数值参数（None 放行），返回 float 或 None。"""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s 需要是数字，收到 %r。" % (name, value))
    v = float(value)
    if not math.isfinite(v):
        raise ValueError("%s 需要是有限数字，收到 %r。" % (name, value))
    if positive and v <= 0:
        raise ValueError("%s 需要大于 0，收到 %r。" % (name, value))
    return v


def _check_min_max(min_value, max_value):
    """校验 visualMap 的上下限。"""
    lo = _check_number(min_value, "min_value")
    hi = _check_number(max_value, "max_value")
    if lo is not None and hi is not None and lo >= hi:
        raise ValueError(
            "min_value 必须小于 max_value，收到 min_value=%r、max_value=%r。"
            "（如果只想固定一端，另一端请传 None）" % (min_value, max_value)
        )
    return lo, hi


def _check_name_map(name_map):
    """校验名称映射表：{"数据里的原值": "地图里的区域名"}。"""
    if name_map is None:
        return None
    if not isinstance(name_map, dict):
        raise TypeError(
            "name_map 需要是 dict，例如 name_map={'USA': 'United States'}，收到 %r。"
            % (type(name_map).__name__,)
        )
    out = {}
    for key, val in name_map.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("name_map 的键需要是非空字符串（数据里的原值），收到 %r。" % (key,))
        if not isinstance(val, str) or not val.strip():
            raise ValueError(
                "name_map 的值需要是非空字符串（地图里的区域名），收到 %r: %r。"
                % (key, val)
            )
        out[key] = val
    return out or None


def _check_zoom(zoom):
    """校验 zoom 参数（地图里表示是否允许缩放/平移）。"""
    if zoom in (None, True, False, "auto"):
        return zoom
    if zoom in ("scale", "move"):
        return zoom
    raise ValueError(
        "zoom 只支持 None / True / False / 'auto'（地图里表示是否允许鼠标缩放和平移），"
        "收到 %r。" % (zoom,)
    )


def _check_palette(palette):
    """校验配色名（复用 palette.check 的中文报错）。"""
    if palette is None:
        return None
    return _palette.check(palette)


def _check_bubble_sizes(min_size, max_size):
    """校验气泡半径范围。"""
    lo = _check_number(min_size, "min_size")
    hi = _check_number(max_size, "max_size")
    if lo is None or hi is None:
        raise ValueError("min_size / max_size 不能为 None。")
    if lo <= 0 or hi <= 0:
        raise ValueError(
            "min_size / max_size 需要大于 0，收到 min_size=%r、max_size=%r。"
            % (min_size, max_size)
        )
    if lo >= hi:
        raise ValueError(
            "min_size 必须小于 max_size，收到 min_size=%r、max_size=%r。"
            % (min_size, max_size)
        )
    return lo, hi


def _require_columns(df, pairs):
    """批量校验列存在（``pairs`` 是 [(参数名, 列名), ...]）。"""
    for role, col in pairs:
        _frame.require_column(df, col, role)


def _check_agg_arg(agg):
    """校验 agg（value 为空时前端会按 count 处理，这里仍先校验用户输入）。"""
    _check_agg(agg)
    return agg


def _drill_dims(drill, region, df):
    """地图的下钻维度：固定以 region 列开头，并保证至少两层以启用点击下钻。

    地图没有城市级 GeoJSON，所以 ``drill`` 的语义是「点击某个区域后，
    地图只保留该区域数据（单层聚焦）」；第一层永远是 ``region`` 列。
    """
    if drill is None:
        return None
    if isinstance(drill, str):
        dims = [drill]
    elif isinstance(drill, (list, tuple)):
        dims = [str(d) for d in drill if d is not None]
    else:
        raise TypeError("drill 需要是列名或列名列表，例如 drill=['省份', '城市']，收到 %r。" % (drill,))
    if not dims:
        raise ValueError("drill 不能是空列表；不需要下钻请传 drill=None。")
    for dim in dims:
        _frame.require_column(df, dim, "下钻维度", "drill 里的每一列都必须是 df 的列名。")
    if dims[0] != region:
        dims = [region] + dims
    if len(dims) == 1:
        # 单层聚焦：复制一份 region，让运行时的「点击 → 过滤」逻辑生效
        dims = dims + [region]
    return dims


# ==========================================================================
# 内部：GeoJSON / 质心
# ==========================================================================
def _load_geo(map_name):
    """读取内置 GeoJSON（带进程级缓存）。"""
    if map_name in _GEO_CACHE:
        return _GEO_CACHE[map_name]
    path = os.path.join(_MAPS_DIR, map_name + ".json")
    if not os.path.isfile(path):
        raise FileNotFoundError(
            "内置地图文件缺失：%s。请确认 eazy_data_viz/assets/maps/ 下存在 %s.json。"
            % (path, map_name)
        )
    with io.open(path, encoding="utf-8") as f:
        geo = json.load(f)
    if not isinstance(geo, dict) or geo.get("type") != "FeatureCollection":
        raise ValueError("内置地图 %s 不是合法的 GeoJSON FeatureCollection。" % path)
    _GEO_CACHE[map_name] = geo
    return geo


def _iter_points(coords):
    """递归遍历 GeoJSON coordinates，产出所有 (经度, 纬度) 点。"""
    stack = [coords]
    while stack:
        cur = stack.pop()
        if not cur:
            continue
        first = cur[0]
        if isinstance(first, (int, float)):
            if len(cur) >= 2:
                yield cur[0], cur[1]
        else:
            stack.extend(cur)


def _feature_center(feature):
    """取一个 feature 的中心点：优先 properties 的 cp/center/centroid，否则顶点均值。"""
    props = feature.get("properties") or {}
    for key in ("cp", "center", "centroid"):
        point = props.get(key)
        if isinstance(point, (list, tuple)) and len(point) >= 2:
            try:
                lng, lat = float(point[0]), float(point[1])
            except (TypeError, ValueError):
                continue
            if -180.0 <= lng <= 180.0 and -90.0 <= lat <= 90.0:
                return [round(lng, 4), round(lat, 4)]
    geometry = feature.get("geometry") or {}
    coords = geometry.get("coordinates")
    if not coords:
        return None
    sx = sy = 0.0
    count = 0
    for lng, lat in _iter_points(coords):
        try:
            x, y = float(lng), float(lat)
        except (TypeError, ValueError):
            continue
        if not (math.isfinite(x) and math.isfinite(y)):
            continue
        sx += x
        sy += y
        count += 1
    if not count:
        return None
    return [round(sx / count, 4), round(sy / count, 4)]


def _region_centers(map_name="china"):
    """{地图区域全名: [经度, 纬度]}（内部使用，可能包含空名称之外的区域）。"""
    key = _check_map(map_name)
    if key in _CENTERS_CACHE:
        return dict(_CENTERS_CACHE[key])
    out = {}
    for feature in _load_geo(key).get("features") or []:
        props = feature.get("properties") or {}
        name = props.get("name")
        if not name:
            # 中国地图里有一个空的南海诸岛占位 feature，跳过
            continue
        center = _feature_center(feature)
        if center is not None:
            out[str(name)] = center
    _CENTERS_CACHE[key] = out
    return dict(out)


def normalize_region(name):
    """把区域名归一化成「短名」，用于跨数据源匹配地图区域。

    规则（与 ``assets/eazy_map.js`` 的 ``normalizeRegion`` 完全一致）：

    * 去掉空格、``·``、``.`` 等间隔符号；
    * 循环去掉中国行政区后缀：``省`` / ``市`` / ``自治区`` / ``特别行政区`` /
      ``自治州`` / ``自治县`` / ``壮族`` / ``回族`` / ``维吾尔`` / ``土家族`` / ``苗族`` 等。

    例::

        >>> normalize_region("广东省")
        '广东'
        >>> normalize_region("内蒙古自治区")
        '内蒙古'
        >>> normalize_region("广西壮族自治区")
        '广西'
        >>> normalize_region("香港特别行政区")
        '香港'
        >>> normalize_region("United States")
        'United States'

    注意：英文名不做大小写转换（前端比较时会 ``toLowerCase``），
    所以 ``normalize_region("W. Sahara")`` 返回 ``"WSahara"``。
    """
    if name is None:
        return ""
    s = str(name).strip()
    for ch in _SPACES:
        if ch in s:
            s = s.replace(ch, "")
    changed = True
    while changed and s:
        changed = False
        for suffix in _ADMIN_SUFFIXES:
            if len(s) > len(suffix) and s.endswith(suffix):
                s = s[: -len(suffix)]
                changed = True
                break
    return s


def province_centers():
    """返回中国省级行政区的中心点坐标：``{短名: [经度, 纬度]}``。

    中心点优先取 GeoJSON 里的 ``properties.center/centroid``，没有时用多边形
    所有顶点的平均值。返回值是**副本**，可以随意修改，不会影响内部缓存。

    例::

        >>> centers = province_centers()
        >>> centers["广东"]
        [113.4061, 23.1423]
        >>> centers["北京"][0] > 100
        True
    """
    if "china" not in _CENTERS_CACHE:
        _region_centers("china")
    out = {}
    for full_name, center in _CENTERS_CACHE["china"].items():
        out[normalize_region(full_name)] = list(center)
    return out


def region_centers(map_name="china"):
    """返回指定地图的 ``{区域全名: [经度, 纬度]}``（质心，自动从 GeoJSON 计算）。

    一般不需要直接调用：``map_bubble`` / ``map_flow`` 在前端会自动算质心。
    这个函数主要用于「自己算距离 / 画别的图」等高级场景。

    :param map_name: ``"china"`` 或 ``"world"``。
    """
    return _region_centers(map_name)


# ==========================================================================
# 内部：spec 组装
# ==========================================================================
def _map_spec(
    kind,
    data,
    roles,
    *,
    title,
    subtitle,
    map_name,
    fmt,
    height,
    theme,
    agg,
    legend,
    labels,
    zoom,
    drill,
    link,
    palette,
    section,
    min_value=None,
    max_value=None,
    name_map=None,
    extra_roles=None,
    extra_spec=None,
    max_rows=_frame.MAX_ROWS,
):
    """组装地图类图表的 spec（校验统一委托给 ``_base_spec``）。"""
    spec_roles = dict(roles)
    if extra_roles:
        spec_roles.update(extra_roles)
    spec, records, ref, info = _base_spec(
        kind,
        data,
        spec_roles,
        title=title,
        subtitle=subtitle,
        xtitle=None,
        ytitle=None,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        theme=theme,
        agg=agg,
        sort=None,
        top_n=None,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=drill,
        link=link,
        max_rows=max_rows,
        map=map_name,
        minValue=min_value,
        maxValue=max_value,
        nameMap=name_map,
    )
    if extra_spec:
        spec.update(extra_spec)
    if palette is not None:
        spec["palette"] = palette
    if section:
        spec["section"] = section
    return spec, records, ref, info


# ==========================================================================
# 1. geo_map —— 区域填色地图
# ==========================================================================
_REGION_KEYS_CACHE = {}


def known_region_keys(map_name="china"):
    """内置地图能识别的区域名（已 :func:`normalize_region` 归一化）。

    中国地图同时包含省级与城市级名称（城市来自 ``china_cities.json``）；
    世界地图只有 GeoJSON 里的国家名。返回值是新的 ``set``，可以随意改动。
    """
    cached = _REGION_KEYS_CACHE.get(map_name)
    if cached is not None:
        return set(cached)
    keys = set()
    for name in region_centers(map_name):
        key = normalize_region(name)
        if key:
            keys.add(key)
    if map_name == "china":
        path = os.path.join(_MAPS_DIR, "china_cities.json")
        if os.path.exists(path):
            with io.open(path, encoding="utf-8") as fh:
                cities = json.load(fh)
            for name in cities:
                key = normalize_region(name)
                if key:
                    keys.add(key)
    _REGION_KEYS_CACHE[map_name] = keys
    return set(keys)


def _region_warning(df, region, map_name, name_map=None):
    """检查 region 列有多少值匹配不到地图，返回提示文案或 None（不抛异常）。"""
    if map_name != "china":
        return None
    known = _REGION_KEYS_CACHE.get(map_name) or known_region_keys(map_name)
    if not known:
        return None
    raw = []
    for v in df[region].dropna().unique():
        v = str(v)
        if v not in raw:
            raw.append(v)
    miss = []
    for v in raw:
        key = normalize_region(v)
        if name_map and v in name_map:
            key = normalize_region(name_map[v])
        if key and key not in known:
            miss.append(v)
    if not miss:
        return None
    miss.sort()
    head = "、".join(miss[:6])
    more = "" if len(miss) <= 6 else " 等 %d 个" % len(miss)
    return (
        "%s 列有 %d 个区域名没匹配到内置中国地图，地图上不会显示这些数据：%s%s。"
        "可用 eazy_data_viz.maps.normalize_region() 自查，或用 name_map 改名。"
        % (region, len(miss), head, more))


def _coerce_numeric(df, cols):
    """把文本型数字列转成数值；某一列几乎无法转数值时抛 ``TypeError``。

    ``cols`` 是 ``[(参数说明, 列名), ...]``，``列名`` 为 ``None`` 时跳过。
    """
    import pandas as pd

    copy = None
    for label, col in cols:
        if col is None:
            continue
        if _frame.column_kind(df[col]) in (_frame.KIND_NUM, _frame.KIND_TIME):
            continue
        conv = pd.to_numeric(df[col], errors="coerce")
        if conv.notna().mean() < 0.99 or conv.notna().sum() == 0:
            bad = df[col].dropna().head(3).tolist()
            raise TypeError(
                "%s %r 需要是数值类型（当前是文本，例如 %r）。"
                "请先用 pd.to_numeric() 清洗，或换一列。" % (label, col, bad))
        if copy is None:
            copy = df.copy()
        copy[col] = conv
    return df if copy is None else copy


def geo_map(
    data,
    region,
    value=None,
    *,
    map="china",
    agg="sum",
    fmt="compact",
    labels=True,
    min_value=None,
    max_value=None,
    name_map=None,
    zoom=None,
    palette=None,
    height=460,
    theme="light",
    title=None,
    subtitle=None,
    drill=None,
    link=None,
    legend=True,
    section=None,
):
    """区域填色地图：用颜色深浅表达一个指标在各省 / 各国上的高低。

    ``region`` 列可以是短名（``"广东"``）也可以是全名（``"广东省"``），
    前端会自动归一化后与内置 GeoJSON 匹配；匹配不到的区域显示为「无数据色」。

    示例
    ----
    >>> eazy_data_viz.maps.geo_map(df, region="省份", value="销售额")
    >>> eazy_data_viz.maps.geo_map(df, region="大区", map="china", min_value=0,
    ...                            max_value=100000)

    参数
    ----
    ``data`` / ``region`` / ``value`` / ``map`` / ``agg`` / ``fmt`` /
    ``labels`` / ``min_value`` / ``max_value`` / ``name_map`` / ``zoom`` /
    ``palette`` / ``height`` / ``theme`` / ``title`` / ``subtitle`` /
    ``drill`` / ``link`` / ``legend`` / ``section`` 的含义见 ``docs/api/geo_map.md``；
    其余函数（``map_bubble`` / ``map_flow``）的公共参数含义与此一致。
    """
    df = _frame.ensure_frame(data)
    region = _check_str(region, "region（区域列）", allow_none=False)
    _check_map(map)
    _check_agg_arg(agg)
    min_value, max_value = _check_min_max(min_value, max_value)
    name_map = _check_name_map(name_map)
    zoom = _check_zoom(zoom)
    palette = _check_palette(palette)
    _require_columns(df, [("region（区域列）", region)])
    if value is not None:
        value = _check_str(value, "value（数值列）", allow_none=False)
        _require_columns(df, [("value（数值列）", value)])
        df = _coerce_numeric(df, [("value（数值列）", value)])
    drills = _drill_dims(drill, region, df)
    if title is None:
        title = "%s · %s地图" % (value or "记录数", _MAP_LABELS[_check_map(map)])
    spec, records, ref, info = _map_spec(
        "geo_map",
        df,
        {"region": region, "value": value, "x": region},
        title=title,
        subtitle=subtitle,
        map_name=_check_map(map),
        fmt=fmt,
        height=height,
        theme=theme,
        agg=("count" if value is None else agg),
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=drills,
        link=link,
        palette=palette,
        section=section,
        min_value=min_value,
        max_value=max_value,
        name_map=name_map,
    )
    _warn = _region_warning(df, region, _check_map(map), name_map)
    if _warn:
        info.setdefault("warnings", []).append(_warn)
    return Chart(spec, records, ref, info)


# ==========================================================================
# 2. map_bubble —— 气泡地图
# ==========================================================================
def map_bubble(
    data,
    region,
    value=None,
    *,
    map="china",
    agg="sum",
    size=None,
    color=None,
    fmt="compact",
    min_size=4,
    max_size=28,
    name_map=None,
    zoom=None,
    palette=None,
    height=460,
    theme="light",
    title=None,
    subtitle=None,
    drill=None,
    link=None,
    legend=True,
    section=None,
):
    """气泡地图：在省份 / 国家中心点画气泡，气泡大小和颜色可以再编码两个指标。

    * ``value``：默认控制气泡大小（没有 ``size`` 时），同时用于 tooltip；
    * ``size``：第二指标，优先用它控制气泡半径；
    * ``color``：分组列（例如产品/渠道），一个区域有多组时并排画多个气泡。

    示例
    ----
    >>> eazy_data_viz.maps.map_bubble(df, region="省份", value="销售额")
    >>> eazy_data_viz.maps.map_bubble(df, region="省份", value="销售额",
    ...                               size="订单数", color="产品")
    """
    df = _frame.ensure_frame(data)
    region = _check_str(region, "region（区域列）", allow_none=False)
    _check_map(map)
    _check_agg_arg(agg)
    name_map = _check_name_map(name_map)
    zoom = _check_zoom(zoom)
    palette = _check_palette(palette)
    min_size, max_size = _check_bubble_sizes(min_size, max_size)
    _require_columns(df, [("region（区域列）", region)])
    if value is not None:
        value = _check_str(value, "value（数值列）", allow_none=False)
    if size is not None:
        size = _check_str(size, "size（气泡大小列）", allow_none=False)
    if color is not None:
        color = _check_str(color, "color（分组列）", allow_none=False)
    if value is not None and value == region:
        raise ValueError("value 不能与 region 是同一列：region 是区域名，value 是数值。")
    if size is not None and size == region:
        raise ValueError("size 不能与 region 是同一列：region 是区域名，size 是数值。")
    if color is not None and color == region:
        raise ValueError("color 不能与 region 是同一列：region 是区域名，color 是分组列。")
    _require_columns(
        df,
        [("value（数值列）", value), ("size（气泡大小列）", size), ("color（分组列）", color)]
        if (value or size or color)
        else [],
    )
    # 数值列做一次清洗：文本数字自动转数值，转不了就报错
    df = _coerce_numeric(
        df, [("value（数值列）", value), ("size（气泡大小列）", size)])
    drills = _drill_dims(drill, region, df)
    if title is None:
        title = "%s · %s气泡地图" % (value or "记录数", region)
    spec, records, ref, info = _map_spec(
        "map_bubble",
        df,
        {"region": region, "value": value, "size": size, "color": color, "x": region},
        title=title,
        subtitle=subtitle,
        map_name=_check_map(map),
        fmt=fmt,
        height=height,
        theme=theme,
        agg=("count" if value is None else agg),
        legend=legend,
        labels=False,
        zoom=zoom,
        drill=drills,
        link=link,
        palette=palette,
        section=section,
        min_value=None,
        max_value=None,
        name_map=name_map,
        extra_spec={"minSize": min_size, "maxSize": max_size},
    )
    _warn = _region_warning(df, region, _check_map(map), name_map)
    if _warn:
        info.setdefault("warnings", []).append(_warn)
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3. map_flow —— 飞线地图
# ==========================================================================
def map_flow(
    data,
    source,
    target,
    value=None,
    *,
    map="china",
    agg="sum",
    fmt="compact",
    name_map=None,
    zoom=None,
    palette=None,
    height=460,
    theme="light",
    title=None,
    subtitle=None,
    link=None,
    legend=True,
    section=None,
):
    """飞线地图：把一条数据当作「source → target」的流量，在地图上画动态飞线。

    线宽和颜色都随数值变化（值越大线越粗、颜色越靠「高热」端）。
    聚合在前端完成：先按 source/target 分组，再按 ``agg`` 汇总 ``value``。

    示例
    ----
    >>> eazy_data_viz.maps.map_flow(df, source="渠道", target="产品", value="销售额")
    >>> eazy_data_viz.maps.map_flow(df, source="大区", target="省份", value="利润")
    """
    df = _frame.ensure_frame(data)
    source = _check_str(source, "source（起点列）", allow_none=False)
    target = _check_str(target, "target（终点列）", allow_none=False)
    _check_map(map)
    _check_agg_arg(agg)
    name_map = _check_name_map(name_map)
    zoom = _check_zoom(zoom)
    palette = _check_palette(palette)
    if source == target:
        raise ValueError(
            "source 和 target 不能是同一列：飞线图需要「起点 → 终点」两个不同的区域列。"
        )
    _require_columns(df, [("source（起点列）", source), ("target（终点列）", target)])
    if value is not None:
        value = _check_str(value, "value（数值列）", allow_none=False)
        _require_columns(df, [("value（数值列）", value)])
        df = _coerce_numeric(df, [("value（数值列）", value)])
    if title is None:
        title = "%s → %s 流向" % (source, target)
    spec, records, ref, info = _map_spec(
        "map_flow",
        df,
        {"source": source, "target": target, "value": value, "x": source},
        title=title,
        subtitle=subtitle,
        map_name=_check_map(map),
        fmt=fmt,
        height=height,
        theme=theme,
        agg=("count" if value is None else agg),
        legend=legend,
        labels=True,
        zoom=zoom,
        drill=None,
        link=link,
        palette=palette,
        section=section,
        min_value=None,
        max_value=None,
        name_map=name_map,
    )
    for _col in (source, target):
        _warn = _region_warning(df, _col, _check_map(map), name_map)
        if _warn and _warn not in info.setdefault("warnings", []):
            info["warnings"].append(_warn)
    return Chart(spec, records, ref, info)
