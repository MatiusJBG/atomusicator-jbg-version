"""Un carril del mezclador: controles, medidor y forma de onda."""

import math
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QSlider, QVBoxLayout, QWidget
from vocal_splitter.ui.audio_widgets import TRACK_COLORS, TRACK_NAMES, LevelMeter, PanDial, Waveform, label


class TrackRow(QFrame):
    gain_changed = Signal(float)
    pan_changed = Signal(float)
    muted_changed = Signal(bool)
    solo_changed = Signal(bool)
    seek_requested = Signal(float)
    export_requested = Signal()

    def __init__(self, stem, index):
        super().__init__()
        self.setObjectName("trackRow")
        self.setFixedHeight(94)
        self.kind = stem.kind
        color = TRACK_COLORS[stem.kind]
        name = TRACK_NAMES[stem.kind]
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        controls = QWidget()
        controls.setFixedWidth(300)
        column = QVBoxLayout(controls)
        column.setContentsMargins(12, 8, 12, 7)
        column.setSpacing(5)
        heading = QHBoxLayout()
        heading.addWidget(label(f"{index + 1:02d}", "trackOrdinal"))
        symbol = label("◉", "trackTitle")
        symbol.setStyleSheet(f"color: {color}; font-size: 17px;")
        heading.addWidget(symbol)
        heading.addWidget(label(name, "trackTitle"), 1)
        save = QPushButton("▣")
        save.setObjectName("transportButton")
        save.setFixedSize(22, 22)
        save.setToolTip(f"Exportar {name}")
        save.setAccessibleName(f"Exportar {name}")
        save.clicked.connect(self.export_requested)
        heading.addWidget(save)
        column.addLayout(heading)
        mix = QHBoxLayout()
        mix.setSpacing(5)
        self.mute = self._toggle("M", f"Silenciar {name}")
        self.solo = self._toggle("S", f"Solo {name}")
        self.mute.toggled.connect(self.muted_changed)
        self.solo.toggled.connect(self.solo_changed)
        mix.addWidget(self.mute)
        mix.addWidget(self.solo)
        self.pan = PanDial()
        self.pan.setRange(-100, 100)
        self.pan.setValue(0)
        self.pan.setFixedSize(28, 28)
        self.pan.setAccessibleName(f"Panorama de {name}")
        self.pan.setToolTip("Panorama: izquierda / centro / derecha")
        self.pan.valueChanged.connect(lambda value: self.pan_changed.emit(value / 100))
        mix.addWidget(self.pan)
        self.gain = QSlider(Qt.Orientation.Horizontal)
        self.gain.setRange(0, 150)
        self.gain.setValue(100)
        self.gain.setAccessibleName(f"Volumen de {name}")
        self.gain.setToolTip("Volumen de pista")
        self.gain.setStyleSheet(f"QSlider::sub-page:horizontal {{ background: {color}; }}")
        self.gain.valueChanged.connect(lambda value: self.gain_changed.emit(value / 100))
        mix.addWidget(self.gain, 1)
        self.meter = LevelMeter()
        self.meter.setFixedWidth(58)
        mix.addWidget(self.meter)
        column.addLayout(mix)
        details = QHBoxLayout()
        self.pan_label = label("L · C · R", "gainValue")
        details.addSpacing(59)
        details.addWidget(self.pan_label)
        self.gain_label = label("0.0 dB", "gainValue")
        details.addWidget(self.gain_label, 1, Qt.AlignmentFlag.AlignCenter)
        self.level_label = label("−∞", "gainValue")
        self.level_label.setFixedWidth(58)
        details.addWidget(self.level_label)
        column.addLayout(details)
        layout.addWidget(controls)
        self.waveform = Waveform(stem.path, color)
        self.waveform.seek_requested.connect(self.seek_requested)
        layout.addWidget(self.waveform, 1)
        self.gain.valueChanged.connect(self._gain_label)
        self.pan.valueChanged.connect(self._pan_label)

    def _toggle(self, text, name):
        button = QPushButton(text)
        button.setCheckable(True)
        button.setObjectName("trackToggle")
        button.setFixedSize(25, 25)
        button.setAccessibleName(name)
        button.setToolTip(name)
        return button

    def _gain_label(self, value):
        self.gain_label.setText("−∞ dB" if value == 0 else f"{20 * math.log10(value / 100):+.1f} dB")

    def _pan_label(self, value):
        self.pan_label.setText("L · C · R" if value == 0 else f"L · {abs(value)}{'L' if value < 0 else 'R'} · R")

    def set_level(self, value):
        self.meter.set_levels(value)
        self.level_label.setText("−∞" if value < .0001 else f"{20 * math.log10(value):.1f}")
