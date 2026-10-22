"""Ejecución de separación local fuera del hilo gráfico."""

import logging
import threading
import uuid

from PySide6.QtCore import QObject, Signal, Slot

from vocal_splitter.application.ports.vocal_separator import ProgressCallback
from vocal_splitter.application.separation_errors import (
    PartialSeparationError,
    SeparationCancelledError,
    SeparationError,
)
from vocal_splitter.application.separate_vocals import SeparateVocals
from vocal_splitter.domain.audio_session import AudioSession
from vocal_splitter.domain.separation_job import (
    SeparationJob,
    SeparationStage,
)
from vocal_splitter.domain.separation_result import SeparationResult

logger = logging.getLogger(__name__)


class _Cancellation:
    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        if self.is_cancelled():
            raise SeparationCancelledError()


class SeparationWorker(QObject):
    progress = Signal(str, int)
    succeeded = Signal(object)
    failed = Signal(str, object)
    cancelled = Signal()
    finished = Signal()

    def __init__(self, service: SeparateVocals, session: AudioSession) -> None:
        super().__init__()
        self._service = service
        self._session = session
        self._cancellation = _Cancellation()
        self._job = SeparationJob(uuid.uuid4().hex).start()

    def cancel(self) -> None:
        self._job = self._job.request_cancel()
        self._cancellation.cancel()

    @Slot()
    def run(self) -> None:
        def report(stage: SeparationStage, percent: int, message: str) -> None:
            if self._job.state.value == "running":
                self._job = self._job.advance(stage, percent, message)
            self.progress.emit(message, percent)

        try:
            result = self._service.execute(
                self._session,
                progress=report,
                cancellation=self._cancellation,
            )
        except SeparationCancelledError:
            self.cancelled.emit()
        except PartialSeparationError as error:
            self.failed.emit(str(error), error.partial_result)
        except SeparationError as error:
            self.failed.emit(error.user_message, None)
        except Exception:
            logger.exception("Unexpected error in separation worker")
            self.failed.emit(
                "No se pudo preparar la separación. Revisa la sesión y vuelve a intentarlo.",
                None,
            )
        else:
            self._job = self._job.succeed()
            self.succeeded.emit(result)
        finally:
            self.finished.emit()
