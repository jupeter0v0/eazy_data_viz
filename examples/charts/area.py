# -*- coding: utf-8 -*-
"""area 示例大全：面积图。

运行方式（在仓库根目录）：

    PYTHONPATH=. PYTHONIOENCODING=utf-8 python examples/charts/area.py

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
    print("area 示例：5 个小节")

    # ---- 数据准备（按需派生） ----
    month_df = df.groupby("月份", observed=True)["销售额"].sum().reset_index()
    region_df = df.groupby("大区", observed=True).agg(
       销售额=("销售额", "sum"), 订单数=("订单数", "sum"), 利润=("利润", "sum")).reset_index()


    # ---- 示例 1：最简用法：日期销售额面积图 ----
    chart = edv.area(df, x="日期", y="销售额")
    chart.save(os.path.join(OUT, "area_1.html"))
    check(os.path.join(OUT, "area_1.html"))

    # ---- 示例 2：按月聚合的面积趋势 ----
    month = df.groupby("月份", observed=True)["销售额"].sum().reset_index()
    chart = edv.area(
        month, x="月份", y="销售额", sort="x",
        title="月度销售额面积图", subtitle="面积强调累计量级",
        xtitle="月份", ytitle="销售额（元）",
    )
    chart.save(os.path.join(OUT, "area_2.html"))
    check(os.path.join(OUT, "area_2.html"))

    # ---- 示例 3：下钻 + 联动 ----
    chart = edv.area(
        df, x="日期", y="销售额",
        drill=["日期", "大区", "产品"], link="面积联动",
        title="销售额面积下钻", subtitle="点击图形逐级下钻",
        xtitle="日期", ytitle="销售额（元）",
    )
    chart.save(os.path.join(OUT, "area_3.html"))
    check(os.path.join(OUT, "area_3.html"))

    # ---- 示例 4：主题 / 配色 / 导出 ----
    month = df.groupby("月份", observed=True)["利润"].sum().reset_index()
    chart = edv.area(
        month, x="月份", y="利润", sort="x",
        theme="dark", title="月度利润（深色）", labels=False,
    )
    chart.palette("echarts")
    chart.save(os.path.join(OUT, "area_4.html"))
    check(os.path.join(OUT, "area_4.html"))

    # ---- 示例 5：百分比份额面积（percent） ----
    month_ch = df.groupby(["月份", "渠道"], observed=True)["销售额"].sum().reset_index()
    chart = edv.area(
        month_ch, x="月份", y="销售额", color="渠道",
        sort="x", percent=True, height=420,
        title="渠道份额走势", subtitle="每个时间点归一化为 100%",
        xtitle="月份", ytitle="份额",
    )
    chart.save(os.path.join(OUT, "area_5.html"))
    check(os.path.join(OUT, "area_5.html"))

    print("OK area")


if __name__ == "__main__":
    main()
