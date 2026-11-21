/*! eazy_data_viz 扩展图表 B：sunburst / tree / sankey / graph / theme_river / calendar / gantt / candlestick / pyramid / area_pct / bar_pct */
(function () {
  'use strict';
  if (typeof window === 'undefined' || !window.EazyViz) return;
  var EazyViz = window.EazyViz, U = EazyViz.core.util;
  var B = EazyViz.extraBuilders, H = EazyViz.htmlBuilders;
  if (!B) return;

  // ======================================================================
  // 0. 通用小工具
  // ======================================================================

  // 主题色轮转（越界自动取模）
  function palAt(theme, i) {
    var p = theme.palette || [];
    if (!p.length) return theme.primary;
    var idx = i % p.length;
    if (idx < 0) idx = 0;
    return p[idx];
  }

  // 数值列：层级/关系类图用 roles.value，柱线类可能用 roles.y
  function measureCol(spec) {
    var roles = spec.roles || {};
    return roles.value || roles.y || null;
  }

  // 聚合方式：没有数值列时按记录数 count
  function aggHow(spec) {
    return spec.agg || (measureCol(spec) ? 'sum' : 'count');
  }

  function tipHead(text) {
    return '<div style="font-weight:600;margin-bottom:4px">' + U.esc(text) + '</div>';
  }

  function tipRow(label, value) {
    return '<div style="line-height:19px">' + U.esc(label) + '：<b>' + value + '</b></div>';
  }

  function cmpCats(data, dim) {
    return U.catRanker(data, dim) || U.compareCatX;
  }

  function pad2(n) {
    return n < 10 ? '0' + n : String(n);
  }

  // 时间值 -> 毫秒时间戳（支持毫秒数字、YYYY-MM-DD、YYYY-MM-DD HH:MM:SS）
  function toTime(v) {
    if (v === null || v === undefined || v === '') return null;
    if (typeof v === 'number' && isFinite(v)) return v;
    var s = String(v).replace(/^\s+|\s+$/g, '');
    if (!s) return null;
    var iso = s.replace(' ', 'T');
    if (/^\d{4}-\d{2}-\d{2}/.test(s)) {
      var t = new Date(iso).getTime();
      if (!isNaN(t)) return t;
    }
    var t2 = new Date(iso).getTime();
    if (isNaN(t2)) t2 = Date.parse(s);
    if (!isNaN(t2)) return t2;
    // 毫秒时间戳字符串（长度足够时才认定，避免把 "2024" 当年份）
    if (/^\d{12,14}$/.test(s)) return Number(s);
    return null;
  }

  // 毫秒时间戳 -> 可读日期（有��分秒时带上）
  function fmtDay(ms) {
    var d = new Date(ms);
    if (isNaN(d.getTime())) return '-';
    var s = d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate());
    if (d.getHours() || d.getMinutes() || d.getSeconds()) {
      s += ' ' + pad2(d.getHours()) + ':' + pad2(d.getMinutes());
    }
    return s;
  }

  // 任意日期值 -> YYYY-MM-DD
  function dateKey(v) {
    var s = String(v === null || v === undefined ? '' : v);
    var m = /^(\d{4})[-\/](\d{1,2})[-\/](\d{1,2})/.exec(s);
    if (m) {
      var mm = m[2].length < 2 ? '0' + m[2] : m[2];
      var dd = m[3].length < 2 ? '0' + m[3] : m[3];
      return m[1] + '-' + mm + '-' + dd;
    }
    var t = toTime(v);
    return t === null ? null : fmtDay(t).slice(0, 10);
  }

  // 一组类目是否全都是可解析的日期（决定主题河流用时间轴还是类目轴）
  function isDateLike(cats) {
    if (!cats.length) return false;
    for (var i = 0; i < cats.length; i++) {
      var s = String(cats[i]);
      if (!/^\d{4}[-\/]\d{1,2}([-\/]\d{1,2})?/.test(s)) return false;
      var t = new Date(s.replace(' ', 'T').replace(/\//g, '-')).getTime();
      if (isNaN(t)) return false;
    }
    return true;
  }

  // ----------------------------------------------------------------------
  // 层级树：每一级都带聚合值（tree 的 symbolSize / tooltip 需要）
  // ----------------------------------------------------------------------
  function buildTree(rows, dims, valCol, how, depth, theme, topIndex) {
    var dim = dims[depth];
    var buckets = {}, order = [];
    for (var i = 0; i < rows.length; i++) {
      var k = U.catName(rows[i][dim]);
      if (!buckets[k]) { buckets[k] = []; order.push(k); }
      buckets[k].push(rows[i]);
    }
    var nodes = [];
    for (var j = 0; j < order.length; j++) {
      var key = order[j];
      var sub = buckets[key];
      var g = U.groupBy(sub, [], valCol, how);
      var v = (g.length && g[0].value !== null && g[0].value !== undefined) ? g[0].value : 0;
      var idx = (topIndex === null || topIndex === undefined) ? j : topIndex;
      var node = {
        name: key,
        value: v,
        // 点击回传联动参数时用：这一层对应哪个维度、值是什么。
        // 不能用 treePathInfo 推，旭日图 rootToNode 放大后根会变、路径会变短。
        nodeDim: dim,
        nodeLayer: depth,
        nodeValue: key,
        itemStyle: { color: palAt(theme, idx) }
      };
      // 同一条分支用同一色相，越深越淡，层级更清楚
      if (depth > 0) node.itemStyle.opacity = Math.max(0.45, 1 - depth * 0.12);
      if (depth < dims.length - 1) {
        node.children = buildTree(sub, dims, valCol, how, depth + 1, theme, idx);
      }
      nodes.push(node);
    }
    return nodes;
  }

  function collectVals(nodes, out) {
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      var v = Number(n.value);
      if (isFinite(v)) out.push(v);
      if (n.children) collectVals(n.children, out);
    }
    return out;
  }

  // ----------------------------------------------------------------------
  // 桑基图分层：无入边的节点为第 0 层，逐层放宽（有环时兜底为 0 层）
  // ----------------------------------------------------------------------
  function sankeyLayer(names, links) {
    var indeg = {}, out = {}, layer = {}, i;
    for (i = 0; i < names.length; i++) indeg[names[i]] = 0;
    for (i = 0; i < links.length; i++) {
      indeg[links[i].target] = (indeg[links[i].target] || 0) + 1;
      if (!out[links[i].source]) out[links[i].source] = [];
      out[links[i].source].push(links[i].target);
    }
    var queue = [], head = 0;
    for (i = 0; i < names.length; i++) {
      if (!indeg[names[i]]) { queue.push(names[i]); layer[names[i]] = 0; }
    }
    while (head < queue.length) {
      var n = queue[head++];
      var next = out[n] || [];
      for (i = 0; i < next.length; i++) {
        var t = next[i];
        var nl = (layer[n] || 0) + 1;
        if (layer[t] === undefined || nl > layer[t]) layer[t] = nl;
        indeg[t]--;
        if (indeg[t] <= 0) queue.push(t);
      }
    }
    for (i = 0; i < names.length; i++) {
      if (layer[names[i]] === undefined) layer[names[i]] = 0;
    }
    return layer;
  }

  // ----------------------------------------------------------------------
  // 百分比堆叠 tooltip（保留 1 位小数）
  // ----------------------------------------------------------------------
  function pctTooltip(params, theme) {
    if (!params || !params.length) return '';
    var html = tipHead(params[0].axisValueLabel || params[0].name);
    for (var i = 0; i < params.length; i++) {
      var p = params[i];
      var raw = p.value;
      if (raw && typeof raw === 'object' && raw.value !== undefined) raw = raw.value;
      var n = Number(raw);
      html += '<div style="display:flex;align-items:center;gap:6px;line-height:19px">' + p.marker +
        '<span style="flex:1;max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' +
        U.esc(p.seriesName) + '</span><b style="margin-left:10px">' +
        (isFinite(n) ? n.toFixed(1) + '%' : '-') + '</b></div>';
    }
    html += '<div style="border-top:1px dashed ' + theme.axis +
      ';margin-top:4px;padding-top:4px;display:flex;justify-content:space-between;line-height:19px">' +
      '<span>合计</span><b>100.0%</b></div>';
    return html;
  }

  // ======================================================================
  // 3.18 sunburst 旭日图
  // ======================================================================
  B['sunburst'] = function (spec, data, state, theme) {
    var rows = U.filteredRows(spec, data, state);
    var dims = (spec.roles && spec.roles.path) || [];
    if (!rows.length || !dims.length) return U.emptyOption(theme);
    var tree = buildTree(rows, dims, measureCol(spec), aggHow(spec), 0, theme, null);
    var vcol = measureCol(spec) || '记录数';

    // 扇形太窄的名字不画：否则文字会互相压住、还会被 ECharts 挤到环外去。
    // 外层扇形最窄，要求占比更高；这些节点仍然能点、能悬停看 tooltip。
    var total = 0;
    for (var t = 0; t < tree.length; t++) total += Number(tree[t].value) || 0;
    var deepest = dims.length - 1;
    (function hideSmall(nodes, depth) {
      for (var i = 0; i < nodes.length; i++) {
        var nd = nodes[i];
        var v = Number(nd.value) || 0;
        var minShare = depth >= deepest ? 0.035 : (depth >= deepest - 1 ? 0.03 : 0.015);
        if (total > 0 && v / total < minShare) nd.label = { show: false };
        if (nd.children) hideSmall(nd.children, depth + 1);
      }
    })(tree, 0);

    // 环半径按层数均分（12% → 88%）：path 给到 4、5 级时也不会画到画布外。
    var ringLevels = [{}];
    var step = (88 - 12) / Math.max(1, dims.length);
    for (var lv = 0; lv < dims.length; lv++) {
      var isLast = lv === dims.length - 1;
      ringLevels.push({
        r0: (12 + step * lv).toFixed(1) + '%',
        r: (12 + step * (lv + 1)).toFixed(1) + '%',
        label: {
          rotate: lv === 0 ? 0 : 'tangential',
          fontSize: lv === 0 ? 12 : (isLast ? 10 : 11),
          fontWeight: lv === 0 ? 600 : 400,
          position: 'inside'
        }
      });
    }

    return {
      color: theme.palette,
      tooltip: (function () {
        var tip = U.tooltipBox(theme);
        tip.trigger = 'item';
        tip.formatter = function (p) {
          var path = [], info = p.treePathInfo || [];
          for (var i = 0; i < info.length; i++) {
            if (info[i] && info[i].name) path.push(info[i].name);
          }
          var title = path.length ? path.join(' / ') : p.name;
          return tipHead(title) + tipRow(vcol, U.fmtValue(p.value, spec.fmt));
        };
        return tip;
      })(),
      toolbox: U.makeToolbox(theme),
      series: [{
        type: 'sunburst',
        data: tree,
        radius: ['12%', '88%'],
        center: ['50%', '52%'],
        sort: null,
        nodeClick: 'rootToNode',
        itemStyle: { borderColor: theme.bg, borderWidth: 1.5 },
        label: {
          color: theme.text,
          fontSize: 11,
          position: 'inside',
          textBorderColor: theme.bg,
          textBorderWidth: 2
        },
        // 只有 3 层以上才需要「重叠就隐藏」：层数少时标签本来就够放，
        // 打开 hideOverlap 反而会把它判定成互相压住、只剩一个名字。
        labelLayout: { hideOverlap: dims.length >= 3 },
        labelLine: { show: false },
        levels: ringLevels,
        emphasis: { focus: 'ancestor', label: { show: true } }
      }]
    };
  };

  // ======================================================================
  // 3.19 tree 树图
  // ======================================================================
  B['tree'] = function (spec, data, state, theme) {
    var rows = U.filteredRows(spec, data, state);
    var dims = (spec.roles && spec.roles.path) || [];
    if (!rows.length || !dims.length) return U.emptyOption(theme);
    var tree = buildTree(rows, dims, measureCol(spec), aggHow(spec), 0, theme, null);
    var vals = collectVals(tree, []);
    var vmin = vals.length ? Math.min.apply(null, vals) : 0;
    var vmax = vals.length ? Math.max.apply(null, vals) : 1;
    if (vmax === vmin) vmax = vmin + 1;
    var total = 0;
    for (var i = 0; i < tree.length; i++) total += Number(tree[i].value) || 0;
    var vcol = measureCol(spec) || '记录数';
    var root = {
      name: '全部',
      value: total,
      itemStyle: { color: palAt(theme, 0) },
      children: tree
    };

    return {
      color: theme.palette,
      tooltip: (function () {
        var tip = U.tooltipBox(theme);
        tip.trigger = 'item';
        tip.formatter = function (p) {
          var html = tipHead(p.name);
          html += tipRow(vcol, U.fmtValue(p.value, spec.fmt));
          if (p.data && p.data.children) html += tipRow('下级节点', p.data.children.length + ' 个');
          return html;
        };
        return tip;
      })(),
      toolbox: U.makeToolbox(theme),
      series: [{
        type: 'tree',
        data: [root],
        layout: 'orthogonal',
        orient: 'LR',
        top: 34,
        left: 24,
        bottom: 30,
        right: 140,
        roam: true,
        expandAndCollapse: true,
        initialTreeDepth: Math.min(dims.length, 3),
        symbol: 'circle',
        symbolSize: function (value) {
          var n = Number(value);
          if (!isFinite(n)) return 10;
          return 9 + 19 * Math.sqrt((n - vmin) / (vmax - vmin));
        },
        label: {
          position: 'left',
          verticalAlign: 'middle',
          align: 'right',
          color: theme.text,
          fontSize: 11
        },
        leaves: {
          label: {
            position: 'right',
            verticalAlign: 'middle',
            align: 'left',
            color: theme.subtext,
            fontSize: 11
          }
        },
        lineStyle: { color: theme.axis, width: 1.2, curveness: 0.5 },
        itemStyle: { borderColor: theme.bg, borderWidth: 1 },
        emphasis: { focus: 'descendant' }
      }]
    };
  };

  // ======================================================================
  // 3.20 sankey 桑基图（多级：roles.path = [一级, 二级, 三级 …]）
  // ======================================================================
  // ECharts sankey 要求全图节点名唯一，而不同层级很容易出现同名值
  // （例如「华东」既是 大区 也是 渠道），所以节点内部名用
  // "层级\u0001值" 编码，label/tooltip/点击回调再解码回真实值。
  var NODE_SEP = '\u0001';

  function sankeyDims(spec) {
    var roles = spec.roles || {};
    var dims = roles.path;
    if (dims && dims.length) return dims;
    var two = [];
    if (roles.source) two.push(roles.source);
    if (roles.target) two.push(roles.target);
    return two;
  }

  B['sankey'] = function (spec, data, state, theme) {
    var rows = U.filteredRows(spec, data, state);
    var dims = sankeyDims(spec);
    var vcol = measureCol(spec);
    var how = aggHow(spec);
    if (!rows.length || dims.length < 2) return U.emptyOption(theme);
    for (var d0 = 0; d0 < dims.length; d0++) {
      if (!U.hasCol(data, dims[d0])) return U.emptyOption(theme);
    }

    var nodeInfo = {};     // 唯一名 -> { dim, value, layer }
    var order = [];        // 唯一名出现顺序
    var totals = {};       // 唯一名 -> 关联总量
    var links = [];
    var dropped = 0;

    function register(name, dim, value, layer) {
      if (!nodeInfo[name]) {
        nodeInfo[name] = { dim: dim, value: value, layer: layer };
        order.push(name);
        totals[name] = 0;
      }
      return name;
    }

    // 逐层聚合：path[i] → path[i+1]，每层各自 groupBy，节点不跨层合并。
    for (var lv = 0; lv < dims.length - 1; lv++) {
      var groups = U.groupBy(rows, [dims[lv], dims[lv + 1]], vcol, how);
      for (var i = 0; i < groups.length; i++) {
        var g = groups[i];
        var sv = g.keys[0], tv = g.keys[1];
        if (sv === null || sv === undefined || sv === '' ||
            tv === null || tv === undefined || tv === '') { dropped++; continue; }
        var v = Number(g.value);
        if (!isFinite(v) || v <= 0 || sv === tv) { dropped++; continue; }
        v = Math.round(v * 1000) / 1000;
        var sn = register(lv + NODE_SEP + sv, dims[lv], sv, lv);
        var tn = register((lv + 1) + NODE_SEP + tv, dims[lv + 1], tv, lv + 1);
        totals[sn] += v;
        totals[tn] += v;
        links.push({ source: sn, target: tn, value: v });
      }
    }
    if (!links.length) return U.emptyOption(theme);

    // 联动高亮：本图作为联动发起方时，把同一维度上的其它节点淡出
    var selDim = null, selValue = null;
    if (spec.link && EazyViz.links) {
      var lk = EazyViz.links[spec.link];
      if (lk && lk.sourceId === spec.id) { selDim = lk.dim; selValue = lk.value; }
    }

    function labelOf(name) {
      var m = nodeInfo[name];
      return m ? U.catName(m.value) : name;
    }

    function dimOf(name) {
      var m = nodeInfo[name];
      return m ? m.dim : '';
    }

    var nodes = [];
    for (var j = 0; j < order.length; j++) {
      var nm = order[j];
      var info = nodeInfo[nm];
      var item = {
        name: nm,
        itemStyle: {
          color: palAt(theme, info.layer || 0),
          borderColor: theme.bg,
          borderWidth: 1
        }
      };
      if (selDim !== null && info.dim === selDim && U.catName(info.value) !== U.catName(selValue)) {
        item.itemStyle.opacity = 0.25;
      }
      nodes.push(item);
    }

    // 供 onChartClick 取回 (维度, 真实值)：点击节点时 p.name 是唯一名
    if (!EazyViz.nodeMaps) EazyViz.nodeMaps = {};
    EazyViz.nodeMaps[spec.id || spec.type] = nodeInfo;

    return {
      color: theme.palette,
      tooltip: (function () {
        var tip = U.tooltipBox(theme);
        tip.trigger = 'item';
        tip.formatter = function (p) {
          if (p.dataType === 'edge') {
            var d = p.data || {};
            return tipHead(labelOf(d.source) + ' → ' + labelOf(d.target)) +
              tipRow(vcol || '记录数', U.fmtValue(d.value, spec.fmt));
          }
          return tipHead(labelOf(p.name)) +
            tipRow(dimOf(p.name) + ' · 关联总量', U.fmtValue(totals[p.name] || 0, spec.fmt));
        };
        return tip;
      })(),
      toolbox: U.makeToolbox(theme),
      series: [{
        type: 'sankey',
        data: nodes,
        links: links,
        left: 16,
        right: 130,
        top: 28,
        bottom: 16,
        nodeWidth: 14,
        nodeGap: 12,
        nodeAlign: 'justify',
        layoutIterations: 40,
        draggable: true,
        label: {
          color: theme.text,
          fontSize: 11,
          formatter: function (p) { return labelOf(p.name); }
        },
        itemStyle: { borderWidth: 0 },
        lineStyle: { color: 'gradient', opacity: 0.3, curveness: 0.5 },
        emphasis: { focus: 'adjacency', lineStyle: { opacity: 0.55 } },
        labelLayout: { hideOverlap: true }
      }]
    };
  };

  // ======================================================================
  // 3.21 graph 关系图（力导向）
  // ======================================================================
  B['graph'] = function (spec, data, state, theme) {
    var rows = U.filteredRows(spec, data, state);
    var roles = spec.roles || {};
    var sdim = roles.source, tdim = roles.target;
    if (!rows.length || !sdim || !tdim) return U.emptyOption(theme);
    var vcol = measureCol(spec);
    var groups = U.groupBy(rows, [sdim, tdim], vcol, aggHow(spec));
    var totals = {}, order = [], rawLinks = [], maxLink = 0, i;

    function touch(name) {
      if (totals[name] === undefined) { totals[name] = 0; order.push(name); }
    }

    for (i = 0; i < groups.length; i++) {
      var g = groups[i];
      var s = U.catName(g.keys[0]);
      var t = U.catName(g.keys[1]);
      var v = Number(g.value);
      if (!isFinite(v) || v <= 0 || s === t) continue;
      touch(s);
      touch(t);
      totals[s] += v;
      totals[t] += v;
      if (v > maxLink) maxLink = v;
      rawLinks.push({ source: s, target: t, value: Math.round(v * 1000) / 1000 });
    }
    if (!rawLinks.length) return U.emptyOption(theme);

    var tmin = Infinity, tmax = -Infinity;
    for (i = 0; i < order.length; i++) {
      var tv = totals[order[i]];
      if (tv < tmin) tmin = tv;
      if (tv > tmax) tmax = tv;
    }
    if (!isFinite(tmin) || !isFinite(tmax)) { tmin = 0; tmax = 1; }
    var span = tmax - tmin;

    var nodes = [];
    for (i = 0; i < order.length; i++) {
      var name = order[i];
      nodes.push({
        name: name,
        value: Math.round(totals[name] * 1000) / 1000,
        symbolSize: span > 0 ? 10 + 26 * Math.sqrt((totals[name] - tmin) / span) : 18,
        itemStyle: {
          color: palAt(theme, i),
          borderColor: theme.bg,
          borderWidth: 1.5
        }
      });
    }
    var links = [];
    for (i = 0; i < rawLinks.length; i++) {
      var rl = rawLinks[i];
      links.push({
        source: rl.source,
        target: rl.target,
        value: rl.value,
        lineStyle: {
          width: Math.round((1 + 4 * Math.sqrt(rl.value / maxLink)) * 10) / 10,
          opacity: 0.55
        }
      });
    }

    return {
      color: theme.palette,
      tooltip: (function () {
        var tip = U.tooltipBox(theme);
        tip.trigger = 'item';
        tip.formatter = function (p) {
          if (p.dataType === 'edge') {
            var d = p.data || {};
            return tipHead(U.catName(d.source) + ' — ' + U.catName(d.target)) +
              tipRow(vcol || '记录数', U.fmtValue(d.value, spec.fmt));
          }
          return tipHead(p.name) + tipRow('连接总值', U.fmtValue(totals[p.name] || 0, spec.fmt));
        };
        return tip;
      })(),
      toolbox: U.makeToolbox(theme),
      series: [{
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        data: nodes,
        links: links,
        force: { repulsion: 230, edgeLength: [50, 140], gravity: 0.1 },
        label: {
          show: true,
          position: 'right',
          color: theme.text,
          fontSize: 11
        },
        lineStyle: { color: theme.axis, curveness: 0.12 },
        itemStyle: { borderColor: theme.bg, borderWidth: 1.5 },
        emphasis: {
          focus: 'adjacency',
          label: { fontWeight: 'bold' },
          lineStyle: { opacity: 0.9 }
        }
      }]
    };
  };

  // ======================================================================
  // 3.22 theme_river 主题河流图
  // ======================================================================
  B['theme_river'] = function (spec, data, state, theme) {
    // 主题河流 = 堆叠平滑面积（streamgraph）。ECharts 的 themeRiver 组件要求
    // time 轴（真实日期），按月份/类目分组时会渲染空白，所以这里用 line+stack
    // 实现等价视觉效果，同时兼容类目轴、联动过滤与主题切换。
    var rows = U.filteredRows(spec, data, state);
    var roles = spec.roles || {};
    var xdim = roles.x, cdim = roles.color;
    if (!rows.length || !xdim || !cdim) return U.emptyOption(theme);
    var vcol = measureCol(spec);
    var groups = U.groupBy(rows, [xdim, cdim], vcol, aggHow(spec));
    var catOrder = [], seriesOrder = [], cell = {}, i;

    for (i = 0; i < groups.length; i++) {
      var g = groups[i];
      var xv = g.keys[0], sv = g.keys[1];
      if (catOrder.indexOf(xv) < 0) catOrder.push(xv);
      if (seriesOrder.indexOf(sv) < 0) seriesOrder.push(sv);
      var v = Number(g.value);
      if (!isFinite(v) || v < 0) v = 0;
      cell[xv + U.SEP + sv] = v;
    }
    if (!catOrder.length || !seriesOrder.length) return U.emptyOption(theme);
    if (spec.sort === 'x' || spec.sort === 'asc' || spec.sort === 'desc' || isDateLike(catOrder)) {
      catOrder.sort(cmpCats(data, xdim));
    }

    var series = [];
    for (var s = 0; s < seriesOrder.length; s++) {
      var arr = [];
      for (var c = 0; c < catOrder.length; c++) {
        var val = cell[catOrder[c] + U.SEP + seriesOrder[s]];
        arr.push(val === undefined ? 0 : val);
      }
      series.push({
        name: String(seriesOrder[s]), type: 'line', stack: 'river',
        data: arr, symbol: 'none', smooth: 0.4,
        lineStyle: { width: 0, opacity: 0 },
        areaStyle: { opacity: 0.9, color: palAt(theme, s) },
        emphasis: { focus: 'series', areaStyle: { opacity: 1 } },
        itemStyle: { borderWidth: 0 }
      });
    }

    var catAxis = U.makeCategoryAxis(spec, catOrder, theme);
    var valAxis = U.makeValueAxis(spec, theme, spec.ylim);
    U.setAxisName(catAxis, U.axisTitle(spec.xtitle, xdim), theme, true);
    U.setAxisName(valAxis, U.axisTitle(spec.ytitle, vcol), theme, false);

    var tip = U.tooltipBox(theme);
    tip.trigger = 'axis';
    tip.axisPointer = { type: 'line', lineStyle: { color: theme.axis } };
    tip.formatter = function (params) {
      if (!params || !params.length) return '';
      var html = tipHead(String(params[0].axisValueLabel || params[0].name || ''));
      for (var k = 0; k < params.length; k++) {
        var p = params[k];
        html += '<div style="display:flex;align-items:center;gap:6px;line-height:19px">' + p.marker +
          '<span style="flex:1;max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' +
          U.esc(p.seriesName) + '</span>' +
          '<b style="margin-left:10px">' + U.fmtValue(p.value, spec.fmt) + '</b></div>';
      }
      return html;
    };

    return {
      color: theme.palette,
      grid: U.makeGrid(theme, { legend: true }),
      legend: U.makeLegend(theme, state.legendSel, true),
      toolbox: U.makeToolbox(theme),
      tooltip: tip,
      xAxis: catAxis,
      yAxis: valAxis,
      series: series
    };
  };

  // ======================================================================
  // 3.23 calendar 日历热力图
  // ======================================================================
  B['calendar'] = function (spec, data, state, theme) {
    var rows = U.filteredRows(spec, data, state);
    var roles = spec.roles || {};
    var ddim = roles.x;
    if (!rows.length || !ddim) return U.emptyOption(theme);
    var vcol = measureCol(spec);
    var groups = U.groupBy(rows, [ddim], vcol, aggHow(spec));
    var dayMap = {}, days = [];

    for (var i = 0; i < groups.length; i++) {
      var g = groups[i];
      var day = dateKey(g.keys[0]);
      if (!day) continue;
      var v = Number(g.value);
      if (!isFinite(v)) continue;
      dayMap[day] = v;
      days.push(day);
    }
    if (!days.length) return U.emptyOption(theme);
    days.sort(U.compareCatX);

    var points = [], minV = Infinity, maxV = -Infinity;
    for (var k = 0; k < days.length; k++) {
      var val = dayMap[days[k]];
      points.push([days[k], val]);
      if (val < minV) minV = val;
      if (val > maxV) maxV = val;
    }
    if (!isFinite(minV)) { minV = 0; maxV = 1; }
    if (maxV === minV) maxV = minV + 1;

    var y0 = parseInt(days[0].slice(0, 4), 10);
    var y1 = parseInt(days[days.length - 1].slice(0, 4), 10);
    var calRange = (y0 === y1) ? String(y0) : [y0 + '-01-01', y1 + '-12-31'];

    return {
      color: theme.palette,
      tooltip: (function () {
        var tip = U.tooltipBox(theme);
        tip.trigger = 'item';
        tip.formatter = function (p) {
          var d = p.value || p.data || [];
          return tipHead(d[0]) + tipRow(vcol || '记录数', U.fmtValue(d[1], spec.fmt));
        };
        return tip;
      })(),
      toolbox: U.makeToolbox(theme),
      visualMap: {
        min: minV,
        max: maxV,
        calculable: false,
        orient: 'horizontal',
        left: 'center',
        bottom: 2,
        itemWidth: 10,
        itemHeight: 70,
        textStyle: { color: theme.subtext, fontSize: 10 },
        formatter: function (v) { return U.fmtValue(v, spec.fmt); },
        inRange: { color: theme.heat }
      },
      calendar: {
        top: 42,
        left: 34,
        right: 30,
        bottom: 64,
        cellSize: ['auto', 14],
        range: calRange,
        orient: 'horizontal',
        yearLabel: { show: true, margin: 26, color: theme.subtext, fontSize: 11 },
        dayLabel: { firstDay: 1, color: theme.subtext, fontSize: 10 },
        monthLabel: { color: theme.text, fontSize: 11 },
        itemStyle: { color: 'transparent', borderColor: theme.split, borderWidth: 1 },
        splitLine: { show: false }
      },
      series: [{
        type: 'heatmap',
        coordinateSystem: 'calendar',
        data: points,
        itemStyle: { borderColor: theme.bg, borderWidth: 1 },
        emphasis: { itemStyle: { borderColor: theme.text, borderWidth: 1 } }
      }]
    };
  };

  // ======================================================================
  // 3.24 gantt 甘特图（custom series 画圆角矩形）
  // ======================================================================
  B['gantt'] = function (spec, data, state, theme) {
    var rows = U.filteredRows(spec, data, state);
    var roles = spec.roles || {};
    var xdim = roles.x, sdim = roles.start, edim = roles.end, cdim = roles.color;
    if (!rows.length || !xdim || !sdim || !edim) return U.emptyOption(theme);

    var map = {}, order = [], i;
    for (i = 0; i < rows.length; i++) {
      var row = rows[i];
      var start = toTime(row[sdim]), end = toTime(row[edim]);
      if (start === null || end === null) continue;
      if (end < start) { var tmp = start; start = end; end = tmp; }
      var task = U.catName(row[xdim]);
      var rec = map[task];
      if (!rec) {
        rec = {
          name: task, start: start, end: end,
          group: cdim ? U.catName(row[cdim]) : ''
        };
        map[task] = rec;
        order.push(task);
      } else {
        if (start < rec.start) rec.start = start;
        if (end > rec.end) rec.end = end;
      }
    }
    if (!order.length) return U.emptyOption(theme);

    // 按开始时间排任务，第一项在顶部（category 轴 inverse）
    order.sort(function (a, b) {
      var ra = map[a], rb = map[b];
      if (ra.start !== rb.start) return ra.start - rb.start;
      return a < b ? -1 : (a > b ? 1 : 0);
    });

    var cats = [], taskIndex = {};
    for (i = 0; i < order.length; i++) {
      taskIndex[order[i]] = i;
      cats.push(order[i]);
    }

    // 按 color 分组，每组一个 custom series（图例、配色都按组）
    var groupMap = {}, groupOrder = [];
    for (i = 0; i < order.length; i++) {
      var r2 = map[order[i]];
      var gname = cdim ? r2.group : '';
      if (groupMap[gname] === undefined) { groupMap[gname] = []; groupOrder.push(gname); }
      groupMap[gname].push({
        name: r2.name,
        value: [taskIndex[r2.name], r2.start, r2.end]
      });
    }

    // renderItem：在任务行上按起止时间画圆角矩形
    function renderItem(params, api) {
      var idx = api.value(0);
      var spt = api.coord([api.value(1), idx]);
      var ept = api.coord([api.value(2), idx]);
      var band = api.size([0, 1])[1] || 20;
      var h = Math.max(8, Math.min(26, band * 0.55));
      var w = Math.max(2, ept[0] - spt[0]);
      var rect = {
        type: 'rect',
        shape: {
          x: spt[0],
          y: spt[1] - h / 2,
          width: w,
          height: h,
          r: Math.min(4, h / 2)
        },
        style: api.style()
      };
      if (!spec.labels || w < 26) return rect;
      var label = cats[idx] === undefined ? '' : cats[idx];
      return {
        type: 'group',
        children: [
          rect,
          {
            type: 'text',
            style: {
              x: spt[0] + 6,
              y: spt[1],
              text: U.truncate(label, 18),
              fill: theme.bg,
              font: '11px ' + U.FONT,
              verticalAlign: 'middle'
            }
          }
        ]
      };
    }

    var series = [];
    for (i = 0; i < groupOrder.length; i++) {
      var gkey = groupOrder[i];
      series.push({
        name: gkey || U.axisTitle(spec.ytitle, '任务'),
        type: 'custom',
        renderItem: renderItem,
        encode: { x: [1, 2], y: 0 },
        data: groupMap[gkey],
        itemStyle: { color: palAt(theme, i) },
        emphasis: { itemStyle: { opacity: 0.9 } }
      });
    }

    var showLegend = !!(cdim && spec.legend !== false);
    var xAxis = {
      type: 'time',
      axisLine: { lineStyle: { color: theme.axis } },
      axisTick: { show: false },
      axisLabel: {
        color: theme.subtext,
        fontSize: 10,
        hideOverlap: true,
        formatter: function (v) { return fmtDay(v).slice(0, 10); }
      },
      splitLine: { lineStyle: { color: theme.split, type: 'dashed' } }
    };
    U.setAxisName(xAxis, U.axisTitle(spec.xtitle, sdim || '时间'), theme, true);

    var yAxis = {
      type: 'category',
      data: cats,
      inverse: true,
      axisLine: { lineStyle: { color: theme.axis } },
      axisTick: { show: false },
      axisLabel: {
        color: theme.subtext,
        fontSize: 11,
        formatter: function (v) { return U.truncate(v, 16); }
      },
      splitLine: { show: false }
    };
    U.setAxisName(yAxis, U.axisTitle(spec.ytitle, xdim), theme, false, 20);

    return {
      color: theme.palette,
      grid: U.makeGrid(theme, { legend: showLegend }),
      legend: U.makeLegend(theme, state.legendSel, showLegend),
      tooltip: (function () {
        var tip = U.tooltipBox(theme);
        tip.trigger = 'item';
        tip.formatter = function (p) {
          var val = p.data && p.data.value ? p.data.value : p.value;
          if (!val) return '';
          var s = Number(val[1]), e = Number(val[2]);
          var days = Math.max(1, Math.round((e - s) / 86400000 * 10) / 10);
          var html = tipHead(p.name);
          if (showLegend) html += tipRow(cdim, p.seriesName);
          html += tipRow('开始', fmtDay(s));
          html += tipRow('结束', fmtDay(e));
          html += tipRow('工期', days + ' 天');
          return html;
        };
        return tip;
      })(),
      toolbox: U.makeToolbox(theme),
      xAxis: xAxis,
      yAxis: yAxis,
      series: series
    };
  };

  // ======================================================================
  // 3.25 candlestick K 线图（中国习惯：红涨绿跌）
  // ======================================================================
  B['candlestick'] = function (spec, data, state, theme) {
    var rows = U.filteredRows(spec, data, state);
    var roles = spec.roles || {};
    var xdim = roles.x;
    if (!rows.length || !xdim || !roles.open || !roles.high || !roles.low || !roles.close) {
      return U.emptyOption(theme);
    }
    var cats = [], ohlc = [];
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      var o = U.num(r[roles.open]);
      var h = U.num(r[roles.high]);
      var l = U.num(r[roles.low]);
      var c = U.num(r[roles.close]);
      if (o === null || h === null || l === null || c === null) continue;
      cats.push(U.catName(r[xdim]));
      ohlc.push([o, c, l, h]);
    }
    if (!cats.length) return U.emptyOption(theme);

    var xAxis = U.makeCategoryAxis(spec, cats, theme);
    xAxis.boundaryGap = true;
    U.setAxisName(xAxis, U.axisTitle(spec.xtitle, xdim), theme, true);
    var yAxis = U.makeValueAxis(spec, theme, spec.ylim);
    U.setAxisName(yAxis, U.axisTitle(spec.ytitle, roles.close), theme, false);

    var zoom = spec.zoom === true || (spec.zoom !== false && cats.length > 30);
    var opt = {
      color: theme.palette,
      grid: U.makeGrid(theme, { legend: false, zoom: zoom }),
      toolbox: U.makeToolbox(theme),
      tooltip: (function () {
        var tip = U.tooltipBox(theme);
        tip.trigger = 'axis';
        tip.axisPointer = {
          type: 'cross',
          label: { backgroundColor: theme.axis, color: theme.bg }
        };
        tip.formatter = function (params) {
          if (!params || !params.length) return '';
          var idx = params[0].dataIndex;
          var d = ohlc[idx];
          if (!d) return '';
          var up = d[1] >= d[0];
          var col = up ? theme.palette[3] : theme.palette[1];
          return tipHead(cats[idx]) +
            '<div style="line-height:19px">开盘：' + U.fmtValue(d[0], spec.fmt) + '</div>' +
            '<div style="line-height:19px">最高：' + U.fmtValue(d[3], spec.fmt) + '</div>' +
            '<div style="line-height:19px">最低：' + U.fmtValue(d[2], spec.fmt) + '</div>' +
            '<div style="line-height:19px">收盘：<b style="color:' + col + '">' +
            U.fmtValue(d[1], spec.fmt) + '</b></div>';
        };
        return tip;
      })(),
      xAxis: xAxis,
      yAxis: yAxis,
      series: [{
        name: roles.close,
        type: 'candlestick',
        data: ohlc,
        itemStyle: {
          color: theme.palette[3],
          color0: theme.palette[1],
          borderColor: theme.palette[3],
          borderColor0: theme.palette[1]
        },
        emphasis: { itemStyle: { borderWidth: 2 } }
      }]
    };
    if (zoom) {
      var startPct = cats.length > 60 ? Math.round((1 - 60 / cats.length) * 100) : 0;
      opt.dataZoom = [
        { type: 'inside', start: startPct, end: 100 },
        {
          type: 'slider', height: 16, bottom: 4,
          borderColor: 'transparent', backgroundColor: 'transparent',
          fillerColor: 'rgba(26,115,232,0.12)',
          handleSize: '88%', brushSelect: false,
          textStyle: { color: theme.subtext, fontSize: 10 }
        }
      ];
    }
    return opt;
  };

  // ======================================================================
  // 3.26 pyramid 金字塔图（漏斗 sort:ascending -> 下宽上窄）
  // ======================================================================
  B['pyramid'] = function (spec, data, state, theme) {
    var rows = U.filteredRows(spec, data, state);
    var roles = spec.roles || {};
    var ndim = roles.names;
    if (!rows.length || !ndim) return U.emptyOption(theme);
    var vcol = measureCol(spec);
    var groups = U.groupBy(rows, [ndim], vcol, aggHow(spec));
    var items = [], total = 0, i;
    for (i = 0; i < groups.length; i++) {
      var v = Number(groups[i].value);
      if (!isFinite(v)) v = 0;
      items.push({ name: groups[i].keys[0], value: v });
      total += v;
    }
    if (!items.length) return U.emptyOption(theme);
    items.sort(function (a, b) { return b.value - a.value; });

    return {
      color: theme.palette,
      tooltip: (function () {
        var tip = U.tooltipBox(theme);
        tip.trigger = 'item';
        tip.formatter = function (p) {
          var pct = total ? (Number(p.value) / total * 100).toFixed(1) : '0.0';
          return tipHead(p.name) + tipRow(vcol || '记录数', U.fmtValue(p.value, spec.fmt)) +
            tipRow('占比', pct + '%');
        };
        return tip;
      })(),
      toolbox: U.makeToolbox(theme),
      series: [{
        type: 'funnel',
        sort: 'ascending',
        gap: 2,
        left: '10%',
        right: '10%',
        top: 24,
        bottom: 16,
        minSize: '18%',
        maxSize: '100%',
        funnelAlign: 'center',
        label: {
          show: spec.labels !== false,
          position: 'inside',
          color: theme.text,
          fontSize: 11,
          textBorderColor: theme.bg,
          textBorderWidth: 1.5,
          formatter: function (p) { return p.name; }
        },
        labelLine: { show: false },
        itemStyle: { borderColor: theme.bg, borderWidth: 1.5 },
        emphasis: { label: { fontSize: 13 } },
        data: items
      }]
    };
  };

  // ======================================================================
  // 3.27 area_pct / bar_pct 百分比堆叠
  // ======================================================================
  function buildPercentStack(spec, data, state, theme, isArea) {
    var rows = U.filteredRows(spec, data, state);
    var roles = spec.roles || {};
    var xdim = U.currentXDim(spec, state) || roles.x;
    var cdim = roles.color;
    if (!rows.length || !xdim || !cdim) return U.emptyOption(theme);
    var vcol = measureCol(spec);
    var groups = U.groupBy(rows, [xdim, cdim], vcol, aggHow(spec));
    var catOrder = [], seriesOrder = [], cell = {}, totals = {}, i;

    for (i = 0; i < groups.length; i++) {
      var g = groups[i];
      var xv = g.keys[0], sv = g.keys[1];
      if (catOrder.indexOf(xv) < 0) { catOrder.push(xv); totals[xv] = 0; }
      if (seriesOrder.indexOf(sv) < 0) seriesOrder.push(sv);
      var v = Number(g.value);
      if (!isFinite(v)) v = 0;
      cell[xv + U.SEP + sv] = v;
      totals[xv] += v;
    }
    if (!catOrder.length || !seriesOrder.length) return U.emptyOption(theme);

    if (spec.sort === 'desc' || spec.sort === 'asc') {
      var dir = spec.sort === 'desc' ? -1 : 1;
      catOrder.sort(function (a, b) { return dir * (totals[a] - totals[b]); });
    } else if (spec.sort === 'x' || U.catRanker(data, xdim)) {
      catOrder.sort(cmpCats(data, xdim));
    }

    var xAxis = U.makeCategoryAxis(spec, catOrder, theme);
    if (isArea) xAxis.boundaryGap = false;
    U.setAxisName(xAxis, U.axisTitle(spec.xtitle, xdim), theme, true);

    var yAxis = U.makeValueAxis(spec, theme, spec.ylim);
    yAxis.min = 0;
    yAxis.max = 100;
    yAxis.axisLabel.formatter = function (v) { return v + '%'; };
    U.setAxisName(yAxis, U.axisTitle(spec.ytitle, '占比'), theme, false);

    var series = [];
    for (var s = 0; s < seriesOrder.length; s++) {
      var name = seriesOrder[s];
      var vals = [];
      for (var c = 0; c < catOrder.length; c++) {
        var tot = totals[catOrder[c]];
        var raw = cell[catOrder[c] + U.SEP + name];
        if (raw === undefined) raw = 0;
        vals.push(tot ? Math.round(raw / tot * 1000) / 10 : 0);
      }
      var sr;
      if (isArea) {
        sr = {
          name: name, type: 'line', stack: 'pct', data: vals,
          smooth: true, symbol: 'none', showSymbol: false,
          lineStyle: { width: 1 },
          areaStyle: { opacity: 0.9 },
          emphasis: { focus: 'series' }
        };
      } else {
        sr = {
          name: name, type: 'bar', stack: 'pct', data: vals,
          barMaxWidth: 38,
          emphasis: { focus: 'series' }
        };
      }
      series.push(sr);
    }

    var showLegend = spec.legend !== false;
    return {
      color: theme.palette,
      grid: U.makeGrid(theme, { legend: showLegend }),
      legend: U.makeLegend(theme, state.legendSel, showLegend),
      toolbox: U.makeToolbox(theme),
      tooltip: (function () {
        var tip = U.tooltipBox(theme);
        tip.trigger = 'axis';
        tip.axisPointer = { type: isArea ? 'line' : 'shadow' };
        tip.formatter = function (params) { return pctTooltip(params, theme); };
        return tip;
      })(),
      xAxis: xAxis,
      yAxis: yAxis,
      series: series
    };
  }

  B['area_pct'] = function (spec, data, state, theme) {
    return buildPercentStack(spec, data, state, theme, true);
  };

  B['bar_pct'] = function (spec, data, state, theme) {
    return buildPercentStack(spec, data, state, theme, false);
  };
})();
