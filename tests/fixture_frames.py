"""Synthetic turntable frames for developing and testing the player.

Each frame shows its own number and a hand rotated by its share of 360 degrees,
so frame-order mistakes are easy to spot by eye.

    python tests/fixture_frames.py              # writes frames + manifest into player/
    python -m http.server -d player             # then open http://localhost:8000

The tests call build_fixture_site() to build a throwaway copy of the site.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DEFAULT_COUNT = 60
WIDTH, HEIGHT = 1280, 720
KEYFRAME_STEP = 8

PLAYER_DIR = Path(__file__).resolve().parent.parent / "player"
PLAYER_FILES = ("index.html", "style.css", "player.js")


def frame_path(index: int) -> str:
    """Manifest path for a 0-based frame index: frames/0001.webp, frames/0002.webp, ..."""
    return f"frames/{index + 1:04d}.webp"


def draw_frame(index: int, count: int) -> Image.Image:
    """One frame: a dial with a hand at index/count of a full turn, plus the frame number."""
    image = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    cx, cy, radius = WIDTH // 2, HEIGHT // 2 - 30, 220

    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        fill=(40, 44, 52, 255),
        outline=(230, 230, 230, 255),
        width=6,
    )
    angle = 2 * math.pi * index / count - math.pi / 2
    tip = (cx + radius * 0.85 * math.cos(angle), cy + radius * 0.85 * math.sin(angle))
    draw.line((cx, cy, *tip), fill=(255, 196, 0, 255), width=14)
    draw.ellipse((tip[0] - 16, tip[1] - 16, tip[0] + 16, tip[1] + 16), fill=(255, 196, 0, 255))

    font = ImageFont.load_default(size=64)
    draw.text((cx, cy + radius + 60), f"{index + 1:04d}", font=font, fill="white", anchor="mm")
    return image


def build_fixture_site(out_dir: Path, count: int = DEFAULT_COUNT, copy_player: bool = True) -> Path:
    """Write frames/, manifest.json and (optionally) the player files into out_dir."""
    out_dir = Path(out_dir)
    (out_dir / "frames").mkdir(parents=True, exist_ok=True)

    frames = []
    for index in range(count):
        path = frame_path(index)
        draw_frame(index, count).save(out_dir / path, "WEBP", quality=75)
        frames.append(path)

    manifest = {
        "version": 1,
        "title": "Fixture turntable",
        "width": WIDTH,
        "height": HEIGHT,
        "frames": frames,
        "credits": "Synthetic test frames from tests/fixture_frames.py",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    if copy_player:
        for name in PLAYER_FILES:
            shutil.copy2(PLAYER_DIR / name, out_dir / name)
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out_dir", nargs="?", type=Path, default=PLAYER_DIR)
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    args = parser.parse_args()

    copy_player = args.out_dir.resolve() != PLAYER_DIR
    build_fixture_site(args.out_dir, args.count, copy_player=copy_player)
    print(f"Wrote {args.count} frames and manifest.json to {args.out_dir}")


if __name__ == "__main__":
    main()
