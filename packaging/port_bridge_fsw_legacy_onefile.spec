# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules,copy_metadata
ROOT=Path(SPEC).resolve().parents[1]
hiddenimports=collect_submodules("pyvisa");datas=copy_metadata("PyVISA")
a=Analysis([str(ROOT/"src"/"port_bridge"/"legacy.py")],pathex=[str(ROOT/"src")],binaries=[],datas=datas,hiddenimports=hiddenimports,hookspath=[],hooksconfig={},runtime_hooks=[],excludes=["PySide6","PyQt5","PyQt6","numpy"],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name="PortBridgeLegacy",debug=False,strip=False,upx=False,console=False)
