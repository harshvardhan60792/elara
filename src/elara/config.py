"""Nested config with defaults for every threshold named in docs/GESTURES.md
and docs/ARCHITECTURE.md. Round-trips through JSON, preserves unknown keys
(so a newer config file opened by an older build doesn't lose data), and has
a migration hook keyed on schema_version for future changes."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

from elara.paths import config_file

SCHEMA_VERSION = 1


@dataclass
class GeneralConfig:
    dry_run: bool = True
    start_armed: bool = False
    active_profile: str = "desktop"


@dataclass
class CameraConfig:
    device_index: int = 0
    width: int = 640
    height: int = 480


@dataclass
class VisionConfig:
    pinch_on: float = 0.055
    pinch_off: float = 0.085
    min_hand_detection_confidence: float = 0.5
    min_hand_presence_confidence: float = 0.5
    min_tracking_confidence: float = 0.5
    trajectory_buffer_s: float = 1.0


@dataclass
class ArmingConfig:
    dwell_ms: int = 250
    vote_n: int = 4
    vote_m: int = 6
    confidence_floor: float = 0.72
    cooldown_ms: int = 800


@dataclass
class CursorConfig:
    mincutoff: float = 1.0
    beta: float = 0.007
    dcutoff: float = 1.0


@dataclass
class UiConfig:
    attention_dwell_ms: int = 700
    radial_timeout_ms: int = 3000
    toast_duration_ms: int = 1400


@dataclass
class VoiceConfig:
    enabled: bool = False
    wake_word: str = "hey_jarvis"
    stt_backend: str = "vosk"


@dataclass
class PresenceConfig:
    enabled: bool = False
    away_delay_s: int = 45
    lock_delay_s: int = 180
    resume_window_s: int = 20


@dataclass
class PrivacyConfig:
    telemetry: bool = False


@dataclass
class PerformanceConfig:
    fps_active: int = 30
    fps_idle: int = 8
    fps_battery_cap: int = 15
    idle_after_ms: int = 1500


@dataclass
class Config:
    schema_version: int = SCHEMA_VERSION
    general: GeneralConfig = field(default_factory=GeneralConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    arming: ArmingConfig = field(default_factory=ArmingConfig)
    cursor: CursorConfig = field(default_factory=CursorConfig)
    ui: UiConfig = field(default_factory=UiConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    presence: PresenceConfig = field(default_factory=PresenceConfig)
    privacy: PrivacyConfig = field(default_factory=PrivacyConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    extra: dict = field(default_factory=dict)


_SECTION_TYPES: dict[str, type] = {
    "general": GeneralConfig,
    "camera": CameraConfig,
    "vision": VisionConfig,
    "arming": ArmingConfig,
    "cursor": CursorConfig,
    "ui": UiConfig,
    "voice": VoiceConfig,
    "presence": PresenceConfig,
    "privacy": PrivacyConfig,
    "performance": PerformanceConfig,
}


def _migrate(raw: dict) -> dict:
    version = raw.get("schema_version", SCHEMA_VERSION)
    if version > SCHEMA_VERSION:
        raise ValueError(
            f"config schema_version {version} is newer than supported {SCHEMA_VERSION}"
        )
    # No migrations exist yet. Future ones add `if version < N: ...` steps here
    # before this line, then bump the stamped version below.
    raw["schema_version"] = SCHEMA_VERSION
    return raw


def _section_from_dict(section_type: type, data: dict) -> tuple[Any, dict]:
    known = {f.name for f in fields(section_type)}
    kwargs = {k: v for k, v in data.items() if k in known}
    unknown = {k: v for k, v in data.items() if k not in known}
    return section_type(**kwargs), unknown


def from_dict(raw: dict) -> Config:
    raw = _migrate(dict(raw))
    extra: dict[str, Any] = dict(raw.get("extra", {}))
    kwargs: dict[str, Any] = {"schema_version": raw.get("schema_version", SCHEMA_VERSION)}

    for name, section_type in _SECTION_TYPES.items():
        section_data = raw.get(name, {})
        if not isinstance(section_data, dict):
            section_data = {}
        section, unknown = _section_from_dict(section_type, section_data)
        kwargs[name] = section
        if unknown:
            extra[f"{name}._unknown"] = unknown

    known_top = set(_SECTION_TYPES) | {"schema_version", "extra"}
    for key, value in raw.items():
        if key not in known_top:
            extra[key] = value

    kwargs["extra"] = extra
    return Config(**kwargs)


def to_dict(config: Config) -> dict:
    data = asdict(config)
    extra = data.pop("extra", {})
    for key, value in extra.items():
        if key.endswith("._unknown") and isinstance(value, dict):
            section_name = key[: -len("._unknown")]
            if section_name in data and isinstance(data[section_name], dict):
                data[section_name].update(value)
        else:
            data[key] = value
    return data


def load(path: Path | None = None) -> Config:
    path = path or config_file()
    if not path.exists():
        return Config()
    with path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return from_dict(raw)


def save(config: Config, path: Path | None = None) -> None:
    path = path or config_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(to_dict(config), fh, indent=2, sort_keys=True)
    tmp.replace(path)
