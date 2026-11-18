# -*- coding: utf-8 -*-
"""table() 中国式报表特性单测（纯 Python，不需要 Chrome / Node）。

覆盖：
* 新参数校验（total / index / bar / stripe 类型与列名）；
* spec 里 total / index / bar / stripe 键的取值；
* build_page 生成的 HTML：内联 CSS（合计行、斑马纹、数据条、固定首列）与
  内联 JS 的表格模板（序号列、合计行、数据条 class、「−」空值占位）。

说明：表格是客户端渲染（eazy_extra_html.js 的 H['table']），所以 HTML 断言落在
「页面内联的 JS 模板字符串 + CSS 规则 + EAZY_PAGE 里的 spec」，不需要运行浏览器。

运行：python tests/test_report_table.py
"""
import json
import os
import re
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import eazy_data_viz  # noqa: E402
from eazy_data_viz import render as _render  # noqa: E402

PASS, FAIL = [], []


def check(name, fn):
    try:
        fn()
        PASS.append(name)
    except Exception:
        FAIL.append((name, traceback.format_exc()))


def _df():
    """小明细表：利润列留一个空值，用于验证「−」占位。"""
    pd = __import__("pandas")
    return pd.DataFrame(
        {
            "月份": ["1月", "2月", "3月"],
            "大区": ["华东", "华南", "华北"],
            "销售额": [1638.25, 996.10, 1015.06],
            "利润": [225.08, None, 207.64],
        }
    )


DF = _df()
COLS = ["月份", "大区", "销售额", "利润"]


def _page(chart):
    return _render.build_page([chart], inline=True)


def _page_chart(html):
    """从 build_page 的结果里取出 window.EAZY_PAGE.charts[0]。"""
    m = re.search(r"window\.EAZY_PAGE = (\{.*?\});</script>", html, re.S)
    assert m, "页面里没有 window.EAZY_PAGE"
    return json.loads(m.group(1))["charts"][0]


def _expect_error(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except ValueError as err:
        return str(err)
    raise AssertionError("这里应该抛 ValueError")


# ---------------------------------------------------------------- spec 层
def t_defaults():
    """不传新参数时：total/index 关闭、bar 为空、stripe 默认开启。"""
    s = eazy_data_viz.table(DF).spec
    assert s["total"] is False, s.get("total")
    assert s["index"] is False, s.get("index")
    assert s["bar"] is None, s.get("bar")
    assert s["stripe"] is True, s.get("stripe")
    assert s["limit"] == 100 and s["columns"] == COLS, (s["limit"], s["columns"])
    assert s["type"] == "table"


def t_spec_flags():
    """total/index/bar/stripe 正确落到 spec，bar 归一化为列名数组。"""
    s = eazy_data_viz.table(
        DF, columns=COLS, total=True, index=True, bar="销售额", stripe=False
    ).spec
    assert s["total"] is True and s["index"] is True and s["stripe"] is False
    assert s["bar"] == ["销售额"], s["bar"]

    s2 = eazy_data_viz.table(DF, columns=COLS, bar=["利润", "销售额"]).spec
    assert s2["bar"] == ["利润", "销售额"], s2["bar"]  # 保持用户给出的顺序

    s3 = eazy_data_viz.table(DF, columns=COLS, bar=True).spec
    assert s3["bar"] == ["销售额"], "bar=True 应自动取第一个数值列，实际 %r" % (s3["bar"],)

    s4 = eazy_data_viz.table(DF, columns=COLS, bar=("销售额", "利润")).spec
    assert s4["bar"] == ["销售额", "利润"], s4["bar"]

    # 重复列名去重
    s5 = eazy_data_viz.table(DF, columns=COLS, bar=["销售额", "销售额"]).spec
    assert s5["bar"] == ["销售额"], s5["bar"]

    # 关闭数据条
    assert eazy_data_viz.table(DF, columns=COLS, bar=False).spec["bar"] is None


def t_limit_unchanged():
    """limit / max_rows 逻辑保持不变（表格内嵌行数仍由 max_rows 控制）。"""
    assert eazy_data_viz.table(DF, limit=2).spec["limit"] == 2
    assert eazy_data_viz.table(DF, limit=5000).spec["limit"] == 200  # 上限 200
    assert len(eazy_data_viz.table(DF, max_rows=2).data["rows"]) == 2
    assert len(eazy_data_viz.table(DF, max_rows=200).data["rows"]) == 3


def t_empty_table():
    """空表（过滤后 0 行）显示「没有数据」，且不会画合计行。"""
    page = _page(eazy_data_viz.table(DF, columns=COLS, total=True))
    early = page.find(
        "if (!rows.length || !cols.length) return '<div class=\"eazy-empty\">当前条件下没有数据</div>';"
    )
    tfoot = page.find("'<tfoot><tr class=\"eazy-table-total\">'")
    assert early > 0, "找不到空表兜底分支"
    assert tfoot > 0, "找不到合计行模板"
    assert early < tfoot, "空表兜底必须早于合计行渲染"


# ---------------------------------------------------------------- 参数校验
def t_param_errors():
    """非法参数必须报中文 ValueError，且提示里带参数名。"""
    msg = _expect_error(eazy_data_viz.table, DF, columns=COLS, bar="不存在的列")
    assert "bar" in msg and "不在 columns 里" in msg, msg

    msg = _expect_error(eazy_data_viz.table, DF, columns=COLS, bar="大区")
    assert "bar" in msg and "数值列" in msg, msg

    msg = _expect_error(eazy_data_viz.table, DF, columns=COLS, bar=3)
    assert "bar" in msg, msg

    msg = _expect_error(eazy_data_viz.table, DF, columns=COLS, bar=[123])
    assert "bar" in msg, msg

    msg = _expect_error(eazy_data_viz.table, DF, columns=COLS, bar=[])
    assert "bar" in msg and "空列表" in msg, msg

    msg = _expect_error(eazy_data_viz.table, DF, columns=COLS, total=1)
    assert "total" in msg and "bool" in msg, msg

    msg = _expect_error(eazy_data_viz.table, DF, columns=COLS, index="yes")
    assert "index" in msg and "bool" in msg, msg

    msg = _expect_error(eazy_data_viz.table, DF, columns=COLS, stripe=None)
    assert "stripe" in msg and "bool" in msg, msg

    # 只有文本列时 bar=True 无法自动选列
    msg = _expect_error(
        eazy_data_viz.table, DF[["大区"]], columns=["大区"], bar=True
    )
    assert "bar=True" in msg and "数值列" in msg, msg


# ---------------------------------------------------------------- 页面 HTML 层
def t_page_spec():
    """build_page 后 EAZY_PAGE 里的 spec 带上 4 个新键。"""
    ch = eazy_data_viz.table(
        DF, columns=COLS, total=True, index=True, bar=["销售额", "利润"], stripe=False
    )
    s = _page_chart(_page(ch))
    assert s["total"] is True and s["index"] is True and s["stripe"] is False
    assert s["bar"] == ["销售额", "利润"], s["bar"]
    assert s["limit"] == 100 and s["columns"] == COLS

    s2 = _page_chart(_page(eazy_data_viz.table(DF, columns=COLS)))
    assert s2["total"] is False and s2["index"] is False and s2["bar"] is None
    assert s2["stripe"] is True


def t_page_css():
    """内联 CSS：合计行双线/加粗、斑马纹、数据条、首列 sticky + 阴影。"""
    page = _page(eazy_data_viz.table(DF, columns=COLS, total=True, index=True, bar="销售额"))
    css = page.split("</style>", 1)[0]

    assert ".eazy-table-wrap{" in css
    # 首列固定 + 阴影（序号列也走同一条规则）
    assert ".eazy-table tbody td:first-child,.eazy-table tfoot td:first-child" in css
    assert "position:sticky;left:0" in css
    assert "box-shadow:8px 0 8px -4px var(--pv-scrim)" in css
    # 序号列
    assert ".eazy-table .eazy-col-idx{" in css
    # 斑马纹（默认开启，可关闭）
    assert ".eazy-table.eazy-table-stripe tbody tr:nth-child(even) td" in css
    assert "background-color:var(--pv-surface-2)" in css
    # 合计行：加粗 + 顶部双线 + 浅底色
    assert ".eazy-table tfoot td{" in css
    assert "font-weight:600" in css
    assert "border-top:4px double var(--pv-outline)" in css
    assert ".eazy-table tfoot .eazy-total-label{" in css
    # 数据条
    assert ".eazy-table td.eazy-bar-cell{" in css
    assert ".eazy-table .eazy-bar-val{position:relative;z-index:1}" in css


def t_page_markup():
    """内联 JS 的表格模板：序号列、合计行、数据条、「−」空值。"""
    page = _page(
        eazy_data_viz.table(
            DF, columns=COLS, total=True, index=True, bar=["销售额", "利润"], stripe=True
        )
    )
    assert '<div class="eazy-table-wrap"><table class="eazy-table' in page
    assert "(striped ? ' eazy-table-stripe' : '')" in page  # 斑马纹 class 按 stripe 开关拼接
    # 序号列：表头 + 1..N 的单元格
    assert '<th class="eazy-col-idx">序号</th>' in page
    assert "'<td class=\"eazy-col-idx\">' + (i + 1) + '</td>'" in page
    # 合计行（有 index 时标签在序号列，没有 index 时占第一列）
    assert '<tfoot><tr class="eazy-table-total">' in page
    assert 'class="eazy-col-idx eazy-total-label">合计</td>' in page
    assert '<td class="eazy-total-label">合计</td>' in page
    assert 'class="num eazy-total-num' in page
    # 第一列是数值列时，「合计」与该列合计同格（避免吞掉第一列的合计）
    assert "var firstIsNum = (!showIndex && t === 0 && kinds[tcol] === 'num');" in page
    assert '<span class="eazy-total-tag">合计</span>' in page
    assert "eazy-total-first" in page
    assert "for (var s = 0; s < shown.length; s++)" in page  # 只统计实际渲染的行
    # 数据条：渐变画条 + 文字层
    assert "eazy-bar-cell" in page
    assert "linear-gradient(90deg," in page
    assert '<span class="eazy-bar-val">' in page
    # 空值统一显示「−」，且所有分支都先判空
    assert "var TABLE_EMPTY = '−';" in page
    assert "if (isBlank(v)) return TABLE_EMPTY;" in page
    # 合计只统计真正渲染出来的行，不改 limit 提示
    assert "共 ' + rows.length + ' 行，仅显示前 ' + limit + ' 行" in page


def t_total_numeric_first():
    """第一列就是数值列时，total 仍要给出这一列的合计（标签进同一格）。"""
    import pandas as pd
    df = pd.DataFrame({"销售额": [10.0, 20.0, 30.5], "利润": [1.0, 2.0, 3.0]})
    c = eazy_data_viz.table(df, columns=["销售额", "利润"], total=True)
    page = _page(c)
    assert "firstIsNum" in page and "eazy-total-tag" in page
    assert c.spec["total"] is True and c.spec["index"] is False
    # 有 index 时仍走「标签独占序号列」的分支
    c2 = eazy_data_viz.table(df, columns=["销售额", "利润"], total=True, index=True)
    assert "eazy-total-label" in _page(c2)


def t_link_source():
    """表格当联动源：spec 带 link，CSS/JS 里有可点单元格与命中行高亮。"""
    tbl = eazy_data_viz.table(DF, columns=COLS, link="g1")
    assert tbl.spec.get("link") == "g1", tbl.spec.get("link")
    assert eazy_data_viz.table(DF, columns=COLS).spec.get("link") is None

    page = _page(tbl)
    css = page.split("</style>", 1)[0]
    assert ".eazy-table td.eazy-cell-link{cursor:pointer}" in css
    assert ".eazy-table tbody tr.eazy-row-hit td" in css
    # 服务端不做表格渲染，但内联的 JS 模板必须带上可点单元格的 data 属性
    assert "data-eazy-cell" in page
    assert "data-eazy-val" in page
    assert "eazy-row-hit" in page


def t_page_dark():
    """深色主题：斑马纹 / 合计行 / 数据条都用主题变量或调深后的 rgba。"""
    page = _page(
        eazy_data_viz.table(
            DF, columns=COLS, total=True, bar="销售额", theme="dark"
        )
    )
    assert 'data-theme="dark"' in page
    assert "--pv-surface-2:#131314" in page  # 深色斑马纹底色
    assert "--pv-surface-3:#2d2e30" in page  # 深色合计行底色
    assert "theme.name === 'dark' ? 0.34 : 0.22" in page


for name, fn in sorted((k[2:], v) for k, v in list(globals().items()) if k.startswith("t_")):
    check(name, fn)

print("PASS %d" % len(PASS))
if FAIL:
    print("FAIL %d" % len(FAIL))
    for name, tb in FAIL:
        print("\n--- %s ---\n%s" % (name, tb))
    sys.exit(1)
print("ALL OK:", ", ".join(PASS))
