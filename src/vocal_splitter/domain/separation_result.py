"""Resultados parciales o completos de las etapas de separación."""

from dataclasses import dataclass

from vocal_splitter.domain.model_usage import EngineUsage
from vocal_splitter.domain.stem import Stem, StemKind


@dataclass(frozen=True, slots=True)
class SeparationResult:
    stems: tuple[Stem, ...]
    engine_usage: EngineUsage | None = None

    def __post_init__(self) -> None:
        if not self.stems:
            raise ValueError("El resultado debe contener al menos un stem")
        kinds = [stem.kind for stem in self.stems]
        if len(kinds) != len(set(kinds)):
            raise ValueError("No se permiten stems duplicados del mismo tipo")
        if len(self.stems) > 1:
            reference = self.stems[0]
            tolerance = 1 / max(stem.sample_rate_hz for stem in self.stems)
            for stem in self.stems[1:]:
                if abs(stem.start_offset_seconds - reference.start_offset_seconds) > tolerance:
                    raise ValueError("Los stems deben comenzar alineados")
                if abs(stem.duration_seconds - reference.duration_seconds) > tolerance:
                    raise ValueError("Los stems deben tener duraciones compatibles")

    @property
    def is_final(self) -> bool:
        return {
            StemKind.LEAD_VOCAL,
            StemKind.BACKING_VOCALS,
            StemKind.DRUMS,
            StemKind.BASS,
            StemKind.INSTRUMENTAL,
        } == {stem.kind for stem in self.stems}

    def stem(self, kind: StemKind) -> Stem:
        for item in self.stems:
            if item.kind is kind:
                return item
        raise KeyError(kind)

    def combine(self, other: "SeparationResult") -> "SeparationResult":
        combined = (*self.stems, *other.stems)
        usages = []
        for result in (self, other):
            if result.engine_usage is not None:
                usages.extend(result.engine_usage.models)
        engine_usage = None
        if usages:
            unique = {usage.profile_id: usage for usage in usages}
            engine_usage = EngineUsage(
                name=(self.engine_usage or other.engine_usage).name,
                version=(self.engine_usage or other.engine_usage).version,
                models=tuple(unique.values()),
            )
        return SeparationResult(tuple(combined), engine_usage)
