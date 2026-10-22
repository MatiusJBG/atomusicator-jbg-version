"""Caso de uso para validar una fuente y preparar su sesión."""

from pathlib import Path

from vocal_splitter.application.project_settings import ProjectSettings
from vocal_splitter.domain.audio_session import AudioSession
from vocal_splitter.infrastructure.audio.errors import AudioImportError
from vocal_splitter.infrastructure.audio.metadata_reader import MetadataReader
from vocal_splitter.infrastructure.projects.session_store import SessionStore


class ImportAudioService:
    def __init__(
        self,
        metadata_reader: MetadataReader | None = None,
        session_store: SessionStore | None = None,
    ) -> None:
        self._metadata_reader = metadata_reader or MetadataReader()
        self._session_store = session_store or SessionStore()

    def import_file(self, source_path: Path, settings: ProjectSettings) -> AudioSession:
        asset = self._metadata_reader.read(source_path)
        try:
            return self._session_store.create(asset, settings.projects_directory)
        except OSError as error:
            raise AudioImportError(
                "No se pudo crear la sesión en la carpeta de proyectos. "
                "Revisa la ubicación o el espacio disponible."
            ) from error
