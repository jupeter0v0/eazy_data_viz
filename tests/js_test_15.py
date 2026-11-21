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
  ok('charts-count', EazyViz.charts.length === 25, EazyViz.charts.length);
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
    if (EazyViz.core.htmlBuilders[c.spec.type]) {
      return;  // HTML 类图表（table / tile / progress …）没有 ECharts option
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

  // ---------------- 1.5：多级桑基 / 旭日 / 汇总表 / 同比 / 联动方向 ----------------
  var cs = chart(18), cu = chart(19), ct = chart(20), cy = chart(21), co = chart(22), ci = chart(23);
  steps.push(function () {
    ok('sankey15-path', cs.spec.roles.path.length === 3, JSON.stringify(cs.spec.roles.path));
    var os = cs.ec.getOption();
    var sr = os.series[0];
    var nodes = sr.data || [];
    var names = nodes.map(function (n) { return n.name; });
    var uniq = names.filter(function (v, i, a) { return a.indexOf(v) === i; });
    ok('sankey15-nodes', nodes.length === uniq.length && nodes.length >= 3, nodes.length);
    ok('sankey15-level-prefix', /\u0001/.test(names[0] || ''), names[0]);
    ok('sankey15-links', (sr.links || []).length >= 3, (sr.links || []).length);
    ok('sankey15-nodeMaps', !!(EazyViz.nodeMaps && EazyViz.nodeMaps[cs.spec.id]));
    // 第二层节点点击 → 维度应为 path[1]
    var lv1 = names.filter(function (n) { return /^1\u0001/.test(n); })[0];
    ok('sankey15-layer1', !!lv1, lv1);
    var info = core0.nodeInfoOf(cs.spec, { componentType: 'series', dataType: 'node', name: lv1 });
    ok('sankey15-info', !!info && info.dim === '渠道' && !!info.value, JSON.stringify(info));
    core0.onChartClick(cs, { componentType: 'series', dataType: 'node', name: lv1, data: { name: lv1 } });
    var lk = EazyViz.links['g15'];
    ok('sankey15-click-dim', !!lk && lk.dim === '渠道', lk && lk.dim);
    ok('sankey15-self-unfiltered', !cs.state.filters['渠道'], JSON.stringify(cs.state.filters));
    ok('sunburst15-filtered', cu.state.filters['渠道'] === lk.value,
       cu.state.filters['渠道'] + '/' + lk.value);
    // 点边不应触发联动
    core0.onChartClick(cs, { componentType: 'series', dataType: 'edge', name: '' });
    ok('sankey15-edge-ignored', EazyViz.links['g15'].dim === '渠道', EazyViz.links['g15'].dim);
    // 旭日层级 → 维度
    var s0 = core0.nodeInfoOf(cu.spec, { treePathInfo: [{}, { name: '华东' }] });
    var s1 = core0.nodeInfoOf(cu.spec, { treePathInfo: [{}, {}, { name: '线上' }] });
    ok('sunburst15-dims', s0 && s0.dim === '大区' && s0.value === '华东'
       && s1 && s1.dim === '渠道' && s1.value === '线上',
       JSON.stringify([s0, s1]));
    // 点开一层后（nodeClick:rootToNode）treePathInfo 会变短，节点自带的 nodeDim 必须压过它
    var deep = core0.nodeInfoOf(cu.spec, {
      name: '线上', data: { nodeDim: '渠道', nodeLayer: 1, nodeValue: '线上' },
      treePathInfo: [{ name: '线上' }]
    });
    ok('sunburst15-nodeDim', deep && deep.dim === '渠道' && deep.value === '线上' && deep.layer === 1,
       JSON.stringify(deep));
    // 旭日标签：环内 + 重叠隐藏，且过小的节点不画 label
    var so = core0.buildOption(cu.spec, cu.data, { filters: {}, drill: [] });
    var sser = so.series && so.series[0] || {};
    ok('sunburst15-label-inside',
       sser.label && sser.label.position === 'inside' && sser.labelLayout && sser.labelLayout.hideOverlap === true,
       JSON.stringify([sser.label, sser.labelLayout]));
    ok('sunburst15-radius', String(sser.radius) === '12%,88%', JSON.stringify(sser.radius));
    var hidden = (function walk(nodes, n) {
      n = n || 0;
      for (var i = 0; i < (nodes || []).length; i++) {
        var nd = nodes[i];
        if (nd.label && nd.label.show === false) n += 1;
        if (nd.children) n = walk(nd.children, n);
      }
      return n;
    })(sser.data);
    ok('sunburst15-small-hidden', hidden > 0, 'hidden=' + hidden);
  });

  // 旭日点击：放大与联动要同时生效（重画后视图根落回所点的节点），重置联动再回根
  steps.push(function () {
    var rows = core0.rowsOf(cu.data);
    var top = String(rows[0]['大区']);
    cu.__zoomTop = top;
    core0.onChartClick(cu, {
      componentType: 'series', name: top,
      treePathInfo: [{ name: 'root' }, { name: top }],
      data: { name: top, nodeDim: '大区', nodeValue: top, nodeLayer: 0 }
    });
    ok('sunburst15-zoom-path', Array.isArray(cu.zoomPath) && cu.zoomPath[0] === top,
       JSON.stringify(cu.zoomPath));
  });

  steps.push(function () {
    var vr = cu.ec.getModel().getSeriesByIndex(0).getViewRoot();
    ok('sunburst15-zoom-applied', String(vr && vr.name) === cu.__zoomTop, String(vr && vr.name));
    EazyViz.core.clearAllLinks();
  });

  steps.push(function () {
    var vr2 = cu.ec.getModel().getSeriesByIndex(0).getViewRoot();
    ok('sunburst15-zoom-reset', String(vr2 && vr2.name) !== cu.__zoomTop, String(vr2 && vr2.name));
  });

  steps.push(function () {
    var theme = core0.util.themeFor('light', null);
    var clean = EazyViz.htmlBuilders['table'](ct.spec, ct.data, { filters: {}, drill: [] }, theme);
    ok('table15-header', /销售额/.test(clean) && /求和/.test(clean), clean.slice(0, 60));
    ok('table15-groups', /共 \d+ 组|汇总为 \d+ 组/.test(clean), (clean.match(/共 \d+ 组|汇总为 \d+ 组/) || [''])[0]);
    var filtered = EazyViz.htmlBuilders['table'](ct.spec, ct.data,
      { filters: { '大区': '华东' }, drill: [] }, theme);
    ok('table15-display-only', /华东/.test(filtered) && !/华北/.test(filtered), filtered.slice(0, 80));
    var rows = core0.rowsOf(ct.data), n0 = rows.length;
    EazyViz.htmlBuilders['table'](ct.spec, ct.data, { filters: { '大区': '华东' }, drill: [] }, theme);
    ok('table15-data-intact', core0.rowsOf(ct.data).length === n0 && n0 === ct.data.rows.length, n0);
    ok('table15-spec', ct.spec.groupby && ct.spec.groupby.agg === 'sum', JSON.stringify(ct.spec.groupby));
  });

  // 1.5.2：同比方向（系列名不是纯数字时按名字里的数字定本期）+ sort 传列名
  steps.push(function () {
    var core = core0;
    ok('yoy15-name-order', core.util.nameOrder('2026年') === 2026 &&
       core.util.nameOrder('第2季度') === 2, String(core.util.nameOrder('2026年')));
    var p1 = core.util.yoyPlan(['2025年', '2026年'], { '2025年': 900, '2026年': 100 });
    ok('yoy15-plan-name', p1.current === '2026年' && p1.base === '2025年', JSON.stringify(p1));
    var p2 = core.util.yoyPlan(['华东', '华南'], { '华东': 100, '华南': 900 });
    ok('yoy15-plan-total', p2.current === '华南', JSON.stringify(p2));

    // sortRank：Python 按「年-月」算好的类目顺序，前端照抄排序
    var sp = JSON.parse(JSON.stringify(cy.spec));
    sp.sort = '年-月';
    sp.sortRank = ['3月', '1月', '2月'];
    sp.roles = { x: '月份', y: '销售额' };
    sp.legend = false;
    sp.yoy = null;
    var opt2 = core.buildOption(sp, cy.data, { filters: {}, drill: [], legendSel: null },
                               core.util.themeFor('light', 'google'));
    var ax = (opt2.xAxis instanceof Array) ? opt2.xAxis[0] : opt2.xAxis;
    var cats = (ax && ax.data) || [];
    ok('yoy15-sort-rank', cats.join(',') === '3月,1月,2月', cats.join(','));
    var sp2 = JSON.parse(JSON.stringify(sp));
    sp2.sortRank = null;
    sp2.sort = 'desc';
    var opt3 = core.buildOption(sp2, cy.data, { filters: {}, drill: [], legendSel: null },
                                core.util.themeFor('light', 'google'));
    var ax3 = (opt3.xAxis instanceof Array) ? opt3.xAxis[0] : opt3.xAxis;
    var cats3 = (ax3 && ax3.data) || [];
    ok('yoy15-sort-desc', cats3.join(',') === '1月,2月,3月', cats3.join(','));
  });

  steps.push(function () {
    // 1.5.4: agg="unique" 去重计数
    var urows = [
      { '大区': '华东', '客户名称': 'A' },
      { '大区': '华东', '客户名称': 'A' },
      { '大区': '华东', '客户名称': 'B' },
      { '大区': '华东', '客户名称': null },
      { '大区': '华东', '客户名称': '' },
      { '大区': '华北', '客户名称': 'A' },
      { '大区': '华北', '客户名称': 'C' },
      { '大区': '华南', '客户名称': 'D' }
    ];
    var ug = core0.groupBy(urows, ['大区'], '客户名称', 'unique');
    var umap = {};
    ug.forEach(function (r) { umap[r.key] = r.value; });
    ok('unique15-basic', umap['华东'] === 2 && umap['华北'] === 2 && umap['华南'] === 1,
       JSON.stringify(umap));
    ok('unique15-cleanup', ug.every(function (r) { return r.uniq === undefined; }),
       JSON.stringify(ug[0]));
    var ugc = core0.groupBy(urows, ['大区'], '客户名称', 'count');
    ok('unique15-count-diff', ugc[0].value === 5, ugc[0].value);
    // 数值列去重
    var nrows = [{ k: 'x', v: 1 }, { k: 'x', v: 1 }, { k: 'x', v: 2 }, { k: 'x', v: null }];
    ok('unique15-number', core0.groupBy(nrows, ['k'], 'v', 'unique')[0].value === 2,
       core0.groupBy(nrows, ['k'], 'v', 'unique')[0].value);

    // 页面上的图：25 号是 agg=unique 的 bar（华东 2 / 华北 2 / 华南 1）
    var cu = chart(24);
    ok('unique15-spec', cu && cu.spec.agg === 'unique', cu && cu.spec.agg);
    var ou = cu.ec.getOption();
    var axu = (ou.xAxis instanceof Array) ? ou.xAxis[0] : ou.xAxis;
    var ucats = (axu && axu.data) || [];
    var uvals = {};
    ((ou.series || [])[0] || { data: [] }).data.forEach(function (d, i) {
      uvals[ucats[i]] = (d && d.value !== undefined) ? d.value : d;
    });
    ok('unique15-bars', Number(uvals['华东']) === 2 && Number(uvals['华北']) === 2
       && Number(uvals['华南']) === 1, JSON.stringify(uvals));
    ok('unique15-kinds', (cu.data.kinds || {})['客户名称'] !== 'num',
       (cu.data.kinds || {})['客户名称']);
  });

  steps.push(function () {
    var oy = cy.ec.getOption();
    var labeled = (oy.series || []).filter(function (s) {
      return (s.data || []).some(function (d) { return d && d.label && d.label.show; });
    });
    ok('yoy15-one-series', labeled.length === 1, labeled.length);
    var first = labeled.length ? (labeled[0].data.filter(function (d) { return d && d.label; })[0] || {}) : {};
    ok('yoy15-label', /^[+-]\d+(\.\d+)?%$/.test((first.label || {}).formatter || ''),
       (first.label || {}).formatter);
    ok('yoy15-spec', !!(cy.spec.yoy && cy.spec.yoy.dim === '年份'), JSON.stringify(cy.spec.yoy));
    // ECharts 的 getOption() 会把 tooltip 归一化成数组
    var tdef = (oy.tooltip instanceof Array) ? oy.tooltip[0] : oy.tooltip;
    var tf = tdef && tdef.formatter;
    var dbg = 'fmtType=' + typeof tf;
    var html = '';
    if (typeof tf === 'function') {
      try { html = tf([{ axisValue: '1月', name: '1月', seriesName: '2026', value: 130 }]); }
      catch (e) { dbg += ' throw=' + e.message; }
      dbg += ' html=' + String(html).slice(-200);
    }
    window.__yoyDebug = dbg;
    ok('yoy15-tooltip',
       /同比/.test(String(html)) && /\+30(\.0)?%/.test(String(html)), dbg);
  });

  steps.push(function () {
    ok('link15-modes', core0.linkMode(co.spec) === 'out' && core0.linkMode(ci.spec) === 'in'
       && core0.linkMode(chart(1).spec) === 'both',
       [core0.linkMode(co.spec), core0.linkMode(ci.spec), core0.linkMode(chart(1).spec)].join(','));
    ok('link15-can', core0.canSendLink(co.spec) && !core0.canRecvLink(co.spec)
       && !core0.canSendLink(ci.spec) && core0.canRecvLink(ci.spec));
    var to = document.querySelector('[data-eazy-toolbar="' + co.index + '"]');
    var ti = document.querySelector('[data-eazy-toolbar="' + ci.index + '"]');
    ok('link15-toolbar-out', !!to && /单向出/.test(to.textContent), to && to.textContent.slice(0, 40));
    ok('link15-toolbar-in', !!ti && /单向进/.test(ti.textContent), ti && ti.textContent.slice(0, 40));
    // 单向出点击：自己不过滤，单向进被过滤
    var g1 = core0.groupBy(core0.rowsOf(co.data), [co.spec.roles.x], co.spec.roles.y, 'sum');
    core0.onChartClick(co, { componentType: 'series', name: g1[0].key });
    ok('link15-out-sent', !!EazyViz.links['g16'] && EazyViz.links['g16'].sourceId === co.spec.id,
       JSON.stringify(EazyViz.links['g16'] || {}));
    ok('link15-out-self', !co.state.filters[co.spec.roles.x], JSON.stringify(co.state.filters));
    ok('link15-in-recv', ci.state.filters[ci.spec.roles.x] === g1[0].key,
       ci.state.filters[ci.spec.roles.x]);
    // 单向进点击：不发起
    core0.onChartClick(ci, { componentType: 'series', name: g1[0].key });
    ok('link15-in-no-send', EazyViz.links['g16'].sourceId === co.spec.id,
       EazyViz.links['g16'].sourceId);
    delete EazyViz.links['g15'];  // 清掉桑基组，避免影响后续
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
        # ---------------- 1.5 新增 ----------------
        eazy_data_viz.sankey(df, path=["大区", "渠道", "产品"], value="销售额",
                             link="g15", title="多级桑基"),
        eazy_data_viz.sunburst(df, path=["大区", "渠道", "产品"], value="销售额",
                               link="g15", title="旭日多级"),
        eazy_data_viz.table(df, groupby={"columns": ["大区"], "value": "销售额", "agg": "sum"},
                            title="汇总表"),
        eazy_data_viz.bar(
            __import__("pandas").DataFrame({
                "月份": ["1月", "1月", "2月", "2月", "3月", "3月"],
                "年份": ["2026", "2025", "2026", "2025", "2026", "2025"],
                "销售额": [130, 100, 90, 120, 96, 80]}),
            x="月份", y="销售额", color="年份", yoy=True, title="同比"),
        eazy_data_viz.bar(df, x="大区", y="销售额", link=("g16", "out"), title="单向出"),
        eazy_data_viz.bar(df, x="大区", y="销售额", link=("g16", "in"), title="单向进"),
        # 1.5.4：agg="unique" 去重计数（文本列）
        eazy_data_viz.bar(
            __import__("pandas").DataFrame({
                "大区": ["华东", "华东", "华东", "华北", "华北", "华南"],
                "客户名称": ["A", "A", "B", "A", "C", "D"]}),
            x="大区", y="客户名称", agg="unique", title="去重计数"),
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
        # 独立的临时 profile：避免和正在运行的 Chrome 抢用户目录导致拿不到 DOM
        "--user-data-dir=" + os.path.join(TMP, "profile"),
        "--no-first-run", "--no-default-browser-check", "--disable-extensions",
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
