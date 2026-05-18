from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QByteArray, QSize
from PyQt6.QtGui import QFont, QPixmap, QImage, QIcon, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtMultimediaWidgets import QVideoWidget

class VideoDisplay(QFrame):
    hideToggled = pyqtSignal(bool)
    muteToggled = pyqtSignal(bool)

    MUTE_SVG = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><!--!Font Awesome Free v7.2.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2026 Fonticons, Inc.--><path d="M73 39.1C63.6 29.7 48.4 29.7 39.1 39.1C29.8 48.5 29.7 63.7 39 73.1L567 601.1C576.4 610.5 591.6 610.5 600.9 601.1C610.2 591.7 610.3 576.5 600.9 567.2L456.7 422.8C490.9 388.2 512 340.6 512 288L512 248C512 234.7 501.3 224 488 224C474.7 224 464 234.7 464 248L464 288C464 327.3 448.3 362.9 422.7 388.9L388.8 355C405.6 337.7 416 314 416 288L416 160C416 107 373 64 320 64C267 64 224 107 224 160L224 190.2L73 39.2zM371.3 473.1L329.9 431.7C326.6 431.9 323.4 432 320.1 432C240.6 432 176.1 367.5 176.1 288L176.1 277.8L132.5 234.2C129.7 238.1 128.1 242.9 128.1 248L128.1 288C128.1 385.9 201.4 466.7 296.1 478.5L296.1 528L248.1 528C234.8 528 224.1 538.7 224.1 552C224.1 565.3 234.8 576 248.1 576L392.1 576C405.4 576 416.1 565.3 416.1 552C416.1 538.7 405.4 528 392.1 528L344.1 528L344.1 478.5C353.4 477.3 362.5 475.5 371.4 473.1z"/></svg>'''
    UNMUTE_SVG = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><!--!Font Awesome Free v7.2.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2026 Fonticons, Inc.--><path d="M320 64C267 64 224 107 224 160L224 288C224 341 267 384 320 384C373 384 416 341 416 288L416 160C416 107 373 64 320 64zM176 248C176 234.7 165.3 224 152 224C138.7 224 128 234.7 128 248L128 288C128 385.9 201.3 466.7 296 478.5L296 528L248 528C234.7 528 224 538.7 224 552C224 565.3 234.7 576 248 576L392 576C405.3 576 416 565.3 416 552C416 538.7 405.3 528 392 528L344 528L344 478.5C438.7 466.7 512 385.9 512 288L512 248C512 234.7 501.3 224 488 224C474.7 224 464 234.7 464 248L464 288C464 367.5 399.5 432 320 432C240.5 432 176 367.5 176 288L176 248z"/></svg>'''
    HIDE_SVG = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><!--!Font Awesome Free v7.2.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2026 Fonticons, Inc.--><path d="M73 39.1C63.6 29.7 48.4 29.7 39.1 39.1C29.8 48.5 29.7 63.7 39 73.1L567 601.1C576.4 610.5 591.6 610.5 600.9 601.1C610.2 591.7 610.3 576.5 600.9 567.2L447.9 414.2L447.9 192C447.9 156.7 419.2 128 383.9 128L161.8 128L73 39.1zM64 192L64 448C64 483.3 92.7 512 128 512L384 512C391.8 512 399.3 510.6 406.2 508L68 169.8C65.4 176.7 64 184.2 64 192zM496 400L569.5 458.8C573.7 462.2 578.9 464 584.3 464C597.4 464 608 453.4 608 440.3L608 199.7C608 186.6 597.4 176 584.3 176C578.9 176 573.7 177.8 569.5 181.2L496 240L496 400z"/></svg>'''
    UNHIDE_SVG = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><!--!Font Awesome Free v7.2.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2026 Fonticons, Inc.--><path d="M128 128C92.7 128 64 156.7 64 192L64 448C64 483.3 92.7 512 128 512L384 512C419.3 512 448 483.3 448 448L448 192C448 156.7 419.3 128 384 128L128 128zM496 400L569.5 458.8C573.7 462.2 578.9 464 584.3 464C597.4 464 608 453.4 608 440.3L608 199.7C608 186.6 597.4 176 584.3 176C578.9 176 573.7 177.8 569.5 181.2L496 240L496 400z"/></svg>'''

    def __init__(self):
        super().__init__()
        self.setObjectName("VideoDisplay")
        self.init_ui()

    def svg_icon(self, svg_bytes, size=QSize(32, 32)):
        renderer = QSvgRenderer(QByteArray(svg_bytes))
        pixmap = QPixmap(size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)

    def init_ui(self):
        # Vertical layout for the main container
        self.main_layout = QVBoxLayout(self)
        
        # 1. Bottom controls
        bottom_controls_layout = QHBoxLayout()
        bottom_controls_layout.addStretch()
        
        self.hide_btn = QPushButton()
        self.hide_btn.setCheckable(True)
        self.hide_btn.setIconSize(QSize(32, 32))
        self.hide_btn.setIcon(self.svg_icon(self.HIDE_SVG))

        self.mute_btn = QPushButton()
        self.mute_btn.setCheckable(True)
        self.mute_btn.setIconSize(QSize(32, 32))
        self.mute_btn.setIcon(self.svg_icon(self.MUTE_SVG))
        
        self.hide_btn.clicked.connect(self.handle_hide_clicked)
        self.mute_btn.clicked.connect(self.handle_mute_clicked)

        bottom_controls_layout.addStretch()
        bottom_controls_layout.addWidget(self.hide_btn)
        bottom_controls_layout.addSpacing(15)
        bottom_controls_layout.addWidget(self.mute_btn)
        bottom_controls_layout.addStretch()
        
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
        # Create a horizontal row for side-by-side video feeds
        video_track_layout = QHBoxLayout()
        video_track_layout.addWidget(self.video_surface)
        video_track_layout.addWidget(self.remote_view)

        # najpierw video
        self.main_layout.addLayout(video_track_layout)

        # potem przyciski
        self.main_layout.addLayout(bottom_controls_layout)

        # placeholder
        self.main_layout.addWidget(self.display_label)
        
        # Set stretch factor on the video row layout index (1) so it expands dynamically
        self.main_layout.setStretch(1, 1)
        
        button_style = """
        QPushButton {
            background-color: rgba(40, 40, 40, 200);
            color: white;
            border-radius: 20px;
            padding: 10px 20px;
            font-weight: bold;
            min-width: 120px;
        }

        QPushButton:hover {
            background-color: rgba(70, 70, 70, 220);
        }

        QPushButton:checked {
            background-color: #C62828;
        }
        """

        self.hide_btn.setStyleSheet(button_style)
        self.mute_btn.setStyleSheet(button_style)

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
        self.hide_btn.setIcon(
            self.svg_icon(self.UNHIDE_SVG) if checked else self.svg_icon(self.HIDE_SVG)
        )
        if checked:
            self.video_surface.hide()
            self.display_label.show()
        else:
            self.display_label.hide()
            self.video_surface.show()
        self.hideToggled.emit(checked)

    def handle_mute_clicked(self, checked):
        self.mute_btn.setIcon(
            self.svg_icon(self.UNMUTE_SVG) if checked else self.svg_icon(self.MUTE_SVG)
        )
        self.muteToggled.emit(checked)
        
    def display_remote_frame(self, sender_ip, q_image):
        """Displays the received QImage on the remote_view label."""
        if not q_image.isNull():
            # Convert QImage to Pixmap for display
            pixmap = QPixmap.fromImage(q_image)
            
            # Scale to fit the current label size
            # Using SmoothTransformation is key for video quality
            scaled_pixmap = pixmap.scaled(
                self.remote_view.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.remote_view.setPixmap(scaled_pixmap)