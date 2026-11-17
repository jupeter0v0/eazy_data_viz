# -*- coding: utf-8 -*-
"""graph（关系图（力导向网络））完整示例：5 个用法，覆盖最简/典型/进阶参数/边界/联动/配色。

运行方式（在仓库根目录）：

    cd F:/deepseek/eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/graph.py

输出：examples/output/graph_*.html（每个文件都是可离线打开的独立页面）。
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


    # ---- 示例 1：最简：大区 × 产品网络 ----
    chart = edv.graph(df, source="大区", target="产品", value="订单数")
    chart.save("examples/output/graph_1.html")

    # ---- 示例 2：典型：不传权重，按共现次数 ----
    chart = edv.graph(
        df,
        source="渠道",
        target="产品",
        title="渠道与产品的共现网络",
        height=460,
    )
    chart.save("examples/output/graph_2.html")

    # ---- 示例 3：进阶：拼出产品共现网络 ----
    pairs = df.groupby(["大区", "渠道"], as_index=False)["订单数"].sum()
    pairs.columns = ["source", "target", "value"]
    chart = edv.graph(pairs, source="source", target="target", value="value", height=520)
    chart.save("examples/output/graph_3.html")

    # ---- 示例 4：深色主题与自定义配色 ----
    chart = edv.graph(df, source="产品", target="渠道", value="销售额", theme="dark")
    chart.palette("morandi")
    chart.save("examples/output/graph_4.html")

    # ---- 示例 5：联动：点击节点过滤明细 ----
    g = edv.graph(df, source="大区", target="产品", value="订单数", link="g1")
    tbl = edv.table(df, columns=["大区", "产品", "订单数"], link="g1", limit=40)
    edv.dashboard(g, tbl, title="关系图联动", cols=2).save("examples/output/graph_5.html")

if __name__ == "__main__":
    main()
    print("OK graph")
