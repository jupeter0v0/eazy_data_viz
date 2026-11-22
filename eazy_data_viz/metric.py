"""指标切换（1.6）：一个角色映射多列，点 KPI 卡片就换全局指标。

用法
----
>>> import eazy_data_viz as edv
>>> amount = edv.switch(sale="金额", qty="数量", balance="余额")
>>> edv.show(
...     edv.kpi(df, value=amount, label="销售额", metric="sale"),
...     edv.bar(df, x="月份", y=amount),
... )

``edv.switch(...)`` 返回一个 :class:`Switch` —— 它本身是个有序字典
「指标名 → 列名」，传给任何接受角色列名的参数（``y`` / ``value`` / ``size`` /
``spark`` / ``names`` …）都可以：

* 第一次出现的指标（这里是 ``sale``）是**默认指标**，Python 侧先用它出图；
* 同一个看板里，带 ``metric="sale"`` 的 KPI 卡片被点击时，浏览器把所有用到
  这个 switch 的图表切到对应的列，**不触发 Python 重算**；
* 数据准备时会把 switch 里所有列一起带上，所以切换是纯前端的。

注意：switch 里的列必须是同一类（都数值 / 都文本），否则切换后类型对不上。
"""

from __future__ import annotations


class Switch(dict):
    """「指标名 → 列名」的有序映射，可传给任何角色参数。"""

    def __init__(self, mapping: dict, label: str | None = None):
        super().__init__(mapping)
        self.label = label

    @property
    def default_name(self) -> str:
        """默认指标名（第一个键）。"""
        return next(iter(self))

    @property
    def default_column(self) -> str:
        """默认指标对应的列名。"""
        return self[self.default_name]

    @property
    def columns(self) -> list:
        """全部列名（按声明顺序，可能有重复列）。"""
        out = []
        for col in self.values():
            if col not in out:
                out.append(col)
        return out

    @property
    def names(self) -> list:
        """全部指标名。"""
        return list(self.keys())

    def __repr__(self) -> str:  # pragma: no cover - 只影响交互式显示
        body = ", ".join("%s=%r" % (k, v) for k, v in self.items())
        return "switch(%s)" % body


def switch(**kwargs) -> Switch:
    """声明「指标名 → 列名」的切换映射。

    参数
    ----
    **kwargs
        指标名 = 列名，例如 ``switch(sale="金额", qty="数量")``。
        至少一个；指标名不能为空；列名必须是字符串。

    返回
    ----
    Switch
        有序映射，可传给 ``y`` / ``value`` / ``size`` / ``spark`` 等角色参数。

    报错
    ----
    ``ValueError: edv.switch 至少需要一个指标，例如 edv.switch(sale="金额", qty="数量")。``
    ``ValueError: edv.switch 的指标名不能是空字符串。``
    ``ValueError: edv.switch[%r] 需要是列名字符串，收到 %r。``
    """
    if not kwargs:
        raise ValueError(
            'edv.switch 至少需要一个指标，例如 edv.switch(sale="金额", qty="数量")。'
        )
    mapping = {}
    for name, col in kwargs.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("edv.switch 的指标名不能是空字符串。")
        if not isinstance(col, str) or not col.strip():
            raise ValueError("edv.switch[%r] 需要是列名字符串，收到 %r。" % (name, col))
        mapping[name.strip()] = col
    return Switch(mapping)


def is_switch(value) -> bool:
    """判断某个角色参数是不是 switch 映射。"""
    return isinstance(value, Switch)


def resolve_roles(roles: dict) -> tuple:
    """把 roles 里的 Switch 解析成默认列，返回 ``(roles, switch_map)``。

    ``switch_map`` 形如 ``{"y": {"sale": "金额", "qty": "数量"}}``，会写进 spec，
    供浏览器在切换指标时使用。
    """
    switch_map = {}
    plain = {}
    for role, value in (roles or {}).items():
        if isinstance(value, Switch):
            if not value:
                raise ValueError(
                    "edv.switch 不能是空的：至少给一个指标，"
                    '例如 edv.switch(sale="金额", qty="数量")。'
                )
            switch_map[role] = dict(value)
            plain[role] = value.default_column
        elif isinstance(value, (list, tuple)) and any(isinstance(v, Switch) for v in value):
            raise ValueError(
                "switch 不能出现在多列参数里（例如 path=[...] / drill=[...]）："
                "一个角色只能切换单列，需要多列请拆成两个参数。"
            )
        else:
            plain[role] = value
    return plain, switch_map


def switch_metrics(switch_map: dict) -> list:
    """收集 switch_map 里出现过的全部指标名（按声明顺序）。"""
    out = []
    for mapping in (switch_map or {}).values():
        for name in mapping:
            if name not in out:
                out.append(name)
    return out


def switch_columns(switch_map: dict) -> list:
    """收集 switch_map 里出现过的全部列名（按声明顺序）。"""
    out = []
    for mapping in (switch_map or {}).values():
        for col in mapping.values():
            if col not in out:
                out.append(col)
    return out
