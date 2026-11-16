# -*- coding: utf-8 -*-
"""scatter 示例大全：散点 / 气泡图。

运行方式（在仓库根目录）：

    PYTHONPATH=. PYTHONIOENCODING=utf-8 python examples/charts/scatter.py

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
    print("scatter 示例：5 个小节")

    # ---- 数据准备（按需派生） ----
    month_df = df.groupby("月份", observed=True)["销售额"].sum().reset_index()
    region_df = df.groupby("大区", observed=True).agg(
       销售额=("销售额", "sum"), 订单数=("订单数", "sum"), 利润=("利润", "sum")).reset_index()


    # ---- 示例 1：最简用法：销售额与订单数 ----
    chart = edv.scatter(df, x="销售额", y="订单数")
    chart.save(os.path.join(OUT, "scatter_1.html"))
    check(os.path.join(OUT, "scatter_1.html"))

    # ---- 示例 2：气泡图：size 表达第三维 ----
    chart = edv.scatter(
        df, x="销售额", y="订单数", size="客户数",
        title="销售额 / 订单数 / 客户数", subtitle="气泡大小 = 客户数",
        xtitle="销售额（元）", ytitle="订单数",
        height=420,
    )
    chart.save(os.path.join(OUT, "scatter_2.html"))
    check(os.path.join(OUT, "scatter_2.html"))

    # ---- 示例 3：按类别着色：产品分组 ----
    chart = edv.scatter(
        df, x="销售额", y="利润", color="产品",
        title="销售额与利润（按产品着色）",
        subtitle="不同颜色代表不同产品",
        xtitle="销售额（元）", ytitle="利润（元）",
    )
    chart.save(os.path.join(OUT, "scatter_3.html"))
    check(os.path.join(OUT, "scatter_3.html"))

    # ---- 示例 4：先聚合再画：城市级散点 ----
    city = df.groupby("城市", observed=True).agg(
        销售额=("销售额", "sum"), 订单数=("订单数", "sum"),
    ).reset_index()
    chart = edv.scatter(
        city, x="销售额", y="订单数", color="城市",
        title="城市级销售额 vs 订单数", subtitle="先在 pandas 聚合，避免点重叠",
        xtitle="销售额（元）", ytitle="订单数", legend=False,
    )
    chart.save(os.path.join(OUT, "scatter_4.html"))
    check(os.path.join(OUT, "scatter_4.html"))

    # ---- 示例 5：配色 / 深色 / 导出 ----
    chart = edv.scatter(
        df, x="订单数", y="利润", color="产品", size="客户数",
        theme="dark",
        title="订单数 / 利润 / 客户数（深色气泡）",
        height=460,
    )
    chart.palette("carbon")
    chart.save(os.path.join(OUT, "scatter_5.html"))
    check(os.path.join(OUT, "scatter_5.html"))

    print("OK scatter")


if __name__ == "__main__":
    main()
