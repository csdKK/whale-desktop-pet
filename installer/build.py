"""
构建离线安装包
基于系统 Python 创建便携运行环境 + 下载依赖 wheels，与源码一起打包
最终生成 installer_bundle/ 目录，运行 installer.bat 即可安装
"""
import os
import sys
import shutil
import subprocess
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLE_DIR = os.path.join(ROOT, "installer_bundle")

PY_MIRROR = "https://mirrors.huaweicloud.com/python/3.11.9/python-3.11.9-embed-amd64.zip"
PIP_INDEX = "https://pypi.tuna.tsinghua.edu.cn/simple"

WHEELS = ["shiboken6", "PySide6", "Pillow", "psutil"]


def copy_tkinter(python_dir):
    """从系统 Python 复制 tkinter 运行时到嵌入式 Python"""
    sys_python = sys.prefix
    dlls_dir = os.path.join(python_dir, "DLLs")
    os.makedirs(dlls_dir, exist_ok=True)

    tkinter_src = os.path.join(sys_python, "Lib", "tkinter")
    if os.path.isdir(tkinter_src):
        tkinter_dst = os.path.join(python_dir, "Lib", "tkinter")
        if os.path.exists(tkinter_dst):
            shutil.rmtree(tkinter_dst, ignore_errors=True)
        shutil.copytree(tkinter_src, tkinter_dst)

    for name in ["_tkinter.pyd", "tcl86t.dll", "tk86t.dll"]:
        src = os.path.join(sys_python, "DLLs", name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dlls_dir, name))

    tcl_src = os.path.join(sys_python, "tcl")
    if os.path.isdir(tcl_src):
        tcl_dst = os.path.join(python_dir, "tcl")
        if os.path.exists(tcl_dst):
            shutil.rmtree(tcl_dst, ignore_errors=True)
        shutil.copytree(tcl_src, tcl_dst)
    print("  tkinter 运行时已就绪")


def cleanup_pyside(python_dir):
    """清理 PySide6 中运行时不需要的开发文件，减小体积并避免路径过长"""
    site_packages = os.path.join(python_dir, "Lib", "site-packages")
    pyside_dir = os.path.join(site_packages, "PySide6")
    if not os.path.isdir(pyside_dir):
        return

    remove_dirs = ["doc", "include", "typesystems", "glue", "metatypes", "support", "scripts", "QtAsyncio"]
    for d in remove_dirs:
        p = os.path.join(pyside_dir, d)
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)

    skip_qml_modules = {
        "Qt3D", "Qt5Compat", "QtCharts", "QtDataVisualization", "QtGraphs",
        "QtLocation", "QtPositioning", "QtQuick3D", "QtRemoteObjects", "QtScxml",
        "QtSensors", "QtTest", "QtTextToSpeech", "QtWebChannel", "QtWebEngine",
        "QtWebSockets", "QtWebView", "QtPdf", "QtSpatialAudio", "QtVirtualKeyboard",
        "QtQuick3D", "QtBluetooth", "QtNfc", "QtSerialPort", "QtSerialBus",
        "QtNetworkAuth", "QtOpcUa", "QtCoap", "QtMqtt",
    }
    qml_dir = os.path.join(pyside_dir, "qml")
    if os.path.isdir(qml_dir):
        for name in os.listdir(qml_dir):
            if name in skip_qml_modules:
                shutil.rmtree(os.path.join(qml_dir, name), ignore_errors=True)

    for root, dirs, files in os.walk(site_packages):
        for d in list(dirs):
            if d in ("__pycache__", "objects-Debug", "objects-RelWithDebInfo"):
                shutil.rmtree(os.path.join(root, d), ignore_errors=True)
        for f in files:
            if f.endswith((".lib", ".exp", ".pdb", ".obj", ".cpp", ".h")):
                try:
                    os.remove(os.path.join(root, f))
                except Exception:
                    pass

    resources_dir = os.path.join(pyside_dir, "resources")
    if os.path.isdir(resources_dir):
        for f in os.listdir(resources_dir):
            fp = os.path.join(resources_dir, f)
            if ".debug." in f or "qtwebengine" in f.lower() or f == "v8_context_snapshot.bin":
                try:
                    os.remove(fp)
                except Exception:
                    pass

    translations_dir = os.path.join(pyside_dir, "translations")
    if os.path.isdir(translations_dir):
        for f in os.listdir(translations_dir):
            if not f.startswith("qt_zh") and not f.startswith("qtbase_zh"):
                try:
                    os.remove(os.path.join(translations_dir, f))
                except Exception:
                    pass

    keep_modules = {
        "Core", "Gui", "Widgets", "Multimedia", "MultimediaWidgets",
        "Network", "Svg", "SvgWidgets", "OpenGL", "OpenGLWidgets",
        "HttpServer", "StateMachine", "CanvasPainter", "AxContainer",
    }
    remove_keywords = [
        "3D", "5Compat", "Charts", "DataVisualization", "Graphs",
        "Location", "Positioning", "Quick", "Qml", "RemoteObjects",
        "Scxml", "Sensors", "Serial", "SpatialAudio", "Test",
        "TextToSpeech", "WebChannel", "WebEngine", "WebSockets",
        "WebView", "Pdf", "VirtualKeyboard", "Bluetooth", "Nfc",
        "NetworkAuth", "OpcUa", "Coap", "Mqtt", "Designer",
        "Help", "Sql", "PrintSupport", "Xml", "Concurrent",
        "DBus", "UiTools",
    ]
    for f in os.listdir(pyside_dir):
        fp = os.path.join(pyside_dir, f)
        if not os.path.isfile(fp):
            continue
        if f.endswith((".dll", ".pyd")):
            name_no_ext = os.path.splitext(f)[0]
            if name_no_ext.startswith("Qt6"):
                name_no_ext = name_no_ext[3:]
            if name_no_ext in keep_modules:
                continue
            if any(name_no_ext.startswith(kw) for kw in remove_keywords):
                try:
                    os.remove(fp)
                except Exception:
                    pass
        elif f.endswith(".pyi"):
            module_name = f.replace(".pyi", "")
            if module_name.startswith("Qt"):
                module_name = module_name[2:]
            if any(module_name.startswith(kw) for kw in remove_keywords):
                try:
                    os.remove(fp)
                except Exception:
                    pass

    plugins_dir = os.path.join(pyside_dir, "plugins")
    if os.path.isdir(plugins_dir):
        keep_plugins = {
            "platforms", "imageformats", "multimedia", "tls", "styles",
            "iconengines", "generic", "vectorimageformats",
            "platforminputcontexts", "renderplugins",
        }
        for name in os.listdir(plugins_dir):
            if name not in keep_plugins:
                shutil.rmtree(os.path.join(plugins_dir, name), ignore_errors=True)

    print("  PySide6 已清理多余开发文件")



def download_python_embed():
    import urllib.request
    embed_zip = os.path.join(BUNDLE_DIR, "python-embed.zip")
    if os.path.exists(embed_zip) and os.path.getsize(embed_zip) > 1_000_000:
        return embed_zip
    print("  尝试从华为云镜像下载 Python 嵌入式环境...")
    try:
        urllib.request.urlretrieve(PY_MIRROR, embed_zip)
        return embed_zip
    except Exception as e:
        print(f"  下载失败: {e}")
        return None


def build_portable_python_from_system():
    """从系统 Python 复制创建便携环境"""
    python_dir = os.path.join(BUNDLE_DIR, "python")
    sys_python = sys.prefix
    print(f"  从系统 Python 复制: {sys_python}")
    if os.path.exists(python_dir):
        shutil.rmtree(python_dir, ignore_errors=True)
    os.makedirs(python_dir, exist_ok=True)

    skip_dirs = {"__pycache__", "pip", "setuptools", "wheel", "tcl", "tk",
                 "Tools", "Doc", "include", "libs", "Scripts", "share",
                 "lib2to3", "test", "tests", "idlelib", "ensurepip"}
    skip_files = {"pythonw.exe"}

    for item in os.listdir(sys_python):
        src = os.path.join(sys_python, item)
        dst = os.path.join(python_dir, item)
        if os.path.isdir(src):
            if item in skip_dirs or item.startswith("Lib"):
                if item == "Lib":
                    os.makedirs(dst, exist_ok=True)
                    for sub in os.listdir(src):
                        ssub = os.path.join(src, sub)
                        dsub = os.path.join(dst, sub)
                        if sub in skip_dirs:
                            continue
                        if os.path.isdir(ssub):
                            shutil.copytree(ssub, dsub, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                        else:
                            shutil.copy2(ssub, dsub)
                continue
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            if item in skip_files:
                continue
            shutil.copy2(src, dst)

    for d in glob.glob(os.path.join(python_dir, "**", "__pycache__"), recursive=True):
        shutil.rmtree(d, ignore_errors=True)

    return python_dir


def main():
    os.makedirs(BUNDLE_DIR, exist_ok=True)
    python_dir = os.path.join(BUNDLE_DIR, "python")
    wheels_dir = os.path.join(python_dir, "wheels")

    print("=" * 50)
    print("步骤 1/4: 准备 Python 运行环境")
    print("=" * 50)

    embed_zip = download_python_embed()
    if embed_zip:
        import zipfile
        if os.path.exists(python_dir):
            shutil.rmtree(python_dir, ignore_errors=True)
        os.makedirs(python_dir)
        with zipfile.ZipFile(embed_zip, "r") as z:
            z.extractall(python_dir)
        pth_files = glob.glob(os.path.join(python_dir, "python*._pth"))
        for pth in pth_files:
            with open(pth, "w", encoding="utf-8", newline="") as f:
                f.write("python311.zip\n.\nLib\nLib\\site-packages\nDLLs\n\nimport site\n")
        print("  使用嵌入式 Python")
    else:
        build_portable_python_from_system()
        print("  使用系统 Python 副本")

    python_exe = os.path.join(python_dir, "python.exe")
    sys_python_exe = sys.executable

    print("=" * 50)
    print("步骤 2/4: 下载并安装依赖包")
    print("=" * 50)
    os.makedirs(wheels_dir, exist_ok=True)

    for pkg in WHEELS:
        print(f"  下载 {pkg} wheel...")
        subprocess.run(
            [sys_python_exe, "-m", "pip", "download", pkg, "-d", wheels_dir,
             "--only-binary=:all:", "-i", PIP_INDEX],
            cwd=python_dir
        )

    print("  安装依赖到嵌入式 Python...")
    site_packages = os.path.join(python_dir, "Lib", "site-packages")
    os.makedirs(site_packages, exist_ok=True)
    subprocess.run(
        [sys_python_exe, "-m", "pip", "install", "--no-index", "--force-reinstall",
         "--find-links", wheels_dir, "--target", site_packages] + WHEELS,
        cwd=python_dir
    )

    copy_tkinter(python_dir)
    cleanup_pyside(python_dir)

    wheels_dir = os.path.join(python_dir, "wheels")
    if os.path.isdir(wheels_dir):
        shutil.rmtree(wheels_dir, ignore_errors=True)
        print("  已清理 wheels 缓存目录")

    embed_zip = os.path.join(BUNDLE_DIR, "python-embed.zip")
    if os.path.exists(embed_zip):
        os.remove(embed_zip)
        print("  已清理 python-embed.zip")

    print("=" * 50)
    print("步骤 3/4: 复制源码和资源")
    print("=" * 50)
    source_files = [
        "main.py", "pet_window.py", "pet_config.py", "ai_monitor.py",
        "ai_chat.py", "balance.py", "animations.py", "gif_player.py",
        "splash.py", "requirements.txt",
        "启动动画.mp4", "圆角-蓝色大肥鱼.ico",
    ]
    source_dirs = ["assets"]

    for name in source_files:
        src = os.path.join(ROOT, name)
        dst = os.path.join(BUNDLE_DIR, name)
        if os.path.exists(src):
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst, ignore_errors=True)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            print(f"  复制: {name}")

    for name in source_dirs:
        src = os.path.join(ROOT, name)
        dst = os.path.join(BUNDLE_DIR, name)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(src, dst)
            print(f"  复制目录: {name}")

    installer_src = os.path.join(ROOT, "installer", "installer.py")
    uninstaller_src = os.path.join(ROOT, "installer", "uninstaller.py")
    shutil.copy2(installer_src, os.path.join(BUNDLE_DIR, "installer.py"))
    shutil.copy2(uninstaller_src, os.path.join(BUNDLE_DIR, "uninstaller.py"))

    print("=" * 50)
    print("步骤 4/4: 生成启动脚本")
    print("=" * 50)
    readme = os.path.join(BUNDLE_DIR, "安装说明.txt")
    with open(readme, "w", encoding="utf-8") as f:
        f.write("鲸鱼娘桌宠 - 离线安装包\n")
        f.write("=" * 40 + "\n\n")
        f.write("安装方法：\n")
        f.write("1. 双击运行 installer.bat\n")
        f.write("2. 选择安装目录（程序会自动创建 DSH-FatFish 文件夹）\n")
        f.write("3. 点击安装\n")
        f.write("4. 安装完成后，桌面会出现快捷方式\n\n")
        f.write("卸载方法：\n")
        f.write("1. 打开 控制面板 -> 程序和功能\n")
        f.write("2. 找到 鲸鱼娘桌宠，点击卸载\n")

    installer_bat = os.path.join(BUNDLE_DIR, "installer.bat")
    with open(installer_bat, "w", encoding="gbk") as f:
        f.write("@echo off\n")
        f.write('cd /d "%~dp0"\n')
        f.write('python\\python.exe installer.py\n')

    print("=" * 50)
    print(f"构建完成！安装包目录：{BUNDLE_DIR}")
    print(f"请运行 installer.bat 进行安装")
    print("=" * 50)


if __name__ == "__main__":
    main()