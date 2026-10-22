"""Exporta copias WAV sin bloquear la interfaz."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from vocal_splitter.domain.separation_result import SeparationResult
from vocal_splitter.domain.stem import StemKind


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

    def __init__(self, result: SeparationResult, destination: Path) -> None:
        super().__init__()
        self.result = result
        self.destination = destination

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
            for stem in self.result.stems:
                target = export_dir / _FILENAMES[stem.kind]
                partial = target.with_suffix(".wav.part")
                shutil.copy2(stem.path, partial)
                partial.replace(target)
            self.exported.emit(str(export_dir))
        except Exception as error:
            shutil.rmtree(export_dir, ignore_errors=True)
            self.failed.emit(str(error))
        finally:
            self.done.emit()
