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
import os
import weakref
from collections import OrderedDict

import numpy as np
import pandas as pd

# 单图最多嵌入多少行 / 列（防止 1M 行直接把 HTML 撑爆）
# 单图默认最多嵌入的数据行数。经营看板常见明细表在 5 万~20 万行量级，
# 默认给到 20 万行（200000），超过才均匀采样；传 max_rows=None 可完全关闭采样。
MAX_ROWS = 2000000
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
def column_values(series, kind):
    """把一列转成可安全 JSON 的 Python 列表（向量化，比逐元素 map 快 2~4 倍）。"""
    if kind == KIND_NUM:
        arr = series.to_numpy()
        if arr.dtype.kind in ("i", "u"):
            return arr.tolist()
        vals = np.asarray(arr, dtype="float64")
        mask = np.isnan(vals)
        out = np.round(vals, 4).tolist()
        if mask.any():
            for i in np.flatnonzero(mask).tolist():
                out[i] = None
        return out

    if kind == KIND_TIME:
        dt = pd.to_datetime(series, errors="coerce")
        midnight = dt.dt.normalize() == dt
        fmt = "%Y-%m-%d" if bool(midnight.all()) else "%Y-%m-%d %H:%M"
        texts = dt.dt.strftime(fmt).to_numpy(dtype=object)
        out = texts.tolist()
        null = pd.isna(texts)
        if null.any():
            for i in np.flatnonzero(null).tolist():
                out[i] = None
        return out

    if kind == KIND_BOOL:
        filled = series.fillna(False).astype(bool).to_numpy()
        out = np.where(filled, "是", "否").tolist()
        null = pd.isna(series).to_numpy(dtype=bool)
        if null.any():
            for i in np.flatnonzero(null).tolist():
                out[i] = None
        return out

    # 类别 / 文本 / 时间间隔
    s = series
    if pd.api.types.is_timedelta64_dtype(s):
        s = s.astype(str)
    texts = s.astype(str)
    out = texts.tolist()
    if out:
        try:
            maxlen = int(texts.str.len().max())
        except (TypeError, ValueError):
            maxlen = 0
        if maxlen > 120:
            out = [_truncate_text(v) for v in out]
    null = pd.isna(s).to_numpy(dtype=bool)
    if null.any():
        for i in np.flatnonzero(null).tolist():
            out[i] = None
    return out


def convert_series(series, force_numeric=False):
    """把一列转换成可安全 JSON 化的 pandas Series（保留旧接口）。"""
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

    return pd.Series(column_values(series, kind), index=series.index, dtype=object)


# --------------------------------------------------------------------------
# 列缓存：同一份 DataFrame 会被多张图反复 prepare
# --------------------------------------------------------------------------
_PREP_CACHE = OrderedDict()
_PREP_CACHE_MAX_ENTRIES = 6
_PREP_CACHE_MAX_CELLS = 4000000
# 原地修改 DataFrame（同一个对象、改了中间几行）无法被自动发现：
# 关掉缓存或用 clear_cache() 即可，见 use_cache()。
_PREP_CACHE_ENABLED = os.environ.get("EAZY_NO_CACHE", "") not in ("1", "true", "yes")


def use_cache(enabled=True):
    """打开 / 关闭 prepare 的列缓存（默认打开）。返回当前状态。"""
    global _PREP_CACHE_ENABLED
    _PREP_CACHE_ENABLED = bool(enabled)
    if not enabled:
        _PREP_CACHE.clear()
    return _PREP_CACHE_ENABLED


def clear_cache():
    """清空 prepare 的列缓存（原地改了 DataFrame 但对象没换时可用）。"""
    _PREP_CACHE.clear()


def _fingerprint(df):
    """便宜的「内容指纹」：形状 + 首尾两行，用于发现原地修改。"""
    try:
        head = df.iloc[0].tolist()
    except (IndexError, TypeError):
        head = None
    try:
        tail = df.iloc[-1].tolist()
    except (IndexError, TypeError):
        tail = None
    return (len(df), tuple(map(str, df.columns)), repr(head)[:240], repr(tail)[:240])


def cache_info():
    """返回缓存条目数与占用单元格数（调试用）。"""
    cells = sum(int(e.get("n") or 0) * len(e.get("lists") or ()) for e in _PREP_CACHE.values())
    return {"entries": len(_PREP_CACHE), "cells": cells}


def _cache_get(key, df):
    entry = _PREP_CACHE.get(key)
    if entry is None:
        return None
    ref = entry.get("df")
    if ref is None or ref() is not df:
        _PREP_CACHE.pop(key, None)
        return None
    _PREP_CACHE.move_to_end(key)
    return entry


def _cache_put(key, df, entry):
    entry["df"] = weakref.ref(df)
    _PREP_CACHE[key] = entry
    _PREP_CACHE.move_to_end(key)
    while len(_PREP_CACHE) > _PREP_CACHE_MAX_ENTRIES:
        _PREP_CACHE.popitem(last=False)


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
        必须按数值处理的列。
    dimension_roles : 可迭代的列名, 可选
        必须按维度（分类）处理的列。
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
    seen, ordered_roles = set(), []
    for c in role_cols:
        if c not in seen:
            seen.add(c)
            ordered_roles.append(c)

    for c in ordered_roles:
        require_column(df, c, "")

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

    n_total = len(df)
    idx = None
    if max_rows is not None and n_total > max_rows:
        idx = np.linspace(0, n_total - 1, max_rows).astype(np.int64)

    key = (id(df), n_total, max_rows, tuple(use_cols))
    entry = _cache_get(key, df) if _PREP_CACHE_ENABLED else None
    stamp = _fingerprint(df) if entry is not None else None
    if entry is not None and entry.get("stamp") != stamp:
        _PREP_CACHE.pop(key, None)
        entry = None
    if entry is None:
        view = df if idx is None else df.iloc[idx]
        lists, kinds_raw, orders = [], {}, {}
        for c in use_cols:
            k = column_kind(view[c])
            kinds_raw[c] = k
            lists.append(column_values(view[c], k))
            try:
                if isinstance(view[c].dtype, pd.CategoricalDtype) and view[c].cat.ordered:
                    orders[str(c)] = [str(x) for x in view[c].cat.categories]
            except (AttributeError, TypeError):
                pass
        entry = {"lists": lists, "kinds": kinds_raw, "orders": orders,
                 "n": len(view), "rows": None, "ref": None,
                 "stamp": _fingerprint(df)}
        if _PREP_CACHE_ENABLED and len(view) * len(use_cols) <= _PREP_CACHE_MAX_CELLS:
            _cache_put(key, df, entry)

    lists = entry["lists"]
    kinds_raw = entry["kinds"]
    orders = entry["orders"]
    n = entry["n"]

    # 被强制成数值的文本列：只重算这一列，且不复用缓存的 rows（避免污染）
    forced = False
    for pos, c in enumerate(use_cols):
        if c in numeric_roles and kinds_raw.get(c) not in (KIND_NUM, KIND_TIME, KIND_BOOL):
            view = df if idx is None else df.iloc[idx]
            lists = list(entry["lists"])
            lists[pos] = convert_series(view[c], force_numeric=True).tolist()
            forced = True

    if forced:
        rows = [list(t) for t in zip(*lists)]
    else:
        rows = entry.get("rows")
        if rows is None:
            rows = [list(t) for t in zip(*lists)]
            entry["rows"] = rows

    kinds = {}
    measures, dims = [], []
    for c in use_cols:
        k = kinds_raw[c]
        if c in numeric_roles:
            k = KIND_NUM
        kinds[str(c)] = k
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
        "n": int(n),
        "n_total": int(n_total),
    }
    if forced:
        ref = data_ref(data)
    else:
        ref = entry.get("ref")
        if ref is None:
            ref = data_ref(data)
            entry["ref"] = ref
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
