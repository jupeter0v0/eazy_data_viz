# -*- coding: utf-8 -*-
"""eazy_data_viz 快速上手：3 个场景，复制任意一段都能直接跑。

    python examples/quickstart.py            # 生成 examples/output/*.html
    python examples/quickstart.py --open     # 生成后自动用浏览器打开

没有 pip install 也能跑（脚本会把仓库根目录加进 sys.path）。
"""
from __future__ import annotations

import os
import sys
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "output")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import eazy_data_viz as edv  # noqa: E402


def main():
    os.makedirs(OUT, exist_ok=True)
    df = edv.sample_df()
    print("演示数据：", df.shape, list(df.columns))
    print("列类型自动识别：", {c: str(df[c].dtype) for c in df.columns})

    # ------------------------------------------------------------------
    # 1. 一张图 → 一个 HTML 文件（不需要任何前端知识）
    # ------------------------------------------------------------------
    chart = edv.bar(
        df, x="大区", y="销售额", color="产品",
        title="各区域销售额（按产品分组）", height=420,
    )
    p1 = os.path.join(OUT, "01_single_chart.html")
    chart.save(p1)
    print("① 已生成", p1)

    # ------------------------------------------------------------------
    # 2. 下钻 + 联动：一个文件、一个看板
    #    - drill：点击柱形逐级下钻
    #    - link ：同组图表点击即交叉筛选
    # ------------------------------------------------------------------
    pages = edv.dashboard(
        edv.kpi(df, value="销售额", label="全年销售额", delta=0.128,
                delta_label="同比", target=2_000_000, hint="点击图表可联动"),
        edv.kpi(df, value="订单数", agg="sum", label="订单数", fmt="thousands",
                unit=" 单", delta=0.064),
        edv.line(df, x="月份", y="销售额", color="渠道", link="g1",
                 title="月度趋势（点击图例筛选）"),
        edv.bar(df, x="大区", y="销售额", color="产品", stack=True, link="g1",
                drill=["大区", "省份", "城市"], title="区域结构（可下钻）"),
        edv.pie(df, names="渠道", values="销售额", donut=True, title="渠道构成"),
        edv.heatmap(df, x="月份", y="大区", value="销售额", title="月份 × 大区"),
        edv.table(df, columns=["日期", "大区", "省份", "产品", "销售额", "利润"],
                  title="明细（前 100 行）"),
        cols=2,
        title="经营驾驶舱",
        desc="下钻：点柱形 · 联动：点同组任意图形 · 顶栏可切深浅色 / 配色",
    )
    p2 = os.path.join(OUT, "02_cockpit.html")
    pages.save(p2)
    print("② 已生成", p2)

    # ------------------------------------------------------------------
    # 3. Streamlit：一行 components.html 嵌入（交互仍在浏览器内完成）
    #    详见 examples/streamlit_app.py
    # ------------------------------------------------------------------
    html = edv.dashboard(
        edv.bar(df, x="月份", y="销售额", title="月度销售"),
        edv.line(df, x="日期", y="销售额", title="日趋势"),
        cols=2, title="Streamlit 内嵌示例",
    ).to_html()
    p3 = os.path.join(OUT, "03_streamlit_payload.html")
    with open(p3, "w", encoding="utf-8") as f:
        f.write(html)
    print("③ 已生成", p3, "（在 Streamlit 里用 st.components.v1.html 嵌入）")

    if "--open" in sys.argv:
        webbrowser.open("file:///" + os.path.abspath(p2).replace("\\", "/"))
    print("\n完成。改数据只改 df，剩下只需要列名。")


if __name__ == "__main__":
    main()
