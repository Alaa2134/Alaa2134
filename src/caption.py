"""Build the Instagram caption for a verse."""
from . import config


def build_caption(verse: dict) -> str:
    parts = [
        verse["text"],
        "",
        f"﴿ {verse['surah_name']} : {verse['ayah_number']} ﴾",
    ]
    if config.CAPTION_HASHTAGS:
        parts += ["", config.CAPTION_HASHTAGS]
    return "\n".join(parts)
