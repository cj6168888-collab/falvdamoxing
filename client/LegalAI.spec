# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\重要\\www\\www\\法律大模型\\client\\run_client.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\重要\\www\\www\\法律大模型\\client\\dist', 'client/dist'), ('D:\\重要\\www\\www\\法律大模型\\client\\app', 'app'), ('D:\\重要\\www\\www\\法律大模型\\client\\.env', '.')],
    hiddenimports=['uvicorn.logging', 'uvicorn.loops.auto', 'uvicorn.protocols.http.auto', 'fastapi', 'sqlalchemy', 'pydantic', 'passlib', 'jose', 'webview', 'multipart', 'aiofiles'],
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
    [],
    exclude_binaries=True,
    name='LegalAI',
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
    icon=['D:\\重要\\www\\www\\法律大模型\\client\\legal-ai.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LegalAI',
)
