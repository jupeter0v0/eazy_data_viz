# -*- coding: utf-8 -*-
"""eazy_data_viz 扩展图表 API（瀑布图 / 子弹图 / 雷达 / 桑基 / K 线 / 驾驶舱组件 …）。

本模块只**新增**函数，不修改 ``eazy_data_viz.chart`` / ``eazy_data_viz.frame`` / ``eazy_data_viz.render`` /
``eazy_data_viz.__init__``。所有函数最终都返回 :class:`eazy_data_viz.chart.Chart`；前端按
``spec["type"]``（= 函数名）在 ``EazyViz.extraBuilders`` / ``EazyViz.htmlBuilders``
里查找构建器。

分工约定（详见 ``docs/EXTRA_CHARTS.md``）：

* Python 只做「列名校验 + 角色声明 + 少量预计算」（相关系数、回归系数、中位数、
  分组指标等），**聚合一律交给前端**，这样联动过滤 / 下钻后能自动重算；
* 图表类型名 = 函数名；
* 所有列名参数都用 :func:`frame.require_column` 校验，错误信息为中文并指明参数名。

用法示例::

    import eazy_data_viz
    import eazy_data_viz.charts_extra as px

    px.waterfall(df, x="月份", y="利润", title="利润瀑布")
    px.matrix(df)
    px.ring_progress(72.5, label="完成率")
"""
from __future__ import annotations

import base64
import math
import os

import numpy as np
import pandas as pd

from . import frame as _frame
from . import metric as _metric
from .metric import Follow
from .chart import (
    AGGS,
    Chart,
    _COMMON_DOC,
    _base_spec,
    _check_agg,
    _check_fmt,
    _check_lim,
    _next_id,
    _parse_link,
)

__all__ = [
    "waterfall",
    "bullet",
    "lollipop",
    "dumbbell",
    "pareto",
    "slope",
    "bump",
    "radar",
    "rose",
    "parallel",
    "pictorial",
    "target",
    "trend",
    "quadrant",
    "matrix",
    "sparkline",
    "ring_progress",
    "sunburst",
    "tree",
    "sankey",
    "graph",
    "theme_river",
    "calendar",
    "gantt",
    "candlestick",
    "pyramid",
    "area_pct",
    "bar_pct",
    "progress",
    "tile",
    "table",
    "wordcloud",
    "group_kpi",
]


# ==========================================================================
# 内部工具
# ==========================================================================
def _ext(
    kind,
    data,
    roles,
    *,
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    xlim=None,
    ylim=None,
    fmt="compact",
    height=380,
    abs_height=False,
    theme="light",
    agg="sum",
    sort=None,
    top_n=None,
    legend=False,
    labels=False,
    zoom="auto",
    drill=None,
    link=None,
    max_rows=_frame.MAX_ROWS,
    **extra
):
    """``_base_spec`` 的轻量包装：给扩展图表一套统一的默认值。"""
    return _base_spec(
        kind,
        data,
        roles,
        title=title,
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=agg,
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=drill,
        link=link,
        max_rows=max_rows,
        **extra
    )


def _manual_spec(
    kind,
    *,
    title=None,
    subtitle=None,
    theme="light",
    height=380,
    abs_height=False,
    fmt=None,
    agg="sum",
    sort=None,
    top_n=None,
    roles=None,
    xtitle=None,
    ytitle=None,
    xlim=None,
    ylim=None,
    legend=False,
    labels=False,
    zoom=False,
    link=None,
    **extra
):
    """手工构造 spec（不接 DataFrame 的图：matrix / ring_progress / group_kpi）。"""
    agg = _check_agg(agg or "sum")
    _check_fmt(fmt)
    if theme not in ("light", "dark"):
        raise ValueError('theme 只支持 "light" / "dark"，收到 %r' % (theme,))
    if height is not None and (not isinstance(height, (int, float)) or height < 120):
        raise ValueError("height 至少 120（像素），收到 %r" % (height,))
    if top_n is not None:
        if not isinstance(top_n, int) or isinstance(top_n, bool) or top_n < 1:
            raise ValueError("top_n 需要是 >=1 的整数（只显示前 N 项），收到 %r" % (top_n,))
    _link_group, _link_mode = _parse_link(link)
    spec = {
        "id": _next_id(),
        "type": kind,
        "title": title,
        "subtitle": subtitle,
        "theme": theme,
        "height": int(height if height is not None else 380),
        "absHeight": bool(abs_height),
        "dataRef": None,
        "roles": dict(roles or {}),
        "agg": agg,
        "fmt": fmt or "compact",
        "sort": sort,
        "topN": top_n,
        "xtitle": xtitle,
        "ytitle": ytitle,
        "xlim": _check_lim(xlim, "xlim"),
        "ylim": _check_lim(ylim, "ylim"),
        "legend": bool(legend),
        "labels": bool(labels),
        "zoom": zoom,
        "drill": None,
        "link": _link_group,
        "linkMode": _link_mode,
    }
    spec.update(extra)
    return spec


def _empty_chart(spec):
    """不嵌入记录集的图（数据已预计算进 spec）。"""
    return Chart(spec, {"cols": [], "rows": [], "n": 0}, None, {})


def _as_list(value):
    """把可选列名参数统一成列表（None → []，单值 → [值]）。"""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _require_cols(df, pairs):
    """批量校验列存在；``pairs`` 是 [(参数名, 列名或列名列表), ...]。"""
    for role, col in pairs:
        if isinstance(col, (list, tuple)):
            for c in col:
                if c is not None:
                    _frame.require_column(df, c, role)
        else:
            _frame.require_column(df, col, role)


def _coerce_numeric(data, pairs, agg=None):
    """校验数值列；object 里近似全数字的列自动转成数值（返回可能复制过的 df）。"""
    df = _frame.ensure_frame(data)
    copy = None
    for role, col in pairs:
        if col is None:
            continue
        if _metric.is_follow(col):
            continue
        # agg="count"/"unique"（或 edv.column 登记成这两者）时，文本列也合法。
        if (agg if agg is not None else _metric.agg_for(col)) in ("count", "unique"):
            _frame.require_column(df, col, role)
            continue
        _frame.require_column(df, col, role)
        kind = _frame.column_kind(df[col])
        if kind == _frame.KIND_NUM:
            continue
        if kind == _frame.KIND_TIME:
            raise TypeError(
                "%s列 %r 需要是数值类型，但当前是日期时间类型。请换一列。" % (role, col)
            )
        conv = pd.to_numeric(df[col], errors="coerce")
        total = int(conv.notna().sum())
        if total == 0:
            raise TypeError(
                "%s列 %r 里没有可用的数值（整列为空或全是文本）。"
                "请先清洗这一列，或换一列。" % (role, col)
            )
        if conv.notna().mean() < 0.99:
            bad = df[col].dropna().head(3).tolist()
            raise TypeError(
                "%s列 %r 需要是数值类型（当前是文本，例如 %r）。"
                "请先用 pd.to_numeric() 清洗，或换一列。" % (role, col, bad)
            )
        if copy is None:
            copy = df.copy()
        copy[col] = conv
    return copy if copy is not None else df


def _coerce_time(data, pairs):
    """校验日期列；object 日期字符串转成 datetime（返回可能复制过的 df）。"""
    df = _frame.ensure_frame(data)
    copy = None
    for role, col in pairs:
        if col is None or _metric.is_follow(col):
            continue
        _frame.require_column(df, col, role)
        kind = _frame.column_kind(df[col])
        if kind == _frame.KIND_TIME:
            continue
        if kind == _frame.KIND_NUM:
            raise TypeError(
                "%s列 %r 需要是日期/时间类型，但当前是数值类型。请换一列。"
                "（例如 gantt(df, task=\"任务\", start=start_col, end=end_col)）" % (role, col)
            )
        conv = pd.to_datetime(df[col], errors="coerce")
        if not bool(conv.notna().any()):
            bad = df[col].dropna().head(3).tolist()
            raise TypeError(
                "%s列 %r 无法解析为日期（例如 %r）。请先用 pd.to_datetime() 转换。"
                % (role, col, bad)
            )
        if not bool(conv.notna().all()):
            bad = df[col][conv.isna()].head(3).tolist()
            raise ValueError(
                "%s列 %r 存在无法解析为日期的值（例如 %r），请先清洗。"
                % (role, col, bad)
            )
        if copy is None:
            copy = df.copy()
        copy[col] = conv
    return copy if copy is not None else df


def _pick_dim(df):
    """自动挑一个类目列（优先文本分类，其次时间）。"""
    for c in df.columns:
        if _frame.column_kind(df[c]) == _frame.KIND_CAT:
            return c
    for c in df.columns:
        if _frame.column_kind(df[c]) == _frame.KIND_TIME:
            return c
    return None


def _pick_num(df):
    """自动挑第一个数值列。"""
    for c in df.columns:
        if _frame.column_kind(df[c]) == _frame.KIND_NUM:
            return c
    return None


def _apply_agg(values, agg):
    """在 Python 侧对一小段数据做聚合（只用于预计算类图表）。"""
    if agg == "unique":
        seen = set()
        for v in values:
            if v is None:
                continue
            try:
                if v != v:  # NaN
                    continue
            except Exception:
                pass
            text = str(v)
            if text != "":
                seen.add(text)
        return float(len(seen))
    clean = []
    for v in values:
        if v is None:
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if not math.isnan(f) and not math.isinf(f):
            clean.append(f)
    if agg == "count":
        return float(len(clean))
    if not clean:
        return 0.0
    s = pd.Series(clean, dtype="float64")
    return float(getattr(s, agg)())


def _num_param(value, name):
    """把用户显式传入的数值参数转成 float；不可转换时给出明确报错（不要静默变 None）。"""
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("%s 需要是数字，收到 %r。" % (name, value))
    try:
        f = float(value)
    except (TypeError, ValueError):
        raise ValueError("%s 需要是数字，收到 %r。" % (name, value))
    if math.isnan(f) or math.isinf(f):
        raise ValueError("%s 不能是 NaN / Inf。" % (name,))
    return f


def _num_or_none(value):
    """numpy / pandas 标量 → 可 JSON 的 float 或 None（NaN/Inf → None）。"""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


# ==========================================================================
# 3.1 waterfall 瀑布图
# ==========================================================================
def waterfall(
    data: pd.DataFrame,
    x: str | None,
    y: str | None | Follow = None,
    *,
    agg: str | None = None,
    total: bool = None,
    sort: str | None = None,
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    xlim: tuple | None = None,
    ylim: tuple | None = None,
    fmt: str = "compact",
    height: int = 380,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = False,
    labels: bool = False,
    zoom: bool | str = "auto",
    drill: list[str] | None = None,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """瀑布图：各分项正负增量逐段累加，直观看到「从哪来、累计到多少」。

    示例
    ----
    >>> eazy_data_viz.charts_extra.waterfall(df, x="科目", y="金额", total=True)
    """
    df = _frame.ensure_frame(data)
    _frame.require_column(df, x, "x（类目）")
    if x is None:
        raise ValueError('waterfall 需要 x（类目列），例如 waterfall(df, x="月份", y="利润")。')
    if y is not None:
        df = _coerce_numeric(df, [("y（数值）", y)], agg=agg)
    spec, records, ref, info = _ext(
        "waterfall",
        df,
        {"x": x, "y": y},
        title=title if title is not None else "%s 瀑布图" % (y or "记录数"),
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=("count" if (y is None and agg != "unique") else agg),
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=drill,
        link=link,
        max_rows=max_rows,
        total=bool(total),
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.2 bullet 子弹图
# ==========================================================================
def bullet(
    data: pd.DataFrame,
    x: str | None,
    actual: str | None,
    target: str | None = None,
    *,
    target_value: str | None = None,
    agg: str | None = None,
    sort: str | None = None,
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    xlim: tuple | None = None,
    ylim: tuple | None = None,
    fmt: str = "compact",
    height: int = 380,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = False,
    labels: bool = False,
    zoom: bool | str = False,
    drill: list[str] | None = None,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """子弹图：每类一个实际值，对比目标值（横向，目标用刻度线表示）。

    ``target`` 可以是列名；传常数（如 ``target=100``）或 ``target_value=100``
    表示所有类目共用一个目标。

    示例
    ----
    >>> eazy_data_viz.charts_extra.bullet(df, x="部门", actual="完成额", target="目标额")
    """
    df = _frame.ensure_frame(data)
    if x is None:
        raise ValueError('bullet 需要 x（类目列），例如 bullet(df, x="部门", actual="完成额")。')
    _frame.require_column(df, x, "x（类目）")
    df = _coerce_numeric(df, [("actual（实际值）", actual)], agg=agg)
    tcol = None
    if isinstance(target, (int, float, np.integer, np.floating)) and not isinstance(target, bool):
        if target_value is None:
            target_value = float(target)
    else:
        tcol = target
    if tcol is not None:
        df = _coerce_numeric(df, [("target（目标值）", tcol)], agg=agg)
    spec, records, ref, info = _ext(
        "bullet",
        df,
        {"x": x, "y": actual, "target": tcol},
        title=title if title is not None else "%s 达成情况" % actual,
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=agg,
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=drill,
        link=link,
        max_rows=max_rows,
        targetValue=_num_param(target_value, "target_value"),
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.3 lollipop 棒棒糖图
# ==========================================================================
def lollipop(
    data: pd.DataFrame,
    x: str | None,
    y: str | None | Follow = None,
    *,
    agg: str | None = None,
    sort: str | None = None,
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    xlim: tuple | None = None,
    ylim: tuple | None = None,
    fmt: str = "compact",
    height: int = 380,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = False,
    labels: bool = False,
    zoom: bool | str = "auto",
    drill: list[str] | None = None,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """棒棒糖图：细柱 + 顶端圆点，比柱状图更清爽的排行榜。

    示例
    ----
    >>> eazy_data_viz.charts_extra.lollipop(df, x="门店", y="销售额")
    """
    df = _frame.ensure_frame(data)
    if x is None:
        raise ValueError('lollipop 需要 x（类目列），例如 lollipop(df, x="门店", y="销售额")。')
    _frame.require_column(df, x, "x（类目）")
    if y is not None:
        df = _coerce_numeric(df, [("y（数值）", y)], agg=agg)
    spec, records, ref, info = _ext(
        "lollipop",
        df,
        {"x": x, "y": y},
        title=title if title is not None else "%s 按 %s" % (y or "记录数", x),
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=("count" if (y is None and agg != "unique") else agg),
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=drill,
        link=link,
        max_rows=max_rows,
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.4 dumbbell 哑铃图
# ==========================================================================
def dumbbell(
    data: pd.DataFrame,
    x: str | None,
    y1: str | None,
    y2: str | None | Follow,
    *,
    labels: bool = None,
    series_names: list[str] | None = None,
    agg: str | None = None,
    sort: str | None = None,
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    xlim: tuple | None = None,
    ylim: tuple | None = None,
    fmt: str = "compact",
    height: int = 380,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = True,
    zoom: bool | str = "auto",
    drill: list[str] | None = None,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """哑铃图：同一类目两个数值（如两期、两组）之间的差距对比。

    ``labels`` 传 ``["期初", "期末"]`` 之类可覆盖两个系列名（传 bool 则控制数值标签）。

    示例
    ----
    >>> eazy_data_viz.charts_extra.dumbbell(df, x="门店", y1="去年", y2="今年",
    ...                            labels=["去年", "今年"])
    """
    df = _frame.ensure_frame(data)
    if x is None:
        raise ValueError('dumbbell 需要 x（类目列），例如 dumbbell(df, x="门店", y1="去年", y2="今年")。')
    df = _coerce_numeric(df, [("y1（第一个数值）", y1), ("y2（第二个数值）", y2)], agg=agg)
    show_labels = isinstance(labels, bool) and labels
    if series_names is None and labels is not None and not isinstance(labels, bool):
        series_names = [str(v) for v in _as_list(labels)]
    if series_names is None:
        series_names = [y1, y2]
    spec, records, ref, info = _ext(
        "dumbbell",
        df,
        {"x": x, "y": y1, "y2": y2},
        title=title if title is not None else "%s / %s 对比" % (y1, y2),
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=agg,
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=show_labels,
        zoom=zoom,
        drill=drill,
        link=link,
        max_rows=max_rows,
        seriesNames=list(series_names),
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.5 pareto 帕累托图
# ==========================================================================
def pareto(
    data: pd.DataFrame,
    x: str | None,
    y: str | None | Follow = None,
    *,
    agg: str | None = None,
    top_n: int | None = None,
    cum_fmt: str = "percent",
    sort: str | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    xlim: tuple | None = None,
    ylim: tuple | None = None,
    fmt: str = "compact",
    height: int = 400,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = False,
    labels: bool = False,
    zoom: bool | str = "auto",
    drill: list[str] | None = None,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """帕累托图：按数值降序的柱 + 累计占比折线（右轴 0~100%）。

    示例
    ----
    >>> eazy_data_viz.charts_extra.pareto(df, x="问题类型", y="数量", top_n=10)
    """
    df = _frame.ensure_frame(data)
    if x is None:
        raise ValueError('pareto 需要 x（类目列），例如 pareto(df, x="问题类型", y="数量")。')
    _frame.require_column(df, x, "x（类目）")
    if y is not None:
        df = _coerce_numeric(df, [("y（数值）", y)], agg=agg)
    try:
        _check_fmt(cum_fmt)
    except ValueError:
        raise ValueError("cum_fmt 只支持 \"percent\" / \"raw\" / \"compact\"，收到 %r。" % (cum_fmt,))
    spec, records, ref, info = _ext(
        "pareto",
        df,
        {"x": x, "y": y},
        title=title if title is not None else "%s 帕累托分析" % (y or "记录数"),
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=("count" if (y is None and agg != "unique") else agg),
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=drill,
        link=link,
        max_rows=max_rows,
        cumFmt=cum_fmt or "percent",
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.6 slope 斜率图
# ==========================================================================
def slope(
    data: pd.DataFrame,
    x: str | None,
    y: str | None | Follow,
    color: str | None = None,
    *,
    group: str | None = None,
    period: str | None = None,
    agg: str | None = None,
    sort: str | None = None,
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    xlim: tuple | None = None,
    ylim: tuple | None = None,
    fmt: str = "compact",
    height: int = 380,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = True,
    labels: bool = False,
    zoom: bool | str = False,
    drill: list[str] | None = None,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """斜率图：同一类目在两个「期」之间的变化（两点连线，斜率即变化）。

    ``color`` 是期别列，正常情况下应恰好 2 个取值（如 "去年" / "今年"）；
    取值多于 2 个时只取前两个并在 ``warnings`` 里提示。

    示例
    ----
    >>> eazy_data_viz.charts_extra.slope(df, x="门店", y="销售额", color="年份")
    """
    df = _frame.ensure_frame(data)
    if x is None:
        raise ValueError('slope 需要 x（类目列），例如 slope(df, x="门店", y="销售额", color="年份")。')
    if y is None:
        raise ValueError('slope 需要 y（数值列），例如 slope(df, x="门店", y="销售额", color="年份")。')
    if color is None:
        color = group
    if color is None:
        raise ValueError("slope 需要 color（两期对比列，如年份/期别），也可以用 group= 传入。")
    _require_cols(df, [("x（类目）", x), ("color（期别）", color)])
    df = _coerce_numeric(df, [("y（数值）", y)], agg=agg)
    if period is not None:
        arms = [str(p) for p in _as_list(period)]
    else:
        arms = []
        _ck_ind = _frame.column_kind(df[color])
        for v in _frame.column_values(df[color], _ck_ind):
            if v is None:
                continue
            s = str(v)
            if s not in arms:
                arms.append(s)
    warnings = []
    if len(arms) < 2:
        warnings.append(
            "slope 的 color 列 %r 只有 %d 个取值，斜率图至少需要两期才能展示变化。"
            % (color, len(arms))
        )
    elif len(arms) > 2:
        warnings.append(
            "slope 的 color 列 %r 有 %d 个取值，只取前两个：%s / %s。"
            "如需对比其它期别，请先过滤数据。" % (color, len(arms), arms[0], arms[1])
        )
    spec, records, ref, info = _ext(
        "slope",
        df,
        {"x": x, "y": y, "color": color},
        title=title if title is not None else "%s 变化" % y,
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=agg,
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=drill,
        link=link,
        max_rows=max_rows,
        arms=arms[:2],
    )
    info["warnings"].extend(warnings)
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.7 bump 排名变化图
# ==========================================================================
def bump(
    data: pd.DataFrame,
    x: str | None,
    y: str | None | Follow,
    *,
    group: str | None,
    agg: str | None = None,
    sort: str | None = None,
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    xlim: tuple | None = None,
    ylim: tuple | None = None,
    fmt: str = "compact",
    height: int = 420,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = True,
    labels: bool = False,
    zoom: bool | str = "auto",
    drill: list[str] | None = None,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """排名变化图（bump chart）：每个 group 一条折线，y 轴是排名。

    示例
    ----
    >>> eazy_data_viz.charts_extra.bump(df, x="月份", y="销售额", group="产品")
    """
    df = _frame.ensure_frame(data)
    if x is None or y is None:
        raise ValueError('bump 需要 x（时间/类目）和 y（数值），例如 bump(df, x="月份", y="销售额", group="产品")。')
    _require_cols(df, [("x（时间/类目）", x), ("group（分组）", group)])
    df = _coerce_numeric(df, [("y（数值）", y)], agg=agg)
    spec, records, ref, info = _ext(
        "bump",
        df,
        {"x": x, "y": y, "color": group},
        title=title if title is not None else "%s 排名变化" % y,
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=agg,
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=drill,
        link=link,
        max_rows=max_rows,
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.8 radar 雷达图
# ==========================================================================
def radar(
    data: pd.DataFrame,
    x: str | None,
    y: str | None | Follow = None,
    color: str | None = None,
    *,
    max: float | None = None,
    agg: str | None = None,
    sort: str | None = None,
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    xlim: tuple | None = None,
    ylim: tuple | None = None,
    fmt: str = "compact",
    height: int = 400,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = True,
    labels: bool = False,
    zoom: bool | str = False,
    drill: list[str] | None = None,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """雷达图：每个 color 组一条闭合折线，指标是 x 的各个类目。

    ``max`` 不传时由前端按各指标最大值上浮 10% 自动确定。

    示例
    ----
    >>> eazy_data_viz.charts_extra.radar(df, x="能力项", y="得分", color="对象")
    """
    df = _frame.ensure_frame(data)
    if x is None:
        raise ValueError('radar 需要 x（指标项），例如 radar(df, x="能力项", y="得分", color="对象")。')
    _require_cols(df, [("x（指标项）", x), ("color（分组）", color)])
    if y is not None:
        df = _coerce_numeric(df, [("y（数值）", y)], agg=agg)
    spec, records, ref, info = _ext(
        "radar",
        df,
        {"x": x, "y": y, "color": color},
        title=title if title is not None else "%s 雷达图" % (y or "记录数"),
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=("count" if (y is None and agg != "unique") else (agg or "mean")),
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=drill,
        link=link,
        max_rows=max_rows,
        maxValue=(_num_or_none(max) if max is not None else None),
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.9 rose 南丁格尔玫瑰图
# ==========================================================================
def rose(
    data: pd.DataFrame,
    names: str | None | Follow,
    values: str | None | Follow = None,
    *,
    donut: bool = False,
    agg: str | None = None,
    sort: str | None = "desc",
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    xlim: tuple | None = None,
    ylim: tuple | None = None,
    fmt: str = "compact",
    height: int = 380,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = True,
    labels: bool = True,
    zoom: bool | str = False,
    drill: list[str] | None = None,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """南丁格尔玫瑰图：用半径表达数值的饼图。

    示例
    ----
    >>> eazy_data_viz.charts_extra.rose(df, names="产品", values="销售额")
    """
    df = _frame.ensure_frame(data)
    if names is None:
        raise ValueError('rose 需要 names（类目列），例如 rose(df, names="产品", values="销售额")。')
    if drill:
        # 扇区类目就是 names 列：下钻第一层必须从 names 开始，否则点击后按实例列过滤会变空图。
        drill = [names] + [d for d in _as_list(drill) if d != names]
    _frame.require_column(df, names, "names（类目）")
    if values is not None:
        df = _coerce_numeric(df, [("values（数值）", values)], agg=agg)
    spec, records, ref, info = _ext(
        "rose",
        df,
        {"names": names, "value": values},
        title=title if title is not None else "%s 构成" % (values or names),
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=("count" if (values is None and agg != "unique") else agg),
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=drill,
        link=link,
        max_rows=max_rows,
        donut=bool(donut),
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.10 parallel 平行坐标
# ==========================================================================
def parallel(
    data: pd.DataFrame,
    dims: list[str] | None,
    *,
    color: str | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    xlim: tuple | None = None,
    ylim: tuple | None = None,
    fmt: str = "compact",
    height: int = 440,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = False,
    labels: bool = False,
    zoom: bool | str = False,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """平行坐标：每一行是一条折线，每个维度一根纵轴，用来看多维分布/聚类。

    ``dims`` 是数值列名列表（至少 1 个，通常 3~8 个）。

    示例
    ----
    >>> eazy_data_viz.charts_extra.parallel(df, ["价格", "销量", "利润"], color="品类")
    """
    df = _frame.ensure_frame(data)
    dims = [c for c in _as_list(dims) if c is not None]
    if not dims:
        raise ValueError('parallel 需要 dims（数值列名列表），例如 parallel(df, ["价格", "销量", "利润"])。')
    pairs = [("dims[%d]" % i, c) for i, c in enumerate(dims)]
    _require_cols(df, [("color（分组）", color)])
    df = _coerce_numeric(df, pairs)
    spec, records, ref, info = _ext(
        "parallel",
        df,
        {"dims": list(dims), "color": color},
        title=title if title is not None else "平行坐标",
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg="sum",
        sort=None,
        top_n=None,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=None,
        link=link,
        max_rows=max_rows,
        parallelDims=list(dims),
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.11 pictorial 象形柱图
# ==========================================================================
def pictorial(
    data: pd.DataFrame,
    x: str | None,
    y: str | None | Follow = None,
    *,
    symbol: str | None = "circle",
    agg: str | None = None,
    sort: str | None = None,
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    xlim: tuple | None = None,
    ylim: tuple | None = None,
    fmt: str = "compact",
    height: int = 380,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = False,
    labels: bool = True,
    zoom: bool | str = "auto",
    drill: list[str] | None = None,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """象形柱图：用重复的小图形（circle / rect / roundRect / diamond / triangle）堆出柱子。

    示例
    ----
    >>> eazy_data_viz.charts_extra.pictorial(df, x="产品", y="销量", symbol="roundRect")
    """
    allowed = ("circle", "rect", "roundRect", "diamond", "triangle")
    if symbol not in allowed:
        raise ValueError(
            "symbol=%r 不支持，可选：%s" % (symbol, " / ".join(allowed))
        )
    df = _frame.ensure_frame(data)
    if x is None:
        raise ValueError('pictorial 需要 x（类目列），例如 pictorial(df, x="产品", y="销量")。')
    _frame.require_column(df, x, "x（类目）")
    if y is not None:
        df = _coerce_numeric(df, [("y（数值）", y)], agg=agg)
    spec, records, ref, info = _ext(
        "pictorial",
        df,
        {"x": x, "y": y},
        title=title if title is not None else "%s 按 %s" % (y or "记录数", x),
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=("count" if (y is None and agg != "unique") else agg),
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=drill,
        link=link,
        max_rows=max_rows,
        symbol=symbol,
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.12 target 目标对比图
# ==========================================================================
def target(
    data: pd.DataFrame,
    x: str | None,
    actual: str | None,
    target: str | None = None,
    *,
    target_value: str | None = None,
    agg: str | None = None,
    sort: str | None = None,
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    xlim: tuple | None = None,
    ylim: tuple | None = None,
    fmt: str = "compact",
    height: int = 380,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = True,
    labels: bool = False,
    zoom: bool | str = "auto",
    drill: list[str] | None = None,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """目标对比图：实际值柱子 + 目标值折线（虚线）。

    ``target`` 传列名时逐项对齐目标；传常数或 ``target_value=`` 时全体共用一个目标。

    示例
    ----
    >>> eazy_data_viz.charts_extra.target(df, x="月份", actual="销售额", target="目标额")
    """
    df = _frame.ensure_frame(data)
    if x is None:
        raise ValueError('target 需要 x（类目列），例如 target(df, x="月份", actual="销售额")。')
    _frame.require_column(df, x, "x（类目）")
    df = _coerce_numeric(df, [("actual（实际值）", actual)], agg=agg)
    tcol = None
    if isinstance(target, (int, float, np.integer, np.floating)) and not isinstance(target, bool):
        if target_value is None:
            target_value = float(target)
    else:
        tcol = target
    if tcol is not None:
        df = _coerce_numeric(df, [("target（目标值）", tcol)], agg=agg)
    spec, records, ref, info = _ext(
        "target",
        df,
        {"x": x, "y": actual, "target": tcol},
        title=title if title is not None else "%s 目标对比" % actual,
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=agg,
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=drill,
        link=link,
        max_rows=max_rows,
        targetValue=_num_param(target_value, "target_value"),
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.13 trend 趋势散点
# ==========================================================================
def trend(
    data: pd.DataFrame,
    x: str | None,
    y: str | None | Follow,
    color: str | None = None,
    *,
    title: str | None = None,
    subtitle: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    xlim: tuple | None = None,
    ylim: tuple | None = None,
    fmt: str = "compact",
    height: int = 400,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = None,
    labels: bool = False,
    zoom: bool | str = False,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """趋势散点图：散点 + 最小二乘回归线，图例/副标题带 R²。

    x / y 必须是数值列；回归系数在 Python 侧用 numpy 算好写进 ``spec.fit``。

    示例
    ----
    >>> eazy_data_viz.charts_extra.trend(df, x="广告投入", y="销售额", color="地区")
    """
    df = _frame.ensure_frame(data)
    if x is None or y is None:
        raise ValueError('trend 需要 x / y 两个数值列，例如 trend(df, x="广告投入", y="销售额")。')
    _require_cols(df, [("color（分组）", color)])
    df = _coerce_numeric(df, [("x（数值）", x), ("y（数值）", y)])

    xv = pd.to_numeric(df[x], errors="coerce")
    yv = pd.to_numeric(df[y], errors="coerce")
    mask = xv.notna() & yv.notna()
    xa = xv[mask].to_numpy(dtype="float64")
    ya = yv[mask].to_numpy(dtype="float64")
    if xa.size < 2:
        raise ValueError("trend 需要至少 2 个有效的 (x, y) 数值点才能拟合回归线。")
    if float(np.ptp(xa)) == 0.0:
        slope = 0.0
        intercept = float(ya.mean())
        r2 = None
    else:
        slope, intercept = np.polyfit(xa, ya, 1)
        pred = slope * xa + intercept
        ss_res = float(np.sum((ya - pred) ** 2))
        ss_tot = float(np.sum((ya - ya.mean()) ** 2))
        r2 = None if ss_tot <= 0.0 else float(1.0 - ss_res / ss_tot)
    fit = {
        "slope": float(slope),
        "intercept": float(intercept),
        "r2": (None if r2 is None else float(r2)),
        "xmin": float(xa.min()),
        "xmax": float(xa.max()),
    }
    spec, records, ref, info = _ext(
        "trend",
        df,
        {"x": x, "y": y, "color": color},
        title=title if title is not None else "%s 与 %s 趋势" % (y, x),
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg="sum",
        sort="none",
        top_n=None,
        legend=(color is not None if legend is None else legend),
        labels=labels,
        zoom=zoom,
        drill=None,
        link=link,
        max_rows=max_rows,
        fit=fit,
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.14 quadrant 四象限散点
# ==========================================================================
def quadrant(
    data: pd.DataFrame,
    x: str | None,
    y: str | None | Follow,
    size: str | None | Follow = None,
    color: str | None = None,
    *,
    quad_labels: list[str] | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    xlim: tuple | None = None,
    ylim: tuple | None = None,
    fmt: str = "compact",
    height: int = 400,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = None,
    labels: bool = False,
    zoom: bool | str = False,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """四象限散点图：用 x / y 的中位数把平面切成四块，看对象落在哪个象限。

    示例
    ----
    >>> eazy_data_viz.charts_extra.quadrant(df, x="增长率", y="利润率", size="营收", color="品类")
    """
    df = _frame.ensure_frame(data)
    if x is None or y is None:
        raise ValueError('quadrant 需要 x / y 两个数值列，例如 quadrant(df, x="增长率", y="利润率")。')
    _require_cols(df, [("color（分组）", color)])
    df = _coerce_numeric(df, [("x（数值）", x), ("y（数值）", y)])
    if size is not None:
        df = _coerce_numeric(df, [("size（气泡大小）", size)])

    xv = pd.to_numeric(df[x], errors="coerce")
    yv = pd.to_numeric(df[y], errors="coerce")
    xmid = _num_or_none(xv.median())
    ymid = _num_or_none(yv.median())
    warnings = []
    if xmid is None:
        warnings.append("quadrant 的 x 列全部为空，无法计算中位数，x 中线按 0 处理。")
        xmid = 0.0
    if ymid is None:
        warnings.append("quadrant 的 y 列全部为空，无法计算中位数，y 中线按 0 处理。")
        ymid = 0.0

    if quad_labels is None:
        # 顺序与前端一致：[左上, 右上, 左下, 右下]
        quad_labels = ["低值·高值", "高值·高值", "低值·低值", "高值·低值"]
    else:
        quad_labels = [str(v) for v in _as_list(quad_labels)]
        if len(quad_labels) != 4:
            raise ValueError(
                'quad_labels 需要 4 个文本（四角说明），例如 '
                'quad_labels=["高增长高利润", "低增长高利润", "低增长低利润", "高增长低利润"]，'
                "收到 %r" % (quad_labels,)
            )

    spec, records, ref, info = _ext(
        "quadrant",
        df,
        {"x": x, "y": y, "size": size, "color": color},
        title=title if title is not None else "%s 与 %s 四象限" % (y, x),
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg="sum",
        sort="none",
        top_n=None,
        legend=(color is not None if legend is None else legend),
        labels=labels,
        zoom=zoom,
        drill=None,
        link=link,
        max_rows=max_rows,
        xmid=xmid,
        ymid=ymid,
        quadrantLabels=quad_labels,
    )
    info["warnings"].extend(warnings)
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.15 matrix 相关系数矩阵
# ==========================================================================
def matrix(
    data: pd.DataFrame,
    columns: str | list[str] | None = None,
    *,
    max_cols: int = 12,
    title: str | None = None,
    subtitle: str | None = None,
    fmt: str = "compact",
    height: int = 460,
    abs_height: bool = False,
    theme: str = "light",
) -> Chart:
    """相关系数矩阵（Pearson）：热力图 + 格子里两位小数的 r 值。

    不接联动 / 过滤——相关系数已在 Python 侧算好放进 ``spec.values``。

    ``columns`` 不传时自动取全部数值列（最多 ``max_cols`` 列）。

    示例
    ----
    >>> eazy_data_viz.charts_extra.matrix(df)
    >>> eazy_data_viz.charts_extra.matrix(df, columns=["销售额", "利润", "订单数"])
    """
    df = _frame.ensure_frame(data)
    if len(df) == 0:
        raise ValueError("数据为空（0 行），无法绘图。")
    if columns is None:
        nums = [
            c for c in df.columns if _frame.column_kind(df[c]) == _frame.KIND_NUM
        ][: int(max_cols)]
    else:
        nums = [c for c in _as_list(columns) if c is not None]
        for i, c in enumerate(nums):
            _frame.require_column(df, c, "columns[%d]" % i)
            if _frame.column_kind(df[c]) != _frame.KIND_NUM:
                raise TypeError(
                    "columns[%d] 列 %r 需要是数值类型（相关系数矩阵只能用数值列）。" % (i, c)
                )
    if len(nums) < 2:
        raise ValueError(
            "matrix 至少需要 2 个数值列才能计算相关系数（当前 %d 个）。"
            "请先检查 DataFrame 的数值列，或用 columns= 指定。" % len(nums)
        )
    corr = df[nums].corr(method="pearson")
    values = []
    for row in corr.to_numpy():
        line = []
        for v in row:
            f = _num_or_none(v)
            line.append(None if f is None else round(f, 4))
        values.append(line)

    spec = _manual_spec(
        "matrix",
        title=title if title is not None else "相关系数矩阵",
        subtitle=subtitle,
        theme=theme,
        height=height,
        abs_height=abs_height,
        fmt=fmt,
    )
    # 契约：labels 是列名数组、values 是二维相关系数（覆盖通用 bool 字段）
    spec["labels"] = [str(c) for c in nums]
    spec["values"] = values
    return _empty_chart(spec)


# ==========================================================================
# 3.16 sparkline 迷你走势
# ==========================================================================
def sparkline(
    data: pd.DataFrame,
    x: str | None,
    y: str | None | Follow,
    *,
    group: str | None,
    agg: str | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    fmt: str = "compact",
    height: int = 260,
    abs_height: bool = False,
    theme: str = "light",
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """迷你走势（sparkline）：每个 group 一张无坐标轴小折线，最多 12 个。

    示例
    ----
    >>> eazy_data_viz.charts_extra.sparkline(df, x="日期", y="销售额", group="产品")
    """
    df = _frame.ensure_frame(data)
    if x is None or y is None:
        raise ValueError('sparkline 需要 x / y，例如 sparkline(df, x="日期", y="销售额", group="产品")。')
    _require_cols(df, [("x", x), ("group（分组）", group)])
    df = _coerce_numeric(df, [("y（数值）", y)], agg=agg)
    spec, records, ref, info = _ext(
        "sparkline",
        df,
        {"x": x, "y": y, "color": group},
        title=title if title is not None else "%s 走势" % y,
        subtitle=subtitle,
        xtitle=None,
        ytitle=None,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=agg,
        sort=None,
        top_n=None,
        legend=False,
        labels=False,
        zoom=False,
        drill=None,
        link=None,
        max_rows=max_rows,
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.17 ring_progress 环形进度
# ==========================================================================
def ring_progress(
    percent: float,
    *,
    label: str | None = None,
    max: float | None = 100,
    fmt: str = None,
    height: int = None,
    abs_height: bool = False,
    theme: str = "light",
    title: str | None = None,
) -> Chart:
    """环形进度：一个百分比/完成值画成圆环，中心显示数值（不接 DataFrame）。

    示例
    ----
    >>> eazy_data_viz.charts_extra.ring_progress(72.5, label="完成率")
    >>> eazy_data_viz.charts_extra.ring_progress(1280, max=2000, label="销售额", fmt="thousands")
    """
    try:
        p = float(percent)
    except (TypeError, ValueError):
        raise TypeError(
            "ring_progress 接受单个数值，例如 ring_progress(72.5, label=\"完成率\")。"
            "如果要画 DataFrame，请用 eazy_data_viz.charts_extra.progress(df, x=..., y=...)。"
        )
    try:
        mx = float(max)
    except (TypeError, ValueError):
        raise TypeError("ring_progress 的 max 需要是数值，例如 max=100，收到 %r" % (max,))
    if math.isnan(p) or math.isinf(p):
        raise ValueError("ring_progress 的 percent 必须是有限数值，收到 %r" % (percent,))
    if math.isnan(mx) or math.isinf(mx) or mx <= 0:
        raise ValueError("ring_progress 的 max 必须大于 0，收到 %r" % (max,))
    _check_fmt(fmt)
    spec = _manual_spec(
        "ring_progress",
        title=title if title is not None else (label or "进度"),
        theme=theme,
        height=(260 if height is None else height),
        abs_height=abs_height,
        fmt=(fmt or "raw"),
        labels=True,
    )
    spec["percentValue"] = p
    spec["max"] = mx
    spec["maxValue"] = mx
    spec["label"] = label
    return _empty_chart(spec)


# ==========================================================================
# 3.18 sunburst 旭日图
# ==========================================================================
def sunburst(
    data: pd.DataFrame,
    path: str | list[str] | None,
    value: str | None | Follow = None,
    *,
    agg: str | None = None,
    sort: str | None = "desc",
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    fmt: str = "compact",
    height: int = 460,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = False,
    labels: bool = True,
    zoom: bool | str = False,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """旭日图：多层级构成的同心圆环。

    ``path`` 是层级列名列表，例如 ``["大区", "省份", "城市"]``。

    示例
    ----
    >>> eazy_data_viz.charts_extra.sunburst(df, ["大区", "品类"], value="销售额")
    """
    df = _frame.ensure_frame(data)
    path = [c for c in _as_list(path) if c is not None]
    if not path:
        raise ValueError('sunburst 需要 path（层级列名列表），例如 sunburst(df, ["大区", "品类"], value="销售额")。')
    _require_cols(df, [("path[%d]" % i, c) for i, c in enumerate(path)])
    if value is not None:
        df = _coerce_numeric(df, [("value（数值）", value)], agg=agg)
    spec, records, ref, info = _ext(
        "sunburst",
        df,
        {"path": list(path), "value": value},
        title=title if title is not None else "%s 层级构成" % (value or path[0]),
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=("count" if (value is None and agg != "unique") else agg),
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=None,
        link=link,
        max_rows=max_rows,
    )
    _is_sun = spec.get("type") == "sunburst"
    chart = Chart(spec, records, ref, info)
    if sort not in (None, "desc") or top_n is not None:
        info.setdefault("warnings", []).append(
            "%s 的层级排序固定为「子节点按值从大到小」，sort=%r / top_n=%r 不生效；"
            "要控制顺序请先对数据聚合排序后再画。" % ("sunburst" if _is_sun else "tree", sort, top_n)
        )
    return chart


# ==========================================================================
# 3.19 tree 树图
# ==========================================================================
def tree(
    data: pd.DataFrame,
    path: str | list[str] | None,
    value: str | None | Follow = None,
    *,
    agg: str | None = None,
    sort: str | None = "desc",
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    fmt: str = "compact",
    height: int = 460,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = False,
    labels: bool = True,
    zoom: bool | str = False,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """树图：从左到右的层级结构（树状），节点大小可反映数值。

    示例
    ----
    >>> eazy_data_viz.charts_extra.tree(df, ["大区", "省份"], value="销售额")
    """
    df = _frame.ensure_frame(data)
    path = [c for c in _as_list(path) if c is not None]
    if not path:
        raise ValueError('tree 需要 path（层级列名列表），例如 tree(df, ["大区", "省份"], value="销售额")。')
    _require_cols(df, [("path[%d]" % i, c) for i, c in enumerate(path)])
    if value is not None:
        df = _coerce_numeric(df, [("value（数值）", value)], agg=agg)
    spec, records, ref, info = _ext(
        "tree",
        df,
        {"path": list(path), "value": value},
        title=title if title is not None else "%s 层级构成" % (value or path[0]),
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=("count" if (value is None and agg != "unique") else agg),
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=None,
        link=link,
        max_rows=max_rows,
    )
    _is_sun = spec.get("type") == "sunburst"
    chart = Chart(spec, records, ref, info)
    if sort not in (None, "desc") or top_n is not None:
        info.setdefault("warnings", []).append(
            "%s 的层级排序固定为「子节点按值从大到小」，sort=%r / top_n=%r 不生效；"
            "要控制顺序请先对数据聚合排序后再画。" % ("sunburst" if _is_sun else "tree", sort, top_n)
        )
    return chart


# ==========================================================================
# 3.20 sankey 桑基图
# ==========================================================================
def sankey(
    data: pd.DataFrame,
    source: str | None = None,
    target: str | None = None,
    value: str | None | Follow = None,
    *,
    path: str | list[str] | None = None,
    agg: str | None = None,
    sort: str | None = None,
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    fmt: str = "compact",
    height: int = 420,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = False,
    labels: bool = True,
    zoom: bool | str = False,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """桑基图：展示流量在多层「来源 → 去向」之间的流转及大小。

    两种写法（二选一）：

    - 两级：``sankey(df, source="渠道", target="产品", value="销售额")``
    - 多级：``sankey(df, path=["大区", "渠道", "产品"], value="销售额")``
      每一级与下一级各画一层流量（大区→渠道、渠道→产品），
      跨层同名值（例如「华东」既是 大区也是渠道）不会被合并。

    示例
    ----
    >>> eazy_data_viz.charts_extra.sankey(df, source="渠道", target="产品", value="销售额")
    >>> eazy_data_viz.charts_extra.sankey(df, path=["大区", "渠道", "产品"], value="销售额")
    """
    df = _frame.ensure_frame(data)
    if path is not None:
        if source is not None or target is not None:
            raise ValueError(
                "sankey 的 path 与 source/target 不能同时使用：多级流量用 "
                'path=["一级", "二级", "三级"]，两级流量用 source= / target=。'
            )
        dims = [c for c in _as_list(path) if c is not None]
    else:
        if source is None or target is None:
            raise ValueError(
                'sankey 需要 path（多级）或 source / target（两级），例如 '
                'sankey(df, path=["大区", "渠道", "产品"], value="销售额")。'
            )
        dims = [source, target]
    if len(dims) < 2:
        raise ValueError(
            "sankey 至少需要 2 级：path=[一级, 二级]，收到 %d 级。" % len(dims)
        )
    if len(set(dims)) != len(dims):
        raise ValueError(
            "sankey 的 path 里不能有重复列：%r。同一列不能同时当两级。"
            % (list(dims),)
        )
    _require_cols(
        df,
        [("path[%d]（第 %d 级）" % (i, i + 1), d) for i, d in enumerate(dims)],
    )
    if value is not None:
        df = _coerce_numeric(df, [("value（数值）", value)], agg=agg)
    spec, records, ref, info = _ext(
        "sankey",
        df,
        {"path": list(dims), "value": value},
        title=title if title is not None else "%s 流向" % " → ".join(str(d) for d in dims),
        subtitle=subtitle,
        xtitle=None,
        ytitle=None,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=("count" if (value is None and agg != "unique") else agg),
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=None,
        link=link,
        max_rows=max_rows,
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.21 graph 关系图
# ==========================================================================
def graph(
    data: pd.DataFrame,
    source: str | None,
    target: str | None,
    value: str | None | Follow = None,
    *,
    agg: str | None = None,
    sort: str | None = None,
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    fmt: str = "compact",
    height: int = 420,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = False,
    labels: bool = True,
    zoom: bool | str = False,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """关系图：力导向网络图，节点大小/边宽反映数值。

    示例
    ----
    >>> eazy_data_viz.charts_extra.graph(df, source="客户", target="产品", value="订单数")
    """
    df = _frame.ensure_frame(data)
    if source is None or target is None:
        raise ValueError(
            'graph 需要 source / target 两列，例如 graph(df, source="客户", target="产品", value="订单数")。'
        )
    _require_cols(df, [("source（来源）", source), ("target（去向）", target)])
    if value is not None:
        df = _coerce_numeric(df, [("value（数值）", value)], agg=agg)
    spec, records, ref, info = _ext(
        "graph",
        df,
        {"source": source, "target": target, "value": value},
        title=title if title is not None else "%s 关系图" % source,
        subtitle=subtitle,
        xtitle=None,
        ytitle=None,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=("count" if (value is None and agg != "unique") else agg),
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=None,
        link=link,
        max_rows=max_rows,
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.22 theme_river 主题河流图
# ==========================================================================
def theme_river(
    data: pd.DataFrame,
    x: str | None,
    color: str | None,
    value: str | None | Follow = None,
    *,
    agg: str | None = None,
    sort: str | None = None,
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    fmt: str = "compact",
    height: int = 380,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = True,
    labels: bool = False,
    zoom: bool | str = "auto",
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """主题河流图：各类目随时间的体量变化，像河流一样堆叠流动。

    示例
    ----
    >>> eazy_data_viz.charts_extra.theme_river(df, x="日期", color="产品", value="销售额")
    """
    df = _frame.ensure_frame(data)
    if x is None or color is None:
        raise ValueError(
            'theme_river 需要 x（时间/类目）和 color（分组），例如 '
            'theme_river(df, x="日期", color="产品", value="销售额")。'
        )
    _require_cols(df, [("x（时间/类目）", x), ("color（分组）", color)])
    if value is not None:
        df = _coerce_numeric(df, [("value（数值）", value)], agg=agg)
    spec, records, ref, info = _ext(
        "theme_river",
        df,
        {"x": x, "color": color, "value": value},
        title=title if title is not None else "%s 主题河流" % (value or color),
        subtitle=subtitle,
        xtitle=None,
        ytitle=None,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=("count" if (value is None and agg != "unique") else agg),
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=None,
        link=link,
        max_rows=max_rows,
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.23 calendar 日历热力图
# ==========================================================================
def calendar(
    data: pd.DataFrame,
    date: str | None,
    value: str | None | Follow = None,
    *,
    agg: str | None = None,
    sort: str | None = "x",
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    fmt: str = "compact",
    height: int = 300,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = False,
    labels: bool = False,
    zoom: bool | str = False,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """日历热力图：按天显示数值深浅（日期列会在 Python 侧转成 YYYY-MM-DD）。

    示例
    ----
    >>> eazy_data_viz.charts_extra.calendar(df, date="日期", value="订单数")
    """
    df = _frame.ensure_frame(data)
    if date is None:
        raise ValueError('calendar 需要 date（日期列），例如 calendar(df, date="日期", value="订单数")。')
    df = _coerce_time(df, [("date（日期）", date)])
    if value is not None:
        df = _coerce_numeric(df, [("value（数值）", value)], agg=agg)
    spec, records, ref, info = _ext(
        "calendar",
        df,
        {"x": date, "value": value},
        title=title if title is not None else "%s 日历热力" % (value or "记录数"),
        subtitle=subtitle,
        xtitle=None,
        ytitle=None,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=("count" if (value is None and agg != "unique") else agg),
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=None,
        link=link,
        max_rows=max_rows,
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.24 gantt 甘特图
# ==========================================================================
def gantt(
    data: pd.DataFrame,
    task: str | None,
    start: str | None,
    end: str | None,
    *,
    color: str | None = None,
    agg: str | None = None,
    sort: str | None = None,
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    fmt: str = "compact",
    height: int = 420,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = None,
    labels: bool = True,
    zoom: bool | str = False,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """甘特图：横向时间条，展示每个任务的起止时间。

    示例
    ----
    >>> eazy_data_viz.charts_extra.gantt(df, task="任务", start="开始日期", end="结束日期", color="负责人")
    """
    df = _frame.ensure_frame(data)
    if task is None or start is None or end is None:
        raise ValueError(
            'gantt 需要 task / start / end 三列，例如 '
            'gantt(df, task="任务", start="开始日期", end="结束日期")。'
        )
    _require_cols(df, [("task（任务）", task), ("color（分组）", color)])
    df = _coerce_time(df, [("start（开始日期）", start), ("end（结束日期）", end)])
    warnings = []
    try:
        sd = pd.to_datetime(df[start], errors="coerce")
        ed = pd.to_datetime(df[end], errors="coerce")
        bad = int((ed < sd).sum())
        if bad:
            warnings.append(
                "gantt 有 %d 行结束日期早于开始日期，已按「开始在前」自动交换这两列的值。" % bad
            )
    except (TypeError, ValueError):  # pragma: no cover - 防御式
        pass
    spec, records, ref, info = _ext(
        "gantt",
        df,
        {"x": task, "start": start, "end": end, "color": color},
        title=title if title is not None else "任务甘特图",
        subtitle=subtitle,
        xtitle=None,
        ytitle=None,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=agg,
        sort=sort,
        top_n=top_n,
        legend=(color is not None if legend is None else legend),
        labels=labels,
        zoom=zoom,
        drill=None,
        link=link,
        max_rows=max_rows,
    )
    info["warnings"].extend(warnings)
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.25 candlestick K 线图
# ==========================================================================
def candlestick(
    data: pd.DataFrame,
    date: str | None,
    open: str | None,
    high: str | None,
    low: str | None,
    close: str | None,
    *,
    title: str | None = None,
    subtitle: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    xlim: tuple | None = None,
    ylim: tuple | None = None,
    fmt: str = "compact",
    height: int = 420,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = False,
    labels: bool = False,
    zoom: bool | str = "auto",
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """K 线图（红涨绿跌）：需要日期 + 开 / 高 / 低 / 收 四列。

    Python 侧按日期升序整理记录（``records 已按日期升序``），其余交给前端。

    示例
    ----
    >>> eazy_data_viz.charts_extra.candlestick(df, date="日期", open="开盘", high="最高",
    ...                               low="最低", close="收盘")
    """
    df = _frame.ensure_frame(data)
    if date is None:
        raise ValueError('candlestick 需要 date（日期列），例如 candlestick(df, date="日期", open="开盘", ...)。')
    df = _coerce_time(df, [("date（日期）", date)])
    df = _coerce_numeric(
        df,
        [
            ("open（开盘价）", open),
            ("high（最高价）", high),
            ("low（最低价）", low),
            ("close（收盘价）", close),
        ],
    )
    try:
        df = df.sort_values(by=date, kind="mergesort")
    except (KeyError, TypeError):  # pragma: no cover - 防御式
        pass
    spec, records, ref, info = _ext(
        "candlestick",
        df,
        {"x": date, "open": open, "high": high, "low": low, "close": close},
        title=title if title is not None else "%s K线图" % date,
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg="sum",
        sort="x",
        top_n=None,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=None,
        link=link,
        max_rows=max_rows,
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.26 pyramid 金字塔图
# ==========================================================================
def pyramid(
    data: pd.DataFrame,
    names: str | None | Follow,
    values: str | None | Follow = None,
    *,
    agg: str | None = None,
    sort: str | None = "asc",
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    fmt: str = "compact",
    height: int = 380,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = False,
    labels: bool = True,
    zoom: bool | str = False,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """金字塔图：漏斗图上下翻转（下宽上窄），常用于层级/转化结构。

    示例
    ----
    >>> eazy_data_viz.charts_extra.pyramid(df, names="层级", values="人数")
    """
    df = _frame.ensure_frame(data)
    if names is None:
        raise ValueError('pyramid 需要 names（类目列），例如 pyramid(df, names="层级", values="人数")。')
    _frame.require_column(df, names, "names（类目）")
    if values is not None:
        df = _coerce_numeric(df, [("values（数值）", values)], agg=agg)
    spec, records, ref, info = _ext(
        "pyramid",
        df,
        {"names": names, "value": values},
        title=title if title is not None else "%s 金字塔" % names,
        subtitle=subtitle,
        xtitle=None,
        ytitle=None,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=("count" if (values is None and agg != "unique") else agg),
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=None,
        link=link,
        max_rows=max_rows,
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 3.27 area_pct / bar_pct 百分比堆叠
# ==========================================================================
def area_pct(
    data: pd.DataFrame,
    x: str | None,
    y: str | None | Follow,
    color: str | None = None,
    *,
    agg: str | None = None,
    sort: str | None = None,
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    xlim: tuple | None = None,
    ylim: tuple | None = None,
    fmt: str = "compact",
    height: int = 380,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = True,
    labels: bool = False,
    zoom: bool | str = "auto",
    drill: list[str] | None = None,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """百分比堆叠面积图：每个 x 归一化到 100%，看各 color 的占比变化。

    示例
    ----
    >>> eazy_data_viz.charts_extra.area_pct(df, x="日期", y="销售额", color="产品")
    """
    df = _frame.ensure_frame(data)
    if x is None or y is None:
        raise ValueError('area_pct 需要 x / y，例如 area_pct(df, x="日期", y="销售额", color="产品")。')
    if color is None:
        raise ValueError(
            'area_pct 需要 color（百分比的分组列），例如 area_pct(df, x="日期", y="销售额", color="产品")。'
        )
    _require_cols(df, [("x", x), ("color（分组）", color)])
    df = _coerce_numeric(df, [("y（数值）", y)], agg=agg)
    spec, records, ref, info = _ext(
        "area_pct",
        df,
        {"x": x, "y": y, "color": color},
        title=title if title is not None else "%s 百分比构成" % y,
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=agg,
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=drill,
        link=link,
        max_rows=max_rows,
        percent=True,
    )
    return Chart(spec, records, ref, info)


def bar_pct(
    data: pd.DataFrame,
    x: str | None,
    y: str | None | Follow,
    color: str | None = None,
    *,
    agg: str | None = None,
    sort: str | None = None,
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    xlim: tuple | None = None,
    ylim: tuple | None = None,
    fmt: str = "compact",
    height: int = 380,
    abs_height: bool = False,
    theme: str = "light",
    legend: bool = True,
    labels: bool = False,
    zoom: bool | str = "auto",
    drill: list[str] | None = None,
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """百分比堆叠柱图：每个 x 归一化到 100%，看各 color 的占比。

    示例
    ----
    >>> eazy_data_viz.charts_extra.bar_pct(df, x="月份", y="销售额", color="产品")
    """
    df = _frame.ensure_frame(data)
    if x is None or y is None:
        raise ValueError('bar_pct 需要 x / y，例如 bar_pct(df, x="月份", y="销售额", color="产品")。')
    if color is None:
        raise ValueError(
            'bar_pct 需要 color（百分比的分组列），例如 bar_pct(df, x="月份", y="销售额", color="产品")。'
        )
    _require_cols(df, [("x", x), ("color（分组）", color)])
    df = _coerce_numeric(df, [("y（数值）", y)], agg=agg)
    spec, records, ref, info = _ext(
        "bar_pct",
        df,
        {"x": x, "y": y, "color": color},
        title=title if title is not None else "%s 百分比构成" % y,
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=agg,
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=drill,
        link=link,
        max_rows=max_rows,
        percent=True,
    )
    return Chart(spec, records, ref, info)


# ==========================================================================
# 驾驶舱补充：progress / tile / table / wordcloud / group_kpi
# ==========================================================================
def progress(
    data: pd.DataFrame,
    x: str | None = None,
    y: str | None | Follow = None,
    *,
    max: float | None = None,
    agg: str | None = None,
    sort: str | None = "desc",
    top_n: int | None = 10,
    title: str | None = None,
    subtitle: str | None = None,
    fmt: str = "compact",
    height: int = 340,
    abs_height: bool = False,
    theme: str = "light",
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """进度条列表（HTML 渲染）：每类一条「名称 + 数值 + 进度条」。

    ``max`` 是进度条的满量程；不传时由前端取最大值。

    示例
    ----
    >>> eazy_data_viz.charts_extra.progress(df, x="渠道", y="完成量", max=1000)
    """
    df = _frame.ensure_frame(data)
    if x is None:
        x = _pick_dim(df)
    if x is None:
        raise ValueError(
            'progress 需要 x（类目列），例如 progress(df, x="渠道", y="完成量")；'
            "当前 DataFrame 里没有分类/时间列。"
        )
    _frame.require_column(df, x, "x（类目）")
    if y is not None:
        df = _coerce_numeric(df, [("y（数值）", y)], agg=agg)
    spec, records, ref, info = _ext(
        "progress",
        df,
        {"x": x, "y": y},
        title=title if title is not None else "%s 进度" % (y or "记录数"),
        subtitle=subtitle,
        xtitle=None,
        ytitle=None,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=("count" if (y is None and agg != "unique") else agg),
        sort=sort,
        top_n=top_n,
        legend=False,
        labels=False,
        zoom=False,
        drill=None,
        link=link,
        max_rows=max_rows,
        maxValue=(_num_or_none(max) if max is not None else None),
    )
    return Chart(spec, records, ref, info)


def tile(
    data: pd.DataFrame,
    names: str | None | Follow = None,
    values: str | None | Follow = None,
    *,
    agg: str | None = None,
    sort: str | None = None,
    top_n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    fmt: str = "compact",
    height: int = 360,
    abs_height: bool = False,
    theme: str = "light",
    link: str | tuple | dict | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """瓦片图（HTML 渲染）：每个类目一个方块，颜色深浅表示数值大小。

    示例
    ----
    >>> eazy_data_viz.charts_extra.tile(df, names="门店", values="销售额")
    """
    df = _frame.ensure_frame(data)
    if names is None:
        names = _pick_dim(df)
    if names is None:
        raise ValueError(
            'tile 需要 names（类目列），例如 tile(df, names="门店", values="销售额")；'
            "当前 DataFrame 里没有分类/时间列。"
        )
    _frame.require_column(df, names, "names（类目）")
    if values is not None:
        df = _coerce_numeric(df, [("values（数值）", values)], agg=agg)
    spec, records, ref, info = _ext(
        "tile",
        df,
        {"names": names, "value": values},
        title=title if title is not None else "%s 瓦片图" % (values or "记录数"),
        subtitle=subtitle,
        xtitle=None,
        ytitle=None,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=("count" if (values is None and agg != "unique") else agg),
        sort=sort,
        top_n=top_n,
        legend=False,
        labels=False,
        zoom=False,
        drill=None,
        link=link,
        max_rows=max_rows,
    )
    return Chart(spec, records, ref, info)


_TABLE_GROUPBY_KEYS = ("columns", "value", "agg")


def _parse_table_groupby(df, groupby):
    """校验 table 的 groupby 参数，返回规范化的 dict。"""
    if not isinstance(groupby, dict):
        raise ValueError(
            'groupby 需要是字典，例如 groupby={"columns": ["大区"], "value": "销售额", "agg": "sum"}。'
        )
    unknown = [str(k) for k in groupby if k not in _TABLE_GROUPBY_KEYS]
    if unknown:
        raise ValueError(
            'groupby 只支持 columns / value / agg 三个键，收到未知键：%s。'
            % "、".join(sorted(unknown))
        )
    dims = groupby.get("columns")
    if dims is None:
        raise ValueError(
            'groupby 需要 columns（按哪些列分组），例如 groupby={"columns": ["大区"], "value": "销售额"}。'
        )
    dims = [c for c in _as_list(dims) if c is not None]
    if not dims:
        raise ValueError("groupby 的 columns 不能为空：至少指定 1 个分组列。")
    _require_cols(df, [("groupby.columns[%d]" % i, c) for i, c in enumerate(dims)])

    value = groupby.get("value")
    if isinstance(value, (list, tuple)):
        if len(value) != 1:
            raise ValueError(
                "groupby 的 value 只能是一列（汇总 / 去重计数的列），收到 %d 列。" % len(value)
            )
        value = value[0]
    if value is not None and not _metric.is_follow(value):
        _require_cols(df, [("groupby.value", value)])
        if value in dims:
            raise ValueError(
                "groupby 的 value（%r）不能同时出现在 columns 里：同一列不能既分组又求和。"
                % (value,)
            )

    agg = groupby.get("agg")
    if agg is None:
        agg = _metric.agg_for(value if isinstance(value, str) else None)
        if agg is None and _metric.is_follow(value):
            agg = _metric.agg_for(value.default)
        if agg is None:
            agg = "sum" if value is not None else "count"
    if not isinstance(agg, str):
        raise ValueError("groupby 的 agg 需要是字符串，可选：%s。" % "、".join(AGGS))
    agg = agg.lower()
    if agg not in AGGS:
        raise ValueError(
            "groupby 的 agg=%r 不支持，可选：%s。" % (agg, "、".join(AGGS))
        )
    if value is None and agg != "count":
        raise ValueError(
            'groupby 没给 value 时 agg 只能是 "count"（按组计数）；'
            'unique（去重计数）需要指定 value 列。收到 agg=%r。' % (agg,)
        )
    return {
        "columns": [str(c) for c in dims],
        # follow() 要原样往上传，交给 _base_spec 解析成 spec["follow"]
        "value": value if _metric.is_follow(value) else (str(value) if value is not None else None),
        "agg": agg,
    }


def _json_groupby(group):
    """groupby 的 spec 版本：follow() 换成 None（浏览器端随选中指标填回）。"""
    if not group:
        return group
    out = dict(group)
    if _metric.is_follow(out.get("value")):
        out["value"] = None
        out["follow"] = True
    return out


def table(
    data: pd.DataFrame,
    columns: str | list[str] | None = None,
    *,
    groupby: dict | None = None,
    limit: int = 100,
    title: str | None = None,
    subtitle: str | None = None,
    fmt: str = "compact",
    height: int = 400,
    abs_height: bool = False,
    theme: str = "light",
    link: str | tuple | dict | None = None,
    max_rows: int | None = None,
    total: bool = False,
    index: bool = False,
    bar: str | list[str] | None = None,
    stripe: bool = True,
) -> Chart:
    """表格（HTML 渲染）：明细表，或按 groupby 汇总后的汇总表。

    两种用法：

    - 明细：``table(df, columns=["月份", "大区", "销售额"])`` 逐行展示原始数据。
    - 汇总：``table(df, groupby={"columns": ["大区"], "value": "销售额", "agg": "sum"})``
      按 ``columns`` 分组，对 ``value`` 做 ``agg`` 聚合后每行显示一个分组。

    ``groupby`` 是字典，只有三个键：

    - ``columns``：分组维度列（1 列或多列）。
    - ``value``：汇总的数值列；不给则按组计数（此时 ``agg`` 只能是 ``count``）。
    - ``agg``：聚合方式，可选 sum / mean / count / unique / max / min / median，默认 ``sum``。

    汇总只发生在**显示层**：联动筛选后表格里显示的是「筛选后数据的汇总」，
    后台数据与其它图表的联动值不受影响。

    ``total=True`` 的合计行只累加**当前显示的那些行**（受 ``limit`` 限制），不是
    整份数据的合计；要全量合计请用 ``groupby`` 汇总表，或先自己 ``df.sum()``。

    展示 ``limit`` 行（上限 200）；嵌入多少行由 ``max_rows`` 决定——默认明细表嵌 200 行，
    汇总表（``groupby``）嵌入全部行，因为汇总必须基于完整数据，否则数字会和 pandas 对不上。

    中国式报表参数（参考 FineReport 明细表 / 观远 BI 表格）
    ------------------------------------------------------
    total : bool
        底部「合计」行：数值列按单元格同样的格式求和，文本 / 时间列留空；
        合计行加粗、顶部双线、浅底色。空表（0 行）不显示合计；
        没有 index 时「合计」两个字占用第一列（通常是维度列）；
        第一列本身是数值列时，「合计」与该列合计同格显示。默认 False。
    index : bool
        最左侧「序号」列（1..N），该列同样固定在左侧。默认 False。
    bar : bool | str | list[str] | None
        单元格数据条（条件格式）：True 自动取第一个数值列；"列名" 指定一列；
        ["列1", "列2"] 指定多列。条按该列最大值等比绘制，颜色取主题配色。
        None 表示不画数据条（默认）。
    stripe : bool
        斑马纹（tbody 偶数行浅底色），默认 True。

    联动（1.4.0 起双向）
    --------------------
    ``link`` 同时支持两个方向：点其它图会筛这张表（只留命中的行）；反过来，
    这张表里的**维度列**（文本 / 日期列，不含数值列）会变成可点单元格，
    点一下即按「列 = 该格的值」筛选同组图表，表格自身不筛行、只把命中的行高亮。
    再点同一格取消。没有 ``link`` 时单元格不可点，行为与旧版完全一致。

    示例
    ----
    >>> eazy_data_viz.charts_extra.table(df, columns=["月份", "大区", "销售额"], limit=50)
    >>> eazy_data_viz.charts_extra.table(
    ...     df, groupby={"columns": ["大区"], "value": "销售额", "agg": "sum"})
    >>> eazy_data_viz.charts_extra.table(
    ...     df, columns=["大区", "销售额"], total=True, index=True, bar="销售额"
    ... )
    """
    df = _frame.ensure_frame(data)
    group = None
    if groupby is not None:
        if columns is not None:
            raise ValueError(
                "table 的 columns 参数已由 groupby 取代：要明细就只传 columns，"
                '要汇总就只传 groupby={"columns": [...], "value": "...", "agg": "sum"}，不要同时传。'
            )
        group = _parse_table_groupby(df, groupby)
        if group["value"] is not None:
            if group["agg"] not in ("count", "unique"):
                df = _coerce_numeric(df, [("groupby.value（汇总数值）", group["value"])])
        columns = list(group["columns"])
        if group["value"] is not None and not _metric.is_follow(group["value"]):
            columns.append(group["value"])
    elif columns is None:
        columns = [c for c in df.columns][:12]
    else:
        columns = [c for c in _as_list(columns) if c is not None]
    if not columns:
        raise ValueError(
            'table 需要至少 1 列，例如 table(df, columns=["月份", "销售额"])。'
        )
    if group is None:
        _require_cols(df, [("columns[%d]" % i, c) for i, c in enumerate(columns)])
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("limit 需要是 >=1 的整数（最多显示多少行），收到 %r" % (limit,))
    show_limit = int(min(limit, 200))
    if max_rows is None:
        # 汇总必须基于完整数据算，否则数字和 pandas 对不上；明细表默认只嵌 200 行。
        max_rows = _frame.MAX_ROWS if group is not None else 200
    if not isinstance(max_rows, int) or isinstance(max_rows, bool) or max_rows < 0:
        raise ValueError("max_rows 需要是 >=0 的整数（或 None 表示自动），收到 %r" % (max_rows,))
    embed_rows = int(min(int(max_rows), _frame.MAX_ROWS))

    # ---- 中国式报表参数校验（total / index / bar / stripe）----
    for _pname, _pval in (("total", total), ("index", index), ("stripe", stripe)):
        if not isinstance(_pval, bool):
            raise ValueError(
                "%s 需要是 bool（True / False），收到 %r" % (_pname, _pval)
            )
    bar_cols = _table_bar_cols(df, columns, bar)

    spec, records, ref, info = _ext(
        "table",
        df,
        {
            "columns": [c for c in columns if not _metric.is_follow(c)],
            "value": group["value"] if group else None,
        },
        title=title
        if title is not None
        else ("汇总数据" if group else "明细数据"),
        subtitle=subtitle,
        xtitle=None,
        ytitle=None,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=group["agg"] if group else "sum",
        sort=None,
        top_n=None,
        legend=False,
        labels=False,
        zoom=False,
        drill=None,
        link=link,
        max_rows=embed_rows,
        columns=[str(c) for c in columns],
        limit=show_limit,
        groupby=_json_groupby(group),
        total=total,
        index=index,
        bar=(list(bar_cols) if bar_cols else None),
        stripe=stripe,
    )
    if group is not None and (total or index or bar_cols):
        info.setdefault("warnings", []).append(
            "汇总表模式下 total / index / bar 不生效：汇总表每行已经是一个分组，"
            "没有可加合计或行号的明细行（1.6.2 起会提示，不再静默忽略）。"
        )
    if group is not None and info.get("n_total", 0) > 50000 and not info.get("truncated"):
        est = info["n_total"] * max(1, len(records.get("cols") or [])) * 12 / 1000000.0
        info.setdefault("warnings", []).append(
            "汇总表需要完整数据才能算准，默认嵌入了全部 %d 行（约 %.1f MB），页面会比较大："
            "数据稳定时可以先 df.groupby(...).sum() 预聚合，或传 max_rows=20000 限制嵌入行数"
            "（注意此时汇总是按嵌入的行算的）。" % (info["n_total"], est)
        )
    return Chart(spec, records, ref, info)


# 词云内置形状（前端 canvas 里按这些名字画掩膜）
_WC_SHAPES = (
    "circle", "cardioid", "diamond", "triangle",
    "square", "star", "pentagon", "heart",
)
_WC_IMAGE_EXT = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".webp": "image/webp", ".gif": "image/gif", ".bmp": "image/bmp",
    ".svg": "image/svg+xml",
}
_WC_MAX_SHAPE_BYTES = 2 * 1024 * 1024


def _parse_cloud_shape(shape):
    """把 shape 归一化成前端能用的字典：内置形状只存名字，图片转成 data URI。"""
    if shape is None:
        return None
    if not isinstance(shape, str):
        raise ValueError(
            "wordcloud 的 shape 需要是内置形状名或图片路径，收到 %r。内置形状：%s。"
            % (shape, "、".join(_WC_SHAPES))
        )
    key = shape.strip()
    if not key:
        raise ValueError('wordcloud 的 shape 不能是空字符串：内置形状 %s，或本地图片路径。'
                         % "、".join(_WC_SHAPES))
    if key.lower() in _WC_SHAPES:
        return {"type": "builtin", "name": key.lower()}
    path = os.path.abspath(os.path.expanduser(key))
    if not os.path.isfile(path):
        raise ValueError(
            "wordcloud 的 shape=%r 既不是内置形状（%s），也不是存在的图片文件。"
            % (shape, "、".join(_WC_SHAPES))
        )
    ext = os.path.splitext(path)[1].lower()
    if ext not in _WC_IMAGE_EXT:
        raise ValueError(
            "wordcloud 的 shape 图片只支持 %s，收到 %s。"
            % ("、".join(sorted(_WC_IMAGE_EXT)), ext or "(无扩展名)")
        )
    size = os.path.getsize(path)
    if size > _WC_MAX_SHAPE_BYTES:
        raise ValueError(
            "wordcloud 的 shape 图片不能超过 2 MB（当前 %.1f MB）：图片会整段内联进 HTML。"
            % (size / 1048576.0,)
        )
    with open(path, "rb") as fh:
        raw = fh.read()
    mime = _WC_IMAGE_EXT[ext]
    b64 = base64.b64encode(raw).decode("ascii")
    return {
        "type": "image",
        "mime": mime,
        "name": os.path.basename(path),
        "src": "data:%s;base64,%s" % (mime, b64),
    }


def wordcloud(
    data: pd.DataFrame,
    names: str | None | Follow = None,
    values: str | None | Follow = None,
    *,
    agg: str | None = None,
    sort: str | None = None,
    top_n: int | None = 30,
    title: str | None = None,
    subtitle: str | None = None,
    fmt: str = "compact",
    height: int = 360,
    abs_height: bool = False,
    theme: str = "light",
    link: str | tuple | dict | None = None,
    shape: str | None = None,
    max_rows: int = _frame.MAX_ROWS,
) -> Chart:
    """词云（HTML/CSS 或 canvas 渲染）：每个类目一个词，字号随数值变化，最多 30 个。

    示例
    ----
    >>> eazy_data_viz.charts_extra.wordcloud(df, names="关键词", values="提及次数")

    ``shape`` 可以给内置形状（circle / cardioid / diamond / triangle / square /
    star / pentagon / heart），也可以给一张本地图片的路径（png / jpg / webp / gif /
    bmp / svg，≤ 2 MB）：词会按这张图的轮廓排布。::

        px.wordcloud(df, names="关键词", values="次数", shape="star")
        px.wordcloud(df, names="关键词", values="次数", shape="assets/logo.png")
    """
    df = _frame.ensure_frame(data)
    shape_spec = _parse_cloud_shape(shape)
    if names is None:
        names = _pick_dim(df)
    if names is None:
        raise ValueError(
            'wordcloud 需要 names（词/类目列），例如 wordcloud(df, names="关键词", values="次数")；'
            "当前 DataFrame 里没有分类/时间列。"
        )
    _frame.require_column(df, names, "names（词/类目）")
    if values is not None:
        df = _coerce_numeric(df, [("values（数值）", values)], agg=agg)
    spec, records, ref, info = _ext(
        "wordcloud",
        df,
        {"names": names, "value": values},
        title=title if title is not None else "%s 词云" % names,
        subtitle=subtitle,
        xtitle=None,
        ytitle=None,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        abs_height=abs_height,
        theme=theme,
        agg=("count" if (values is None and agg != "unique") else agg),
        sort=sort,
        top_n=top_n,
        legend=False,
        labels=False,
        zoom=False,
        drill=None,
        link=link,
        max_rows=max_rows,
        shape=shape_spec,
    )
    return Chart(spec, records, ref, info)


def group_kpi(
    data: pd.DataFrame = None,
    names: str | None | Follow = None,
    values: str | None | Follow = None,
    *,
    items: list | None = None,
    agg: str | None = None,
    sort: str | None = "desc",
    top_n: int | None = 6,
    unit: str | None = None,
    delta: float | None = None,
    fmt: str = "compact",
    title: str | None = None,
    subtitle: str | None = None,
    height: int = 140,
    abs_height: bool = False,
    theme: str = "light",
) -> Chart:
    """KPI 卡片组（HTML 渲染）：一排指标卡片。

    三种用法：

    * ``group_kpi(df)`` —— 每个数值列一张卡片（按列自动取总量，默认只取前 6 项，用 ``top_n`` 调整）；
    * ``group_kpi(df, names="大区", values="销售额")`` —— 每个类目一张卡片；
    * ``group_kpi(items=[{"label": "总销售额", "value": 123, "delta": 0.12}])``
      —— 完全手工指定（``delta`` 是百分比小数，>0 显示上涨）。

    示例
    ----
    >>> eazy_data_viz.charts_extra.group_kpi(df, names="大区", values="销售额", unit="万元")
    """
    if _metric.is_follow(values):
        values = values.default
    if agg is None:
        agg = _metric.agg_for(values or names)
    _check_agg(agg or "sum")
    agg = agg or "sum"
    _check_fmt(fmt)
    if not isinstance(top_n, int) or isinstance(top_n, bool) or top_n < 1:
        raise ValueError("top_n 需要是 >=1 的整数，收到 %r" % (top_n,))

    result = []
    if items is not None:
        if isinstance(items, dict):
            items = [items]
        for i, it in enumerate(_as_list(items)):
            if not isinstance(it, dict):
                raise TypeError(
                    "items[%d] 需要是 dict，例如 {\"label\": \"总销售额\", \"value\": 123}，收到 %r"
                    % (i, type(it).__name__)
                )
            value = _num_or_none(it.get("value"))
            if value is None:
                raise ValueError("items[%d] 缺少可用的数值 value，收到 %r" % (i, it.get("value")))
            result.append(
                {
                    "label": str(it.get("label", "")),
                    "value": value,
                    "delta": (None if it.get("delta") is None else _num_or_none(it.get("delta"))),
                    "unit": (None if it.get("unit") is None else str(it.get("unit"))),
                    "fmt": str(it.get("fmt") or fmt or "compact"),
                    "hint": (None if it.get("hint") is None else str(it.get("hint"))),
                }
            )
    else:
        if data is None:
            raise ValueError(
                'group_kpi 需要 data（DataFrame）或 items=[...]，例如 '
                'group_kpi(df, names="大区", values="销售额")。'
            )
        df = _frame.ensure_frame(data)
        if len(df) == 0:
            raise ValueError("数据为空（0 行），无法绘图。")
        if names is None and values is None:
            num_cols = [
                c for c in df.columns if _frame.column_kind(df[c]) == _frame.KIND_NUM
            ][: int(top_n)]
            if not num_cols:
                raise ValueError(
                    "group_kpi 需要至少 1 个数值列（或直接传 items=[...]）；"
                    "当前 DataFrame 里没有数值列。"
                )
            for c in num_cols:
                if agg == "unique":
                    v = _apply_agg(df[c].tolist(), agg)
                else:
                    s = pd.to_numeric(df[c], errors="coerce")
                    v = _apply_agg(s.tolist(), agg)
                result.append(
                    {
                        "label": str(c),
                        "value": v,
                        "delta": None,
                        "unit": (None if unit is None else str(unit)),
                        "fmt": fmt or "compact",
                        "hint": None,
                    }
                )
        else:
            if names is None:
                names = _pick_dim(df)
            if names is None:
                raise ValueError(
                    'group_kpi 需要 names（分组列），例如 group_kpi(df, names="大区", values="销售额")。'
                )
            _frame.require_column(df, names, "names（分组）")
            if values is not None:
                df = _coerce_numeric(df, [("values（数值）", values)], agg=agg)
            if values is None or agg == "count":
                # 计数看的是行数，values 列只用来分组，取什么值都一样
                raw_values = [1.0] * len(df)
            elif agg == "unique":
                # 去重计数要保留原始值（文本也要数），不能 to_numeric
                raw_values = df[values].tolist()
            else:
                raw_values = pd.to_numeric(df[values], errors="coerce").tolist()
            buckets = {}
            order = []
            for lab, raw in zip(df[names].tolist(), raw_values):
                key = "—" if pd.isna(lab) else str(lab)
                if key not in buckets:
                    buckets[key] = []
                    order.append(key)
                buckets[key].append(raw)
            for key in order:
                v = _apply_agg(buckets[key], agg)
                result.append(
                    {
                        "label": key,
                        "value": v,
                        "delta": None,
                        "unit": (None if unit is None else str(unit)),
                        "fmt": fmt or "compact",
                        "hint": None,
                    }
                )
            if sort == "desc":
                result.sort(key=lambda d: d["value"], reverse=True)
            elif sort == "asc":
                result.sort(key=lambda d: d["value"])
            result = result[: int(top_n)]

    if not result:
        raise ValueError("group_kpi 没有可展示的指标。")
    if delta is not None:
        if isinstance(delta, (list, tuple)):
            for i, d in enumerate(delta):
                if i < len(result):
                    result[i]["delta"] = _num_or_none(d)
        else:
            result[0]["delta"] = _num_or_none(delta)

    spec = _manual_spec(
        "group_kpi",
        title=title if title is not None else "关键指标",
        subtitle=subtitle,
        theme=theme,
        height=height,
        abs_height=abs_height,
        fmt=fmt,
        agg=agg,
        top_n=int(top_n),
    )
    spec["items"] = result
    return _empty_chart(spec)


# ==========================================================================
# 把公共参数说明追加到每个函数的 docstring（_COMMON_DOC 是纯文本，需运行期拼接）
# ==========================================================================
_EXTRA_FUNCS = [
    waterfall,
    bullet,
    lollipop,
    dumbbell,
    pareto,
    slope,
    bump,
    radar,
    rose,
    parallel,
    pictorial,
    target,
    trend,
    quadrant,
    matrix,
    sparkline,
    ring_progress,
    sunburst,
    tree,
    sankey,
    graph,
    theme_river,
    calendar,
    gantt,
    candlestick,
    pyramid,
    area_pct,
    bar_pct,
    progress,
    tile,
    table,
    wordcloud,
    group_kpi,
]
for _fn in _EXTRA_FUNCS:
    _doc = (_fn.__doc__ or "").rstrip()
    _fn.__doc__ = (_doc + "\n" + _COMMON_DOC).strip() if _doc else _COMMON_DOC.strip()
del _fn, _doc, _EXTRA_FUNCS


# ==========================================================================
# table() 的辅助函数（中国式报表：数据条列归一化）
# ==========================================================================
def _table_bar_cols(df, columns, bar):
    """把 ``table(bar=...)`` 归一化成数据条列名列表（保持用户给出的顺序）。

    ``bar`` 支持 True（自动取第一个数值列）/ "列名" / ["列1", "列2"] / None，
    类型或列名不合法时抛中文 ValueError。
    """
    col_map = {}
    for c in columns:
        col_map.setdefault(str(c), c)

    if bar is None or bar is False:
        return []
    if bar is True:
        for name in [str(c) for c in columns]:
            if _frame.column_kind(df[col_map[name]]) == _frame.KIND_NUM:
                return [name]
        raise ValueError(
            "bar=True 需要一个数值列来自动画数据条，但 columns 里没有数值列；"
            '请改用 bar="列名" 指定数值列。'
        )
    if isinstance(bar, str):
        names = [bar]
    elif isinstance(bar, (list, tuple)):
        names = list(bar)
        if not names:
            raise ValueError("bar 不能是空列表；不需要数据条请传 bar=None。")
    else:
        raise ValueError(
            'bar 只支持 True / "列名" / ["列1", "列2"] / None，收到 %r' % (bar,)
        )

    out = []
    kind_cn = {
        _frame.KIND_NUM: "数值",
        _frame.KIND_TIME: "时间",
        _frame.KIND_CAT: "文本",
        _frame.KIND_BOOL: "布尔",
    }
    for name in names:
        if not isinstance(name, str):
            raise ValueError(
                'bar 列表里只能放列名（str），收到 %r。' % (name,)
            )
        if name in out:  # 去重，避免同一列画两遍
            continue
        if name not in col_map:
            raise ValueError(
                "bar 指定的列 %r 不在 columns 里；当前可用的列有：%s。"
                % (name, "、".join([str(c) for c in columns]))
            )
        kind = _frame.column_kind(df[col_map[name]])
        if kind != _frame.KIND_NUM:
            raise ValueError(
                "bar 只能用于数值列，%r 是%s列；请改用 total=True 求和或去掉 bar。"
                % (name, kind_cn.get(kind, kind))
            )
        out.append(name)
    return out
