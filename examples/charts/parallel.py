# -*- coding: utf-8 -*-
"""parallel 平行坐标 完整示例。

平行坐标把每一行数据画成一条折线，每个数值列是一根纵向坐标轴：
线在维度间的交叉、聚拢能揭示多维分布、离群点和分组差异。
适合 Exploratory 分析，不适合精确读数；维度建议 3~8 个，行数太多时用 max_rows 采样。

运行方式（Windows / PowerShell 或 CMD 均可）：
    cd F:\\deepseek\\eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/parallel.py

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
NUMERIC = ["销售额", "订单数", "利润", "客户数"]
print("数值列：", NUMERIC, "行数：", len(df))

# 1500 行全画会糊成一片，演示时先抽样 200 行（生产环境可交给 max_rows 自动采样）
sample = df.sample(200, random_state=0)


# ---- 示例 1：最简用法 —— 四个数值维度的平行坐标 ----
#   dims 是数值列名列表，每个维度一根纵轴；每一行一条折线。
# ==========================================================================
chart = edv.parallel(sample, NUMERIC)
chart.save(out("parallel_1.html"))

# ---- 示例 2：按「产品」着色（color= 分组列，图例显示 4 个产品） ----
chart = edv.parallel(sample, NUMERIC, color="产品")
chart.save(out("parallel_2.html"))

# ---- 示例 3：错误用法 —— dims 为空 ----
try:
    edv.parallel(df, [])
except ValueError as exc:
    print("3 [预期错误] 空 dims ->", exc)

# ---- 示例 4：深色主题 + 单图配色 ----
chart = edv.parallel(
    sample, NUMERIC, color="渠道", theme="dark", height=460,
    title="渠道多维分布（深色）",
)
chart.palette("carbon")
chart.save(out("parallel_3.html"))

# ---- 示例 5：与雷达图组合成看板 ----
two = df[df["月份"].isin(["1月", "2月"])].copy()
two["期别"] = two["月份"].astype(str)
c1 = edv.parallel(sample, NUMERIC, color="产品", height=380)
c2 = edv.slope(two, x="产品", y="销售额", color="期别", height=380)
dash = edv.dashboard(c1, c2, cols=2, title="多维分布 + 两期变化")
dash.save(out("parallel_12_dashboard.html"))

print("OK parallel")
