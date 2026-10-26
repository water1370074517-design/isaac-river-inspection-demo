"""Build the player and verified release video as one static GitHub Pages site."""
from __future__ import annotations

import argparse
import hashlib
import shutil
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIDEO_URL = "https://github.com/water1370074517-design/isaac-river-inspection-demo/releases/download/v1.0/river_inspection_demo_en.mp4"
VIDEO_SHA256 = "afbcc0e8e6f3d1c93dbff31b25cf544ae160ad3245b9ed2671c72f8bba1325dd"


def digest(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def download_video(destination: Path) -> None:
    temporary = destination.with_suffix(".part")
    for attempt in range(3):
        try:
            request = urllib.request.Request(VIDEO_URL, headers={"User-Agent": "river-inspection-pages-build"})
            with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as output:
                shutil.copyfileobj(response, output, length=1024 * 1024)
            if digest(temporary) != VIDEO_SHA256:
                raise ValueError("Release video SHA-256 does not match the verified original")
            temporary.replace(destination)
            return
        except Exception:
            temporary.unlink(missing_ok=True)
            if attempt == 2:
                raise
            time.sleep(3 * (attempt + 1))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-file", type=Path, help="Use a verified local copy for an offline preview")
    args = parser.parse_args()
    site = ROOT / "_site"
    media = site / "media"
    media.mkdir(parents=True, exist_ok=True)
    destination = media / "river_inspection_demo_en.mp4"
    if args.video_file:
        if digest(args.video_file) != VIDEO_SHA256:
            raise ValueError("Local video SHA-256 does not match the verified original")
        shutil.copyfile(args.video_file, destination)
    elif not destination.exists() or digest(destination) != VIDEO_SHA256:
        download_video(destination)
    shutil.copyfile(ROOT / "site" / "index.html", site / "index.html")
    shutil.copyfile(ROOT / "preview.jpg", site / "poster.jpg")
    (site / ".nojekyll").touch()
    print(f"Built {site}: verified video ({destination.stat().st_size:,} bytes), player, and poster")


if __name__ == "__main__":
    main()
