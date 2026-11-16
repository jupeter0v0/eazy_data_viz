# -*- coding: utf-8 -*-
"""bump 排名变化图 完整示例。

bump chart 把 y 轴变成「排名」：每个 group 一条折线，线往上走 = 名次上升。
它只关心相对位置，不关心绝对数值大小，适合看多个对象在时间上的此消彼长。
注意：排名是每个 x（时间点）内按 y 值从大到小重新计算，y 轴 1 在顶部。

运行方式（Windows / PowerShell 或 CMD 均可）：
    cd F:\\deepseek\\eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/bump.py

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
print("数据行数：", len(df), "月份数：", df["月份"].nunique(), "产品：", df["产品"].unique())


# ---- 示例 1：最简用法 —— 4 个产品在 12 个月里的销售额排名变化 ----
#   x=时间列，y=数值列，group=参与排名的分组列（必填，且没有默认值）。
# ==========================================================================
chart = edv.bump(df, x="月份", y="销售额", group="产品")
chart.save(out("bump_1.html"))

# ---- 示例 2：换分组 —— 四大区销售额排名变化 ----
chart = edv.bump(df, x="月份", y="销售额", group="大区")
chart.save(out("bump_2.html"))

# ---- 示例 3：边界 —— 只有一个时间点（每条线只有一个点，排名仍会画出） ----
one = df[df["月份"] == "3月"]
chart = edv.bump(one, x="月份", y="销售额", group="产品", title="仅 3 月（单点边界）")
chart.save(out("bump_3.html"))

# ---- 示例 4：深色主题 + 单图配色 ----
chart = edv.bump(df, x="月份", y="份额", group="产品") if "份额" in df.columns else edv.bump(
    df, x="月份", y="销售额", group="产品", theme="dark", title="产品排名变化（深色）"
)
chart.palette("tableau")
chart.save(out("bump_4.html"))

# ---- 示例 5：与斜率图组合成看板 ----
two = df[df["月份"].isin(["1月", "2月"])].copy()
two["期别"] = two["月份"].astype(str)
c1 = edv.bump(df, x="月份", y="销售额", group="产品")
c2 = edv.slope(two, x="产品", y="销售额", color="期别")
dash = edv.dashboard(c1, c2, cols=2, title="排名变化 + 两期变化")
dash.save(out("bump_14_dashboard.html"))

print("OK bump")
