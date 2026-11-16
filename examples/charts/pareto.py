# -*- coding: utf-8 -*-
"""
pareto —— 帕累托图示例（降序柱 + 累计占比折线）
================================================================
本脚本演示 eazy_data_viz.pareto 的常用写法：先按值降序排柱，再用累计
占比折线找出「贡献 80% 的关键少数」；支持 top_n 截断、cum_fmt 控制
tooltip 累计显示口径、labels、sort、fmt、ylim、下钻与联动。

运行方式（Windows）：
    cd F:\\deepseek\\eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples\\charts\\pareto.py

输出：examples/output/pareto_*.html
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


# ---- 示例 1：最简：产品销售额帕累托（柱按值降序，折线是累计占比） ----
c1 = edv.pareto(df, x="产品", y="销售额")
c1.save(out("pareto_1.html"))
# 输出：4 根降序柱 + 一条从低到高的累计占比折线（右轴 0~100%）

# ---- 示例 2：典型场景：城市销售额，找贡献 80% 的关键城市 ----
c2 = edv.pareto(df, x="城市", y="销售额", top_n=10,
                title="城市销售额帕累托", subtitle="折线 = 累计占比")
c2.save(out("pareto_2.html"))
# 输出：城市按销售额降序排列，折线前几项迅速抬升，说明头部集中

# ---- 示例 3：高度 + 深色主题 ----
c10 = edv.pareto(df, x="城市", y="销售额", height=460, theme="dark",
                 title="帕累托图（深色）")
c10.save(out("pareto_3.html"))
# 输出：深色背景，累计折线用主题第 4 色

# ---- 示例 4：下钻 + 联动 ----
c11 = edv.pareto(df, x="大区", y="销售额", drill=["大区", "省份", "城市"],
                 link="g5", title="可下钻的帕累托图")
b5 = edv.bar(df, x="大区", y="销售额", link="g5", title="同组柱图")
edv.dashboard(c11, b5, cols=2, title="帕累托 + 柱图联动").save(out("pareto_4.html"))
# 输出：点击柱图筛选大区，帕累托图只对该大区重算

# ---- 示例 5：边界：单行数据（累计占比恒 100%） ----
one = df[df["产品"] == "智能终端"]
c12 = edv.pareto(one, x="产品", y="销售额", title="单类目")
c12.save(out("pareto_5.html"))
# 输出：一根柱 + 一个 100% 的点

print("OK pareto")
