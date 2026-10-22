"""Navegación lateral con iconos vectoriales dibujados por Qt."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QFrame, QToolButton, QVBoxLayout, QWidget
from vocal_splitter.ui.audio_widgets import label


def navigation_icon(kind: str) -> QIcon:
    pixmap = QPixmap(28, 28)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor("#91A7B5"), 1.5))
    if kind == "projects":
        painter.drawRoundedRect(4, 9, 20, 15, 2, 2)
        painter.drawLine(4, 9, 4, 5)
        painter.drawLine(4, 5, 12, 5)
        painter.drawLine(12, 5, 15, 9)
    elif kind == "mixer":
        for y, x in ((7, 10), (14, 18), (21, 9)):
            painter.drawLine(4, y, 24, y)
            painter.fillRect(x - 2, y - 3, 4, 6, QColor("#2DD4BF"))
    elif kind == "export":
        painter.drawLine(14, 3, 14, 19)
        painter.drawLine(8, 13, 14, 19)
        painter.drawLine(20, 13, 14, 19)
        painter.drawLine(5, 19, 5, 24)
        painter.drawLine(5, 24, 23, 24)
        painter.drawLine(23, 24, 23, 19)
    else:
        for y, x in ((7, 17), (14, 9), (21, 18)):
            painter.drawLine(4, y, 24, y)
            painter.drawEllipse(x - 3, y - 3, 6, 6)
    painter.end()
    return QIcon(pixmap)


class BrandMark(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(48, 48)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#123C38"))
        painter.drawRoundedRect(self.rect(), 12, 12)
        painter.setPen(QPen(QColor("#2DD4BF"), 2))
        for index, height in enumerate((9, 18, 25, 15, 9)):
            x = 14 + index * 5
            painter.drawLine(x, 24 - height // 2, x, 24 + height // 2)


class Sidebar(QFrame):
    projects_requested = Signal()
    mixer_requested = Signal()
    export_requested = Signal()
    settings_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(96)
        root = QVBoxLayout(self)
        root.setContentsMargins(7, 24, 7, 16)
        root.setSpacing(14)
        brand = BrandMark()
        root.addWidget(brand, 0, Qt.AlignmentFlag.AlignHCenter)
        root.addSpacing(14)
        self.projects = self._button("Proyectos", "projects", self.projects_requested)
        self.mixer = self._button("Mezclador DAW", "mixer", self.mixer_requested)
        self.export = self._button("Exportar", "export", self.export_requested, checkable=False)
        self.settings = self._button("Configuración", "settings", self.settings_requested, checkable=False)
        for button in (self.projects, self.mixer, self.export, self.settings):
            root.addWidget(button)
        root.addStretch(1)
        root.addWidget(label("●  Local", "accent"), 0, Qt.AlignmentFlag.AlignCenter)
        root.addWidget(label("v0.4.0", "gainValue"), 0, Qt.AlignmentFlag.AlignCenter)
        self.export.setEnabled(False)
        self.set_page("projects")

    def _button(self, text, icon, signal, checkable=True):
        button = QToolButton()
        button.setObjectName("navButton")
        button.setText(text)
        button.setIcon(navigation_icon(icon))
        button.setIconSize(QSize(24, 24))
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        button.setFixedSize(82, 74)
        button.setCheckable(checkable)
        button.setAccessibleName(text)
        button.clicked.connect(signal)
        return button

    def set_page(self, page):
        self.projects.setChecked(page == "projects")
        self.mixer.setChecked(page == "mixer")
