import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import soundfile as sf

from vocal_splitter.domain.stem import Stem, StemKind
from vocal_splitter.domain.separation_result import SeparationResult
from vocal_splitter.ui.pitch_worker import PitchWorker


class PitchProgressTests(unittest.TestCase):
    def test_progress_counts_completed_stems_and_preserves_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.wav"
            sf.write(source, np.zeros((800, 2)), 8000)
            original = source.read_bytes()
            result = SeparationResult(tuple(Stem(k, source, .1, 8000, 2) for k in
                                            (StemKind.LEAD_VOCAL, StemKind.DRUMS)))
            from vocal_splitter.infrastructure.audio.pitch_processor import PitchProcessor
            worker = PitchWorker(result, root / "renders", 0, preserve_formants=True)
            progress, outputs, failures = [], [], []
            worker.progress.connect(progress.append)
            worker.finished.connect(outputs.append)
            worker.failed.connect(failures.append)
            worker.run()
            self.assertEqual(failures, [])
            self.assertEqual(progress, [0, 50, 100])
            self.assertEqual(len(outputs[0].stems), 2)
            self.assertEqual(source.read_bytes(), original)
            self.assertTrue(all(s.path.is_file() for s in outputs[0].stems))
