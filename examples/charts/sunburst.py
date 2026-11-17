# -*- coding: utf-8 -*-
"""sunburst（旭日图）完整示例：5 个用法，覆盖最简/典型/进阶参数/边界/联动/配色。

运行方式（在仓库根目录）：

    cd F:/deepseek/eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/sunburst.py

输出：examples/output/sunburst_*.html（每个文件都是可离线打开的独立页面）。
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


    # ---- 示例 1：最简两层旭日图 ----
    chart = edv.sunburst(df, path=["大区", "省份"], value="销售额")
    chart.save("examples/output/sunburst_1.html")

    # ---- 示例 2：典型：产品 → 渠道三层结构 ----
    chart = edv.sunburst(
        df,
        path=["产品", "渠道"],
        value="订单数",
        title="产品 × 渠道 层级占比",
        height=520,
    )
    chart.save("examples/output/sunburst_2.html")

    # ---- 示例 3：进阶：三层下钻到城市 ----
    chart = edv.sunburst(
        df,
        path=["大区", "省份", "城市"],
        value="销售额",
        title="大区 → 省份 → 城市",
        height=620,
    )
    chart.save("examples/output/sunburst_3.html")

    # ---- 示例 4：不传数值：按记录条数决定角度 ----
    chart = edv.sunburst(df, path=["渠道", "产品"], title="渠道 × 产品 记录结构")
    chart.save("examples/output/sunburst_4.html")

    # ---- 示例 5：深色主题 + 自定义配色 ----
    chart = edv.sunburst(df, path=["大区", "产品"], value="销售额", theme="dark")
    chart.palette("echarts")
    chart.save("examples/output/sunburst_5.html")

if __name__ == "__main__":
    main()
    print("OK sunburst")
