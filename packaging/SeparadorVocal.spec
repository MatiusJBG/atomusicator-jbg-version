# PyInstaller build configuration. Model weights and user audio are never bundled.
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from pathlib import Path
import sys

project_root = Path(SPECPATH).resolve().parent

datas = collect_data_files("vocal_splitter")
datas += collect_data_files("audio_separator", includes=["**/*.json", "**/*.yaml"])
hiddenimports = collect_submodules("audio_separator.separator.architectures")
hiddenimports += collect_submodules("audio_separator.separator.uvr_lib_v5")
hiddenimports += collect_submodules("audio_separator.separator.roformer")

a = Analysis(
    [str(project_root / "src" / "vocal_splitter" / "__main__.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(project_root / "packaging" / "pyi_rth_qt_dll_path.py")],
    excludes=["pytest", "IPython", "notebook"],
    noarchive=False,
)

# Do not package same-named C/C++ runtimes selected from arbitrary PATH
# entries. Qt and Python need a compatible pair; the build host may expose
# newer copies from Java, image libraries, or other software.
runtime_overrides = {
    "msvcp140.dll": project_root / ".venv" / "Lib" / "site-packages" / "PySide6" / "MSVCP140.dll",
    "vcruntime140.dll": Path(sys.base_prefix) / "VCRUNTIME140.dll",
    "vcruntime140_1.dll": Path(sys.base_prefix) / "VCRUNTIME140_1.dll",
}
a.binaries = [entry for entry in a.binaries if entry[0].casefold() not in runtime_overrides]
for destination, source in runtime_overrides.items():
    if source.is_file():
        a.binaries.append((destination, str(source), "BINARY"))

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SeparadorVocal",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)
