"""Render the gradient background and the Arabic verse text to PNG images.

Arabic must be shaped (letters joined) and ordered right-to-left before it can
be drawn. When Pillow is built with libraqm (the common case, including pip
wheels) we pass the raw text with ``direction="rtl"`` and let harfbuzz shape it
correctly. Otherwise we fall back to ``arabic_reshaper`` + the bidi algorithm.
"""
import glob
import os

from PIL import Image, ImageDraw, ImageFont, features

from . import config

_RAQM = features.check("raqm")

if not _RAQM:  # only needed for the fallback path
    import arabic_reshaper

    try:  # python-bidi < 0.5
        from bidi.algorithm import get_display
    except ImportError:  # python-bidi >= 0.5
        from bidi import get_display

# NOTE: the fallback (arabic_reshaper) emits Unicode Presentation-Forms
# codepoints, so the font must contain those glyphs. Amiri-Regular and Noto
# Naskh do; AmiriQuran.ttf does NOT (it relies on OpenType shaping), so it must
# not be selected here.
_FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Regular.ttf",
    "/usr/share/fonts/truetype/hosny-amiri/Amiri-Regular.ttf",
    "/usr/share/fonts/truetype/amiri/Amiri-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
    "/usr/share/fonts/opentype/noto/NotoNaskhArabic-Regular.ttf",
    "/usr/share/fonts/truetype/kacst/KacstQurn.ttf",
]

_FONT_GLOBS = [
    "/usr/share/fonts/**/Amiri-Regular.ttf",
    "/usr/share/fonts/**/NotoNaskh*Arabic*.ttf",
    "/usr/share/fonts/**/*Naskh*.ttf",
    "/usr/share/fonts/**/Amiri-Bold.ttf",
    "/usr/share/fonts/**/*Arabic*.ttf",
]


def find_font() -> str:
    if config.FONT_PATH and os.path.exists(config.FONT_PATH):
        return config.FONT_PATH
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    for pattern in _FONT_GLOBS:
        matches = sorted(glob.glob(pattern, recursive=True))
        if matches:
            return matches[0]
    raise FileNotFoundError(
        "No Arabic font found. Install one (e.g. 'fonts-hosny-amiri') "
        "or set the QURAN_FONT environment variable to a .ttf path."
    )


def _prep(text: str):
    """Return (text_to_render, draw_kwargs) for the active shaping path."""
    if _RAQM:
        return text, {"direction": "rtl"}
    return get_display(arabic_reshaper.reshape(text)), {}


def make_gradient(out_path: str, top=(13, 46, 35), bottom=(3, 17, 12)) -> str:
    """Create a smooth vertical gradient background as a PNG."""
    w, h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    column = Image.new("RGB", (1, h))
    px = column.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        px[0, y] = (
            int(top[0] * (1 - t) + bottom[0] * t),
            int(top[1] * (1 - t) + bottom[1] * t),
            int(top[2] * (1 - t) + bottom[2] * t),
        )
    column.resize((w, h)).save(out_path)
    return out_path


def _wrap_lines(text, font, max_width, draw):
    """Greedy word-wrap; returns logical (unshaped) Arabic lines."""
    words = text.split()
    lines, current = [], []
    for word in words:
        trial = current + [word]
        render_text, kw = _prep(" ".join(trial))
        width = draw.textlength(render_text, font=font, **kw)
        if width <= max_width or not current:
            current = trial
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def render_text_image(verse_text, surah_name, ayah_number, out_path) -> str:
    """Draw the verse onto a transparent full-frame PNG with a readable panel."""
    w, h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font_path = find_font()

    margin = 90
    panel_pad = 60
    max_text_width = w - 2 * margin - 2 * panel_pad

    size = 76
    font = ImageFont.truetype(font_path, size)
    lines = _wrap_lines(verse_text, font, max_text_width, draw)
    while len(lines) > 7 and size > 42:
        size -= 6
        font = ImageFont.truetype(font_path, size)
        lines = _wrap_lines(verse_text, font, max_text_width, draw)

    line_height = int(size * 1.75)
    meta_size = max(int(size * 0.55), 34)
    meta_font = ImageFont.truetype(font_path, meta_size)

    text_block_h = line_height * len(lines)
    meta_gap = int(size * 0.9)
    content_h = text_block_h + meta_gap + meta_size
    panel_h = content_h + 2 * panel_pad
    panel_w = w - 2 * margin

    panel_x0 = margin
    panel_y0 = (h - panel_h) // 2
    panel_x1 = panel_x0 + panel_w
    panel_y1 = panel_y0 + panel_h

    draw.rounded_rectangle(
        [panel_x0, panel_y0, panel_x1, panel_y1],
        radius=48,
        fill=(0, 0, 0, 140),
        outline=(212, 175, 95, 180),
        width=3,
    )

    center_x = w // 2
    y = panel_y0 + panel_pad + line_height // 2
    for line in lines:
        rt, kw = _prep(line)
        draw.text((center_x + 2, y + 2), rt, font=font, fill=(0, 0, 0, 200), anchor="mm", **kw)
        draw.text((center_x, y), rt, font=font, fill=(245, 245, 240, 255), anchor="mm", **kw)
        y += line_height

    meta_y = panel_y0 + panel_pad + text_block_h + meta_gap
    meta_rt, meta_kw = _prep(f"{surah_name} ﴿ {ayah_number} ﴾")
    draw.text((center_x, meta_y), meta_rt, font=meta_font, fill=(212, 175, 95, 255), anchor="mm", **meta_kw)

    img.save(out_path)
    return out_path
