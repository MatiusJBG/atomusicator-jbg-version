"""Persistencia de preferencias con QSettings."""

from pathlib import Path

from PySide6.QtCore import QSettings

from vocal_splitter.application.project_settings import ProjectSettings


class SettingsStore:
    def __init__(self) -> None:
        self._settings = QSettings()

    def load(self) -> ProjectSettings:
        default = ProjectSettings.default()
        value = self._settings.value("projects/directory", str(default.projects_directory))
        return ProjectSettings(projects_directory=Path(str(value)).expanduser())

    def save(self, settings: ProjectSettings) -> None:
        self._settings.setValue("projects/directory", str(settings.projects_directory))
        self._settings.sync()
