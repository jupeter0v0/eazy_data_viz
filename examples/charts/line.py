# -*- coding: utf-8 -*-
"""line 示例大全：折线 / 趋势图。

运行方式（在仓库根目录）：

    PYTHONPATH=. PYTHONIOENCODING=utf-8 python examples/charts/line.py

脚本会运行 4 个小节，每个小节把图保存到 examples/output/，并校验 HTML 大于 100KB。
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "examples", "output")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# examples/charts/ 目录下的其它示例脚本可能与标准库模块同名（例如 calendar.py），
# 直接运行本脚本时该目录会排在 sys.path 首位、遮蔽标准库，导致 import pandas 失败。
# 因此先把脚本所在目录从 sys.path 中移除，再 import 第三方库。
for _p in list(sys.path):
    try:
        if _p and os.path.abspath(_p) == HERE:
            sys.path.remove(_p)
    except OSError:
        pass

import pandas as pd  # noqa: E402

import eazy_data_viz as edv  # noqa: E402


def check(path):
    """校验生成的 HTML 文件存在且大于 100KB。返回文件大小（字节）。"""
    assert os.path.isfile(path), "没有生成文件：%s" % path
    size = os.path.getsize(path)
    assert size > 100_000, "HTML 只有 %d 字节，疑似资源没有内联：%s" % (size, path)
    print("    saved %-42s %8.1f KB" % (os.path.basename(path), size / 1024.0))
    return size


def main():
    os.makedirs(OUT, exist_ok=True)
    df = edv.sample_df()
    print("line 示例：4 个小节")

    # ---- 数据准备（按需派生） ----
    month_df = df.groupby("月份", observed=True)["销售额"].sum().reset_index()
    region_df = df.groupby("大区", observed=True).agg(
       销售额=("销售额", "sum"), 订单数=("订单数", "sum"), 利润=("利润", "sum")).reset_index()


    # ---- 示例 1：最简用法：销售额趋势 ----
    chart = edv.line(df, x="日期", y="销售额")
    chart.save(os.path.join(OUT, "line_1.html"))
    check(os.path.join(OUT, "line_1.html"))

    # ---- 示例 2：按月聚合：12 个月的销售额 ----
    month = df.groupby("月份", observed=True)["销售额"].sum().reset_index()
    chart = edv.line(
        month, x="月份", y="销售额", sort="x",
        title="月度销售额趋势", subtitle="按订单月份汇总",
        xtitle="月份", ytitle="销售额（元）",
    )
    chart.save(os.path.join(OUT, "line_2.html"))
    check(os.path.join(OUT, "line_2.html"))

    # ---- 示例 3：坐标范围 + 标题：固定 y 轴上限 ----
    month = df.groupby("月份", observed=True)["销售额"].sum().reset_index()
    chart = edv.line(
        month, x="月份", y="销售额", sort="x",
        ylim=(0, 4000000), xlim=(0, 12),
        title="月度销售额（固定坐标范围）",
        subtitle="y 轴 0~400万，便于多图对比",
        xtitle="月份", ytitle="销售额（元）", fmt="thousands",
    )
    chart.save(os.path.join(OUT, "line_3.html"))
    check(os.path.join(OUT, "line_3.html"))

    # ---- 示例 4：下钻 + 联动：日期 → 大区 → 产品 ----
    chart = edv.line(
        df, x="日期", y="销售额",
        drill=["日期", "大区", "产品"], link="趋势",
        title="销售额趋势下钻", subtitle="点击数据点进入下一层维度",
        xtitle="日期", ytitle="销售额（元）",
    )
    chart.save(os.path.join(OUT, "line_4.html"))
    check(os.path.join(OUT, "line_4.html"))

    print("OK line")


if __name__ == "__main__":
    main()
