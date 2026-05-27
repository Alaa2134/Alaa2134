"""Daily Quran reel generator + Instagram publisher.

Pipeline:
  1. pick a verse (sequential / random / forced)
  2. fetch its Arabic text + recitation audio
  3. render the verse text and compose a 9:16 reel with ffmpeg
  4. (unless DRY_RUN) host the MP4 on a GitHub Release and publish to Instagram
  5. record the verse so it is not repeated
"""
import datetime as dt
import os
import sys

from src import caption as caption_mod
from src import config, publisher, quran, render, state, video


def _ensure_dirs():
    for path in (config.OUTPUT_DIR, config.WORK_DIR, config.DATA_DIR):
        os.makedirs(path, exist_ok=True)


def main() -> int:
    _ensure_dirs()

    verses = state.load_verses()
    st = state.load_state()
    reference = state.pick_reference(verses, st)
    print(f"[1/5] Selected verse: {reference} (mode={config.SELECTION_MODE})")

    verse = quran.get_verse(reference)
    print(f"[2/5] Fetched {verse['surah_english']} {verse['surah_number']}:{verse['ayah_number']}")

    stamp = dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    safe_ref = reference.replace(":", "_")
    audio_path = os.path.join(config.WORK_DIR, f"audio-{safe_ref}.mp3")
    text_png = os.path.join(config.WORK_DIR, f"text-{safe_ref}.png")
    gradient_png = os.path.join(config.WORK_DIR, "gradient.png")
    out_path = os.path.join(config.OUTPUT_DIR, f"reel-{safe_ref}-{stamp}.mp4")

    quran.download_audio(verse["audio_url"], audio_path)
    render.make_gradient(gradient_png)
    render.render_text_image(verse["text"], verse["surah_name"], verse["ayah_number"], text_png)
    print("[3/5] Rendered text + background")

    video.build_reel(audio_path, text_png, gradient_png, out_path)
    print(f"[3/5] Built reel: {out_path}")

    if config.DRY_RUN:
        print("[done] DRY_RUN enabled — skipping upload and publish.")
        return 0

    asset_name = f"reel-{safe_ref}-{stamp}.mp4"
    hosted = os.path.join(config.OUTPUT_DIR, asset_name)
    if hosted != out_path:
        os.replace(out_path, hosted)
    video_url = publisher.upload_to_github_release(hosted, config.RELEASE_TAG)
    print(f"[4/5] Hosted video: {video_url}")

    text = caption_mod.build_caption(verse)
    media_id = publisher.publish_reel(video_url, text)
    print(f"[5/5] Published to Instagram. Media ID: {media_id}")

    state.record(st, reference)
    state.save_state(st)
    print("[done] State updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
