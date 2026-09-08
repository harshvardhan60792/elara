"""Generates assets/icon_idle.png and assets/icon_armed.png programmatically
so the repo has no binary-blob dependency nobody can regenerate. Idle is a
hollow ring (watching, disarmed); armed is a filled circle in the brand
colour (watching, live)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

BRAND = (108, 99, 255, 255)  # soft violet
SIZE = 64


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def make_idle() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad, width = 6, 6
    draw.ellipse([pad, pad, SIZE - pad, SIZE - pad], outline=BRAND, width=width)
    return img


def make_armed() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = 6
    draw.ellipse([pad, pad, SIZE - pad, SIZE - pad], fill=BRAND)
    return img


def main() -> None:
    assets = _repo_root() / "assets"
    assets.mkdir(exist_ok=True)
    make_idle().save(assets / "icon_idle.png")
    armed = make_armed()
    armed.save(assets / "icon_armed.png")
    # PyInstaller's EXE(icon=...) needs .ico on Windows, not .png.
    armed.save(assets / "icon_armed.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    print(f"wrote {assets / 'icon_idle.png'}, {assets / 'icon_armed.png'}, {assets / 'icon_armed.ico'}")


if __name__ == "__main__":
    main()
