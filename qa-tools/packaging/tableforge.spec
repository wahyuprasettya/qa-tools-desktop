# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

project = Path.cwd()

a = Analysis(
    [str(project / "app" / "main.py")],
    pathex=[str(project)],
    binaries=[],
    datas=[
        (str(project / "app" / "assets"), "app/assets"),
        (str(project / "examples"), "examples"),
    ],
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
    name="QA-Generator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="QA-Generator",
)
