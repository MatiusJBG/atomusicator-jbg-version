"""Keep PySide6 bound to the Qt and Python DLLs bundled with the app."""

import ctypes
import os
import sys
from pathlib import Path


if getattr(sys, "frozen", False) and sys.platform == "win32":
    bundle_root = Path(sys._MEIPASS)
    qt_directory = bundle_root / "PySide6"
    dll_directories = [qt_directory, bundle_root]

    # os.add_dll_directory uses the Windows user DLL search path. Keep the
    # handles alive for the process lifetime so PATH entries from other apps
    # (for example MySQL Shell's python3.dll) cannot shadow this bundle.
    _dll_directory_handles = [
        os.add_dll_directory(str(directory))
        for directory in dll_directories
        if directory.is_dir()
    ]

    # Other dependencies (notably scikit-learn) can ship another msvcp140.dll
    # at the bundle root. Load Qt's matching runtime by absolute path before
    # QtWidgets.pyd asks Windows to resolve it by basename.
    _qt_runtime_libraries = [
        ctypes.WinDLL(str(qt_directory / name))
        for name in ("MSVCP140.dll", "VCRUNTIME140.dll", "VCRUNTIME140_1.dll")
        if (qt_directory / name).is_file()
    ]

    bundled_paths = [str(directory) for directory in dll_directories if directory.is_dir()]
    existing_path = os.environ.get("PATH", "")
    os.environ["PATH"] = os.pathsep.join([*bundled_paths, existing_path])
