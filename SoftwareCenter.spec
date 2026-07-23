# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['SoftwareCenter.py'],
    pathex=[],
    binaries=[],
    # icon.ico wird zur Laufzeit per Dateipfad geladen (Tray-Icon, Fenster-Icon) -- ohne
    # Buendelung erhaelt der Onefile-Build ein Null-Icon (T-20260721-02).
    datas=[('icon.ico', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pandas', 'playwright'],
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
    name='SoftwareCenter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
