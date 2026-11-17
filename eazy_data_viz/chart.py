"""图表对象与用户 API。

用户只需要：

    import eazy_data_viz
    chart = eazy_data_viz.bar(df, x="月份", y="销售额", color="地区", title="月度销售")
    chart.show()

不需要写任何 JSON / JavaScript / 前端配置。
"""
from __future__ import annotations

import os
import sys
import tempfile
import webbrowser

from . import frame as _frame

__all__ = [
    "Chart",
    "bar",
    "line",
    "area",
    "pie",
    "scatter",
    "histogram",
    "heatmap",
    "box",
    "funnel",
    "treemap",
    "gauge",
    "kpi",
    "combo",
]

# 支持的聚合方式
AGGS = ("sum", "mean", "count", "max", "min", "median")
FORMATS = ("compact", "thousands", "raw", "percent", "currency")

# 各类图表里「必须是数值」的角色键；其余角色键一律按维度处理。
_NUMERIC_ROLE_KEYS = {
    "bar": ("y",),
    "line": ("y",),
    "area": ("y",),
    "combo": ("y", "y2"),
    "scatter": ("x", "y", "size"),
    "pie": ("value",),
    "funnel": ("value",),
    "histogram": ("value", "y"),
    "heatmap": ("value",),
    "box": ("y",),
    "treemap": ("value",),
}

_SEQ = [0]


def _next_id():
    _SEQ[0] += 1
    return "c%d" % _SEQ[0]


def _check_agg(agg):
    if agg not in AGGS:
        raise ValueError("agg=%r 不支持，可选：%s" % (agg, ", ".join(AGGS)))
    return agg


def _check_fmt(fmt):
    if fmt is not None and fmt not in FORMATS:
        raise ValueError("fmt=%r 不支持，可选：%s" % (fmt, ", ".join(FORMATS)))
    return fmt


def _check_lim(lim, name):
    if lim is None:
        return None
    if not isinstance(lim, (list, tuple)) or len(lim) != 2:
        raise ValueError("%s 需要是 (最小值, 最大值) 两元组，例如 %s=(0, 100)" % (name, name))
    lo, hi = lim
    lo = None if lo is None else float(lo)
    hi = None if hi is None else float(hi)
    if lo is not None and hi is not None and lo > hi:
        lo, hi = hi, lo
    return [lo, hi]


# --------------------------------------------------------------------------
# Chart 对象
# --------------------------------------------------------------------------
class Chart:
    """一张图。由 ``eazy_data_viz.bar / line / pie ...`` 返回，通常不需要直接构造。"""

    def __init__(self, spec, data, ref, warnings=None):
        self.spec = spec
        self.data = data
        self.data_ref = ref
        self.warnings = warnings or {}

    # ---- 展示 -----------------------------------------------------------
    def to_html(self, inline=True):
        """返回一张完整的独立 HTML 页面（可直接写文件 / 放进 iframe / 发邮件）。"""
        from .render import build_page

        return build_page([self], inline=inline)

    def palette(self, name):
        """单独给这一张图指定配色（覆盖页面默认），返回自身，方便链式调用。

        可用配色见 ``eazy_data_viz.palettes()``：google / antd / tableau / carbon /
        echarts / morandi / tailwind。
        """
        from . import palette as _palette

        self.spec["palette"] = _palette.check(name)
        return self

    def unit(self, unit):
        """给整张图统一一个数值单位（对齐帆软 / 观远等中文 BI 的观感）。

        支持中文单位：``"千"`` / ``"万"`` / ``"百万"`` / ``"亿"``，
        也可以直接传倍数：``1e3`` / ``1e4`` / ``1e6`` / ``1e8``。
        设置后坐标轴、tooltip、标签、KPI 卡、明细表里的数值都按
        「数值 / 倍数」展示，最多 2 位小数并去掉末尾的 0，例如::

            bar(df, x="大区", y="销售额").unit("万")      # 12345678 → 1235万
            bar(df, x="大区", y="销售额").unit(1e6)       # 2500000 → 2.5百万

        与 ``fmt="percent"/"currency"/"raw"/"thousands"`` 同时存在时以 fmt 为准
        （unit 不参与换算）。返回自身，方便链式调用。
        """
        scales = {"千": 1e3, "万": 1e4, "百万": 1e6, "亿": 1e8}
        if unit is None or (isinstance(unit, str) and not unit.strip()):
            raise ValueError("unit 不能为空，可选：千 / 万 / 百万 / 亿，或 1e3 / 1e4 / 1e6 / 1e8")
        if isinstance(unit, str):
            name = unit.strip()
            if name in scales:
                self.spec["unit"] = name
                return self
            try:
                num = float(name)
            except (TypeError, ValueError):
                raise ValueError(
                    "unit=%r 不支持，可选：千 / 万 / 百万 / 亿，或 1e3 / 1e4 / 1e6 / 1e8" % (unit,))
        else:
            try:
                num = float(unit)
            except (TypeError, ValueError):
                raise ValueError(
                    "unit=%r 不支持，可选：千 / 万 / 百万 / 亿，或 1e3 / 1e4 / 1e6 / 1e8" % (unit,))
        if num not in (1e3, 1e4, 1e6, 1e8):
            raise ValueError(
                "unit=%r 不是常用的数量级，可选：千 / 万 / 百万 / 亿，或 1e3 / 1e4 / 1e6 / 1e8" % (unit,))
        self.spec["unit"] = int(num)
        return self

    def save(self, path, inline=True):
        """保存为 HTML 文件，返回绝对路径。"""
        html = self.to_html(inline=inline)
        path = os.path.abspath(path)
        d = os.path.dirname(path)
        if d and not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        return path

    def show(self, open_browser=None):
        """在 Streamlit / Jupyter / 普通脚本里都能正确显示。

        * Streamlit：优先 ``st.components.v2``（无 iframe、高度自适应），
          旧版本自动回退到 ``st.components.v1.html``；
        * Jupyter Notebook / Lab：自动使用 ``IPython.display.HTML``；
        * 普通 Python 脚本：写一个临时 HTML 文件并打印路径（tty 环境自动打开浏览器）。
        """
        from .render import is_streamlit, in_notebook, streamlit_show

        if is_streamlit():
            streamlit_show([self], cols=1)
            return self

        if in_notebook():
            from IPython.display import HTML, display

            display(HTML(self.to_html(inline=True)))
            return self

        path = os.path.join(tempfile.mkdtemp(prefix="eazy_"), "chart.html")
        self.save(path)
        if open_browser is None:
            open_browser = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
        print("[eazy_data_viz] 已生成图表：%s" % path)
        if open_browser:
            webbrowser.open("file://" + path.replace("\\", "/"))
        return self

    def _repr_html_(self):
        # Jupyter 直接输入 chart 时也能看到图
        return self.to_html(inline=True)

    # ---- 便捷 -----------------------------------------------------------
    @property
    def title(self):
        return self.spec.get("title")

    def __repr__(self):
        return "<eazy_data_viz.Chart %s title=%r rows=%d>" % (
            self.spec.get("type"),
            self.spec.get("title"),
            self.data.get("n", 0),
        )


# --------------------------------------------------------------------------
# 内部：组装 spec
# --------------------------------------------------------------------------
def _auto_title(kind, roles, agg):
    x, y, color = roles.get("x"), roles.get("y"), roles.get("color")
    names, value = roles.get("names"), roles.get("value")
    if agg == "count" and y is None:
        y = "记录数"
    if kind == "bar":
        t = "%s 按 %s" % (y, x)
    elif kind in ("line", "area"):
        t = "%s 趋势" % y
    elif kind == "pie":
        t = "%s 构成" % (value or names)
    elif kind == "scatter":
        t = "%s 与 %s" % (y, x)
    elif kind == "histogram":
        t = "%s 分布" % (roles.get("value") or y)
    elif kind == "heatmap":
        t = "%s 热力图" % value
    elif kind == "box":
        t = "%s 分布" % y
    elif kind == "funnel":
        t = "%s 漏斗" % names
    elif kind == "treemap":
        t = "%s 层级构成" % value
    else:
        t = None
    if t and color:
        t += " · 按 %s" % color
    return t


# 各图表在「用户显式传 height=None」时使用的默认高度（与函数签名里的默认值保持一致）。
_HEIGHT_DEFAULTS = {
    "bar": 380, "line": 380, "area": 360, "pie": 360, "scatter": 400,
    "histogram": 380, "heatmap": 380, "box": 380, "funnel": 380,
    "treemap": 420, "gauge": 260, "combo": 400, "pareto": 400,
    "bump": 420, "waterfall": 400, "sankey": 420, "graph": 420,
}


def _base_spec(
    kind,
    data,
    roles,
    *,
    title,
    subtitle,
    xtitle,
    ytitle,
    xlim,
    ylim,
    fmt,
    height,
    theme,
    agg,
    sort,
    top_n,
    legend,
    labels,
    zoom,
    drill,
    link,
    max_rows,
    **extra
):
    _check_agg(agg)
    _check_fmt(fmt)
    if theme not in ("light", "dark"):
        raise ValueError('theme 只支持 "light" / "dark"，收到 %r' % (theme,))
    if height is not None and (not isinstance(height, (int, float)) or height < 120):
        raise ValueError("height 至少 120（像素），收到 %r" % (height,))
    if top_n is not None:
        if not isinstance(top_n, int) or isinstance(top_n, bool) or top_n < 1:
            raise ValueError("top_n 需要是 >=1 的整数（只显示前 N 项），收到 %r" % (top_n,))

    df = _frame.ensure_frame(data)

    # 下钻维度：drill 的第一层就是 x；也可以只传 drill 让 x 自动取 drill[0]。
    if drill is not None:
        if isinstance(drill, str):
            drill = [drill]
        drill = [str(d) for d in drill]
        if not drill:
            raise ValueError("drill 不能是空列表；不需要下钻请传 drill=None。")
        for d in drill:
            _frame.require_column(df, d, "下钻维度", "drill 里的每一列都必须是 df 的列名。")
        if roles.get("x") is None:
            roles["x"] = drill[0]
        elif roles["x"] != drill[0]:
            # x="大区" + drill=["产品","渠道"] → 自动补全为 ["大区","产品","渠道"]
            drill = [roles["x"]] + drill
        roles["_extra"] = drill

    # 按图表类型决定哪些角色是数值、哪些是维度：
    # 例如热力图的 y 是分类维度，散点图的 x 是数值，饼图的 value 是数值。
    numeric_cols, dim_cols = [], []
    for rk, rv in roles.items():
        if rv is None:
            continue
        if rk in _NUMERIC_ROLE_KEYS.get(kind, ()):
            numeric_cols.append(rv)
        else:
            dim_cols.append(rv)
    records, ref, info = _frame.prepare(
        df, roles, max_rows=max_rows,
        numeric_roles=numeric_cols, dimension_roles=dim_cols,
    )


    if roles.get("x") is None and kind in ("bar", "line", "area", "scatter", "heatmap"):
        raise ValueError(
            "缺少 x：请用 x=\"列名\" 指定横轴（分类/时间）列。"
        )

    # 排序默认值（按语义自动选择，用户不用关心）：
    #   - x 是时间/数值列 → 按 x 升序（时间线天然顺序）
    #   - 柱状图 → 按数值降序（排行榜更直观）
    #   - 折线/面积/热力图 → 保持数据原始顺序
    if sort is None:
        xcol = roles.get("x")
        xkind = records["kinds"].get(str(xcol)) if xcol is not None else None
        ordered_x = xcol is not None and str(xcol) in (records.get("orders") or {})
        if kind in ("bar", "line", "area", "combo", "heatmap"):
            if xkind in (_frame.KIND_TIME, _frame.KIND_NUM) or ordered_x:
                sort = "x"
            elif kind == "bar":
                sort = "desc"
            else:
                sort = "none"

    warnings = []
    if info["truncated"]:
        warnings.append(
            "数据 %d 行，超过 max_rows=%d，已均匀采样 %d 行用于绘图。"
            % (info["n_total"], max_rows, records["n"])
        )
    if info["dropped_cols"]:
        warnings.append(
            "列数超过 %d，以下列未嵌入（不影响已用到的列）：%s"
            % (_frame.MAX_COLS, ", ".join(info["dropped_cols"][:8]))
        )

    spec = {
        "id": _next_id(),
        "type": kind,
        "title": title if title is not None else _auto_title(kind, roles, agg),
        "subtitle": subtitle,
        "theme": theme,
        "height": int(height if height is not None else _HEIGHT_DEFAULTS.get(kind, 380)),
        "dataRef": ref,
        "roles": dict(roles),
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
        "drill": drill,
        "link": link,
    }
    spec.update(extra)
    return spec, records, ref, {"warnings": warnings, "n_total": info["n_total"]}


# --------------------------------------------------------------------------
# 公共参数说明（写进每个函数的 docstring）
# --------------------------------------------------------------------------
_COMMON_DOC = """
    通用参数（所有图表函数都支持）
    ------------------------------
    title, subtitle : str
        标题 / 副标题，默认自动生成。
    xtitle, ytitle : str
        坐标轴名称，默认用列名；传 "" 隐藏。
    xlim, ylim : (min, max)
        坐标轴范围，例如 ylim=(0, 100000)。
    fmt : str
        数值格式：compact(默认, 1.2万) / thousands(12,345) / raw / percent / currency(¥)。
    height : int
        图高（像素），默认 380。
    theme : str
        "light"（默认）或 "dark"。
    agg : str
        聚合方式：sum(默认) / mean / count / max / min / median。
    sort : str
        类目排序："desc"(默认) / "asc" / "none"(保持数据顺序)。
    top_n : int
        只保留前 N 个类目，其余合并为"其他"。
    legend : bool
        是否显示图例（有 color 时默认显示）。
    labels : bool
        是否在图形上直接标数值。
    zoom : "auto" | True | False
        数据缩放条：auto 表示类目较多时自动出现。
    drill : list[str]
        下钻维度，例如 drill=["大区", "省份", "城市"]，点击图形逐级下钻。
    link : str
        联动组名。同一组内的图点击后会互相过滤（需要数据里有同名列）。
    max_rows : int
        单图最多嵌入行数，默认 200000（超出自动均匀采样；传 None 表示不采样）。
"""


# --------------------------------------------------------------------------
# 各图表构造函数
# --------------------------------------------------------------------------
def bar(
    data,
    x,
    y=None,
    color=None,
    *,
    agg="sum",
    stack=False,
    horizontal=False,
    sort=None,
    top_n=None,
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    xlim=None,
    ylim=None,
    fmt="compact",
    height=380,
    theme="light",
    drill=None,
    link=None,
    legend=True,
    labels=False,
    zoom="auto",
    max_rows=_frame.MAX_ROWS,
    percent=False,
    section=None,
):
    """柱状图 / 条形图（支持分组、堆叠、百分比、下钻、联动）。

    参数
    ----
    data : DataFrame
    x : str
        横轴（类目）列，例如 "月份"。
    y : str, 可选
        数值列；不传则统计每个类目的行数（count）。
    color : str, 可选
        分组/图例列，例如 "地区"（会变成多条系列）。

    示例
    ----
    >>> eazy_data_viz.bar(df, x="月份", y="销售额", color="地区", title="月度销售")
    >>> eazy_data_viz.bar(df, x="大区", y="销售额", horizontal=True, drill=["大区", "省份", "城市"])
    """
    spec, records, ref, info = _base_spec(
        "bar",
        data,
        {"x": x, "y": y, "color": color},
        title=title,
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        theme=theme,
        agg=("count" if y is None else agg),
        sort=sort,
        top_n=top_n,
        legend=legend,
        labels=labels,
        zoom=zoom,
        drill=drill,
        link=link,
        max_rows=max_rows,
        stack=bool(stack),
        horizontal=bool(horizontal),
        percent=bool(percent) or None,
        section=section,
    )
    return Chart(spec, records, ref, info)


def line(
    data,
    x,
    y,
    color=None,
    *,
    agg="sum",
    smooth=True,
    area=False,
    markers=None,
    sort=None,
    top_n=None,
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    xlim=None,
    ylim=None,
    fmt="compact",
    height=380,
    theme="light",
    drill=None,
    link=None,
    legend=True,
    labels=False,
    zoom="auto",
    max_rows=_frame.MAX_ROWS,
    step=False,
    percent=False,
    section=None,
):
    """折线图 / 面积图 / 阶梯图。

    示例
    ----
    >>> eazy_data_viz.line(df, x="日期", y="销售额", color="产品", area=True)
    """
    spec, records, ref, info = _base_spec(
        "line",
        data,
        {"x": x, "y": y, "color": color},
        title=title,
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
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
        smooth=bool(smooth),
        area=bool(area),
        markers=markers,
        step=bool(step) or None,
        percent=bool(percent) or None,
        section=section,
    )
    return Chart(spec, records, ref, info)


def area(data, x, y, color=None, **kwargs):
    """面积图 = ``line(..., area=True)``。"""
    kwargs["area"] = True
    return line(data, x, y, color, **kwargs)


def pie(
    data,
    names,
    values=None,
    *,
    donut=False,
    agg="sum",
    sort="desc",
    top_n=None,
    title=None,
    subtitle=None,
    fmt="compact",
    height=360,
    theme="light",
    labels=True,
    link=None,
    max_rows=_frame.MAX_ROWS,
):
    """饼图 / 环图。

    参数
    ----
    names : str
        类目列（决定扇区）。
    values : str, 可选
        数值列；不传则统计行数。

    示例
    ----
    >>> eazy_data_viz.pie(df, names="产品", values="销售额", donut=True)
    """
    spec, records, ref, info = _base_spec(
        "pie",
        data,
        {"names": names, "value": values},
        title=title,
        subtitle=subtitle,
        xtitle=None,
        ytitle=None,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        theme=theme,
        agg=("count" if values is None else agg),
        sort=sort,
        top_n=top_n,
        legend=True,
        labels=labels,
        zoom=False,
        drill=None,
        link=link,
        max_rows=max_rows,
        donut=bool(donut),
    )
    return Chart(spec, records, ref, info)


def scatter(
    data,
    x,
    y,
    color=None,
    size=None,
    *,
    agg="sum",
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    xlim=None,
    ylim=None,
    fmt="compact",
    height=380,
    theme="light",
    link=None,
    legend=True,
    max_rows=_frame.MAX_ROWS,
):
    """散点图（x / y 都必须是数值列，可选气泡大小）。

    示例
    ----
    >>> eazy_data_viz.scatter(df, x="广告投入", y="销售额", size="订单数", color="地区")
    """
    spec, records, ref, info = _base_spec(
        "scatter",
        data,
        {"x": x, "y": y, "color": color, "size": size},
        title=title,
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=xlim,
        ylim=ylim,
        fmt=fmt,
        height=height,
        theme=theme,
        agg=agg,
        sort="none",
        top_n=None,
        legend=legend,
        labels=False,
        zoom=False,
        drill=None,
        link=link,
        max_rows=max_rows,
    )
    _ensure_numeric(records, x, "x")
    _ensure_numeric(records, y, "y")
    if size is not None:
        _ensure_numeric(records, size, "size")
    return Chart(spec, records, ref, info)


def histogram(
    data,
    column=None,
    *,
    bins=20,
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle="频数",
    fmt="compact",
    height=360,
    theme="light",
    labels=False,
    max_rows=_frame.MAX_ROWS,
):
    """直方图（数值分布）。

    column 不传时，自动取 DataFrame 里唯一的数值列。
    """
    df = _frame.ensure_frame(data)
    if column is None:
        nums = [c for c in df.columns if _frame.column_kind(df[c]) == _frame.KIND_NUM]
        if len(nums) != 1:
            raise ValueError(
                "histogram 需要指定一个数值列，例如 histogram(df, column=\"销售额\")。"
                "当前数值列有：%s" % (", ".join(map(str, nums)) or "无")
            )
        column = nums[0]
    spec, records, ref, info = _base_spec(
        "histogram",
        data,
        {"value": column, "y": column},
        title=title,
        subtitle=subtitle,
        xtitle=xtitle or column,
        ytitle=ytitle,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        theme=theme,
        agg="count",
        sort="none",
        top_n=None,
        legend=False,
        labels=labels,
        zoom=False,
        drill=None,
        link=None,
        max_rows=max_rows,
        bins=int(bins),
    )
    _ensure_numeric(records, column, "column")
    return Chart(spec, records, ref, info)


def heatmap(
    data,
    x,
    y,
    value,
    *,
    agg="sum",
    sort=None,
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    fmt="compact",
    height=400,
    theme="light",
    labels=False,
    max_rows=_frame.MAX_ROWS,
    link=None,
):
    """热力图（x × y 的数值矩阵）。

    示例
    ----
    >>> eazy_data_viz.heatmap(df, x="星期", y="小时", value="订单数")
    >>> eazy_data_viz.heatmap(df, x="月份", y="大区", value="销售额", labels=True)  # 格子里显示数值
    """
    spec, records, ref, info = _base_spec(
        "heatmap",
        data,
        {"x": x, "y": y, "value": value},
        title=title,
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        theme=theme,
        agg=agg,
        sort=sort,
        top_n=None,
        legend=False,
        labels=labels,
        zoom=False,
        drill=None,
        link=link,
        max_rows=max_rows,
    )
    _ensure_numeric(records, value, "value")
    return Chart(spec, records, ref, info)


def box(
    data,
    x=None,
    y=None,
    *,
    title=None,
    subtitle=None,
    ytitle=None,
    fmt="compact",
    height=380,
    theme="light",
    max_rows=_frame.MAX_ROWS,
):
    """箱线图（按类目展示数值分布）。

    x 不传则只有一个箱子。
    """
    df = _frame.ensure_frame(data)
    if y is None:
        nums = [c for c in df.columns if _frame.column_kind(df[c]) == _frame.KIND_NUM]
        if len(nums) != 1:
            raise ValueError(
                "box 需要指定数值列 y，例如 box(df, x=\"地区\", y=\"销售额\")。"
                "当前数值列有：%s" % (", ".join(map(str, nums)) or "无")
            )
        y = nums[0]
    roles = {"x": x, "y": y}
    if x is None:
        roles["x"] = None
    spec, records, ref, info = _base_spec(
        "box",
        data,
        roles,
        title=title,
        subtitle=subtitle,
        xtitle=None,
        ytitle=ytitle,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        theme=theme,
        agg="median",
        sort="none",
        top_n=None,
        legend=False,
        labels=False,
        zoom=False,
        drill=None,
        link=None,
        max_rows=max_rows,
    )
    spec["roles"]["x"] = x
    _ensure_numeric(records, y, "y")
    return Chart(spec, records, ref, info)


def funnel(
    data,
    names,
    values=None,
    *,
    agg="sum",
    fmt="compact",
    height=380,
    theme="light",
    title=None,
    subtitle=None,
    labels=True,
    link=None,
    max_rows=_frame.MAX_ROWS,
):
    """漏斗图（转化/流程）。

    示例
    ----
    >>> eazy_data_viz.funnel(df, names="环节", values="人数")
    """
    spec, records, ref, info = _base_spec(
        "funnel",
        data,
        {"names": names, "value": values},
        title=title,
        subtitle=subtitle,
        xtitle=None,
        ytitle=None,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        theme=theme,
        agg=("count" if values is None else agg),
        sort="desc",
        top_n=None,
        legend=False,
        labels=labels,
        zoom=False,
        drill=None,
        link=link,
        max_rows=max_rows,
    )
    return Chart(spec, records, ref, info)


def treemap(
    data,
    path,
    value,
    *,
    agg="sum",
    title=None,
    subtitle=None,
    fmt="compact",
    height=420,
    theme="light",
    max_rows=_frame.MAX_ROWS,
):
    """矩形树图（多层级构成）。

    参数
    ----
    path : str | list[str]
        层级列，例如 ["大区", "省份", "城市"]，点击节点会自动放大下一层。

    示例
    ----
    >>> eazy_data_viz.treemap(df, path=["大区", "品类"], value="销售额")
    """
    if isinstance(path, str):
        path = [path]
    if not path:
        raise ValueError("treemap 的 path 不能为空，例如 path=[\"大区\", \"品类\"]。")
    spec, records, ref, info = _base_spec(
        "treemap",
        data,
        {"path": list(path), "value": value},
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
        sort="desc",
        top_n=None,
        legend=False,
        labels=True,
        zoom=False,
        drill=None,
        link=None,
        max_rows=max_rows,
    )
    _ensure_numeric(records, value, "value")
    return Chart(spec, records, ref, info)


def gauge(
    value,
    *,
    label=None,
    min=0,
    max=100,
    fmt="raw",
    unit=None,
    height=260,
    theme="light",
    title=None,
    subtitle=None,
):
    """仪表盘（单个数值）。

    示例
    ----
    >>> eazy_data_viz.gauge(87.5, label="完成率", max=100, unit="%")
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise TypeError(
            "gauge 接受单个数值，例如 eazy_data_viz.gauge(87.5)。"
            "如果要聚合 DataFrame，请用 eazy_data_viz.kpi(df, value=\"销售额\")。"
        )
    if max <= min:
        raise ValueError("gauge 的 max 必须大于 min。")
    spec = {
        "id": _next_id(),
        "type": "gauge",
        "title": title if title is not None else (label or ""),
        "subtitle": subtitle,
        "theme": theme,
        "height": int(height),
        "dataRef": None,
        "roles": {},
        "agg": "sum",
        "fmt": fmt,
        "sort": None,
        "topN": None,
        "xtitle": None,
        "ytitle": None,
        "xlim": None,
        "ylim": None,
        "legend": False,
        "labels": True,
        "zoom": False,
        "drill": None,
        "link": None,
        "value": value,
        "min": float(min),
        "max": float(max),
        "label": label,
        "unit": unit,
    }
    return Chart(spec, {"cols": [], "rows": [], "n": 1}, None, {})


def kpi(
    data=None,
    value=None,
    *,
    agg="sum",
    label=None,
    fmt=None,
    delta=None,
    delta_label=None,
    inverse=False,
    target=None,
    target_label=None,
    spark=None,
    spark_x=None,
    hint=None,
    unit=None,
    prefix=None,
    accent=0,
    height=150,
    theme="light",
    title=None,
    subtitle=None,
    link=None,
    section=None,
):
    """KPI 数字卡片（驾驶舱指标头，可跟随联动筛选自动重算）。

    三种用法
    --------
    >>> eazy_data_viz.kpi(1630000, label="全年销售额", delta=0.128)          # 直接给数值
    >>> eazy_data_viz.kpi(df, value="销售额", label="全年销售额", delta=0.128)  # 从 df 聚合
    >>> eazy_data_viz.kpi(df, value="销售额", spark="销售额", spark_x="月份")   # 带迷你走势

    参数
    ----
    data : DataFrame | int | float
        数据；也可以直接传一个数值。
    value : str
        数值列（从 df 聚合时必填）。
    agg : str
        聚合方式，sum / mean / count / max / min / median。
    label : str
        指标名（显示在数值上方）。
    fmt : str
        数字格式：compact（默认，163万）/ thousands / raw / percent / currency（¥）。
    delta : float
        同比环比：0.128 显示 ▲12.8%；传 12.8 这类绝对值时按原样显示。
    delta_label : str
        涨跌幅口径说明，例如 "同比" / "环比" / "较上月"。
    inverse : bool
        True 表示「越小越好」（成本、投诉率），下降显示为绿色。
    target : float
        目标值，传入后卡片右上角显示达成率、底部显示进度条。
    target_label : str
        目标标签，默认 "目标"。
    spark : str
        迷你走势的数值列；配合 spark_x 使用。
    spark_x : str
        迷你走势的横轴（时间/有序分类列，如 "月份"、"日期"）。
    hint : str
        底部小字说明，例如 "2024 全年 · 含税"。
    unit : str
        数值后缀，例如 "%"、"人"、"单"。
    prefix : str
        数值前缀，例如 "≈"。
    accent : int
        强调色在配色库中的序号（0 起），用于左下角走势线 / 进度条颜色。
    link : str
        联动组名；同一组的图被点击过滤时，这个 KPI 会跟着重算。
    section : str
        看板分区标题（dashboard 里自动分组）。

    示例
    ----
    >>> eazy_data_viz.kpi(df, value="销售额", label="全年销售额", delta=0.128,
    ...          delta_label="同比", target=2000000, hint="2024 全年")
    >>> eazy_data_viz.dashboard(
    ...     eazy_data_viz.kpi(df, value="销售额", label="销售额", link="g1"),
    ...     eazy_data_viz.bar(df, x="大区", y="销售额", link="g1"),
    ...     cols=2)
    """
    if fmt is not None:
        _check_fmt(fmt)
    if theme not in ("light", "dark"):
        raise ValueError('theme 只支持 "light" / "dark"，收到 %r' % (theme,))
    if height is not None and (not isinstance(height, (int, float)) or height < 120):
        raise ValueError("height 至少 120（像素），收到 %r" % (height,))
    if target is not None and not isinstance(target, (int, float)):
        raise ValueError("target 需要是数字（目标值），收到 %r" % (target,))
    if spark is not None and spark_x is None:
        raise ValueError(
            '带迷你走势的 KPI 需要 spark_x（横轴列），例如 '
            'kpi(df, value="销售额", spark="销售额", spark_x="月份")。'
        )
    if accent is not None and (not isinstance(accent, int) or isinstance(accent, bool) or accent < 0):
        raise ValueError("accent 需要是 >=0 的整数（配色序号），收到 %r" % (accent,))

    static_value = None
    records = {"cols": [], "rows": [], "n": 0, "kinds": {}}
    ref = None
    warnings = []

    if isinstance(data, (int, float)) and not isinstance(data, bool) and value is None:
        static_value = float(data)
        if label is None:
            label = title
    else:
        if data is None:
            raise ValueError(
                'kpi 需要数据：kpi(df, value="销售额") 或 kpi(1630000, label="销售额")。'
            )
        _check_agg(agg)
        df = _frame.ensure_frame(data)
        if value is None:
            nums = [c for c in df.columns if _frame.column_kind(df[c]) == _frame.KIND_NUM]
            if len(nums) != 1:
                raise ValueError('kpi 需要指定 value 列，例如 kpi(df, value="销售额")。')
            value = nums[0]
        _frame.require_column(df, value, "value")
        if spark is not None:
            _frame.require_column(df, spark, "spark")
            _frame.require_column(df, spark_x, "spark_x")

        roles = {"value": value}
        if spark is not None:
            roles["spark_x"] = spark_x
            roles["spark_y"] = spark
        numeric = [value] + ([spark] if spark is not None else [])
        dims = [spark_x] if spark is not None else []
        records, ref, info = _frame.prepare(
            df, roles, numeric_roles=numeric, dimension_roles=dims,
        )
        if info.get("truncated"):
            warnings.append(
                "数据 %d 行，超过 max_rows=%d，已均匀采样 %d 行用于绘图。"
                % (info["n_total"], _frame.MAX_ROWS, records["n"])
            )

    spec = {
        "id": _next_id(),
        "type": "kpi",
        "title": title,
        "subtitle": subtitle,
        "theme": theme,
        "height": int(height or 150),
        "dataRef": ref,
        "roles": {"value": value} if value is not None else {},
        "agg": agg,
        "fmt": fmt or "compact",
        "sort": None,
        "topN": None,
        "xtitle": None,
        "ytitle": None,
        "xlim": None,
        "ylim": None,
        "legend": False,
        "labels": False,
        "zoom": False,
        "drill": None,
        "link": link,
        "value": static_value,
        "label": label,
        "delta": delta,
        "deltaLabel": delta_label,
        "inverse": bool(inverse),
        "target": target,
        "targetLabel": target_label,
        "spark": {"x": spark_x, "y": spark, "agg": agg} if spark is not None else None,
        "hint": hint,
        "unit": unit,
        "prefix": prefix,
        "accent": int(accent or 0),
        "section": section,
    }
    return Chart(spec, records, ref, {"warnings": warnings})


def combo(
    data,
    x,
    bar=None,
    line=None,
    *,
    agg="sum",
    title=None,
    subtitle=None,
    xtitle=None,
    ytitle=None,
    fmt="compact",
    height=400,
    theme="light",
    zoom="auto",
    max_rows=_frame.MAX_ROWS,
):
    """柱线混合图（一根柱子 + 一条折线，双坐标轴）。

    ``zoom="auto"`` 在类目很多时自动开启缩放；``zoom=True`` 强制开启。
    """
    if bar is None or line is None:
        raise ValueError("combo 需要同时指定 bar=\"数值列\" 和 line=\"数值列\"。")
    roles = {"x": x, "y": bar, "y2": line}
    spec, records, ref, info = _base_spec(
        "combo",
        data,
        roles,
        title=title if title is not None else "%s / %s 按 %s" % (bar, line, x),
        subtitle=subtitle,
        xtitle=xtitle,
        ytitle=ytitle,
        xlim=None,
        ylim=None,
        fmt=fmt,
        height=height,
        theme=theme,
        agg=agg,
        sort=None,
        top_n=None,
        legend=True,
        labels=False,
        zoom=zoom,
        drill=None,
        link=None,
        max_rows=max_rows,
    )
    _ensure_numeric(records, bar, "bar")
    _ensure_numeric(records, line, "line")
    return Chart(spec, records, ref, info)


# --------------------------------------------------------------------------
# 小工具
# --------------------------------------------------------------------------
def _ensure_numeric(records, col, role):
    """确认某列在记录里是数值型（否则给中文提示）。"""
    kind = (records.get("kinds") or {}).get(str(col))
    if kind not in (None, _frame.KIND_NUM):
        sample = None
        for row in records["rows"][:5]:
            try:
                sample = row[records["cols"].index(str(col))]
            except (ValueError, IndexError):
                break
        raise TypeError(
            "%s 列 %r 需要是数值类型（当前为 %s，示例值 %r）。"
            "请先用 pd.to_numeric() 转换，或换一列。"
            % (role, col, "文本" if kind == _frame.KIND_CAT else kind, sample)
        )
