# -*- mode: python ; coding: utf-8 -*-
import importlib.util
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules,copy_metadata
ROOT=Path(SPEC).resolve().parents[1]
hs=importlib.util.spec_from_file_location("runtime",ROOT/"packaging"/"pyinstaller_runtime.py");m=importlib.util.module_from_spec(hs);hs.loader.exec_module(m)
hiddenimports=collect_submodules("pyvisa_py",filter=lambda n:not n.startswith("pyvisa_py.testsuite"));datas=copy_metadata("PyVISA")+copy_metadata("PyVISA-py")
a=Analysis([str(ROOT/"src"/"port_bridge"/"modern_entry.py")],pathex=[str(ROOT/"src")],binaries=[],datas=datas,hiddenimports=hiddenimports,hookspath=[],hooksconfig={},runtime_hooks=[],excludes=[],noarchive=False,optimize=0)
a.binaries=m.normalize_msvc_runtime_binaries(a.binaries);pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name="PortBridge",debug=False,strip=False,upx=False,console=False)
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name="PortBridge")
