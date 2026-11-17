# -*- coding: utf-8 -*-
"""wordcloud（词云）完整示例：5 个用法，覆盖最简/典型/进阶参数/边界/联动/配色。

运行方式（在仓库根目录）：

    cd F:/deepseek/eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/wordcloud.py

输出：examples/output/wordcloud_*.html（每个文件都是可离线打开的独立页面）。
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


    # ---- 示例 1：最简：产品销售额词云 ----
    chart = edv.wordcloud(df, names="产品", values="销售额")
    chart.save("examples/output/wordcloud_1.html")

    # ---- 示例 2：典型：城市维度与记录数 ----
    chart = edv.wordcloud(df, names="城市", title="城市记录热度", height=420)
    chart.save("examples/output/wordcloud_2.html")

    # ---- 示例 3：深色主题与配色 ----
    chart = edv.wordcloud(df, names="渠道", values="客户数", theme="dark")
    chart.palette("morandi")
    chart.save("examples/output/wordcloud_3.html")

    # ---- 示例 4：先聚合再画：两列组合成词 ----
    combo = df.copy()
    combo["标签"] = combo["大区"] + "·" + combo["渠道"]
    chart = edv.wordcloud(combo, names="标签", values="利润", top_n=20, height=460)
    chart.save("examples/output/wordcloud_4.html")

    # ---- 示例 5：联动：词云作为被过滤方 ----
    cal = edv.calendar(df, date="日期", value="订单数", link="wc1")
    wc = edv.wordcloud(df, names="产品", values="销售额", link="wc1", top_n=4)
    edv.dashboard(cal, wc, title="日历 → 词云", cols=2).save("examples/output/wordcloud_5.html")

if __name__ == "__main__":
    main()
    print("OK wordcloud")
