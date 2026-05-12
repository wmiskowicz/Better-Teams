from PyQt6.QtMultimedia import QMediaCaptureSession, QCamera, QAudioInput, QMediaDevices
from PyQt6.QtCore import QObject, pyqtSlot

class AppController(QObject):
    """
    Controller class managing multimedia sessions and hardware state.
    Centralizes camera display management and sound blocking logic.
    """
    def __init__(self, video_output_widget):
        super().__init__()
        
        # Core capture session handles the sync between inputs and outputs
        self.capture_session = QMediaCaptureSession()
        
        # Initialize Microphone (Sound Blocking/Source Management)
        self.audio_input = QAudioInput()
        # Uses default system microphone automatically
        self.capture_session.setAudioInput(self.audio_input)
        
        # Initialize Camera
        self.camera = QCamera(QMediaDevices.defaultVideoInput())
        self.capture_session.setCamera(self.camera)
        
        # Display Management: Routing the camera feed to the UI widget
        # video_output_widget should be a QVideoWidget or a widget with a videoSink
        self.capture_session.setVideoOutput(video_output_widget)
        
        # Start the camera by default
        self.camera.start()

    @pyqtSlot(bool)
    def toggle_mute(self, is_muted: bool):
        """
        Handles sound blocking by muting/unmuting the audio input device.
        """
        self.audio_input.setMuted(is_muted)

    @pyqtSlot(bool)
    def toggle_camera(self, should_hide: bool):
        """
        Manages the camera hardware state. 
        Turning off the camera stops the hardware stream to save resources.
        """
        if should_hide:
            self.camera.stop()
        else:
            self.camera.start()

    def set_active_microphone(self, device):
        """
        Allows switching between different system microphones if available.
        """
        self.audio_input.setDevice(device)