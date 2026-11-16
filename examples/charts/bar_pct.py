# -*- coding: utf-8 -*-
"""bar_pct 百分比堆叠柱图 完整示例。

百分比堆叠柱把每个 x 上的各分组归一化到 100%：
看的是「结构/占比」，不是绝对量；跨 x 比较时也不会被总量差异带偏。
典型用途：各月产品结构、各大区渠道构成、各渠道客户等级占比。

运行方式（Windows / PowerShell 或 CMD 均可）：
    cd F:\\deepseek\\eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/bar_pct.py

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
print("数据行数：", len(df), "月份：", list(df["月份"].cat.categories)[:3], "...")
print("产品：", list(df["产品"].unique()), "渠道：", list(df["渠道"].unique()))


# ---- 示例 1：最简用法 —— 各月销售额的产品结构（每根柱 100%） ----
#   x=类目轴，y=数值，color=构成分组；每个 x 的 y 会被重新归一化为百分比。
# ==========================================================================
chart = edv.bar_pct(df, x="月份", y="销售额", color="产品")
chart.save(out("bar_pct_1.html"))

# ---- 示例 2：换聚合方式 agg="mean"（先按 (x, color) 求均值再归一化） ----
chart = edv.bar_pct(
    df, x="大区", y="利润", color="产品", agg="mean", fmt="currency"
)
chart.save(out("bar_pct_2.html"))

# ---- 示例 3：边界 —— 只有 1 个分组时，每根柱恒为 100% ----
east = df[df["大区"] == "华东"]
chart = edv.bar_pct(east, x="月份", y="销售额", color="大区", title="单分组（恒 100%）")
chart.save(out("bar_pct_3.html"))

# ---- 示例 4：深色主题 + 单图配色 ----
chart = edv.bar_pct(
    df, x="大区", y="销售额", color="产品", theme="dark", height=420,
    title="大区产品结构（深色）",
)
chart.palette("antd")
chart.save(out("bar_pct_4.html"))

# ---- 示例 5：与百分比堆叠面积图组合成看板 ----
c1 = edv.bar_pct(df, x="月份", y="销售额", color="渠道", height=380)
c2 = edv.area_pct(df, x="月份", y="销售额", color="渠道", height=380)
dash = edv.dashboard(c1, c2, cols=2, title="渠道结构：柱状 vs 面积")
dash.save(out("bar_pct_13_dashboard.html"))

print("OK bar_pct")
