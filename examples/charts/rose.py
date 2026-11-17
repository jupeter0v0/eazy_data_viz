# -*- coding: utf-8 -*-
"""rose（南丁格尔玫瑰图）完整示例：5 个用法，覆盖最简/典型/进阶参数/边界/联动/配色。

运行方式（在仓库根目录）：

    cd F:/deepseek/eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/rose.py

输出：examples/output/rose_*.html（每个文件都是可离线打开的独立页面）。
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


    # ---- 示例 1：最简玫瑰图 ----
    chart = edv.rose(df, names="大区", values="销售额")
    chart.save("examples/output/rose_1.html")

    # ---- 示例 2：典型用法：产品线订单结构 ----
    chart = edv.rose(
        df,
        names="产品",
        values="订单数",
        title="四大产品线订单结构",
        subtitle="按订单数汇总 · 2024 年",
    )
    chart.save("examples/output/rose_2.html")

    # ---- 示例 3：进阶：只保留前 5 名并合并“其他” ----
    chart = edv.rose(
        df,
        names="省份",
        values="销售额",
        sort="desc",
        top_n=5,
        labels=False,
    )
    chart.save("examples/output/rose_3.html")

    # ---- 示例 4：深色主题 + 单图配色 ----
    chart = edv.rose(df, names="产品", values="订单数", theme="dark")
    chart.palette("morandi")
    chart.save("examples/output/rose_4.html")

    # ---- 示例 5：联动：点击扇区过滤明细表 ----
    rose = edv.rose(df, names="大区", values="销售额", link="g1")
    tbl = edv.table(df, columns=["大区", "产品", "销售额"], link="g1", limit=50)
    edv.dashboard(rose, tbl, title="玫瑰图联动明细", cols=2).save("examples/output/rose_5.html")

if __name__ == "__main__":
    main()
    print("OK rose")
