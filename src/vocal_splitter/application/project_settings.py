"""Preferencias de ubicación de proyectos."""

from dataclasses import dataclass
import ctypes
import os
from pathlib import Path
import tempfile


@dataclass(frozen=True, slots=True)
class ProjectSettings:
    projects_directory: Path

    @classmethod
    def default(cls) -> "ProjectSettings":
        if os.name == "nt":
            local_app_data = Path(
                os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")
            )
        else:
            local_app_data = Path(
                os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")
            )
        projects_directory = (
            local_app_data / "Separador Vocal" / "Separador Vocal" / "projects"
        )
        return cls(projects_directory=projects_directory)

    def validate_writable_local_directory(self) -> None:
        target = self.projects_directory.expanduser()
        if (
            not target.anchor
            or os.path.normcase(str(target)) == os.path.normcase(target.anchor)
        ):
            raise ValueError("Elige una subcarpeta, no la raíz de una unidad.")

        if os.name == "nt":
            if target.anchor.startswith("\\\\"):
                raise ValueError("La carpeta de proyectos debe estar en una unidad local.")
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(target.anchor)
            if drive_type not in (2, 3):
                raise ValueError(
                    "La carpeta de proyectos debe estar en un disco local o extraíble."
                )

        target.mkdir(parents=True, exist_ok=True)
        descriptor, probe_name = tempfile.mkstemp(
            prefix=".separador-write-check-",
            dir=target,
        )
        try:
            with os.fdopen(descriptor, "wb") as probe:
                probe.write(b"local storage check")
                probe.flush()
                os.fsync(probe.fileno())
        finally:
            Path(probe_name).unlink(missing_ok=True)
