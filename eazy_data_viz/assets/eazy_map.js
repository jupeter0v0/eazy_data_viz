/*!
 * eazy_map.js —— 地图类图表运行时（geo_map / map_bubble / map_flow）
 * ------------------------------------------------------------------
 * 与 eazy.js / eazy_extra_*.js 同一套约定：
 *   - 由 render.py 在 eazy.js 之后加载；
 *   - 通过 EazyViz.extraBuilders['type'] 注册构建器；
 *   - 构建器签名 (spec, data, state, theme) -> ECharts option；
 *   - 聚合一律在前端完成（U.filteredRows + U.groupBy），所以联动过滤 /
 *     下钻之后地图会自动重算；
 *   - 地图 GeoJSON 由 render.py 注入 window.EAZY_MAPS = {"china": {...}, "world": {...}}，
 *     首次使用时 echarts.registerMap(name, geoJSON)。
 *
 * 名称匹配（重点）：
 *   数据里的区域列既可能是短名（广东 / 北京），也可能是全名（广东省 /
 *   北京市 / 广西壮族自治区 / 香港特别行政区），还可能带空格、点号。
 *   前端对「数据值」和「GeoJSON 里的区域名」两边都做 normalizeRegion()
 *   归一化后再比较；规则与 Python 侧 eazy_data_viz.maps.normalize_region()
 *   完全一致（见 SUFFIXES 常量）。
 *
 *   匹配成功后，地图区域的显示名会被改写成数据里的**原值**（nameMap），
 *   这样 ECharts 点击事件拿到的 p.name 就等于数据列原值，联动 / 下钻
 *   过滤（按列原值精确比较）才能生效。
 */
(function (global) {
  "use strict";

  var E = global.EazyViz;
  if (!E || !E.core) { return; }
  var U = E.core.util;
  var B = E.extraBuilders = E.extraBuilders || {};

  // ======================================================================
  // 0. 常量
  // ======================================================================
  // 中国行政区全名后缀，按「从长到短」匹配，循环剥离直到稳定。
  // 必须与 eazy_data_viz/maps.py 的 _ADMIN_SUFFIXES 保持一致。
  var SUFFIXES = [
    "特别行政区", "维吾尔自治区", "壮族自治区", "回族自治区", "自治区",
    "自治州", "自治县", "自治旗",
    "土家族", "苗族", "侗族", "瑶族", "彝族", "藏族", "羌族", "白族",
    "傣族", "哈尼族", "景颇族", "傈僳族", "拉祜族", "佤族", "纳西族",
    "朝鲜族", "满族", "水族", "仡佬族", "布依族", "黎族", "畲族",
    "仫佬族", "毛南族", "京族",
    "省", "市", "地区", "盟", "林区", "矿区",
    "维吾尔", "壮族", "回族", "蒙古族"
  ];

  // 名称里直接抹掉的空白 / 间隔符号（"W. Sahara" 之类）
  var SPACES = ["\u3000", " ", "\t", "\r", "\n", "·", "・", ".", "。", "—", "-"];

  // 世界地图：常见中文国名 -> GeoJSON 英文名（数据里写中文也能匹配上）
  var WORLD_ALIAS = {
    "美国": "United States", "中国": "China", "俄罗斯": "Russia",
    "英国": "United Kingdom", "法国": "France", "德国": "Germany",
    "日本": "Japan", "韩国": "Korea", "朝鲜": "Dem. Rep. Korea",
    "印度": "India", "巴西": "Brazil", "加拿大": "Canada",
    "澳大利亚": "Australia", "意大利": "Italy", "西班牙": "Spain",
    "墨西哥": "Mexico", "印度尼西亚": "Indonesia", "沙特阿拉伯": "Saudi Arabia",
    "土耳其": "Turkey", "南非": "South Africa", "埃及": "Egypt",
    "阿根廷": "Argentina", "智利": "Chile", "新西兰": "New Zealand",
    "泰国": "Thailand", "越南": "Vietnam", "马来西亚": "Malaysia",
    "菲律宾": "Philippines", "巴基斯坦": "Pakistan", "伊朗": "Iran",
    "伊拉克": "Iraq", "以色列": "Israel", "瑞典": "Sweden",
    "挪威": "Norway", "芬兰": "Finland", "丹麦": "Denmark",
    "荷兰": "Netherlands", "瑞士": "Switzerland", "奥地利": "Austria",
    "波兰": "Poland", "葡萄牙": "Portugal", "希腊": "Greece",
    "乌克兰": "Ukraine", "哈萨克斯坦": "Kazakhstan", "蒙古": "Mongolia",
    "缅甸": "Myanmar", "柬埔寨": "Cambodia", "老挝": "Laos",
    "尼泊尔": "Nepal", "孟加拉国": "Bangladesh", "斯里兰卡": "Sri Lanka",
    "阿联酋": "United Arab Emirates", "卡塔尔": "Qatar", "科威特": "Kuwait",
    "尼日利亚": "Nigeria", "肯尼亚": "Kenya", "埃塞俄比亚": "Ethiopia",
    "摩洛哥": "Morocco", "阿尔及利亚": "Algeria", "秘鲁": "Peru",
    "哥伦比亚": "Colombia", "委内瑞拉": "Venezuela", "古巴": "Cuba",
    "爱尔兰": "Ireland", "捷克": "Czech Rep.", "匈牙利": "Hungary",
    "罗马尼亚": "Romania", "保加利亚": "Bulgaria", "白俄罗斯": "Belarus",
    "乌兹别克斯坦": "Uzbekistan", "阿富汗": "Afghanistan", "叙利亚": "Syria",
    "约旦": "Jordan", "也门": "Yemen", "阿曼": "Oman",
    "加纳": "Ghana", "坦桑尼亚": "Tanzania", "安哥拉": "Angola",
    "莫桑比克": "Mozambique", "赞比亚": "Zambia", "津巴布韦": "Zimbabwe",
    "苏丹": "Sudan", "利比亚": "Libya", "突尼斯": "Tunisia",
    "塞内加尔": "Senegal", "马里": "Mali", "尼日尔": "Niger",
    "乍得": "Chad", "索马里": "Somalia", "马达加斯加": "Madagascar",
    "巴拿马": "Panama", "哥斯达黎加": "Costa Rica", "危地马拉": "Guatemala",
    "厄瓜多尔": "Ecuador", "玻利维亚": "Bolivia", "巴拉圭": "Paraguay",
    "乌拉圭": "Uruguay"
  };

  // 中国地图：少量常见简称 -> 全名（归一化本身已经能覆盖「广东/广东省」）
  var CHINA_ALIAS = {
    "内蒙": "内蒙古",
    "广西省": "广西",
    "新疆省": "新疆",
    "西藏省": "西藏",
    "宁夏省": "宁夏"
  };

  // 英文常见写法
  var WORLD_EN_ALIAS = {
    "usa": "United States",
    "u.s.a": "United States",
    "uk": "United Kingdom",
    "south korea": "Korea",
    "north korea": "Dem. Rep. Korea",
    "russian federation": "Russia",
    "korea, republic of": "Korea",
    "korea, dem. rep.": "Dem. Rep. Korea"
  };

  var REGISTERED = {};      // 已 registerMap 的地图名
  var MAP_CACHE = {};       // 地图名 -> {entries, byKey, byName}
  var WARNED = {};          // 一次性 console.warn 去重
  var CITY_CACHE = null;    // window.EAZY_CITIES 解析后的城市索引（懒加载）

  // ======================================================================
  // 1. 名称归一化
  // ======================================================================
  /**
   * 归一化区域名：去空格/间隔符，循环剥离行政区后缀。
   * 与 Python 侧 eazy_data_viz.maps.normalize_region 规则一致。
   */
  function normalizeRegion(name) {
    if (name === null || name === undefined) { return ""; }
    var s = String(name).replace(/^\s+|\s+$/g, "");
    var i, j;
    for (i = 0; i < SPACES.length; i++) {
      if (s.indexOf(SPACES[i]) >= 0) { s = s.split(SPACES[i]).join(""); }
    }
    var changed = true;
    var suffix;
    while (changed && s) {
      changed = false;
      for (j = 0; j < SUFFIXES.length; j++) {
        suffix = SUFFIXES[j];
        if (s.length > suffix.length && s.slice(s.length - suffix.length) === suffix) {
          s = s.slice(0, s.length - suffix.length);
          changed = true;
          break;
        }
      }
    }
    return s;
  }

  /** 别名：中文国名 -> 英文 GeoJSON 名（找不到返回 null）。 */
  function aliasOf(name) {
    var s = String(name === null || name === undefined ? "" : name);
    if (WORLD_ALIAS[s]) { return WORLD_ALIAS[s]; }
    var n = normalizeRegion(s);
    if (WORLD_ALIAS[n]) { return WORLD_ALIAS[n]; }
    if (CHINA_ALIAS[s]) { return CHINA_ALIAS[s]; }
    if (CHINA_ALIAS[n]) { return CHINA_ALIAS[n]; }
    var lower = s.toLowerCase();
    if (WORLD_EN_ALIAS[lower]) { return WORLD_EN_ALIAS[lower]; }
    return null;
  }

  /**
   * 匹配键：别名 + normalizeRegion + 小写。
   * 中文不受影响；英文「United States / united states」都能匹配。
   */
  function keyOf(name) {
    var s = String(name === null || name === undefined ? "" : name);
    var a = aliasOf(s);
    if (a !== null) { s = a; }
    return normalizeRegion(s).toLowerCase();
  }

  /**
   * 地图区域的显示短名：中文名剥离后缀（广东省 -> 广东），
   * 英文名保持原样（避免把 "W. Sahara" 变成 "WSahara"）。
   */
  function shortLabel(fullName) {
    var s = String(fullName === null || fullName === undefined ? "" : fullName);
    if (!/[\u4e00-\u9fa5]/.test(s)) { return s; }
    var n = normalizeRegion(s);
    return n || s;
  }

  // ======================================================================
  // 2. 地图数据：registerMap / 区域索引 / 中心点
  // ======================================================================
  function mapGeo(mapName) {
    var maps = global.EAZY_MAPS || {};
    return maps[mapName] || null;
  }

  /** 首次使用时注册地图，成功返回 true。 */
  function ensureMap(mapName) {
    if (REGISTERED[mapName]) { return true; }
    var geo = mapGeo(mapName);
    if (!geo || !geo.features) {
      warnOnce("miss-" + mapName,
        "没有找到地图数据 window.EAZY_MAPS['" + mapName + "']，请确认 render.py 已注入资产。");
      return false;
    }
    try {
      global.echarts.registerMap(mapName, geo);
    } catch (err) {
      warnOnce("reg-" + mapName, "registerMap('" + mapName + "') 失败：" + err);
      return false;
    }
    REGISTERED[mapName] = true;
    return true;
  }

  /** 构建名称索引（按归一化 key 查找）。 */
  function indexOf(mapName) {
    if (MAP_CACHE[mapName]) { return MAP_CACHE[mapName]; }
    var geo = mapGeo(mapName);
    var entries = [], byKey = {}, byName = {}, i, f, nm, key, entry;
    var features = (geo && geo.features) || [];
    for (i = 0; i < features.length; i++) {
      f = features[i];
      nm = f && f.properties ? f.properties.name : null;
      if (!nm) { continue; }  // 中国地图里空的「南海诸岛」占位 feature
      nm = String(nm);
      key = keyOf(nm);
      entry = { key: key, name: nm, feature: f, at: entries.length };
      entries.push(entry);
      if (!byKey[key]) { byKey[key] = entry; }
      byName[nm.toLowerCase()] = entry;
    }
    MAP_CACHE[mapName] = { mapName: mapName, entries: entries, byKey: byKey, byName: byName };
    return MAP_CACHE[mapName];
  }

  /**
   * 把数据里的区域值解析成地图区域（entry）。
   * 优先用户自定义 spec.nameMap（{"数据原值": "地图区域名"}）。
   */
  function resolveRegion(name, idx, spec) {
    if (name === null || name === undefined) { return null; }
    var raw = String(name);
    var map = spec && spec.nameMap;
    if (map && map.hasOwnProperty(raw)) {
      var target = String(map[raw]);
      var hit = idx.byName[target.toLowerCase()] || idx.byKey[keyOf(target)];
      if (hit) { return hit; }
      warnOnce("nm-" + target,
        "name_map 把「" + raw + "」映射到了「" + target + "」，但地图里没有这个区域，已忽略该映射。");
    }
    return idx.byKey[keyOf(raw)] || null;
  }

  // ----------------------------------------------------------------------
  // 2.1 城市级回退（window.EAZY_CITIES）
  //     城市没有独立 GeoJSON：气泡图 / 飞线图用城市真实坐标打点，
  //     区域填色图把城市值聚合到所属省份再上色。
  //     数据可能来自三个位置，老页面没有也不影响省级用法：
  //       window.EAZY_CITIES             （render.py 注入，推荐）
  //       EazyViz.page.cities            （页面配置里带）
  //       window.EAZY_MAPS.cities        （兜底）
  // ----------------------------------------------------------------------
  function citySource() {
    if (global.EAZY_CITIES) { return global.EAZY_CITIES; }
    if (E.page && E.page.cities) { return E.page.cities; }
    if (global.EAZY_MAPS && global.EAZY_MAPS.cities) { return global.EAZY_MAPS.cities; }
    return null;
  }

  /** {归一化城市名: {key,name,center,city:true,province}} */
  function cityIndexOf() {
    if (CITY_CACHE) { return CITY_CACHE; }
    var raw = citySource(), byKey = {}, count = 0, k, item, key, c, lng, lat;
    if (raw) {
      for (k in raw) {
        if (!raw.hasOwnProperty(k)) { continue; }
        item = raw[k] || {};
        key = keyOf(k);
        if (!key || byKey[key]) { continue; }
        c = item.c || item.center;
        if (!c || c.length < 2) { continue; }
        lng = Number(c[0]);
        lat = Number(c[1]);
        if (!isFinite(lng) || !isFinite(lat)) { continue; }
        byKey[key] = {
          key: key,
          name: String(k),
          center: [lng, lat],
          city: true,
          province: item.p ? String(item.p) : ""
        };
        count += 1;
      }
    }
    CITY_CACHE = { byKey: byKey, n: count, mapName: "china" };
    return CITY_CACHE;
  }

  /** 城市名 -> 伪区域 entry；未命中返回 null（支持「广州 / 广州市」两种写法）。 */
  function resolveCity(name) {
    if (name === null || name === undefined) { return null; }
    var idx = cityIndexOf();
    if (!idx.n) { return null; }
    return idx.byKey[keyOf(String(name))] || null;
  }

  /**
   * 区域解析：先查地图区域索引（省 / 国家），未命中再回退到城市表。
   * 返回的 entry.city === true 表示这是城市伪区域，调用方自行决定
   * 用中心点打点（气泡 / 飞线）还是聚合到省（区域填色）。
   */
  function resolveAny(name, idx, spec, allowCity) {
    if (name === null || name === undefined) { return null; }
    var raw = String(name);
    var map = spec && spec.nameMap;
    if (map && map.hasOwnProperty(raw)) {
      var target = String(map[raw]);
      var hit = idx.byName[target.toLowerCase()] || idx.byKey[keyOf(target)] || null;
      if (!hit && allowCity !== false) { hit = resolveCity(target); }
      if (hit) { return hit; }
      warnOnce("nm-" + target,
        "name_map 把「" + raw + "」映射到了「" + target + "」，但地图里没有这个区域，已忽略该映射。");
    }
    var entry = idx.byKey[keyOf(raw)] || null;
    if (entry) {
      if (allowCity !== false && idx.mapName === "china" &&
          /(市|地区|盟|自治州|自治县|旗)$/.test(raw)) {
        var cityFirst = resolveCity(raw);
        if (cityFirst) { return cityFirst; }
      }
      return entry;
    }
    if (allowCity !== false && idx.mapName === "china") { return resolveCity(raw); }
    return null;
  }

  /** 城市 -> 所属省级区域 entry（区域填色时把城市值聚合到省）。 */
  function provinceOfCity(city, idx) {
    if (!city || !city.province) { return null; }
    return idx.byKey[keyOf(city.province)] || null;
  }

  /** 区域中心点：城市伪区域用城市坐标，真实区域用 GeoJSON 中心/质心。 */
  function entryCenter(entry) {
    if (!entry) { return null; }
    if (entry.city) { return entry.center; }
    return centerOf(entry);
  }

  /**
   * 生成 ECharts 的 nameMap：{GeoJSON 原区域名: 新区域名}。
   * 有数据的区域 -> 数据原值（保证点击值 === 数据列原值）；
   * 无数据的区域 -> 中文短名 / 英文原名（显示更干净）。
   */
  function buildNameMap(idx, rawByKey) {
    var nm = {}, i, entry, raw;
    for (i = 0; i < idx.entries.length; i++) {
      entry = idx.entries[i];
      raw = rawByKey[entry.key];
      nm[entry.name] = (raw !== undefined && raw !== null) ? raw : shortLabel(entry.name);
    }
    return nm;
  }

  /** 取区域中心点：优先 GeoJSON properties 的中心/质心，否则所有顶点均值。 */
  function centerOf(entry) {
    var feature = entry.feature;
    if (feature.__eazyCenter) { return feature.__eazyCenter; }
    var props = feature.properties || {};
    var keys = ["cp", "center", "centroid"], i, point, lng, lat;
    for (i = 0; i < keys.length; i++) {
      point = props[keys[i]];
      if (point && point.length >= 2) {
        lng = Number(point[0]);
        lat = Number(point[1]);
        if (isFinite(lng) && isFinite(lat) && lng >= -180 && lng <= 180 && lat >= -90 && lat <= 90) {
          feature.__eazyCenter = [lng, lat];
          return feature.__eazyCenter;
        }
      }
    }
    var center = avgCoords(feature.geometry ? feature.geometry.coordinates : null);
    feature.__eazyCenter = center;
    return center;
  }

  /** 递归求坐标顶点均值（用显式栈，避免深层多边形递归爆栈）。 */
  function avgCoords(coords) {
    if (!coords) { return null; }
    var sx = 0, sy = 0, n = 0;
    var stack = [coords], cur, i, first;
    while (stack.length) {
      cur = stack.pop();
      if (!cur || !cur.length) { continue; }
      first = cur[0];
      if (typeof first === "number") {
        if (cur.length >= 2 && isFinite(cur[0]) && isFinite(cur[1])) {
          sx += Number(cur[0]);
          sy += Number(cur[1]);
          n += 1;
        }
      } else {
        for (i = 0; i < cur.length; i++) { stack.push(cur[i]); }
      }
    }
    if (!n) { return null; }
    return [sx / n, sy / n];
  }

  function regionCenterByName(mapName, name, spec) {
    var idx = indexOf(mapName);
    var entry = resolveAny(name, idx, spec);
    if (!entry) { return null; }
    return entryCenter(entry);
  }

  // ======================================================================
  // 3. 通用小工具
  // ======================================================================
  function warnOnce(key, msg) {
    if (WARNED[key]) { return; }
    WARNED[key] = 1;
    if (global.console && global.console.warn) {
      global.console.warn("[eazy_map] " + msg);
    }
  }

  function head(txt) {
    return '<div style="font-weight:600;margin-bottom:4px">' + U.esc(txt) + "</div>";
  }

  function row(k, v) {
    return '<div style="line-height:19px">' + U.esc(k) + "：<b>" + U.esc(v) + "</b></div>";
  }

  function pctText(v, total) {
    if (!total || !isFinite(v)) { return "-"; }
    return (v / total * 100).toFixed(1) + "%";
  }

  /** 区域填色 / 飞线共用的 5 档色阶（由主题主色向底色混出）。 */
  function heatColors(theme) {
    var p = theme.primary, bg = theme.surface;
    return [
      U.mixColor(p, bg, 0.94),
      U.mixColor(p, bg, 0.72),
      U.mixColor(p, bg, 0.48),
      U.mixColor(p, bg, 0.24),
      p
    ];
  }

  /** 飞线色阶：低值偏底色的主色，高值偏向更「热」的一端。 */
  function flowColors(theme) {
    var p = theme.primary, bg = theme.surface;
    if (theme.name === "dark") {
      return [
        U.mixColor(p, bg, 0.55),
        U.mixColor(p, bg, 0.25),
        p,
        U.mixColor(p, "#ffffff", 0.28),
        U.mixColor(p, "#ffffff", 0.5)
      ];
    }
    return [
      U.mixColor(p, bg, 0.55),
      U.mixColor(p, bg, 0.25),
      p,
      U.mixColor(p, "#000000", 0.22),
      U.mixColor(p, "#000000", 0.4)
    ];
  }

  function paletteColor(theme, i) {
    var pal = theme.palette || [];
    if (!pal.length) { return theme.primary; }
    return pal[i % pal.length];
  }

  /** 线性映射（数组下标做颜色 / 线宽时用）。 */
  function scaleLinear(v, lo, hi, outLo, outHi) {
    if (!isFinite(v) || !isFinite(lo) || !isFinite(hi) || hi === lo) {
      return (outLo + outHi) / 2;
    }
    var t = (v - lo) / (hi - lo);
    if (t < 0) { t = 0; }
    if (t > 1) { t = 1; }
    return outLo + (outHi - outLo) * t;
  }

  /** 气泡半径：sqrt 缩放（面积感知更均匀）。 */
  function bubbleRadius(v, lo, hi, minSize, maxSize) {
    if (!isFinite(v) || !isFinite(lo) || !isFinite(hi) || hi === lo) {
      return Math.round((minSize + maxSize) / 2);
    }
    var t = (v - lo) / (hi - lo);
    if (t < 0) { t = 0; }
    if (t > 1) { t = 1; }
    return Math.round(minSize + (maxSize - minSize) * Math.sqrt(t));
  }

  /** 多个聚合结果落到同一区域时合并（例如「广东」和「广东省」同时出现）。 */
  function mergeValue(cell, value, cnt, how) {
    if (value === null || value === undefined || !isFinite(value)) { return cell; }
    if (cell.value === null) {
      cell.value = value;
      cell.cnt = cnt || 1;
      return cell;
    }
    if (how === "sum" || how === "count") {
      cell.value += value;
      cell.cnt += (cnt || 1);
    } else if (how === "max") {
      if (value > cell.value) { cell.value = value; }
    } else if (how === "min") {
      if (value < cell.value) { cell.value = value; }
    } else if (how === "mean") {
      var total = cell.cnt + (cnt || 1);
      cell.value = total ? (cell.value * cell.cnt + value * (cnt || 1)) / total : value;
      cell.cnt = total;
    }
    // median：无法增量合并，保留第一个值（同一区域出现多种写法时只提示一次）
    return cell;
  }

  /** 地图还没注册 / 资产缺失时的兜底 option。 */
  function missMapOption(theme, mapName) {
    return {
      backgroundColor: "transparent",
      graphic: {
        type: "text", left: "center", top: "middle",
        style: {
          text: "未加载地图：" + mapName + "（请检查 window.EAZY_MAPS）",
          fill: theme.subtext, fontSize: 13, font: U.FONT
        }
      },
      xAxis: { show: false },
      yAxis: { show: false },
      series: []
    };
  }

  /**
   * 地图初始视角：内置地图的包围盒包含了南海诸岛插图 / 南极等边缘区域，
   * ECharts 默认整包适配后主体会偏小，这里给一个更「满」的初始 zoom / center。
   * 用户如果通过 spec.mapZoom / spec.mapCenter 指定则优先用用户的。
   */
  var DEFAULT_VIEW = {
    china: { zoom: 1.32, center: [104, 35.5] },
    world: { zoom: 1.12, center: null }
  };

  function initialView(spec, mapName) {
    var view = DEFAULT_VIEW[mapName] || DEFAULT_VIEW.china;
    var out = {};
    if (view.zoom) { out.zoom = view.zoom; }
    if (view.center) { out.center = view.center.slice(); }
    if (spec && spec.mapZoom !== undefined && spec.mapZoom !== null) {
      out.zoom = Number(spec.mapZoom);
    }
    if (spec && spec.mapCenter) { out.center = spec.mapCenter; }
    return out;
  }

  /** geo 组件基础配置（气泡图 / 飞线图共用）。 */
  function geoBase(spec, theme, mapName, nameMap) {
    var view = initialView(spec, mapName);
    var geo = {
      map: mapName,
      roam: spec.zoom === false ? false : true,
      scaleLimit: { min: 0.7, max: 12 },
      nameMap: nameMap,
      label: { show: false, color: theme.text, fontSize: 10 },
      itemStyle: {
        areaColor: theme.surfaceVar,
        borderColor: theme.outline,
        borderWidth: 0.6
      },
      emphasis: {
        label: { show: true, color: theme.text, fontSize: 10 },
        itemStyle: {
          areaColor: U.mixColor(theme.surfaceVar, theme.primary, 0.18),
          borderColor: theme.outline
        }
      },
      select: { disabled: true },
      zlevel: 0
    };
    if (view.zoom) { geo.zoom = view.zoom; }
    if (view.center) { geo.center = view.center; }
    return geo;
  }

  /** 计算一组数值的 [min, max]（忽略 null/NaN）。 */
  function extentOf(values) {
    var lo = Infinity, hi = -Infinity, i, v;
    for (i = 0; i < values.length; i++) {
      v = values[i];
      if (v === null || v === undefined || !isFinite(v)) { continue; }
      if (v < lo) { lo = v; }
      if (v > hi) { hi = v; }
    }
    return [lo, hi];
  }

  // ======================================================================
  // 4. geo_map —— 区域填色
  // ======================================================================
  B.geo_map = function (spec, data, state, theme) {
    var roles = spec.roles || {};
    var mapName = spec.map || "china";
    if (!ensureMap(mapName)) { return missMapOption(theme, mapName); }
    var idx = indexOf(mapName);
    var rows = U.filteredRows(spec, data, state);
    var dim = roles.region || U.currentXDim(spec, state);
    if (!dim || !rows.length) { return U.emptyOption(theme); }

    var how = spec.agg || "sum";
    var measure = roles.value || null;
    if (!measure) { how = "count"; }
    var groups = U.groupBy(rows, [dim], measure, how);

    var cells = [], byKey = {}, unmatched = [], i, g, entry, cell, v, fromCity, cityKey, province;
    for (i = 0; i < groups.length; i++) {
      g = groups[i];
      entry = resolveAny(g.keys[0], idx, spec);
      if (!entry) { unmatched.push(g.keys[0]); continue; }
      fromCity = false;
      cityKey = null;
      if (entry.city) {
        // 城市没有独立的填色区域：把城市值聚合到所属省份再上色。
        cityKey = entry.key;
        province = provinceOfCity(entry, idx);
        if (!province) { unmatched.push(g.keys[0]); continue; }
        entry = province;
        fromCity = true;
      }
      v = g.value;
      if (v === null || v === undefined) { continue; }
      v = Number(v);
      if (!isFinite(v)) { continue; }
      cell = byKey[entry.key];
      if (!cell) {
        cell = {
          entry: entry,
          raw: fromCity ? shortLabel(entry.name) : g.keys[0],
          value: null,
          cnt: 0,
          cityKeys: {}
        };
        byKey[entry.key] = cell;
        cells.push(cell);
      }
      // 同一个省可能来自多个城市（也兼容「广州 / 广州市」这类同城写法），
      // 用去重后的城市数提示「覆盖城市」。
      if (fromCity) { cell.cityKeys[cityKey] = 1; }
      mergeValue(cell, v, g.cnt, how);
    }
    if (!cells.length) { return U.emptyOption(theme); }
    if (unmatched.length) {
      warnOnce("geo-unmatched-" + mapName,
        "以下区域没有匹配到地图（已跳过）：" + unmatched.slice(0, 8).join("、") +
        (unmatched.length > 8 ? " 等 " + unmatched.length + " 个" : "") +
        "。可统一改名，或用 name_map 指定映射" +
        (mapName === "china" ? "；城市名需在内置城市表（window.EAZY_CITIES）里。" : "。"));
    }

    var items = [], rawByKey = {}, total = 0, values = [], cityN, k;
    for (i = 0; i < cells.length; i++) {
      cell = cells[i];
      rawByKey[cell.entry.key] = cell.raw;
      cityN = 0;
      for (k in cell.cityKeys) {
        if (cell.cityKeys.hasOwnProperty(k)) { cityN += 1; }
      }
      items.push({ name: cell.raw, value: cell.value, cities: cityN });
      values.push(cell.value);
      total += cell.value;
    }
    var ext = extentOf(values);
    var low = (spec.minValue === null || spec.minValue === undefined) ? ext[0] : Number(spec.minValue);
    var high = (spec.maxValue === null || spec.maxValue === undefined) ? ext[1] : Number(spec.maxValue);
    if (!isFinite(low) || !isFinite(high)) { return U.emptyOption(theme); }
    if (!(high > low)) { high = low + 1; }

    var nameMap = buildNameMap(idx, rawByKey);
    var view = initialView(spec, mapName);
    // 区域特别多时（世界地图 200+）只显示有数据的标签，否则标签会糊成一片
    var allLabels = idx.entries.length <= 60;
    var measureLabel = measure || "记录数";
    var tip = U.tooltipBox(theme);
    tip.trigger = "item";
    tip.formatter = function (p) {
      var name = p && p.name ? String(p.name) : "";
      if (!name) { return ""; }
      var d = p.data, n = d ? U.num(d.value) : null;
      var html = head(name) + row(measureLabel, n === null ? "无数据" : U.fmtValue(n, spec.fmt));
      if (n !== null) { html += row("占比", pctText(n, total)); }
      // 城市数据聚合到省时，提示这个省由多少个城市汇总而来
      if (d && Number(d.cities) > 1) { html += row("覆盖城市", Number(d.cities) + " 个"); }
      return html;
    };

    var opt = {
      tooltip: tip,
      toolbox: U.makeToolbox(theme),
      visualMap: {
        type: "continuous",
        show: spec.legend !== false,
        min: low,
        max: high,
        calculable: false,
        orient: "vertical",
        right: 8,
        top: "middle",
        itemWidth: 10,
        itemHeight: 90,
        itemGap: 8,
        text: [U.fmtValue(high, spec.fmt), U.fmtValue(low, spec.fmt)],
        textStyle: { color: theme.subtext, fontSize: 11 },
        formatter: function (val) { return U.fmtValue(val, spec.fmt); },
        inRange: { color: heatColors(theme) }
      },
      series: [{
        type: "map",
        name: measureLabel,
        map: mapName,
        nameMap: nameMap,
        roam: spec.zoom === false ? false : true,
        zoom: view.zoom,
        center: view.center,
        scaleLimit: { min: 0.7, max: 12 },
        selectedMode: false,
        label: {
          show: spec.labels !== false,
          formatter: function (p) {
            if (!allLabels) {
              var d = p && p.data;
              if (!d || d.value === null || d.value === undefined) { return ""; }
            }
            return p && p.name ? p.name : "";
          },
          color: theme.text,
          fontSize: 10,
          textBorderColor: theme.surface,
          textBorderWidth: 2
        },
        itemStyle: {
          areaColor: theme.surfaceVar,
          borderColor: theme.outline,
          borderWidth: 0.6
        },
        emphasis: {
          label: { show: true, color: theme.text, fontSize: 11, fontWeight: "bold" },
          itemStyle: {
            areaColor: theme.primary,
            borderColor: theme.outline,
            shadowBlur: 8,
            shadowColor: "rgba(0,0,0,.18)"
          }
        },
        select: { disabled: true },
        data: items
      }]
    };
    return opt;
  };

  // ======================================================================
  // 5. map_bubble —— 气泡地图
  // ======================================================================
  B.map_bubble = function (spec, data, state, theme) {
    var roles = spec.roles || {};
    var mapName = spec.map || "china";
    if (!ensureMap(mapName)) { return missMapOption(theme, mapName); }
    var idx = indexOf(mapName);
    var rows = U.filteredRows(spec, data, state);
    var dim = roles.region || U.currentXDim(spec, state);
    if (!dim || !rows.length) { return U.emptyOption(theme); }

    var how = spec.agg || "sum";
    var vcol = roles.value || null;
    var scol = roles.size || null;
    var ccol = roles.color || null;
    if (!vcol && !scol) { how = "count"; }
    var dims = ccol ? [dim, ccol] : [dim];

    var gv = U.groupBy(rows, dims, vcol, vcol ? how : (scol ? how : "count"));
    var sizeMap = null, i, g, entry, cell;
    if (scol) {
      var gs = (scol === vcol) ? gv : U.groupBy(rows, dims, scol, how);
      sizeMap = {};
      for (i = 0; i < gs.length; i++) { sizeMap[gs[i].key] = gs[i].value; }
    }

    var cells = [], unmatched = [], cellIndex = {};
    var groups = [], groupMap = {}, groupName;
    for (i = 0; i < gv.length; i++) {
      g = gv[i];
      entry = resolveAny(g.keys[0], idx, spec);
      if (!entry) { unmatched.push(g.keys[0]); continue; }
      var val = g.value;
      if (val === null || val === undefined || !isFinite(Number(val))) { continue; }
      val = Number(val);
      groupName = ccol ? (g.keys[1] === undefined ? "(空)" : g.keys[1]) : null;
      var ckey = entry.key + "|" + (groupName === null ? "" : groupName);
      var sizeVal = sizeMap ? sizeMap[g.key] : val;
      sizeVal = U.num(sizeVal);
      if (sizeVal === null) { sizeVal = val; }
      cell = cellIndex[ckey];
      if (!cell) {
        cell = {
          entry: entry,
          raw: g.keys[0],
          group: groupName,
          value: null,
          cnt: 0,
          size: null,
          scnt: 0,
          merged: 0,
          province: entry.city ? entry.province : null
        };
        cellIndex[ckey] = cell;
        cells.push(cell);
        if (groupName !== null && !groupMap[groupName]) {
          groupMap[groupName] = { name: groupName, total: 0 };
          groups.push(groupMap[groupName]);
        }
      } else {
        // 同一地图区域有多种写法（广东 / 广东省、广州 / 广州市）时按 agg 合并，
        // 避免后出现的写法被静默丢弃。
        cell.merged += 1;
      }
      mergeValue(cell, val, g.cnt, how);
      var sizeTmp = { value: cell.size, cnt: cell.scnt };
      mergeValue(sizeTmp, sizeVal, g.cnt, how);
      cell.size = sizeTmp.value;
      cell.scnt = sizeTmp.cnt;
    }
    if (!cells.length) { return U.emptyOption(theme); }
    if (unmatched.length) {
      warnOnce("bubble-unmatched-" + mapName,
        "以下区域没有匹配到地图（已跳过）：" + unmatched.slice(0, 8).join("、") +
        (unmatched.length > 8 ? " 等 " + unmatched.length + " 个" : "") +
        "。可统一改名、用 name_map 指定映射" +
        (mapName === "china" ? "，或检查城市名是否在内置城市表里。" : "。"));
    }

    var sizes = [], values = [], total = 0;
    for (i = 0; i < cells.length; i++) {
      sizes.push(cells[i].size);
      values.push(cells[i].value);
      total += cells[i].value;
      if (cells[i].group !== null) { groupMap[cells[i].group].total += cells[i].value; }
    }
    var ext = extentOf(values);
    var sizeExt = extentOf(sizes);
    var minSize = U.num(spec.minSize);
    var maxSize = U.num(spec.maxSize);
    if (minSize === null) { minSize = 4; }
    if (maxSize === null) { maxSize = 28; }
    if (maxSize <= minSize) { maxSize = minSize + 1; }

    groups.sort(function (a, b) { return b.total - a.total; });
    var groupIndex = {}, gi;
    for (i = 0; i < groups.length; i++) {
      groupIndex[groups[i].name] = i;
      groups[i].color = paletteColor(theme, i);
    }

    var seriesData = {}, seriesList = [], seriesByGroup = {};
    function seriesOf(gname) {
      if (seriesByGroup[gname]) { return seriesByGroup[gname]; }
      var color = gname === null ? theme.primary : paletteColor(theme, groupIndex[gname] || 0);
      var series = {
        type: "scatter",
        name: gname === null ? (vcol || "记录数") : gname,
        coordinateSystem: "geo",
        geoIndex: 0,
        symbol: "circle",
        large: false,
        label: {
          show: !!spec.labels,
          position: "right",
          formatter: function (p) { return U.truncate(p.name, 10); },
          color: theme.text,
          fontSize: 10
        },
        itemStyle: { color: color, opacity: 0.85, borderColor: theme.surface, borderWidth: 1 },
        emphasis: {
          scale: 1.15,
          label: { show: true },
          itemStyle: { opacity: 1 }
        },
        data: []
      };
      seriesByGroup[gname] = series;
      seriesList.push(series);
      return series;
    }

    var nameMap = {}, rawByKey = {};
    for (i = 0; i < cells.length; i++) {
      cell = cells[i];
      var center = cell.entry.city ? cell.entry.center : centerOf(cell.entry);
      if (!center) { continue; }
      rawByKey[cell.entry.key] = cell.raw;
      var radius = bubbleRadius(cell.size, sizeExt[0], sizeExt[1], minSize, maxSize);
      var lng = center[0], lat = center[1];
      // 同一区域有多个分组（color 列）时，把气泡在中心点周围散开一点，
      // 否则几个气泡会完全叠在一起、互相遮挡。
      if (ccol && groups.length > 1) {
        var gidx = groupIndex[cell.group] || 0;
        var ang = -Math.PI / 2 + (2 * Math.PI * gidx) / groups.length;
        var dist = (mapName === "world" ? 4.0 : 1.2) + radius / 30;
        lng += (Math.cos(ang) * dist) / Math.max(0.4, Math.cos(lat * Math.PI / 180));
        lat += Math.sin(ang) * dist;
      }
      var gkey = cell.group === null ? null : cell.group;
      var ser = seriesOf(gkey);
      ser.data.push({
        name: cell.raw,
        value: [lng, lat, cell.size, cell.value],
        symbolSize: radius,
        group: gkey,
        prov: cell.province || null
      });
      seriesData[cell.entry.key] = 1;
    }
    if (!seriesList.length) { return U.emptyOption(theme); }
    nameMap = buildNameMap(idx, rawByKey);

    var measureLabel = vcol || "记录数";
    var sizeLabel = scol || measureLabel;
    var tip = U.tooltipBox(theme);
    tip.trigger = "item";
    tip.formatter = function (p) {
      var d = p && p.data ? p.data : {};
      var name = p && p.name ? String(p.name) : "";
      var html = head(name);
      var valueNum = (d.value && d.value.length >= 4) ? U.num(d.value[3]) : null;
      var sizeNum = (d.value && d.value.length >= 4) ? U.num(d.value[2]) : null;
      if (valueNum !== null) { html += row(measureLabel, U.fmtValue(valueNum, spec.fmt)); }
      if (scol && sizeNum !== null) { html += row(sizeLabel, U.fmtValue(sizeNum, spec.fmt)); }
      if (d.group !== null && d.group !== undefined) { html += row(roles.color || "分组", d.group); }
      if (d.prov) { html += row("所属省份", d.prov); }
      if (valueNum !== null) { html += row("占比", pctText(valueNum, total)); }
      return html;
    };

    var legend = { show: false };
    if (ccol && spec.legend !== false && groups.length > 1) {
      legend = U.makeLegend(theme, state.legendSel, true);
      legend.data = (function () {
        var arr = [], k;
        for (k = 0; k < groups.length; k++) { arr.push(groups[k].name); }
        return arr;
      })();
    }

    var opt = {
      tooltip: tip,
      toolbox: U.makeToolbox(theme),
      legend: legend,
      geo: geoBase(spec, theme, mapName, nameMap),
      series: seriesList
    };
    return opt;
  };

  // ======================================================================
  // 6. map_flow —— 飞线地图
  // ======================================================================
  B.map_flow = function (spec, data, state, theme) {
    var roles = spec.roles || {};
    var mapName = spec.map || "china";
    if (!ensureMap(mapName)) { return missMapOption(theme, mapName); }
    var idx = indexOf(mapName);
    var rows = U.filteredRows(spec, data, state);
    var src = roles.source;
    var tgt = roles.target;
    if (!src || !tgt || !rows.length) { return U.emptyOption(theme); }

    var how = spec.agg || "sum";
    var measure = roles.value || null;
    if (!measure) { how = "count"; }
    var groups = U.groupBy(rows, [src, tgt], measure, how);
    var flows = [], unmatched = [], total = 0, values = [], absMax = 0, i, g, se, te, v, sc, tc;
    for (i = 0; i < groups.length; i++) {
      g = groups[i];
      se = resolveAny(g.keys[0], idx, spec);
      te = resolveAny(g.keys[1], idx, spec);
      if (!se) { unmatched.push(g.keys[0]); }
      if (!te) { unmatched.push(g.keys[1]); }
      if (!se || !te || se.key === te.key) { continue; }
      v = g.value;
      if (v === null || v === undefined) { continue; }
      v = Number(v);
      if (!isFinite(v)) { continue; }
      sc = entryCenter(se);
      tc = entryCenter(te);
      if (!sc || !tc) { continue; }
      flows.push({
        source: g.keys[0],
        target: g.keys[1],
        from: sc,
        to: tc,
        value: v,
        cnt: g.cnt,
        fromProvince: se.city ? se.province : null,
        toProvince: te.city ? te.province : null
      });
      values.push(v);
      total += v;
      if (Math.abs(v) > absMax) { absMax = Math.abs(v); }
    }
    if (!flows.length) { return U.emptyOption(theme); }
    if (unmatched.length) {
      warnOnce("flow-unmatched-" + mapName,
        "以下区域没有匹配到地图（对应的飞线已跳过）：" + unmatched.slice(0, 8).join("、") +
        (unmatched.length > 8 ? " 等 " + unmatched.length + " 个" : "") +
        "。可统一改名、用 name_map 指定映射" +
        (mapName === "china" ? "，或检查城市名是否在内置城市表里。" : "。"));
    }

    var ext = extentOf(values);
    var low = ext[0], high = ext[1];
    if (!isFinite(low) || !isFinite(high)) { return U.emptyOption(theme); }
    if (!(high > low)) { high = low + 1; }

    var nameMapForAll = buildNameMap(idx, {});
    var measureLabel = measure || "流量";
    var items = [];
    for (i = 0; i < flows.length; i++) {
      var f = flows[i];
      var width = 1 + 2 * (absMax ? Math.abs(f.value) / absMax : 0.5);
      items.push({
        // name 用起点区域原值：点击飞线 -> 联动过滤「起点」维度，行为可预期
        name: f.source,
        sourceName: f.source,
        targetName: f.target,
        value: f.value,
        coords: [f.from, f.to],
        fromProvince: f.fromProvince,
        toProvince: f.toProvince,
        lineStyle: { width: Math.round(width * 10) / 10 }
      });
    }

    var tip = U.tooltipBox(theme);
    tip.trigger = "item";
    tip.formatter = function (p) {
      var d = p && p.data ? p.data : {};
      if (!d.sourceName || !d.targetName) { return ""; }
      var n = U.num(d.value);
      var html = head(d.sourceName + " → " + d.targetName);
      html += row(measureLabel, n === null ? "-" : U.fmtValue(n, spec.fmt));
      if (d.fromProvince) { html += row("起点省份", d.fromProvince); }
      if (d.toProvince) { html += row("终点省份", d.toProvince); }
      if (n !== null) { html += row("占比", pctText(n, total)); }
      return html;
    };

    var opt = {
      tooltip: tip,
      toolbox: U.makeToolbox(theme),
      geo: geoBase(spec, theme, mapName, nameMapForAll),
      visualMap: {
        type: "continuous",
        show: spec.legend !== false,
        min: low,
        max: high,
        calculable: false,
        orient: "vertical",
        right: 8,
        top: "middle",
        itemWidth: 10,
        itemHeight: 90,
        itemGap: 8,
        text: [U.fmtValue(high, spec.fmt), U.fmtValue(low, spec.fmt)],
        textStyle: { color: theme.subtext, fontSize: 11 },
        formatter: function (val) { return U.fmtValue(val, spec.fmt); },
        inRange: { color: flowColors(theme) }
      },
      series: [{
        type: "lines",
        name: measureLabel,
        coordinateSystem: "geo",
        geoIndex: 0,
        zlevel: 2,
        symbol: "none",
        symbolSize: 0,
        effect: {
          show: true,
          period: 5,
          trailLength: 0.35,
          symbol: "arrow",
          symbolSize: 5,
          color: theme.primary
        },
        lineStyle: { curveness: 0.25, opacity: 0.55, width: 1 },
        emphasis: { lineStyle: { opacity: 0.95, width: 3 } },
        progressive: 0,
        data: items
      }]
    };
    return opt;
  };

  // ======================================================================
  // 7. 调试 / 工具接口（供控制台与文档示例使用，非图表契约）
  // ======================================================================
  E.mapUtil = {
    normalizeRegion: normalizeRegion,
    shortLabel: shortLabel,
    keyOf: keyOf,
    /** 地图区域全名列表（例如检查地图里到底有哪些名字）。 */
    regions: function (mapName) {
      var idx = indexOf(mapName || "china");
      var arr = [], i;
      for (i = 0; i < idx.entries.length; i++) { arr.push(idx.entries[i].name); }
      return arr;
    },
    /** {区域全名: [经度, 纬度]} */
    centers: function (mapName) {
      var idx = indexOf(mapName || "china");
      var out = {}, c, i;
      for (i = 0; i < idx.entries.length; i++) {
        c = centerOf(idx.entries[i]);
        if (c) { out[idx.entries[i].name] = c; }
      }
      return out;
    },
    /** {短名: [经度, 纬度]}（中国地图常用） */
    provinceCenters: function () {
      var idx = indexOf("china");
      var out = {}, c, i;
      for (i = 0; i < idx.entries.length; i++) {
        c = centerOf(idx.entries[i]);
        if (c) { out[shortLabel(idx.entries[i].name)] = c; }
      }
      return out;
    },
    /** {城市名: [经度, 纬度]}（依赖 window.EAZY_CITIES；没有城市表时返回空对象） */
    cities: function () {
      var idx = cityIndexOf(), out = {}, k;
      for (k in idx.byKey) {
        if (idx.byKey.hasOwnProperty(k)) { out[idx.byKey[k].name] = idx.byKey[k].center; }
      }
      return out;
    },
    /** 城市总数（没有城市表时为 0） */
    cityCount: function () { return cityIndexOf().n; },
    resolveCity: resolveCity,
    ensureMap: ensureMap,
    indexOf: indexOf
  };
})(window);
