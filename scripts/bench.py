"""Benchmark harness: runs the vision engine against a video or synth
source for N seconds (or until the source is exhausted) and reports mean/p95
per-step latency, achieved rate, CPU%, and peak RSS. Writes bench_results.json
to D:\\tmp\\elara\\ — never into the repo or C:. These numbers are the
baseline Phase 9's performance work must meet or beat.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import psutil  # noqa: E402

from elara.app import build_context  # noqa: E402
from elara.config import Config  # noqa: E402
from elara.vision.camera import SynthSource, VideoFileSource  # noqa: E402
from elara.vision.engine import VisionEngine  # noqa: E402


def _open_source(spec: str):
    kind, _, value = spec.partition(":")
    if kind == "synth":
        return SynthSource(value)
    if kind == "video":
        return VideoFileSource(value, loop=True, realtime=False)
    raise ValueError(f"unsupported source spec: {spec!r} (use synth:PATH or video:PATH)")


def run_bench(source_spec: str, seconds: float) -> dict:
    ctx = build_context(Config(), dry_run=True)
    source = _open_source(source_spec)
    engine = VisionEngine(source, ctx.config, ctx.event_bus)

    process = psutil.Process()
    process.cpu_percent(interval=None)  # prime the internal counter

    latencies_ms: list[float] = []
    peak_rss = process.memory_info().rss
    start = time.perf_counter()
    steps = 0

    while time.perf_counter() - start < seconds:
        t0 = time.perf_counter()
        if not engine.step():
            break
        latencies_ms.append((time.perf_counter() - t0) * 1000.0)
        steps += 1
        peak_rss = max(peak_rss, process.memory_info().rss)

    elapsed = time.perf_counter() - start
    cpu_percent = process.cpu_percent(interval=None)

    sorted_lat = sorted(latencies_ms)
    p95 = sorted_lat[int(len(sorted_lat) * 0.95)] if sorted_lat else 0.0

    return {
        "source": source_spec,
        "steps": steps,
        "elapsed_s": elapsed,
        "achieved_fps": steps / elapsed if elapsed > 0 else 0.0,
        "mean_latency_ms": sum(latencies_ms) / len(latencies_ms) if latencies_ms else 0.0,
        "p95_latency_ms": p95,
        "cpu_percent": cpu_percent,
        "peak_rss_mb": peak_rss / (1024 * 1024),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="synth:PATH or video:PATH")
    parser.add_argument("--seconds", type=float, default=5.0)
    parser.add_argument("--out", default=r"D:\tmp\elara\bench_results.json")
    args = parser.parse_args()

    result = run_bench(args.source, args.seconds)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))

    print(json.dumps(result, indent=2))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
