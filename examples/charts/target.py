# -*- coding: utf-8 -*-
"""
target —— 目标对比图示例（柱 = 实际，虚线 = 目标）
================================================================
本脚本演示 eazy_data_viz.target 的常用写法：固定目标 target_value、
逐类目标列 target、图例开关、数值标签、排序/截断、ylim 数值轴、
轴标题、主题、下钻与联动，以及“缺目标/负数/单行”等边界。

运行方式（Windows）：
    cd F:\\deepseek\\eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples\\charts\\target.py

输出：examples/output/target_*.html
"""
from __future__ import print_function

import os

import sys


# 直接运行本文件时，sys.path[0] 是 examples/charts；该目录里的 calendar.py
# 会遮蔽标准库 calendar，导致 pandas 导入失败。这里在导入 pandas 前移除它。
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path
              if os.path.abspath(p or os.getcwd()) != _HERE]

import pandas as pd

import eazy_data_viz as edv

OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "output"))
os.makedirs(OUT_DIR, exist_ok=True)


def out(name):
    """拼出 examples/output/ 下的绝对路径。"""
    return os.path.join(OUT_DIR, name)


df = edv.sample_df()
# 逐类目标列：每个城市的目标 = 该城市销售额 × 1.08
df["城市目标"] = df.groupby("城市")["销售额"].transform("sum") * 1.08


# ---- 示例 1：最简：固定目标（target_value），柱为实际值，虚线为目标 ----
c1 = edv.target(df, x="大区", actual="销售额", target_value=480000)
c1.save(out("target_1.html"))
# 输出：4 根实际柱 + 一条 48 万的虚线；图例默认显示「实际 / 目标」

# ---- 示例 2：逐类目标：target 传列名，按同一 agg 聚合后逐类对比 ----
c2 = edv.target(df, x="城市", actual="销售额", target="城市目标",
                title="城市销售额 vs 城市目标")
c2.save(out("target_2.html"))
# 输出：每个城市一根柱 + 该城市自己的目标虚线点

# ---- 示例 3：高度与深色主题 ----
c9 = edv.target(df, x="大区", actual="销售额", target_value=500000,
                height=440, theme="dark", title="目标对比（深色）")
c9.save(out("target_3.html"))
# 输出：深色背景，目标虚线为浅灰，图例文字为浅色

# ---- 示例 4：下钻 + 联动 ----
c10 = edv.target(df, x="大区", actual="销售额", target_value=500000,
                 drill=["大区", "省份", "城市"], link="g2", title="可下钻的目标图")
b2 = edv.bar(df, x="大区", y="销售额", link="g2", title="同组柱图")
edv.dashboard(c10, b2, cols=2, title="目标图 + 柱图联动").save(out("target_4.html"))
# 输出：点击柱图筛选大区后，目标图只显示该大区；点击目标柱可下钻

# ---- 示例 5：边界：不给目标（target 与 target_value 都为空 → 目标线在 0） ----
c11 = edv.target(df, x="大区", actual="销售额", title="没有目标值")
c11.save(out("target_5.html"))
# 输出：目标虚线贴着 0 轴，tooltip 达成率为 0（目标为 0 时不显示达成率）

print("OK target")
