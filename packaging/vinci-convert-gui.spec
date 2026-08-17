# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the vinci-convert GUI (windowed, one-dir)."""

from pathlib import Path

ROOT = Path(SPECPATH).parent  # repository root

a = Analysis(
    [str(ROOT / "packaging" / "gui_launcher.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="vinci-convert-gui",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(ROOT / "packaging" / "assets" / "vinci-convert.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="vinci-convert-gui",
)
