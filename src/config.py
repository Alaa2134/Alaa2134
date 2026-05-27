"""Central configuration, read from environment variables with sane defaults."""
import os


def _bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


# --- Instagram Graph API ---
IG_USER_ID = os.environ.get("IG_USER_ID", "").strip()
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "").strip()
GRAPH_API_VERSION = os.environ.get("GRAPH_API_VERSION", "v21.0").strip()

# --- GitHub (used to host the rendered video as a public Release asset) ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "").strip()  # "owner/repo"
RELEASE_TAG = os.environ.get("RELEASE_TAG", "daily-reels").strip()

# --- Quran content (Al Quran Cloud API editions) ---
# Audio editions: ar.alafasy, ar.abdulbasitmurattal, ar.husary, ar.minshawi, ...
AUDIO_EDITION = os.environ.get("AUDIO_EDITION", "ar.alafasy").strip()
API_BASE = os.environ.get("QURAN_API_BASE", "https://api.alquran.cloud/v1").strip()

# --- Verse selection ---
# "sequential" walks the curated list in order; "random" picks one at random.
SELECTION_MODE = os.environ.get("SELECTION_MODE", "sequential").strip().lower()
# Force a specific verse, e.g. "2:255". Overrides selection mode when set.
VERSE_REFERENCE = os.environ.get("VERSE_REFERENCE", "").strip()

# --- Video ---
VIDEO_WIDTH = int(os.environ.get("VIDEO_WIDTH", "1080"))
VIDEO_HEIGHT = int(os.environ.get("VIDEO_HEIGHT", "1920"))
FPS = int(os.environ.get("FPS", "30"))
TAIL_SECONDS = float(os.environ.get("TAIL_SECONDS", "1.5"))

# Optional explicit Arabic font path; otherwise common locations are searched.
FONT_PATH = os.environ.get("QURAN_FONT", "").strip()

# --- Caption ---
CAPTION_HASHTAGS = os.environ.get(
    "CAPTION_HASHTAGS",
    "#قرآن #قران_كريم #تلاوة #اسلام #quran #islam #recitation #reels",
).strip()

# --- Behaviour ---
# When true, generate the video locally but do NOT upload or publish.
DRY_RUN = _bool("DRY_RUN", False)

# --- Paths ---
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
BACKGROUNDS_DIR = os.path.join(ASSETS_DIR, "backgrounds")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
WORK_DIR = os.path.join(ROOT_DIR, "work")
VERSES_FILE = os.path.join(DATA_DIR, "verses.json")
STATE_FILE = os.path.join(DATA_DIR, "state.json")
