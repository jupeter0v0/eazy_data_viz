# -*- coding: utf-8 -*-
"""一致性修补：参数校验、height 默认值、雷达图缺 y、KPI 组 delta 语义。"""
import io
import os
import sys

ROOT = r"F:\deepseek\eazy_data_viz"
OK = 0


def rep(path, old, new, count=1):
    global OK
    full = os.path.join(ROOT, path)
    s = io.open(full, encoding="utf-8").read()
    n = s.count(old)
    if n == 0:
        if new in s:
            print("skip %s (already applied)" % path)
            return
        print("FAIL %s: found 0\n---\n%s\n---" % (path, old[:200]))
        sys.exit(1)
    if n != count:
        print("FAIL %s: found %d (expect %d)\n---\n%s\n---" % (path, n, count, old[:200]))
        sys.exit(1)
    s = s.replace(old, new, count)
    io.open(full, "w", encoding="utf-8", newline="\n").write(s)
    OK += 1
    print("ok   %s" % path)


# ---------------------------------------------------------------- A. height 默认值
rep(
    "eazy_data_viz/chart.py",
    'def _base_spec(\n',
    '''# 各图表在「用户显式传 height=None」时使用的默认高度（与函数签名里的默认值保持一致）。
_HEIGHT_DEFAULTS = {
    "bar": 380, "line": 380, "area": 360, "pie": 360, "scatter": 400,
    "histogram": 380, "heatmap": 380, "box": 380, "funnel": 380,
    "treemap": 420, "gauge": 260, "combo": 400, "pareto": 400,
    "bump": 420, "waterfall": 400, "sankey": 420, "graph": 420,
}


def _base_spec(
''',
)

rep(
    "eazy_data_viz/chart.py",
    '        "height": int(height or 380),',
    '        "height": int(height if height is not None else _HEIGHT_DEFAULTS.get(kind, 380)),',
)

# ---------------------------------------------------------------- B. max_rows 校验
rep(
    "eazy_data_viz/frame.py",
    "def prepare(df, roles, max_rows=MAX_ROWS, max_cols=MAX_COLS,\n",
    '''def prepare(df, roles, max_rows=MAX_ROWS, max_cols=MAX_COLS,
    if max_rows is not None:
        if isinstance(max_rows, bool) or not isinstance(max_rows, numbers.Integral):
            raise TypeError(
                "max_rows 需要是正整数（如 50000），或 None 表示不采样；收到 %r。" % (max_rows,))
        if max_rows < 1:
            raise ValueError("max_rows 需要 >= 1，或传 None 表示不采样；收到 %r。" % (max_rows,))
        max_rows = int(max_rows)''',
)

# ---------------------------------------------------------------- C. charts_extra 参数校验
rep(
    "eazy_data_viz/charts_extra.py",
    'def _num_or_none(value):',
    '''def _num_param(value, name):
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


def _num_or_none(value):''',
)

rep(
    "eazy_data_viz/charts_extra.py",
    'targetValue=(_num_or_none(target_value) if target_value is not None else None),',
    'targetValue=_num_param(target_value, "target_value"),',
    count=2,
)

# pareto 的 cum_fmt 报错文案
rep(
    "eazy_data_viz/charts_extra.py",
    "    _check_fmt(cum_fmt)",
    '''    try:
        _check_fmt(cum_fmt)
    except ValueError:
        raise ValueError("cum_fmt 只支持 \\"percent\\" / \\"raw\\" / \\"compact\\"，收到 %r。" % (cum_fmt,))''',
)

# ---------------------------------------------------------------- D. group_kpi delta 语义（小数 -> 百分比）
rep(
    "eazy_data_viz/assets/eazy_extra_html.js",
    "          Math.abs(delta).toFixed(1) + '%</div>') +",
    "          Math.abs(delta * 100).toFixed(1) + '%</div>') +",
)

# ---------------------------------------------------------------- E. radar 缺 y 时按记录数
rep(
    "eazy_data_viz/assets/eazy_extra_a.js",
    """    var ycol = roles.y, cdim = roles.color;
    if (!xdim || !ycol || !rows.length) return U.emptyOption(theme);

    var how = spec.agg || 'mean';
    var groups = U.groupBy(rows, cdim && U.hasCol(data, cdim) ? [xdim, cdim] : [xdim], ycol, how);""",
    """    var ycol = roles.y, cdim = roles.color;
    var countMode = !ycol;
    if (!xdim || !rows.length) return U.emptyOption(theme);

    var mcol = countMode ? xdim : ycol;
    var how = countMode ? 'count' : (spec.agg || 'mean');
    var groups = U.groupBy(rows, cdim && U.hasCol(data, cdim) ? [xdim, cdim] : [xdim], mcol, how);""",
)

rep(
    "eazy_data_viz/assets/eazy_extra_a.js",
    "      var ser = cdim && U.hasCol(data, cdim) ? g.keys[1] : (ycol || '数值');",
    "      var ser = cdim && U.hasCol(data, cdim) ? g.keys[1] : (countMode ? '记录数' : ycol);",
)

print("\npatch ok, %d edits" % OK)
