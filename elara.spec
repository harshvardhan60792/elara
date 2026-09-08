# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Elara. Build with scripts/build.ps1, which sets
TEMP/TMP to D:\\tmp\\build before invoking PyInstaller - the default C:
temp dir does not have room for the intermediate unpack (ADR-003).

onedir, not onefile: onefile re-unpacks ~200MB to a temp dir on every
launch, which is slow and would land on C: unless TEMP is redirected
(ADR-017 territory - this is the same "never touch C:" constraint that
governs the whole dev environment, now applying to the shipped app too).
"""

from PyInstaller.utils.hooks import collect_all

block_cipher = None

mediapipe_datas, mediapipe_binaries, mediapipe_hidden = collect_all("mediapipe")

a = Analysis(
    ["src/elara/__main__.py"],
    pathex=["src"],
    binaries=mediapipe_binaries,
    datas=[
        ("assets/icon_idle.png", "assets"),
        ("assets/icon_armed.png", "assets"),
        *mediapipe_datas,
    ],
    hiddenimports=[
        "mediapipe.tasks.c",
        "win32timezone",  # pywin32 quirk: not auto-detected by PyInstaller's hook
        *mediapipe_hidden,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib.tests"],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="elara",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon="assets/icon_armed.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="elara",
)
