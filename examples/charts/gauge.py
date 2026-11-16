# -*- coding: utf-8 -*-
"""gauge 示例大全：仪表盘。

运行方式（在仓库根目录）：

    PYTHONPATH=. PYTHONIOENCODING=utf-8 python examples/charts/gauge.py

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
    print("gauge 示例：5 个小节")

    # ---- 数据准备（按需派生） ----
    month_df = df.groupby("月份", observed=True)["销售额"].sum().reset_index()
    region_df = df.groupby("大区", observed=True).agg(
       销售额=("销售额", "sum"), 订单数=("订单数", "sum"), 利润=("利润", "sum")).reset_index()


    # ---- 示例 1：最简用法：单个百分比 ----
    chart = edv.gauge(87.5)
    chart.save(os.path.join(OUT, "gauge_1.html"))
    check(os.path.join(OUT, "gauge_1.html"))

    # ---- 示例 2：百分比格式：fmt=percent ----
    chart = edv.gauge(
        87.5, fmt="percent",
        label="目标达成", unit=None,
        title="目标达成率", subtitle="percent 只加 %，不乘 100",
    )
    chart.save(os.path.join(OUT, "gauge_2.html"))
    check(os.path.join(OUT, "gauge_2.html"))

    # ---- 示例 3：负数区间：温度 ----
    chart = edv.gauge(
        -4.5, label="当前温度", min=-20, max=45,
        fmt="raw", unit="℃",
        title="室外温度", subtitle="min=-20, max=45",
        height=300,
    )
    chart.save(os.path.join(OUT, "gauge_3.html"))
    check(os.path.join(OUT, "gauge_3.html"))

    # ---- 示例 4：深色主题 ----
    chart = edv.gauge(
        68, label="健康分", theme="dark",
        title="设备健康分（深色）", height=300,
    )
    chart.save(os.path.join(OUT, "gauge_4.html"))
    check(os.path.join(OUT, "gauge_4.html"))

    # ---- 示例 5：聚合后传入：由 DataFrame 算出单值 ----
    total = df["销售额"].sum() / 1e6  # 换算成百万元
    chart = edv.gauge(
        total, label="累计销售额（百万元）",
        min=0, max=20, fmt="raw", unit=" 百万",
        title="全年销售额完成度", subtitle="目标 2000 万",
        height=320,
    )
    chart.save(os.path.join(OUT, "gauge_5.html"))
    check(os.path.join(OUT, "gauge_5.html"))

    print("OK gauge")


if __name__ == "__main__":
    main()
