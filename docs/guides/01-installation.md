# 01 · 安装与环境矩阵

> 目标：在 10 分钟内把 `eazy_data_viz` 装进一个干净、可复现的 Python 环境，并跑通第一张图。
> 本篇覆盖四种安装来源（PyPI / GitHub 归档 zip / 本地源码 / 本地 wheel）、离线安装、无 git 机器，
> 以及 12 类真实安装报错的定位与修法。

## 适用人群与前置条件

| 项 | 要求 |
| --- | --- |
| 读者 | 会用命令行、知道 `pip` 与 `python` 区别的工程师 / 分析师 |
| Python | **3.8 ~ 3.14**（`setup.py` 中 `python_requires=">=3.8"`） |
| 必需依赖 | `pandas>=1.3`（唯一硬依赖） |
| 可选依赖 | `streamlit>=1.10`（Streamlit 嵌入）、`ipython>=7`（Jupyter 内联显示） |
| 磁盘 | 源码约 3 MB；单个 HTML 产物约 1.1 MB（ECharts 已内联） |
| 网络 | 仅安装阶段需要；**产物运行不需要任何 CDN** |

先确认解释器与 pip 是同一套（Windows 上这是 90% 安装问题的根源）：

```bash
python -c "import sys; print(sys.executable)"
python -m pip --version
# 两个路径里的 Python 版本目录应当一致，例如都出现 Python38
```

> **重要结论**：始终使用 `python -m pip install ...` 而不是裸 `pip install ...`。
> 裸 `pip` 可能属于另一个 Python（比如 pyenv、conda base、Windows Store 版），
> 装完 `import eazy_data_viz` 会报 `ModuleNotFoundError`。

## 1. 环境矩阵：哪些组合验证过

`eazy_data_viz` 只用 pandas 的标准 API，不编译 C 扩展，因此是纯 Python wheel（`py3-none-any`）。
官方 CI/手工验证过的组合：

| Python | pandas | Streamlit | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| 3.8.10 | 2.0.3 | 1.27.1 | ✅ 全部测试通过 | Windows 10/11 主力环境 |
| 3.12.14 | 2.x | 1.67.0 | ✅ | 新项目推荐 |
| 3.14.10 | 3.1.1 | 1.67.0 | ✅ `tests/test_eazy.py` PASS 28 | 最新版验证 |
| 3.8 ~ 3.14 | >=1.3 | 任意 >=1.10 | 理论支持 | `setup.py` classifiers 覆盖全区间 |

选择建议：

- **新项目**：Python 3.11 / 3.12 + 最新 pandas。生态最稳。
- **老服务器**：Python 3.8 + pandas 1.3~2.0 可用；不要为了图表库升级生产 pandas。
- **pandas 3.x**：官方已在新 Python 上验证；pandas 3 的 Copy-on-Write 不影响本库（本库只读 DataFrame）。
- 32 位 Python：pandas 自身没有 32 位 wheel，装不上 pandas，本库也无法使用。

## 2. 方式一：从 PyPI 安装（最省事）

包在 `setup.py` 里注册的名称是 `eazy_data_viz`；PyPI 会把它归一化成 `eazy-data-viz`。
两种写法等价，`pip install eazy_data_viz` 也可以：

```bash
# 只装核心（pandas）
python -m pip install eazy-data-viz

# 需要 Streamlit 时（会额外装 streamlit）
python -m pip install "eazy-data-viz[streamlit]"

# 需要 Jupyter 内联显示时
python -m pip install "eazy-data-viz[notebook]"

# 两个都要
python -m pip install "eazy-data-viz[streamlit,notebook]"
```

装完立刻验证（不依赖任何示例文件）：

```bash
python -c "import eazy_data_viz as edv; print(edv.__version__); print(edv.sample_df().shape)"
# 期望输出：
# 1.0.0
# (1500, 11)
```

### 2.1 国内镜像与内网 PyPI

若下载超时，可临时指定镜像（不要写进项目配置，避免污染）：

```bash
python -m pip install eazy-data-viz -i https://pypi.tuna.tsinghua.edu.cn/simple
```

公司内网私服常见两种失败：

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `No matching distribution found for eazy-data-viz` | 私服未同步该包 | 让运维同步，或改用第 3/4/5 种安装方式 |
| 装到的是旧版本（`__version__` 不是 1.0.0） | 私服缓存旧包 | `python -m pip install -U --no-cache-dir eazy-data-viz` 或指定 `==1.0.0` |

**判断是否真的发布在 PyPI**：如果你执行上面的命令得到 `No matching distribution found`，
说明当前网络/PyPI 上没有该发行版，直接跳到「方式三：本地源码」或「方式四：本地 wheel」。
本仓库的 `dist/` 目录已经内置了可安装的 wheel，见方式四。

## 3. 方式二：从 GitHub 归档 zip 安装（机器上没有 git）

`git clone` 和 `pip install git+https://...` 都要求本机有 **git 可执行文件**。
很多生产服务器、跳板机、Windows Server 没有 git。此时用 GitHub 的「源码归档 zip」：
zip 解压后就是普通目录，`pip` 直接本地构建，全程不需要 git。

### 3.1 直接让 pip 拉归档 zip（需要外网）

```bash
python -m pip install "https://github.com/jupeter0v0/eazy_data_viz/archive/refs/heads/main.zip"
```

这条命令只要求 Python 能访问 HTTPS，**不要求 git**。

### 3.2 先下载 zip 再安装（内网、离线、需要审计时）

1. 浏览器打开仓库页面 → `Code` → `Download ZIP`，得到 `eazy_data_viz-main.zip`；
2. 拷到目标机器，执行：

```bash
# Windows（注意引号，路径里有空格时必须加）
python -m pip install "D:\packages\eazy_data_viz-main.zip"

# 解压后从目录安装也可以
python -m pip install "D:\packages\eazy_data_viz-main"
```

zip 安装会自动构建 wheel，需要本机有可用的 `setuptools` 与 `wheel`
（Python 3.12+ 默认不再自带 `wheel`，见第 9 节报错表）。

### 3.3 为什么 `git+https` 会失败

```bash
# 没有 git 的机器上执行：
python -m pip install "git+https://github.com/jupeter0v0/eazy_data_viz.git"
```

典型输出（这正是「无 git」的固定报错形状）：

```text
ERROR: Cannot find command 'git' - do you have 'git' installed and in your PATH?
```

或者：

```text
error: subprocess-exited-with-error
  × git clone --filter=blob:none ... did not run successfully.
  │ exit code: 1
  ╰─> [2 lines of output]
      'git' is not recognized as an internal or external command,
      operable program or batch file.
```

三种修法，按推荐度排序：

1. **换 zip 安装**（本节 3.1 / 3.2），零额外依赖；
2. 安装 git：Windows 用 [Git for Windows](https://git-scm.com/download/win)，装完重开终端让 PATH 生效；
3. 离线机器：在有网的机器 `pip download` 打包，再拷过去（见第 6 节）。

## 4. 方式三：本地源码目录安装（开发 / 改源码）

```bash
git clone https://github.com/jupeter0v0/eazy_data_viz.git
cd eazy_data_viz
python -m pip install .
```

三种子模式的区别：

| 命令 | 行为 | 适合 |
| --- | --- | --- |
| `pip install .` | 复制一份到 site-packages 并构建 wheel | 普通使用者，装完与源码目录无关 |
| `pip install -e .` | 可编辑安装，site-packages 里放指向源码目录的链接 | 要改库代码、要跑仓库内示例 |
| `pip install -e ".[streamlit]"` | 同上 + Streamlit extra | 开发 Streamlit 应用 |

**注意**：做文档里示例时推荐 `-e .`，否则你 `cd` 到别的目录后导入的是已安装副本，
修改源码不会生效。验证安装方式：

```bash
python -c "import eazy_data_viz as edv; print(edv.__file__)"
# pip install .        -> ...\site-packages\eazy_data_viz\__init__.py
# pip install -e .     -> F:\deepseek\eazy_data_viz\eazy_data_viz\__init__.py
```

## 5. 方式四：本地 wheel 安装（离线交付的标准做法）

仓库 `dist/` 里带有构建好的 wheel，文件名固定为
`eazy_data_viz-1.0.0-py3-none-any.whl`（约 845 KB，`py3-none-any` 表示任意平台通用）。
wheel 自带全部 JS 资源（ECharts、运行时、地图 JSON），装完即可离线出图：

```bash
# 在仓库根目录执行
python -m pip install "dist\eazy_data_viz-1.0.0-py3-none-any.whl"

# 拷到别的机器后（任何目录）
python -m pip install "D:\offline\eazy_data_viz-1.0.0-py3-none-any.whl"
```

不想污染当前环境时，可以只装到一个目录，再用 `PYTHONPATH` 指过去：

```bash
python -m pip install --no-deps --target "D:\libs\edv" "dist\eazy_data_viz-1.0.0-py3-none-any.whl"
# Windows CMD: set PYTHONPATH=D:\libs\edv
# PowerShell:  $env:PYTHONPATH="D:\libs\edv"
# Git Bash:    export PYTHONPATH=/d/libs/edv
python -c "import eazy_data_viz as edv; print(edv.__version__)"
```

wheel 安装不会编译、不需要 setuptools、不需要联网，是**生产环境最推荐**的方式。

## 6. 虚拟环境：隔离 pandas 版本

本库依赖 pandas，而 pandas 的版本又经常被其它项目锁死。
新项目一律建独立虚拟环境：

### 6.1 venv（标准库，最轻）

```bash
# 创建（Windows）
python -m venv .venv
# 激活，Git Bash：
source .venv/Scripts/activate
# 激活，CMD：
# .venv\Scripts\activate.bat
# 激活，PowerShell：
# .venv\Scripts\Activate.ps1

python -m pip install -U pip
python -m pip install "eazy-data-viz[streamlit]"
```

macOS / Linux 把 `Scripts` 换成 `bin` 即可。退出用 `deactivate`。

### 6.2 conda

```bash
conda create -n edv python=3.11 -y
conda activate edv
pip install "eazy-data-viz[streamlit]"
```

> **重要结论**：不要在同一个环境里混用 conda 的 pandas 和 pip 装的 pandas 版本锁定；
> 若出现 `pandas ... has requirement ...` 冲突，先 `conda list pandas` 看来源，
> 再统一用 `pip install "pandas>=1.3"` 覆盖。

## 7. “离线安装”到底离了什么线

这是本库最容易误会的一点：**产物运行时不需要网络，连 CDN 都不用。**
HTML 页面里内联了两样东西：

| 内联资源 | 大小 | 来源 | 是否访问网络 |
| --- | --- | --- | --- |
| `echarts.min.js` | 约 1.0 MB | `eazy_data_viz/assets/echarts.min.js` | 否 |
| 运行时 `eazy.js` + 各扩展 JS | 约 130 KB | `eazy_data_viz/assets/*.js` | 否 |
| 数据 + 页面配置 | 视数据量 | 生成时序列化进 HTML | 否 |
| 字体 | 系统字体栈 | 不下载 webfont | 否 |

因此安装阶段离线的唯一问题是：**拿不到 wheel 文件**。做法：

```bash
# 在有网的机器上（与目标机同 Python 版本、同平台）
python -m pip download eazy-data-viz --no-deps -d wheelhouse
# wheelhouse/ 里会出现 eazy_data_viz-1.0.0-py3-none-any.whl

# 把 wheelhouse 拷到离线机器
python -m pip install --no-index --find-links wheelhouse eazy-data-viz

# 连带 pandas 也要离线时，去掉 --no-deps 把依赖一起下载：
python -m pip download "eazy-data-viz[streamlit]" -d wheelhouse
```

验证资源确实随包安装、而不是运行时要下载：

```bash
python -c "import eazy_data_viz as edv; h=edv.bar(edv.sample_df(), x='大区'); print(len(h.to_html()))"
# 输出应 > 1000000；若只有几十 KB，说明 assets 没被装进去（见报错表）
```

浏览器打开生成的 HTML 后 **断网刷新**，图表仍然渲染，即验证通过。

## 8. 第一次运行：安装后自检脚本

把下面脚本保存为 `selfcheck.py`。若已 `pip install`，任意目录都能跑；
若只是从源码目录临时运行（没安装），在仓库根目录加 `PYTHONPATH=.`：

```bash
PYTHONIOENCODING=utf-8 python selfcheck.py
# 未安装、仅源码目录时：
PYTHONIOENCODING=utf-8 PYTHONPATH=. python selfcheck.py
```

```python
import eazy_data_viz as edv
from eazy_data_viz import render, palette

print("版本:", edv.__version__)
print("Python:", __import__("sys").version.split()[0])
print("pandas:", __import__("pandas").__version__)

df = edv.sample_df()
print("示例数据:", df.shape, list(df.columns))

chart = edv.bar(df, x="大区", y="销售额", color="产品", stack=True)
html = chart.to_html()
print("单图 HTML:", len(html), "字节")
print("内联 ECharts:", ("echarts" in html.lower()), "内联运行时:", ("EazyViz" in html))

print("配色:", palette.names())
print("当前默认:", palette.current())
print("导出模块:", render.__name__)
```

期望输出（数值会随版本略有差异，但量级一致）：

```text
版本: 1.0.0
Python: 3.8.10
pandas: 2.0.3
示例数据: (1500, 11) ['日期', '月份', '大区', '省份', '城市', '产品', '渠道', '销售额', '订单数', '利润', '客户数']
单图 HTML: 1342736 字节
内联 ECharts: True 内联运行时: True
配色: ['google', 'antd', 'tableau', 'carbon', 'echarts', 'morandi', 'tailwind']
当前默认: google
导出模块: eazy_data_viz.render
```

再跑一遍官方测试（只有从源码目录安装时才有 `tests/`）：

```bash
python tests/test_eazy.py   # 期望最后一行：PASS 28
python tests/js_test.py     # 期望：JS PASS 59（需要 node）
```

## 9. 常见安装报错对照表

下表报错文本来自真实终端输出；每行给出「原因 → 修法」。

| 报错（关键片段） | 原因 | 修法 |
| --- | --- | --- |
| `ERROR: Cannot find command 'git'` | 用 `git+https` 安装但没有 git | 改用第 3 节的归档 zip，或装 Git for Windows |
| `'git' is not recognized as an internal or external command` | Windows PATH 里没有 git | 同上；装完 git 后**重开终端** |
| `No matching distribution found for eazy-data-viz` | PyPI/私服上没有该版本，或网络不通 | 换镜像；或改用方式三/四（源码目录 / 本地 wheel） |
| `Could not find a version that satisfies the requirement pandas>=1.3` | 当前 Python 太老/太新，或平台无 pandas wheel | 升 Python 到 3.8+；`python -m pip install -U pip` 后重试 |
| `ModuleNotFoundError: No module named 'eazy_data_viz'` | 装进了另一个解释器 | `python -c "import sys;print(sys.executable)"`，统一用 `python -m pip` |
| `ImportError: cannot import name 'ring_progress' from 'eazy_data_viz'` | 装的是旧版本（0.x），`__all__` 里没有该函数 | `python -m pip install -U --no-cache-dir eazy-data-viz`；或 `print(edv.__version__)` 确认 |
| `error: Microsoft Visual C++ 14.0 or greater is required` | 装的是 pandas **源码包**，正在编译 | 不要 `--no-binary`；升级 pip 以拿到 pandas wheel；或换 Python 3.8+ |
| `error: invalid command 'bdist_wheel'` | 缺 `wheel` 包，zip/源码安装时无法构建 | `python -m pip install -U setuptools wheel` 后重装 |
| `No module named 'setuptools'`（Python 3.12+） | 新 Python 默认不装 setuptools | `python -m pip install setuptools wheel` |
| `ERROR: Could not build wheels for eazy-data-viz` | 构建环境缺 setuptools / 权限不足 | 直接用 `dist/` 的 wheel；或 `pip install --no-build-isolation .` |
| `PermissionError: [WinError 5] Access is denied` | 装到了系统 Python 的 Program Files | 用虚拟环境；或 `python -m pip install --user ...` |
| `WARNING: The script ... is installed in 'C:\Users\...\AppData\...\Scripts' which is not on PATH` | 用户脚本目录不在 PATH | 警告无害（本库没有命令行入口）；可把该目录加进 PATH |
| `SSLError(SSLCertVerificationError(...))` | 公司代理/杀毒软件替换证书 | 设 `pip config set global.trusted-host pypi.org` + 对应镜像；或找运维要证书 |
| `ReadTimeoutError` / `ConnectionResetError` | 网络慢/代理阻断 | `pip install --timeout 120 --retries 5 ...`；换镜像 |
| `ValueError: pandas 版本过低`（运行期） | pandas < 1.3 | `python -m pip install -U "pandas>=1.3"` |
| 图表空白，控制台 `echarts is not defined` | 装在别处的旧包，assets 缺失/被裁剪 | 重装 wheel；检查 `site-packages/eazy_data_viz/assets/echarts.min.js` 是否存在 |

### 9.1 如何确认 assets 装全了

```bash
python -c "import os, eazy_data_viz.render as r; print(r.ASSETS_DIR); print(sorted(os.listdir(r.ASSETS_DIR))[:6])"
# 应看到 echarts.min.js / eazy.js / eazy_extra_a.js / maps 等
```

若目录为空或没有 `echarts.min.js`，说明打包时 `package_data` 没生效（常见于自己裁剪 wheel），
重装官方 wheel 即可。

## 10. 升级、降级与卸载

```bash
# 升级到最新
python -m pip install -U eazy-data-viz

# 精确安装某个版本
python -m pip install "eazy-data-viz==1.0.0"

# 卸载
python -m pip uninstall -y eazy-data-viz
```

升级后图空白/报找不到函数时，先清缓存再重装：

```bash
python -m pip install -U --no-cache-dir --force-reinstall eazy-data-viz
```

> **结论**：`--force-reinstall` 只在该升级没生效时用；日常升级用 `-U` 足够。

## 11. 常见问题（FAQ）

**Q1：公司电脑不能装 Python 包，能不能只拷一个 HTML？**
能。图表是纯前端 HTML，生成一次后发给任何人（含没有 Python 的同事），对方双击即可交互；
下钻、联动都在浏览器里跑。这也意味着**下钻数据必须在生成 HTML 前就嵌进去**（`drill=[...]`）。

**Q2：`pip install .` 和 `pip install -e .` 为什么导入路径不一样？**
前者是复制安装，后者是链接安装。改库源码时必须用 `-e`；只写业务代码用普通安装即可。

**Q3：必须装 Streamlit 吗？**
不必。核心只依赖 pandas。只有需要在 Streamlit 页面里嵌入图表时才装
`.[streamlit]`；只生成 HTML 的场景完全不需要。

**Q4：Python 3.7 能用吗？**
不能。`setup.py` 要求 `>=3.8`，源码中使用了 f-string 之外的 3.8 语法与 pandas 新 API。
若被锁死在 3.7，只能升级 Python 或使用容器。

**Q5：需要 Node、npm、浏览器驱动吗？**
不需要。JS 已经构建好并内联；`tests/js_test.py` 需要 node，但那只是开发测试，使用者无感。

**Q6：安装体积多大？**
wheel 约 845 KB，装完 site-packages 里约 1.6 MB（ECharts 占大头）。产物单个 HTML 约 1.1 MB。

## 下一篇

环境就绪后，进入 [02 · 五分钟上手](02-quickstart.md)，从 `sample_df()` 一路走到主题切换。
