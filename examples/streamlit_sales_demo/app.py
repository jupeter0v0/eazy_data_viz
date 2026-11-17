# -*- coding: utf-8 -*-
"""销售经营分析看板 —— eazy_data_viz × Streamlit 完整 Demo。

数据来自用友 ERP 的销售明细导出（``2025-05-20T09-10_export.csv``），原始文件里
客户、物料、部门、业务员全是主键 ID；``prepare_data.py`` 已把它们翻译成可读中文，
并按月抽样 2.4 万行，生成 ``data/sales_demo.csv``。

运行::

    pip install "eazy_data_viz[streamlit]"
    streamlit run examples/streamlit_sales_demo/app.py

演示了这几件事：

* **components v2**：``edv.streamlit_dashboard()``，没有 iframe、高度自适应；
* **默认 0 rerun**：点图 / 联动 / 下钻全在浏览器内完成（1.3.0 起）；
* **跨图联动**：趋势、大区、地图、TOP 客户共享 ``link="biz"``，点一处其余跟着过滤；
* **下钻**：大区 → 省份 → 客户；
* **中文本地化**：``.unit("万")`` 纵轴缩略、``年月`` 自动显示「3月 / 2026年3月」；
* **中国式报表**：``table(total=True, index=True, bar="销售额")`` 合计行 + 序号列 + 数据条；
* **可选的双向事件**：勾选侧栏「点图回传 Python」后传 ``on_select``，点击触发一次 rerun。
"""

from __future__ import annotations

import os
import sys

import pandas as pd
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import eazy_data_viz as edv  # noqa: E402

DATA = os.path.join(HERE, "data", "sales_demo.csv")

st.set_page_config(page_title="销售经营分析 · eazy_data_viz", page_icon="📈", layout="wide")


@st.cache_data(show_spinner="正在加载销售明细…")
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA, parse_dates=["下单日期"])
    df["年月"] = df["下单日期"].dt.strftime("%Y-%m")
    df["季度"] = (df["下单日期"].dt.year.astype(str) + "Q"
                  + df["下单日期"].dt.quarter.astype(str))
    df["回款率"] = (df["已回款"] / df["销售额"].where(df["销售额"] > 0)).fillna(0.0)
    return df


raw = load_data()

# ---------------------------------------------------------------------------
# 侧栏：筛选 + 主题 + 事件开关
# ---------------------------------------------------------------------------
st.sidebar.header("筛选")
d_min, d_max = raw["下单日期"].min().date(), raw["下单日期"].max().date()
date_range = st.sidebar.date_input("下单日期", value=(d_min, d_max),
                                   min_value=d_min, max_value=d_max,
                                   format="YYYY-MM-DD")
regions = st.sidebar.multiselect("大区", sorted(raw["大区"].unique()), placeholder="全部大区")
categories = st.sidebar.multiselect("产品大类", sorted(raw["产品大类"].unique()),
                                     placeholder="全部大类")
order_types = st.sidebar.multiselect("订单类型", sorted(raw["订单类型"].unique()),
                                      placeholder="全部类型")

st.sidebar.divider()
theme = st.sidebar.radio("主题", ["light", "dark"], horizontal=True)
trigger = st.sidebar.checkbox(
    "点图回传 Python（on_select）", value=False,
    help="不勾选：点击 / 联动 / 下钻全部在浏览器内完成，脚本 0 次 rerun。\n"
         "勾选：点击会 trigger 一次，Python 重跑脚本并拿到 result.select。",
)
st.sidebar.caption("数据：用友销售明细抽样 %s 行，主键已翻译成中文名称。" % format(len(raw), ","))

# ---------------------------------------------------------------------------
# 过滤
# ---------------------------------------------------------------------------
df = raw
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start, end = date_range
    df = df[(df["下单日期"].dt.date >= start) & (df["下单日期"].dt.date <= end)]
if regions:
    df = df[df["大区"].isin(regions)]
if categories:
    df = df[df["产品大类"].isin(categories)]
if order_types:
    df = df[df["订单类型"].isin(order_types)]

st.title("销售经营分析看板")
st.caption(
    "eazy_data_viz × Streamlit（components v2）· 当前筛选 %s 行 / %s 个订单"
    % (format(len(df), ","), format(df["订单号"].nunique(), ","))
)

if df.empty:
    st.warning("当前筛选条件下没有数据，请放宽左侧条件。")
    st.stop()

# ---------------------------------------------------------------------------
# KPI
# ---------------------------------------------------------------------------
total_amount = float(df["销售额"].sum())
received = float(df["已回款"].sum())
kpi_df = pd.DataFrame([{
    "销售额": total_amount,
    "订单数": int(df["订单号"].nunique()),
    "客户数": int(df["客户"].nunique()),
    # fmt="percent" 的语义是「数值已经是百分数」，所以这里乘 100
    "回款率": (received / total_amount * 100) if total_amount else 0.0,
}])

def _yoy(frame: pd.DataFrame) -> dict:
    """同比：拿 2026 年已发生的月份对比 2025 年同期。

    演示数据只有 17 个月，不能拿整段时间直接除；而且 delta 写死一个数字一看就是假的。
    这里按「月份匹配」算，筛选条件变了 delta 也跟着变。
    """
    cur = frame[frame["下单日期"].dt.year == 2026]
    if cur.empty:
        return {"销售额": 0.0, "订单数": 0.0, "客户数": 0.0, "回款率": 0.0}
    months = set(cur["下单日期"].dt.month)
    prev = frame[(frame["下单日期"].dt.year == 2025)
                 & (frame["下单日期"].dt.month.isin(months))]
    if prev.empty:
        return {"销售额": 0.0, "订单数": 0.0, "客户数": 0.0, "回款率": 0.0}

    def _rate(x):
        total = float(x["销售额"].sum())
        return float(x["已回款"].sum()) / total if total else 0.0

    def _grow(a, b):
        return (a - b) / b if b else 0.0

    return {
        "销售额": _grow(float(cur["销售额"].sum()), float(prev["销售额"].sum())),
        "订单数": _grow(cur["订单号"].nunique(), prev["订单号"].nunique()),
        "客户数": _grow(cur["客户"].nunique(), prev["客户"].nunique()),
        "回款率": _rate(cur) - _rate(prev),
    }


yoy = _yoy(df)

kpis = [
    edv.kpi(kpi_df, value="销售额", label="销售额", unit="万", theme=theme,
            delta=yoy["销售额"], delta_label="同比", hint="含税销售额合计"),
    edv.kpi(kpi_df, value="订单数", label="订单数", fmt="thousands", theme=theme,
            delta=yoy["订单数"], delta_label="同比", hint="去重后的销售订单数"),
    edv.kpi(kpi_df, value="客户数", label="合作客户", fmt="thousands", theme=theme,
            delta=yoy["客户数"], delta_label="同比", inverse=True, hint="去重后的客户数"),
    edv.kpi(kpi_df, value="回款率", label="回款率", fmt="percent", theme=theme,
            delta=yoy["回款率"], delta_label="同比", hint="已回款 / 销售额"),
]

edv.streamlit_dashboard(kpis, cols=4, theme=theme)

# ---------------------------------------------------------------------------
# 主图：联动 + 下钻 + 中文本地化
# ---------------------------------------------------------------------------
region_agg = (
    df.groupby("大区", as_index=False)
      .agg(销售额=("销售额", "sum"), 已回款=("已回款", "sum"))
)
region_agg["回款率"] = (region_agg["已回款"] / region_agg["销售额"]).replace([float("inf")], 0) * 100

charts = [
    # 趋势：年月是 "YYYY-MM" 字符串，坐标轴会自动显示成「1月 / 2026年1月」
    edv.line(df, x="年月", y="销售额", color="大区", link="biz", theme=theme, zoom=False,
             title="月度销售趋势").unit("万"),
    # 结构：大区 × 产品大类堆叠，点柱子会联动其它图
    edv.bar(df, x="大区", y="销售额", color="产品线", stack=True, link="biz",
            drill=["大区", "省份", "客户"], theme=theme,
            title="大区 × 产品线").unit("万"),
    # 地理：按省份的销售额
    edv.geo_map(df, region="省份", value="销售额", link="biz", theme=theme,
                title="各省销售额"),
    # TOP 客户：自己算好前 10 再画。组件内置的 top_n 会补一根「其他」，
    # 排行图里那根没有名字的柱子反而挡视线；排序用升序，横向条形图会把
    # 第一行画在最下面，升序看起来才是「最大在最上面」。
    edv.bar(
        df.groupby("客户简称", as_index=False)["销售额"].sum()
          .nlargest(10, "销售额").sort_values("销售额"),
        x="客户简称", y="销售额", horizontal=True, link="biz", theme=theme,
        title="销售额 TOP 10 客户",
    ).unit("万"),
    # 双轴：柱子看销售额、折线看回款率（%）
    edv.combo(region_agg, x="大区", bar="销售额", line="回款率", theme=theme,
              title="大区销售额与回款率"),
    # 占比：订单类型
    edv.pie(df, names="订单类型", values="销售额", donut=True, labels=False,
            theme=theme, title="订单类型占比").unit("万"),
]

st.subheader("经营分析")
st.caption("趋势 / 大区 / 地图 / TOP 客户 四张图共享 `link=\"biz\"`：点任意一根柱子，其余图会跟着过滤；"
           "再点一次取消。堆叠图还支持下钻（大区 → 省份 → 客户）。")

dash_kwargs = {"cols": 2, "title": None, "theme": theme}
if trigger:
    def _on_click():
        st.session_state["eazy_clicked"] = True

    dash_kwargs["on_select"] = _on_click

result = edv.streamlit_dashboard(charts, **dash_kwargs)
if trigger and result.select:
    st.info("Python 收到点击：%s" % result.select)

# ---------------------------------------------------------------------------
# 中国式报表
# ---------------------------------------------------------------------------
st.subheader("销售明细（中国式报表）")
st.caption("`table(total=True, index=True, bar=\"销售额\")`：表尾合计、固定序号列、单元格数据条、"
           "斑马纹；只统计实际渲染的前 20 行。")

detail = df.sort_values("销售额", ascending=False)
tbl = edv.table(
    detail,
    columns=["下单日期", "大区", "省份", "客户", "产品大类", "订单类型", "数量",
             "销售额", "已回款", "应收余额"],
    limit=20, total=True, index=True, bar="销售额", theme=theme,
    height=800, title=None,
)
# 表格是「固定高度 + 内部滚动」的 HTML 组件，v2 默认给 500px，20 行会被裁掉
# 一半并藏住表尾合计；这里显式给足高度。
edv.streamlit_dashboard([tbl], cols=1, theme=theme, height=840)

# ---------------------------------------------------------------------------
# 说明
# ---------------------------------------------------------------------------
with st.expander("这个 Demo 用到了哪些能力？"):
    st.markdown(
        """
| 能力 | 代码 |
| --- | --- |
| 组件 v2（无 iframe、自动高度） | `edv.streamlit_dashboard(charts, cols=2)` |
| 默认 0 rerun | 不传 `on_select`，点击 / 联动 / 下钻都在浏览器内完成 |
| 跨图联动 | 图表都带 `link="biz"` |
| 下钻 | `drill=["大区", "省份", "客户"]` |
| 数值单位 | `.unit("万")`，轴刻度、tooltip、标签统一按万显示 |
| 中文日期轴 | `x="年月"`（`2026-03` → `3月`，跨年自动补 `2026年3月`） |
| 中国式报表 | `table(total=True, index=True, bar="销售额")` |
| Python 感知点击 | `streamlit_dashboard(..., on_select=回调)`，点击触发一次 rerun |
        """
    )

with st.expander("查看明细数据（前 100 行）"):
    st.dataframe(df.head(100), use_container_width=True, height=420)
