"""Lectura local de los metadatos de los formatos de audio admitidos."""

import math
from pathlib import Path

from mutagen import File as MutagenFile
from mutagen import MutagenError

from vocal_splitter.domain.audio_asset import AudioAsset
from vocal_splitter.infrastructure.audio.errors import (
    InvalidAudioFileError,
    UnsupportedAudioFormatError,
)


SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a"}


class MetadataReader:
    def read(self, source_path: Path) -> AudioAsset:
        path = source_path.expanduser()
        extension = path.suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise UnsupportedAudioFormatError(
                "Formato no compatible. Elige un archivo WAV, MP3, FLAC o M4A."
            )

        try:
            resolved_path = path.resolve(strict=True)
            if not resolved_path.is_file():
                raise InvalidAudioFileError("La ruta seleccionada no es un archivo.")
            size_bytes = resolved_path.stat().st_size
            if size_bytes == 0:
                raise InvalidAudioFileError("El archivo está vacío.")
            audio_file = MutagenFile(resolved_path)
            info = audio_file.info if audio_file is not None else None
            duration = float(info.length) if info and info.length is not None else 0.0
            sample_rate = int(info.sample_rate) if info and info.sample_rate else 0
            channels = int(info.channels) if info and info.channels else 0
        except InvalidAudioFileError:
            raise
        except (OSError, MutagenError, ValueError, TypeError, EOFError) as error:
            raise InvalidAudioFileError(
                "No se pudo leer el audio. Verifica que el archivo no esté dañado."
            ) from error

        if not math.isfinite(duration) or duration <= 0 or sample_rate <= 0 or channels <= 0:
            raise InvalidAudioFileError(
                "El archivo no contiene una pista de audio válida o sus metadatos están incompletos."
            )

        return AudioAsset(
            source_path=resolved_path,
            duration_seconds=duration,
            sample_rate_hz=sample_rate,
            channels=channels,
            size_bytes=size_bytes,
        )
