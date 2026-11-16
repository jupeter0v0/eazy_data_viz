# -*- coding: utf-8 -*-
"""quadrant（四象限散点图）完整示例：5 个用法，覆盖最简/典型/进阶参数/边界/联动/配色。

运行方式（在仓库根目录）：

    cd F:/deepseek/eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/quadrant.py

输出：examples/output/quadrant_*.html（每个文件都是可离线打开的独立页面）。
"""

import os
import sys

# 直接运行本文件时，sys.path[0] 是 examples/charts；该目录里的 calendar.py
# 会遮蔽标准库 calendar，导致 pandas 导入失败。这里在导入 pandas 前移除它。
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path
              if os.path.abspath(p or os.getcwd()) != _HERE]

import pandas as pd

import eazy_data_viz as edv


def main():
    df = edv.sample_df()
    print("数据：%d 行 × %d 列" % (df.shape[0], df.shape[1]))


    # ---- 示例 1：最简四象限 ----
    chart = edv.quadrant(df, x="销售额", y="利润")
    chart.save("examples/output/quadrant_1.html")

    # ---- 示例 2：典型：颜色分组 + 气泡大小 ----
    chart = edv.quadrant(
        df,
        x="销售额",
        y="客户数",
        size="订单数",
        color="大区",
        title="销售额 × 客户数",
        subtitle="气泡大小=订单数 · 颜色=大区",
    )
    chart.save("examples/output/quadrant_2.html")

    # ---- 示例 3：深色主题与配色 ----
    chart = edv.quadrant(df, x="销售额", y="利润", color="渠道", theme="dark")
    chart.palette("antd")
    chart.save("examples/output/quadrant_3.html")

    # ---- 示例 4：联动：点击气泡过滤明细 ----
    q = edv.quadrant(df, x="销售额", y="利润", color="大区", link="q1")
    tbl = edv.table(df, columns=["大区", "产品", "销售额", "利润"], link="q1", limit=40)
    edv.dashboard(q, tbl, title="四象限联动", cols=2).save("examples/output/quadrant_4.html")

    # ---- 示例 5：按产品分组：四个产品各自的位置 ----
    # 先聚合到「产品」粒度，再放入四象限，避免 1500 个点重叠
    agg = df.groupby("产品", as_index=False).agg(
        销售额=("销售额", "sum"),
        利润=("利润", "sum"),
        订单数=("订单数", "sum"),
    )
    chart = edv.quadrant(
        agg,
        x="销售额",
        y="利润",
        size="订单数",
        color="产品",
        quad_labels=["低销高利", "高销高利", "低销低利", "高销低利"],
    )
    chart.save("examples/output/quadrant_5.html")

if __name__ == "__main__":
    main()
    print("OK quadrant")
