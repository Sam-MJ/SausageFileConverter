# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/app.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[
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
    "utils",
    "datetime",
    "os",
    "json",
    "dotenv"
],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
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
