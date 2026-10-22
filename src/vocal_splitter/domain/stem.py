"""Metadatos de un stem generado por el motor de separación."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from pathlib import Path


class StemKind(StrEnum):
    VOCAL_MIX = "vocal_mix"
    LEAD_VOCAL = "lead_vocal"
    BACKING_VOCALS = "backing_vocals"
    DRUMS = "drums"
    BASS = "bass"
    INSTRUMENTAL = "instrumental"


@dataclass(frozen=True, slots=True)
class Stem:
    kind: StemKind
    path: Path
    duration_seconds: float
    sample_rate_hz: int
    channels: int
    start_offset_seconds: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path):
            object.__setattr__(self, "path", Path(self.path))
        if not isfinite(self.duration_seconds) or self.duration_seconds <= 0:
            raise ValueError("La duración del stem debe ser un número positivo")
        if self.sample_rate_hz <= 0:
            raise ValueError("La frecuencia de muestreo debe ser positiva")
        if self.channels <= 0:
            raise ValueError("El número de canales debe ser positivo")
        if not isfinite(self.start_offset_seconds) or self.start_offset_seconds < 0:
            raise ValueError("El inicio del stem debe ser un número no negativo")
