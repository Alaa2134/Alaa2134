"""Runtime settings shared by the daily job and the web dashboard.

Stored in data/settings.json so the dashboard can change behaviour without
touching code. Environment variables still win for one-off overrides.
"""
import json
import os

from . import config

DEFAULTS = {
    "reciter_mode": "rotate",          # fixed | rotate | random
    "reciter": "ar.alafasy",           # used when reciter_mode == fixed
    "reciter_pool": ["ar.alafasy"],    # used when reciter_mode in (rotate, random)
    "selection_mode": "sequential",    # sequential | random
    "hashtags": config.CAPTION_HASHTAGS,
    "tail_seconds": config.TAIL_SECONDS,
    "background_mode": "gradient",     # gradient | video | auto
}


def load_settings() -> dict:
    data = dict(DEFAULTS)
    if os.path.exists(config.SETTINGS_FILE):
        with open(config.SETTINGS_FILE, encoding="utf-8") as fh:
            data.update(json.load(fh))
    if not data.get("reciter_pool"):
        data["reciter_pool"] = [data.get("reciter", "ar.alafasy")]
    return data


def save_settings(settings: dict) -> dict:
    current = load_settings()
    allowed = set(DEFAULTS)
    current.update({k: v for k, v in settings.items() if k in allowed})
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.SETTINGS_FILE, "w", encoding="utf-8") as fh:
        json.dump(current, fh, ensure_ascii=False, indent=2)
    return current


def load_reciters() -> list:
    with open(config.RECITERS_FILE, encoding="utf-8") as fh:
        return json.load(fh)


def load_surahs() -> list:
    with open(config.SURAHS_FILE, encoding="utf-8") as fh:
        return json.load(fh)


def reciter_name(reciter_id: str) -> str:
    for r in load_reciters():
        if r["id"] == reciter_id:
            return r["name"]
    return reciter_id
