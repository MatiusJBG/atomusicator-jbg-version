"""Arranque de la aplicación de escritorio."""

import sys

from PySide6.QtWidgets import QApplication

from vocal_splitter.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Separador Vocal")
    app.setOrganizationName("Separador Vocal")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
