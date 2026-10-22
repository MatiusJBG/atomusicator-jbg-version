import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from vocal_splitter.infrastructure.audio.realtime_mixer import MixerTrack, RealtimeMixer


class FiveStemMixerTests(unittest.TestCase):
    def test_pan_master_and_meters_follow_audible_samples(self):
        mixer = RealtimeMixer([MixerTrack("Voice", np.full((16, 2), 0.4, dtype=np.float32))], 8000)
        mixer.set_controls(0, pan=-1)
        mixer.set_master_gain(0.5)
        output = np.empty((4, 2), dtype=np.float32)
        mixer._callback(output, 4, None, None)
        np.testing.assert_allclose(output[:, 0], 0.2)
        np.testing.assert_allclose(output[:, 1], 0)
        levels, master = mixer.meter_levels()
        self.assertAlmostEqual(levels[0], 0.4)
        self.assertAlmostEqual(master[0], 0.2)
        self.assertEqual(master[1], 0)
        mixer.set_controls(0, muted=True)
        mixer._callback(output, 4, None, None)
        self.assertFalse(np.any(output))
        self.assertEqual(mixer.meter_levels()[0], (0.0,))

    def test_mono_pan_is_safe_and_master_keeps_peak_guard(self):
        mixer = RealtimeMixer([MixerTrack("Mono", np.ones((8, 1), dtype=np.float32))], 8000)
        mixer.set_controls(0, pan=1)
        mixer.set_master_gain(1.5)
        output = np.empty((4, 1), dtype=np.float32)
        mixer._callback(output, 4, None, None)
        np.testing.assert_allclose(output, 0.98)

    def test_five_tracks_support_live_gain_mute_solo_and_peak_guard(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            names = ["Voz", "Coros", "Batería", "Bajo", "Instrumental"]
            paths = []
            for name in names:
                path = root / f"{name}.wav"
                sf.write(path, np.full((16, 2), 0.25, dtype=np.float32), 8000, subtype="FLOAT")
                paths.append((name, path))

            mixer = RealtimeMixer.from_files(paths)
            self.assertEqual(len(mixer.tracks), 5)
            mixer.set_controls(0, gain=0.5)
            mixer.set_controls(1, muted=True)
            mixer.set_controls(2, solo=True)
            output = np.empty((4, 2), dtype=np.float32)
            mixer._callback(output, 4, None, None)
            np.testing.assert_allclose(output, 0.25, atol=1e-6)

            mixer.seek(0)
            mixer.set_controls(2, solo=False)
            mixer.set_controls(0, gain=1.5)
            mixer.set_controls(1, muted=False)
            mixer._callback(output, 4, None, None)
            np.testing.assert_allclose(output, 0.98, atol=1e-6)
            self.assertLessEqual(float(np.max(np.abs(output))), 0.98)


if __name__ == "__main__":
    unittest.main()
