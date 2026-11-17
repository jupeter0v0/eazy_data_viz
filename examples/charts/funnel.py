# -*- coding: utf-8 -*-
"""funnel 示例大全：漏斗图。

运行方式（在仓库根目录）：

    PYTHONPATH=. PYTHONIOENCODING=utf-8 python examples/charts/funnel.py

脚本会运行 5 个小节，每个小节把图保存到 examples/output/，并校验 HTML 大于 100KB。
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "examples", "output")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# examples/charts/ 目录下的其它示例脚本可能与标准库模块同名（例如 calendar.py），
# 直接运行本脚本时该目录会排在 sys.path 首位、遮蔽标准库，导致 import pandas 失败。
# 因此先把脚本所在目录从 sys.path 中移除，再 import 第三方库。
for _p in list(sys.path):
    try:
        if _p and os.path.abspath(_p) == HERE:
            sys.path.remove(_p)
    except OSError:
        pass

import pandas as pd  # noqa: E402

import eazy_data_viz as edv  # noqa: E402


def check(path):
    """校验生成的 HTML 文件存在且大于 100KB。返回文件大小（字节）。"""
    assert os.path.isfile(path), "没有生成文件：%s" % path
    size = os.path.getsize(path)
    assert size > 100_000, "HTML 只有 %d 字节，疑似资源没有内联：%s" % (size, path)
    print("    saved %-42s %8.1f KB" % (os.path.basename(path), size / 1024.0))
    return size


def main():
    os.makedirs(OUT, exist_ok=True)
    df = edv.sample_df()
    print("funnel 示例：5 个小节")

    # ---- 数据准备（按需派生） ----
    month_df = df.groupby("月份", observed=True)["销售额"].sum().reset_index()
    region_df = df.groupby("大区", observed=True).agg(
       销售额=("销售额", "sum"), 订单数=("订单数", "sum"), 利润=("利润", "sum")).reset_index()


    # ---- 示例 1：最简用法：转化漏斗 ----
    stage = pd.DataFrame({
        "阶段": ["曝光", "访问", "加购", "下单", "支付"],
        "人数": [120000, 48000, 16000, 5200, 3100],
    })
    chart = edv.funnel(stage, names="阶段", values="人数")
    chart.save(os.path.join(OUT, "funnel_1.html"))
    check(os.path.join(OUT, "funnel_1.html"))

    # ---- 示例 2：省略 values：按阶段统计记录数 ----
    chart = edv.funnel(
        df, names="渠道",
        title="各渠道记录数漏斗", subtitle="values 省略时按 count 统计",
        height=380,
    )
    chart.save(os.path.join(OUT, "funnel_2.html"))
    check(os.path.join(OUT, "funnel_2.html"))

    # ---- 示例 3：深色主题 + 配色 ----
    stage = pd.DataFrame({
        "阶段": ["曝光", "点击", "下单", "支付"],
        "人数": [98000, 41000, 12000, 7600],
    })
    chart = edv.funnel(
        stage, names="阶段", values="人数",
        theme="dark", height=440,
        title="广告转化漏斗（深色）",
    )
    chart.palette("antd")
    chart.save(os.path.join(OUT, "funnel_3.html"))
    check(os.path.join(OUT, "funnel_3.html"))

    # ---- 示例 4：联动：点击层筛选 ----
    stage = pd.DataFrame({
        "阶段": ["访问", "注册", "下单", "复购"],
        "人数": [64000, 28000, 9500, 3200],
    })
    chart = edv.funnel(
        stage, names="阶段", values="人数",
        link="转化联动",
        title="转化漏斗（可联动）", subtitle="点击某层筛选同组图表",
        height=420,
    )
    chart.save(os.path.join(OUT, "funnel_4.html"))
    check(os.path.join(OUT, "funnel_4.html"))

    # ---- 示例 5：mean 聚合：平均金额漏斗 ----
    stage = pd.DataFrame({
        "阶段": ["询价", "报价", "成交"],
        "平均金额": [8600, 12400, 18600],
    })
    chart = edv.funnel(
        stage, names="阶段", values="平均金额", agg="mean",
        fmt="currency", labels=True,
        title="平均金额漏斗", subtitle="注意：均值漏斗不代表转化率",
    )
    chart.save(os.path.join(OUT, "funnel_5.html"))
    check(os.path.join(OUT, "funnel_5.html"))

    print("OK funnel")


if __name__ == "__main__":
    main()
