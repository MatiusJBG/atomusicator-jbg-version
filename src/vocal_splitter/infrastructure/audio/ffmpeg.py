"""Resuelve las herramientas incluidas; usa el sistema solo en desarrollo."""

import os
import sys
from pathlib import Path
from shutil import which


def bundled_tools_directory() -> Path:
    if getattr(sys, "frozen", False):
        root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        return root / "runtime" / "ffmpeg" / "bin"
    return Path(__file__).resolve().parents[4] / "build" / "ffmpeg-runtime" / "bin"


def _bundled_tool(name: str) -> str | None:
    directory = bundled_tools_directory()
    if all((directory / tool).is_file() for tool in ("ffmpeg.exe", "ffprobe.exe")):
        return str(directory / name)
    return None


def find_ffmpeg() -> str | None:
    bundled = _bundled_tool("ffmpeg.exe")
    if bundled:
        return bundled
    # A frozen package must work on its own. Falling back to the build host
    # would conceal a broken distribution until it reaches another computer.
    if getattr(sys, "frozen", False) or bundled_tools_directory().exists():
        return None
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


def find_ffprobe() -> str | None:
    bundled = _bundled_tool("ffprobe.exe")
    if bundled:
        return bundled
    if getattr(sys, "frozen", False) or bundled_tools_directory().exists():
        return None
    executable = find_ffmpeg()
    if executable:
        sibling = Path(executable).with_name("ffprobe.exe" if os.name == "nt" else "ffprobe")
        if sibling.is_file():
            return str(sibling)
    try:
        found = which("ffprobe")
    except OSError:
        return None
    return _resolved_link_target(found) if found else None


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
