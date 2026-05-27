"""Daily Quran reel generator + Instagram publisher.

Pipeline:
  1. load settings, pick a verse + reciter (sequential/random/rotate, or forced)
  2. fetch Arabic text + recitation audio and build a 9:16 reel
  3. (unless DRY_RUN) host the MP4 on a GitHub Release and publish to Instagram
  4. record state so verses/reciters are not repeated
"""
import sys

from src import caption as caption_mod
from src import config, pipeline, publisher, settings as settings_mod, state


def main() -> int:
    settings = settings_mod.load_settings()

    verses = state.load_verses()
    st = state.load_state()
    reference = state.pick_reference(verses, st, settings)
    reciter = state.pick_reciter(st, settings)
    print(f"[1/5] Verse {reference} | reciter {reciter} "
          f"(verse={settings.get('selection_mode')}, reciter={settings.get('reciter_mode')})")

    result = pipeline.generate_reel(
        reference, reciter,
        background_mode=settings.get("background_mode", "gradient"),
        tail_seconds=settings.get("tail_seconds"),
    )
    verse = result["verse"]
    out_path = result["path"]
    print(f"[2/5] Fetched {verse['surah_english']} {verse['surah_number']}:{verse['ayah_number']}")
    print(f"[3/5] Built reel: {out_path}")

    if config.DRY_RUN:
        print("[done] DRY_RUN enabled — skipping upload and publish.")
        return 0

    video_url = publisher.upload_to_github_release(out_path, config.RELEASE_TAG)
    print(f"[4/5] Hosted video: {video_url}")

    text = caption_mod.build_caption(verse, settings.get("hashtags"))
    media_id = publisher.publish_reel(video_url, text)
    print(f"[5/5] Published to Instagram. Media ID: {media_id}")

    state.record(st, reference, settings, verses)
    state.save_state(st)
    print("[done] State updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
