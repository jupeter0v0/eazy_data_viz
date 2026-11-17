# -*- coding: utf-8 -*-
"""
waterfall —— 瀑布图示例（增减拆解 / 累计变化）
================================================================
本脚本演示 eazy_data_viz.waterfall 的常用写法：把「增量项」逐段堆叠成
瀑布，直观看到每一项对总量的贡献；支持末尾「合计」柱 total、数值标签
labels、按值排序 sort、数值格式 fmt、ylim、下钻与联动。

运行方式（Windows）：
    cd F:\\deepseek\\eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples\\charts\\waterfall.py

输出：examples/output/waterfall_*.html
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

# 业务口径的增减项拆解数据：期初 + 各项增减 = 期末
wf = pd.DataFrame({
    "项目": ["期初收入", "新客增长", "老客复购", "客单价提升", "价格下调", "退款", "渠道费用"],
    "变化": [800000, 220000, 150000, 60000, -40000, -90000, -120000],
})


# ---- 示例 1：最简：按月份聚合利润画瀑布（每个月的利润作为一段增量） ----
c1 = edv.waterfall(df, x="月份", y="利润")
c1.save(out("waterfall_1.html"))
# 输出：12 段柱子，上涨段绿色、下跌段红色，柱子顶部对齐上一步的累计

# ---- 示例 2：典型业务场景：预算增减项拆解（自定义 DataFrame） ----
c3 = edv.waterfall(wf, x="项目", y="变化", total=True,
                   title="收入预算拆解", subtitle="期初 + 增减项 = 期末")
c3.save(out("waterfall_2.html"))
# 输出：期初 80 万逐段累加，新客/复购/提价向上，退款/渠道费用向下，最后是合计

# ---- 示例 3：ylim：固定数值轴范围（瀑布图的 ylim 生效，xlim 对类目轴无效） ----
c8 = edv.waterfall(wf, x="项目", y="变化", ylim=(0, 1200000), total=True,
                   title="数值轴 0~120 万")
c8.save(out("waterfall_3.html"))
# 输出：数值轴固定 0~120 万；为负的增量段会落到轴外/被裁剪

# ---- 示例 4：高度 + 深色主题 ----
c10 = edv.waterfall(wf, x="项目", y="变化", total=True, height=440,
                    theme="dark", title="瀑布图（深色）")
c10.save(out("waterfall_4.html"))
# 输出：深色背景，涨跌色与文字颜色自动适配

# ---- 示例 5：下钻 + 联动：drill 逐级下钻，link 与同页图表共享筛选 ----
c11 = edv.waterfall(df, x="大区", y="利润", total=True,
                    drill=["大区", "省份", "城市"], link="g3",
                    title="可下钻的瀑布图")
b3 = edv.bar(df, x="大区", y="利润", link="g3", title="同组柱图")
edv.dashboard(c11, b3, cols=2, title="瀑布图 + 柱图联动").save(out("waterfall_5.html"))
# 输出：点击柱图筛选大区后，瀑布图只显示该大区；点击瀑布柱可下钻

print("OK waterfall")
