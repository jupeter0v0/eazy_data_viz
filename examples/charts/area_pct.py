# -*- coding: utf-8 -*-
"""area_pct 百分比堆叠面积图 完整示例。

百分比堆叠面积图和 bar_pct 表达同一件事（每个 x 归一化到 100%），
区别是 x 轴连续时用面积更强调「趋势」：各分组的份额随时间怎么此消彼长。
典型用途：月度渠道份额、季度产品结构、区域占比的连续演变。

运行方式（Windows / PowerShell 或 CMD 均可）：
    cd F:\\deepseek\\eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/area_pct.py

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

# 时间序列演示：把 2024 年的日期切成月份（月份列本身是有序分类 1月..12月）
df["月"] = df["月份"].astype(str)
print("数据行数：", len(df), "月份数：", df["月"].nunique())


# ---- 示例 1：最简用法 —— 各月销售额的产品结构（面积堆叠到 100%） ----
#   x=时间/类目轴，y=数值，color=构成分组。
# ==========================================================================
chart = edv.area_pct(df, x="月", y="销售额", color="产品")
chart.save(out("area_pct_1.html"))

# ---- 示例 2：sort="desc" —— 按类目总量排序（面积图里常用于把大区从多到少排开） ----
chart = edv.area_pct(df, x="大区", y="销售额", color="产品", sort="desc")
chart.save(out("area_pct_2.html"))

# ---- 示例 3：边界 —— 只有 1 个分组时，占比恒为 100% ----
east = df[df["大区"] == "华东"]
chart = edv.area_pct(east, x="月", y="销售额", color="大区", title="单分组（恒 100%）")
chart.save(out("area_pct_3.html"))

# ---- 示例 4：深色主题 + 单图配色 ----
chart = edv.area_pct(
    df, x="月", y="销售额", color="产品", theme="dark", height=420,
    title="产品结构演变（深色）",
)
chart.palette("echarts")
chart.save(out("area_pct_4.html"))

# ---- 示例 5：与百分比堆叠柱组合成看板 ----
c1 = edv.area_pct(df, x="月", y="销售额", color="产品", height=380)
c2 = edv.bar_pct(df, x="月", y="销售额", color="产品", height=380)
dash = edv.dashboard(c1, c2, cols=2, title="产品结构：面积 vs 柱状")
dash.save(out("area_pct_14_dashboard.html"))

print("OK area_pct")
