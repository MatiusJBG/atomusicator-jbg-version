"""Localiza FFmpeg en PATH o en los enlaces de WinGet del usuario."""

import os
from pathlib import Path
from shutil import which


def find_ffmpeg() -> str | None:
    if os.name == "nt":
        candidate = Path.home() / "AppData/Local/Microsoft/WinGet/Links/ffmpeg.exe"
        try:
            target = os.readlink(candidate)
        except OSError:
            pass
        else:
            resolved = _resolved_link_target(str(candidate), target)
            if resolved != str(candidate):
                return resolved

    try:
        found = which("ffmpeg")
    except OSError:
        found = None
    if found:
        return _resolved_link_target(found)

    if os.name == "nt":
        candidate = Path.home() / "AppData/Local/Microsoft/WinGet/Links/ffmpeg.exe"
        try:
            return str(candidate) if candidate.is_file() else None
        except OSError:
            return None
    return None


def _resolved_link_target(executable: str, target: str | None = None) -> str:
    """Use the physical target of WinGet's link instead of traversing its reparse point."""
    if target is None:
        try:
            target = os.readlink(executable)
        except OSError:
            return executable

    if target.startswith("\\\\?\\"):
        target = target[4:]
    target_path = Path(target)
    if not target_path.is_absolute():
        target_path = Path(executable).parent / target_path
    try:
        return str(target_path) if target_path.is_file() else executable
    except OSError:
        return executable


def ensure_ffmpeg_on_path() -> str | None:
    executable = find_ffmpeg()
    if executable:
        directory = str(Path(executable).parent)
        entries = os.environ.get("PATH", "").split(os.pathsep)
        normalized_directory = os.path.normcase(directory)
        remaining = [
            entry
            for entry in entries
            if entry and os.path.normcase(entry) != normalized_directory
        ]
        os.environ["PATH"] = os.pathsep.join([directory, *remaining])
    return executable
