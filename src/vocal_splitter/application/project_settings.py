"""Preferencias de ubicación de proyectos."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ProjectSettings:
    projects_directory: Path

    @classmethod
    def default(cls) -> "ProjectSettings":
        documents = Path.home() / "Documents"
        return cls(projects_directory=documents / "Separador Vocal")
