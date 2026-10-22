import unittest
from types import ModuleType
from pathlib import Path

from vocal_splitter.__main__ import validate_torchvision_runtime
from vocal_splitter.infrastructure.separation.audio_separator_engine import (
    disable_mdx_progress_output,
)


class FrozenInferenceRuntimeTests(unittest.TestCase):
    def test_pyinstaller_bundles_torchvision_native_extensions(self) -> None:
        spec_path = Path(__file__).parents[1] / "packaging" / "SeparadorVocal.spec"
        source = spec_path.read_text(encoding="utf-8")

        self.assertIn('glob("*.pyd")', source)
        self.assertIn('"torchvision"', source)

    def test_torchvision_nms_operator_is_loadable(self) -> None:
        validate_torchvision_runtime()

    def test_mdx_progress_bar_is_disabled_for_desktop_runtime(self) -> None:
        module = ModuleType("audio_separator.separator.architectures.mdx_separator")
        calls: list[dict[str, object]] = []

        def progress_bar(*args: object, **kwargs: object) -> tuple[object, ...]:
            calls.append(kwargs)
            return args

        module.tqdm = progress_bar
        disable_mdx_progress_output(module)
        self.assertEqual(module.tqdm("frames"), ("frames",))

        self.assertEqual(calls, [{"disable": True}])


if __name__ == "__main__":
    unittest.main()
