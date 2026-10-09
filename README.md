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
- **提示词方案**：可保存/切换多套自定义系统提示词，内置系统提示词为默认方案
- **配置持久化**：所有设置（动画速度、窗口位置、AI 配置等）退出后自动保存，下次启动恢复

## 下载安装

### 在线安装器（推荐）

本项目采用「核心文件内嵌 + 大资源按需下载」的在线安装方案，安装器仅 **5.42 MB**，秒开不卡顿。

**下载地址：** [GitHub Release v1.0.0](https://github.com/csdKK/whale-desktop-pet/releases/download/v1.0.0/WhalePetOnlineInstaller.exe)

**安装步骤：**

1. 下载 `WhalePetOnlineInstaller.exe`（5.42 MB）并双击运行
2. 选择安装目录，点击「开始安装」
3. 等待资源下载完成（约 1.5GB，通过国内 CDN 镜像加速，约 6-7 分钟）
4. 安装完成后，桌面会出现「鲸鱼娘桌宠」快捷方式，双击即可启动
5. 桌宠也会出现在「控制面板 → 程序和功能」中，可随时完全卸载

**卸载：** 控制面板 → 程序和功能 → 鲸鱼娘桌宠 → 卸载（会自动删除安装目录、快捷方式和注册表项）

> 安装器会从以下 CDN 镜像源按顺序尝试下载（自动 fallback）：
> gh-proxy.com → ghproxy.net → ghps.cc → GitHub 直连

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
│   ├── build.py            # 打包核心文件到 core.zip
│   ├── pack_resources.py   # 将大资源拆分为 <45MB 的 part zip
│   ├── upload_to_release.py# 批量上传资源到 GitHub Release
│   └── online_installer.cs # C# 在线安装器源码
├── build_online_installer.py # 编译 C# + 嵌入 core.zip
└── 安装程序exe/
    └── WhalePetOnlineInstaller.exe  # 最终产物（约 5.42 MB）
```

## 打包成在线安装器 EXE

### 前置条件

| 条件 | 说明 |
|------|------|
| 操作系统 | Windows 10/11 |
| Python | 3.11（用于运行打包脚本） |
| .NET Framework | 系统自带（用于编译 C# 安装器） |
| GitHub Token | 仅当需要上传资源到 Release 时需要 |

### 打包流程

#### 1. 打包核心文件 → `core.zip`

```bash
python installer/build.py
```

将源码、启动动画、图标等核心文件打包为 `core.zip`，由安装器内嵌分发。

#### 2. 拆分大资源 → `installer_resources/`

```bash
python installer/pack_resources.py
```

将 `python/`、`assets/gif/`、`assets/gif_hd/` 拆分为多个 <45MB 的 part zip，并生成 `resources_manifest.json`（含每个 part 的 MD5 和大小）。

> 仅当大资源有变动时才需要执行此步。

#### 3. 上传资源到 GitHub Release

```powershell
$env:GITHUB_TOKEN = "你的 GitHub Token"
python installer/upload_to_release.py
```

将 `installer_resources/` 下的所有 part 文件和清单上传到 GitHub Release（tag: `v1.0.0`）。

> 仅当资源有变动时才需要执行此步。需要提前在 GitHub 创建仓库并生成 Token。

#### 4. 编译在线安装器 EXE

```bash
python build_online_installer.py
```

- 编译 `installer/online_installer.cs` 为 EXE
- 将 `core.zip` 嵌入到 EXE 末尾（通过标记 `WHALEPET_CORE_ZIP_START` 定位）
- 输出：`安装程序exe/WhalePetOnlineInstaller.exe`（约 5.42 MB）

#### 5. 上传安装器到 GitHub Release

将 `安装程序exe/WhalePetOnlineInstaller.exe` 上传到 GitHub Release（v1.0.0），方便用户下载。

可通过网页手动上传：打开 Release 编辑页 → 拖入 EXE → Update release。

### 打包产物说明

| 项目 | 值 |
|------|-----|
| 文件名 | `WhalePetOnlineInstaller.exe` |
| 体积 | 约 **5.42 MB** |
| 类型 | 在线安装器（核心文件内嵌，大资源从 CDN 下载） |
| 安装时下载 | 约 1.5GB（46 个 part 文件） |
| 分发方式 | 从 GitHub Release 下载，双击即可安装 |

### 常见改动对应的打包步骤

| 改动内容 | 需要执行的步骤 |
|---------|---------------|
| 修改了源代码（.py 文件） | 步骤 1 + 步骤 4 + 步骤 5 |
| 修改了启动动画/图标 | 步骤 1 + 步骤 4 + 步骤 5 |
| 增删了 gif 动画 | 步骤 2 + 步骤 3 + 步骤 4 + 步骤 5 |
| 修改了 Python 运行时/依赖 | 步骤 2 + 步骤 3 + 步骤 4 + 步骤 5 |
| 修改了安装器界面逻辑 | 步骤 4 + 步骤 5 |

## 安装器工作原理

```
用户双击 WhalePetOnlineInstaller.exe (5.42MB)
    ↓
1. 从 GitHub Release 下载 resources_manifest.json（多镜像 fallback）
    ↓
2. 显示总下载大小和文件数，等待用户确认
    ↓
3. 逐个下载 46 个 part zip，每个都做 MD5 校验
    ↓
4. 解压所有 part 到安装目录
    ↓
5. 解压内嵌的 core.zip（源码 + mp4 + ico）
    ↓
6. 创建桌面快捷方式 + 开始菜单项
    ↓
7. 写入注册表（控制面板可见）
    ↓
8. 生成 uninstall.bat
    ↓
✅ 安装完成
```

## 配置文件位置

每个实例的配置存放在：

```
C:\Users\<用户名>\.whale-pet\instances\<instance_id>\config.json
```

包含 API Key、窗口位置、缩放、AI 服务商、监测工具列表、动画速度、提示词方案等设置。

## 常见问题排查

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 安装时下载很慢 | 默认直连 GitHub 慢 | 安装器已配置国内镜像（gh-proxy.com 优先），约 4MB/s |
| 安装时下载失败 | 网络波动 | 安装器会自动尝试多个镜像源，可重新安装 |
| 安装后设置窗口不弹出 | Qt.Tool + pythonw.exe 导致 | 代码中已添加 `SetForegroundWindow` 修复 |
| 点击设置"确定"后位置偏移 | setFixedSize 触发窗口重定位 | 代码中已用保存位置 + `move()` 恢复修复 |
| 卸载后还有残留 | 旧版注册表项 | 新版安装器已修复，uninstall.bat 会清理注册表 |