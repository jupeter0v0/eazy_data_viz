# -*- coding: utf-8 -*-
"""下钻 + 联动：驾驶舱里最常用的两个交互。

    python examples/drill_link.py

要点：
* drill=["大区", "省份", "城市"]：点击图形逐级下钻，工具栏出现面包屑，可返回上一级
* link="销售"：多张图传同一个 link，点任意一张图的类目，其余图自动过滤；
  再点同一类目取消（也可点顶栏「重置联动」）
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

    page = edv.dashboard(
        # 下钻：三级
        edv.bar(df, x="大区", y="销售额", drill=["大区", "省份", "城市"],
                title="① 下钻：大区 → 省份 → 城市（点柱形）", height=380),

        # 联动组 "销售"
        edv.bar(df, x="产品", y="销售额", link="销售",
                title="② 联动：点产品", height=380),
        edv.line(df, x="月份", y="销售额", color="渠道", link="销售",
                 title="③ 联动：趋势随之过滤", height=380),
        edv.pie(df, names="渠道", values="销售额", link="销售",
                title="④ 联动：渠道占比随之变化", height=380),

        # KPI 也参与联动：会自动按筛选结果重算
        edv.kpi(df, value="销售额", label="当前筛选销售额", link="销售",
                hint="点 ②③④ 任意图形，本卡实时重算", height=150),

        cols=2,
        title="下钻 + 联动示例",
        desc="两套交互都在浏览器内完成，不触发 Python 重算",
    )
    path = os.path.join(OUT, "drill_link.html")
    page.save(path)
    print("已生成", path, "（%.2f MB）" % (os.path.getsize(path) / 1048576.0))


if __name__ == "__main__":
    main()
