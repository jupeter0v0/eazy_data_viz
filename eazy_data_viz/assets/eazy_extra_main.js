/*!
 * eazy_data_viz 扩展图表 · 主控实现：waterfall（瀑布图）/ bullet（子弹图）/ lollipop（棒棒糖）
 * 约定见 docs/EXTRA_CHARTS.md；工具见 EazyViz.core.util。
 */
(function () {
  'use strict';
  if (typeof window === 'undefined' || !window.EazyViz) return;

  var EazyViz = window.EazyViz;
  var U = EazyViz.core.util;
  var B = EazyViz.extraBuilders;

  function sortRecs(recs, spec, data, xdim) {
    if (spec.sort === 'x') {
      var ranker = U.catRanker(data, xdim);
      recs.sort(function (a, b) {
        if (ranker) return ranker(a.name, b.name);
        return U.compareCatX(a.name, b.name);
      });
    } else if (spec.sort === 'asc') {
      recs.sort(function (a, b) { return a.value - b.value; });
    } else if (spec.sort === 'desc') {
      recs.sort(function (a, b) { return b.value - a.value; });
    }
    return recs;
  }

  // ------------------------------------------------------------------
  // waterfall 瀑布图：每段增量 + 累计
  // ------------------------------------------------------------------
  B['waterfall'] = function (spec, data, state, theme) {
    var rows = U.filteredRows(spec, data, state);
    var xdim = U.currentXDim(spec, state);
    if (!xdim || !rows.length) return U.emptyOption(theme);
    var groups = U.groupBy(rows, [xdim], spec.roles.y, spec.agg || 'sum');
    var recs = [];
    for (var i = 0; i < groups.length; i++) {
      recs.push({ name: groups[i].keys[0], value: groups[i].value || 0 });
    }
    sortRecs(recs, spec, data, xdim);

    var cats = [], bases = [], deltas = [], cums = [], colors = [];
    var cum = 0;
    for (var k = 0; k < recs.length; k++) {
      var d = Number(recs[k].value) || 0;
      var start = cum;
      cum += d;
      cats.push(recs[k].name);
      bases.push(start);
      deltas.push(Math.abs(d));
      cums.push(cum);
      colors.push(d < 0 ? theme.palette[3] : theme.palette[1]);
    }
    if (spec.total) {
      cats.push('合计');
      bases.push(0);
      deltas.push(Math.abs(cum));
      cums.push(cum);
      colors.push(theme.palette[0]);
    }
    var idxMap = {};
    for (var j = 0; j < cats.length; j++) idxMap[cats[j]] = j;

    function tipHtml(idx) {
      var last = spec.total ? cats.length - 2 : cats.length - 1;
      if (idx > last) return '<b>合计</b><br/>累计：' + U.fmtValue(cums[idx], spec.fmt);
      var d = cums[idx] - (idx ? cums[idx - 1] : 0);
      return '<b>' + U.esc(cats[idx]) + '</b><br/>增量：' + U.fmtValue(d, spec.fmt) +
        '<br/>累计：' + U.fmtValue(cums[idx], spec.fmt);
    }

    var tip = U.tooltipBox(theme);
    tip.trigger = 'axis';
    tip.axisPointer = { type: 'shadow' };
    tip.formatter = function (ps) {
      if (!ps || !ps.length) return '';
      var idx = idxMap[ps[0].name];
      return idx === undefined ? '' : tipHtml(idx);
    };

    var catAxis = U.makeCategoryAxis(spec, cats, theme);
    U.setAxisName(catAxis, U.axisTitle(spec.xtitle, spec.roles.x), theme, true);
    var valAxis = U.makeValueAxis(spec, theme, spec.ylim);
    U.setAxisName(valAxis, U.axisTitle(spec.ytitle, spec.roles.y), theme, false);

    return {
      grid: U.makeGrid(theme, { legend: false }),
      toolbox: U.makeToolbox(theme),
      tooltip: tip,
      xAxis: catAxis,
      yAxis: valAxis,
      series: [
        {
          name: 'base', type: 'bar', stack: 'wf', silent: true,
          itemStyle: { color: 'transparent' }, emphasis: { disabled: true },
          data: bases
        },
        {
          name: '增量', type: 'bar', stack: 'wf', barMaxWidth: 34,
          data: deltas.map(function (v, i) {
            return { value: v, itemStyle: { color: colors[i], borderRadius: [4, 4, 0, 0] } };
          }),
          label: {
            show: !!spec.labels, position: 'top', color: theme.subtext, fontSize: 11,
            formatter: function (p) {
              var d = cums[p.dataIndex] - (p.dataIndex ? cums[p.dataIndex - 1] : 0);
              return U.fmtValue(d, spec.fmt);
            }
          }
        }
      ]
    };
  };

  // ------------------------------------------------------------------
  // bullet 子弹图：实际值 vs 目标（横向）
  // ------------------------------------------------------------------
  B['bullet'] = function (spec, data, state, theme) {
    var rows = U.filteredRows(spec, data, state);
    var xdim = U.currentXDim(spec, state);
    if (!xdim || !rows.length) return U.emptyOption(theme);
    var groups = U.groupBy(rows, [xdim], spec.roles.y, spec.agg || 'sum');
    var recs = [];
    for (var i = 0; i < groups.length; i++) {
      recs.push({ name: groups[i].keys[0], value: groups[i].value || 0 });
    }
    sortRecs(recs, spec, data, xdim);

    var tMap = {};
    if (spec.roles.target && U.hasCol(data, spec.roles.target)) {
      var tg = U.groupBy(rows, [xdim], spec.roles.target, spec.agg || 'sum');
      for (var t = 0; t < tg.length; t++) tMap[tg[t].keys[0]] = tg[t].value;
    }
    var cats = [], actual = [], targets = [], maxVals = [];
    for (var j = 0; j < recs.length; j++) {
      var tv = tMap[recs[j].name];
      if (tv === undefined || tv === null) tv = spec.targetValue;
      tv = Number(tv) || 0;
      var av = Number(recs[j].value) || 0;
      cats.push(recs[j].name);
      actual.push(av);
      targets.push(tv);
      maxVals.push(Math.max(av, tv) * 1.06 || 1);
    }

    var tip = U.tooltipBox(theme);
    tip.trigger = 'axis';
    tip.axisPointer = { type: 'shadow' };
    tip.formatter = function (ps) {
      if (!ps || !ps.length) return '';
      var idx = ps[0].dataIndex;
      var a = actual[idx] || 0, tg = targets[idx] || 0;
      var rate = tg ? (a / tg * 100) : null;
      return '<b>' + U.esc(cats[idx]) + '</b><br/>实际：' + U.fmtValue(a, spec.fmt) +
        '<br/>目标：' + U.fmtValue(tg, spec.fmt) +
        (rate === null ? '' : '<br/>达成率：<b>' + rate.toFixed(1) + '%</b>');
    };

    var catAxis = U.makeCategoryAxis(spec, cats, theme);
    catAxis.inverse = true;
    U.setAxisName(catAxis, U.axisTitle(spec.ytitle, spec.roles.x), theme, false, 24);
    var valAxis = U.makeValueAxis(spec, theme, spec.xlim);
    U.setAxisName(valAxis, U.axisTitle(spec.xtitle, spec.roles.y), theme, true);

    return {
      grid: U.makeGrid(theme, { legend: false }),
      toolbox: U.makeToolbox(theme),
      tooltip: tip,
      xAxis: valAxis,
      yAxis: catAxis,
      series: [
        {
          name: '背景', type: 'bar', barWidth: 22, silent: true, z: 1,
          itemStyle: { color: theme.surfaceVar, borderRadius: 4 },
          data: maxVals
        },
        {
          name: '实际', type: 'bar', barWidth: 10, z: 3, barGap: '-135%',
          itemStyle: { color: theme.palette[0], borderRadius: 4 },
          data: actual
        },
        {
          name: '目标', type: 'scatter', z: 4, symbol: 'rect', symbolSize: [3, 18],
          itemStyle: { color: theme.text }, data: targets
        }
      ]
    };
  };

  // ------------------------------------------------------------------
  // lollipop 棒棒糖图
  // ------------------------------------------------------------------
  B['lollipop'] = function (spec, data, state, theme) {
    var rows = U.filteredRows(spec, data, state);
    var xdim = U.currentXDim(spec, state);
    if (!xdim || !rows.length) return U.emptyOption(theme);
    var groups = U.groupBy(rows, [xdim], spec.roles.y, spec.agg || 'sum');
    var recs = [];
    for (var i = 0; i < groups.length; i++) {
      recs.push({ name: groups[i].keys[0], value: groups[i].value || 0 });
    }
    sortRecs(recs, spec, data, xdim);
    var cats = [], vals = [];
    for (var k = 0; k < recs.length; k++) { cats.push(recs[k].name); vals.push(recs[k].value); }

    var catAxis = U.makeCategoryAxis(spec, cats, theme);
    U.setAxisName(catAxis, U.axisTitle(spec.xtitle, spec.roles.x), theme, true);
    var valAxis = U.makeValueAxis(spec, theme, spec.ylim);
    U.setAxisName(valAxis, U.axisTitle(spec.ytitle, spec.roles.y), theme, false);

    var tip = U.tooltipBox(theme);
    tip.trigger = 'axis';
    tip.axisPointer = { type: 'shadow' };

    return {
      grid: U.makeGrid(theme, { legend: false }),
      toolbox: U.makeToolbox(theme),
      tooltip: tip,
      xAxis: catAxis,
      yAxis: valAxis,
      series: [
        {
          name: spec.roles.y || '值', type: 'bar', barWidth: 2,
          itemStyle: { color: theme.palette[0], opacity: 0.55 }, data: vals
        },
        {
          name: spec.roles.y || '值', type: 'scatter', symbolSize: 9, z: 3,
          itemStyle: { color: theme.palette[0], borderColor: theme.bg, borderWidth: 2 },
          data: vals,
          label: {
            show: !!spec.labels, position: 'top', color: theme.subtext, fontSize: 11,
            formatter: function (p) { return U.fmtValue(p.value, spec.fmt); }
          }
        }
      ]
    };
  };

})();
