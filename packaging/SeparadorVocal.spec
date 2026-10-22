# PyInstaller build configuration. Model weights and user audio are never bundled.
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from pathlib import Path
import importlib.util
import sys
import runpy

project_root = Path(SPECPATH).resolve().parent
prepare_ffmpeg = runpy.run_path(str(project_root / "packaging" / "prepare_ffmpeg.py"))
ffmpeg_binaries, ffmpeg_data = prepare_ffmpeg["get_bundle_entries"](project_root)

datas = collect_data_files("vocal_splitter")
datas += ffmpeg_data
datas += collect_data_files("audio_separator", includes=["**/*.json", "**/*.yaml"])
hiddenimports = collect_submodules("audio_separator.separator.architectures")
hiddenimports += collect_submodules("audio_separator.separator.uvr_lib_v5")
hiddenimports += collect_submodules("audio_separator.separator.roformer")

torchvision_spec = importlib.util.find_spec("torchvision")
if torchvision_spec is None or not torchvision_spec.submodule_search_locations:
    raise RuntimeError("No se encontró el paquete torchvision del entorno de compilación.")
torchvision_package = Path(next(iter(torchvision_spec.submodule_search_locations)))
torchvision_extensions = [
    (str(extension), "torchvision")
    for extension in torchvision_package.glob("*.pyd")
]
if not any(Path(source).name == "_C_stable.pyd" for source, _ in torchvision_extensions):
    raise RuntimeError(
        "torchvision/_C_stable.pyd no está instalado; no se puede compilar una app funcional."
    )

a = Analysis(
    [str(project_root / "src" / "vocal_splitter" / "__main__.py")],
    pathex=[str(project_root / "src")],
    binaries=torchvision_extensions + ffmpeg_binaries,
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
