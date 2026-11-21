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
  var ck = chart(13), cp = chart(14), cd = chart(18);
  var core0 = core();
  try {

  // ---------------- 纯逻辑 ----------------
  ok('charts-count', EazyViz.charts.length === 22, EazyViz.charts.length);
  ok('dataStore', Object.keys(EazyViz.dataStore).length >= 1);
  ok('fmt-compact', core0.fmtValue(12345678, 'compact') === '1235万', core0.fmtValue(12345678, 'compact'));
  ok('fmt-percent', core0.fmtValue(12.5, 'percent') === '12.5%', core0.fmtValue(12.5, 'percent'));
  ok('fmt-thousands', core0.fmtValue(1234567, 'thousands') === '1,234,567', core0.fmtValue(1234567, 'thousands'));
  ok('fmt-null', core0.fmtValue(null) === '-', core0.fmtValue(null));
  ok('quantile', Math.abs(core0.quantile([1, 2, 3, 4], 0.5) - 2.5) < 1e-9, core0.quantile([1, 2, 3, 4], 0.5));
  ok('median', core0.median([1, 2, 3, 4, 100]) === 3, core0.median([1, 2, 3, 4, 100]));

  // ---------------- 中文数字：自动缩略单位 ----------------
  var U = core0.util;
  var fv = U.fmtValue;
  ok('fmt-wan-1', fv(10000) === '1万', fv(10000));
  ok('fmt-wan-12.3', fv(123456) === '12.3万', fv(123456));
  ok('fmt-wan-1235', fv(12345678) === '1235万', fv(12345678));
  ok('fmt-yi', fv(1.5e8) === '1.5亿', fv(1.5e8));
  ok('fmt-wan-neg', fv(-123456) === '-12.3万', fv(-123456));
  ok('fmt-zero', fv(0) === '0', fv(0));
  ok('fmt-under-wan', fv(9999) === '9,999', fv(9999));

  // ---------------- 中文数字：显式单位 ----------------
  ok('unit-baiwan', fv(2500000, null, { unit: '百万' }) === '2.5百万', fv(2500000, null, { unit: '百万' }));
  ok('unit-scale-num', fv(2500000, null, { unit: 1e6 }) === '2.5百万', fv(2500000, null, { unit: 1e6 }));
  ok('unit-wan-2dp', fv(12345678, null, { unit: '万' }) === '1234.57万', fv(12345678, null, { unit: '万' }));
  ok('unit-qian', fv(1234, null, { unit: '千' }) === '1.23千', fv(1234, null, { unit: '千' }));
  ok('unit-percent-wins', fv(12.5, 'percent', { unit: '万' }) === '12.5%', fv(12.5, 'percent', { unit: '万' }));
  ok('unit-thousands-wins', fv(12345678, 'thousands', { unit: '万' }) === '12,345,678', fv(12345678, 'thousands', { unit: '万' }));
  ok('unit-currency-wins', fv(1234.5, 'currency', { unit: '万' }) === '¥1,234.5', fv(1234.5, 'currency', { unit: '万' }));
  ok('unit-raw-wins', fv(123456, 'raw', { unit: '万' }) === '123456', fv(123456, 'raw', { unit: '万' }));
  ok('unit-table-col', fv(12345678, 'thousands', { unit: '万', type: 'table' }) === '1234.57万', fv(12345678, 'thousands', { unit: '万', type: 'table' }));
  ok('unit-text-suffix', fv(12345, 'thousands', { unit: ' 单' }) === '12,345 单', fv(12345, 'thousands', { unit: ' 单' }));
  var khtml = core0.kpiHTML({ type: 'kpi', value: 2500000, fmt: 'compact', unit: '万', label: 'KPI' },
                            { cols: [], rows: [] }, null, core0.THEME.light);
  ok('kpi-unit', khtml.indexOf('250万') >= 0, khtml.slice(0, 120));

  // ---------------- 中文日期类目轴 ----------------
  function catAxis(cats, spec) {
    return U.makeCategoryAxis(spec || {}, cats, core0.THEME.light);
  }
  var ax1 = catAxis(['2024-03-01', '2024-03-02', '2024-03-03']);
  ok('axis-day-same-year', ax1.axisLabel.formatter('2024-03-01') === '3月1日', ax1.axisLabel.formatter('2024-03-01'));
  ok('axis-day-raw-data', ax1.data[0] === '2024-03-01', ax1.data[0]);
  var ax2 = catAxis(['2023-12-31', '2024-01-01']);
  ok('axis-day-cross-year', ax2.axisLabel.formatter('2024-01-01') === '2024年1月1日', ax2.axisLabel.formatter('2024-01-01'));
  var ax3 = catAxis(['2024-03', '2024-04']);
  ok('axis-month-same-year', ax3.axisLabel.formatter('2024-03') === '3月', ax3.axisLabel.formatter('2024-03'));
  var ax4 = catAxis(['2023-11', '2024-01']);
  ok('axis-month-cross-year', ax4.axisLabel.formatter('2024-01') === '2024年1月', ax4.axisLabel.formatter('2024-01'));
  var ax5 = catAxis(['2024-03-01 09:30', '2024-03-01 10:30']);
  ok('axis-datetime', ax5.axisLabel.formatter('2024-03-01 09:30') === '3月1日 09:30', ax5.axisLabel.formatter('2024-03-01 09:30'));
  var ax6 = catAxis(['2024/03/01', '2024/03/02']);
  ok('axis-slash-date', ax6.axisLabel.formatter('2024/03/01') === '3月1日', ax6.axisLabel.formatter('2024/03/01'));
  var ax7 = catAxis(['1月', '2月']);
  ok('axis-plain-month-keep', ax7.axisLabel.formatter('1月') === '1月', ax7.axisLabel.formatter('1月'));
  var denseCats = [];
  for (var dc = 1; dc <= 40; dc++) {
    denseCats.push('2024-05-' + (dc < 10 ? '0' : '') + dc);
  }
  var ax8 = catAxis(denseCats);
  ok('axis-dense-interval', ax8.axisLabel.interval >= 1, ax8.axisLabel.interval);
  ok('axis-dense-label', ax8.axisLabel.formatter('2024-05-02') === '5月2日', ax8.axisLabel.formatter('2024-05-02'));
  var ax9 = catAxis([1000, 2000], { unit: '万' });
  ok('axis-cat-unit', ax9.axisLabel.formatter(2000) === '0.2万', ax9.axisLabel.formatter(2000));
  var va = U.makeValueAxis({ unit: '亿' }, core0.THEME.light, null);
  ok('axis-value-unit', va.axisLabel.formatter(150000000) === '1.5亿', va.axisLabel.formatter(150000000));

  // tooltip 表头保留原始完整日期，数值按单位换算
  var tipHtml = U.axisTooltip({ type: 'line' }, core0.THEME.light, false).formatter([
    { axisValue: '2024-03-01', axisValueLabel: '3月1日', name: '2024-03-01',
      seriesName: '销售额', marker: '', value: 123456 }]);
  ok('tooltip-head-raw-date', tipHtml.indexOf('2024-03-01') >= 0, tipHtml.slice(0, 90));
  var tipUnit = U.axisTooltip({ type: 'line', unit: '万' }, core0.THEME.light, false).formatter([
    { axisValue: '3月', name: '3月', seriesName: 'A', marker: '', value: 123000 }]);
  ok('tooltip-value-unit', tipUnit.indexOf('12.3万') >= 0, tipUnit.slice(0, 90));

  var r0 = core0.rowsOf(c0.data);
  ok('rows-nonempty', r0.length > 0, r0.length);
  var spec0 = c0.spec;
  var g = core0.groupBy(r0, [spec0.roles.x], spec0.roles.y, 'sum');
  ok('groupBy', g.length >= 2 && g[0].key && typeof g[0].value === 'number', JSON.stringify(g[0]));

  // ---------------- 地图 ----------------
  var cm = chart(15), cb = chart(16), cf = chart(17);
  ok('maps-payload', !!(window.EAZY_MAPS && window.EAZY_MAPS.china),
     Object.keys(window.EAZY_MAPS || {}).join(','));
  ok('cities-payload', !!(window.EAZY_CITIES && window.EAZY_CITIES['广州市']),
     !!window.EAZY_CITIES);
  try {
    var om = cm.ec.getOption();
    ok('geo_map-series', om.series && om.series.length === 1 && om.series[0].type === 'map',
       om.series && om.series[0] && om.series[0].type);
    ok('geo_map-data', (om.series[0].data || []).length >= 2, (om.series[0].data || []).length);
    ok('geo_map-visualmap', !!(om.visualMap && om.visualMap.length));
  } catch (e) { ok('geo_map-render', false, String(e).slice(0, 120)); }
  try {
    var ob = cb.ec.getOption();
    ok('map_bubble-geo', !!(ob.geo && ob.geo.length), (ob.geo || []).length);
    ok('map_bubble-points', (ob.series[0].data || []).length >= 3, (ob.series[0].data || []).length);
  } catch (e2) { ok('map_bubble-render', false, String(e2).slice(0, 120)); }
  try {
    var of = cf.ec.getOption();
    ok('map_flow-lines', (of.series[0].data || []).length >= 2, (of.series[0].data || []).length);
    ok('map_flow-geo', !!(of.geo && of.geo.length), (of.geo || []).length);
  } catch (e3) { ok('map_flow-render', false, String(e3).slice(0, 120)); }

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
    // 表格/瓦片等 HTML 图没有 ECharts option，单独断言它们渲染出了内容
    if (EazyViz.core.htmlBuilders[c.spec.type]) {
      var nChild = c.el.children.length;
      ok('html-' + c.spec.type + '-' + c.index, nChild > 0, nChild);
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

  // ---------------- 交互：重置下钻（含它自己发出的联动） ----------------
  steps.push(function () {
    var gd = core0.groupBy(core0.rowsOf(cd.data), [cd.spec.roles.x], cd.spec.roles.y, cd.spec.agg || 'sum');
    clickCat(cd, gd[0].key, gd[0].value);
  });
  steps.push(function () {
    ok('drill-link-both', cd.state.drill.length === 1 && !!(EazyViz.links || {})['g1'],
       cd.state.drill.length + '/' + JSON.stringify((EazyViz.links || {})['g1'] || null));
    var btn = document.querySelector('[data-eazy-reset-drill]');
    ok('drill-reset-btn', !!btn);
    if (btn) btn.click();
  });
  steps.push(function () {
    ok('drill-reset-all', cd.state.drill.length === 0, cd.state.drill.length);
    ok('drill-reset-own-link', !(EazyViz.links || {})['g1'], JSON.stringify(EazyViz.links || {}));
    ok('drill-reset-api', typeof EazyViz.resetDrill === 'function');
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

  // ---------------- 交互：表格 ↔ 图表 双向联动 ----------------
  var tbl = chart(19);
  var tblCat = null, tblVal = null;
  function cellOf(col) {
    var tds = tbl.el.querySelectorAll('td[data-eazy-cell]');
    for (var i = 0; i < tds.length; i++) {
      if (tds[i].getAttribute('data-eazy-cell') === col) return tds[i];
    }
    return null;
  }
  function fire(el) {
    el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
  }
  steps.push(function () {
    var cell = cellOf('大区');
    ok('tbl-cell-exists', !!cell);
    ok('tbl-cell-attr', !!cell && cell.getAttribute('data-eazy-val') === cell.textContent.trim(),
       cell && (cell.getAttribute('data-eazy-val') + '/' + cell.textContent.trim()));
    // 数值列不该变成可点的联动源
    var numCell = tbl.el.querySelector('td.eazy-bar-cell');
    ok('tbl-num-cell-not-link', !!numCell && !numCell.hasAttribute('data-eazy-cell'));
    if (cell) fire(cell);
  });
  steps.push(function () {
    var lk = (EazyViz.links || {}).g1 || null;
    ok('tbl-link-set', !!lk && lk.sourceId === tbl.spec.id && lk.dim === '大区', JSON.stringify(lk));
    ok('tbl-chart-filtered', !!c1.state.filters['大区'], JSON.stringify(c1.state.filters));
    ok('tbl-row-hit', tbl.el.querySelectorAll('tr.eazy-row-hit').length > 0,
       tbl.el.querySelectorAll('tr.eazy-row-hit').length);
    ok('tbl-keeps-rows', tbl.el.querySelectorAll('tbody tr').length === 5,
       tbl.el.querySelectorAll('tbody tr').length);
    var cell = cellOf('大区');
    if (cell) fire(cell);
  });
  steps.push(function () {
    ok('tbl-link-cleared', !(EazyViz.links || {}).g1, JSON.stringify(EazyViz.links || {}));
    ok('tbl-hit-cleared', tbl.el.querySelectorAll('tr.eazy-row-hit').length === 0);
    var gd = core0.groupBy(core0.rowsOf(c1.data), [c1.spec.roles.x], c1.spec.roles.y, 'sum');
    tblCat = gd[0].key; tblVal = gd[0].value;
    clickCat(c1, tblCat, tblVal);
  });
  steps.push(function () {
    ok('tbl-filtered-by-chart', !!tbl.state.filters['产品'], JSON.stringify(tbl.state.filters));
    ok('tbl-no-hit-when-target', tbl.el.querySelectorAll('tr.eazy-row-hit').length === 0,
       tbl.el.querySelectorAll('tr.eazy-row-hit').length);
    var tb = document.querySelector('[data-eazy-toolbar="19"]');
    ok('tbl-toolbar-hint', !!tb && /单元格/.test(tb.textContent), tb && tb.textContent.slice(0, 30));
    clickCat(c1, tblCat, tblVal);
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

  // ---------------- 词云形状（canvas 引擎） ----------------
  steps.push(function () {
    var cw = EazyViz.charts[20], cc = EazyViz.charts[21];
    ok('wc-shape-spec', !!(cw.spec.shape && cw.spec.shape.type === 'builtin'
       && cw.spec.shape.name === 'star'), JSON.stringify(cw.spec.shape));
    ok('wc-css-spec', !EazyViz.charts[21].spec.shape);
    var cv = document.querySelectorAll('canvas.eazy-wc-canvas');
    ok('wc-canvas-count', cv.length === 1, cv.length);
    var c0cv = cv[0];
    if (c0cv) {
      var boxes = c0cv.__wcBoxes || [];
      ok('wc-word-count', boxes.length >= 9, boxes.length);
      ok('wc-placed-attr', (c0cv.getAttribute('data-wc') || '').indexOf('/') > 0, c0cv.getAttribute('data-wc'));
      var overlap = false;
      for (var a = 0; a < boxes.length; a++) {
        for (var b = a + 1; b < boxes.length; b++) {
          var A = boxes[a], B = boxes[b];
          if (A.x < B.x + B.w && B.x < A.x + A.w && A.y < B.y + B.h && B.y < A.y + A.h) overlap = true;
        }
      }
      ok('wc-no-overlap', !overlap);
      var inside = 0;
      for (var q = 0; q < boxes.length; q++) {
        var bx = boxes[q];
        if (bx.x >= -2 && bx.y >= -2 && bx.x + bx.w <= c0cv.clientWidth + 2
            && bx.y + bx.h <= c0cv.clientHeight + 2) inside += 1;
      }
      ok('wc-inside', inside === boxes.length, inside + '/' + boxes.length);
    }
    var wcOld = (cc.el.querySelectorAll('.eazy-wc-word') || []).length;
    ok('wc-css-mode', wcOld >= 10 && !cc.el.querySelector('canvas.eazy-wc-canvas'), wcOld);
    ok('wc-hook', typeof EazyViz.htmlHooks === 'object' && typeof EazyViz.htmlHooks.wordcloud === 'function');
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
        eazy_data_viz.geo_map(df.groupby("省份", as_index=False)["销售额"].sum(),
                              region="省份", value="销售额", title="中国地图"),
        eazy_data_viz.map_bubble(df.groupby("城市", as_index=False)["销售额"].sum(),
                                 region="城市", value="销售额", title="城市气泡"),
        eazy_data_viz.map_flow(
            __import__("pandas").DataFrame({
                "出发城市": ["北京市", "上海市", "广州市", "成都市"],
                "到达城市": ["广州市", "成都市", "上海市", "北京市"],
                "件数": [320, 280, 260, 180]}),
            source="出发城市", target="到达城市", value="件数", title="城市飞线"),
        eazy_data_viz.bar(df, x="渠道", y="销售额", drill=["渠道", "产品"], link="g1",
                           title="下钻 + 联动"),
        eazy_data_viz.table(df, columns=["大区", "产品", "销售额"], limit=5, index=True,
                            total=True, bar="销售额", link="g1", height=360,
                            title="明细联动表"),
        eazy_data_viz.wordcloud(df, names="城市", values="销售额", top_n=20,
                                shape="star", height=300, title="词云形状"),
        eazy_data_viz.wordcloud(df, names="城市", values="销售额", top_n=20,
                                height=300, title="词云旧版"),
    ]
    # 中文单位：链式 unit() 只写进 spec，不影响页面里的图表数量
    _u1 = eazy_data_viz.bar(df, x="大区", y="销售额").unit("万")
    assert _u1.spec["unit"] == "万", _u1.spec.get("unit")
    _u2 = eazy_data_viz.line(df, x="月份", y="销售额").unit(1e6)
    assert _u2.spec["unit"] == 1000000, _u2.spec.get("unit")
    _u3 = eazy_data_viz.kpi(df, value="销售额", agg="sum").unit("百万")
    assert _u3.spec["unit"] == "百万", _u3.spec.get("unit")
    for _bad in (None, "", "十", 42, 2e3):
        try:
            eazy_data_viz.bar(df, x="大区", y="销售额").unit(_bad)
        except ValueError:
            pass
        else:
            raise AssertionError("unit(%r) 应当报错" % (_bad,))
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
        "--user-data-dir=" + os.path.join(tempfile.gettempdir(), "eazy_js_test_profile"),
        "--no-first-run", "--no-default-browser-check", "--disable-extensions",
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
