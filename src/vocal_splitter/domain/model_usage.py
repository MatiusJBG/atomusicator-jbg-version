"""Procedencia de un peso empleado durante una separación."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelUsage:
    profile_id: str
    filename: str
    sha256: str
    license: str
    source_url: str
    attribution: str
    elapsed_seconds: float | None = None
    parameters: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class EngineUsage:
    name: str
    version: str
    models: tuple[ModelUsage, ...]
