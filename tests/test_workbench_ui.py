import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf
from PySide6.QtWidgets import QApplication

from vocal_splitter.domain.separation_result import SeparationResult
from vocal_splitter.domain.stem import Stem, StemKind
from vocal_splitter.ui.audio_workbench import AudioWorkbench


class WorkbenchUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        stems = []
        for kind in (StemKind.LEAD_VOCAL, StemKind.BACKING_VOCALS,
                     StemKind.DRUMS, StemKind.BASS, StemKind.INSTRUMENTAL):
            path = Path(self.temporary.name) / f"{kind}.wav"
            sf.write(path, np.full((800, 2), 0.1), 8000)
            stems.append(Stem(kind, path, 0.1, 8000, 2))
        self.workbench = AudioWorkbench(SeparationResult(tuple(stems)))

    def tearDown(self):
        self.workbench.dispose()
        self.workbench.deleteLater()
        self.app.processEvents()
        self.temporary.cleanup()

    def test_controls_change_real_mixer_and_seek_all_tracks(self):
        self.assertEqual(len(self.workbench._rows), 5)
        _, gain, mute, solo, _ = self.workbench._rows[2]
        gain.setValue(60)
        mute.click()
        solo.click()
        track = self.workbench._mixer.tracks[2]
        self.assertAlmostEqual(track.gain, 0.6)
        self.assertTrue(track.muted)
        self.assertTrue(track.solo)
        self.workbench._seek(0.5)
        self.assertEqual(self.workbench._mixer.position, 400)
        self.assertTrue(all(row[0]._playhead == 0.5 for row in self.workbench._rows))

    def test_pitch_emits_selected_semitones_without_rendering_in_ui(self):
        requested = []
        self.workbench.pitch_requested.connect(requested.append)
        self.workbench.pitch.setValue(-3)
        self.workbench.apply_pitch_button.click()
        self.assertEqual(requested, [-3])
