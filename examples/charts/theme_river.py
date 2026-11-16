# -*- coding: utf-8 -*-
"""theme_river（主题河流图）完整示例：5 个用法，覆盖最简/典型/进阶参数/边界/联动/配色。

运行方式（在仓库根目录）：

    cd F:/deepseek/eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/theme_river.py

输出：examples/output/theme_river_*.html（每个文件都是可离线打开的独立页面）。
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


    # ---- 示例 1：最简河流图：月份 × 产品 ----
    chart = edv.theme_river(df, x="月份", color="产品", value="销售额")
    chart.save("examples/output/theme_river_1.html")

    # ---- 示例 2：典型：按日期看渠道结构漂移 ----
    chart = edv.theme_river(
        df,
        x="日期",
        color="渠道",
        value="订单数",
        title="订单渠道结构演化",
        subtitle="2024 全年 · 逐日",
        height=420,
    )
    chart.save("examples/output/theme_river_2.html")

    # ---- 示例 3：进阶：排序 + 数值格式 + 高度 ----
    chart = edv.theme_river(
        df,
        x="月份",
        color="产品",
        value="销售额",
        sort="x",
        fmt="thousands",
        height=460,
    )
    chart.save("examples/output/theme_river_3.html")

    # ---- 示例 4：深色主题与配色 ----
    chart = edv.theme_river(df, x="月份", color="大区", value="客户数", theme="dark")
    chart.palette("morandi")
    chart.save("examples/output/theme_river_4.html")

    # ---- 示例 5：联动：点击色带过滤明细 ----
    river = edv.theme_river(df, x="月份", color="产品", value="销售额", link="r1")
    tbl = edv.table(df, columns=["月份", "产品", "销售额"], link="r1", limit=30)
    edv.dashboard(river, tbl, title="河流图联动", cols=2).save("examples/output/theme_river_5.html")

if __name__ == "__main__":
    main()
    print("OK theme_river")
