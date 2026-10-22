"""Diálogo para elegir la carpeta local de proyectos."""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from vocal_splitter.application.project_settings import ProjectSettings


class SettingsDialog(QDialog):
    def __init__(self, settings: ProjectSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Carpeta de proyectos")
        self.setMinimumWidth(520)

        self._directory = QLineEdit(str(settings.projects_directory))
        self._directory.setAccessibleName("Carpeta de proyectos")
        browse_button = QPushButton("Elegir…")
        browse_button.clicked.connect(self._browse)

        row = QHBoxLayout()
        row.addWidget(self._directory, 1)
        row.addWidget(browse_button)

        heading = QLabel("Dónde guardar las sesiones")
        heading.setStyleSheet("font-size: 20px; font-weight: 650; color: #edf3f5;")
        description = QLabel(
            "El archivo de audio original queda en su ubicación. "
            "Esta carpeta guarda las sesiones y las pistas que se generen."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #a9bbc4;")

        save_button = QPushButton("Guardar ubicación")
        save_button.setDefault(True)
        cancel_button = QPushButton("Cancelar")
        save_button.clicked.connect(self._accept_if_valid)
        cancel_button.clicked.connect(self.reject)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(cancel_button)
        actions.addWidget(save_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)
        layout.addWidget(heading)
        layout.addWidget(description)
        layout.addLayout(row)
        layout.addLayout(actions)

    def project_settings(self) -> ProjectSettings:
        return ProjectSettings(projects_directory=Path(self._directory.text()).expanduser())

    def _browse(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Elegir carpeta de proyectos",
            self._directory.text(),
        )
        if selected:
            self._directory.setText(selected)

    def _accept_if_valid(self) -> None:
        if not self._directory.text().strip():
            QMessageBox.warning(self, "Carpeta requerida", "Escribe o elige una carpeta.")
            return
        self.accept()
