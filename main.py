"""
Teams-v2: A lightweight, cross-platform voice/video/text chat application.
Entry point — launches the Welcome/Setup window.
"""

import sys
from PyQt6.QtWidgets import QApplication
from ui.welcome_window import WelcomeWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Teams-v2")
    app.setStyle("Fusion")

    window = WelcomeWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
