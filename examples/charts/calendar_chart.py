# -*- coding: utf-8 -*-
"""calendar（日历热力图）完整示例：5 个用法，覆盖最简/典型/进阶参数/边界/联动/配色。

运行方式（在仓库根目录）：

    cd F:/deepseek/eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/calendar_chart.py

输出：examples/output/calendar_*.html（每个文件都是可离线打开的独立页面）。
"""

import os
import sys

# 直接运行本文件时 sys.path[0] 是 examples/charts；早期同目录里的 calendar.py
# 会遮蔽标准库 calendar，导致 pandas 导入失败。文件已改名为 calendar_chart.py，
# 这里保留 shim 以兼容在其它目录内联运行的情况。
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path
              if os.path.abspath(p or os.getcwd()) != _HERE]

import pandas as pd

import eazy_data_viz as edv


def main():
    df = edv.sample_df()
    print("数据：%d 行 × %d 列" % (df.shape[0], df.shape[1]))


    # ---- 示例 1：最简：全年订单热力 ----
    chart = edv.calendar(df, date="日期", value="订单数")
    chart.save("examples/output/calendar_1.html")

    # ---- 示例 2：典型：按记录条数着色 ----
    chart = edv.calendar(df, date="日期", title="每日记录条数", height=320)
    chart.save("examples/output/calendar_2.html")

    # ---- 示例 3：进阶：先聚合再画 + 数值格式 ----
    daily = (
        df.groupby("日期", as_index=False)
          .agg(销售额=("销售额", "sum"))
    )
    chart = edv.calendar(
        daily,
        date="日期",
        value="销售额",
        fmt="thousands",
        title="每日销售额",
        height=340,
    )
    chart.save("examples/output/calendar_3.html")

    # ---- 示例 4：深色主题与配色 ----
    chart = edv.calendar(df, date="日期", value="客户数", theme="dark")
    chart.palette("carbon")
    chart.save("examples/output/calendar_4.html")

    # ---- 示例 5：看板：日历 + 明细表 ----
    cal = edv.calendar(df, date="日期", value="订单数", title="每日订单")
    top = df.nlargest(30, "订单数")[["日期", "大区", "产品", "订单数"]]
    tbl = edv.table(top, columns=["日期", "大区", "产品", "订单数"], limit=30)
    edv.dashboard(cal, tbl, title="日历看板", cols=1).save("examples/output/calendar_5.html")

if __name__ == "__main__":
    main()
    print("OK calendar")
