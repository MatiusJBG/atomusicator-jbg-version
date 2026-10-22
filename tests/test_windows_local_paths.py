import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from vocal_splitter.application.project_settings import ProjectSettings
from vocal_splitter.domain.audio_asset import AudioAsset
from vocal_splitter.infrastructure.audio import ffmpeg
from vocal_splitter.infrastructure.projects.session_store import SessionStore
from vocal_splitter.infrastructure.projects.settings_store import SettingsStore
import vocal_splitter.application.project_settings as project_settings_module


@unittest.skipUnless(os.name == "nt", "Windows path behavior")
class WindowsLocalPathsTests(unittest.TestCase):
    def test_find_ffmpeg_uses_reparse_target_instead_of_winget_link(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            home = root / "home"
            link = home / "AppData" / "Local" / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe"
            target = root / "Packages" / "ffmpeg.exe"
            link.parent.mkdir(parents=True)
            target.parent.mkdir()
            target.touch()

            with (
                patch.object(ffmpeg, "which", side_effect=OSError(448, "untrusted mount point")),
                patch.object(ffmpeg.os, "readlink", return_value=str(target)),
                patch.object(Path, "home", return_value=home),
            ):
                found = ffmpeg.find_ffmpeg()

        self.assertEqual(found, str(target))

    def test_real_ffmpeg_directory_is_first_even_if_already_in_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            link_directory = root / "WinGet" / "Links"
            real_directory = root / "WinGet" / "Packages" / "ffmpeg" / "bin"
            old_path = os.pathsep.join((str(link_directory), str(real_directory), "C:\\Windows"))

            with (
                patch.object(ffmpeg, "find_ffmpeg", return_value=str(real_directory / "ffmpeg.exe")),
                patch.dict(os.environ, {"PATH": old_path}),
            ):
                ffmpeg.ensure_ffmpeg_on_path()
                entries = os.environ["PATH"].split(os.pathsep)

        self.assertEqual(os.path.normcase(entries[0]), os.path.normcase(str(real_directory)))

    def test_default_project_storage_is_under_local_app_data(self) -> None:
        local_app_data = Path(os.environ["LOCALAPPDATA"])

        with patch.dict(os.environ, {"LOCALAPPDATA": str(local_app_data)}):
            settings = ProjectSettings.default()

        self.assertEqual(
            settings.projects_directory,
            local_app_data / "Separador Vocal" / "Separador Vocal" / "projects",
        )
        self.assertNotIn("Documents", str(settings.projects_directory))

    def test_invalid_saved_project_directory_recovers_to_local_app_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            local_app_data = Path(temporary_directory) / "local-app-data"
            invalid_saved_path = Path(os.environ["LOCALAPPDATA"]).anchor
            with (
                patch.dict(os.environ, {"LOCALAPPDATA": str(local_app_data)}),
                patch("vocal_splitter.infrastructure.projects.settings_store.QSettings") as qsettings,
            ):
                qsettings.return_value.value.return_value = str(invalid_saved_path)

                settings = SettingsStore().load()

        self.assertEqual(
            settings.projects_directory,
            local_app_data / "Separador Vocal" / "Separador Vocal" / "projects",
        )
        qsettings.return_value.setValue.assert_called_once_with(
            "projects/directory", str(settings.projects_directory)
        )
        qsettings.return_value.sync.assert_called_once_with()

    def test_local_storage_preflight_creates_folder_and_removes_write_probe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = Path(temporary_directory) / "projects"

            ProjectSettings(target).validate_writable_local_directory()

            self.assertTrue(target.is_dir())
            self.assertEqual(list(target.iterdir()), [])

    def test_local_storage_preflight_rejects_drive_root(self) -> None:
        root = Path(os.environ["LOCALAPPDATA"]).anchor

        with self.assertRaisesRegex(ValueError, "subcarpeta"):
            ProjectSettings(Path(root)).validate_writable_local_directory()

    def test_local_storage_preflight_rejects_network_paths(self) -> None:
        network_path = Path(r"\\server\share\projects")

        with self.assertRaisesRegex(ValueError, "unidad local"):
            ProjectSettings(network_path).validate_writable_local_directory()

    def test_local_storage_preflight_rejects_remote_mapped_drives(self) -> None:
        settings = ProjectSettings(Path(os.environ["LOCALAPPDATA"]) / "projects")
        with patch.object(
            project_settings_module.ctypes.windll.kernel32,
            "GetDriveTypeW",
            return_value=4,
        ):
            with self.assertRaisesRegex(ValueError, "disco local"):
                settings.validate_writable_local_directory()

    def test_session_store_creates_manifest_and_outputs_in_local_app_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.wav"
            source.touch()
            local_app_data = root / "local-app-data"
            with patch.dict(os.environ, {"LOCALAPPDATA": str(local_app_data)}):
                settings = ProjectSettings.default()
            asset = AudioAsset(
                source_path=source,
                duration_seconds=1.0,
                sample_rate_hz=44100,
                channels=2,
                size_bytes=1,
            )

            session = SessionStore().create(asset, settings.projects_directory)

            self.assertTrue((session.directory / "session.json").is_file())
            self.assertTrue((session.directory / "outputs").is_dir())
            self.assertTrue(session.directory.is_relative_to(local_app_data))

    @unittest.skipUnless(ffmpeg.find_ffmpeg(), "FFmpeg is not installed")
    def test_ffmpeg_preflight_runs_the_real_executable(self) -> None:
        from vocal_splitter.infrastructure.separation.audio_separator_engine import (
            AudioSeparatorEngine,
        )

        executable = AudioSeparatorEngine._ensure_ffmpeg()

        self.assertTrue(Path(executable).is_file())

    def test_installer_uses_protected_program_files_target_and_requires_elevation(self) -> None:
        installer = Path(__file__).parents[1] / "packaging" / "SeparadorVocal.iss"
        source = installer.read_text(encoding="utf-8")

        self.assertIn(r"DefaultDirName={autopf}\Separador Vocal", source)
        self.assertIn("PrivilegesRequired=admin", source)
        self.assertIn("function NextButtonClick(CurPageID: Integer): Boolean;", source)
        self.assertIn("DriveRoot", source)
        self.assertNotIn(r"DefaultDirName=C:\Separador Vocal", source)


if __name__ == "__main__":
    unittest.main()
