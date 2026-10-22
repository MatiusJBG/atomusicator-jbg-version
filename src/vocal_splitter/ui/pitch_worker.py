"""Procesamiento de pitch en segundo plano para mantener libre la interfaz."""

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from vocal_splitter.domain.separation_result import SeparationResult
from vocal_splitter.domain.stem import Stem
from vocal_splitter.infrastructure.audio.pitch_processor import PitchProcessor


class PitchWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)
    done = Signal()
    progress = Signal(int)

    def __init__(self, result: SeparationResult, output_dir: Path, semitones: int,
                 preserve_formants: bool = False) -> None:
        super().__init__()
        self.result = result
        self.output_dir = output_dir
        self.semitones = semitones
        self.preserve_formants = preserve_formants

    @Slot()
    def run(self) -> None:
        try:
            processor = PitchProcessor()
            rendered: list[Stem] = []
            suffix = "-formants" if self.preserve_formants else ""
            target_dir = self.output_dir / f"pitch-{self.semitones:+d}{suffix}"
            self.progress.emit(0)
            for index, stem in enumerate(self.result.stems):
                target = target_dir / f"{stem.kind}.wav"
                processor.render(stem.path, target, self.semitones,
                                 preserve_formants=self.preserve_formants)
                rendered.append(Stem(
                    kind=stem.kind, path=target,
                    duration_seconds=stem.duration_seconds,
                    sample_rate_hz=stem.sample_rate_hz, channels=stem.channels,
                    start_offset_seconds=stem.start_offset_seconds,
                ))
                self.progress.emit(round((index + 1) * 100 / len(self.result.stems)))
            self.finished.emit(SeparationResult(tuple(rendered), self.result.engine_usage))
        except Exception as error:
            self.failed.emit(str(error))
        finally:
            self.done.emit()
