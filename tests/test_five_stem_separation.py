import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from vocal_splitter.application.separate_vocals import SeparateVocals
from vocal_splitter.application.separation_errors import PartialSeparationError
from vocal_splitter.domain.audio_asset import AudioAsset
from vocal_splitter.domain.audio_session import AudioSession
from vocal_splitter.domain.separation_job import SeparationStage
from vocal_splitter.domain.separation_result import SeparationResult
from vocal_splitter.domain.stem import Stem, StemKind
from vocal_splitter.infrastructure.projects.session_store import SessionStore


class FakeFiveStemSeparator:
    def __init__(self, sample_rate: int = 8000) -> None:
        self.sample_rate = sample_rate
        self.calls: list[str] = []

    def _stems(self, output_dir: Path, specs) -> SeparationResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        stems = []
        audio = np.zeros((800, 2), dtype=np.float32)
        for filename, kind in specs:
            path = output_dir / filename
            sf.write(path, audio, self.sample_rate)
            stems.append(Stem(kind, path, 0.1, self.sample_rate, 2))
        return SeparationResult(tuple(stems))

    def separate_voice_and_instrumental(self, _source, output_dir, **_kwargs):
        self.calls.append("voice_and_instrumental")
        return self._stems(output_dir, [("voice.wav", StemKind.VOCAL_MIX), ("accompaniment.wav", StemKind.INSTRUMENTAL)])

    def separate_lead_and_backing(self, _vocal, output_dir, **_kwargs):
        self.calls.append("lead_and_backing")
        return self._stems(output_dir, [("lead.wav", StemKind.LEAD_VOCAL), ("backing.wav", StemKind.BACKING_VOCALS)])

    def separate_drums_and_residual(self, _instrumental, output_dir, **_kwargs):
        self.calls.append("drums")
        return self._stems(output_dir, [("drums.wav", StemKind.DRUMS), ("no_drums.wav", StemKind.INSTRUMENTAL)])

    def separate_bass_and_instrumental(self, _instrumental, output_dir, **_kwargs):
        self.calls.append("bass")
        return self._stems(output_dir, [("bass.wav", StemKind.BASS), ("instrumental.wav", StemKind.INSTRUMENTAL)])


class FakeDrumFailureSeparator(FakeFiveStemSeparator):
    def separate_drums_and_residual(self, _instrumental, _output_dir, **_kwargs):
        raise RuntimeError("fallo simulado en la separación de batería")


class NotCancelled:
    def is_cancelled(self):
        return False

    def raise_if_cancelled(self):
        return None


class FiveStemSeparationTests(unittest.TestCase):
    @staticmethod
    def _create_session(root: Path) -> AudioSession:
        source = root / "source.wav"
        sf.write(source, np.zeros((800, 2), dtype=np.float32), 8000)
        return SessionStore().create(
            AudioAsset(source, 0.1, 8000, 2, source.stat().st_size), root / "projects"
        )

    def test_separation_publishes_exactly_five_named_stems(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = self._create_session(root)
            separator = FakeFiveStemSeparator()
            stages = []
            result = SeparateVocals(separator).execute(
                session,
                progress=lambda stage, _percent, _message: stages.append(stage),
                cancellation=NotCancelled(),
            )

            self.assertEqual(
                {stem.kind for stem in result.stems},
                {StemKind.LEAD_VOCAL, StemKind.BACKING_VOCALS, StemKind.DRUMS, StemKind.BASS, StemKind.INSTRUMENTAL},
            )
            self.assertEqual(len(result.stems), 5)
            self.assertEqual(separator.calls, ["voice_and_instrumental", "lead_and_backing", "drums", "bass"])
            self.assertEqual(
                {stem.path.name for stem in result.stems},
                {"voz_principal.wav", "coros.wav", "bateria.wav", "bajo.wav", "instrumental.wav"},
            )
            self.assertTrue(result.is_final)
            record = json.loads((session.directory / "session.json").read_text(encoding="utf-8"))["separation"]
            self.assertEqual(record["status"], "complete")
            self.assertEqual(len(record["stems"]), 5)
            self.assertIn(SeparationStage.FINALIZING, stages)

    def test_instrument_failure_preserves_completed_vocal_stems_as_partial(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = self._create_session(root)
            with self.assertRaises(PartialSeparationError) as raised:
                SeparateVocals(FakeDrumFailureSeparator()).execute(
                    session,
                    progress=lambda *_: None,
                    cancellation=NotCancelled(),
                )

            partial = raised.exception.partial_result
            self.assertEqual(
                {stem.kind for stem in partial.stems},
                {StemKind.LEAD_VOCAL, StemKind.BACKING_VOCALS, StemKind.INSTRUMENTAL},
            )
            self.assertTrue(all(stem.path.is_file() for stem in partial.stems))
            record = json.loads((session.directory / "session.json").read_text(encoding="utf-8"))["separation"]
            self.assertEqual(record["status"], "partial")


if __name__ == "__main__":
    unittest.main()
