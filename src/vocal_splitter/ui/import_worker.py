"""Ejecución de la importación fuera del hilo de interfaz."""

import logging
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from vocal_splitter.application.import_audio import ImportAudioService
from vocal_splitter.application.project_settings import ProjectSettings
from vocal_splitter.domain.audio_session import AudioSession
from vocal_splitter.infrastructure.audio.errors import AudioImportError

logger = logging.getLogger(__name__)


class ImportWorker(QObject):
    succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        service: ImportAudioService,
        source_path: Path,
        settings: ProjectSettings,
    ) -> None:
        super().__init__()
        self._service = service
        self._source_path = source_path
        self._settings = settings

    @Slot()
    def run(self) -> None:
        try:
            session: AudioSession = self._service.import_file(
                self._source_path,
                self._settings,
            )
        except AudioImportError as error:
            self.failed.emit(str(error))
        except Exception:
            logger.exception("Unexpected error while importing audio")
            self.failed.emit(
                "No se pudo preparar la sesión. Revisa el archivo y la carpeta de proyectos."
            )
        else:
            self.succeeded.emit(session)
        finally:
            self.finished.emit()
