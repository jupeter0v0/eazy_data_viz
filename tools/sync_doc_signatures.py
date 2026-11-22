# -*- coding: utf-8 -*-
"""把 docs/api/<函数名>.md 里的「## 函数签名」代码块与真实签名对齐。

文档里的签名块是手写的，参数一多就会漂（1.5.2 把 ``max_rows`` 默认值改成
2000000 后，39 个文档页的签名块还写着 200000）。这个工具直接读
``inspect.signature()`` 重新生成代码块，只替换 fenced block 本身，其它内容
（参数总览、详解、示例）一律不动。

用法::

    python tools/sync_doc_signatures.py          # 就地同步
    python tools/sync_doc_signatures.py --check  # 只报告，不写文件（漂移则退出码 1）
    python tools/sync_doc_signatures.py --verbose
"""
from __future__ import annotations

import inspect
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_DIR = os.path.join(ROOT, "docs", "api")
HEADING = "## 函数签名"


def _fmt_default(value):
    if isinstance(value, str):
        return '"%s"' % value
    if isinstance(value, bool) or value is None or isinstance(value, (int, float)):
        return repr(value)
    return repr(value)


def _fmt_param(name, prm):
    if prm.default is inspect.Parameter.empty:
        return name
    return "%s=%s" % (name, _fmt_default(prm.default))


def signature_text(name, func):
    """按文档里的写法生成签名（不写类型注解，保留 keyword-only 的 ``*``）。"""
    sig = inspect.signature(func)
    lines = ["eazy_data_viz.%s(" % name]
    body = []
    star_done = False
    for pname, prm in sig.parameters.items():
        if pname in ("self", "cls"):
            continue
        if prm.kind is inspect.Parameter.VAR_KEYWORD:
            continue
        if prm.kind is inspect.Parameter.VAR_POSITIONAL:
            body.append("    *%s," % pname)
            star_done = True
            continue
        if prm.kind is inspect.Parameter.KEYWORD_ONLY and not star_done:
            body.append("    *,")
            star_done = True
        body.append("    %s," % _fmt_param(pname, prm))
    lines.extend(body)
    lines.append(") -> Chart")
    return "\n".join(lines)


def replace_block(text, new_block):
    """替换 ``## 函数签名`` 之后的第一个 ``` 代码块；找不到返回 None。"""
    i = text.find(HEADING)
    if i < 0:
        return None
    start = text.find("```", i)
    if start < 0:
        return None
    nl = text.find("\n", start)
    if nl < 0:
        return None
    end = text.find("```", nl)
    if end < 0:
        return None
    return text[:nl + 1] + new_block + "\n" + text[end:]


def current_block(text):
    i = text.find(HEADING)
    if i < 0:
        return None
    start = text.find("```", i)
    nl = text.find("\n", start)
    end = text.find("```", nl)
    if start < 0 or nl < 0 or end < 0:
        return None
    return text[nl + 1:end].rstrip("\n")


def main(argv):
    check_only = "--check" in argv
    verbose = "--verbose" in argv
    sys.path.insert(0, ROOT)
    import eazy_data_viz as edv

    changed, missing, skipped = [], [], []
    for name in getattr(edv, "__all__", []):
        obj = getattr(edv, name, None)
        if not callable(obj) or inspect.isclass(obj):
            continue
        path = os.path.join(API_DIR, name + ".md")
        if not os.path.isfile(path):
            missing.append(name)
            continue
        with open(path, encoding="utf-8", newline="") as fh:
            raw = fh.read()
        crlf = "\r\n" in raw
        text = raw.replace("\r\n", "\n")
        want = signature_text(name, obj)
        got = current_block(text)
        if got is None:
            skipped.append(name)
            continue
        if got.strip() == want.strip():
            if verbose:
                print("  ok      %s" % name)
            continue
        changed.append(name)
        if check_only:
            print("  drift   %s" % name)
            continue
        new_text = replace_block(text, want)
        out = new_text.replace("\n", "\r\n") if crlf else new_text
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(out)
        print("  fixed   %s" % name)

    print("\n同步 %d 个 / 无签名块 %d 个 / 无文档 %d 个"
          % (len(changed), len(skipped), len(missing)))
    if check_only and changed:
        print("签名块与代码不一致：请运行 python tools/sync_doc_signatures.py")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
