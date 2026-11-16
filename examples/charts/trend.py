# -*- coding: utf-8 -*-
"""trend（趋势图（散点 + 线性拟合））完整示例：5 个用法，覆盖最简/典型/进阶参数/边界/联动/配色。

运行方式（在仓库根目录）：

    cd F:/deepseek/eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/trend.py

输出：examples/output/trend_*.html（每个文件都是可离线打开的独立页面）。
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


    # ---- 示例 1：最简：销售额 vs 利润 ----
    chart = edv.trend(df, x="销售额", y="利润")
    chart.save("examples/output/trend_1.html")

    # ---- 示例 2：典型：按大区分组着色 ----
    chart = edv.trend(
        df,
        x="销售额",
        y="利润",
        color="大区",
        title="销售额与利润的线性关系",
        subtitle="颜色=大区 · 回归线基于全量数据",
        height=440,
    )
    chart.save("examples/output/trend_2.html")

    # ---- 示例 3：格式化与深色主题 ----
    chart = edv.trend(df, x="客户数", y="销售额", fmt="thousands", theme="dark")
    chart.palette("tableau")
    chart.save("examples/output/trend_3.html")

    # ---- 示例 4：先聚合再拟合：大区层面 ----
    agg = df.groupby("大区", as_index=False).agg(
        销售额=("销售额", "sum"),
        利润=("利润", "sum"),
    )
    chart = edv.trend(agg, x="销售额", y="利润", color="大区", height=380)
    chart.save("examples/output/trend_4.html")

    # ---- 示例 5：联动：点击分组点过滤明细 ----
    tr = edv.trend(df, x="销售额", y="利润", color="大区", link="tr1")
    tbl = edv.table(df, columns=["大区", "销售额", "利润"], link="tr1", limit=40)
    edv.dashboard(tr, tbl, title="趋势图联动", cols=2).save("examples/output/trend_5.html")

if __name__ == "__main__":
    main()
    print("OK trend")
