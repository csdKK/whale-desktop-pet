"""
构建在线安装器 EXE：
1. 编译 online_installer.cs 为 stub exe
2. 把 core.zip 嵌入到 exe 末尾
输出：安装程序exe/WhalePetOnlineInstaller.exe（约 4-5MB）
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
CS_PATH = ROOT / "installer" / "online_installer.cs"
CORE_ZIP = ROOT / "installer_bundle" / "core.zip"
STUB_EXE = ROOT / "_online_installer_stub.exe"
OUT_DIR = ROOT / "安装程序exe"
OUT_EXE = OUT_DIR / "WhalePetOnlineInstaller.exe"
MARKER = b"WHALEPET_CORE_ZIP_START"


def main():
    if not CORE_ZIP.exists():
        print(f"错误：找不到 {CORE_ZIP}")
        print("请先运行 python installer/build.py")
        sys.exit(1)

    OUT_DIR.mkdir(exist_ok=True)

    print("步骤 1/2: 编译 C# 安装器...")
    csc_paths = [
        r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
        r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe",
    ]
    csc = None
    for p in csc_paths:
        if os.path.exists(p):
            csc = p
            break

    refs = [
        "System.dll", "System.Net.Http.dll",
        "System.IO.Compression.dll", "System.IO.Compression.FileSystem.dll",
        "System.Windows.Forms.dll", "System.Drawing.dll", "System.Core.dll",
        "System.Web.Extensions.dll",
    ]
    cmd = [
        csc, "/nologo", "/target:winexe",
        f"/out:{STUB_EXE}",
        str(CS_PATH),
    ]
    for r in refs:
        cmd.append(f"/reference:{r}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("编译失败：")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)
    print("  编译成功")

    print("步骤 2/2: 嵌入 core.zip...")
    stub_bytes = STUB_EXE.read_bytes()
    core_bytes = CORE_ZIP.read_bytes()

    with open(OUT_EXE, "wb") as f:
        f.write(stub_bytes)
        f.write(MARKER)
        f.write(core_bytes)

    print(f"  输出: {OUT_EXE}")
    print(f"  大小: {OUT_EXE.stat().st_size / 1024 / 1024:.2f} MB")

    if STUB_EXE.exists():
        STUB_EXE.unlink()
    print("  清理临时文件")

    print("\n构建完成！")


if __name__ == "__main__":
    main()