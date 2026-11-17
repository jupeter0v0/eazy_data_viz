# -*- coding: utf-8 -*-
"""七套配色库：同一份数据，一页看完全部配色。

    python examples/palettes.py

配色可在三个层级生效：
    1) 全局默认   edv.set_palette("antd")
    2) 单图覆盖   edv.bar(...).palette("tableau")
    3) 整个看板   edv.dashboard(..., palette="morandi")
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "output")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import eazy_data_viz as edv  # noqa: E402


def main():
    os.makedirs(OUT, exist_ok=True)
    df = edv.sample_df()

    print("可用配色：")
    edv.palettes()

    charts = []
    for name in edv.palette.names():
        info = edv.palette.get(name)
        charts.append(
            edv.bar(df, x="月份", y="销售额", color="产品",
                    title="月度销售 · %s" % info["label"],
                    subtitle=info["desc"], height=300).palette(name)
        )

    page = edv.dashboard(*charts, cols=2, title="配色库：7 套主题 × 同一份数据",
                         palette="google")
    path = os.path.join(OUT, "palettes.html")
    page.save(path)
    print("已生成", path, "（%.2f MB）" % (os.path.getsize(path) / 1048576.0))

    # 全局默认切换（影响之后创建的所有图）
    edv.set_palette("tableau")
    print("当前全局配色：", edv.palette.current())


if __name__ == "__main__":
    main()
