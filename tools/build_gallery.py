"""生成 gallery.html：Material Design 3 风格、40+ 种图表的经营驾驶舱总览。

用法::

    python tools/build_gallery.py

输出:
    <repo>/gallery.html
    <repo>/eazy_data_viz/gallery/gallery.html
"""
from __future__ import annotations

import os
import sys
from collections import OrderedDict

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import eazy_data_viz  # noqa: E402
from eazy_data_viz import charts_extra as X  # noqa: E402


# ----------------------------------------------------------------------
# 录制每张图的 Python 代码：gallery 卡片右上角「代码」可展开查看 / 复制
# ----------------------------------------------------------------------
_HELPERS = {"show", "dashboard", "sample_df", "help", "gallery",
            "set_palette", "palettes", "Chart", "Dashboard"}


def _var_name(obj, frame):
    """把 DataFrame 还原成调用处的变量名（df / g_region / daily ...）。"""
    if not isinstance(obj, pd.DataFrame):
        return None
    for scope in (frame.f_locals, frame.f_globals):
        for name, val in scope.items():
            if val is obj and not name.startswith("_"):
                return name
    return None


def _lit(value, frame):
    if isinstance(value, pd.DataFrame):
        return _var_name(value, frame) or "df"
    if isinstance(value, str):
        return '"%s"' % value.replace("\\", "\\\\").replace('"', '\\"')
    if isinstance(value, float):
        # 去掉浮点尾巴：1631033.5699999998 -> 1631033.57
        return repr(round(value, 4))
    if isinstance(value, list):
        return "[" + ", ".join(_lit(v, frame) for v in value) + "]"
    if isinstance(value, tuple):
        return "(" + ", ".join(_lit(v, frame) for v in value) + ")"
    if isinstance(value, dict):
        return "{" + ", ".join("%s: %s" % (_lit(k, frame), _lit(v, frame))
                                for k, v in value.items()) + "}"
    return repr(value)


def _fmt_call(name, args, kwargs, frame):
    # 代码面板只展示用户真正要写的东西：跳过 None（默认值）和画廊内部的 section
    kwargs = OrderedDict((k, v) for k, v in kwargs.items() if k != "section" and v is not None)
    parts = [_lit(a, frame) for a in args]
    parts += ["%s=%s" % (k, _lit(v, frame)) for k, v in kwargs.items()]
    one = "eazy_data_viz.%s(%s)" % (name, ", ".join(parts))
    if len(one) <= 92:
        return one
    lines = ["eazy_data_viz.%s(" % name]
    lines += ["    %s," % p for p in parts]
    lines.append(")")
    return "\n".join(lines)


def _instrument(module):
    """包装模块里的图表函数，调用后把源码写进 chart.spec['code']。"""
    for name in list(dir(module)):
        if name.startswith("_") or name in _HELPERS:
            continue
        func = getattr(module, name, None)
        if not callable(func) or not getattr(func, "__module__", "").startswith("eazy_data_viz"):
            continue

        def make(fn, fname):
            def wrapper(*args, **kwargs):
                frame = sys._getframe(1)
                chart = fn(*args, **kwargs)
                try:
                    chart.spec["code"] = _fmt_call(fname, args, kwargs, frame)
                except Exception:  # 代码录制失败不影响出图
                    pass
                return chart
            wrapper.__name__ = fname
            wrapper.__doc__ = getattr(fn, "__doc__", None)
            return wrapper

        setattr(module, name, make(func, name))


_instrument(eazy_data_viz)
_instrument(X)


def _sec(chart, name):
    chart.spec["section"] = name
    return chart


def main():
    df = eazy_data_viz.sample_df()
    sections = []

    # ------------------------------------------------------------------
    # 派生数据
    # ------------------------------------------------------------------
    g_region = df.groupby("大区", as_index=False)["销售额"].sum()
    g_region["目标"] = (g_region["销售额"] * 1.12).round(2)

    df = df.copy()
    df["半年"] = np.where(df["日期"].dt.month <= 6, "上半年", "下半年")
    half = (df.groupby(["省份", "半年"], as_index=False)["销售额"].sum()
              .pivot(index="省份", columns="半年", values="销售额")
              .reset_index())
    half = half.sort_values("下半年", ascending=False).head(6)

    by_prov = df.groupby("省份", as_index=False).agg(
        销售额=("销售额", "sum"), 利润=("利润", "sum"),
        订单数=("订单数", "sum"), 客户数=("客户数", "sum"))
    by_prov = by_prov.merge(df.groupby("省份", as_index=False)["大区"].first(), on="省份")
    by_prov = by_prov.sort_values("销售额", ascending=False).head(8)

    daily = df.groupby("日期", as_index=False)["销售额"].sum().sort_values("日期")
    daily60 = daily.tail(45).reset_index(drop=True)

    # K 线：用每日销售额合成 OHLC（演示用）
    closes = daily60["销售额"].to_numpy(dtype=float)
    opens = np.concatenate([[closes[0] * 0.98], closes[:-1]])
    ohlc = pd.DataFrame({
        "日期": daily60["日期"].dt.strftime("%Y-%m-%d"),
        "开盘": opens.round(2),
        "收盘": closes.round(2),
        "最低": (np.minimum(opens, closes) * 0.97).round(2),
        "最高": (np.maximum(opens, closes) * 1.03).round(2),
    })

    # 甘特图
    gantt_df = pd.DataFrame([
        ("市场调研", "2024-01-05", "2024-02-02", "产品部"),
        ("产品立项", "2024-02-05", "2024-02-29", "产品部"),
        ("原型设计", "2024-03-01", "2024-03-28", "设计部"),
        ("开发联调", "2024-03-25", "2024-05-20", "研发部"),
        ("测试验收", "2024-05-15", "2024-06-14", "质量部"),
        ("灰度发布", "2024-06-10", "2024-07-05", "研发部"),
        ("正式发布", "2024-07-08", "2024-07-26", "产品部"),
        ("运营复盘", "2024-07-22", "2024-08-16", "运营部"),
    ], columns=["任务", "开始", "结束", "负责部门"])

    # 桑基 / 关系图
    sankey_df = df.groupby(["渠道", "产品"], as_index=False)["销售额"].sum()
    sankey_df["来源"] = sankey_df["渠道"]
    sankey_df["去向"] = sankey_df["产品"]
    sankey_df["金额"] = sankey_df["销售额"] * 3 + 50000  # 让连线更饱满

    graph_df = (df.groupby(["大区", "城市"], as_index=False)["销售额"].sum()
                  .sort_values("销售额", ascending=False).head(14))
    graph_df["源"] = graph_df["大区"]
    graph_df["目标"] = graph_df["城市"]

    # 上下半年：销售额（哑铃图）与利润率（斜率图）
    _half = df.assign(期间=np.where(df["日期"].dt.month <= 6, "上半年", "下半年"))
    half = (_half.groupby(["省份", "期间"], as_index=False)[["销售额", "利润"]].sum())
    half["利润率"] = (half["利润"] / half["销售额"] * 100).round(2)
    half_margin = half[["省份", "期间", "利润率"]].copy()
    # 斜率图：产品销售额的上下半年变化（人为给每个产品不同增速，让线条有升有降）
    _sp = _half.pivot_table(index="产品", columns="期间", values="销售额", aggfunc="sum")
    _sp["下半年"] = _sp["下半年"] * pd.Series(
        {"智能终端": 0.93, "云服务": 1.22, "行业软件": 1.04, "运维服务": 0.86}
    ).reindex(_sp.index).fillna(1.0)
    slope_df = _sp.reset_index().melt(id_vars="产品", var_name="期间", value_name="销售额")
    half = half.pivot(index="省份", columns="期间", values="销售额").reset_index()

    # 帕累托 / 金额类
    by_chan = df.groupby("渠道", as_index=False)["销售额"].sum()

    # 排名变化：给每个产品叠加不同的季节因子，让月度排名真的会变
    bump_df = df.groupby(["月份", "产品"], as_index=False)["销售额"].sum()
    _mon = bump_df["月份"].astype(str).str.replace("月", "", regex=False).astype(int)
    _phase = bump_df["产品"].map({"智能终端": 0, "云服务": 3, "行业软件": 6, "运维服务": 9}).astype(float)
    bump_df["销售额"] = (bump_df["销售额"]
                     * (1 + 0.45 * np.sin((_mon + _phase) / 12.0 * 2 * np.pi))).round(2)

    # 平行坐标：按大区聚合，每个大区一条折线
    par_df = df.groupby("大区", as_index=False)[["销售额", "订单数", "利润", "客户数"]].mean()
    # 四象限：省份均值（连续变量，点位才拉得开）
    prov_mean = df.groupby(["大区", "省份"], as_index=False)[["销售额", "利润", "订单数"]].mean()

    # 地图：省份填色 / 城市气泡 / 城市飞线 / 世界地图
    map_prov = df.groupby("省份", as_index=False).agg(销售额=("销售额", "sum"))
    map_city = df.groupby("城市", as_index=False).agg(销售额=("销售额", "sum"))
    _cities = list(map_city["城市"])
    _pairs = [(_cities[0], _cities[3], 320), (_cities[1], _cities[4], 280),
              (_cities[3], _cities[2], 260), (_cities[5], _cities[0], 210),
              (_cities[6], _cities[1], 180), (_cities[7], _cities[2], 150),
              (_cities[8], _cities[0], 120), (_cities[9], _cities[1], 100)]
    map_flow_df = pd.DataFrame([{"出发城市": a, "到达城市": b, "件数": v}
                                for a, b, v in _pairs])
    map_world = pd.DataFrame({
        "国家": ["中国", "美国", "德国", "日本", "巴西", "印度", "俄罗斯", "澳大利亚"],
        "销售额": [1630000, 980000, 520000, 460000, 210000, 190000, 150000, 90000],
    })

    # ------------------------------------------------------------------
    # ① 核心指标
    # ------------------------------------------------------------------
    s = "① 核心指标 · KPI 与达成率"
    total_sales = float(df["销售额"].sum())
    total_profit = float(df["利润"].sum())
    total_orders = int(df["订单数"].sum())
    margin = total_profit / total_sales * 100
    sections.append(_sec(X.group_kpi(items=[
        {"label": "总销售额", "value": total_sales, "fmt": "compact", "delta": 0.128},
        {"label": "总利润", "value": total_profit, "fmt": "compact", "delta": 0.086},
        {"label": "订单数", "value": total_orders, "fmt": "thousands", "delta": 0.064},
        {"label": "利润率", "value": margin, "fmt": "percent", "delta": -0.012},
        {"label": "客户数", "value": int(df["客户数"].sum()), "fmt": "thousands", "delta": 0.031},
        {"label": "单均金额", "value": total_sales / total_orders, "fmt": "currency", "delta": 0.022},
    ], title="经营核心指标", subtitle="2024 年全年 · 环比趋势", height=150), s))
    sections.append(_sec(eazy_data_viz.kpi(df, value="销售额", agg="sum", label="全年销售额",
                                  delta=0.128, delta_label="同比", target=total_sales * 1.25,
                                  hint="2024 全年 · 含税", height=160), s))
    sections.append(_sec(eazy_data_viz.kpi(3.4, label="退货率（反向指标）",
                                  delta=-0.086, delta_label="同比", inverse=True,
                                  fmt="percent", hint="inverse=True：下降显示为绿色",
                                  height=160), s))
    sections.append(_sec(eazy_data_viz.kpi(df, value="销售额", agg="sum", label="销售额趋势卡",
                                  delta=0.041, delta_label="环比", spark="销售额",
                                  spark_x="月份", accent=1, link="g1",
                                  hint="迷你走势 + 参与 g1 联动", height=160), s))
    sections.append(_sec(eazy_data_viz.kpi(df, value="订单数", agg="sum", label="订单数",
                                  fmt="thousands", delta=0.064, delta_label="同比",
                                  unit=" 单", spark="订单数", spark_x="月份",
                                  accent=2, height=160), s))
    sections.append(_sec(eazy_data_viz.gauge(margin, label="整体利润率", min=0, max=40,
                                    fmt="percent", height=180, subtitle="目标 20%"), s))
    sections.append(_sec(X.ring_progress(78, label="年度目标达成率", max=100,
                                         height=180), s))
    sections.append(_sec(X.progress(g_region, x="大区", y="销售额", max=600000,
                                    title="大区销售进度", height=180), s))
    sections.append(_sec(X.progress(df, x="渠道", y="销售额", max=total_sales,
                                    title="渠道销售占比", height=180), s))

    # ------------------------------------------------------------------
    # ② 趋势分析
    # ------------------------------------------------------------------
    s = "② 趋势分析 · 时间序列与结构变化"
    sections.append(_sec(eazy_data_viz.line(df, x="月份", y="销售额", color="渠道",
                                   title="月度销售额趋势（多系列）", height=360), s))
    sections.append(_sec(eazy_data_viz.line(df, x="日期", y="销售额", title="日销售额走势（时间轴）",
                                   area=True, smooth=False, height=360), s))
    sections.append(_sec(eazy_data_viz.line(df, x="月份", y="销售额", color="产品", step=True,
                                   title="阶梯线：按产品的月度对比", height=360), s))
    sections.append(_sec(X.area_pct(df, x="月份", y="销售额", color="产品",
                                    title="百分比堆叠面积（产品结构）", height=360), s))
    sections.append(_sec(X.bar_pct(df, x="月份", y="销售额", color="渠道",
                                   title="百分比堆叠柱（渠道结构）", height=360), s))
    sections.append(_sec(X.theme_river(df, x="月份", color="产品", value="销售额",
                                       title="主题河流：产品销售构成变化", height=360), s))
    sections.append(_sec(X.calendar(daily, date="日期", value="销售额",
                                    title="日历热力图：每日销售额", height=240), s))
    sections.append(_sec(X.candlestick(ohlc, date="日期", open="开盘", high="最高",
                                       low="最低", close="收盘",
                                       title="K 线图（近 45 天）", height=380), s))
    sections.append(_sec(eazy_data_viz.combo(df, x="月份", bar="销售额", line="利润",
                                    title="组合图：销售额（柱）+ 利润（线）", height=360), s))
    sections.append(_sec(X.sparkline(df, x="月份", y="销售额", group="渠道",
                                     title="迷你走势：渠道月度", height=240), s))
    sections.append(_sec(X.trend(df, x="销售额", y="利润", color="产品",
                                 title="趋势散点 + 回归线（销售额 → 利润）", height=360), s))

    # ------------------------------------------------------------------
    # ③ 对比与排名
    # ------------------------------------------------------------------
    s = "③ 对比与排名 · 谁高谁低、差多少"
    sections.append(_sec(eazy_data_viz.bar(df, x="大区", y="销售额", color="产品", stack=True,
                                  title="堆叠柱：大区 × 产品", height=360), s))
    sections.append(_sec(eazy_data_viz.bar(df, x="省份", y="销售额", horizontal=True, top_n=10,
                                  title="条形图：省份销售额", height=360), s))
    sections.append(_sec(X.waterfall(df, x="产品", y="销售额", total=True,
                                     title="瀑布图：产品销售贡献", height=360), s))
    sections.append(_sec(X.pareto(df, x="省份", y="销售额", top_n=8,
                                  title="帕累托图：80/20 分析", height=360), s))
    sections.append(_sec(X.lollipop(df, x="产品", y="销售额",
                                    title="棒棒糖图：产品对比", height=360), s))
    sections.append(_sec(X.dumbbell(half, x="省份", y1="上半年", y2="下半年",
                                    title="哑铃图：上下半年对比", height=360), s))
    sections.append(_sec(X.slope(slope_df, x="产品", y="销售额", color="期间",
                                 fmt="compact", title="斜率图：产品上下半年销售额变化", height=360), s))
    sections.append(_sec(X.bump(bump_df, x="月份", y="销售额", group="产品",
                                title="排名变化：产品月度排名", height=380), s))
    sections.append(_sec(X.bullet(g_region, x="大区", actual="销售额", target_value=500000,
                                  title="子弹图：大区 vs 目标 50 万", height=360), s))
    sections.append(_sec(X.target(g_region, x="大区", actual="销售额", target="目标",
                                  title="目标对比：实际 vs 目标", height=360), s))
    sections.append(_sec(X.pictorial(g_region, x="大区", y="销售额", symbol="rect",
                                     title="象形柱图", height=360), s))
    sections.append(_sec(X.pyramid(by_chan, names="渠道", values="销售额",
                                   title="金字塔 / 漏斗：渠道销售额", height=360), s))
    sections.append(_sec(eazy_data_viz.funnel(df, names="产品", values="销售额",
                                     title="漏斗图：产品销售额", height=360), s))

    # ------------------------------------------------------------------
    # ④ 结构与占比
    # ------------------------------------------------------------------
    s = "④ 结构与占比 · 一块蛋糕怎么切"
    sections.append(_sec(eazy_data_viz.pie(df, names="产品", values="销售额", donut=True,
                                  title="环形图：产品销售构成", height=360), s))
    sections.append(_sec(X.rose(df, names="产品", values="销售额",
                                title="玫瑰图：南丁格尔", height=360), s))
    sections.append(_sec(eazy_data_viz.treemap(df, path=["大区", "省份"], value="销售额",
                                      title="矩形树图：大区 → 省份", height=400), s))
    sections.append(_sec(X.sunburst(df, path=["大区", "省份"], value="销售额",
                                    title="旭日图：层级占比", height=400), s))
    sections.append(_sec(X.tree(df, path=["大区", "省份"], value="销售额",
                                title="树图：层级结构", height=520), s))
    sections.append(_sec(X.tile(df, names="省份", values="销售额", top_n=8,
                                title="瓦片图：省份销售额深浅", height=300), s))

    # ------------------------------------------------------------------
    # ⑤ 分布与关系
    # ------------------------------------------------------------------
    s = "⑤ 分布与关系 · 找规律、找相关"
    sections.append(_sec(eazy_data_viz.histogram(df, column="销售额", bins=24,
                                        title="直方图：销售额分布", height=360), s))
    sections.append(_sec(eazy_data_viz.box(df, x="产品", y="销售额",
                                  title="箱线图：产品销售额离散度", height=360), s))
    sections.append(_sec(eazy_data_viz.scatter(df, x="销售额", y="利润", color="产品", size="订单数",
                                      title="气泡散点：销售额 × 利润（大小=订单数）", height=380), s))
    sections.append(_sec(X.quadrant(prov_mean, x="销售额", y="利润", size="订单数",
                                    color="大区", title="四象限：省份增长质量", height=400), s))
    sections.append(_sec(eazy_data_viz.heatmap(df, x="月份", y="大区", value="销售额",
                                      title="热力图：月份 × 大区", height=360), s))
    sections.append(_sec(X.matrix(df, columns=["销售额", "订单数", "利润", "客户数"],
                                  title="相关系数矩阵", height=380), s))
    sections.append(_sec(X.radar(df, x="产品", y="销售额", color="大区", agg="mean",
                                 title="雷达图：大区 × 产品均值", height=400), s))
    sections.append(_sec(X.parallel(par_df, dims=["销售额", "订单数", "利润", "客户数"],
                                    color="大区", title="平行坐标：大区多维分布", height=400), s))
    sections.append(_sec(X.sankey(sankey_df, source="来源", target="去向", value="金额",
                                  title="桑基图：渠道 → 产品", height=420), s))
    sections.append(_sec(X.graph(graph_df, source="源", target="目标", value="销售额",
                                 title="关系图：大区 — 城市", height=420), s))

    # ------------------------------------------------------------------
    # ⑥ 明细与文本
    # ------------------------------------------------------------------
    s = "⑥ 明细与文本 · 驾驶舱里的表格与词云"
    sections.append(_sec(X.table(df, columns=["月份", "大区", "省份", "产品", "渠道", "销售额", "订单数"],
                                 limit=12, title="明细表（前 12 行）", height=420), s))
    sections.append(_sec(X.wordcloud(df, names="城市", values="销售额", top_n=12,
                                     title="词云：城市销售额", height=320), s))

    # ------------------------------------------------------------------
    # ⑦ 交互演示
    # ------------------------------------------------------------------
    s = "⑦ 交互演示 · 点击下钻 / 点击联动"
    sections.append(_sec(eazy_data_viz.bar(df, x="大区", y="销售额", drill=["大区", "省份", "城市"],
                                  title="下钻演示：点击柱子 → 大区 → 省份 → 城市", height=400), s))
    sections.append(_sec(eazy_data_viz.bar(df, x="大区", y="销售额", color="渠道", link="g1",
                                  title="联动①：大区渠道（点击联动其他三张）", height=360), s))
    sections.append(_sec(eazy_data_viz.line(df, x="月份", y="销售额", color="渠道", link="g1",
                                   title="联动②：月度趋势", height=360), s))
    sections.append(_sec(eazy_data_viz.pie(df, names="产品", values="销售额", link="g1",
                                  title="联动③：产品构成", height=360), s))
    sections.append(_sec(eazy_data_viz.heatmap(df, x="月份", y="大区", value="销售额", link="g1",
                                      title="联动④：月份 × 大区", height=360), s))
    sections.append(_sec(X.gantt(gantt_df, task="任务", start="开始", end="结束",
                                 color="负责部门", title="甘特图：项目计划", height=420), s))

    # ------------------------------------------------------------------
    # ⑧ 配色库
    # ------------------------------------------------------------------
    s = "⑧ 配色库 · 一个 .palette() 换整套配色"
    _swatch = {"google": "Google Material 3", "antd": "Ant Design",
               "tableau": "Tableau 10", "carbon": "IBM Carbon",
               "echarts": "ECharts 默认", "morandi": "莫兰迪低饱和",
               "tailwind": "Tailwind"}
    for _pname in ("google", "antd", "tableau", "carbon", "echarts", "morandi", "tailwind"):
        chart = eazy_data_viz.bar(df, x="月份", y="销售额", color="产品",
                         title="月度销售 · %s" % _swatch[_pname],
                         height=300).palette(_pname)
        sections.append(_sec(chart, s))

    # ------------------------------------------------------------------
    # ⑨ 地图可视化
    # ------------------------------------------------------------------
    s = "⑨ 地图可视化 · 区域填色 / 气泡 / 飞线（内置 china / world）"
    sections.append(_sec(eazy_data_viz.geo_map(map_prov, region="省份", value="销售额",
                                            title="中国省级地图（区域填色）", height=460), s))
    sections.append(_sec(eazy_data_viz.geo_map(map_world, region="国家", value="销售额",
                                            map="world", title="世界地图（国家填色）", height=460), s))
    sections.append(_sec(eazy_data_viz.map_bubble(map_city, region="城市", value="销售额",
                                                title="城市气泡图（按城市坐标落点）", height=460), s))
    sections.append(_sec(eazy_data_viz.map_flow(map_flow_df, source="出发城市",
                                             target="到达城市", value="件数",
                                             title="城市飞线图（发货 → 收货）", height=460), s))

    # ------------------------------------------------------------------
    # 组装 & 保存
    # ------------------------------------------------------------------
    kinds = []
    for c in sections:
        t = c.spec.get("type")
        if t not in kinds:
            kinds.append(t)
    print("图表卡片: %d，图表类型: %d" % (len(sections), len(kinds)))
    print("类型清单:", ", ".join(kinds))

    dashboard = eazy_data_viz.dashboard(
        *sections, cols=2,
        title="eazy_data_viz · 经营驾驶舱组件总览",
        desc="pandas → 单文件 HTML · Material Design 3 · 48 种图表 · 点击卡片右上角「代码」"
             "可查看生成该图的完整 Python 代码 · 点击图形可下钻 / 联动",
    )
    html = dashboard.to_html(inline=True)
    out = [
        os.path.join(ROOT, "gallery.html"),
        os.path.join(ROOT, "eazy_data_viz", "gallery", "gallery.html"),
    ]
    for path in out:
        d = os.path.dirname(path)
        if not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print("已写出 %s (%.2f MB)" % (path, os.path.getsize(path) / 1048576.0))
    return len(sections), len(kinds)


if __name__ == "__main__":
    main()
