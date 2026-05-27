"""Fetch verse text and recitation audio from the Al Quran Cloud API."""
import requests

from . import config


def get_verse(reference: str) -> dict:
    """Return verse text + audio for a reference like "2:255".

    A single call to an audio edition returns the Arabic text, a CDN audio
    URL, and surah metadata.
    """
    url = f"{config.API_BASE}/ayah/{reference}/{config.AUDIO_EDITION}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()["data"]

    audio_url = data.get("audio")
    if not audio_url:
        secondary = data.get("audioSecondary") or []
        if secondary:
            audio_url = secondary[0]
    if not audio_url:
        raise ValueError(f"No audio URL returned for {reference} ({config.AUDIO_EDITION})")

    surah = data["surah"]
    return {
        "reference": reference,
        "text": data["text"].strip(),
        "audio_url": audio_url,
        "surah_name": surah["name"],
        "surah_english": surah.get("englishName", ""),
        "surah_number": surah["number"],
        "ayah_number": data["numberInSurah"],
    }


def download_audio(audio_url: str, out_path: str) -> str:
    resp = requests.get(audio_url, timeout=120)
    resp.raise_for_status()
    with open(out_path, "wb") as fh:
        fh.write(resp.content)
    return out_path
