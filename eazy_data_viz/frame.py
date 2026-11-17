"""数据准备层：把 pandas DataFrame 压成一份紧凑、可 JSON 序列化的记录集。

设计原则
--------
1. 用户只传 DataFrame + 列名，库内部负责类型识别、聚合、序列化；
2. 只嵌入图表真正可能需要用到的列（角色列 + 其余列，最多 ``MAX_COLS`` 列），
   这样"同名列"天然成为跨图联动的维度；
3. 所有 NaN / NaT / pd.NA 统一变成 ``None``，保证前端 JSON.parse 不会崩。
"""
from __future__ import annotations

import hashlib
import json
import numbers

import numpy as np
import pandas as pd

# 单图最多嵌入多少行 / 列（防止 1M 行直接把 HTML 撑爆）
# 单图默认最多嵌入的数据行数。经营看板常见明细表在 5 万~20 万行量级，
# 默认给到 20 万行（200000），超过才均匀采样；传 max_rows=None 可完全关闭采样。
MAX_ROWS = 200000
MAX_COLS = 40

# 列的语义分类
KIND_NUM = "num"
KIND_TIME = "time"
KIND_CAT = "cat"
KIND_BOOL = "bool"


# --------------------------------------------------------------------------
# 输入归一化
# --------------------------------------------------------------------------
def ensure_frame(data):
    """把用户传来的 data 统一成 DataFrame。"""
    if isinstance(data, pd.DataFrame):
        return data
    if isinstance(data, pd.Series):
        return data.to_frame()
    if isinstance(data, dict):
        return pd.DataFrame(data)
    if isinstance(data, (list, tuple)):
        return pd.DataFrame(data)
    if data is None:
        raise ValueError("data 不能为空，请传入 pandas.DataFrame（或 dict / list）。")
    raise TypeError(
        "无法识别 data 类型 %r，请传入 pandas.DataFrame（或 dict / list）。" % type(data).__name__
    )


def require_column(df, name, role, hint=""):
    """校验列存在，不存在时给出中文可读错误。"""
    if name is None:
        return None
    if name not in df.columns:
        cols = ", ".join(str(c) for c in list(df.columns)[:20])
        more = "" if len(df.columns) <= 20 else " ..."
        raise KeyError(
            "%s列 %r 不存在。当前可用的列有：%s%s%s"
            % (role, name, cols, more, ("\n提示：" + hint) if hint else "")
        )
    return name


def column_kind(series):
    """返回列的语义类型：num / time / cat / bool。"""
    if pd.api.types.is_bool_dtype(series):
        return KIND_BOOL
    if pd.api.types.is_datetime64_any_dtype(series):
        return KIND_TIME
    if pd.api.types.is_numeric_dtype(series):
        return KIND_NUM
    return KIND_CAT


def _looks_numeric(series):
    """object 列里是否几乎全是数字（例如 '1,234' 这种脏数据不做猜测）。"""
    vals = series.dropna()
    if vals.empty:
        return False
    try:
        converted = pd.to_numeric(vals, errors="coerce")
    except (TypeError, ValueError):
        return False
    return converted.notna().mean() >= 0.99


def _truncate_text(v, limit=120):
    s = str(v)
    return s if len(s) <= limit else s[: limit - 1] + "…"


# --------------------------------------------------------------------------
# 单列转换
# --------------------------------------------------------------------------
def convert_series(series, force_numeric=False):
    """把一列转换成可安全 JSON 化的 pandas Series。"""
    kind = column_kind(series)

    if force_numeric and kind not in (KIND_NUM, KIND_TIME, KIND_BOOL):
        if _looks_numeric(series):
            series = pd.to_numeric(series, errors="coerce")
            kind = KIND_NUM
        else:
            bad = series.dropna().head(5).tolist()
            raise TypeError(
                "列 %r 需要是数值类型，但当前是文本类型（例如 %r）。"
                "请先用 pd.to_numeric() 清洗，或换一列。" % (series.name, bad)
            )

    if kind == KIND_NUM:
        # 可空整型 / 浮点统一成 object，NaN -> None
        out = series.astype(object)
        return out.where(pd.notna(series), None)

    if kind == KIND_TIME:
        dt = pd.to_datetime(series, errors="coerce")
        midnight = dt.dt.normalize() == dt
        fmt = "%Y-%m-%d" if bool(midnight.all()) else "%Y-%m-%d %H:%M"
        out = dt.dt.strftime(fmt).astype(object)
        return out.where(dt.notna(), None)

    if kind == KIND_BOOL:
        out = series.map(lambda v: None if pd.isna(v) else ("是" if bool(v) else "否"))
        return out.astype(object)

    # 类别 / 文本 / 时间间隔
    if pd.api.types.is_timedelta64_dtype(series):
        series = series.astype(str)
    out = series.map(lambda v: None if pd.isna(v) else _truncate_text(v)).astype(object)
    return out


# --------------------------------------------------------------------------
# 主入口
# --------------------------------------------------------------------------
def prepare(df, roles, max_rows=MAX_ROWS, max_cols=MAX_COLS,
            numeric_roles=None, dimension_roles=None):
    if max_rows is not None:
        if isinstance(max_rows, bool) or not isinstance(max_rows, numbers.Integral):
            raise TypeError(
                "max_rows 需要是正整数（如 50000），或 None 表示不采样；收到 %r。" % (max_rows,))
        if max_rows < 1:
            raise ValueError("max_rows 需要 >= 1，或传 None 表示不采样；收到 %r。" % (max_rows,))
        max_rows = int(max_rows)
    """把 DataFrame 压成 ``{"cols": [...], "rows": [[...]], ...}``。

    参数
    ----
    roles : dict
        角色名 -> 列名，例如 ``{"x": "月份", "y": "销售额", "color": "地区"}``。
        这决定了列的顺序（角色列排最前），也用于类型强制（y 必须是数值）。
    numeric_roles : 可迭代的列名, 可选
        必须按数值处理的列。图表函数会按图表类型传入
        （例如热力图的 y 是分类维度、饼图的 value 是数值）。
    dimension_roles : 可迭代的列名, 可选
        必须按维度（分类）处理的列，哪怕它本身是数字（例如年份 2023）。
    """
    df = ensure_frame(df)
    if len(df) == 0:
        raise ValueError("数据为空（0 行），无法绘图。")

    role_cols = []
    for k, v in roles.items():
        if v is None:
            continue
        if isinstance(v, (list, tuple)):
            role_cols.extend([c for c in v if c is not None])
        else:
            role_cols.append(v)
    # 去重并保持顺序
    seen, ordered_roles = set(), []
    for c in role_cols:
        if c not in seen:
            seen.add(c)
            ordered_roles.append(c)

    for c in ordered_roles:
        require_column(df, c, "")

    # 列顺序：始终按 DataFrame 原始列顺序，保证"同一份数据 + 多张图"能命中同一个
    # data_ref（多图共享同一份嵌入数据，页面体积不随图数增长）。列数超限时才让角色列优先。
    all_cols = list(df.columns)
    dropped = []
    if len(all_cols) > max_cols:
        keep = [c for c in all_cols if c in seen]
        rest = [c for c in all_cols if c not in seen]
        full = keep + rest
        dropped = [str(c) for c in full[max_cols:]]
        use_cols = full[:max_cols]
    else:
        use_cols = all_cols

    dim_set = set()
    if dimension_roles:
        for v in dimension_roles:
            if isinstance(v, (list, tuple)):
                dim_set.update([c for c in v if c is not None])
            elif v is not None:
                dim_set.add(v)
    else:
        dim_set = _role_dimension_set(roles)

    if numeric_roles is None:
        numeric_roles = {roles.get("y"), roles.get("y2"), roles.get("value"), roles.get("size")}
    numeric_roles = set(c for c in numeric_roles if c is not None) - dim_set

    out = pd.DataFrame(index=df.index)
    for c in use_cols:
        out[c] = convert_series(df[c], force_numeric=(c in numeric_roles))

    n_total = len(df)
    # max_rows=None 表示不采样（全部行嵌入）；否则超过上限时均匀采样。
    # 均匀采样比截断更能代表整体分布，同时保持行顺序。
    if max_rows is not None and n_total > max_rows:
        idx = np.linspace(0, n_total - 1, max_rows).astype(np.int64)
        out = out.iloc[idx]

    # 数值列四舍五入到 4 位小数：图表精度足够，同时显著减小嵌入 JSON 体积
    # （浮点原始 repr 常有 15+ 位有效数字，200k 行时能省下几 MB）。
    for c in use_cols:
        if c in numeric_roles or column_kind(df[c]) == KIND_NUM:
            try:
                out[c] = out[c].map(lambda v: round(v, 4) if isinstance(v, float) else v)
            except (TypeError, ValueError):
                pass

    out = out.astype(object).where(pd.notna(out), None)
    rows = out.values.tolist()

    kinds = {}
    measures, dims = [], []
    orders = {}
    for c in use_cols:
        k = column_kind(df[c])
        if c in numeric_roles:
            k = KIND_NUM
        kinds[str(c)] = k
        # 有序分类列（pd.Categorical(ordered=True)）的类目顺序交给前端排序用
        try:
            if isinstance(df[c].dtype, pd.CategoricalDtype) and df[c].cat.ordered:
                orders[str(c)] = [str(x) for x in df[c].cat.categories]
        except (AttributeError, TypeError):
            pass
        if k == KIND_NUM and c not in dim_set:
            measures.append(str(c))
        else:
            dims.append(str(c))

    data = {
        "cols": [str(c) for c in use_cols],
        "rows": rows,
        "dims": dims,
        "measures": measures,
        "kinds": kinds,
        "orders": orders,
        "n": int(len(out)),
        "n_total": int(n_total),
    }
    ref = data_ref(data)
    return data, ref, {
        "truncated": bool(max_rows is not None and n_total > max_rows),
        "n_total": n_total,
        "dropped_cols": dropped,
    }


def _role_dimension_set(roles):
    """被显式当作维度用的列（哪怕是数字，例如 2023 年）。"""
    s = set()
    for k in ("x", "color", "names", "path", "_extra"):
        v = roles.get(k)
        if isinstance(v, (list, tuple)):
            s.update([c for c in v if c is not None])
        elif v is not None:
            s.add(v)
    return s


def data_ref(data):
    """数据指纹，用于同一页面里多图共享同一份数据，避免重复传输。"""
    payload = json.dumps(
        {"cols": data["cols"], "rows": data["rows"], "orders": data.get("orders") or {}},
        ensure_ascii=False,
    )
    return "d" + hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


# --------------------------------------------------------------------------
# JSON 输出
# --------------------------------------------------------------------------
def to_json(obj):
    """安全的 JSON 序列化：兼容 numpy 标量，禁止 NaN/Infinity，转义 ``<``。"""
    text = json.dumps(obj, ensure_ascii=False, default=_json_default, allow_nan=False)
    # 防止提前闭合 <script>，同时不破坏 JSON 语义
    return text.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (pd.Timestamp,)):
        return o.strftime("%Y-%m-%d %H:%M:%S")
    if o is pd.NaT or o is pd.NA:
        return None
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError("无法序列化的类型: %r" % type(o))
