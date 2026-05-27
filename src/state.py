"""Track which verses have been posted so the daily job does not repeat itself."""
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
    return {"index": 0, "posted": []}


def save_state(state: dict) -> None:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.STATE_FILE, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)


def pick_reference(verses: list, state: dict) -> str:
    """Choose the next verse reference based on the configured selection mode."""
    if config.VERSE_REFERENCE:
        return config.VERSE_REFERENCE

    if config.SELECTION_MODE == "random":
        recent = set(state.get("posted", [])[-len(verses) // 2 or 1:])
        pool = [v for v in verses if v not in recent] or verses
        return random.choice(pool)

    # sequential
    index = state.get("index", 0) % len(verses)
    return verses[index]


def record(state: dict, reference: str) -> dict:
    if config.VERSE_REFERENCE:
        # manual override: don't advance the sequential cursor
        pass
    elif config.SELECTION_MODE != "random":
        state["index"] = (state.get("index", 0) + 1) % max(len(load_verses()), 1)

    posted = state.setdefault("posted", [])
    posted.append(reference)
    # keep the history bounded
    if len(posted) > 500:
        state["posted"] = posted[-500:]
    return state
