# -*- coding: utf-8 -*-
"""端到端交互测试：在浏览器里模拟真人操作，把 show / dashboard 的联动走一遍。

覆盖：点柱状图联动全组、汇总表单元格反向联动、桑基多级节点按真实层级联动、
旭日「放大 + 联动」并存与重置回根、下钻 + 单向出/单向进、主题 / 配色 / 重置、
onSelect 回调载荷。

运行：python tests/e2e_test.py
"""
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pandas as pd  # noqa: E402

import eazy_data_viz as ev  # noqa: E402
import eazy_data_viz.charts_extra as px  # noqa: E402

TMP = os.path.join(tempfile.gettempdir(), "eazy_e2e_test")


def find_chrome():
    env = os.environ.get("EAZY_CHROME")
    if env and os.path.exists(env):
        return env
    for cand in (
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
        os.path.expanduser("~/AppData/Local/Google/Chrome/Application/chrome.exe"),
    ):
        if os.path.exists(cand):
            return cand
    for name in ("google-chrome", "chromium", "chrome"):
        hit = shutil.which(name)
        if hit:
            return hit
    return None


PRELUDE = r"""
<script>
window.__P = []; window.__F = [];
function P(name, cond, extra) {
  if (cond) { window.__P.push(name); }
  else { window.__F.push(name + (extra !== undefined ? '[' + extra + ']' : '')); }
}
function finish() {
  var d = document.createElement('div');
  d.id = 'probe-result';
  d.setAttribute('data-pass', String(window.__P.length));
  d.setAttribute('data-fail', String(window.__F.length));
  d.textContent = window.__F.join('|');
  document.body.appendChild(d);
}
</script>
"""

WRAP = r"""
<script>
try {
%s
} catch (e) {
  P('js-exception', false, (e && e.message) || e);
}
if (!window.__deferFinish) finish();
</script>
"""


def build_charts():
    df = ev.sample_df(600)
    yoy = pd.concat([
        df.assign(年份="2025", 销售额=df["销售额"] * 0.86),
        df.assign(年份="2026"),
    ])
    return [
        ev.bar(df, x="大区", y="销售额", link="G", title="大区销售"),
        ev.line(df, x="月份", y="销售额", link="G", title="月度趋势"),
        ev.table(df, groupby={"columns": ["大区"], "value": "销售额", "agg": "sum"},
                 link="G", title="汇总表"),
        px.sankey(df, path=["大区", "渠道", "产品"], value="销售额", link="G", title="桑基"),
        px.sunburst(df, path=["大区", "渠道"], value="销售额", link="G", title="旭日"),
        ev.wordcloud(df, names="产品", values="销售额", shape="star", top_n=10, link="G",
                     title="词云"),
        ev.bar(yoy, x="月份", y="销售额", color="年份", yoy=True, title="同比（不联动）"),
        ev.bar(df, x="渠道", y="销售额", drill=["渠道", "产品"], link="H", title="下钻"),
        ev.bar(df, x="产品", y="销售额", link=("H", "in"), title="只接收"),
    ]


TEST_JS = r"""
(function () {
  var V = EazyViz, C = V.core, U = C.util;
  var charts = V.charts;
  function spec(i) { return charts[i].spec; }
  function st(i) { return charts[i].state; }
  function click(i, name, extra) {
    var p = { componentType: 'series', seriesIndex: 0, name: name, value: 1 };
    if (extra) { for (var k in extra) p[k] = extra[k]; }
    C.onChartClick(charts[i], p);
  }
  function viewRoot(i) {
    return charts[i].ec.getModel().getSeriesByIndex(0).getViewRoot();
  }

  // ---------- 0. 页面自检 ----------
  P('charts', charts.length === 9, charts.length);
  P('ready', document.documentElement.getAttribute('data-eazy-ready') === '1');
  P('toolbar-text', document.querySelectorAll('[data-eazy-toolbar]').length >= 5,
    document.querySelectorAll('[data-eazy-toolbar]').length);
  P('wc-canvas', document.querySelectorAll('canvas.eazy-wc-canvas').length === 1);
  P('palette-select', !!document.querySelector('[data-eazy-palette]'));
  P('theme-btn', !!document.querySelector('[data-eazy-theme]'));

  // ---------- 1. 点柱状图 → 全组过滤 ----------
  click(0, '华东');
  P('link-set', V.links['G'] && V.links['G'].dim === '大区' && V.links['G'].value === '华东',
    JSON.stringify(V.links['G']));
  P('bar-self-no-filter', !st(0).filters['大区'], JSON.stringify(st(0).filters));
  P('line-filtered', st(1).filters['大区'] === '华东', JSON.stringify(st(1).filters));
  P('table-filtered', st(2).filters['大区'] === '华东', JSON.stringify(st(2).filters));
  P('sankey-filtered', st(3).filters['大区'] === '华东');
  P('sunburst-filtered', st(4).filters['大区'] === '华东');

  // 汇总表按过滤后的数据重算，但后台数据不动
  var tblHtml = V.htmlBuilders['table'](spec(2), charts[2].data, st(2), charts[2].theme);
  var rows2 = charts[2].data.rows.length;
  P('table-render', tblHtml.indexOf('销售额') >= 0 && tblHtml.indexOf('华北') < 0, tblHtml.length);
  P('table-data-untouched', rows2 > 100, rows2);

  // ---------- 2. 点汇总表的格子 → 反向联动 ----------
  var cellEl = charts[2].el.querySelector('[data-eazy-cell]');
  P('table-cell-exists', !!cellEl, cellEl && cellEl.getAttribute('data-eazy-cell'));
  if (cellEl) {
    var dim = cellEl.getAttribute('data-eazy-cell'), val = cellEl.getAttribute('data-eazy-val');
    C.setLink('G', dim, val, charts[2]);
    P('cell-link', V.links['G'].sourceId === spec(2).id, V.links['G'].sourceId);
    P('cell-bar-follow', st(0).filters[dim] === val, JSON.stringify(st(0).filters));
    P('cell-table-self', !st(2).filters[dim] || st(2).filters[dim] !== val,
      JSON.stringify(st(2).filters));
  }

  // ---------- 3. 桑基节点 → 用真实层级联动 ----------
  var sk = V.nodeMaps[spec(3).id] || V.nodeMaps['sankey'];
  var skKeys = sk ? Object.keys(sk) : [];
  P('sankey-node-map', skKeys.length >= 3, skKeys.length);
  if (skKeys.length) {
    var lvl0 = null;
    for (var i = 0; i < skKeys.length; i++) {
      if (skKeys[i].indexOf('0\u0001') === 0) { lvl0 = skKeys[i]; break; }
    }
    P('sankey-level0-node', !!lvl0, lvl0);
    if (lvl0) {
      click(3, lvl0, { dataType: 'node', data: { name: sk[lvl0].value } });
      P('sankey-click-dim', V.links['G'].dim === '大区', V.links['G'].dim);
      P('sankey-click-value', V.links['G'].value === sk[lvl0].value, V.links['G'].value);
      P('sankey-self-no-filter', !st(3).filters['大区'], JSON.stringify(st(3).filters));
    }
  }

  // ---------- 4. 旭日：联动 + 放大并存 ----------
  var sun = charts[4];
  var topName = String(sun.ec.getModel().getSeriesByIndex(0).getData().tree.root.children[0].name);
  click(4, topName, {
    dataType: 'node',
    treePathInfo: [{ name: 'root' }, { name: topName }],
    data: { name: topName, nodeDim: '大区', nodeValue: topName, nodeLayer: 0 },
  });
  P('sun-link', V.links['G'].dim === '大区' && V.links['G'].value === topName,
    JSON.stringify(V.links['G']));

  // 放大是异步生效的（ECharts 下一帧才应用 rootToNode），放到 phase2 里查
  setTimeout(phase2, 350);

  function phase2() {
  var vr = viewRoot(4);
  P('sun-zoom', String(vr.name) === topName,
    'view=' + vr.name + ' top=' + topName + ' zoomPath=' + JSON.stringify(sun.zoomPath));

  // ---------- 5. 下钻 + 单向联动 ----------
  click(7, '线上商城');
  P('drill-crumb', st(7).drill.length === 1 && st(7).drill[0].value === '线上商城',
    JSON.stringify(st(7).drill));
  P('out-link', V.links['H'] && V.links['H'].dim === '渠道', JSON.stringify(V.links['H']));
  P('in-receives', st(8).filters['渠道'] === '线上商城', JSON.stringify(st(8).filters));
  P('out-self-no-filter', !st(7).filters['渠道'], JSON.stringify(st(7).filters));
  var before = JSON.stringify(V.links['H']);
  click(8, '智能终端');
  P('in-no-send', JSON.stringify(V.links['H']) === before, JSON.stringify(V.links['H']));
  var backBtn = document.querySelector('[data-back]');
  P('back-btn', !!backBtn);
  if (backBtn) { backBtn.click(); }
  P('drill-cleared', st(7).drill.length === 0, JSON.stringify(st(7).drill));

  // ---------- 6. 主题 / 配色 / 重置 ----------
  var themeBtn = document.querySelector('[data-eazy-theme]');
  themeBtn.click();
  P('theme-dark', document.documentElement.getAttribute('data-eazy-theme') === 'dark'
     || document.body.getAttribute('data-eazy-theme') === 'dark'
     || charts[0].theme.mode === 'dark' || charts[0].theme.bg !== '#ffffff',
     charts[0].theme.bg);
  themeBtn.click();
  var sel = document.querySelector('[data-eazy-palette]');
  sel.value = 'tableau';
  sel.dispatchEvent(new Event('change', { bubbles: true }));
  var opt = C.buildOption(charts[0].spec, charts[0].data, charts[0].state,
                          U.themeFor('light', 'tableau'));
  P('palette-switch', opt.color && opt.color[0] === '#4e79a7', opt.color && opt.color[0]);

  var resetBtn = document.querySelector('[data-eazy-reset]');
  P('reset-btn', !!resetBtn);
  if (resetBtn) { resetBtn.click(); }
  P('reset-links', !V.links['G'] && !V.links['H'], JSON.stringify(V.links));
  P('reset-filters', !st(1).filters['大区'] && !st(8).filters['渠道'],
    JSON.stringify(st(1).filters) + JSON.stringify(st(8).filters));

  // ---------- 7. 重置后：旭日回到根 + onSelect 回调 ----------
  setTimeout(function () {
    var vr2 = viewRoot(4);
    P('reset-zoom', String(vr2.name) !== topName,
      'view=' + vr2.name + ' zoomPath=' + JSON.stringify(sun.zoomPath));

    var got = null;
    V.onSelect = function (info) { got = info; };
    click(0, '华东');
    P('onselect-fired', !!got, JSON.stringify(got));
    if (got) {
      P('onselect-dim', got.dim === '大区' && got.value === '华东', got.dim + '/' + got.value);
      P('onselect-has-mode', got.linkMode === 'both' && got.canSend === true,
        got.linkMode + '/' + got.canSend);
    }
    finish();
  }, 300);
  }
})();
"""


def main():
    chrome = find_chrome()
    if not chrome:
        print("跳过：没有找到 Chrome（可用 EAZY_CHROME 指定路径）")
        return 0
    os.makedirs(TMP, exist_ok=True)
    html = ev.dashboard(build_charts(), cols=3, title="E2E 联动复盘").to_html()
    head, sep, tail = html.rpartition("</body>")
    html = (head + PRELUDE + "<script>window.__deferFinish = true;</script>"
            + (WRAP % TEST_JS) + "\n" + sep + tail)
    path = os.path.join(TMP, "e2e.html")
    io.open(path, "w", encoding="utf-8").write(html)

    cmd = [
        chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
        "--virtual-time-budget=15000", "--window-size=1500,1400", "--dump-dom",
        "--user-data-dir=" + os.path.join(TMP, "profile"),
        "--no-first-run", "--no-default-browser-check", "--disable-extensions",
        "--allow-file-access-from-files",
        "file:///" + path.replace("\\", "/"),
    ]
    cp = subprocess.run(cmd, capture_output=True)
    dom = cp.stdout.decode("utf-8", "replace")
    if not dom:
        print("没有拿到 DOM。stderr:", cp.stderr.decode("utf-8", "replace")[:1200])
        return 2
    m = re.search(r'<div id="probe-result" data-pass="(\d+)" data-fail="(\d+)">([^<]*)</div>', dom)
    if not m:
        print("没有结果节点")
        return 2
    passed, failed, detail = int(m.group(1)), int(m.group(2)), m.group(3)
    print("E2E PASS %d, FAIL %d" % (passed, failed))
    if failed:
        for item in detail.split("|"):
            print("  FAIL:", item)
        return 1
    print("ALL E2E OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
