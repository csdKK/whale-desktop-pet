"""
配置持久化：配置存放在 ~/.whale-pet/config.json
所有实例共享同一份配置，最后一个退出的实例写入的配置会保留。
"""
import json
import os

BASE_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".whale-pet")
_CONFIG_FILE = os.path.join(BASE_CONFIG_DIR, "config.json")

DEFAULTS = {
    "api_key": "",
    "pos_x": -1,
    "pos_y": -1,
    "scale": 1.5,
    "mirrored": False,
    "auto_action_sec": 30,
    "balance_refresh_sec": 180,
    "balance_cap": 20.0,
    "snap_enabled": True,
    "on_top": True,
    "last_balance": 0.0,
    "ai_provider": "none",
    "ai_model": "",
    "ai_api_base": "",
    "ai_api_key": "",
    "ai_system_prompt": "",
    "ai_stream": True,
    "monitor_enabled": False,
    "monitor_tools": [],
    "monitor_interval": 15,
    "auto_start": False,
    "anim_speed": 1.0,
    "ai_presets": [],
    "ai_active_preset": "__system__",
}


def load() -> dict:
    cfg = dict(DEFAULTS)
    try:
        migrated = False
        if os.path.exists(_CONFIG_FILE):
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            cfg.update(user_cfg)

            old_prompt = user_cfg.get("ai_system_prompt", "")
            if old_prompt and "ai_presets" not in user_cfg:
                cfg["ai_presets"] = [{"name": "自定义", "text": old_prompt}]
                cfg["ai_active_preset"] = "自定义"
                migrated = True

        if migrated:
            save(cfg)
    except Exception:
        pass
    return cfg


def save(cfg: dict):
    try:
        os.makedirs(os.path.dirname(_CONFIG_FILE), exist_ok=True)
        with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass