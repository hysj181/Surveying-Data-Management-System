# 测量数据管理系统

基于 Python + PySide6 的 Windows 桌面水准测量数据处理软件，支持闭合/附合水准路线计算、闭合差评定、重复观测误差分析与 CSV / Excel 成果导出。项目使用项目级 `.venv` 管理环境，代码位于 `src` 目录并按业务层、服务层、界面层分层。

## 功能

- 闭合水准路线与附合水准路线计算
- 三等、四等、图根水准限差评定（±12√L、±20√L、±40√L mm）
- 按测段距离比例分配闭合差，计算改正后高差和各点高程
- 闭合差利用率、闭合差与路线长之比、改正数中误差、最大改正数
- 重复观测列统计：均值、中位数、样本标准差、标准误差、极差、RMSE、相对标准差
- 2σ / 3σ 粗差提示
- 导出带 BOM 的 CSV、格式化的 Excel 工作簿（工程概况、水准计算、误差分析）
- 工程文件保存与打开（JSON），包含测段、控制点和观测列
- 未保存更改提示、新建 / 打开 / 保存 / 另存为、快捷键和示例数据
- 使用 PySide6 `pyside6-deploy` 打包为单文件 EXE

## 环境

- Windows 10 / 11
- Python 3.10 及以上（本项目已在 Python 3.13 验证）
- PySide6 6.12.0
- openpyxl 3.1.5

运行依赖记录在 `requirements.txt`，测试依赖记录在 `requirements-dev.txt`，打包依赖记录在 `requirements-build.txt`。`.venv`、`dist`、缓存和打包中间文件均已加入 `.gitignore`，克隆后按依赖文件重建环境即可。

## 快速开始

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe src\main.py
```

如使用其他受支持的 Python 版本，将 `py -3.13` 替换为对应命令即可。

如果不激活虚拟环境，也可以直接使用 `.venv\Scripts\python.exe` 运行。

## 使用流程

1. 在“数据输入与计算”页面填写工程名称、观测者、日期、路线类型、测量等级、起点和终点信息。
2. 输入各测段的起点、终点、距离和观测高差。闭合路线会自动把终点同步为起点。
3. 点击“执行水准计算”，查看闭合差、容许闭合差、质量评定、各测段改正数和各点高程。
4. 切换到“误差分析”，查看闭合差评定；在右侧输入重复观测值并进行精度与粗差分析。
5. 切换到“成果导出”，导出 CSV、Excel，或保存为 JSON 工程文件。

## 计算规则

- 闭合路线：`f_h = Σh观测`
- 附合路线：`f_h = Σh观测 - (H终点 - H起点)`
- 容许闭合差：`f容 = C × √L`，其中 `C` 为等级系数，`L` 为路线长度（km）
- 改正数：`v_i = -f_h × L_i / ΣL`
- 改正后高差：`h_i' = h_i + v_i`
- 各点高程：从起点高程开始逐段累加改正后高差

界面中高差和距离均以米为单位，改正数以毫米显示。闭合差超限时仍会显示计算过程，但会给出警示，导出前需要确认。

## 项目结构

```text
测量数据管理系统/
├─ .venv/                     # 项目级虚拟环境
├─ assets/
│  └─ app.ico                 # 应用与打包图标
├─ scripts/
│  └─ build.ps1               # 单文件打包脚本
├─ src/
│  ├─ main.py                 # 程序入口
│  └─ surveying/
│     ├─ application.py       # QApplication 初始化
│     ├─ domain/              # 纯业务模型与计算
│     │  ├─ models.py
│     │  ├─ leveling.py
│     │  └─ error_analysis.py
│     ├─ services/            # 文件、导出、示例数据
│     │  ├─ project_io.py
│     │  ├─ exporters.py
│     │  └─ samples.py
│     └─ ui/                  # PySide6 界面层
│        ├─ main_window.py
│        ├─ leveling_page.py
│        ├─ analysis_page.py
│        ├─ export_page.py
│        ├─ widgets.py
│        └─ style.py
├─ tests/                     # 业务与界面冒烟测试
├─ requirements.txt
├─ requirements-dev.txt
├─ requirements-build.txt
├─ pysidedeploy.spec
├─ pytest.ini
├─ LICENSE
└─ README.md
```

## 测试

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest
```

测试覆盖水准计算、限差判定、观测统计、粗差检测、工程文件读写、CSV / Excel 导出和界面冒烟。

## 打包为单文件

`pysidedeploy.spec` 已配置为 onefile 模式、无控制台窗口，并指定应用图标。执行：

```powershell
.\scripts\build.ps1
```

构建成功后生成单文件：

```text
dist\SurveyingDataManager.exe
```

同时生成免安装便携版（推荐分发给其他电脑）：

```powershell
.\scripts\build.ps1 -Portable
```

输出：

```text
dist\SurveyingDataManager-Portable\
dist\SurveyingDataManager-Portable.zip
```

便携版包含 Python、PySide6、VC 运行库及全部 Qt 依赖，解压后直接双击 `SurveyingDataManager.exe` 即可运行，不需要安装 Python、配置环境变量或联网。

如需使用国内 PyPI 镜像：

```powershell
.\scripts\build.ps1 -IndexUrl https://pypi.tuna.tsinghua.edu.cn/simple
```

依赖已经安装、只需要重新编译时可使用：

```powershell
.\scripts\build.ps1 -SkipInstall
```

说明：

- `pyside6-deploy` 使用 Nuitka 编译，首次构建会按 `requirements-build.txt` 安装 `Nuitka==4.1.1` 并可能下载编译工具，耗时较长。
- 构建需要可用的 C/C++ 编译环境；Windows 推荐安装 Visual Studio Build Tools（MSVC）。
- Nuitka 的 MSVC 工具链对中文路径支持不稳定。当项目路径包含中文时，`build.ps1` 会自动将源码复制到 `%PUBLIC%\SurveyingDataManagerBuild`，并在 ASCII 路径下使用独立虚拟环境完成编译，最后把 EXE 复制回项目 `dist` 目录。
- onefile 模式会在运行时解压到临时目录，因此启动速度略慢于目录模式，但便于单文件分享。
- 应用数据、导出文件和工程文件均保存在用户选择的路径，不会写入安装目录。
- 如需生成工程文件示例，可在软件中点击“载入示例”，再使用“保存工程”。
- 单文件版每次启动会先解压运行库，部分低配置电脑或开启实时杀毒扫描时启动较慢；对稳定性要求高时建议分发便携版 ZIP。
- 文件选择使用 Qt 内置对话框，避免 Windows 网络驱动器或第三方 Shell 扩展导致文件对话框卡死。

## 兼容性与排查

- 支持 Windows 10 / Windows 11 64 位。32 位 Windows、Windows 7 不受 PySide6 6.12 支持。
- 启动画面、日志和全局异常处理已内置，启动阶段不会出现无反馈窗口。
- 诊断日志位于 `%LOCALAPPDATA%\SurveyingTools\测量数据管理系统\logs\app.log`，也可通过菜单“帮助 → 打开诊断日志目录”打开。
- 若某台电脑上单文件 EXE 启动缓慢，请改用 `SurveyingDataManager-Portable.zip` 解压版，并将整个文件夹加入杀毒软件信任区。
- 遇到无响应时，请提供日志文件、Windows 版本和具体操作步骤，便于定位。

## 数据文件

工程文件为 UTF-8 JSON，顶层字段包括：

- `format`: 固定为 `surveying-data-manager`
- `schema_version`: 当前为 `1`
- `project`: 工程信息与测段数组
- `observations`: 重复观测值数组
- `observation_target`: 参考值，可为 `null`

## 开源许可

本项目采用 MIT License，详见 `LICENSE`。

## 备注

- 计算采用距离比例分配闭合差，适用于常规水准路线平差。
- 三等、四等、图根系数用于快速限差评定，生产项目请以相应测量规范为准。
- 粗差提示基于均值和样本标准差，样本数量较少时统计判定灵敏度有限，应结合外业记录复核。
