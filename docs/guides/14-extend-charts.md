# 14 · 扩展图表

> 目标：照着本文新增一种图表（Python 函数 + 前端 builder + 测试 + 文档 + gallery），并且不在仓库里留下半成品。
> 先读 [EXTRA_CHARTS.md](../EXTRA_CHARTS.md) 了解「Python 只校验、JS 做聚合」的分工，本篇给一个从零到可运行的完整样例 `heat_strip`（一行一条热力带）。

## 1. 先判断该不该新增

| 你的需求 | 做法 |
| --- | --- |
| 现有 49 种图的参数组合能表达 | 不要新增，直接用（见 [10 · 选图](10-chart-selection.md)） |
| 只是换配色 / 轴 / 标签 | 用公共参数 `palette/xtitle/fmt/...`，不要改源码 |
| 新的图形，但仍是「按维度分组 + 聚合一个数值」 | 走本文路线：`extraBuilders` + ECharts option |
| 纯文字/HTML 卡片（类似 KPI、表格） | 走 `htmlBuilders`，见第 6 节 |
| 交互能通过 ECharts 配置实现 | 优先用 `extraBuilders`，不要自己写 DOM 事件 |

## 2. 改动地图

| 文件 | 改什么 | 是否必须 |
| --- | --- | --- |
| `eazy_data_viz/charts_extra.py` | 新增 `heat_strip()` 函数，内部调 `_ext()` 并 `return Chart(...)` | 必须 |
| `eazy_data_viz/chart.py` | 在 `_NUMERIC_ROLE_KEYS` 里加 `"heat_strip": ("value",)`；否则数值列会被当类目转成字符串 | 必须 |
| `eazy_data_viz/__init__.py` | `from .charts_extra import heat_strip` + 加进 `__all__` | 必须 |
| `eazy_data_viz/assets/eazy_extra_b.js` | 注册 `EazyViz.extraBuilders.heat_strip = function (spec, data, state, theme) {...}` | 必须 |
| `eazy_data_viz/render.py` | 新建 JS 文件才要加进 `EXTRA_JS` / `ALL_JS`；HTML 类还要加进 `HTML_TYPES` | 视情况 |
| `tests/test_eazy.py` | 加一个 `t_heat_strip()` 并用 `check(...)` 注册 | 必须 |
| `tests/js_test.py` | 页面里加一张 `heat_strip`，断言渲染成功 | 必须 |
| `docs/api/heat_strip.md` | 函数 API 文档（`tools/check_docs.py` 会校验） | 必须 |
| `examples/charts/heat_strip.py` | 示例脚本 | 建议 |
| `tools/build_gallery.py` | 在 `main()` 里 `sections.append(_sec(X.heat_strip(...), s))` | 建议 |
| `tools/sync_doc_signatures.py` | 不用改：跑一遍就会用真实签名回填 `docs/api/heat_strip.md` 的「函数签名」块 | 建议 |

## 3. Python 侧

三个要点：**校验列 → 声明 roles → 交给 `_ext()` 打包**。`_ext()` 会做 `agg/fmt/theme/height/top_n` 校验、`max_rows` 采样、`dataRef` 计算，并返回 `spec, records, ref, info`。

```python
import eazy_data_viz as edv
from eazy_data_viz.chart import Chart, _NUMERIC_ROLE_KEYS
from eazy_data_viz.charts_extra import _ext
from eazy_data_viz import frame as _frame

# 正式提交时把这一行加进 chart.py 的 _NUMERIC_ROLE_KEYS 字典；
# 这里放在函数前，保证 value 按数值列处理。
_NUMERIC_ROLE_KEYS["heat_strip"] = ("value",)


def heat_strip(data, x, value, color=None, *, agg="sum", fmt="compact",
               labels=False, height=250, theme="light", title=None,
               subtitle=None, link=None, max_rows=200000):
    df = _frame.ensure_frame(data)
    _frame.require_column(df, x, "x（类目）")
    _frame.require_column(df, value, "value（数值）")
    if color is not None:
        _frame.require_column(df, color, "color（分组）")
    spec, records, ref, info = _ext(
        "heat_strip", df,
        {"x": x, "value": value, "color": color},
        title=title if title is not None else "%s 热力条" % value,
        subtitle=subtitle, fmt=fmt, height=height, theme=theme,
        agg=agg, labels=labels, legend=color is not None,
        link=link, max_rows=max_rows,
    )
    return Chart(spec, records, ref, info)
```

`Chart` 负责 `.to_html() / .save() / .show()`、`.palette()`、`.warnings`；不要在函数里写文件或开浏览器，保持「函数只返回 Chart」的约定。

## 4. JS 侧

注册一个 builder，签名固定为 `function (spec, data, state, theme)`，返回 ECharts option（或 `null` 表示空图）。数据在 `data.rows`（数组的数组），列名在 `data.cols`，别假设列顺序：

```javascript
EazyViz.extraBuilders.heat_strip = function (spec, data, state, theme) {
  var U = EazyViz.core.util;
  var rows = U.filteredRows(spec, data, state);   // 已应用联动/下钻筛选
  if (!rows.length) return U.emptyOption(theme);
  var roles = spec.roles, xdim = roles.x, vdim = roles.value, cdim = roles.color;
  var how = spec.agg || 'sum';
  var groups = U.groupBy(rows, cdim ? [cdim, xdim] : [xdim], vdim, how);
  var cats = [], strips = [], map = {};
  for (var i = 0; i < groups.length; i++) {
    var g = groups[i];
    var xv = cdim ? g.keys[1] : g.keys[0];
    var sv = cdim ? g.keys[0] : '';
    if (cats.indexOf(xv) < 0) cats.push(xv);
    if (strips.indexOf(sv) < 0) strips.push(sv);
    map[sv + U.SEP + xv] = g.value === null ? 0 : g.value;
  }
  var points = [], min = Infinity, max = -Infinity;
  for (var si = 0; si < strips.length; si++) {
    for (var xi = 0; xi < cats.length; xi++) {
      var v = map[strips[si] + U.SEP + cats[xi]];
      if (v === undefined) continue;
      if (v < min) min = v;
      if (v > max) max = v;
      points.push({ value: [xi, si, v], name: cats[xi] });
    }
  }
  if (!isFinite(min)) { min = 0; max = 1; }
  var xAxis = U.makeCategoryAxis(spec, cats, theme);
  var yAxis = U.makeCategoryAxis(spec, strips, theme);
  U.setAxisName(xAxis, spec.xtitle === undefined ? xdim : spec.xtitle, theme, true);
  U.setAxisName(yAxis, spec.ytitle === undefined ? '' : spec.ytitle, theme, false);
  return {
    grid: U.makeGrid(theme, { legend: false, rightExtra: 62 }),
    tooltip: {
      trigger: 'item',
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      textStyle: { color: theme.text, fontSize: 12 },
      formatter: function (p) {
        return '<b>' + U.esc(cats[p.value[0]]) + '</b><br/>' +
          U.esc(String(strips[p.value[1]])) + '：' + U.fmtValue(p.value[2], spec.fmt);
      }
    },
    xAxis: xAxis,
    yAxis: yAxis,
    visualMap: { show: false, min: min, max: max, inRange: { color: theme.heat } },
    series: [{
      type: 'heatmap',
      data: points,
      itemStyle: { borderColor: theme.bg, borderWidth: 2 },
      label: {
        show: !!spec.labels, color: theme.text, fontSize: 10,
        formatter: function (p) { return U.fmtValue(p.value[2], spec.fmt); }
      }
    }]
  };
};
```

### 常用工具（`EazyViz.core.util`）

| 工具 | 用途 |
| --- | --- |
| `rowsOf(data)` / `hasCol(data, col)` | 取行 / 判断列存在 |
| `filteredRows(spec, data, state)` | 应用联动、下钻、图例筛选后的行；所有 builder 都应先调它 |
| `groupBy(rows, dims, measure, how)` | 分组聚合，返回 `[{key, keys, value, cnt}]`；`how` 为 `sum/mean/count/max/min/median` |
| `catName(v)` / `num(v)` | 类目名（`null → "(空)"`）/ 数值（`NaN → null`） |
| `fmtValue(v, spec.fmt)` / `esc(s)` | 数值格式化 / HTML 转义（拼 tooltip 必须用） |
| `makeGrid(theme, opts)` / `makeCategoryAxis` / `makeValueAxis` / `setAxisName` | 坐标轴与网格的统一样式 |
| `makeLegend` / `makeToolbox` / `tooltipBox` / `emptyOption` | 图例 / 工具箱 / tooltip / 空图 |
| `THEME` / `theme.heat` / `theme.palette` | 主题色；不要硬编码颜色 |
| `currentXDim(spec, state)` / `setLink` | 联动维度；点击要能联动的图需在数据项上设置 `name` |
| `SEP` | 拼分组键的分隔符，避免自己造字符串 |

## 5. 完整可运行示例

下面这段不修改仓库任何文件：生成 PNG/HTML 后把 builder 注入页面，用于本地验证（正式扩展请按第 2 节把 JS 放进 `eazy_extra_b.js`）。运行后打开 `examples/output/heat_strip.html` 应看到 3 条色带、12 个月份。

```python
import eazy_data_viz as edv
from eazy_data_viz.chart import Chart, _NUMERIC_ROLE_KEYS
from eazy_data_viz.charts_extra import _ext
from eazy_data_viz import frame as _frame

_NUMERIC_ROLE_KEYS["heat_strip"] = ("value",)


def heat_strip(data, x, value, color=None, *, agg="sum", fmt="compact",
               labels=False, height=250, theme="light", title=None,
               subtitle=None, link=None, max_rows=200000):
    df = _frame.ensure_frame(data)
    _frame.require_column(df, x, "x（类目）")
    _frame.require_column(df, value, "value（数值）")
    if color is not None:
        _frame.require_column(df, color, "color（分组）")
    spec, records, ref, info = _ext(
        "heat_strip", df,
        {"x": x, "value": value, "color": color},
        title=title if title is not None else "%s 热力条" % value,
        subtitle=subtitle, fmt=fmt, height=height, theme=theme,
        agg=agg, labels=labels, legend=color is not None,
        link=link, max_rows=max_rows,
    )
    return Chart(spec, records, ref, info)


HEAT_STRIP_JS = r"""
EazyViz.extraBuilders.heat_strip = function (spec, data, state, theme) {
  var U = EazyViz.core.util;
  var rows = U.filteredRows(spec, data, state);
  if (!rows.length) return U.emptyOption(theme);
  var roles = spec.roles, xdim = roles.x, vdim = roles.value, cdim = roles.color;
  var groups = U.groupBy(rows, cdim ? [cdim, xdim] : [xdim], vdim, spec.agg || 'sum');
  var cats = [], strips = [], map = {};
  for (var i = 0; i < groups.length; i++) {
    var g = groups[i];
    var xv = cdim ? g.keys[1] : g.keys[0];
    var sv = cdim ? g.keys[0] : '';
    if (cats.indexOf(xv) < 0) cats.push(xv);
    if (strips.indexOf(sv) < 0) strips.push(sv);
    map[sv + U.SEP + xv] = g.value === null ? 0 : g.value;
  }
  var points = [], min = Infinity, max = -Infinity;
  for (var si = 0; si < strips.length; si++) {
    for (var xi = 0; xi < cats.length; xi++) {
      var v = map[strips[si] + U.SEP + cats[xi]];
      if (v === undefined) continue;
      if (v < min) min = v;
      if (v > max) max = v;
      points.push({ value: [xi, si, v], name: cats[xi] });
    }
  }
  if (!isFinite(min)) { min = 0; max = 1; }
  var xAxis = U.makeCategoryAxis(spec, cats, theme);
  var yAxis = U.makeCategoryAxis(spec, strips, theme);
  U.setAxisName(xAxis, spec.xtitle === undefined ? xdim : spec.xtitle, theme, true);
  U.setAxisName(yAxis, '', theme, false);
  return {
    grid: U.makeGrid(theme, { legend: false, rightExtra: 62 }),
    tooltip: {
      trigger: 'item',
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      textStyle: { color: theme.text, fontSize: 12 },
      formatter: function (p) {
        return '<b>' + U.esc(cats[p.value[0]]) + '</b><br/>' +
          U.esc(String(strips[p.value[1]])) + '：' + U.fmtValue(p.value[2], spec.fmt);
      }
    },
    xAxis: xAxis, yAxis: yAxis,
    visualMap: { show: false, min: min, max: max, inRange: { color: theme.heat } },
    series: [{
      type: 'heatmap', data: points,
      itemStyle: { borderColor: theme.bg, borderWidth: 2 },
      label: {
        show: !!spec.labels, color: theme.text, fontSize: 10,
        formatter: function (p) { return U.fmtValue(p.value[2], spec.fmt); }
      }
    }]
  };
};
"""

df = edv.sample_df()
chart = heat_strip(df, x="月份", value="销售额", color="渠道", height=260)
html = chart.to_html().replace("EazyViz.init(window.EAZY_PAGE);",
                               HEAT_STRIP_JS + "\nEazyViz.init(window.EAZY_PAGE);")
with open("examples/output/heat_strip.html", "w", encoding="utf-8") as f:
    f.write(html)
print(chart.spec["type"], chart.data_ref, chart.data["n"], "%.2f MB" % (len(html) / 1024 / 1024))
```

已验证：页面无 JS 报错，`EazyViz.charts[0].ec.getOption().series[0].data.length === 36`（12 个月 × 3 渠道），`xAxis.data.length === 12`，`yAxis.data.length === 3`。

## 6. HTML 类图表（`htmlBuilders`）

返回字符串而不是 ECharts option，适合 KPI、进度条、明细表这类 DOM 卡片。要点：

- 注册 `EazyViz.htmlBuilders.heat_strip = function (spec, data, state, theme) { return '<div>…</div>'; }`；
- 所有用户数据必须 `U.esc()`，否则列名/类目里的尖括号会破坏页面；
- 在 `render.py` 的 `HTML_TYPES` 里加上类型名，卡片高度/滚动样式才会按 HTML 组件处理；需要自适应高度的加到 `AUTO_HEIGHT_TYPES`；
- HTML 类图表**不能作为联动源**（`onChartClick` 只挂在 ECharts 实例上），也不参与下钻。

## 7. 测试

`tests/test_eazy.py` 是纯 Python 冒烟测试，加一个函数并 `check("heat_strip", t_heat_strip)`：

```python
import eazy_data_viz as edv

df = edv.sample_df(rows=600)
chart = edv.bar(df, x="大区", y="销售额")
assert chart.spec["type"] == "bar" and chart.data_ref.startswith("d")
assert chart.data["n"] == 600
assert "eazy-chart" in chart.to_html()
```

`tests/js_test.py` 用真实生成的页面 + 无头 Chrome 断言：在页面里安排一张新图，然后检查

| 断言 | 期望 |
| --- | --- |
| `EazyViz.charts.length` | 与页面图表数一致 |
| `EazyViz.charts[i].ec.getOption().series.length` | 新图 series 数量正确 |
| `document.getElementById('eazy-js-error')` | `null` |
| `EazyViz.core.buildOption(spec, data, state, theme)` | 不抛异常且返回对象 |

## 8. 文档与 gallery

- `docs/api/heat_strip.md`：按现有 API 文档模板写，`tools/check_docs.py` 会校验 `## 函数签名`、`## 参数总览`、`## 参数详解`、`## 完整示例` 四节齐全、每个参数都有 `### \`参数\``，且不少于 200 行。
- `examples/charts/heat_strip.py`：仿照现有示例，跑通后把 HTML 写到 `examples/output/` 并 `assert os.path.getsize(path) > 100_000`。
- `tools/gen_ai_doc.py`：从函数签名自动生成 `docs/eazy_catalog.json` 和 `docs/AI_GUIDE.md` 中的分组条目；新函数要加进 `GROUPS` 列表，然后重跑脚本。

```bash
python tools/sync_doc_signatures.py  # 用真实签名回填各页「函数签名」块（--check 只检查）
python tools/gen_ai_doc.py           # 刷新 catalog 与 AI 指南
python tools/check_docs.py           # 检查 API 文档完整性
python tools/build_gallery.py        # 重新生成 gallery.html
```

- `tools/sync_doc_signatures.py`：改过函数参数后先跑它，避免文档里的默认值和实际签名
  对不上（例如 `max_rows` 已从 20 万改成 200 万）。`--check` 不写文件，只列出不一致的
  页面并以退出码 1 结束，可以直接挂到 CI。

- `tools/build_gallery.py`：在 `main()` 的对应分区里加一行，`_sec()` 负责分区标题，重跑后根目录 `gallery.html` 与包内 `gallery.html` 都会更新。

```python
from eazy_data_viz import charts_extra as X

sections = []
s = "⑨ 自定义图表"
sections.append(X.waterfall(edv.sample_df(), x="产品", y="销售额", total=True))
print(len(sections), s)
```

## 9. ES5 与常见坑

| 约束 | 原因 |
| --- | --- |
| 只用 `var` / `function`，不用箭头函数、`let/const`、模板字符串 | 资产要兼容旧浏览器，测试也不做转译 |
| 不要 `console.log` | 会污染用户页面控制台 |
| 聚合只在前端做，Python 只做列校验 | 联动、下钻时不能回调 Python，见 [EXTRA_CHARTS.md](../EXTRA_CHARTS.md) |
| 所有从数据里来的字符串都 `U.esc()` | 防 XSS、防样式串台 |
| 返回 option 前先处理空行 | `if (!rows.length) return U.emptyOption(theme);` |
| 类目顺序跟随数据首现顺序 | 需要排序时用 `spec.sort` + `U.catRanker(data, dim)` |
| `dataRef` 自动生成，不要手写 | 同名不同内容会串数据 |
| 新类型必须先进 `_NUMERIC_ROLE_KEYS` | 否则数值被当类目，图上全是字符串 |

## 10. 相关阅读

- [EXTRA_CHARTS.md](../EXTRA_CHARTS.md) —— 每个扩展图的 Python⇄JS 契约与已知限制
- [10 · 选图](10-chart-selection.md) —— 先确认现有图表不够用
- [13 · 性能与体积](13-performance.md) —— 自定义图也要遵守前端聚合的代价
