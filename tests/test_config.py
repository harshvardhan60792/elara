from __future__ import annotations

from pathlib import Path

from elara.config import Config, from_dict, load, save, to_dict


def test_round_trip_defaults(tmp_path: Path) -> None:
    cfg = Config()
    path = tmp_path / "config.json"
    save(cfg, path)
    loaded = load(path)
    assert loaded == cfg


def test_unknown_keys_survive_round_trip(tmp_path: Path) -> None:
    raw = to_dict(Config())
    raw["a_future_top_level_key"] = "keep me"
    raw["arming"]["a_future_arming_key"] = 42

    cfg = from_dict(raw)
    assert cfg.extra["a_future_top_level_key"] == "keep me"
    assert cfg.extra["arming._unknown"]["a_future_arming_key"] == 42

    path = tmp_path / "config.json"
    save(cfg, path)
    reloaded_raw = to_dict(load(path))
    assert reloaded_raw["a_future_top_level_key"] == "keep me"
    assert reloaded_raw["arming"]["a_future_arming_key"] == 42


def test_missing_sections_fill_in_defaults() -> None:
    cfg = from_dict({"schema_version": 1, "general": {"dry_run": False}})
    assert cfg.general.dry_run is False
    assert cfg.arming.dwell_ms == 250  # default, section was absent entirely


def test_load_missing_file_returns_defaults(tmp_path: Path) -> None:
    cfg = load(tmp_path / "does_not_exist.json")
    assert cfg == Config()
