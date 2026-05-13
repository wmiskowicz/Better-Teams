from PyQt6.QtMultimedia import QMediaCaptureSession, QCamera, QAudioInput, QMediaDevices
from PyQt6.QtCore import QObject, QThread, pyqtSlot
from PyQt6.QtCore import QBuffer, QIODevice, QByteArray

from tcp.tcp_worker import TCPWorker

class AppController(QObject):
    """
    Controller class managing multimedia sessions and hardware state.
    Centralizes camera display management and sound blocking logic.
    """
    def __init__(self, parent_container):
        super().__init__()
        
        self.capture_session = QMediaCaptureSession()
        self.parent_container = parent_container # MainWindow
        
        self.audio_input = QAudioInput()
        self.capture_session.setAudioInput(self.audio_input)
                
        self.network_thread = QThread()
        self.tcp_worker = TCPWorker()
        self.tcp_worker.moveToThread(self.network_thread)

        # self.tcp_worker.message_received.connect(self.handle_incoming_chat)
        self.network_thread.start()
        
        
        
    def init_camera(self):
        self.video_output_widget = self.parent_container.display.video_surface
        self.video_output_widget.videoSink().videoFrameChanged.connect(self.process_video_frame)

        self.camera = QCamera(QMediaDevices.defaultVideoInput())
        self.capture_session.setCamera(self.camera)
        self.capture_session.setVideoOutput(self.video_output_widget)
        
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
        
        
    def host_session(self):
        self.tcp_worker.start_host(12345)

    def join_session(self, ip):
        self.tcp_worker.start_join(ip, 12345)

    def process_video_frame(self, frame):
        """Intercepts the frame, compresses it, and sends it to the worker."""
        if not self.tcp_worker.socket or not self.tcp_worker.socket.isOpen():
            return

        # 1. Convert QVideoFrame to QImage
        image = frame.toImage()
        if image.isNull():
            return

        # 2. Compress to bytes (JPEG)
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "JPG", 70) # 70 is quality: balance between speed and clarity
        
        # 3. Send via TCP
        frame_bytes = byte_array.data()
        self.tcp_worker.send_data(b'IMG:' + frame_bytes) 
        
