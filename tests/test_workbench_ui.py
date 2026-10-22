import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import numpy as np
import soundfile as sf
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase, QCloseEvent

from vocal_splitter.domain.separation_result import SeparationResult
from vocal_splitter.domain.stem import Stem, StemKind
from vocal_splitter.ui.audio_workbench import AudioWorkbench


class WorkbenchUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        for font in ("segoeui.ttf", "segoeuib.ttf", "consola.ttf"):
            path = Path("C:/Windows/Fonts") / font
            if path.is_file():
                QFontDatabase.addApplicationFont(str(path))

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

    def test_rendered_audio_preserves_mix_controls_and_position(self):
        row = self.workbench.track_rows[1]
        row.gain.setValue(35)
        row.pan.setValue(-40)
        row.mute.setChecked(True)
        self.workbench.master_gain.setValue(75)
        self.workbench._seek(.6)
        self.workbench.set_result(self.workbench.result)
        track = self.workbench._mixer.tracks[1]
        self.assertEqual((track.gain, track.pan, track.muted), (.35, -.4, True))
        self.assertEqual(self.workbench._mixer.position, 480)
        self.assertEqual(self.workbench._mixer.master_gain, .75)

    def test_export_dialog_requires_selection_and_returns_actual_settings(self):
        from vocal_splitter.ui.export_dialog import ExportDialog
        dialog = ExportDialog(self.workbench.result, self.workbench)
        for _, check in dialog.selected:
            check.setChecked(False)
        self.assertFalse(dialog.export.isEnabled())
        stem, check = dialog.selected[2]
        check.setChecked(True)
        dialog.formats.button(2).click()
        dialog.channels.setCurrentIndex(1)
        self.assertTrue(dialog.export.isEnabled())
        self.assertEqual(dialog.selected_result().stems, (stem,))
        self.assertEqual(dialog.options().format, "mp3")
        self.assertEqual(dialog.options().channels, 1)
        self.assertFalse(dialog.depth.isEnabled())

    def test_busy_pitch_blocks_audio_and_export_and_releases_controls(self):
        self.workbench.set_pitch_busy(True)
        self.workbench.set_pitch_progress(40)
        self.assertFalse(self.workbench.export_button.isEnabled())
        self.assertFalse(self.workbench.play_button.isEnabled())
        self.assertFalse(self.workbench.pitch_slider.isEnabled())
        self.assertEqual(self.workbench.pitch_progress.value(), 40)
        self.workbench.set_pitch_busy(False)
        self.assertTrue(self.workbench.play_button.isEnabled())
        self.assertTrue(self.workbench.export_button.isEnabled())

