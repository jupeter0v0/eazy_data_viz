# 09 · 数据准备

> 目标：把原始 DataFrame 整理成「画出来就对」的数据。本库不要求你改表结构，但列类型、缺失值、日期格式、分类顺序会直接决定排序、聚合和联动是否正确。
>
> 约定：下文都用 `import eazy_data_viz as edv` 与 `df = edv.sample_df()`，代码可在仓库根目录直接运行。

## 0. 先给数据做一次体检

出图前先看 dtype、缺失、重复、唯一值四件事，90% 的「图不对」都能在这一步发现。

```python
import pandas as pd
import eazy_data_viz as edv

df = edv.sample_df()
check = pd.DataFrame({"dtype": df.dtypes.astype(str), "缺失": df.isna().sum(),
                      "唯一值": df.nunique(), "示例": [df[c].iloc[0] for c in df.columns]})
print(check)
```

体检结论要能回答：哪列是度量（能求和）、哪列是维度（用来分组）、时间列是不是真的 `datetime64`、有没有 `object` 里混着数字或布尔。

## 1. 列类型：本库只认四类

| 类型 | pandas 判定 | 典型角色 | 本库怎么处理 |
| --- | --- | --- | --- |
| 数值 `num` | `int*` / `float*` / 可空数值 | `y`、`value`、`size` | 聚合前 `round(4)`；`NaN` 变 `null` |
| 时间 `time` | `datetime64[ns]`（含 tz） | `x`、`date`、`start/end` | 格式化为 `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM` |
| 分类 `cat` | `object` / `string` / `category` | `x`、`names`、`color`、`drill` | 转字符串，超过 120 字符截断加 `…` |
| 布尔 `bool` | 真正的 `bool` dtype | `x`、`color` | 转成「是 / 否」 |

```python
import pandas as pd
import eazy_data_viz as edv

df = edv.sample_df()
df["是否大额"] = df["销售额"] > 8000          # 真正的 bool dtype
df["销售额文本"] = df["销售额"].map(lambda v: "%.2f" % v)

print(df["是否大额"].dtype)                  # bool
c = edv.bar(df, x="是否大额", y="订单数")
print(c.spec["roles"]["x"])                  # '是否大额'
print(c.data["kinds"]["是否大额"])           # 'bool'
```

注意两个坑：

* `bool` 列一旦混入 `None`，dtype 会退化成 `object`，本库按**分类**处理（`None` 会变成 `null`，图上出现 `(空)` 组），不会显示「是 / 否」。
* 只有数值角色（`y`/`value`/`size` 等）会自动尝试把「像数字的文本」转成数值；`x` 永远按分类/时间处理。

### 1.1 文本数字：≥99% 能转才自动转

```python
import pandas as pd
import eazy_data_viz as edv

df = edv.sample_df()
df["销售额文本"] = df["销售额"].map(lambda v: "%.2f" % v)
print(edv.bar(df, x="大区", y="销售额文本").data["kinds"]["销售额文本"])   # 'num'

df["脏列"] = ["1", "2", "不是数字", "4", "5"] + ["1"] * (len(df) - 5)
try:
    edv.bar(df, x="大区", y="脏列")
except TypeError as exc:
    print(type(exc).__name__, str(exc)[:60])
```

转换阈值是「非空值里 ≥99% 可被 `pd.to_numeric` 解析」。不达标时请自己清洗，不要依赖自动转换：

```python
import pandas as pd

raw = pd.Series(["12.5", "x", "8"])
clean = pd.to_numeric(raw, errors="coerce")
print(clean.tolist())        # [12.5, nan, 8.0]，坏值变 NaN，再决定 fillna 还是丢弃
```

### 1.2 日期列的唯一标准：`datetime64`

`bar` / `line` **不会**把 `"2024-01-31"` 这种字符串解析成日期，只会把它当分类列，排序和横轴粒度都会错。

```python
import pandas as pd
import eazy_data_viz as edv

raw = edv.sample_df()[["日期", "销售额"]].copy()
raw["日期"] = raw["日期"].dt.strftime("%Y-%m-%d")     # 变成 object
print(edv.line(raw, x="日期", y="销售额").spec["sort"])      # 'none'：按首次出现顺序

fixed = raw.copy()
fixed["日期"] = pd.to_datetime(fixed["日期"])
print(edv.line(fixed, x="日期", y="销售额").spec["sort"])    # 'x'：按时间排序
```

例外：`calendar(date=...)`、`gantt(start=..., end=...)`、`candlestick(date=...)` 三个函数会对日期列自动做 `pd.to_datetime`，并校验无法解析的值；但为了统一，仍建议进门先转好。

## 2. 缺失值：先决定它代表什么

本库把 `NaN` / `NaT` / `pd.NA` 统一转成 JSON `null`，前端规则是：

* 分类列的 `null` → 归入 `(空)` 组，**会出现在图上**；
* 数值列的 `null` → `sum/mean/max/min/median` 跳过该值，`count` 仍统计这一行；
* 时间列的 `null` → 该点在时间轴上没有位置（折线可能断开）。

```python
import pandas as pd
import eazy_data_viz as edv

d = pd.DataFrame({
    "城市": ["上海市", "南京市", None, "杭州市"],
    "销售额": [100.0, None, 300.0, 400.0],
})
c = edv.bar(d, x="城市", y="销售额")
print(c.data["rows"])        # 第 3 行 ['(空)', None] 对应空城市、空销售额

d["城市"] = d["城市"].fillna("未知")       # 空值有业务含义时才补
d["销售额"] = d["销售额"].fillna(0)
edv.bar(d, x="城市", y="销售额").save("examples/output/09-missing.html")
```

不要无条件 `fillna(0)`：对 `mean` 而言，补 0 会把均值拉低。比率类指标（利润率、达成率）要先保证分子分母同时非空，再计算。

## 3. 重复值：本库不自动去重

`count` 聚合统计的是**行数**，重复行会让计数和求和翻倍。出图前用业务主键检查：

```python
import pandas as pd
import eazy_data_viz as edv

df = edv.sample_df()
df = pd.concat([df, df.head(10)], ignore_index=True)   # 人为制造 10 条重复
print(df.duplicated().sum())                           # 10
print(edv.bar(df, x="大区", y="订单数").data["n"])      # 1510，重复行也嵌进去了

clean = df.drop_duplicates()
print(edv.bar(clean, x="大区", y="订单数").data["n"])    # 1500
```

真实业务往往不能整行去重（同一天同一门店可能有多笔订单），应指定业务主键：`df.drop_duplicates(subset=["日期", "城市", "产品"])`。

## 4. 日期列：转换、粒度与排序

### 4.1 字符串 → datetime

```python
import pandas as pd

raw = pd.DataFrame({"月": ["2024-01", "2024-02", "2024-03"], "销售额": [10, 12, 9]})
raw["月"] = pd.to_datetime(raw["月"], format="%Y-%m")     # 2024-01-01 等月初
print(raw.dtypes)
```

`errors="coerce"` 可以把脏值变成 `NaT` 便于定位，但不要直接把 `NaT` 丢给图表——先决定丢弃还是补值。

### 4.2 月 / 季 / 年：生成稳定的排序键

```python
import pandas as pd
import eazy_data_viz as edv

df = edv.sample_df()
df["月"] = df["日期"].dt.to_period("M").astype(str)       # '2024-01'
df["季度"] = df["日期"].dt.to_period("Q").astype(str)     # '2024Q1'
df["年"] = df["日期"].dt.year
print(df[["日期", "月", "季度", "年"]].head(3))

monthly = df.groupby("月", as_index=False)["销售额"].sum()
edv.line(monthly, x="月", y="销售额").save("examples/output/09-monthly.html")
```

`to_period("M").astype(str)` 得到的是 `2024-01` 而不是 `2024-01-01`，横轴更干净；它是**字符串**，所以画之前要按 `月` 排一次序（或设成有序分类，见第 5 节）。

### 4.3 时间粒度与排序

* `line` / `area` / `combo` 的 `x` 是 `datetime64` 时，默认 `sort="x"`，前端按时间升序；
* `x` 是字符串类别时，默认 `sort="none"`（按首次出现顺序），很容易画出「1月、10月、11月、2月」这种顺序；
* 需要固定顺序就设有序分类，或先 `sort_values` 再出图。

## 5. 分类顺序：`pd.Categorical(ordered=True)` 才生效

`edv.sample_df()` 的 `月份` 列本身就是有序分类。本库会把分类的 `categories` 顺序写进页面数据（`data["orders"]`），前端按它排序。

```python
import pandas as pd
import eazy_data_viz as edv

df = edv.sample_df()
c = edv.bar(df, x="月份", y="销售额")
print(c.spec["sort"])                 # 'x'：识别为有序分类，按类别顺序
print(c.data["orders"]["月份"][:3])   # ['1月', '2月', '3月']
```

自己构造时注意两点：`categories` 要写全（否则未列出的值变 `NaN`），`ordered=True` 不能漏。

```python
import pandas as pd
import eazy_data_viz as edv

df = edv.sample_df()
df["季度"] = pd.Categorical(
    df["日期"].dt.to_period("Q").astype(str),
    categories=["2024Q1", "2024Q2", "2024Q3", "2024Q4"],
    ordered=True,
)
c = edv.bar(df, x="季度", y="利润")
print(c.spec["sort"])                 # 'x'
print(c.data["orders"]["季度"])       # ['2024Q1', '2024Q2', '2024Q3', '2024Q4']
```

如果顺序该由指标决定（从高到低），不要设有序分类，直接用 `sort="desc"` 或 `top_n`（Top N 写法见 [11-cookbook.md](11-cookbook.md) 配方 1）。

`top_n` 会把尾部合并成「其他」；「其他」不可点击下钻/联动（它的名字不对应任何行），需要完整覆盖时请先自己过滤数据。

## 6. 长表 / 宽表：进库前统一成长表

本库每个图表函数只接收**一个数值列**（`combo`、`bullet`、`target`、`dumbbell` 等少数例外接收两个）。宽表请先 `melt`：

```python
import pandas as pd
import eazy_data_viz as edv

df = edv.sample_df()
wide = df.pivot_table(index="月份", columns="渠道", values="销售额",
                      aggfunc="sum", observed=True).reset_index()
print(wide.columns.tolist())          # ['月份', '直销', '渠道代理', '线上商城']

long = wide.melt(id_vars="月份", var_name="渠道", value_name="销售额")
c = edv.bar(long, x="月份", y="销售额", color="渠道", stack=True)
print(c.spec["roles"])                # x=月份, y=销售额, color=渠道
```

反过来的宽表需求（每行一个对象、多列指标）不是本库的输入格式：
想同时看多个指标，用多张图，或 `combo` / `bullet` 这类原生双列的图。

## 7. 派生列：比率、同比、期间、目标

### 7.1 利润率：先算比率再决定 `fmt`

`fmt="percent"` 只负责在**数值后面加 `%`**，不会乘 100。所以传 12.8 显示 `12.8%`，传 0.128 显示 `0.1%`。

```python
import numpy as np
import eazy_data_viz as edv

df = edv.sample_df()
df["利润率"] = np.where(df["销售额"] > 0, df["利润"] / df["销售额"] * 100, np.nan)
c = edv.bar(df, x="产品", y="利润率", agg="mean", fmt="percent", sort="desc")
print(c.spec["fmt"])                  # 'percent'
```

### 7.2 同比 / 环比：本质是「同一维度错位一期」

```python
import pandas as pd
import eazy_data_viz as edv

df = edv.sample_df()
df["月"] = df["日期"].dt.to_period("M").astype(str)
monthly = df.groupby("月", as_index=False)["销售额"].sum().sort_values("月")
monthly["环比"] = monthly["销售额"].pct_change() * 100
monthly["同比"] = monthly["销售额"].pct_change(12) * 100
print(monthly.dropna().head(1)[["月", "环比", "同比"]])
edv.line(monthly, x="月", y="环比", fmt="percent").save("examples/output/09-mom.html")
```

`pct_change(12)` 用第 12 行之前的值当去年同期；如果数据不是连续 12 个月，请先按业务期间补全或直接 merge 去年同期，别让错位变成「错 12 行」。

### 7.3 期间划分与目标列

```python
import numpy as np
import pandas as pd
import eazy_data_viz as edv

df = edv.sample_df()
df["档期"] = np.select(
    [df["日期"] < "2024-04-01", df["日期"] < "2024-10-01"],
    ["Q1", "Q2-Q3"], default="Q4",
)
df["销售额目标"] = df["销售额"] * 1.1          # 演示：目标列与实绩同表
print(df[["档期", "销售额", "销售额目标"]].head(2))

edv.bullet(df, x="产品", actual="销售额", target="销售额目标").save(
    "examples/output/09-bullet.html")
```

`bullet` / `target` / `dumbbell` 是「宽表友好」的少数派：它们直接吃两列数值列，不用 melt。

## 8. 大数据量：`max_rows` 默认 200000，采样是均匀的

本库在 Python 侧只做校验与数据嵌入，聚合全部在浏览器里完成，所以行数直接决定 HTML 体积。`max_rows` 控制**嵌入前**的采样：

```python
import eazy_data_viz as edv

big = edv.sample_df(rows=200000)
c = edv.bar(big, x="大区", y="销售额", max_rows=5000)
print(c.data["n"], c.warnings["warnings"][:1])
# 5000 ['数据 200000 行，超过 max_rows=5000，已均匀采样 5000 行用于绘图。']

c_all = edv.bar(big, x="大区", y="销售额", max_rows=None)
print(c_all.data["n"])                # 200000，不采样（文件也会大一个量级）

c2 = edv.line(big.sort_values("日期"), x="日期", y="销售额", max_rows=2000)
print(c2.data["n"], c2.data["n_total"])   # 2000 200000
```

采样不是随机抽签，而是 `np.linspace` 等距取行号：**按行位置均匀覆盖整张表**。因此：

* 表按时间排好序再采样 → 时间覆盖仍然均匀；
* 表按业务分组排序后采样，会近似按组分层；
* 若要「每个类目都保留」，请先聚合到类目级再出图，或先分组采样后 `concat`。

体积经验值（11 列 `sample_df`，单图）：1 千行 ≈ 1.3 MB、5 千行 ≈ 1.7 MB、5 万行 ≈ 6.7 MB、20 万行 ≈ 23 MB；而图表运行时代码本身固定约 1.2 MB。精确测量见 [13-performance.md](13-performance.md)。

## 9. 多张图复用同一份 DataFrame：`dataRef` 去重

本库给每份嵌入数据算内容指纹 `data_ref`（基于列、行、分类顺序的 SHA-1）。同一个 `df`（甚至 `df.copy()`）画多张图，指纹相同，看板里**只嵌一次**：

```python
import eazy_data_viz as edv

df = edv.sample_df()
c1 = edv.bar(df, x="大区", y="销售额")
c2 = edv.pie(df, names="渠道", values="销售额")
c3 = edv.bar(df.copy(), x="产品", y="利润")
print(c1.data_ref == c2.data_ref == c3.data_ref)     # True

page = edv.dashboard(c1, c2, c3, cols=2, title="复用").to_html()
print(round(len(page.encode("utf-8")) / 1024 / 1024, 2), "MB")   # 约 1.4 MB
```

反过来，如果每张图各拿一份**过滤后不同**的数据（例如四个大区各一份），每份都会嵌一遍。更省体积的写法是合成一张表、加一列来源、让图去分组：

```python
import pandas as pd
import eazy_data_viz as edv

df = edv.sample_df()
east = df[df["大区"] == "华东"]
north = df[df["大区"] == "华北"]
merged = pd.concat([east, north], ignore_index=True)
c = edv.bar(merged, x="城市", y="销售额", color="大区", stack=True)
print(len(c.data["rows"]))            # 只有一份数据
```

数据准备做到这里就够了：列类型对、缺失有交代、日期是真时间、分类顺序明确、派生列算好、大表采样有数。下一步按「要回答的问题」选图：[10-chart-selection.md](10-chart-selection.md)。
