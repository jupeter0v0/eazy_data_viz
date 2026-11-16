/*!
 * eazy_data_viz runtime 1.0.0
 * 一套零依赖（除 ECharts 外）的图表交互运行时：
 *   - 客户端聚合（HTML 内只带原始记录，切换维度/筛选不需要回服务器）
 *   - 下钻（drill）/ 面包屑
 *   - 多图联动（link）：点击一张图的类目，同组其他图自动过滤
 *   - 图例、缩放、tooltip、导出 PNG
 * 设计成 UMD 风格：浏览器里挂到 window.EazyViz，测试里可以 require。
 */
(function (global) {
  'use strict';

  var EazyViz = {};
  global.EazyViz = EazyViz;

  EazyViz.version = '0.1.0';

  var FONT = 'Roboto,"Google Sans","Segoe UI",-apple-system,BlinkMacSystemFont,"Microsoft YaHei","PingFang SC",sans-serif';
  var SEP = '\u0001';

  // Material Design 3 配色：Google Blue / Green / Yellow / Red / Purple / Teal / Orange / Pink
  var PALETTE_LIGHT = ['#1a73e8', '#188038', '#f9ab00', '#d93025', '#9334e6',
                       '#12b5cb', '#fa7b17', '#e52592', '#3c4043', '#795548'];
  var PALETTE_DARK = ['#8ab4f8', '#81c995', '#fdd663', '#f28b82', '#c58af9',
                      '#78d9ec', '#ffb74d', '#ff8bcb', '#9aa0a6', '#bcaaa4'];

  // Material Design 3 基础色（文字/描边/表面），分类色由 PALETTES 决定
  var THEME_BASE = {
    light: {
      name: 'light', text: '#202124', subtext: '#5f6368', axis: '#dadce0',
      split: '#f1f3f4', border: '#e8eaed', bg: '#ffffff', tooltipBg: '#ffffff',
      tooltipBorder: '#e8eaed',
      surface: '#ffffff', surfaceVar: '#f8f9fa', outline: '#dadce0',
      primary: '#1a73e8', error: '#d93025', success: '#188038'
    },
    dark: {
      name: 'dark', text: '#e8eaed', subtext: '#9aa0a6', axis: '#3c4043',
      split: '#2d2e30', border: '#3c4043', bg: '#202124', tooltipBg: '#2d2e30',
      tooltipBorder: '#3c4043',
      surface: '#202124', surfaceVar: '#292a2d', outline: '#3c4043',
      primary: '#8ab4f8', error: '#f28b82', success: '#81c995'
    }
  };

  // ---- 配色库 -----------------------------------------------------------
  // 每个配色 10 个分类色，深色模式自动「提亮」派生，热力图色阶由首色派生。
  var PALETTES = {
    google: { label: 'Google Material 3', colors: [
      '#1a73e8', '#188038', '#f9ab00', '#d93025', '#9334e6',
      '#12b5cb', '#fa7b17', '#e52592', '#3c4043', '#795548'] },
    antd: { label: 'Ant Design', colors: [
      '#1677ff', '#52c41a', '#faad14', '#ff4d4f', '#722ed1',
      '#13c2c2', '#fa8c16', '#eb2f96', '#2f54eb', '#a0d911'] },
    tableau: { label: 'Tableau 10', colors: [
      '#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f',
      '#edc949', '#af7aa1', '#ff9da7', '#9c755f', '#bab0ab'] },
    carbon: { label: 'IBM Carbon', colors: [
      '#6929c4', '#1192e8', '#005d5d', '#9f1853', '#fa4d56',
      '#570408', '#198038', '#002d9c', '#ee538b', '#b28600'] },
    echarts: { label: 'ECharts 默认', colors: [
      '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
      '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#48b3bd'] },
    morandi: { label: '莫兰迪', colors: [
      '#8fa3b0', '#b7a89a', '#a8b8a0', '#c4a49a', '#9fa8c4',
      '#b6a8bd', '#93b0aa', '#cbbfa7', '#a9a9b0', '#d0b8ac'] },
    tailwind: { label: 'Tailwind', colors: [
      '#3f83f8', '#0e9f6e', '#faca15', '#f05252', '#9061f9',
      '#16bdca', '#ff8a4c', '#e74694', '#6b7280', '#31c48d'] }
  };

  function hex2rgb(h) {
    var s = String(h).replace('#', '');
    if (s.length === 3) s = s[0] + s[0] + s[1] + s[1] + s[2] + s[2];
    return [parseInt(s.slice(0, 2), 16), parseInt(s.slice(2, 4), 16), parseInt(s.slice(4, 6), 16)];
  }

  function rgb2hex(r, g, b) {
    var f = function (v) {
      var s = Math.max(0, Math.min(255, Math.round(v))).toString(16);
      return s.length === 1 ? '0' + s : s;
    };
    return '#' + f(r) + f(g) + f(b);
  }

  // 把 a 往 b 混 t（0=全 a，1=全 b）
  function mixColor(a, b, t) {
    var x = hex2rgb(a), y = hex2rgb(b);
    return rgb2hex(
      x[0] + (y[0] - x[0]) * t,
      x[1] + (y[1] - x[1]) * t,
      x[2] + (y[2] - x[2]) * t
    );
  }

  var THEME_CACHE = {};

  /**
   * 取主题对象：mode = light|dark，paletteName = PALETTES 的键。
   * 返回的对象里 palette / heat / primary 已按配色改写，其余（文字、描边）沿用 MD3 基础色。
   */
  function themeFor(mode, paletteName) {
    mode = (mode === 'dark') ? 'dark' : 'light';
    var pname = PALETTES[paletteName] ? paletteName : 'google';
    var key = mode + '|' + pname;
    if (THEME_CACHE[key]) return THEME_CACHE[key];
    var base = THEME_BASE[mode];
    var colors = PALETTES[pname].colors;
    var pal = [], i;
    if (mode === 'dark') {
      for (i = 0; i < colors.length; i++) pal.push(mixColor(colors[i], '#ffffff', 0.2));
    } else {
      pal = colors.slice();
    }
    var heat;
    if (mode === 'dark') {
      heat = [
        mixColor(colors[0], '#101418', 0.86), mixColor(colors[0], '#101418', 0.62),
        mixColor(colors[0], '#101418', 0.3), mixColor(colors[0], '#ffffff', 0.18),
        mixColor(colors[0], '#ffffff', 0.45)
      ];
    } else {
      heat = [
        mixColor(colors[0], '#ffffff', 0.92), mixColor(colors[0], '#ffffff', 0.72),
        mixColor(colors[0], '#ffffff', 0.45), mixColor(colors[0], '#ffffff', 0.16),
        colors[0]
      ];
    }
    var t = {}, k;
    for (k in base) if (base.hasOwnProperty(k)) t[k] = base[k];
    t.palette = pal;
    t.heat = heat;
    t.primary = pal[0];
    t.paletteName = pname;
    THEME_CACHE[key] = t;
    return t;
  }

  // 向后兼容：THEME.light / THEME.dark 是最常用的一组（google）
  var THEME = {
    light: themeFor('light', 'google'),
    dark: themeFor('dark', 'google')
  };

  // ======================================================================
  // 1. 小工具
  // ======================================================================
  function isNum(v) {
    return typeof v === 'number' && isFinite(v);
  }

  function num(v) {
    if (v === null || v === undefined || v === '') return null;
    var n = Number(v);
    return isFinite(n) ? n : null;
  }

  function esc(s) {
    return String(s === null || s === undefined ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function trimNum(n) {
    if (!isFinite(n)) return '-';
    var r = Math.round(n * 1000) / 1000;
    if (Math.abs(r - Math.round(r)) < 1e-9) return String(Math.round(r));
    return String(r);
  }

  function groupThousand(n) {
    var s = trimNum(Math.abs(n)).split('.');
    s[0] = s[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return (n < 0 ? '-' : '') + s.join('.');
  }

  function roundTo(n, d) {
    if (!isFinite(n)) return '-';
    var p = Math.pow(10, d);
    var r = Math.round(n * p) / p;
    return trimNum(r);
  }

  function compactCN(n) {
    var a = Math.abs(n);
    if (a >= 1e8) {
      var q = n / 1e8;
      return roundTo(q, Math.abs(q) < 100 ? 1 : 0) + '亿';
    }
    if (a >= 1e4) {
      var w = n / 1e4;
      return roundTo(w, Math.abs(w) < 100 ? 1 : 0) + '万';
    }
    return groupThousand(n);
  }

  function fmtValue(v, fmt) {
    if (v === null || v === undefined || v === '') return '-';
    if (typeof v === 'object') v = v.value;
    var n = num(v);
    if (n === null) return String(v);
    switch (fmt) {
      case 'raw': return trimNum(n);
      case 'percent': return roundTo(n, 1) + '%';
      case 'thousands': return groupThousand(n);
      case 'currency': return '¥' + groupThousand(roundTo(n, 2));
      default: return compactCN(n);
    }
  }

  function truncate(s, n) {
    s = String(s === null || s === undefined ? '' : s);
    return s.length <= n ? s : s.slice(0, n - 1) + '…';
  }

  function catName(v) {
    return (v === null || v === undefined) ? '(空)' : String(v);
  }

  function debounce(fn, ms) {
    var t = null;
    return function () {
      var args = arguments, self = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(self, args); }, ms);
    };
  }

  // ======================================================================
  // 2. 数据访问 / 聚合
  // ======================================================================
  function rowsOf(data) {
    if (!data || !data.cols || !data.rows) return [];
    if (!data._objs) {
      var cols = data.cols, rows = data.rows, out = new Array(rows.length);
      for (var i = 0; i < rows.length; i++) {
        var o = {}, r = rows[i];
        for (var j = 0; j < cols.length; j++) o[cols[j]] = r[j];
        out[i] = o;
      }
      data._objs = out;
    }
    return data._objs;
  }

  function hasCol(data, name) {
    return !!(data && data.cols && data.cols.indexOf(name) >= 0);
  }

  function currentXDim(spec, state) {
    var roles = spec.roles || {};
    var type = spec.type;
    if (type === 'pie' || type === 'funnel') return roles.names || null;
    if (type === 'histogram' || type === 'treemap' || type === 'gauge' || type === 'kpi') return null;
    if (type === 'scatter' || type === 'heatmap' || type === 'box') return roles.x || null;
    if (type === 'sunburst' || type === 'tree') {
      var path = roles.path || [];
      if (!path.length) return null;
      var pd = (state && state.drill) ? state.drill.length : 0;
      return path[Math.min(pd, path.length - 1)];
    }
    if (type === 'sankey' || type === 'graph') return roles.source || null;
    if (type === 'pyramid') return roles.names || null;
    if (type === 'theme_river' || type === 'sparkline') return roles.x || null;
    if (type === 'gantt' || type === 'candlestick') return roles.x || null;
    if (type === 'progress') return roles.x || null;
    if (type === 'wordcloud' || type === 'tile') return roles.names || null;
    if (type === 'calendar' || type === 'matrix' || type === 'ring_progress' ||
      type === 'parallel' || type === 'table' || type === 'group_kpi') return null;
    if (spec.drill && spec.drill.length) {
      var depth = (state && state.drill) ? state.drill.length : 0;
      return spec.drill[Math.min(depth, spec.drill.length - 1)];
    }
    return roles.x || null;
  }

  function filteredRows(spec, data, state) {
    var rows = rowsOf(data);
    state = state || {};
    var filters = state.filters || {};
    var drill = state.drill || [];
    var keys = Object.keys(filters);
    var active = [];
    for (var i = 0; i < keys.length; i++) {
      if (hasCol(data, keys[i])) active.push(keys[i]);
    }
    if (!active.length && !drill.length) return rows;
    return rows.filter(function (r) {
      for (var i = 0; i < active.length; i++) {
        if (catName(r[active[i]]) !== filters[active[i]]) return false;
      }
      for (var j = 0; j < drill.length; j++) {
        if (catName(r[drill[j].dim]) !== drill[j].value) return false;
      }
      return true;
    });
  }

  function median(vals) {
    if (!vals.length) return null;
    var s = vals.slice().sort(function (a, b) { return a - b; });
    var mid = Math.floor(s.length / 2);
    return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
  }

  function quantile(sorted, q) {
    if (!sorted.length) return null;
    var pos = (sorted.length - 1) * q;
    var base = Math.floor(pos), rest = pos - base;
    if (sorted[base + 1] !== undefined) {
      return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
    }
    return sorted[base];
  }

  /**
   * 按维度聚合。
   * @returns {Array<{key,keys,value,cnt}>}
   */
  function groupBy(rows, dims, measure, how) {
    how = how || 'sum';
    var map = {}, list = [];
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i], key = '', keys = [];
      for (var j = 0; j < dims.length; j++) {
        var cv = catName(r[dims[j]]);
        keys.push(cv);
        key += (j ? SEP : '') + cv;
      }
      var rec = map[key];
      if (!rec) {
        rec = { key: key, keys: keys, sum: 0, cnt: 0, vals: [] };
        map[key] = rec;
        list.push(rec);
      }
      if (how === 'count') {
        rec.cnt++;
      } else {
        var v = measure ? num(r[measure]) : null;
        if (v !== null) {
          rec.sum += v;
          rec.cnt++;
          if (how === 'max' || how === 'min' || how === 'median') rec.vals.push(v);
        }
      }
    }
    for (var k = 0; k < list.length; k++) {
      var g = list[k];
      if (how === 'count') g.value = g.cnt;
      else if (how === 'sum') g.value = g.cnt ? g.sum : null;
      else if (how === 'mean') g.value = g.cnt ? g.sum / g.cnt : null;
      else if (how === 'max') g.value = g.vals.length ? Math.max.apply(null, g.vals) : null;
      else if (how === 'min') g.value = g.vals.length ? Math.min.apply(null, g.vals) : null;
      else if (how === 'median') g.value = g.vals.length ? median(g.vals) : null;
      else g.value = g.sum;
      delete g.vals;
    }
    return list;
  }

  // ======================================================================
  // 3. 通用 ECharts 配置片段
  // ======================================================================
  function makeGrid(theme, opts) {
    opts = opts || {};
    var grid = {
      left: 10, right: 22, containLabel: true,
      top: opts.legend ? 48 : 30,
      bottom: 44
    };
    if (opts.zoom) grid.bottom = 76;
    if (opts.rightExtra) grid.right = opts.rightExtra;
    return grid;
  }

  function makeLegend(theme, selected, show) {
    if (!show) return { show: false };
    var legend = {
      show: true, type: 'scroll', top: 6, left: 'center',
      itemWidth: 12, itemHeight: 8, itemGap: 12,
      textStyle: { color: theme.subtext, fontSize: 11 }
    };
    if (selected) legend.selected = selected;
    return legend;
  }

  function makeToolbox(theme) {
    return {
      show: true, right: 4, top: 0, itemSize: 11,
      iconStyle: { borderColor: theme.subtext },
      emphasis: { iconStyle: { borderColor: theme.text } },
      feature: { saveAsImage: { title: '保存图片', pixelRatio: 2, name: 'eazy-chart' } }
    };
  }

  function axisTitle(userVal, fallback) {
    if (userVal === null || userVal === undefined) return fallback || '';
    return userVal;
  }

  function axisLabelRotate(cats) {
    var maxLen = 0;
    for (var i = 0; i < cats.length; i++) {
      var s = String(cats[i]);
      if (s.length > maxLen) maxLen = s.length;
    }
    return maxLen > 7 ? 30 : 0;
  }

  function applyLim(axis, lim) {
    if (!lim) return axis;
    if (lim[0] !== null && lim[0] !== undefined) axis.min = lim[0];
    if (lim[1] !== null && lim[1] !== undefined) axis.max = lim[1];
    return axis;
  }

  // 按横轴自身排序（时间列在 Python 侧已格式化成 ISO 字符串，可直接比较）
  function compareCatX(a, b) {
    var sa = String(a), sb = String(b);
    var na = Number(sa), nb = Number(sb);
    if (sa !== '' && sb !== '' && isFinite(na) && isFinite(nb)) return na - nb;
    return sa < sb ? -1 : (sa > sb ? 1 : 0);
  }

  // 有序分类列（pd.Categorical(ordered=True)）用声明顺序排序
  function catRanker(data, dim) {
    var orders = data && data.orders;
    if (!orders || !dim || !orders[dim]) return null;
    var list = orders[dim], map = {};
    for (var i = 0; i < list.length; i++) map[list[i]] = i;
    return function (a, b) {
      var ia = map[a], ib = map[b];
      if (ia === undefined || ib === undefined) return compareCatX(a, b);
      return ia - ib;
    };
  }

  function setAxisName(axis, name, theme, isX, gap) {
    if (!name) return axis;
    axis.name = name;
    axis.nameLocation = isX ? 'middle' : 'end';
    axis.nameGap = gap || (isX ? 30 : 14);
    axis.nameTextStyle = { color: theme.subtext, fontSize: 11 };
    return axis;
  }

  function makeCategoryAxis(spec, cats, theme) {
    // 类目很多时（例如按日期画线），自动抽稀标签，否则会挤成一堆斜字
    var n = cats.length;
    var dense = n > 12;
    var interval = dense ? Math.max(1, Math.ceil(n / 10) - 1) : 0;
    var rotate = dense ? (axisLabelRotate(cats) > 0 ? 30 : 0) : axisLabelRotate(cats);
    return {
      type: 'category',
      data: cats,
      boundaryGap: true,
      axisTick: { show: false },
      axisLine: { lineStyle: { color: theme.axis } },
      axisLabel: {
        color: theme.subtext, hideOverlap: true,
        interval: interval,
        rotate: rotate,
        formatter: function (v) {
          var s = String(v);
          var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(s);
          if (m) return dense ? (m[2] + '-' + m[3]) : s.slice(0, 10);
          return truncate(v, 14);
        }
      },
      splitLine: { show: false }
    };
  }

  function makeValueAxis(spec, theme, lim) {
    var axis = {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: theme.split, type: 'dashed' } },
      axisLabel: {
        color: theme.subtext,
        formatter: function (v) { return fmtValue(v, spec.fmt); }
      }
    };
    return applyLim(axis, lim);
  }

  function tooltipBox(theme) {
    return {
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      borderWidth: 1,
      padding: [8, 10],
      textStyle: { color: theme.text, fontSize: 12 },
      extraCssText: 'box-shadow:0 4px 14px rgba(16,24,40,.12);border-radius:8px;'
    };
  }

  function axisTooltip(spec, theme, stacked) {
    var tip = tooltipBox(theme);
    tip.trigger = 'axis';
    tip.axisPointer = { type: spec.type === 'bar' ? 'shadow' : 'line', lineStyle: { color: theme.axis } };
    tip.formatter = function (params) {
      if (!params || !params.length) return '';
      var head = '<div style="font-weight:600;margin-bottom:4px">' +
        esc(params[0].axisValueLabel || params[0].name) + '</div>';
      var lines = [], total = 0, hasTotal = false;
      for (var i = 0; i < params.length; i++) {
        var p = params[i];
        var raw = p.value;
        if (raw && typeof raw === 'object' && !(raw instanceof Array)) raw = raw.value;
        var n = num(raw);
        if (n !== null) { total += n; hasTotal = true; }
        lines.push(
          '<div style="display:flex;align-items:center;gap:6px;line-height:19px">' + p.marker +
          '<span style="flex:1;max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' +
          esc(p.seriesName) + '</span><b style="margin-left:10px">' + fmtValue(raw, spec.fmt) + '</b></div>'
        );
      }
      if (stacked && hasTotal && params.length > 1) {
        lines.push('<div style="border-top:1px dashed ' + theme.axis +
          ';margin-top:4px;padding-top:4px;display:flex"><span style="flex:1">合计</span><b>' +
          fmtValue(total, spec.fmt) + '</b></div>');
      }
      return head + lines.join('');
    };
    return tip;
  }

  // ======================================================================
  // 4. 各图表 option 构造
  // ======================================================================
  function sourceSelection(spec, state) {
    if (!spec.link || !EazyViz.links) return null;
    var link = EazyViz.links[spec.link];
    if (!link || link.sourceId !== spec.id) return null;
    var xdim = currentXDim(spec, state);
    return (xdim && link.dim === xdim) ? link.value : null;
  }

  function dimItem(v, sel, cat) {
    if (sel === null || sel === undefined) return v;
    if (cat === sel) return v;
    return { value: v, itemStyle: { opacity: 0.28 } };
  }

  // ---- 柱 / 折线 --------------------------------------------------------
  function buildCartesian(spec, data, state, theme) {
    var rows = filteredRows(spec, data, state);
    var xdim = currentXDim(spec, state);
    var ydim = spec.roles.y;
    var cdim = spec.roles.color;
    var how = spec.agg || (ydim ? 'sum' : 'count');
    if (!rows.length) return null;

    var dims = cdim ? [xdim, cdim] : [xdim];
    var groups = groupBy(rows, dims, ydim, how);
    var totals = {}, catOrder = [], seriesTotals = {}, seriesOrder = [], map = {};

    for (var i = 0; i < groups.length; i++) {
      var g = groups[i];
      var xv = g.keys[0];
      var sv = cdim ? g.keys[1] : '';
      if (totals[xv] === undefined) { totals[xv] = 0; catOrder.push(xv); }
      if (g.value !== null) totals[xv] += g.value;
      if (cdim && seriesTotals[sv] === undefined) { seriesTotals[sv] = 0; seriesOrder.push(sv); }
      if (cdim && g.value !== null) seriesTotals[sv] += g.value;
      map[xv + SEP + sv] = g.value;
    }

    var cats = catOrder.slice();
    if (spec.sort === 'desc') {
      cats.sort(function (a, b) { return (totals[b] || 0) - (totals[a] || 0); });
    } else if (spec.sort === 'asc') {
      cats.sort(function (a, b) { return (totals[a] || 0) - (totals[b] || 0); });
    } else if (spec.sort === 'x') {
      cats.sort(catRanker(data, xdim) || compareCatX);
    }

    var otherCats = [];
    if (spec.topN && cats.length > spec.topN) {
      otherCats = cats.slice(spec.topN);
      cats = cats.slice(0, spec.topN).concat(['其他']);
    }

    var catTotals = {};
    if (spec.percent) {
      for (var qi = 0; qi < cats.length; qi++) {
        var qsum = 0;
        for (var qj = 0; qj < seriesOrder.length; qj++) {
          var qv = map[cats[qi] + SEP + seriesOrder[qj]];
          if (qv !== null && qv !== undefined) qsum += qv;
        }
        catTotals[cats[qi]] = qsum;
      }
    }

    var seriesNames;
    if (cdim) {
      seriesNames = seriesOrder.slice();
      if (spec.sort !== 'none') {
        seriesNames.sort(function (a, b) { return (seriesTotals[b] || 0) - (seriesTotals[a] || 0); });
      }
    } else {
      seriesNames = [ydim || '记录数'];
    }

    function valueOf(cat, sname) {
      if (cat === '其他') {
        var s = 0, has = false;
        for (var k = 0; k < otherCats.length; k++) {
          var ov = map[otherCats[k] + SEP + sname];
          if (ov !== null && ov !== undefined) { s += ov; has = true; }
        }
        return has ? s : null;
      }
      var v = map[cat + SEP + (cdim ? sname : '')];
      return (v === undefined) ? null : v;
    }

    var sel = sourceSelection(spec, state);
    var isBar = (spec.type === 'bar');
    var needZoom = (spec.zoom === true) || (spec.zoom !== false && cats.length > 15);
    var series = [];

    for (var si = 0; si < seriesNames.length; si++) {
      var name = seriesNames[si];
      var sdata = [];
      for (var ci = 0; ci < cats.length; ci++) {
        var val = valueOf(cats[ci], name);
        if (spec.percent && val !== null && val !== undefined) {
          var ct = catTotals[cats[ci]] || 0;
          val = ct ? (val / ct * 100) : 0;
        }
        if (spec.percent && val !== null) val = Math.round(val * 10) / 10;
        if (isBar) {
          sdata.push(dimItem(val === null ? 0 : val, sel, cats[ci]));
        } else {
          sdata.push(val);
        }
      }
      if (isBar) {
        var barSeries = {
          name: name, type: 'bar', data: sdata,
          barMaxWidth: 34,
          itemStyle: { borderRadius: spec.horizontal ? [0, 3, 3, 0] : [3, 3, 0, 0] },
          emphasis: { focus: 'series' },
          select: { itemStyle: { opacity: 1 } }
        };
        if (spec.stack) barSeries.stack = 'total';
        if (spec.labels) {
          barSeries.label = {
            show: true, position: spec.horizontal ? 'right' : 'top',
            color: theme.subtext, fontSize: 10,
            formatter: function (p) { return fmtValue(p.value, spec.fmt); }
          };
        }
        series.push(barSeries);
      } else {
        var lineSeries = {
          name: name, type: 'line', data: sdata,
          smooth: spec.smooth !== false,
          symbol: 'circle', symbolSize: 6,
          showSymbol: cats.length <= 40,
          lineStyle: { width: 2 },
          connectNulls: true,
          emphasis: { focus: 'series' }
        };
        if (spec.step) lineSeries.step = 'middle';
        if (spec.area) lineSeries.areaStyle = { opacity: spec.stack ? 0.45 : 0.16 };
        if (spec.stack) lineSeries.stack = 'total';
        if (spec.markers) lineSeries.markPoint = { data: [], symbolSize: 0 };
        if (spec.labels) {
          lineSeries.label = {
            show: true, position: 'top', color: theme.subtext, fontSize: 10,
            formatter: function (p) { return fmtValue(p.value, spec.fmt); }
          };
        }
        series.push(lineSeries);
      }
    }

    var catAxis = makeCategoryAxis(spec, cats, theme);
    var valAxis = makeValueAxis(spec, theme, null);
    var opt = {
      grid: makeGrid(theme, { legend: !!(cdim && spec.legend), zoom: needZoom }),
      legend: makeLegend(theme, state.legendSel, !!(cdim && spec.legend)),
      toolbox: makeToolbox(theme),
      tooltip: axisTooltip(spec, theme, !!spec.stack),
      series: series
    };
    if (spec.percent) {
      var origTip = opt.tooltip;
      origTip.valueFormatter = function (v) { return Number(v).toFixed(1) + '%'; };
    }

    if (spec.horizontal) {
      catAxis.boundaryGap = true;
      setAxisName(valAxis, axisTitle(spec.xtitle, ydim || '记录数'), theme, true);
      setAxisName(catAxis, axisTitle(spec.ytitle, xdim), theme, false, 20);
      opt.xAxis = applyLim(valAxis, spec.xlim);
      opt.yAxis = catAxis;
    } else {
      catAxis.boundaryGap = spec.type !== 'line';
      setAxisName(catAxis, axisTitle(spec.xtitle, xdim), theme, true);
      setAxisName(valAxis, axisTitle(spec.ytitle, ydim || '记录数'), theme, false);
      opt.xAxis = catAxis;
      opt.yAxis = applyLim(valAxis, spec.ylim);
    }
    if (spec.percent) {
      var pctAxis = spec.horizontal ? opt.xAxis : opt.yAxis;
      pctAxis.max = 100;
      pctAxis.axisLabel.formatter = function (v) { return v + '%'; };
    }
    if (needZoom) {
      opt.dataZoom = [
        { type: 'inside', filterMode: 'filter' },
        {
          type: 'slider', height: 16, bottom: 4, borderColor: 'transparent',
          backgroundColor: 'transparent', fillerColor: spec.percent ? 'rgba(26,115,232,0.10)' : 'rgba(26,115,232,0.12)',
          handleSize: '88%', brushSelect: false,
          textStyle: { color: theme.subtext, fontSize: 10 }
        }
      ];
    }
    return opt;
  }

  // ---- 柱线组合 ---------------------------------------------------------
  function buildCombo(spec, data, state, theme) {
    var rows = filteredRows(spec, data, state);
    if (!rows.length) return null;
    var xdim = currentXDim(spec, state);
    var how = spec.agg || 'sum';
    var g1 = groupBy(rows, [xdim], spec.roles.y, how);
    var g2 = groupBy(rows, [xdim], spec.roles.y2, how);
    var cats = [], v1 = {}, v2 = {};
    g1.forEach(function (g) { if (cats.indexOf(g.keys[0]) < 0) cats.push(g.keys[0]); v1[g.keys[0]] = g.value; });
    g2.forEach(function (g) { if (cats.indexOf(g.keys[0]) < 0) cats.push(g.keys[0]); v2[g.keys[0]] = g.value; });
    if (spec.sort === 'x') cats.sort(catRanker(data, xdim) || compareCatX);

    var catAxis = makeCategoryAxis(spec, cats, theme);
    var leftAxis = makeValueAxis(spec, theme, null);
    var rightAxis = makeValueAxis(spec, theme, null);
    rightAxis.splitLine = { show: false };
    setAxisName(catAxis, axisTitle(spec.xtitle, xdim), theme, true);
    setAxisName(leftAxis, axisTitle(spec.ytitle, spec.roles.y), theme, false);
    setAxisName(rightAxis, spec.roles.y2, theme, false, 18);

    return {
      grid: makeGrid(theme, { legend: spec.legend, rightExtra: 26 }),
      legend: makeLegend(theme, state.legendSel, spec.legend),
      toolbox: makeToolbox(theme),
      tooltip: axisTooltip(spec, theme, false),
      xAxis: catAxis,
      yAxis: [leftAxis, rightAxis],
      series: [
        {
          name: spec.roles.y, type: 'bar', data: cats.map(function (c) { return v1[c] === undefined ? 0 : v1[c]; }),
          barMaxWidth: 32, itemStyle: { borderRadius: [3, 3, 0, 0] }
        },
        {
          name: spec.roles.y2, type: 'line', yAxisIndex: 1,
          data: cats.map(function (c) { return v2[c] === undefined ? null : v2[c]; }),
          smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { width: 2 }
        }
      ]
    };
  }

  // ---- 饼 / 环 ----------------------------------------------------------
  function buildPie(spec, data, state, theme) {
    var rows = filteredRows(spec, data, state);
    if (!rows.length) return null;
    var ndim = spec.roles.names;
    var vdim = spec.roles.value;
    var how = spec.agg || (vdim ? 'sum' : 'count');
    var groups = groupBy(rows, [ndim], vdim, how);
    var items = groups.map(function (g) {
      return { name: g.keys[0], value: g.value === null ? 0 : g.value };
    });
    items.sort(function (a, b) { return b.value - a.value; });
    if (spec.topN && items.length > spec.topN) {
      var rest = items.slice(spec.topN).reduce(function (s, it) { return s + it.value; }, 0);
      items = items.slice(0, spec.topN).concat([{ name: '其他', value: rest }]);
    }
    var sel = sourceSelection(spec, state);
    var dataArr = items.map(function (it) {
      var item = { name: it.name, value: it.value };
      if (sel !== null && sel !== undefined && it.name !== sel) item.itemStyle = { opacity: 0.3 };
      return item;
    });
    return {
      tooltip: (function () {
        var tip = tooltipBox(theme);
        tip.trigger = 'item';
        tip.formatter = function (p) {
          return '<div style="font-weight:600;margin-bottom:3px">' + esc(p.name) + '</div>' +
            p.marker + ' ' + fmtValue(p.value, spec.fmt) + '（' + p.percent + '%）';
        };
        return tip;
      })(),
      legend: {
        show: spec.legend !== false, type: 'scroll', orient: 'vertical',
        right: 6, top: 'middle', itemWidth: 10, itemHeight: 8,
        textStyle: { color: theme.subtext, fontSize: 11 },
        selected: state.legendSel || undefined
      },
      toolbox: makeToolbox(theme),
      series: [{
        type: 'pie',
        radius: spec.donut ? ['46%', '70%'] : ['0%', '68%'],
        center: ['38%', '52%'],
        avoidLabelOverlap: true,
        minAngle: 2,
        itemStyle: { borderColor: theme.bg, borderWidth: 2 },
        label: {
          show: spec.labels !== false,
          formatter: spec.labels !== false ? '{b}\n{d}%' : '{b}',
          color: theme.text, fontSize: 11, lineHeight: 15
        },
        labelLine: { show: spec.labels !== false, length: 10, length2: 8, lineStyle: { color: theme.axis } },
        emphasis: { scale: true, scaleSize: 6, itemStyle: { shadowBlur: 12, shadowColor: 'rgba(0,0,0,.2)' } },
        data: dataArr
      }]
    };
  }

  // ---- 散点 -------------------------------------------------------------
  function buildScatter(spec, data, state, theme) {
    var rows = filteredRows(spec, data, state);
    if (!rows.length) return null;
    var xdim = spec.roles.x, ydim = spec.roles.y, sdim = spec.roles.size, cdim = spec.roles.color;

    var sizes = [];
    var raw = [];
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      var xv = num(r[xdim]), yv = num(r[ydim]);
      if (xv === null || yv === null) continue;
      var sv = sdim ? num(r[sdim]) : null;
      if (sv !== null) sizes.push(sv);
      raw.push({ x: xv, y: yv, s: sv, c: cdim ? catName(r[cdim]) : '' });
    }
    if (!raw.length) return null;
    var sMin = sizes.length ? Math.min.apply(null, sizes) : 0;
    var sMax = sizes.length ? Math.max.apply(null, sizes) : 1;
    function symbolSize(val) {
      if (!sdim) return 9;
      var s = num(val[2]);
      if (s === null) return 6;
      if (sMax === sMin) return 12;
      return 6 + 22 * Math.sqrt((s - sMin) / (sMax - sMin));
    }

    var byColor = {}, order = [];
    for (var k = 0; k < raw.length; k++) {
      var key = raw[k].c;
      if (!byColor[key]) { byColor[key] = []; order.push(key); }
      byColor[key].push([raw[k].x, raw[k].y, raw[k].s, raw[k].c]);
    }

    var series = order.map(function (name, idx) {
      var s = {
        name: name || ydim, type: 'scatter', data: byColor[name],
        symbolSize: symbolSize,
        emphasis: { focus: 'series' },
        itemStyle: { opacity: 0.82, borderColor: theme.bg, borderWidth: 1 }
      };
      return s;
    });

    var xAxis = makeValueAxis(spec, theme, spec.xlim);
    var yAxis = makeValueAxis(spec, theme, spec.ylim);
    setAxisName(xAxis, axisTitle(spec.xtitle, xdim), theme, true);
    setAxisName(yAxis, axisTitle(spec.ytitle, ydim), theme, false);

    return {
      grid: makeGrid(theme, { legend: !!(cdim && spec.legend) }),
      legend: makeLegend(theme, state.legendSel, !!(cdim && spec.legend)),
      toolbox: makeToolbox(theme),
      tooltip: (function () {
        var tip = tooltipBox(theme);
        tip.trigger = 'item';
        tip.formatter = function (p) {
          var d = p.data || [];
          var html = '';
          if (cdim) html += '<div style="font-weight:600;margin-bottom:2px">' + esc(d[3]) + '</div>';
          html += '<div style="line-height:19px">' + esc(xdim) + '：<b>' + fmtValue(d[0], spec.fmt) + '</b></div>';
          html += '<div style="line-height:19px">' + esc(ydim) + '：<b>' + fmtValue(d[1], spec.fmt) + '</b></div>';
          if (sdim) html += '<div style="line-height:19px">' + esc(sdim) + '：<b>' + fmtValue(d[2], spec.fmt) + '</b></div>';
          return html;
        };
        return tip;
      })(),
      xAxis: xAxis,
      yAxis: yAxis,
      series: series
    };
  }

  // ---- 直方图 -----------------------------------------------------------
  function buildHistogram(spec, data, state, theme) {
    var rows = filteredRows(spec, data, state);
    var col = spec.roles.value || spec.roles.y;
    var vals = [];
    for (var i = 0; i < rows.length; i++) {
      var v = num(rows[i][col]);
      if (v !== null) vals.push(v);
    }
    if (!vals.length) return null;
    var bins = spec.bins || 20;
    var min = Math.min.apply(null, vals), max = Math.max.apply(null, vals);
    if (min === max) { min -= 0.5; max += 0.5; }
    var width = (max - min) / bins;
    var counts = new Array(bins);
    for (var b = 0; b < bins; b++) counts[b] = 0;
    for (var j = 0; j < vals.length; j++) {
      var idx = Math.floor((vals[j] - min) / width);
      if (idx >= bins) idx = bins - 1;
      if (idx < 0) idx = 0;
      counts[idx]++;
    }
    function binLabel(v) {
      var a = Math.abs(v);
      if (a >= 1e4) return fmtValue(v, 'compact');
      if (a >= 10) return String(Math.round(v));
      return String(Math.round(v * 10) / 10);
    }
    var cats = [], dataArr = [];
    for (var c = 0; c < bins; c++) {
      var lo = min + c * width, hi = lo + width;
      cats.push(binLabel(lo) + '~' + binLabel(hi));
      dataArr.push({ value: counts[c], itemStyle: { borderRadius: [3, 3, 0, 0] } });
    }
    var catAxis = makeCategoryAxis(spec, cats, theme);
    var valAxis = makeValueAxis(spec, theme, null);
    setAxisName(catAxis, axisTitle(spec.xtitle, col), theme, true);
    setAxisName(valAxis, axisTitle(spec.ytitle, '频数'), theme, false);
    return {
      grid: makeGrid(theme, { legend: false }),
      toolbox: makeToolbox(theme),
      tooltip: (function () {
        var tip = tooltipBox(theme);
        tip.trigger = 'axis';
        tip.axisPointer = { type: 'shadow' };
        tip.formatter = function (params) {
          var p = params[0];
          var lo = min + p.dataIndex * width, hi = lo + width;
          return '<div style="font-weight:600">' + esc(col) + '</div>' +
            '<div style="line-height:19px">区间：' + fmtValue(lo, spec.fmt) + ' ~ ' + fmtValue(hi, spec.fmt) + '</div>' +
            '<div style="line-height:19px">频数：<b>' + p.value + '</b></div>';
        };
        return tip;
      })(),
      xAxis: catAxis,
      yAxis: valAxis,
      series: [{
        type: 'bar', data: dataArr, barWidth: '98%',
        itemStyle: { borderRadius: [3, 3, 0, 0] }
      }]
    };
  }

  // ---- 热力图 -----------------------------------------------------------
  function buildHeatmap(spec, data, state, theme) {
    var rows = filteredRows(spec, data, state);
    if (!rows.length) return null;
    var xdim = spec.roles.x, ydim = spec.roles.y, vdim = spec.roles.value;
    var how = spec.agg || 'sum';
    var groups = groupBy(rows, [xdim, ydim], vdim, how);
    var xOrder = [], yOrder = [], xTotals = {}, yTotals = {}, map = {};
    var min = Infinity, max = -Infinity;
    for (var i = 0; i < groups.length; i++) {
      var g = groups[i], xv = g.keys[0], yv = g.keys[1];
      if (xOrder.indexOf(xv) < 0) { xOrder.push(xv); xTotals[xv] = 0; }
      if (yOrder.indexOf(yv) < 0) { yOrder.push(yv); yTotals[yv] = 0; }
      var v = g.value === null ? 0 : g.value;
      map[xv + SEP + yv] = v;
      xTotals[xv] += v; yTotals[yv] += v;
      if (v < min) min = v;
      if (v > max) max = v;
    }
    if (spec.sort === 'desc') {
      xOrder.sort(function (a, b) { return xTotals[b] - xTotals[a]; });
      yOrder.sort(function (a, b) { return yTotals[b] - yTotals[a]; });
    } else if (spec.sort === 'x') {
      xOrder.sort(catRanker(data, xdim) || compareCatX);
    }
    var points = [];
    for (var yi = 0; yi < yOrder.length; yi++) {
      for (var xi = 0; xi < xOrder.length; xi++) {
        var key = xOrder[xi] + SEP + yOrder[yi];
        points.push([xi, yi, map[key] === undefined ? 0 : map[key]]);
      }
    }
    if (!isFinite(min)) { min = 0; max = 1; }
    var showLabel = !!spec.labels && points.length <= 60;
    var xAxis = makeCategoryAxis(spec, xOrder, theme);
    xAxis.splitArea = { show: false };
    setAxisName(xAxis, axisTitle(spec.xtitle, xdim), theme, true);
    var yAxis = makeCategoryAxis(spec, yOrder, theme);
    yAxis.splitArea = { show: false };
    setAxisName(yAxis, axisTitle(spec.ytitle, ydim), theme, false);
    var heatGrid = makeGrid(theme, { legend: false, rightExtra: 46 });
    heatGrid.bottom = 44;
    return {
      grid: heatGrid,
      toolbox: makeToolbox(theme),
      tooltip: (function () {
        var tip = tooltipBox(theme);
        tip.trigger = 'item';
        tip.formatter = function (p) {
          return '<div style="font-weight:600">' + esc(xdim) + '：' + esc(xOrder[p.data[0]]) + '</div>' +
            '<div style="line-height:19px">' + esc(ydim) + '：' + esc(yOrder[p.data[1]]) + '</div>' +
            '<div style="line-height:19px">' + esc(vdim) + '：<b>' + fmtValue(p.data[2], spec.fmt) + '</b></div>';
        };
        return tip;
      })(),
      xAxis: xAxis,
      yAxis: yAxis,
      visualMap: {
        min: min, max: max, calculable: false, orient: 'vertical',
        right: 2, top: 'middle', itemWidth: 10, itemHeight: 90,
        textStyle: { color: theme.subtext, fontSize: 10 },
        formatter: function (v) { return fmtValue(v, spec.fmt); },
        inRange: { color: theme.heat }
      },
      series: [{
        type: 'heatmap', data: points,
        label: {
          show: showLabel, color: theme.text, fontSize: 10,
          formatter: function (p) { return fmtValue(p.data[2], spec.fmt); }
        },
        itemStyle: { borderColor: theme.bg, borderWidth: 1 },
        emphasis: { itemStyle: { borderColor: theme.text, borderWidth: 1 } }
      }]
    };
  }

  // ---- 箱线图 -----------------------------------------------------------
  function buildBox(spec, data, state, theme) {
    var rows = filteredRows(spec, data, state);
    var ydim = spec.roles.y, xdim = spec.roles.x;
    if (!rows.length) return null;
    var buckets = {}, order = [];
    for (var i = 0; i < rows.length; i++) {
      var v = num(rows[i][ydim]);
      if (v === null) continue;
      var key = xdim ? catName(rows[i][xdim]) : '全部';
      if (!buckets[key]) { buckets[key] = []; order.push(key); }
      buckets[key].push(v);
    }
    if (!order.length) return null;
    var cats = [], stats = [];
    for (var k = 0; k < order.length; k++) {
      var vals = buckets[order[k]].sort(function (a, b) { return a - b; });
      if (!vals.length) continue;
      cats.push(order[k]);
      stats.push([
        vals[0],
        quantile(vals, 0.25),
        quantile(vals, 0.5),
        quantile(vals, 0.75),
        vals[vals.length - 1]
      ]);
    }
    var catAxis = makeCategoryAxis(spec, cats, theme);
    var valAxis = makeValueAxis(spec, theme, spec.ylim);
    setAxisName(catAxis, axisTitle(spec.xtitle, xdim || ''), theme, true);
    setAxisName(valAxis, axisTitle(spec.ytitle, ydim), theme, false);
    return {
      grid: makeGrid(theme, { legend: false }),
      toolbox: makeToolbox(theme),
      tooltip: (function () {
        var tip = tooltipBox(theme);
        tip.trigger = 'item';
        tip.formatter = function (p) {
          var d = p.data;
          return '<div style="font-weight:600;margin-bottom:3px">' + esc(p.name) + '</div>' +
            '<div style="line-height:19px">最大：<b>' + fmtValue(d[4], spec.fmt) + '</b></div>' +
            '<div style="line-height:19px">上四分位：' + fmtValue(d[3], spec.fmt) + '</div>' +
            '<div style="line-height:19px">中位数：<b>' + fmtValue(d[2], spec.fmt) + '</b></div>' +
            '<div style="line-height:19px">下四分位：' + fmtValue(d[1], spec.fmt) + '</div>' +
            '<div style="line-height:19px">最小：' + fmtValue(d[0], spec.fmt) + '</div>';
        };
        return tip;
      })(),
      xAxis: catAxis,
      yAxis: valAxis,
      series: [{
        type: 'boxplot', data: stats, boxWidth: [12, 40],
        itemStyle: { borderWidth: 1.2 },
        emphasis: { itemStyle: { borderWidth: 2 } }
      }]
    };
  }

  // ---- 漏斗 -------------------------------------------------------------
  function buildFunnel(spec, data, state, theme) {
    var rows = filteredRows(spec, data, state);
    if (!rows.length) return null;
    var ndim = spec.roles.names, vdim = spec.roles.value;
    var how = spec.agg || (vdim ? 'sum' : 'count');
    var groups = groupBy(rows, [ndim], vdim, how);
    var items = groups.map(function (g) {
      return { name: g.keys[0], value: g.value === null ? 0 : g.value };
    });
    items.sort(function (a, b) { return b.value - a.value; });
    var sel = sourceSelection(spec, state);
    var dataArr = items.map(function (it) {
      var item = { name: it.name, value: it.value };
      if (sel !== null && sel !== undefined && it.name !== sel) item.itemStyle = { opacity: 0.3 };
      return item;
    });
    return {
      tooltip: (function () {
        var tip = tooltipBox(theme);
        tip.trigger = 'item';
        tip.formatter = function (p) { return esc(p.name) + '：<b>' + fmtValue(p.value, spec.fmt) + '</b>'; };
        return tip;
      })(),
      toolbox: makeToolbox(theme),
      legend: { show: false },
      series: [{
        type: 'funnel', sort: 'descending', gap: 3,
        left: '8%', right: '8%', top: 24, bottom: 12,
        minSize: '18%', maxSize: '100%',
        label: { show: spec.labels !== false, position: 'inside', color: '#fff', fontSize: 11 },
        labelLine: { show: false },
        itemStyle: { borderColor: theme.bg, borderWidth: 1.5 },
        emphasis: { label: { fontSize: 13 } },
        data: dataArr
      }]
    };
  }

  // ---- 矩形树图 ---------------------------------------------------------
  function buildTreemapTree(rows, dims, valueCol, how, depth) {
    var map = {}, order = [];
    var dim = dims[depth];
    for (var i = 0; i < rows.length; i++) {
      var k = catName(rows[i][dim]);
      if (!map[k]) { map[k] = []; order.push(k); }
      map[k].push(rows[i]);
    }
    return order.map(function (k) {
      var sub = map[k];
      if (depth === dims.length - 1) {
        var g = groupBy(sub, [], valueCol, how);
        var v = g.length && g[0].value !== null ? g[0].value : 0;
        return { name: k, value: v };
      }
      return { name: k, children: buildTreemapTree(sub, dims, valueCol, how, depth + 1) };
    });
  }

  function buildTreemap(spec, data, state, theme) {
    var rows = filteredRows(spec, data, state);
    if (!rows.length) return null;
    var dims = spec.roles.path || [];
    var valCol = spec.roles.value;
    var tree = buildTreemapTree(rows, dims, valCol, spec.agg || 'sum', 0);
    return {
      tooltip: (function () {
        var tip = tooltipBox(theme);
        tip.trigger = 'item';
        tip.formatter = function (p) {
          return '<div style="font-weight:600">' + esc(p.name) + '</div>' +
            '<div style="line-height:19px">' + esc(valCol) + '：<b>' + fmtValue(p.value, spec.fmt) + '</b></div>';
        };
        return tip;
      })(),
      toolbox: makeToolbox(theme),
      series: [{
        type: 'treemap',
        data: tree,
        roam: false,
        nodeClick: 'zoomToNode',
        breadcrumb: { show: true, bottom: 2, height: 20, itemStyle: { color: theme.split, textStyle: { color: theme.subtext, fontSize: 10 } } },
        top: 8, left: 4, right: 4, bottom: 24,
        label: { show: true, formatter: '{b}', color: '#fff', fontSize: 12 },
        upperLabel: { show: true, height: 22, color: theme.text, fontSize: 11 },
        itemStyle: { borderColor: theme.bg, borderWidth: 2, gapWidth: 2 },
        levels: [
          { itemStyle: { borderWidth: 0, gapWidth: 3 } },
          { itemStyle: { gapWidth: 2 } },
          { itemStyle: { gapWidth: 1 } }
        ]
      }]
    };
  }

  // ---- 仪表盘 -----------------------------------------------------------
  function buildGauge(spec, data, state, theme) {
    var unit = spec.unit || '';
    return {
      series: [{
        type: 'gauge',
        startAngle: 210, endAngle: -30,
        min: spec.min === undefined ? 0 : spec.min,
        max: spec.max === undefined ? 100 : spec.max,
        radius: '88%',
        center: ['50%', '58%'],
        splitNumber: 4,
        progress: { show: true, width: 14, roundCap: true, itemStyle: { opacity: 0.9 } },
        axisLine: { lineStyle: { width: 14, color: [[1, theme.split]] } },
        pointer: { width: 4, length: '55%', itemStyle: { color: theme.subtext } },
        axisTick: { show: false },
        splitLine: { length: 8, lineStyle: { width: 1, color: theme.axis } },
        axisLabel: { distance: 10, color: theme.subtext, fontSize: 9 },
        detail: {
          valueAnimation: true,
          formatter: function (v) {
            if (spec.fmt === 'percent') return roundTo(v, 1) + '%' + unit;
            return fmtValue(v, spec.fmt) + unit;
          },
          color: theme.text, fontSize: 28, fontWeight: 600, offsetCenter: [0, '42%']
        },
        title: { show: !!spec.label, offsetCenter: [0, '70%'], color: theme.subtext, fontSize: 12 },
        data: [{ value: spec.value, name: spec.label || '' }]
      }]
    };
  }

  // ---- KPI 卡片 ---------------------------------------------------------
  // 从（联动过滤后的）数据里现算 KPI 数值
  function kpiValue(spec, data, state) {
    if (spec.value !== null && spec.value !== undefined) return num(spec.value);
    var rows = filteredRows(spec, data, state);
    if (!rows.length) return null;
    var g = groupBy(rows, [], spec.roles.value, spec.agg || 'sum');
    return g.length ? g[0].value : null;
  }

  // 迷你走势的点（按 x 排序）
  function kpiSparkPoints(spec, data, state) {
    var sp = spec.spark;
    if (!sp || !sp.y) return [];
    var rows = filteredRows(spec, data, state);
    if (!rows.length) return [];
    var g = groupBy(rows, [sp.x], sp.y, sp.agg || spec.agg || 'sum');
    var pts = [];
    for (var i = 0; i < g.length; i++) pts.push({ x: g[i].keys[0], v: g[i].value });
    pts.sort(function (a, b) { return compareCatX(a.x, b.x); });
    return pts;
  }

  function kpiSparkSVG(pts, color) {
    if (!pts || pts.length < 2) return '';
    var w = 120, h = 34, pad = 3;
    var min = Infinity, max = -Infinity, i;
    for (i = 0; i < pts.length; i++) {
      var v = pts[i].v;
      if (v === null || v === undefined || !isFinite(v)) continue;
      if (v < min) min = v;
      if (v > max) max = v;
    }
    if (!isFinite(min)) return '';
    if (min === max) { min -= 1; max += 1; }
    var n = pts.length, coords = [];
    for (i = 0; i < n; i++) {
      var cv = num(pts[i].v);
      var x = pad + i * (w - 2 * pad) / (n - 1);
      var y = cv === null ? (h - pad) : (h - pad - (cv - min) / (max - min) * (h - 2 * pad));
      coords.push([Math.round(x * 100) / 100, Math.round(y * 100) / 100]);
    }
    var d = 'M ' + coords[0][0] + ' ' + coords[0][1];
    for (i = 1; i < coords.length; i++) d += ' L ' + coords[i][0] + ' ' + coords[i][1];
    var area = d + ' L ' + coords[n - 1][0] + ' ' + (h - pad) + ' L ' + coords[0][0] + ' ' + (h - pad) + ' Z';
    var last = coords[n - 1];
    return '<svg class="eazy-kpi-spark" viewBox="0 0 ' + w + ' ' + h + '"' +
      ' preserveAspectRatio="none" aria-hidden="true">' +
      '<path d="' + area + '" fill="' + color + '" opacity="0.13"></path>' +
      '<path d="' + d + '" fill="none" stroke="' + color + '" stroke-width="1.8"' +
      ' stroke-linejoin="round" stroke-linecap="round"></path>' +
      '<circle cx="' + last[0] + '" cy="' + last[1] + '" r="2.1" fill="' + color + '"></circle>' +
      '</svg>';
  }

  function deltaText(v) {
    var isRatio = Math.abs(v) <= 1;
    return isRatio ? roundTo(Math.abs(v) * 100, 1) + '%' : trimNum(Math.abs(v));
  }

  function kpiHTML(spec, data, state, theme) {
    theme = theme || THEME.light;
    state = state || { filters: {}, drill: [] };
    var pal = theme.palette || PALETTES.google.colors;
    var accent = pal[Math.abs(Number(spec.accent) || 0) % pal.length];
    var val = kpiValue(spec, data, state);
    var txt = fmtValue(val, spec.fmt);
    if (spec.prefix) txt = spec.prefix + txt;
    if (spec.unit) txt = txt + spec.unit;

    var html = '<div class="eazy-kpi" style="--eazy-accent:' + accent + '">';
    html += '<div class="eazy-kpi-head"><span class="eazy-kpi-label">' +
      esc(spec.label || '') + '</span>';
    var achieved = null, targetV = num(spec.target);
    if (spec.target !== null && spec.target !== undefined &&
        isFinite(targetV) && targetV !== 0) {
      achieved = (num(val) || 0) / targetV * 100;
      html += '<span class="eazy-kpi-badge">' +
        esc(spec.targetLabel || ('目标 ' + fmtValue(targetV, spec.fmt))) + '</span>';
    }
    html += '</div>';

    html += '<div class="eazy-kpi-main"><span class="eazy-kpi-value">' + esc(txt) + '</span>';
    if (spec.delta !== null && spec.delta !== undefined) {
      var dv = Number(spec.delta);
      if (isFinite(dv)) {
        var good = (dv >= 0) !== !!spec.inverse;
        html += '<span class="eazy-kpi-delta ' + (good ? 'eazy-up' : 'eazy-down') + '">' +
          (dv >= 0 ? '▲' : '▼') + ' ' + deltaText(dv) + '</span>';
        if (spec.deltaLabel) {
          html += '<span class="eazy-kpi-deltalabel">' + esc(spec.deltaLabel) + '</span>';
        }
      }
    }
    html += '</div>';

    var hint = spec.hint;
    if (!hint && spec.link) hint = '联动组 ' + spec.link + ' · 点同组图表筛选';
    if (hint) html += '<div class="eazy-kpi-hint">' + esc(hint) + '</div>';

    var spark = kpiSparkSVG(kpiSparkPoints(spec, data, state), accent);
    if (spark) html += '<div class="eazy-kpi-sparkwrap">' + spark + '</div>';
    if (achieved !== null) {
      var w = Math.max(0, Math.min(100, achieved));
      html += '<div class="eazy-kpi-progress"><div class="eazy-kpi-track">' +
        '<span style="width:' + roundTo(w, 1) + '%;background:' + accent + '"></span></div>' +
        '<span class="eazy-kpi-pct' + (achieved >= 100 ? ' eazy-pct-done' : '') + '">' +
        roundTo(achieved, 0) + '%</span></div>';
    }
    html += '</div>';
    return html;
  }

  // ---- 分发 -------------------------------------------------------------
  var BUILDERS = {
    bar: buildCartesian,
    line: buildCartesian,
    combo: buildCombo,
    pie: buildPie,
    scatter: buildScatter,
    histogram: buildHistogram,
    heatmap: buildHeatmap,
    box: buildBox,
    funnel: buildFunnel,
    treemap: buildTreemap,
    gauge: buildGauge
  };

  // 扩展图表：eazy_extra_a.js / eazy_extra_b.js 等文件注册进来
  var EXTRA = EazyViz.extraBuilders = EazyViz.extraBuilders || {};
  // HTML 类图表（KPI、表格、词云、进度条、瓦片等，不用 ECharts）
  var HTML_BUILDERS = EazyViz.htmlBuilders = EazyViz.htmlBuilders || {};
  HTML_BUILDERS.kpi = kpiHTML;

  function emptyOption(theme) {
    return {
      backgroundColor: 'transparent',
      graphic: {
        type: 'text', left: 'center', top: 'middle',
        style: { text: '当前条件下没有数据', fill: theme.subtext, fontSize: 13, font: FONT }
      },
      xAxis: { show: false },
      yAxis: { show: false },
      series: []
    };
  }

  function buildOption(spec, data, state, theme) {
    theme = theme || THEME.light;
    state = state || { filters: {}, drill: [] };
    var builder = BUILDERS[spec.type] || EXTRA[spec.type];
    if (!builder) throw new Error('不支持的图表类型: ' + spec.type);
    var opt = builder(spec, data || { cols: [], rows: [] }, state, theme);
    if (!opt) return null;
    opt.backgroundColor = 'transparent';
    opt.textStyle = { fontFamily: FONT, color: theme.text, fontSize: 12 };
    // 配色库：ECharts 默认按 option.color 循环取色，builder 自己指定过的优先
    if (!opt.color && theme.palette) opt.color = theme.palette.slice();
    opt.animation = true;
    opt.animationDuration = 380;
    opt.animationDurationUpdate = 260;
    opt.animationEasing = 'cubicOut';
    return opt;
  }

  // ======================================================================
  // 5. 页面状态 / 交互
  // ======================================================================
  EazyViz.charts = [];
  EazyViz.links = {};
  EazyViz.page = {};
  EazyViz.dataStore = {};
  // components.v2 里页面挂在 Shadow DOM 中：scope 指向 ShadowRoot，host 指向宿主元素。
  // 静态 HTML 导出时两者为 null，所有查询自动退化为 document。
  EazyViz.scope = null;
  EazyViz.host = null;
  EazyViz.onSelect = null;

  function scopeNode() { return EazyViz.scope || document; }

  function findOne(sel) {
    var n = scopeNode();
    try { var el = n.querySelector(sel); if (el) return el; } catch (e) { /* ignore */ }
    return document.querySelector(sel);
  }

  function findAll(sel) {
    var n = scopeNode();
    try { return n.querySelectorAll(sel); } catch (e) { return document.querySelectorAll(sel); }
  }

  function chartById(id) {
    for (var i = 0; i < EazyViz.charts.length; i++) {
      if (EazyViz.charts[i].spec.id === id) return EazyViz.charts[i];
    }
    return null;
  }

  function chartByIndex(idx) {
    for (var i = 0; i < EazyViz.charts.length; i++) {
      if (EazyViz.charts[i].index === idx) return EazyViz.charts[i];
    }
    return null;
  }

  function syncFilters(c) {
    var f = {};
    if (c.spec.link && EazyViz.links && EazyViz.links[c.spec.link]) {
      var link = EazyViz.links[c.spec.link];
      // 发起联动的图自己不过滤（保持全量 + 高亮），其他图按类目过滤
      if (link.sourceId !== c.spec.id && hasCol(c.data, link.dim)) {
        f[link.dim] = link.value;
      }
    }
    c.state.filters = f;
  }

  function renderToolbar(c) {
    var el = findOne('[data-eazy-toolbar="' + c.index + '"]');
    if (!el) return;
    var spec = c.spec, html = '';
    if (spec.drill && spec.drill.length) {
      html += '<div class="eazy-crumb">';
      html += '<button data-chart="' + c.index + '" data-crumb="0">全部</button>';
      for (var i = 0; i < c.state.drill.length; i++) {
        html += '<span class="sep">›</span>';
        var cur = (i === c.state.drill.length - 1) ? ' class="cur"' : '';
        html += '<button' + cur + ' data-chart="' + c.index + '" data-crumb="' + (i + 1) + '">' +
          esc(c.state.drill[i].value) + '</button>';
      }
      html += '</div>';
      if (c.state.drill.length) {
        html += '<button class="eazy-btn" data-back="' + c.index + '">↰ 返回</button>';
      }
      html += '<span class="eazy-hint">点击图形逐级下钻</span>';
    } else if (spec.link && !HTML_BUILDERS[spec.type]) {
      html += '<span class="eazy-hint" style="margin-left:0">点击图形可联动同组图表</span>';
    }
    el.innerHTML = html;
  }

  function renderChart(c) {
    var spec = c.spec;
    var htmlBuilder = HTML_BUILDERS[spec.type];
    if (htmlBuilder) {
      c.el.innerHTML = htmlBuilder(spec, c.data, c.state, c.theme);
      renderToolbar(c);
      return;
    }
    if (!c.ec) {
      c.ec = global.echarts.init(c.el, null, { renderer: 'canvas' });
      c.ec.on('click', function (p) { onChartClick(c, p); });
      c.ec.on('legendselectchanged', function (e) {
        c.state.legendSel = e.selected;
      });
    }
    var opt = buildOption(spec, c.data, c.state, c.theme);
    if (!opt) {
      c.ec.clear();
      c.ec.setOption(emptyOption(c.theme), true);
      renderToolbar(c);
      return;
    }
    c.ec.setOption(opt, true);
    renderToolbar(c);
    c._w = c.el.clientWidth;
  }

  function onChartClick(c, p) {
    if (!p || p.componentType !== 'series') return;
    var spec = c.spec;
    var xdim = currentXDim(spec, c.state);
    if (!xdim || p.name === null || p.name === undefined) return;
    var value = String(p.name);
    if (value === '其他') return;

    var drilled = false;
    if (spec.drill && c.state.drill.length < spec.drill.length - 1) {
      var depth = c.state.drill.length;
      if (spec.drill[depth] === xdim) {
        c.state.drill.push({ dim: xdim, value: value });
        drilled = true;
      }
    }
    if (spec.link) {
      setLink(spec.link, xdim, value, c);
    } else if (drilled) {
      renderChart(c);
    }
    syncFilterBar();
    if (EazyViz.onSelect) {
      try {
        EazyViz.onSelect({
          chart: spec.id,
          title: spec.title || '',
          type: spec.type,
          dim: xdim,
          value: value,
          drill: (c.state.drill || []).slice(),
          link: (spec.link && EazyViz.links[spec.link]) ? EazyViz.links[spec.link] : null
        });
      } catch (err) { /* 回调异常不影响渲染 */ }
    }
  }

  function reRenderGroup(group) {
    for (var i = 0; i < EazyViz.charts.length; i++) {
      var c = EazyViz.charts[i];
      if (c.spec.link !== group) continue;
      syncFilters(c);
      renderChart(c);
    }
  }

  function setLink(group, dim, value, chart) {
    var cur = EazyViz.links[group];
    if (cur && cur.dim === dim && cur.value === value && cur.sourceId === chart.spec.id) {
      delete EazyViz.links[group];
    } else {
      EazyViz.links[group] = { dim: dim, value: value, sourceId: chart.spec.id };
    }
    reRenderGroup(group);
  }

  function clearLink(group) {
    delete EazyViz.links[group];
    reRenderGroup(group);
    syncFilterBar();
  }

  function syncFilterBar() {
    var el = findOne('#eazy-filters');
    if (!el) return;
    var groups = Object.keys(EazyViz.links || {});
    var html = '<span class="eazy-filters-label">联动筛选</span>';
    if (!groups.length) {
      el.style.display = 'none';
      el.innerHTML = html;
      return;
    }
    for (var i = 0; i < groups.length; i++) {
      var g = groups[i], link = EazyViz.links[g];
      html += '<span class="eazy-chip"><span>' + esc(link.dim) + ' = <b>' + esc(link.value) +
        '</b></span><span class="eazy-chip-x" data-clear-link="' + esc(g) + '" title="清除">×</span></span>';
    }
    el.innerHTML = html;
    el.style.display = '';
  }

  function handleCrumb(c, depth) {
    if (!c) return;
    c.state.drill = c.state.drill.slice(0, depth);
    renderChart(c);
  }

  function handleBack(c) {
    if (!c || !c.state.drill.length) return;
    c.state.drill.pop();
    renderChart(c);
  }

  function resizeAll() {
    for (var i = 0; i < EazyViz.charts.length; i++) {
      var c = EazyViz.charts[i];
      if (!c.ec) continue;
      var w = c.el.clientWidth;
      if (c._w === w) continue;
      c._w = w;
      c.ec.resize();
    }
  }

  // ----- 卡片代码区（查看 / 复制生成这张图的 Python 代码）-----
  function toggleCode(idx) {
    var box = findOne('[data-eazy-codebox="' + idx + '"]');
    if (!box) return;
    var open = box.classList.toggle('is-open');
    var btn = findOne('[data-eazy-code="' + idx + '"]');
    if (btn) btn.textContent = open ? '收起代码' : '代码';
  }

  function fallbackCopy(text) {
    try {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    } catch (err) { /* 忽略 */ }
  }

  function copyCode(idx, btn) {
    var box = findOne('[data-eazy-codebox="' + idx + '"]');
    if (!box) return;
    var code = box.querySelector('code');
    var text = code ? code.textContent : '';
    var done = function () {
      if (!btn) return;
      var old = btn.textContent;
      btn.textContent = '已复制';
      setTimeout(function () { btn.textContent = old; }, 1400);
    };
    try {
      if (global.navigator && global.navigator.clipboard && global.navigator.clipboard.writeText) {
        global.navigator.clipboard.writeText(text).then(done, function () { fallbackCopy(text); done(); });
        return;
      }
    } catch (err) { /* 忽略, 走回退 */ }
    fallbackCopy(text);
    done();
  }

  function bindGlobalEvents() {
    scopeNode().addEventListener('click', function (e) {
      var el = e.target;
      while (el && el !== document) {
        if (el.getAttribute) {
          if (el.hasAttribute('data-crumb')) {
            handleCrumb(chartByIndex(Number(el.getAttribute('data-chart'))),
              Number(el.getAttribute('data-crumb')));
            return;
          }
          var codeIdx = el.getAttribute('data-eazy-code');
          if (codeIdx !== null && codeIdx !== undefined) { toggleCode(Number(codeIdx)); return; }
          var copyIdx = el.getAttribute('data-eazy-copy');
          if (copyIdx !== null && copyIdx !== undefined) { copyCode(Number(copyIdx), el); return; }
          if (el.hasAttribute('data-eazy-theme')) {
            setTheme(EazyViz.page.theme === 'dark' ? 'light' : 'dark');
            return;
          }
          if (el.hasAttribute('data-eazy-reset')) {
            clearAllLinks();
            return;
          }
          if (el.hasAttribute('data-back')) {
            handleBack(chartByIndex(Number(el.getAttribute('data-back'))));
            return;
          }
          var gl = el.getAttribute('data-clear-link');
          if (gl) { clearLink(gl); return; }
        }
        el = el.parentNode;
      }
    });

    scopeNode().addEventListener('change', function (e) {
      var el = e.target;
      if (el && el.getAttribute && el.getAttribute('data-eazy-palette') !== null) {
        setPalette(el.value);
      }
    });

    var onResize = debounce(resizeAll, 140);
    global.addEventListener('resize', onResize);
    if (global.ResizeObserver) {
      try {
        var ro = new ResizeObserver(debounce(resizeAll, 160));
        EazyViz.charts.forEach(function (c) { ro.observe(c.el); });
      } catch (err) { /* ignore */ }
    }
  }

  function setTheme(name) {
    var themeName = (name === 'dark') ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', themeName);
    if (document.body) document.body.setAttribute('data-theme', themeName);
    if (EazyViz.host && EazyViz.host.setAttribute) {
      EazyViz.host.setAttribute('data-theme', themeName);
      EazyViz.host.setAttribute('data-palette', EazyViz.page.palette || 'google');
    }
    EazyViz.page.theme = themeName;
    for (var i = 0; i < EazyViz.charts.length; i++) {
      var c = EazyViz.charts[i];
      c.theme = themeFor(themeName, c.paletteName || EazyViz.page.palette);
      if (c.ec) {
        try { c.ec.dispose(); } catch (e) { /* ignore */ }
        c.ec = null;
      }
      renderChart(c);
    }
    syncFilterBar();
  }

  function setPalette(name) {
    var pname = PALETTES[name] ? name : 'google';
    EazyViz.page.palette = pname;
    var sel = findOne('[data-eazy-palette]');
    if (sel) sel.value = pname;
    for (var i = 0; i < EazyViz.charts.length; i++) {
      var c = EazyViz.charts[i];
      c.paletteName = c.spec.palette || pname;
      c.theme = themeFor(c.spec.theme || EazyViz.page.theme || 'light', c.paletteName);
      if (c.ec) {
        try { c.ec.dispose(); } catch (e) { /* ignore */ }
        c.ec = null;
      }
      renderChart(c);
    }
    syncFilterBar();
    return pname;
  }

  function clearAllLinks() {
    EazyViz.links = {};
    for (var i = 0; i < EazyViz.charts.length; i++) {
      var c = EazyViz.charts[i];
      syncFilters(c);
      renderChart(c);
    }
    syncFilterBar();
  }

  EazyViz.init = function (page, rootEl) {
    EazyViz.page = page || {};
    EazyViz.charts = [];
    EazyViz.links = {};
    EazyViz.dataStore = global.EAZY_DATA || {};
    EazyViz.scope = rootEl || null;
    EazyViz.host = (rootEl && rootEl.host) ? rootEl.host : null;
    EazyViz.page.palette = PALETTES[EazyViz.page.palette] ? EazyViz.page.palette : 'google';
    if (EazyViz.host && EazyViz.host.setAttribute) {
      EazyViz.host.setAttribute('data-theme', EazyViz.page.theme || 'light');
      EazyViz.host.setAttribute('data-palette', EazyViz.page.palette);
    }
    var palSel = findOne('[data-eazy-palette]');
    if (palSel) palSel.value = EazyViz.page.palette;

    var els = findAll('[data-eazy-chart]');
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      var idx = Number(el.getAttribute('data-eazy-chart'));
      var spec = (EazyViz.page.charts || [])[idx];
      if (!spec) continue;
      var themeName = spec.theme || EazyViz.page.theme || 'light';
      var palName = spec.palette || EazyViz.page.palette || 'google';
      var c = {
        spec: spec, el: el, index: idx,
        paletteName: palName,
        theme: themeFor(themeName, palName),
        state: { filters: {}, drill: [], legendSel: null },
        data: spec.dataRef ? EazyViz.dataStore[spec.dataRef] : null,
        ec: null, _w: 0
      };
      EazyViz.charts.push(c);
    }
    EazyViz.charts.forEach(function (c) { renderChart(c); });
    syncFilterBar();
    bindGlobalEvents();
    document.documentElement.setAttribute('data-eazy-ready', '1');
    document.documentElement.setAttribute('data-eazy-count', String(EazyViz.charts.length));
    return EazyViz;
  };

  // ======================================================================
  // 6. 测试用导出
  // ======================================================================
  EazyViz.core = {
    builders: BUILDERS,
    extraBuilders: EXTRA,
    htmlBuilders: HTML_BUILDERS,
    util: {
      isNum: isNum, num: num, esc: esc, trimNum: trimNum, roundTo: roundTo,
      compactCN: compactCN, fmtValue: fmtValue, truncate: truncate, catName: catName,
      rowsOf: rowsOf, hasCol: hasCol, currentXDim: currentXDim,
      filteredRows: filteredRows, median: median, quantile: quantile,
      groupBy: groupBy, makeGrid: makeGrid, makeLegend: makeLegend,
      makeToolbox: makeToolbox, axisTitle: axisTitle, axisLabelRotate: axisLabelRotate,
      applyLim: applyLim, compareCatX: compareCatX, catRanker: catRanker,
      setAxisName: setAxisName, makeCategoryAxis: makeCategoryAxis,
      makeValueAxis: makeValueAxis, tooltipBox: tooltipBox, axisTooltip: axisTooltip,
      sourceSelection: sourceSelection, dimItem: dimItem, emptyOption: emptyOption,
      THEME: THEME, FONT: FONT, SEP: SEP,
      PALETTES: PALETTES, themeFor: themeFor, mixColor: mixColor,
      kpiValue: kpiValue, kpiSparkPoints: kpiSparkPoints, kpiSparkSVG: kpiSparkSVG
    },
    groupBy: groupBy,
    filteredRows: filteredRows,
    currentXDim: currentXDim,
    buildOption: buildOption,
    fmtValue: fmtValue,
    catName: catName,
    quantile: quantile,
    median: median,
    rowsOf: rowsOf,
    kpiHTML: kpiHTML,
    buildTreemapTree: buildTreemapTree,
    onChartClick: onChartClick,
    setLink: setLink,
    setTheme: setTheme,
    setPalette: setPalette,
    PALETTES: PALETTES,
    clearAllLinks: clearAllLinks,
    syncFilterBar: syncFilterBar,
    THEME: THEME
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = EazyViz;
  }
})(typeof window !== 'undefined' ? window : this);
