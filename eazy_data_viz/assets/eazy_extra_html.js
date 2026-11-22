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

  var AGG_LABELS = {
    sum: '求和', mean: '平均', count: '计数', unique: '去重数', max: '最大', min: '最小',
    median: '中位数'
  };

  // 汇总表：按 groupby.columns 分组，对 groupby.value 做 groupby.agg 聚合。
  // 聚合只发生在渲染层（rows 已经过联动筛选），不改变 dataStore 里的原始数据。
  // 联动和明细表完全一致：分组列可点（发 link），别的图筛它时行不变、只高亮命中的分组。
  function buildGroupedTable(spec, rows, kinds, state) {
    var g = spec.groupby || {};
    var dims = g.columns || [];
    var measure = g.value || null;
    var how = g.agg || (measure ? 'sum' : 'count');
    var limit = Math.min(spec.limit || 100, 500);
    var clickable = !!spec.link;
    var link = (spec.link && state && state.link && state.link.sourceId === spec.id)
      ? state.link : null;
    var groups = U.groupBy(rows, dims, measure, how);
    groups.sort(function (a, b) {
      var av = a.value, bv = b.value;
      if (av === null || av === undefined) return 1;
      if (bv === null || bv === undefined) return -1;
      return bv - av;
    });
    var numFmt = spec.fmt === 'compact' ? 'thousands' : spec.fmt;
    var html = '<div class="eazy-table-wrap"><table class="eazy-table"><thead><tr>';
    for (var c = 0; c < dims.length; c++) {
      html += '<th>' + U.esc(dims[c]) + '</th>';
    }
    var head = measure ? measure : '记录数';
    if (measure) head += '（' + (AGG_LABELS[how] || how) + '）';
    html += '<th class="num">' + U.esc(head) + '</th>';
    html += '</tr></thead><tbody>';
    for (var i = 0; i < groups.length && i < limit; i++) {
      var grp = groups[i];
      var rowHit = false;
      if (link) {
        var lconds = (link.conds && link.conds.length) ? link.conds
          : [{ dim: link.dim, value: link.value }];
        var matched = 0, hitAll = true;
        for (var lc = 0; lc < lconds.length; lc++) {
          var dimIdx = -1;
          for (var ld = 0; ld < dims.length; ld++) {
            if (String(lconds[lc].dim) === String(dims[ld])) { dimIdx = ld; break; }
          }
          if (dimIdx < 0) continue;                       // 这级不在表的分组列里，跳过
          matched += 1;
          if (U.catName(grp.keys[dimIdx]) !== String(lconds[lc].value)) { hitAll = false; break; }
        }
        rowHit = matched > 0 && hitAll;
      }
      html += '<tr' + (rowHit ? ' class="eazy-row-hit"' : '') + '>';
      for (var d = 0; d < dims.length; d++) {
        var kind = kinds[dims[d]];
        var cell = grp.keys[d];
        var cls = '', attrs = '';
        // 分组列就是维度列：可点，点了按「列 = 分组值」联动同组图表（再点取消）
        if (clickable && kind !== 'num' && kind !== 'time' && !isBlank(cell)) {
          var catv = U.catName(cell);
          cls = ' class="eazy-cell-link"';
          attrs = ' data-eazy-cell="' + U.esc(dims[d]) + '" data-eazy-val="' + U.esc(catv) + '"' +
            ' title="按「' + U.esc(dims[d]) + ' = ' + U.esc(catv) + '」联动同组图表（再点一次取消）"';
        }
        var text = (kind === 'time')
          ? U.esc(String(U.catName(cell)).slice(0, 16))
          : U.esc(U.catName(cell));
        html += '<td' + cls + attrs + '>' + text + '</td>';
      }
      var val = grp.value;
      var text2 = (val === null || val === undefined) ? '—' : U.fmtValue(val, numFmt);
      html += '<td class="num">' + text2 + '</td>';
      html += '</tr>';
    }
    html += '</tbody></table></div>';
    var more = '';
    if (groups.length > limit) {
      more = '共 ' + groups.length + ' 组，仅显示前 ' + limit + ' 组';
    } else {
      more = '共 ' + rows.length + ' 行，汇总为 ' + groups.length + ' 组';
    }
    if (rows.length > limit && groups.length <= limit) {
      more = '基于 ' + rows.length + ' 行汇总，共 ' + groups.length + ' 组';
    }
    html += '<div class="eazy-table-more">' + more + '</div>';
    return html;
  }

  H['table'] = function (spec, data, state, theme) {
    state = state || {};
    var rows = U.filteredRows(spec, data, state);
    var cols = spec.columns || [];
    if (spec.groupby) {
      if (!rows.length) return '<div class="eazy-empty">当前条件下没有数据</div>';
      return buildGroupedTable(spec, rows, data.kinds || {}, state);
    }
    if (!rows.length || !cols.length) return '<div class="eazy-empty">当前条件下没有数据</div>';
    var limit = Math.min(spec.limit || 100, 500);
    var kinds = data.kinds || {};
    var showIndex = spec.index === true;
    var showTotal = spec.total === true;
    var striped = spec.stripe !== false;  // 斑马纹默认开启，stripe=False 关闭
    var numFmt = spec.fmt === 'compact' ? 'thousands' : spec.fmt;
    // 数据条 / 合计只统计真正渲染出来的行，和 limit 后的表格内容保持一致
    var shown = rows.length > limit ? rows.slice(0, limit) : rows;
    // 联动：表格既可以「被图筛」（rows 已经过滤过），也可以「筛图」——
    // 后者说明这条联动是表格自己发起的，行不筛掉，只把命中的行高亮出来。
    var link = (spec.link && state.link && state.link.sourceId === spec.id) ? state.link : null;
    var clickable = !!spec.link;
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
      var rowHit = false;
      if (link) {
        var lconds2 = (link.conds && link.conds.length) ? link.conds
          : [{ dim: link.dim, value: link.value }];
        var anyHit = 0, allOk = true;
        for (var lc2 = 0; lc2 < lconds2.length; lc2++) {
          var ldim = lconds2[lc2].dim;
          if (!(ldim in shown[i])) continue;       // 这一级不在明细表里，跳过
          anyHit += 1;
          if (U.catName(shown[i][ldim]) !== String(lconds2[lc2].value)) { allOk = false; break; }
        }
        rowHit = anyHit > 0 && allOk;
      }
      html += '<tr' + (rowHit ? ' class="eazy-row-hit"' : '') + '>';
      if (showIndex) html += '<td class="eazy-col-idx">' + (i + 1) + '</td>';
      for (var k = 0; k < cols.length; k++) {
        var col = cols[k];
        var v = shown[i][col];
        var kind = kinds[col];
        var text = cellText(v, kind, numFmt);
        var cls = kind === 'num' ? 'num' : '';
        var style = '', attrs = '';
        // 维度列可点：点了按「列 = 单元格值」联动同组图表（数值/时间列点着没意义，不挂）
        if (clickable && kind !== 'num' && kind !== 'time' && !isBlank(v)) {
          var catv = U.catName(v);
          cls += ' eazy-cell-link';
          attrs = ' data-eazy-cell="' + U.esc(col) + '" data-eazy-val="' + U.esc(catv) + '"' +
            ' title="按「' + U.esc(col) + ' = ' + U.esc(catv) + '」联动同组图表（再点一次取消）"';
        }
        if (barColor[col] && kind === 'num' && typeof v === 'number' && isFinite(v)) {
          // 用 linear-gradient 在单元格背景上按「该列最大值」等比画条；
          // 数值文字包一层 span，压在色条上层（不改变右对齐）
          var pct = Math.max(0, Math.min(100, Math.abs(v) / barMax[col] * 100));
          cls += ' eazy-bar-cell';
          style = ' style="background-image:linear-gradient(90deg,' +
            barColor[col] + ' ' + pct.toFixed(1) + '%,transparent ' + pct.toFixed(1) + '%)"';
          text = '<span class="eazy-bar-val">' + text + '</span>';
        }
        html += '<td' + (cls ? ' class="' + cls + '"' : '') + style + attrs + '>' + text + '</td>';
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
    } else {
      html += '<div class="eazy-table-more">共 ' + rows.length + ' 行</div>';
    }
    return html;
  };

  // ------------------------------------------------------------------
  // wordcloud 词云
  //   不传 shape：原来的 CSS flex 排版（轻、快、老页面保持不变）
  //   传了 shape：canvas + 形状掩膜 + 螺旋装箱，词按图片/内置形状的轮廓排布
  // ------------------------------------------------------------------
  function wcItems(spec, data, state) {
    var rows = U.filteredRows(spec, data, state);
    var ndim = spec.roles.names || spec.roles.x;
    if (!ndim || !rows.length) return null;
    var groups = U.groupBy(rows, [ndim], spec.roles.value || spec.roles.y, spec.agg || 'sum');
    var items = [];
    for (var i = 0; i < groups.length; i++) {
      if (groups[i].value > 0) items.push({ name: groups[i].keys[0], value: groups[i].value });
    }
    items.sort(function (a, b) { return b.value - a.value; });
    return items.slice(0, spec.topN || 30);
  }

  H['wordcloud'] = function (spec, data, state, theme) {
    var items = wcItems(spec, data, state);
    if (!items || !items.length) return '<div class="eazy-empty">当前条件下没有数据</div>';
    if (spec.shape) {
      var h = parseInt(spec.height, 10) || 360;
      return '<div class="eazy-wc-wrap" style="height:' + h + 'px">' +
        '<canvas class="eazy-wc-canvas"></canvas></div>';
    }
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

  // 按形状名画一条闭合路径：统一在「单位圆」坐标系里画，再按画布宽高拉伸，
  // 这样 circle 会变成椭圆、star 会铺满整张卡片 —— 词云要的是铺满，不是留白。
  function wcShapePath(ctx, name, W, H) {
    var hw = W / 2, hh = H / 2, i, a, rr, px, py;
    ctx.save();
    ctx.translate(hw, hh);
    ctx.scale(hw * 0.99, hh * 0.99);
    ctx.beginPath();
    if (name === 'square') {
      ctx.rect(-1, -1, 2, 2);
    } else if (name === 'diamond') {
      ctx.moveTo(0, -1); ctx.lineTo(1, 0); ctx.lineTo(0, 1); ctx.lineTo(-1, 0); ctx.closePath();
    } else if (name === 'triangle') {
      ctx.moveTo(0, -1); ctx.lineTo(0.96, 0.72); ctx.lineTo(-0.96, 0.72); ctx.closePath();
    } else if (name === 'star') {
      for (i = 0; i < 10; i++) {
        a = -Math.PI / 2 + i * Math.PI / 5;
        rr = (i % 2 === 0) ? 1 : 0.45;
        px = Math.cos(a) * rr; py = Math.sin(a) * rr;
        if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      }
      ctx.closePath();
    } else if (name === 'pentagon') {
      for (i = 0; i < 5; i++) {
        a = -Math.PI / 2 + i * Math.PI * 2 / 5;
        px = Math.cos(a); py = Math.sin(a);
        if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      }
      ctx.closePath();
    } else if (name === 'heart') {
      ctx.moveTo(0, 0.95);
      ctx.bezierCurveTo(-1.45, -0.05, -0.6, -1.15, 0, -0.4);
      ctx.bezierCurveTo(0.6, -1.15, 1.45, -0.05, 0, 0.95);
      ctx.closePath();
    } else if (name === 'cardioid') {
      for (i = 0; i <= 240; i++) {
        a = i / 240 * Math.PI * 2;
        rr = 0.62 * (1 - Math.cos(a));
        px = Math.sin(a) * rr;
        py = 0.25 - Math.cos(a) * rr;
        if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      }
      ctx.closePath();
    } else {
      ctx.arc(0, 0, 1, 0, Math.PI * 2);
    }
    ctx.restore();
  }

  // 建掩膜：内置形状直接描路径；图片按 alpha（有透明通道）或亮度（白底图）判定
  function wcBuildMask(shape, W, H, done) {
    var MW = 260, MH = Math.max(80, Math.round(MW * H / W));
    var mc = document.createElement('canvas');
    mc.width = MW; mc.height = MH;
    var mctx = mc.getContext('2d');
    var isImage = shape && shape.type === 'image' && shape.src;
    function finish(imgEl) {
      var data = mctx.getImageData(0, 0, MW, MH).data;
      var totalPx = MW * MH, ii, nAlpha = 0, nDark = 0, nLight = 0;
      var mode = 'alpha';
      if (isImage) {
        for (ii = 0; ii < totalPx; ii++) {
          if (data[ii * 4 + 3] < 128) continue;
          nAlpha += 1;
          var lum0 = data[ii * 4] * 0.299 + data[ii * 4 + 1] * 0.587 + data[ii * 4 + 2] * 0.114;
          if (lum0 < 246) nDark += 1;
          if (lum0 > 12) nLight += 1;
        }
        // 深色形状 + 白底 → 认暗像素；浅色/白色 logo → 认亮像素；透明底 → 认 alpha
        if (nAlpha && nDark >= totalPx * 0.02 && nDark < nAlpha * 0.98) mode = 'dark';
        else if (nAlpha && nLight >= totalPx * 0.02) mode = 'light';
        else if (nAlpha) mode = 'light';
      }
      done(function inside(px, py) {
        var x = px | 0, y = py | 0;
        if (x < 0 || y < 0 || x >= MW || y >= MH) return false;
        var i = (y * MW + x) * 4;
        if (data[i + 3] < 128) return false;
        if (!isImage) return true;
        var lum = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
        if (mode === 'dark') return lum < 246;
        return lum > 12;
      }, MW, MH, imgEl);
    }
    if (isImage) {
      var img = new Image();
      img.onload = function () {
        var s = Math.min(MW / img.width, MH / img.height) * 0.98;
        mctx.clearRect(0, 0, MW, MH);
        mctx.drawImage(img, (MW - img.width * s) / 2, (MH - img.height * s) / 2,
          img.width * s, img.height * s);
        finish(img);
      };
      img.onerror = function () { mctx.clearRect(0, 0, MW, MH); finish(null); };
      img.src = shape.src;
      return;
    }
    mctx.fillStyle = '#fff';
    wcShapePath(mctx, (shape && shape.name) || 'circle', MW, MH);
    mctx.fill();
    finish();
  }

  function wcFont(size, weight) {
    return (weight || 600) + ' ' + size + 'px "Inter", "Noto Sans SC", "PingFang SC", ' +
      'system-ui, -apple-system, "Segoe UI", sans-serif';
  }

  // 螺旋装箱：从中心往外找第一个「完全落在形状内、且不和已放文字重叠」的位置
  function wcDraw(cv, items, shape, theme) {
    var W = Math.max(120, cv.clientWidth || (cv.parentNode && cv.parentNode.clientWidth) || 600);
    var H = Math.max(80, cv.clientHeight || (cv.parentNode && cv.parentNode.clientHeight) || 360);
    var dpr = window.devicePixelRatio || 1;
    cv.width = Math.round(W * dpr);
    cv.height = Math.round(H * dpr);
    cv.style.width = W + 'px';
    cv.style.height = H + 'px';
    var ctx = cv.getContext('2d');
    cv.__wcBoxes = [];   // 自检脚本读它查重叠，重画时清空
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    if (!ctx.measureText) return;

    wcBuildMask(shape, W, H, function (inside, MW, MH, imgEl) {
      // 淡淡地铺一层形状底影：词铺不满的尖角/镂空也能看出形状
      ctx.save();
      ctx.globalAlpha = 0.1;
      ctx.fillStyle = theme.line || theme.axis || theme.text;
      if (imgEl) {
        var sc = Math.min(W / imgEl.width, H / imgEl.height) * 0.98;
        var iw = imgEl.width * sc, ih = imgEl.height * sc;
        ctx.drawImage(imgEl, (W - iw) / 2, (H - ih) / 2, iw, ih);
      } else {
        wcShapePath(ctx, (shape && shape.name) || 'circle', W, H);
        ctx.fill();
      }
      ctx.restore();
      var cell = 2, GW = Math.ceil(MW / cell), GH = Math.ceil(MH / cell);
      var taken = new Uint8Array(GW * GH);
      var insideCells = 0, gx, gy;
      for (gy = 0; gy < GH; gy++) {
        for (gx = 0; gx < GW; gx++) {
          if (inside(gx * cell + 1, gy * cell + 1)) { insideCells += 1; }
        }
      }
      if (!insideCells) return;
      // 形状体积 → 每个词的面积份额：让所有词合起来大约铺满形状的 62%
      var cellCss = (W / MW) * cell;
      var budget = insideCells * cellCss * cellCss * 0.45;
      var maxV = items[0].value || 1;
      var weights = [], wsum = 0, i;
      for (i = 0; i < items.length; i++) {
        var wgt = Math.pow(Math.max(items[i].value, maxV * 0.01) / maxV, 0.45);
        weights.push(wgt);
        wsum += wgt;
      }
      var maxSize = Math.min(H * 0.22, W * 0.17);
      var minSize = Math.max(8, Math.min(14, maxSize * 0.22));

      function sizeOf(idx, shrink) {
        var len = Math.max(1, String(items[idx].name).length);
        var area = budget * weights[idx] / Math.max(0.0001, wsum);
        // 文字面积 ≈ 0.58 × 字号² × 字数（汉字近似方块，英文更窄，取折中）
        var size = Math.sqrt(area / (0.58 * len));
        // 第一轮保可读性（不低于 minSize）；重试轮允许更小，避免「词被丢掉」
        var floor2 = (shrink === undefined || shrink >= 0.6) ? minSize : Math.max(7, minSize * 0.55);
        return Math.max(floor2, Math.min(maxSize, size * (shrink || 1)));
      }

      var placed = 0, doneIdx = {};
      function tryPlace(idx, shrink) {
        var nm = String(items[idx].name);
        if (!nm) return false;
        return wcPlace(ctx, nm, sizeOf(idx, shrink), taken, inside, cell, GW, GH, MW, MH, W, H,
          theme.palette[idx % theme.palette.length], idx);
      }
      // 第一轮：按面积份额一次到位；放不下就缩到 0.62 再试
      for (i = 0; i < items.length; i++) {
        if (tryPlace(i, 1) || tryPlace(i, 0.62)) { placed += 1; doneIdx[i] = 1; }
      }
      // 第二轮：还没进形状的，缩到 0.42 / 0.3 再抢一次空位
      for (i = 0; i < items.length; i++) {
        if (doneIdx[i]) continue;
        if (tryPlace(i, 0.42) || tryPlace(i, 0.3)) { placed += 1; doneIdx[i] = 1; }
      }
      // 第三轮：词多、形状小的时候再降两档，让每个词都能露脸（不再丢词）
      for (i = 0; i < items.length; i++) {
        if (doneIdx[i]) continue;
        if (tryPlace(i, 0.24) || tryPlace(i, 0.18) || tryPlace(i, 0.14)) {
          placed += 1; doneIdx[i] = 1;
        }
      }
      cv.__wcPlaced = placed;
      cv.__wcItems = items.length;
      cv.setAttribute('data-wc', items.length + '/' + placed);
      // 一个词都放不下时兜底：把最大的词硬画在中心
      if (!placed) {
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = theme.text;
        ctx.font = wcFont(Math.max(12, minSize), 600);
        ctx.fillText(String(items[0].name), W / 2, H / 2);
      }
    });
  }

  function wcPlace(ctx, name, size, taken, inside, cell, GW, GH, MW, MH, W, H, color, order) {
    var hCss = size * 1.3;
    ctx.font = wcFont(size, 600);
    var wRaw = ctx.measureText(name).width;
    var variants = [
      { rot: 0, w: wRaw, h: hCss },
      { rot: -Math.PI / 2, w: hCss, h: wRaw }
    ];
    for (var v = 0; v < variants.length; v++) {
      var box = variants[v];
      // 每边多留若干格当行距：字越大留得越宽，避免笔画视觉上贴在一起
      var pad = size >= 26 ? 3 : (size >= 12 ? 2 : 1);
      var cw = Math.max(1, Math.ceil(box.w * MW / W / cell)) + pad;
      var ch = Math.max(1, Math.ceil(box.h * MH / H / cell)) + pad;
      var cxg = Math.floor(GW / 2), cyg = Math.floor(GH / 2);
      var maxR = Math.sqrt(GW * GW + GH * GH);
      for (var step = 0; step < 9000; step++) {
        var r = step * 0.9;
        if (r > maxR) break;
        var a = step * 0.35 + (order % 7) * 0.6;
        var gx = Math.round(cxg + Math.cos(a) * r * 1.18 - cw / 2);
        var gy = Math.round(cyg + Math.sin(a) * r - ch / 2);
        if (gx < 0 || gy < 0 || gx + cw > GW || gy + ch > GH) continue;
        var fits = true;
        for (var yy = gy; yy < gy + ch && fits; yy++) {
          for (var xx = gx; xx < gx + cw; xx++) {
            var gi = yy * GW + xx;
            if (taken[gi]) { fits = false; break; }
            if (!inside(xx * cell + 1, yy * cell + 1)) { fits = false; break; }
          }
        }
        if (!fits) continue;
        for (var y2 = gy; y2 < gy + ch; y2++) {
          for (var x2 = gx; x2 < gx + cw; x2++) taken[y2 * GW + x2] = 1;
        }
        var px = (gx + cw / 2) * cell, py = (gy + ch / 2) * cell;
        ctx.save();
        ctx.translate(px * W / MW, py * H / MH);
        ctx.rotate(box.rot);
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.92;
        ctx.font = wcFont(size, 600);
        ctx.fillText(name, 0, 0);
        ctx.restore();
        // 调试/自检用：记下每个词的实际外框（自检脚本会读这个数组查重叠）
        var reg = ctx.canvas.__wcBoxes || (ctx.canvas.__wcBoxes = []);
        reg.push({ name: name, x: px * W / MW - box.w / 2, y: py * H / MH - box.h / 2,
                   w: box.w, h: box.h, rot: box.rot });
        return true;
      }
    }
    return false;
  }

  var WC_HOOKS = (EazyViz.htmlHooks = EazyViz.htmlHooks || {});
  WC_HOOKS['wordcloud'] = function (c) {
    var spec = c.spec;
    if (!spec.shape) return;
    var cv = c.el.querySelector('canvas.eazy-wc-canvas');
    if (!cv) return;
    var items = wcItems(spec, c.data, c.state);
    if (!items || !items.length) return;
    wcDraw(cv, items, spec.shape, c.theme);
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
