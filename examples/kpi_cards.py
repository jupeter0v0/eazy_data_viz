# -*- coding: utf-8 -*-
"""KPI 卡片全用法：目标达成、迷你走势、反向指标、联动重算、派生指标（客单价）。

    python examples/kpi_cards.py
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
    total = df["销售额"].sum()
    margin = df["利润"].sum() / total * 100

    cards = edv.dashboard(
        # 1) 最简：一个数 + 标签
        edv.kpi(df, value="销售额", label="销售额"),

        # 2) 目标 + 达成率进度条
        edv.kpi(df, value="销售额", label="销售额（年度目标）",
                target=2_000_000, target_label="年度目标 200 万"),

        # 3) 同比 / 环比 + 迷你走势
        edv.kpi(df, value="销售额", label="销售额（含走势）",
                delta=0.128, delta_label="同比",
                spark="销售额", spark_x="月份", accent=1),

        # 4) 反向指标：下降才是好事（inverse=True 会让下跌显示为绿色）
        edv.kpi(3.4, label="退货率", fmt="percent", delta=-0.086,
                delta_label="同比", inverse=True,
                hint="inverse=True：下降显示为绿色"),

        # 5) 单位 / 前缀 / 指定小数
        edv.kpi(df, value="订单数", agg="sum", label="订单数", fmt="thousands",
                unit=" 单", delta=0.064),

        # 6) 静态值 + 百分比 + 目标（没有 DataFrame 也能用）
        edv.kpi(margin, label="利润率", fmt="percent", target=25,
                delta=0.012, delta_label="环比", accent=2),

        # 7) 参与联动：点同 link 组的图，卡片自动按筛选条件重算
        edv.kpi(df, value="销售额", label="销售额（联动重算）", link="g1",
                hint="点击下方任意图形，本卡随筛选条件变化"),

        # 8) 派生指标：客单价 = 销售额 ÷ 订单数（先各自聚合，再相除）
        edv.kpi(df, metrics={"销售额": "销售额", "订单数": "订单数"},
                expr="销售额 / 订单数", label="客单价", fmt="currency",
                link="g1", spark_x="月份", accent=3,
                hint="销售额合计 ÷ 订单数合计；联动后按筛选结果重算"),

        # 9) 分母是 unique 数：品类均摊销售额（换成客户号即人均消费）
        edv.kpi(df, metrics=[("销售额", "sum"), ("产品", "unique")],
                expr="销售额 / 产品", label="品类均摊销售额", fmt="currency",
                accent=4, hint="销售额 ÷ 在售品类数（unique）"),

        cols=4,
        title="KPI 卡片全用法",
        desc="目标达成率 / 迷你走势 / 同比环比 / 反向指标 / 联动重算 / 派生比率",
    )
    path = os.path.join(OUT, "kpi_cards.html")
    cards.save(path)
    print("已生成", path, "（%.2f MB）" % (os.path.getsize(path) / 1048576.0))


if __name__ == "__main__":
    main()
