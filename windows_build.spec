# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

# ── Collect third-party packages ──────────────────────────────────────────────
datas = []
binaries = []
hiddenimports = []

for pkg in ('PySide6', 'google.genai', 'requests', 'timezonefinder', 'h3', 'msal', 'cryptography'):
    tmp = collect_all(pkg)
    datas    += tmp[0]
    binaries += tmp[1]
    hiddenimports += tmp[2]

# Add local assets
datas += [
    ('Icons', 'Icons'),
    ('app.ico', '.'),
    ('ui/world_map.jpg', 'ui'),
]

# Ensure all sub-modules of requests and google are found
hiddenimports += collect_submodules('requests')
hiddenimports += collect_submodules('google.genai')
hiddenimports += [
    'http.server',
    'socketserver',
    'urllib.parse',
    'webbrowser',
    'base64',
    'json',
    'threading',
    'ui.main_window',
    'ui.settings_window',
    'ui.utils',
    'ui.import_preview',
    'modules.config_manager',
    'modules.contact_book',
    'modules.gemini_ai',
    'modules.auth_handler',
    'modules.goto_api',
    'modules.ollama_ai',
    'modules.rate_limiter',
    'modules.calendar_sync',
    'ui.auth_window',
]

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'mypy', 'pydantic.mypy'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# ── Executable ────────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PKB SMS Assistant.exe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app.ico'],
)
