import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QMenuBar, QMenu, QTextEdit, 
                             QLineEdit, QPushButton, QFrame)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import pyqtSignal

class TopBar(QMenuBar):
    """Subclass for the top navigation menu."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # File Menu
        file_menu = self.addMenu("File")
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        file_menu.addAction(exit_action)

        # Settings Menu
        settings_menu = self.addMenu("Settings")
        preferences_action = QAction("Preferences", self)
        audio_action = QAction("Audio Settings", self)
        settings_menu.addAction(preferences_action)
        settings_menu.addAction(audio_action)