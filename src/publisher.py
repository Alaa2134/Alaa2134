"""Host the rendered reel on a GitHub Release, then publish it via the
Instagram Graph API.

Instagram's Content Publishing API downloads the video from a public URL, so
we upload the MP4 as a GitHub Release asset (which has a stable public
download URL) and hand that URL to Instagram.
"""
import os
import time

import requests

from . import config


# --------------------------------------------------------------------------
# GitHub Release hosting
# --------------------------------------------------------------------------
def _gh_headers():
    return {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def upload_to_github_release(file_path: str, tag: str) -> str:
    """Ensure a release with `tag` exists, upload the file, return public URL."""
    if not config.GITHUB_REPOSITORY or not config.GITHUB_TOKEN:
        raise ValueError("GITHUB_REPOSITORY and GITHUB_TOKEN are required to host the video.")

    owner, repo = config.GITHUB_REPOSITORY.split("/", 1)
    api = f"https://api.github.com/repos/{owner}/{repo}/releases"

    resp = requests.get(f"{api}/tags/{tag}", headers=_gh_headers(), timeout=30)
    if resp.status_code == 200:
        release = resp.json()
    else:
        create = requests.post(
            api,
            headers=_gh_headers(),
            json={
                "tag_name": tag,
                "name": "Daily Quran Reels",
                "body": "Auto-generated Quran reels hosted for Instagram publishing.",
                "draft": False,
                "prerelease": False,
            },
            timeout=30,
        )
        create.raise_for_status()
        release = create.json()

    upload_base = release["upload_url"].split("{", 1)[0]
    name = os.path.basename(file_path)
    with open(file_path, "rb") as fh:
        upload = requests.post(
            f"{upload_base}?name={name}",
            headers={**_gh_headers(), "Content-Type": "video/mp4"},
            data=fh,
            timeout=300,
        )
    if upload.status_code not in (200, 201):
        raise RuntimeError(f"Release asset upload failed ({upload.status_code}): {upload.text}")

    return upload.json()["browser_download_url"]


# --------------------------------------------------------------------------
# Instagram Graph API publishing
# --------------------------------------------------------------------------
def publish_reel(video_url: str, caption: str, *, poll_timeout=300, poll_interval=5) -> str:
    """Create a REELS container, wait for processing, then publish it."""
    if not config.IG_USER_ID or not config.IG_ACCESS_TOKEN:
        raise ValueError("IG_USER_ID and IG_ACCESS_TOKEN are required to publish.")

    base = f"https://graph.facebook.com/{config.GRAPH_API_VERSION}"

    create = requests.post(
        f"{base}/{config.IG_USER_ID}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": config.IG_ACCESS_TOKEN,
        },
        timeout=60,
    )
    _raise_graph_error(create, "create media container")
    creation_id = create.json()["id"]

    deadline = time.time() + poll_timeout
    while time.time() < deadline:
        status = requests.get(
            f"{base}/{creation_id}",
            params={"fields": "status_code,status", "access_token": config.IG_ACCESS_TOKEN},
            timeout=30,
        )
        _raise_graph_error(status, "check media status")
        code = status.json().get("status_code")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise RuntimeError(f"Instagram processing error: {status.json()}")
        time.sleep(poll_interval)
    else:
        raise TimeoutError("Timed out waiting for Instagram to process the video.")

    publish = requests.post(
        f"{base}/{config.IG_USER_ID}/media_publish",
        data={"creation_id": creation_id, "access_token": config.IG_ACCESS_TOKEN},
        timeout=60,
    )
    _raise_graph_error(publish, "publish media")
    return publish.json()["id"]


def _raise_graph_error(resp, action: str) -> None:
    if resp.status_code >= 400:
        raise RuntimeError(f"Graph API failed to {action} ({resp.status_code}): {resp.text}")
