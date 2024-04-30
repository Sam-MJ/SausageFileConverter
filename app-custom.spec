# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = []
hiddenimports += collect_submodules('D:\Documents\Programming_stuff\Python_projects\sausagebuild\app_build\src')
hiddenimports += [
    "PySide6",
    "struct",
    "io",
    "numpy",
    "concurrent",
    "shutil",
    "taglib",
    "trackback",
    "soundfile",
    "re",
    "mainwindow",
    "telem",
    "metadata_v2",
    "exceptions",
    "requests",
    "uuid",
    "worker",
    "utils"
]


a = Analysis(
    ['D:\\Documents\\Programming_stuff\\Python_projects\\sausagebuild\\app_build\\src\\app.py'],
    pathex=['D:\\Documents\\Programming_stuff\\Python_projects\\sausagebuild\\app_build\\src'],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=['D:\\Documents\\Programming_stuff\\Python_projects\\sausagebuild\\app_build\\hook-data.py'],
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
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='app',
)
