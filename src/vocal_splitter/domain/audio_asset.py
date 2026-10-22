"""Metadatos normalizados de un archivo de audio local."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AudioAsset:
    source_path: Path
    duration_seconds: float
    sample_rate_hz: int
    channels: int
    size_bytes: int

    @property
    def file_name(self) -> str:
        return self.source_path.name
