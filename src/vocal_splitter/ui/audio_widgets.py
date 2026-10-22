"""Componentes visuales de la línea de tiempo y los medidores de audio."""

from pathlib import Path
import math

import numpy as np
import soundfile as sf
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QCheckBox, QDial, QLabel, QStyle, QStyleOptionButton, QWidget

from vocal_splitter.domain.stem import StemKind


TRACK_NAMES = {
    StemKind.LEAD_VOCAL: "Voz principal", StemKind.BACKING_VOCALS: "Coros",
    StemKind.DRUMS: "Batería", StemKind.BASS: "Bajo",
    StemKind.INSTRUMENTAL: "Instrumental", StemKind.VOCAL_MIX: "Voces (total)",
}
TRACK_COLORS = {
    StemKind.LEAD_VOCAL: "#F34E7A", StemKind.BACKING_VOCALS: "#A66BEB",
    StemKind.DRUMS: "#F5B52E", StemKind.BASS: "#5794EF",
    StemKind.INSTRUMENTAL: "#2DD4AA", StemKind.VOCAL_MIX: "#8A9AA8",
}


def label(text: str, name: str = "muted") -> QLabel:
    widget = QLabel(text)
    widget.setObjectName(name)
    return widget


def time_text(seconds: float) -> str:
    whole = max(0, int(seconds))
    return f"{whole // 60:02}:{whole % 60:02}"


class CheckBox(QCheckBox):
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.isChecked():
            option = QStyleOptionButton()
            self.initStyleOption(option)
            rect = self.style().subElementRect(QStyle.SubElement.SE_CheckBoxIndicator, option, self)
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor("#07372F"), 1.8))
            painter.drawLine(rect.left() + 3, rect.center().y(), rect.left() + 6, rect.bottom() - 3)
            painter.drawLine(rect.left() + 6, rect.bottom() - 3, rect.right() - 2, rect.top() + 3)


class PanDial(QDial):
    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#10171F"))
        painter.setPen(QPen(QColor("#2DD4BF" if self.hasFocus() else "#718391"), 1.4))
        painter.drawEllipse(4, 4, self.width() - 8, self.height() - 8)
        angle = math.radians(-90 + self.value() * 1.35)
        center = self.rect().center()
        painter.drawLine(center.x(), center.y(), round(center.x() + math.cos(angle) * 8),
                         round(center.y() + math.sin(angle) * 8))


class LevelMeter(QWidget):
    def __init__(self, stereo: bool = False):
        super().__init__()
        self._levels = (0.0, 0.0)
        self.stereo = stereo
        self.setMinimumSize(56, 14 if stereo else 9)
        self.setAccessibleName("Nivel de salida" if stereo else "Nivel de pista")

    def set_levels(self, left: float, right: float | None = None):
        self._levels = (left, left if right is None else right)
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        count = 24
        rows = 2 if self.stereo else 1
        for row in range(rows):
            peak = self._levels[row]
            db = 20 * math.log10(max(peak, 0.0001))
            active = round(max(0, min(1, (db + 60) / 60)) * count)
            height = max(2, (self.height() - (rows - 1) * 3) // rows)
            for index in range(count):
                color = "#2DD4BF" if index < 18 else "#F5B52E" if index < 22 else "#F34E7A"
                painter.fillRect(round(index * self.width() / count), row * (height + 3),
                                 max(1, self.width() // count - 1), height,
                                 QColor(color if index < active else "#26333E"))


class TimelineRuler(QWidget):
    seek_requested = Signal(float)

    def __init__(self, duration: float):
        super().__init__()
        self.duration = duration
        self.setFixedHeight(30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Pulsa para buscar en la canción")

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#10171F"))
        painter.setPen(QColor("#8A9AA8"))
        steps = max(2, self.width() // 100)
        for index in range(steps + 1):
            x = round(index * (self.width() - 1) / steps)
            painter.drawLine(x, 22, x, 29)
            painter.drawText(min(x + 5, self.width() - 38), 15,
                             time_text(index * self.duration / steps))

    def mousePressEvent(self, event):
        self.seek_requested.emit(max(0, min(1, event.position().x() / max(1, self.width()))))


class Waveform(QWidget):
    seek_requested = Signal(float)

    def __init__(self, path: Path, color: str = "#2DD4BF"):
        super().__init__()
        self.setMinimumSize(220, 78)
        self._peaks = self._read_peaks(path)
        self._playhead = 0.0
        self._color = QColor(color)
        self._name = path.name
        self._dimmed = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Pulsa para buscar en esta posición")

    @staticmethod
    def _read_peaks(path: Path) -> np.ndarray:
        with sf.SoundFile(path) as audio:
            blocks = max(1, min(1600, audio.frames // 64))
            window = max(1, math.ceil(audio.frames / blocks))
            peaks = np.zeros((blocks, min(audio.channels, 2)), dtype=np.float32)
            for index in range(blocks):
                chunk = audio.read(window, dtype="float32", always_2d=True)
                if len(chunk):
                    peaks[index] = np.max(np.abs(chunk[:, :2]), axis=0)
        return peaks

    def set_playhead(self, value: float):
        self._playhead = max(0.0, min(1.0, value))
        self.update()

    def set_dimmed(self, dimmed: bool):
        self._dimmed = dimmed
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#0E141C"))
        tint = QColor(self._color)
        tint.setAlpha(12 if self._dimmed else 24)
        painter.fillRect(self.rect(), tint)
        painter.setPen(QColor("#25313D"))
        steps = max(2, self.width() // 100)
        for index in range(steps + 1):
            x = round(index * self.width() / steps)
            painter.drawLine(x, 0, x, self.height())
        color = QColor(self._color)
        color.setAlpha(50 if self._dimmed else 220)
        painter.setPen(QPen(color, 1))
        painter.drawText(8, 13, self._name)
        channels = self._peaks.shape[1]
        available = self.height() - 19
        for channel in range(channels):
            middle = 18 + (channel + 0.5) * available / channels
            for index, peak in enumerate(self._peaks[:, channel]):
                amplitude = max(0.5, float(peak) * available / channels * 0.46)
                x = int(index * self.width() / len(self._peaks))
                painter.drawLine(x, round(middle - amplitude), x, round(middle + amplitude))
        painter.setPen(QPen(self._color, 1))
        painter.drawLine(0, 0, self.width(), 0)
        painter.setPen(QPen(QColor("#F5B52E"), 1))
        x = round(self._playhead * (self.width() - 1))
        painter.drawLine(x, 0, x, self.height())

    def mousePressEvent(self, event):
        self.seek_requested.emit(max(0.0, min(1.0, event.position().x() / max(1, self.width()))))
