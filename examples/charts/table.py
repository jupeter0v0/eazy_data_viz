# -*- coding: utf-8 -*-
"""table（明细表）完整示例：5 个用法，覆盖最简/典型/进阶参数/边界/联动/配色。

运行方式（在仓库根目录）：

    cd F:/deepseek/eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/table.py

输出：examples/output/table_*.html（每个文件都是可离线打开的独立页面）。
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


def main():
    df = edv.sample_df()
    print("数据：%d 行 × %d 列" % (df.shape[0], df.shape[1]))


    # ---- 示例 1：最简：默认取全部列 ----
    chart = edv.table(df)
    chart.save("examples/output/table_1.html")

    # ---- 示例 2：典型：指定列与行数 ----
    chart = edv.table(
        df,
        columns=["日期", "大区", "产品", "渠道", "销售额", "利润"],
        limit=30,
        title="重点字段明细",
        subtitle="仅展示前 30 行",
    )
    chart.save("examples/output/table_2.html")

    # ---- 示例 3：进阶：数值格式与深色主题 ----
    a = edv.table(df, columns=["大区", "销售额", "利润"], limit=20, fmt="currency")
    a.save("examples/output/table_3.html")
    b = edv.table(df, columns=["大区", "销售额", "利润"], limit=20, theme="dark")
    b.save("examples/output/table_4.html")

    # ---- 示例 4：边界：先筛选再展示（避免空表） ----
    east = df[df["大区"] == "华东"]
    chart = edv.table(east, columns=["日期", "产品", "销售额"], limit=15, title="华东明细")
    chart.save("examples/output/table_5.html")

    empty = df[df["大区"] == "不存在的区域"]
    try:
        edv.table(empty, columns=["日期", "销售额"], title="空结果")
    except ValueError as exc:
        print("空数据会直接报错，符合预期：", exc)

    # ---- 示例 5：联动：作为被过滤的明细表 ----
    rose = edv.rose(df, names="大区", values="销售额", link="tb1")
    tbl = edv.table(df, columns=["大区", "产品", "销售额"], link="tb1", limit=40)
    edv.dashboard(rose, tbl, title="玫瑰图 → 明细表", cols=2).save("examples/output/table_6.html")

if __name__ == "__main__":
    main()
    print("OK table")
