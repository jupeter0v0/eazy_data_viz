# -*- coding: utf-8 -*-
"""Streamlit ``components.v2`` 渲染器。

与 ``st.components.v1.html``（iframe）相比，components v2：

- 组件的 HTML/CSS/JS 直接挂在应用页面里（默认 Shadow DOM），**不再有 iframe**：
  没有二次滚动条、没有 iframe 高度裁剪问题，图表宽度跟随列宽自适应；
- 组件高度默认「按内容撑开」（``height="content"``），不需要手工计算
  ``page_height()``；
- 支持 **双向通信**：图表点击会以 trigger 值回传给 Python（``on_select``），
  可据此做详情表、跳转、写 session_state 等；
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
    window.EazyViz.onSelect = function (info) {
      try { setTriggerValue('select', info); } catch (e) { /* 忽略 */ }
    };
    window.EazyViz.init(payload.page || {}, root);
    if (host && host.setAttribute) {
      host.setAttribute('data-eazy-ready', '1');
      host.setAttribute('data-eazy-count',
        String(((payload.page || {}).charts || []).length));
    }
  }

  try {
    if (!window.echarts) inject(SOURCES.echarts);
    if (!window.EazyViz) {
      inject(SOURCES.runtime);
      inject(SOURCES.main);
      inject(SOURCES.extra_a);
      inject(SOURCES.extra_b);
      inject(SOURCES.extra_html);
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
    out = {}
    for name, key in (
        (_render.ECHARTS_JS, "echarts"),
        (_render.RUNTIME_JS, "runtime"),
        ("eazy_extra_main.js", "main"),
        ("eazy_extra_a.js", "extra_a"),
        ("eazy_extra_b.js", "extra_b"),
        ("eazy_extra_html.js", "extra_html"),
    ):
        out[key] = _render._read_asset(name)
    return out


def _component():
    """注册（并缓存）v2 组件。"""
    global _COMPONENT, _COMPONENT_KEY
    import streamlit as st
    from streamlit.components.v2 import component as mount_component

    key = _asset_signature()
    if _COMPONENT is not None and key == _COMPONENT_KEY:
        return _COMPONENT
    js = _JS_TEMPLATE.replace("__SOURCES__", json.dumps(_sources(), ensure_ascii=True))
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


def render_dashboard(charts, *, title=None, desc=None, cols=None, theme=None,
                     palette=None, height=None, key=None, on_select=None,
                     layout=None, direction=None, grid=None):
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

    返回
    ----
    ComponentResult
        带有 ``select`` 触发值（最近一次点击：``chart`` / ``title`` / ``type`` /
        ``dim`` / ``value`` / ``drill`` / ``link``）以及组件状态。
    """
    if not is_available():
        raise RuntimeError(
            "当前环境不支持 Streamlit components v2（需要 streamlit>=1.50 左右的新版本）。"
            "可以改用 st.components.v1.html(dashboard(...).to_html(), height=...)。"
        )
    frag = _render.build_fragment(
        charts, title=title, desc=desc, cols=cols, theme=theme, palette=palette,
        layout=layout, direction=direction, grid=grid,
    )
    data = {
        "html": frag["html"],
        "page": frag["page"],
        "data_store": frag["data_store"],
        "maps": frag["maps"],
        "cities": frag["cities"],
    }
    renderer = _component()
    kwargs = {
        "data": data,
        "key": key,
        "on_select_change": on_select if on_select is not None else (lambda: None),
    }
    if height is not None:
        kwargs["height"] = int(height)
    return renderer(**kwargs)
