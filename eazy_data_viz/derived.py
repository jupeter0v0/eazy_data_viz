# -*- coding: utf-8 -*-
"""派生指标（由其它指标算出来的 KPI，1.7.0）。

``kpi(df, metrics=..., expr=...)`` 里的公式在这一层编译成逆波兰式（RPN），
再原样写进 ``spec["kpi"]``；浏览器在联动筛选后的行集上按同一个 RPN 重算，
所以 Python 预渲染与前端联动后的数值、口径完全一致。

为什么用 RPN 而不是 ``eval`` / ``new Function``：

* 前端不需要把公式当代码执行，页面加 CSP 也不会失效；
* Python 侧就能把括号不配对、``a / / b`` 这类公式错误报成人话；
* 求值只有「取指标值、四则运算」两种操作，除零、空值可以统一处理。
"""

from __future__ import annotations

from collections import OrderedDict

from . import frame as _frame
from .metric import _AGGS as AGGS

#: 需要一个数值列的聚合；count / unique 对列类型没要求。
NUMERIC_AGGS = tuple(a for a in AGGS if a not in ("count", "unique"))

_OPS = "+-*/()"
_PREC = {"+": 1, "-": 1, "*": 2, "/": 2}


def tokenize(expr, names):
    """把公式切成 ``("ref", 指标名)`` / ``("num", 数字)`` / ``("op", 符号)``。

    指标名按「最长匹配」优先：名字里带空格、括号、斜杠也能直接用
    （``"销售额(元)"`` 不会被拆成 ``"销售额"`` + ``"(元)"``）。
    """
    if not isinstance(expr, str) or not expr.strip():
        raise ValueError(
            'kpi 的 expr 需要是字符串公式，例如 expr="销售额 / 订单数"，收到 %r。'
            % (expr,)
        )
    order = sorted(names, key=lambda s: (-len(s), s))
    toks, i, n = [], 0, len(expr)
    while i < n:
        ch = expr[i]
        if ch.isspace():
            i += 1
            continue
        hit = None
        for name in order:
            if expr.startswith(name, i):
                hit = name
                break
        if hit is not None:
            toks.append(("ref", hit))
            i += len(hit)
            continue
        if ch.isdigit() or (ch == "." and i + 1 < n and expr[i + 1].isdigit()):
            j = i
            while j < n and (expr[j].isdigit() or expr[j] == "."):
                j += 1
            try:
                toks.append(("num", float(expr[i:j])))
            except ValueError:  # pragma: no cover - 字符判断已经保证能转
                raise ValueError("kpi 的 expr 里的数字 %r 无法识别。" % (expr[i:j],))
            i = j
            continue
        if ch in _OPS:
            toks.append(("op", ch))
            i += 1
            continue
        raise ValueError(
            "kpi 的 expr 里 %r 无法识别（第 %d 个字符）。公式只支持 + - * / 和括号；"
            "参与计算的指标要先在 metrics= 里定义，当前已定义：%s。"
            % (ch, i + 1, "、".join(names) if names else "（空）")
        )
    return toks


def to_rpn(toks, names):
    """调度场算法：中缀 token → RPN。一元负号按 ``(-1) *`` 处理。"""
    out, stack = [], []
    expect_operand = True
    for kind, val in toks:
        if kind == "num":
            out.append(["n", val])
            expect_operand = False
        elif kind == "ref":
            out.append(["v", names.index(val)])
            expect_operand = False
        elif val == "(":
            stack.append(val)
            expect_operand = True
        elif val == ")":
            if expect_operand:
                raise ValueError('kpi 的 expr 里 ")" 前面的公式不完整，请检查公式。')
            while stack and stack[-1] != "(":
                out.append([stack.pop()])
            if not stack:
                raise ValueError('kpi 的 expr 里 ")" 多了，括号不配对。')
            stack.pop()
            expect_operand = False
        else:  # + - * /
            if expect_operand:
                if val == "-":
                    out.append(["n", -1.0])
                    stack.append("*")
                    continue
                if val == "+":
                    continue
                raise ValueError(
                    'kpi 的 expr 里 "%s" 前面缺少指标或数字，请检查公式。' % (val,)
                )
            while stack and stack[-1] != "(" and _PREC[stack[-1]] >= _PREC[val]:
                out.append([stack.pop()])
            stack.append(val)
            expect_operand = True
    if expect_operand:
        raise ValueError("kpi 的 expr 公式不完整（结尾少了指标或数字）。")
    while stack:
        op = stack.pop()
        if op == "(":
            raise ValueError('kpi 的 expr 里 "(" 多了，括号不配对。')
        out.append([op])
    depth = 0
    for item in out:
        if item[0] in ("n", "v"):
            depth += 1
        elif item[0] in ("+", "-", "*", "/"):
            if depth < 2:
                raise ValueError("kpi 的 expr 公式结构不完整，请检查运算符两侧都有值。")
            depth -= 1
    if depth != 1:
        raise ValueError("kpi 的 expr 公式结构不完整，请检查运算符两侧都有值。")
    return out


def compile_expr(expr, names):
    """公式 + 指标名列表 → RPN。"""
    return to_rpn(tokenize(expr, names), names)


def eval_rpn(rpn, values):
    """Python 侧的 RPN 求值（预渲染 / 测试用；前端另有一份等价实现）。"""
    stack = []
    for item in rpn:
        kind = item[0]
        if kind == "n":
            stack.append(float(item[1]))
        elif kind == "v":
            idx = int(item[1])
            stack.append(values[idx] if 0 <= idx < len(values) else None)
        else:
            b = stack.pop() if stack else None
            a = stack.pop() if stack else None
            if a is None or b is None:
                stack.append(None)
                continue
            if kind == "+":
                stack.append(a + b)
            elif kind == "-":
                stack.append(a - b)
            elif kind == "*":
                stack.append(a * b)
            else:
                stack.append(None if b == 0 else a / b)
    return stack[0] if stack else None


def auto_from_column(df, name):
    """``value`` 是 ``edv.column(...)`` 登记的公式列 → 自动拆成 (metrics, expr)。"""
    from . import metric as _metric

    info = _metric.column_spec(name)
    if not info or not info.get("expr"):
        return None
    expr = info["expr"]
    cols = [str(c) for c in df.columns]
    names = [t[1] for t in tokenize(expr, cols) if t[0] == "ref"]
    metrics = OrderedDict()
    for dep in names:
        if dep in metrics:
            continue
        metrics[dep] = {
            "name": dep,
            "col": dep,
            "agg": _metric.agg_for(dep) or "sum",
        }
    return list(metrics.values()), expr


def normalize_metrics(df, metrics, default_agg="sum"):
    """把 ``metrics=`` 归一化成 ``[{"name", "col", "agg"}, ...]`` 并校验列。

    支持几种写法（越短越常用）::

        metrics={"销售额": "销售额", "订单数": ("订单号", "unique")}
        metrics=[("销售额", "销售额", "sum"), ("客户数", "客户ID", "unique")]
        metrics=[{"name": "订单数", "agg": "count"}]      # 只数行数，不需要列
        metrics="销售额"                                 # 单个指标
    """
    if isinstance(metrics, str):
        metrics = {metrics: metrics}
    items = []
    if isinstance(metrics, dict):
        for name, spec in metrics.items():
            if isinstance(spec, dict):
                items.append((name, spec.get("col"), spec.get("agg")))
            elif isinstance(spec, (list, tuple)):
                if not 1 <= len(spec) <= 2:
                    raise ValueError(
                        "metrics[%r] 需要写成 (列名,) / (列名, 聚合)，收到 %r。"
                        % (name, spec)
                    )
                items.append((name, spec[0], spec[1] if len(spec) > 1 else None))
            elif isinstance(spec, str) and spec in AGGS and spec not in df.columns:
                # {"订单数": "count"} —— 只数行数，没有列名
                items.append((name, None, spec))
            else:
                items.append((name, spec, None))
    elif isinstance(metrics, (list, tuple)):
        for i, spec in enumerate(metrics):
            if isinstance(spec, str):
                items.append((spec, spec, None))
            elif isinstance(spec, dict):
                items.append((spec.get("name"), spec.get("col"), spec.get("agg")))
            elif isinstance(spec, (list, tuple)) and 1 <= len(spec) <= 3:
                name = spec[0]
                col = spec[1] if len(spec) > 1 else None
                agg = spec[2] if len(spec) > 2 else None
                # ("销售额", "sum") / ("订单数", "count")：第二项是聚合名，
                # 列名默认与指标名相同，省得写三遍。
                if (len(spec) == 2 and isinstance(col, str) and col in AGGS
                        and col != name):
                    col, agg = name, col
                items.append((name, col, agg))
            else:
                raise ValueError(
                    "metrics[%d] 写法不支持，收到 %r；可用 str / (name, col[, agg]) / dict。"
                    % (i, spec)
                )
    elif metrics is None:
        raise ValueError('metrics 不能为空：例如 metrics={"销售额": "销售额"}。')
    else:
        raise TypeError(
            "metrics 需要是 dict / list / str，收到 %r。" % (type(metrics).__name__,)
        )
    if not items:
        raise ValueError(
            'metrics 不能为空：至少要定义 1 个指标，例如 metrics={"销售额": "销售额"}。'
        )

    out = OrderedDict()
    for i, (name, col, agg) in enumerate(items):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("metrics[%d] 的指标名需要是非空字符串，收到 %r。" % (i, name))
        name = name.strip()
        agg = agg or default_agg
        if agg not in AGGS:
            raise ValueError(
                "metrics[%r] 的 agg=%r 不支持，可选：%s"
                % (name, agg, ", ".join(AGGS))
            )
        if name in out:
            raise ValueError("metrics 里的指标名 %r 重复了，请换一个名字。" % (name,))
        if agg == "count":
            if col is not None:
                _frame.require_column(df, col, "metrics[%r] 的列" % (name,))
            out[name] = {"name": name, "col": None, "agg": "count"}
            continue
        if col is None:
            raise ValueError(
                "metrics[%r] 缺少列名：agg!=count 时必须说明用哪一列，"
                '例如 metrics={"%s": ("客户号", "unique")}。' % (name, name)
            )
        if col not in df.columns:
            _frame.require_column(df, col, "metrics[%r] 的列" % (name,))
        if agg in NUMERIC_AGGS:
            kind = _frame.column_kind(df[col])
            if kind != _frame.KIND_NUM and not _frame._looks_numeric(df[col]):
                raise ValueError(
                    "metrics[%r] 的列 %r 是文本列，不能用 agg=%r。"
                    '数不同值请用 agg="unique"，数行数请用 agg="count"。'
                    % (name, col, agg)
                )
        out[name] = {"name": name, "col": str(col), "agg": agg}
    return list(out.values())
