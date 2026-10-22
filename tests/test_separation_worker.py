import unittest

from vocal_splitter.domain.separation_job import SeparationStage
from vocal_splitter.ui.separation_worker import SeparationWorker


class DecreasingProgressService:
    def execute(self, _session, *, progress, cancellation):
        progress(SeparationStage.PREPARING, 0, "Preparando")
        progress(SeparationStage.PREPARING, 7, "Descargando modelo (1 MB)…")
        progress(SeparationStage.PREPARING, 2, "Descargando modelo (2 MB)…")
        return object()


class SeparationWorkerTests(unittest.TestCase):
    def test_progress_callback_never_moves_job_progress_backwards(self) -> None:
        worker = SeparationWorker(DecreasingProgressService(), None)
        reported: list[tuple[str, str, int]] = []
        failures: list[str] = []
        worker.progress.connect(
            lambda stage, message, percent: reported.append((stage, message, percent))
        )
        worker.failed.connect(lambda message, _partial: failures.append(message))

        worker.run()

        self.assertEqual(failures, [])
        self.assertEqual([event[2] for event in reported], [0, 7, 7])
        self.assertTrue(all(
            reported[index][2] <= reported[index + 1][2]
            for index in range(len(reported) - 1)
        ))


if __name__ == "__main__":
    unittest.main()
