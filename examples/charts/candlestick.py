# -*- coding: utf-8 -*-
"""candlestick（K 线图）完整示例：4 个用法，覆盖最简/典型/进阶参数/边界/联动/配色。

运行方式（在仓库根目录）：

    cd F:/deepseek/eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/candlestick.py

输出：examples/output/candlestick_*.html（每个文件都是可离线打开的独立页面）。
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


    # ---- 示例 1：最简：周线 OHLC ----
    ohlc = (
        df.set_index("日期")["销售额"]
          .resample("W")
          .agg(["first", "max", "min", "last"])
          .dropna()
          .reset_index()
    )
    ohlc.columns = ["日期", "开盘", "最高", "最低", "收盘"]
    chart = edv.candlestick(
        ohlc,
        date="日期",
        open="开盘",
        high="最高",
        low="最低",
        close="收盘",
    )
    chart.save("examples/output/candlestick_1.html")

    # ---- 示例 2：典型：手工构造 5 期 OHLC ----
    data = pd.DataFrame({
        "日期": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]),
        "开盘": [100, 103, 101, 105, 104],
        "最高": [104, 106, 104, 108, 106],
        "最低": [99, 100, 98, 103, 101],
        "收盘": [103, 101, 104, 104, 102],
    })
    chart = edv.candlestick(
        data,
        date="日期",
        open="开盘",
        high="最高",
        low="最低",
        close="收盘",
        title="5 日 K 线",
        height=380,
    )
    chart.save("examples/output/candlestick_2.html")

    # ---- 示例 3：进阶：强制缩放 + 轴标题 + 纵轴范围 ----
    ohlc = (
        df.set_index("日期")["订单数"]
          .resample("MS")
          .agg(["first", "max", "min", "last"])
          .dropna()
          .reset_index()
    )
    ohlc.columns = ["日期", "开盘", "最高", "最低", "收盘"]
    chart = edv.candlestick(
        ohlc,
        date="日期",
        open="开盘",
        high="最高",
        low="最低",
        close="收盘",
        xtitle="月份",
        ytitle="订单数",
        ylim=(0, 300),
        zoom=True,
        title="月度订单 K 线",
    )
    chart.save("examples/output/candlestick_3.html")

    # ---- 示例 4：边界：数据量 >30 自动缩放，只显示最后一段 ----
    ohlc = (
        df.set_index("日期")["客户数"]
          .resample("D")
          .agg(["first", "max", "min", "last"])
          .dropna()
          .reset_index()
    )
    ohlc.columns = ["日期", "开盘", "最高", "最低", "收盘"]
    chart = edv.candlestick(ohlc, date="日期", open="开盘", high="最高", low="最低", close="收盘",
                            title="日线（自动缩放）")
    chart.save("examples/output/candlestick_4.html")

if __name__ == "__main__":
    main()
    print("OK candlestick")
