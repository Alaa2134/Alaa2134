"""Track posting state: verse cursor, reciter rotation, and posted history."""
import json
import os
import random

from . import config


def load_verses() -> list:
    with open(config.VERSES_FILE, encoding="utf-8") as fh:
        return json.load(fh)


def load_state() -> dict:
    if os.path.exists(config.STATE_FILE):
        with open(config.STATE_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    return {"index": 0, "reciter_index": 0, "posted": []}


def save_state(state: dict) -> None:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.STATE_FILE, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)


def pick_reference(verses: list, state: dict, settings: dict) -> str:
    if config.VERSE_REFERENCE:
        return config.VERSE_REFERENCE
    if settings.get("selection_mode") == "random":
        recent = set(state.get("posted", [])[-(len(verses) // 2 or 1):])
        pool = [v for v in verses if v not in recent] or verses
        return random.choice(pool)
    index = state.get("index", 0) % len(verses)
    return verses[index]


def pick_reciter(state: dict, settings: dict) -> str:
    if config.AUDIO_EDITION_OVERRIDE:
        return config.AUDIO_EDITION_OVERRIDE
    mode = settings.get("reciter_mode", "fixed")
    pool = settings.get("reciter_pool") or [settings.get("reciter", "ar.alafasy")]
    if mode == "fixed":
        return settings.get("reciter", "ar.alafasy")
    if mode == "random":
        return random.choice(pool)
    # rotate
    index = state.get("reciter_index", 0) % len(pool)
    return pool[index]


def record(state, reference, settings, verses) -> dict:
    if not config.VERSE_REFERENCE and settings.get("selection_mode") != "random":
        state["index"] = (state.get("index", 0) + 1) % max(len(verses), 1)
    if not config.AUDIO_EDITION_OVERRIDE and settings.get("reciter_mode") == "rotate":
        pool = settings.get("reciter_pool") or ["ar.alafasy"]
        state["reciter_index"] = (state.get("reciter_index", 0) + 1) % max(len(pool), 1)

    posted = state.setdefault("posted", [])
    posted.append(reference)
    if len(posted) > 500:
        state["posted"] = posted[-500:]
    return state
