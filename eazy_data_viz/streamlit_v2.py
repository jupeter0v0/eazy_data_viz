# -*- coding: utf-8 -*-
"""Streamlit ``components.v2`` 渲染器。

与 ``st.components.v1.html``（iframe）相比，components v2：

- 组件的 HTML/CSS/JS 直接挂在应用页面里（默认 Shadow DOM），**不再有 iframe**：
  没有二次滚动条、没有 iframe 高度裁剪问题，图表宽度跟随列宽自适应；
- 组件高度默认「按内容撑开」（``height="content"``），不需要手工计算
  ``page_height()``；
- 支持 **可选的双向通信**：只有显式传了 ``on_select`` 时，图表点击才会以 trigger
  值回传给 Python，可据此做详情表、跳转、写 session_state 等；不传 ``on_select``
  时点击完全在浏览器内处理，**不会触发脚本 rerun**；
- ``data`` 参数原生支持 JSON / bytes / Arrow，不必再把数据序列化进 HTML 字符串。

本模块的用法（推荐）：::

    import eazy_data_viz as edv

    charts = [edv.kpi(df, value="销售额"), edv.bar(df, x="大区", y="销售额")]

    def on_click(info):          # info 是 dict：chart / title / type / dim / value / drill
        ...

    result = edv.streamlit_dashboard(charts, title="经营驾驶舱", cols=2,
                                     on_select=on_click)
    if result.select:
        st.write("你点了：", result.select["value"])

旧版 Streamlit（无 components v2）可继续用 ``pviz`` 的 v1 路径：::

    st.components.v1.html(edv.dashboard(charts).to_html(), height=..., scrolling=False)

该模块不在导入时依赖 Streamlit，因此普通 Python 环境 import 本包不会受影响。
"""

from __future__ import annotations

import json
import os

from . import render as _render

__all__ = ["is_available", "render_dashboard", "component_html_placeholder"]

_HTML_PLACEHOLDER = '<div id="eazy-v2-mount"></div>'

_COMPONENT = None
_COMPONENT_KEY = None

_JS_TEMPLATE = r"""
export default function (component) {
  const { parentElement, data, setTriggerValue } = component;
  const root = parentElement;                       // ShadowRoot（isolate_styles 默认开启）
  const host = (parentElement && parentElement.host) ? parentElement.host : parentElement;
  const payload = data || {};
  const SOURCES = __SOURCES__;
  const ORDER = __ORDER__;

  function inject(code) {
    const s = document.createElement('script');
    s.textContent = code;
    document.head.appendChild(s);
  }

  function boot() {
    const mount = (root.querySelector ? root.querySelector('#eazy-v2-mount') : null) || root;
    if (payload.html) mount.innerHTML = payload.html;
    window.EAZY_DATA = payload.data_store || {};
    window.EAZY_MAPS = payload.maps || {};
    window.EAZY_CITIES = payload.cities || {};
    if (!window.EazyViz) throw new Error('eazy.js 未加载');
    // 只有调用方显式传了 on_select（data.trigger 为真）才把点击回传 Python；
    // 否则 onSelect 置空，点图 / 联动 / 下钻全部在浏览器内完成，不触发脚本 rerun。
    if (payload.trigger) {
      window.EazyViz.onSelect = function (info) {
        try { setTriggerValue('select', info); } catch (e) { /* 忽略 */ }
      };
    } else {
      window.EazyViz.onSelect = null;
    }
    window.EazyViz.init(payload.page || {}, root);
    if (host && host.setAttribute) {
      host.setAttribute('data-eazy-ready', '1');
      host.setAttribute('data-eazy-count',
        String(((payload.page || {}).charts || []).length));
    }
  }

  try {
    if (!window.echarts) inject(SOURCES['__ECHARTS__']);
    if (!window.EazyViz) {
      for (let i = 0; i < ORDER.length; i++) {
        if (ORDER[i] === '__ECHARTS__') continue;
        inject(SOURCES[ORDER[i]]);
      }
    }
  } catch (err) {
    const box = document.createElement('pre');
    box.style.cssText = 'color:#d93025;font:12px monospace;white-space:pre-wrap;padding:8px';
    box.textContent = 'eazy_data_viz: 运行时加载失败 ' + (err && err.message ? err.message : err);
    root.appendChild(box);
    return;
  }

  requestAnimationFrame(function () {
    try {
      boot();
    } catch (err) {
      const box = document.createElement('pre');
      box.style.cssText = 'color:#d93025;font:12px monospace;white-space:pre-wrap;padding:8px';
      box.textContent = 'eazy_data_viz: 初始化失败 ' + (err && err.message ? err.message : err);
      root.appendChild(box);
    }
  });
}
"""


def is_available():
    """当前环境是否支持 Streamlit components v2。"""
    try:
        import streamlit as st  # noqa: F401
        from streamlit.components.v2 import component  # noqa: F401
        return True
    except Exception:  # pragma: no cover - 依赖环境
        return False


def _asset_signature():
    names = _render.ALL_JS
    items = []
    for name in names:
        path = os.path.join(_render.ASSETS_DIR, name)
        try:
            st = os.stat(path)
            items.append((name, st.st_size, int(st.st_mtime)))
        except OSError:
            items.append((name, 0, 0))
    return tuple(items)


def _sources():
    """按文件名收集全部资源。

    必须用 ``_render.ALL_JS`` 而不是手写清单：少一个文件（例如
    ``eazy_map.js``）就会让对应图表在 v2 下报「不支持的图表类型」。
    """
    return {name: _render._read_asset(name) for name in _render.ALL_JS}


def _component():
    """注册（并缓存）v2 组件。"""
    global _COMPONENT, _COMPONENT_KEY
    import streamlit as st
    from streamlit.components.v2 import component as mount_component

    key = _asset_signature()
    if _COMPONENT is not None and key == _COMPONENT_KEY:
        return _COMPONENT
    js = (
        _JS_TEMPLATE
        .replace("__ECHARTS__", _render.ECHARTS_JS)
        .replace("__ORDER__", json.dumps(list(_render.ALL_JS), ensure_ascii=True))
        .replace("__SOURCES__", json.dumps(_sources(), ensure_ascii=True))
    )
    _COMPONENT = mount_component(
        "eazy_data_viz.dashboard",
        html=_HTML_PLACEHOLDER,
        css=_render._scope_css(_render._CSS),
        js=js,
    )
    _COMPONENT_KEY = key
    return _COMPONENT


def component_html_placeholder():
    """v2 组件的固定 HTML 骨架（调试用）。"""
    return _HTML_PLACEHOLDER


_SKELETON_HTML = """
<div class="eazy-skel">
  <div class="eazy-skel-head">
    <span class="eazy-skel-spin"></span>
    <span class="eazy-skel-tip">正在渲染图表…</span>
  </div>
  <div class="eazy-skel-bar" style="width:34%"></div>
  <div class="eazy-skel-grid">
    <div class="eazy-skel-card"></div>
    <div class="eazy-skel-card"></div>
    <div class="eazy-skel-card"></div>
    <div class="eazy-skel-card"></div>
  </div>
</div>
<style>
.eazy-skel{padding:10px 2px 6px;font-family:system-ui,-apple-system,"Segoe UI",sans-serif}
.eazy-skel-head{display:flex;align-items:center;gap:8px;margin-bottom:12px;color:inherit;opacity:.75}
.eazy-skel-spin{width:13px;height:13px;border-radius:50%;border:2px solid currentColor;
  border-right-color:transparent;animation:eazy-skel-rot .8s linear infinite;display:inline-block}
.eazy-skel-tip{font-size:12.5px;line-height:1}
.eazy-skel-bar{height:14px;border-radius:7px;background:var(--eazy-skel-bg,rgba(125,145,180,.26))}
.eazy-skel-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:14px}
.eazy-skel-card{height:150px;border-radius:12px;background:var(--eazy-skel-bg2,rgba(125,145,180,.18))}
@keyframes eazy-skel-rot{to{transform:rotate(360deg)}}
@keyframes eazy-skel-pulse{0%,100%{opacity:.5}50%{opacity:1}}
.eazy-skel-bar,.eazy-skel-card{animation:eazy-skel-pulse 1.5s ease-in-out infinite}
@media (max-width:820px){.eazy-skel-grid{grid-template-columns:1fr}.eazy-skel-card{height:120px}}
</style>
"""


def _payload_signature(charts, options):
    """按内容（数据指纹 + spec）算签名：rerun 后内容没变就能直接复用。"""
    import hashlib

    parts = []
    for c in charts:
        spec = getattr(c, "spec", None) or {}
        clean = dict(spec)
        clean.pop("id", None)
        parts.append(json.dumps(clean, sort_keys=True, default=str, ensure_ascii=False))
        parts.append(str(getattr(c, "ref", "") or ""))
    parts.append(json.dumps(options, sort_keys=True, default=str, ensure_ascii=False))
    return hashlib.sha1("\x00".join(parts).encode("utf-8")).hexdigest()


def _placeholder():
    """先放一个骨架屏占位，渲染完成后再替换；失败就返回 None 按普通方式渲染。"""
    try:
        import streamlit as st

        holder = st.empty()
        holder.markdown(_SKELETON_HTML, unsafe_allow_html=True)
        return holder
    except Exception:  # pragma: no cover - 非 Streamlit 环境
        return None


def _cached_payload(signature):
    try:
        import streamlit as st

        store = st.session_state.get("_eazy_v2_payload")
        if isinstance(store, dict) and store.get("sig") == signature:
            return store.get("data")
    except Exception:  # pragma: no cover - 非 Streamlit 环境
        return None
    return None


def _store_payload(signature, data):
    try:
        import streamlit as st

        st.session_state["_eazy_v2_payload"] = {"sig": signature, "data": data}
    except Exception:  # pragma: no cover
        pass


def render_dashboard(charts, *, title=None, desc=None, cols=None, theme=None,
                     palette=None, height=None, key=None, on_select=None,
                     layout=None, direction=None, grid=None,
                     hints=None, card_style="default"):
    """在 Streamlit 页面里用 components v2 渲染一张看板。

    参数
    ----
    charts : list[Chart]
        要渲染的图表（``kpi`` / ``bar`` / ``geo_map`` ... 任意组合）。
    title, desc, cols, theme, palette
        与 ``dashboard()`` 相同：标题、描述、网格列数、主题、配色库。
    height : int or None
        组件高度（像素）。默认 ``None`` 表示按内容自适应（v2 的 ``height="content"``）。
    key : str or None
        组件实例 key，用于 ``st.session_state[key]``。
    on_select : callable or None
        图表点击回调（无参数）。回调里可读 :class:`ComponentResult` 的
        ``select`` 属性；也可直接用返回值。
        默认 ``None``：不挂 trigger 通道，点击只在浏览器内完成，**不会触发
        脚本 rerun**，此时返回值的 ``select`` 恒为 ``None``。需要「点图 → 重新
        计算」时才传回调；若只是想在浏览器内联动/下钻，不需要传。

    返回
    ----
    ComponentResult
        带有 ``select`` 触发值（最近一次点击：``chart`` / ``title`` / ``type`` /
        ``dim`` / ``value`` / ``drill`` / ``link``）以及组件状态。
        未传 ``on_select`` 时 ``select`` 为 ``None``。
    """
    if not is_available():
        raise RuntimeError(
            "当前环境不支持 Streamlit components v2（需要 streamlit>=1.50 左右的新版本）。"
            "可以改用 st.components.v1.html(dashboard(...).to_html(), height=...)。"
        )
    signature = _payload_signature(charts, {
        "title": title, "desc": desc, "cols": cols, "theme": theme, "palette": palette,
        "layout": layout, "direction": direction, "grid": grid,
        "hints": hints, "card_style": card_style,
        # 是否挂了点击回调会影响 data["trigger"]，必须进签名，否则换个用法会拿到旧的
        "trigger": on_select is not None,
    })
    data = _cached_payload(signature)
    if data is None:
        frag = _render.build_fragment(
            charts, title=title, desc=desc, cols=cols, theme=theme, palette=palette,
            layout=layout, direction=direction, grid=grid,
            hints=hints, card_style=card_style,
        )
        data = {
            "html": frag["html"],
            "page": frag["page"],
            "data_store": frag["data_store"],
            "maps": frag["maps"],
            "cities": frag["cities"],
            # 前端据此决定是否挂 setTriggerValue；False 时点击不产生任何 rerun。
            "trigger": on_select is not None,
        }
        _store_payload(signature, data)
    renderer = _component()
    kwargs = {"data": data, "key": key}
    if on_select is not None:
        kwargs["on_select_change"] = on_select
    if height is not None:
        kwargs["height"] = int(height)
    holder = _placeholder()
    target = holder.container() if holder is not None else None
    if target is None:
        return renderer(**kwargs)
    with target:
        return renderer(**kwargs)
