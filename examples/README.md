# 示例

全部示例都可直接运行（无需 `pip install`，脚本会把仓库根目录加入 `sys.path`）：

```bash
python examples/quickstart.py     # 3 个最小场景：单图 / 看板 / Streamlit
python examples/cockpit.py        # 经营驾驶舱：KPI + 趋势 + 结构 + 排名 + 明细
python examples/kpi_cards.py      # KPI 卡片全用法（目标、走势、反向指标、联动重算）
python examples/palettes.py       # 7 套配色库同屏对比
python examples/drill_link.py     # 下钻 + 联动
streamlit run examples/streamlit_app.py   # Streamlit 内嵌
```

生成的 HTML 在 `examples/output/`（已加入 `.gitignore`）。

| 文件 | 内容 |
| --- | --- |
| `quickstart.py` | 单图 → HTML、下钻+联动看板、Streamlit payload |
| `cockpit.py` | 完整经营驾驶舱（14 张卡片，2 列布局） |
| `kpi_cards.py` | 7 种 KPI 卡片写法 |
| `palettes.py` | google/antd/tableau/carbon/echarts/morandi/tailwind |
| `drill_link.py` | 三级下钻、四图联动、KPI 联动重算 |
| `streamlit_app.py` | `st.components.v1.html` 嵌入 + 侧栏控件 |

想直接看效果，也可以打开仓库根目录的 `gallery.html`：64 张卡片、45 种图表，
每张卡片右上角「代码」按钮会展开生成该图的完整 Python 代码。
