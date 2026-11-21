# -*- coding: utf-8 -*-
"""自由排列布局（1.5 新增）。

看板默认是「等宽网格」（``cols=2`` 之类）。1.5 起可以自定义排列，有两种模式：

**模式 A：方向 + 每行/列图表数**（``direction`` + ``layout``）

>>> eazy_data_viz.show(c1, c2, c3, c4, layout=[1, 3], direction="h")
>>> eazy_data_viz.show(c1, c2, c3, layout=[1, 2], direction="v")

``direction="h"``（从左到右）：``[1, 3]`` 表示第一列 1 张图、第二列 3 张图；
``direction="v"``（从上到下）：``[1, 2]`` 表示第一行 1 张图、第二行 2 张图。

**模式 B：先申请网格，再按顺序占位**（``grid`` + ``layout``）

>>> eazy_data_viz.show(a, b, grid=(3, 3), layout=[[2, 2], [1, 1]])

``layout`` 里第 i 个 ``[行, 列]`` 是第 i 张图要占的空间。占位顺序是「从左到右、
从上到下找第一个放得下的空位」。上例中 ``[2,2]`` 先占满左上 2×2，``[1,1]``
自然落在它的右上角（第 1 行第 3 列）。放不下会直接 ``ValueError``。
"""

from __future__ import annotations

__all__ = [
    "parse_layout",
    "normalize_direction",
    "layout_height",
    "layout_summary",
    "GAP",
]

#: 卡片间距（与 CSS 里的 ``gap:16px`` 保持一致，用于估算高度）。
GAP = 16

_H_ALIASES = {
    "h", "horiz", "horizontal", "lr", "l-r", "left-to-right", "leftright",
    "left", "col", "cols", "column", "columns", "x", "横", "横向", "左右",
    "从左到右", "左到右",
}
_V_ALIASES = {
    "v", "vert", "vertical", "tb", "t-b", "top-to-bottom", "topdown",
    "top", "row", "rows", "y", "竖", "纵向", "上下", "从上到下", "上到下",
}


def normalize_direction(direction):
    """把方向参数归一化成 ``"h"``（从左到右）/ ``"v"``（从上到下）。"""
    if direction is None:
        return "h"
    if not isinstance(direction, str):
        raise ValueError(
            'direction 只支持 "h"（从左到右）/ "v"（从上到下），收到 %r'
            % (direction,)
        )
    key = direction.strip().lower().replace("_", "-").replace(" ", "")
    if key in _H_ALIASES:
        return "h"
    if key in _V_ALIASES:
        return "v"
    raise ValueError(
        'direction 只支持 "h"（从左到右）/ "v"（从上到下），收到 %r' % (direction,)
    )


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_span(value):
    return (
        isinstance(value, (list, tuple))
        and len(value) == 2
        and _is_int(value[0])
        and _is_int(value[1])
    )


def _parse_grid(grid):
    """``(3, 3)`` / ``[3, 3]`` / ``"3x3"`` / ``3`` → ``(3, 3)``。"""
    if grid is None:
        raise ValueError(
            "网格排列需要先申请行列：grid=(行, 列)，例如 grid=(3, 3)。"
        )
    if isinstance(grid, str):
        text = grid.strip().lower().replace("×", "x").replace("*", "x")
        parts = [p for p in text.split("x") if p.strip()]
        if len(parts) != 2:
            raise ValueError('grid 需要写成 (行, 列) 或 "3x3"，收到 %r' % (grid,))
        try:
            grid = (int(parts[0]), int(parts[1]))
        except ValueError:
            raise ValueError('grid 需要写成 (行, 列) 或 "3x3"，收到 %r' % (grid,))
    elif _is_int(grid):
        grid = (grid, grid)
    elif isinstance(grid, (list, tuple)) and len(grid) == 2:
        grid = (grid[0], grid[1])
    else:
        raise ValueError("grid 需要写成 (行, 列)，例如 grid=(3, 3)，收到 %r" % (grid,))
    rows, cols = grid
    if not _is_int(rows) or not _is_int(cols) or rows < 1 or cols < 1:
        raise ValueError("grid 的行数和列数都必须是 >=1 的整数，收到 %r" % (grid,))
    return int(rows), int(cols)


def parse_layout(n, layout=None, direction=None, grid=None):
    """解析自由排列参数。

    参数
    ----
    n : int
        图表数量。
    layout : list or dict or None
        - ``[1, 3]``：每列/行图表数（配合 ``direction``）；
        - ``[[2, 2], [1, 1]]``：每张图占用的 ``[行, 列]``（配合 ``grid``）；
        - dict：``{"mode": "flow"/"span", "direction": ..., "counts": [...],
          "grid": (3, 3), "spans": [[2, 2], [1, 1]]}``。
    direction : str
        ``"h"`` / ``"v"``（也接受 "horizontal" / "vertical" / "从左到右" 等）。
    grid : tuple or str
        网格行列，例如 ``(3, 3)`` / ``"3x3"``。

    返回
    ----
    dict or None
        ``None`` 表示不启用自由排列（按 ``cols`` 等宽网格）。启用时返回::

            {"mode": "flow" | "span",
             "direction": "h" | "v",
             "counts": [1, 3],          # flow 模式
             "grid": (3, 3),            # span 模式
             "spans": [[2, 2], ...],    # span 模式
             "cells": [(row, col, row_span, col_span), ...],  # 第 i 张图的位置
             "cols": 2, "rows": 3,      # 布局占用的总列数 / 总行数
             "slots": 4}
    """
    if not _is_int(n) or n < 1:
        raise ValueError("图表数量必须是 >=1 的整数，收到 %r" % (n,))

    if layout is None:
        if grid is not None:
            raise ValueError(
                "grid 需要配合 layout 一起使用：grid=(行, 列) 申请网格，"
                "layout=[[行, 列], ...] 声明每张图占用的空间。"
            )
        if direction is not None:
            raise ValueError(
                "direction 需要配合 layout 一起使用：layout=[每列/行图表数]，"
                "例如 layout=[1, 3], direction=\"h\"。"
            )
        return None

    mode = None
    if isinstance(layout, dict):
        cfg = dict(layout)
        direction = cfg.pop("direction", direction)
        grid = cfg.pop("grid", grid)
        raw_mode = cfg.pop("mode", cfg.pop("type", None))
        counts = cfg.pop("counts", None)
        spans = cfg.pop("spans", None)
        inner = cfg.pop("layout", None)
        if cfg:
            raise ValueError(
                "layout 字典里有无法识别的键：%s（只支持 mode / direction / "
                "counts / spans / grid / layout）" % ", ".join(sorted(cfg))
            )
        if raw_mode is not None:
            key = str(raw_mode).strip().lower()
            if key in ("flow", "direction", "counts", "auto"):
                mode = "flow"
            elif key in ("span", "grid", "blocks", "tile"):
                mode = "span"
            else:
                raise ValueError(
                    'layout 的 mode 只支持 "flow"（方向+数量）/ "span"（网格占位），'
                    "收到 %r" % (raw_mode,)
                )
        if inner is not None:
            if counts is not None or spans is not None:
                raise ValueError(
                    "layout 字典里的 layout 不能和 counts / spans 同时出现。"
                )
            layout = inner
        elif counts is not None:
            layout = counts
        elif spans is not None:
            layout = spans
        else:
            raise ValueError("layout 字典需要包含 counts 或 spans。")

    if isinstance(layout, (str, bytes)) or not isinstance(layout, (list, tuple)):
        raise ValueError(
            "layout 需要是 [每列/行图表数]（如 [1, 3]）或 "
            "[[行, 列], ...]（如 [[2, 2], [1, 1]]），收到 %r" % (layout,)
        )
    items = list(layout)
    if not items:
        raise ValueError("layout 不能是空列表。")

    if all(_is_int(x) for x in items):
        inferred = "flow"
    elif all(_is_span(x) for x in items):
        inferred = "span"
    else:
        raise ValueError(
            "layout 需要统一是整数（每列/行图表数）或 [行, 列] 组合，收到 %r"
            % (layout,)
        )
    if mode is not None and mode != inferred:
        raise ValueError(
            "layout 的形式（%s）和 mode=%r 不一致。" % (inferred, mode)
        )
    mode = inferred

    if mode == "flow":
        direction = normalize_direction(direction)
        counts = [int(x) for x in items]
        for i, c in enumerate(counts):
            if c < 1:
                raise ValueError(
                    "layout 里第 %d 个每行/列图表数需要是正整数，收到 %r"
                    % (i + 1, c)
                )
        total = sum(counts)
        if total < n:
            raise ValueError(
                "layout=%r 只提供了 %d 个位置，但有 %d 张图。"
                % (counts, total, n)
            )
        cells = []
        if direction == "h":
            for col, cnt in enumerate(counts):
                for row in range(cnt):
                    cells.append((row, col, 1, 1))
        else:
            for row, cnt in enumerate(counts):
                for col in range(cnt):
                    cells.append((row, col, 1, 1))
        cells = cells[:n]
        return {
            "mode": "flow",
            "direction": direction,
            "counts": counts,
            "grid": None,
            "spans": None,
            "cells": cells,
            "cols": len(counts) if direction == "h" else max(counts),
            "rows": max(counts) if direction == "h" else len(counts),
            "slots": total,
        }

    # ---- span：先申请网格，再从左到右、从上到下占位 -------------------
    rows, cols = _parse_grid(grid)
    spans = [(int(r), int(c)) for r, c in items]
    if len(spans) != n:
        raise ValueError(
            "网格排列需要为每张图声明 [行, 列] 占用：共 %d 张图，"
            "收到 %d 个占位声明。" % (n, len(spans))
        )
    for i, (row_span, col_span) in enumerate(spans):
        if row_span < 1 or col_span < 1:
            raise ValueError(
                "第 %d 张图申请的空间 %r 非法：行列都必须 >=1。"
                % (i + 1, [row_span, col_span])
            )
        if row_span > rows or col_span > cols:
            raise ValueError(
                "第 %d 张图申请 %d×%d 的空间，超过网格 %d×%d。"
                % (i + 1, row_span, col_span, rows, cols)
            )

    occupied = [[False] * cols for _ in range(rows)]
    cells = []
    for i, (row_span, col_span) in enumerate(spans):
        spot = None
        for r in range(rows - row_span + 1):
            for c in range(cols - col_span + 1):
                free = True
                for dr in range(row_span):
                    for dc in range(col_span):
                        if occupied[r + dr][c + dc]:
                            free = False
                            break
                    if not free:
                        break
                if free:
                    spot = (r, c)
                    break
            if spot is not None:
                break
        if spot is None:
            used = sum(1 for line in occupied for cell in line if cell)
            raise ValueError(
                "第 %d 张图申请 %d×%d 的空间放不下：%d×%d 网格已经占用了 "
                "%d 格，剩下的空位放不下这个尺寸。"
                % (i + 1, row_span, col_span, rows, cols, used)
            )
        r, c = spot
        for dr in range(row_span):
            for dc in range(col_span):
                occupied[r + dr][c + dc] = True
        cells.append((r, c, row_span, col_span))

    used_rows = max(r + rs for r, _c, rs, _cs in cells)
    return {
        "mode": "span",
        "direction": "h",
        "counts": None,
        "grid": (rows, cols),
        "spans": [list(s) for s in spans],
        "cells": cells,
        "cols": cols,
        "rows": used_rows,
        "slots": rows * cols,
    }


def layout_height(layout, heights, gap=GAP):
    """按布局估算内容区高度（不含 page padding / header）。

    ``heights`` 是每张图的卡片高度（与 ``cells`` 一一对应）。
    """
    if not layout:
        return 0
    cells = layout["cells"]
    if len(heights) < len(cells):  # pragma: no cover - 防御式
        heights = list(heights) + [380] * (len(cells) - len(heights))
    if layout["mode"] == "flow":
        if layout["direction"] == "h":
            per_col = {}
            for (row, col, _rs, _cs), h in zip(cells, heights):
                per_col.setdefault(col, {})[row] = h
            total = 0
            for grouped in per_col.values():
                total = max(total, sum(grouped.values()) + gap * (len(grouped) - 1))
            return total
        per_row = {}
        for (row, col, _rs, _cs), h in zip(cells, heights):
            per_row.setdefault(row, {})[col] = h
        total = 0
        for grouped in per_row.values():
            total += max(grouped.values())
        return total + gap * max(0, len(per_row) - 1)

    rows, _boxes = grid_row_heights(layout, heights, gap)
    return sum(rows) + gap * max(0, len(rows) - 1)


def grid_row_heights(layout, heights, gap=GAP):
    """网格占位模式的每行高度：让所有卡片正好铺满一个矩形。

    返回 ``(rows, boxes)``：``rows`` 是每行的像素高度，``boxes`` 是每张卡片
    最终的外框高度（跨行卡片 = 它跨过的行高之和 + 行间距）。

    算法：先用单行卡片顶住各自的行；再从跨行卡片里找出「自然高度大于
    已分配高度」的，把差额加进它跨的**最后一行**，反复迭代到稳定。
    行高只增不减，所以每张卡片都至少和它的自然高度一样高，整个网格
    不会出现某张卡片高出同行的情况。
    """
    if not layout or layout.get("mode") != "span":
        return [], []
    cells = layout["cells"]
    if len(heights) < len(cells):  # pragma: no cover - 防御式
        heights = list(heights) + [380] * (len(cells) - len(heights))
    used = max(row + row_span for row, _col, row_span, _col_span in cells)
    rows = [0.0] * used
    for i, (row, _col, row_span, _col_span) in enumerate(cells):
        if row_span <= 1:
            rows[row] = max(rows[row], float(heights[i]))
    for _ in range(len(cells) * 2 + 2):
        changed = False
        for i, (row, _col, row_span, _col_span) in enumerate(cells):
            if row_span <= 1:
                continue
            have = sum(rows[row:row + row_span]) + gap * (row_span - 1)
            need = float(heights[i]) - have
            if need > 0.5:
                rows[row + row_span - 1] += need
                changed = True
        if not changed:
            break
    boxes = [
        sum(rows[row:row + row_span]) + gap * (row_span - 1)
        for row, _col, row_span, _col_span in cells
    ]
    return rows, boxes


def layout_summary(layout):
    """布局的一句话描述（写进页面/日志，便于排查）。"""
    if not layout:
        return ""
    if layout["mode"] == "flow":
        arrow = "从左到右" if layout["direction"] == "h" else "从上到下"
        unit = "列" if layout["direction"] == "h" else "行"
        parts = ["第%d%s %d 张" % (i + 1, unit, c) for i, c in enumerate(layout["counts"])]
        return "%s：%s" % (arrow, "、".join(parts))
    rows, cols = layout["grid"]
    parts = []
    for i, (r, c, rs, cs) in enumerate(layout["cells"]):
        parts.append("#%d (%d,%d) %d×%d" % (i + 1, r + 1, c + 1, rs, cs))
    return "网格 %d×%d：%s" % (rows, cols, "；".join(parts))
