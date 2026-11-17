# -*- coding: utf-8 -*-
"""geo_map 示例大全：中国 / 世界地图的区域填色。

运行方式（在仓库根目录）：

    PYTHONPATH=. PYTHONIOENCODING=utf-8 python examples/charts/geo_map.py

脚本运行 5 个小节，全部产物保存到 examples/output/（geo_map_1.html ~ geo_map_2.html），
每个小节都会校验 HTML 大于 100KB，保证资源确实内联进来了。
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

# 1.0.0 版本 map 系列从 eazy_data_viz.maps 导入；集成后会直接挂在 edv 命名空间，
# 所以这里先试 edv，再回退到子模块，两种版本都能跑。
try:  # pragma: no cover - 只是导入兼容
    geo_map = edv.geo_map
except AttributeError:  # pragma: no cover
    from eazy_data_viz.maps import geo_map


def check(path):
    """校验生成的 HTML 存在且大于 100KB，返回文件大小。"""
    assert os.path.isfile(path), "没有生成文件：%s" % path
    size = os.path.getsize(path)
    assert size > 100_000, "HTML 只有 %d 字节，疑似资源没有内联：%s" % (size, path)
    print("    saved %-34s %8.1f KB" % (os.path.basename(path), size / 1024.0))
    return size


def main():
    os.makedirs(OUT, exist_ok=True)
    df = edv.sample_df()
    print("geo_map 示例：5 个小节")


    # ---- 示例 1：最简 ----
    # data + region 必填，value 省略时按「每个区域的记录数」填色。
    chart = geo_map(df, "省份", "销售额")
    path = os.path.join(OUT, "geo_map_1.html")
    chart.save(path)
    check(path)

    # ---- 示例 2：全名数据 ----
    # 数据里是「广东省」「北京市」这类全名也没问题：前端会把两边都归一化后再匹配。
    full_df = pd.DataFrame(
        {
            "省份": ["广东省", "北京市", "内蒙古自治区", "广西壮族自治区",
                    "新疆维吾尔自治区", "西藏自治区", "香港特别行政区"],
            "销售额": [182000, 96000, 74000, 68000, 52000, 31000, 27000],
        }
    )
    chart = geo_map(
        full_df,
        "省份",
        "销售额",
        fmt="thousands",
        title="全名省份数据也能匹配",
        subtitle="广东省 / 北京市 / 内蒙古自治区 … 无需先转短名",
    )
    path = os.path.join(OUT, "geo_map_3.html")
    chart.save(path)
    check(path)

    # ---- 示例 3：固定色阶 ----
    # min_value / max_value 把 visualMap 的两端钉死，多张图之间颜色才可比。
    # 例如所有图都固定 0 ~ 200000，颜色深的图就一定数值大。
    chart = geo_map(
        df,
        "省份",
        "销售额",
        min_value=0,
        max_value=200000,
        title="固定色阶：0 ~ 20 万",
        subtitle="min_value / max_value 让多张图配色可横向比较",
        fmt="compact",
    )
    path = os.path.join(OUT, "geo_map_4.html")
    chart.save(path)
    check(path)

    # ---- 示例 4：下钻 + 联动 ----
    # drill 在地图里的语义是「点击省份 → 只看这个省」（单层聚焦）；
    # link 则让同一看板里其它图按点击的省份过滤。
    chart = geo_map(
        df,
        "省份",
        "销售额",
        drill=["省份"],
        link="区域联动",
        title="点击省份聚焦 / 联动其它图",
        subtitle="地图下钻=单层聚焦；link 与柱状图共享",
    )
    path = os.path.join(OUT, "geo_map_5.html")
    chart.save(path)
    check(path)

    # 联动看板：地图 + 柱状图 + 折线图共享 link="区域联动"
    page = edv.dashboard(
        geo_map(df, "省份", "销售额", link="区域联动",
                title="① 区域填色（点省份）", height=460),
        edv.bar(df, "省份", "销售额", link="区域联动",
                title="② 柱状图随地图联动", height=460),
        edv.line(df, "月份", "销售额", color="渠道", link="区域联动",
                 title="③ 时间趋势也随点击过滤", height=380),
        cols=2,
        title="geo_map 联动看板",
    )
    path = os.path.join(OUT, "geo_map_6.html")
    page.save(path)
    check(path)

    # ---- 示例 5：世界地图 ----
    # map="world"：GeoJSON 是英文国名（United States / China …），
    # 前端内置了常见中文别名（美国 / 中国 / 德国 …），中文数据可直接用。
    world_df = pd.DataFrame(
        {
            "国家": ["美国", "中国", "德国", "巴西", "印度", "澳大利亚", "日本", "英国"],
            "GDP": [100, 90, 70, 60, 55, 40, 35, 30],
        }
    )
    chart = geo_map(
        world_df,
        "国家",
        "GDP",
        map="world",
        fmt="raw",
        title="世界地图：中文国名",
        subtitle="map='world'，常见中文国名内置别名表",
    )
    path = os.path.join(OUT, "geo_map_7.html")
    chart.save(path)
    check(path)

    # 也支持英文原名（与 GeoJSON 完全一致的名字，无需别名）
    world_en = pd.DataFrame(
        {
            "country": ["United States", "China", "Germany", "Brazil",
                        "India", "Australia"],
            "gdp": [100, 90, 70, 60, 55, 40],
        }
    )
    chart = geo_map(
        world_en,
        "country",
        "gdp",
        map="world",
        palette="morandi",
        title="世界地图：英文原名",
        subtitle="名字与 GeoJSON 完全一致时直接命中",
    )
    path = os.path.join(OUT, "geo_map_2.html")
    chart.save(path)
    check(path)

    print("OK geo_map")


if __name__ == "__main__":
    main()
