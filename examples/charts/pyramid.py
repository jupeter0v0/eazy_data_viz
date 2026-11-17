# -*- coding: utf-8 -*-
"""pyramid（金字塔图）完整示例：5 个用法，覆盖最简/典型/进阶参数/边界/联动/配色。

运行方式（在仓库根目录）：

    cd F:/deepseek/eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/pyramid.py

输出：examples/output/pyramid_*.html（每个文件都是可离线打开的独立页面）。
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


    # ---- 示例 1：最简金字塔 ----
    chart = edv.pyramid(df, names="大区", values="销售额")
    chart.save("examples/output/pyramid_1.html")

    # ---- 示例 2：典型：渠道订单分层 ----
    chart = edv.pyramid(
        df,
        names="渠道",
        values="订单数",
        title="渠道订单分层",
        subtitle="订单数 · 自上而下递减",
        height=400,
    )
    chart.save("examples/output/pyramid_2.html")

    # ---- 示例 3：进阶：不传数值，按记录条数分层 ----
    chart = edv.pyramid(df, names="产品", title="各产品线记录条数")
    chart.save("examples/output/pyramid_3.html")

    # ---- 示例 4：深色主题与标签开关 ----
    on = edv.pyramid(df, names="渠道", values="利润", theme="dark", labels=True)
    on.save("examples/output/pyramid_4.html")
    off = edv.pyramid(df, names="渠道", values="利润", theme="dark", labels=False)
    off.save("examples/output/pyramid_5.html")

    # ---- 示例 5：联动：点击漏斗层过滤明细 ----
    funnel = edv.pyramid(df, names="产品", values="销售额", link="p1")
    tbl = edv.table(df, columns=["产品", "渠道", "销售额"], link="p1", limit=30)
    edv.dashboard(funnel, tbl, title="产品结构联动", cols=2).save("examples/output/pyramid_6.html")

if __name__ == "__main__":
    main()
    print("OK pyramid")
