# -*- coding: utf-8 -*-
"""map_flow 示例大全：两个区域之间的流量飞线图。

运行方式（在仓库根目录）：

    PYTHONPATH=. PYTHONIOENCODING=utf-8 python examples/charts/map_flow.py

脚本运行 5 个小节，产物保存到 examples/output/
（map_flow_1.html ~ map_flow_2.html）。

飞线图适合表达「从哪来、到哪去、量多大」：
线宽和颜色都随数值变化，数值越大线越粗、颜色越靠高热端；
图的右侧 visualMap 就是数值色阶，可当图例读。
注意：起点和终点必须都能在**同一张地图**里找到（都是省份或都是国家），
找不到的那条数据会被跳过。
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "examples", "output")
# 注意：examples/charts/ 下有 calendar.py，直接 python examples/charts/xxx.py 运行时
# 脚本目录会排在 sys.path[0]，把标准库 calendar 遮住（pandas 启动时就会用它）。
# 这里把自己所在目录从 sys.path 移除，保证标准库优先。
if HERE in sys.path:
    sys.path.remove(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pandas as pd  # noqa: E402

import eazy_data_viz as edv  # noqa: E402

try:  # 兼容 1.0.0（从子模块导入）和后续版本（edv.xxx 直接可用）
    map_flow = edv.map_flow
except AttributeError:  # pragma: no cover
    from eazy_data_viz.maps import map_flow


def check(path):
    """校验 HTML 存在且大于 100KB。"""
    assert os.path.isfile(path), "没有生成文件：%s" % path
    size = os.path.getsize(path)
    assert size > 100_000, "HTML 只有 %d 字节：%s" % (size, path)
    print("    saved %-36s %8.1f KB" % (os.path.basename(path), size / 1024.0))
    return size


def main():
    os.makedirs(OUT, exist_ok=True)
    df = edv.sample_df()
    print("map_flow 示例：5 个小节")

    # 省际调拨：起点 / 终点都是省份短名，货量是流量指标。
    flows = pd.DataFrame(
        {
            "起点": ["北京", "广东", "上海", "江苏", "浙江", "四川", "河北", "湖北"],
            "终点": ["上海", "北京", "广东", "浙江", "北京", "陕西", "天津", "湖南"],
            "货量": [120, 80, 60, 45, 90, 30, 25, 18],
        }
    )


    # ---- 示例 1：最简 ----
    # source / target 必填，value 省略时按「记录数」算流量。
    chart = map_flow(flows, "起点", "终点", "货量")
    path = os.path.join(OUT, "map_flow_1.html")
    chart.save(path)
    check(path)

    # ---- 示例 2：聚合方式 ----
    # 同一对起终点有多条明细时，会按 agg 聚合成一条飞线。
    # 下面的数据里「北京 → 上海」有三条（40/80/30）：
    #   agg="sum" → 150，agg="max" → 80，agg="count" → 3。
    detail = pd.DataFrame(
        {
            "起点": ["北京", "北京", "北京", "广东", "广东", "上海"],
            "终点": ["上海", "上海", "上海", "北京", "北京", "广东"],
            "货量": [40, 80, 30, 50, 70, 60],
        }
    )
    chart = map_flow(
        detail,
        "起点",
        "终点",
        "货量",
        agg="max",
        title="同一对起终点取最大值",
        subtitle="北京→上海 三条明细 40/80/30，agg='max' → 80",
    )
    path = os.path.join(OUT, "map_flow_3.html")
    chart.save(path)
    check(path)

    # 换成 count：看每条线上有多少条记录（此时 value 省略）
    chart = map_flow(
        detail,
        "起点",
        "终点",
        agg="count",
        title="同一对起终点的记录条数",
        subtitle="value 省略 + agg='count'，北京→上海 = 3",
    )
    path = os.path.join(OUT, "map_flow_4.html")
    chart.save(path)
    check(path)

    # ---- 示例 3：全名数据 ----
    # 起点/终点写全名也可以，前端会把两边都归一化再匹配。
    full_flows = pd.DataFrame(
        {
            "起点": ["广东省", "北京市", "内蒙古自治区", "上海市", "新疆维吾尔自治区"],
            "终点": ["北京市", "广东省", "黑龙江省", "浙江省", "西藏自治区"],
            "金额": [520000, 430000, 210000, 180000, 90000],
        }
    )
    chart = map_flow(
        full_flows,
        "起点",
        "终点",
        "金额",
        fmt="thousands",
        title="全名省份飞线",
        subtitle="广东省 → 北京市 这类全名无需先转短名",
    )
    path = os.path.join(OUT, "map_flow_5.html")
    chart.save(path)
    check(path)

    # ---- 示例 4：世界地图 ----
    # 跨国流向：map="world"，中文国名有内置别名（美国 → United States）。
    world_flows = pd.DataFrame(
        {
            "起点": ["中国", "美国", "德国", "巴西", "印度", "澳大利亚"],
            "终点": ["美国", "中国", "法国", "阿根廷", "日本", "中国"],
            "贸易额": [100, 90, 60, 45, 35, 28],
        }
    )
    chart = map_flow(
        world_flows,
        "起点",
        "终点",
        "贸易额",
        map="world",
        fmt="raw",
        title="世界贸易流向",
        subtitle="map='world'，起终点都要是同一张地图里的国家",
    )
    path = os.path.join(OUT, "map_flow_6.html")
    chart.save(path)
    check(path)

    # ---- 示例 5：联动看板 ----
    # 飞线图默认 legend=False（它用右侧 visualMap 表示数值），
    # 但 link 一样可以工作：点飞线的起点区域，其它图按来源列过滤。
    page = edv.dashboard(
        map_flow(flows, "起点", "终点", "货量",
                 link="流向联动", title="① 省际调拨飞线", height=460),
        edv.bar(df, "省份", "销售额", link="区域联动",
                title="② 各省销售额", height=460),
        edv.bar(flows, "起点", "货量", link="流向联动",
                title="③ 按起点汇总货量（跟随飞线联动）", height=460),
        cols=2,
        title="map_flow 联动看板",
        theme="dark",
        desc="暗色主题看板；图内主题跟随各图 theme 参数",
    )
    path = os.path.join(OUT, "map_flow_2.html")
    page.save(path)
    check(path)

    print("OK map_flow")


if __name__ == "__main__":
    main()
