"""Mezclador DAW con carriles sincronizados y controles conectados al audio local."""

from pathlib import Path

from PySide6.QtCore import QThread, Qt, QTimer, Signal
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QAbstractSpinBox, QDialog, QFrame, QHBoxLayout, QMessageBox, QPushButton,
    QProgressBar, QScrollArea, QSlider, QSpinBox, QVBoxLayout, QWidget,
)

from vocal_splitter.domain.separation_result import SeparationResult
from vocal_splitter.infrastructure.audio.realtime_mixer import RealtimeMixer
from vocal_splitter.ui.audio_widgets import CheckBox, LevelMeter, TimelineRuler, Waveform, label, time_text
from vocal_splitter.ui.export_dialog import ExportDialog
from vocal_splitter.ui.export_worker import ExportWorker
from vocal_splitter.ui.track_row import TrackRow


class AudioWorkbench(QWidget):
    pitch_requested = Signal(int)

    def __init__(self, result: SeparationResult, parent=None):
        super().__init__(parent)
        self.setObjectName("audioWorkbench")
        self.result = result
        self._mixer = None
        self._rows = []
        self.track_rows = []
        self._export_thread = None
        self._export_worker = None
        self._pitch_busy = False
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._update_playhead)
        self._build()
        self.reload_audio()
        self.shortcut = QShortcut(QKeySequence("Space"), self)
        self.shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut.activated.connect(self._toggle_playback)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)
        heading = QHBoxLayout()
        heading.addWidget(label("Mezclador DAW", "workbenchTitle"))
        self.stem_count = label("5 stems", "stemCount")
        heading.addWidget(self.stem_count)
        self.mix_status = label("Todas las pistas activas")
        heading.addWidget(self.mix_status)
        heading.addStretch(1)
        self.export_status = label("", "accent")
        heading.addWidget(self.export_status)
        root.addLayout(heading)
        timeline = QHBoxLayout()
        timeline.setSpacing(0)
        tracks_heading = label("Pista / mezcla                                      Pico", "controlEyebrow")
        tracks_heading.setContentsMargins(12, 0, 0, 0)
        tracks_heading.setFixedWidth(300)
        timeline.addWidget(tracks_heading)
        self.ruler = TimelineRuler(self.result.stems[0].duration_seconds)
        self.ruler.seek_requested.connect(self._seek)
        timeline.addWidget(self.ruler, 1)
        root.addLayout(timeline)
        self.track_scroll = QScrollArea()
        self.track_scroll.setObjectName("trackScroll")
        self.track_scroll.setWidgetResizable(True)
        self.track_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("trackContent")
        self.track_container = QVBoxLayout(content)
        self.track_container.setContentsMargins(0, 0, 0, 0)
        self.track_container.setSpacing(0)
        self.track_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.track_scroll.setWidget(content)
        root.addWidget(self.track_scroll, 1)
        bottom = QHBoxLayout()
        bottom.setSpacing(10)
        transport = QFrame()
        transport.setObjectName("transportPanel")
        transport.setMinimumWidth(205)
        transport.setMaximumWidth(350)
        controls = QVBoxLayout(transport)
        controls.setContentsMargins(14, 12, 14, 12)
        controls.addWidget(label("Reproducción", "controlEyebrow"))
        buttons = QHBoxLayout()
        restart = QPushButton("|◀")
        restart.setObjectName("transportButton")
        restart.setAccessibleName("Volver al inicio")
        restart.setToolTip("Volver al inicio")
        restart.clicked.connect(lambda: self._seek(0))
        buttons.addWidget(restart)
        self.play_button = QPushButton("▶")
        self.play_button.setObjectName("playButton")
        self.play_button.setFixedSize(34, 34)
        self.play_button.setAccessibleName("Reproducir")
        self.play_button.setToolTip("Reproducir / pausar (Espacio)")
        self.play_button.clicked.connect(self._toggle_playback)
        buttons.addWidget(self.play_button)
        stop = QPushButton("■")
        stop.setObjectName("transportButton")
        stop.setAccessibleName("Detener")
        stop.clicked.connect(self.stop)
        buttons.addWidget(stop)
        self.position_label = label("00:00 / 00:00", "transportTime")
        buttons.addWidget(self.position_label)
        controls.addLayout(buttons)
        controls.addWidget(label("Espacio: reproducir / pausar", "gainValue"))
        bottom.addWidget(transport, 2)
        pitch_panel = QFrame()
        pitch_panel.setObjectName("pitchPanel")
        pitch_column = QVBoxLayout(pitch_panel)
        pitch_column.setContentsMargins(14, 12, 14, 12)
        pitch_heading = QHBoxLayout()
        pitch_heading.addWidget(label("Pitcher", "controlEyebrow"))
        self.pitch_status = label("Tempo original", "accent")
        pitch_heading.addWidget(self.pitch_status, 1, Qt.AlignmentFlag.AlignRight)
        pitch_column.addLayout(pitch_heading)
        pitch_controls = QHBoxLayout()
        pitch_steps = QHBoxLayout()
        pitch_steps.setSpacing(0)
        minus = QPushButton("−")
        minus.setFixedWidth(23)
        minus.setObjectName("transportButton")
        minus.setAccessibleName("Bajar un semitono")
        pitch_steps.addWidget(minus)
        self.pitch = QSpinBox()
        self.pitch.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.pitch.setRange(-12, 12)
        self.pitch.setPrefix("Pitch: ")
        self.pitch.setSuffix(" st")
        self.pitch.setAccessibleName("Transposición en semitonos")
        self.pitch.setMinimumWidth(84)
        pitch_steps.addWidget(self.pitch)
        plus = QPushButton("+")
        plus.setFixedWidth(23)
        plus.setObjectName("transportButton")
        plus.setAccessibleName("Subir un semitono")
        minus.clicked.connect(self.pitch.stepDown)
        plus.clicked.connect(self.pitch.stepUp)
        pitch_steps.addWidget(plus)
        self.pitch_steps = (minus, plus)
        pitch_controls.addLayout(pitch_steps)
        self.formants = CheckBox("Formantes")
        self.formants.setChecked(True)
        self.formants.setToolTip("Conservar el carácter de las voces al cambiar la tonalidad")
        pitch_controls.addWidget(self.formants)
        self.apply_pitch_button = QPushButton("Aplicar pitch")
        self.apply_pitch_button.clicked.connect(lambda: self.pitch_requested.emit(self.pitch.value()))
        pitch_controls.addWidget(self.apply_pitch_button)
        pitch_column.addLayout(pitch_controls)
        pitch_range = QHBoxLayout()
        pitch_range.addWidget(label("−12", "gainValue"))
        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_slider.setRange(-12, 12)
        self.pitch_slider.setAccessibleName("Ajustar tonalidad")
        self.pitch_slider.valueChanged.connect(self.pitch.setValue)
        self.pitch.valueChanged.connect(self.pitch_slider.setValue)
        pitch_range.addWidget(self.pitch_slider, 1)
        pitch_range.addWidget(label("+12 st", "gainValue"))
        pitch_column.addLayout(pitch_range)
        self.pitch_progress = QProgressBar()
        self.pitch_progress.setRange(0, 100)
        self.pitch_progress.setValue(0)
        self.pitch_progress.setTextVisible(False)
        pitch_column.addWidget(self.pitch_progress)
        bottom.addWidget(pitch_panel, 3)
        master = QFrame()
        master.setObjectName("masterPanel")
        master.setMinimumWidth(160)
        master.setMaximumWidth(300)
        master_column = QVBoxLayout(master)
        master_column.setContentsMargins(12, 12, 12, 12)
        master_column.addWidget(label("Master", "controlEyebrow"))
        self.master_meter = LevelMeter(stereo=True)
        master_column.addWidget(self.master_meter)
        self.master_gain = QSlider(Qt.Orientation.Horizontal)
        self.master_gain.setRange(0, 150)
        self.master_gain.setValue(100)
        self.master_gain.setAccessibleName("Volumen master")
        self.master_gain.setToolTip("Volumen de escucha; la exportación conserva el nivel de los stems")
        self.master_gain.valueChanged.connect(lambda value: self._mixer and self._mixer.set_master_gain(value / 100))
        master_column.addWidget(self.master_gain)
        self.export_button = QPushButton("↓ Exportar stems")
        self.export_button.setObjectName("primaryButton")
        self.export_button.clicked.connect(self._choose_export_directory)
        master_column.addWidget(self.export_button)
        bottom.addWidget(master, 2)
        root.addLayout(bottom)

    def set_result(self, result):
        self.result = result
        self.reload_audio()

    def dispose(self):
        self._timer.stop()
        if self._mixer:
            self._mixer.close()
            self._mixer = None

    @property
    def export_running(self):
        return self._export_thread is not None

    def _choose_export_directory(self, _checked=False, result=None):
        if self.export_running or self._pitch_busy:
            return
        dialog = ExportDialog(result or self.result, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        thread = QThread(self)
        worker = ExportWorker(dialog.selected_result(), Path(dialog.destination.text()), dialog.options())
        worker.moveToThread(thread)
        worker.exported.connect(self._export_succeeded)
        worker.failed.connect(self._export_failed)
        worker.progress.connect(lambda value: self.export_status.setText(f"Exportando · {value}%"))
        worker.done.connect(thread.quit)
        worker.done.connect(worker.deleteLater)
        thread.started.connect(worker.run)
        thread.finished.connect(self._export_finished)
        thread.finished.connect(thread.deleteLater)
        self._export_thread = thread
        self._export_worker = worker
        self.export_button.setEnabled(False)
        self.export_button.setText("Exportando…")
        self.apply_pitch_button.setEnabled(False)
        thread.start()

    def _export_succeeded(self, path):
        self.export_status.setText("Exportación lista")
        QMessageBox.information(self, "Exportación lista", f"Stems exportados en:\n{path}")

    def _export_failed(self, message):
        self.export_status.setText("No se pudo exportar")
        QMessageBox.warning(self, "No se pudieron exportar los stems", message)

    def _export_finished(self):
        self._export_thread = None
        self._export_worker = None
        self.export_button.setEnabled(not self._pitch_busy)
        self.export_button.setText("↓ Exportar stems")
        self.apply_pitch_button.setEnabled(not self._pitch_busy)

    def reload_audio(self):
        saved = {}
        position = 0
        if self._mixer:
            position = self._mixer.position
            for row, track in zip(self.track_rows, self._mixer.tracks):
                saved[row.kind] = (track.gain, track.muted, track.solo, track.pan)
            self._mixer.close()
        self._timer.stop()
        self.play_button.setText("▶")
        self.play_button.setAccessibleName("Reproducir")
        while self.track_container.count():
            item = self.track_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._rows.clear()
        self.track_rows.clear()
        from vocal_splitter.ui.audio_widgets import TRACK_NAMES
        try:
            self._mixer = RealtimeMixer.from_files([(TRACK_NAMES[s.kind], s.path) for s in self.result.stems])
        except (OSError, RuntimeError, ValueError) as error:
            self._mixer = None
            self.play_button.setEnabled(False)
            self.export_status.setText("No se pudo cargar el audio")
            QMessageBox.warning(self, "No se pudo cargar el mezclador", str(error))
            return
        self.stem_count.setText(f"{len(self.result.stems)} stems")
        self.ruler.duration = self.result.stems[0].duration_seconds
        self.ruler.update()
        for index, stem in enumerate(self.result.stems):
            row = TrackRow(stem, index)
            row.gain_changed.connect(lambda value, i=index: self._mixer and self._mixer.set_controls(i, gain=value))
            row.pan_changed.connect(lambda value, i=index: self._mixer and self._mixer.set_controls(i, pan=value))
            row.muted_changed.connect(lambda value, i=index: self._mixer and self._mixer.set_controls(i, muted=value))
            row.solo_changed.connect(lambda value, i=index: self._mixer and self._mixer.set_controls(i, solo=value))
            row.muted_changed.connect(self._refresh_mix_status)
            row.solo_changed.connect(self._refresh_mix_status)
            row.seek_requested.connect(self._seek)
            row.export_requested.connect(lambda s=stem: self._choose_export_directory(result=SeparationResult((s,))))
            if stem.kind in saved:
                gain, muted, solo, pan = saved[stem.kind]
                row.gain.setValue(round(gain * 100))
                row.mute.setChecked(muted)
                row.solo.setChecked(solo)
                row.pan.setValue(round(pan * 100))
            self._rows.append((row.waveform, row.gain, row.mute, row.solo, row.gain_label))
            self.track_rows.append(row)
            self.track_container.addWidget(row)
        self._mixer.set_master_gain(self.master_gain.value() / 100)
        self._mixer.seek(position)
        self._refresh_mix_status()
        self._update_playhead()

    def _refresh_mix_status(self, _value=False):
        if not self._mixer:
            return
        solo = any(track.solo for track in self._mixer.tracks)
        muted = sum(track.muted for track in self._mixer.tracks)
        muted_text = f"{muted} pista{'s' if muted != 1 else ''} silenciada{'s' if muted != 1 else ''}"
        self.mix_status.setText("Solo activo" if solo else muted_text if muted else "Todas las pistas activas")
        for row, track in zip(self.track_rows, self._mixer.tracks):
            row.waveform.set_dimmed(track.muted or (solo and not track.solo))

    def _toggle_playback(self):
        if not self._mixer or self._pitch_busy:
            return
        try:
            stream = self._mixer._stream
            if stream is not None and stream.active:
                self._mixer.pause()
                self._timer.stop()
                self.play_button.setText("▶")
                self.play_button.setAccessibleName("Reproducir")
                self._clear_meters()
            else:
                if self._mixer.position >= self._mixer.frame_count:
                    self._mixer.seek(0)
                self._mixer.start()
                self._timer.start()
                self.play_button.setText("Ⅱ")
                self.play_button.setAccessibleName("Pausar")
        except (RuntimeError, OSError) as error:
            QMessageBox.warning(self, "No se pudo reproducir", str(error))

    def stop(self):
        if self._mixer:
            self._mixer.pause()
        self._timer.stop()
        self.play_button.setText("▶")
        self.play_button.setAccessibleName("Reproducir")
        self._seek(0)
        self._clear_meters()

    def _clear_meters(self):
        for row in self.track_rows:
            row.set_level(0)
        self.master_meter.set_levels(0)

    def _seek(self, ratio):
        if self._mixer:
            self._mixer.seek(round(ratio * self._mixer.frame_count))
            self._update_playhead()

    def _update_playhead(self):
        if not self._mixer:
            return
        duration = max(1, self._mixer.frame_count)
        position = self._mixer.position
        for waveform, *_ in self._rows:
            waveform.set_playhead(position / duration)
        self.position_label.setText(f"{time_text(position / self._mixer.sample_rate)} / {time_text(duration / self._mixer.sample_rate)}")
        if self._timer.isActive():
            levels, master = self._mixer.meter_levels()
            for row, level in zip(self.track_rows, levels):
                row.set_level(level)
            self.master_meter.set_levels(*master)
        if position >= duration:
            self._timer.stop()
            self.play_button.setText("▶")
            self.play_button.setAccessibleName("Reproducir")
            self._clear_meters()

    def set_pitch_busy(self, busy):
        self._pitch_busy = busy
        if busy:
            if self._mixer:
                self._mixer.pause()
            self._timer.stop()
            self.play_button.setText("▶")
            self.play_button.setAccessibleName("Reproducir")
            self._clear_meters()
            self.set_pitch_progress(0)
        else:
            self.pitch_status.setText("Tempo original")
            self.apply_pitch_button.setText("Aplicar pitch")
        for control in (self.pitch, self.pitch_slider, self.formants, self.play_button, *self.pitch_steps):
            control.setEnabled(not busy)
        self.apply_pitch_button.setEnabled(not busy and not self.export_running)
        self.export_button.setEnabled(not busy and not self.export_running)

    def set_pitch_progress(self, value):
        self.pitch_progress.setValue(value)
        self.pitch_status.setText(f"Procesando · {value}%")
        self.apply_pitch_button.setText(f"Aplicando… {value}%")

    @staticmethod
    def _time(seconds):
        return time_text(seconds)

    def closeEvent(self, event):
        self.dispose()
        super().closeEvent(event)
