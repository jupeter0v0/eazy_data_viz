# 11 · 常用配方（Cookbook）

> 目标：20 个「拿来即用」的代码，覆盖经营分析里最常做的 20 件事。每段都能直接跑，只改列名就能换成你自己的数据。

## 使用说明

所有配方都假设已经执行：

```python
import numpy as np
import pandas as pd
import eazy_data_viz as edv

df = edv.sample_df()          # 换成你的 DataFrame
```

- 示例统一写到 `examples/output/`（仓库已 gitignore）；正式项目把路径换成你自己的即可。
- 每个配方都是独立代码块，先 `save()` 出 HTML 再用浏览器打开就能看到效果；交互（悬浮、点选、下钻、联动）都在浏览器里完成，不重启 Python。
- 需要调色板时给 `save` 前加一行 `.palette("antd")`，或全局 `edv.set_palette("antd")`。
- 配方里出现的 `fmt="percent"` 只是「在数字后加 %」，**不会乘以 100**，所以比率列要自己 `* 100`。

## 1. Top N 横向柱状图

**问题**：老板只想知道卖得最好的 8 个城市，名字长的类目竖排会挤在一起。

```python
g = df.groupby("城市", as_index=False)["销售额"].sum()
g = g.sort_values("销售额", ascending=False).head(8)
edv.bar(g, x="城市", y="销售额", horizontal=True, sort="desc",
        labels=True, fmt="thousands").save("examples/output/11-01-topn.html")
```

**效果**：横向条形按销售额降序，柱尾直接标数值。`horizontal=True` 配合 `sort="desc"` 才是「从上到下由大到小」。

## 2. 占比环图

**问题**：想一眼看出渠道结构，且类目不多（3–6 个）。

```python
g = df.groupby("渠道", as_index=False)["销售额"].sum()
edv.pie(g, names="渠道", values="销售额", donut=True,
        labels=True, sort="desc").save("examples/output/11-02-donut.html")
```

**效果**：环形图 + 百分比标签；类目超过 6 个时改用 `bar_pct` 或 `treemap`（见 [10-chart-selection](10-chart-selection.md)）。

## 3. 同比 / 环比

**问题**：月度销售额涨了，但到底是季节性还是真的增长？

```python
m = df.groupby(df["日期"].dt.to_period("M"))["销售额"].sum().reset_index()
m.columns = ["月", "销售额"]
m["月"] = m["月"].astype(str).str[-2:] + "月"
m["环比%"] = (m["销售额"].pct_change() * 100).round(1)
m["同比%"] = (m["销售额"].pct_change(12) * 100).round(1)
edv.bar(m, x="月", y="环比%", fmt="percent", sort="x",
        labels=True).save("examples/output/11-03-mom.html")
```

**效果**：把月粒度汇总后计算 `pct_change()`；同比用 `pct_change(12)`（12 个月前的同一期）。缺月会错位，先用 `asfreq("M")` 补齐。

## 4. 目标达成率

**问题**：每个大区的实际值离目标还有多远？

```python
g = df.groupby("大区", as_index=False)["销售额"].sum()
g["目标"] = g["销售额"] * 1.15
g["达成率%"] = (g["销售额"] / g["目标"] * 100).round(1)
edv.bullet(g, x="大区", actual="销售额", target="目标",
           fmt="compact", labels=True).save("examples/output/11-04-bullet.html")
```

**效果**：子弹图 = 实际横条 + 目标刻度线；`target` 传列名按行取目标，传 `target_value=100000` 则所有行共用一个目标。

## 5. 利润率

**问题**：哪个产品线「卖得多但赚得少」？

```python
g = df.groupby("产品", as_index=False).agg(
    销售额=("销售额", "sum"), 利润=("利润", "sum"))
g["利润率%"] = (g["利润"] / g["销售额"] * 100).round(1)
edv.bar(g, x="产品", y="利润率%", fmt="percent", sort="desc",
        labels=True, color="产品").save("examples/output/11-05-margin.html")
```

**效果**：比率要**先聚合再相除**，不能对每行利润率求平均；`fmt="percent"` 只负责加 %，所以乘了 100。

## 6. 月度趋势 + 移动平均

**问题**：日数据太抖，想同时看原始月趋势和 3 月移动平均。

```python
m = df.groupby(df["日期"].dt.to_period("M"))["销售额"].sum().reset_index()
m.columns = ["月", "销售额"]
m["月"] = m["月"].astype(str)
m["3月均"] = m["销售额"].rolling(3, min_periods=1).mean().round(0)
long = m.melt(id_vars="月", value_vars=["销售额", "3月均"],
              var_name="口径", value_name="金额")
edv.line(long, x="月", y="金额", color="口径", sort="x",
         labels=True).save("examples/output/11-06-trend-ma.html")
```

**效果**：宽表 `melt` 成长表后按 `口径` 分两条线；`sort="x"` 保证 `YYYY-MM` 按时间顺序而不是数值大小排。

## 7. 渠道结构堆叠

**问题**：每个月的销售额里，直销 / 渠道代理 / 线上商城各占多少？

```python
p = df.pivot_table(index="月份", columns="渠道", values="销售额",
                   aggfunc="sum", observed=True).reset_index()
long = p.melt(id_vars="月份", var_name="渠道", value_name="销售额")
edv.bar(long, x="月份", y="销售额", color="渠道", stack=True,
        sort="x").save("examples/output/11-07-stack.html")
```

**效果**：每月一根堆叠柱；宽表转长表是堆叠图的固定套路。想看份额变化把 `stack=True` 换成 `edv.area_pct(...)`。

## 8. 区域下钻三级

**问题**：从大区到省份再到城市，一张图逐级看下去。

```python
edv.bar(df, x="大区", y="销售额", drill=["大区", "省份", "城市"],
        top_n=10, link="drill").save("examples/output/11-08-drill.html")
```

**效果**：点柱子进入省份，再点进入城市，左上角面包屑可返回；`drill` 里第一列就是初始横轴，不必再传 `x` 也可以。

## 9. 多图联动筛选

**问题**：点中「华东」，想同时看该区域的渠道结构和日期走势。

```python
c1 = edv.bar(df, x="大区", y="销售额", link="sales")
c2 = edv.pie(df, names="渠道", values="销售额", link="sales")
c3 = edv.line(df, x="日期", y="销售额", link="sales")
edv.dashboard(c1, c2, c3, cols=2, title="联动看板").save(
    "examples/output/11-09-linked.html")
```

**效果**：三张图 `link` 同名即同组，点任意一张的图形，其余图按同名列自动过滤；页面右上角「重置联动」清除筛选。联动只在同一页面生效，必须用 `dashboard()` / `show()` 放在一起。

## 10. KPI 随联动重算

**问题**：筛选区域后，顶部 KPI 数字要跟着变，而不是只过滤明细图。

```python
k = edv.kpi(df, value="销售额", label="销售额", agg="sum", link="sales",
            spark="销售额", spark_x="日期", fmt="compact")
b = edv.bar(df, x="渠道", y="销售额", link="sales")
edv.dashboard(k, b, cols=1, title="KPI 联动").save(
    "examples/output/11-10-kpi-link.html")
```

**效果**：KPI 传了 `link` 后会随同组筛选在前端重算；`spark` / `spark_x` 生成迷你走势。KPI 的 `agg` 对 `spark` 序列同样生效。

## 11. 瀑布图看增减来源

**问题**：总利润从各产品来看，谁贡献正增量、谁在拖后腿？

```python
g = df.groupby("产品", as_index=False)["利润"].sum()
g = g.sort_values("利润", ascending=False)
edv.waterfall(g, x="产品", y="利润", total=True, labels=True,
              fmt="compact").save("examples/output/11-11-waterfall.html")
```

**效果**：正负增量逐段累加，最后一根是合计（`total=True`）；适合「从 A 到 B 差了 80 万，差在哪」。

## 12. 帕累托看 80/20

**问题**：哪些产品贡献了 80% 的销售额？

```python
edv.pareto(df, x="产品", y="销售额", top_n=10, labels=True,
           cum_fmt="percent").save("examples/output/11-12-pareto.html")
```

**效果**：柱 = 各项销售额（降序），折线 = 累计占比；`pareto` 自动排序并累计，不用自己算。

## 13. 四象限找重点客户

**问题**：按「销售额 × 利润」把客户/城市分成四类，重点维护高销售高利润的。

```python
acct = df.groupby("城市", as_index=False).agg(
    销售额=("销售额", "sum"), 利润=("利润", "sum"),
    客户数=("客户数", "sum"))
edv.quadrant(acct, x="销售额", y="利润", size="客户数", color="城市",
             quad_labels=["高销售·高利润", "低销售·高利润",
                          "低销售·低利润", "高销售·低利润"]).save(
    "examples/output/11-13-quadrant.html")
```

**效果**：默认以 x、y 的中位数分割四象限，气泡大小可再编码一个指标。`quad_labels` 顺序是左上、右上、左下、右下。

## 14. 箱线图找异常

**问题**：销售额里有没有极端大单，是否要单独剔除？

```python
q1, q3 = df["销售额"].quantile([0.25, 0.75])
iqr = q3 - q1
out = df[(df["销售额"] < q1 - 1.5 * iqr) | (df["销售额"] > q3 + 1.5 * iqr)]
edv.box(df, x="渠道", y="销售额").save("examples/output/11-14-box.html")
print("异常值 %d / %d" % (len(out), len(df)))
```

**效果**：箱线图按渠道对比分布并显示离群点；`1.5 * IQR` 是常用的离群阈值，把 `out` 落库即可做清洗白名单。

## 15. 热力图看时段规律

**问题**：销售额在「星期 × 月份」上有没有明显规律？

```python
week = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
df["星期"] = pd.Categorical(df["日期"].dt.dayofweek.map(dict(enumerate(week))),
                            categories=week, ordered=True)
edv.heatmap(df, x="月份", y="星期", value="销售额",
            labels=True).save("examples/output/11-15-heatmap.html")
```

**效果**：颜色深浅看高低；`星期` 用 `ordered=True` 的分类保证周一到周日顺序，否则会按字典序/出现顺序排。

## 16. 日历图看每日活跃

**问题**：全年哪几天是销售高峰，有没有断档？

```python
edv.calendar(df, date="日期", value="订单数", agg="sum",
             fmt="thousands").save("examples/output/11-16-calendar.html")
```

**效果**：一年日历格子，颜色 = 当日订单数；只有部分日期有数据时其余格子留白，可据此发现缺数。

## 17. 甘特图看项目排期

**问题**：5 个任务的起止时间和负责人，一张图说清楚。

```python
plan = pd.DataFrame({
    "任务": ["需求", "设计", "开发", "测试", "上线"],
    "开始": pd.to_datetime(["2024-01-01", "2024-01-10", "2024-01-22",
                           "2024-03-01", "2024-04-01"]),
    "结束": pd.to_datetime(["2024-01-12", "2024-01-25", "2024-03-10",
                           "2024-03-28", "2024-04-08"]),
    "负责人": ["产品", "设计", "研发", "测试", "运营"]})
edv.gantt(plan, task="任务", start="开始", end="结束",
          color="负责人", labels=True).save("examples/output/11-17-gantt.html")
```

**效果**：按任务画时间条，`color` 按负责人上色；结束早于开始的行会在 `chart.warnings` 里提示并先清洗。

## 18. K 线看股价

**问题**：把日线 OHLC 画成蜡烛图，看涨跌和波动区间。

```python
px = df.groupby("日期", as_index=False).agg(
    开=("销售额", "first"), 高=("销售额", "max"),
    低=("销售额", "min"), 收=("销售额", "last"))
edv.candlestick(px, date="日期", open="开", high="高", low="低",
                close="收").save("examples/output/11-18-kline.html")
```

**效果**：红涨绿跌（A 股习惯），带缩放条；`date` 列可以是 datetime 或日期字符串，函数会自动解析排序。

## 19. 地图看省份 / 城市

**问题**：销售额在地理上集中在哪里？

```python
edv.geo_map(df, region="省份", value="销售额", labels=True).save(
    "examples/output/11-19-map.html")
edv.map_bubble(df, region="城市", value="销售额").save(
    "examples/output/11-19-map-city.html")
```

**效果**：`geo_map` 按省份填色，`map_bubble` 按城市中心点画气泡；「广东省」「广东」都能匹配，`name_map={"沪": "上海"}` 可做自定义别名。地图数据（GeoJSON + 城市坐标）已内联，离线可用。

## 20. 表格明细导出

**问题**：图表看完后，老板还要一份可筛选的明细。

```python
g = df.groupby(["大区", "产品"], as_index=False)["销售额"].sum()
g = g.sort_values("销售额", ascending=False)
g.to_csv("examples/output/11-20-detail.csv", index=False, encoding="utf-8-sig")
edv.table(g, limit=20, fmt="thousands").save("examples/output/11-20-table.html")
```

**效果**：`table` 是 HTML 表格组件（支持滚动、排序、联动筛选），旁边同时落一份 CSV；CSV 用 `utf-8-sig` 是为了 Excel 打开中文不乱码。

## 把配方拼成驾驶舱

```python
edv.show(
    edv.kpi(df, value="销售额", label="总销售额", delta=0.12, delta_label="同比"),
    edv.line(df, x="日期", y="销售额"),
    edv.bar(df, x="大区", y="销售额", top_n=8),
    edv.pie(df, names="渠道", values="销售额", donut=True),
    cols=2, title="经营日报", desc="2024 年数据 · eazy_data_viz",
).save("examples/output/11-cockpit.html")
```

组合规则只有两条：**同一 DataFrame 用同一个 `link` 才能联动；`dashboard()` / `show()` 才能把多张图放进同一页面。** 其余参数按单图习惯写即可。
