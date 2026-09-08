"""Downloads MediaPipe task-bundle models into models_dir(), verifying
SHA-256 and skipping re-download if the file is already present and
correct. Never writes to C: — models_dir() resolves under the OS app-data
location via platformdirs, which is fine (megabytes), or under a directory
the caller overrides for local dev via --out.

This is the one sanctioned network call at dev/setup time (ADR-012); the
running app only calls this on explicit user action (enabling a feature
whose model isn't bundled), never automatically.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from elara.paths import models_dir  # noqa: E402

MODELS = {
    "hand_landmarker.task": {
        "url": "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task",
        # Populated after first verified download; see docs/DECISIONS.md.
        "sha256": "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1",
    },
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(name: str, out_dir: Path, force: bool = False) -> Path:
    spec = MODELS[name]
    dest = out_dir / name
    if dest.exists() and not force:
        if _sha256(dest) == spec["sha256"]:
            print(f"{name}: already present, hash OK")
            return dest
        print(f"{name}: present but hash mismatch, re-downloading")

    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    urllib.request.urlretrieve(spec["url"], tmp)

    digest = _sha256(tmp)
    if digest != spec["sha256"]:
        tmp.unlink(missing_ok=True)
        raise ValueError(f"{name}: SHA-256 mismatch (got {digest}, expected {spec['sha256']})")

    tmp.replace(dest)
    print(f"{name}: downloaded and verified -> {dest}")
    return dest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None, help="Override output directory (default: models_dir())")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--only", default=None, help="Fetch a single named model")
    args = parser.parse_args()

    out_dir = Path(args.out) if args.out else models_dir()
    names = [args.only] if args.only else list(MODELS)
    for name in names:
        fetch(name, out_dir, force=args.force)


if __name__ == "__main__":
    main()
