"""Localiza FFmpeg en PATH o en los enlaces de WinGet del usuario."""

import os
from pathlib import Path
from shutil import which


def find_ffmpeg() -> str | None:
    found = which("ffmpeg")
    if found:
        return found
    if os.name == "nt":
        candidate = Path.home() / "AppData/Local/Microsoft/WinGet/Links/ffmpeg.exe"
        if candidate.is_file():
            return str(candidate)
    return None


def ensure_ffmpeg_on_path() -> str | None:
    executable = find_ffmpeg()
    if executable:
        directory = str(Path(executable).parent)
        entries = os.environ.get("PATH", "").split(os.pathsep)
        if not any(os.path.normcase(entry) == os.path.normcase(directory) for entry in entries):
            os.environ["PATH"] = directory + os.pathsep + os.environ.get("PATH", "")
    return executable
