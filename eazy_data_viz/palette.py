"""配色库（palette）注册表。

每个 palette 是一组「分类色」序列 + 适用场景说明；渲染时由前端
``eazy.js`` 派生出浅色 / 深色主题（深色是把颜色往白里提亮）。

用法::

    import eazy_data_viz
    eazy_data_viz.set_palette("tableau")          # 全局默认（之后画的图都用它）
    eazy_data_viz.palettes()                      # 列出全部配色
    eazy_data_viz.bar(df, x="大区", y="销售额").palette("carbon")   # 单图覆盖
    eazy_data_viz.dashboard(c1, c2, palette="antd").save("dash.html")  # 单页覆盖
"""

COLOR_PALETTES = {
    "google": {
        "label": "Google Material 3",
        "desc": "谷歌产品线配色（Google Blue 为主），干净、品牌感强，适合大多数经营看板。",
        "best_for": "通用 / 公司经营驾驶舱默认",
        "colors": [
            "#1a73e8", "#188038", "#f9ab00", "#d93025", "#9334e6",
            "#12b5cb", "#fa7b17", "#e52592", "#3c4043", "#795548",
        ],
    },
    "antd": {
        "label": "Ant Design",
        "desc": "蚂蚁 Ant Design 5 的默认色板，蓝紫为主、饱和度略高，企业后台最常见。",
        "best_for": "中后台 / 业务报表",
        "colors": [
            "#1677ff", "#52c41a", "#faad14", "#ff4d4f", "#722ed1",
            "#13c2c2", "#fa8c16", "#eb2f96", "#2f54eb", "#a0d911",
        ],
    },
    "tableau": {
        "label": "Tableau 10",
        "desc": "Tableau 默认十色，明度层次分明，多系列折线/散点分组可读性极好。",
        "best_for": "多系列对比 / BI 分析图",
        "colors": [
            "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
            "#edc949", "#af7aa1", "#ff9da7", "#9c755f", "#bab0ab",
        ],
    },
    "carbon": {
        "label": "IBM Carbon",
        "desc": "IBM Carbon Design 的分类色，冷色偏多、对比强，适合深色大屏与数据密集型看板。",
        "best_for": "深色大屏 / 技术运营",
        "colors": [
            "#6929c4", "#1192e8", "#005d5d", "#9f1853", "#fa4d56",
            "#570408", "#198038", "#002d9c", "#ee538b", "#b28600",
        ],
    },
    "echarts": {
        "label": "ECharts 默认",
        "desc": "ECharts 官方默认色板，国内报表里认知度最高，几乎不用解释。",
        "best_for": "兼容既有 ECharts 报表",
        "colors": [
            "#5470c6", "#91cc75", "#fac858", "#ee6666", "#73c0de",
            "#3ba272", "#fc8452", "#9a60b4", "#ea7ccc", "#48b3bd",
        ],
    },
    "morandi": {
        "label": "莫兰迪（低饱和）",
        "desc": "低饱和灰调色板，柔和、彼此不抢眼，适合给老板看的汇报型看板。",
        "best_for": "汇报 / 印刷 / 弱对比大屏",
        "colors": [
            "#8fa3b0", "#b7a89a", "#a8b8a0", "#c4a49a", "#9fa8c4",
            "#b6a8bd", "#93b0aa", "#cbbfa7", "#a9a9b0", "#d0b8ac",
        ],
    },
    "tailwind": {
        "label": "Tailwind / Flowbite",
        "desc": "现代 Web 产品常用的 Tailwind 色板，明亮活泼，适合面向 C 端的增长看板。",
        "best_for": "产品增长 / 运营看板",
        "colors": [
            "#3f83f8", "#0e9f6e", "#faca15", "#f05252", "#9061f9",
            "#16bdca", "#ff8a4c", "#e74694", "#6b7280", "#31c48d",
        ],
    },
}

DEFAULT_PALETTE = "google"

_current = {"name": DEFAULT_PALETTE}


def names():
    """全部配色名（按注册顺序）。"""
    return list(COLOR_PALETTES.keys())


def check(name):
    """校验配色名，返回规范化后的名字。"""
    if name is None or name == "":
        return _current["name"]
    if name not in COLOR_PALETTES:
        raise ValueError(
            "未知配色 %r，可选：%s" % (name, "、".join(names()))
        )
    return name


def set_default(name):
    """设置进程级默认配色（之后创建的图都用它）。"""
    _current["name"] = check(name)
    return _current["name"]


def current():
    """当前默认配色名。"""
    return _current["name"]


def get(name=None):
    """取一个配色的完整信息（dict）。"""
    return dict(COLOR_PALETTES[check(name)], name=check(name))


def listing():
    """给文档 / 界面用的配色清单。"""
    out = []
    for n in names():
        info = COLOR_PALETTES[n]
        out.append({
            "name": n,
            "label": info["label"],
            "desc": info["desc"],
            "best_for": info["best_for"],
            "colors": list(info["colors"]),
        })
    return out
