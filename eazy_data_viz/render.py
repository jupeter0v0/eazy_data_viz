"""HTML 渲染层：把若干 Chart 组装成一个自包含页面 / Streamlit 组件。

关键设计（也是和 ``streamlit-echarts`` 等现成组件最大的区别）：

* 所有页面元素（ECharts、交互运行时、图数据）都内联进 **同一个 HTML 文档**，
  因此多图联动不依赖 iframe 之间通信 —— Streamlit 的 ``components.html``
  每次调用就是一个独立 iframe，跨 iframe 共享 JS 状态是不可能的；
* 页面本身不依赖 CDN，离线可用（ECharts 5.5.1 已随库一起分发）；
* 视觉遵循 Google Material Design 3：Roboto 字体、12px 卡片圆角、
  #1a73e8 主色、AppBar / chips / 分层阴影。
"""
from __future__ import annotations

import html as _html
import io
import json
import os
import shutil
import sys

from . import frame as _frame
from . import palette as _palette

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
ECHARTS_JS = "echarts.min.js"
RUNTIME_JS = "eazy.js"
# 扩展图表运行时（按顺序加载：主控 → A 组 → B 组 → HTML 类）
EXTRA_JS = (
    "eazy_extra_main.js",
    "eazy_map.js",
    "eazy_extra_a.js",
    "eazy_extra_b.js",
    "eazy_extra_html.js",
)
ALL_JS = (ECHARTS_JS, RUNTIME_JS) + EXTRA_JS

# HTML 类（不用 ECharts）图表：高度规则不同，容器不带 toolbar
HTML_TYPES = ("kpi", "group_kpi", "progress", "tile", "table", "wordcloud")

_asset_cache = {}


# --------------------------------------------------------------------------
# 运行环境探测
# --------------------------------------------------------------------------
def is_streamlit():
    """当前是否跑在 Streamlit 的脚本上下文里。"""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        if get_script_run_ctx() is not None:
            return True
    except Exception:
        pass
    try:
        import streamlit as st  # noqa: F401

        # 老版本（<1.12）没有 get_script_run_ctx 的兼容路径
        from streamlit.script_run_context import get_script_run_ctx as _old  # type: ignore

        return _old() is not None
    except Exception:
        return False


def in_notebook():
    """当前是否在 Jupyter / IPython Notebook 里。"""
    try:
        from IPython import get_ipython

        ip = get_ipython()
        if ip is None:
            return False
        name = ip.__class__.__name__
        return name in ("ZMQInteractiveShell", "Shell") and bool(getattr(ip, "kernel", None))
    except Exception:
        return False


# --------------------------------------------------------------------------
# 资源
# --------------------------------------------------------------------------
def _read_asset(name):
    if name not in _asset_cache:
        path = os.path.join(ASSETS_DIR, name)
        if not os.path.isfile(path):
            # 扩展文件允许缺失（例如裁剪发行版），不要因此炸掉整个页面
            _asset_cache[name] = "/* eazy_data_viz: %s 未安装 */" % name
        else:
            with open(path, "r", encoding="utf-8") as f:
                _asset_cache[name] = f.read()
    return _asset_cache[name]


MAPS_DIR = os.path.join(ASSETS_DIR, "maps")
_MAP_CACHE = {}


def _read_map(name):
    """读取内置 GeoJSON 地图（china / world），带缓存。"""
    name = str(name or "china").strip().lower()
    if name in _MAP_CACHE:
        return _MAP_CACHE[name]
    path = os.path.join(MAPS_DIR, name + ".json")
    if not os.path.isfile(path):
        raise ValueError(
            "未知地图 %r；当前只内置 china（中国）与 world（世界）。" % name)
    with io.open(path, encoding="utf-8") as f:
        geo = json.load(f)
    _MAP_CACHE[name] = geo
    return geo


def _map_payload(specs):
    """收集页面里用到哪些地图，返回 {name: geojson}。"""
    used, out = [], {}
    for s in specs or []:
        name = s.get("map")
        if name and name not in used:
            used.append(name)
    for name in used:
        try:
            out[str(name)] = _read_map(name)
        except (ValueError, OSError):
            continue
    return out


_CITIES_CACHE = {}


def _cities_payload():
    """读取内置城市坐标表（china_cities.json），供气泡/飞线地图按城市落点。"""
    if "cities" in _CITIES_CACHE:
        return _CITIES_CACHE["cities"]
    path = os.path.join(MAPS_DIR, "china_cities.json")
    try:
        with io.open(path, encoding="utf-8") as f:
            cities = json.load(f)
    except (IOError, OSError, ValueError):
        cities = {}
    _CITIES_CACHE["cities"] = cities
    return cities


def _script_tags(inline, prefix="eazy_assets"):
    if inline:
        return "\n".join("<script>%s</script>" % _read_asset(n) for n in ALL_JS)
    return "\n".join(
        '<script src="%s/%s"></script>' % (prefix, n) for n in ALL_JS
    )


# --------------------------------------------------------------------------
# 高度估算（Streamlit iframe 需要精确高度，否则会出现滚动条）
# --------------------------------------------------------------------------
def _card_height(spec):
    kind = spec.get("type")
    head = 46 if (spec.get("title") or spec.get("subtitle")) else 8
    toolbar = 30 if (spec.get("drill") or spec.get("link")) else 0
    base = spec.get("height")
    if kind == "kpi":
        return int(base or 150) + 24
    if kind == "group_kpi":
        n = max(1, len(spec.get("items") or [1]))
        per_row = 4
        rows = (n + per_row - 1) // per_row
        return 30 + 62 * rows + 10 * (rows - 1) + 10
    if kind == "table":
        return int(base or 320) + head + 10
    if kind in ("progress", "wordcloud", "tile"):
        return int(base or 320) + head + 10
    if kind in ("geo_map", "map_bubble", "map_flow"):
        return int(base or 460) + head + toolbar + 14
    return int(base or 380) + head + toolbar + 14


def page_height(charts, cols=None, has_header=False, has_filters=False):
    """估算页面总高度，供 ``st.components.v1.html`` 使用。"""
    specs = [c.spec for c in charts]
    n = len(specs)
    if n == 0:
        return 200
    cols = cols or (1 if n == 1 else 2)
    rows = [specs[i: i + cols] for i in range(0, n, cols)]
    total = sum(max(_card_height(s) for s in row) for row in rows)
    total += 16 * max(0, len(rows) - 1)  # grid gap
    total += 40  # body padding
    if has_header:
        total += 60
    if has_filters:
        total += 46
    return int(total)


# --------------------------------------------------------------------------
# Material Design 3 样式
# --------------------------------------------------------------------------
_CSS = """
:root{
  --pv-primary:#1a73e8;--pv-primary-dark:#185abc;--pv-on-primary:#ffffff;
  --pv-surface:#ffffff;--pv-surface-1:#ffffff;--pv-surface-2:#f8f9fa;
  --pv-surface-3:#f1f3f4;--pv-on-surface:#202124;--pv-on-surface-var:#5f6368;
  --pv-outline:#dadce0;--pv-outline-var:#e8eaed;--pv-error:#d93025;--pv-success:#188038;
  --pv-scrim:rgba(32,33,36,.14);
}
html[data-theme=dark],body[data-theme=dark]{
  --pv-surface:#1e1f20;--pv-surface-1:#1e1f20;--pv-surface-2:#131314;
  --pv-surface-3:#2d2e30;--pv-on-surface:#e3e3e3;--pv-on-surface-var:#9aa0a6;
  --pv-outline:#444746;--pv-outline-var:#2d2e30;--pv-error:#f28b82;--pv-success:#81c995;
  --pv-primary:#8ab4f8;--pv-on-primary:#202124;--pv-scrim:rgba(0,0,0,.32);
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  font-family:Roboto,"Google Sans","Helvetica Neue",Arial,"Segoe UI",
    "Microsoft YaHei","PingFang SC","Hiragino Sans GB",sans-serif;
  font-size:14px;line-height:1.5;letter-spacing:.01em;
  background:var(--pv-surface-2);color:var(--pv-on-surface);
  -webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;
}
.eazy-root{padding:0 0 28px}

/* ---------- AppBar ---------- */
.eazy-appbar{
  position:sticky;top:0;z-index:30;display:flex;align-items:center;gap:14px;
  min-height:64px;padding:10px 24px;background:var(--pv-surface);
  border-bottom:1px solid var(--pv-outline-var);
  box-shadow:0 1px 2px rgba(60,64,67,.08);
}
.eazy-appbar-main{min-width:0;display:flex;flex-direction:column;gap:2px}
.eazy-header-title{font-family:"Google Sans",Roboto,sans-serif;font-size:20px;font-weight:500;
  letter-spacing:.1px;line-height:26px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.eazy-header-desc{font-size:12.5px;color:var(--pv-on-surface-var);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.eazy-appbar-actions{margin-left:auto;display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.eazy-iconbtn{width:40px;height:40px;border:0;border-radius:50%;background:transparent;
  color:var(--pv-on-surface-var);cursor:pointer;font-size:18px;line-height:40px;text-align:center;
  padding:0;transition:background .15s}
.eazy-iconbtn:hover{background:var(--pv-surface-3)}
.eazy-textbtn{border:1px solid var(--pv-outline);background:transparent;color:var(--pv-primary);
  border-radius:20px;padding:7px 16px;font:inherit;font-size:13px;font-weight:500;cursor:pointer;
  transition:background .15s,box-shadow .15s}
.eazy-textbtn:hover{background:rgba(26,115,232,.08)}
html[data-theme=dark] .eazy-textbtn:hover{background:rgba(138,180,248,.12)}
.eazy-select{border:1px solid var(--pv-outline);background:var(--pv-surface);color:var(--pv-on-surface);
  border-radius:20px;height:36px;padding:0 12px;font:inherit;font-size:13px;cursor:pointer;
  outline:none;max-width:200px}
.eazy-select:hover{border-color:var(--pv-primary)}
.eazy-select:focus{box-shadow:0 0 0 3px rgba(26,115,232,.16)}

/* ---------- 联动筛选条 ---------- */
.eazy-filters{display:flex;align-items:center;gap:8px;flex-wrap:wrap;
  margin:16px 24px 0;padding:10px 14px;border-radius:12px;
  background:var(--pv-surface-1);border:1px solid var(--pv-outline-var);
  box-shadow:0 1px 2px rgba(60,64,67,.05)}
.eazy-filters-label{color:var(--pv-on-surface-var);font-size:12.5px;font-weight:500}
.eazy-hint{color:var(--pv-on-surface-var);font-size:11.5px;margin-left:auto}
.eazy-empty{display:flex;align-items:center;justify-content:center;height:100%;
  color:var(--pv-on-surface-var);font-size:13px}

/* ---------- Card ---------- */
.eazy-grid{display:grid;gap:16px;padding:16px 24px 0;align-items:start}
.eazy-section{grid-column:1/-1;display:flex;align-items:baseline;gap:10px;
  margin:14px 2px -2px;font-family:"Google Sans",Roboto,sans-serif;
  font-size:16px;font-weight:500;letter-spacing:.1px;color:var(--pv-on-surface)}
.eazy-section:first-child{margin-top:0}
.eazy-section::before{content:"";width:4px;height:18px;border-radius:2px;background:var(--pv-primary)}
.eazy-section-desc{font-size:12.5px;font-weight:400;color:var(--pv-on-surface-var)}
.eazy-card{position:relative;min-width:0;background:var(--pv-surface-1);
  border:1px solid var(--pv-outline-var);border-radius:12px;padding:16px 18px 12px;
  box-shadow:0 1px 2px rgba(60,64,67,.08);transition:box-shadow .2s}
.eazy-card:hover{box-shadow:0 1px 3px rgba(60,64,67,.16),0 4px 8px rgba(60,64,67,.08)}
.eazy-card-head{margin:0 0 6px;display:flex;align-items:flex-start;gap:8px}
.eazy-card-head>div{min-width:0;flex:1}
.eazy-codebtn{margin-left:auto;flex:none;border:1px solid var(--pv-outline);background:transparent;
  color:var(--pv-on-surface-var);border-radius:14px;cursor:pointer;font:inherit;font-size:11px;
  font-weight:500;line-height:18px;padding:1px 9px;white-space:nowrap}
.eazy-codebtn:hover{color:var(--pv-primary);border-color:var(--pv-primary);background:rgba(26,115,232,.08)}
.eazy-code{display:none;margin:10px 0 2px;border:1px solid var(--pv-outline-var);border-radius:10px;
  background:var(--pv-surface-3);overflow:hidden}
.eazy-code.is-open{display:block}
.eazy-code-top{display:flex;align-items:center;justify-content:space-between;gap:8px;
  padding:6px 10px;border-bottom:1px solid var(--pv-outline-var);font-size:11.5px;
  color:var(--pv-on-surface-var)}
.eazy-code-top .lang{font-weight:600;letter-spacing:.4px}
.eazy-copybtn{border:0;background:transparent;color:var(--pv-primary);cursor:pointer;
  font:inherit;font-size:11.5px;font-weight:500;padding:2px 6px;border-radius:6px}
.eazy-copybtn:hover{background:rgba(26,115,232,.1)}
.eazy-code pre{margin:0;padding:10px 12px;overflow:auto;max-height:340px;
  font-family:"Roboto Mono",Consolas,"Courier New",monospace;font-size:12px;line-height:1.55;
  color:var(--pv-on-surface);tab-size:4}
.eazy-code code{font:inherit;white-space:pre}
.eazy-card-title{font-family:"Google Sans",Roboto,sans-serif;font-size:14.5px;
  font-weight:500;line-height:20px;color:var(--pv-on-surface)}
.eazy-card-sub{font-size:12px;color:var(--pv-on-surface-var);margin-top:2px}
.eazy-chart{width:100%}
.eazy-toolbar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px}
.eazy-toolbar:not(:empty){margin:0 0 8px}

/* ---------- 下钻面包屑 / chips ---------- */
.eazy-crumb{display:inline-flex;align-items:center;gap:2px;flex-wrap:wrap}
.eazy-crumb button{border:0;background:none;color:var(--pv-primary);cursor:pointer;
  font:inherit;font-size:12.5px;font-weight:500;padding:3px 6px;border-radius:6px}
.eazy-crumb button:hover{background:rgba(26,115,232,.08)}
.eazy-crumb .sep{color:var(--pv-on-surface-var)}
.eazy-crumb .cur{color:var(--pv-on-surface);font-weight:600}
.eazy-btn{border:1px solid var(--pv-outline);background:transparent;border-radius:16px;
  color:var(--pv-primary);cursor:pointer;font:inherit;font-size:12px;font-weight:500;padding:3px 12px}
.eazy-btn:hover{background:rgba(26,115,232,.08)}
.eazy-chip{display:inline-flex;align-items:center;gap:6px;height:32px;padding:0 6px 0 12px;
  border-radius:8px;border:1px solid var(--pv-outline);background:var(--pv-surface-1);
  color:var(--pv-on-surface);font-size:12.5px}
.eazy-chip b{font-weight:600;color:var(--pv-primary)}
.eazy-chip-x{cursor:pointer;width:20px;height:20px;line-height:18px;text-align:center;
  border-radius:50%;color:var(--pv-on-surface-var);font-size:14px}
.eazy-chip-x:hover{background:rgba(217,48,37,.12);color:var(--pv-error)}

/* ---------- KPI（单指标） ---------- */
.eazy-kpi{display:flex;flex-direction:column;gap:7px;justify-content:center;
  height:100%;padding:2px 2px 0}
.eazy-kpi-head{display:flex;align-items:center;justify-content:space-between;gap:10px}
.eazy-kpi-label{font-size:13px;color:var(--pv-on-surface-var);font-weight:500;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.eazy-kpi-badge{flex:none;font-size:11px;color:var(--pv-on-surface-var);
  background:var(--pv-surface-3);border-radius:999px;padding:2px 9px;font-weight:500}
.eazy-kpi-main{display:flex;align-items:baseline;gap:9px;flex-wrap:wrap}
.eazy-kpi-value{font-family:"Google Sans",Roboto,sans-serif;font-size:34px;font-weight:600;
  line-height:1.12;letter-spacing:-.6px;color:var(--pv-on-surface);
  font-variant-numeric:tabular-nums}
.eazy-kpi-delta{display:inline-flex;align-items:center;gap:2px;font-size:12px;font-weight:600;
  padding:2px 8px;border-radius:999px;line-height:1.5}
.eazy-kpi-delta.eazy-up{color:var(--pv-success);background:rgba(24,128,56,.10)}
.eazy-kpi-delta.eazy-down{color:var(--pv-error);background:rgba(217,48,37,.10)}
html[data-theme=dark] .eazy-kpi-delta.eazy-up{background:rgba(129,201,149,.14)}
html[data-theme=dark] .eazy-kpi-delta.eazy-down{background:rgba(242,139,130,.14)}
.eazy-kpi-deltalabel{font-size:11.5px;color:var(--pv-on-surface-var)}
.eazy-kpi-hint{font-size:11.5px;color:var(--pv-on-surface-var);margin-top:-2px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.eazy-kpi-sparkwrap{height:34px;margin-top:1px}
.eazy-kpi-spark{display:block;width:100%;height:100%;overflow:visible}
.eazy-kpi-progress{display:flex;align-items:center;gap:8px}
.eazy-kpi-track{flex:1;height:6px;border-radius:999px;background:var(--pv-surface-3);overflow:hidden}
.eazy-kpi-track>span{display:block;height:100%;border-radius:999px}
.eazy-kpi-pct{flex:none;font-size:11.5px;color:var(--pv-on-surface-var);
  font-variant-numeric:tabular-nums}
.eazy-kpi-pct.eazy-pct-done{color:var(--pv-success);font-weight:600}
.eazy-up{color:var(--pv-success)}.eazy-down{color:var(--pv-error)}

/* ---------- group_kpi 指标组 ---------- */
.eazy-kpi-group{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:16px}
.eazy-metric{padding:2px 4px}
.eazy-metric .m-label{font-size:12.5px;color:var(--pv-on-surface-var);font-weight:500}
.eazy-metric .m-value{font-family:"Google Sans",Roboto,sans-serif;font-size:28px;font-weight:500;
  line-height:1.2;letter-spacing:-.2px;margin-top:6px;color:var(--pv-on-surface)}
.eazy-metric .m-unit{font-size:13px;font-weight:400;color:var(--pv-on-surface-var);margin-left:4px}
.eazy-metric .m-delta{font-size:12.5px;font-weight:600;margin-top:4px}
.eazy-metric .m-hint{font-size:11.5px;color:var(--pv-on-surface-var);margin-top:4px}

/* ---------- progress 进度条 ---------- */
.eazy-progress-list{display:flex;flex-direction:column;gap:12px;padding:4px 2px}
.eazy-progress-head{display:flex;justify-content:space-between;align-items:baseline;
  font-size:12.5px;margin-bottom:5px}
.eazy-progress-head .name{color:var(--pv-on-surface);font-weight:500}
.eazy-progress-head .val{color:var(--pv-on-surface-var)}
.eazy-progress-track{height:8px;border-radius:4px;background:var(--pv-surface-3);overflow:hidden}
.eazy-progress-fill{height:100%;border-radius:4px;transition:width .4s ease}

/* ---------- tile 瓦片 ---------- */
.eazy-tile-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));gap:8px;padding:2px}
.eazy-tile{display:flex;flex-direction:column;justify-content:center;gap:4px;height:74px;
  padding:8px 10px;border-radius:8px;overflow:hidden}
.eazy-tile .t-name{font-size:12px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.eazy-tile .t-val{font-family:"Google Sans",Roboto,sans-serif;font-size:16px;font-weight:500}

/* ---------- table 明细表 ---------- */
.eazy-table-wrap{overflow:auto;max-height:100%}
.eazy-table{width:100%;border-collapse:collapse;font-size:12.5px}
.eazy-table th{position:sticky;top:0;background:var(--pv-surface-1);color:var(--pv-on-surface-var);
  font-weight:500;text-align:left;padding:9px 12px;border-bottom:1px solid var(--pv-outline);
  white-space:nowrap}
.eazy-table td{padding:8px 12px;border-bottom:1px solid var(--pv-outline-var);
  white-space:nowrap;color:var(--pv-on-surface)}
.eazy-table tbody tr:hover td{background:var(--pv-surface-3)}
.eazy-table .num{text-align:right;font-variant-numeric:tabular-nums}
.eazy-table-more{font-size:11.5px;color:var(--pv-on-surface-var);padding:8px 2px 0}

/* ---------- wordcloud 词云 ---------- */
.eazy-wc{display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:6px 14px;
  height:100%;padding:6px 4px;overflow:hidden}
.eazy-wc-word{font-weight:500;line-height:1.15;transition:transform .15s;cursor:default}
.eazy-wc-word:hover{transform:scale(1.06)}
"""

_JS_ERR = """
window.addEventListener('error', function (e) {
  var d = document.createElement('div');
  d.id = 'eazy-js-error';
  d.style.cssText = 'color:#d93025;font:12px monospace;padding:8px 20px;white-space:pre-wrap';
  d.textContent = 'JS ERROR: ' + (e.message || e) + ' @ ' + (e.filename || '') + ':' + (e.lineno || '');
  (document.body || document.documentElement).appendChild(d);
});
"""


def _esc(text):
    return _html.escape("" if text is None else str(text))


def _card_html(spec, index):
    title = spec.get("title")
    subtitle = spec.get("subtitle")
    code = spec.get("code")
    head = ""
    if title or subtitle or code:
        head = '<div class="eazy-card-head"><div>'
        if title:
            head += '<div class="eazy-card-title">%s</div>' % _esc(title)
        if subtitle:
            head += '<div class="eazy-card-sub">%s</div>' % _esc(subtitle)
        head += "</div>"
        if code:
            head += ('<button class="eazy-codebtn" type="button" data-eazy-code="%d" '
                     'title="显示生成这张图的完整 Python 代码">代码</button>' % index)
        head += "</div>"
    kind = spec.get("type")
    # HTML 类组件（KPI/进度/瓦片/词云）按内容自适应高度，避免展开代码面板时压住正文；
    # table 需要固定高度才能内部滚动。
    AUTO_HEIGHT_TYPES = ("kpi", "group_kpi", "progress", "tile", "wordcloud")
    if kind == "kpi":
        body = ('<div class="eazy-kpi" data-eazy-chart="%d" style="min-height:%dpx"></div>'
                % (index, int(spec.get("height", 150))))
    elif kind in AUTO_HEIGHT_TYPES:
        body = ('<div class="eazy-chart" data-eazy-chart="%d" style="min-height:%dpx"></div>'
                % (index, int(spec.get("height", 320))))
    elif kind in HTML_TYPES:
        body = ('<div class="eazy-chart" data-eazy-chart="%d" style="height:%dpx"></div>'
                % (index, int(spec.get("height", 320))))
    else:
        body = ('<div class="eazy-chart" data-eazy-chart="%d" style="height:%dpx"></div>'
                % (index, int(spec.get("height", 380))))
    code_block = ""
    if code:
        code_block = (
            '<div class="eazy-code" data-eazy-codebox="%d">'
            '<div class="eazy-code-top"><span class="lang">PYTHON</span>'
            '<button class="eazy-copybtn" type="button" data-eazy-copy="%d">复制</button></div>'
            '<pre><code>%s</code></pre></div>' % (index, index, _esc(code))
        )
    return (
        '<section class="eazy-card" style="min-height:%dpx">%s'
        '<div class="eazy-toolbar" data-eazy-toolbar="%d"></div>%s%s</section>'
        % (_card_height(spec), head, index, body, code_block)
    )


#: 最近一次 v2 渲染失败的原因（调试用；成功时为 None）。
_LAST_STREAMLIT_ERROR = None


def streamlit_show(charts, cols=2, title=None, desc=None, theme=None, palette=None,
                   key=None, on_select=None):
    """在 Streamlit 页面里渲染一张或多张图，返回实际使用的模式（``"v2"`` / ``"v1"``）。

    优先使用 ``st.components.v2``（无 iframe、高度按内容自适应、图表点击可回传
    Python）；若当前 Streamlit 版本不支持 v2，自动回退到
    ``st.components.v1.html``（iframe）——行为与旧版本一致。

    只在已运行在 Streamlit 中时调用（``eazy_data_viz.render.is_streamlit()``）。
    """
    global _LAST_STREAMLIT_ERROR

    try:
        from . import streamlit_v2 as _v2

        if _v2.is_available():
            _v2.render_dashboard(
                charts,
                title=title,
                desc=desc,
                cols=cols,
                theme=theme,
                palette=palette,
                key=key,
                on_select=on_select,
            )
            _LAST_STREAMLIT_ERROR = None
            return "v2"
    except Exception as exc:  # pragma: no cover - 依赖 Streamlit 版本
        _LAST_STREAMLIT_ERROR = exc

    import streamlit.components.v1 as components

    height = page_height(
        charts,
        cols=cols,
        has_header=bool(title or desc),
        has_filters=any(c.spec.get("link") for c in charts),
    )
    html = build_page(
        charts, inline=True, title=title, cols=cols, theme=theme, desc=desc,
        palette=palette,
    )
    components.html(html, height=height, scrolling=False)
    return "v1"


def build_page(charts, inline=True, title=None, cols=None, theme=None, desc=None,
               palette=None):
    """把一组 Chart 组装成一个完整 HTML 文档字符串。

    ``palette`` 指定页面默认配色（google / antd / tableau / carbon / echarts /
    morandi / tailwind）；单图可以用 ``Chart.palette()`` 覆盖。
    """
    if isinstance(charts, (list, tuple)):
        charts = list(charts)
    else:  # pragma: no cover - 防御式
        charts = [charts]
    if not charts:
        raise ValueError("至少需要一张图。")

    theme = theme or (charts[0].spec.get("theme") or "light")
    palette = _palette.check(palette) if palette else _palette.current()
    n = len(charts)
    cols = int(cols) if cols else (1 if n == 1 else min(2, n))
    cols = max(1, min(cols, 6))

    # 数据去重：同一份 DataFrame 只嵌入一次
    data_store = {}
    for c in charts:
        ref, data = c.data_ref, c.data
        if not ref or ref in data_store:
            continue
        payload = {"cols": data["cols"], "rows": data["rows"], "kinds": data.get("kinds")}
        if data.get("orders"):
            payload["orders"] = data["orders"]
        data_store[ref] = payload

    specs = [c.spec for c in charts]
    # 按位置固定 id：Chart 构造时用的是全局自增 id（c1、c2…），每次 rerun 都会变，
    # components.v2 会因此判定 data 变化、整块重挂组件，导致联动/下钻状态被清空。
    # 这里统一按位置覆盖成稳定 id，rerun 前后 data 完全一致，组件就不再重挂。
    for _i, _s in enumerate(specs):
        _s["id"] = "eazy-%d" % _i
    has_filters = any(s.get("link") for s in specs)

    header = ""
    if title or desc:
        header = ('<header class="eazy-appbar"><div class="eazy-appbar-main">'
                  '<div class="eazy-header-title">%s</div>' % _esc(title or "eazy_data_viz 看板"))
        if desc:
            header += '<div class="eazy-header-desc">%s</div>' % _esc(desc)
        opts = []
        for _p in _palette.listing():
            _sel = " selected" if _p["name"] == palette else ""
            opts.append('<option value="%s"%s>配色：%s</option>'
                        % (_p["name"], _sel, _esc(_p["label"])))
        header += ('</div><div class="eazy-appbar-actions">'
                   '<select class="eazy-select" data-eazy-palette title="切换配色库">%s</select>'
                   '<button class="eazy-iconbtn" data-eazy-theme title="切换浅色/深色">◐</button>'
                   '<button class="eazy-textbtn" data-eazy-reset title="清除所有联动筛选">重置联动</button>'
                   '</div></header>' % "".join(opts))

    card_parts, last_section = [], None
    for _i, _s in enumerate(specs):
        sec = _s.get("section")
        if sec and sec != last_section:
            card_parts.append('<div class="eazy-section">%s</div>' % _esc(sec))
            last_section = sec
        card_parts.append(_card_html(_s, _i))
    cards = "\n".join(card_parts)

    page = {"theme": theme, "palette": palette, "charts": specs, "links": []}
    maps = _map_payload(specs)
    cities = _cities_payload() if maps else {}
    payload = {"maps": _frame.to_json(maps) if maps else "{}",
               "cities": _frame.to_json(cities) if cities else "{}",
               "data": _frame.to_json(data_store), "page": _frame.to_json(page)}

    filters = ""
    if has_filters:
        filters = ('<div class="eazy-filters" id="eazy-filters" style="display:none">'
                   '<span class="eazy-filters-label">联动筛选</span></div>')

    doc = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="{theme}" data-palette="{palette}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head>
<body data-theme="{theme}" data-palette="{palette}">
<div class="eazy-root">
{header}
{filters}
<div class="eazy-grid" style="grid-template-columns:repeat({cols},minmax(0,1fr))">
{cards}
</div>
</div>
<script>window.EAZY_MAPS = {maps};window.EAZY_CITIES = {cities};window.EAZY_DATA = {data};window.EAZY_PAGE = {page};</script>
{scripts}
<script>{js_err}
try {{
  EazyViz.init(window.EAZY_PAGE);
}} catch (err) {{
  var d = document.createElement('div');
  d.id = 'eazy-js-error';
  d.style.cssText = 'color:#d93025;font:12px monospace;padding:8px 20px;white-space:pre-wrap';
  d.textContent = 'INIT ERROR: ' + (err && err.stack ? err.stack : err);
  document.body.appendChild(d);
  if (window.console) console.error(err);
}}
</script>
</body>
</html>
""".format(
        theme=theme,
        palette=palette,
        title=_esc(title or "eazy_data_viz 图表"),
        css=_CSS,
        header=header,
        filters=filters,
        cols=cols,
        cards=cards,
        maps=payload["maps"],
        cities=payload["cities"],
        data=payload["data"],
        page=payload["page"],
        scripts=_script_tags(inline),
        js_err=_JS_ERR,
    )
    return doc


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------


def _scope_css(css):
    """把整页 CSS 改写成 Shadow DOM 可用的形式（:host 代替 html/body）。"""
    out = css
    out = out.replace(":root{", ":host{", 1)
    out = out.replace("html[data-theme=dark],body[data-theme=dark]{",
                      ":host([data-theme=dark]){")
    out = out.replace("html[data-theme=dark] ", ":host([data-theme=dark]) ")
    out = out.replace("html,body{margin:0;padding:0}",
                      ":host{display:block;margin:0;padding:0}")
    out = out.replace("\nbody{", "\n:host{", 1)
    return out


def build_fragment(charts, title=None, desc=None, cols=None, theme=None, palette=None):
    """组装 components.v2 组件所需的三部分：HTML 片段、CSS、data。

    返回值是 dict：

    - ``html``：DOM 片段（不含 ``<html>`` / ``<head>`` / ``<body>`` / ``<script>``）
    - ``css``：作用域化后的样式表（``:host`` 形式，配合 Shadow DOM 使用）
    - ``page`` / ``data_store`` / ``maps`` / ``cities``：传给组件 ``data`` 参数的
      JSON 可序列化对象，前端会写入 ``window.EAZY_*`` 后调用 ``EazyViz.init``
    - ``cols``：网格列数
    """
    if isinstance(charts, (list, tuple)):
        charts = list(charts)
    else:  # pragma: no cover - 防御式
        charts = [charts]
    if not charts:
        raise ValueError("至少需要一张图。")

    theme = theme or (charts[0].spec.get("theme") or "light")
    palette = _palette.check(palette) if palette else _palette.current()
    n = len(charts)
    cols = int(cols) if cols else (1 if n == 1 else min(2, n))
    cols = max(1, min(cols, 6))

    data_store = {}
    for c in charts:
        ref, data = c.data_ref, c.data
        if not ref or ref in data_store:
            continue
        payload = {"cols": data["cols"], "rows": data["rows"], "kinds": data.get("kinds")}
        if data.get("orders"):
            payload["orders"] = data["orders"]
        data_store[ref] = payload

    specs = [c.spec for c in charts]
    # 按位置固定 id：Chart 构造时用的是全局自增 id（c1、c2…），每次 rerun 都会变，
    # components.v2 会因此判定 data 变化、整块重挂组件，导致联动/下钻状态被清空。
    # 这里统一按位置覆盖成稳定 id，rerun 前后 data 完全一致，组件就不再重挂。
    for _i, _s in enumerate(specs):
        _s["id"] = "eazy-%d" % _i
    has_filters = any(s.get("link") for s in specs)

    header = ""
    if title or desc:
        header = ('<header class="eazy-appbar"><div class="eazy-appbar-main">'
                  '<div class="eazy-header-title">%s</div>' % _esc(title or "eazy_data_viz 看板"))
        if desc:
            header += '<div class="eazy-header-desc">%s</div>' % _esc(desc)
        opts = []
        for _p in _palette.listing():
            _sel = " selected" if _p["name"] == palette else ""
            opts.append('<option value="%s"%s>配色：%s</option>'
                        % (_p["name"], _sel, _esc(_p["label"])))
        header += ('</div><div class="eazy-appbar-actions">'
                   '<select class="eazy-select" data-eazy-palette title="切换配色库">%s</select>'
                   '<button class="eazy-iconbtn" data-eazy-theme title="切换浅色/深色">◐</button>'
                   '<button class="eazy-textbtn" data-eazy-reset title="清除所有联动筛选">重置联动</button>'
                   '</div></header>' % "".join(opts))

    card_parts, last_section = [], None
    for _i, _s in enumerate(specs):
        sec = _s.get("section")
        if sec and sec != last_section:
            card_parts.append('<div class="eazy-section">%s</div>' % _esc(sec))
            last_section = sec
        card_parts.append(_card_html(_s, _i))
    cards = "\n".join(card_parts)

    filters = ""
    if has_filters:
        filters = ('<div class="eazy-filters" id="eazy-filters" style="display:none">'
                   '<span class="eazy-filters-label">联动筛选</span></div>')

    markup = ('<div class="eazy-root" data-theme="%s" data-palette="%s">%s'
              '<div class="eazy-grid" style="grid-template-columns:repeat(%d,minmax(0,1fr))">'
              '%s</div></div>' % (theme, palette, header + filters, cols, cards))

    page = {"theme": theme, "palette": palette, "charts": specs, "links": []}
    maps = _map_payload(specs)
    cities = _cities_payload() if maps else {}
    return {
        "html": markup,
        "css": _scope_css(_CSS),
        "page": page,
        "data_store": data_store,
        "maps": maps,
        "cities": cities,
        "cols": cols,
        "has_filters": has_filters,
    }

class Dashboard:
    """多图看板：把多张图放进同一个 HTML 文档，联动/下钻才能跨图生效。"""

    def __init__(self, charts, cols=2, title=None, desc=None, theme=None, inline=True,
                 palette=None):
        charts = list(charts)
        if not charts:
            raise ValueError("dashboard 至少需要一张图。")
        self.charts = charts
        self.cols = cols
        self.title = title
        self.desc = desc
        self.theme = theme
        self.palette = _palette.check(palette) if palette else _palette.current()
        self.inline = inline

    # ---- 展示 -----------------------------------------------------------
    def to_html(self, inline=None):
        return build_page(
            self.charts,
            inline=self.inline if inline is None else inline,
            title=self.title,
            desc=self.desc,
            cols=self.cols,
            theme=self.theme,
            palette=self.palette,
        )

    def save(self, path, inline=None):
        inline = self.inline if inline is None else inline
        path = os.path.abspath(path)
        d = os.path.dirname(path)
        if d and not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_html(inline=inline))
        if not inline:
            _copy_assets(os.path.dirname(path))
        return path

    def show(self, open_browser=None):
        if is_streamlit():
            streamlit_show(
                self.charts,
                cols=self.cols,
                title=self.title,
                desc=self.desc,
                theme=self.theme,
                palette=getattr(self, "palette", None),
            )
            self._print_warnings()
            return self

        if in_notebook():
            from IPython.display import HTML, display

            display(HTML(self.to_html(inline=True)))
            self._print_warnings()
            return self

        import tempfile
        import webbrowser

        path = os.path.join(tempfile.mkdtemp(prefix="eazy_"), "dashboard.html")
        self.save(path)
        if open_browser is None:
            open_browser = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
        print("[eazy_data_viz] 已生成看板：%s" % path)
        if open_browser:
            webbrowser.open("file://" + path.replace("\\", "/"))
        self._print_warnings()
        return self

    def _repr_html_(self):
        return self.to_html(inline=True)

    def _print_warnings(self):
        for c in self.charts:
            for w in (c.warnings.get("warnings") or []):
                print("[eazy_data_viz 提示] " + w)

    def __repr__(self):
        return "<eazy_data_viz.Dashboard charts=%d cols=%d title=%r>" % (
            len(self.charts),
            self.cols,
            self.title,
        )


def _copy_assets(target_dir):
    dest = os.path.join(target_dir, "eazy_assets")
    os.makedirs(dest, exist_ok=True)
    for name in ALL_JS:
        src = os.path.join(ASSETS_DIR, name)
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(dest, name))
    maps_dest = os.path.join(dest, "maps")
    if os.path.isdir(MAPS_DIR):
        os.makedirs(maps_dest, exist_ok=True)
        for name in os.listdir(MAPS_DIR):
            src = os.path.join(MAPS_DIR, name)
            if os.path.isfile(src):
                shutil.copyfile(src, os.path.join(maps_dest, name))
    return dest


def dashboard(nums=None, *charts, **kwargs):
    """创建一个多图看板。

    >>> eazy_data_viz.dashboard(c1, c2, c3, cols=2, title="销售看板").show()
    """
    items = []
    if isinstance(nums, (list, tuple)):
        items.extend(nums)
    elif nums is not None:
        items.append(nums)
    items.extend(charts)
    return Dashboard(items, **kwargs)
