import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from vocal_splitter.infrastructure.audio import ffmpeg


class PortableFfmpegTests(unittest.TestCase):
    def test_frozen_app_finds_its_tools_without_system_installation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tools = root / "runtime" / "ffmpeg" / "bin"
            tools.mkdir(parents=True)
            for name in ("ffmpeg.exe", "ffprobe.exe"):
                (tools / name).touch()
            with (patch.object(sys, "frozen", True, create=True),
                  patch.object(sys, "_MEIPASS", str(root), create=True),
                  patch.object(Path, "home", return_value=root / "empty-home"),
                  patch.object(ffmpeg, "which", return_value=None),
                  patch.dict(os.environ, {"PATH": ""})):
                self.assertEqual(ffmpeg.find_ffmpeg(), str(tools / "ffmpeg.exe"))
                self.assertEqual(ffmpeg.find_ffprobe(), str(tools / "ffprobe.exe"))
                ffmpeg.ensure_ffmpeg_on_path()
                ffmpeg.ensure_ffmpeg_on_path()
                self.assertEqual(os.environ["PATH"], str(tools))

    def test_packaged_tools_take_priority_over_machine_specific_tools(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tools = root / "runtime" / "ffmpeg" / "bin"
            tools.mkdir(parents=True)
            (tools / "ffmpeg.exe").touch()
            (tools / "ffprobe.exe").touch()
            with (patch.object(sys, "frozen", True, create=True),
                  patch.object(sys, "_MEIPASS", str(root), create=True),
                  patch.object(ffmpeg, "which", return_value="C:/different/ffmpeg.exe"),
                  patch.object(Path, "home", return_value=root)):
                self.assertEqual(ffmpeg.find_ffmpeg(), str(tools / "ffmpeg.exe"))

    def test_incomplete_frozen_bundle_does_not_hide_failure_with_host_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tools = root / "runtime" / "ffmpeg" / "bin"
            tools.mkdir(parents=True)
            (tools / "ffmpeg.exe").touch()
            with (patch.object(sys, "frozen", True, create=True),
                  patch.object(sys, "_MEIPASS", str(root), create=True),
                  patch.object(ffmpeg, "which", return_value="C:/different/ffmpeg.exe"),
                  patch.object(Path, "home", return_value=root)):
                self.assertIsNone(ffmpeg.find_ffmpeg())

    def test_bundle_lookup_does_not_trust_current_working_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "ffmpeg.exe").touch()
            (root / "ffprobe.exe").touch()
            with (patch.object(sys, "frozen", True, create=True),
                  patch.object(sys, "_MEIPASS", str(root), create=True),
                  patch.object(Path, "home", return_value=root),
                  patch.object(ffmpeg, "which", return_value=None)):
                self.assertIsNone(ffmpeg.find_ffmpeg())
