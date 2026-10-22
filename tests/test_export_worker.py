import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from vocal_splitter.domain.separation_result import SeparationResult
from vocal_splitter.domain.stem import Stem, StemKind
from vocal_splitter.ui.export_worker import ExportWorker


class ExportWorkerTests(unittest.TestCase):
    def test_export_options_validate_and_convert_selected_stem(self):
        from vocal_splitter.application.export_options import ExportOptions
        from vocal_splitter.infrastructure.audio.ffmpeg import find_ffmpeg
        if not find_ffmpeg():
            self.skipTest("FFmpeg is required for conversion integration")
        with self.assertRaises(ValueError):
            ExportOptions(format="exe")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "original.wav"
            sf.write(source, np.full((8000, 2), 0.1), 8000)
            stem = Stem(StemKind.DRUMS, source, 1.0, 8000, 2)
            worker = ExportWorker(SeparationResult((stem,)), root,
                                  ExportOptions(format="flac", sample_rate=44100,
                                                bit_depth=24, channels=1))
            exported, failed = [], []
            worker.exported.connect(exported.append)
            worker.failed.connect(failed.append)
            worker.run()
            self.assertEqual(failed, [])
            info = sf.info(Path(exported[0]) / "bateria.flac")
            self.assertEqual((info.samplerate, info.channels, info.subtype), (44100, 1, "PCM_24"))
            self.assertAlmostEqual(info.duration, 1.0, places=2)
            for format in ("wav", "mp3"):
                with self.subTest(format=format):
                    converted = ExportWorker(SeparationResult((stem,)), root,
                                             ExportOptions(format=format, bit_depth=16,
                                                           normalize=True))
                    paths, errors = [], []
                    converted.exported.connect(paths.append)
                    converted.failed.connect(errors.append)
                    converted.run()
                    self.assertEqual(errors, [])
                    audio, rate = sf.read(Path(paths[0]) / f"bateria.{format}")
                    self.assertEqual(rate, 48000)
                    self.assertEqual(audio.shape[1], 2)
                    self.assertGreater(len(audio), 47000)
                    self.assertLessEqual(np.max(np.abs(audio)), 1.0)

    def test_failed_export_cleans_partial_directory_and_emits_done(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            missing = Stem(StemKind.BASS, root / "missing.wav", 1, 8000, 2)
            worker = ExportWorker(SeparationResult((missing,)), root)
            errors, done = [], []
            worker.failed.connect(errors.append)
            worker.done.connect(lambda: done.append(True))
            worker.run()
            self.assertEqual(len(errors), 1)
            self.assertEqual(done, [True])
            self.assertEqual(list(root.iterdir()), [])

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
