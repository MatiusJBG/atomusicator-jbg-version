"""Exporta copias WAV sin bloquear la interfaz."""

from __future__ import annotations

import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from vocal_splitter.domain.separation_result import SeparationResult
from vocal_splitter.domain.stem import StemKind
from vocal_splitter.application.export_options import ExportOptions
from vocal_splitter.infrastructure.audio.ffmpeg import find_ffmpeg


_FILENAMES = {
    StemKind.LEAD_VOCAL: "voz_principal.wav",
    StemKind.BACKING_VOCALS: "coros.wav",
    StemKind.DRUMS: "bateria.wav",
    StemKind.BASS: "bajo.wav",
    StemKind.INSTRUMENTAL: "acompanamiento.wav",
    StemKind.VOCAL_MIX: "voz_total.wav",
}


class ExportWorker(QObject):
    exported = Signal(str)
    failed = Signal(str)
    done = Signal()
    progress = Signal(int)

    def __init__(self, result: SeparationResult, destination: Path,
                 options: ExportOptions | None = None) -> None:
        super().__init__()
        self.result = result
        self.destination = destination
        self.options = options

    @Slot()
    def run(self) -> None:
        export_dir = self.destination / (
            "Separador Vocal - " + datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        )
        try:
            if not self.destination.is_dir():
                raise OSError("La carpeta de destino ya no está disponible.")
            required = sum(stem.path.stat().st_size for stem in self.result.stems)
            if shutil.disk_usage(self.destination).free < required:
                raise OSError("No hay espacio suficiente para copiar los stems seleccionados.")
            export_dir.mkdir(parents=True)
            for index, stem in enumerate(self.result.stems):
                target = export_dir / _FILENAMES[stem.kind]
                if self.options is not None:
                    target = target.with_suffix("." + self.options.format)
                partial = target.with_name(target.stem + ".part" + target.suffix)
                if self.options is None:
                    shutil.copy2(stem.path, partial)
                else:
                    self._convert(stem.path, partial)
                partial.replace(target)
                self.progress.emit(round((index + 1) * 100 / len(self.result.stems)))
            self.exported.emit(str(export_dir))
        except Exception as error:
            shutil.rmtree(export_dir, ignore_errors=True)
            self.failed.emit(str(error))
        finally:
            self.done.emit()

    def _convert(self, source: Path, destination: Path) -> None:
        ffmpeg = find_ffmpeg()
        if not ffmpeg:
            raise OSError("No se encontró FFmpeg para convertir los stems.")
        options = self.options
        codec = {
            "wav": ["-c:a", f"pcm_s{options.bit_depth}le"],
            "flac": ["-c:a", "flac", "-sample_fmt", "s16" if options.bit_depth == 16 else "s32"],
            "mp3": ["-c:a", "libmp3lame", "-b:a", "320k"],
        }[options.format]
        command = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                   "-i", str(source)]
        if options.normalize:
            command += ["-af", "loudnorm=I=-16:TP=-1:LRA=11"]
        command += ["-ar", str(options.sample_rate), "-ac", str(options.channels),
                    *codec, str(destination)]
        completed = subprocess.run(command, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", check=False,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if completed.returncode != 0 or not destination.is_file():
            raise OSError(completed.stderr.strip() or "No se pudo convertir el audio.")
