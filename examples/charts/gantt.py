# -*- coding: utf-8 -*-
"""gantt（甘特图）完整示例：5 个用法，覆盖最简/典型/进阶参数/边界/联动/配色。

运行方式（在仓库根目录）：

    cd F:/deepseek/eazy_data_viz
    set PYTHONPATH=.
    set PYTHONIOENCODING=utf-8
    python examples/charts/gantt.py

输出：examples/output/gantt_*.html（每个文件都是可离线打开的独立页面）。
"""

import os
import sys

# 直接运行本文件时，sys.path[0] 是 examples/charts；该目录里的 calendar.py
# 会遮蔽标准库 calendar，导致 pandas 导入失败。这里在导入 pandas 前移除它。
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path
              if os.path.abspath(p or os.getcwd()) != _HERE]

import pandas as pd

import eazy_data_viz as edv


def main():
    df = edv.sample_df()
    print("数据：%d 行 × %d 列" % (df.shape[0], df.shape[1]))


    # ---- 示例 1：最简：手工任务表 ----
    tasks = pd.DataFrame({
        "任务": ["数据清洗", "指标对齐", "图表开发", "联调", "上线"],
        "开始": pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-15", "2024-02-01", "2024-02-12"]),
        "结束": pd.to_datetime(["2024-01-12", "2024-01-20", "2024-02-05", "2024-02-14", "2024-02-20"]),
    })
    chart = edv.gantt(tasks, task="任务", start="开始", end="结束")
    chart.save("examples/output/gantt_1.html")

    # ---- 示例 2：典型：按负责人分组着色 ----
    tasks = pd.DataFrame({
        "任务": ["数据清洗", "指标对齐", "图表开发", "联调", "上线"],
        "开始": pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-15", "2024-02-01", "2024-02-12"]),
        "结束": pd.to_datetime(["2024-01-12", "2024-01-20", "2024-02-05", "2024-02-14", "2024-02-20"]),
        "负责人": ["张三", "李四", "张三", "王五", "王五"],
    })
    chart = edv.gantt(
        tasks,
        task="任务",
        start="开始",
        end="结束",
        color="负责人",
        title="项目排期",
        height=420,
    )
    chart.save("examples/output/gantt_2.html")

    # ---- 示例 3：进阶：从明细数据汇总任务区间 ----
    tasks = (
        df.groupby(["大区", "产品"], as_index=False)
          .agg(开始=("日期", "min"), 结束=("日期", "max"))
          .rename(columns={"产品": "任务"})
    )
    chart = edv.gantt(tasks, task="任务", start="开始", end="结束", color="大区", height=520)
    chart.save("examples/output/gantt_3.html")

    # ---- 示例 4：深色主题、货币/时间格式与标签开关 ----
    tasks = pd.DataFrame({
        "任务": ["需求评审", "设计", "开发", "测试", "发布"],
        "开始": pd.to_datetime(["2024-03-01", "2024-03-05", "2024-03-12", "2024-04-01", "2024-04-15"]),
        "结束": pd.to_datetime(["2024-03-06", "2024-03-14", "2024-04-02", "2024-04-16", "2024-04-20"]),
        "阶段": ["前期", "前期", "中期", "后期", "后期"],
    })
    a = edv.gantt(tasks, task="任务", start="开始", end="结束", color="阶段",
                  theme="dark", labels=True)
    a.save("examples/output/gantt_4.html")
    b = edv.gantt(tasks, task="任务", start="开始", end="结束", color="阶段",
                  theme="dark", labels=False)
    b.save("examples/output/gantt_5.html")

    # ---- 示例 5：联动：点击时间条过滤明细 ----
    tasks = pd.DataFrame({
        "任务": ["数据清洗", "指标对齐", "图表开发", "联调", "上线"],
        "开始": pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-15", "2024-02-01", "2024-02-12"]),
        "结束": pd.to_datetime(["2024-01-12", "2024-01-20", "2024-02-05", "2024-02-14", "2024-02-20"]),
        "负责人": ["张三", "李四", "张三", "王五", "王五"],
    })
    g = edv.gantt(tasks, task="任务", start="开始", end="结束", color="负责人", link="gt1")
    tbl = edv.table(tasks, columns=["任务", "负责人", "开始", "结束"], link="gt1", limit=20)
    edv.dashboard(g, tbl, title="甘特图联动", cols=2).save("examples/output/gantt_6.html")

if __name__ == "__main__":
    main()
    print("OK gantt")
