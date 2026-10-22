"""Arranque de la aplicación de escritorio."""

import logging
import sys
import tempfile
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QStandardPaths, QTimer
from PySide6.QtWidgets import QApplication

from vocal_splitter.application.project_settings import ProjectSettings
from vocal_splitter.domain.stem import StemKind
from vocal_splitter.infrastructure.separation.audio_separator_engine import (
    AudioSeparatorEngine,
)
from vocal_splitter.infrastructure.separation.model_profile import load_reviewed_profiles
from vocal_splitter.ui.main_window import MainWindow


class _DiagnosticCancellation:
    def raise_if_cancelled(self) -> None:
        return None


def main() -> int:
    if "--diagnostics-separation" in sys.argv[1:]:
        return _run_separation_diagnostics()
    if "--diagnostics" in sys.argv[1:]:
        return _run_diagnostics()
    if "--diagnostics-ui" in sys.argv[1:]:
        return _run_gui_diagnostics()

    app = QApplication(sys.argv)
    app.setApplicationName("Separador Vocal")
    app.setOrganizationName("Separador Vocal")
    _configure_logging()
    logging.getLogger(__name__).info("Separador Vocal desktop application started")
    window = MainWindow()
    window.show()
    return app.exec()


def _run_diagnostics() -> int:
    app = QCoreApplication([sys.argv[0]])
    app.setApplicationName("Separador Vocal")
    app.setOrganizationName("Separador Vocal")
    _configure_logging()

    project_settings = ProjectSettings.default()
    projects_directory = project_settings.projects_directory
    try:
        project_settings.validate_writable_local_directory()
        ffmpeg_path = AudioSeparatorEngine._ensure_ffmpeg()
        inference_runtime = validate_torchvision_runtime()
    except Exception:
        logging.getLogger(__name__).exception("Desktop self-check failed")
        return 1

    logging.getLogger(__name__).info(
        "Desktop self-check passed; ffmpeg=%s; inference=%s; projects=%s",
        ffmpeg_path,
        inference_runtime,
        projects_directory,
    )
    return 0


def _run_gui_diagnostics() -> int:
    app = QApplication([sys.argv[0]])
    app.setApplicationName("Separador Vocal")
    app.setOrganizationName("Separador Vocal")
    _configure_logging()
    window = MainWindow()
    window.show()

    def finish_smoke_test() -> None:
        logging.getLogger(__name__).info(
            "GUI self-test passed; window_created=true; window_shown=true"
        )
        window.close()
        app.quit()

    QTimer.singleShot(1500, finish_smoke_test)
    return app.exec()


def _run_separation_diagnostics() -> int:
    import numpy as np
    import soundfile as sf

    app = QCoreApplication([sys.argv[0]])
    app.setApplicationName("Separador Vocal")
    app.setOrganizationName("Separador Vocal")
    _configure_logging()
    logger = logging.getLogger(__name__)
    project_directory = ProjectSettings.default().projects_directory
    model_directory = (
        Path(QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppLocalDataLocation
        ))
        / "models"
    )
    try:
        ProjectSettings.default().validate_writable_local_directory()
        profiles = load_reviewed_profiles()
        missing = [
            profile.filename
            for profile in profiles.values()
            if not (model_directory / profile.filename).is_file()
        ]
        if missing:
            raise FileNotFoundError(
                "Faltan modelos en la caché local; primero ejecuta una separación normal: "
                + ", ".join(missing)
            )

        cancellation = _DiagnosticCancellation()
        engine = AudioSeparatorEngine(model_directory)
        with tempfile.TemporaryDirectory(
            prefix="separacion-diagnostics-",
            dir=project_directory,
        ) as temporary:
            root = Path(temporary)
            sample_rate = 44100
            time = np.arange(sample_rate * 8, dtype=np.float32) / sample_rate
            voice = (
                0.24 * np.sin(2 * np.pi * 220 * time)
                + 0.08 * np.sin(2 * np.pi * 440 * time)
            )
            instruments = (
                0.16 * np.sin(2 * np.pi * 110 * time)
                + 0.08 * np.sin(2 * np.pi * 330 * time)
            )
            mixture = np.column_stack((voice + instruments, voice + instruments))
            source = root / "diagnostic-mix.wav"
            sf.write(source, mixture, sample_rate, subtype="PCM_16")

            first = engine.separate_voice_and_instrumental(
                source,
                root / "stage-one",
                progress=lambda *_: None,
                cancellation=cancellation,
            )
            expected_first = {StemKind.VOCAL_MIX, StemKind.INSTRUMENTAL}
            if {stem.kind for stem in first.stems} != expected_first:
                raise RuntimeError("La etapa 1 no produjo voz total y acompañamiento.")

            vocal_mix = first.stem(StemKind.VOCAL_MIX)
            second = engine.separate_lead_and_backing(
                vocal_mix,
                root / "stage-two",
                progress=lambda *_: None,
                cancellation=cancellation,
            )
            instrumental = first.stem(StemKind.INSTRUMENTAL)
            result_stems = (instrumental, *second.stems)
            expected = {
                StemKind.LEAD_VOCAL,
                StemKind.BACKING_VOCALS,
                StemKind.INSTRUMENTAL,
            }
            if {stem.kind for stem in result_stems} != expected:
                raise RuntimeError("La etapa 2 no produjo voz principal, coros e instrumental.")
            expected_duration = sf.info(source).duration
            for stem in result_stems:
                info = sf.info(stem.path)
                if info.frames == 0 or info.samplerate <= 0 or info.channels <= 0:
                    raise RuntimeError(f"El stem {stem.kind.value} está vacío o no es legible.")
                if abs(info.duration - expected_duration) > 0.1:
                    raise RuntimeError(
                        f"El stem {stem.kind.value} dura {info.duration:.3f} s y la fuente "
                        f"{expected_duration:.3f} s; se detectó truncamiento."
                    )
                logger.info(
                    "Separation self-test stem passed; kind=%s; duration=%.3f; frames=%s; sample_rate=%s; channels=%s",
                    stem.kind.value,
                    info.duration,
                    info.frames,
                    info.samplerate,
                    info.channels,
                )

        logger.info("Separation self-test passed; stems=3; stages=2")
        return 0
    except Exception:
        logger.exception("Separation self-test failed")
        return 1


def validate_torchvision_runtime() -> str:
    """Load and execute a native TorchVision op required by the frozen inference stack."""
    try:
        import torch
        from torchvision.ops import nms

        boxes = torch.tensor(
            [[0.0, 0.0, 1.0, 1.0], [0.1, 0.1, 0.9, 0.9]],
            dtype=torch.float32,
        )
        scores = torch.tensor([0.9, 0.8], dtype=torch.float32)
        selected = nms(boxes, scores, 0.5)
        if selected.tolist() != [0]:
            raise RuntimeError(f"resultado inesperado de NMS: {selected.tolist()}")
    except Exception as error:
        raise RuntimeError(
            "Las extensiones nativas de TorchVision no se cargaron correctamente. "
            "Recompila/reinstala la aplicación con los componentes de inferencia completos. "
            f"Detalle: {type(error).__name__}: {error}"
        ) from error

    return f"torch={torch.__version__}; torchvision={torchvision_version()}; nms=ok"


def torchvision_version() -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("torchvision")
    except PackageNotFoundError:
        return "desconocida"


def _configure_logging() -> None:
    """Guarda diagnósticos locales para poder identificar errores de escritura."""
    app_data = Path(
        QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppLocalDataLocation
        )
    )
    try:
        log_directory = app_data / "logs"
        log_directory.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            log_directory / "separador-vocal.log",
            maxBytes=2 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)
    except OSError:
        # La app debe arrancar incluso si el usuario no tiene una carpeta de logs disponible.
        logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    raise SystemExit(main())
