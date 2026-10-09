"""
资源打包脚本：把大资源拆分成多个 part zip（每包 < 45MB，适配 jsDelivr 限制）
"""
import os
import json
import zipfile
import hashlib
from pathlib import Path

ROOT = Path(__file__).parent.parent
BUNDLE_DIR = ROOT / "installer_bundle"
OUT_DIR = ROOT / "installer_resources"
MAX_PART_SIZE = 45 * 1024 * 1024


def calc_md5(filepath: Path) -> str:
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def zip_dir(src_dir: Path, zip_prefix: str) -> list:
    if not src_dir.exists():
        print(f"  skip (not exist): {src_dir}")
        return []

    parts = []
    part_idx = 1
    current_zip = None
    current_size = 0

    files = []
    for root, _, filenames in os.walk(src_dir):
        for fn in filenames:
            fp = Path(root) / fn
            arcname = fp.relative_to(src_dir)
            files.append((fp, arcname))

    files.sort(key=lambda x: str(x[1]))

    def open_new_part():
        nonlocal current_zip, current_size, part_idx
        if current_zip:
            current_zip.close()
        name = f"{zip_prefix}.part{part_idx:02d}.zip"
        path = OUT_DIR / name
        current_zip = zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED)
        current_size = 0
        part_idx += 1
        return path

    zip_path = open_new_part()

    for fp, arcname in files:
        fp_size = fp.stat().st_size
        if current_size + fp_size > MAX_PART_SIZE and current_size > 0:
            current_zip.close()
            md5 = calc_md5(zip_path)
            size = zip_path.stat().st_size
            parts.append({"name": zip_path.name, "size": size, "md5": md5})
            print(f"  done: {zip_path.name} ({size / 1024 / 1024:.1f} MB)")
            zip_path = open_new_part()

        current_zip.write(fp, arcname.as_posix())
        current_size += fp_size

    if current_zip:
        current_zip.close()
        md5 = calc_md5(zip_path)
        size = zip_path.stat().st_size
        parts.append({"name": zip_path.name, "size": size, "md5": md5})
        print(f"  done: {zip_path.name} ({size / 1024 / 1024:.1f} MB)")

    return parts


def main():
    OUT_DIR.mkdir(exist_ok=True)
    manifest = {"version": "1.0.0", "packages": {}}

    print("=" * 50)
    print("Packing Python runtime...")
    print("=" * 50)
    manifest["packages"]["python-runtime"] = {
        "target_dir": "python",
        "parts": zip_dir(BUNDLE_DIR / "python", "python-runtime"),
    }

    print("\n" + "=" * 50)
    print("Packing assets/gif...")
    print("=" * 50)
    manifest["packages"]["assets-gif"] = {
        "target_dir": "assets/gif",
        "parts": zip_dir(BUNDLE_DIR / "assets" / "gif", "assets-gif"),
    }

    print("\n" + "=" * 50)
    print("Packing assets/gif_hd...")
    print("=" * 50)
    manifest["packages"]["assets-gif-hd"] = {
        "target_dir": "assets/gif_hd",
        "parts": zip_dir(BUNDLE_DIR / "assets" / "gif_hd", "assets-gif-hd"),
    }

    total_size = 0
    for pkg in manifest["packages"].values():
        for p in pkg["parts"]:
            total_size += p["size"]

    manifest["total_size"] = total_size
    manifest_path = OUT_DIR / "resources_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 50)
    print(f"Done! Output: {OUT_DIR}")
    print(f"Total size: {total_size / 1024 / 1024:.1f} MB")
    print(f"Manifest: {manifest_path}")
    print("=" * 50)


if __name__ == "__main__":
    main()