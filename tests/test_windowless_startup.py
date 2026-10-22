"""Exercise first-run model metadata downloads with no console attached."""

import io
import runpy
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from vocal_splitter.infrastructure.standard_streams import ensure_standard_streams


class WindowlessStartupTests(unittest.TestCase):
    def test_build_installs_stream_hook_before_dependency_hooks(self) -> None:
        spec = Path(__file__).parents[1] / "packaging" / "SeparadorVocal.spec"
        source = spec.read_text(encoding="utf-8")
        self.assertLess(
            source.index('"pyi_rth_standard_streams.py"'),
            source.index('"pyi_rth_qt_dll_path.py"'),
        )

    def test_preserves_existing_console_or_redirected_outputs(self) -> None:
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr):
            ensure_standard_streams()
            self.assertIs(sys.stdout, stdout)
            self.assertIs(sys.stderr, stderr)

    def test_replaces_only_missing_output_and_is_idempotent(self) -> None:
        for missing in ("stdout", "stderr"):
            with self.subTest(stream=missing), patch.object(sys, missing, None):
                other_name = "stderr" if missing == "stdout" else "stdout"
                other = getattr(sys, other_name)
                ensure_standard_streams()
                replacement = getattr(sys, missing)
                try:
                    replacement.write("progress\n")
                    replacement.flush()
                    ensure_standard_streams()
                    self.assertIs(getattr(sys, missing), replacement)
                    self.assertIs(getattr(sys, other_name), other)
                finally:
                    replacement.close()

    def test_packaged_runtime_hook_provides_outputs(self) -> None:
        hook = Path(__file__).parents[1] / "packaging" / "pyi_rth_standard_streams.py"
        with patch.object(sys, "stdout", None), patch.object(sys, "stderr", None):
            runpy.run_path(str(hook))
            try:
                sys.stdout.write("dependency startup")
                sys.stderr.write("dependency progress")
            finally:
                sys.stdout.close()
                sys.stderr.close()

    def test_first_run_metadata_download_without_standard_streams(self) -> None:
        script = textwrap.dedent('''
            import logging
            import sys
            import tempfile
            from pathlib import Path
            from types import SimpleNamespace
            from unittest.mock import patch

            sys.stdout = None
            sys.stderr = None
            try:
                import vocal_splitter.__main__
                from audio_separator.separator import Separator

                payload = b'{"mdx_download_list": {}}'
                response = SimpleNamespace(
                    status_code=200,
                    headers={"content-length": str(len(payload))},
                    iter_content=lambda **_: iter([payload]),
                )
                owner = SimpleNamespace(logger=logging.getLogger("metadata-test"))
                with tempfile.TemporaryDirectory() as directory:
                    target = Path(directory) / "download_checks.json"
                    with patch("audio_separator.separator.separator.requests.get", return_value=response):
                        Separator.download_file_if_not_exists(owner, "https://example.invalid/metadata", target)
                    assert target.read_bytes() == payload
            except BaseException:
                import traceback
                sys.__stderr__.write(traceback.format_exc())
                raise SystemExit(1)
        ''')
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path(__file__).parents[1],
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
