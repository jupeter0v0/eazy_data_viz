/*!
 * eazy_data_viz 扩展图表 · HTML 类（不走 ECharts）：progress / tile / table / wordcloud / group_kpi
 * 注册到 EazyViz.htmlBuilders['type'] = function (spec, data, state, theme) -> html string
 * 样式在 render.py 的 Material 样式中定义（.eazy-* 类）。
 */
(function () {
  'use strict';
  if (typeof window === 'undefined' || !window.EazyViz) return;

  var EazyViz = window.EazyViz;
  var U = EazyViz.core.util;
  var H = EazyViz.htmlBuilders;

  // 颜色插值：heat 色阶取 t ∈ [0,1]
  function heatColor(theme, t) {
    var heat = theme.heat || ['#e8f0fe', '#1967d2'];
    if (t <= 0) return heat[0];
    if (t >= 1) return heat[heat.length - 1];
    var pos = t * (heat.length - 1);
    var i = Math.floor(pos), frac = pos - i;
    var a = hexRgb(heat[i]), b = hexRgb(heat[i + 1]);
    return 'rgb(' + Math.round(a[0] + (b[0] - a[0]) * frac) + ',' +
      Math.round(a[1] + (b[1] - a[1]) * frac) + ',' +
      Math.round(a[2] + (b[2] - a[2]) * frac) + ')';
  }

  function hexRgb(hex) {
    var s = String(hex).replace('#', '');
    if (s.length === 3) s = s[0] + s[0] + s[1] + s[1] + s[2] + s[2];
    var n = parseInt(s, 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }

  function isDarkColor(rgbStr) {
    var m = /rgba?\(([^)]+)\)/.exec(rgbStr);
    if (!m) return false;
    var p = m[1].split(',').map(function (x) { return parseFloat(x); });
    return (p[0] * 0.299 + p[1] * 0.587 + p[2] * 0.114) < 145;
  }

  // ------------------------------------------------------------------
  // progress 进度条列表
  // ------------------------------------------------------------------
  H['progress'] = function (spec, data, state, theme) {
    var rows = U.filteredRows(spec, data, state);
    var xdim = U.currentXDim(spec, state);
    if (!xdim || !rows.length) return '<div class="eazy-empty">当前条件下没有数据</div>';
    var groups = U.groupBy(rows, [xdim], spec.roles.y, spec.agg || 'sum');
    var pairs = [];
    for (var i = 0; i < groups.length; i++) {
      pairs.push({ name: groups[i].keys[0], value: groups[i].value || 0 });
    }
    if (spec.sort === 'desc') pairs.sort(function (a, b) { return b.value - a.value; });
    else if (spec.sort === 'asc') pairs.sort(function (a, b) { return a.value - b.value; });
    else if (spec.sort === 'x') {
      var ranker = U.catRanker(data, xdim);
      pairs.sort(function (a, b) { return ranker ? ranker(a.name, b.name) : U.compareCatX(a.name, b.name); });
    }
    var limit = spec.topN || 10;
    if (pairs.length > limit) pairs = pairs.slice(0, limit);
    var maxV = spec.maxValue || 0;
    if (!maxV) {
      for (var k = 0; k < pairs.length; k++) maxV = Math.max(maxV, pairs[k].value);
    }
    if (!maxV) maxV = 1;

    var html = '<div class="eazy-progress-list">';
    for (var j = 0; j < pairs.length; j++) {
      var pct = Math.max(0, Math.min(100, pairs[j].value / maxV * 100));
      var color = theme.palette[j % theme.palette.length];
      html += '<div class="eazy-progress-row">' +
        '<div class="eazy-progress-head"><span class="name">' + U.esc(pairs[j].name) + '</span>' +
        '<span class="val">' + U.fmtValue(pairs[j].value, spec.fmt) +
        (maxV ? ' · ' + pct.toFixed(0) + '%' : '') + '</span></div>' +
        '<div class="eazy-progress-track"><div class="eazy-progress-fill" style="width:' +
        pct.toFixed(1) + '%;background:' + color + '"></div></div></div>';
    }
    return html + '</div>';
  };

  // ------------------------------------------------------------------
  // tile 瓦片图（方块按数值深浅着色）
  // ------------------------------------------------------------------
  H['tile'] = function (spec, data, state, theme) {
    var rows = U.filteredRows(spec, data, state);
    var ndim = spec.roles.names || spec.roles.x;
    if (!ndim || !rows.length) return '<div class="eazy-empty">当前条件下没有数据</div>';
    var groups = U.groupBy(rows, [ndim], spec.roles.value || spec.roles.y, spec.agg || 'sum');
    var items = [];
    for (var i = 0; i < groups.length; i++) {
      items.push({ name: groups[i].keys[0], value: groups[i].value || 0 });
    }
    items.sort(function (a, b) { return b.value - a.value; });
    var minV = items.length ? items[items.length - 1].value : 0;
    var maxV = items.length ? items[0].value : 0;
    var span = (maxV - minV) || 1;
    var html = '<div class="eazy-tile-grid">';
    for (var j = 0; j < items.length; j++) {
      var t = (items[j].value - minV) / span;
      var bg = heatColor(theme, 0.15 + t * 0.85);
      var fg = isDarkColor(bg) ? '#ffffff' : theme.text;
      html += '<div class="eazy-tile" style="background:' + bg + ';color:' + fg + '">' +
        '<span class="t-name">' + U.esc(items[j].name) + '</span>' +
        '<span class="t-val">' + U.fmtValue(items[j].value, spec.fmt) + '</span></div>';
    }
    return html + '</div>';
  };

  // ------------------------------------------------------------------
  // table 明细表
  // ------------------------------------------------------------------
  H['table'] = function (spec, data, state, theme) {
    var rows = U.filteredRows(spec, data, state);
    var cols = spec.columns || [];
    if (!rows.length || !cols.length) return '<div class="eazy-empty">当前条件下没有数据</div>';
    var limit = Math.min(spec.limit || 100, 500);
    var kinds = data.kinds || {};
    var html = '<div class="eazy-table-wrap"><table class="eazy-table"><thead><tr>';
    for (var c = 0; c < cols.length; c++) {
      var numCol = kinds[cols[c]] === 'num' || kinds[cols[c]] === 'time';
      html += '<th' + (numCol ? ' class="num"' : '') + '>' + U.esc(cols[c]) + '</th>';
    }
    html += '</tr></thead><tbody>';
    for (var i = 0; i < rows.length && i < limit; i++) {
      html += '<tr>';
      for (var k = 0; k < cols.length; k++) {
        var v = rows[i][cols[k]];
        var kind = kinds[cols[k]];
        var text;
        if (kind === 'num' && typeof v === 'number') text = U.fmtValue(v, spec.fmt === 'compact' ? 'thousands' : spec.fmt);
        else if (kind === 'time') text = String(U.catName(v)).slice(0, 16);
        else text = U.esc(U.catName(v));
        html += '<td' + (kind === 'num' ? ' class="num"' : '') + '>' + text + '</td>';
      }
      html += '</tr>';
    }
    html += '</tbody></table></div>';
    if (rows.length > limit) {
      html += '<div class="eazy-table-more">共 ' + rows.length + ' 行，仅显示前 ' + limit + ' 行</div>';
    }
    return html;
  };

  // ------------------------------------------------------------------
  // wordcloud 词云（纯 CSS 排版）
  // ------------------------------------------------------------------
  H['wordcloud'] = function (spec, data, state, theme) {
    var rows = U.filteredRows(spec, data, state);
    var ndim = spec.roles.names || spec.roles.x;
    if (!ndim || !rows.length) return '<div class="eazy-empty">当前条件下没有数据</div>';
    var groups = U.groupBy(rows, [ndim], spec.roles.value || spec.roles.y, spec.agg || 'sum');
    var items = [];
    for (var i = 0; i < groups.length; i++) {
      if (groups[i].value > 0) items.push({ name: groups[i].keys[0], value: groups[i].value });
    }
    items.sort(function (a, b) { return b.value - a.value; });
    items = items.slice(0, spec.topN || 30);
    if (!items.length) return '<div class="eazy-empty">当前条件下没有数据</div>';
    var maxV = items[0].value, minV = items[items.length - 1].value;
    var span = (maxV - minV) || 1;
    var html = '<div class="eazy-wc">';
    for (var j = 0; j < items.length; j++) {
      var t = (items[j].value - minV) / span;
      var size = 13 + Math.round(t * 17);
      var color = theme.palette[j % theme.palette.length];
      html += '<span class="eazy-wc-word" style="font-size:' + size + 'px;color:' + color +
        ';opacity:' + (0.72 + t * 0.28).toFixed(2) + '">' + U.esc(items[j].name) + '</span>';
    }
    return html + '</div>';
  };

  // ------------------------------------------------------------------
  // group_kpi 指标卡片组
  // ------------------------------------------------------------------
  H['group_kpi'] = function (spec, data, state, theme) {
    var items = spec.items || [];
    if (!items.length) return '<div class="eazy-empty">没有指标</div>';
    var html = '<div class="eazy-kpi-group">';
    for (var i = 0; i < items.length; i++) {
      var it = items[i];
      var delta = (it.delta === null || it.delta === undefined) ? null : Number(it.delta);
      var dcls = delta === null ? '' : (delta >= 0 ? ' up' : ' down');
      html += '<div class="eazy-metric">' +
        '<div class="m-label">' + U.esc(it.label || '') + '</div>' +
        '<div class="m-value">' + U.fmtValue(it.value, it.fmt || 'compact') +
        (it.unit ? '<span class="m-unit">' + U.esc(it.unit) + '</span>' : '') + '</div>' +
        (delta === null ? '' :
          '<div class="m-delta' + dcls + '">' + (delta >= 0 ? '▲' : '▼') + ' ' +
          Math.abs(delta * 100).toFixed(1) + '%</div>') +
        (it.hint ? '<div class="m-hint">' + U.esc(it.hint) + '</div>' : '') +
        '</div>';
    }
    return html + '</div>';
  };

})();
