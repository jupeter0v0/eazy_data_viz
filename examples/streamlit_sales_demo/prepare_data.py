# -*- coding: utf-8 -*-
"""把用友导出的销售明细（全是主键 ID）翻译成可读的中文 Demo 数据。

原始导出里客户、物料、部门、业务员都是 ``PK_*`` / 一长串主键，直接画图没有可读性。
本脚本做两件事：

1. **主键 → 可读名称**：确定性映射（同一 ID 每次运行都得到同一个名字），
   客户名按「城市 + 品牌 + 行业」生成，产品按「品类 + 系列 + 编号」生成；
2. **按月份分层抽样**：默认从 2025-01-01 到 2026-11-01 抽 4 万行，
   保证趋势图每个月都有数据，生成的文件可以直接进仓库。

用法::

    python prepare_data.py --src "D:/导出/2025-05-20T09-10_export.csv"
    python prepare_data.py --src ... --rows 60000 --start 2025-01-01 --end 2026-11-01

生成的 ``data/sales_demo.csv`` 已经是中文列名，``app.py`` 直接读它即可，
不需要再跑本脚本（仓库里已经带了一份抽样结果）。
"""

from __future__ import annotations

import argparse
import io
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")

# ---------------------------------------------------------------------------
# 名称素材：城市 / 省份、品牌、行业、产品品类、部门、业务员
# ---------------------------------------------------------------------------

CITIES = [
    ("上海市", "上海市"), ("杭州市", "浙江省"), ("宁波市", "浙江省"), ("苏州市", "江苏省"),
    ("南京市", "江苏省"), ("合肥市", "安徽省"), ("福州市", "福建省"), ("厦门市", "福建省"),
    ("济南市", "山东省"), ("青岛市", "山东省"), ("南昌市", "江西省"),
    ("广州市", "广东省"), ("深圳市", "广东省"), ("东莞市", "广东省"), ("佛山市", "广东省"),
    ("南宁市", "广西"), ("海口市", "海南省"),
    ("北京市", "北京市"), ("天津市", "天津市"), ("石家庄市", "河北省"), ("太原市", "山西省"),
    ("呼和浩特市", "内蒙古"),
    ("武汉市", "湖北省"), ("长沙市", "湖南省"), ("郑州市", "河南省"),
    ("成都市", "四川省"), ("重庆市", "重庆市"), ("昆明市", "云南省"), ("贵阳市", "贵州省"),
    ("西安市", "陕西省"), ("兰州市", "甘肃省"), ("乌鲁木齐市", "新疆"), ("银川市", "宁夏"),
    ("西宁市", "青海省"),
    ("沈阳市", "辽宁省"), ("大连市", "辽宁省"), ("长春市", "吉林省"), ("哈尔滨市", "黑龙江省"),
    ("无锡市", "江苏省"), ("温州市", "浙江省"),
]

BRANDS = [
    "恒信", "华创", "远东", "中泰", "新宇", "天成", "宏图", "瑞达", "金桥", "广联",
    "卓越", "世纪", "鼎盛", "汇通", "银河", "长江", "东方", "南方", "北方", "西部",
    "中原", "海川", "山川", "泰山", "昆仑", "长城", "黄河", "珠江", "湘江", "松江",
    "蓝天", "白云", "星辰", "明月", "朝阳", "晨曦", "春雷", "秋实", "冬阳", "夏禾",
    "万隆", "千禧", "百川", "十方", "一诺", "三分", "四季", "五洲", "六合", "七彩",
    "八方", "九州", "十里", "亿丰", "兆丰", "光谷", "科创", "智造", "精工", "匠心",
    "腾飞", "鹏程", "鸿运", "骏马", "麒麟", "凤凰", "龙腾", "虎跃", "鹰翔", "鲲鹏",
    "松柏", "梅兰", "竹菊", "荷塘", "柳岸", "桃李", "枫林", "榕树", "杉木", "榆林",
    "梧桐", "红杉", "银杏", "香樟", "水杉", "云杉", "白桦", "青松", "翠竹", "紫荆",
    "玉兰", "嘉禾", "嘉华", "和金", "和顺", "安泰", "安康", "康泰", "泰和", "祥和",
]

INDUSTRIES = ["科技有限公司", "智能装备有限公司", "精密制造有限公司", "自动化有限公司",
              "实业有限公司", "贸易有限公司", "机电有限公司", "新材料有限公司"]

CATEGORIES = [
    "工业机器人", "数控机床", "激光设备", "自动化产线", "传动部件", "电气元件",
    "仪器仪表", "切削刀具", "仓储设备", "备品备件", "工装夹具", "检测设备",
]

# 12 个产品大类归并成 5 条产品线：堆叠图的图例最好像素友好，
# 12 个色块会被 ECharts 分页成「1/3」翻页，演示效果差。
PRODUCT_LINE = {
    "工业机器人": "机器人与机床", "数控机床": "机器人与机床",
    "激光设备": "激光与产线", "自动化产线": "激光与产线",
    "电气元件": "电气与仪表", "仪器仪表": "电气与仪表", "检测设备": "电气与仪表",
    "传动部件": "传动与刀具", "切削刀具": "传动与刀具", "工装夹具": "传动与刀具",
    "仓储设备": "仓储与备件", "备品备件": "仓储与备件",
}

SERIES = ["R 系列", "α 系列", "S 系列", "H 系列", "G 系列", "X 系列", "M 系列", "T 系列",
          "P 系列", "C 系列", "V 系列", "Q 系列", "L 系列", "K 系列", "D 系列", "B 系列",
          "N 系列", "F 系列", "W 系列", "Y 系列", "Z 系列", "J 系列", "A 系列", "E 系列"]

REGIONS = ["华东大区", "华南大区", "华北大区", "华中大区", "西南大区", "东北大区"]

# 省份 → 大区：真实 BI 里「大区」就是按省份划分的，这里显式映射，
# 保证地图（省份）和柱图（大区）口径一致。
PROVINCE_REGION = {
    "上海市": "华东大区", "江苏省": "华东大区", "浙江省": "华东大区",
    "安徽省": "华东大区", "福建省": "华东大区", "江西省": "华东大区", "山东省": "华东大区",
    "广东省": "华南大区", "广西": "华南大区", "海南省": "华南大区",
    "北京市": "华北大区", "天津市": "华北大区", "河北省": "华北大区",
    "山西省": "华北大区", "内蒙古": "华北大区",
    "湖北省": "华中大区", "湖南省": "华中大区", "河南省": "华中大区",
    "四川省": "西南大区", "重庆市": "西南大区", "云南省": "西南大区",
    "贵州省": "西南大区", "陕西省": "西南大区", "甘肃省": "西南大区",
    "新疆": "西南大区", "宁夏": "西南大区", "青海省": "西南大区",
    "辽宁省": "东北大区", "吉林省": "东北大区", "黑龙江省": "东北大区",
}
DEPT_TYPES = ["直销部", "渠道部", "大客户部", "电商部", "服务部"]

SURNAMES = list("王李张刘陈杨黄赵吴周徐孙马朱胡郭何高林罗")
GIVEN = ["伟", "芳", "娜", "秀英", "敏", "静", "丽", "强", "磊", "军", "洋", "勇", "艳",
         "杰", "娟", "涛", "明", "超", "霞", "平", "刚", "桂英", "建国", "志强", "海燕",
         "晓东", "文博", "雨欣", "子豪", "梓涵"]

CN_NUM = "一二三四五六七八九十"


def _cn(n: int) -> str:
    if 1 <= n <= len(CN_NUM):
        return CN_NUM[n - 1]
    return str(n)


def _company(idx: int) -> tuple[str, str]:
    """客户主键序号 → (客户名, 省份)。城市 × 品牌 已足够 3600 个不重复组合。"""
    city, province = CITIES[idx % len(CITIES)]
    brand = BRANDS[(idx // len(CITIES)) % len(BRANDS)]
    industry = INDUSTRIES[(idx // (len(CITIES) * len(BRANDS))) % len(INDUSTRIES)]
    return "%s%s%s" % (city[:-1], brand, industry), province


def _product(idx: int) -> tuple[str, str]:
    cat = CATEGORIES[idx % len(CATEGORIES)]
    series = SERIES[(idx // len(CATEGORIES)) % len(SERIES)]
    return "%s %s-%03d" % (cat, series, idx + 101), cat


def _dept(idx: int) -> str:
    region = REGIONS[idx % len(REGIONS)]
    dtype = DEPT_TYPES[(idx // len(REGIONS)) % len(DEPT_TYPES)]
    seq = idx // (len(REGIONS) * len(DEPT_TYPES)) + 1
    return "%s·%s%s部" % (region, dtype[:-1], _cn(seq))


def _person(idx: int) -> str:
    return SURNAMES[idx % len(SURNAMES)] + GIVEN[(idx // len(SURNAMES)) % len(GIVEN)]


def _order_type(idx: int) -> str:
    names = ["标准销售订单", "赊销订单", "样品订单", "补货订单", "退货订单", "服务订单"]
    return names[idx % len(names)]


def _order_type_mix(n: int, rng) -> list[str]:
    """按业务上合理的比例生成订单类型。

    原始导出的 SO_ORDERTYPE 只有 6 个码值，直接按码值顺序套名字会得到
    「样品订单 9 成」这种失真的分布，饼图只剩一块。这里按标准销售为主
    的长尾分布重新生成，重复运行结果一致（固定种子）。
    """
    names = ["标准销售订单", "赊销订单", "补货订单", "样品订单", "服务订单", "退货订单"]
    p = [0.55, 0.22, 0.10, 0.07, 0.04, 0.02]
    return list(rng.choice(names, size=n, p=p))


def _trade_type(idx: int) -> str:
    return ["内销", "外销"][idx % 2]


def _bill_type(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or value == "\\N":
        return "未标记"
    return "发票" if "发票" in value else ("签收用途单" if "签收" in value else value)


COLS = ["SODATE", "PURCHASEORDER", "PK_ORG", "CUSTOMER", "MATERIAL", "SO_DEPTID",
        "SO_PSNDOC", "SO_ORDERTYPE", "PK_TRADETYPE", "SRC_BILLTYPENAME",
        "MONEY_DE", "NOTAX_DE1", "MONEY_REC", "MONEY_BAL", "QUANTITY_DE"]


def _map_column(series: pd.Series, fn) -> list[str]:
    """类别列 → 名称列：按类别序号（排序后的字典序）映射，保证结果稳定。"""
    cats = list(series.cat.categories)
    names = [fn(i) for i in range(len(cats))]
    codes = series.cat.codes.to_numpy()
    return [names[c] if c >= 0 else "" for c in codes]


def build(src: str, rows: int, start: str, end: str) -> pd.DataFrame:
    dtypes = {c: "category" for c in ("PK_ORG", "CUSTOMER", "MATERIAL", "SO_DEPTID",
                                      "SO_PSNDOC", "SO_ORDERTYPE", "PK_TRADETYPE",
                                      "SRC_BILLTYPENAME")}
    dtypes["SODATE"] = "string"
    # 金额/数量列里有 "\N" 空值，不能按 float 解析，先读成字符串再 to_numeric
    df = pd.read_csv(src, usecols=COLS, dtype=dtypes, low_memory=False,
                     na_values=["\\N"], keep_default_na=False)

    df["下单日期"] = pd.to_datetime(df["SODATE"], errors="coerce")
    df = df[df["下单日期"].notna()]
    df = df[(df["下单日期"] >= pd.Timestamp(start)) & (df["下单日期"] < pd.Timestamp(end))]
    if df.empty:
        raise SystemExit("筛选后没有数据：检查 --start / --end 是否与导出文件的日期范围重叠")

    rng = np.random.default_rng(20251117)
    company = [_company(i) for i in range(len(df["CUSTOMER"].cat.categories))]
    material = [_product(i) for i in range(len(df["MATERIAL"].cat.categories))]
    for c in ("MONEY_DE", "NOTAX_DE1", "MONEY_REC", "MONEY_BAL", "QUANTITY_DE"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

    out = pd.DataFrame({
        "订单号": df["PURCHASEORDER"].astype("string").fillna(""),
        "下单日期": df["下单日期"].dt.strftime("%Y-%m-%d"),
        "大区": [PROVINCE_REGION.get(p, "其他大区") for p in
                 (company[c][1] if c >= 0 else "" for c in df["CUSTOMER"].cat.codes.to_numpy())],
        "省份": [company[c][1] if c >= 0 else "" for c in df["CUSTOMER"].cat.codes.to_numpy()],
        "客户": [company[c][0] if c >= 0 else "" for c in df["CUSTOMER"].cat.codes.to_numpy()],
        "产品大类": [material[c][1] if c >= 0 else "" for c in df["MATERIAL"].cat.codes.to_numpy()],
        "产品": [material[c][0] if c >= 0 else "" for c in df["MATERIAL"].cat.codes.to_numpy()],
        "部门": _map_column(df["SO_DEPTID"], _dept),
        "业务员": _map_column(df["SO_PSNDOC"], _person),
        "订单类型": _order_type_mix(len(df), rng),
        "交易类型": _map_column(df["PK_TRADETYPE"], _trade_type),
        "单据类型": [_bill_type(v) for v in df["SRC_BILLTYPENAME"].astype("string").fillna("")],
        "数量": df["QUANTITY_DE"].round(3),
        # 导出里的红字（退货/冲销）是负数，demo 统一取绝对值：否则地图会出现
        # 负的省份合计、饼图扇区互相抵消。是否为退货由「订单类型」区分。
        "销售额": df["MONEY_DE"].abs().round(2),
        "不含税金额": df["NOTAX_DE1"].abs().round(2),
    })
    # 回款：六成订单一次结清，其余按 20%–90% 分批回款。原始导出里 MONEY_REC
    # 几乎等于 MONEY_DE，直接照搬会让「回款率」恒为 100%、应收余额全是 0，
    # 应收回款这几个指标就没有可看的了。
    ratio = np.where(rng.random(len(out)) < 0.6, 1.0, rng.uniform(0.2, 0.9, len(out)))
    out["已回款"] = (out["销售额"] * ratio).round(2)
    out["应收余额"] = (out["销售额"] - out["已回款"]).round(2)
    # 客户简称：横向条形图的 Y 轴放不下「兰州金桥科技有限公司」这种 10 字名，
    # 缩短后不必旋转 45°，卡片里也压不到坐标轴。
    out.insert(out.columns.get_loc("客户") + 1, "客户简称",
               out["客户"].str.replace(r"有限公司$", "", regex=True))

    # 产品线放在产品大类右侧，堆叠图 / 图例用它，明细表仍用产品大类
    out.insert(out.columns.get_loc("产品大类") + 1, "产品线",
               out["产品大类"].map(lambda c: PRODUCT_LINE.get(c, "其他")))

    # 剔除极端单（单笔 > 30 万，约 0.03%）：这类项目型大单会让月趋势出现
    # 与业务无关的尖峰，演示里反而看不清趋势。
    out = out[out["销售额"] <= 300000.0]

    # 按月份分层抽样：每个月抽相同行数（不足则全取），避免「某月只剩 200 行
    # 却恰好塞进几张百万大单」造成假尖峰。
    out["_月"] = out["下单日期"].str[:7]
    months = sorted(out["_月"].unique())
    per_month = max(1, int(rows / len(months))) if months else rows
    parts = []
    for _, g in out.groupby("_月", sort=True):
        parts.append(g.sample(n=min(per_month, len(g)), random_state=20251117))
    out = pd.concat(parts, ignore_index=True).drop(columns=["_月"])
    out = out.sort_values(["下单日期", "订单号"], kind="mergesort").reset_index(drop=True)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="用友销售导出 → 可读中文 Demo 数据")
    ap.add_argument("--src", required=True, help="原始导出 CSV（主键 ID 版）")
    ap.add_argument("--out", default=os.path.join(DATA_DIR, "sales_demo.csv"))
    ap.add_argument("--rows", type=int, default=40000, help="抽样总行数")
    ap.add_argument("--start", default="2025-01-01")
    ap.add_argument("--end", default="2026-06-01")
    args = ap.parse_args()

    df = build(args.src, args.rows, args.start, args.end)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    # utf-8-sig：Windows 上用 Excel 直接打开也不会乱码
    df.to_csv(args.out, index=False, encoding="utf-8-sig", lineterminator="\n")

    money = df["销售额"].sum()
    print("写出 %s" % args.out)
    print("行数 %d · 订单 %d · 客户 %d · 产品 %d · 日期 %s ~ %s"
          % (len(df), df["订单号"].nunique(), df["客户"].nunique(),
             df["产品"].nunique(), df["下单日期"].min(), df["下单日期"].max()))
    print("销售额合计 %.2f · 已回款 %.2f" % (money, df["已回款"].sum()))
    print("大区：%s" % "、".join(df["大区"].value_counts().index))


if __name__ == "__main__":
    main()
