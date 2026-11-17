# -*- coding: utf-8 -*-
"""经营驾驶舱（cockpit）：一页看完全公司经营状况。

    python examples/cockpit.py

输出 examples/output/cockpit.html，单文件可发给业务方（离线可用）。
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "output")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import eazy_data_viz as edv  # noqa: E402


def build(df: pd.DataFrame):
    total = df["销售额"].sum()
    profit = df["利润"].sum()
    margin = profit / total * 100
    by_region = df.groupby("大区", as_index=False)["销售额"].sum()
    by_region["目标"] = (by_region["销售额"] * 1.12).round(2)
    daily = df.groupby("日期", as_index=False)["销售额"].sum()
    half = df.assign(期间=np.where(df["日期"] < pd.Timestamp("2024-07-01"),
                              "上半年", "下半年"))

    return edv.dashboard(
        # ---- 第一行：四个核心指标 ----
        edv.kpi(df, value="销售额", agg="sum", label="全年销售额",
                delta=0.128, delta_label="同比", target=2_000_000,
                spark="销售额", spark_x="月份", accent=0),
        edv.kpi(df, value="利润", agg="sum", label="利润总额",
                delta=0.086, delta_label="同比", accent=1),
        edv.kpi(df, value="订单数", agg="sum", label="订单数", fmt="thousands",
                unit=" 单", delta=0.064, accent=2),
        edv.kpi(margin, label="利润率", fmt="percent", delta=-0.012,
                delta_label="同比", target=25, inverse=False, accent=3),
        # ---- 趋势 ----
        edv.line(df, x="月份", y="销售额", color="渠道", link="g1",
                 title="月度销售额（按渠道）", height=360),
        edv.area(df, x="日期", y="销售额", title="日销售额走势", height=360),
        # ---- 结构 ----
        edv.bar(df, x="大区", y="销售额", color="产品", stack=True, link="g1",
                drill=["大区", "省份", "城市"], title="区域 × 产品结构（可下钻）", height=380),
        edv.pie(df, names="渠道", values="销售额", donut=True,
                title="渠道构成", height=380),
        # ---- 排名 / 目标 ----
        edv.bar(by_region, x="大区", y="销售额", horizontal=True, top_n=10,
                title="区域销售额 Top 10", height=360),
        edv.bullet(by_region, x="大区", actual="销售额", target="目标",
                   title="目标达成（子弹图）", height=360),
        # ---- 明细 ----
        edv.table(df, columns=["日期", "大区", "省份", "城市", "产品", "渠道",
                               "销售额", "订单数", "利润"],
                  title="经营明细", limit=100, height=420),
        # ---- 分布 ----
        edv.histogram(df, column="销售额", bins=24, title="销售额分布", height=340),
        edv.scatter(df, x="订单数", y="销售额", color="大区", size="客户数",
                    title="订单数 vs 销售额（气泡=客户数）", height=340),
        cols=2,
        title="XX 公司经营驾驶舱",
        desc="数据：2024 全年 · 点击图形下钻 / 联动 · 右上角可切主题与配色",
        palette="google",
    )


def main():
    os.makedirs(OUT, exist_ok=True)
    df = edv.sample_df()
    page = build(df)
    path = os.path.join(OUT, "cockpit.html")
    page.save(path)
    print("已生成", path, "（%.2f MB）" % (os.path.getsize(path) / 1048576.0))
    print("提示：想看柔和配色可 build(df) 里把 palette 换成 'tableau' / 'morandi'。")


if __name__ == "__main__":
    main()
