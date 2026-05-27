"""Web dashboard for the automated Quran reels platform.

Run locally:  python app.py   then open http://127.0.0.1:5000
Lets you browse every reciter and surah, generate/preview reels, manage the
posting schedule and settings, view the gallery, and publish on demand.
"""
import os

import requests
from flask import (Flask, jsonify, render_template, request,
                   send_from_directory)

from src import (caption as caption_mod, config, pipeline, publisher,
                 settings as settings_mod, state)

app = Flask(__name__)


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
@app.route("/")
def page_dashboard():
    return render_template("dashboard.html", active="dashboard")


@app.route("/reciters")
def page_reciters():
    return render_template("reciters.html", active="reciters")


@app.route("/quran")
def page_quran():
    return render_template("quran.html", active="quran")


@app.route("/studio")
def page_studio():
    return render_template("studio.html", active="studio")


@app.route("/gallery")
def page_gallery():
    return render_template("gallery.html", active="gallery")


@app.route("/settings")
def page_settings():
    return render_template("settings.html", active="settings")


# --------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------
@app.get("/api/reciters")
def api_reciters():
    return jsonify(settings_mod.load_reciters())


@app.get("/api/surahs")
def api_surahs():
    return jsonify(settings_mod.load_surahs())


@app.get("/api/surah/<int:number>")
def api_surah(number):
    resp = requests.get(f"{config.API_BASE}/surah/{number}/quran-uthmani", timeout=30)
    resp.raise_for_status()
    data = resp.json()["data"]
    ayahs = [{"numberInSurah": a["numberInSurah"], "text": a["text"]} for a in data["ayahs"]]
    return jsonify({
        "number": data["number"],
        "name": data["name"],
        "englishName": data["englishName"],
        "ayahs": ayahs,
    })


@app.get("/api/stats")
def api_stats():
    st = state.load_state()
    settings = settings_mod.load_settings()
    verses = state.load_verses()
    posted = st.get("posted", [])
    next_ref = state.pick_reference(verses, st, settings)
    next_reciter = state.pick_reciter(st, settings)
    return jsonify({
        "posted_count": len(posted),
        "last_posted": posted[-1] if posted else None,
        "verse_count": len(verses),
        "reciter_count": len(settings.get("reciter_pool", [])),
        "total_reciters": len(settings_mod.load_reciters()),
        "next_reference": next_ref,
        "next_reciter": next_reciter,
        "next_reciter_name": settings_mod.reciter_name(next_reciter),
        "selection_mode": settings.get("selection_mode"),
        "reciter_mode": settings.get("reciter_mode"),
        "instagram_ready": bool(config.IG_USER_ID and config.IG_ACCESS_TOKEN),
        "recent_posted": posted[-12:][::-1],
    })


@app.get("/api/settings")
def api_get_settings():
    return jsonify(settings_mod.load_settings())


@app.post("/api/settings")
def api_save_settings():
    payload = request.get_json(force=True) or {}
    return jsonify(settings_mod.save_settings(payload))


@app.post("/api/generate")
def api_generate():
    payload = request.get_json(force=True) or {}
    reference = (payload.get("reference") or "").strip()
    reciter = (payload.get("reciter") or "ar.alafasy").strip()
    background_mode = payload.get("background_mode", "gradient")
    if not reference:
        return jsonify({"error": "reference is required (e.g. 2:255)"}), 400
    try:
        result = pipeline.generate_reel(reference, reciter, background_mode=background_mode)
    except Exception as exc:  # surface a clean message to the UI
        return jsonify({"error": str(exc)}), 500
    return jsonify({
        "filename": result["filename"],
        "url": f"/media/{result['filename']}",
        "verse": result["verse"],
        "reciter": reciter,
        "reciter_name": settings_mod.reciter_name(reciter),
    })


@app.post("/api/publish")
def api_publish():
    payload = request.get_json(force=True) or {}
    filename = os.path.basename((payload.get("filename") or "").strip())
    path = os.path.join(config.OUTPUT_DIR, filename)
    if not filename or not os.path.exists(path):
        return jsonify({"error": "file not found"}), 404
    if not (config.IG_USER_ID and config.IG_ACCESS_TOKEN):
        return jsonify({"error": "Instagram credentials are not configured."}), 400
    try:
        verse = payload.get("verse") or {}
        settings = settings_mod.load_settings()
        cap = caption_mod.build_caption(verse, settings.get("hashtags")) if verse else (payload.get("caption") or "")
        video_url = publisher.upload_to_github_release(path, config.RELEASE_TAG)
        media_id = publisher.publish_reel(video_url, cap)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    return jsonify({"media_id": media_id, "video_url": video_url})


@app.get("/api/gallery")
def api_gallery():
    items = []
    if os.path.isdir(config.OUTPUT_DIR):
        for name in os.listdir(config.OUTPUT_DIR):
            if name.endswith(".mp4"):
                full = os.path.join(config.OUTPUT_DIR, name)
                items.append({
                    "filename": name,
                    "url": f"/media/{name}",
                    "size": os.path.getsize(full),
                    "mtime": os.path.getmtime(full),
                })
    items.sort(key=lambda x: x["mtime"], reverse=True)
    return jsonify(items)


@app.get("/media/<path:filename>")
def media(filename):
    return send_from_directory(config.OUTPUT_DIR, filename)


if __name__ == "__main__":
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=bool(os.environ.get("FLASK_DEBUG")))
