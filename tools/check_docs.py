# -*- coding: utf-8 -*-
"""文档完整性检查：每个图表函数的 docs/api/<fn>.md 是否覆盖全部参数。

用法::

    python tools/check_docs.py           # 只输出缺失/不完整
    python tools/check_docs.py --verbose # 输出每个函数的覆盖情况

检查项：
1. ``eazy_data_viz.__all__`` 里每个图表函数是否有 ``docs/api/<函数名>.md``；
2. 文档是否包含该函数签名中的**每一个参数**（以 ``### `参数名``` 或参数总览表格出现为准）；
3. 文档是否包含 ``## 函数签名`` ``## 参数总览`` ``## 参数详解`` ``## 完整示例`` 等必备小节；
4. 文档行数是否达到参考下限（默认 200 行，可 ``--min-lines`` 调整）。
"""
from __future__ import annotations

import inspect
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_DIR = os.path.join(ROOT, "docs", "api")
REQUIRED_SECTIONS = ("## 函数签名", "## 参数总览", "## 参数详解", "## 完整示例")
# 不算"图表函数"的辅助对象
NON_CHART = {
    "Chart", "Dashboard", "show", "dashboard", "sample_df", "help", "gallery",
    "set_palette", "palettes", "palette", "render", "maps",
    # Streamlit 集成入口，文档在 guides/07-streamlit.md
    "streamlit_dashboard", "streamlit_available",
    # 缓存与性能辅助，文档在 docs/api/README.md「缓存与性能辅助」与 guides/07、13
    "cached", "clear_cache", "cache_info", "use_cache",
}


def chart_functions():
    sys.path.insert(0, ROOT)
    import eazy_data_viz as edv

    out = []
    for name in getattr(edv, "__all__", []):
        obj = getattr(edv, name, None)
        if not callable(obj) or name in NON_CHART:
            continue
        try:
            sig = inspect.signature(obj)
        except (TypeError, ValueError):
            continue
        out.append((name, sig))
    return out


def main(argv):
    verbose = "--verbose" in argv
    min_lines = 200
    for i, a in enumerate(argv):
        if a == "--min-lines" and i + 1 < len(argv):
            min_lines = int(argv[i + 1])

    funcs = chart_functions()
    missing, partial, ok = [], [], []
    for name, sig in funcs:
        path = os.path.join(API_DIR, name + ".md")
        params = [p for p, prm in sig.parameters.items()
                  if p not in ("self", "cls")
                  and prm.kind not in (inspect.Parameter.VAR_POSITIONAL,
                                       inspect.Parameter.VAR_KEYWORD)]
        if not os.path.isfile(path):
            missing.append((name, params))
            continue
        text = open(path, encoding="utf-8").read()
        lack = [p for p in params
                if ("### `%s`" % p) not in text and ("| `%s` |" % p) not in text]
        secs = [s for s in REQUIRED_SECTIONS if s not in text]
        lines = text.count("\n") + 1
        if lack or secs or lines < min_lines:
            partial.append((name, lack, secs, lines, len(params)))
        else:
            ok.append((name, lines, len(params)))

    print("文档检查：共 %d 个图表函数" % len(funcs))
    print("  完整：%d    不完整：%d    缺失：%d" % (len(ok), len(partial), len(missing)))
    for name, params in missing:
        print("  [缺失文件] %-14s 参数 %d 个: %s" % (name, len(params), ", ".join(params)))
    for name, lack, secs, lines, nparams in partial:
        msg = []
        if lack:
            msg.append("未覆盖参数: " + ", ".join(lack))
        if secs:
            msg.append("缺小节: " + ", ".join(secs))
        if lines < min_lines:
            msg.append("仅 %d 行（< %d）" % (lines, min_lines))
        print("  [待完善] %-14s %s" % (name, "；".join(msg)))
    if verbose:
        print("\n完整清单：")
        for name, lines, nparams in sorted(ok):
            print("  %-16s %5d 行 / %d 参数" % (name, lines, nparams))
    total_lines = sum(l for _, l, _ in ok) + sum(p[3] for p in partial)
    print("\n文档总行数（已存在的 api 文档）：%d" % total_lines)
    return 0 if not missing and not partial else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
