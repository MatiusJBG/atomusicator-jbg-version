import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import soundfile as sf
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint
from PySide6.QtGui import QCloseEvent, QFontDatabase
from vocal_splitter.domain.separation_result import SeparationResult
from vocal_splitter.domain.stem import Stem, StemKind


class MainWindowUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        for font in ("segoeui.ttf", "segoeuib.ttf", "consola.ttf"):
            path = Path("C:/Windows/Fonts") / font
            if path.is_file():
                QFontDatabase.addApplicationFont(str(path))

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        source = Path(self.temporary.name) / "test.wav"
        sf.write(source, np.zeros((800, 2)), 8000)
        self.result = SeparationResult(tuple(
            Stem(k, source, .1, 8000, 2) for k in
            (StemKind.LEAD_VOCAL, StemKind.BACKING_VOCALS,
             StemKind.DRUMS, StemKind.BASS, StemKind.INSTRUMENTAL)))

    def tearDown(self):
        self.app.processEvents()
        self.temporary.cleanup()

    def test_main_window_navigation_and_active_import_close_guard(self):
        from vocal_splitter.application.project_settings import ProjectSettings
        from vocal_splitter.ui.main_window import MainWindow
        with patch("vocal_splitter.ui.main_window.SettingsStore.load",
                   return_value=ProjectSettings(Path(self.temporary.name))):
            window = MainWindow()
        window.show()
        window._separation_succeeded(self.result)
        self.app.processEvents()
        self.assertTrue(window.workbench_host.isVisible())
        window.sidebar.projects.click()
        self.assertTrue(window.drop_area.isVisible())
        self.assertFalse(window.workbench_host.isVisible())
        window.sidebar.mixer.click()
        self.assertTrue(window.workbench_host.isVisible())
        window.resize(940, 650)
        window.project_title.setText("Un nombre de canción muy largo " * 20)
        self.app.processEvents()
        self.assertEqual((window.width(), window.height()), (940, 650))
        self.assertLessEqual(window.import_button.mapTo(window, QPoint(0, 0)).x()
                             + window.import_button.width(), window.width())
        window._thread = object()
        event = QCloseEvent()
        window.closeEvent(event)
        self.assertFalse(event.isAccepted())
        with patch.object(window._import_service, "import_file") as imported:
            window._start_import("other.wav")
            imported.assert_not_called()
        window._thread = None
        window.close()
