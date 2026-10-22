"""Sesión de trabajo asociada con una fuente de audio."""

from dataclasses import dataclass
from pathlib import Path

from vocal_splitter.domain.audio_asset import AudioAsset


@dataclass(frozen=True, slots=True)
class AudioSession:
    session_id: str
    directory: Path
    asset: AudioAsset
