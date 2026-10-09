"""
AI 编程工具状态监测模块
支持检测进程运行状态，并对部分工具读取本地会话数据
状态：working（正在工作）/ just_finished（工作完成）/ idle（在线空闲）
"""
import os
import json
import time
import subprocess
import tempfile
import multiprocessing
from pathlib import Path

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False

_CPU_COUNT = multiprocessing.cpu_count() or 4
CPU_ACTIVE_THRESHOLD = 15.0

_snapshot_file = Path(tempfile.gettempdir()) / "ai_monitor_snapshot.json"

def set_snapshot_instance(instance_id: str):
    global _snapshot_file
    _snapshot_file = Path(tempfile.gettempdir()) / f"ai_monitor_snapshot_{instance_id}.json"

WORKING_TIMEOUT = 20
FINISHED_TIMEOUT = 90

TOOLS = {
    "trae": {
        "label": "Trae",
        "processes": [],
        "data_source": "trae",
    },
    "claude_code": {
        "label": "Claude Code",
        "processes": ["claude.exe"],
        "data_source": "claude",
    },
    "copilot": {
        "label": "GitHub Copilot",
        "processes": [],
        "data_source": "copilot",
    },
    "cursor": {
        "label": "Cursor",
        "processes": ["cursor.exe"],
        "data_source": None,
    },
    "windsurf": {
        "label": "Windsurf",
        "processes": ["windsurf.exe"],
        "data_source": None,
    },
}


def _list_processes() -> set:
    try:
        out = subprocess.check_output(
            ["tasklist", "/NH", "/FO", "CSV"],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        names = set()
        for line in out.decode("gbk", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split('","')
            if parts:
                name = parts[0].strip('"').lower()
                names.add(name)
        return names
    except Exception:
        return set()


def _check_running(tool_key: str, procs: set) -> bool:
    info = TOOLS.get(tool_key)
    if not info:
        return False
    for p in info["processes"]:
        if p.lower() in procs:
            return True
    return False


def _get_process_cpu_time(proc_names: list) -> float:
    """获取指定进程的总CPU时间（用户+内核），单位秒"""
    if not _HAS_PSUTIL or not proc_names:
        return 0.0
    total = 0.0
    lower_names = [n.lower() for n in proc_names]
    try:
        for p in psutil.process_iter(["name", "pid"]):
            try:
                if p.info["name"] and p.info["name"].lower() in lower_names:
                    total += sum(p.cpu_times()[:2])
            except Exception:
                pass
    except Exception:
        pass
    return total


def _read_claude_status() -> dict:
    base = Path.home() / ".claude" / "projects"
    if not base.exists():
        return {}
    latest_file = None
    latest_time = 0
    for proj_dir in base.iterdir():
        if not proj_dir.is_dir():
            continue
        for f in proj_dir.glob("*.jsonl"):
            try:
                mt = f.stat().st_mtime
                if mt > latest_time:
                    latest_time = mt
                    latest_file = f
            except Exception:
                continue
    if not latest_file:
        return {}
    last_user = ""
    last_model = ""
    last_time_str = ""
    try:
        with open(latest_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for line in reversed(lines):
            try:
                obj = json.loads(line)
            except Exception:
                continue
            msg = obj.get("message", {})
            role = msg.get("role")
            if role == "assistant":
                if not last_model:
                    last_model = msg.get("model", "")
                content = msg.get("content", [])
                if isinstance(content, list):
                    for c in content:
                        if c.get("type") == "text" and c.get("text"):
                            last_time_str = obj.get("timestamp", "")
                            break
            elif role == "user":
                content = msg.get("content", [])
                if isinstance(content, list) and not last_user:
                    for c in content:
                        if c.get("type") == "text" and c.get("text"):
                            last_user = c["text"][:80]
                            break
            if last_user and last_model and last_time_str:
                break
    except Exception:
        pass
    return {
        "model": last_model,
        "last_user_message": last_user,
        "last_time": last_time_str,
        "file_mtime": latest_time,
    }


def _read_copilot_status() -> dict:
    base = Path.home() / ".copilot" / "session-state"
    if not base.exists():
        return {}
    latest_file = None
    latest_time = 0
    for sess_dir in base.iterdir():
        if not sess_dir.is_dir():
            continue
        f = sess_dir / "events.jsonl"
        if f.exists():
            try:
                mt = f.stat().st_mtime
                if mt > latest_time:
                    latest_time = mt
                    latest_file = f
            except Exception:
                continue
    if not latest_file:
        return {}
    total_tokens = 0
    last_event = ""
    last_time_str = ""
    try:
        with open(latest_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for line in reversed(lines[-50:]):
            try:
                obj = json.loads(line)
            except Exception:
                continue
            etype = obj.get("type", "")
            if not last_event:
                last_event = etype
                last_time_str = obj.get("timestamp", "")
            if etype == "session.shutdown":
                data = obj.get("data", {})
                td = data.get("tokenDetails", {})
                for k, v in td.items():
                    if isinstance(v, dict):
                        total_tokens += v.get("tokenCount", 0)
                break
    except Exception:
        pass
    return {
        "last_event": last_event,
        "total_tokens": total_tokens,
        "last_time": last_time_str,
        "file_mtime": latest_time,
    }


def _read_trae_status(procs: set = None) -> dict:
    if procs is None:
        procs = _list_processes()

    if "trae.exe" in procs:
        return {"running": True, "mode": "独立版 Trae IDE", "watch_procs": ["trae.exe"]}

    jb_prefixes = ("pycharm", "idea", "webstorm", "goland", "rider", "clion",
                   "datagrip", "rubymine", "phpstorm", "appcode")
    jb_running = any(p.startswith(jb_prefixes) for p in procs)
    if jb_running:
        try:
            jb_dir = Path.home() / "AppData" / "Roaming" / "JetBrains"
            if jb_dir.exists():
                for prod_dir in jb_dir.iterdir():
                    if not prod_dir.is_dir():
                        continue
                    trae_plugin = prod_dir / "plugins" / "marscode"
                    if trae_plugin.exists():
                        return {"running": True, "mode": f"JetBrains 插件 ({prod_dir.name})",
                                "watch_procs": ["ai-agent.exe"]}
        except Exception:
            pass

    if "code.exe" in procs:
        try:
            vscode_ext = Path.home() / ".vscode" / "extensions"
            if vscode_ext.exists():
                for ext in vscode_ext.iterdir():
                    if ext.is_dir() and "trae" in ext.name.lower():
                        return {"running": True, "mode": "VS Code 插件",
                                "watch_procs": ["ai-agent.exe"]}
        except Exception:
            pass

    return {"running": False}


def _load_snapshot() -> dict:
    try:
        if _snapshot_file.exists():
            with open(_snapshot_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_snapshot(snap: dict):
    try:
        with open(_snapshot_file, "w", encoding="utf-8") as f:
            json.dump(snap, f)
    except Exception:
        pass


def _is_cpu_active(cur_cpu: float, prev_cpu: float, now: float, prev_ts: float) -> bool:
    """根据CPU时间增量判断进程是否处于活跃工作状态"""
    if prev_cpu <= 0 or prev_ts <= 0:
        return True
    time_diff = now - prev_ts
    if time_diff < 1:
        return False
    cpu_diff = cur_cpu - prev_cpu
    if cpu_diff <= 0:
        return False
    cpu_percent = (cpu_diff / time_diff) * 100.0 / _CPU_COUNT
    return cpu_percent > CPU_ACTIVE_THRESHOLD


def _determine_state(activity_now: bool, last_activity: float, now: float) -> str:
    """根据活动时间判断状态"""
    if activity_now:
        return "working"
    if last_activity:
        elapsed = now - last_activity
        if elapsed < WORKING_TIMEOUT:
            return "working"
        elif elapsed < FINISHED_TIMEOUT:
            return "just_finished"
    return "idle"


def monitor(selected_tools: list) -> dict:
    procs = _list_processes()
    snap = _load_snapshot()
    now = time.time()
    result = {}

    for key in selected_tools:
        if key not in TOOLS:
            continue
        info = TOOLS[key]
        prev = snap.get(key, {})

        if info.get("data_source") == "trae":
            trae_info = _read_trae_status(procs)
            running = trae_info.get("running", False)
            status = {"running": running, "label": info["label"], "state": "idle"}
            if running:
                status["detail"] = trae_info
                watch_procs = trae_info.get("watch_procs", [])
                cpu = _get_process_cpu_time(watch_procs)
                prev_cpu = prev.get("cpu_time", 0)
                prev_ts = prev.get("timestamp", 0)
                activity_changed = _is_cpu_active(cpu, prev_cpu, now, prev_ts)
                last_activity = prev.get("last_activity_time", 0)
                if activity_changed:
                    last_activity = now
                state = _determine_state(activity_changed, last_activity, now)
                status["state"] = state
                snap[key] = {
                    "cpu_time": cpu,
                    "last_activity_time": last_activity,
                    "timestamp": now,
                }

        elif info["data_source"] == "claude":
            running = _check_running(key, procs)
            status = {"running": running, "label": info["label"], "state": "idle"}
            if running:
                detail = _read_claude_status()
                status["detail"] = detail
                file_mtime = detail.get("file_mtime", 0)
                prev_mtime = prev.get("file_mtime", 0)
                activity_changed = file_mtime > prev_mtime + 0.5
                last_activity = prev.get("last_activity_time", 0)
                if activity_changed:
                    last_activity = now
                state = _determine_state(activity_changed, last_activity, now)
                status["state"] = state
                snap[key] = {
                    "file_mtime": file_mtime,
                    "last_activity_time": last_activity,
                    "timestamp": now,
                }

        elif info["data_source"] == "copilot":
            running = _check_running(key, procs)
            status = {"running": running, "label": info["label"], "state": "idle"}
            if running:
                detail = _read_copilot_status()
                status["detail"] = detail
                file_mtime = detail.get("file_mtime", 0)
                prev_mtime = prev.get("file_mtime", 0)
                activity_changed = file_mtime > prev_mtime + 0.5
                last_activity = prev.get("last_activity_time", 0)
                if activity_changed:
                    last_activity = now
                state = _determine_state(activity_changed, last_activity, now)
                status["state"] = state
                snap[key] = {
                    "file_mtime": file_mtime,
                    "last_activity_time": last_activity,
                    "timestamp": now,
                }

        else:
            running = _check_running(key, procs)
            status = {"running": running, "label": info["label"], "state": "idle"}
            if running:
                cpu = _get_process_cpu_time(info["processes"])
                prev_cpu = prev.get("cpu_time", 0)
                prev_ts = prev.get("timestamp", 0)
                activity_changed = _is_cpu_active(cpu, prev_cpu, now, prev_ts)
                last_activity = prev.get("last_activity_time", 0)
                if activity_changed:
                    last_activity = now
                state = _determine_state(activity_changed, last_activity, now)
                status["state"] = state
                snap[key] = {
                    "cpu_time": cpu,
                    "last_activity_time": last_activity,
                    "timestamp": now,
                }

        result[key] = status

    _save_snapshot(snap)
    return result


def format_status_text(statuses: dict) -> str:
    lines = []
    for key, st in statuses.items():
        if not st.get("running"):
            continue
        label = st["label"]
        state = st.get("state", "idle")
        if state == "working":
            lines.append(f"{label}正在工作")
        elif state == "just_finished":
            lines.append(f"{label}工作完成")
        else:
            lines.append(f"{label}在线，空闲")
    return "\n".join(lines)