# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — Pynote
Génère un exécutable Windows autonome (un seul dossier).
"""

import os
from pathlib import Path

block_cipher = None

# Inclure build_type.txt et VERSION dans le bundle
_datas = []
if os.path.exists("build_type.txt"):
    _datas.append(("build_type.txt", "."))
if os.path.exists("VERSION"):
    _datas.append(("VERSION", "."))

a = Analysis(
    ["main.py"],
    pathex=[str(Path(".").resolve())],
    binaries=[],
    datas=_datas,
    hiddenimports=[
        "customtkinter",
        "pronotepy",
        "dotenv",
        "PIL",
        "PIL._tkinter_finder",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Pynote",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Pynote",
)
