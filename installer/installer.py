"""
鲸鱼娘桌宠 - 安装程序
用户选择安装目录（自动追加 DSH-FatFish），解压内嵌 Python 和源码，创建桌面快捷方式
"""
import os
import sys
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_NAME = "DSH-FatFish"
APP_DISPLAY = "鲸鱼娘桌宠"
INSTALL_FOLDER_NAME = "DSH-FatFish"
REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\DSH-FatFish"

# 源码目录（相对于安装包根目录）
SOURCE_DIRS = ["assets"]
SOURCE_FILES = [
    "main.py", "pet_window.py", "pet_config.py", "ai_monitor.py",
    "ai_chat.py", "balance.py", "animations.py", "gif_player.py",
    "splash.py", "requirements.txt",
    "启动动画.mp4", "圆角-蓝色大肥鱼.ico",
    "AI聊天头像.png", "白色米饭.png",
]


def get_python_dir():
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "python")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "python")


def get_source_root():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(here) == "installer":
        return os.path.dirname(here)
    return here


def get_python_exe(python_dir):
    return os.path.join(python_dir, "python.exe")


def get_desktop_dir():
    try:
        import ctypes
        from ctypes import wintypes
        CSIDL_DESKTOPDIRECTORY = 0x0010
        buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOPDIRECTORY, None, 0, buf)
        if buf.value:
            return buf.value
    except Exception:
        pass
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.exists(desktop):
        desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
    return desktop


def create_shortcut(target, work_dir, icon, shortcut_path, arguments=""):
    vbs = f'''Set oWS = WScript.CreateObject("WScript.Shell")
Set oLink = oWS.CreateShortcut("{shortcut_path}")
oLink.TargetPath = "{target}"
oLink.Arguments = "{arguments}"
oLink.WorkingDirectory = "{work_dir}"
oLink.IconLocation = "{icon}"
oLink.WindowStyle = 7
oLink.Save
'''
    vbs_file = os.path.join(os.environ.get("TEMP", "."), "_whale_shortcut.vbs")
    with open(vbs_file, "w", encoding="gbk") as f:
        f.write(vbs)
    cscript = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "cscript.exe")
    subprocess.run([cscript, "//nologo", vbs_file], capture_output=True)
    try:
        os.remove(vbs_file)
    except Exception:
        pass


def register_uninstall(install_dir, pythonw_exe):
    try:
        import winreg
        install_dir = os.path.normpath(install_dir)
        pythonw_exe = os.path.normpath(pythonw_exe)
        uninstaller_py = os.path.normpath(os.path.join(install_dir, "uninstaller.py"))

        uninstall_vbs = os.path.join(install_dir, "uninstall.vbs")
        with open(uninstall_vbs, "w", encoding="gbk") as f:
            f.write('Set WshShell = CreateObject("WScript.Shell")\n')
            f.write(f'WshShell.CurrentDirectory = "{install_dir}"\n')
            f.write(f'WshShell.Run """{pythonw_exe}"" ""{uninstaller_py}""", 0, False\n')

        wscript = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "wscript.exe")
        uninstall_cmd = f'"{wscript}" "{uninstall_vbs}"'

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_KEY) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_DISPLAY)
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, uninstall_cmd)
            winreg.SetValueEx(key, "QuietUninstallString", 0, winreg.REG_SZ, uninstall_cmd)
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ,
                              os.path.normpath(os.path.join(install_dir, "圆角-蓝色大肥鱼.ico")))
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "DSH")
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
    except Exception:
        pass


class InstallerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_DISPLAY} 安装程序")
        self.root.geometry("520x380")
        self.root.resizable(False, False)

        self.install_dir = tk.StringVar(
            value=os.path.join("C:\\", "Program Files", INSTALL_FOLDER_NAME)
        )

        self._build_ui()

    def _ensure_folder(self, path):
        path = path.strip().rstrip("\\/")
        if path and not path.endswith(INSTALL_FOLDER_NAME):
            path = os.path.join(path, INSTALL_FOLDER_NAME)
        return os.path.normpath(path)

    def _build_ui(self):
        pad = {"padx": 15, "pady": 8}

        title = tk.Label(self.root, text=f"{APP_DISPLAY}", font=("微软雅黑", 18, "bold"))
        title.pack(**pad)

        desc = tk.Label(
            self.root,
            text="欢迎安装鲸鱼娘桌宠。\n请选择安装目录，安装程序会自动创建 DSH-FatFish 文件夹。",
            font=("微软雅黑", 10),
            justify="left",
        )
        desc.pack(**pad)

        dir_frame = tk.Frame(self.root)
        dir_frame.pack(fill="x", **pad)

        tk.Label(dir_frame, text="安装目录：", font=("微软雅黑", 10)).pack(side="left")
        self.dir_entry = tk.Entry(dir_frame, textvariable=self.install_dir, font=("微软雅黑", 10))
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(dir_frame, text="浏览...", command=self._browse, font=("微软雅黑", 10)).pack(side="left")

        self.install_btn = tk.Button(
            self.root, text="安装", command=self._start_install,
            font=("微软雅黑", 12, "bold"), width=15, height=1, bg="#4a90d9", fg="white"
        )
        self.install_btn.pack(pady=10)

        self.progress = ttk.Progressbar(self.root, mode="determinate", length=460)
        self.progress.pack(pady=5)

        self.status_label = tk.Label(self.root, text="", font=("微软雅黑", 9), fg="#333")
        self.status_label.pack(pady=5)

    def _browse(self):
        path = filedialog.askdirectory(title="选择安装父目录")
        if path:
            full = os.path.join(path, INSTALL_FOLDER_NAME)
            self.install_dir.set(full)

    def _start_install(self):
        install_dir = self._ensure_folder(self.install_dir.get())
        if not install_dir:
            messagebox.showerror("错误", "请选择安装目录")
            return

        self.install_btn.config(state="disabled")
        threading.Thread(target=self._do_install, args=(install_dir,), daemon=True).start()

    def _set_status(self, text, progress=None):
        self.status_label.config(text=text)
        if progress is not None:
            self.progress["value"] = progress
        self.root.update_idletasks()

    def _do_install(self, install_dir):
        try:
            python_dir = get_python_dir()
            source_root = get_source_root()

            total_steps = 7
            step = 0

            step += 1
            self._set_status("创建安装目录...", step / total_steps * 100)
            os.makedirs(install_dir, exist_ok=True)

            step += 1
            self._set_status("复制 Python 运行环境（含依赖包）...", step / total_steps * 100)
            dest_python = os.path.join(install_dir, "python")
            if os.path.exists(dest_python):
                shutil.rmtree(dest_python, ignore_errors=True)
            shutil.copytree(python_dir, dest_python)
            python_exe = get_python_exe(dest_python)

            step += 1
            self._set_status("复制程序文件...", step / total_steps * 100)
            for name in SOURCE_FILES:
                src = os.path.join(source_root, name)
                if os.path.exists(src):
                    dst = os.path.join(install_dir, name)
                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst, ignore_errors=True)
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)

            for name in SOURCE_DIRS:
                src = os.path.join(source_root, name)
                if os.path.isdir(src):
                    dst = os.path.join(install_dir, name)
                    if os.path.exists(dst):
                        shutil.rmtree(dst, ignore_errors=True)
                    shutil.copytree(src, dst)

            step += 1
            self._set_status("创建启动脚本...", step / total_steps * 100)
            pythonw_exe = os.path.join(dest_python, "pythonw.exe")

            uninstaller_dst = os.path.join(install_dir, "uninstaller.py")
            uninstaller_src = os.path.join(source_root, "uninstaller.py")
            if not os.path.exists(uninstaller_src):
                uninstaller_src = os.path.join(source_root, "installer", "uninstaller.py")
            if os.path.exists(uninstaller_src):
                shutil.copy2(uninstaller_src, uninstaller_dst)

            step += 1
            self._set_status("创建桌面快捷方式...", step / total_steps * 100)
            desktop = get_desktop_dir()
            shortcut_path = os.path.join(desktop, f"{APP_DISPLAY}.lnk")
            if os.path.exists(shortcut_path):
                try:
                    os.remove(shortcut_path)
                except Exception:
                    pass
            icon_path = os.path.join(install_dir, "圆角-蓝色大肥鱼.ico")
            create_shortcut(pythonw_exe, install_dir, icon_path, shortcut_path, "main.py")

            step += 1
            self._set_status("注册卸载信息...", step / total_steps * 100)
            register_uninstall(install_dir, pythonw_exe)

            step += 1
            self._set_status("安装完成！", 100)
            messagebox.showinfo("安装完成", f"{APP_DISPLAY} 已成功安装到：\n{install_dir}\n\n桌面已创建快捷方式，双击即可运行。")
            self.root.destroy()

        except Exception as e:
            self._set_status(f"安装失败：{e}")
            messagebox.showerror("安装失败", str(e))
            self.install_btn.config(state="normal")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    InstallerApp().run()