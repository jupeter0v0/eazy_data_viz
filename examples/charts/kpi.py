# -*- coding: utf-8 -*-
"""kpi 示例大全：KPI 数字卡片。

运行方式（在仓库根目录）：

    PYTHONPATH=. PYTHONIOENCODING=utf-8 python examples/charts/kpi.py

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
    print("kpi 示例：5 个小节")

    # ---- 数据准备（按需派生） ----
    month_df = df.groupby("月份", observed=True)["销售额"].sum().reset_index()
    region_df = df.groupby("大区", observed=True).agg(
       销售额=("销售额", "sum"), 订单数=("订单数", "sum"), 利润=("利润", "sum")).reset_index()


    # ---- 示例 1：最简用法：聚合销售额 ----
    chart = edv.kpi(df, value="销售额")
    chart.save(os.path.join(OUT, "kpi_1.html"))
    check(os.path.join(OUT, "kpi_1.html"))

    # ---- 示例 2：指标名 + 金额格式 ----
    chart = edv.kpi(
        df, value="销售额",
        label="全年销售额", fmt="currency",
        hint="2024 全年 · 含税",
    )
    chart.save(os.path.join(OUT, "kpi_2.html"))
    check(os.path.join(OUT, "kpi_2.html"))

    # ---- 示例 3：同比涨跌：delta + delta_label ----
    chart = edv.kpi(
        df, value="销售额",
        label="销售额", fmt="compact",
        delta=0.128, delta_label="同比",
        hint="较去年同期",
    )
    chart.save(os.path.join(OUT, "kpi_3.html"))
    check(os.path.join(OUT, "kpi_3.html"))

    # ---- 示例 4：强调色 + 分区 + 联动 ----
    chart = edv.kpi(
        df, value="订单数", agg="sum",
        label="总订单数", fmt="thousands", unit=" 单",
        accent=2, section="总览", link="销售",
        hint="联动组：销售",
    )
    chart.save(os.path.join(OUT, "kpi_4.html"))
    check(os.path.join(OUT, "kpi_4.html"))

    # ---- 示例 5：深色主题 + 标题 + 高度 ----
    chart = edv.kpi(
        df, value="客户数", agg="sum",
        label="累计客户数", unit=" 人", fmt="thousands",
        title="客户规模", subtitle="截至 2024-12-31",
        theme="dark", height=190, accent=1,
    )
    chart.save(os.path.join(OUT, "kpi_5.html"))
    check(os.path.join(OUT, "kpi_5.html"))

    print("OK kpi")


if __name__ == "__main__":
    main()
