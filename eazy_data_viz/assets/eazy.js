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

  // 自动缩略单位（帆软 FineBI 风格）：>=1e4 用「万」，>=1e8 用「亿」。
  // 换算后的数字 < 100 保留 1 位小数，>= 100 取整：
  //   123456 → 12.3万，12345678 → 1235万，1.5e8 → 1.5亿
  // 缩略出来的数字不带千分位（12.3万 而不是 12.3,0000），末尾的 .0 去掉（10000 → 1万），
  // 负数保留负号，0 → 0（走下面的千分位分支）。
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

  // ======================================================================
  // 显式单位（spec.unit）：千 / 万 / 百万 / 亿，或直接给倍数 1e3/1e4/1e6/1e8。
  // 数值统一按 v / 倍数 展示，最多 2 位小数、去掉末尾 0，后面接单位字：
  //   2500000 + unit="百万" → 2.5百万
  // 与 fmt=percent/currency/raw/thousands 同时存在时以 fmt 为准（unit 不生效）。
  // ======================================================================
  var UNIT_TEXTS = { 1000: '千', 10000: '万', 1000000: '百万', 100000000: '亿' };
  // 扩展图表（table / group_kpi 等）内部调用 fmtValue 时只传 fmt，
  // 用这个模块变量兜底当前正在构建的 spec，才能拿到 unit
  var activeSpec = null;
  // 当前渲染时的容器宽度（px）：窄卡片里图例要挪到底部、字号要收，靠它判断；0 = 未知
  var activeWidth = 0;

  function unitInfo(spec) {
    var u = spec && spec.unit;
    if (u === null || u === undefined || u === '') return null;
    if (typeof u === 'number') {
      if (!isFinite(u) || u <= 0) return null;
      return { scale: u, text: UNIT_TEXTS[String(Math.round(u))] || '' };
    }
    var s = String(u).replace(/^\s+|\s+$/g, '');
    if (s === '千') return { scale: 1e3, text: s };
    if (s === '万') return { scale: 1e4, text: s };
    if (s === '百万') return { scale: 1e6, text: s };
    if (s === '亿') return { scale: 1e8, text: s };
    // 「 单 / % / ℃ / 万元」这类纯文字单位不做换算，只当后缀拼接
    return null;
  }

  // fmt 优先：这几种格式下 unit 不参与换算
  function unitBlocked(fmt) {
    return fmt === 'raw' || fmt === 'percent' ||
      fmt === 'thousands' || fmt === 'currency';
  }

  function fmtUnit(n, ui) {
    return roundTo(n / ui.scale, 2) + (ui.text || '');
  }

  // 纯文字单位：数值不动，末尾补后缀（已经带同样的后缀就不重复补）
  function unitSuffix(spec, txt) {
    var u = spec && spec.unit;
    if (u === null || u === undefined || u === '') return txt;
    if (unitInfo(spec)) return txt;
    var s = String(u);
    return txt.slice(-s.length) === s ? txt : txt + s;
  }

  // 构建图时挂上当前 spec，供只传 fmt 的扩展脚本读单位；fn 结束后恢复
  function withSpec(spec, fn) {
    var prev = activeSpec;
    activeSpec = spec;
    try {
      return fn();
    } finally {
      activeSpec = prev;
    }
  }

  function fmtValue(v, fmt, spec) {
    if (v === null || v === undefined || v === '') return '-';
    if (typeof v === 'object') v = v.value;
    var n = num(v);
    if (n === null) return String(v);
    if (!spec) spec = activeSpec;
    var ui = unitInfo(spec);
    // 明细表为了可读性把 compact 换成了 thousands，这类调用仍按显式单位展示，
    // 否则表格里看不出「万 / 亿」
    var useUnit = !!ui && (!unitBlocked(fmt) || (fmt === 'thousands' && spec && spec.type === 'table'));
    if (useUnit) return fmtUnit(n, ui);
    var s;
    switch (fmt) {
      case 'raw': s = trimNum(n); break;
      case 'percent': s = roundTo(n, 1) + '%'; break;
      case 'thousands': s = groupThousand(n); break;
      case 'currency': s = '¥' + groupThousand(roundTo(n, 2)); break;
      default: s = compactCN(n);
    }
    return unitSuffix(spec, s);
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
      } else if (how === 'unique') {
        // 去重计数：保留原始值（文本也数），忽略 null / NaN / 空串
        var uv = measure ? r[measure] : null;
        if (uv !== null && uv !== undefined && uv === uv && String(uv) !== '') {
          if (!rec.uniq) rec.uniq = {};
          rec.uniq['$' + String(uv)] = 1;
          rec.cnt++;
        }
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
      if (how === 'unique') g.value = g.uniq ? Object.keys(g.uniq).length : 0;
      else if (how === 'count') g.value = g.cnt;
      else if (how === 'sum') g.value = g.cnt ? g.sum : null;
      else if (how === 'mean') g.value = g.cnt ? g.sum / g.cnt : null;
      else if (how === 'max') g.value = g.vals.length ? Math.max.apply(null, g.vals) : null;
      else if (how === 'min') g.value = g.vals.length ? Math.min.apply(null, g.vals) : null;
      else if (how === 'median') g.value = g.vals.length ? median(g.vals) : null;
      else g.value = g.sum;
      delete g.vals;
      delete g.uniq;
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
      // 有图例时顶部要同时留给「图例 + 纵轴名（nameLocation:end, nameGap:14）」，
      // 60 才不会让纵轴名压在图例文字上
      top: opts.legend ? 60 : 30,
      bottom: 44
    };
    if (opts.zoom) grid.bottom = 76;
    if (opts.rightExtra) grid.right = opts.rightExtra;
    return grid;
  }

  function makeLegend(theme, selected, show) {
    if (!show) return { show: false };
    var legend = {
      // width 要写死：不给宽度时 ECharts 会把图例当成无限长，
      // 项目多了就直接溢出卡片（最后一项被截断），而不是分页。
      show: true, type: 'scroll', top: 6, left: 'center', width: '92%',
      itemWidth: 10, itemHeight: 8, itemGap: 8,
      pageIconColor: theme.subtext, pageIconInactiveColor: theme.axis,
      pageTextStyle: { color: theme.subtext, fontSize: 10 },
      textStyle: { color: theme.subtext, fontSize: 10 }
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
  // 1.5.6：带数字后缀的类目（"1月" / "第2季度" / "2026年"）按「数字优先」比，
  // 否则 "10月" < "2月" 会按字符串比较把月份排乱。
  function firstNum(v) {
    var m = String(v === null || v === undefined ? '' : v).match(/-?\d+(?:\.\d+)?/);
    return m ? parseFloat(m[0]) : null;
  }

  function compareCatX(a, b) {
    var sa = String(a), sb = String(b);
    var na = Number(sa), nb = Number(sb);
    if (sa !== '' && sb !== '' && isFinite(na) && isFinite(nb)) return na - nb;
    var fa = firstNum(sa), fb = firstNum(sb);
    if (fa !== null && fb !== null && fa !== fb) return fa - fb;
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

  // 按 Python 端算好的类目顺序（spec.sortRank）排序：
  // sort="年-月" 这类「按另一列排」的写法，Python 会算好每个类目的代表值顺序。
  function listRanker(list) {
    if (!list || !list.length) return null;
    var map = {};
    for (var i = 0; i < list.length; i++) map[String(list[i])] = i;
    return function (a, b) {
      var ia = map[String(a)], ib = map[String(b)];
      if (ia === undefined || ib === undefined) return 0;
      return ia - ib;
    };
  }

  // 系列的默认顺序：跟「color 列自己的顺序」走，而不是按合计大小排。
  // 原因：按合计排会让图例/柱子左右位置随着「当前指标」跳（2025 忽左忽右），
  // 用户看到的是「同一张图换了个指标就换了图」。合计排序只有显式 sort="desc"/"asc" 才做。
  function seriesRanker(data, dim, names) {
    var rank = catRanker(data, dim);
    if (rank) return rank;                       // 声明过顺序的分类列
    var kind = ((data && data.kinds) || {})[dim];
    if (kind === 'time') return compareCatX;     // 日期/年月：按自然序
    if (kind === 'num') {
      return function (a, b) {
        var na = num(a), nb = num(b);
        if (na === null || nb === null) return 0;
        return na - nb;
      };
    }
    // 文本但值里带数字（'2025年' / '第2季度'）：按数字升序
    var hasNum = false;
    for (var i = 0; i < names.length; i++) {
      if (nameOrder(names[i]) !== null) { hasNum = true; break; }
    }
    if (!hasNum) return null;                    // 普通文本：保持 df 里的出现顺序
    return function (a, b) {
      var na = nameOrder(a), nb = nameOrder(b);
      if (na === null || nb === null) return 0;
      return na - nb;
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

  // 解析中文 BI 里常见的日期类目：
  //   YYYY-MM-DD / YYYY/MM/DD（可带 HH:MM[:SS]）、YYYY-MM / YYYY/MM
  function parseCatDate(v) {
    var s = String(v);
    var m = /^(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}:\d{2})(?::\d{2})?)?$/.exec(s);
    if (!m) m = /^(\d{4})\/(\d{1,2})\/(\d{1,2})(?:[ T](\d{1,2}:\d{2})(?::\d{2})?)?$/.exec(s);
    if (m) return { y: m[1], m: Number(m[2]), d: Number(m[3]), hm: m[4] || '', prec: 'day' };
    m = /^(\d{4})-(\d{1,2})$/.exec(s);
    if (!m) m = /^(\d{4})\/(\d{1,2})$/.exec(s);
    if (m) return { y: m[1], m: Number(m[2]), d: 0, hm: '', prec: 'month' };
    return null;
  }

  // 中文日期文本：同一年省略年份（3月1日 / 3月），跨年补上（2024年3月1日 / 2024年3月）
  function dateCatText(p, sameYear) {
    var head = sameYear ? '' : (p.y + '年');
    if (p.prec === 'month') return head + p.m + '月';
    return head + p.m + '月' + p.d + '日' + (p.hm ? ' ' + p.hm : '');
  }

  // 整个轴都能解析、粒度一致时才本地化；全部同一年才省略年份
  function dateCatMode(cats) {
    var year = null, prec = null, sameYear = true;
    for (var i = 0; i < cats.length; i++) {
      var p = parseCatDate(cats[i]);
      if (!p) return null;
      if (year === null) { year = p.y; prec = p.prec; }
      if (p.y !== year) sameYear = false;
      if (p.prec !== prec) return null;
    }
    return year === null ? null : { sameYear: sameYear };
  }

  function makeCategoryAxis(spec, cats, theme) {
    // 类目很多时（例如按日期画线），自动抽稀标签，否则会挤成一堆斜字
    var n = cats.length;
    var dense = n > 12;
    var dm = dateCatMode(cats);
    // 跨年的月度轴（例如 17 个月）如果写成一行「2025年3月」，
    // 密集时斜着写也会互相重叠；拆成两行（年 / 月）宽度减半，看得清。
    var yearOnOwnLine = dense && !!dm && !dm.sameYear;
    // 标记一下：两行标签比单行高一行，后面要把 x 轴名与 grid 底部一起下让
    var twoLine = yearOnOwnLine;
    // 两行标签比单行占地，抽稀要狠一点（大约 6 个）
    var interval = dense ? Math.max(1, Math.ceil(n / (yearOnOwnLine ? 6 : 10)) - 1) : 0;
    var hasUnit = !!unitInfo(spec);
    // 坐标轴显示文本：日期按中文习惯缩短 / 数值按显式单位换算 / 其它沿用截断
    function labelText(v) {
      var p = dm ? parseCatDate(v) : null;
      if (p) {
        if (yearOnOwnLine && p.prec === 'month') return p.y + '年\n' + p.m + '月';
        if (yearOnOwnLine && p.prec === 'day') return p.y + '年\n' + p.m + '月' + p.d + '日';
        return dateCatText(p, dm.sameYear);
      }
      if (hasUnit && /^-?\d+(\.\d+)?$/.test(String(v))) return fmtValue(v, spec.fmt, spec);
      return truncate(v, 14);
    }
    var shown = [];
    for (var si = 0; si < n; si++) shown.push(labelText(cats[si]));
    var rotate = dense ? (axisLabelRotate(shown) > 0 ? 30 : 0) : axisLabelRotate(shown);
    var axis = {
      type: 'category',
      data: cats,
      boundaryGap: true,
      axisTick: { show: false },
      axisLine: { lineStyle: { color: theme.axis } },
      axisLabel: {
        color: theme.subtext, hideOverlap: true,
        interval: interval,
        rotate: yearOnOwnLine ? 0 : rotate,
        lineHeight: yearOnOwnLine ? 14 : 12,
        // 注意：只缩短坐标轴文本，类目原始值不变，tooltip 表头仍是完整日期
        formatter: function (v) { return labelText(v); }
      },
      splitLine: { show: false }
    };
    if (twoLine) axis.__twoLine = true;
    return axis;
  }

  function makeValueAxis(spec, theme, lim) {
    var axis = {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: theme.split, type: 'dashed' } },
      axisLabel: {
        color: theme.subtext,
        formatter: function (v) { return fmtValue(v, spec.fmt, spec); }
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
      // 表头用原始类目值：日期类目在坐标轴上会缩成「3月1日」，tooltip 里要看完整日期
      var headVal = params[0].axisValue;
      if (headVal === undefined || headVal === null || headVal === '') {
        headVal = params[0].axisValueLabel || params[0].name;
      }
      var head = '<div style="font-weight:600;margin-bottom:4px">' +
        esc(headVal) + '</div>';
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
          esc(p.seriesName) + '</span><b style="margin-left:10px">' + fmtValue(raw, spec.fmt, spec) + '</b></div>'
        );
      }
      if (stacked && hasTotal && params.length > 1) {
        lines.push('<div style="border-top:1px dashed ' + theme.axis +
          ';margin-top:4px;padding-top:4px;display:flex"><span style="flex:1">合计</span><b>' +
          fmtValue(total, spec.fmt, spec) + '</b></div>');
      }
      return head + lines.join('');
    };
    return tip;
  }

  // ======================================================================
  // 4. 各图表 option 构造
  // ======================================================================
  // ---- 联动方向 ---------------------------------------------------------
  // both：双向（默认）；out：单向出（只发起）；in：单向进（只接收）
  function linkMode(spec) {
    var m = spec && spec.linkMode;
    return (m === 'in' || m === 'out') ? m : 'both';
  }
  function canSendLink(spec) { return !!spec.link && linkMode(spec) !== 'in'; }
  function canRecvLink(spec) { return !!spec.link && linkMode(spec) !== 'out'; }

  // 联动条件统一成 [{dim, value}...]：多级下钻时一条联动会带多个维度。
  // 旧数据（只有 dim/value）自动包成一条，外部代码读 link.dim / link.value 仍然有效。
  function linkConds(link) {
    if (!link) return [];
    if (link.conds && link.conds.length) return link.conds;
    if (link.dim === null || link.dim === undefined || link.dim === '') return [];
    return [{ dim: link.dim, value: link.value }];
  }

  function makeLink(conds, sourceId) {
    var list = [], i;
    for (i = 0; i < conds.length; i++) {
      var c = conds[i];
      if (!c || c.dim === null || c.dim === undefined || c.dim === '') continue;
      list.push({ dim: String(c.dim), value: String(c.value === null || c.value === undefined ? '' : c.value) });
    }
    if (!list.length) return null;
    var last = list[list.length - 1];
    return { dim: last.dim, value: last.value, conds: list, sourceId: sourceId };
  }

  function sameLink(a, b) {
    if (!a || !b) return false;
    if (a.sourceId !== b.sourceId) return false;
    var ca = linkConds(a), cb = linkConds(b);
    if (ca.length !== cb.length) return false;
    for (var i = 0; i < ca.length; i++) {
      if (String(ca[i].dim) !== String(cb[i].dim)) return false;
      if (String(ca[i].value) !== String(cb[i].value)) return false;
    }
    return true;
  }

  function sourceSelection(spec, state) {
    if (!spec.link || !EazyViz.links) return null;
    var link = EazyViz.links[spec.link];
    if (!link || link.sourceId !== spec.id) return null;
    var xdim = currentXDim(spec, state);
    if (!xdim) return null;
    var conds = linkConds(link);
    // 当前这一级找不到时，用最深一级兜底（比如柱状图重画后类目名一致的情况）
    for (var i = 0; i < conds.length; i++) {
      if (String(conds[i].dim) === String(xdim)) return conds[i].value;
    }
    return null;
  }

  // ---- 指定类目颜色 -----------------------------------------------------
  // spec.colors = {类目名: 颜色}：命中的类目用指定色，其余走调色板。
  function catColor(spec, name) {
    var m = spec && spec.colors;
    if (!m || name === null || name === undefined) return null;
    var v = m[name];
    if (v === undefined) v = m[String(name)];
    return (typeof v === 'string' && v) ? v : null;
  }

  // 把颜色刷到「值 / {value,itemStyle}」两种形态的 data item 上
  function paintItem(item, color) {
    if (!color) return item;
    if (item && typeof item === 'object') {
      item.itemStyle = item.itemStyle || {};
      item.itemStyle.color = color;
      return item;
    }
    return { value: item, itemStyle: { color: color } };
  }

  function paintTree(spec, nodes) {
    if (!nodes) return;
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      if (!n || typeof n !== 'object') continue;
      var c = catColor(spec, n.name);
      if (c) {
        n.itemStyle = n.itemStyle || {};
        n.itemStyle.color = c;
      }
      if (n.children) paintTree(spec, n.children);
    }
  }

  function dimItem(v, sel, cat) {
    if (sel === null || sel === undefined) return v;
    if (cat === sel) return v;
    return { value: v, itemStyle: { opacity: 0.28 } };
  }

  // ---- 同比（yoy）------------------------------------------------------
  // 规则：图中恰好 2 条 color 系列时，类目值大的那条当"本期"、小的当"上期"。
  // 例：color="年份"，2026 vs 2025 → 2026 同比 2025。
  // 系列名不是数字时（如"华东"/"华南"），退化为总和大的当本期。
  // 系列名里的第一个数字：'2026年' -> 2026、'第2季度' -> 2、'2026-06' -> 2026。
  // 用户常常把年份写成 '2025年 / 2026年'（不是纯数字），直接 num() 解析失败，
  // 这时只能退化成「合计大的算本期」——数据里 2026 只到 8 月时 2026 合计更小，
  // 同比方向就会反。所以先按名字里的数字定大小，再退回合计。
  function nameOrder(v) {
    var m = String(v === null || v === undefined ? '' : v).match(/-?\d+(?:\.\d+)?/);
    return m ? parseFloat(m[0]) : null;
  }

  function yoyPlan(seriesNames, seriesTotals) {
    var a = seriesNames[0], b = seriesNames[1];
    var na = num(a), nb = num(b);
    if (na === null || nb === null || na === nb) {
      var oa = nameOrder(a), ob = nameOrder(b);
      if (oa !== null && ob !== null && oa !== ob) {
        na = oa;
        nb = ob;
      }
    }
    var cur;
    if (na !== null && nb !== null && na !== nb) {
      cur = (na > nb) ? a : b;
    } else if ((seriesTotals[b] || 0) > (seriesTotals[a] || 0)) {
      cur = b;
    } else {
      cur = a;
    }
    return { current: cur, base: (cur === a) ? b : a };
  }

  function yoyGrowth(cur, base) {
    var c = num(cur), b = num(base);
    if (c === null || b === null || b === 0) return null;
    return (c - b) / Math.abs(b) * 100;
  }

  function yoyItem(item, growth, spec, theme) {
    var obj = (item !== null && typeof item === 'object' && !(item instanceof Array))
      ? item : { value: item };
    obj.label = {
      show: true,
      position: spec.horizontal ? 'right' : 'top',
      fontSize: 10,
      fontWeight: 600,
      color: growth >= 0 ? theme.error : theme.success,
      formatter: (growth >= 0 ? '+' : '') + growth.toFixed(1) + '%'
    };
    return obj;
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
    } else if (spec.sortRank) {
      cats.sort(listRanker(spec.sortRank) || compareCatX);
    }

    // 1.6.4：用 follow() 的图（KPI 卡片切指标）在这里把类目顺序钉住。
    // 第一次渲染按「当前指标」的合计降序排一次并记住，之后切卡片只改值、不再重排，
    // 柱子的左右位置保持稳定。显式传了 sort= 时以用户为准（sortUser）。
    var pinOrder = !!spec.follow && !spec.sortUser;
    if (pinOrder) {
      // 直接记下「这一次默认排序的结果」（时间轴还是时间轴、排行榜还是排行榜），
      // 之后每次渲染按这份名单还原，切指标不再重排。
      if (!spec.pinCats) spec.pinCats = cats.slice();
      else cats.sort(listRanker(spec.pinCats) || compareCatX);
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
      var _explicitSort = spec.sortUser && (spec.sort === 'desc' || spec.sort === 'asc');
      if (_explicitSort) {
        seriesNames.sort(function (a, b) { return (seriesTotals[b] || 0) - (seriesTotals[a] || 0); });
        if (spec.sort === 'asc') seriesNames.reverse();
      } else if (spec.sort !== 'none') {
        var _sr = seriesRanker(data, cdim, seriesNames);
        if (_sr) seriesNames.sort(_sr);
      }
    } else {
      seriesNames = [ydim || '记录数'];
    }

    function valueOf(cat, sname) {
      if (cat === '其他') {
        var s = 0, has = false;
        for (var k = 0; k < otherCats.length; k++) {
          // 有 color 时键是 "类目\u0001系列"，没有 color 时是 "类目\u0001"
          var ov = map[otherCats[k] + SEP + (cdim ? sname : '')];
          if (ov !== null && ov !== undefined) { s += ov; has = true; }
        }
        return has ? s : null;
      }
      var v = map[cat + SEP + (cdim ? sname : '')];
      return (v === undefined) ? null : v;
    }

    // 同比（yoy）：只有 2 条 color 系列、且不是百分比模式时才做对比
    var yoy = null, yoyG = null;
    if (spec.yoy && cdim && seriesNames.length === 2 && !spec.percent) {
      yoy = yoyPlan(seriesNames, seriesTotals);
      yoyG = {};
      for (var yi = 0; yi < cats.length; yi++) {
        yoyG[cats[yi]] = yoyGrowth(valueOf(cats[yi], yoy.current), valueOf(cats[yi], yoy.base));
      }
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
          // 没有 color 时没有"堆叠组"，保持原值（清零会让整张图变成 0 柱）
          val = ct ? (val / ct * 100) : val;
        }
        if (spec.percent && val !== null) val = Math.round(val * 10) / 10;
        if (isBar) {
          var item = dimItem(val === null ? 0 : val, sel, cats[ci]);
          // 没有 color 时按横轴类目上色；有 color 时系列名才是上色单位
          if (!cdim) item = paintItem(item, catColor(spec, cats[ci]));
          var g = (yoy && name === yoy.current) ? yoyG[cats[ci]] : null;
          if (g !== null && g !== undefined) item = yoyItem(item, g, spec, theme);
          sdata.push(item);
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
        var _bc = cdim ? catColor(spec, name) : null;
        if (_bc) barSeries.color = _bc;
        if (spec.stack) barSeries.stack = 'total';
        if (spec.labels) {
          barSeries.label = {
            show: true, position: spec.horizontal ? 'right' : 'top',
            color: theme.subtext, fontSize: 10,
            formatter: function (p) { return fmtValue(p.value, spec.fmt, spec); }
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
        var _lc = catColor(spec, name);
        if (_lc) lineSeries.color = _lc;
        if (spec.step) lineSeries.step = 'middle';
        if (spec.area) lineSeries.areaStyle = { opacity: spec.stack ? 0.45 : 0.16 };
        if (spec.stack) lineSeries.stack = 'total';
        if (spec.markers) lineSeries.markPoint = { data: [], symbolSize: 0 };
        if (spec.labels) {
          lineSeries.label = {
            show: true, position: 'top', color: theme.subtext, fontSize: 10,
            formatter: function (p) { return fmtValue(p.value, spec.fmt, spec); }
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
    if (yoy) {
      var yoyTipBase = opt.tooltip.formatter;
      opt.tooltip.formatter = function (params) {
        var html = yoyTipBase(params);
        if (!params || !params.length) return html;
        var cands = [params[0].axisValue, params[0].name, params[0].axisValueLabel];
        var g = null, hit = false;
        for (var ck = 0; ck < cands.length; ck++) {
          var key = cands[ck];
          if (key === null || key === undefined) continue;
          if (Object.prototype.hasOwnProperty.call(yoyG, key)) { g = yoyG[key]; hit = true; break; }
        }
        if (!hit || g === null || g === undefined) return html;
        var tcolor = g >= 0 ? theme.error : theme.success;
        return html + '<div style="border-top:1px dashed ' + theme.axis +
          ';margin-top:4px;padding-top:4px;display:flex;gap:6px;align-items:center">' +
          '<span style="flex:1">同比 ' + esc(yoy.current) + ' vs ' + esc(yoy.base) + '</span>' +
          '<b style="color:' + tcolor + '">' + (g >= 0 ? '+' : '') + g.toFixed(1) + '%</b></div>';
      };
    }

    if (spec.horizontal) {
      catAxis.boundaryGap = true;
      // 横向条形图的类目在 Y 轴上，已经是横着读的，再旋转 30°
      // 反而要歪着脖子看，这里强制不旋转。
      catAxis.axisLabel.rotate = 0;
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
    else if (spec.sortRank) cats.sort(listRanker(spec.sortRank) || compareCatX);

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
      var _ic = catColor(spec, it.name);
      if (_ic) item.itemStyle = { color: _ic };
      if (sel !== null && sel !== undefined && it.name !== sel) {
        item.itemStyle = item.itemStyle || {};
        item.itemStyle.opacity = 0.3;
      }
      return item;
    });
    // 窄卡片（手机）里外置标签会和环、图例互相压，改成「关标签 + 底部横排图例」
    var narrow = activeWidth > 0 && activeWidth < 430;
    var showLabels = spec.labels !== false && !narrow;
    return {
      tooltip: (function () {
        var tip = tooltipBox(theme);
        tip.trigger = 'item';
        tip.formatter = function (p) {
          return '<div style="font-weight:600;margin-bottom:3px">' + esc(p.name) + '</div>' +
            p.marker + ' ' + fmtValue(p.value, spec.fmt, spec) + '（' + p.percent + '%）';
        };
        return tip;
      })(),
      legend: narrow ? {
        // 窄屏饼图图例：放到底部并允许换行（plain）。
        // scroll 模式下 6 个分类会只显示前 4 个再出现「1/2」翻页箭头，底部就两个小字还看不全。
        show: spec.legend !== false, type: 'plain', orient: 'horizontal',
        left: 'center', bottom: 2, width: '94%', itemWidth: 9, itemHeight: 7,
        itemGap: 6, textStyle: { color: theme.subtext, fontSize: 9.5 },
        selected: state.legendSel || undefined
      } : {
        show: spec.legend !== false, type: 'scroll', orient: 'vertical',
        right: 6, top: 'middle', itemWidth: 10, itemHeight: 8,
        textStyle: { color: theme.subtext, fontSize: 11 },
        selected: state.legendSel || undefined
      },
      __legendFixed: narrow,
      toolbox: makeToolbox(theme),
      series: [{
        type: 'pie',
        radius: narrow ? (spec.donut ? ['28%', '60%'] : ['0%', '60%'])
                       : (spec.donut ? ['46%', '70%'] : ['0%', '68%']),
        center: narrow ? ['50%', '44%'] : ['38%', '52%'],
        avoidLabelOverlap: true,
        minAngle: 2,
        itemStyle: { borderColor: theme.bg, borderWidth: 2 },
        label: {
          show: showLabels,
          // 设了换算单位时，饼图标签带出「数值 + 单位」和占比，否则沿用「名称 + 百分比」
          formatter: showLabels ? (unitInfo(spec) ? function (p) {
            return p.name + '\n' + fmtValue(p.value, spec.fmt, spec) + '（' + p.percent + '%）';
          } : '{b}\n{d}%') : '{b}',
          color: theme.text, fontSize: narrow ? 10 : 11, lineHeight: 15
        },
        labelLine: { show: showLabels, length: 10, length2: 8, lineStyle: { color: theme.axis } },
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
          html += '<div style="line-height:19px">' + esc(xdim) + '：<b>' + fmtValue(d[0], spec.fmt, spec) + '</b></div>';
          html += '<div style="line-height:19px">' + esc(ydim) + '：<b>' + fmtValue(d[1], spec.fmt, spec) + '</b></div>';
          if (sdim) html += '<div style="line-height:19px">' + esc(sdim) + '：<b>' + fmtValue(d[2], spec.fmt, spec) + '</b></div>';
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
            '<div style="line-height:19px">区间：' + fmtValue(lo, spec.fmt, spec) + ' ~ ' + fmtValue(hi, spec.fmt, spec) + '</div>' +
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
            '<div style="line-height:19px">' + esc(vdim) + '：<b>' + fmtValue(p.data[2], spec.fmt, spec) + '</b></div>';
        };
        return tip;
      })(),
      xAxis: xAxis,
      yAxis: yAxis,
      visualMap: {
        min: min, max: max, calculable: false, orient: 'vertical',
        right: 2, top: 'middle', itemWidth: 10, itemHeight: 90,
        textStyle: { color: theme.subtext, fontSize: 10 },
        formatter: function (v) { return fmtValue(v, spec.fmt, spec); },
        inRange: { color: theme.heat }
      },
      series: [{
        type: 'heatmap', data: points,
        label: {
          show: showLabel, color: theme.text, fontSize: 10,
          formatter: function (p) { return fmtValue(p.data[2], spec.fmt, spec); }
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
            '<div style="line-height:19px">最大：<b>' + fmtValue(d[4], spec.fmt, spec) + '</b></div>' +
            '<div style="line-height:19px">上四分位：' + fmtValue(d[3], spec.fmt, spec) + '</div>' +
            '<div style="line-height:19px">中位数：<b>' + fmtValue(d[2], spec.fmt, spec) + '</b></div>' +
            '<div style="line-height:19px">下四分位：' + fmtValue(d[1], spec.fmt, spec) + '</div>' +
            '<div style="line-height:19px">最小：' + fmtValue(d[0], spec.fmt, spec) + '</div>';
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
      var _ic = catColor(spec, it.name);
      if (_ic) item.itemStyle = { color: _ic };
      if (sel !== null && sel !== undefined && it.name !== sel) {
        item.itemStyle = item.itemStyle || {};
        item.itemStyle.opacity = 0.3;
      }
      return item;
    });
    var funnelLabel = { show: spec.labels !== false, position: 'inside', color: '#fff', fontSize: 11 };
    if (unitInfo(spec)) {
      // 设了换算单位时，漏斗标签带出换算后的数值（名称 + 2.5百万）
      funnelLabel.formatter = function (p) {
        return p.name + ' ' + fmtValue(p.value, spec.fmt, spec);
      };
    }
    return {
      tooltip: (function () {
        var tip = tooltipBox(theme);
        tip.trigger = 'item';
        tip.formatter = function (p) { return esc(p.name) + '：<b>' + fmtValue(p.value, spec.fmt, spec) + '</b>'; };
        return tip;
      })(),
      toolbox: makeToolbox(theme),
      legend: { show: false },
      series: [{
        type: 'funnel', sort: 'descending', gap: 3,
        left: '8%', right: '8%', top: 24, bottom: 12,
        minSize: '18%', maxSize: '100%',
        label: funnelLabel,
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
    paintTree(spec, tree);
    return {
      tooltip: (function () {
        var tip = tooltipBox(theme);
        tip.trigger = 'item';
        tip.formatter = function (p) {
          return '<div style="font-weight:600">' + esc(p.name) + '</div>' +
            '<div style="line-height:19px">' + esc(valCol) + '：<b>' + fmtValue(p.value, spec.fmt, spec) + '</b></div>';
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
          // 换算单位（万 / 亿）和文字后缀（% / ℃ / 单）统一由 fmtValue 处理
          formatter: function (v) { return fmtValue(v, spec.fmt, spec); },
          color: theme.text, fontSize: 28, fontWeight: 600, offsetCenter: [0, '42%']
        },
        title: { show: !!spec.label, offsetCenter: [0, '70%'], color: theme.subtext, fontSize: 12 },
        data: [{ value: spec.value, name: spec.label || '' }]
      }]
    };
  }

  // ---- KPI 卡片 ---------------------------------------------------------
  // 从（联动过滤后的）数据里现算 KPI 数值
  // ------------------------------------------------------------------
  // 1.6：动态对比（同比 / 环比）与指标切换
  //
  // 设计：spec 里只放「怎么算」的声明（compare / switch），真正的数字每次渲染都
  // 从 filteredRows() 现算 —— 所以联动一过滤，本期值、上期值、同比率会一起重算。
  // ------------------------------------------------------------------

  // 增长率（小数）：(cur - base) / |base|。基期为空 / 0 → null；基期为负时用绝对值，
  // 方向不会反（-100 → -50 是 +50%）。
  function rateOf(cur, base) {
    var c = num(cur), b = num(base);
    if (c === null || b === null || b === 0) return null;
    return (c - b) / Math.abs(b);
  }

  function aggValue(rows, measure, how) {
    if (measure === null || measure === undefined) return null;
    if (!rows || !rows.length) return null;
    var g = groupBy(rows, [], measure, how || 'sum');
    return g.length ? g[0].value : null;
  }

  // 在联动过滤之后，再按 compare 的列切出「本期 / 基期」两组行。
  function compareRows(spec, data, state, variant) {
    var rows = filteredRows(spec, data, state);
    var cmp = spec.compare;
    if (!cmp || !cmp.dim) return rows;
    var want = String(variant === 'base' ? cmp.base : cmp.cur);
    var out = [];
    for (var i = 0; i < rows.length; i++) {
      if (String(catName(rows[i][cmp.dim])) === want) out.push(rows[i]);
    }
    return out;
  }

  // 同期对齐：基期只保留本期出现过的期（2026 只有 1–8 月，就只比 2025 的 1–8 月）。
  function periodAligned(curRows, baseRows, period) {
    if (!period) return baseRows;
    var seen = {}, i;
    for (i = 0; i < curRows.length; i++) {
      seen['$' + String(catName(curRows[i][period]))] = 1;
    }
    var out = [];
    for (i = 0; i < baseRows.length; i++) {
      if (seen['$' + String(catName(baseRows[i][period]))]) out.push(baseRows[i]);
    }
    return out;
  }

  // 环比：本期最后一期 vs 上一期。
  function kpiMom(rows, period, measure, how) {
    if (!period || !rows || !rows.length) return null;
    var buckets = {}, order = [], i;
    for (i = 0; i < rows.length; i++) {
      var k = String(catName(rows[i][period]));
      if (!Object.prototype.hasOwnProperty.call(buckets, k)) {
        buckets[k] = [];
        order.push(k);
      }
      buckets[k].push(rows[i]);
    }
    if (order.length < 2) return null;
    order.sort(compareCatX);
    var last = order[order.length - 1], prev = order[order.length - 2];
    var curV = aggValue(buckets[last], measure, how);
    var baseV = aggValue(buckets[prev], measure, how);
    return { cur: curV, base: baseV, rate: rateOf(curV, baseV), label: last, baseLabel: prev };
  }

  function computeKpi(spec, data, state) {
    var measure = (spec.roles && spec.roles.value) ||
      (spec.compute && spec.compute.measure) || null;
    var how = spec.agg || 'sum';
    var out = {
      cur: null, base: null, rate: null, mom: null,
      hasBase: false, hasMom: false,
      curLabel: '', baseLabel: '', dim: null
    };
    if (spec.value !== null && spec.value !== undefined) {
      out.cur = num(spec.value);
      return out;
    }
    var cmp = spec.compare;
    if (!cmp || !cmp.dim) {
      out.cur = aggValue(filteredRows(spec, data, state), measure, how);
      return out;
    }
    var curRows = compareRows(spec, data, state, 'cur');
    var baseRows = periodAligned(curRows, compareRows(spec, data, state, 'base'), cmp.period);
    out.cur = aggValue(curRows, measure, how);
    out.base = aggValue(baseRows, measure, how);
    out.hasBase = out.base !== null && out.base !== undefined;
    out.rate = rateOf(out.cur, out.base);
    out.mom = kpiMom(curRows, cmp.period, measure, how);
    out.hasMom = !!(out.mom && out.mom.rate !== null);
    out.dim = cmp.dim;
    out.curLabel = String(cmp.cur);
    out.baseLabel = String(cmp.baseLabel || cmp.base);
    return out;
  }

  // 指标选择器（1.6.1）
  //
  // 带 metricSel 的 KPI 卡片本身就是一个按钮：点它把这张卡的 {column, agg}
  // 广播给所有 follow 图（spec.follow = {角色: {default, agg}}），不触发 Python 重算。
  function metricSelOf(spec) {
    return (spec && spec.metricSel) ? spec.metricSel : null;
  }

  function currentSelection() {
    return EazyViz.selection || null;
  }

  function applyFollow(spec) {
    if (!spec || !spec.follow) return spec;
    var sel = currentSelection();
    var col = (sel && sel.column) ? sel.column : null;
    if (!spec.__followBase) spec.__followBase = {};
    for (var role in spec.follow) {
      if (!Object.prototype.hasOwnProperty.call(spec.follow, role)) continue;
      if (!Object.prototype.hasOwnProperty.call(spec.__followBase, role)) {
        spec.__followBase[role] = spec.roles ? spec.roles[role] : null;
      }
      var def = spec.follow[role] || {};
      var use = col || def.default || spec.__followBase[role] || null;
      if (!spec.roles) spec.roles = {};
      spec.roles[role] = use;
      // 汇总表按 spec.groupby.value 取度量列，这里一起换
      if (role === 'value' && spec.groupby) spec.groupby.value = use;
      if (col) {
        if (sel && sel.agg) spec.agg = sel.agg;
      } else if (def.agg) {
        spec.agg = def.agg;
      }
    }
    return spec;
  }

  function selectMetric(id) {
    var target = null, i;
    for (i = 0; i < EazyViz.charts.length; i++) {
      var c0 = EazyViz.charts[i];
      if (c0 && c0.spec && c0.spec.id === id) { target = c0; break; }
    }
    var ms = target ? metricSelOf(target.spec) : null;
    if (!ms) return;
    var cur = currentSelection();
    if (cur && cur.id === id) {
      EazyViz.selection = null;   // 再点一次取消，回到各自的默认列
    } else {
      EazyViz.selection = {
        id: id, name: ms.name, column: ms.column, agg: ms.agg, label: ms.label
      };
    }
    applySelection();
  }

  function applySelection() {
    for (var i = 0; i < EazyViz.charts.length; i++) {
      var c = EazyViz.charts[i];
      if (!c || !c.spec) continue;
      if (c.spec.follow || c.spec.metricSel) renderChart(c);
    }
  }

  function pctText(v) {
    if (v === null || v === undefined || !isFinite(v)) return '';
    return (v >= 0 ? '+' : '') + (v * 100).toFixed(1) + '%';
  }

  function kpiValue(spec, data, state) {
    return computeKpi(spec, data, state).cur;
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

  // Catmull-Rom → 三次贝塞尔，把折线画成顺滑曲线
  function sparkCurve(coords) {
    var d = 'M ' + coords[0][0] + ' ' + coords[0][1];
    for (var i = 0; i < coords.length - 1; i++) {
      var p0 = coords[i === 0 ? 0 : i - 1];
      var p1 = coords[i];
      var p2 = coords[i + 1];
      var p3 = coords[i + 2 < coords.length ? i + 2 : coords.length - 1];
      var c1x = p1[0] + (p2[0] - p0[0]) / 6;
      var c1y = p1[1] + (p2[1] - p0[1]) / 6;
      var c2x = p2[0] - (p3[0] - p1[0]) / 6;
      var c2y = p2[1] - (p3[1] - p1[1]) / 6;
      d += ' C ' + Math.round(c1x * 100) / 100 + ' ' + Math.round(c1y * 100) / 100 +
        ' ' + Math.round(c2x * 100) / 100 + ' ' + Math.round(c2y * 100) / 100 +
        ' ' + p2[0] + ' ' + p2[1];
    }
    return d;
  }

  var sparkSeq = 0;

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
    var d = sparkCurve(coords);
    var area = d + ' L ' + coords[n - 1][0] + ' ' + (h - pad) + ' L ' + coords[0][0] + ' ' + (h - pad) + ' Z';
    var last = coords[n - 1];
    sparkSeq += 1;
    var gid = 'eazy-spark-' + sparkSeq;
    return '<svg class="eazy-kpi-spark" viewBox="0 0 ' + w + ' ' + h + '"' +
      ' preserveAspectRatio="none" aria-hidden="true">' +
      '<defs><linearGradient id="' + gid + '" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0%" stop-color="' + color + '" stop-opacity="0.28"></stop>' +
      '<stop offset="100%" stop-color="' + color + '" stop-opacity="0.02"></stop>' +
      '</linearGradient></defs>' +
      '<path d="' + area + '" fill="url(#' + gid + ')"></path>' +
      '<path d="' + d + '" fill="none" stroke="' + color + '" stroke-width="1.8"' +
      ' stroke-linejoin="round" stroke-linecap="round"' +
      ' vector-effect="non-scaling-stroke"></path>' +
      '</svg>' +
      '<i class="eazy-kpi-sparkdot" style="top:' + roundTo(last[1] / h * 100, 1) + '%;' +
      'background:' + color + '"></i>';
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
    var kres = computeKpi(spec, data, state);
    var cmpOn = !!spec.compare;
    var ms = metricSelOf(spec);
    var nowSel = currentSelection();
    var selected = !!(ms && nowSel && nowSel.id === spec.id);
    var val = kres.cur;
    // 换算单位（万 / 亿 / 百万）和文字后缀（ 单 / ℃ / %）都由 fmtValue 拼好
    var txt = fmtValue(val, spec.fmt, spec);
    if (spec.prefix) txt = spec.prefix + txt;

    var html = '<div class="eazy-kpi' + (ms ? ' eazy-kpi-selectable' : '') +
      (selected ? ' is-selected' : '') + '" style="--eazy-accent:' + accent + '"' +
      (ms ? ' data-eazy-metric="' + esc(spec.id) + '"' : '') + '>';
    html += '<div class="eazy-kpi-head"><span class="eazy-kpi-label">' +
      esc(spec.label || '') + '</span>';
    var achieved = null, targetV = num(spec.target);
    if (spec.target !== null && spec.target !== undefined &&
        isFinite(targetV) && targetV !== 0) {
      achieved = (num(val) || 0) / targetV * 100;
      html += '<span class="eazy-kpi-badge">' +
        esc(spec.targetLabel || ('目标 ' + fmtValue(targetV, spec.fmt, spec))) + '</span>';
    }
    html += '</div>';

    html += '<div class="eazy-kpi-main"><span class="eazy-kpi-value">' + esc(txt) + '</span>';
    if (cmpOn) {
      var momMode = spec.compare.mode === 'mom';
      var rateUse = momMode ? (kres.mom ? kres.mom.rate : null) : kres.rate;
      var rateName = momMode ? '环比' : '同比';
      if (rateUse !== null && rateUse !== undefined && isFinite(rateUse)) {
        var rGood = (rateUse >= 0) !== !!spec.inverse;
        html += '<span class="eazy-kpi-delta ' + (rGood ? 'eazy-up' : 'eazy-down') + '">' +
          (rateUse >= 0 ? '▲' : '▼') + ' ' + pctText(rateUse) + '</span>';
        html += '<span class="eazy-kpi-deltalabel">' + esc(rateName) + '</span>';
      } else {
        html += '<span class="eazy-kpi-deltalabel">' +
          esc(kres.hasBase ? (rateName + ' —') : (rateName + ' 新增')) + '</span>';
      }
    } else if (spec.delta !== null && spec.delta !== undefined) {
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
    if (!hint && spec.link && EazyViz.hints) hint = '联动组 ' + spec.link + ' · 点同组图表筛选';
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

  // 图例排版：项目少时用 plain 自动换行（不会把最后一项截断成「1/2」），
  // 项目多时仍用 scroll；并按图例行数把 grid.top 往下推，避免压住纵轴名。
  // 图例单项的像素宽度：图标 22px + 文字。中文按 1em、西文按 0.56em 估，
  // 之前按「字符数 * 7」一律算宽，中文名会被低估 → 行数算少 → 图例压到纵轴名上。
  function legendItemPx(name, fs) {
    var t = String(name || '');
    var px = 0;
    for (var i = 0; i < t.length; i++) {
      px += t.charCodeAt(i) > 255 ? fs : fs * 0.56;
    }
    return px + 22;
  }

  function legendRowInfo(opt, avail) {
    var names = [];
    if (opt.legend && opt.legend.data && opt.legend.data.length) {
      names = opt.legend.data.slice();
    } else {
      (opt.series || []).forEach(function (s) {
        if (s && s.name && names.indexOf(s.name) < 0) names.push(s.name);
      });
    }
    if (!names.length) return null;
    var fs = 11;
    var total = 0;
    names.forEach(function (n) { total += legendItemPx(n, fs) + 8; });
    // 每行能放多少像素取决于容器宽度：手机卡片只有 ~150px，按 440 估会严重低估行数
    var per = Math.max(120, avail || 440);
    return { rows: Math.max(1, Math.ceil(total / per)) };
  }

  // 日期轴拆成两行（「2025年\n3月」）时，x 轴名与 grid 底部要再多让一行，
  // 否则「月份」会直接压在最后一行标签上（实测在 17 个月的看板里重叠）。
  function fixTwoLineAxis(opt) {
    if (!opt || !opt.xAxis) return opt;
    var xs = opt.xAxis.length ? opt.xAxis : [opt.xAxis];
    var two = false, i;
    for (i = 0; i < xs.length; i++) {
      if (xs[i] && xs[i].__twoLine) { two = true; delete xs[i].__twoLine; }
    }
    if (!two) return opt;
    for (i = 0; i < xs.length; i++) {
      if (xs[i] && xs[i].name) xs[i].nameGap = 44;
    }
    if (opt.grid && opt.grid.bottom < 58) opt.grid.bottom = 58;
    return opt;
  }

  function layoutLegend(opt) {
    if (!opt || !opt.legend || opt.legend.show === false) return opt;
    // 饼图 / 漏斗自带竖排图例（贴着卡片右侧），不要被通用排版改成顶部横排
    if (opt.legend.orient === 'vertical' || opt.__legendFixed) return opt;
    var lg = opt.legend;
    var w = activeWidth || 0;
    // 极窄容器（手机竖屏一张卡片 ~150px、窄侧栏）：顶部图例能占掉三分之一高度，
    // 改成底部一行可滚动图例，纵向空间全留给绘图区。
    // 323px 这种「窄但还放得下两行图例」的情况仍留在顶部，底栏会和 x 轴刻度/轴名打架。
    var narrow = w > 0 && w < 270;
    lg.width = narrow ? '96%' : '92%';
    lg.left = 'center';
    lg.itemGap = narrow ? 6 : 8;
    lg.textStyle = { fontSize: narrow ? 10 : 11 };
    if (narrow) {
      lg.type = 'scroll';
      lg.top = 'auto';
      lg.bottom = 0;
      if (opt.grid) {
        opt.grid.top = 34;
        opt.grid.bottom = 26;
      }
      return opt;
    }
    var info = legendRowInfo(opt, w ? w - 28 : 440);
    if (!info) return opt;
    lg.top = 6;
    // 半屏 / 窄侧栏允许三行，桌面只放两行就转成可滚动，避免图例压到绘图区
    var maxRows = (w > 0 && w < 720) ? 4 : 2;
    if (info.rows <= maxRows) {
      lg.type = 'plain';
      // 图例占 6 + rows*20，再加纵轴名的 14px，所以 46 + rows*20
      if (opt.grid) opt.grid.top = 46 + info.rows * 20;
    } else {
      lg.type = 'scroll';
      if (opt.grid) opt.grid.top = 60;
    }
    return opt;
  }

  function buildOption(spec, data, state, theme) {
    theme = theme || THEME.light;
    state = state || { filters: {}, drill: [] };
    var builder = BUILDERS[spec.type] || EXTRA[spec.type];
    if (!builder) throw new Error('不支持的图表类型: ' + spec.type);
    // 构建期间挂上 spec：扩展图表（eazy_extra_*.js）只传 fmt，靠它拿到显式单位
    var opt = withSpec(spec, function () {
      return builder(spec, data || { cols: [], rows: [] }, state, theme);
    });
    if (!opt) return null;
    opt.backgroundColor = 'transparent';
    opt.textStyle = { fontFamily: FONT, color: theme.text,
      fontSize: (activeWidth > 0 && activeWidth < 480) ? 11 : 12 };
    // 配色库：ECharts 默认按 option.color 循环取色，builder 自己指定过的优先
    if (!opt.color && theme.palette) opt.color = theme.palette.slice();
    opt.animation = true;
    opt.animationDuration = 380;
    opt.animationDurationUpdate = 260;
    opt.animationEasing = 'cubicOut';
    return fixTwoLineAxis(layoutLegend(opt));
  }

  // ======================================================================
  // 5. 页面状态 / 交互
  // ======================================================================
  EazyViz.charts = [];
  EazyViz.links = {};
  EazyViz.page = {};
  EazyViz.dataStore = {};
  EazyViz.hints = false;
  EazyViz.selection = null;
  EazyViz.cardStyle = 'default';
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

  // 按图形自己的根节点查找。多组件页面里 EazyViz.scope 只指向「最后挂载」的那个组件，
  // 用 findOne 去别的组件里找工具条 / 筛选条会落空，面包屑与 chip 就永远不刷新。
  function rootOfChart(c) {
    try { return (c && c.el && c.el.getRootNode) ? c.el.getRootNode() : document; }
    catch (e) { return document; }
  }

  // 当前页面上所有看板根节点（去重）；静态 HTML 只有 document 一个。
  function chartRoots() {
    var out = [], i, r;
    for (i = 0; i < EazyViz.charts.length; i++) {
      r = rootOfChart(EazyViz.charts[i]);
      if (out.indexOf(r) < 0) out.push(r);
    }
    if (!out.length) out.push(scopeNode());
    return out;
  }

  // 一个页面上可以有多个 streamlit_dashboard（每个是一个 components v2 实例），
  // 它们共享 window.EazyViz，所以查找要按当前挂载点（EazyViz.scope）过一遍，
  // 否则点第二个看板的「代码」按钮会打开第一个看板的卡片。
  function inScope(el) {
    var scope = EazyViz.scope;
    if (!scope || !el || !el.isConnected) return false;
    return scope === document ? true : (scope.contains ? scope.contains(el) : false);
  }

  function chartById(id) {
    var fallback = null;
    for (var i = 0; i < EazyViz.charts.length; i++) {
      var c = EazyViz.charts[i];
      if (c.spec.id !== id) continue;
      if (!fallback) fallback = c;
      if (inScope(c.el)) return c;
    }
    return fallback;
  }

  function chartByIndex(idx) {
    var fallback = null;
    for (var i = 0; i < EazyViz.charts.length; i++) {
      var c = EazyViz.charts[i];
      if (c.index !== idx) continue;
      if (!fallback) fallback = c;
      if (inScope(c.el)) return c;
    }
    return fallback;
  }

  function chartOfEl(el) {
    for (var i = 0; i < EazyViz.charts.length; i++) {
      var c = EazyViz.charts[i];
      if (c && c.el && c.el.contains && c.el.contains(el)) return c;
    }
    return null;
  }

  // 按「点击发生的那块看板根节点」定位图表：多个看板的 chart index 都从 0 开始，
  // 只用 chartByIndex 会在多看板页面里点错图（面包屑/返回指向另一块看板）。
  function chartFor(el, idx) {
    var root = rootOf(el), fallback = null;
    for (var i = 0; i < EazyViz.charts.length; i++) {
      var c = EazyViz.charts[i];
      if (c.index !== idx) continue;
      if (!fallback) fallback = c;
      if (root && c.el && root.contains && root.contains(c.el)) return c;
      if (!root && inScope(c.el)) return c;
    }
    return fallback;
  }

  function syncFilters(c) {
    var f = {};
    if (canRecvLink(c.spec) && EazyViz.links && EazyViz.links[c.spec.link]) {
      var link = EazyViz.links[c.spec.link];
      // 发起联动的图自己不过滤（保持全量 + 高亮），其他图按类目过滤；
      // 单向出（out）的图永远只发起、不接收。
      // 多级下钻会带来多条条件（月=1月 AND 渠道=直销），能对上的列都收。
      if (link.sourceId !== c.spec.id) {
        var conds = linkConds(link);
        for (var ci = 0; ci < conds.length; ci++) {
          if (hasCol(c.data, conds[ci].dim)) f[conds[ci].dim] = conds[ci].value;
        }
      }
    }
    c.state.filters = f;
    // 把本组的联动条件也记到 state 上：明细表据此知道「这条联动是不是我发起的」，
    // 是的话就不筛行，而是把命中的行高亮出来（和图表「自己不过滤、只高亮」一致）。
    c.state.link = (c.spec.link && EazyViz.links && EazyViz.links[c.spec.link]) || null;
  }

  // 面包屑每一段显示成「维度:值」（例如 地区:北京）。
  function crumbLabel(entry) {
    if (!entry) return '';
    var d = (entry.dim === null || entry.dim === undefined) ? '' : String(entry.dim);
    var v = (entry.value === null || entry.value === undefined) ? '' : String(entry.value);
    return d ? (d + ':' + v) : v;
  }

  function renderToolbar(c) {
    var root = rootOfChart(c), el = null;
    try { el = root.querySelector('[data-eazy-toolbar="' + c.index + '"]'); }
    catch (e) { el = null; }
    if (!el) el = findOne('[data-eazy-toolbar="' + c.index + '"]');
    if (!el) return;
    var spec = c.spec, html = '';
    if (spec.drill && spec.drill.length) {
      var depthNow = c.state.drill.length;
      html += '<div class="eazy-crumb">';
      html += '<button data-chart="' + c.index + '" data-crumb="0"' +
        (depthNow ? '' : ' class="cur"') + ' title="返回到「全部」">全部</button>';
      for (var i = 0; i < depthNow; i++) {
        html += '<span class="sep">›</span>';
        var cur = (i === depthNow - 1) ? ' class="cur"' : '';
        var label = crumbLabel(c.state.drill[i]);
        html += '<button' + cur + ' data-chart="' + c.index + '" data-crumb="' + (i + 1) + '"' +
          ' title="返回到「' + esc(label) + '」层">' + esc(label) + '</button>';
      }
      html += '</div>';
      if (depthNow) {
        html += '<button class="eazy-btn" data-back="' + c.index + '">↰ 返回</button>';
      }
      if (EazyViz.hints) {
        html += '<span class="eazy-hint">' +
          (depthNow >= spec.drill.length ? '已到最末级' : ('点击图形下钻到「' + esc(spec.drill[depthNow]) + '」')) +
          '</span>';
      }
    } else if (spec.link && HTML_BUILDERS[spec.type]) {
      if (EazyViz.hints) {
        html += '<span class="eazy-hint" style="margin-left:0">点击单元格可按该列联动同组图表</span>';
      }
    } else if (spec.link && EazyViz.hints) {
      var mode = linkMode(spec);
      var hint = mode === 'out'
        ? '单向出：点击图形联动到同组其他图表'
        : (mode === 'in'
          ? '单向进：本图只接收联动，点其他图会过滤本图'
          : '点击图形可联动同组图表（双向）');
      html += '<span class="eazy-hint" style="margin-left:0">' + hint + '</span>';
    }
    el.innerHTML = html;
  }

  // KPI 数字按容器宽度自动缩：手机上一张指标卡只有 ~120px 宽，
  // 「47,771,40…」被裁掉就看不出数了，所以从设计字号起按 2px 递减直到放得下。
  function fitTexts(root) {
    if (!root || !root.querySelectorAll) return;
    var els = root.querySelectorAll('.eazy-kpi-value,.eazy-metric .m-value');
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      el.style.fontSize = '';
      var cs = global.getComputedStyle ? global.getComputedStyle(el) : null;
      var base = parseInt(cs ? cs.fontSize : '', 10) || 30;
      var box = el.parentNode;
      var room = (box && box.clientWidth) || 0;
      if (!room) continue;
      var size = base, guard = 0;
      el.style.fontSize = size + 'px';
      while (el.scrollWidth > room && size > 13 && guard < 24) {
        size -= 2;
        el.style.fontSize = size + 'px';
        guard++;
      }
    }
  }

  // 窄屏把画布高度压到视口比例：390px 宽时 380px 高的图又细又长，
  // 压到约 0.8 倍屏宽（不低于 210）更顺手；表格压到 60vh，免得一屏只看到表头。
  function fitResponsiveHeights() {
    var vw = global.innerWidth || 0;
    var root = EazyViz.scope || document;
    if (!root.querySelectorAll) return;
    // 媒体查询看的是视口宽度，但 Streamlit 里组件可能只占半屏/侧栏：
    // 组件实际宽度不够 720px 时也把栅格降成一列，否则卡片会挤成一条缝。
    var grid = root.querySelector ? root.querySelector('.eazy-grid') : null;
    if (grid) {
      var gw = grid.clientWidth || 0;
      if (!grid.getAttribute('data-eazy-cols')) {
        grid.setAttribute('data-eazy-cols', grid.style.getPropertyValue('--eazy-cols') || '2');
      }
      var colsWanted = (gw > 0 && gw < 720) ? '1' : (EazyViz.page && EazyViz.page.cols
        ? String(EazyViz.page.cols) : grid.getAttribute('data-eazy-cols'));
      if (String(colsWanted) !== grid.style.getPropertyValue('--eazy-cols')) {
        grid.style.setProperty('--eazy-cols', String(colsWanted));
      }
    }
    if (!vw) return;
    var narrow = vw <= 720;
    var els = root.querySelectorAll('[data-eazy-chart]');
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      var h = parseInt(el.getAttribute('data-eazy-h') || '', 10);
      if (!h) {
        h = parseInt(el.style.height || '0', 10) || 0;
        if (!h) continue; // KPI 等按内容自适应高度，不动
        el.setAttribute('data-eazy-h', String(h));
      }
      var target = h;
      if (narrow) {
        target = el.querySelector('.eazy-table')
          ? Math.round((global.innerHeight || 700) * 0.6)
          : Math.max(210, Math.min(h, Math.round(vw * 0.8)));
      }
      if ((parseInt(el.style.height || '0', 10) || 0) !== target) el.style.height = target + 'px';
      var card = el.parentNode;
      while (card && card.classList && !card.classList.contains('eazy-card')) card = card.parentNode;
      if (card) {
        if (!card.getAttribute('data-eazy-mh')) card.setAttribute('data-eazy-mh', card.style.minHeight || '');
        card.style.minHeight = narrow ? (target + 96) + 'px' : (card.getAttribute('data-eazy-mh') || '');
      }
    }
  }

  function renderChart(c) {
    var spec = applyFollow(c.spec);
    var htmlBuilder = HTML_BUILDERS[spec.type];
    // 先记下容器宽度，图例排版 / 字号收敛 / KPI 缩放都依赖它
    activeWidth = c.el.clientWidth || 0;
    if (htmlBuilder) {
      // KPI / 明细表等 HTML 图：构建期间挂上 spec，扩展脚本里的 fmtValue 才能拿到 unit
      c.el.innerHTML = withSpec(spec, function () {
        return htmlBuilder(spec, c.data, c.state, c.theme);
      });
      renderToolbar(c);
      // HTML 类图（词云 canvas 等）在 innerHTML 落盘之后可能还要画一笔
      var htmlHook = EazyViz.htmlHooks && EazyViz.htmlHooks[spec.type];
      if (htmlHook) { try { htmlHook(c); } catch (htmlErr) { /* 画不出来不影响其它图 */ } }
      fitTexts(c.el);
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
    // 旭日图点节点会 rootToNode 放大；但联动一触发就会重画（setOption notMerge），
    // 放大状态会跟着丢。这里在重画之后把用户点开的那一层重新落回去，做到「放大 + 联动」同时生效。
    if (spec.type === 'sunburst') {
      if (c.zoomPath && c.zoomPath.length) applyZoomRoot(c);
      else resetZoomRoot(c);
    }
    renderToolbar(c);
    c._w = c.el.clientWidth;
    c._narrow = activeWidth > 0 && activeWidth < 480;
  }

  // 在当前（可能已被筛选过的）树里按名字路径找节点：节点 id 会随视图根变化，
  // 只有「名字路径」在重画前后稳定。
  function findNodeByPath(root, path) {
    var node = root;
    for (var i = 0; i < path.length; i++) {
      var kids = (node && node.children) || [];
      var hit = null;
      for (var k = 0; k < kids.length; k++) {
        if (String(kids[k].name) === String(path[i])) { hit = kids[k]; break; }
      }
      if (!hit) return null;
      node = hit;
    }
    return node;
  }

  // 旭日图的视图根是存在 series model 上的：重画时若保留着上一次的放大状态，
  // 一键重置 / 换筛选条件后用户就永远停在那一层，所以没有 zoomPath 时显式退回整棵树。
  function resetZoomRoot(c) {
    if (!c || !c.ec || !c.spec || c.spec.type !== 'sunburst') return;
    function go() {
      try {
        var sm = c.ec.getModel().getSeriesByIndex(0);
        var root = sm.getData().tree.root;
        if (sm.getViewRoot() !== root) sm.resetViewRoot(root);
      } catch (e) { /* 没有 model 时忽略 */ }
    }
    go();
    setTimeout(go, 16);
  }

  // 旭日图把视图根节点切到 zoomPath 指向的节点；找不到（被联动筛掉了）就停在当前根。
  function applyZoomRoot(c) {
    var path = c.zoomPath;
    if (!path || !path.length || !c.ec) return;
    function go() {
      if (!c.ec || c.spec.type !== 'sunburst') return;
      try {
        var series = c.ec.getModel().getSeriesByIndex(0);
        var root = series.getData().tree.root;
        var node = findNodeByPath(root, path);
        if (node && node !== root) {
          c.ec.dispatchAction({ type: 'sunburstRootToNode', targetNode: node });
        }
      } catch (e) { /* 节点已不存在时忽略 */ }
    }
    go();
    // 数据刚换过时第一帧可能还没建好节点，再补一次（幂等）
    setTimeout(go, 16);
  }

  // 点击的图形到底代表「哪一列 = 哪个值」。
  // 桑基图（多级）/ 旭日图 / 树图 的节点名不一定是 x 的类目，必须按节点信息还原，
  // 否则联动会把「二级节点的值」当成「一级列的值」传给其他图。
  function nodeInfoOf(spec, p) {
    if (!p || !spec) return null;
    // 旭日 / 树：节点自带层级（点过之后 rootToNode 会重设根，treePathInfo 会变短，
    // 只能用建树时写好的 nodeDim / nodeLayer 才不会传错维度）。
    if (p.data && p.data.nodeDim !== undefined) {
      // nodeDim === null 表示「这一层没有可联动的维度」（树 / 旭日的合成根，名字通常是「全部」）：
      // 显式返回 null，避免继续走 treePathInfo 兜底把根当成第一层维度去筛别的图（1.6.2 修复）。
      if (p.data.nodeDim === null) return null;
      return {
        dim: p.data.nodeDim,
        value: (p.data.nodeValue !== undefined && p.data.nodeValue !== null)
          ? String(p.data.nodeValue) : String(p.name),
        layer: p.data.nodeLayer
      };
    }
    var maps = EazyViz.nodeMaps || {};
    var map = maps[spec.id] || maps[spec.type];
    if (map) {
      var key = (p.data && p.data.nodeKey !== undefined) ? p.data.nodeKey : p.name;
      var hit = map[key];
      if (!hit && p.data && p.data.name !== undefined) hit = map[p.data.name];
      if (hit) return { dim: hit.dim, value: String(hit.value), layer: hit.layer };
    }
    if (p.treePathInfo && p.treePathInfo.length) {
      var dims = (spec.roles && spec.roles.path) || null;
      if (dims && dims.length) {
        var idx = p.treePathInfo.length - 2;
        if (idx < 0) idx = 0;
        if (idx > dims.length - 1) idx = dims.length - 1;
        var node = p.treePathInfo[p.treePathInfo.length - 1] || {};
        var nm = (node.name !== undefined && node.name !== null) ? node.name : p.name;
        if (nm !== undefined && nm !== null) {
          return { dim: dims[idx], value: String(nm), layer: idx };
        }
      }
    }
    return null;
  }

  // 层级图（旭日 / 树 / 矩形树）点击时：把从根到该节点的整条路径作为联动条件，
  // 这样点第三层产品时，其它图同时按「大区 AND 渠道 AND 产品」筛，而不是只筛产品。
  function pathConds(spec, p) {
    var dims = (spec && spec.roles && spec.roles.path) || null;
    var tp = (p && p.treePathInfo) || [];
    if (!dims || !dims.length || tp.length < 2) return [];
    var out = [];
    for (var i = 1; i < tp.length && (i - 1) < dims.length; i++) {
      var nm = tp[i] ? tp[i].name : undefined;
      if (nm === undefined || nm === null || nm === '' || nm === '(空)') continue;
      out.push({ dim: String(dims[i - 1]), value: String(nm) });
    }
    return out;
  }

  function onChartClick(c, p) {
    if (!p || p.componentType !== 'series') return;
    var spec = c.spec;
    var info = nodeInfoOf(spec, p);
    if (!info && (spec.type === 'sankey' || spec.type === 'graph')) return;  // 桑基的连线没有维度
    // 树 / 旭日的合成根（nodeDim 显式为 null）没有维度可联动，点了不该筛别的图（1.6.2 修复）
    if (!info && p.data && p.data.nodeDim === null) return;
    var xdim = info ? info.dim : currentXDim(spec, c.state);
    if (!xdim || p.name === null || p.name === undefined) return;
    var value = info ? info.value : String(p.name);
    if (value === '其他') return;

    // 旭日图：记住用户点开的那一层（用名字路径，重画后节点 id 会变），联动重画后再落回去
    if (spec.type === 'sunburst') {
      var zp = [], tp = p.treePathInfo || [];
      for (var ti = 1; ti < tp.length; ti++) {
        if (tp[ti] && tp[ti].name !== undefined && tp[ti].name !== null && tp[ti].name !== '') {
          zp.push(String(tp[ti].name));
        }
      }
      if (!zp.length && p.name !== undefined && p.name !== null) zp = [String(p.name)];
      c.zoomPath = zp;
    }

    var drilled = false;
    if (spec.drill && c.state.drill.length < spec.drill.length) {
      var depth = c.state.drill.length;
      if (spec.drill[depth] === xdim) {
        c.state.drill.push({ dim: xdim, value: value });
        drilled = true;
      }
    }
    // 联动条件：层级图用整条祖先路径，下钻图用整条下钻路径，其余用当前一级。
    var conds = pathConds(spec, p);
    if (!conds.length) conds = [{ dim: xdim, value: value }];
    // 带下钻的图：它发出的联动始终等于「当前最深一级的下钻条件」，回退时就不会残留旧层级；
    // 纯联动图（没有下钻）：按点击切换联动。
    if (canSendLink(spec) && spec.drill) {
      afterDrillChange(c);
    } else if (canSendLink(spec)) {
      setLink(spec.link, conds, null, c);
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
          linkMode: spec.link ? linkMode(spec) : null,
          canSend: canSendLink(spec),
          link: (spec.link && EazyViz.links[spec.link]) ? EazyViz.links[spec.link] : null,
          linkConds: (spec.link && EazyViz.links[spec.link]) ? linkConds(EazyViz.links[spec.link]) : []
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
    // 单向进（in）的图不允许发起联动
    if (chart && chart.spec && !canSendLink(chart.spec)) return;
    var sourceId = chart && chart.spec ? chart.spec.id : null;
    // dim 传数组时表示「一次带多条条件」（多级下钻 / 多列筛选）
    var conds = (Object.prototype.toString.call(dim) === '[object Array]')
      ? dim
      : [{ dim: dim, value: value }];
    var next = makeLink(conds, sourceId);
    var cur = EazyViz.links[group];
    if (!next || sameLink(cur, next)) {
      delete EazyViz.links[group];
    } else {
      EazyViz.links[group] = next;
    }
    reRenderGroup(group);
  }

  function clearLink(group) {
    delete EazyViz.links[group];
    reRenderGroup(group);
    syncFilterBar();
  }

  function syncFilterBar() {
    var groups = Object.keys(EazyViz.links || {});
    var html = '<span class="eazy-filters-label">联动筛选</span>';
    for (var i = 0; i < groups.length; i++) {
      var g = groups[i], link = EazyViz.links[g];
      var conds = linkConds(link), parts = [];
      for (var ci = 0; ci < conds.length; ci++) {
        parts.push(esc(conds[ci].dim) + ' = <b>' + esc(conds[ci].value) + '</b>');
      }
      html += '<span class="eazy-chip"><span>' + parts.join(' · ') +
        '</span><span class="eazy-chip-x" data-clear-link="' + esc(g) + '" title="清除">×</span></span>';
    }
    // 每个看板都有自己的筛选条：都刷一遍，别只刷最后挂载的那块。
    var roots = chartRoots();
    for (var k = 0; k < roots.length; k++) {
      var el = null;
      try { el = roots[k].querySelector('#eazy-filters'); } catch (e) { el = null; }
      if (!el) continue;
      el.innerHTML = html;
      el.style.display = groups.length ? '' : 'none';
    }
  }

  // 一个页面上可以挂多个看板，「重置下钻」只应该动当前这个看板：
  // 从点击元素往上找 .eazy-root，得到它所属的看板根节点。
  function rootOf(el) {
    while (el && el !== document) {
      if (el.classList && el.classList.contains('eazy-root')) return el;
      el = el.parentNode;
    }
    return null;
  }

  function inRoot(c, root) {
    if (!root) return true;
    return !!(c && c.el && root.contains && root.contains(c.el));
  }

  // 下钻那次点击同时会把这张图写成联动筛选的来源，
  // 所以只清 drill 的话，图还会被自己那条「大区 = 华东」过滤着，
  // 看起来像「回不去」。这里连同这些图自己发出的联动一起清掉。
  function dropOwnLinks(c) {
    if (!c || !EazyViz.links) return;
    var keys = Object.keys(EazyViz.links), groups = [];
    for (var i = 0; i < keys.length; i++) {
      var lk = EazyViz.links[keys[i]];
      if (lk && lk.sourceId === c.spec.id) { delete EazyViz.links[keys[i]]; groups.push(keys[i]); }
    }
    for (var j = 0; j < groups.length; j++) reRenderGroup(groups[j]);
  }

  // 把「本图当前最深的下钻条件」同步成它发出的联动：
  //   - 还有下钻：联动 = 最深一级的 {dim, value}（与面包屑当前层级一致）
  //   - 已回到顶层：清掉本图自己发出的那条联动
  // 返回是否改动过联动，调用方据此决定要不要重绘本组。
  function applyDrillLink(c) {
    if (!c || !c.spec || !c.spec.link || !EazyViz.links) return false;
    var group = c.spec.link;
    var drill = (c.state && c.state.drill) ? c.state.drill : [];
    var cur = EazyViz.links[group];
    if (drill.length) {
      // 整条下钻路径都作为联动条件：月=1月 AND 渠道=直销（不是只留最末一级）
      var next = makeLink(drill, c.spec.id);
      if (!sameLink(cur, next)) {
        EazyViz.links[group] = next;
        return true;
      }
      return false;
    }
    if (cur && cur.sourceId === c.spec.id) { delete EazyViz.links[group]; return true; }
    return false;
  }

  // 下钻状态改变后的统一收尾：同步联动（需要时重绘本组，本图也在组内）→ 否则只重绘本图 → 刷新筛选条。
  function afterDrillChange(c) {
    var changed = applyDrillLink(c);
    if (changed && c.spec && c.spec.link) {
      reRenderGroup(c.spec.link);
    } else {
      renderChart(c);
    }
    syncFilterBar();
  }

  // 重置下钻：把当前看板里所有图的 drill 清空（并清掉它们自己发出的联动），
  // 回到第一层。返回被重置的图数，没有下钻时不重绘。
  function resetDrill(el) {
    var root = rootOf(el) || null;
    var hit = [], i;
    for (i = 0; i < EazyViz.charts.length; i++) {
      var c = EazyViz.charts[i];
      if (!c || !c.state || !c.state.drill || !c.state.drill.length) continue;
      if (root && !inRoot(c, root)) continue;
      hit.push(c);
    }
    if (!hit.length) return 0;
    for (i = 0; i < hit.length; i++) {
      hit[i].state.drill = [];
      applyDrillLink(hit[i]);
    }
    for (i = 0; i < EazyViz.charts.length; i++) {
      var ch = EazyViz.charts[i];
      if (root && !inRoot(ch, root)) continue;
      syncFilters(ch);
      renderChart(ch);
    }
    syncFilterBar();
    return hit.length;
  }

  function handleCrumb(c, depth) {
    if (!c || !c.state) return;
    var n = (c.state.drill || []).length;
    depth = Math.max(0, Math.min(Number(depth) || 0, n));
    c.state.drill = c.state.drill.slice(0, depth);
    afterDrillChange(c);
  }

  function handleBack(c) {
    if (!c || !c.state || !c.state.drill || !c.state.drill.length) return;
    c.state.drill.pop();
    afterDrillChange(c);
  }

  function resizeAll() {
    for (var i = 0; i < EazyViz.charts.length; i++) {
      var c = EazyViz.charts[i];
      var w = c.el.clientWidth;
      var narrow = w > 0 && w < 480;
      // 宽度跨过断点：图例位置 / 字号 / grid 边距都要重算，光 resize 只是拉伸旧布局
      if (c.ec && c._narrow !== undefined && c._narrow !== narrow) {
        activeWidth = w;
        c.ec.setOption(buildOption(c.spec, c.data, c.state, c.theme), true);
      }
      c._narrow = narrow;
      if (c.ec) {
        if (c._w === w) { continue; }
        c._w = w;
        c.ec.resize();
      }
      fitTexts(c.el);
    }
    fitResponsiveHeights();
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
    var node = scopeNode();
    // 关键：Streamlit 组件在同一 ShadowRoot 上可能重复调用 init()，
    // 若每次都 addEventListener，一个「返回」点击会被处理多次（回退多级甚至跳空），
    // 联动也会被 setLink 反复 toggle。这里保证同一个挂载点只绑定一次。
    if (node.__eazyGlobalBound) return;
    node.__eazyGlobalBound = true;

    node.addEventListener('click', function (e) {
      var el = e.target;
      while (el && el !== document) {
        if (el.getAttribute) {
          if (el.hasAttribute('data-crumb')) {
            handleCrumb(chartFor(el, Number(el.getAttribute('data-chart'))),
              Number(el.getAttribute('data-crumb')));
            return;
          }
          var metricId = el.getAttribute('data-eazy-metric');
          if (metricId) { selectMetric(metricId); return; }
          var codeIdx = el.getAttribute('data-eazy-code');
          if (codeIdx !== null && codeIdx !== undefined) { toggleCode(Number(codeIdx)); return; }
          var copyIdx = el.getAttribute('data-eazy-copy');
          if (copyIdx !== null && copyIdx !== undefined) { copyCode(Number(copyIdx), el); return; }
          if (el.hasAttribute('data-eazy-theme')) {
            setTheme(EazyViz.page.theme === 'dark' ? 'light' : 'dark');
            return;
          }
          if (el.hasAttribute('data-eazy-reset')) {
            resetAll();
            return;
          }
          if (el.hasAttribute('data-eazy-reset-drill')) {
            resetDrill(el);
            return;
          }
          if (el.hasAttribute('data-back')) {
            handleBack(chartFor(el, Number(el.getAttribute('data-back'))));
            return;
          }
          var gl = el.getAttribute('data-clear-link');
          if (gl) { clearLink(gl); return; }
          // 明细表单元格 → 联动：把「列 = 单元格值」写进联动组，图表跟着筛。
          // 点同一格再点一次 = 取消（setLink 内部做 toggle）。
          var cellDim = el.getAttribute('data-eazy-cell');
          if (cellDim !== null && cellDim !== undefined && cellDim !== '') {
            var cellChart = chartOfEl(el);
            if (cellChart && cellChart.spec && cellChart.spec.link) {
              var cellVal = el.getAttribute('data-eazy-val');
              setLink(cellChart.spec.link, cellDim, cellVal, cellChart);
              syncFilterBar();
              // 表格单元格点击同样是「选中了一个数据点」：开了 on_select 就回传 Python
              if (EazyViz.onSelect) {
                try {
                  EazyViz.onSelect({
                    chart: cellChart.spec.id,
                    title: cellChart.spec.title || '',
                    type: 'table',
                    dim: cellDim,
                    value: cellVal,
                    drill: [],
                    link: EazyViz.links[cellChart.spec.link] || null
                  });
                } catch (err) { /* 回调异常不影响渲染 */ }
              }
            }
            return;
          }
        }
        el = el.parentNode;
      }
    });

    node.addEventListener('change', function (e) {
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

  // 一键重置：清联动 + 清每张图的下钻，回到初始视图
  function resetAll() {
    EazyViz.links = {};
    for (var i = 0; i < EazyViz.charts.length; i++) {
      var c = EazyViz.charts[i];
      c.zoomPath = null;   // 旭日图也回到根，别停在某个圈里
      if (c.state && c.state.drill) c.state.drill = [];
      syncFilters(c);
      renderChart(c);
      renderToolbar(c);
    }
    syncFilterBar();
  }

  function clearAllLinks() {
    resetAll();
  }

  // 供外部（streamlit 回调 / 自定义工具栏）主动重置下钻
  EazyViz.resetDrill = resetDrill;
  EazyViz.resetAll = resetAll;
  EazyViz.chartOfEl = chartOfEl;

  EazyViz.init = function (page, rootEl) {
    EazyViz.page = page || {};
    // 同一个页面可能挂了几个看板：不能每次 init 都把别人的图清掉，
    // 否则后面的看板一初始化，前面看板的联动就失效了。
    // 这里只剔除已经从 DOM 上摘掉的图（streamlit rerun 会换 innerHTML）。
    var alive = [];
    for (var ai = 0; ai < (EazyViz.charts || []).length; ai++) {
      var oldc = EazyViz.charts[ai];
      if (oldc.el && oldc.el.isConnected) alive.push(oldc);
      else if (oldc.ec && oldc.ec.dispose) { try { oldc.ec.dispose(); } catch (e0) { /* ignore */ } }
    }
    EazyViz.charts = alive;
    if (!alive.length) EazyViz.links = {};
    EazyViz.hints = !!EazyViz.page.hints;
    EazyViz.selection = EazyViz.page.selection || null;
    EazyViz.cardStyle = EazyViz.page.cardStyle || 'default';
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
    // 窄屏（手机 / 窄侧栏）先把画布高度收一收，再让 ECharts 按新高度重排
    fitResponsiveHeights();
    EazyViz.charts.forEach(function (c) { if (c.ec) { c._w = 0; c.ec.resize(); } });
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
      firstNum: firstNum, sparkCurve: sparkCurve,
      setAxisName: setAxisName, makeCategoryAxis: makeCategoryAxis,
      makeValueAxis: makeValueAxis, tooltipBox: tooltipBox, axisTooltip: axisTooltip,
      sourceSelection: sourceSelection, dimItem: dimItem, emptyOption: emptyOption,
      linkMode: linkMode, canSendLink: canSendLink, canRecvLink: canRecvLink,
    linkConds: linkConds, sameLink: sameLink,
      yoyPlan: yoyPlan,
    nameOrder: nameOrder, yoyGrowth: yoyGrowth, yoyItem: yoyItem,
      nodeInfoOf: nodeInfoOf,
      catColor: catColor, paintItem: paintItem,
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
    rateOf: rateOf,
    computeKpi: computeKpi,
    compareRows: compareRows,
    applyFollow: applyFollow,
    selectMetric: selectMetric,
    applySelection: applySelection,
    metricSelOf: metricSelOf,
    kpiHTML: kpiHTML,
    buildTreemapTree: buildTreemapTree,
    onChartClick: onChartClick,
    setLink: setLink,
    applyDrillLink: applyDrillLink,
    syncFilters: syncFilters,
    reRenderGroup: reRenderGroup,
    linkMode: linkMode,
    canSendLink: canSendLink,
    canRecvLink: canRecvLink,
    linkConds: linkConds,
    sameLink: sameLink,
    makeLink: makeLink,
    nodeInfoOf: nodeInfoOf,
    afterDrillChange: afterDrillChange,
    handleCrumb: handleCrumb,
    handleBack: handleBack,
    renderToolbar: renderToolbar,
    setTheme: setTheme,
    setPalette: setPalette,
    PALETTES: PALETTES,
    clearAllLinks: clearAllLinks,
    resetAll: resetAll,
    kpiSparkPoints: kpiSparkPoints,
    kpiSparkSVG: kpiSparkSVG,
    renderToolbar: renderToolbar,
    syncFilterBar: syncFilterBar,
    THEME: THEME
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = EazyViz;
  }
})(typeof window !== 'undefined' ? window : this);
