"""Creación de sesiones locales sin copiar ni modificar el audio fuente."""

import json
import shutil
import uuid
from pathlib import Path

from vocal_splitter.domain.audio_asset import AudioAsset
from vocal_splitter.domain.audio_session import AudioSession


class SessionStore:
    def create(self, asset: AudioAsset, projects_directory: Path) -> AudioSession:
        session_id = uuid.uuid4().hex
        projects_directory.mkdir(parents=True, exist_ok=True)
        session_directory = projects_directory / session_id
        session_directory.mkdir()

        try:
            (session_directory / "outputs").mkdir()
            metadata_path = session_directory / "session.json"
            temporary_path = session_directory / "session.json.tmp"
            with temporary_path.open("w", encoding="utf-8", newline="\n") as metadata_file:
                json.dump(
                    {
                        "session_id": session_id,
                        "source_path": str(asset.source_path),
                        "file_name": asset.file_name,
                        "duration_seconds": asset.duration_seconds,
                        "sample_rate_hz": asset.sample_rate_hz,
                        "channels": asset.channels,
                        "size_bytes": asset.size_bytes,
                    },
                    metadata_file,
                    ensure_ascii=False,
                    indent=2,
                )
                metadata_file.write("\n")
            temporary_path.replace(metadata_path)
        except OSError:
            shutil.rmtree(session_directory, ignore_errors=True)
            raise

        return AudioSession(
            session_id=session_id,
            directory=session_directory,
            asset=asset,
        )

    def record_separation(self, session: AudioSession, record: dict) -> None:
        metadata_path = session.directory / "session.json"
        temporary_path = session.directory / "session.json.tmp"
        with metadata_path.open("r", encoding="utf-8") as metadata_file:
            metadata = json.load(metadata_file)
        if metadata.get("session_id") != session.session_id:
            raise OSError("La sesión no coincide con sus metadatos")
        metadata["separation"] = record
        with temporary_path.open("w", encoding="utf-8", newline="\n") as metadata_file:
            json.dump(metadata, metadata_file, ensure_ascii=False, indent=2)
            metadata_file.write("\n")
        temporary_path.replace(metadata_path)
