from gui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication
import sys

from gui.qss import GLOBAL_STYLE


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())