"""Build the Instagram caption for a verse."""
from . import config


def build_caption(verse: dict, hashtags: str | None = None) -> str:
    tags = config.CAPTION_HASHTAGS if hashtags is None else hashtags
    parts = [
        verse["text"],
        "",
        f"﴿ {verse['surah_name']} : {verse['ayah_number']} ﴾",
    ]
    if tags:
        parts += ["", tags]
    return "\n".join(parts)
