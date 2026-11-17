# 04 · KPI 卡片全参数详解

> 适用人群：已经跑通 [02 · 快速上手](02-quickstart.md)，需要给驾驶舱做指标头的分析师 / 工程师。
> 前置条件：`import eazy_data_viz as edv`，示例数据 `df = edv.sample_df()`（1500 行）。
> 读完你会：准确使用 16 个 KPI 参数，写出同比、目标达成、反向指标、联动重算等 8 类真实卡片。

KPI 卡片是驾驶舱里唯一“不画图”的图表类型：它显示一个聚合数字、一个涨跌标记、
一条迷你走势和一条目标进度。因为它**参与联动**，所以它和普通图表一样使用 `link`、
`section`，并由同一套前端运行时重算。

先看它的三种用法，后面所有内容都围绕这张表展开：

| 用法 | 代码 | 数据来源 | 能否联动重算 |
| --- | --- | --- | --- |
| 静态值 | `edv.kpi(1630000, label="销售额")` | Python 直接传入数字 | 否（`dataRef=None`，页面里没有明细数据） |
| 从 DataFrame 聚合 | `edv.kpi(df, value="销售额")` | 前端按 `agg` 现算 | 是 |
| 带迷你走势 | `edv.kpi(df, value="销售额", spark="销售额", spark_x="月份")` | 前端按 `spark_x` 分组 | 是 |

```python
import eazy_data_viz as edv

df = edv.sample_df()
df.shape          # (1500, 11)
df["销售额"].sum()  # 约 1631033.57

# 三种用法各来一张
edv.kpi(1630000, label="销售额（静态）")
edv.kpi(df, value="销售额", label="销售额（聚合）")
edv.kpi(df, value="销售额", label="销售额（带走势）", spark="销售额", spark_x="月份")
```

三张卡都能 `.to_html()` / `.save()` / `.show()`；真正做驾驶舱时把它们和别的图一起放进
`edv.dashboard(...)`。

## 1. 参数总表

签名（Python 3.8 下和文档一致，全部是关键字参数）：

```python
kpi(data=None, value=None, *, agg="sum", label=None, fmt=None,
    delta=None, delta_label=None, inverse=False,
    target=None, target_label=None,
    spark=None, spark_x=None,
    hint=None, unit=None, prefix=None, accent=0,
    height=150, theme="light", title=None, subtitle=None,
    link=None, section=None)
```

| 参数 | 默认 | 作用 | 坑 |
| --- | --- | --- | --- |
| `data` | `None` | DataFrame，或直接一个数字 | 数字必须 `int`/`float` 且没传 `value` |
| `value` | `None` | 要聚合的数值列 | DataFrame 里只有 1 个数值列时可省略 |
| `agg` | `"sum"` | `sum/mean/count/max/min/median` | 传 `avg` 会报 `ValueError` |
| `label` | `None` | 数值上方的指标名 | 静态用法下 `title` 会兜底成 `label` |
| `fmt` | `"compact"` | `compact/thousands/raw/percent/currency` | 只是**显示格式**，不改变数值 |
| `delta` | `None` | 涨跌幅 | `0.128` 显示 12.8%；`1280` 按原值显示 |
| `delta_label` | `None` | 涨跌幅口径，如“同比”“环比” | 不传就只显示箭头和数字 |
| `inverse` | `False` | 越小越好（成本、退货率） | 只影响**颜色**，箭头方向不变 |
| `target` | `None` | 目标数值 | 必须是数字；`0` 不显示徽标 |
| `target_label` | `None` | 徽标文字 | 默认渲染成“目标 200万” |
| `spark` | `None` | 迷你走势的数值列 | 必须同时给 `spark_x` |
| `spark_x` | `None` | 走势横轴列 | 建议时间列或有序分类列 |
| `hint` | `None` | 卡片底部小字（口径说明） | 不写且带 `link` 时自动显示联动提示 |
| `unit` | `None` | 数值后缀 | 字符串，如 `" 单"`、`"%"` |
| `prefix` | `None` | 数值前缀 | 常用于 `"≈"`、`"<"` |
| `accent` | `0` | 配色序号（0 起） | 超出会按 `accent % 10` 循环 |
| `height` | `150` | 卡片高度 | 最小 120，低于报 `ValueError` |
| `theme` | `"light"` | `light/dark` | 通常由 Dashboard 统一控制 |
| `title` / `subtitle` | `None` | 卡片标题/副标题 | 一般不用，`label` 已够 |
| `link` | `None` | 联动组名 | 同组图表点击后这张卡重算 |
| `section` | `None` | 看板分区标题 | KPI 卡**自带**该参数，不是所有图都有 |

**结论**：KPI 参数分四组——取数（`data/value/agg`）、显示（`label/fmt/unit/prefix`）、
状态（`delta*/inverse/target*/spark*`）、布局（`accent/height/theme/link/section`）。
记住分组，就不会在 16 个参数里迷路。

## 2. 数字格式化：`fmt` 到底输出什么

`fmt` 的实现在前端 `fmtValue()`，规则如下（`1,630,000` 为例）：

| `fmt` | 输出 | 规则 |
| --- | --- | --- |
| `compact`（默认） | `163万` | ≥1 亿用“亿”，≥1 万用“万”，否则千分位 |
| `thousands` | `1,630,000` | 千分位，最多 3 位小数后去掉尾零 |
| `raw` | `1630000` | 原样，最多 3 位小数 |
| `percent` | `1630000%` | 数字后直接加 `%`，**不会乘 100** |
| `currency` | `¥1,630,000` | 加 `¥`，保留 2 位小数（尾零去掉） |

```python
money = 1_630_000.0

edv.kpi(money, label="compact", fmt="compact")     # 163万
edv.kpi(money, label="thousands", fmt="thousands") # 1,630,000
edv.kpi(money, label="raw", fmt="raw")             # 1630000
edv.kpi(money, label="currency", fmt="currency")   # ¥1,630,000
edv.kpi(19.87, label="毛利率", fmt="percent")       # 19.9%
```

- `percent` **不乘 100**：传 `0.1987` 会显示 `0.2%`，传 `19.87` 才是 `19.9%`。
  这是新手第一大坑；
- `compact` 的小数位由量级决定：`<100` 保留 1 位，`>=100` 取整（`1631033` → `163万`）；
- `prefix` 加在格式化后的最前面，`unit` 加在最后面：

```python
edv.kpi(df, value="订单数", fmt="thousands", prefix="≈", unit=" 单")
# 显示：≈12,345 单
```

- **`fmt` 只影响显示，不影响 `delta`**：`delta` 永远按“比例 / 绝对量”两套规则走，见第 4 节。

## 3. 八个真实场景

下面每段都能单独运行；每段后面写了预期看到的结果（数值随 `sample_df()` 固定 seed 稳定）。

### 场景 1：同比增长

```python
edv.kpi(df, value="销售额", label="全年销售额",
        delta=0.128, delta_label="同比", accent=0)
```

预期：大数字 `163万`，右侧绿色 `▲ 12.8%`，再右边灰色小字 `同比`。
`0.128` 的绝对值 ≤ 1，被当作比例，显示为百分比。

### 场景 2：目标达成

```python
edv.kpi(df, value="销售额", label="销售额",
        target=2_000_000, target_label="年度目标", accent=1)
```

预期：右上角徽标“年度目标”，底部进度条 + `82%`（163万 ÷ 200万）。
把 `target` 改成 `1_000_000` 再看，进度条到 100% 封顶，右侧百分比变绿并显示 `163%`。

```python
# 达成率超过 100%：进度条封顶，但百分比照实显示
edv.kpi(df, value="销售额", label="销售额", target=1_000_000)
```

- `target` 是**常量**；想让每个大区各自的目标来自数据列，用 `bullet`（见 10 篇）；
- 徽标文字 = `target_label` 或 `目标 <格式化后的 target>`；
- `target=0` 视为没目标，不显示徽标（避免除零）。

### 场景 3：反向指标（越小越好）

```python
edv.kpi(df, value="利润", label="获客成本（示例）",
        delta=-0.03, delta_label="环比", inverse=True, accent=2)
```

预期：`▼ 3%` 是**绿色**。因为 `inverse=True` 时，“下降”被判定为好事。
箭头方向永远表示数值升降，颜色才表示好坏：

| `inverse` | `delta` | 箭头 | 颜色 | 含义 |
| --- | --- | --- | --- | --- |
| `False` | `+0.08` | ▲ | 绿 | 涨了，且涨是好事 |
| `False` | `-0.08` | ▼ | 红 | 跌了，且跌是坏事 |
| `True` | `+0.08` | ▲ | 红 | 涨了，但涨是坏事 |
| `True` | `-0.08` | ▼ | 绿 | 跌了，是好事 |

### 场景 4：单位与前后缀

```python
edv.kpi(df, value="订单数", label="订单量",
        fmt="thousands", unit=" 单", accent=3)
edv.kpi(df, value="客户数", label="客户数", fmt="raw", unit=" 人")
edv.kpi(df, value="销售额", label="GMV（估算）", fmt="compact", prefix="≈")
```

预期：`2,568 单` / `1,922 人` / `≈163万`。
单位写在 `unit` 里而不是拼进 `label`，这样数字仍能按数值格式化、换主题不跑版。

### 场景 5：口径提示

```python
edv.kpi(df, value="销售额", label="销售额",
        hint="2024 全年 · 含税 · 未剔除退款", delta=0.128, delta_label="同比")
```

预期：卡片底部一行灰色小字，清晰写出统计口径。
**口径提示是 KPI 卡最容易被忽略、又最能减少扯皮的功能**——凡是“这个数怎么来的”
会被追问的指标，都写 `hint`。

### 场景 6：联动重算

```python
page = edv.dashboard(
    edv.kpi(df, value="销售额", label="销售额", link="g1",
            delta=0.128, delta_label="同比", hint="点击下方大区联动"),
    edv.kpi(df, value="利润", label="利润", link="g1"),
    edv.bar(df, x="大区", y="销售额", link="g1",
            title="点柱子 → 上面两张卡按大区重算"),
    cols=2, title="联动演示")
page.save("examples/output/kpi_link.html")
```

预期：打开 HTML，点任意柱子，两张卡的数值变成该大区的合计；再点同一根柱子取消筛选，
卡片恢复全年值。

- 联动要求**组名一致**（都在 `"g1"` 组）；
- KPI 卡必须从 DataFrame 聚合（`value=`）才能重算；静态值不参与；
- 如果卡片没写 `hint`，带 `link` 时会自动显示“联动组 g1 · 点同组图表筛选”。

### 场景 7：静态值

```python
# 外部算好的比率/外部系统同步来的数字
edv.kpi(19.87, label="毛利率", fmt="percent", delta=0.012, delta_label="同比")
edv.kpi(1280000, label="竞品销售额（第三方口径）", fmt="compact", hint="数据源：行业报告")
```

预期：渲染与聚合型完全一样，但页面里**不嵌明细数据**（`dataRef=None`），
体积更小，也**不会**随联动变化。

什么时候用静态值：

1. 比率已经在外部分母/分子算好，前端 `sum/mean` 会算错；
2. 数据来自别的系统，不可能随当前筛选重算；
3. 纯展示的“行业基准”“目标值”本身。

### 场景 8：环比

```python
last_month = df[df["月份"] == "12月"]["销售额"].sum()
prev_month = df[df["月份"] == "11月"]["销售额"].sum()
mom = (last_month - prev_month) / prev_month        # -0.018657...

edv.kpi(df, value="销售额", label="12 月销售额",
        delta=mom, delta_label="环比", fmt="compact")
```

预期：`▼ 1.9% 环比`。注意 `-0.018657` 的绝对值 ≤ 1 → 按比例显示为 `1.9%`；
如果业务给的已经是“-4.1 个百分点”，直接传 `delta=-4.1`，会按绝对量显示 `▼ 4.1`。

**涨跌幅两套规则**（`deltaText()` 实现）：

| `abs(delta)` | 显示 | 适用 |
| --- | --- | --- |
| `<= 1` | 百分比，保留 1 位（`0.128` → `12.8%`） | 增长率、环比、占比变化 |
| `> 1` | 原数值，最多 3 位小数（`-4.1` → `4.1`） | 百分点、分数、人数变化 |

## 4. 迷你走势 `spark` / `spark_x`

```python
edv.kpi(df, value="销售额", label="销售额",
        spark="销售额", spark_x="月份", accent=0)
```

渲染逻辑（`kpiSparkPoints()`）：

1. 先按当前联动筛选过滤行（所以走势也会跟着联动变）；
2. 按 `spark_x` 分组、对 `spark` 做 `agg` 聚合；
3. 按分类/时间的自然顺序排序（`2月` 在 `10月` 前，日期按时间先后）；
4. 点数 ≥ 2 才画；少于 2 个点静默不显示（不报错）；
5. 折线 + 13% 透明度面积 + 最后一个点的圆点，颜色取 `accent`。

```python
# 按日：1500 行会聚合成 30 多个点，太密，不建议
edv.kpi(df, value="销售额", label="日销售额", spark="销售额", spark_x="日期")

# 按月：12 个点，最合适的粒度
edv.kpi(df, value="销售额", label="月度走势", spark="销售额", spark_x="月份")

# 按渠道没有“顺序”概念，走势没意义
# edv.kpi(df, value="销售额", spark="销售额", spark_x="渠道")   # 不推荐
```

**`spark_x` 最好是有序的**：时间列、`pd.Categorical(ordered=True)` 的月份列，
或者本身就是数值的列。普通字符串分类虽然能画，但顺序取决于数据里出现的先后，
容易画出“乱跳”的线。

错误示范：

```python
edv.kpi(df, value="销售额", spark="销售额")
# ValueError: 带迷你走势的 KPI 需要 spark_x（横轴列），例如
# kpi(df, value="销售额", spark="销售额", spark_x="月份")。
```

## 5. `accent` 与配色

`accent` 是**配色库里的序号**，`0` 是主色。默认 `google` 配色：

| `accent` | 0 | 1 | 2 | 3 |
| --- | --- | --- | --- | --- |
| google 色值 | `#1a73e8` 蓝 | `#188038` 绿 | `#f9ab00` 黄 | `#d93025` 红 |

- 它影响：卡片左侧强调色、迷你走势线、目标进度条；
- 序号会 `% 10` 循环（10 套色只有 10 个），`accent=12` 等价于 `accent=2`；
- 换 `dashboard(palette="tableau")` 或 `chart.palette("morandi")` 后，序号对应的色自动换；
- `accent` 必须是 ≥0 的整数，`-1` / `1.5` 报 `ValueError`。

```python
cards = [edv.kpi(df, value="销售额", label=f"指标{i}", accent=i) for i in range(4)]
page = edv.dashboard(*cards, cols=4, title="四色指标头", palette="tableau")
```

预期：四张卡的颜色依次取 `tableau` 的前 4 色（蓝、橙、红、青）。

## 6. `group_kpi`：一屏多指标

当指标很多（比如 8 个渠道的完成率），一张张写 `kpi` 太啰嗦。`group_kpi` 用一个
HTML 卡片组渲染多个小指标，支持三种数据来源：

```python
# 用法 A：每个数值列一张小卡（自动取全部数值列）
edv.group_kpi(df)

# 用法 B：按维度分组，每组一张小卡
edv.group_kpi(df, names="大区", values="销售额")

# 用法 C：完全手工 items
edv.group_kpi(items=[
    {"label": "销售额", "value": 1630000, "delta": 0.128, "fmt": "compact"},
    {"label": "流失率", "value": 3.2, "unit": "%", "hint": "越低越好"},
    {"label": "目标达成", "value": 82, "unit": "%", "delta": 0.02},
])
```

`items` 每项可用字段：`label` / `value` / `delta` / `unit` / `fmt` / `hint`。
排序 `sort="desc"`（默认按值降序），`top_n=6` 只显示前 6 个，`height=140`。

```python
edv.group_kpi(df, names="产品", values="销售额", top_n=4, unit=" 元", fmt="compact")
```

预期：4 张小卡一行排开，每张显示产品名 + 销售额。

- `items` 不是 dict 会报 `TypeError: items[0] 需要是 dict，例如 {"label": "总销售额", "value": 123}，收到 'str'`；
- 什么都不给会报 `ValueError: group_kpi 需要 data（DataFrame）或 items=[...]，例如 group_kpi(df, names="大区", values="销售额")。`；
- `group_kpi` 是 HTML 组件，**没有** ECharts 画布，`height` 按行数自动撑开
  （每行 4 个小卡，行高 62px）。

## 7. 在 Dashboard 里排 KPI 区

```python
kpis = [
    edv.kpi(df, value="销售额", label="销售额", fmt="compact",
            delta=0.128, delta_label="同比", target=2_000_000,
            spark="销售额", spark_x="月份", accent=0,
            link="g1", section="一、核心指标"),
    edv.kpi(df, value="利润", label="利润", delta=0.086, delta_label="同比",
            accent=1, link="g1", section="一、核心指标"),
    edv.kpi(df, value="订单数", label="订单数", fmt="thousands", unit=" 单",
            delta=0.064, accent=2, link="g1", section="一、核心指标"),
    edv.kpi(19.87, label="毛利率", fmt="percent", delta=0.012,
            delta_label="同比", accent=3, hint="静态值，不参与联动",
            section="一、核心指标"),
]

page = edv.dashboard(
    *kpis,
    edv.bar(df, x="大区", y="销售额", link="g1", title="点柱子联动上方 KPI"),
    cols=2, title="KPI 区示例")
```

排版建议：

| 卡片数 | `cols` | `height` | 说明 |
| --- | --- | --- | --- |
| 2~3 | 2 | 150 | 常规驾驶舱首行 |
| 4 | 4 | 150 | 最紧凑，宽屏推荐 |
| 4 | 2 | 150 | 两行两列，适合中等宽度 |
| 6+ | 用 `group_kpi` | 140 | 避免 KPI 卡占满首屏 |

- `cols` 是**整个 Dashboard** 的网格列数，KPI 和普通图共用；KPI 区想 4 列、
  图表区想 2 列时，把 KPI 单独做成一个 Dashboard 再拼 iframe（见 07 篇），
  或者接受 2 列布局（更稳）；
- 4 张卡写同一个 `section`，Dashboard 只插一次分区标题；
- 静态卡不会随联动重算，最好在 `hint` 里讲明，否则观众会以为它坏了。

## 8. 常见问题

| 现象 / 报错 | 原因 | 修法 |
| --- | --- | --- |
| `ValueError: target 需要是数字（目标值），收到 '200万'` | `target` 传了字符串 | 传 `2000000`，单位交给 `fmt`/`unit` |
| `ValueError: 带迷你走势的 KPI 需要 spark_x（横轴列）…` | 只给了 `spark` | 补 `spark_x="月份"` |
| `ValueError: kpi 需要指定 value 列，例如 kpi(df, value="销售额")。` | 表里有多个数值列却没给 `value` | 显式指定 `value="销售额"` |
| `ValueError: kpi 需要数据：kpi(df, value="销售额") 或 kpi(1630000, label="销售额")。` | `data=None` | 给 DataFrame 或直接给数字 |
| `ValueError: accent 需要是 >=0 的整数（配色序号），收到 -1` | `accent` 负数/浮点 | 用 0~9 的整数 |
| `ValueError: height 至少 120（像素），收到 100` | 卡片压得太矮 | `height=120` 起 |
| 数字显示 `0.2%` 而不是 `20%` | `fmt="percent"` 不乘 100 | 传百分数（19.9）或改用 `delta` |
| 涨跌幅显示成 `1280%` 而不是 `12.8%` | `delta=12.8` 被当作绝对量 | 传比例 `0.128` |
| 目标徽标不出现 | `target=None` 或 `target=0` | 给非零数字 |
| 卡片不随筛选变 | 用了静态值，或 `link` 组名不一致 | 用 `value=` 聚合并统一 `link` |
| 迷你走势没画出来 | 分组后点数 < 2 | 换更粗的粒度（月/周） |

最后一条最隐蔽：`spark_x` 如果传了全是唯一值的列（例如每行一个订单号），
前端聚合后每个点只有 1 行，虽然能画但会是一条噪声线。**迷你走势是给“少量有序点”用的**。

## 下一篇

- 想控制整页颜色和深浅色：[05 · 配色与主题](05-palette-and-theme.md)
- 想让 KPI 和别的图真正联动起来：[06 · 交互总览](06-interaction.md)
- 想要一个完整驾驶舱：[03 · 经营驾驶舱实战](03-cockpit-tutorial.md)
