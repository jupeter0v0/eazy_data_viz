# -*- coding: utf-8 -*-
"""lollipop 棒棒糖图 完整示例。

棒棒糖图 = 一条细柱 + 顶端一个圆点，适合「一列类目、一个数值」的排名比较：
比横向条形图更轻、更聚焦，比饼图更精确；类目 5~12 个时观感最好。

运行方式（Windows / PowerShell 或 CMD 均可）：
    cd F:\\deepseek\\eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/lollipop.py

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


# sample_df() 共 1500 行，列：日期 月份 大区 省份 城市 产品 渠道 销售额 订单数 利润 客户数
df = edv.sample_df()
print("数据行数：", len(df), "列：", list(df.columns))


# ---- 示例 1：最简用法 —— 城市销售额 ----
chart = edv.lollipop(df, x="城市", y="销售额")
chart.save(out("lollipop_1.html"))

# ---- 示例 2：排序 + 只看前 6 名（sort="desc" 与 top_n 组合） ----
chart = edv.lollipop(df, x="城市", y="销售额", sort="desc", top_n=6)
chart.save(out("lollipop_2.html"))

# ---- 示例 3：边界 —— 空 DataFrame ----
#   注意 sample_df 里没有「杭州」，直接筛城市会得到 0 行，必须用真实取值。
# ==========================================================================
# 空表要分两种：数值列给 float64 才会走到「数据为空」；若给 object/text 会先报类型错误。
empty = pd.DataFrame(
    {"城市": pd.Series(dtype="object"), "销售额": pd.Series(dtype="float64")}
)
try:
    edv.lollipop(empty, x="城市", y="销售额")
except ValueError as exc:
    print("3 [预期错误] 空数据 ->", exc)

text_empty = pd.DataFrame(columns=["城市", "销售额"])
try:
    edv.lollipop(text_empty, x="城市", y="销售额")
except TypeError as exc:
    print("6b [预期错误] 空文本列 ->", exc)

# ---- 示例 4：深色主题（theme="dark"） ----
chart = edv.lollipop(
    df, x="渠道", y="销售额", theme="dark", labels=True, height=400
)
chart.save(out("lollipop_3.html"))

# ---- 示例 5：下钻（drill）—— 点击柱子会按「产品」维度继续展开 ----
chart = edv.lollipop(
    df, x="大区", y="销售额", drill="产品", labels=True, title="大区销售额（可下钻到产品）"
)
chart.save(out("lollipop_4.html"))

print("OK lollipop")
