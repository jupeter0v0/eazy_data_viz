# -*- coding: utf-8 -*-
"""
pictorial —— 象形柱图示例（用图形符号重复堆叠出柱高）
================================================================
本脚本演示 eazy_data_viz.pictorial 的常用写法：把数值画成一列重复的
小图形（circle / rect / roundRect / diamond / triangle），符号大小随
height 自适应；支持排序/截断、labels、fmt、ylim、主题、下钻与联动。

运行方式（Windows）：
    cd F:\\deepseek\\eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples\\charts\\pictorial.py

输出：examples/output/pictorial_*.html
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


# ---- 示例 1：最简：产品销售额画成圆形符号柱（symbol 默认 circle） ----
c1 = edv.pictorial(df, x="产品", y="销售额")
c1.save(out("pictorial_1.html"))
# 输出：每个产品一列小圆点，圆点堆得越高表示销售额越大；顶部默认显示数值

# ---- 示例 2：排序 + 截断：sort='desc' 按值降序，top_n 只保留前 N 类 ----
c7 = edv.pictorial(df, x="城市", y="销售额", sort="desc", top_n=6,
                   title="城市销售额 TOP 6")
c7.save(out("pictorial_2.html"))
# 输出：只显示 6 个城市，按销售额从高到低

# ---- 示例 3：ylim：固定数值轴范围（xlim 对类目轴无效） ----
c9 = edv.pictorial(df, x="产品", y="销售额", ylim=(0, 600000),
                   title="数值轴 0~60 万")
c9.save(out("pictorial_3.html"))
# 输出：数值轴固定 0~60 万

# ---- 示例 4：高度与主题：符号大小 = clamp(height/26, 7~18) 像素，height 变了符号也变 ----
c10 = edv.pictorial(df, x="产品", y="销售额", height=300, theme="dark",
                    title="高 300px（符号更小）")
c10.save(out("pictorial_4.html"))
# 输出：深色页面，符号尺寸比默认 380 时更小一些

c11 = edv.pictorial(df, x="产品", y="销售额", height=520,
                    title="高 520px（符号更大）")
c11.save(out("pictorial_5.html"))
# 输出：符号尺寸接近上限 18px

# ---- 示例 5：下钻 + 联动 ----
c12 = edv.pictorial(df, x="大区", y="销售额", drill=["大区", "省份", "城市"],
                    link="g4", title="可下钻的象形柱图")
b4 = edv.bar(df, x="大区", y="销售额", link="g4", title="同组柱图")
edv.dashboard(c12, b4, cols=2, title="象形柱 + 柱图联动").save(out("pictorial_6.html"))
# 输出：点击柱图筛选，象形柱图跟随；点击象形柱可下钻

print("OK pictorial")
