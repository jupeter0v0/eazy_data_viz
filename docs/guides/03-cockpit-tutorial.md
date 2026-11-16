# 03 · 从零搭一个经营驾驶舱

> 目标：用 13 张卡片、5 个分区、3 条交互链（KPI 联动 / 区域下钻 / 主题切换），
> 从一张原始订单表开始，做出一个能直接发给老板的单文件经营驾驶舱。
> 本文所有代码都可运行，最终产物约 1.4 MB、离线可用。

## 适用人群与前置条件

| 项 | 要求 |
| --- | --- |
| 读者 | 已完成 [02 · 五分钟上手](02-quickstart.md)，知道 `bar/line/pie` 怎么调用 |
| 数据 | 任意「一行一条记录」的经营明细表；本文用 `edv.sample_df()` |
| 时间 | 25~40 分钟 |
| 产物 | `examples/output/cockpit_guide.html` |

驾驶舱不是“把图堆满”。一个能用的驾驶舱遵守三条规则：

1. **一屏之内回答三个问题**：现在怎么样（KPI）→ 趋势往哪走（趋势）→ 问题出在哪（结构/排名）。
2. **每张图都有明确的点击结果**：要么下钻、要么联动，不做“只好看”的图。
3. **数据只准备一次**：原始明细 → 派生小表 → 全部图表共用，避免每张图各写一遍 groupby。

## 第 0 步：定信息架构（写代码前）

| 分区（`section`） | 卡片 | 回答的问题 | 交互 |
| --- | --- | --- | --- |
| 核心指标 | 4 张 `kpi` | 总量/利润/订单/利润率，同比达标吗 | `link="全局"`，随其它图筛选重算 |
| 趋势 | `line` + `area` | 全年走势、渠道分化、有没有断崖 | `link="全局"` |
| 结构 | 堆叠 `bar` + 环图 `pie` | 哪些大区/产品贡献最大 | 柱图 `drill` 大区→省份→城市 |
| 排名与目标 | 横向 `bar` + `bullet` | 谁领先、谁没达标 | 无（静态对比） |
| 明细与分布 | `table` + `histogram` + `scatter` | 异常订单长什么样、分布是否偏态 | 表格只做展示 |

共 **13 张卡片**（4 + 2 + 2 + 2 + 3）。`cols=2`，宽屏下两列，卡片高度统一 340~420。

> **重要结论**：`section` 只是“分区标题”。**连续**使用同一个 `section` 值才会合并成一组；
> 同一个标题如果隔了别的图再出现，会再插一次标题。所以按分区连续写图。

> **真实限制**：`section` 形参只存在于 `kpi` / `bar` / `line` 三个函数上（`pie`、`table`、
> `histogram`、`scatter`、`bullet`、`area` 等传了会直接 `TypeError: unexpected keyword argument`）。
> 但渲染层读的是 `spec["section"]`，所以用一个 3 行 helper 就能给**任意**图补分区，见第 3 步开头。

## 第 1 步：数据准备（只做一次）

原则：**原始明文列 + 少量派生小表**。不要把所有计算都塞进图表函数。

```python
import pandas as pd
import eazy_data_viz as edv

def load_data(path=None):
    """读取并校验数据；path=None 时用内置示例数据。"""
    if path is None:
        df = edv.sample_df()
    else:
        df = pd.read_excel(path, parse_dates=["日期"])

    # 1) 数值列兜底：真实 Excel 里金额常是文本（带 ￥ / 逗号 / 空串）
    for col in ["销售额", "利润", "订单数", "客户数"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 2) 月份列转有序分类，保证折线按 1月 → 12月 排，而不是按字符串
    months = [f"{i}月" for i in range(1, 13)]
    df["月份"] = pd.Categorical(df["月份"], categories=months, ordered=True)

    # 3) 日期列确保是 datetime（示例数据已经是）
    if not pd.api.types.is_datetime64_any_dtype(df["日期"]):
        df["日期"] = pd.to_datetime(df["日期"])

    return df
```

然后准备两张**派生小表**：区域目标表、月度汇总表。它们的数据量小，可以让图表更快：

```python
def build_tables(df):
    total = float(df["销售额"].sum())
    profit = float(df["利润"].sum())

    # 区域目标：真实场景从预算系统读；这里用「实际 × 1.12」模拟
    by_region = df.groupby("大区", as_index=False).agg(
        销售额=("销售额", "sum"),
        利润=("利润", "sum"),
        订单数=("订单数", "sum"),
    )
    by_region["目标"] = (by_region["销售额"] * 1.12).round(2)

    # 月度 × 渠道趋势（给 line / area_pct 用）
    by_month_channel = df.groupby(["月份", "渠道"], as_index=False, observed=True).agg(
        销售额=("销售额", "sum"),
    )
    return {
        "df": df,
        "total": total,
        "profit": profit,
        "margin": profit / total * 100 if total else 0.0,
        "by_region": by_region,
        "by_month_channel": by_month_channel,
    }
```

三个容易踩的点：

| 坑 | 后果 | 修法 |
| --- | --- | --- |
| `月份` 是字符串 | 折线按 10月, 11月, 12月, 1月… 排 | `pd.Categorical(..., ordered=True)` |
| `groupby` 时 `月份` 是 Categorical | pandas 2 默认 `observed=False` 会补 12 个空组 | 加 `observed=True` |
| 直接用 `df["销售额"].sum()` 做 KPI | 联动筛选后 KPI 不重算 | KPI 用 `kpi(df, value="销售额", link=...)`，别传静态值 |

## 第 2 步：KPI 区（4 张卡，跟随联动重算）

```python
def kpi_section(t):
    df = t["df"]
    return [
        edv.kpi(df, value="销售额", agg="sum", label="全年销售额",
                delta=0.128, delta_label="同比", target=2_000_000,
                spark="销售额", spark_x="月份", accent=0,
                link="全局", section="一、核心指标", height=150),
        edv.kpi(df, value="利润", agg="sum", label="利润总额",
                delta=0.086, delta_label="同比", accent=1,
                link="全局", section="一、核心指标", height=150),
        edv.kpi(df, value="订单数", agg="sum", label="订单数", fmt="thousands",
                unit=" 单", delta=0.064, accent=2,
                link="全局", section="一、核心指标", height=150),
        edv.kpi(t["margin"], label="利润率", fmt="percent",
                delta=-0.012, delta_label="同比", accent=3,
                section="一、核心指标", height=150),
    ]
```

说明（每个参数在 [04 · KPI 卡片](04-kpi-cards.md) 有详解）：

- `value="销售额"` + `agg="sum"`：从 DataFrame 聚合，**不是**你算好传进去；
- `link="全局"`：当别的图触发联动 `全局` 组筛选时，这张卡会按筛选后的行重新聚合；
- `spark/spark_x`：迷你走势，`spark_x` 必填，否则抛 `ValueError`；
- `accent=0..3`：四张卡各取配色里第 0~3 号色，形成色彩节奏；
- `target=2_000_000`：显示达成率徽标 + 进度条；
- 四张卡都写 `section="一、核心指标"`，Dashboard 只插一次标题。

> **注意**：最后一张利润率是**先算好再传静态值**（`kpi(t["margin"], ...)`），没有 `link`。
> 比率不能直接 `sum`/`mean`（各渠道权重不同，简单平均是错的），所以不参与联动重算；
> 真想让它跟随筛选，需要在钩子里按筛选结果重算，属于高级用法（见 [04 · KPI 卡片](04-kpi-cards.md) 末尾）。

## 第 3 步：趋势区（2 张卡）

先补一个 helper：给没有 `section` 形参的图（`area`/`pie`/`bullet`/`table`/`histogram`/`scatter`…）
设置分区。`Chart.spec` 是普通 dict，渲染层只读 `spec["section"]`，所以这样是安全的：

```python
def with_section(chart, name):
    """给任意图表补 section（kpi/bar/line 已有该形参，其它图用这个）。"""
    chart.spec["section"] = name
    return chart
```

```python
def trend_section(t):
    df = t["df"]
    return [
        edv.line(df, x="月份", y="销售额", color="渠道", smooth=True,
                 link="全局", title="月度销售额（按渠道）",
                 subtitle="点击折线上的点，可筛掉其它渠道",
                 section="二、趋势", height=380),
        with_section(
            edv.area(df, x="日期", y="销售额",
                     title="日销售额走势", subtitle="看波动与异常日",
                     height=380),
            "二、趋势"),
    ]
```

- 折线 `x="月份"` 能按自然月排序，靠的是第 1 步把 `月份` 转成了有序 Categorical；
- `area` 本质是 `line(..., area=True)`，用于“看总量波动”；
- 折线图默认**不排序**、保留分组后的 x 顺序；分类柱图默认按值降序。这是全库统一规则。

## 第 4 步：结构区（1 张可下钻柱图 + 1 张环图）

```python
def structure_section(t):
    df = t["df"]
    return [
        edv.bar(df, x="大区", y="销售额", color="产品", stack=True,
                drill=["大区", "省份", "城市"], link="全局",
                title="区域 × 产品结构（可下钻）",
                subtitle="点击柱子：大区 → 省份 → 城市；面包屑可回退",
                section="三、结构", height=400),
        with_section(
            edv.pie(df, names="渠道", values="销售额", donut=True,
                    title="渠道构成", height=400),
            "三、结构"),
    ]
```

下钻的准确行为（来自运行时实现）：

1. 点第一层柱子（大区）→ 图表横轴切到 `drill[1]`（省份），且只保留该大区的行；
2. 面包屑出现 `全部 / 华东`，点“全部”回到上一层；
3. 点到最后一级（城市）后不再下钻，点击只做联动；
4. **同时**写了 `drill` 和 `link` 的图，点击会“先记录下钻、再触发联动”——
   所以同组其它图会按“大区=华东”筛选，而这张图自己继续下钻。

> **结论**：一张图不要既 drill 又 link 到很多图，容易让观众迷失。本驾驶舱只让这张柱图
> 同时承担两个职责，且副标题写清了操作方式。

## 第 5 步：排名与目标区（横向排名 + 子弹图）

```python
def ranking_section(t):
    by_region = t["by_region"]
    return [
        edv.bar(by_region, x="大区", y="销售额", horizontal=True,
                top_n=10, title="区域销售额 Top 10",
                subtitle="横向条形图比竖向柱图更适合长类目名",
                section="四、排名与目标", height=380),
        with_section(
            edv.bullet(by_region, x="大区", actual="销售额", target="目标",
                       title="目标达成（子弹图）",
                       subtitle="灰条=目标，彩色条=实际，超出即达标",
                       height=380),
            "四、排名与目标"),
    ]
```

`bullet` 的 `target` 有两种写法：

| 写法 | 含义 | 例 |
| --- | --- | --- |
| `target="目标"` | 用同一张表里的**列**做目标 | `bullet(by_region, x="大区", actual="销售额", target="目标")` |
| `target_value=500000` | 所有类目共用一个**常量**目标 | `bullet(df, x="大区", actual="销售额", target_value=500000)` |

## 第 6 步：明细与分布区（3 张卡）

```python
def detail_section(t):
    df = t["df"]
    detail = [
        with_section(
            edv.table(df, columns=["日期", "大区", "省份", "城市", "产品", "渠道",
                                   "销售额", "订单数", "利润"],
                      title="经营明细", subtitle="最多嵌入 200 行，展示 limit 行",
                      limit=100, height=420),
            "五、明细与分布"),
        with_section(
            edv.histogram(df, column="销售额", bins=24,
                          title="销售额分布", subtitle="右偏说明有大额订单",
                          height=340),
            "五、明细与分布"),
        with_section(
            edv.scatter(df, x="订单数", y="销售额", color="大区", size="客户数",
                        title="订单数 vs 销售额", subtitle="气泡大小=客户数",
                        height=340),
            "五、明细与分布"),
    ]
    return detail
```

`table` 的两个体积开关：

- `max_rows=200`（默认且上限 200）：**最多嵌入 200 行原始数据**；
- `limit=100`（默认 100，上限 200）：**页面上默认显示多少行**。
  想给下载/复制留更多行就调大 `limit`，但不会超过 200。

## 第 7 步：组装、导出、交付

```python
def build(df):
    t = build_tables(df)
    charts = (
        kpi_section(t)
        + trend_section(t)
        + structure_section(t)
        + ranking_section(t)
        + detail_section(t)
    )
    return edv.dashboard(
        *charts,
        cols=2,
        title="XX 公司经营驾驶舱",
        desc="2024 全年 · 点击图形联动/下钻 · 右上角切换主题与配色",
        palette="google",
        theme="light",
    )

path = build(load_data()).save("examples/output/cockpit_guide.html")
print(path)
```

`dashboard(...)` 的参数：

| 参数 | 说明 | 建议 |
| --- | --- | --- |
| `cols` | 网格列数 | 2 列最稳；图表多时 2；纯 KPI 卡可 4 |
| `title` / `desc` | 顶栏标题/副标题 | 有标题才出现顶栏与配色/主题按钮 |
| `theme` | `light` / `dark` | 投屏建议 light，夜间看板 dark |
| `palette` | 7 套配色之一 | 见 [05 · 配色与主题](05-palette-and-theme.md) |
| `inline` | 是否内联 JS/数据 | 默认 `True`（单文件）；拆资源见第 08 篇 |

## 第 8 步：完整可运行脚本

保存为 `examples/cockpit_guide.py`，在仓库根目录执行
`PYTHONIOENCODING=utf-8 python examples/cockpit_guide.py`：

```python
# -*- coding: utf-8 -*-
"""13 卡经营驾驶舱：KPI 联动 + 区域下钻 + 分区 + 导出。"""
import os
import eazy_data_viz as edv

OUT = "examples/output"

def load_data(path=None):
    import pandas as pd
    if path is None:
        df = edv.sample_df()
    else:
        df = pd.read_excel(path, parse_dates=["日期"])
    for col in ["销售额", "利润", "订单数", "客户数"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    months = [f"{i}月" for i in range(1, 13)]
    df["月份"] = pd.Categorical(df["月份"], categories=months, ordered=True)
    df["日期"] = pd.to_datetime(df["日期"])
    return df

def build_tables(df):
    total = float(df["销售额"].sum())
    profit = float(df["利润"].sum())
    by_region = df.groupby("大区", as_index=False).agg(
        销售额=("销售额", "sum"), 利润=("利润", "sum"), 订单数=("订单数", "sum"))
    by_region["目标"] = (by_region["销售额"] * 1.12).round(2)
    return {"df": df, "total": total, "profit": profit,
            "margin": profit / total * 100 if total else 0.0,
            "by_region": by_region}

def with_section(chart, name):
    """给没有 section 形参的图（area/pie/bullet/table/histogram/scatter…）补分区。"""
    chart.spec["section"] = name
    return chart

def build(df):
    t = build_tables(df)
    charts = [
        # 一、核心指标
        edv.kpi(df, value="销售额", label="全年销售额", delta=0.128, delta_label="同比",
                target=2_000_000, spark="销售额", spark_x="月份", accent=0,
                link="全局", section="一、核心指标"),
        edv.kpi(df, value="利润", label="利润总额", delta=0.086, delta_label="同比",
                accent=1, link="全局", section="一、核心指标"),
        edv.kpi(df, value="订单数", label="订单数", fmt="thousands", unit=" 单",
                delta=0.064, accent=2, link="全局", section="一、核心指标"),
        edv.kpi(t["margin"], label="利润率", fmt="percent",
                delta=-0.012, delta_label="同比", accent=3,
                section="一、核心指标"),
        # 二、趋势
        edv.line(df, x="月份", y="销售额", color="渠道", smooth=True, link="全局",
                 title="月度销售额（按渠道）", subtitle="点击折线点筛选渠道",
                 section="二、趋势", height=380),
        with_section(
            edv.area(df, x="日期", y="销售额", title="日销售额走势",
                     subtitle="看波动与异常日", height=380),
            "二、趋势"),
        # 三、结构
        edv.bar(df, x="大区", y="销售额", color="产品", stack=True,
                drill=["大区", "省份", "城市"], link="全局",
                title="区域 × 产品结构（可下钻）", subtitle="大区 → 省份 → 城市",
                section="三、结构", height=400),
        with_section(
            edv.pie(df, names="渠道", values="销售额", donut=True,
                    title="渠道构成", height=400),
            "三、结构"),
        # 四、排名与目标
        edv.bar(t["by_region"], x="大区", y="销售额", horizontal=True, top_n=10,
                title="区域销售额 Top 10", section="四、排名与目标", height=380),
        with_section(
            edv.bullet(t["by_region"], x="大区", actual="销售额", target="目标",
                       title="目标达成（子弹图）", height=380),
            "四、排名与目标"),
        # 五、明细与分布
        with_section(
            edv.table(df, columns=["日期", "大区", "省份", "城市", "产品", "渠道",
                                   "销售额", "订单数", "利润"],
                      title="经营明细", limit=100, height=420),
            "五、明细与分布"),
        with_section(
            edv.histogram(df, column="销售额", bins=24, title="销售额分布",
                          height=340),
            "五、明细与分布"),
        with_section(
            edv.scatter(df, x="订单数", y="销售额", color="大区", size="客户数",
                        title="订单数 vs 销售额", height=340),
            "五、明细与分布"),
    ]
    return edv.dashboard(*charts, cols=2, title="XX 公司经营驾驶舱",
                         desc="2024 全年 · 点击图形联动/下钻 · 右上角切换主题与配色",
                         palette="google")

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    df = load_data()
    page = build(df)
    path = page.save(os.path.join(OUT, "cockpit_guide.html"))
    print("已生成", path, "(%.2f MB)" % (os.path.getsize(path) / 1048576.0))
    print("卡片数:", len(page.charts))
```

预期输出：

```text
已生成 F:\deepseek\eazy_data_viz\examples\output\cockpit_guide.html (1.40 MB)
卡片数: 13
```

## 第 9 步：在浏览器里验收（12 项）

打开 HTML 后逐项打勾，这是交付前的最小回归清单：

| # | 检查项 | 期望 |
| --- | --- | --- |
| 1 | 顶栏 | 标题、副标题、配色下拉、◐ 主题按钮都在 |
| 2 | 五个分区标题 | 一、核心指标 … 五、明细与分布，左侧有 4px 主色竖条 |
| 3 | 13 张卡片 | 4 KPI + 2 趋势 + 2 结构 + 2 排名/目标 + 3 明细/分布 |
| 4 | KPI 迷你走势 | 第一张卡有 sparkline，其它三张没有 |
| 5 | 目标徽标 | 销售额卡显示目标与达成率进度条 |
| 6 | 点折线 | 出现「联动筛选 渠道 = 线上商城」chip，KPI 数值变化 |
| 7 | 再点同一点 | chip 消失，KPI 恢复全年值 |
| 8 | 点区域柱 | 柱图下钻到省份，面包屑出现「全部 / 华东」；KPI 变为该大区口径 |
| 9 | 点面包屑「全部」 | 回到大区层，筛选 chip 仍保留（联动与下钻是两套状态） |
| 10 | 重置联动 | 顶栏「重置联动」清空所有 chip，KPI 回全年 |
| 11 | 切主题 | 点 ◐ 整页深色，图与文字对比度正常 |
| 12 | 尺寸变化 | 拖动窗口宽度，卡片与图表自适应重绘（ECharts resize） |

**常见验收失败**：

| 现象 | 原因 | 修法 |
| --- | --- | --- |
| KPI 不随筛选变化 | KPI 没写 `link`，或 link 组名与图不一致 | 两者都写 `link="全局"` |
| 点图没有 chip | 该图没写 `link`（下钻不算联动） | 加 `link="全局"`；或单独点带 link 的图 |
| 点柱图不联动只下钻 | 同时写 drill 后，`link` 仍会生效，但目标图可能没有该维度列 | 确认 link 组里每张图的数据都有被点击的维度列 |
| 分区标题重复出现 | 同一个 section 值被非连续使用 | 让同 section 的图连续排列 |
| 表格 100 行后没数据 | `limit` 只是默认显示行数；嵌入上限 200 | 需要全量数据请走导出 Excel，不是 `table` |

## 第 10 步：交付与二次分发

1. **单文件**：`cockpit_guide.html` 直接发微信/邮件，双击就能用；
2. **定投**：放进内网 Nginx 目录 / OSS 静态托管，内部访问；
3. **嵌入现有系统**：`iframe src="cockpit.html"`，或后端渲染时用 `to_html()` 拿字符串；
4. **定期刷新**：用调度脚本每天重新 `build(df).save("cockpit.html")`，覆盖同名文件即可。

> **注意**：单文件里已经内联数据。发给外部时等于把明细数据也发出去（`table` 前 200 行尤甚）。
> 对外分享前先确认数据口径与脱敏。

## 常见问题

**Q1：卡片高度参差不齐？**
每张图都可传 `height=`（最小 120，否则 `ValueError`）。同一行取最高卡片，视觉上会留白。
建议同一分区内统一高度（本文趋势 380、结构 400、明细 420）。

**Q2：13 张卡在同一页里会不会互相拖慢？**
不会。数据只嵌入一次（相同 DataFrame 合并为同一 `data_ref`），图表是各自独立的 ECharts 实例。
真实上限与优化见 [13 · 性能与体积](13-performance.md)。

**Q3：能不能让 KPI 显示“筛选后的占比”这种复杂口径？**
KPI 只支持 `agg` 五种聚合。复杂口径要么在派生表里算好传静态值，要么写自定义图表（第 14 篇）。

**Q4：下钻维度里有一列在过滤后为空？**
下钻每一层都必须存在于同一张 DataFrame 里。若某层是 join 出来的，先 `merge` 进主表再传。

## 下一篇

驾驶舱里最有价值的组件是 KPI 卡，它 15 个参数各有含义：
[04 · KPI 卡片全参数详解](04-kpi-cards.md)。
