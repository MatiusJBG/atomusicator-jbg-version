"""Arranque de la aplicación de escritorio."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QStandardPaths
from PySide6.QtWidgets import QApplication

from vocal_splitter.application.project_settings import ProjectSettings
from vocal_splitter.infrastructure.separation.audio_separator_engine import (
    AudioSeparatorEngine,
)
from vocal_splitter.ui.main_window import MainWindow


def main() -> int:
    if "--diagnostics" in sys.argv[1:]:
        return _run_diagnostics()

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
    except Exception:
        logging.getLogger(__name__).exception("Desktop self-check failed")
        return 1

    logging.getLogger(__name__).info(
        "Desktop self-check passed; ffmpeg=%s; projects=%s",
        ffmpeg_path,
        projects_directory,
    )
    return 0


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
