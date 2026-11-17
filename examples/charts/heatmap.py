# -*- coding: utf-8 -*-
"""heatmap 示例大全：热力图。

运行方式（在仓库根目录）：

    PYTHONPATH=. PYTHONIOENCODING=utf-8 python examples/charts/heatmap.py

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
    print("heatmap 示例：5 个小节")

    # ---- 数据准备（按需派生） ----
    month_df = df.groupby("月份", observed=True)["销售额"].sum().reset_index()
    region_df = df.groupby("大区", observed=True).agg(
       销售额=("销售额", "sum"), 订单数=("订单数", "sum"), 利润=("利润", "sum")).reset_index()


    # ---- 示例 1：最简用法：大区 × 产品 ----
    chart = edv.heatmap(df, x="大区", y="产品", value="销售额")
    chart.save(os.path.join(OUT, "heatmap_1.html"))
    check(os.path.join(OUT, "heatmap_1.html"))

    # ---- 示例 2：按合计排序：sort=desc ----
    chart = edv.heatmap(
        df, x="大区", y="产品", value="利润",
        sort="desc", labels=True,
        title="利润热力图（按合计降序）", subtitle="大额行列排在前面",
        xtitle="大区", ytitle="产品",
    )
    chart.save(os.path.join(OUT, "heatmap_2.html"))
    check(os.path.join(OUT, "heatmap_2.html"))

    # ---- 示例 3：mean 聚合：平均利润热力图 ----
    chart = edv.heatmap(
        df, x="大区", y="渠道", value="利润",
        agg="mean", fmt="currency", labels=True,
        title="各大区渠道平均利润", subtitle="均值口径",
        xtitle="大区", ytitle="渠道",
    )
    chart.save(os.path.join(OUT, "heatmap_3.html"))
    check(os.path.join(OUT, "heatmap_3.html"))

    # ---- 示例 4：深色主题 + 配色 ----
    chart = edv.heatmap(
        df, x="月份", y="大区", value="销售额",
        theme="dark", sort="x", labels=True,
        title="月份 × 大区销售额（深色）",
        xtitle="月份", ytitle="大区",
    )
    chart.palette("echarts")
    chart.save(os.path.join(OUT, "heatmap_4.html"))
    check(os.path.join(OUT, "heatmap_4.html"))

    # ---- 示例 5：综合：标题 + fmt + 高度 + 暗色 ----
    chart = edv.heatmap(
        df, x="渠道", y="产品", value="销售额",
        agg="sum", fmt="compact", height=420,
        theme="dark", labels=True,
        title="产品 × 渠道销售额", subtitle="深色 + compact 数值格式",
        xtitle="渠道", ytitle="产品",
    )
    chart.palette("morandi")
    chart.save(os.path.join(OUT, "heatmap_5.html"))
    check(os.path.join(OUT, "heatmap_5.html"))

    print("OK heatmap")


if __name__ == "__main__":
    main()
