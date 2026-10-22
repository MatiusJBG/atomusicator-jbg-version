"""Mezclador de stems con formas de onda y transporte sincronizado."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf
from PySide6.QtCore import QThread, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QScrollArea,
    QSlider, QSpinBox, QVBoxLayout, QWidget,
)

from vocal_splitter.domain.separation_result import SeparationResult
from vocal_splitter.domain.stem import StemKind
from vocal_splitter.infrastructure.audio.realtime_mixer import RealtimeMixer
from vocal_splitter.ui.export_worker import ExportWorker


_NAMES = {
    StemKind.LEAD_VOCAL: "Voz principal",
    StemKind.BACKING_VOCALS: "Coros",
    StemKind.DRUMS: "Batería",
    StemKind.BASS: "Bajo",
    StemKind.INSTRUMENTAL: "Instrumental",
    StemKind.VOCAL_MIX: "Voces (total)",
}

_TRACK_COLORS = {
    StemKind.LEAD_VOCAL: "#55cfc0",
    StemKind.BACKING_VOCALS: "#a895e8",
    StemKind.DRUMS: "#e5b35b",
    StemKind.BASS: "#75b9e4",
    StemKind.INSTRUMENTAL: "#a7b9ae",
    StemKind.VOCAL_MIX: "#9baab0",
}


class Waveform(QWidget):
    seek_requested = Signal(float)

    def __init__(self, path: Path, color: str = "#55cfc0") -> None:
        super().__init__()
        self.setMinimumHeight(48)
        self.setMinimumWidth(220)
        self._peaks = self._read_peaks(path)
        self._playhead = 0.0
        self._color = QColor(color)

    @staticmethod
    def _read_peaks(path: Path) -> np.ndarray:
        info = sf.info(path)
        with sf.SoundFile(path) as audio:
            blocks = max(1, min(1600, info.frames // 256))
            window = max(1, info.frames // blocks)
            peaks = np.zeros(blocks, dtype=np.float32)
            for index in range(blocks):
                chunk = audio.read(window, dtype="float32", always_2d=True)
                if len(chunk):
                    peaks[index] = np.max(np.abs(chunk))
        return peaks

    def set_playhead(self, value: float) -> None:
        self._playhead = max(0.0, min(1.0, value))
        self.update()

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#101923"))
        if len(self._peaks):
            mid = self.height() / 2
            painter.setPen(QPen(self._color, 1))
            for index, peak in enumerate(self._peaks):
                amplitude = max(1.0, peak * (self.height() * 0.46))
                x = index * self.width() / len(self._peaks)
                painter.drawLine(int(x), int(mid - amplitude), int(x), int(mid + amplitude))
        x = int(self._playhead * self.width())
        painter.setPen(QPen(QColor("#ff8b6a"), 2))
        painter.drawLine(x, 0, x, self.height())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.width() > 0:
            self.seek_requested.emit(max(0.0, min(1.0, event.position().x() / self.width())))


class AudioWorkbench(QWidget):
    pitch_requested = Signal(int)

    def __init__(self, result: SeparationResult, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("audioWorkbench")
        self.result = result
        self._mixer: RealtimeMixer | None = None
        self._rows: list[tuple[Waveform, QSlider, QPushButton, QPushButton, QLabel]] = []
        self._export_thread: QThread | None = None
        self._export_worker: ExportWorker | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._update_playhead)
        self._build()
        self.reload_audio()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 12, 0, 0)
        root.setSpacing(12)
        heading = QHBoxLayout()
        title_stack = QVBoxLayout()
        title = QLabel("Mezclador de stems")
        title.setObjectName("workbenchTitle")
        helper = QLabel("Ajusta cada pista en tiempo real. Las cinco comparten el mismo cursor.")
        helper.setObjectName("workbenchHint")
        title_stack.addWidget(title)
        title_stack.addWidget(helper)
        heading.addLayout(title_stack)
        heading.addStretch(1)
        self.stem_count = QLabel("5 PISTAS")
        self.stem_count.setObjectName("stemCount")
        heading.addWidget(self.stem_count, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(heading)

        track_scroll = QScrollArea()
        track_scroll.setObjectName("trackScroll")
        track_scroll.setWidgetResizable(True)
        track_scroll.setFrameShape(QFrame.Shape.NoFrame)
        track_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        track_content = QWidget()
        track_content.setObjectName("trackContent")
        self.track_container = QVBoxLayout(track_content)
        self.track_container.setContentsMargins(1, 1, 8, 1)
        self.track_container.setSpacing(8)
        track_scroll.setWidget(track_content)
        root.addWidget(track_scroll, 1)

        transport = QFrame()
        transport.setObjectName("transportPanel")
        controls = QHBoxLayout(transport)
        controls.setContentsMargins(14, 10, 14, 10)
        self.play_button = QPushButton("▶")
        self.play_button.setObjectName("playButton")
        self.play_button.setAccessibleName("Reproducir")
        self.play_button.setFixedSize(46, 42)
        self.play_button.clicked.connect(self._toggle_playback)
        controls.addWidget(self.play_button)
        self.position_label = QLabel("00:00 / 00:00")
        self.position_label.setObjectName("transportTime")
        controls.addWidget(self.position_label)
        controls.addStretch(1)
        pitch_label = QLabel("PITCH")
        pitch_label.setObjectName("controlEyebrow")
        controls.addWidget(pitch_label)
        self.pitch = QSpinBox()
        self.pitch.setRange(-12, 12)
        self.pitch.setSuffix(" st")
        self.pitch.setToolTip("Cambiar tonalidad sin alterar el tempo")
        self.pitch.setFixedWidth(82)
        controls.addWidget(self.pitch)
        self.apply_pitch_button = QPushButton("Aplicar pitch")
        self.apply_pitch_button.setObjectName("secondaryButton")
        self.apply_pitch_button.clicked.connect(lambda: self.pitch_requested.emit(self.pitch.value()))
        controls.addWidget(self.apply_pitch_button)
        self.export_button = QPushButton("Exportar stems")
        self.export_button.setObjectName("primaryButton")
        self.export_button.clicked.connect(self._choose_export_directory)
        controls.addWidget(self.export_button)
        root.addWidget(transport)

    def set_result(self, result: SeparationResult) -> None:
        self.result = result
        self.reload_audio()

    def dispose(self) -> None:
        self._timer.stop()
        if self._mixer:
            self._mixer.close()
            self._mixer = None

    @property
    def export_running(self) -> bool:
        return self._export_thread is not None

    def _choose_export_directory(self) -> None:
        destination = QFileDialog.getExistingDirectory(self, "Exportar stems", str(Path.home()))
        if not destination or self._export_thread is not None:
            return
        thread = QThread(self)
        worker = ExportWorker(self.result, Path(destination))
        worker.moveToThread(thread)
        worker.exported.connect(self._export_succeeded)
        worker.failed.connect(self._export_failed)
        worker.done.connect(thread.quit)
        worker.done.connect(worker.deleteLater)
        thread.started.connect(worker.run)
        thread.finished.connect(self._export_finished)
        thread.finished.connect(thread.deleteLater)
        self._export_thread = thread
        self._export_worker = worker
        self.export_button.setEnabled(False)
        self.export_button.setText("Exportando…")
        thread.start()

    def _export_succeeded(self, path: str) -> None:
        QMessageBox.information(self, "Exportación lista", f"Stems exportados en:\n{path}")

    def _export_failed(self, message: str) -> None:
        QMessageBox.warning(self, "No se pudieron exportar los stems", message)

    def _export_finished(self) -> None:
        self._export_thread = None
        self._export_worker = None
        self.export_button.setEnabled(True)
        self.export_button.setText("Exportar stems")

    def reload_audio(self) -> None:
        if self._mixer:
            self._mixer.close()
        while self.track_container.count():
            item = self.track_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._rows.clear()
        stems = [s for s in self.result.stems if s.kind in _NAMES]
        try:
            self._mixer = RealtimeMixer.from_files([(_NAMES[s.kind], s.path) for s in stems])
        except (OSError, RuntimeError, ValueError) as error:
            self._mixer = None
            QMessageBox.warning(self, "No se pudo cargar el mezclador", str(error))
            return
        self.stem_count.setText(f"{len(stems)} PISTAS")
        for index, stem in enumerate(stems):
            row = QFrame()
            row.setObjectName("trackRow")
            layout = QHBoxLayout(row)
            layout.setContentsMargins(12, 6, 12, 6)
            layout.setSpacing(10)
            color = _TRACK_COLORS[stem.kind]
            marker = QFrame()
            marker.setObjectName("trackMarker")
            marker.setFixedSize(4, 32)
            marker.setStyleSheet(f"background: {color}; border-radius: 2px;")
            layout.addWidget(marker)
            label_column = QVBoxLayout()
            label_column.setSpacing(3)
            name = QLabel(_NAMES[stem.kind])
            name.setObjectName("trackTitle")
            name.setMinimumWidth(120)
            ordinal = QLabel(f"PISTA {index + 1:02d}")
            ordinal.setObjectName("trackOrdinal")
            label_column.addWidget(name)
            label_column.addWidget(ordinal)
            layout.addLayout(label_column)
            waveform = Waveform(stem.path, _TRACK_COLORS[stem.kind])
            waveform.setObjectName("waveform")
            waveform.seek_requested.connect(self._seek)
            layout.addWidget(waveform, 1)
            gain = QSlider(Qt.Orientation.Horizontal)
            gain.setRange(0, 150)
            gain.setValue(100)
            gain.setMaximumWidth(112)
            gain.setToolTip("Volumen de esta pista")
            gain.valueChanged.connect(lambda value, i=index: self._mixer and self._mixer.set_controls(i, gain=value / 100))
            layout.addWidget(gain)
            gain_label = QLabel("100 %")
            gain_label.setObjectName("gainValue")
            gain_label.setMinimumWidth(42)
            gain.valueChanged.connect(lambda value, label=gain_label: label.setText(f"{value} %"))
            layout.addWidget(gain_label)
            mute = QPushButton("M")
            mute.setObjectName("trackToggle")
            mute.setToolTip(f"Silenciar {_NAMES[stem.kind]}")
            mute.setCheckable(True)
            mute.setMaximumWidth(34)
            mute.toggled.connect(lambda value, i=index: self._mixer and self._mixer.set_controls(i, muted=value))
            solo = QPushButton("S")
            solo.setObjectName("trackToggle")
            solo.setToolTip(f"Solo {_NAMES[stem.kind]}")
            solo.setCheckable(True)
            solo.setMaximumWidth(34)
            solo.toggled.connect(lambda value, i=index: self._mixer and self._mixer.set_controls(i, solo=value))
            layout.addWidget(mute)
            layout.addWidget(solo)
            self._rows.append((waveform, gain, mute, solo, gain_label))
            self.track_container.addWidget(row)

    def _toggle_playback(self) -> None:
        if not self._mixer:
            return
        try:
            stream = getattr(self._mixer, "_stream", None)
            if stream is not None and stream.active:
                self._mixer.pause()
                self._timer.stop()
                self.play_button.setText("▶")
                self.play_button.setAccessibleName("Reproducir")
            else:
                if self._mixer.position >= self._mixer.frame_count:
                    self._mixer.seek(0)
                self._mixer.start()
                self._timer.start()
                self.play_button.setText("Ⅱ")
                self.play_button.setAccessibleName("Pausar")
        except (RuntimeError, OSError) as error:
            QMessageBox.warning(self, "No se pudo reproducir", str(error))

    def _seek(self, ratio: float) -> None:
        if self._mixer is not None:
            self._mixer.seek(round(ratio * self._mixer.frame_count))
            self._update_playhead()

    def _update_playhead(self) -> None:
        if not self._mixer:
            return
        position = self._mixer.position
        duration = max(1, self._mixer.frame_count)
        ratio = position / duration
        for waveform, _, _, _, _ in self._rows:
            waveform.set_playhead(ratio)
        current_seconds = position / self._mixer.sample_rate
        total_seconds = duration / self._mixer.sample_rate
        self.position_label.setText(f"{self._time(current_seconds)} / {self._time(total_seconds)}")
        if position >= duration:
            self._timer.stop()
            self.play_button.setText("▶")
            self.play_button.setAccessibleName("Reproducir")

    @staticmethod
    def _time(seconds: float) -> str:
        whole = int(seconds)
        return f"{whole // 60:02}:{whole % 60:02}"

    def closeEvent(self, event: object) -> None:
        self.dispose()
        super().closeEvent(event)

