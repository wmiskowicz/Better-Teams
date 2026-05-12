from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QTextEdit, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont



class VideoDisplay(QFrame):
    """Represents the large blue display area with control buttons."""
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #D0E0FF; border-radius: 15px; border: 1px solid #A0A0A0;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Central Label
        display_label = QLabel("DISPLAY")
        display_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        display_label.setStyleSheet("color: #4070C0; border: none;")
        display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        

        layout.addStretch()
        layout.addWidget(display_label)
        layout.addStretch()
        self.setLayout(layout)
