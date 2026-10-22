import os
import sys
import tempfile
import unittest
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from vocal_splitter.infrastructure.audio import ffmpeg


class PortableFfmpegTests(unittest.TestCase):
    def test_preflight_reports_a_probe_that_cannot_execute(self):
        from vocal_splitter.application.separation_errors import SeparationFfmpegUnavailableError
        from vocal_splitter.infrastructure.separation import audio_separator_engine as engine
        completed = subprocess.CompletedProcess(["ffmpeg", "-version"], 0, "ffmpeg version fixture", "")
        with (patch.object(engine, "ensure_ffmpeg_on_path", return_value="ffmpeg.exe"),
              patch.object(engine, "find_ffprobe", return_value="ffprobe.exe"),
              patch.object(engine.subprocess, "run", side_effect=[completed, OSError("missing DLL")])):
            with self.assertRaises(SeparationFfmpegUnavailableError):
                engine.AudioSeparatorEngine._ensure_ffmpeg()

    @unittest.skipUnless(
        (Path(__file__).parents[1] / "build/ffmpeg-runtime/bin/ffmpeg.exe").is_file(),
        "Prepare the pinned runtime to run the isolated Windows integration test",
    )
    def test_real_tools_decode_export_and_pitch_with_empty_path(self):
        import numpy as np
        import soundfile as sf
        from vocal_splitter.application.export_options import ExportOptions
        from vocal_splitter.domain.stem import Stem, StemKind
        from vocal_splitter.domain.separation_result import SeparationResult
        from vocal_splitter.infrastructure.audio.pitch_processor import PitchProcessor
        from vocal_splitter.infrastructure.separation.audio_separator_engine import AudioSeparatorEngine
        from vocal_splitter.ui.export_worker import ExportWorker

        prepared = Path(__file__).parents[1] / "build/ffmpeg-runtime/bin"
        with tempfile.TemporaryDirectory(prefix="audio portátil ") as temporary:
            root = Path(temporary)
            tools = root / "runtime/ffmpeg/bin"
            tools.mkdir(parents=True)
            for name in ("ffmpeg.exe", "ffprobe.exe"):
                os.link(prepared / name, tools / name)
            source = root / "audio de prueba.wav"
            t = np.arange(44100) / 44100
            sf.write(source, .2 * np.sin(2 * np.pi * 220 * t), 44100)
            original = source.read_bytes()
            with (patch.object(sys, "frozen", True, create=True),
                  patch.object(sys, "_MEIPASS", str(root), create=True),
                  patch.object(Path, "home", return_value=root / "empty-home"),
                  patch.dict(os.environ, {"PATH": ""})):
                self.assertEqual(AudioSeparatorEngine._ensure_ffmpeg(), str(tools / "ffmpeg.exe"))
                # This is how the third-party separator invokes its dependency.
                command = subprocess.run(["ffmpeg", "-version"], cwd=root,
                                         capture_output=True, timeout=15)
                self.assertEqual(command.returncode, 0)
                result = SeparationResult((Stem(StemKind.LEAD_VOCAL, source, 1, 44100, 1),))
                worker = ExportWorker(result, root, ExportOptions(format="mp3"))
                outputs, errors = [], []
                worker.exported.connect(outputs.append)
                worker.failed.connect(errors.append)
                worker.run()
                self.assertEqual(errors, [])
                exported = Path(outputs[0]) / "voz_principal.mp3"
                probe = subprocess.run([ffmpeg.find_ffprobe(), "-v", "error", "-show_format",
                                        "-of", "json", str(exported)],
                                       capture_output=True, text=True, timeout=15)
                self.assertEqual(probe.returncode, 0)
                self.assertGreater(float(json.loads(probe.stdout)["format"]["duration"]), .9)
                import audioread.ffdec
                with audioread.ffdec.FFmpegAudioFile(str(exported)) as decoded:
                    self.assertGreater(sum(len(block) for block in decoded), 0)
                shifted = root / "tono aplicado.wav"
                PitchProcessor().render(source, shifted, 2, preserve_formants=True)
                self.assertLessEqual(abs(sf.info(shifted).frames - 44100), 1)
                self.assertEqual(source.read_bytes(), original)

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
