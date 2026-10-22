import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from vocal_splitter.domain.separation_result import SeparationResult
from vocal_splitter.domain.stem import Stem, StemKind
from vocal_splitter.ui.export_worker import ExportWorker


class ExportWorkerTests(unittest.TestCase):
    def test_all_five_stems_are_exported_without_modifying_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            stems = []
            for kind in (StemKind.LEAD_VOCAL, StemKind.BACKING_VOCALS,
                         StemKind.DRUMS, StemKind.BASS, StemKind.INSTRUMENTAL):
                path = root / f"{kind}.wav"
                sf.write(path, np.full((800, 2), 0.1), 8000)
                stems.append(Stem(kind, path, 0.1, 8000, 2))
            originals = [s.path.read_bytes() for s in stems]
            worker = ExportWorker(SeparationResult(tuple(stems)), root)
            exported, failed = [], []
            worker.exported.connect(exported.append)
            worker.failed.connect(failed.append)
            worker.run()
            self.assertEqual(failed, [])
            self.assertEqual(len(exported), 1)
            self.assertEqual(len(list(Path(exported[0]).glob('*.wav'))), 5)
            self.assertEqual(originals, [s.path.read_bytes() for s in stems])
