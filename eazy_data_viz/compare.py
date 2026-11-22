"""同比 / 环比（1.6）：KPI 卡片的动态对比引擎。

``kpi(..., compare={"年": ["2026年", "2025年"], "show": "rate"})`` 会让卡片
**自己从数据里算**本期值、上期值和增长率，而不是让用户先把两年数据筛好再手动
传 ``delta``。联动过滤之后两个值会一起重算，所以「联动后同比还准」是默认行为。

设计要点
--------
* 只吃「一列 + 两个取值」：``{"年": ["2026年", "2025年"]}``，第一个是本期，
  第二个是上期（基期）；
* ``show`` 决定显示什么：``"value"`` 双数值、``"rate"`` 同比率、``"both"`` 两者；
* ``mode`` 决定默认口径：``"yoy"`` 同比（对比两个取值）、``"mom"`` 环比
  （本期最后一期 vs 上一期，需要 period 列，默认取 ``spark_x``）；
* 有 period 列时，**基期只取本期已有的那些期**，做同期对齐（2026 只有 1–8 月，
  就只比 2025 的 1–8 月），避免「半年对全年」；
* 基期为 0 / 空 / 负数都有明确显示规则，见 :func:`rate_of`。
"""

from __future__ import annotations

import re

_SHOW_ALIASES = {
    "value": "value",
    "数值": "value",
    "双值": "value",
    "双数值": "value",
    "rate": "rate",
    "ratio": "rate",
    "比率": "rate",
    "增速": "rate",
    "同比率": "rate",
    "both": "both",
    "all": "both",
    "全部": "both",
    "同时": "both",
    "都显示": "both",
}

_MODE_ALIASES = {
    "yoy": "yoy",
    "同比": "yoy",
    "年同比": "yoy",
    "on-year": "yoy",
    "mom": "mom",
    "环比": "mom",
    "月环比": "mom",
    "previous": "mom",
}

RESERVED_KEYS = ("show", "mode", "period", "base_label", "label")

_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _norm_choice(value, aliases, what, allowed):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(
            "compare 的 %s 需要是字符串，可选：%s，收到 %r。" % (what, allowed, value)
        )
    key = aliases.get(value.strip().lower())
    if key is None:
        key = aliases.get(value.strip())
    if key is None:
        raise ValueError(
            "compare 的 %s 只支持 %s，收到 %r。" % (what, allowed, value)
        )
    return key


def rate_of(cur, base):
    """增长率（小数）：``(cur - base) / |base|``。

    规则（Python / 浏览器两侧保持一致）：

    ===============  ============================================
    情况             返回
    ===============  ============================================
    ``cur`` 为空      ``None``（显示 ``—``）
    ``base`` 为空     ``None``（本期有值、基期无值 → 显示「新增」）
    ``base == 0``     ``None``（从 0 到正数 → 「新增」；仍为 0 → ``—``）
    ``base < 0``      正常算，但分母取绝对值（避免「负负得正」把方向搞反）
    其它              ``(cur - base) / |base|``
    ===============  ============================================
    """
    if cur is None or base is None:
        return None
    cur = float(cur)
    base = float(base)
    if base == 0:
        return None
    return (cur - base) / abs(base)


def _agg_value(series, agg):
    """按 agg 聚合一个 Series；空值 / 全空返回 None。"""
    if series is None or len(series) == 0:
        return None
    if agg == "count":
        n = int(series.notna().sum())
        return float(n)
    if agg == "unique":
        seen = set()
        for value in series.tolist():
            if value is None:
                continue
            try:
                if value != value:  # NaN
                    continue
            except Exception:  # pragma: no cover - 防御
                pass
            text = str(value)
            if text != "" and text.lower() != "nan":
                seen.add(text)
        return float(len(seen))
    nums = __import__("pandas").to_numeric(series, errors="coerce").dropna()
    if len(nums) == 0:
        return None
    if agg == "sum":
        return float(nums.sum())
    if agg == "mean":
        return float(nums.mean())
    if agg == "median":
        return float(nums.median())
    if agg == "max":
        return float(nums.max())
    if agg == "min":
        return float(nums.min())
    return float(nums.sum())


def _period_key(value):
    """自然排序键：先按名字里第一个数字，再按原始字符串。"""
    text = "" if value is None else str(value)
    match = _NUM_RE.search(text)
    if match:
        try:
            return (0, float(match.group(0)), text)
        except ValueError:  # pragma: no cover - 正则已保证
            pass
    return (1, 0.0, text)


def _mom(cur_rows, period, value, agg):
    """环比：把本期行按 period 分期，取最后一期 vs 上一期。"""
    if period is None or period not in cur_rows.columns or len(cur_rows) == 0:
        return None
    buckets = {}
    order = []
    labels = cur_rows[period].tolist()
    for i, label in enumerate(labels):
        key = "" if label is None else str(label)
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(i)
    if len(order) < 2:
        return None
    order.sort(key=_period_key)
    last, prev = order[-1], order[-2]
    cur_slice = cur_rows.iloc[buckets[last]]
    prev_slice = cur_rows.iloc[buckets[prev]]
    cur_val = _agg_value(cur_slice[value], agg) if value else None
    prev_val = _agg_value(prev_slice[value], agg) if value else None
    return {
        "cur": cur_val,
        "base": prev_val,
        "rate": rate_of(cur_val, prev_val),
        "label": last,
        "baseLabel": prev,
    }


def parse_compare(df, compare, *, spark_x=None, value=None, agg="sum"):
    """校验并归一化 ``compare`` 参数，返回写进 spec 的字典（或 None）。

    ``df`` 是已经过的 DataFrame（用于校验列和取值是否存在）。
    """
    if compare is None:
        return None
    if not isinstance(compare, dict):
        raise ValueError(
            'compare 需要是字典，例如 compare={"年": ["2026年", "2025年"], "show": "rate"}，'
            "收到 %r。" % (compare,)
        )

    data_keys = [k for k in compare.keys() if k not in RESERVED_KEYS]
    if not data_keys:
        raise ValueError(
            'compare 需要给出「对比列 + 两个取值」，例如 compare={"年": ["2026年", "2025年"]}。'
        )
    if len(data_keys) > 1:
        raise ValueError(
            "compare 只能对比一列（一个列名 + 两个取值），收到多列：%s。"
            % "、".join(map(str, data_keys))
        )
    dim = data_keys[0]
    pair = compare.get(dim)
    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
        raise ValueError(
            "compare[%r] 需要是 [本期值, 上期值] 两个取值，收到 %r。" % (dim, pair)
        )
    cur, base = pair[0], pair[1]
    if str(cur) == str(base):
        raise ValueError(
            "compare[%r] 的两个取值不能相同（都是 %r）。" % (dim, cur)
        )

    columns = [str(c) for c in df.columns]
    if str(dim) not in columns:
        raise ValueError(
            "compare 的对比列 %r 不在数据里（现有列：%s）。" % (str(dim), "、".join(columns))
        )
    present = []
    for v in df[dim].dropna().tolist():
        text = str(v)
        if text not in present:
            present.append(text)
    for label, v in (("本期", cur), ("上期", base)):
        if str(v) not in present:
            raise ValueError(
                "compare[%r] 的%s取值 %r 在数据里不存在，现有取值：%s。"
                "如果你已经把数据筛到本期，请改传未筛选的完整数据——compare 会自己切本期/基期。"
                % (str(dim), label, str(v), "、".join(present[:12]) or "（无）")
            )

    show = _norm_choice(compare.get("show"), _SHOW_ALIASES, "show",
                        '"value"（数值）/ "rate"（同比率）/ "both"（两者）') or "both"
    mode = _norm_choice(compare.get("mode"), _MODE_ALIASES, "mode",
                        '"yoy"（同比）/ "mom"（环比）') or "yoy"

    period = compare.get("period", spark_x)
    if period is not None and str(period) not in columns:
        raise ValueError(
            "compare 的 period=%r 不在数据里（现有列：%s）。" % (period, "、".join(columns))
        )

    cfg = {
        "dim": str(dim),
        "cur": str(cur),
        "base": str(base),
        "show": show,
        "mode": mode,
        "period": str(period) if period is not None else None,
        "baseLabel": str(compare.get("base_label") or base),
        "label": str(compare.get("label") or ""),
    }

    # 静态快照：Python 侧先算一遍，便于测试 / 无 JS 环境兜底。
    cfg["static"] = static_values(df, cfg, value=value, agg=agg)
    return cfg


def static_values(df, cfg, *, value=None, agg="sum"):
    """按 compare 配置用 pandas 算一遍：本期、上期、增长率、环比。"""
    if df is None or value is None or str(value) not in [str(c) for c in df.columns]:
        return {"cur": None, "base": None, "rate": None, "mom": None}
    dim_series = df[str(cfg["dim"])].astype(str)
    cur_rows = df[dim_series == str(cfg["cur"])]
    base_rows = df[dim_series == str(cfg["base"])]
    period = cfg.get("period")
    if period and str(period) in [str(c) for c in df.columns]:
        cur_periods = set(cur_rows[str(period)].astype(str).tolist())
        base_rows = base_rows[base_rows[str(period)].astype(str).isin(cur_periods)]
    cur_val = _agg_value(cur_rows[value], agg) if len(cur_rows) else None
    base_val = _agg_value(base_rows[value], agg) if len(base_rows) else None
    return {
        "cur": cur_val,
        "base": base_val,
        "rate": rate_of(cur_val, base_val),
        "mom": _mom(cur_rows, period, value, agg),
    }
