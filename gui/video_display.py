from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QImage
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
        
        self.display_label = QLabel("CAMERA OFF")
        self.display_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display_label.hide()
        
        self.remote_view = QLabel("Waiting for peer...")
        self.remote_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.remote_view.setStyleSheet("background-color: black; border: 2px solid #444; color: white;")
        self.remote_view.setMinimumSize(400, 300)
        
        # 4. Assembly
        # Add the top navigation buttons
        self.main_layout.addLayout(top_button_layout)
        
        # Create a horizontal row for side-by-side video feeds
        video_track_layout = QHBoxLayout()
        video_track_layout.addWidget(self.video_surface)
        video_track_layout.addWidget(self.remote_view)
        
        # Add the video row and the placeholder label to the main layout
        self.main_layout.addLayout(video_track_layout)
        self.main_layout.addWidget(self.display_label)
        
        # Set stretch factor on the video row layout index (1) so it expands dynamically
        self.main_layout.setStretch(1, 1)
        
    def display_remote_frame(self, jpg_bytes):
        """Converts incoming bytes back into a picture."""
        image = QImage.fromData(jpg_bytes)
        if not image.isNull():
            # Scale the image to fit the label while keeping aspect ratio
            pixmap = QPixmap.fromImage(image)
            scaled_pixmap = pixmap.scaled(
                self.remote_view.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.remote_view.setPixmap(scaled_pixmap)

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