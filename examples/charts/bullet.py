# -*- coding: utf-8 -*-
"""
bullet —— 子弹图示例（实际值 vs 目标，横向）
================================================================
本脚本演示 eazy_data_viz.bullet 的常用写法：每个类目一条实际值横条，
目标用刻度线标出；支持固定目标 target_value、逐类目标列 target、
排序/截断、数值格式、xlim 控制数值轴、下钻与联动。

运行方式（Windows）：
    cd F:\\deepseek\\eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples\\charts\\bullet.py

输出：examples/output/bullet_*.html
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

# 为「逐类目标」示例准备一列目标值：每个大区的目标 = 该大区销售额 × 1.1
df["目标额"] = df.groupby("大区")["销售额"].transform("sum") * 1.1


# ---- 示例 1：最简：所有类目共用一个固定目标（target_value） ----
c1 = edv.bullet(df, x="大区", actual="销售额", target_value=500000)
c1.save(out("bullet_1.html"))
# 输出：4 条横向实际条，每条右侧有一条竖线刻度代表 50 万的目标

# ---- 示例 2：逐类目标：target 传「列名」，按同一 agg 聚合后逐个类目对比 ----
c2 = edv.bullet(df, x="大区", actual="销售额", target="目标额", title="大区销售额 vs 目标")
c2.save(out("bullet_2.html"))
# 输出：每条第目标刻度不同（目标额 = 该大区销售额 × 1.1），全部未达标

# ---- 示例 3：数值格式：fmt='currency' 货币（也支持 thousands / raw / compact / percent） ----
c4 = edv.bullet(df, x="产品", actual="销售额", target_value=450000,
                fmt="currency", title="产品销售额（货币格式）")
c4.save(out("bullet_3.html"))
# 输出：tooltip 中的实际值/目标值带 ¥ 前缀，坐标轴刻度同样按货币缩写

# ---- 示例 4：高度与深色主题 ----
c8 = edv.bullet(df, x="大区", actual="利润", target_value=200000,
                height=440, theme="dark", title="大区利润（深色）")
c8.save(out("bullet_4.html"))
# 输出：深色页面、440px 高，目标刻度线为浅色

# ---- 示例 5：下钻 + 联动：drill 逐级下钻，link 与同页柱图共享筛选 ----
c9 = edv.bullet(df, x="大区", actual="销售额", target_value=500000,
                drill=["大区", "省份", "城市"], link="g1", title="可下钻的子弹图")
b1 = edv.bar(df, x="大区", y="销售额", link="g1", title="同组柱图")
edv.dashboard(c9, b1, cols=2, title="子弹图 + 柱图联动").save(out("bullet_5.html"))
# 输出：点击柱图的大区，子弹图只看该大区；点击子弹图可继续下钻到省份/城市

print("OK bullet")
