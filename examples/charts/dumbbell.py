# -*- coding: utf-8 -*-
"""dumbbell 哑铃图 完整示例。

哑铃图用「两个点 + 一条连线」表示同一类目在两个时点/两组之间的差距：
线越长差距越大，看的是「变化」而不是单个绝对值。
典型用途：去年 vs 今年、期初 vs 期末、实际 vs 目标、两组人群对比。

运行方式（Windows / PowerShell 或 CMD 均可）：
    cd F:\\deepseek\\eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/dumbbell.py

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
print("数据行数：", len(df), "月份取值：", list(df["月份"].cat.categories))


def pick(month, dim, value, new_name):
    """从 sample_df 取某个月份，按 dim 聚合 value，并把数值列改名。"""
    sub = df[df["月份"] == month].groupby(dim, as_index=False)[value].sum()
    return sub.rename(columns={value: new_name})


# 两期数据：1 月 vs 2 月（同一批产品 / 城市 / 大区）
prod = pick("1月", "产品", "销售额", "1月销售额").merge(
    pick("2月", "产品", "销售额", "2月销售额"), on="产品"
)
print("产品两期数据：\n", prod)


# ---- 示例 1：最简用法 —— 产品的两期销售额 ----
#   y1、y2 必须是数值列；默认图例就是两个列名。
# ==========================================================================
chart = edv.dumbbell(prod, x="产品", y1="1月销售额", y2="2月销售额")
chart.save(out("dumbbell_1.html"))

# ---- 示例 2：城市维度 + 排序 + top_n（按第一个数值 y1 排序，desc 大→小） ----
city = pick("1月", "城市", "销售额", "1月销售额").merge(
    pick("2月", "城市", "销售额", "2月销售额"), on="城市"
)
chart = edv.dumbbell(city, x="城市", y1="1月销售额", y2="2月销售额", sort="desc", top_n=8)
chart.save(out("dumbbell_2.html"))

# ---- 示例 3：自定义系列名（series_names）—— 把列名换成「上期 / 本期」 ----
chart = edv.dumbbell(
    prod,
    x="产品",
    y1="1月销售额",
    y2="2月销售额",
    series_names=["上期（1月）", "本期（2月）"],
    title="产品销售额：上期 vs 本期",
)
chart.save(out("dumbbell_3.html"))

# ---- 示例 4：深色主题 + 单图配色 ----
chart = edv.dumbbell(
    prod,
    x="产品",
    y1="1月销售额",
    y2="2月销售额",
    theme="dark",
    labels=True,
    title="产品两期对比（深色）",
)
chart.palette("carbon")
chart.save(out("dumbbell_4.html"))

# ---- 示例 5：与棒棒糖图组合成看板 ----
c1 = edv.dumbbell(prod, x="产品", y1="1月销售额", y2="2月销售额", labels=True)
c2 = edv.lollipop(df, x="产品", y="订单数", sort="desc")
dash = edv.dashboard(c1, c2, cols=2, title="两期对比 + 排名")
dash.save(out("dumbbell_12_dashboard.html"))

print("OK dumbbell")
