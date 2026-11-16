# -*- coding: utf-8 -*-
"""Streamlit 里使用 eazy_data_viz 的最小示例。

    pip install "eazy_data_viz[streamlit]"
    streamlit run examples/streamlit_app.py

要点：
* 用 st.components.v1.html 嵌入，必须显式给 height（默认 150px 会被裁）
* 一个 components.html 就是一个独立 iframe：跨图联动要放进同一个 dashboard
* 交互（下钻 / 联动 / 主题）都在浏览器里完成，不会触发 Streamlit rerun
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st  # noqa: E402

import eazy_data_viz as edv  # noqa: E402
from eazy_data_viz import render as edv_render  # noqa: E402

st.set_page_config(page_title="eazy_data_viz × Streamlit", layout="wide")
st.title("eazy_data_viz × Streamlit")
st.caption("所有交互都在 iframe 内完成，点击图表不会触发页面 rerun。")

rows = st.sidebar.slider("数据行数", 300, 3000, 1500, step=100)
palette = st.sidebar.selectbox("配色", edv.palette.names(), index=0)
theme = st.sidebar.radio("主题", ["light", "dark"], horizontal=True)
edv.set_palette(palette)

df = edv.sample_df(rows=rows)

charts = [
    edv.kpi(df, value="销售额", label="销售额", delta=0.128, delta_label="同比",
            target=2_000_000, spark="销售额", spark_x="月份", theme=theme),
    edv.kpi(df, value="利润", label="利润", delta=0.086, delta_label="同比", theme=theme),
    edv.line(df, x="月份", y="销售额", color="渠道", link="g1", theme=theme),
    edv.bar(df, x="大区", y="销售额", color="产品", stack=True, link="g1",
            drill=["大区", "省份"], theme=theme),
    edv.pie(df, names="渠道", values="销售额", donut=True, theme=theme),
    edv.heatmap(df, x="月份", y="大区", value="销售额", theme=theme),
]

page = edv.dashboard(*charts, cols=2, title="经营驾驶舱（Streamlit 内嵌）",
                     theme=theme, palette=palette)
html = page.to_html(inline=True)

# 高度 = 页面估算高度；scrolling=False 由 iframe 自己滚动
height = edv_render.page_height(charts, cols=2, has_header=True, has_filters=False)
st.components.v1.html(html, height=height + 20, scrolling=False)

with st.expander("查看这段代码"):
    st.code(
        "page = edv.dashboard(*charts, cols=2, theme=theme, palette=palette)\n"
        "st.components.v1.html(page.to_html(), height=page_height(...), scrolling=False)",
        language="python",
    )

st.subheader("原始数据（前 10 行）")
st.dataframe(df.head(10), use_container_width=True)
