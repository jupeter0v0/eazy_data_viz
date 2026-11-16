# -*- coding: utf-8 -*-
"""统计仓库有效行数（排除 .git / build / dist / __pycache__ / 输出产物）。

用法::

    python tools/count_lines.py            # 总表
    python tools/count_lines.py --files    # 按文件明细（前 40 名）
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUDE_DIRS = {".git", "build", "dist", "__pycache__", ".venv", ".venv314",
                "output", "tmp", "node_modules", ".egg-info"}
EXCLUDE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".whl", ".gz", ".zip", ".pdf"}
KEEP_EXT = {".py", ".js", ".md", ".html", ".json", ".txt", ".toml", ".cfg", ".in",
            ".yml", ".yaml", ".css", ".sh", ""}
GROUP_ORDER = ["Python", "JavaScript", "Markdown", "HTML", "JSON", "其它"]
GROUP_OF = {".py": "Python", ".js": "JavaScript", ".md": "Markdown",
            ".html": "HTML", ".json": "JSON"}


def walk(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in EXCLUDE_DIRS and not d.endswith(".egg-info")]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in EXCLUDE_EXT:
                continue
            if ext and ext not in KEEP_EXT:
                continue
            yield os.path.join(dirpath, fn)


def count_file(path):
    try:
        with open(path, "rb") as f:
            return f.read().count(b"\n") + (1 if f.read(0) else 0), 0
    except OSError:
        return 0, 1


def main(argv):
    show_files = "--files" in argv
    groups = {g: [0, 0] for g in GROUP_ORDER}
    files = []
    for path in walk(ROOT):
        ext = os.path.splitext(path)[1].lower()
        group = GROUP_OF.get(ext, "其它")
        try:
            with open(path, "rb") as f:
                data = f.read()
            n = data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)
        except OSError:
            continue
        groups[group][0] += 1
        groups[group][1] += n
        files.append((n, os.path.relpath(path, ROOT)))

    total_files = sum(v[0] for v in groups.values())
    total_lines = sum(v[1] for v in groups.values())
    print("eazy_data_viz 仓库行数统计  (root=%s)" % ROOT)
    print("-" * 56)
    for g in GROUP_ORDER:
        cnt, lines = groups[g]
        if cnt:
            print("%-12s %5d 个文件   %8d 行" % (g, cnt, lines))
    print("-" * 56)
    print("%-12s %5d 个文件   %8d 行" % ("合计", total_files, total_lines))
    if show_files:
        print("\n行数最多的 40 个文件：")
        for n, rel in sorted(files, reverse=True)[:40]:
            print("%8d  %s" % (n, rel))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
