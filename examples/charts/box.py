# -*- coding: utf-8 -*-
"""box 示例大全：箱线图。

运行方式（在仓库根目录）：

    PYTHONPATH=. PYTHONIOENCODING=utf-8 python examples/charts/box.py

脚本会运行 5 个小节，每个小节把图保存到 examples/output/，并校验 HTML 大于 100KB。
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
    print("box 示例：5 个小节")

    # ---- 数据准备（按需派生） ----
    month_df = df.groupby("月份", observed=True)["销售额"].sum().reset_index()
    region_df = df.groupby("大区", observed=True).agg(
       销售额=("销售额", "sum"), 订单数=("订单数", "sum"), 利润=("利润", "sum")).reset_index()


    # ---- 示例 1：最简用法：各大区销售额分布 ----
    chart = edv.box(df, x="大区", y="销售额")
    chart.save(os.path.join(OUT, "box_1.html"))
    check(os.path.join(OUT, "box_1.html"))

    # ---- 示例 2：只给 y：整体分布单箱 ----
    chart = edv.box(
        df, y="销售额",
        title="销售额整体分布", subtitle="不分组时只画一个箱子",
        ytitle="销售额（元）",
    )
    chart.save(os.path.join(OUT, "box_2.html"))
    check(os.path.join(OUT, "box_2.html"))

    # ---- 示例 3：分组对比：产品利润分布 ----
    chart = edv.box(
        df, x="产品", y="利润",
        title="各产品利润分布", subtitle="利润有负值，须线会跨过 0",
        ytitle="利润（元）", fmt="currency",
    )
    chart.save(os.path.join(OUT, "box_3.html"))
    check(os.path.join(OUT, "box_3.html"))

    # ---- 示例 4：按月份分组（有序分类） ----
    chart = edv.box(
        df, x="月份", y="销售额",
        height=480,
        title="月度销售额分布", subtitle="12 个箱子按月排列",
        ytitle="销售额（元）", fmt="compact",
    )
    chart.save(os.path.join(OUT, "box_4.html"))
    check(os.path.join(OUT, "box_4.html"))

    # ---- 示例 5：深色主题 + 配色 ----
    chart = edv.box(
        df, x="大区", y="利润",
        theme="dark", height=440,
        title="各大区利润分布（深色）",
        ytitle="利润（元）",
    )
    chart.palette("tableau")
    chart.save(os.path.join(OUT, "box_5.html"))
    check(os.path.join(OUT, "box_5.html"))

    print("OK box")


if __name__ == "__main__":
    main()
