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

本项目采用「便携 Python + 源码 + 资源」的离线安装包方案，最终产物为单文件 `WhalePetInstaller.exe`。

### 第一步：生成安装包目录

在项目根目录运行：

```bash
python installer/build.py
```

`build.py` 会执行以下步骤：

1. 下载嵌入式 Python 3.11.9（华为云镜像），失败则回退到复制系统 Python
2. 下载并安装依赖 wheel（PySide6、Pillow、psutil，清华镜像）
3. 复制 tkinter 运行时，并清理 PySide6 中不需要的开发文件（减小体积）
4. 复制源码与 `assets/` 资源到 `installer_bundle/`
5. 复制 `installer.py`、`uninstaller.py`，生成 `installer.bat` 与 `安装说明.txt`

完成后得到 `installer_bundle/` 目录，结构如下：

```
installer_bundle/
├── python/                 # 便携 Python 运行环境（含 PySide6 等依赖）
├── assets/                 # 动画资源副本
├── main.py / pet_window.py / ...   # 源码
├── installer.py            # 安装程序
├── uninstaller.py          # 卸载程序
├── installer.bat           # 入口批处理
└── 安装说明.txt
```

> 此时可直接双击 `installer_bundle/installer.bat` 测试安装流程。

### 第二步：用 SFX 方式打包成单文件 exe

在项目根目录运行（无需安装 PyInstaller，只需系统自带 .NET）：

```bash
powershell -ExecutionPolicy Bypass -File make_sfx.ps1
```

`make_sfx.ps1` 会执行以下步骤：

1. 把 `installer_bundle/` 压缩为 `_bundle.zip`（最优压缩）
2. 用 .NET 的 `Add-Type` 将 `_sfx_stub.cs` 编译为 `_sfx_stub.exe`（自解压桩程序）
3. 将「桩 EXE + 标记 `WHALEPET_ZIP_DATA_START` + ZIP 数据」拼接为最终的 `WhalePetInstaller.exe`，输出到项目根目录

完成后得到单文件 `WhalePetInstaller.exe`，可将其放到 `安装程序exe/` 目录。

> 说明：由于内嵌了完整的 Python 运行时、PySide6 以及 106 个高清动画，最终 exe 体积约 1.5 GB，这是正常现象。

### 第三步：分发安装

用户双击 `WhalePetInstaller.exe`：

1. 弹出安装目录选择窗口（默认 `C:\Program Files\DSH-FatFish`）
2. 解压便携 Python、源码、资源到所选目录
3. 创建桌面快捷方式
4. 注册卸载信息（控制面板可见）

卸载方式：控制面板 → 程序和功能 → 鲸鱼娘桌宠 → 卸载。

## 重新打包的清理建议

`installer_bundle/` 与 `安装程序exe/` 都是构建产物，不影响源码。需要重新打包时直接运行 `python installer/build.py` 即可重新生成。

## 配置文件位置

每个实例的配置存放在：

```
C:\Users\<用户名>\.whale-pet\instances\<instance_id>\config.json
```

包含 API Key、窗口位置、缩放、AI 服务商、监测工具列表等设置。