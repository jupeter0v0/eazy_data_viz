"""指标跟随与列聚合约定（1.6.1）。

两块能力：

1. ``edv.column(...)`` —— 一次性声明每列怎么汇总，图表不用再逐张写 ``agg=``：

   >>> import eazy_data_viz as edv
   >>> edv.column(金额="sum", 数量="sum", 客户名称="unique", 订单数="count",
   ...            订单均价="金额/订单数")

   之后 ``edv.bar(df, x="月", y="客户名称")`` 自动按 ``unique`` 去重计数；
   没登记的列仍然按 ``sum``（也就是旧行为）。

2. ``edv.follow()`` —— 图表的度量跟着「当前选中的 KPI 卡片」走：

   >>> edv.show(
   ...     edv.kpi(df, value="金额", metric="sale", label="销售额"),
   ...     edv.kpi(df, value="客户名称", metric="cust", label="客户数"),
   ...     edv.bar(df, x="月", y=edv.follow()),
   ... )

   点「销售额」卡片 = 选中 ``sale``，柱状图的 ``y`` 自动变成 ``金额``、聚合
   自动变成它登记的 ``sum``；点「客户数」卡片，同一根柱子换成去重计数。
   选中的卡片只是**选择器**，不改变它自己的数值。

运行期（浏览器）只改 ``spec.roles`` 与 ``spec.agg`` 后重绘，不触发 Python 重算。
"""

from __future__ import annotations

import re

# 与 chart.AGGS 保持一致（这里单独列一份，避免 metric ← chart 循环导入）
_AGGS = ("sum", "mean", "count", "unique", "max", "min", "median")

# 只能接 follow() 的角色（度量角色）；维度角色接了会报错
_MEASURE_ROLES = ("y", "y2", "value", "values", "names", "size", "spark", "spark_y")

# 列登记表：列名 -> {"agg": str | None, "expr": str | None}
_COLUMNS: "dict[str, dict]" = {}

# 表达式里允许出现的字符（+ - * / 和列名里的中英文数字下划线）
_EXPR_RE = re.compile(r"[+\-*/]")


class Follow:
    """``edv.follow()`` 的返回值：占位符，表示「用当前选中的指标列」。"""

    def __init__(self, default: str | None = None):
        self.default = default

    def __repr__(self) -> str:  # pragma: no cover - 只影响交互式显示
        if self.default is None:
            return "follow()"
        return "follow(default=%r)" % (self.default,)


def follow(default: str | None = None) -> Follow:
    """声明「这个度量跟着选中的 KPI 卡片走」。

    参数
    ----
    default
        还没有任何卡片被选中时使用的列名。不传时用页面里第一张带
        ``metric=`` 的 KPI 卡片的列。

    返回
    ----
    Follow
        占位符，可传给 ``y`` / ``y2`` / ``value`` / ``values`` / ``names`` /
        ``size`` / ``spark``。

    报错
    ----
    ``ValueError: follow 的 default 需要是列名字符串，收到 5。``
    ``ValueError: follow() 只能用在度量角色（y / value / names / size / spark），
    不能给 x / path / columns 这类维度用。``
    """
    if default is not None:
        if not isinstance(default, str):
            raise ValueError(
                "follow 的 default 需要是列名字符串，收到 %r。" % (default,))
        if default.strip() == "":
            raise ValueError("follow 的 default 不能是空字符串。")
        default = default.strip()
    return Follow(default)


def is_follow(value) -> bool:
    """``value`` 是不是 ``edv.follow(...)`` 的返回值。"""
    return isinstance(value, Follow)


# --------------------------------------------------------------- 列聚合约定

def column(**specs) -> dict:
    """声明每列的汇总方式（全局生效，之后建的图都按它来）。

    参数
    ----
    **specs
        ``列名=聚合方式`` 或 ``列名=表达式``：

        * 聚合方式：``sum`` / ``mean`` / ``count`` / ``unique`` / ``max`` /
          ``min`` / ``median``；
        * 表达式：用其它列算出新列，例如 ``订单均价="金额/订单数"``
          （支持 ``+ - * /``）；算出来的列默认按 ``mean`` 汇总（除法）或
          ``sum`` 汇总（加减乘）。

    返回
    ----
    dict
        列名 → ``{"agg": …, "expr": …}`` 的副本，方便自查。

    报错
    ----
    ``ValueError: edv.column 至少需要一列，例如 edv.column(金额="sum")。``
    ``ValueError: edv.column['金额'] 的聚合方式 'avg' 不支持，可选：sum、mean、count、unique、max、min、median。``
    ``ValueError: edv.column['订单均价'] 的表达式里的列 '单价' 不在数据里，也不在别处登记过。``（建图时才校验）
    ``ValueError: edv.column 的列名不能是空字符串。``
    """
    if not specs:
        raise ValueError(
            'edv.column 至少需要一列，例如 edv.column(金额="sum", 客户名称="unique")。')

    for name, rule in specs.items():
        if not isinstance(name, str) or name.strip() == "":
            raise ValueError("edv.column 的列名不能是空字符串。")
        name = name.strip()
        if isinstance(rule, (list, tuple)):
            # 支持 ("金额/订单数", "mean") 这种「表达式 + 聚合」写法
            if len(rule) == 2:
                rule, agg = rule
            else:
                raise ValueError(
                    "edv.column[%r] 的取值只能是聚合方式、表达式，或 (表达式, 聚合方式)。"
                    % (name,))
            if not isinstance(agg, str) or agg not in _AGGS:
                raise ValueError(
                    "edv.column[%r] 的聚合方式 %r 不支持，可选：%s。"
                    % (name, agg, "、".join(_AGGS)))
        elif not isinstance(rule, str):
            raise ValueError(
                "edv.column[%r] 需要是字符串（聚合方式或表达式），收到 %r。"
                % (name, rule))
        if not isinstance(rule, str):
            raise ValueError("edv.column[%r] 需要是字符串。" % (name,))
        rule = rule.strip()
        if rule == "":
            raise ValueError("edv.column[%r] 的取值不能是空字符串。" % (name,))

        if rule in _AGGS:
            _COLUMNS[name] = {"agg": rule, "expr": None}
            continue

        agg = None
        if isinstance(specs[name], (list, tuple)):
            agg = specs[name][1]
        if not _EXPR_RE.search(rule):
            # 既不是聚合名、也不含运算符 -> 多半是把聚合名写错了（例如 "avg"）
            raise ValueError(
                "edv.column[%r] 的聚合方式 %r 不支持，可选：%s；"
                "要写表达式请用 + - * / ，例如 订单均价=\"金额/订单数\"。"
                % (name, rule, "、".join(_AGGS)))
        if agg is None:
            agg = "mean" if "/" in rule else "sum"
        _COLUMNS[name] = {"agg": agg, "expr": rule}

    return column_table()


def column_table() -> dict:
    """当前登记表（副本）。"""
    return {k: dict(v) for k, v in _COLUMNS.items()}


def reset_columns() -> None:
    """清空登记表（测试用）。"""
    _COLUMNS.clear()


def column_spec(name: str) -> dict | None:
    """取某一列的登记信息，没登记返回 ``None``。"""
    if not isinstance(name, str):
        return None
    return _COLUMNS.get(name)


def is_formula(name: str) -> bool:
    """这一列是不是「用表达式算出来的」列。"""
    spec = column_spec(name)
    return bool(spec and spec.get("expr"))


def agg_for(name: str | None, agg: str | None = None) -> str | None:
    """求某列该用的聚合方式：显式传的优先，其次登记表，最后返回 ``None``。"""
    if agg:
        return agg
    spec = column_spec(name) if name else None
    if spec and spec.get("agg"):
        return spec["agg"]
    return None


_OP_SPLIT = re.compile(r"\s*([+\-*/])\s*")


def _expr_deps(expr: str) -> list:
    parts = [p for p in _OP_SPLIT.split(expr) if p and p not in "+-*/"]
    return [p.strip() for p in parts if p.strip()]


def _compute_expr(df, expr: str, known: set):
    deps = _expr_deps(expr)
    for dep in deps:
        if dep not in known:
            raise ValueError(
                "edv.column 的表达式 %r 里用到列 %r，但数据里没有这一列，"
                "也没有在 edv.column(...) 里登记过。" % (expr, dep))
    pieces = _OP_SPLIT.split(expr)
    out = None
    op = "+"
    for piece in pieces:
        piece = piece.strip()
        if piece in ("+", "-", "*", "/"):
            op = piece
            continue
        cur = df[piece]
        if out is None:
            out = cur.astype(float)
            continue
        if op == "+":
            out = out + cur.astype(float)
        elif op == "-":
            out = out - cur.astype(float)
        elif op == "*":
            out = out * cur.astype(float)
        else:
            den = cur.astype(float)
            out = out / den.where(den != 0)
    if out is None:
        raise ValueError("edv.column 的表达式 %r 解析失败。" % (expr,))
    # 除以 0 会得到 inf，统一成缺失值，前端按空处理
    try:
        out = out.replace([float("inf"), float("-inf")], None)
    except Exception:
        pass
    return out


def materialize(df, names):
    """按登记表把表达式列算出来（只算被用到的那些）。

    返回 ``(df, added)``；``added`` 是本次新增的列名列表。
    没有表达式列时原样返回，不复制 DataFrame。
    """
    if not names:
        return df, []
    added = []
    known = set(map(str, df.columns))
    for name in names:
        if name in known or not is_formula(name):
            continue
        spec = column_spec(name) or {}
        series = _compute_expr(df, spec["expr"], known)
        df = df.copy()
        df[name] = series
        known.add(name)
        added.append(name)
    return df, added


# ------------------------------------------------------------------ 角色解析

def measure_of(roles: dict) -> str | None:
    """从角色字典里取「度量列」（用于查登记的聚合方式）。"""
    for rk in ("y", "value", "y2", "values", "spark", "spark_y", "size"):
        col = roles.get(rk)
        if isinstance(col, str) and col:
            return col
    return None


def resolve_roles(roles: dict):
    """把 ``follow()`` 从角色字典里摘出来。

    返回 ``(plain_roles, follow_map)``：

    * ``plain_roles``：``follow()`` 的角色置成 ``None``（Python 侧先用默认列，
      真正用哪列由浏览器按当前选中卡片决定）；
    * ``follow_map``：``{角色: {"default": 列名或 None}}``，写进 ``spec["follow"]``。
    """
    plain = dict(roles or {})
    follow_map = {}
    for role, val in list(plain.items()):
        if not is_follow(val):
            continue
        if role not in _MEASURE_ROLES:
            raise ValueError(
                "follow() 只能用在度量角色（y / y2 / value / values / names / size / spark），"
                "不能给 %r 这类维度用。" % (role,))
        follow_map[role] = {"default": val.default}
        plain[role] = None
    return plain, follow_map


def follow_columns(follow_map: dict, fallback: str | None = None) -> list:
    """``follow`` 里可能需要用到的列（默认列 + 兜底列）。"""
    out = []
    for info in (follow_map or {}).values():
        col = (info or {}).get("default") or fallback
        if col and col not in out:
            out.append(col)
    return out
