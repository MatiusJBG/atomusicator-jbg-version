"""Persistencia de preferencias con QSettings."""

import logging
from pathlib import Path

from PySide6.QtCore import QSettings

from vocal_splitter.application.project_settings import ProjectSettings

logger = logging.getLogger(__name__)


class SettingsStore:
    def __init__(self) -> None:
        self._settings = QSettings()

    def load(self) -> ProjectSettings:
        default = ProjectSettings.default()
        value = self._settings.value("projects/directory", str(default.projects_directory))
        settings = ProjectSettings(projects_directory=Path(str(value)).expanduser())
        try:
            settings.validate_writable_local_directory()
        except (OSError, ValueError) as error:
            logger.warning(
                "Stored project directory %s is unavailable; using local default %s: %s",
                settings.projects_directory,
                default.projects_directory,
                error,
            )
            default.validate_writable_local_directory()
            self.save(default)
            return default
        return settings

    def save(self, settings: ProjectSettings) -> None:
        self._settings.setValue("projects/directory", str(settings.projects_directory))
        self._settings.sync()
