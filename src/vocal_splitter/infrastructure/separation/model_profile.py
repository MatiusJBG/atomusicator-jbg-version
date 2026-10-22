"""Perfiles integrados y revisión de procedencia/licencia de los pesos."""

import hashlib
import json
import re
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path


class ModelProfileError(Exception):
    """Un perfil no está aprobado o su manifiesto no es válido."""


@dataclass(frozen=True, slots=True)
class ModelProfile:
    profile_id: str
    stage: str
    filename: str
    sha256: str
    download_url: str
    license: str
    attribution: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-f0-9]{64}", self.sha256):
            raise ModelProfileError(f"SHA-256 no válido para {self.profile_id}")
        if not self.download_url.startswith("https://"):
            raise ModelProfileError("La descarga del modelo debe usar HTTPS")
        if Path(self.filename).name != self.filename:
            raise ModelProfileError("El nombre de modelo no puede incluir una ruta")


def load_reviewed_profiles(manifest_path: Path | None = None) -> dict[str, ModelProfile]:
    path = manifest_path or Path(
        str(files("vocal_splitter.infrastructure.separation").joinpath(
            "model_license_manifest.json"
        ))
    )
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ModelProfileError("No se pudo leer el manifiesto de modelos") from error

    models = manifest.get("models")
    if not isinstance(models, list):
        raise ModelProfileError("El manifiesto no contiene una lista de modelos")

    profiles: dict[str, ModelProfile] = {}
    for entry in models:
        if entry.get("license_status") != "reviewed":
            continue
        profile = ModelProfile(
            profile_id=str(entry["profile_id"]),
            stage=str(entry["stage"]),
            filename=str(entry["filename"]),
            sha256=str(entry["sha256"]).lower(),
            download_url=str(entry["download_url"]),
            license=str(entry["license"]),
            attribution=str(entry["attribution"]),
        )
        if profile.profile_id in profiles:
            raise ModelProfileError(f"Perfil duplicado: {profile.profile_id}")
        profiles[profile.profile_id] = profile
    return profiles


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as model_file:
        for chunk in iter(lambda: model_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
