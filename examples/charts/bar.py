# -*- coding: utf-8 -*-
"""bar 示例大全：分组 / 堆叠柱状图。

运行方式（在仓库根目录）：

    PYTHONPATH=. PYTHONIOENCODING=utf-8 python examples/charts/bar.py

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
    print("bar 示例：4 个小节")

    # ---- 数据准备（按需派生） ----
    month_df = df.groupby("月份", observed=True)["销售额"].sum().reset_index()
    region_df = df.groupby("大区", observed=True).agg(
       销售额=("销售额", "sum"), 订单数=("订单数", "sum"), 利润=("利润", "sum")).reset_index()


    # ---- 示例 1：最简用法：各大区销售额 ----
    chart = edv.bar(df, x="大区", y="销售额")
    chart.save(os.path.join(OUT, "bar_1.html"))
    check(os.path.join(OUT, "bar_1.html"))

    # ---- 示例 2：按类目聚合 + 排序 + top_n：省份销售额前 8 ----
    chart = edv.bar(
        df, x="省份", y="销售额",
        agg="sum", sort="desc", top_n=8,
        fmt="currency", labels=True,
        title="销售额 TOP 8 省份", subtitle="2024 全年，含税",
        xtitle="省份", ytitle="销售额（元）",
    )
    chart.save(os.path.join(OUT, "bar_2.html"))
    check(os.path.join(OUT, "bar_2.html"))

    # ---- 示例 3：分组堆叠：产品 × 渠道 ----
    chart = edv.bar(
        df, x="产品", y="销售额", color="渠道",
        stack=True, sort="x",
        title="各产品渠道构成", subtitle="堆叠显示合计",
        xtitle="产品", ytitle="销售额（元）",
    )
    chart.save(os.path.join(OUT, "bar_3.html"))
    check(os.path.join(OUT, "bar_3.html"))

    # ---- 示例 4：下钻 + 联动：大区 → 省份 → 城市 ----
    chart = edv.bar(
        df, x="大区", y="销售额",
        drill=["大区", "省份", "城市"],
        link="销售", sort="desc",
        title="销售额下钻", subtitle="点击柱子逐级查看，联动组“销售”",
        xtitle="大区", ytitle="销售额（元）",
    )
    chart.save(os.path.join(OUT, "bar_4.html"))
    check(os.path.join(OUT, "bar_4.html"))

    print("OK bar")


if __name__ == "__main__":
    main()
