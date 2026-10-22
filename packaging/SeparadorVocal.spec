# PyInstaller build configuration. Model weights and user audio are never bundled.
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from pathlib import Path

project_root = Path(SPECPATH).resolve().parent.parent

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
    runtime_hooks=[],
    excludes=["pytest", "IPython", "notebook"],
    noarchive=False,
)
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
