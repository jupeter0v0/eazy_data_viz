# 销售经营分析看板（Streamlit Demo）

一个可以直接跑的 Streamlit 看板示例：KPI、月度趋势、大区堆叠、中国地图、TOP 客户、
回款双轴、订单类型占比，加一张中国式报表（序号 / 合计 / 数据条 / 斑马纹）。

默认走 **components v2**（不走 iframe），点击图表默认 **0 rerun**；侧栏勾上
「点图回传 Python」才会把点击事件回传脚本。

## 快速开始

```bash
pip install -e ../..            # 或 pip install eazy_data_viz
cd examples/streamlit_sales_demo
python -m streamlit run app.py
```

仓库里已经带了一份抽样数据 `data/sales_demo.csv`（约 2.4 万行、5 MB），
不装原始 ERP 导出也能直接跑。

## 换成你自己的数据

`prepare_data.py` 负责把用友/ERP 导出的「全是主键」的明细翻译成可读中文名：

```bash
python prepare_data.py --src /path/to/你的导出.csv --rows 24000
```

- `--src`：原始导出（需要包含 `SODATE / PURCHASEORDER / CUSTOMER / MATERIAL /
  MONEY_DE / MONEY_REC / SO_DEPTID / SO_PSNDOC / SO_ORDERTYPE / PK_TRADETYPE /
  SRC_BILLTYPENAME / QUANTITY_DE / NOTAX_DE1` 等列）。
- `--rows`：抽多少行（默认 40000，演示用 24000）。
- `--start` / `--end`：日期窗口（默认 2025-01-01 ~ 2026-06-01）。

转换时会做这些事：

| 处理 | 原因 |
| --- | --- |
| 客户 / 产品 / 部门 / 业务员按主键序号生成中文名 | 原始导出只有 `PK_*` 主键，画图没法看 |
| 省份 → 大区显式映射 | 保证地图和堆叠图口径一致 |
| 金额取绝对值 | 导出里的红字退货是负数，会让地图出现负合计 |
| 剔除单笔 > 30 万的大单 | 项目型大单会盖掉月度趋势 |
| 按月等量抽样 | 避免尾部稀疏月份只剩几百行却塞进百万大单 |
| 已回款按 6 成结清 / 4 成分批生成 | 原始数据回款率恒为 100%，应收指标没有可看的 |
| 订单类型按常见分布生成 | 原始码值长尾，直接套名字会得到「样品订单占九成」 |

## 页面结构

| 区块 | 用到的东西 |
| --- | --- |
| KPI 行（4 张卡） | `edv.kpi(...)` + `streamlit_dashboard(cols=4)`，同比按 2026 vs 2025 同期真算 |
| 月度销售趋势 | `edv.line(...).unit("万")`，类目是 `2025-01`，坐标轴自动变「1月」 |
| 大区 × 产品线 | `edv.bar(stack=True, drill=[...])`，点柱子逐级下钻 |
| 各省销售额 | `edv.geo_map("省份", "销售额")` |
| TOP 10 客户 | 先在 pandas 里聚合前 10，再 `bar(horizontal=True)` |
| 大区销售额与回款率 | `edv.combo(bar=..., line=...)` |
| 订单类型占比 | `edv.pie(donut=True)` |
| 销售明细 | `edv.table(total=True, index=True, bar="销售额", height=800)` |

四张图共享 `link="biz"`：点任意一根柱子，其余图跟着过滤，再点一次取消。
这一整套联动都在浏览器里完成，不会触发脚本 rerun。

## 两个容易踩的点

**1. table 是固定高度 + 内部滚动。** 默认 500px 只露十行，`tfoot` 的合计会被
藏在滚动区里。要显示 20 行就给 `edv.table(..., height=800)`，并把组件的
`streamlit_dashboard(..., height=840)` 一起给足。

**2. v2 组件高度按内容自适应。** 折线图不用手动算高度，但 table / 词云这种
固定高度组件需要自己给。

## 性能

2.4 万行、6 张图 + 1 张表，首屏约 1.5s；带上 `on_select` 时每次点击会多一次
脚本 rerun（约 0.3s），不带则没有任何 rerun。数据读取走 `@st.cache_data`，
切换筛选条件只重跑聚合。
