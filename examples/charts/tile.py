# -*- coding: utf-8 -*-
"""
tile —— 瓦片图示例（HTML 渲染的方块矩阵）
================================================================
本脚本演示 eazy_data_viz.tile 的常用写法：按类目聚合后铺成方块，
方块颜色按数值深浅（主题 heat 色阶）自动着色；支持 values 缺省计数、
names 自动选择、agg 聚合、fmt 数值格式、深色主题与同页联动。

运行方式（Windows）：
    cd F:\\deepseek\\eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples\\charts\\tile.py

输出：examples/output/tile_*.html
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


# ---- 示例 1：最简：城市销售额铺成方块，数值越大颜色越深 ----
c1 = edv.tile(df, names="城市", values="销售额")
c1.save(out("tile_1.html"))
# 输出：8 个城市方块按销售额降序排列，颜色由浅到深

# ---- 示例 2：values 缺省：不传数值列 → 按行数计数 ----
c3 = edv.tile(df, names="渠道", title="各渠道记录数")
c3.save(out("tile_2.html"))
# 输出：三个渠道方块，数值为行数

# ---- 示例 3：聚合方式：agg='mean' 比较平均值 ----
c5 = edv.tile(df, names="产品", values="订单数", agg="mean",
              title="产品平均订单数")
c5.save(out("tile_3.html"))
# 输出：每个产品一个方块，值为平均订单数

# ---- 示例 4：高度与深色主题：深色底会自动用白字保证对比度 ----
c8 = edv.tile(df, names="城市", values="销售额", height=420, theme="dark",
              title="瓦片图（深色）")
c8.save(out("tile_4.html"))
# 输出：深色页面，浅色方块配深色文字、深色方块配白字

# ---- 示例 5：联动：link="g1" 与同页柱图共享筛选（tile 参与 filteredRows） ----
t1 = edv.tile(df, names="城市", values="销售额", link="g1", title="城市瓦片（联动）")
b1 = edv.bar(df, x="大区", y="销售额", link="g1", title="大区柱图")
edv.dashboard(t1, b1, cols=2, title="瓦片图 + 柱图联动").save(out("tile_5.html"))
# 输出：点击柱图的大区，瓦片图只保留该大区下的城市

print("OK tile")
