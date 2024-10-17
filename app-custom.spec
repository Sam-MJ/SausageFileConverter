# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = []
hiddenimports += collect_submodules('src')
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
    "file_tree",
    "requests",
    "uuid",
    "worker",
    "utils",
    "datetime",
    "os",
    "json",
    "dotenv",
    "math",
    "natsort",
    "soxr",
    "dataclasses",
    "mdutils"
]


a = Analysis(
    ['src/app.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
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
    name='SausageFileConverter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
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
    name='SausageFileConverter',
)

app = BUNDLE(exe,
    name='SausageFileConverter.app',
    icon=None,
    bundle_identifier=None,
    version='0.0.1',
    info_plist={
    'NSPrincipalClass': 'NSApplication',
    'NSAppleScriptEnabled': False,
    },
    )
