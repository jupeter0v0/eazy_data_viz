# -*- coding: utf-8 -*-
"""
ring_progress —— 环形进度示例（单个数值，不接 DataFrame）
================================================================
本脚本演示 eazy_data_viz.ring_progress 的常用写法：完成率圆环、
自定义总量 max、中心数值格式 fmt、中心标签 label、高度与主题、
边界值（0 / 超额 / 负数）以及和 gauge、progress 的搭配。

运行方式（Windows）：
    cd F:\\deepseek\\eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples\\charts\\ring_progress.py

输出：examples/output/ring_progress_*.html
"""
from __future__ import print_function

import os

import sys


# 直接运行本文件时，sys.path[0] 是 examples/charts；该目录里的 calendar.py
# 会遮蔽标准库 calendar，导致 pandas 导入失败。这里在导入 pandas 前移除它。
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path
              if os.path.abspath(p or os.getcwd()) != _HERE]

import eazy_data_viz as edv

OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "output"))
os.makedirs(OUT_DIR, exist_ok=True)


def out(name):
    """拼出 examples/output/ 下的绝对路径。"""
    return os.path.join(OUT_DIR, name)


df = edv.sample_df()


# ---- 示例 1：最简：72.5% 的完成率圆环（percent 是「完成值」，max 默认 100） ----
c1 = edv.ring_progress(72.5)
c1.save(out("ring_progress_1.html"))
# 输出：圆环填充 72.5%，中心大字显示 72.5%

# ---- 示例 2：自定义总量 max：percent=3、max=8 表示 8 个里完成 3 个（37.5%） ----
c3 = edv.ring_progress(3, max=8, label="8 项任务完成 3 项")
c3.save(out("ring_progress_2.html"))
# 输出：圆环填充 37.5%；tooltip 显示「完成 3 / 占比 37.5%」

# ---- 示例 3：深色主题：theme='dark' ----
c7 = edv.ring_progress(64, label="服务 SLA", theme="dark", title="SLA 达成")
c7.save(out("ring_progress_3.html"))
# 输出：深色背景 + 浅色圆环，中心文字为浅色

# ---- 示例 4：与 gauge / progress 组合成一张小看板 ----
r1 = edv.ring_progress(72.5, label="销售完成率", height=240)
g1 = edv.gauge(19.9, label="利润率", min=0, max=40, fmt="percent", height=240)
p1 = edv.progress(df, x="渠道", y="销售额", max=600000, title="渠道进度", height=240)
edv.dashboard(r1, g1, p1, cols=3, title="指标看板").save(out("ring_progress_4.html"))
# 输出：一页三个指标组件并排展示

# ---- 示例 5：语义说明：percent 是「完成值」而不是百分比，占比 = percent / max ----
#     想画 72.5% 可以写 ring_progress(72.5)（max 默认 100），
#     也可以写 ring_progress(0.725, max=1)，两者等效。
# ------------------------------------------------------------------
c12 = edv.ring_progress(0.725, max=1, label="等价写法：0.725 / 1")
c12.save(out("ring_progress_5.html"))
# 输出：与示例 1 的圆环填充比例相同，tooltip 的「完成」值显示 0.725

print("OK ring_progress")
