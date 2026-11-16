/*! eazy_data_viz 扩展图表 A：dumbbell / pareto / slope / bump / radar / rose / parallel /
 *  pictorial / target / trend / quadrant / matrix / sparkline / ring_progress
 *
 * 契约见 docs/EXTRA_CHARTS.md 3.4–3.17；注册键 = Python 函数名。
 * 每个 builder 返回完整 ECharts option；数据一律用 U.filteredRows 现算（matrix/
 * sparkline/ring_progress 的数据由 Python 预计算，见各自注释）。
 * ES5 only：var + function，无箭头函数/模板字符串。
 */
(function () {
  'use strict';
  if (typeof window === 'undefined' || !window.EazyViz) return;

  var EazyViz = window.EazyViz, U = EazyViz.core.util;
  var B = EazyViz.extraBuilders, H = EazyViz.htmlBuilders;
  var SEP = U.SEP || '\u0001';

  // ====================================================================
  // 本文件共用小工具
  // ====================================================================
  function pc(theme, i) { return theme.palette[i % theme.palette.length]; }

  // 单维度聚合 → [{name, value}]（value 为 null 时按 0 处理）
  function recsOf(rows, xdim, ycol, how) {
    var gs = U.groupBy(rows, [xdim], ycol, how || 'sum');
    var out = [];
    for (var i = 0; i < gs.length; i++) {
      out.push({ name: gs[i].keys[0], value: gs[i].value === null ? 0 : gs[i].value });
    }
    return out;
  }

  // 统一排序：spec.sort = x / asc / desc / none，key 指定排序字段
  function sortRecs(recs, xdim, spec, data, key) {
    key = key || 'value';
    if (!recs.length) return recs;
    if (spec.sort === 'x') {
      var ranker = U.catRanker(data, xdim);
      recs.sort(function (a, b) {
        return ranker ? ranker(a.name, b.name) : U.compareCatX(a.name, b.name);
      });
    } else if (spec.sort === 'asc' || spec.sort === 'desc') {
      var dir = spec.sort === 'asc' ? 1 : -1;
      recs.sort(function (a, b) {
        var va = (a[key] === null || a[key] === undefined) ? 0 : a[key];
        var vb = (b[key] === null || b[key] === undefined) ? 0 : b[key];
        return dir * (va - vb);
      });
    }
    return recs;
  }

  // 类目轴（带轴名）
  function catAxisOf(spec, cats, theme, fallbackName) {
    var a = U.makeCategoryAxis(spec, cats, theme);
    return U.setAxisName(a, U.axisTitle(spec.xtitle, fallbackName), theme, true);
  }

  // 数值轴（带轴名，lim 默认 spec.ylim）
  function valAxisOf(spec, theme, fallbackName, lim) {
    var a = U.makeValueAxis(spec, theme, lim === undefined ? spec.ylim : lim);
    return U.setAxisName(a, U.axisTitle(spec.ytitle, fallbackName), theme, false);
  }

  function tipAxis(theme) {
    var t = U.tooltipBox(theme);
    t.trigger = 'axis';
    t.axisPointer = { type: 'shadow' };
    return t;
  }

  function tipItem(theme) {
    var t = U.tooltipBox(theme);
    t.trigger = 'item';
    return t;
  }

  function head(txt) {
    return '<div style="font-weight:600;margin-bottom:4px">' + U.esc(txt) + '</div>';
  }

  function row(k, v) {
    return '<div style="line-height:19px">' + U.esc(k) + '：<b>' + U.esc(v) + '</b></div>';
  }

  // 最小二乘拟合（spec.fit 缺失时的兜底），返回 {slope, intercept, r2}
  function linfit(pts) {
    var n = pts.length, sx = 0, sy = 0, sxx = 0, sxy = 0, i;
    if (n < 2) return null;
    for (i = 0; i < n; i++) { sx += pts[i].x; sy += pts[i].y; sxx += pts[i].x * pts[i].x; sxy += pts[i].x * pts[i].y; }
    var den = n * sxx - sx * sx;
    if (!den) return null;
    var slope = (n * sxy - sx * sy) / den;
    var intercept = (sy - slope * sx) / n;
    var my = sy / n, ssTot = 0, ssRes = 0;
    for (i = 0; i < n; i++) {
      var e = pts[i].y - (intercept + slope * pts[i].x);
      ssRes += e * e;
      ssTot += (pts[i].y - my) * (pts[i].y - my);
    }
    return { slope: slope, intercept: intercept, r2: ssTot ? (1 - ssRes / ssTot) : 0 };
  }

  // 由 size 列换算散点半径
  function sizeScaler(sMin, sMax) {
    return function (v) {
      var s = U.num(v);
      if (s === null) return 10;
      if (sMax === sMin) return 14;
      return 7 + 24 * Math.sqrt((s - sMin) / (sMax - sMin));
    };
  }

  // ====================================================================
  // 3.4 dumbbell 哑铃图：两期值 + 差值连接
  // ====================================================================
  B['dumbbell'] = function (spec, data, state, theme) {
    var roles = spec.roles || {};
    var rows = U.filteredRows(spec, data, state);
    var xdim = U.currentXDim(spec, state);
    var how = spec.agg || 'sum';
    if (!xdim || !rows.length || !roles.y || !roles.y2) return U.emptyOption(theme);

    var names = spec.seriesNames || [];
    var n1 = names[0] || roles.y, n2 = names[1] || roles.y2;

    var g1 = U.groupBy(rows, [xdim], roles.y, how);
    var g2 = U.groupBy(rows, [xdim], roles.y2, how);
    var map1 = {}, map2 = {}, recs = [], seen = {}, i, g, k;
    for (i = 0; i < g1.length; i++) {
      g = g1[i]; k = g.keys[0];
      map1[k] = g.value;
      if (!seen[k]) { seen[k] = 1; recs.push({ name: k, value1: null, value2: null }); }
    }
    for (i = 0; i < g2.length; i++) {
      g = g2[i]; k = g.keys[0];
      map2[k] = g.value;
      if (!seen[k]) { seen[k] = 1; recs.push({ name: k, value1: null, value2: null }); }
    }
    var list = [];
    for (i = 0; i < recs.length; i++) {
      var r = recs[i];
      if (map1[r.name] !== undefined) r.value1 = map1[r.name];
      if (map2[r.name] !== undefined) r.value2 = map2[r.name];
      if (r.value1 !== null || r.value2 !== null) list.push(r);
    }
    if (!list.length) return U.emptyOption(theme);
    recs = sortRecs(list, xdim, spec, data, 'value1');

    var cats = [], v1 = [], v2 = [], bases = [], diffs = [];
    for (i = 0; i < recs.length; i++) {
      var a = recs[i].value1 === null ? recs[i].value2 : recs[i].value1;
      var b = recs[i].value2 === null ? recs[i].value1 : recs[i].value2;
      if (a === null) a = 0;
      if (b === null) b = 0;
      cats.push(recs[i].name);
      v1.push(recs[i].value1);
      v2.push(recs[i].value2);
      bases.push(a);
      diffs.push(Math.abs(b - a));
    }

    function endData(vals) {
      var out = [];
      for (var j = 0; j < cats.length; j++) out.push({ name: cats[j], value: vals[j] });
      return out;
    }

    var tip = tipItem(theme);
    tip.formatter = function (p) {
      var idx = p.dataIndex;
      if (idx < 0 || idx >= recs.length) return '';
      var rr = recs[idx];
      var diff = (rr.value1 === null || rr.value2 === null) ? null : (rr.value2 - rr.value1);
      var rate = (rr.value1 && diff !== null) ? (diff / Math.abs(rr.value1) * 100) : null;
      var html = head(rr.name) + row(n1, U.fmtValue(rr.value1, spec.fmt)) + row(n2, U.fmtValue(rr.value2, spec.fmt));
      if (diff !== null) html += row('差值', U.fmtValue(diff, spec.fmt));
      if (rate !== null) html += row('变化率', (rate >= 0 ? '+' : '') + rate.toFixed(1) + '%');
      return html;
    };

    var lg = U.makeLegend(theme, state.legendSel, spec.legend !== false);
    lg.data = [n1, n2];
    return {
      grid: U.makeGrid(theme, { legend: spec.legend !== false }),
      legend: lg,
      toolbox: U.makeToolbox(theme),
      tooltip: tip,
      xAxis: catAxisOf(spec, cats, theme, roles.x),
      yAxis: valAxisOf(spec, theme, roles.y),
      series: [
        {
          name: 'base', type: 'bar', stack: 'd', silent: true, z: 1, barWidth: 3,
          itemStyle: { color: 'transparent' }, emphasis: { disabled: true },
          tooltip: { show: false }, data: bases
        },
        {
          name: 'diff', type: 'bar', stack: 'd', silent: true, z: 2,
          barWidth: 3, itemStyle: { color: theme.axis, borderRadius: 2 },
          emphasis: { disabled: true }, tooltip: { show: false }, data: diffs
        },
        {
          name: n1, type: 'scatter', z: 4, symbolSize: 9, data: endData(v1),
          itemStyle: { color: pc(theme, 0), borderColor: theme.bg, borderWidth: 2 },
          label: {
            show: !!spec.labels, position: 'top', color: theme.subtext, fontSize: 11,
            formatter: function (p) { return U.fmtValue(p.value, spec.fmt); }
          }
        },
        {
          name: n2, type: 'scatter', z: 4, symbolSize: 9, data: endData(v2),
          itemStyle: { color: pc(theme, 3), borderColor: theme.bg, borderWidth: 2 },
          label: {
            show: !!spec.labels, position: 'bottom', color: theme.subtext, fontSize: 11,
            formatter: function (p) { return U.fmtValue(p.value, spec.fmt); }
          }
        }
      ]
    };
  };

  // ====================================================================
  // 3.5 pareto 帕累托图：降序柱 + 累计占比折线（右轴 0~100%）
  // ====================================================================
  B['pareto'] = function (spec, data, state, theme) {
    var roles = spec.roles || {};
    var rows = U.filteredRows(spec, data, state);
    var xdim = U.currentXDim(spec, state);
    if (!xdim || !rows.length) return U.emptyOption(theme);

    var how = spec.agg || 'sum';
    var recs = recsOf(rows, xdim, roles.y, how);
    if (!recs.length) return U.emptyOption(theme);
    // 帕累托默认降序；sort='x' 时按类目顺序
    if (spec.sort === 'x') sortRecs(recs, xdim, spec, data);
    else if (spec.sort === 'asc') sortRecs(recs, xdim, spec, data, 'value');
    else recs.sort(function (a, b) { return b.value - a.value; });

    var cats = [], vals = [], cums = [], pcts = [], total = 0, i;
    for (i = 0; i < recs.length; i++) total += recs[i].value;
    var cum = 0;
    for (i = 0; i < recs.length; i++) {
      cats.push(recs[i].name);
      vals.push(recs[i].value);
      cum += recs[i].value;
      cums.push(cum);
      pcts.push(total ? cum / total * 100 : 0);
    }

    var tip = tipAxis(theme);
    tip.formatter = function (ps) {
      var idx = (ps && ps.length) ? ps[0].dataIndex : -1;
      if (idx < 0 || idx >= cats.length) return '';
      var cumText = (spec.cumFmt && spec.cumFmt !== 'percent')
        ? U.fmtValue(cums[idx], spec.cumFmt)
        : U.fmtValue(pcts[idx], 'percent');
      return head(cats[idx]) +
        row(U.axisTitle(spec.ytitle, roles.y), U.fmtValue(vals[idx], spec.fmt)) +
        row('累计', cumText);
    };

    var pctAxis = {
      type: 'value', min: 0, max: 100,
      axisLine: { show: false }, axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { color: theme.subtext, formatter: '{value}%' }
    };
    U.setAxisName(pctAxis, '累计占比', theme, false, 18);

    var barData = [];
    for (i = 0; i < cats.length; i++) barData.push({ name: cats[i], value: vals[i] });
    var lineData = [];
    for (i = 0; i < cats.length; i++) lineData.push({ name: cats[i], value: pcts[i] });

    return {
      grid: U.makeGrid(theme, { legend: spec.legend !== false, rightExtra: 48 }),
      legend: U.makeLegend(theme, state.legendSel, spec.legend !== false),
      toolbox: U.makeToolbox(theme),
      tooltip: tip,
      xAxis: catAxisOf(spec, cats, theme, roles.x),
      yAxis: [valAxisOf(spec, theme, roles.y), pctAxis],
      series: [
        {
          name: U.axisTitle(spec.ytitle, roles.y), type: 'bar', barMaxWidth: 34,
          itemStyle: { color: pc(theme, 0), borderRadius: [4, 4, 0, 0] }, data: barData,
          label: {
            show: !!spec.labels, position: 'top', color: theme.subtext, fontSize: 11,
            formatter: function (p) { return U.fmtValue(p.value, spec.fmt); }
          }
        },
        {
          name: '累计占比', type: 'line', yAxisIndex: 1, smooth: false, z: 4,
          symbol: 'circle', symbolSize: 7, data: lineData,
          lineStyle: { width: 2, color: pc(theme, 3) },
          itemStyle: { color: pc(theme, 3), borderColor: theme.bg, borderWidth: 1.5 }
        }
      ]
    };
  };

  // ====================================================================
  // 3.6 slope 斜率图：横轴两期，每个类目一条线
  // ====================================================================
  B['slope'] = function (spec, data, state, theme) {
    var roles = spec.roles || {};
    var rows = U.filteredRows(spec, data, state);
    var xdim = U.currentXDim(spec, state);
    var ycol = roles.y, cdim = roles.color;
    if (!xdim || !ycol || !rows.length) return U.emptyOption(theme);

    var arms = spec.arms || spec.seriesNames || [];
    if ((!arms || arms.length < 2) && cdim && U.hasCol(data, cdim)) {
      arms = [];
      var seenArm = {};
      for (var ri = 0; ri < rows.length; ri++) {
        var av = U.catName(rows[ri][cdim]);
        if (!seenArm[av]) { seenArm[av] = 1; arms.push(av); }
      }
    }
    if (!arms || arms.length < 2) return U.emptyOption(theme);
    arms = [arms[0], arms[1]];

    var how = spec.agg || 'sum';
    var groups = U.groupBy(rows, cdim ? [xdim, cdim] : [xdim], ycol, how);
    var startMap = {}, endMap = {}, catOrder = [], catSeen = {}, gi, g;
    for (gi = 0; gi < groups.length; gi++) {
      g = groups[gi];
      var cat = g.keys[0];
      if (!catSeen[cat]) { catSeen[cat] = 1; catOrder.push(cat); }
      if (!cdim || g.keys[1] === arms[0]) startMap[cat] = g.value;
      if (!cdim || g.keys[1] === arms[1]) endMap[cat] = g.value;
    }
    if (!catOrder.length) return U.emptyOption(theme);

    var recs = [];
    for (gi = 0; gi < catOrder.length; gi++) {
      recs.push({
        name: catOrder[gi],
        start: startMap[catOrder[gi]] === undefined ? null : startMap[catOrder[gi]],
        end: endMap[catOrder[gi]] === undefined ? null : endMap[catOrder[gi]]
      });
    }
    // desc/asc 按第二期值排序
    if (spec.sort === 'x') {
      var ranker = U.catRanker(data, xdim);
      recs.sort(function (a, b) { return ranker ? ranker(a.name, b.name) : U.compareCatX(a.name, b.name); });
    } else if (spec.sort === 'asc' || spec.sort === 'desc') {
      var dir = spec.sort === 'asc' ? 1 : -1;
      recs.sort(function (a, b) { return dir * ((a.end || 0) - (b.end || 0)); });
    }

    var cats = [], seriesData = [], series = [], i;
    for (i = 0; i < recs.length; i++) {
      cats.push(recs[i].name);
      seriesData.push([recs[i].start, recs[i].end]);
      series.push({
        name: recs[i].name, type: 'line', data: [
          { name: recs[i].name, value: recs[i].start },
          { name: recs[i].name, value: recs[i].end }
        ],
        symbol: 'circle', symbolSize: 7, lineStyle: { width: 2.2, color: pc(theme, i) },
        itemStyle: { color: pc(theme, i), borderColor: theme.bg, borderWidth: 1.5 },
        emphasis: { focus: 'series' },
        label: {
          show: !!spec.labels, position: 'top', color: theme.subtext, fontSize: 11,
          formatter: function (p) { return U.fmtValue(p.value, spec.fmt); }
        }
      });
    }

    var tip = tipItem(theme);
    tip.formatter = function (p) {
      var idx = p.seriesIndex;
      if (idx < 0 || idx >= seriesData.length) return '';
      var a = seriesData[idx][0], b = seriesData[idx][1];
      var rate = (a !== null && b !== null && a !== 0) ? ((b - a) / Math.abs(a) * 100) : null;
      var html = head(cats[idx]) + row(arms[0], U.fmtValue(a, spec.fmt)) + row(arms[1], U.fmtValue(b, spec.fmt));
      if (rate !== null) html += row('变化率', (rate >= 0 ? '+' : '') + rate.toFixed(1) + '%');
      return html;
    };

    var catAxis = U.makeCategoryAxis(spec, arms, theme);
    catAxis.boundaryGap = false;
    U.setAxisName(catAxis, U.axisTitle(spec.xtitle, cdim || ''), theme, true);

    // 斜率图每个类目是一条折线，类目多时图例会挤成一排，超过 6 个类目就隐藏图例
    var showLegend = spec.legend !== false && cats.length <= 6;
    var legend = U.makeLegend(theme, state.legendSel, showLegend);
    if (showLegend) { legend.top = 0; legend.left = 'center'; }
    return {
      grid: U.makeGrid(theme, { legend: showLegend, legendMany: cats.length > 4 }),
      legend: legend,
      toolbox: U.makeToolbox(theme),
      tooltip: tip,
      xAxis: catAxis,
      yAxis: valAxisOf(spec, theme, ycol),
      series: series
    };
  };

  // ====================================================================
  // 3.7 bump 排名变化图：y 轴为排名（逆向）
  // ====================================================================
  B['bump'] = function (spec, data, state, theme) {
    var roles = spec.roles || {};
    var rows = U.filteredRows(spec, data, state);
    var xdim = U.currentXDim(spec, state);
    var ycol = roles.y, gdim = roles.color;
    if (!xdim || !ycol || !gdim || !rows.length) return U.emptyOption(theme);

    var how = spec.agg || 'sum';
    var groups = U.groupBy(rows, [xdim, gdim], ycol, how);
    var times = [], tSeen = {}, gnames = [], gSeen = {}, score = {}, i, g, k;
    for (i = 0; i < groups.length; i++) {
      g = groups[i];
      var tv = g.keys[0], gv = g.keys[1];
      if (!tSeen[tv]) { tSeen[tv] = 1; times.push(tv); }
      if (!gSeen[gv]) { gSeen[gv] = 1; gnames.push(gv); }
      score[tv + SEP + gv] = g.value;
    }
    if (!times.length || !gnames.length) return U.emptyOption(theme);
    if (spec.sort === 'x') {
      var ranker = U.catRanker(data, xdim);
      times.sort(function (a, b) { return ranker ? ranker(a, b) : U.compareCatX(a, b); });
    }

    // 每个时间点内按值降序算出排名
    var rank = {}, ti, gj;
    for (ti = 0; ti < times.length; ti++) {
      var entries = [];
      for (gj = 0; gj < gnames.length; gj++) {
        var sv = score[times[ti] + SEP + gnames[gj]];
        if (sv !== null && sv !== undefined) entries.push({ name: gnames[gj], value: sv });
      }
      entries.sort(function (a, b) { return b.value - a.value; });
      for (gj = 0; gj < entries.length; gj++) rank[times[ti] + SEP + entries[gj].name] = gj + 1;
    }

    var series = [], si;
    for (si = 0; si < gnames.length; si++) {
      var name = gnames[si], pts = [];
      for (ti = 0; ti < times.length; ti++) {
        var rk = rank[times[ti] + SEP + name];
        var sv2 = score[times[ti] + SEP + name];
        pts.push({
          name: times[ti],
          value: rk === undefined ? null : rk,
          actual: (sv2 === undefined ? null : sv2)
        });
      }
      series.push({
        name: name, type: 'line', data: pts, connectNulls: false,
        symbol: 'circle', symbolSize: 8, smooth: true,
        lineStyle: { width: 2.4, color: pc(theme, si) },
        itemStyle: { color: pc(theme, si), borderColor: theme.bg, borderWidth: 1.5 },
        emphasis: { focus: 'series' },
        label: {
          show: !!spec.labels, position: 'top', color: theme.subtext, fontSize: 11,
          formatter: function (p) {
            var d = p.data;
            return (d && d.actual !== null && d.actual !== undefined) ? U.fmtValue(d.actual, spec.fmt) : '';
          }
        }
      });
    }

    var tip = tipItem(theme);
    tip.formatter = function (p) {
      var d = p.data || {};
      var html = head(d.name || p.name || '') + row('分组', p.seriesName);
      html += row(U.axisTitle(spec.ytitle, ycol), U.fmtValue(d.actual, spec.fmt));
      html += row('排名', d.value === null || d.value === undefined ? '-' : String(d.value));
      return html;
    };

    var valAxis = {
      type: 'value', inverse: true, min: 1, max: Math.max(2, gnames.length),
      axisLine: { show: false }, axisTick: { show: false },
      splitLine: { lineStyle: { color: theme.split, type: 'dashed' } },
      axisLabel: {
        color: theme.subtext,
        formatter: function (v) { return String(Math.round(v)); }
      }
    };
    U.setAxisName(valAxis, '排名', theme, false);

    var catAxis = U.makeCategoryAxis(spec, times, theme);
    catAxis.boundaryGap = false;
    U.setAxisName(catAxis, U.axisTitle(spec.xtitle, xdim), theme, true);

    return {
      grid: U.makeGrid(theme, { legend: spec.legend !== false }),
      legend: U.makeLegend(theme, state.legendSel, spec.legend !== false),
      toolbox: U.makeToolbox(theme),
      tooltip: tip,
      xAxis: catAxis,
      yAxis: valAxis,
      series: series
    };
  };

  // ====================================================================
  // 3.8 radar 雷达图：指标 = x 类目，每个 color 组一条雷达
  // ====================================================================
  B['radar'] = function (spec, data, state, theme) {
    var roles = spec.roles || {};
    var rows = U.filteredRows(spec, data, state);
    var xdim = U.currentXDim(spec, state);
    var ycol = roles.y, cdim = roles.color;
    var countMode = !ycol;
    if (!xdim || !rows.length) return U.emptyOption(theme);

    var mcol = countMode ? xdim : ycol;
    var how = countMode ? 'count' : (spec.agg || 'mean');
    var groups = U.groupBy(rows, cdim && U.hasCol(data, cdim) ? [xdim, cdim] : [xdim], mcol, how);
    var catOrder = [], cSeen = {}, serOrder = [], sSeen = {}, map = {}, totals = {}, i, g;
    for (i = 0; i < groups.length; i++) {
      g = groups[i];
      var cat = g.keys[0];
      var ser = cdim && U.hasCol(data, cdim) ? g.keys[1] : (countMode ? '记录数' : ycol);
      if (!cSeen[cat]) { cSeen[cat] = 1; catOrder.push(cat); totals[cat] = 0; }
      if (!sSeen[ser]) { sSeen[ser] = 1; serOrder.push(ser); }
      var v = g.value === null ? null : g.value;
      map[cat + SEP + ser] = v;
      if (v !== null) totals[cat] += v;
    }
    if (!catOrder.length) return U.emptyOption(theme);

    // 指标排序
    if (spec.sort === 'x') {
      var ranker = U.catRanker(data, xdim);
      catOrder.sort(function (a, b) { return ranker ? ranker(a, b) : U.compareCatX(a, b); });
    } else if (spec.sort === 'asc' || spec.sort === 'desc') {
      var dir = spec.sort === 'asc' ? 1 : -1;
      catOrder.sort(function (a, b) { return dir * (totals[a] - totals[b]); });
    }

    var indicators = [], ci, si;
    for (ci = 0; ci < catOrder.length; ci++) {
      var mx = U.num(spec.maxValue);
      if (mx === null) {
        var m = 0;
        for (si = 0; si < serOrder.length; si++) {
          var vv = map[catOrder[ci] + SEP + serOrder[si]];
          if (vv !== null && vv > m) m = vv;
        }
        mx = m > 0 ? Math.ceil(m * 1.1 * 10) / 10 : 1;
      }
      indicators.push({ name: U.truncate(catOrder[ci], 12), max: mx });
    }

    var series = [];
    for (si = 0; si < serOrder.length; si++) {
      var vals = [];
      for (ci = 0; ci < catOrder.length; ci++) {
        var raw = map[catOrder[ci] + SEP + serOrder[si]];
        vals.push(raw === undefined || raw === null ? 0 : raw);
      }
      series.push({
        name: serOrder[si], type: 'radar',
        data: [{ name: serOrder[si], value: vals }],
        symbolSize: 4,
        itemStyle: { color: pc(theme, si) },
        lineStyle: { width: 2, color: pc(theme, si) },
        areaStyle: { color: pc(theme, si), opacity: 0.10 },
        emphasis: { lineStyle: { width: 3 } }
      });
    }

    var tip = tipItem(theme);
    tip.formatter = function (p) {
      var vals = p.value || [];
      var html = head(p.name || p.seriesName);
      for (var j = 0; j < catOrder.length; j++) html += row(catOrder[j], U.fmtValue(vals[j], spec.fmt));
      return html;
    };

    return {
      legend: U.makeLegend(theme, state.legendSel, spec.legend !== false),
      toolbox: U.makeToolbox(theme),
      tooltip: tip,
      radar: {
        indicator: indicators,
        center: ['50%', '55%'],
        radius: '64%',
        axisName: { color: theme.subtext, fontSize: 11 },
        axisLine: { lineStyle: { color: theme.axis } },
        splitLine: { lineStyle: { color: theme.split } },
        splitArea: { show: false }
      },
      series: series
    };
  };

  // ====================================================================
  // 3.9 rose 南丁格尔玫瑰图
  // ====================================================================
  B['rose'] = function (spec, data, state, theme) {
    var roles = spec.roles || {};
    var rows = U.filteredRows(spec, data, state);
    var ndim = roles.names || roles.x;
    var vdim = roles.value || roles.y;
    if (!ndim || !rows.length) return U.emptyOption(theme);

    var how = spec.agg || (vdim ? 'sum' : 'count');
    var groups = U.groupBy(rows, [ndim], vdim, how);
    var items = [], i;
    for (i = 0; i < groups.length; i++) {
      items.push({ name: groups[i].keys[0], value: groups[i].value === null ? 0 : groups[i].value });
    }
    if (!items.length) return U.emptyOption(theme);
    if (spec.sort === 'asc') items.sort(function (a, b) { return a.value - b.value; });
    else items.sort(function (a, b) { return b.value - a.value; });
    if (spec.topN && items.length > spec.topN) {
      var rest = 0, j;
      for (j = spec.topN; j < items.length; j++) rest += items[j].value;
      items = items.slice(0, spec.topN);
      items.push({ name: '其他', value: rest });
    }

    var sel = U.sourceSelection(spec, state);
    var dataArr = [];
    for (i = 0; i < items.length; i++) {
      var it = { name: items[i].name, value: items[i].value };
      if (sel !== null && sel !== undefined && items[i].name !== sel) it.itemStyle = { opacity: 0.3 };
      dataArr.push(it);
    }

    var tip = tipItem(theme);
    tip.formatter = function (p) {
      return head(p.name) + row(U.axisTitle(spec.ytitle, vdim || '数量'), U.fmtValue(p.value, spec.fmt)) +
        row('占比', p.percent + '%');
    };

    return {
      legend: {
        show: spec.legend !== false, type: 'scroll', orient: 'vertical',
        right: 6, top: 'middle', itemWidth: 10, itemHeight: 8,
        textStyle: { color: theme.subtext, fontSize: 11 },
        selected: state.legendSel || undefined
      },
      toolbox: U.makeToolbox(theme),
      tooltip: tip,
      series: [{
        type: 'pie', roseType: 'radius',
        radius: spec.donut ? ['38%', '70%'] : ['0%', '70%'],
        center: ['38%', '52%'],
        avoidLabelOverlap: true, minAngle: 2,
        itemStyle: { borderColor: theme.bg, borderWidth: 2, borderRadius: 3 },
        label: {
          show: !!spec.labels, color: theme.text, fontSize: 11, lineHeight: 15,
          formatter: '{b}\n{d}%'
        },
        labelLine: { show: !!spec.labels, length: 10, length2: 8, lineStyle: { color: theme.axis } },
        emphasis: { scale: true, scaleSize: 6, itemStyle: { shadowBlur: 12, shadowColor: 'rgba(0,0,0,.2)' } },
        data: dataArr
      }]
    };
  };

  // ====================================================================
  // 3.10 parallel 平行坐标：parallelDims 每维一个坐标轴
  // ====================================================================
  B['parallel'] = function (spec, data, state, theme) {
    var roles = spec.roles || {};
    var rows = U.filteredRows(spec, data, state);
    var dims = spec.parallelDims || [];
    if (!rows.length || !dims.length) return U.emptyOption(theme);
    var cdim = roles.color;
    var useColor = !!(cdim && U.hasCol(data, cdim));

    var buckets = {}, order = [], i, d;
    for (i = 0; i < rows.length; i++) {
      var r = rows[i], vals = [], has = false;
      for (d = 0; d < dims.length; d++) {
        var n = U.num(r[dims[d]]);
        if (n !== null) has = true;
        vals.push(n === null ? '-' : n);
      }
      if (!has) continue;
      var key = useColor ? U.catName(r[cdim]) : '';
      if (!buckets[key]) { buckets[key] = []; order.push(key); }
      buckets[key].push(vals);
    }
    if (!order.length) return U.emptyOption(theme);

    var series = [], k;
    for (k = 0; k < order.length; k++) {
      series.push({
        name: order[k] || (roles.y || '数据'), type: 'parallel',
        lineStyle: { width: 1.6, opacity: 0.75, color: pc(theme, k) },
        emphasis: { lineStyle: { width: 3, opacity: 1 } },
        data: buckets[order[k]]
      });
    }

    var parallelAxis = [];
    for (d = 0; d < dims.length; d++) {
      parallelAxis.push({
        dim: d, name: dims[d], type: 'value',
        nameTextStyle: { color: theme.text, fontSize: 11 },
        axisLine: { lineStyle: { color: theme.axis } },
        axisTick: { show: false },
        axisLabel: {
          color: theme.subtext, fontSize: 10,
          formatter: function (v) { return U.fmtValue(v, spec.fmt); }
        },
        splitLine: { lineStyle: { color: theme.split, type: 'dashed' } }
      });
    }

    var tip = tipItem(theme);
    tip.formatter = function (p) {
      var vals = p.data || [];
      var html = head(p.seriesName || '');
      for (var j = 0; j < dims.length; j++) {
        html += row(dims[j], U.fmtValue(vals[j], spec.fmt));
      }
      return html;
    };

    var showLegend = useColor && order.length > 1 && spec.legend !== false;
    return {
      legend: U.makeLegend(theme, state.legendSel, showLegend),
      toolbox: U.makeToolbox(theme),
      tooltip: tip,
      parallelAxis: parallelAxis,
      parallel: {
        left: 56, right: 56,
        top: showLegend ? 62 : 32,
        bottom: 28,
        parallelAxisDefault: {
          type: 'value',
          nameTextStyle: { color: theme.text, fontSize: 11 }
        }
      },
      series: series
    };
  };

  // ====================================================================
  // 3.11 pictorial 象形柱图
  // ====================================================================
  B['pictorial'] = function (spec, data, state, theme) {
    var roles = spec.roles || {};
    var rows = U.filteredRows(spec, data, state);
    var xdim = U.currentXDim(spec, state);
    if (!xdim || !rows.length) return U.emptyOption(theme);

    var recs = sortRecs(recsOf(rows, xdim, roles.y, spec.agg || 'sum'), xdim, spec, data);
    if (!recs.length) return U.emptyOption(theme);
    var cats = [], vals = [], maxV = 0, i;
    for (i = 0; i < recs.length; i++) {
      cats.push(recs[i].name);
      vals.push(recs[i].value);
      if (recs[i].value > maxV) maxV = recs[i].value;
    }
    if (maxV <= 0) maxV = 1;

    // 象形符号大小随图高自适应
    var h = Number(spec.height) || 360;
    var sym = Math.max(7, Math.min(18, Math.round(h / 26)));
    var barData = [];
    for (i = 0; i < cats.length; i++) barData.push({ name: cats[i], value: vals[i] });

    var tip = tipAxis(theme);
    tip.formatter = function (ps) {
      var p = ps && ps.length ? ps[0] : null;
      if (!p) return '';
      return head(p.name) + row(U.axisTitle(spec.ytitle, roles.y), U.fmtValue(p.value, spec.fmt));
    };

    return {
      grid: U.makeGrid(theme, { legend: false }),
      tooltip: tip,
      toolbox: U.makeToolbox(theme),
      xAxis: catAxisOf(spec, cats, theme, roles.x),
      yAxis: valAxisOf(spec, theme, roles.y),
      series: [{
        name: U.axisTitle(spec.ytitle, roles.y), type: 'pictorialBar',
        data: barData,
        symbol: spec.symbol || 'circle',
        symbolRepeat: true, symbolRepeatDirection: 'start',
        symbolClip: true, symbolMargin: 0,
        symbolSize: [sym, sym],
        symbolBoundingData: maxV * 1.02,
        symbolPosition: 'start',
        barCategoryGap: '30%',
        z: 2,
        itemStyle: { color: pc(theme, 0), opacity: 0.92 },
        label: {
          show: !!spec.labels, position: 'top', color: theme.subtext, fontSize: 11,
          formatter: function (p) { return U.fmtValue(p.value, spec.fmt); }
        }
      }]
    };
  };

  // ====================================================================
  // 3.12 target 目标对比图：实际值柱 + 目标值线
  // ====================================================================
  B['target'] = function (spec, data, state, theme) {
    var roles = spec.roles || {};
    var rows = U.filteredRows(spec, data, state);
    var xdim = U.currentXDim(spec, state);
    var ycol = roles.y;
    if (!xdim || !rows.length || !ycol) return U.emptyOption(theme);

    var how = spec.agg || 'sum';
    var recs = sortRecs(recsOf(rows, xdim, ycol, how), xdim, spec, data);
    if (!recs.length) return U.emptyOption(theme);

    var tcol = roles.target;
    var tMap = {};
    if (tcol && U.hasCol(data, tcol)) {
      var tg = U.groupBy(rows, [xdim], tcol, how);
      for (var ti = 0; ti < tg.length; ti++) tMap[tg[ti].keys[0]] = tg[ti].value;
    }

    var cats = [], actual = [], targets = [], i;
    for (i = 0; i < recs.length; i++) {
      var t = (tMap[recs[i].name] === undefined) ? spec.targetValue : tMap[recs[i].name];
      t = U.num(t);
      cats.push(recs[i].name);
      actual.push(recs[i].value);
      targets.push(t === null ? 0 : t);
    }

    var tip = tipAxis(theme);
    tip.formatter = function (ps) {
      var p = ps && ps.length ? ps[0] : null;
      if (!p) return '';
      var idx = p.dataIndex;
      var a = actual[idx] || 0, tg = targets[idx] || 0;
      var rate = tg ? (a / tg * 100) : null;
      var html = head(cats[idx]) +
        row('实际', U.fmtValue(a, spec.fmt)) + row('目标', U.fmtValue(tg, spec.fmt));
      if (rate !== null) html += row('达成率', rate.toFixed(1) + '%');
      return html;
    };

    var barData = [], lineData = [];
    for (i = 0; i < cats.length; i++) {
      barData.push({ name: cats[i], value: actual[i] });
      lineData.push({ name: cats[i], value: targets[i] });
    }

    return {
      grid: U.makeGrid(theme, { legend: spec.legend !== false }),
      legend: U.makeLegend(theme, state.legendSel, spec.legend !== false),
      toolbox: U.makeToolbox(theme),
      tooltip: tip,
      xAxis: catAxisOf(spec, cats, theme, roles.x),
      yAxis: valAxisOf(spec, theme, ycol),
      series: [
        {
          name: '实际', type: 'bar', barMaxWidth: 34, data: barData,
          itemStyle: { color: pc(theme, 0), borderRadius: [4, 4, 0, 0] },
          label: {
            show: !!spec.labels, position: 'top', color: theme.subtext, fontSize: 11,
            formatter: function (p) { return U.fmtValue(p.value, spec.fmt); }
          }
        },
        {
          name: '目标', type: 'line', z: 4, data: lineData,
          symbol: 'none', lineStyle: { color: theme.subtext, width: 1.6, type: 'dashed' },
          itemStyle: { color: theme.subtext }
        }
      ]
    };
  };

  // ====================================================================
  // 3.13 trend 趋势散点：散点 + 回归线 + R²
  // ====================================================================
  B['trend'] = function (spec, data, state, theme) {
    var roles = spec.roles || {};
    var rows = U.filteredRows(spec, data, state);
    var xcol = roles.x, ycol = roles.y, cdim = roles.color;
    if (!xcol || !ycol || !rows.length) return U.emptyOption(theme);

    var pts = [], i;
    for (i = 0; i < rows.length; i++) {
      var r = rows[i];
      var xv = U.num(r[xcol]), yv = U.num(r[ycol]);
      if (xv === null || yv === null) continue;
      pts.push({ x: xv, y: yv, c: (cdim && U.hasCol(data, cdim)) ? U.catName(r[cdim]) : '', n: U.catName(r[xcol]) });
    }
    if (!pts.length) return U.emptyOption(theme);

    var fit = spec.fit;
    if (!fit || !U.isNum(fit.slope)) fit = linfit(pts);
    if (!fit) fit = { slope: 0, intercept: pts[0].y, r2: null };

    var minX = pts[0].x, maxX = pts[0].x;
    for (i = 1; i < pts.length; i++) {
      if (pts[i].x < minX) minX = pts[i].x;
      if (pts[i].x > maxX) maxX = pts[i].x;
    }
    if (minX === maxX) { minX -= 0.5; maxX += 0.5; }

    var byColor = {}, order = [], k;
    for (i = 0; i < pts.length; i++) {
      var key = pts[i].c;
      if (!byColor[key]) { byColor[key] = []; order.push(key); }
      byColor[key].push({ name: pts[i].n, value: [pts[i].x, pts[i].y] });
    }

    var series = [], si;
    for (si = 0; si < order.length; si++) {
      series.push({
        name: order[si] || ycol, type: 'scatter', data: byColor[order[si]],
        symbolSize: 8, z: 3,
        itemStyle: { color: pc(theme, si), opacity: 0.82, borderColor: theme.bg, borderWidth: 1 },
        emphasis: { focus: 'series' }
      });
    }

    var lineData = [[minX, fit.intercept + fit.slope * minX], [maxX, fit.intercept + fit.slope * maxX]];
    series.push({
      name: '回归线', type: 'line', data: lineData, z: 5,
      symbol: 'none', silent: true, tooltip: { show: false },
      lineStyle: { color: pc(theme, 3), width: 2, type: 'dashed' }
    });

    var tip = tipItem(theme);
    tip.formatter = function (p) {
      if (p.seriesName === '回归线') return head('回归线') + row('拟合线', 'y = ' + U.roundTo(fit.slope, 3) + 'x + ' + U.roundTo(fit.intercept, 3));
      var d = p.data || {};
      var vals = d.value || [];
      var html = '';
      if (cdim && U.hasCol(data, cdim)) html += head(p.seriesName);
      html += row(xcol, U.fmtValue(vals[0], spec.fmt));
      html += row(ycol, U.fmtValue(vals[1], spec.fmt));
      return html;
    };

    var opt = {
      grid: U.makeGrid(theme, { legend: !!(cdim && spec.legend !== false), rightExtra: 24 }),
      legend: U.makeLegend(theme, state.legendSel, !!(cdim && spec.legend !== false)),
      toolbox: U.makeToolbox(theme),
      tooltip: tip,
      xAxis: (function () {
        var a = U.makeValueAxis(spec, theme, spec.xlim);
        return U.setAxisName(a, U.axisTitle(spec.xtitle, xcol), theme, true);
      })(),
      yAxis: (function () {
        var a = U.makeValueAxis(spec, theme, spec.ylim);
        return U.setAxisName(a, U.axisTitle(spec.ytitle, ycol), theme, false);
      })(),
      series: series
    };
    if (U.isNum(fit.r2)) {
      opt.graphic = {
        type: 'text', right: 30, top: 8, silent: true, z: 9,
        style: { text: 'R² = ' + U.roundTo(fit.r2, 3), fill: theme.subtext, fontSize: 11 }
      };
    }
    return opt;
  };

  // ====================================================================
  // 3.14 quadrant 四象限散点
  // ====================================================================
  B['quadrant'] = function (spec, data, state, theme) {
    var roles = spec.roles || {};
    var rows = U.filteredRows(spec, data, state);
    var xcol = roles.x, ycol = roles.y, sdim = roles.size, cdim = roles.color;
    if (!xcol || !ycol || !rows.length) return U.emptyOption(theme);

    var pts = [], sizes = [], i;
    for (i = 0; i < rows.length; i++) {
      var r = rows[i];
      var xv = U.num(r[xcol]), yv = U.num(r[ycol]);
      if (xv === null || yv === null) continue;
      var sv = sdim ? U.num(r[sdim]) : null;
      if (sv !== null) sizes.push(sv);
      pts.push({
        x: xv, y: yv, s: sv,
        c: (cdim && U.hasCol(data, cdim)) ? U.catName(r[cdim]) : '',
        n: U.catName(r[xcol])
      });
    }
    if (!pts.length) return U.emptyOption(theme);

    var sMin = sizes.length ? Math.min.apply(null, sizes) : 0;
    var sMax = sizes.length ? Math.max.apply(null, sizes) : 0;
    var scaler = sizeScaler(sMin, sMax);

    var xs = [], ys = [];
    for (i = 0; i < pts.length; i++) { xs.push(pts[i].x); ys.push(pts[i].y); }
    var xmid = U.num(spec.xmid);
    var ymid = U.num(spec.ymid);
    if (xmid === null) xmid = U.median(xs);
    if (ymid === null) ymid = U.median(ys);

    var byColor = {}, order = [], k;
    for (i = 0; i < pts.length; i++) {
      var key = pts[i].c;
      if (!byColor[key]) { byColor[key] = []; order.push(key); }
      byColor[key].push({
        name: pts[i].n,
        value: [pts[i].x, pts[i].y, pts[i].s === null ? 0 : pts[i].s]
      });
    }

    var series = [], si;
    for (si = 0; si < order.length; si++) {
      series.push({
        name: order[si] || ycol, type: 'scatter', data: byColor[order[si]],
        symbolSize: (sdim || cdim) ? function (v) { return scaler(v[2]); } : 9,
        z: 3,
        itemStyle: { color: pc(theme, si), opacity: 0.84, borderColor: theme.bg, borderWidth: 1 },
        emphasis: { focus: 'series' }
      });
    }
    // 两条中线只画一次
    if (series.length) {
      series[0].markLine = {
        silent: true, symbol: 'none', animation: false,
        lineStyle: { color: theme.subtext, type: 'dashed', width: 1, opacity: 0.6 },
        label: { show: false },
        data: [{ xAxis: xmid }, { yAxis: ymid }]
      };
    }

    var tip = tipItem(theme);
    tip.formatter = function (p) {
      var vals = (p.data && p.data.value) || [];
      var html = '';
      if (cdim && U.hasCol(data, cdim)) html += head(p.seriesName);
      html += row(xcol, U.fmtValue(vals[0], spec.fmt));
      html += row(ycol, U.fmtValue(vals[1], spec.fmt));
      if (sdim) html += row(sdim, U.fmtValue(vals[2], spec.fmt));
      return html;
    };

    var opt = {
      grid: U.makeGrid(theme, { legend: !!(cdim && spec.legend !== false) }),
      legend: U.makeLegend(theme, state.legendSel, !!(cdim && spec.legend !== false)),
      toolbox: U.makeToolbox(theme),
      tooltip: tip,
      xAxis: (function () {
        var a = U.makeValueAxis(spec, theme, spec.xlim);
        return U.setAxisName(a, U.axisTitle(spec.xtitle, xcol), theme, true);
      })(),
      yAxis: (function () {
        var a = U.makeValueAxis(spec, theme, spec.ylim);
        return U.setAxisName(a, U.axisTitle(spec.ytitle, ycol), theme, false);
      })(),
      series: series
    };

    // 四角说明文本：quadrantLabels = [左上, 右上, 左下, 右下]
    var ql = spec.quadrantLabels || [];
    var gl = [];
    for (i = 0; i < 4; i++) {
      var txt = (ql[i] === null || ql[i] === undefined) ? '' : String(ql[i]);
      if (!txt) continue;
      var pos;
      if (i === 0) pos = { left: '9%', top: '10%' };
      else if (i === 1) pos = { right: '13%', top: '10%' };
      else if (i === 2) pos = { left: '9%', bottom: '16%' };
      else pos = { right: '13%', bottom: '16%' };
      gl.push({
        type: 'text', silent: true, z: 1,
        left: pos.left, right: pos.right, top: pos.top, bottom: pos.bottom,
        style: { text: txt, fill: theme.subtext, fontSize: 12, opacity: 0.65 }
      });
    }
    if (gl.length) opt.graphic = gl;
    return opt;
  };

  // ====================================================================
  // 3.15 matrix 相关系数矩阵（数据由 Python 预计算：spec.labels / spec.values）
  // ====================================================================
  B['matrix'] = function (spec, data, state, theme) {
    // 预计算数据，不参与联动/过滤；filteredRows 仅保持调用契约
    U.filteredRows(spec, data, state);
    var labels = spec.labels || [];
    var values = spec.values || [];
    if (!labels.length || !values.length) return U.emptyOption(theme);

    var points = [], i, j;
    for (i = 0; i < labels.length; i++) {
      var rv = values[i] || [];
      for (j = 0; j < labels.length; j++) {
        var v = U.num(rv[j]);
        points.push([j, i, v === null ? 0 : v]);
      }
    }

    var xAxis = U.makeCategoryAxis(spec, labels, theme);
    xAxis.axisLabel.interval = 0;
    xAxis.axisLabel.formatter = function (v) { return U.truncate(v, 12); };
    xAxis.splitArea = { show: false };
    var yAxis = U.makeCategoryAxis(spec, labels, theme);
    yAxis.inverse = true;
    yAxis.axisLabel.interval = 0;
    yAxis.axisLabel.formatter = function (v) { return U.truncate(v, 12); };
    yAxis.splitArea = { show: false };
    U.setAxisName(xAxis, spec.xtitle, theme, true, 30);
    U.setAxisName(yAxis, spec.ytitle, theme, false, 12);

    var tip = tipItem(theme);
    tip.formatter = function (p) {
      var d = p.data || [0, 0, 0];
      return head(labels[d[0]] + ' × ' + labels[d[1]]) +
        row('相关系数', Number(d[2]).toFixed(2));
    };

    var heatGrid = U.makeGrid(theme, { legend: false, rightExtra: 56 });
    heatGrid.bottom = 40;
    return {
      grid: heatGrid,
      toolbox: U.makeToolbox(theme),
      tooltip: tip,
      xAxis: xAxis,
      yAxis: yAxis,
      visualMap: {
        min: -1, max: 1, calculable: false, orient: 'vertical',
        right: 2, top: 'middle', itemWidth: 10, itemHeight: 90,
        textStyle: { color: theme.subtext, fontSize: 10 },
        formatter: function (v) { return Number(v).toFixed(1); },
        inRange: { color: [pc(theme, 3), theme.bg, pc(theme, 0)] }
      },
      series: [{
        type: 'heatmap', data: points,
        label: {
          show: spec.labels !== false, color: theme.text, fontSize: 10,
          formatter: function (p) { return Number(p.data[2]).toFixed(2); }
        },
        itemStyle: { borderColor: theme.bg, borderWidth: 1 },
        emphasis: { itemStyle: { borderColor: theme.text, borderWidth: 1 } }
      }]
    };
  };

  // ====================================================================
  // 3.16 sparkline 迷你走势（Python 预计算：spec.series / spec.sparkData；
  //      缺失时回退到 groupBy 现算，最多 12 组）
  // ====================================================================
  B['sparkline'] = function (spec, data, state, theme) {
    var roles = spec.roles || {};
    var rows = U.filteredRows(spec, data, state);
    var groups = [], i, j;

    var pre = spec.series || spec.sparkData || null;
    if (pre && pre.length) {
      for (i = 0; i < pre.length; i++) {
        var item = pre[i];
        var vals0 = [], nm;
        if (item && item.length !== undefined) { vals0 = item; nm = '系列' + (i + 1); }
        else if (item) {
          nm = item.name || ('系列' + (i + 1));
          var src = item.values || item.data || [];
          vals0 = src;
        }
        var nums = [];
        for (j = 0; j < vals0.length; j++) {
          var n0 = U.num(vals0[j]);
          nums.push(n0 === null ? null : n0);
        }
        groups.push({ name: String(nm), values: nums });
      }
    } else {
      var xdim = U.currentXDim(spec, state);
      var gdim = roles.color || roles.names;
      var ycol = roles.y || roles.value;
      if (xdim && rows.length) {
        var useColor = !!(gdim && U.hasCol(data, gdim));
        var how = spec.agg || (ycol ? 'sum' : 'count');
        var gs = U.groupBy(rows, useColor ? [xdim, gdim] : [xdim], ycol, how);
        var times = [], tSeen = {}, gnames = [], gSeen = {}, map = {};
        for (i = 0; i < gs.length; i++) {
          var tv = gs[i].keys[0];
          var gv = useColor ? gs[i].keys[1] : (ycol || '数值');
          if (!tSeen[tv]) { tSeen[tv] = 1; times.push(tv); }
          if (!gSeen[gv]) { gSeen[gv] = 1; gnames.push(gv); }
          map[tv + SEP + gv] = gs[i].value;
        }
        if (spec.sort === 'x') {
          var ranker = U.catRanker(data, xdim);
          times.sort(function (a, b) { return ranker ? ranker(a, b) : U.compareCatX(a, b); });
        }
        for (i = 0; i < gnames.length; i++) {
          var arr = [];
          for (j = 0; j < times.length; j++) {
            var v0 = map[times[j] + SEP + gnames[i]];
            arr.push(v0 === undefined ? null : v0);
          }
          groups.push({ name: gnames[i], values: arr });
        }
      }
    }
    if (!groups.length) return U.emptyOption(theme);
    if (groups.length > 12) groups = groups.slice(0, 12);

    var n = groups.length;
    var totalH = Number(spec.height) || 360;
    var blockH = totalH / n;
    var grids = [], xAxes = [], yAxes = [], series = [], graphics = [];
    for (i = 0; i < n; i++) {
      var vals = groups[i].values;
      var latest = null;
      for (j = vals.length - 1; j >= 0; j--) { if (vals[j] !== null) { latest = vals[j]; break; } }
      var color = pc(theme, i);
      grids.push({ left: 78, right: 56, top: i * blockH + 6, height: Math.max(12, blockH - 12) });
      xAxes.push({
        type: 'category', show: false, boundaryGap: false,
        data: (function (len) { var a = []; for (var q = 0; q < len; q++) a.push(String(q)); return a; })(vals.length)
      });
      yAxes.push({ type: 'value', show: false, scale: true, min: 'dataMin', max: 'dataMax' });
      series.push({
        name: groups[i].name, type: 'line',
        xAxisIndex: i, yAxisIndex: i, data: vals,
        symbol: 'none', smooth: true, connectNulls: false,
        lineStyle: { width: 1.6, color: color },
        areaStyle: { color: color, opacity: 0.12 },
        emphasis: { disabled: true }
      });
      graphics.push({
        type: 'text', left: 8, top: i * blockH + blockH / 2 - 6, silent: true, z: 5,
        style: { text: U.truncate(groups[i].name, 12), fill: theme.subtext, fontSize: 11 }
      });
      graphics.push({
        type: 'text', right: 8, top: i * blockH + blockH / 2 - 6, silent: true, z: 5,
        style: { text: U.fmtValue(latest, spec.fmt), fill: theme.text, fontSize: 11, fontWeight: 600 }
      });
    }

    var tip = tipItem(theme);
    tip.formatter = function (p) {
      return head(p.seriesName) + row('序号', String(p.dataIndex + 1)) +
        row('数值', U.fmtValue(p.value, spec.fmt));
    };

    return {
      tooltip: tip,
      toolbox: U.makeToolbox(theme),
      grid: grids,
      xAxis: xAxes,
      yAxis: yAxes,
      series: series,
      graphic: graphics
    };
  };

  // ====================================================================
  // 3.17 ring_progress 环形进度（Python 预计算：spec.percentValue / spec.label）
  // ====================================================================
  B['ring_progress'] = function (spec, data, state, theme) {
    // 预计算数据，不参与联动/过滤；filteredRows 仅保持调用契约
    U.filteredRows(spec, data, state);
    var max = U.num(spec.max);
    if (max === null || max <= 0) max = 100;
    var v = U.num(spec.percentValue);
    if (v === null) return U.emptyOption(theme);
    var pct = v / max * 100;
    if (pct < 0) pct = 0;
    if (pct > 100) pct = 100;

    var txt = U.fmtValue(pct, spec.fmt || 'percent');
    if (String(txt).indexOf('%') < 0) txt += '%';

    var tip = tipItem(theme);
    tip.formatter = function () {
      return head(spec.label || '进度') + row('完成', U.fmtValue(v, spec.fmt)) +
        row('占比', U.fmtValue(pct, 'percent'));
    };

    var graphics = [{
      type: 'text', left: 'center', top: '42%', silent: true, z: 5,
      style: { text: txt, fill: theme.text, fontSize: 30, fontWeight: 600 }
    }];
    if (spec.label) {
      graphics.push({
        type: 'text', left: 'center', top: '60%', silent: true, z: 5,
        style: { text: String(spec.label), fill: theme.subtext, fontSize: 12 }
      });
    }

    return {
      tooltip: tip,
      toolbox: U.makeToolbox(theme),
      graphic: graphics,
      series: [{
        type: 'pie', startAngle: 90, radius: ['74%', '92%'], center: ['50%', '52%'],
        avoidLabelOverlap: false, silent: false,
        label: { show: false }, labelLine: { show: false },
        itemStyle: { borderRadius: 50 },
        data: [
          { name: '进度', value: pct, itemStyle: { color: pc(theme, 0) } },
          { name: '余量', value: 100 - pct, itemStyle: { color: theme.surfaceVar } }
        ]
      }]
    };
  };

})();
