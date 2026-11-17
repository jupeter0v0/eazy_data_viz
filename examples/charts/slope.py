# -*- coding: utf-8 -*-
"""slope 斜率图 完整示例。

斜率图把「两个期别」放在 x 轴两端，每个类目画一条连线：
线上翘 = 增长，线下滑 = 下降，斜率越大变化越剧烈。
典型用途：去年→今年、上期→本期、改版前→改版后的排名/份额/指标变化。

运行方式（Windows / PowerShell 或 CMD 均可）：
    cd F:\\deepseek\\eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/slope.py

所有图表保存到 examples/output/，单图内联 HTML 约 1.2MB，可直接双击打开。
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

OUT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "output")
)


def out(name):
    """拼接 examples/output/ 下的输出路径。"""
    return os.path.join(OUT_DIR, name)


df = edv.sample_df()

# slope 的 color 列应当恰好有两个取值（期别）。这里取 1 月和 2 月两期数据，
# 并把月份列复制成「期别」列，避免直接拿 12 个月的月份列（会被截断并给出 warning）。
two = df[df["月份"].isin(["1月", "2月"])].copy()
two["期别"] = two["月份"].astype(str)
print("两期数据行数：", len(two), "期别取值：", sorted(two["期别"].unique()))


# ---- 示例 1：最简用法 —— 产品销售额从 1 月到 2 月的变化 ----
#   color 传「期别」列，前端按该列的两个取值作为 x 轴两端。
# ==========================================================================
chart = edv.slope(two, x="产品", y="销售额", color="期别")
chart.save(out("slope_1.html"))

# ---- 示例 2：period 显式指定两期（颜色列有更多取值时只对比指定的两期） ----
#   注意：period 只决定 x 轴两端与 writes spec.arms，数据本身仍建议先过滤。
# ==========================================================================
chart = edv.slope(
    two, x="城市", y="销售额", color="期别", period=["1月", "2月"], sort="desc"
)
chart.save(out("slope_2.html"))

# ---- 示例 3：类目多于 6 个时图例自动隐藏（城市 10 个，legend 不会挤占画布） ----
chart = edv.slope(
    two, x="城市", y="订单数", color="期别", legend=True, labels=False
)
chart.save(out("slope_3.html"))

# ---- 示例 4：深色主题 + 单图配色 ----
chart = edv.slope(
    two, x="产品", y="销售额", color="期别", theme="dark", labels=True,
    title="产品销售额变化（深色）",
)
chart.palette("antd")
chart.save(out("slope_4.html"))

# ---- 示例 5：与哑铃图组合成看板 ----
c1 = edv.slope(two, x="产品", y="销售额", color="期别", labels=True)
c2 = edv.dumbbell(
    df[df["月份"] == "1月"].groupby("产品", as_index=False)["订单数"].sum().rename(
        columns={"订单数": "1月订单数"}
    ),
    x="产品",
    y1="1月订单数",
    y2="1月订单数",
    title="单期订单数",
)
dash = edv.dashboard(c1, c2, cols=2, title="变化与对比")
try:
    dash.save(out("slope_13_dashboard.html"))
except Exception as exc:  # 组合图失败不影响前面示例
    print("5 [提示] 看板未生成 ->", exc)

print("OK slope")
