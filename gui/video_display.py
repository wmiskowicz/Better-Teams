from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtMultimediaWidgets import QVideoWidget

class VideoDisplay(QFrame):
    hideToggled = pyqtSignal(bool)
    muteToggled = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.setObjectName("VideoDisplay")
        self.init_ui()

    def init_ui(self):
        # Vertical layout for the main container
        self.main_layout = QVBoxLayout(self)
        
        # 1. Top Buttons
        top_button_layout = QHBoxLayout()
        top_button_layout.addStretch()
        
        self.hide_btn = QPushButton("Hide")
        self.mute_btn = QPushButton("Mute")
        self.hide_btn.setCheckable(True)
        self.mute_btn.setCheckable(True)
        
        self.hide_btn.clicked.connect(self.handle_hide_clicked)
        self.mute_btn.clicked.connect(self.handle_mute_clicked)
        
        top_button_layout.addWidget(self.hide_btn)
        top_button_layout.addWidget(self.mute_btn)
        
        # 2. The Video Widget
        # IMPORTANT: Do not set a background-color via QSS here, 
        # as it can interfere with the camera frame painting.
        self.video_surface = QVideoWidget()
        
        # 3. Placeholder Label (for when camera is off)
        self.display_label = QLabel("CAMERA OFF")
        self.display_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display_label.hide()
        
        # 4. Assembly
        self.main_layout.addLayout(top_button_layout)
        self.main_layout.addWidget(self.video_surface)
        self.main_layout.addWidget(self.display_label)
        
        # Ensure the video/label takes up all available space
        self.main_layout.setStretch(1, 1)

    def videoSink(self):
        """Standard method for QMediaCaptureSession to find the display surface."""
        return self.video_surface.videoSink()

    def handle_hide_clicked(self, checked):
        self.hide_btn.setText("Show" if checked else "Hide")
        if checked:
            self.video_surface.hide()
            self.display_label.show()
        else:
            self.display_label.hide()
            self.video_surface.show()
        self.hideToggled.emit(checked)

    def handle_mute_clicked(self, checked):
        self.mute_btn.setText("Unmute" if checked else "Mute")
        self.muteToggled.emit(checked)