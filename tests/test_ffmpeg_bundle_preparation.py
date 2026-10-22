import hashlib
import io
import importlib.util
import tempfile
import unittest
import zipfile
from unittest.mock import patch
from pathlib import Path


def load_preparer():
    path = Path(__file__).parents[1] / "packaging" / "prepare_ffmpeg.py"
    spec = importlib.util.spec_from_file_location("prepare_ffmpeg", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FfmpegBundlePreparationTests(unittest.TestCase):
    def test_failed_download_never_leaves_a_partial_runtime_archive(self):
        preparer = load_preparer()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = b"tampered payload"
            manifest = {"archive_root": "fixture", "archive_url": "https://example.test/tools.zip",
                        "archive_size": len(data), "archive_sha256": "0" * 64}
            with patch.object(preparer, "urlopen", return_value=io.BytesIO(data)):
                with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                    preparer._download_archive(root, manifest)
            self.assertEqual(list(root.iterdir()), [])

    def test_corrupted_binary_is_rejected_before_packaging(self):
        preparer = load_preparer()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "bin").mkdir()
            files = {"bin/ffmpeg.exe": b"encoder", "bin/ffprobe.exe": b"probe"}
            for name, data in files.items():
                (root / name).write_bytes(data)
            (root / "LICENSE").write_text("GNU GENERAL PUBLIC LICENSE", encoding="utf-8")
            (root / "README.txt").write_text("provider", encoding="utf-8")
            manifest = {"files": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
            preparer.validate_runtime(root, manifest, check_tools=False)
            (root / "bin/ffprobe.exe").write_bytes(b"corrupt")
            with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                preparer.validate_runtime(root, manifest, check_tools=False)

    def test_extraction_only_writes_expected_files(self):
        preparer = load_preparer()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "tools.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                for name in preparer.RUNTIME_FILES:
                    zipped.writestr("release/" + name, b"fixture")
                zipped.writestr("release/../../escape.txt", b"untrusted")
                zipped.writestr("release/bin/unrequested.exe", b"untrusted")
            target = root / "target"
            preparer.extract_runtime(archive, target, "release")
            self.assertEqual({str(p.relative_to(target)).replace("\\", "/") for p in target.rglob("*") if p.is_file()}, set(preparer.RUNTIME_FILES))
            self.assertFalse((root / "escape.txt").exists())

    def test_archive_checksum_mismatch_is_rejected(self):
        preparer = load_preparer()
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "archive.zip"
            archive.write_bytes(b"wrong file")
            with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                preparer.verify_sha256(archive, "0" * 64)

    def test_bundle_requires_both_tools_and_license(self):
        preparer = load_preparer()
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(RuntimeError):
                preparer.validate_runtime(Path(temporary), {"files": {}}, check_tools=False)
