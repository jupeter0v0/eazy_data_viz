# -*- coding: utf-8 -*-
"""histogram 示例大全：直方图。

运行方式（在仓库根目录）：

    PYTHONPATH=. PYTHONIOENCODING=utf-8 python examples/charts/histogram.py

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
    print("histogram 示例：5 个小节")

    # ---- 数据准备（按需派生） ----
    month_df = df.groupby("月份", observed=True)["销售额"].sum().reset_index()
    region_df = df.groupby("大区", observed=True).agg(
       销售额=("销售额", "sum"), 订单数=("订单数", "sum"), 利润=("利润", "sum")).reset_index()


    # ---- 示例 1：最简用法：销售额分布 ----
    chart = edv.histogram(df, column="销售额", bins=20)
    chart.save(os.path.join(OUT, "histogram_1.html"))
    check(os.path.join(OUT, "histogram_1.html"))

    # ---- 示例 2：调整分箱数：bins 对比 ----
    chart = edv.histogram(
        df, column="销售额", bins=10,
        title="销售额分布（10 箱）", subtitle="箱数少，形状更平滑",
        xtitle="销售额（元）", ytitle="记录数",
    )
    chart.save(os.path.join(OUT, "histogram_2.html"))
    check(os.path.join(OUT, "histogram_2.html"))

    # ---- 示例 3：省略 column：自动选择唯一数值列 ----
    profit = df[["利润"]].copy()
    chart = edv.histogram(
        profit, bins=15,
        title="利润分布（自动选列）", subtitle="子表只剩一个数值列，column 可省略",
        height=380,
    )
    chart.save(os.path.join(OUT, "histogram_3.html"))
    check(os.path.join(OUT, "histogram_3.html"))

    # ---- 示例 4：深色主题 + 配色 ----
    chart = edv.histogram(
        df, column="利润", bins=24,
        theme="dark",
        title="利润分布（深色）", subtitle="24 箱，观察长尾",
        xtitle="利润（元）", ytitle="记录数",
    )
    chart.palette("antd")
    chart.save(os.path.join(OUT, "histogram_4.html"))
    check(os.path.join(OUT, "histogram_4.html"))

    # ---- 示例 5：对数变换后的分布 ----
    import numpy as np
    log_df = df.assign(对数销售额=np.log1p(df["销售额"]))
    chart = edv.histogram(
        log_df, column="对数销售额", bins=20,
        title="销售额的对数分布", subtitle="log1p 变换后更接近对称",
        xtitle="log(1 + 销售额)", ytitle="记录数",
    )
    chart.save(os.path.join(OUT, "histogram_5.html"))
    check(os.path.join(OUT, "histogram_5.html"))

    print("OK histogram")


if __name__ == "__main__":
    main()
