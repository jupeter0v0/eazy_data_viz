# -*- coding: utf-8 -*-
"""
group_kpi —— KPI 卡片组示例（HTML 渲染，一排指标卡片）
================================================================
本脚本演示 eazy_data_viz.group_kpi 的常用写法：分组聚合、手工 items、
涨跌 delta、单位 unit、数值格式 fmt、排序与截断 top_n、深浅主题，
以及在 dashboard 中与其它图表组合使用。

运行方式（Windows）：
    cd F:\\deepseek\\eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples\\charts\\group_kpi.py

输出：examples/output/group_kpi_*.html（每个文件约 1.2 MB，单文件可双击打开）
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

# examples/charts/ 的上一级就是 examples/，输出统一放到 examples/output/
OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "output"))
os.makedirs(OUT_DIR, exist_ok=True)


def out(name):
    """拼出 examples/output/ 下的绝对路径。"""
    return os.path.join(OUT_DIR, name)


df = edv.sample_df()  # 1500 行演示数据


# ---- 示例 1：最简：按「大区」分组，把「销售额」求和后排成一排卡片 ----
c1 = edv.group_kpi(df, names="大区", values="销售额")
c1.save(out("group_kpi_1.html"))
# 输出：4 张卡片（华东 / 华北 / 华南 / 西部），数值按 compact（万）显示，默认降序

# ---- 示例 2：标题、副标题、自定义高度（height 最小 120） ----
c2 = edv.group_kpi(
    df, names="大区", values="销售额",
    title="2024 年大区销售概况",
    subtitle="数据来源：sample_df（2024 全年）",
    height=160,
)
c2.save(out("group_kpi_2.html"))
# 输出：卡片组上方出现标题和副标题

# ---- 示例 3：同比/环比：delta 传「百分数数值」，不是小数 ----
#    delta=12.8 显示「▲ 12.8%」；delta=-5.2 显示「▼ 5.2%」
# ------------------------------------------------------------------
c3 = edv.group_kpi(
    df, names="大区", values="销售额",
    delta=[12.8, -5.2, 8.0, 0.4],   # 按卡片顺序逐个覆盖；标量则只改第 1 张
    title="大区销售额环比",
    subtitle="delta 传入的是百分比数值（12.8 = 12.8%）",
)
c3.save(out("group_kpi_3.html"))
# 输出：每张卡片底部出现 ▲/▼ 与百分比，正数偏绿、负数偏红

# ---- 示例 4：深色主题：theme='dark' ----
c10 = edv.group_kpi(
    df, names="大区", values="利润",
    theme="dark", title="大区利润（深色）",
)
c10.save(out("group_kpi_4.html"))
# 输出：深色卡片底、浅色文字，适合大屏/驾驶舱

# ---- 示例 5：边界：单行数据也能画（一张卡片） ----
one = df[df["大区"] == "华东"].head(1)
c11 = edv.group_kpi(one, names="大区", values="销售额", title="单行数据")
c11.save(out("group_kpi_5.html"))
# 输出：只有一张「华东」卡片

print("OK group_kpi")
