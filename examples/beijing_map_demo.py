# -*- coding: utf-8 -*-
"""北京区级地图组件示例：16 个市辖区填色 + 气泡 + 明细表。

运行：
    py examples/beijing_map_demo.py        # 生成 beijing_map_demo.html 并自动打开

要点：
    edv.beijing_map(df, region="区", value="销售额") 等价于
    edv.geo_map(df, region="区", value="销售额", map="beijing")；
    区名写 "朝阳" 或 "朝阳区" 都能匹配。
"""
import os

import pandas as pd

import eazy_data_viz as edv

DATA = [
    ("东城区", 52.0, 1820, 9),
    ("西城区", 68.0, 2240, 11),
    ("朝阳区", 128.0, 4360, 26),
    ("丰台区", 61.0, 2050, 12),
    ("石景山区", 33.0, 1120, 7),
    ("海淀区", 142.0, 4980, 28),
    ("门头沟区", 24.0, 760, 5),
    ("房山区", 47.0, 1480, 8),
    ("通州区", 58.0, 1930, 10),
    ("顺义区", 66.0, 2100, 11),
    ("昌平区", 74.0, 2560, 14),
    ("大兴区", 63.0, 2170, 12),
    ("怀柔区", 26.0, 820, 5),
    ("平谷区", 22.0, 690, 4),
    ("密云区", 25.0, 800, 5),
    ("延庆区", 18.0, 560, 3),
]

df = pd.DataFrame(DATA, columns=["区", "销售额", "订单数", "门店数"])
df["万元/店"] = (df["销售额"] / df["门店数"]).round(1)

charts = [
    edv.beijing_map(df, region="区", value="销售额",
                    title="北京各区销售额", labels=True, height=540),
    edv.geo_map(df, region="区", value="订单数", map="beijing",
                title="北京各区订单数", labels=True, height=540),
    edv.table(df, columns=["区", "销售额", "订单数", "门店数", "万元/店"],
              title="各区明细", total=True, bar="销售额", height=520),
]

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "beijing_map_demo.html")
    edv.dashboard(charts, cols=2, title="北京区级地图组件 · 示例").save(out, inline=True)
    print("saved:", out)
