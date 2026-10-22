"""Renderizado offline de transposición con Rubber Band mediante FFmpeg."""

from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

from vocal_splitter.infrastructure.audio.ffmpeg import find_ffmpeg


class PitchProcessingError(RuntimeError):
    pass


class PitchProcessor:
    def __init__(self, ffmpeg: str | None = None) -> None:
        self.ffmpeg = ffmpeg or find_ffmpeg()
        if not self.ffmpeg:
            raise PitchProcessingError("No se encontró FFmpeg en PATH")

    def supports_rubberband(self) -> bool:
        result = subprocess.run(
            [self.ffmpeg, "-hide_banner", "-filters"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        return result.returncode == 0 and "rubberband" in result.stdout

    def render(self, source: Path, destination: Path, semitones: int,
               *, preserve_formants: bool = False) -> Path:
        if not -12 <= semitones <= 12:
            raise PitchProcessingError("El cambio debe estar entre -12 y +12 semitonos")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if semitones == 0:
            shutil.copy2(source, destination)
            return destination
        if not self.supports_rubberband():
            raise PitchProcessingError(
                "Esta compilación de FFmpeg no incluye el filtro Rubber Band. "
                "Instala una compilación que lo incluya para cambiar el pitch."
            )
        ratio = math.pow(2.0, semitones / 12.0)
        temporary = destination.with_suffix(destination.suffix + ".part.wav")
        command = [
            self.ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(source), "-af",
            f"rubberband=pitch={ratio:.12f}:tempo=1.0:formant={'preserved' if preserve_formants else 'shifted'}",
            "-c:a", "pcm_f32le", str(temporary),
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=None,
                check=False,
            )
            if result.returncode != 0 or not temporary.is_file() or temporary.stat().st_size == 0:
                raise PitchProcessingError(result.stderr.strip() or "FFmpeg no pudo procesar el pitch")
            temporary.replace(destination)
            return destination
        finally:
            temporary.unlink(missing_ok=True)
