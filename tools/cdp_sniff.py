"""用 CDP 打开 HTML 页面，收集控制台错误并执行 JS 表达式（用于验证真实渲染结果）。

用法::

    python tools/cdp_sniff.py <url> [--wait 15] [--expr "JS 表达式"]

前置：另开一个带调试端口的 headless Chrome::

    chrome --headless=new --remote-debugging-port=9222 --remote-allow-origins=*
"""
import json
import sys
import time
import urllib.request

import websocket

CDP = "http://127.0.0.1:9222"
DEFAULT_EXPR = """(function () {
  var out = { ready: null, charts: [], pageErrors: [] };
  var root = document.querySelector('[data-eazy-ready]');
  out.ready = root ? root.getAttribute('data-eazy-ready') : null;
  var list = (window.EazyViz && EazyViz.charts) || [];
  for (var i = 0; i < list.length; i++) {
    var c = list[i];
    var item = { id: c.spec && c.spec.id, type: c.spec && c.spec.type };
    try {
      var ec = c.ec || c.chart;
      var opt = ec ? ec.getOption() : null;
      item.series = [];
      if (opt && opt.series) {
        for (var s = 0; s < opt.series.length; s++) {
          var se = opt.series[s];
          item.series.push(se.type + ':' + ((se.data && se.data.length) || 0));
        }
      }
      item.geo = !!(opt && opt.geo);
      item.geoSeries = opt && opt.geo && opt.geo.length;
    } catch (e) { item.err = String(e); }
    out.charts.push(item);
  }
  return JSON.stringify(out);
})()"""


def http_json(path):
    with urllib.request.urlopen(CDP + path, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def main(argv):
    url = argv[0]
    wait = 15.0
    expr = DEFAULT_EXPR
    i = 1
    while i < len(argv):
        if argv[i] == "--wait" and i + 1 < len(argv):
            wait = float(argv[i + 1])
            i += 2
        elif argv[i] == "--expr" and i + 1 < len(argv):
            expr = argv[i + 1]
            i += 2
        else:
            i += 1

    ver = http_json("/json/version")
    ws = websocket.create_connection(ver["webSocketDebuggerUrl"], timeout=60)
    mid = [0]

    def send(method, params=None):
        sid = mid[0]
        mid[0] += 1
        ws.send(json.dumps({"id": sid, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == sid:
                return msg

    try:
        send("Target.createTarget", {"url": "about:blank"})
    except Exception:
        pass
    page = [t for t in http_json("/json/list") if t["type"] == "page"][-1]
    ws.close()
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=180)

    logs = []

    def pump(seconds):
        end = time.time() + seconds
        ws.settimeout(0.5)
        while time.time() < end:
            try:
                msg = json.loads(ws.recv())
            except Exception:
                continue
            m = msg.get("method")
            p = msg.get("params", {})
            if m == "Runtime.consoleAPICalled" and p.get("type") in ("error", "warning"):
                txt = " ".join(str(a.get("value", a.get("description", "")))
                               for a in p.get("args", []))
                logs.append("[console.%s] %s" % (p.get("type"), txt))
            elif m == "Runtime.exceptionThrown":
                d = p.get("exceptionDetails", {})
                ex = d.get("exception") or {}
                logs.append("[exception] %s | %s" % (d.get("text"), ex.get("description", "")[:300]))
            elif m == "Log.entryAdded":
                e = p.get("entry", {})
                if e.get("level") in ("error", "warning"):
                    logs.append("[log.%s] %s" % (e.get("level"), e.get("text")))
        ws.settimeout(60)

    send("Page.enable")
    send("Runtime.enable")
    send("Log.enable")
    send("Emulation.setDeviceMetricsOverride",
         {"width": 1500, "height": 1200, "deviceScaleFactor": 1, "mobile": False})
    send("Page.navigate", {"url": url})
    pump(wait)
    res = send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
    value = res.get("result", {}).get("result", {}).get("value")
    print("== console / exceptions ==")
    for line in (logs[:40] or ["  (none)"]):
        print("  " + line)
    print("== expression ==")
    try:
        print(json.dumps(json.loads(value), ensure_ascii=False, indent=2))
    except Exception:
        print(value)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
