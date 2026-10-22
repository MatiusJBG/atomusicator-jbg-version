"""Diálogo de exportación de stems inspirado en el prototipo Figma."""

from pathlib import Path

from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QDialog, QFileDialog,
    QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout,
)

from vocal_splitter.application.export_options import ExportOptions
from vocal_splitter.domain.separation_result import SeparationResult
from vocal_splitter.ui.audio_widgets import CheckBox, TRACK_NAMES, label


class ExportDialog(QDialog):
    def __init__(self, result: SeparationResult, parent=None):
        super().__init__(parent)
        self.result = result
        self.setWindowTitle("Exportar stems")
        self.setMinimumWidth(600)
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 24, 26, 24)
        root.setSpacing(18)
        root.addWidget(label("Exportar stems", "sectionTitle"))
        root.addWidget(label("Lleva tus pistas a tu DAW. Los originales se conservan."))
        root.addWidget(label("Formato de audio", "controlEyebrow"))
        formats = QHBoxLayout()
        self.formats = QButtonGroup(self)
        for index, (name, detail) in enumerate((("WAV", "Sin compresión"),
                                              ("FLAC", "Sin pérdida"), ("MP3", "320 kbps"))):
            button = QPushButton(f"{name}\n{detail}")
            button.setObjectName("formatCard")
            button.setCheckable(True)
            button.setAccessibleName(name)
            self.formats.addButton(button, index)
            formats.addWidget(button)
        self.formats.button(0).setChecked(True)
        self.formats.idClicked.connect(self._format_changed)
        root.addLayout(formats)
        specs = QHBoxLayout()
        self.rate = self._combo(specs, "Frecuencia de muestreo", ["44.1 kHz", "48 kHz"])
        self.rate.setCurrentIndex(1)
        self.depth = self._combo(specs, "Profundidad de bits", ["16 bits", "24 bits"])
        self.depth.setCurrentIndex(1)
        self.channels = self._combo(specs, "Canales", ["Estéreo", "Mono"])
        root.addLayout(specs)
        root.addWidget(label("Stems para exportar", "controlEyebrow"))
        stems = QHBoxLayout()
        self.selected = []
        for stem in result.stems:
            check = CheckBox(TRACK_NAMES[stem.kind])
            check.setChecked(True)
            check.toggled.connect(self._selection_changed)
            self.selected.append((stem, check))
            stems.addWidget(check)
        root.addLayout(stems)
        self.normalize = CheckBox("Normalizar sonoridad (−16 LUFS, pico máximo −1 dBTP)")
        self.normalize.setToolTip("Ajusta la sonoridad de cada archivo con FFmpeg; no modifica los originales.")
        root.addWidget(self.normalize)
        root.addWidget(label("Guardar en", "controlEyebrow"))
        destination = QHBoxLayout()
        self.destination = QLineEdit(str(Path.home() / "Music" if (Path.home() / "Music").is_dir() else Path.home()))
        self.destination.setReadOnly(True)
        self.destination.setAccessibleName("Carpeta de exportación")
        destination.addWidget(self.destination, 1)
        browse = QPushButton("Cambiar…")
        browse.clicked.connect(self._browse)
        destination.addWidget(browse)
        root.addLayout(destination)
        root.addWidget(label("Se creará una carpeta nueva para esta exportación."))
        footer = QHBoxLayout()
        self.summary = label("")
        footer.addWidget(self.summary, 1)
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(self.reject)
        footer.addWidget(cancel)
        self.export = QPushButton("Exportar stems")
        self.export.setObjectName("primaryButton")
        self.export.setDefault(True)
        self.export.clicked.connect(self.accept)
        footer.addWidget(self.export)
        root.addLayout(footer)
        self._selection_changed()

    def _combo(self, layout, title, items):
        column = QVBoxLayout()
        column.addWidget(label(title, "controlEyebrow"))
        combo = QComboBox()
        combo.addItems(items)
        combo.setAccessibleName(title)
        column.addWidget(combo)
        layout.addLayout(column)
        return combo

    def _format_changed(self, index):
        self.depth.setEnabled(index != 2)
        self.depth.setToolTip("MP3 usa compresión a 320 kbps" if index == 2 else "")

    def _selection_changed(self):
        count = sum(check.isChecked() for _, check in self.selected)
        self.export.setEnabled(count > 0)
        self.summary.setText(f"{count} pista{'s' if count != 1 else ''} seleccionada{'s' if count != 1 else ''}")

    def _browse(self):
        destination = QFileDialog.getExistingDirectory(self, "Carpeta de exportación", self.destination.text())
        if destination:
            self.destination.setText(destination)

    def selected_result(self):
        return SeparationResult(tuple(stem for stem, check in self.selected if check.isChecked()),
                                self.result.engine_usage)

    def options(self):
        return ExportOptions(format=("wav", "flac", "mp3")[self.formats.checkedId()],
                             sample_rate=(44100, 48000)[self.rate.currentIndex()],
                             bit_depth=(16, 24)[self.depth.currentIndex()],
                             channels=(2, 1)[self.channels.currentIndex()],
                             normalize=self.normalize.isChecked())
