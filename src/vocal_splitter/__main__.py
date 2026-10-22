"""Arranque de la aplicación de escritorio."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QApplication

from vocal_splitter.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Separador Vocal")
    app.setOrganizationName("Separador Vocal")
    _configure_logging()
    window = MainWindow()
    window.show()
    return app.exec()


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
