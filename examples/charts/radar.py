# -*- coding: utf-8 -*-
"""radar 雷达图 完整示例。

雷达图把多个指标画成同一张「多边形」：指标越靠外、面积越大表示整体越强。
它适合「少量对象 × 少量指标」的综合对比（如产品力、区域能力评估）；
指标之间量纲不同时必须先归一化，否则某一个大数值指标会把其它指标压扁。

运行方式（Windows / PowerShell 或 CMD 均可）：
    cd F:\\deepseek\\eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/radar.py

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


def to_score(series):
    """min-max 归一化到 0~100（浮点，保留 1 位小数）。"""
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series([50.0] * len(series), index=series.index)
    return ((series - lo) / (hi - lo) * 100).round(1)


def make_radar_df(group_col):
    """按 group_col 聚合 4 个指标，并把每个指标归一化到 0~100。

    返回长表：对象 / 指标 / 得分，可直接喂给 edv.radar()。
    """
    wide = df.groupby(group_col, as_index=False).agg(
        销售额=("销售额", "sum"),
        订单数=("订单数", "sum"),
        利润=("利润", "sum"),
        客户数=("客户数", "sum"),
    )
    long = wide.melt(id_vars=group_col, var_name="指标", value_name="原始值")
    long["得分"] = long.groupby("指标")["原始值"].transform(to_score)
    return long[[group_col, "指标", "得分"]].rename(columns={group_col: "对象"})


df = edv.sample_df()
radar_prod = make_radar_df("产品")
print("产品雷达数据：\n", radar_prod.head(8))


# ---- 示例 1：最简用法 —— 4 个产品的 4 项指标综合对比 ----
#   x=指标项，y=数值，color=对比对象（每个对象一个多边形）。
# ==========================================================================
chart = edv.radar(radar_prod, x="指标", y="得分", color="对象")
chart.save(out("radar_1.html"))

# ---- 示例 2：固定指标轴上限（max=100，归一化后每个指标都撑满 0~100） ----
chart = edv.radar(radar_prod, x="指标", y="得分", color="对象", max=100)
chart.save(out("radar_2.html"))

# ---- 示例 3：top_n 截断指标（保留前 3 个指标，其余合并为「其他」） ----
chart = edv.radar(
    radar_prod, x="指标", y="得分", color="对象", top_n=3, max=100
)
chart.save(out("radar_3.html"))

# ---- 示例 4：深色主题 + 单图配色 ----
chart = edv.radar(
    radar_prod, x="指标", y="得分", color="对象", max=100,
    theme="dark", labels=True, title="产品能力雷达（深色）",
)
chart.palette("morandi")
chart.save(out("radar_4.html"))

# ---- 示例 5：与平行坐标组合成看板（都是「多维对比」类图表） ----
c1 = edv.radar(radar_prod, x="指标", y="得分", color="对象", max=100)
c2 = edv.parallel(
    df, ["销售额", "订单数", "利润", "客户数"], color="产品", height=380
)
dash = edv.dashboard(c1, c2, cols=2, title="多维对比：雷达 + 平行坐标")
dash.save(out("radar_12_dashboard.html"))

print("OK radar")
