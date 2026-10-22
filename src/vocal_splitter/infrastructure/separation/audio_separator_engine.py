"""Adaptador verificado para el paquete opcional ``audio-separator``."""

import hashlib
import logging
import os
import subprocess
import time
from functools import partial
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from vocal_splitter.application.ports.vocal_separator import (
    CancellationToken,
    ProgressCallback,
)
from vocal_splitter.application.separation_errors import (
    SeparationCancelledError,
    SeparationEngineUnavailableError,
    SeparationFfmpegUnavailableError,
    SeparationModelDownloadError,
    SeparationModelIntegrityError,
    SeparationModelProfileError,
    SeparationOutputError,
)
from vocal_splitter.domain.model_usage import EngineUsage, ModelUsage
from vocal_splitter.domain.separation_job import SeparationStage
from vocal_splitter.domain.separation_result import SeparationResult
from vocal_splitter.domain.stem import Stem, StemKind
from vocal_splitter.infrastructure.audio.metadata_reader import MetadataReader
from vocal_splitter.infrastructure.audio.ffmpeg import ensure_ffmpeg_on_path, find_ffprobe
from vocal_splitter.infrastructure.separation.model_profile import (
    ModelProfile,
    ModelProfileError,
    load_reviewed_profiles,
    sha256_file,
)

logger = logging.getLogger(__name__)

_STAGE_ONE_PROFILE = "uvr-mdxnet-main-v1"
_STAGE_TWO_PROFILE = "uvr-mdxnet-kara-2-v1"
_DRUMS_PROFILE = "kuielab-mdxnet-drums-v1"
_BASS_PROFILE = "kuielab-mdxnet-bass-v1"
_MAX_MODEL_BYTES = 512 * 1024 * 1024
_DOWNLOAD_CHUNK_BYTES = 1024 * 1024
_DEFAULT_MDX_SEGMENT_SIZE = 256
_MDX_SEGMENT_SIZE_BY_PROFILE = {
    _DRUMS_PROFILE: 512,
    _BASS_PROFILE: 512,
}
_MDX_OVERLAP = 0.35


def disable_mdx_progress_output(mdx_module=None) -> None:
    """Disable tqdm's console bar, which can fail in a windowed Windows app."""
    if mdx_module is None:
        from audio_separator.separator.architectures import mdx_separator as mdx_module

    if not getattr(mdx_module.tqdm, "_vocal_splitter_quiet", False):
        quiet_tqdm = partial(mdx_module.tqdm, disable=True)
        quiet_tqdm._vocal_splitter_quiet = True
        mdx_module.tqdm = quiet_tqdm


class AudioSeparatorEngine:
    """Ejecuta y verifica las cuatro pasadas locales de separación."""

    def __init__(
        self,
        model_cache_dir: Path,
        *,
        metadata_reader: MetadataReader | None = None,
    ) -> None:
        self._model_cache_dir = model_cache_dir.expanduser()
        self._metadata_reader = metadata_reader or MetadataReader()
        try:
            self._profiles = load_reviewed_profiles()
        except ModelProfileError as error:
            raise SeparationModelProfileError(str(error)) from error

    def separate_voice_and_instrumental(
        self,
        source: Path,
        output_dir: Path,
        *,
        progress: ProgressCallback,
        cancellation: CancellationToken,
    ) -> SeparationResult:
        return self._separate(
            source,
            output_dir,
            profile_id=_STAGE_ONE_PROFILE,
            stage=SeparationStage.VOICE_AND_INSTRUMENTAL,
            outputs={
                "Vocals": ("separacion_voz_total", StemKind.VOCAL_MIX),
                "Instrumental": ("separacion_acompanamiento", StemKind.INSTRUMENTAL),
            },
            progress=progress,
            cancellation=cancellation,
        )

    def separate_lead_and_backing(
        self,
        vocal_stem: Stem,
        output_dir: Path,
        *,
        progress: ProgressCallback,
        cancellation: CancellationToken,
    ) -> SeparationResult:
        return self._separate(
            vocal_stem.path,
            output_dir,
            profile_id=_STAGE_TWO_PROFILE,
            stage=SeparationStage.LEAD_AND_BACKING,
            outputs={
                "Vocals": ("separacion_voz_principal", StemKind.LEAD_VOCAL),
                "Instrumental": ("separacion_residuo_vocal", StemKind.BACKING_VOCALS),
            },
            progress=progress,
            cancellation=cancellation,
        )

    def separate_drums_and_residual(
        self,
        instrumental_stem: Stem,
        output_dir: Path,
        *,
        progress: ProgressCallback,
        cancellation: CancellationToken,
    ) -> SeparationResult:
        return self._separate(
            instrumental_stem.path,
            output_dir,
            profile_id=_DRUMS_PROFILE,
            stage=SeparationStage.DRUMS_AND_REMAINDER,
            outputs={
                "Drums": ("bateria", StemKind.DRUMS),
                "No Drums": ("sin_bateria", StemKind.INSTRUMENTAL),
            },
            progress=progress,
            cancellation=cancellation,
        )

    def separate_bass_and_instrumental(
        self,
        instrumental_stem: Stem,
        output_dir: Path,
        *,
        progress: ProgressCallback,
        cancellation: CancellationToken,
    ) -> SeparationResult:
        return self._separate(
            instrumental_stem.path,
            output_dir,
            profile_id=_BASS_PROFILE,
            stage=SeparationStage.BASS_AND_INSTRUMENTAL,
            outputs={
                "Bass": ("bajo", StemKind.BASS),
                "No Bass": ("instrumental", StemKind.INSTRUMENTAL),
            },
            progress=progress,
            cancellation=cancellation,
        )

    def _separate(
        self,
        source: Path,
        output_dir: Path,
        *,
        profile_id: str,
        stage: SeparationStage,
        outputs: dict[str, tuple[str, StemKind]],
        progress: ProgressCallback,
        cancellation: CancellationToken,
    ) -> SeparationResult:
        cancellation.raise_if_cancelled()
        self._ensure_ffmpeg()
        try:
            from audio_separator.separator import Separator
        except ImportError as error:
            raise SeparationEngineUnavailableError() from error

        try:
            profile = self._profiles[profile_id]
        except KeyError as error:
            raise SeparationModelProfileError(
                f"No hay perfil revisado para {profile_id}"
            ) from error

        model_path = self._ensure_model(profile, progress, cancellation)
        cancellation.raise_if_cancelled()

        output_dir.mkdir(parents=True, exist_ok=True)
        output_names = {label: filename for label, (filename, _) in outputs.items()}
        progress(stage, 8, "Preparando el modelo de separación…")
        started_at = time.perf_counter()
        try:
            separator = Separator(
                output_dir=str(output_dir),
                model_file_dir=str(self._model_cache_dir),
                output_format="WAV",
                log_level=logging.WARNING,
                mdx_params={
                    "hop_length": 1024,
                    "segment_size": _MDX_SEGMENT_SIZE_BY_PROFILE.get(
                        profile_id, _DEFAULT_MDX_SEGMENT_SIZE
                    ),
                    "overlap": _MDX_OVERLAP,
                    "batch_size": 1,
                    "enable_denoise": False,
                },
            )
            separator.load_model(model_filename=profile.filename)
            disable_mdx_progress_output()
            cancellation.raise_if_cancelled()
            progress(stage, 12, "Separando audio localmente…")
            output_files = separator.separate(str(source), output_names)
        except SeparationCancelledError:
            raise
        except Exception as error:
            logger.exception("Local separation failed for profile %s", profile.profile_id)
            if "torchvision::nms" in str(error):
                message = (
                    "La instalación del motor de audio está incompleta: TorchVision no pudo "
                    "cargar su extensión nativa necesaria para procesar el modelo. "
                    "Instala una compilación actualizada de Separador Vocal."
                )
            else:
                message = (
                    f"Falló el modelo {profile.profile_id} "
                    f"({type(error).__name__}: {error}). Consulta el registro local y vuelve a intentarlo."
                )
            raise SeparationOutputError(message) from error

        cancellation.raise_if_cancelled()
        stems = self._map_outputs(output_files, output_dir, outputs)
        progress(stage, 92, "Validando pistas generadas…")
        try:
            validated_stems = tuple(self._read_stem(path, kind) for path, kind in stems)
        except Exception as error:
            logger.exception("Could not read a generated audio stem")
            raise SeparationOutputError() from error
        elapsed_seconds = time.perf_counter() - started_at
        parameters = (
            ("output_format", "WAV"),
            ("model_filename", profile.filename),
            ("outputs", ",".join(f"{label}:{filename}" for label, filename in output_names.items())),
            ("device", "auto (selección de audio-separator)"),
            (
                "mdx_segment_size",
                str(_MDX_SEGMENT_SIZE_BY_PROFILE.get(profile_id, _DEFAULT_MDX_SEGMENT_SIZE)),
            ),
            ("mdx_overlap", str(_MDX_OVERLAP)),
            ("mdx_batch_size", "1"),
        )
        return SeparationResult(
            validated_stems,
            self._engine_usage(profile, elapsed_seconds, parameters),
        )

    @staticmethod
    def _engine_usage(
        profile: ModelProfile,
        elapsed_seconds: float,
        parameters: tuple[tuple[str, str], ...],
    ) -> EngineUsage:
        try:
            engine_version = version("audio-separator")
        except PackageNotFoundError:
            engine_version = "desconocida"
        usage = ModelUsage(
            profile_id=profile.profile_id,
            filename=profile.filename,
            sha256=profile.sha256,
            license=profile.license,
            source_url=profile.download_url,
            attribution=profile.attribution,
            elapsed_seconds=round(elapsed_seconds, 3),
            parameters=parameters,
        )
        return EngineUsage("python-audio-separator", engine_version, (usage,))

    @staticmethod
    def _ensure_ffmpeg() -> str:
        executable = ensure_ffmpeg_on_path()
        probe = find_ffprobe()
        if executable is None or probe is None:
            raise SeparationFfmpegUnavailableError()
        for tool in (executable, probe):
            try:
                completed = subprocess.run(
                    [tool, "-version"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            except (OSError, subprocess.SubprocessError) as error:
                raise SeparationFfmpegUnavailableError(
                    f"Windows no pudo ejecutar el componente de audio {tool}: "
                    f"{error}. Reinstala la aplicación desde su instalador completo."
                ) from error
            if completed.returncode != 0:
                detail = completed.stderr.strip() or completed.stdout.strip()
                raise SeparationFfmpegUnavailableError(
                    f"El componente de audio {tool} no inició correctamente. {detail}".strip()
                )
        return executable

    def _ensure_model(
        self,
        profile: ModelProfile,
        progress: ProgressCallback,
        cancellation: CancellationToken,
    ) -> Path:
        self._model_cache_dir.mkdir(parents=True, exist_ok=True)
        target_path = self._model_cache_dir / profile.filename
        if target_path.exists():
            if sha256_file(target_path) != profile.sha256:
                raise SeparationModelIntegrityError(
                    f"La suma del modelo en caché no coincide: {profile.profile_id}"
                )
            return target_path

        partial_path = target_path.with_name(f"{target_path.name}.part")
        digest = hashlib.sha256()
        received = 0
        request = Request(
            profile.download_url,
            headers={"User-Agent": "SeparadorVocal/0.1 model-fetch"},
        )
        try:
            with urlopen(request, timeout=30) as response:
                if not response.geturl().startswith("https://"):
                    raise SeparationModelDownloadError(
                        "La URL redirigió fuera de HTTPS"
                    )
                content_length = response.headers.get("Content-Length")
                expected_length = int(content_length) if content_length else None
                if expected_length is not None and expected_length > _MAX_MODEL_BYTES:
                    raise SeparationModelDownloadError("El modelo supera el límite permitido")
                with partial_path.open("wb") as partial_file:
                    while True:
                        cancellation.raise_if_cancelled()
                        chunk = response.read(_DOWNLOAD_CHUNK_BYTES)
                        if not chunk:
                            break
                        received += len(chunk)
                        if received > _MAX_MODEL_BYTES:
                            raise SeparationModelDownloadError(
                                "El modelo supera el límite permitido"
                            )
                        digest.update(chunk)
                        partial_file.write(chunk)
                        if expected_length:
                            percent = min(7, 1 + (received * 6 // expected_length))
                            progress(
                                SeparationStage.PREPARING,
                                percent,
                                f"Descargando modelo ({received // (1024 * 1024)} MB)…",
                            )
                    partial_file.flush()
                    os.fsync(partial_file.fileno())
            if expected_length is not None and received != expected_length:
                raise SeparationModelDownloadError("La descarga del modelo quedó incompleta")
            if digest.hexdigest() != profile.sha256:
                raise SeparationModelIntegrityError(
                    f"El archivo descargado no coincide con SHA-256 de {profile.profile_id}"
                )
            os.replace(partial_path, target_path)
        except SeparationCancelledError:
            self._remove_partial(partial_path)
            raise
        except SeparationModelIntegrityError:
            self._remove_partial(partial_path)
            raise
        except SeparationModelDownloadError:
            self._remove_partial(partial_path)
            raise
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
            self._remove_partial(partial_path)
            logger.warning("Could not download model %s", profile.profile_id, exc_info=True)
            raise SeparationModelDownloadError() from error
        except Exception:
            self._remove_partial(partial_path)
            raise
        progress(SeparationStage.PREPARING, 8, "Modelo verificado")
        return target_path

    @staticmethod
    def _remove_partial(path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Could not remove partial model file %s", path, exc_info=True)

    @staticmethod
    def _map_outputs(
        output_files: list[str],
        output_dir: Path,
        expected: dict[str, tuple[str, StemKind]],
    ) -> list[tuple[Path, StemKind]]:
        expected_paths = {
            f"{filename}.wav": (filename, kind)
            for filename, kind in expected.values()
        }
        mapped: dict[StemKind, Path] = {}
        root = output_dir.resolve()
        for raw_path in output_files:
            candidate = Path(raw_path)
            if not candidate.is_absolute():
                candidate = output_dir / candidate
            resolved = candidate.resolve()
            if root not in resolved.parents:
                raise SeparationOutputError("El motor devolvió una ruta fuera de la sesión")
            match = expected_paths.get(resolved.name)
            if match is None:
                raise SeparationOutputError(
                    f"Salida de motor no reconocida: {resolved.name}"
                )
            _, kind = match
            if kind in mapped:
                raise SeparationOutputError(f"El motor duplicó la salida {kind.value}")
            if not resolved.is_file() or resolved.stat().st_size == 0:
                raise SeparationOutputError(f"La salida {resolved.name} está vacía")
            mapped[kind] = resolved

        if set(mapped) != {kind for _, kind in expected.values()}:
            raise SeparationOutputError("Falta una o más salidas del motor")
        return [(path, kind) for kind, path in mapped.items()]

    def _read_stem(self, path: Path, kind: StemKind) -> Stem:
        asset = self._metadata_reader.read(path)
        return Stem(
            kind=kind,
            path=asset.source_path,
            duration_seconds=asset.duration_seconds,
            sample_rate_hz=asset.sample_rate_hz,
            channels=asset.channels,
        )
