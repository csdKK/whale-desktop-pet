# 鲸鱼娘桌宠 (DSH-FatFish)

一只基于 PySide6 的桌面宠物，自带 106 个动画，支持 AI 对话、AI 编程工具状态监测、多实例等功能。

## 功能特性

- **桌面宠物**：透明无边框置顶窗口，可拖拽、缩放、镜像翻转、调节动画播放速度（0.5x~3.0x）
- **丰富动画**：106 个动画（待机、吃东西、工作、互动、节日等），优先使用 `assets/gif_hd/` 下的高清 WebP，回退到 `assets/gif/` 下的 GIF
- **AI 对话**：支持 Ollama、DeepSeek、Claude、OpenAI、通义千问、智谱 GLM、Kimi、文心一言、豆包、讯飞星火、Gemini、Groq、OpenRouter 等 16+ 服务商，流式输出
- **AI 工具监测**：实时检测 Trae、Claude Code 等 AI 编程工具的工作状态（工作中 / 刚完成 / 空闲）
- **余额提醒**：可配置刷新间隔与上限提醒
- **多实例**：每次启动生成独立实例，配置互不干扰（存放于 `~/.whale-pet/instances/`）
- **系统托盘**：右键菜单、开机自启、位置记忆
- **启动动画**：播放 `启动动画.mp4` 后进入主界面

## 环境要求

- Windows 10/11
- Python 3.11（打包使用嵌入式 Python 3.11.9）
- 依赖：见 `requirements.txt`
  ```
  PySide6>=6.5
  Pillow>=10.0
  psutil>=5.9
  ```

## 本地开发运行

```bash
pip install -r requirements.txt
python main.py
```

## 目录结构

```
whale-desktop-pet/
├── main.py                 # 启动入口
├── pet_window.py           # 主窗口（动画播放、拖拽、托盘、菜单）
├── pet_config.py           # 配置持久化（多实例）
├── animations.py           # 动画目录与 gif_path() 解析
├── gif_player.py           # GIF/WebP 播放器
├── ai_chat.py              # AI 对话模块（多服务商）
├── ai_monitor.py           # AI 编程工具状态监测
├── balance.py              # 余额提醒
├── splash.py               # 启动动画窗口
├── requirements.txt        # 依赖清单
├── 启动动画.mp4            # 启动视频
├── 圆角-蓝色大肥鱼.ico      # 程序图标
├── AI聊天头像.png          # AI 对话头像
├── 白色米饭.png            # 资源图片
├── assets/
│   ├── gif/                # 低清 GIF 动画（备用）
│   └── gif_hd/             # 高清 WebP 动画（主用）
├── installer/
│   ├── build.py            # 构建离线安装包 → installer_bundle/
│   ├── installer.py        # 安装程序 GUI
│   └── uninstaller.py      # 卸载程序
├── make_sfx.ps1            # SFX 打包脚本（将 installer_bundle 打成单文件 exe）
└── _sfx_stub.cs            # SFX 自解压桩程序源码（C#）
```

## 打包成 exe（离线安装包）

本项目采用「便携 Python + 源码 + 资源」的离线安装包方案，最终产物为单文件 `WhalePetInstaller.exe`。整个打包过程**不依赖 PyInstaller**，仅需系统自带的 Python 和 .NET Framework。

### 前置条件

| 条件 | 说明 |
|------|------|
| 操作系统 | Windows 10/11 |
| Python | 3.11（系统已安装的 Python，用于运行 build.py） |
| .NET Framework | 系统自带即可（用于编译 SFX 桩程序） |
| 磁盘空间 | 至少预留 5 GB（ZIP 压缩过程需要临时空间） |
| 网络 | 需要访问华为云镜像和清华镜像（见下方 pip 配置） |

### 重要：配置 pip 国内镜像源

如果不配置镜像源，下载依赖时会从 pypi.org 拉取，在国内网络下极易超时失败。**打包前务必先配置：**

```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip config set global.timeout 60
```

验证配置：
```bash
pip config list
# 应输出: global.index-url='https://pypi.tuna.tsinghua.edu.cn/simple'
```

### 完整打包流程（共 2 步）

#### 第一步：生成安装包目录 installer_bundle/

在项目根目录运行：

```bash
python installer/build.py
```

执行内容：

1. 下载嵌入式 Python 3.11.9（华为云镜像 `repo.huaweicloud.com`），下载失败则回退到复制系统 Python
2. 下载依赖 wheel 并安装到嵌入式 Python：
   - PySide6 6.12.0（含 Essentials + Addons + WebEngine + Pdf + shiboken6）
   - Pillow 12.3.0
   - psutil 7.2.2
3. 复制 tkinter 运行时（tcl/、tk/ 目录）
4. 清理 PySide6 开发文件（examples、tests、*.pdb、*.lib 等，减小约 300MB）
5. 复制源码（main.py、pet_window.py 等 10 个 .py 文件）和资源（assets/、启动动画.mp4、图标等）
6. 复制 installer.py、uninstaller.py，生成 installer.bat 和 安装说明.txt

**完成标志：** 控制台输出 `构建完成！安装包目录：...installer_bundle`

此时可先测试安装流程：双击 `installer_bundle/installer.bat`

#### 第二步：将 installer_bundle 打成单文件 EXE

在项目根目录运行（PowerShell）：

```powershell
powershell -ExecutionPolicy Bypass -File make_sfx.ps1
```

执行内容：

1. 将 `installer_bundle/` 以「最优压缩」打成 `_bundle.zip`
2. 用 `.NET Add-Type` 将 `_sfx_stub.cs`（C# 源码）编译为 `_sfx_stub.exe`（自解压桩程序，约 8KB）
3. 二进制拼接：`_sfx_stub.exe` + 标记 `WHALEPET_ZIP_DATA_START` + `_bundle.zip` → 最终的 `WhalePetInstaller.exe`
4. 清理临时文件 `_bundle.zip` 和 `_sfx_stub.exe`

**完成标志：** 控制台输出 `SUCCESS: WhalePetInstaller.exe` 和文件大小

产物位置：`E:\All-Code\python-Code\whale-desktop-pet\WhalePetInstaller.exe`

### 打包产物说明

| 项目 | 值 |
|------|-----|
| 文件名 | `WhalePetInstaller.exe` |
| 体积 | 约 **1.54 GB**（Python 运行时 ~60MB + PySide6 ~200MB + 动画资源 ~1.2GB） |
| 类型 | 自解压安装程序（SFX） |
| 分发方式 | 可直接放到 `安装程序exe/` 目录或上传到网盘分发 |

> 体积大是因为内嵌了完整的 Python 运行时、PySide6（含 WebEngine）和 106 个高清 WebP 动画。用户双击后 SFX 桩程序会先弹出安装界面，确认后再解压到目标目录。

### 安装流程（用户视角）

用户双击 `WhalePetInstaller.exe` 后：

1. **弹出安装界面**：选择安装目录（默认 `C:\Program Files\DSH-FatFish`）
2. **解压**：将便携 Python、源码、资源解压到所选目录
3. **创建快捷方式**：桌面和开始菜单各一个
4. **注册卸载信息**：控制面板 → 程序和功能中可见「鲸鱼娘桌宠」
5. **完成**：可勾选立即启动

卸载方式：控制面板 → 程序和功能 → 鲸鱼娘桌宠 → 卸载

### 目录结构说明

```
whale-desktop-pet/
├── main.py                 # 启动入口
├── pet_window.py           # 主窗口（动画播放、拖拽、托盘、菜单）
├── pet_config.py           # 配置持久化
├── animations.py           # 动画目录与 gif_path() 解析
├── gif_player.py           # GIF/WebP 播放器
├── ai_chat.py              # AI 对话模块（多服务商）
├── ai_monitor.py           # AI 编程工具状态监测
├── balance.py              # 余额提醒
├── splash.py               # 启动动画窗口
├── requirements.txt        # 依赖清单
├── 启动动画.mp4            # 启动视频
├── 圆角-蓝色大肥鱼.ico      # 程序图标
├── AI聊天头像.png          # AI 对话头像
├── 白色米饭.png            # 资源图片
├── assets/
│   ├── gif/                # 低清 GIF 动画（备用）
│   └── gif_hd/             # 高清 WebP 动画（主用）
├── installer/
│   ├── build.py            # 构建脚本 → 生成 installer_bundle/
│   ├── installer.py        # 安装程序 GUI（build.py 会复制到 bundle）
│   └── uninstaller.py      # 卸载程序（build.py 会复制到 bundle）
├── installer_bundle/       # ⚠️ 第一步产物（中间目录，build.py 生成）
├── make_sfx.ps1            # SFX 打包脚本 → 生成单文件 EXE
├── _sfx_stub.cs            # SFX 自解压桩程序源码（C#，无需编译预产物）
├── WhalePetInstaller.exe   # ✅ 最终产物（make_sfx.ps1 生成，约 1.54 GB）
└── 安装程序exe/            # 存放历史版本 EXE 的目录
```

### 重新打包的清理建议

| 目录/文件 | 性质 | 可否删除 | 影响 |
|-----------|------|---------|------|
| `installer_bundle/` | 中间产物 | ✅ 可删 | 重新打包时 `build.py` 会自动重建 |
| `WhalePetInstaller.exe` | 最终产物 | ✅ 可删 | 重新运行 `make_sfx.ps1` 会重建 |
| `__pycache__/` | Python 缓存 | ✅ 可删 | 无影响 |
| `安装程序exe/` | 历史版本存档 | ✅ 可删 | 仅影响旧版本存档 |
| `installer/build.py` | 打包脚本 | ❌ 勿删 | 打包依赖 |
| `installer/installer.py` | 安装界面源码 | ❌ 勿删 | 打包依赖 |
| `installer/uninstaller.py` | 卸载源码 | ❌ 勿删 | 打包依赖 |
| `make_sfx.ps1` | SFX 脚本 | ❌ 勿删 | 打包依赖 |
| `_sfx_stub.cs` | C# 桩源码 | ❌ 勿删 | 打包依赖 |
| `assets/` | 动画资源 | ❌ 勿删 | 运行和打包都需要 |

**清理命令（重新打包前建议先清理）：**

```powershell
Remove-Item -Recurse -Force installer_bundle, __pycache__, WhalePetInstaller.exe
```

然后重新执行两步打包即可。

### 常见问题排查

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| `build.py` 下载依赖超时 | 未配置 pip 镜像源 | 执行 `pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple` |
| `build.py` 下载 Python 失败 | 华为云镜像暂时不可用 | 脚本会自动回退到复制系统 Python，无需处理 |
| `make_sfx.ps1` 报错"找不到 .NET" | 系统缺少 .NET Framework | 安装 .NET Framework 4.8 或更高版本 |
| 打包出来的 EXE 很小（只有几 MB） | `installer_bundle/` 是空的 | 重新运行 `python installer/build.py` |
| 运行 EXE 报杀毒软件拦截 | SFX 自解压可能误报 | 添加白名单，或换用数字签名证书签名 |
| 安装后设置窗口不弹出 | Qt.Tool + pythonw.exe 导致 | 代码中已添加 `SetForegroundWindow` 修复 |
| 点击设置"确定"后位置偏移 | setFixedSize 触发窗口重定位 | 代码中已用 `QTimer.singleShot` 延迟恢复位置修复 |

## 配置文件位置

每个实例的配置存放在：

```
C:\Users\<用户名>\.whale-pet\instances\<instance_id>\config.json
```

包含 API Key、窗口位置、缩放、AI 服务商、监测工具列表等设置。