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
  // table 明细表（中国式报表：序号 / 合计 / 数据条 / 斑马纹 / 固定首列）
  // ------------------------------------------------------------------
  // 空值占位符：统一显示「−」，不要出现 None / null
  var TABLE_EMPTY = '−';

  function isBlank(v) {
    return v === null || v === undefined || v === '';
  }

  // 颜色加透明度（hex / rgb() / rgba() 都支持），用于数据条底色
  function fadeColor(color, alpha) {
    var s = String(color || '').replace(/^\s+|\s+$/g, '');
    if (s.charAt(0) === '#') {
      var c = hexRgb(s);
      return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + alpha + ')';
    }
    var m = /^rgba?\(([^)]+)\)$/.exec(s);
    if (m) {
      var p = m[1].split(',');
      if (p.length >= 3) {
        return 'rgba(' + p[0].replace(/^\s+|\s+$/g, '') + ',' +
          p[1].replace(/^\s+|\s+$/g, '') + ',' + p[2].replace(/^\s+|\s+$/g, '') +
          ',' + alpha + ')';
      }
    }
    return s;
  }

  // 单元格文本：空值 → 「−」；数值列统一 thousands；时间列截到分钟
  function cellText(v, kind, numFmt) {
    if (isBlank(v)) return TABLE_EMPTY;
    if (kind === 'num' && typeof v === 'number') return U.fmtValue(v, numFmt);
    if (kind === 'time') return U.esc(String(U.catName(v)).slice(0, 16));
    return U.esc(U.catName(v));
  }

  // spec.bar 归一化成列名数组（Python 已校验，这里再兜一次底）
  function barColumns(spec, cols, kinds) {
    var bar = spec.bar;
    var out = [];
    if (bar === true) {
      for (var i = 0; i < cols.length; i++) {
        if (kinds[cols[i]] === 'num') return [cols[i]];
      }
      return out;
    }
    if (typeof bar === 'string') bar = [bar];
    if (!bar || !bar.length) return out;
    for (var j = 0; j < bar.length; j++) {
      if (bar[j] && out.indexOf(bar[j]) < 0 && kinds[bar[j]] === 'num') {
        out.push(bar[j]);
      }
    }
    return out;
  }

  H['table'] = function (spec, data, state, theme) {
    var rows = U.filteredRows(spec, data, state);
    var cols = spec.columns || [];
    if (!rows.length || !cols.length) return '<div class="eazy-empty">当前条件下没有数据</div>';
    var limit = Math.min(spec.limit || 100, 500);
    var kinds = data.kinds || {};
    var showIndex = spec.index === true;
    var showTotal = spec.total === true;
    var striped = spec.stripe !== false;  // 斑马纹默认开启，stripe=False 关闭
    var numFmt = spec.fmt === 'compact' ? 'thousands' : spec.fmt;
    // 数据条 / 合计只统计真正渲染出来的行，和 limit 后的表格内容保持一致
    var shown = rows.length > limit ? rows.slice(0, limit) : rows;
    var barCols = barColumns(spec, cols, kinds);
    var barColor = {}, barMax = {}, b, m;
    for (b = 0; b < barCols.length; b++) {
      var bc = barCols[b];
      // 依次取主题配色；深色主题下加深一些，保证条和文字都看得清
      barColor[bc] = fadeColor(theme.palette[b % theme.palette.length],
        theme.name === 'dark' ? 0.34 : 0.22);
      var mx = 0;
      for (m = 0; m < shown.length; m++) {
        var mv = shown[m][bc];
        if (typeof mv === 'number' && isFinite(mv)) mx = Math.max(mx, Math.abs(mv));
      }
      barMax[bc] = mx || 1;
    }

    var html = '<div class="eazy-table-wrap"><table class="eazy-table' +
      (striped ? ' eazy-table-stripe' : '') + '"><thead><tr>';
    if (showIndex) html += '<th class="eazy-col-idx">序号</th>';
    for (var c = 0; c < cols.length; c++) {
      var numCol = kinds[cols[c]] === 'num' || kinds[cols[c]] === 'time';
      html += '<th' + (numCol ? ' class="num"' : '') + '>' + U.esc(cols[c]) + '</th>';
    }
    html += '</tr></thead><tbody>';
    for (var i = 0; i < shown.length; i++) {
      html += '<tr>';
      if (showIndex) html += '<td class="eazy-col-idx">' + (i + 1) + '</td>';
      for (var k = 0; k < cols.length; k++) {
        var col = cols[k];
        var v = shown[i][col];
        var kind = kinds[col];
        var text = cellText(v, kind, numFmt);
        var cls = kind === 'num' ? 'num' : '';
        var style = '';
        if (barColor[col] && kind === 'num' && typeof v === 'number' && isFinite(v)) {
          // 用 linear-gradient 在单元格背景上按「该列最大值」等比画条；
          // 数值文字包一层 span，压在色条上层（不改变右对齐）
          var pct = Math.max(0, Math.min(100, Math.abs(v) / barMax[col] * 100));
          cls += ' eazy-bar-cell';
          style = ' style="background-image:linear-gradient(90deg,' +
            barColor[col] + ' ' + pct.toFixed(1) + '%,transparent ' + pct.toFixed(1) + '%)"';
          text = '<span class="eazy-bar-val">' + text + '</span>';
        }
        html += '<td' + (cls ? ' class="' + cls + '"' : '') + style + '>' + text + '</td>';
      }
      html += '</tr>';
    }
    html += '</tbody>';
    if (showTotal) {
      // 合计行：放在 tfoot，加粗 + 顶部双线 + 浅底色（样式见 render.py 的 _CSS）
      html += '<tfoot><tr class="eazy-table-total">';
      if (showIndex) html += '<td class="eazy-col-idx eazy-total-label">合计</td>';
      for (var t = 0; t < cols.length; t++) {
        var tcol = cols[t];
        // 没有序号列时，「合计」标签占用第一列（通常是维度列）；
        // 若第一列本身就是数值列，标签与该列合计同格显示，避免这一列的合计被吞掉
        var firstIsNum = (!showIndex && t === 0 && kinds[tcol] === 'num');
        if (!showIndex && t === 0 && !firstIsNum) {
          html += '<td class="eazy-total-label">合计</td>';
          continue;
        }
        if (kinds[tcol] !== 'num') {
          html += '<td></td>';
          continue;
        }
        var sum = 0, cnt = 0;
        for (var s = 0; s < shown.length; s++) {
          var sv = shown[s][tcol];
          if (typeof sv === 'number' && isFinite(sv)) { sum += sv; cnt += 1; }
        }
        html += '<td class="num eazy-total-num' + (firstIsNum ? ' eazy-total-first' : '') + '">' +
          (firstIsNum && cnt ? '<span class="eazy-total-tag">合计</span>' : '') +
          (cnt ? U.fmtValue(sum, numFmt) : TABLE_EMPTY) + '</td>';
      }
      html += '</tr></tfoot>';
    }
    html += '</table></div>';
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
