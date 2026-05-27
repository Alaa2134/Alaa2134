"""Compose the final vertical reel (background + text overlay + audio) via ffmpeg."""
import glob
import os
import random
import subprocess

from . import config

_BG_EXTENSIONS = ("*.mp4", "*.mov", "*.webm", "*.mkv")


def probe_duration(path: str) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1",
            path,
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def pick_background():
    if not os.path.isdir(config.BACKGROUNDS_DIR):
        return None
    files = []
    for ext in _BG_EXTENSIONS:
        files.extend(glob.glob(os.path.join(config.BACKGROUNDS_DIR, ext)))
    return random.choice(files) if files else None


def build_reel(audio_path, text_png, gradient_png, out_path) -> str:
    """Render an H.264/AAC 9:16 MP4 ready for Instagram Reels.

    Uses a random background video from assets/backgrounds when available,
    otherwise falls back to the gradient image.
    """
    w, h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    duration = probe_duration(audio_path)
    total = round(duration + config.TAIL_SECONDS, 2)

    background = pick_background()
    cmd = ["ffmpeg", "-y"]
    if background:
        cmd += ["-stream_loop", "-1", "-i", background]
    else:
        cmd += ["-loop", "1", "-i", gradient_png]
    cmd += ["-i", text_png, "-i", audio_path]

    filter_complex = (
        f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},setsar=1,eq=brightness=-0.05[bg];"
        f"[bg][1:v]overlay=0:0:format=auto[v];"
        f"[2:a]apad[a]"
    )

    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-t", str(total),
        "-r", str(config.FPS),
        "-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-profile:v", "high", "-level", "4.0",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-movflags", "+faststart",
        out_path,
    ]

    subprocess.run(cmd, check=True)
    return out_path
