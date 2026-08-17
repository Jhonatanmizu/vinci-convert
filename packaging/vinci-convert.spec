# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the vinci-convert CLI (console, one-dir)."""

from pathlib import Path

ROOT = Path(SPECPATH).parent  # repository root

a = Analysis(
    [str(ROOT / "packaging" / "cli_launcher.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PySide6"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="vinci-convert",
    debug=False,
    strip=False,
    upx=False,
    console=True,
    icon=str(ROOT / "packaging" / "assets" / "vinci-convert.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="vinci-convert",
)
