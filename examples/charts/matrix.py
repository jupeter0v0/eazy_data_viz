# -*- coding: utf-8 -*-
"""matrix（相关系数矩阵）完整示例：5 个用法，覆盖最简/典型/进阶参数/边界/联动/配色。

运行方式（在仓库根目录）：

    cd F:/deepseek/eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/matrix.py

输出：examples/output/matrix_*.html（每个文件都是可离线打开的独立页面）。
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


    # ---- 示例 1：最简：自动选全部数值列 ----
    chart = edv.matrix(df)
    chart.save("examples/output/matrix_1.html")

    # ---- 示例 2：典型：显式指定指标与顺序 ----
    chart = edv.matrix(
        df,
        columns=["销售额", "订单数", "利润", "客户数"],
        title="核心指标相关性",
        subtitle="Pearson · 保留两位小数",
    )
    chart.save("examples/output/matrix_2.html")

    # ---- 示例 3：进阶：只保留 3 个指标 ----
    chart = edv.matrix(df, columns=["销售额", "利润", "客户数"], height=380)
    chart.save("examples/output/matrix_3.html")

    # ---- 示例 4：自动截断：`max_cols` 限制列数 ----
    chart = edv.matrix(df, max_cols=3, title="只取前 3 个数值列")
    chart.save("examples/output/matrix_4.html")

    # ---- 示例 5：深色主题与配色 ----
    chart = edv.matrix(df, theme="dark")
    chart.palette("tableau")
    chart.save("examples/output/matrix_5.html")

if __name__ == "__main__":
    main()
    print("OK matrix")
