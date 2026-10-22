"""Mezclador de stems con formas de onda y transporte sincronizado."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QSlider,
    QSpinBox, QVBoxLayout, QWidget,
)

from vocal_splitter.domain.separation_result import SeparationResult
from vocal_splitter.domain.stem import StemKind
from vocal_splitter.infrastructure.audio.pitch_processor import PitchProcessingError
from vocal_splitter.infrastructure.audio.realtime_mixer import RealtimeMixer


_NAMES = {
    StemKind.LEAD_VOCAL: "Voz principal",
    StemKind.BACKING_VOCALS: "Coros",
    StemKind.INSTRUMENTAL: "Acompañamiento",
    StemKind.VOCAL_MIX: "Voces (total)",
}


class Waveform(QWidget):
    seek_requested = Signal(float)

    def __init__(self, path: Path) -> None:
        super().__init__()
        self.setMinimumHeight(68)
        self.setMinimumWidth(220)
        self._peaks = self._read_peaks(path)
        self._playhead = 0.0

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
            step = max(1, self.width() // len(self._peaks))
            painter.setPen(QPen(QColor("#13bfd2"), 1))
            for index, peak in enumerate(self._peaks):
                amplitude = max(1.0, peak * (self.height() * 0.46))
                x = index * self.width() / len(self._peaks)
                painter.drawLine(int(x), int(mid - amplitude), int(x), int(mid + amplitude))
        x = int(self._playhead * self.width())
        painter.setPen(QPen(QColor("#ff8b6a"), 2))
        painter.drawLine(x, 0, x, self.height())

    def mousePressEvent(self, event: object) -> None:
        if self.width() > 0:
            self.seek_requested.emit(max(0.0, min(1.0, event.position().x() / self.width())))


class AudioWorkbench(QWidget):
    pitch_requested = Signal(int)

    def __init__(self, result: SeparationResult, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.result = result
        self._mixer: RealtimeMixer | None = None
        self._rows: list[tuple[Waveform, QSlider, QPushButton, QPushButton]] = []
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._update_playhead)
        self._build()
        self.reload_audio()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        title = QLabel("Mezclador de stems")
        title.setStyleSheet("font-size: 18px; font-weight: 650; color: #edf3f5")
        root.addWidget(title)
        self.track_container = QVBoxLayout()
        self.track_container.setSpacing(8)
        root.addLayout(self.track_container)
        controls = QHBoxLayout()
        self.play_button = QPushButton("▶ Reproducir")
        self.play_button.clicked.connect(self._toggle_playback)
        controls.addWidget(self.play_button)
        controls.addWidget(QLabel("Tonalidad"))
        self.pitch = QSpinBox()
        self.pitch.setRange(-12, 12)
        self.pitch.setSuffix(" semitonos")
        controls.addWidget(self.pitch)
        self.apply_pitch_button = QPushButton("Aplicar pitch")
        self.apply_pitch_button.clicked.connect(lambda: self.pitch_requested.emit(self.pitch.value()))
        controls.addWidget(self.apply_pitch_button)
        controls.addStretch(1)
        root.addLayout(controls)
        self.position_label = QLabel("00:00 / 00:00")
        root.addWidget(self.position_label)

    def set_result(self, result: SeparationResult) -> None:
        self.result = result
        self.reload_audio()

    def dispose(self) -> None:
        self._timer.stop()
        if self._mixer:
            self._mixer.close()
            self._mixer = None

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
        for index, stem in enumerate(stems):
            row = QFrame()
            row.setStyleSheet("QFrame { background: #0b1219; border-radius: 5px; }")
            layout = QHBoxLayout(row)
            layout.setContentsMargins(8, 5, 8, 5)
            name = QLabel(_NAMES[stem.kind])
            name.setMinimumWidth(120)
            layout.addWidget(name)
            waveform = Waveform(stem.path)
            waveform.seek_requested.connect(self._seek)
            layout.addWidget(waveform, 1)
            gain = QSlider(Qt.Orientation.Horizontal)
            gain.setRange(0, 150)
            gain.setValue(100)
            gain.setMaximumWidth(120)
            gain.valueChanged.connect(lambda value, i=index: self._mixer and self._mixer.set_controls(i, gain=value / 100))
            layout.addWidget(gain)
            mute = QPushButton("M")
            mute.setCheckable(True)
            mute.setMaximumWidth(34)
            mute.toggled.connect(lambda value, i=index: self._mixer and self._mixer.set_controls(i, muted=value))
            solo = QPushButton("S")
            solo.setCheckable(True)
            solo.setMaximumWidth(34)
            solo.toggled.connect(lambda value, i=index: self._mixer and self._mixer.set_controls(i, solo=value))
            layout.addWidget(mute)
            layout.addWidget(solo)
            self._rows.append((waveform, gain, mute, solo))
            self.track_container.addWidget(row)

    def _toggle_playback(self) -> None:
        if not self._mixer:
            return
        try:
            stream = getattr(self._mixer, "_stream", None)
            if stream is not None and stream.active:
                self._mixer.pause()
                self._timer.stop()
                self.play_button.setText("▶ Reproducir")
            else:
                if self._mixer.position >= self._mixer.frame_count:
                    self._mixer.seek(0)
                self._mixer.start()
                self._timer.start()
                self.play_button.setText("❚❚ Pausar")
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
        for waveform, _, _, _ in self._rows:
            waveform.set_playhead(ratio)
        current_seconds = position / self._mixer.sample_rate
        total_seconds = duration / self._mixer.sample_rate
        self.position_label.setText(f"{self._time(current_seconds)} / {self._time(total_seconds)}")
        if position >= duration:
            self._timer.stop()
            self.play_button.setText("▶ Reproducir")

    @staticmethod
    def _time(seconds: float) -> str:
        whole = int(seconds)
        return f"{whole // 60:02}:{whole % 60:02}"

    def closeEvent(self, event: object) -> None:
        self.dispose()
        super().closeEvent(event)

