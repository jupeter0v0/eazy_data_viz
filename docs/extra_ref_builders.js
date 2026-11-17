/*!
 * eazy_data_viz 扩展图表 —— 参考实现（示例，供其他扩展文件模仿写法）
 *
 * 注册方式：EazyViz.extraBuilders['<type>'] = function (spec, data, state, theme) -> ECharts option
 * 可用工具：U = EazyViz.core.util（见 docs/EXTRA_CHARTS.md）
 *
 * 本文件在 eazy.js 之后加载（可选）；实际产品里的同名图表由 eazy_extra_a.js 提供。
 */
(function () {
  'use strict';
  if (typeof window === 'undefined' || !window.EazyViz) return;

  var EazyViz = window.EazyViz;
  var U = EazyViz.core.util;
  var B = EazyViz.extraBuilders;

  function catsSorted(records, xdim, spec, data) {
    var ranker = U.catRanker(data, xdim);
    if (spec.sort === 'x') records.sort(function (a, b) {
      if (ranker) return ranker(a.name, b.name);
      return U.compareCatX(a.name, b.name);
    });
    else if (spec.sort === 'asc') records.sort(function (a, b) { return a.value - b.value; });
    else if (spec.sort === 'desc') records.sort(function (a, b) { return b.value - a.value; });
    return records;
  }

  // ------------------------------------------------------------------
  // waterfall 瀑布图：增量 + 累计
  // ------------------------------------------------------------------
  B['waterfall'] = function (spec, data, state, theme) {
    var rows = U.filteredRows(spec, data, state);
    var xdim = U.currentXDim(spec, state);
    if (!xdim || !rows.length) return U.emptyOption(theme);
    var ycol = spec.roles.y;
    var groups = U.groupBy(rows, [xdim], ycol, spec.agg || 'sum');
    var recs = [];
    for (var i = 0; i < groups.length; i++) {
      recs.push({ name: groups[i].keys[0], value: groups[i].value || 0 });
    }
    catsSorted(recs, xdim, spec, data);

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

    function tipHtml(idx) {
      var total = spec.total ? cats.length - 1 : cats.length;
      if (idx >= total) return '<b>合计</b><br/>' + U.fmtValue(cums[idx], spec.fmt);
      var d = cums[idx] - (idx ? cums[idx - 1] : 0);
      return '<b>' + U.esc(cats[idx]) + '</b><br/>增量：' + U.fmtValue(d, spec.fmt) +
        '<br/>累计：' + U.fmtValue(cums[idx], spec.fmt);
    }

    var idxMap = {};
    for (var j = 0; j < cats.length; j++) idxMap[cats[j]] = j;

    return {
      grid: U.makeGrid(theme, { legend: false, zoom: false }),
      tooltip: (function () {
        var t = U.tooltipBox(theme);
        t.trigger = 'axis';
        t.axisPointer = { type: 'shadow' };
        t.formatter = function (ps) {
          if (!ps || !ps.length) return '';
          var idx = idxMap[ps[0].name];
          return idx === undefined ? '' : tipHtml(idx);
        };
        return t;
      })(),
      xAxis: (function () {
        var a = U.makeCategoryAxis(spec, cats, theme);
        return U.setAxisName(a, U.axisTitle(spec.xtitle, spec.roles.x), theme, true);
      })(),
      yAxis: (function () {
        var a = U.makeValueAxis(spec, theme, spec.ylim);
        return U.setAxisName(a, U.axisTitle(spec.ytitle, spec.roles.y), theme, false);
      })(),
      series: [
        {
          name: 'base', type: 'bar', stack: 'wf', silent: true,
          itemStyle: { color: 'transparent' }, emphasis: { disabled: true },
          data: bases
        },
        {
          name: U.axisTitle(spec.ytitle, spec.roles.y), type: 'bar', stack: 'wf',
          barMaxWidth: 34,
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
  // bullet 子弹图：实际值 vs 目标
  // ------------------------------------------------------------------
  B['bullet'] = function (spec, data, state, theme) {
    var rows = U.filteredRows(spec, data, state);
    var xdim = U.currentXDim(spec, state);
    if (!xdim || !rows.length) return U.emptyOption(theme);
    var ycol = spec.roles.y;
    var groups = U.groupBy(rows, [xdim], ycol, spec.agg || 'sum');
    var recs = [];
    for (var i = 0; i < groups.length; i++) {
      recs.push({ name: groups[i].keys[0], value: groups[i].value || 0 });
    }
    catsSorted(recs, xdim, spec, data);

    var cats = [], actual = [], targets = [], maxVals = [];
    var tcol = spec.roles.target;
    var tMap = {};
    if (tcol && U.hasCol(data, tcol)) {
      var tg = U.groupBy(rows, [xdim], tcol, spec.agg || 'sum');
      for (var k = 0; k < tg.length; k++) tMap[tg[k].keys[0]] = tg[k].value;
    }
    for (var j = 0; j < recs.length; j++) {
      var t = tMap[recs[j].name];
      if (t === undefined || t === null) t = spec.targetValue;
      t = Number(t) || 0;
      cats.push(recs[j].name);
      actual.push(recs[j].value || 0);
      targets.push(t);
      if (targets[j] < 0) targets[j] = 0;
      maxVals.push(Math.max(recs[j].value || 0, t) * 1.08);
    }

    return {
      grid: U.makeGrid(theme, { legend: false }),
      tooltip: (function () {
        var t = U.tooltipBox(theme);
        t.trigger = 'axis';
        t.axisPointer = { type: 'shadow' };
        t.formatter = function (ps) {
          if (!ps || !ps.length) return '';
          var idx = ps[0].dataIndex;
          var a = actual[idx] || 0, tg = targets[idx] || 0;
          var rate = tg ? (a / tg * 100) : null;
          return '<b>' + U.esc(cats[idx]) + '</b><br/>实际：' + U.fmtValue(a, spec.fmt) +
            '<br/>目标：' + U.fmtValue(tg, spec.fmt) +
            (rate === null ? '' : '<br/>达成率：' + rate.toFixed(1) + '%');
        };
        return t;
      })(),
      xAxis: U.makeValueAxis(spec, theme, spec.xlim),
      yAxis: (function () {
        var a = U.makeCategoryAxis(spec, cats, theme);
        a.inverse = true;
        return U.setAxisName(a, U.axisTitle(spec.xtitle, spec.roles.x), theme, false, 14);
      })(),
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
          name: '目标', type: 'scatter', z: 4, symbol: 'rect',
          symbolSize: [3, 18],
          itemStyle: { color: theme.text },
          data: targets
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
    catsSorted(recs, xdim, spec, data);
    var cats = [], vals = [];
    for (var k = 0; k < recs.length; k++) { cats.push(recs[k].name); vals.push(recs[k].value); }

    return {
      grid: U.makeGrid(theme, { legend: false }),
      tooltip: (function () {
        var t = U.tooltipBox(theme);
        t.trigger = 'axis';
        t.axisPointer = { type: 'shadow' };
        return t;
      })(),
      xAxis: (function () {
        var a = U.makeCategoryAxis(spec, cats, theme);
        return U.setAxisName(a, U.axisTitle(spec.xtitle, spec.roles.x), theme, true);
      })(),
      yAxis: (function () {
        var a = U.makeValueAxis(spec, theme, spec.ylim);
        return U.setAxisName(a, U.axisTitle(spec.ytitle, spec.roles.y), theme, false);
      })(),
      series: [
        {
          name: U.axisTitle(spec.ytitle, spec.roles.y), type: 'bar', barWidth: 2,
          itemStyle: { color: theme.palette[0] }, data: vals
        },
        {
          type: 'scatter', symbolSize: 9, z: 3,
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
