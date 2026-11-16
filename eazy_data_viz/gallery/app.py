# -*- coding: utf-8 -*-
"""eazy_data_viz gallery · Streamlit 版（Material Design 3 风格，48 种图表）

启动方式（二选一）::

    streamlit run eazy_data_viz/gallery/app.py
    python -c "import eazy_data_viz; eazy_data_viz.gallery()"

每张图都由 ``st.components.v1.html(...)`` 渲染成自包含文档：ECharts 与 eazy_data_viz 运行时
都内联在页面里，交互（下钻 / 联动 / 图例筛选 / 缩放 / 主题切换）全部在浏览器内
完成，不触发 Streamlit rerun，所以点击是零延迟的；离线也能用。
"""
import streamlit as st

import eazy_data_viz
from eazy_data_viz import render as pvrender

st.set_page_config(
    page_title="eazy_data_viz · pandas 经营驾驶舱组件库",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner=False)
def load_data(rows=1200, seed=42):
    return eazy_data_viz.sample_df(rows=rows, seed=seed)


@st.cache_data(show_spinner=False)
def derived(df):
    """驾驶舱常用派生表（和 gallery.html 用的是同一套口径）。"""
    import numpy as np

    g_region = df.groupby("大区", as_index=False)["销售额"].sum()
    g_region["目标"] = [620000, 520000, 420000, 300000]
    by_prov = df.groupby(["大区", "省份"], as_index=False)["销售额"].sum()
    prov_mean = df.groupby(["大区", "省份"], as_index=False)[
        ["销售额", "利润", "订单数"]
    ].mean()
    by_chan = df.groupby("渠道", as_index=False)["销售额"].sum()
    daily = df.groupby("日期", as_index=False)["销售额"].sum().sort_values("日期")
    daily60 = daily.tail(45).reset_index(drop=True)

    closes = daily60["销售额"].to_numpy(dtype=float)
    opens = np.concatenate([[closes[0] * 0.98], closes[:-1]])
    ohlc = {
        "日期": daily60["日期"].dt.strftime("%Y-%m-%d"),
        "开盘": opens.round(2),
        "收盘": closes.round(2),
        "最低": (np.minimum(opens, closes) * 0.97).round(2),
        "最高": (np.maximum(opens, closes) * 1.03).round(2),
    }
    import pandas as pd

    ohlc = pd.DataFrame(ohlc)

    half = (df.assign(期间=df["日期"].dt.month.le(6).map({True: "上半年", False: "下半年"}))
              .pivot_table(index="省份", columns="期间", values="销售额", aggfunc="sum")
              .reset_index())
    bump = df.groupby(["月份", "产品"], as_index=False)["销售额"].sum()
    mon = bump["月份"].astype(str).str.replace("月", "", regex=False).astype(int)
    phase = bump["产品"].map({"智能终端": 0, "云服务": 3, "行业软件": 6, "运维服务": 9}).astype(float)
    bump["销售额"] = (bump["销售额"] * (1 + 0.45 * np.sin((mon + phase) / 12.0 * 2 * np.pi))).round(2)

    par = df.groupby("大区", as_index=False)[["销售额", "订单数", "利润", "客户数"]].mean()

    return {
        "g_region": g_region,
        "by_prov": by_prov,
        "prov_mean": prov_mean,
        "by_chan": by_chan,
        "daily": daily,
        "ohlc": ohlc,
        "half": half,
        "bump": bump,
        "par": par,
    }


PALETTE = "google"


def _render_v1(items, cols, title, desc, theme, palette):
    """旧版 Streamlit 的 iframe 渲染路径（components.v1）。"""
    if len(items) == 1 and cols == 1:
        page, has_header = items[0], False
    else:
        page = eazy_data_viz.dashboard(items, cols=cols, title=title, desc=desc, theme=theme,
                                       palette=palette or PALETTE)
        has_header = bool(title)
    st.components.v1.html(
        page.to_html(),
        height=pvrender.page_height(
            items, cols=cols, has_header=has_header,
            has_filters=any((getattr(c, "spec", {}) or {}).get("link") for c in items),
        ),
        scrolling=False,
    )


def show(charts, code=None, cols=2, title=None, desc=None, theme="light", palette=None,
         events=False):
    """渲染一组图表（同一份 HTML 文档 → 支持跨图联动）并附上调用代码。

    优先使用 ``st.components.v2``：没有 iframe、高度按内容自适应，
    并且（``events=True`` 时）点击图表会把事件回传给 Python。
    旧版 Streamlit 自动回退到 ``components.v1.html``。
    """
    items = charts if isinstance(charts, (list, tuple)) else [charts]
    multi = not (len(items) == 1 and cols == 1)
    use_v2 = eazy_data_viz.streamlit_available()
    if use_v2:
        try:
            result = eazy_data_viz.streamlit_dashboard(
                items,
                cols=cols,
                title=title if multi else None,
                desc=desc if multi else None,
                theme=theme,
                palette=palette or PALETTE,
                on_select=(_on_select if events else None),
            )
            if events:
                sel = getattr(result, "select", None)
                if sel:
                    st.session_state["_last_select"] = sel
                last = st.session_state.get("_last_select")
                if last:
                    st.info(
                        "**v2 事件回传**：你点中了「%s」"
                        "（%s = %s）%s"
                        % (
                            last.get("title") or last.get("chart") or "-",
                            last.get("dim") or "-",
                            last.get("value"),
                            " · 下钻层级：%s" % " > ".join(last["drill"])
                            if last.get("drill")
                            else "",
                        )
                    )
        except Exception as exc:  # pragma: no cover - 环境差异
            st.warning("components v2 渲染失败，已回退 iframe：%s" % exc)
            _render_v1(items, cols, title, desc, theme, palette)
    else:
        _render_v1(items, cols, title, desc, theme, palette)
    if code:
        with st.expander("查看 Python 代码", expanded=False):
            st.code(code.strip(), language="python")


def _on_select():
    """v2 组件回调：不需要参数，重跑后从返回值读取 ``select`` 触发值。"""
    return None


# ---------------------------------------------------------------------------
# 侧边栏
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📊 eazy_data_viz")
    st.caption("pandas → 可交互 HTML 图表 · 经营驾驶舱组件库")
    theme = st.radio("主题", ["light", "dark"], horizontal=True)
    _pal_labels = {n: "%s · %s" % (n, eazy_data_viz.palette.get(n)["label"]) for n in eazy_data_viz.palette.names()}
    _pal = st.selectbox(
        "配色", list(_pal_labels), format_func=lambda n: _pal_labels[n],
        index=list(_pal_labels).index(PALETTE), key="palette_select")
    if _pal != PALETTE:
        PALETTE = _pal
        eazy_data_viz.set_palette(_pal)
    rows = st.slider("示例数据行数", 300, 5000, 1200, step=300)
    page = st.radio(
        "页面",
        [
            "快速开始",
            "经营驾驶舱",
            "指标卡与配色",
            "趋势分析",
            "对比与排名",
            "结构与占比",
            "分布与关系",
            "地图可视化",
            "明细与文本",
            "交互：下钻 + 联动",
            "v2 双向事件",
        ],
    )
    with st.expander("48 种图表一览"):
        st.caption(
            "KPI：kpi / group_kpi / gauge / ring_progress / progress\n\n"
            "趋势：line / area / area_pct / theme_river / sparkline / trend / "
            "candlestick / calendar / combo / bar_pct\n\n"
            "对比：bar / waterfall / pareto / lollipop / dumbbell / slope / bump / "
            "bullet / target / pictorial / pyramid / funnel\n\n"
            "结构：pie / rose / treemap / sunburst / tree / tile\n\n"
            "分布：histogram / box / scatter / quadrant / heatmap / matrix / radar / "
            "parallel / sankey / graph\n\n"
            "明细：table / wordcloud\n\n"
            "地图：geo_map / map_bubble / map_flow（内置 china / world）"
        )
    st.divider()
    st.caption("所有图表都接受同一个 DataFrame，只需写列名；不用写 JSON。")

df = load_data(rows)
d = derived(df)

st.title("eazy_data_viz · pandas 经营驾驶舱组件库")
st.caption("Material Design 3 风格 · ECharts 5.5 内联 · 离线可用 · 下钻/联动在浏览器端完成")

# ---------------------------------------------------------------------------
if page == "快速开始":
    st.subheader("三步上手")
    st.code(
        """import eazy_data_viz

df = eazy_data_viz.sample_df()                       # 换成你的 DataFrame
eazy_data_viz.bar(df, x="大区", y="销售额", color="产品").show()

# 多图看板（放进同一个 HTML 文档才会互相联动）
eazy_data_viz.show(
    eazy_data_viz.bar(df, x="大区", y="销售额", link="g1"),
    eazy_data_viz.line(df, x="月份", y="销售额", link="g1"),
    cols=2, title="经营看板",
)""",
        language="python",
    )
    st.markdown(
        "**输出方式**：`.show()`（脚本 / 笔记本 / Streamlit 自适应）、`.to_html()`（取 HTML 字符串）、"
        "`.save(path)`（落地静态文件）。表格数据不用预处理，库内自动识别 数值 / 时间 / 分类列。"
    )
    st.subheader("同一份数据，一行出图")
    show(
        [
            eazy_data_viz.bar(df, x="大区", y="销售额", color="产品", stack=True, title="各区域销售额"),
            eazy_data_viz.line(df, x="月份", y="销售额", color="渠道", smooth=True, title="月度趋势"),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.bar(df, x="大区", y="销售额", color="产品", stack=True)\n'
             'eazy_data_viz.line(df, x="月份", y="销售额", color="渠道", smooth=True)',
    )
    st.subheader("45 种图表，全部从 DataFrame 出发")
    st.markdown(
        "| 分类 | 图表 |\n| --- | --- |\n"
        "| 指标 | `kpi` `group_kpi` `gauge` `ring_progress` `progress` |\n"
        "| 趋势 | `line` `area` `area_pct` `theme_river` `sparkline` `trend` `candlestick` `calendar` `combo` `bar_pct` |\n"
        "| 对比 | `bar` `waterfall` `pareto` `lollipop` `dumbbell` `slope` `bump` `bullet` `target` `pictorial` `pyramid` `funnel` |\n"
        "| 结构 | `pie` `rose` `treemap` `sunburst` `tree` `tile` |\n"
        "| 分布 | `histogram` `box` `scatter` `quadrant` `heatmap` `matrix` `radar` `parallel` `sankey` `graph` |\n"
        "| 明细 | `table` `wordcloud` |"
    )
    st.subheader("示例数据")
    st.dataframe(df.head(8), use_container_width=True)

# ---------------------------------------------------------------------------
elif page == "经营驾驶舱":
    st.subheader("① 核心指标")
    total, profit = float(df["销售额"].sum()), float(df["利润"].sum())
    orders, margin = int(df["订单数"].sum()), profit / total * 100
    show(
        [
            eazy_data_viz.group_kpi(items=[
                {"label": "总销售额", "value": total, "fmt": "compact", "delta": 0.128},
                {"label": "总利润", "value": profit, "fmt": "compact", "delta": 0.086},
                {"label": "订单数", "value": orders, "fmt": "thousands", "delta": 0.064},
                {"label": "利润率", "value": margin, "fmt": "percent", "delta": -0.012},
                {"label": "客户数", "value": int(df["客户数"].sum()), "fmt": "thousands", "delta": 0.031},
                {"label": "单均金额", "value": total / orders, "fmt": "currency", "delta": 0.022},
            ], title="经营核心指标", subtitle="全年 · 环比趋势", height=150),
            eazy_data_viz.kpi(df, value="销售额", agg="sum", label="全年销售额",
                     delta=0.128, height=150),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.group_kpi(items=[...])   # 或 group_kpi(df) 自动按数值列取总量\n'
             'eazy_data_viz.kpi(df, value="销售额", agg="sum", label="全年销售额", delta=0.128)',
    )

    st.subheader("② 达成率")
    show(
        [
            eazy_data_viz.gauge(margin, label="整体利润率", min=0, max=40, fmt="percent", subtitle="目标 20%"),
            eazy_data_viz.ring_progress(78, label="年度目标达成率", max=100),
            eazy_data_viz.progress(d["g_region"], x="大区", y="销售额", max=600000, title="大区销售进度"),
            eazy_data_viz.progress(df, x="渠道", y="销售额", title="渠道销售占比"),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.gauge(19.9, label="利润率", min=0, max=40, fmt="percent")\n'
             'eazy_data_viz.ring_progress(78, label="目标达成率", max=100)\n'
             'eazy_data_viz.progress(region_df, x="大区", y="销售额", max=600000)',
    )

    st.subheader("③ 驾驶舱主视图")
    show(
        [
            eazy_data_viz.bar(df, x="大区", y="销售额", color="产品", stack=True, title="大区 × 产品"),
            eazy_data_viz.line(df, x="月份", y="销售额", color="渠道", smooth=True, title="月度趋势"),
            eazy_data_viz.pie(df, names="产品", values="销售额", donut=True, title="产品构成"),
            eazy_data_viz.heatmap(df, x="月份", y="大区", value="销售额", title="月份 × 大区"),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.show(\n'
             '    eazy_data_viz.bar(df, x="大区", y="销售额", color="产品", stack=True),\n'
             '    eazy_data_viz.line(df, x="月份", y="销售额", color="渠道"),\n'
             '    eazy_data_viz.pie(df, names="产品", values="销售额", donut=True),\n'
             '    eazy_data_viz.heatmap(df, x="月份", y="大区", value="销售额"),\n'
             '    cols=2, title="经营驾驶舱",\n)',
    )

    st.subheader("④ 明细")
    show(
        eazy_data_viz.table(df, columns=["月份", "大区", "省份", "产品", "渠道", "销售额", "订单数"],
                   limit=12, title="明细表（前 12 行）"),
        cols=1, theme=theme,
        code='eazy_data_viz.table(df, columns=[...], limit=12)',
    )

# ---------------------------------------------------------------------------
elif page == "指标卡与配色":
    st.subheader("KPI 卡片：目标达成 · 迷你走势 · 反向指标 · 联动重算")
    total_sales = float(df["销售额"].sum())
    show(
        [
            eazy_data_viz.kpi(df, value="销售额", label="全年销售额", delta=0.128, delta_label="同比",
                     target=total_sales * 1.25, hint="2024 全年 · 含税"),
            eazy_data_viz.kpi(df, value="利润", agg="sum", label="总利润", delta=0.086,
                     delta_label="同比", spark="利润", spark_x="月份", accent=1),
            eazy_data_viz.kpi(3.4, label="退货率（反向指标）", fmt="percent", delta=-0.086,
                     delta_label="同比", inverse=True, hint="inverse=True：下降是好事"),
            eazy_data_viz.kpi(df, value="订单数", label="订单数", fmt="thousands", delta=0.064,
                     delta_label="同比", unit=" 单", spark="订单数", spark_x="月份",
                     accent=2, link="g1", hint="点击下方图表，这张卡会重算"),
            eazy_data_viz.kpi(df, value="客户数", label="客户数", delta=-0.021,
                     delta_label="较上月", spark="客户数", spark_x="月份", accent=4),
            eazy_data_viz.kpi(19.9, label="利润率", fmt="percent", delta=0.021, delta_label="同比",
                     target=25, prefix="≈", hint="利润 / 销售额"),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.kpi(df, value="销售额", label="全年销售额", delta=0.128,\n'
             '         target=2000000, spark="销售额", spark_x="月份", link="g1")',
    )
    st.subheader("配色库：一套色板换掉整页风格")
    st.caption("侧栏「配色」可以切 7 套；下面这张同样的图用 7 套配色各画一次做对比。")
    _names = ["google", "antd", "tableau", "carbon", "echarts", "morandi", "tailwind"]
    show(
        [eazy_data_viz.bar(df, x="月份", y="销售额", color="产品", height=280,
                  title="月度销售 · " + n).palette(n) for n in _names],
        cols=1, theme=theme,
        code='for n in ["google", "antd", "tableau", "carbon", "echarts", "morandi", "tailwind"]:\n'
             '    eazy_data_viz.bar(df, x="月份", y="销售额", color="产品").palette(n)',
    )


if page == "趋势分析":
    st.subheader("折线 / 平滑 / 面积 / 阶梯")
    show(
        [
            eazy_data_viz.line(df, x="月份", y="销售额", color="渠道", smooth=True, title="多线：渠道月度"),
            eazy_data_viz.area(df, x="月份", y="订单数", title="面积图：订单数"),
            eazy_data_viz.line(df, x="月份", y="销售额", color="产品", step=True, title="阶梯线：产品月度"),
            eazy_data_viz.line(df, x="日期", y="销售额", area=True, smooth=False, title="时间轴：日销售额"),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.line(df, x="月份", y="销售额", color="渠道", smooth=True)\n'
             'eazy_data_viz.line(df, x="月份", y="销售额", color="产品", step=True)\n'
             'eazy_data_viz.line(df, x="日期", y="销售额", area=True)',
    )

    st.subheader("百分比堆叠 / 主题河流 / 迷你走势")
    show(
        [
            eazy_data_viz.area_pct(df, x="月份", y="销售额", color="产品", title="百分比堆叠面积"),
            eazy_data_viz.bar_pct(df, x="月份", y="销售额", color="渠道", title="百分比堆叠柱"),
            eazy_data_viz.theme_river(df, x="月份", color="产品", value="销售额", title="主题河流：产品结构"),
            eazy_data_viz.sparkline(df, x="月份", y="销售额", group="渠道", title="迷你走势：渠道月度"),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.area_pct(df, x="月份", y="销售额", color="产品")\n'
             'eazy_data_viz.bar_pct(df, x="月份", y="销售额", color="渠道")\n'
             'eazy_data_viz.theme_river(df, x="月份", color="产品", value="销售额")\n'
             'eazy_data_viz.sparkline(df, x="月份", y="销售额", group="渠道")',
    )

    st.subheader("趋势拟合 / K 线 / 日历 / 组合")
    show(
        [
            eazy_data_viz.trend(df, x="销售额", y="利润", color="产品", title="趋势散点 + 回归线"),
            eazy_data_viz.candlestick(d["ohlc"], date="日期", open="开盘", high="最高",
                             low="最低", close="收盘", title="K 线（近 45 天）"),
            eazy_data_viz.combo(df, x="月份", bar="销售额", line="利润", zoom=True, title="柱 + 线组合"),
            eazy_data_viz.calendar(d["daily"], date="日期", value="销售额", title="日历热力图"),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.trend(df, x="销售额", y="利润", color="产品")\n'
             'eazy_data_viz.combo(df, x="月份", bar="销售额", line="利润", zoom=True)',
    )

# ---------------------------------------------------------------------------
elif page == "对比与排名":
    st.subheader("柱状 / 横向 / 瀑布 / 帕累托")
    show(
        [
            eazy_data_viz.bar(df, x="省份", y="销售额", horizontal=True, top_n=8, title="条形图 TOP8"),
            eazy_data_viz.waterfall(df, x="产品", y="销售额", total=True, title="瀑布图：产品贡献"),
            eazy_data_viz.pareto(df, x="省份", y="销售额", top_n=8, title="帕累托：80/20"),
            eazy_data_viz.bar(df, x="大区", y="销售额", color="产品", stack=True, title="堆叠柱：大区 × 产品"),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.bar(df, x="省份", y="销售额", horizontal=True, top_n=8)\n'
             'eazy_data_viz.waterfall(df, x="产品", y="销售额", total=True)\n'
             'eazy_data_viz.pareto(df, x="省份", y="销售额", top_n=8)',
    )

    st.subheader("棒棒糖 / 哑铃 / 斜率 / 排名变化")
    show(
        [
            eazy_data_viz.lollipop(df, x="产品", y="销售额", title="棒棒糖图"),
            eazy_data_viz.dumbbell(d["half"], x="省份", y1="上半年", y2="下半年", title="哑铃图：上下半年"),
            eazy_data_viz.slope(d["half"].melt(id_vars=["省份"], var_name="期间", value_name="销售额"),
                       x="省份", y="销售额", color="期间", title="斜率图"),
            eazy_data_viz.bump(d["bump"], x="月份", y="销售额", group="产品", title="排名变化"),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.lollipop(df, x="产品", y="销售额")\n'
             'eazy_data_viz.dumbbell(half_df, x="省份", y1="上半年", y2="下半年")\n'
             'eazy_data_viz.bump(bump_df, x="月份", y="销售额", group="产品")',
    )

    st.subheader("目标 / 子弹 / 象形 / 金字塔 / 漏斗")
    show(
        [
            eazy_data_viz.bullet(d["g_region"], x="大区", actual="销售额", target_value=500000, title="子弹图 vs 目标"),
            eazy_data_viz.target(d["g_region"], x="大区", actual="销售额", target="目标", title="实际 vs 目标"),
            eazy_data_viz.pictorial(d["g_region"], x="大区", y="销售额", symbol="rect", title="象形柱图"),
            eazy_data_viz.pyramid(d["by_chan"], names="渠道", values="销售额", title="金字塔"),
            eazy_data_viz.funnel(df, names="产品", values="销售额", title="漏斗图"),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.bullet(region_df, x="大区", actual="销售额", target_value=500000)\n'
             'eazy_data_viz.target(region_df, x="大区", actual="销售额", target="目标")\n'
             'eazy_data_viz.pictorial(region_df, x="大区", y="销售额", symbol="rect")',
    )

# ---------------------------------------------------------------------------
elif page == "结构与占比":
    st.subheader("饼 / 玫瑰 / 矩形树图 / 旭日 / 树 / 瓦片")
    show(
        [
            eazy_data_viz.pie(df, names="产品", values="销售额", donut=True, title="环形图"),
            eazy_data_viz.rose(df, names="产品", values="销售额", title="玫瑰图"),
            eazy_data_viz.treemap(df, path=["大区", "省份"], value="销售额", title="矩形树图"),
            eazy_data_viz.sunburst(df, path=["大区", "省份"], value="销售额", title="旭日图"),
            eazy_data_viz.tree(df, path=["大区", "省份"], value="销售额", height=460, title="树图"),
            eazy_data_viz.tile(df, names="省份", values="销售额", top_n=8, title="瓦片图"),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.pie(df, names="产品", values="销售额", donut=True)\n'
             'eazy_data_viz.treemap(df, path=["大区", "省份"], value="销售额")\n'
             'eazy_data_viz.sunburst(df, path=["大区", "省份"], value="销售额")\n'
             'eazy_data_viz.tile(df, names="省份", values="销售额", top_n=8)',
    )

# ---------------------------------------------------------------------------
elif page == "分布与关系":
    st.subheader("直方 / 箱线 / 散点 / 四象限")
    show(
        [
            eazy_data_viz.histogram(df, column="销售额", bins=24, title="直方图"),
            eazy_data_viz.box(df, x="产品", y="销售额", title="箱线图"),
            eazy_data_viz.scatter(df, x="销售额", y="利润", color="产品", size="订单数", title="气泡散点"),
            eazy_data_viz.quadrant(d["prov_mean"], x="销售额", y="利润", size="订单数",
                          color="大区", title="四象限"),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.histogram(df, column="销售额", bins=24)\n'
             'eazy_data_viz.box(df, x="产品", y="销售额")\n'
             'eazy_data_viz.quadrant(prov_df, x="销售额", y="利润", size="订单数", color="大区")',
    )

    st.subheader("热力 / 相关矩阵 / 雷达 / 平行坐标")
    show(
        [
            eazy_data_viz.heatmap(df, x="月份", y="大区", value="销售额", title="热力图"),
            eazy_data_viz.matrix(df, columns=["销售额", "订单数", "利润", "客户数"], title="相关矩阵"),
            eazy_data_viz.radar(df, x="产品", y="销售额", color="大区", agg="mean", title="雷达图"),
            eazy_data_viz.parallel(d["par"], dims=["销售额", "订单数", "利润", "客户数"],
                          color="大区", title="平行坐标"),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.heatmap(df, x="月份", y="大区", value="销售额")\n'
             'eazy_data_viz.matrix(df, columns=["销售额", "订单数", "利润", "客户数"])\n'
             'eazy_data_viz.radar(df, x="产品", y="销售额", color="大区", agg="mean")',
    )

    st.subheader("桑基 / 关系图")
    sankey = df.groupby(["渠道", "产品"], as_index=False)["销售额"].sum()
    sankey["来源"], sankey["去向"] = sankey["渠道"], sankey["产品"]
    graph = (df.groupby(["大区", "城市"], as_index=False)["销售额"].sum()
               .sort_values("销售额", ascending=False).head(12))
    graph["源"], graph["目标"] = graph["大区"], graph["城市"]
    show(
        [
            eazy_data_viz.sankey(sankey, source="来源", target="去向", value="销售额", title="桑基图"),
            eazy_data_viz.graph(graph, source="源", target="目标", value="销售额", title="关系图"),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.sankey(flow_df, source="来源", target="去向", value="销售额")\n'
             'eazy_data_viz.graph(node_df, source="源", target="目标", value="销售额")',
    )

# ---------------------------------------------------------------------------
elif page == "地图可视化":
    st.subheader("区域填色地图：中国省级 / 世界国家")
    map_prov = df.groupby("省份", as_index=False)["销售额"].sum()
    map_world = __import__("pandas").DataFrame({
        "国家": ["中国", "美国", "德国", "日本", "巴西", "印度", "俄罗斯", "澳大利亚"],
        "销售额": [1630000, 980000, 520000, 460000, 210000, 190000, 150000, 90000],
    })
    show(
        [
            eazy_data_viz.geo_map(map_prov, region="省份", value="销售额",
                                  title="中国省级地图（区域填色）"),
            eazy_data_viz.geo_map(map_world, region="国家", value="销售额", map="world",
                                  title="世界地图（国家填色）"),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.geo_map(df, region="省份", value="销售额")           # 中国\n'
             'eazy_data_viz.geo_map(df, region="国家", value="销售额", map="world")  # 世界',
    )

    st.subheader("城市气泡 / 城市飞线（按真实城市坐标落点）")
    map_city = df.groupby("城市", as_index=False)["销售额"].sum()
    _cities = list(map_city["城市"])
    flow = __import__("pandas").DataFrame([
        {"出发城市": _cities[i % len(_cities)], "到达城市": _cities[(i * 3 + 1) % len(_cities)],
         "件数": 320 - i * 30} for i in range(min(8, len(_cities)))])
    show(
        [
            eazy_data_viz.map_bubble(map_city, region="城市", value="销售额",
                                     title="城市气泡图"),
            eazy_data_viz.map_flow(flow, source="出发城市", target="到达城市", value="件数",
                                   title="城市飞线图"),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.map_bubble(df, region="城市", value="销售额")\n'
             'eazy_data_viz.map_flow(flow_df, source="出发城市", target="到达城市", value="件数")',
    )

    st.info("内置中国 / 世界地图（本地 GeoJSON，离线可用）；region 支持「广东 / 广东省」"
            "「广州 / 广州市」两种写法；地图同样支持 drill 下钻与 link 联动。")

# ---------------------------------------------------------------------------
elif page == "明细与文本":
    st.subheader("表格 / 词云")
    show(
        [
            eazy_data_viz.table(df, columns=["月份", "大区", "省份", "产品", "渠道", "销售额", "订单数"],
                       limit=12, title="明细表"),
            eazy_data_viz.wordcloud(df, names="城市", values="销售额", top_n=12, title="词云"),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.table(df, columns=[...], limit=12)\n'
             'eazy_data_viz.wordcloud(df, names="城市", values="销售额", top_n=12)',
    )
    st.subheader("进度条 / 指标组")
    show(
        [
            eazy_data_viz.progress(df, x="省份", y="销售额", top_n=8, title="省份销售进度"),
            eazy_data_viz.group_kpi(df, names="大区", values="销售额", title="大区销售额", height=140),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.progress(df, x="省份", y="销售额", top_n=8)\n'
             'eazy_data_viz.group_kpi(df, names="大区", values="销售额")',
    )

# ---------------------------------------------------------------------------
elif page == "交互：下钻 + 联动":
    st.subheader("① 下钻：点击逐级深入（大区 → 省份 → 城市）")
    st.caption("点击柱子下钻；顶部面包屑可回退任意层级。全部在浏览器内完成，无服务器往返。")
    show(
        eazy_data_viz.bar(df, x="大区", y="销售额", color="产品",
                 drill=["大区", "省份", "城市"], title="点击下钻：大区 → 省份 → 城市"),
        cols=1, theme=theme,
        code='eazy_data_viz.bar(df, x="大区", y="销售额", color="产品",\n'
             '          drill=["大区", "省份", "城市"])',
    )

    st.subheader("② 联动：同组图表点击即交叉筛选")
    st.caption('四张图都加 `link="g1"`；点击任意柱/点，其他图一起过滤，顶部出现筛选 chip，再点一次取消。')
    show(
        [
            eazy_data_viz.bar(df, x="大区", y="销售额", link="g1", title="按大区"),
            eazy_data_viz.bar(df, x="产品", y="销售额", link="g1", title="按产品"),
            eazy_data_viz.line(df, x="月份", y="销售额", link="g1", title="按月趋势"),
            eazy_data_viz.pie(df, names="渠道", values="销售额", link="g1", title="按渠道"),
        ],
        cols=2, theme=theme,
        code='eazy_data_viz.show(\n'
             '    eazy_data_viz.bar(df, x="大区", y="销售额", link="g1"),\n'
             '    eazy_data_viz.bar(df, x="产品", y="销售额", link="g1"),\n'
             '    eazy_data_viz.line(df, x="月份", y="销售额", link="g1"),\n'
             '    eazy_data_viz.pie(df, names="渠道", values="销售额", link="g1"),\n'
             '    cols=2, title="点击任意图形联动筛选",\n)',
    )

    st.subheader("③ 缩放 + 组合图")
    show(
        eazy_data_viz.combo(df, x="日期", bar="销售额", line="订单数", zoom=True,
                   title="缩放：拖拽下方滑块或滚轮"),
        cols=1, theme=theme,
        code='eazy_data_viz.combo(df, x="日期", bar="销售额", line="订单数", zoom=True)',
    )

elif page == "v2 双向事件":
    st.subheader("components v2：点击图表 → 事件回传 Python")
    st.caption(
        "本页用 `st.components.v2` 渲染：**没有 iframe**、高度按内容自适应，"
        "而且点击柱状图会把 `select` 事件回传给 Python（旧版 Streamlit 自动回退 v1 iframe）。"
    )
    _sel_df = df.groupby("大区", as_index=False)["销售额"].sum()
    show(
        eazy_data_viz.bar(_sel_df, x="大区", y="销售额", link="v2demo",
                          title="点击任意柱子 → Python 收到事件"),
        cols=1, theme=theme, events=True,
        code='result = eazy_data_viz.streamlit_dashboard(\n'
             '    [eazy_data_viz.bar(df, x="大区", y="销售额")],\n'
             '    on_select=lambda: None,\n'
             ')\n'
             'if result.select:\n'
             '    st.write(result.select)   # {title, type, dim, value, drill, link}',
    )
    st.markdown("**最近一次点击（存在 `st.session_state['_last_select']`）**")
    st.json(st.session_state.get("_last_select") or {})

st.divider()
st.caption(
    "eazy_data_viz · 多图共享同一份数据，单页 HTML 约 1.4 MB（含 ECharts，离线可用）；"
    "点击「◐」可切换深浅色，点击「重置联动」清空所有筛选。"
)
