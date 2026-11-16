# -*- coding: utf-8 -*-
"""
progress —— 进度条列表示例（HTML 渲染）
================================================================
本脚本演示 eazy_data_viz.progress 的常用写法：按分类聚合后画「名称 +
数值 + 进度条」列表，支持自定义上限 max、排序 sort、截断 top_n、
数值格式 fmt、深浅主题以及同页联动 link。

运行方式（Windows）：
    cd F:\\deepseek\\eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples\\charts\\progress.py

输出：examples/output/progress_*.html
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


# ---- 示例 1：最简：按渠道聚合销售额，默认降序、最多 10 行 ----
c1 = edv.progress(df, x="渠道", y="销售额")
c1.save(out("progress_1.html"))
# 输出：3 行进度条；最长的一条是该批最大值（默认 100%）

# ---- 示例 2：指定 max：按固定目标算百分比（max=600000 时 60 万=100%） ----
c2 = edv.progress(df, x="渠道", y="销售额", max=600000, title="渠道销售额完成度")
c2.save(out("progress_2.html"))
# 输出：每行右侧显示「数值 · 百分比」，百分比按 max 计算，超过 100% 会被截断

# ---- 示例 3：x 缺省：自动挑第一个分类/时间列（这里是「月份」） ----
c8 = edv.progress(df, y="销售额", title="自动选择 x（月份）")
c8.save(out("progress_3.html"))
# 输出：1~12 月各一行

# ---- 示例 4：标题 / 副标题 / 高度 / 深色主题 ----
c10 = edv.progress(
    df, x="大区", y="销售额",
    title="大区销售额进度",
    subtitle="按 sum 聚合 · 2024 全年",
    height=300,
    theme="dark",
)
c10.save(out("progress_4.html"))
# 输出：深色页面、300px 高的进度条列表

# ---- 示例 5：联动：link="g1" 的进度条与同页柱图共享筛选 ----
p = edv.progress(df, x="渠道", y="销售额", link="g1", title="渠道（联动）")
b = edv.bar(df, x="渠道", y="销售额", color="产品", link="g1", title="渠道 × 产品")
edv.dashboard(p, b, cols=2, title="进度条 + 柱图联动").save(out("progress_5.html"))
# 输出：点击柱图任一条，进度条随之过滤重算

print("OK progress")
