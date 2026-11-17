# -*- coding: utf-8 -*-
"""pie 示例大全：饼图 / 环形图。

运行方式（在仓库根目录）：

    PYTHONPATH=. PYTHONIOENCODING=utf-8 python examples/charts/pie.py

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
    print("pie 示例：5 个小节")

    # ---- 数据准备（按需派生） ----
    month_df = df.groupby("月份", observed=True)["销售额"].sum().reset_index()
    region_df = df.groupby("大区", observed=True).agg(
       销售额=("销售额", "sum"), 订单数=("订单数", "sum"), 利润=("利润", "sum")).reset_index()


    # ---- 示例 1：最简用法：产品销售额占比 ----
    chart = edv.pie(df, names="产品", values="销售额")
    chart.save(os.path.join(OUT, "pie_1.html"))
    check(os.path.join(OUT, "pie_1.html"))

    # ---- 示例 2：计数值饼图：各渠道订单条数 ----
    chart = edv.pie(
        df, names="渠道",
        title="各渠道订单条数占比", subtitle="values 省略时按记录数统计",
        fmt="thousands",
    )
    chart.save(os.path.join(OUT, "pie_2.html"))
    check(os.path.join(OUT, "pie_2.html"))

    # ---- 示例 3：环形图（donut） ----
    chart = edv.pie(
        df, names="大区", values="利润",
        donut=True, labels=True,
        title="各大区利润占比", subtitle="环形图，中心留白",
        height=400,
    )
    chart.save(os.path.join(OUT, "pie_3.html"))
    check(os.path.join(OUT, "pie_3.html"))

    # ---- 示例 4：格式 + 高度 + 暗色主题 ----
    chart = edv.pie(
        df, names="产品", values="订单数",
        theme="dark", fmt="thousands", labels=True,
        height=420, title="产品订单数（深色）",
    )
    chart.save(os.path.join(OUT, "pie_4.html"))
    check(os.path.join(OUT, "pie_4.html"))

    # ---- 示例 5：联动：点击扇区筛选同组图表 ----
    chart = edv.pie(
        df, names="渠道", values="销售额",
        link="渠道联动",
        title="渠道销售额占比", subtitle="点击扇区可筛选同组图表",
    )
    chart.save(os.path.join(OUT, "pie_5.html"))
    check(os.path.join(OUT, "pie_5.html"))

    print("OK pie")


if __name__ == "__main__":
    main()
