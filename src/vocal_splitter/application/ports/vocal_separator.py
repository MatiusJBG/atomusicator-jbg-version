"""Contrato del motor, independiente del paquete de inferencia elegido."""

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from vocal_splitter.domain.separation_job import SeparationStage
from vocal_splitter.domain.separation_result import SeparationResult
from vocal_splitter.domain.stem import Stem


ProgressCallback = Callable[[SeparationStage, int, str], None]


class CancellationToken(Protocol):
    def is_cancelled(self) -> bool: ...

    def raise_if_cancelled(self) -> None: ...


class VocalSeparator(Protocol):
    def separate_voice_and_instrumental(
        self,
        source: Path,
        output_dir: Path,
        *,
        progress: ProgressCallback,
        cancellation: CancellationToken,
    ) -> SeparationResult: ...

    def separate_lead_and_backing(
        self,
        vocal_stem: Stem,
        output_dir: Path,
        *,
        progress: ProgressCallback,
        cancellation: CancellationToken,
    ) -> SeparationResult: ...

    def separate_drums_and_residual(
        self,
        instrumental_stem: Stem,
        output_dir: Path,
        *,
        progress: ProgressCallback,
        cancellation: CancellationToken,
    ) -> SeparationResult: ...

    def separate_bass_and_instrumental(
        self,
        instrumental_stem: Stem,
        output_dir: Path,
        *,
        progress: ProgressCallback,
        cancellation: CancellationToken,
    ) -> SeparationResult: ...
