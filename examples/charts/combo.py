# -*- coding: utf-8 -*-
"""combo 示例大全：柱线混合图。

运行方式（在仓库根目录）：

    PYTHONPATH=. PYTHONIOENCODING=utf-8 python examples/charts/combo.py

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
    print("combo 示例：5 个小节")

    # ---- 数据准备（按需派生） ----
    month_df = df.groupby("月份", observed=True)["销售额"].sum().reset_index()
    region_df = df.groupby("大区", observed=True).agg(
       销售额=("销售额", "sum"), 订单数=("订单数", "sum"), 利润=("利润", "sum")).reset_index()


    # ---- 示例 1：最简用法：销售额柱 + 订单数线 ----
    chart = edv.combo(df, x="月份", bar="销售额", line="订单数")
    chart.save(os.path.join(OUT, "combo_1.html"))
    check(os.path.join(OUT, "combo_1.html"))

    # ---- 示例 2：按大区：柱=销售额，线=利润 ----
    chart = edv.combo(
        df, x="大区", bar="销售额", line="利润",
        title="各大区销售额与利润", subtitle="柱=销售额（左轴），线=利润（右轴）",
    )
    chart.save(os.path.join(OUT, "combo_2.html"))
    check(os.path.join(OUT, "combo_2.html"))

    # ---- 示例 3：mean 聚合：平均客单价 ----
    chart = edv.combo(
        df, x="产品", bar="销售额", line="利润", agg="mean",
        title="产品平均销售额与平均利润", subtitle="agg=mean 口径",
        fmt="currency", height=420,
    )
    chart.save(os.path.join(OUT, "combo_3.html"))
    check(os.path.join(OUT, "combo_3.html"))

    # ---- 示例 4：深色主题 + 配色 ----
    chart = edv.combo(
        df, x="渠道", bar="订单数", line="利润",
        theme="dark", height=440,
        title="渠道订单数与利润（深色）",
    )
    chart.palette("echarts")
    chart.save(os.path.join(OUT, "combo_4.html"))
    check(os.path.join(OUT, "combo_4.html"))

    # ---- 示例 5：count 聚合：记录数柱 + 客户数线 ----
    chart = edv.combo(
        df, x="渠道", bar="订单数", line="客户数", agg="count",
        fmt="thousands", height=440,
        title="渠道记录数对照", subtitle="agg=count 统计非空记录数",
    )
    chart.save(os.path.join(OUT, "combo_5.html"))
    check(os.path.join(OUT, "combo_5.html"))

    print("OK combo")


if __name__ == "__main__":
    main()
