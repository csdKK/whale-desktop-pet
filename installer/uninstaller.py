"""
鲸鱼娘桌宠 - 卸载程序
只删除本程序自己的文件，绝不删除用户原有的 Python 或其它文件
"""
import os
import sys
import shutil
import tkinter as tk
from tkinter import messagebox

APP_DISPLAY = "鲸鱼娘桌宠"
INSTALL_FOLDER_NAME = "DSH-FatFish"
REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\DSH-FatFish"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "DSH-FatFish"


def get_install_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def unregister_uninstall():
    try:
        import winreg
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REG_KEY)
    except Exception:
        pass


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


def remove_shortcuts():
    desktop = get_desktop_dir()
    shortcut = os.path.join(desktop, f"{APP_DISPLAY}.lnk")
    try:
        if os.path.exists(shortcut):
            os.remove(shortcut)
    except Exception:
        pass
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, RUN_NAME)
        winreg.CloseKey(key)
    except OSError:
        pass
    except Exception:
        pass


def remove_config():
    config_dir = os.path.join(os.path.expanduser("~"), ".whale-pet")
    try:
        if os.path.exists(config_dir):
            shutil.rmtree(config_dir, ignore_errors=True)
    except Exception:
        pass


def remove_temp_snapshots():
    import glob
    temp = os.environ.get("TEMP", "")
    if temp:
        pattern = os.path.join(temp, "ai_monitor_snapshot*.json")
        for f in glob.glob(pattern):
            try:
                os.remove(f)
            except Exception:
                pass


def is_safe_to_delete(path):
    norm = os.path.normpath(path).lower()
    if os.path.basename(norm) != "dsh-fatfish":
        return False
    return True


def kill_running_process(install_dir):
    try:
        import subprocess
        import time
        my_pid = os.getpid()
        ps_exe = os.path.join(
            os.environ.get("SystemRoot", r"C:\Windows"),
            "System32", "WindowsPowerShell", "v1.0", "powershell.exe",
        )
        escaped_dir = install_dir.replace("'", "''")
        cmd = (
            f"Get-Process pythonw -ErrorAction SilentlyContinue | "
            f"Where-Object {{ $_.Path -like '*{escaped_dir}*' -and $_.Id -ne {my_pid} }} | "
            f"Stop-Process -Force"
        )
        subprocess.run([ps_exe, "-NoProfile", "-Command", cmd], capture_output=True)
        time.sleep(1.5)
    except Exception:
        pass


def main():
    install_dir = get_install_dir()

    if not is_safe_to_delete(install_dir):
        messagebox.showerror(
            "卸载失败",
            f"检测到安装目录异常：{install_dir}\n为了安全起见，已取消卸载。",
        )
        return

    confirm = messagebox.askyesno(
        "卸载确认",
        f"确定要卸载 {APP_DISPLAY} 吗？\n\n将删除：\n- 安装目录：{install_dir}\n- 桌面快捷方式\n- 用户配置数据（API Key 等）\n\n此操作不可恢复。",
    )
    if not confirm:
        return

    kill_running_process(install_dir)

    root = tk.Tk()
    root.withdraw()

    try:
        unregister_uninstall()
        remove_shortcuts()
        remove_config()
        remove_temp_snapshots()

        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        temp_dir = os.environ.get("TEMP", ".")
        bat_dir = temp_dir
        bat_path = os.path.join(bat_dir, "_whale_cleanup.bat")
        sys32 = os.path.join(system_root, "System32")
        cmd_exe = os.path.join(sys32, "cmd.exe")
        taskkill_exe = os.path.join(sys32, "taskkill.exe")
        tasklist_exe = os.path.join(sys32, "tasklist.exe")
        ping_exe = os.path.join(sys32, "ping.exe")
        log_path = os.path.join(bat_dir, "_whale_cleanup.log")

        bat_content = (
            "@echo off\r\n"
            f"set \"INSTALLDIR={install_dir}\"\r\n"
            f"set \"LOG={log_path}\"\r\n"
            "echo start > \"%LOG%\"\r\n"
            f"\"{ping_exe}\" -n 4 127.0.0.1 >nul\r\n"
            "echo wait_done >> \"%LOG%\"\r\n"
            f"\"{taskkill_exe}\" /F /IM pythonw.exe >> \"%LOG%\" 2>&1\r\n"
            "echo taskkill_exit:%errorlevel% >> \"%LOG%\"\r\n"
            f"\"{ping_exe}\" -n 3 127.0.0.1 >nul\r\n"
            f"\"{tasklist_exe}\" /FI \"IMAGENAME eq pythonw.exe\" >> \"%LOG%\" 2>&1\r\n"
            ":remove_dir\r\n"
            "rmdir /S /Q \"%INSTALLDIR%\" >> \"%LOG%\" 2>&1\r\n"
            "echo rmdir_exit:%errorlevel% >> \"%LOG%\"\r\n"
            "if exist \"%INSTALLDIR%\" (\r\n"
            f"    \"{ping_exe}\" -n 2 127.0.0.1 >nul\r\n"
            "    goto remove_dir\r\n"
            ")\r\n"
            "echo done >> \"%LOG%\"\r\n"
            "del \"%~f0\"\r\n"
        )
        with open(bat_path, "w", encoding="gbk", newline="") as f:
            f.write(bat_content)

        subprocess = __import__("subprocess")
        subprocess.Popen(
            [cmd_exe, "/c", bat_path],
            creationflags=0x08000000,
            cwd=bat_dir,
        )

        messagebox.showinfo("卸载完成", f"{APP_DISPLAY} 已成功卸载。")
        os._exit(0)

    except Exception as e:
        messagebox.showerror("卸载失败", f"卸载过程中出错：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()