"""
上传 installer_resources/ 到 GitHub Release
需要 GitHub Personal Access Token（需要 repo 权限）
"""
import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

OWNER = "csdKK"
REPO = "whale-desktop-pet"
TAG = "v1.0.0"
RESOURCES_DIR = Path(__file__).parent.parent / "installer_resources"


def api_request(url, token, method="GET", data=None, headers=None):
    h = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "WhalePetUploader",
    }
    if headers:
        h.update(headers)

    if data is not None and not isinstance(data, bytes):
        data = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {body[:500]}")
        return e.code, json.loads(body) if body else {}


def get_or_create_release(token):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/tags/{TAG}"
    code, release = api_request(url, token)
    if code == 200:
        print(f"找到已有 Release: {release.get('name', TAG)}")
        return release

    url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases"
    data = {
        "tag_name": TAG,
        "name": f"鲸鱼娘桌宠 {TAG}",
        "body": "鲸鱼娘桌宠在线安装资源包\n\n包含 Python 运行环境、高清/低清动画资源。",
        "draft": False,
        "prerelease": False,
    }
    code, release = api_request(url, token, method="POST", data=data)
    if code != 201:
        raise Exception(f"创建 Release 失败: HTTP {code}")
    print(f"创建 Release 成功: {release['name']}")
    return release


def upload_asset(token, upload_url, filepath):
    name = filepath.name
    size = filepath.stat().st_size
    print(f"  上传: {name} ({size / 1024 / 1024:.1f} MB)")

    url = upload_url.replace("{?name,label}", f"?name={name}")
    with open(filepath, "rb") as f:
        data = f.read()

    headers = {"Content-Type": "application/zip"}
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"token {token}",
        "Content-Type": "application/zip",
        "User-Agent": "WhalePetUploader",
    }, method="POST")

    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        if e.code == 422 and "already exists" in body:
            print(f"    已存在，跳过")
            return 422
        print(f"    上传失败: HTTP {e.code}")
        return e.code


def main():
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        print("请设置环境变量 GITHUB_TOKEN（需要 repo 权限的 Personal Access Token）")
        print("创建 Token: https://github.com/settings/tokens")
        print("权限: repo (Full control of private repositories)")
        sys.exit(1)

    if not RESOURCES_DIR.exists():
        print(f"错误：找不到 {RESOURCES_DIR}")
        print("请先运行 python installer/pack_resources.py")
        sys.exit(1)

    files = sorted(RESOURCES_DIR.glob("*"))
    print(f"待上传文件数: {len(files)}")

    print("\n步骤 1/2: 获取或创建 Release...")
    release = get_or_create_release(token)
    upload_url = release["upload_url"]

    print(f"\n步骤 2/2: 上传资源到 Release...")
    success = 0
    for i, f in enumerate(files, 1):
        print(f"[{i}/{len(files)}] ", end="")
        code = upload_asset(token, upload_url, f)
        if code in (201, 422):
            success += 1

    print(f"\n上传完成！成功: {success}/{len(files)}")
    print(f"\nRelease 页面: https://github.com/{OWNER}/{REPO}/releases/tag/{TAG}")


if __name__ == "__main__":
    main()