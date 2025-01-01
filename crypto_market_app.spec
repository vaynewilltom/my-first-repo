# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all required data files
matplotlib_data = collect_data_files('matplotlib')
tcl_tk_data = collect_data_files('tkinter')
pillow_data = collect_data_files('PIL')

# Collect all submodules to ensure complete packaging
hidden_imports = collect_submodules('matplotlib') + \
                collect_submodules('tkinter') + \
                collect_submodules('PIL') + \
                ['sqlite3', 'requests', 'bs4', 'numpy']

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src', 'src'),
        *matplotlib_data,
        *tcl_tk_data,
        *pillow_data,
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['src/runtime_hooks/init_db.py'],
    version_file='version_info.txt',
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,)

# Create the PYZ archive
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name='crypto_market_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
)
