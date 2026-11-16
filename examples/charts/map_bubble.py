# -*- coding: utf-8 -*-
"""map_bubble 示例大全：省份 / 国家中心点的气泡地图。

运行方式（在仓库根目录）：

    PYTHONPATH=. PYTHONIOENCODING=utf-8 python examples/charts/map_bubble.py

脚本运行 5 个小节，产物保存到 examples/output/
（map_bubble_1.html ~ map_bubble_2.html）。

气泡地图和区域填色的区别：
* geo_map 用颜色表达一个指标（区域之间互斥，一块区域一个值）；
* map_bubble 用气泡大小表达一个指标、再用颜色表达第二个指标，
  适合「数值差异巨大、需要同时看两个指标」或者「一个区域有多条记录」的场景。
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
    map_bubble = edv.map_bubble
except AttributeError:  # pragma: no cover
    from eazy_data_viz.maps import map_bubble


def check(path):
    """校验 HTML 存在且大于 100KB。"""
    assert os.path.isfile(path), "没有生成文件：%s" % path
    size = os.path.getsize(path)
    assert size > 100_000, "HTML 只有 %d 字节：%s" % (size, path)
    print("    saved %-38s %8.1f KB" % (os.path.basename(path), size / 1024.0))
    return size


def main():
    os.makedirs(OUT, exist_ok=True)
    df = edv.sample_df()
    print("map_bubble 示例：5 个小节")


    # ---- 示例 1：最简 ----
    # value 同时决定气泡大小和 tooltip 数值；没有 size 列时它就是半径。
    chart = map_bubble(df, "省份", "销售额")
    path = os.path.join(OUT, "map_bubble_1.html")
    chart.save(path)
    check(path)

    # ---- 示例 2：第二指标 ----
    # size 指定另一个指标控制半径：气泡大小 = 订单数，tooltip 里同时看销售额。
    # 适合「销售额大但订单少」这类偏离，一眼就能看出来。
    chart = map_bubble(
        df,
        "省份",
        "销售额",
        size="订单数",
        title="气泡大小=订单数，颜色/数值=销售额",
        subtitle="size 参数用第二指标控制半径",
    )
    path = os.path.join(OUT, "map_bubble_3.html")
    chart.save(path)
    check(path)

    # ---- 示例 3：分组着色 ----
    # color 传一个分类列（大区 / 产品 / 渠道），一个区域有多组时会并排画多个气泡，
    # 颜色对应图例，可点击图例筛选。
    chart = map_bubble(
        df,
        "省份",
        "销售额",
        color="大区",
        title="按大区着色的气泡",
        subtitle="color='大区'，一个省份最多 4 个气泡",
        legend=True,
    )
    path = os.path.join(OUT, "map_bubble_4.html")
    chart.save(path)
    check(path)

    # ---- 示例 4：大小 + 颜色 ----
    # size 和 color 同时使用：半径编码订单数、颜色编码大区、tooltip 编码销售额。
    chart = map_bubble(
        df,
        "省份",
        "销售额",
        size="订单数",
        color="渠道",
        title="三指标气泡：销售额 / 订单数 / 渠道",
        subtitle="size 管半径、color 管颜色、value 管数值",
    )
    path = os.path.join(OUT, "map_bubble_5.html")
    chart.save(path)
    check(path)

    # ---- 示例 5：下钻 + 联动 ----
    # 地图点击某个省份后可以聚焦（drill），也可以广播给同 link 的其它图（link）。
    chart = map_bubble(
        df,
        "省份",
        "销售额",
        size="订单数",
        color="大区",
        drill=["省份"],
        link="气泡联动",
        title="点击省份聚焦 / 联动",
        subtitle="drill 单层聚焦 + link 广播过滤条件",
    )
    path = os.path.join(OUT, "map_bubble_6.html")
    chart.save(path)
    check(path)

    # 一个完整的联动看板：气泡地图 + 柱状图，共享 link="气泡联动"
    page = edv.dashboard(
        map_bubble(df, "省份", "销售额", size="订单数", color="大区",
                   link="气泡联动", title="① 气泡地图", height=460),
        edv.bar(df, "省份", "订单数", link="气泡联动",
                title="② 订单数柱状图（跟随联动）", height=460),
        cols=2,
        title="map_bubble 联动看板",
        theme="light",
    )
    path = os.path.join(OUT, "map_bubble_2.html")
    page.save(path)
    check(path)

    print("OK map_bubble")


if __name__ == "__main__":
    main()
