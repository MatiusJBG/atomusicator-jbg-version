"""Opciones validadas para exportar copias de las pistas."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExportOptions:
    format: str = "wav"
    sample_rate: int = 48000
    bit_depth: int = 24
    channels: int = 2
    normalize: bool = False

    def __post_init__(self) -> None:
        if self.format not in {"wav", "flac", "mp3"}:
            raise ValueError("Formato de exportación no admitido")
        if self.sample_rate not in {44100, 48000}:
            raise ValueError("Frecuencia de exportación no admitida")
        if self.bit_depth not in {16, 24} or self.channels not in {1, 2}:
            raise ValueError("Profundidad o canales de exportación no admitidos")
