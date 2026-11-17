# -*- coding: utf-8 -*-
"""sankey（桑基图）完整示例：5 个用法，覆盖最简/典型/进阶参数/边界/联动/配色。

运行方式（在仓库根目录）：

    cd F:/deepseek/eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/sankey.py

输出：examples/output/sankey_*.html（每个文件都是可离线打开的独立页面）。
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


    # ---- 示例 1：最简：渠道 → 产品 ----
    chart = edv.sankey(df, source="渠道", target="产品", value="销售额")
    chart.save("examples/output/sankey_1.html")

    # ---- 示例 2：典型：不传权重，按记录条数 ----
    chart = edv.sankey(
        df,
        source="大区",
        target="渠道",
        title="大区 → 渠道 记录流向",
        height=460,
    )
    chart.save("examples/output/sankey_2.html")

    # ---- 示例 3：进阶：拼出三层流向（大区 → 产品 → 渠道） ----
    e1 = df.groupby(["大区", "产品"], as_index=False)["销售额"].sum()
    e1.columns = ["source", "target", "value"]
    e2 = df.groupby(["产品", "渠道"], as_index=False)["销售额"].sum()
    e2.columns = ["source", "target", "value"]
    edges = pd.concat([e1, e2], ignore_index=True)
    chart = edv.sankey(edges, source="source", target="target", value="value", height=560)
    chart.save("examples/output/sankey_3.html")

    # ---- 示例 4：深色主题、货币格式与配色 ----
    chart = edv.sankey(
        df,
        source="渠道",
        target="产品",
        value="利润",
        fmt="currency",
        theme="dark",
    )
    chart.palette("echarts")
    chart.save("examples/output/sankey_4.html")

    # ---- 示例 5：联动：点击节点过滤明细 ----
    sk = edv.sankey(df, source="渠道", target="产品", value="销售额", link="k1")
    tbl = edv.table(df, columns=["渠道", "产品", "销售额"], link="k1", limit=40)
    edv.dashboard(sk, tbl, title="桑基图联动", cols=2).save("examples/output/sankey_5.html")

if __name__ == "__main__":
    main()
    print("OK sankey")
