"""Core reel-generation pipeline, shared by the daily job and the dashboard."""
import datetime as dt
import os

from . import config, quran, render, video


def _ensure_dirs():
    for path in (config.OUTPUT_DIR, config.WORK_DIR, config.DATA_DIR):
        os.makedirs(path, exist_ok=True)


def generate_reel(reference: str, reciter: str,
                  background_mode: str = "gradient", tail_seconds=None) -> dict:
    """Fetch a verse, render it, and build the MP4. Returns metadata + path."""
    _ensure_dirs()

    verse = quran.get_verse(reference, reciter)

    stamp = dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    safe_ref = reference.replace(":", "_")
    audio_path = os.path.join(config.WORK_DIR, f"audio-{safe_ref}.mp3")
    text_png = os.path.join(config.WORK_DIR, f"text-{safe_ref}.png")
    gradient_png = os.path.join(config.WORK_DIR, "gradient.png")
    filename = f"reel-{safe_ref}-{reciter.replace('.', '_')}-{stamp}.mp4"
    out_path = os.path.join(config.OUTPUT_DIR, filename)

    quran.download_audio(verse["audio_url"], audio_path)
    render.make_gradient(gradient_png)
    render.render_text_image(verse["text"], verse["surah_name"], verse["ayah_number"], text_png)
    video.build_reel(audio_path, text_png, gradient_png, out_path,
                     background_mode=background_mode, tail_seconds=tail_seconds)

    return {
        "verse": verse,
        "reciter": reciter,
        "path": out_path,
        "filename": filename,
    }
