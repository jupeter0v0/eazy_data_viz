# -*- coding: utf-8 -*-
"""sparkline（迷你走势图）完整示例：5 个用法，覆盖最简/典型/进阶参数/边界/联动/配色。

运行方式（在仓库根目录）：

    cd F:/deepseek/eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/sparkline.py

输出：examples/output/sparkline_*.html（每个文件都是可离线打开的独立页面）。
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


    # ---- 示例 1：最简：产品 × 月份 ----
    chart = edv.sparkline(df, x="月份", y="销售额", group="产品")
    chart.save("examples/output/sparkline_1.html")

    # ---- 示例 2：典型：大区销售走势对比 ----
    chart = edv.sparkline(
        df,
        x="月份",
        y="订单数",
        group="大区",
        title="各大区订单走势",
        height=300,
    )
    chart.save("examples/output/sparkline_2.html")

    # ---- 示例 3：先聚合再画：按月汇总更清晰 ----
    monthly = (
        df.groupby(["月份", "产品"], as_index=False, observed=True)["销售额"]
          .sum()
    )
    chart = edv.sparkline(monthly, x="月份", y="销售额", group="产品", height=360)
    chart.save("examples/output/sparkline_3.html")

    # ---- 示例 4：深色主题与配色 ----
    chart = edv.sparkline(df, x="月份", y="利润", group="产品", theme="dark")
    chart.palette("carbon")
    chart.save("examples/output/sparkline_4.html")

    # ---- 示例 5：多图拼看板 ----
    sales = edv.sparkline(df, x="月份", y="销售额", group="产品", title="销售额走势")
    orders = edv.sparkline(df, x="月份", y="订单数", group="大区", title="订单数走势")
    edv.dashboard(sales, orders, title="走势看板", cols=2).save("examples/output/sparkline_5.html")

if __name__ == "__main__":
    main()
    print("OK sparkline")
