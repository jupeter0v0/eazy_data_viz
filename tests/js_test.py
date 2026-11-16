# -*- coding: utf-8 -*-
"""前端（eazy.js）逻辑 + 交互回归测试。

做法：用真实的 eazy_data_viz 页面（echarts + eazy.js 内联），在页面末尾注入断言脚本，
再用 headless Chrome 跑一遍并 dump-dom，读取结果节点。

运行：python tests/js_test.py
"""
import io
import json
import os
import tempfile
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import eazy_data_viz  # noqa: E402

TMP = os.path.join(tempfile.gettempdir(), "eazy_data_viz_js_test")
CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe"

TEST_JS = r"""
<script>
(function () {
  var RES = [];
  var P = 0;
  function ok(name, cond, extra) {
    if (cond) { P += 1; } else { RES.push(name + (extra ? ('[' + extra + ']') : '')); }
  }
  function core() { return EazyViz.core; }
  function rows(id) { return (EazyViz.dataStore[id] || {}).rows || []; }
  function chart(i) { return EazyViz.charts[i]; }

  var c0 = chart(0), c1 = chart(1), c2 = chart(2);
  var ck = chart(13), cp = chart(14);
  var core0 = core();
  try {

  // ---------------- 纯逻辑 ----------------
  ok('charts-count', EazyViz.charts.length === 15, EazyViz.charts.length);
  ok('dataStore', Object.keys(EazyViz.dataStore).length >= 1);
  ok('fmt-compact', core0.fmtValue(12345678, 'compact') === '1235万', core0.fmtValue(12345678, 'compact'));
  ok('fmt-percent', core0.fmtValue(12.5, 'percent') === '12.5%', core0.fmtValue(12.5, 'percent'));
  ok('fmt-thousands', core0.fmtValue(1234567, 'thousands') === '1,234,567', core0.fmtValue(1234567, 'thousands'));
  ok('fmt-null', core0.fmtValue(null) === '-', core0.fmtValue(null));
  ok('quantile', Math.abs(core0.quantile([1, 2, 3, 4], 0.5) - 2.5) < 1e-9, core0.quantile([1, 2, 3, 4], 0.5));
  ok('median', core0.median([1, 2, 3, 4, 100]) === 3, core0.median([1, 2, 3, 4, 100]));

  var r0 = core0.rowsOf(c0.data);
  ok('rows-nonempty', r0.length > 0, r0.length);
  var spec0 = c0.spec;
  var g = core0.groupBy(r0, [spec0.roles.x], spec0.roles.y, 'sum');
  ok('groupBy', g.length >= 2 && g[0].key && typeof g[0].value === 'number', JSON.stringify(g[0]));

  // 联动过滤
  c0.state.filters = {};
  c0.state.filters[spec0.roles.x] = g[0].key;
  var fr = core0.filteredRows(c0.spec, c0.data, c0.state);
  ok('filteredRows', fr.length > 0 && fr.length < r0.length, fr.length + '/' + r0.length);
  ok('currentXDim', core0.currentXDim(c0.spec, c0.state) === spec0.roles.x, core0.currentXDim(c0));
  c0.state.filters = {};

  // 每张图都能 buildOption 且 series 非空
  var types = [];
  EazyViz.charts.forEach(function (c) {
    types.push(c.spec.type);
    if (c.spec.type === 'kpi') {
      ok('kpi-html-' + c.index, /总销售额|平均|KPI 进阶/.test(c.el.innerHTML), c.el.innerHTML.slice(0, 30));
      return;
    }
    var opt = core0.buildOption(c.spec, c.data, c.state, c.theme);
    ok('option-' + c.spec.type, opt && opt.series && opt.series.length >= 1, c.spec.type);
  });
  ok('types', types.indexOf('bar') >= 0 && types.indexOf('treemap') >= 0 && types.indexOf('gauge') >= 0);

  } catch (e) { RES.push('SETUP-EXC:' + (e && e.message)); }

  // ---------------- 交互：下钻 / 返回 ----------------
  // 直接驱动 EazyViz 的点击处理器（等价于用户点击某个类目）：
  // 真实 ECharts click 回调参数形如 {componentType:'series', name:..., seriesIndex:0, value:...}
  function clickCat(c, cat, val) {
    ok('ec-ready-' + c.index, !!(c && c.ec), c && c.spec && c.spec.type);
    core0.onChartClick(c, { componentType: 'series', name: cat, seriesIndex: 0, value: val });
    return true;
  }

  var steps = [];
  var drillCat = null, drillVal = null;
  steps.push(function () {
    var gd = core0.groupBy(core0.rowsOf(c0.data), [c0.spec.roles.x], c0.spec.roles.y, c0.spec.agg || 'sum');
    drillCat = gd[0].key; drillVal = gd[0].value;
    ok('drill-cat', !!drillCat, String(drillCat));
    clickCat(c0, drillCat, drillVal);
  });
  steps.push(function () {
    ok('drill-state', c0.state.drill.length === 1, JSON.stringify(c0.state.drill));
    var crumb = document.querySelector('[data-eazy-toolbar="0"] .eazy-crumb');
    ok('drill-crumb', !!crumb && /›/.test(crumb.textContent) && crumb.textContent.replace(/\s/g, '').length > 1, crumb && crumb.textContent);
    ok('drill-back-btn', !!document.querySelector('[data-back="0"]'));
    var back = document.querySelector('[data-back="0"]');
    if (back) back.click();
  });
  steps.push(function () {
    ok('drill-reset', c0.state.drill.length === 0, c0.state.drill.length);
  });

  // ---------------- 交互：联动 ----------------
  var linkSpec = c1.spec;
  steps.push(function () {
    var g1 = core0.groupBy(core0.rowsOf(c1.data), [linkSpec.roles.x], linkSpec.roles.y, 'sum');
    linkSpec._testCat = g1[0].key; linkSpec._testVal = g1[0].value;
    ok('link-cat', !!linkSpec._testCat, String(linkSpec._testCat));
    clickCat(c1, g1[0].key, g1[0].value);
  });
  steps.push(function () {
    ok('link-set', Object.keys(EazyViz.links).length >= 1, JSON.stringify(EazyViz.links));
    var bar = document.getElementById('eazy-filters');
    ok('link-chips', bar && bar.style.display !== 'none' && bar.textContent.length > 4, bar && bar.textContent.slice(0, 40));
    clickCat(c1, linkSpec._testCat, linkSpec._testVal);  // 再点一次 = 取消
  });
  steps.push(function () {
    ok('link-cleared', Object.keys(EazyViz.links).length === 0, JSON.stringify(EazyViz.links));
  });

  // ---------------- KPI 卡片 ----------------
  steps.push(function () {
    ok('kpi-value', ck.el.querySelectorAll('.eazy-kpi-value').length === 1);
    ok('kpi-badge', /目标/.test(ck.el.textContent));
    ok('kpi-spark', !!ck.el.querySelector('.eazy-kpi-sparkwrap svg'));
    ok('kpi-progress', !!ck.el.querySelector('.eazy-kpi-progress'));
    ok('kpi-hint', /联动组/.test(ck.el.textContent));
    ok('kpi-title-clean', !ck.spec.title, String(ck.spec.title));
  });
  var kpiText0 = '';
  steps.push(function () {
    kpiText0 = ck.el.textContent.replace(/\s+/g, '');
    var g1 = core0.groupBy(core0.rowsOf(c1.data), [c1.spec.roles.x], c1.spec.roles.y, 'sum');
    clickCat(c1, g1[0].key, g1[0].value);
  });
  steps.push(function () {
    var now = ck.el.textContent.replace(/\s+/g, '');
    ok('kpi-rerender-on-link', now !== kpiText0, now.slice(0, 40));
    clickCat(c1, Object.keys(EazyViz.links).length ? c1.spec._testCat : c1.spec._testCat,
             c1.spec._testVal);
  });

  // ---------------- 配色库 ----------------
  // ---------------- 卡片代码面板 ----------------
  steps.push(function () {
    var btn = document.querySelector('[data-eazy-code="0"]');
    var box = document.querySelector('[data-eazy-codebox="0"]');
    ok('code-btn', !!btn, btn && btn.textContent);
    ok('code-hidden', !!box && !box.classList.contains('is-open'));
    var text = box ? (box.querySelector('code') || {}).textContent || '' : '';
    ok('code-text', /eazy_data_viz\.[a-z_]+\(df/.test(text), text.slice(0, 48));
    if (btn) btn.click();
    ok('code-open', !!box && box.classList.contains('is-open'));
    if (btn) btn.click();
    ok('code-close', !!box && !box.classList.contains('is-open'));
  });

  steps.push(function () {
    ok('palette-count', Object.keys(core0.PALETTES).length >= 7,
       Object.keys(core0.PALETTES).join(','));
    var t = core0.util.themeFor('light', 'tableau');
    ok('palette-themeFor', t.palette[0] === '#4e79a7', t.palette[0]);
    var opt = core0.buildOption(cp.spec, cp.data, cp.state,
                               core0.util.themeFor('light', cp.spec.palette));
    ok('palette-option-color', !!(opt.color && opt.color[0] === '#4e79a7'),
       opt.color && opt.color[0]);
    ok('palette-setfunc', typeof core0.setPalette === 'function');
    ok('palette-switch', (function () {
      core0.setPalette('morandi');
      var t2 = EazyViz.charts[0].theme;
      var okk = t2.palette[0] === '#8fa3b0';
      core0.setPalette('google');
      return okk;
    })());
  });

  var i = 0;
  function next() {
    if (i < steps.length) {
      try { steps[i](); } catch (e) { RES.push('EXC#' + i + ':' + (e && e.message)); }
      i += 1;
      setTimeout(next, 150);
      return;
    }
    var out = document.createElement('div');
    out.id = 'js-test-result';
    out.setAttribute('data-pass', String(P));
    out.setAttribute('data-fail', String(RES.length));
    out.textContent = RES.join('|');
    document.body.appendChild(out);
    document.title = RES.length ? ('JSFAIL(' + RES.length + ') ' + RES.slice(0, 6).join('|')) : ('JSOK ' + P);
  }
  setTimeout(next, 400);

  window.addEventListener('error', function (e) { RES.push('JSERR:' + e.message); });
})();
</script>
"""


def build_page():
    df = eazy_data_viz.sample_df(rows=800, seed=11)
    charts = [
        eazy_data_viz.bar(df, x="大区", y="销售额", drill=["大区", "产品"], title="下钻：大区→产品"),
        eazy_data_viz.bar(df, x="产品", y="销售额", link="g1", title="联动：产品"),
        eazy_data_viz.line(df, x="月份", y="销售额", link="g1", title="联动：趋势"),
        eazy_data_viz.pie(df, names="渠道", values="销售额", title="饼图"),
        eazy_data_viz.scatter(df, x="订单数", y="销售额", size="客户数", title="散点"),
        eazy_data_viz.histogram(df, column="销售额", bins=16, title="直方图"),
        eazy_data_viz.heatmap(df, x="月份", y="大区", value="销售额", title="热力图"),
        eazy_data_viz.box(df, x="渠道", y="利润", title="箱线图"),
        eazy_data_viz.funnel(df, names="渠道", values="订单数", title="漏斗"),
        eazy_data_viz.treemap(df, path=["大区", "产品"], value="销售额", title="矩形树图"),
        eazy_data_viz.gauge(73.5, label="目标完成率", unit="%", title="仪表盘"),
        eazy_data_viz.kpi(df, value="销售额", agg="sum", label="总销售额", title="KPI"),
        eazy_data_viz.combo(df, x="月份", bar="销售额", line="利润", title="组合图"),
        eazy_data_viz.kpi(df, value="销售额", agg="sum", label="KPI 进阶", delta=0.128,
                 delta_label="同比", target=2000000, spark="销售额", spark_x="月份",
                 hint="联动组演示", link="g1"),
        eazy_data_viz.bar(df, x="月份", y="销售额", color="产品", title="配色表格图").palette("tableau"),
    ]
    for _c in charts[:3]:
        _c.spec["code"] = ('eazy_data_viz.%s(%s)' % (
            _c.spec["type"], "df, x=%r" % _c.spec["roles"].get("x")))
    page = eazy_data_viz.dashboard(charts, cols=3, title="eazy_data_viz 前端测试")
    return page.to_html()


def main():
    os.makedirs(TMP, exist_ok=True)
    html = build_page()
    assert "</body>" in html
    head, sep, tail = html.rpartition("</body>")
    html = head + TEST_JS + "\n" + sep + tail
    path = os.path.join(TMP, "js_test.html")
    io.open(path, "w", encoding="utf-8").write(html)

    cmd = [
        CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--hide-scrollbars", "--virtual-time-budget=9000",
        "--window-size=1500,1400", "--dump-dom",
        "--allow-file-access-from-files",
        "file:///" + path.replace("\\", "/"),
    ]
    cp = subprocess.run(cmd, capture_output=True)
    dom = cp.stdout.decode("utf-8", "replace")
    if not dom:
        print("没有拿到 DOM，Chrome stderr:\n", cp.stderr.decode("utf-8", "replace")[:2000])
        return 1
    m = re.search(r'<div id="js-test-result" data-pass="(\d+)" data-fail="(\d+)">([^<]*)</div>', dom)
    if not m:
        title = re.search(r"<title>([^<]*)</title>", dom)
        print("未找到测试结果节点；title =", title.group(1) if title else "(none)")
        return 2
    passed, failed, detail = int(m.group(1)), int(m.group(2)), m.group(3)
    print("JS PASS %d, FAIL %d" % (passed, failed))
    if failed:
        for item in detail.split("|"):
            print("  FAIL:", item)
        return 1
    print("ALL JS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
