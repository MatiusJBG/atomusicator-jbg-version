"""Orquestación de la separación local en cinco stems finales."""

import json
import logging
import os
import shutil
import uuid
from dataclasses import replace
from pathlib import Path

from vocal_splitter.application.ports.vocal_separator import (
    CancellationToken,
    ProgressCallback,
    VocalSeparator,
)
from vocal_splitter.application.separation_errors import (
    PartialSeparationError,
    SeparationCancelledError,
    SeparationError,
    SeparationOutputError,
    SeparationStorageError,
)
from vocal_splitter.domain.audio_session import AudioSession
from vocal_splitter.domain.separation_job import SeparationStage
from vocal_splitter.domain.separation_result import SeparationResult
from vocal_splitter.domain.stem import Stem, StemKind
from vocal_splitter.infrastructure.projects.session_store import SessionStore

logger = logging.getLogger(__name__)


class SeparateVocals:
    def __init__(
        self,
        separator: VocalSeparator,
        session_store: SessionStore | None = None,
    ) -> None:
        self._separator = separator
        self._session_store = session_store or SessionStore()

    def execute(
        self,
        session: AudioSession,
        *,
        progress: ProgressCallback,
        cancellation: CancellationToken,
    ) -> SeparationResult:
        job_id = uuid.uuid4().hex
        session_dir = session.directory.resolve()
        source = session.asset.source_path.resolve()
        if not source.is_file():
            raise SeparationOutputError("No se encuentra el archivo de audio importado")
        if not (session_dir / "session.json").is_file():
            raise SeparationOutputError("No se encuentra el manifiesto de la sesión")
        self._check_free_space(session)

        processing_root = session_dir / "processing"
        outputs_root = session_dir / "outputs"
        job_dir = processing_root / job_id
        stage_one_dir = job_dir / "stage-one"
        stage_two_dir = job_dir / "stage-two"
        stage_three_dir = job_dir / "stage-three"
        stage_four_dir = job_dir / "stage-four"
        publish_dir = job_dir / "publish"
        try:
            processing_root.mkdir(exist_ok=True)
            outputs_root.mkdir(exist_ok=True)
            job_dir.mkdir()
            stage_one_dir.mkdir()
            stage_two_dir.mkdir()
            stage_three_dir.mkdir()
            stage_four_dir.mkdir()
            publish_dir.mkdir()
        except OSError as error:
            logger.exception("Could not create separation directories in %s", session_dir)
            raise SeparationStorageError(self._storage_message(error, session_dir)) from error

        progress(SeparationStage.PREPARING, 0, "Preparando separación…")
        cancellation.raise_if_cancelled()
        try:
            first_stage = self._separator.separate_voice_and_instrumental(
                source,
                stage_one_dir,
                progress=self._map_progress(progress, 5, 25),
                cancellation=cancellation,
            )
            self._require_kinds(first_stage, {StemKind.VOCAL_MIX, StemKind.INSTRUMENTAL})
            vocal_mix = first_stage.stem(StemKind.VOCAL_MIX)

            try:
                second_stage = self._separator.separate_lead_and_backing(
                    vocal_mix,
                    stage_two_dir,
                    progress=self._map_progress(progress, 28, 48),
                    cancellation=cancellation,
                )
                self._require_kinds(
                    second_stage,
                    {StemKind.LEAD_VOCAL, StemKind.BACKING_VOCALS},
                )
            except SeparationCancelledError:
                raise
            except Exception as error:
                partial_result = self._publish_partial(
                    session, job_id, first_stage, outputs_root, job_dir
                )
                if isinstance(error, SeparationError):
                    message = (
                        f"{error.user_message} Se conservaron voz total y acompañamiento "
                        f"en {partial_result.stems[0].path.parent}."
                    )
                else:
                    logger.exception("Second vocal separation stage failed")
                    message = (
                        "Falló la separación entre voz principal y coros. Se conservaron "
                        f"voz total y acompañamiento en {partial_result.stems[0].path.parent}."
                    )
                raise PartialSeparationError(message, partial_result) from error

            vocals_only = SeparationResult(
                second_stage.stems,
                self._combined_engine_usage(first_stage, second_stage),
            )
            try:
                drums_stage = self._separator.separate_drums_and_residual(
                    first_stage.stem(StemKind.INSTRUMENTAL),
                    stage_three_dir,
                    progress=self._map_progress(progress, 51, 72),
                    cancellation=cancellation,
                )
                self._require_kinds(drums_stage, {StemKind.DRUMS, StemKind.INSTRUMENTAL})
            except SeparationCancelledError:
                raise
            except Exception as error:
                partial = SeparationResult(
                    (*vocals_only.stems, first_stage.stem(StemKind.INSTRUMENTAL)),
                    vocals_only.engine_usage,
                )
                self._raise_partial_failure(
                    session,
                    job_id,
                    partial,
                    outputs_root,
                    job_dir,
                    error,
                    "No se pudo separar la batería. Se conservaron las voces y el acompañamiento como resultados parciales.",
                )

            try:
                bass_stage = self._separator.separate_bass_and_instrumental(
                    drums_stage.stem(StemKind.INSTRUMENTAL),
                    stage_four_dir,
                    progress=self._map_progress(progress, 74, 94),
                    cancellation=cancellation,
                )
                self._require_kinds(bass_stage, {StemKind.BASS, StemKind.INSTRUMENTAL})
            except SeparationCancelledError:
                raise
            except Exception as error:
                partial = vocals_only.combine(drums_stage)
                self._raise_partial_failure(
                    session,
                    job_id,
                    partial,
                    outputs_root,
                    job_dir,
                    error,
                    "No se pudo separar el bajo. Se conservaron las voces, la batería y el resto instrumental como resultados parciales.",
                )

            complete = SeparationResult(
                (
                    second_stage.stem(StemKind.LEAD_VOCAL),
                    second_stage.stem(StemKind.BACKING_VOCALS),
                    drums_stage.stem(StemKind.DRUMS),
                    bass_stage.stem(StemKind.BASS),
                    bass_stage.stem(StemKind.INSTRUMENTAL),
                ),
                self._combined_engine_usage(
                    first_stage, second_stage, drums_stage, bass_stage
                ),
            )
            if not complete.is_final:
                raise SeparationOutputError("El motor no entregó los cinco stems finales")
            cancellation.raise_if_cancelled()
            progress(SeparationStage.FINALIZING, 90, "Guardando pistas alineadas…")
            final_names = {
                StemKind.LEAD_VOCAL: "voz_principal.wav",
                StemKind.BACKING_VOCALS: "coros.wav",
                StemKind.DRUMS: "bateria.wav",
                StemKind.BASS: "bajo.wav",
                StemKind.INSTRUMENTAL: "instrumental.wav",
            }
            published_stems: list[Stem] = []
            for kind, name in final_names.items():
                stem = complete.stem(kind)
                target = publish_dir / name
                os.replace(stem.path, target)
                published_stems.append(replace(stem, path=target))

            final_result = SeparationResult(tuple(published_stems), complete.engine_usage)
            output_dir = outputs_root / f"separation-{job_id}"
            os.replace(publish_dir, output_dir)
            final_result = SeparationResult(
                tuple(replace(stem, path=output_dir / stem.path.name) for stem in final_result.stems),
                final_result.engine_usage,
            )
            try:
                self._session_store.record_separation(
                    session,
                    self._record(session, job_id, "complete", final_result),
                )
            except OSError:
                shutil.rmtree(output_dir, ignore_errors=True)
                raise
            progress(SeparationStage.FINALIZING, 99, "Separación lista")
            shutil.rmtree(job_dir, ignore_errors=True)
            return final_result
        except SeparationCancelledError:
            shutil.rmtree(job_dir, ignore_errors=True)
            raise
        except PartialSeparationError:
            raise
        except SeparationError:
            shutil.rmtree(job_dir, ignore_errors=True)
            raise
        except OSError as error:
            shutil.rmtree(job_dir, ignore_errors=True)
            logger.exception("Storage operation failed in session %s", session_dir)
            raise SeparationStorageError(self._storage_message(error, session_dir)) from error
        except Exception as error:
            shutil.rmtree(job_dir, ignore_errors=True)
            logger.exception("Unexpected failure in vocal separation")
            raise SeparationOutputError() from error

    @staticmethod
    def _check_free_space(session: AudioSession) -> None:
        asset = session.asset
        estimated_bytes = int(
            asset.duration_seconds * asset.sample_rate_hz * asset.channels * 4 * 10
            + 256 * 1024 * 1024
        )
        try:
            available = shutil.disk_usage(session.directory).free
        except OSError as error:
            logger.exception("Could not check free disk space for %s", session.directory)
            raise SeparationStorageError(
                SeparateVocals._storage_message(error, session.directory)
            ) from error
        if available < estimated_bytes:
            available_mb = available // (1024 * 1024)
            required_mb = (estimated_bytes + 1024 * 1024 - 1) // (1024 * 1024)
            raise SeparationStorageError(
                "No hay espacio libre suficiente en la unidad donde se guardan los proyectos. "
                f"La separación necesita aproximadamente {required_mb} MB y hay {available_mb} MB. "
                "Libera espacio o cambia la carpeta desde Archivo > Carpeta de proyectos…"
            )

    @staticmethod
    def _storage_message(error: OSError, fallback_path: Path) -> str:
        failed_path = getattr(error, "filename", None) or fallback_path
        reason = getattr(error, "strerror", None) or str(error) or "error de Windows"
        winerror = getattr(error, "winerror", None)
        code = f" (código {winerror})" if winerror is not None else ""
        return (
            "Windows no pudo guardar los archivos de separación en "
            f"{failed_path}. Motivo: {reason}{code}. Verifica los permisos de esa carpeta "
            "o cámbiala desde Archivo > Carpeta de proyectos…"
        )

    @staticmethod
    def _require_kinds(result: SeparationResult, expected: set[StemKind]) -> None:
        actual = {stem.kind for stem in result.stems}
        if actual != expected:
            raise SeparationOutputError("El motor devolvió tipos de salida inesperados")

    @staticmethod
    def _map_progress(
        callback: ProgressCallback,
        lower: int,
        upper: int,
    ) -> ProgressCallback:
        def mapped(stage: SeparationStage, percent: int, message: str) -> None:
            normalized = lower + round((upper - lower) * max(0, min(percent, 100)) / 100)
            callback(stage, normalized, message)

        return mapped

    def _publish_partial(
        self,
        session: AudioSession,
        job_id: str,
        result: SeparationResult,
        outputs_root: Path,
        job_dir: Path,
    ) -> SeparationResult:
        partial_dir = outputs_root / f"separation-{job_id}-partial"
        partial_dir.mkdir()
        names = {
            StemKind.VOCAL_MIX: "voz_total.wav",
            StemKind.LEAD_VOCAL: "voz_principal.wav",
            StemKind.BACKING_VOCALS: "coros.wav",
            StemKind.DRUMS: "bateria.wav",
            StemKind.BASS: "bajo.wav",
            StemKind.INSTRUMENTAL: "acompanamiento_parcial.wav",
        }
        moved: list[Stem] = []
        for stem in result.stems:
            target = partial_dir / names[stem.kind]
            os.replace(stem.path, target)
            moved.append(replace(stem, path=target))
        partial_result = SeparationResult(tuple(moved), result.engine_usage)
        try:
            self._session_store.record_separation(
                session,
                self._record(session, job_id, "partial", partial_result),
            )
        except OSError:
            shutil.rmtree(partial_dir, ignore_errors=True)
            raise
        shutil.rmtree(job_dir, ignore_errors=True)
        return partial_result

    def _raise_partial_failure(
        self,
        session: AudioSession,
        job_id: str,
        partial: SeparationResult,
        outputs_root: Path,
        job_dir: Path,
        error: Exception,
        message: str,
    ) -> None:
        if isinstance(error, SeparationError):
            message = f"{error.user_message} {message}"
        else:
            logger.exception("Separation stage failed", exc_info=error)
        saved = self._publish_partial(
            session, job_id, partial, outputs_root, job_dir
        )
        raise PartialSeparationError(
            f"{message} Se guardaron en {saved.stems[0].path.parent}.", saved
        ) from error

    @staticmethod
    def _record(
        session: AudioSession,
        job_id: str,
        status: str,
        result: SeparationResult,
    ) -> dict:
        session_root = session.directory.resolve()
        return {
            "job_id": job_id,
            "status": status,
            "stems": [
                {
                    "kind": stem.kind.value,
                    "path": str(stem.path.relative_to(session_root)),
                    "duration_seconds": stem.duration_seconds,
                    "sample_rate_hz": stem.sample_rate_hz,
                    "channels": stem.channels,
                    "start_offset_seconds": stem.start_offset_seconds,
                }
                for stem in result.stems
            ],
            "engine": (
                {
                    "name": result.engine_usage.name,
                    "version": result.engine_usage.version,
                    "models": [
                        {
                            "profile_id": model.profile_id,
                            "filename": model.filename,
                            "sha256": model.sha256,
                            "license": model.license,
                            "source_url": model.source_url,
                            "attribution": model.attribution,
                            "elapsed_seconds": model.elapsed_seconds,
                            "parameters": dict(model.parameters),
                        }
                        for model in result.engine_usage.models
                    ],
                }
                if result.engine_usage
                else None
            ),
        }

    @staticmethod
    def _combined_engine_usage(*results: SeparationResult):
        usages = [result.engine_usage for result in results if result.engine_usage]
        if not usages:
            return None
        unique_models = {
            model.profile_id: model
            for usage in usages
            for model in usage.models
        }
        return replace(usages[0], models=tuple(unique_models.values()))
