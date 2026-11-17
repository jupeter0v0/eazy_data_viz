"""截取 gallery 中一张卡片展开代码面板后的样子。

用法：python tools/shot_code.py <out.png> [标题子串] [等待秒]
前置：chrome --headless=new --remote-debugging-port=9222 --remote-allow-origins=*
"""
import base64
import json
import sys
import time
import urllib.request

import websocket

CDP = "http://127.0.0.1:9222"
URL = "file:///F:/deepseek/eazy_data_viz/gallery.html"
OUT = sys.argv[1]
NEEDLE = sys.argv[2] if len(sys.argv) > 2 else ""
WAIT = float(sys.argv[3]) if len(sys.argv) > 3 else 18.0


def http_json(path):
    with urllib.request.urlopen(CDP + path, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
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

    send("Target.createTarget", {"url": "about:blank"})
    page = [t for t in http_json("/json/list") if t["type"] == "page"][0]
    ws.close()
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=180)
    send("Page.enable")
    send("Runtime.enable")
    send("Emulation.setDeviceMetricsOverride",
         {"width": 1500, "height": 1400, "deviceScaleFactor": 1, "mobile": False})
    send("Page.navigate", {"url": URL})
    print("navigated, waiting %.0fs ..." % WAIT)
    time.sleep(WAIT)

    expr = """(function(){
      var needle=%s;
      var cards=[].slice.call(document.querySelectorAll('.eazy-card'));
      var card=null;
      for (var i=0;i<cards.length;i++){
        if (!needle || (cards[i].textContent||'').indexOf(needle)>=0){ card=cards[i]; break; }
      }
      if(!card) return 'no card';
      var btn=card.querySelector('[data-eazy-code]');
      if(!btn) return 'no code button';
      btn.click();
      var ab=document.querySelector('.eazy-appbar'); if(ab) ab.style.position='static';
      var r=card.getBoundingClientRect();
      window.scrollTo(0, window.scrollY + r.top - 24);
      return 'ok';
    })()""" % json.dumps(NEEDLE)
    res = send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
    print("click:", res.get("result", {}).get("result", {}).get("value"))
    time.sleep(1.5)

    shot = send("Page.captureScreenshot", {"format": "png"})
    data = base64.b64decode(shot["result"]["data"])
    with open(OUT, "wb") as f:
        f.write(data)
    print("saved", OUT, len(data), "bytes")


if __name__ == "__main__":
    main()
