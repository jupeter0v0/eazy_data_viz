# 参与开发

欢迎提 issue / PR。这个项目刻意保持「小」：没有前端构建、没有 CDN、没有服务端。

## 本地开发

```bash
git clone https://github.com/<you>/eazy_data_viz.git
cd eazy_data_viz

# 只跑核心（pandas）
python tests/test_eazy.py

# 前端断言（需要本机 Chrome）
python tests/js_test.py

# 重新生成画廊 / 给 AI 的文档
python tools/build_gallery.py
python tools/gen_ai_doc.py
```

依赖：Python ≥ 3.8、pandas ≥ 1.3；写前端测试需要 Chrome（headless）；
有 Streamlit 时可 `pip install ".[streamlit]"` 跑 `pviz.gallery`。

## 目录

```
eazy_data_viz/          # 库本体（Python + JS 运行时）
  frame.py              # DataFrame → 紧凑记录、列类型识别、采样、有序类目
  chart.py              # 基础 14 种图表与公共参数校验
  charts_extra.py       # 扩展 31 种图表
  render.py             # 页面组装、Material Design 3 CSS、Streamlit 适配
  palette.py            # 7 套配色
  assets/               # ECharts + 运行时 JS（内联进 HTML）
tests/                  # Python 断言 + headless Chrome 前端断言
tools/                  # build_gallery.py（画廊）、gen_ai_doc.py（AI 文档）
docs/                   # AI_GUIDE.md（人读）、EXTRA_CHARTS.md（契约）、catalog.json
examples/               # 可直接运行的示例
```

## 加一种新图表

1. **Python 侧**（`charts_extra.py` 或 `chart.py`）：校验参数、声明角色
   （`roles={"x":..., "y":...}`），调用 `_base_spec(...)` 拿到 `spec`，
   返回 `Chart(spec, records, ref, warnings)`。不要在 Python 里做聚合
   （聚合必须在前端按筛选状态实时算）。
2. **JS 侧**（`assets/eazy_extra_*.js`）：注册
   `EazyViz.extraBuilders[type] = function(spec, data, state, theme) { return option; }`；
   HTML 类组件注册 `EazyViz.htmlBuilders[type] = function(spec, data, state, theme) { return html; }`。
   用户数据一律走 `U.esc()` 转义。
3. **接线**：`__init__.py` 导出函数（含 `__all__`）、`render.py` 的 `HTML_TYPES`
   （若是 HTML 类卡片）。
4. **验证**：在 `tools/build_gallery.py` 增加一张卡片（会自动录制代码），
   `tests/test_eazy.py` 增加断言，跑两个测试脚本。
5. 契约细节见 `docs/EXTRA_CHARTS.md`（spec 字段、可用工具、ES5 约束）。

## 约定

- Python 3.8 语法兼容（不用 `match`、不用 3.9+ 的类型注解语法）。
- 前端运行时代码是 **ES5**（不依赖构建步骤），新增文件按 IIFE 包裹，
  不要把辅助函数放到其它文件的 IIFE 作用域里。
- 面向用户的 API 只接受 DataFrame + 列名，永远不要要求用户写 JSON/spec。
- 中文注释、中文文档；错误信息要指出「哪个参数、什么值、期望什么」。
- 提交前跑：`python tests/test_eazy.py && python tests/js_test.py`。

## 发布

```bash
python tools/build_gallery.py       # 重建 gallery.html
python tools/gen_ai_doc.py          # 重建 docs/AI_GUIDE.md + catalog
python -m pip wheel . --no-deps --no-build-isolation -w dist
```
