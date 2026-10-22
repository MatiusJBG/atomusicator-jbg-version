"""Ventana principal y flujo de importación de audio."""

from pathlib import Path

from PySide6.QtCore import QStandardPaths, QThread, Qt, Signal
from PySide6.QtGui import QAction, QCloseEvent, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from vocal_splitter.application.import_audio import ImportAudioService
from vocal_splitter.application.separate_vocals import SeparateVocals
from vocal_splitter.domain.audio_session import AudioSession
from vocal_splitter.domain.separation_job import SeparationStage
from vocal_splitter.domain.separation_result import SeparationResult
from vocal_splitter.domain.stem import StemKind
from vocal_splitter.infrastructure.separation.audio_separator_engine import AudioSeparatorEngine
from vocal_splitter.infrastructure.separation.model_profile import load_reviewed_profiles
from vocal_splitter.infrastructure.projects.settings_store import SettingsStore
from vocal_splitter.ui.import_worker import ImportWorker
from vocal_splitter.ui.audio_workbench import AudioWorkbench
from vocal_splitter.ui.pitch_worker import PitchWorker
from vocal_splitter.ui.settings_dialog import SettingsDialog
from vocal_splitter.ui.separation_worker import SeparationWorker


class DropArea(QFrame):
    file_dropped = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dropArea")
        self.setAcceptDrops(True)
        self.setMinimumHeight(300)

        wave = QLabel("∿")
        wave.setObjectName("waveMark")
        wave.setAlignment(Qt.AlignmentFlag.AlignCenter)

        prompt = QLabel("Suelta una mezcla de audio aquí")
        prompt.setObjectName("dropPrompt")
        prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)

        formats = QLabel("WAV · MP3 · FLAC · M4A")
        formats.setObjectName("formatList")
        formats.setAlignment(Qt.AlignmentFlag.AlignCenter)

        content = QVBoxLayout(self)
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content.setSpacing(8)
        content.addWidget(wave)
        content.addWidget(prompt)
        content.addWidget(formats)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls() and any(
            url.isLocalFile() for url in event.mimeData().urls()
        ):
            event.acceptProposedAction()
            self.setProperty("dragActive", True)
            self.style().unpolish(self)
            self.style().polish(self)
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self.file_dropped.emit(url.toLocalFile())
                event.acceptProposedAction()
                return
        event.ignore()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Separador Vocal")
        self.resize(980, 680)
        self.setMinimumSize(720, 520)

        self._settings_store = SettingsStore()
        self._project_settings = self._settings_store.load()
        self._import_service = ImportAudioService()
        self._thread: QThread | None = None
        self._worker: ImportWorker | None = None
        self._current_session: AudioSession | None = None
        self._separation_thread: QThread | None = None
        self._separation_worker: SeparationWorker | None = None
        self._separation_result: SeparationResult | None = None
        self._pitch_thread: QThread | None = None
        self._pitch_worker: PitchWorker | None = None
        self.workbench: AudioWorkbench | None = None

        self._build_menu()
        self._build_content()
        self.setStyleSheet(
            "QMainWindow, QWidget#central { background: #0b1219; color: #edf3f5; }"
            "QLabel#pageTitle { font-size: 28px; font-weight: 700; color: #edf3f5; }"
            "QLabel#pageSubtitle { font-size: 14px; color: #a9bbc4; }"
            "QPushButton { background: #56d6d1; color: #102128; border: 0;"
            " border-radius: 7px; padding: 10px 18px; font-weight: 650; }"
            "QPushButton:hover { background: #79e3de; }"
            "QPushButton:checked { background: #ffb547; color: #19202a; }"
            "QPushButton:disabled { background: #3b7776; color: #d7e5e5; }"
            "QFrame#dropArea { background: #101923; border: 1px dashed #49606c;"
            " border-radius: 10px; }"
            "QFrame#dropArea[dragActive='true'] { border: 2px solid #56d6d1;"
            " background: #142631; }"
            "QFrame#separationPanel { background: #101923; border: 1px solid #29404b;"
            " border-radius: 10px; }"
            "QLabel#separationHeading { color: #edf3f5; font-size: 24px; font-weight: 700; }"
            "QLabel#separationPhase { color: #56d6d1; font-size: 18px; font-weight: 650; }"
            "QLabel#separationSteps { color: #c3d4da; font-size: 14px; }"
            "QLabel#separationDetail { color: #a9bbc4; font-size: 14px; }"
            "QLabel#waveMark { color: #56d6d1; font-size: 52px; font-weight: 700; }"
            "QLabel#dropPrompt { color: #edf3f5; font-size: 19px; font-weight: 600; }"
            "QLabel#formatList { color: #93aab5; font-size: 12px; }"
            "QLabel#result { color: #dce8ec; font-size: 14px; }"
            "QProgressBar { border: 0; background: #1b2a37; height: 5px; }"
            "QProgressBar::chunk { background: #ff8b6a; }"
            "QMenuBar { background: #0b1219; color: #dce8ec; }"
            "QMenuBar::item:selected, QMenu::item:selected { background: #1b2a37; }"
        )

    def _build_menu(self) -> None:
        settings_action = QAction("Carpeta de proyectos…", self)
        settings_action.triggered.connect(self._open_settings)
        file_menu = self.menuBar().addMenu("Archivo")
        file_menu.addAction(settings_action)

        credits_action = QAction("Modelos y bibliotecas…", self)
        credits_action.triggered.connect(self._show_credits)
        help_menu = self.menuBar().addMenu("Ayuda")
        help_menu.addAction(credits_action)

    def _build_content(self) -> None:
        title = QLabel("Separador Vocal")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Deja la voz principal al frente. Separa los coros para mezclarlos aparte.")
        subtitle.setObjectName("pageSubtitle")

        self.import_button = QPushButton("Importar audio")
        self.import_button.setMinimumHeight(44)
        self.import_button.clicked.connect(self._choose_file)

        self.separate_button = QPushButton("Separar voz y coros")
        self.separate_button.setMinimumHeight(44)
        self.separate_button.setEnabled(False)
        self.separate_button.clicked.connect(self._start_separation)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setMinimumHeight(44)
        self.cancel_button.hide()
        self.cancel_button.clicked.connect(self._cancel_separation)

        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.separate_button)
        header.addWidget(self.cancel_button)
        header.addWidget(self.import_button)

        self.drop_area = DropArea()
        self.drop_area.file_dropped.connect(self._start_import)
        self.separation_panel = QFrame()
        self.separation_panel.setObjectName("separationPanel")
        self.separation_panel.setMinimumHeight(300)
        process_layout = QVBoxLayout(self.separation_panel)
        process_layout.setContentsMargins(28, 28, 28, 28)
        process_layout.setSpacing(12)
        self.separation_heading = QLabel("Separando la mezcla")
        self.separation_heading.setObjectName("separationHeading")
        self.separation_phase = QLabel("Preparando modelos de audio…")
        self.separation_phase.setObjectName("separationPhase")
        self.separation_steps = QLabel(
            "1  Voz + acompañamiento     →     2  Voz principal + coros     →     "
            "3  Validación de pistas"
        )
        self.separation_steps.setObjectName("separationSteps")
        self.separation_detail = QLabel("Preparando el procesamiento local.")
        self.separation_detail.setObjectName("separationDetail")
        self.separation_detail.setWordWrap(True)
        self.separation_progress = QProgressBar()
        self.separation_progress.setRange(0, 100)
        self.separation_progress.setValue(0)
        self.separation_progress.setTextVisible(True)
        process_layout.addStretch(1)
        process_layout.addWidget(self.separation_heading)
        process_layout.addWidget(self.separation_phase)
        process_layout.addWidget(self.separation_steps)
        process_layout.addWidget(self.separation_progress)
        process_layout.addWidget(self.separation_detail)
        process_layout.addStretch(1)
        self.separation_panel.hide()
        self.workbench_host = QWidget()
        self.workbench_layout = QVBoxLayout(self.workbench_host)
        self.workbench_layout.setContentsMargins(0, 0, 0, 0)
        self.workbench_host.hide()

        self.result_label = QLabel("Tus archivos originales permanecen en su ubicación.")
        self.result_label.setObjectName("result")
        self.result_label.setWordWrap(True)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.hide()

        content = QVBoxLayout()
        content.setContentsMargins(42, 34, 42, 34)
        content.setSpacing(14)
        content.addLayout(header)
        content.addWidget(subtitle)
        content.addSpacing(18)
        content.addWidget(self.drop_area, 1)
        content.addWidget(self.separation_panel, 1)
        content.addWidget(self.workbench_host, 1)
        content.addWidget(self.progress)
        content.addWidget(self.result_label)

        central = QWidget()
        central.setObjectName("central")
        central.setLayout(content)
        self.setCentralWidget(central)
        self.statusBar().showMessage("Listo para importar audio")

    def _choose_file(self) -> None:
        source_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar audio",
            str(Path.home()),
            "Audio (*.wav *.mp3 *.flac *.m4a)",
        )
        if source_path:
            self._start_import(source_path)

    def _start_import(self, source_path: str) -> None:
        if self._thread is not None:
            return

        self.import_button.setEnabled(False)
        self.progress.show()
        self.result_label.setText("Leyendo el archivo y preparando una sesión local…")
        self.statusBar().showMessage("Importando audio…")

        thread = QThread(self)
        worker = ImportWorker(
            self._import_service,
            Path(source_path),
            self._project_settings,
        )
        worker.moveToThread(thread)
        self._worker = worker
        thread.started.connect(worker.run)
        worker.succeeded.connect(self._import_succeeded)
        worker.failed.connect(self._import_failed)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._import_finished)
        thread.finished.connect(thread.deleteLater)
        self._thread = thread
        thread.start()

    def _import_succeeded(self, session: AudioSession) -> None:
        self._current_session = session
        self.separate_button.setEnabled(True)
        asset = session.asset
        duration = self._format_duration(asset.duration_seconds)
        size_mb = asset.size_bytes / (1024 * 1024)
        self.result_label.setText(
            f"{asset.file_name} · {duration} · {asset.sample_rate_hz:,} Hz · "
            f"{asset.channels} canal(es) · {size_mb:.1f} MB\n"
            f"Sesión guardada en: {session.directory}"
        )
        self.statusBar().showMessage("Audio importado y listo para procesar")

    def _import_failed(self, message: str) -> None:
        self.result_label.setText(message)
        self.statusBar().showMessage("No se pudo importar el audio")
        QMessageBox.warning(self, "No se pudo importar", message)

    def _import_finished(self) -> None:
        self.progress.hide()
        self.import_button.setEnabled(True)
        self.separate_button.setEnabled(self._current_session is not None)
        self._worker = None
        self._thread = None

    def _start_separation(self) -> None:
        if self._separation_thread is not None or self._current_session is None:
            return

        app_data = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppLocalDataLocation
        )
        app_data_directory = (
            Path(app_data)
            if app_data
            else Path.home() / "AppData/Local/Separador Vocal"
        )
        model_cache = app_data_directory / "models"
        try:
            profiles = load_reviewed_profiles()
            missing_models = [
                profile.filename
                for profile in profiles.values()
                if not (model_cache / profile.filename).is_file()
            ]
            if missing_models:
                missing = "\n".join(f"• {name}" for name in missing_models)
                answer = QMessageBox.question(
                    self,
                    "Descargar modelos de separación",
                    "Se necesitan estos modelos UVR (descarga total aproximada: "
                    "120 MB):\n\n"
                    f"{missing}\n\n"
                    "Se guardarán en la caché local y se verificarán antes de usarlos. "
                    "¿Descargarlos ahora?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if answer != QMessageBox.StandardButton.Yes:
                    return
            service = SeparateVocals(AudioSeparatorEngine(model_cache))
        except Exception as error:
            QMessageBox.warning(self, "No se pudo iniciar", str(error))
            return

        thread = QThread(self)
        worker = SeparationWorker(service, self._current_session)
        worker.moveToThread(thread)
        worker.progress.connect(self._separation_progress)
        worker.succeeded.connect(self._separation_succeeded)
        worker.failed.connect(self._separation_failed)
        worker.cancelled.connect(self._separation_cancelled)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._separation_finished)
        thread.finished.connect(thread.deleteLater)

        self._separation_thread = thread
        self._separation_worker = worker
        self.import_button.setEnabled(False)
        self.separate_button.setEnabled(False)
        self.cancel_button.show()
        self.drop_area.hide()
        self.workbench_host.hide()
        self.separation_panel.show()
        self.separation_progress.setRange(0, 0)
        self.separation_progress.show()
        self.separation_phase.setText("Preparando los modelos de separación…")
        self.separation_detail.setText(
            "El procesamiento se ejecuta localmente. La primera ejecución puede tardar "
            "mientras se preparan los modelos."
        )
        self.result_label.setText(
            "Preparando la separación local. La primera ejecución descargará los dos modelos UVR configurados."
        )
        self.statusBar().showMessage("Preparando separación…")
        thread.start()

    def _separation_progress(self, stage: str, message: str, percent: int) -> None:
        stage_labels = {
            SeparationStage.PREPARING.value: "Preparando modelos de separación",
            SeparationStage.VOICE_AND_INSTRUMENTAL.value:
                "Etapa 1/2 · Separando voz y acompañamiento",
            SeparationStage.LEAD_AND_BACKING.value:
                "Etapa 2/2 · Separando voz principal y coros",
            SeparationStage.FINALIZING.value: "Validando y guardando las tres pistas",
        }
        self.separation_phase.setText(
            stage_labels.get(stage, "Procesando audio localmente")
        )
        self.separation_detail.setText(message)
        if message.startswith("Descargando modelo"):
            self.separation_progress.setRange(0, 100)
            self.separation_progress.setValue(percent)
        elif message == "Separando audio localmente…":
            self.separation_progress.setRange(0, 0)
        else:
            self.separation_progress.setRange(0, 100)
            self.separation_progress.setValue(percent)
        self.result_label.setText(message)
        self.statusBar().showMessage(message)

    def _separation_succeeded(self, result: SeparationResult) -> None:
        self._separation_result = result
        labels = {
            StemKind.LEAD_VOCAL: "Voz principal",
            StemKind.BACKING_VOCALS: "Coros / residuo vocal",
            StemKind.INSTRUMENTAL: "Acompañamiento",
        }
        paths = "\n".join(
            f"{labels[stem.kind]}: {stem.path}"
            for stem in result.stems
        )
        self.result_label.setText(
            "Separación lista. La voz principal y los coros son estimaciones; "
            "escucha las pistas antes de usarlas.\n" + paths
        )
        self.separation_panel.hide()
        self.drop_area.hide()
        if self.workbench is not None:
            self.workbench.dispose()
            self.workbench.deleteLater()
        self.workbench = AudioWorkbench(result, self.workbench_host)
        self.workbench.pitch_requested.connect(self._start_pitch_render)
        self.workbench_layout.addWidget(self.workbench)
        self.workbench_host.show()
        self.statusBar().showMessage("Separación lista")

    def _start_pitch_render(self, semitones: int) -> None:
        if self._pitch_thread is not None or self._separation_result is None or self._current_session is None:
            return
        if self.workbench is not None:
            self.workbench.apply_pitch_button.setEnabled(False)
            self.workbench.play_button.setEnabled(False)
        thread = QThread(self)
        worker = PitchWorker(
            self._separation_result,
            self._current_session.directory / "outputs" / "pitch-renders",
            semitones,
        )
        worker.moveToThread(thread)
        worker.finished.connect(self._pitch_rendered)
        worker.failed.connect(self._pitch_failed)
        worker.done.connect(thread.quit)
        worker.done.connect(worker.deleteLater)
        thread.started.connect(worker.run)
        thread.finished.connect(self._pitch_finished)
        thread.finished.connect(thread.deleteLater)
        self._pitch_thread = thread
        self._pitch_worker = worker
        self.statusBar().showMessage(f"Renderizando pitch: {semitones:+d} semitonos…")
        thread.start()

    def _pitch_rendered(self, result: SeparationResult) -> None:
        if self.workbench is not None:
            self.workbench.set_result(result)
        self.statusBar().showMessage("Transposición renderizada; tempo y originales conservados")

    def _pitch_failed(self, message: str) -> None:
        QMessageBox.warning(self, "No se pudo cambiar el pitch", message)
        self.statusBar().showMessage("Falló la transposición; los stems originales siguen disponibles")

    def _pitch_finished(self) -> None:
        self._pitch_thread = None
        self._pitch_worker = None
        if self.workbench is not None:
            self.workbench.apply_pitch_button.setEnabled(True)
            self.workbench.play_button.setEnabled(True)

    def _separation_failed(self, message: str, partial_result: object) -> None:
        if isinstance(partial_result, SeparationResult):
            paths = "\n".join(str(stem.path) for stem in partial_result.stems)
            message = f"{message}\nResultados de primera etapa:\n{paths}"
        self.result_label.setText(message)
        self.separation_panel.hide()
        self.drop_area.show()
        self.statusBar().showMessage("No se completó la separación")
        QMessageBox.warning(self, "No se pudo separar", message)

    def _separation_cancelled(self) -> None:
        self.result_label.setText(
            "Separación cancelada. El audio de origen no se modificó."
        )
        self.separation_panel.hide()
        self.drop_area.show()
        self.statusBar().showMessage("Separación cancelada")

    def _cancel_separation(self) -> None:
        if self._separation_worker is not None:
            self._separation_worker.cancel()
            self.cancel_button.setEnabled(False)
            self.statusBar().showMessage(
                "Cancelación solicitada; el modelo terminará la operación actual…"
            )

    def _separation_finished(self) -> None:
        self.separation_progress.setRange(0, 100)
        self.import_button.setEnabled(True)
        self.separate_button.setEnabled(self._current_session is not None)
        self.cancel_button.hide()
        self.cancel_button.setEnabled(True)
        self._separation_worker = None
        self._separation_thread = None

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._separation_thread is not None:
            self._cancel_separation()
            self.statusBar().showMessage(
                "La operación se está cancelando. Cierra la ventana cuando termine."
            )
            event.ignore()
            return
        if self._pitch_thread is not None:
            self.statusBar().showMessage(
                "El render de pitch sigue en curso. Cierra la ventana cuando termine."
            )
            event.ignore()
            return
        if self.workbench is not None and self.workbench.export_running:
            self.statusBar().showMessage(
                "La exportación sigue en curso. Cierra la ventana cuando termine."
            )
            event.ignore()
            return
        super().closeEvent(event)

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self._project_settings, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        new_settings = dialog.project_settings()
        self._settings_store.save(new_settings)
        self._project_settings = new_settings
        self.statusBar().showMessage(
            f"Proyectos: {self._project_settings.projects_directory}",
            5000,
        )

    def _show_credits(self) -> None:
        QMessageBox.information(
            self,
            "Modelos y bibliotecas",
            "UVR solicita respetar MIT y atribuir a UVR, Anjok07 y aufr33. Los pesos no incluyen una licencia individual.\n"
            "Motor opcional: python-audio-separator, karaokenerds (MIT).\n\n"
            "Los pesos se descargan al confirmar y se verifican antes de usarse.\n"
            "Detalles: docs/third-party-notices.md",
        )

    @staticmethod
    def _format_duration(duration_seconds: float) -> str:
        total_seconds = int(round(duration_seconds))
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
