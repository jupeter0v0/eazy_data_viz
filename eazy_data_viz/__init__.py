"""eazy_data_viz —— 给 pandas 用的交互式图表库（HTML / Streamlit）。

对外只有：一组图表函数 + Chart 对象 + dashboard。
用户不需要写任何 JSON / JS / 前端配置。

    import eazy_data_viz
    eazy_data_viz.bar(df, x="月份", y="销售额", color="地区", title="月度销售").show()
"""
from __future__ import annotations

from . import frame
from .chart import (
    AGGS,
    FORMATS,
    Chart,
    area,
    bar,
    box,
    combo,
    funnel,
    gauge,
    heatmap,
    histogram,
    kpi,
    line,
    pie,
    scatter,
    treemap,
)
from .charts_extra import (
    area_pct,
    bar_pct,
    bullet,
    bump,
    calendar,
    candlestick,
    dumbbell,
    gantt,
    graph,
    group_kpi,
    lollipop,
    matrix,
    parallel,
    pareto,
    pictorial,
    progress,
    pyramid,
    quadrant,
    radar,
    ring_progress,
    rose,
    sankey,
    slope,
    sparkline,
    sunburst,
    table,
    target,
    theme_river,
    tile,
    tree,
    trend,
    waterfall,
    wordcloud,
)
from .maps import geo_map, map_bubble, map_flow
from . import palette
from .render import Dashboard, dashboard
from .render import streamlit_show as _streamlit_show
from .streamlit_v2 import is_available as streamlit_available

__version__ = "1.3.2"

__all__ = [
    "Chart",
    "Dashboard",
    "dashboard",
    "streamlit_dashboard",
    "streamlit_available",
    "show",
    # ---- 基础图表（14）----
    "bar",
    "line",
    "area",
    "pie",
    "scatter",
    "histogram",
    "heatmap",
    "box",
    "funnel",
    "treemap",
    "gauge",
    "kpi",
    "combo",
    # ---- 对比 / 排名（10）----
    "waterfall",
    "bullet",
    "lollipop",
    "dumbbell",
    "pareto",
    "slope",
    "bump",
    "pyramid",
    "target",
    "pictorial",
    # ---- 趋势 / 分布 / 关系（12）----
    "area_pct",
    "bar_pct",
    "sparkline",
    "trend",
    "quadrant",
    "matrix",
    "radar",
    "parallel",
    "histogram",
    "scatter",
    "box",
    "rose",
    # ---- 层级 / 流向（8）----
    "sunburst",
    "tree",
    "sankey",
    "graph",
    "theme_river",
    "calendar",
    "gantt",
    "candlestick",
    # ---- 驾驶舱组件（5）----
    "progress",
    "tile",
    "table",
    "wordcloud",
    # ---- 地图（3）----
    "geo_map",
    "map_bubble",
    "map_flow",
    "group_kpi",
    "ring_progress",
    # ---- 配色 / 工具 ----
    "palette",
    "set_palette",
    "palettes",
    "sample_df",
    "help",
    "gallery",
    "AGGS",
    "FORMATS",
    "__version__",
]


# --------------------------------------------------------------------------
# 一个函数显示多张图
# --------------------------------------------------------------------------
def show(*charts, cols=2, title=None, desc=None, theme=None, palette=None):
    """显示一张或多张图。

    >>> eazy_data_viz.show(c1, c2, cols=2, title="经营看板", palette="antd")
    """
    items = []
    for c in charts:
        if isinstance(c, (list, tuple)):
            items.extend(c)
        else:
            items.append(c)
    if len(items) == 1:
        items[0].show()
        return items[0]
    d = Dashboard(items, cols=cols, title=title, desc=desc, theme=theme,
                  palette=palette)
    d.show()
    return d


# --------------------------------------------------------------------------
# Streamlit（components v2：无 iframe、高度自适应、点击回传 Python）
# --------------------------------------------------------------------------
def streamlit_dashboard(charts, *, cols=2, title=None, desc=None, theme=None,
                        palette=None, height=None, key=None, on_select=None):
    """在 Streamlit 页面里用 ``st.components.v2`` 渲染一张看板。

    相比 ``dashboard(...).show()``（内部也会优先走 v2），这个函数把
    :class:`~eazy_data_viz.streamlit_v2` 的返回值直接交给你，
    从而可以读取 **图表点击事件**（``result.select``）。

    参数
    ----
    charts : Chart | list[Chart]
        一张或多张图，放同一个看板里才能跨图联动。
    cols : int
        网格列数（默认 2）。
    title, desc, theme, palette
        与 :func:`dashboard` 相同。
    height : int or None
        组件高度（像素）；``None`` 表示按内容自适应（推荐）。
    key : str or None
        组件实例 key（用于 ``st.session_state[key]``）。
    on_select : callable or None
        图表点击回调（无参数）；回调触发后可用返回值读取最近一次点击。

    返回
    ----
    ComponentResult
        常用字段 ``result.select``：``{chart, title, type, dim, value, drill, link}``。

    示例
    ----
    >>> import streamlit as st
    >>> import eazy_data_viz as edv
    >>> df = edv.sample_df()
    >>> charts = [edv.kpi(df, value="销售额", label="全年销售额"),
    ...           edv.bar(df, x="大区", y="销售额", link="g1")]
    >>> result = edv.streamlit_dashboard(charts, title="经营驾驶舱")
    >>> if result.select:
    ...     st.write("你点了：" + str(result.select.get("value")))
    """
    if isinstance(charts, (list, tuple)):
        items = list(charts)
    else:
        items = [charts]
    from .streamlit_v2 import render_dashboard

    return render_dashboard(
        items,
        title=title,
        desc=desc,
        cols=cols,
        theme=theme,
        palette=palette,
        height=height,
        key=key,
        on_select=on_select,
    )


# --------------------------------------------------------------------------
# 配色库
# --------------------------------------------------------------------------
def set_palette(name):
    """设置全局默认配色库（影响之后创建的图）。

    可用：google（默认，Google 品牌色）/ antd（Ant Design）/ tableau /
    carbon（IBM）/ echarts / morandi（莫兰迪低饱和）/ tailwind。

    >>> eazy_data_viz.set_palette("antd")
    >>> eazy_data_viz.bar(df, x="大区", y="销售额").show()
    >>> eazy_data_viz.bar(df, x="大区", y="销售额").palette("tableau").show()  # 单图覆盖
    """
    return palette.set_default(name)


def palettes(verbose=True):
    """列出所有配色库；返回名字列表。"""
    usable = palette.names()
    if verbose:
        print("可用配色库（eazy_data_viz.set_palette(名字) 或 Chart.palette(名字)）：")
        for item in palette.listing():
            print("  %-9s %-10s %s" % (item["name"], item["label"], item["desc"]))
            swatch = "  ".join(item["colors"][:8])
            print("            " + swatch)
        print("\n当前默认：%s" % palette.current())
    return usable


# --------------------------------------------------------------------------
# 示例数据（开箱即用，方便用户先跑通再换自己的数据）
# --------------------------------------------------------------------------
def sample_df(rows=1500, seed=42):
    """生成一份示例销售数据（日期 / 月份 / 大区 / 省份 / 城市 / 产品 / 渠道 / 销售额 ...）。

    数据按"日期 × 大区"的网格构造：趋势 + 季节性 + 周末效应 + 大区/产品/渠道差异 +
    少量噪声。同一天里所有大区都在，所以按日期或按月份聚合后曲线平滑，适合直接演示
    图表（纯随机数据会造成锯齿）。

    >>> df = eazy_data_viz.sample_df()
    >>> eazy_data_viz.bar(df, x="月份", y="销售额", color="产品").show()
    """
    import numpy as np
    import pandas as pd

    rng = np.random.RandomState(seed)
    regions = {
        "华东": (["上海", "江苏", "浙江"], 1.35),
        "华北": (["北京", "天津", "河北"], 1.10),
        "华南": (["广东", "福建"], 1.20),
        "西部": (["四川", "陕西"], 0.78),
    }
    products = {"智能终端": (1.25, 0.14, 1150.0), "云服务": (0.95, 0.26, 460.0),
                "行业软件": (1.05, 0.22, 880.0), "运维服务": (0.55, 0.19, 330.0)}
    channels = ["直销", "渠道代理", "线上商城"]
    chan_scale = {"直销": 1.10, "渠道代理": 0.95, "线上商城": 0.88}
    months = ["%d月" % m for m in range(1, 13)]

    # 省份 → 省会城市（示例数据里的「城市」列用真实城市名，方便地图/城市维度演示）
    city_of = {"上海": "上海市", "江苏": "南京市", "浙江": "杭州市", "北京": "北京市",
               "天津": "天津市", "河北": "石家庄市", "广东": "广州市", "福建": "厦门市",
               "四川": "成都市", "陕西": "西安市"}
    flat = [(reg, prov, rf) for reg, (provs, rf) in regions.items() for prov in provs]
    n_reg = len(flat)  # 12 个"大区-省份"组合
    n_dates = max(1, int(round(rows / float(n_reg))))
    days = pd.date_range("2024-01-01", "2024-12-30", periods=n_dates)
    doy = np.array([d.dayofyear for d in days], dtype=float)
    trend = 1.0 + 0.30 * doy / 365.0
    season = (1.0 + 0.20 * np.sin((doy - 55) / 365.0 * 2 * np.pi)
              + 0.12 * np.sin((doy - 300) / 365.0 * 4 * np.pi))
    weekend = np.where(np.array([d.dayofweek for d in days]) >= 5, 1.10, 0.97)
    day_base = trend * season * weekend

    records = []
    for di, day in enumerate(days):
        for ri, (reg, prov, rscale) in enumerate(flat):
            pnames = list(products)
            pname = pnames[(di * 5 + ri) % len(pnames)]
            pscale, pmargin, price = products[pname]
            chan = channels[(di + ri) % len(channels)]
            noise = rng.normal(1.0, 0.05)
            sales = 900.0 * day_base[di] * pscale * rscale * chan_scale[chan] * noise
            orders = max(1, int(round(sales / price)))
            profit = sales * pmargin * rng.normal(1.0, 0.04)
            customers = max(1, int(round(orders * rng.uniform(0.55, 0.85))))
            records.append((day, "%d月" % day.month, reg, prov,
                            city_of.get(prov, prov + "市"),
                            pname, chan, round(sales, 2), orders,
                            round(profit, 2), customers))

    df = pd.DataFrame(records, columns=["日期", "月份", "大区", "省份", "城市", "产品",
                                        "渠道", "销售额", "订单数", "利润", "客户数"])
    df["月份"] = pd.Categorical(df["月份"], categories=months, ordered=True)
    if len(df) > rows:  # rows 不能被 12 整除时截断到最接近的整网格
        df = df.iloc[:rows]
    return df.reset_index(drop=True)


# --------------------------------------------------------------------------
# 说明 / gallery
# --------------------------------------------------------------------------
def help():  # noqa: A001 - 故意覆盖内建名，eazy_data_viz.help() 更自然
    """打印速查表。"""
    text = """
eazy_data_viz · pandas 交互式图表库（经营驾驶舱版）  v%s
=========================================================
一行画图：
    import eazy_data_viz
    df = eazy_data_viz.sample_df()
    eazy_data_viz.bar(df, x="月份", y="销售额", color="产品", title="月度销售").show()

45 种图表，全部 = 函数名，参数只有「数据 + 列名 + 少量开关」
注意：Python 里直接 `import eazy_data_viz`，下面写成 ``eazy_data_viz.xxx`` 只是为了标注模块。
--------------------------------------------------------------------------------
【基础 14】bar / line / area / pie / scatter / histogram / heatmap / box /
          funnel / treemap / gauge / kpi / combo / rose
【对比排名 10】waterfall(瀑布) bullet(子弹) lollipop(棒棒糖) dumbbell(哑铃)
          pareto(帕累托) slope(斜率) bump(排名变化) pyramid(金字塔)
          target(目标对比) pictorial(象形柱)
【趋势分布关系 12】area_pct / bar_pct(百分比堆叠) sparkline(迷你线) trend(趋势线)
          quadrant(四象限) matrix(相关矩阵) radar(雷达) parallel(平行坐标)
          histogram / scatter / box / rose
【层级流向 8】sunburst(旭日) tree(树图) sankey(桑基) graph(关系图)
          theme_river(主题河流) calendar(日历) gantt(甘特) candlestick(K线)
【驾驶舱组件 5】progress(进度条) tile(瓦片) table(明细表) wordcloud(词云)
          group_kpi(指标组)
【额外】ring_progress(环形进度)
【地图 3】geo_map(区域填色) map_bubble(气泡地图) map_flow(飞线地图)
          内置 china / world 地图；region 列可写「广东 / 广东省」，城市名支持「广州 / 广州市」

常用签名（其它参数见各函数 docstring）
--------------------------------------------------------------------------------
    eazy_data_viz.bar      (df, x, y=None, color=None, stack=False, horizontal=False,
                   sort=None, top_n=None, percent=False, drill=[...], link="g1")
    eazy_data_viz.line     (df, x, y=None, color=None, area=False, smooth=True,
                   step=False, percent=False, zoom="auto")
    eazy_data_viz.pie      (df, names, values=None, donut=False)
    eazy_data_viz.heatmap  (df, x, y, value, labels=False)
    eazy_data_viz.combo    (df, x, bar="销售额", line="利润")
    eazy_data_viz.kpi      (df, value="销售额", label="总销售额", delta=0.128, delta_label="同比",
                   target=2000000, spark="销售额", spark_x="月份", hint="2024 全年")
    eazy_data_viz.gauge    (87.5, label="完成率", max=100)
    eazy_data_viz.waterfall(df, x="阶段", y="金额", total=True)
    eazy_data_viz.bullet   (df, x="部门", actual="完成", target="目标")
    eazy_data_viz.dumbbell (df, x="省份", y1="去年", y2="今年")
    eazy_data_viz.pareto   (df, x="产品", y="销售额")
    eazy_data_viz.sankey   (df, source="渠道", target="产品", value="销售额")
    eazy_data_viz.candlestick(df, date="日期", open="开", high="高", low="低", close="收")
    eazy_data_viz.geo_map  (df, region="省份", value="销售额")
    eazy_data_viz.map_bubble(df, region="省份", value="销售额")
    eazy_data_viz.map_flow (df, source="发货省", target="收货省", value="件数")
    eazy_data_viz.gantt    (df, task="任务", start="开始", end="结束", color="负责人")
    eazy_data_viz.ring_progress(72.5, label="完成率")
    eazy_data_viz.group_kpi(df, items=[{"label": "总销售额", "value": 1630000, "fmt": "compact"}])

KPI 卡片（驾驶舱指标头）
    eazy_data_viz.kpi(df, value="销售额", label="全年销售额", delta=0.128, delta_label="同比",
             target=2000000, spark="销售额", spark_x="月份", unit="元",
             hint="2024 全年 · 含税", link="g1")
    * delta 传 0.128 显示 ▲12.8%%；inverse=True 表示越小越好（成本/投诉率）
    * target 出现右上角达成率 + 底部进度条；spark + spark_x 出现迷你走势
    * 传 link 后，同组图被点击过滤时 KPI 数字会跟着重算（前端完成）
    * 也可以直接给数：eazy_data_viz.kpi(1630000, label="销售额", delta=0.128)

配色库（7 套，参照 Google / Ant Design / Tableau / IBM Carbon / ECharts / 莫兰迪 / Tailwind）
    eazy_data_viz.set_palette("antd")                       # 全局默认
    eazy_data_viz.bar(...).palette("tableau")                # 单图覆盖
    eazy_data_viz.palettes()                                 # 列出全部 + 色板
    eazy_data_viz.dashboard(..., palette="morandi")          # 整个看板一套配色
    * 页面右上角也有「配色：xxx」下拉框，运行时可切换

公用参数（几乎所有图都支持）
    title / subtitle / xtitle / ytitle / xlim / ylim / fmt / theme("light"/"dark")
    height / section（看板分区标题）/ legend / labels / max_rows
    palette（单图配色）/ drill（下钻层级）/ link（联动组名）

交互能力（全部前端完成，不触发 Python 重算）
--------------------------------------------
* 图例点选过滤、悬浮 tooltip、数据缩放条、右上角工具箱（另存 PNG）
* 下钻：drill=["大区", "省份", "城市"]，点击图形逐级下钻，面包屑返回
* 联动：多张图传同一个 link="销售"，点任意一张图，其它图自动联动过滤
* 看板：eazy_data_viz.dashboard(c1, c2, c3, cols=2, title="经营驾驶舱").show()
* 右上角 ◐ 切换深色/浅色主题，↺ 一键清除所有联动筛选

单独导出 HTML / 在 Streamlit 中使用
-----------------------------------
    eazy_data_viz.bar(df, x="月份", y="销售额").save("chart.html")
    eazy_data_viz.dashboard(c1, c2, c3, cols=3, title="驾驶舱").save("cockpit.html")
    # Streamlit（推荐 v2，无 iframe / 自动高度 / 点击回传）
    #   result = eazy_data_viz.streamlit_dashboard(c1, c2, c3, title="驾驶舱")
    #   旧版 Streamlit 自动回退：st.components.v1.html(dash.to_html(), height=...)

完整示例见 gallery：eazy_data_viz.gallery()
""" % __version__
    print(text)
    return text


def gallery(open_browser=True):
    """打开自带 gallery。

    * 在 Streamlit 里运行时：只打印说明；
    * 否则：优先用 ``streamlit run`` 启动画廊（需要已安装 streamlit），
      同时返回静态 gallery.html 的路径。
    """
    import os
    import subprocess
    import sys
    import webbrowser

    base = os.path.dirname(os.path.abspath(__file__))
    static = os.path.join(base, "gallery", "gallery.html")
    app = os.path.join(base, "gallery", "app.py")

    if os.environ.get("STREAMLIT_SERVER_PORT") or os.environ.get("STREAMLIT_RUN") == "1":
        print("已在 Streamlit 中运行；直接打开 gallery/app.py：%s" % app)
        return static

    try:
        import streamlit  # noqa: F401

        cmd = [sys.executable, "-m", "streamlit", "run", app, "--server.headless=true"]
        print("启动 Streamlit gallery：%s" % " ".join(cmd))
        subprocess.Popen(cmd)
        return app
    except Exception:
        print("未检测到 streamlit，改用静态文件：%s" % static)
        if open_browser and os.path.exists(static):
            webbrowser.open("file://" + static.replace("\\", "/"))
        return static
