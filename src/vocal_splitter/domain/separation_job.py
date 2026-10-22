"""Estado de una operación de separación de voces."""

from dataclasses import dataclass
from enum import StrEnum


class SeparationStage(StrEnum):
    PREPARING = "preparing"
    VOICE_AND_INSTRUMENTAL = "voice_and_instrumental"
    LEAD_AND_BACKING = "lead_and_backing"
    FINALIZING = "finalizing"


class SeparationJobState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    CANCELLING = "cancelling"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class SeparationJob:
    """Immutable UI-friendly snapshot of a separation job."""

    job_id: str
    state: SeparationJobState = SeparationJobState.PENDING
    stage: SeparationStage = SeparationStage.PREPARING
    progress_percent: int = 0
    message: str = "Preparando separación…"
    error_code: str | None = None

    def __post_init__(self) -> None:
        if not self.job_id.strip():
            raise ValueError("job_id no puede estar vacío")
        if not 0 <= self.progress_percent <= 100:
            raise ValueError("progress_percent debe estar entre 0 y 100")
        if self.state is SeparationJobState.SUCCEEDED and self.progress_percent != 100:
            raise ValueError("Un trabajo terminado correctamente debe marcar 100 %")

    def start(self) -> "SeparationJob":
        if self.state is not SeparationJobState.PENDING:
            raise ValueError("Solo se puede iniciar un trabajo pendiente")
        return self._replace(state=SeparationJobState.RUNNING)

    def advance(
        self,
        stage: SeparationStage,
        progress_percent: int,
        message: str,
    ) -> "SeparationJob":
        if self.state is not SeparationJobState.RUNNING:
            raise ValueError("Solo un trabajo activo puede avanzar")
        if progress_percent < self.progress_percent:
            raise ValueError("El progreso de un trabajo no puede retroceder")
        if not 0 <= progress_percent <= 99:
            raise ValueError("El progreso intermedio debe estar entre 0 y 99")
        return self._replace(
            stage=stage,
            progress_percent=progress_percent,
            message=message,
        )

    def request_cancel(self) -> "SeparationJob":
        if self.state not in {
            SeparationJobState.PENDING,
            SeparationJobState.RUNNING,
        }:
            return self
        return self._replace(state=SeparationJobState.CANCELLING, message="Cancelando…")

    def succeed(self) -> "SeparationJob":
        if self.state is not SeparationJobState.RUNNING:
            raise ValueError("Solo un trabajo activo puede finalizar correctamente")
        return self._replace(
            state=SeparationJobState.SUCCEEDED,
            stage=SeparationStage.FINALIZING,
            progress_percent=100,
            message="Separación lista",
            error_code=None,
        )

    def fail(self, error_code: str, message: str, *, partial: bool = False) -> "SeparationJob":
        if self.state not in {
            SeparationJobState.RUNNING,
            SeparationJobState.CANCELLING,
        }:
            raise ValueError("Solo un trabajo activo puede fallar")
        return self._replace(
            state=SeparationJobState.PARTIAL if partial else SeparationJobState.FAILED,
            message=message,
            error_code=error_code,
        )

    def cancel(self) -> "SeparationJob":
        if self.state not in {
            SeparationJobState.RUNNING,
            SeparationJobState.CANCELLING,
        }:
            raise ValueError("Solo un trabajo activo puede cancelarse")
        return self._replace(
            state=SeparationJobState.CANCELLED,
            message="Separación cancelada",
        )

    def _replace(self, **changes) -> "SeparationJob":
        values = {
            "job_id": self.job_id,
            "state": self.state,
            "stage": self.stage,
            "progress_percent": self.progress_percent,
            "message": self.message,
            "error_code": self.error_code,
        }
        values.update(changes)
        return SeparationJob(**values)
