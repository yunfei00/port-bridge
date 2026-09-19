import importlib.util
from pathlib import Path
MSVC_RUNTIME_NAMES={"msvcp140.dll","msvcp140_1.dll","msvcp140_2.dll","vcruntime140.dll","vcruntime140_1.dll"}
def _sources():
    spec=importlib.util.find_spec("PySide6")
    if spec is None or not spec.submodule_search_locations: raise RuntimeError("PySide6 not found")
    root=Path(next(iter(spec.submodule_search_locations))).resolve()
    result={n:root/n for n in MSVC_RUNTIME_NAMES if (root/n).is_file()}
    if "vcruntime140.dll" not in result or "vcruntime140_1.dll" not in result: raise RuntimeError("Required PySide6 MSVC runtime DLLs not found")
    return result
def normalize_msvc_runtime_binaries(binaries):
    sources=_sources();out=[]
    for entry in binaries:
        if len(entry)!=3:out.append(entry);continue
        dest,src,typecode=entry;canonical=sources.get(Path(dest).name.lower())
        out.append((dest,str(canonical) if canonical else src,typecode))
    return out
