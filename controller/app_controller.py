from PyQt6.QtMultimedia import QMediaCaptureSession, QCamera, QAudioInput, QMediaDevices
from PyQt6.QtCore import QObject, QThread, pyqtSlot, pyqtSignal
from PyQt6.QtCore import QBuffer, QIODevice, QByteArray

from tcp.tcp_worker_mcv import TCPWorker

class AppController(QObject):

    message_recieved = pyqtSignal(str, str) # Sender, message

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
                
        self.setup_network_worker()
        
        
        
    def init_camera(self):
        self.video_output_widget = self.parent_container.display.video_surface
        # self.video_output_widget.videoSink().videoFrameChanged.connect(self.process_video_frame)

        self.camera = QCamera(QMediaDevices.defaultVideoInput())
        self.capture_session.setCamera(self.camera)
        self.capture_session.setVideoOutput(self.video_output_widget)
        
        self.camera.start()

    def setup_network_worker(self):
        # 1. Initialize the thread and worker
        self.network_thread = QThread()
        self.tcp_worker = TCPWorker()
        
        # 2. Push worker to the separate thread environment
        self.tcp_worker.moveToThread(self.network_thread)
        
        # 3. Connect signals to update your Views / Models
        self.network_thread.started.connect(self.tcp_worker.start)
        self.tcp_worker.message_received.connect(self.chat_msg_recieved_handler)
        # self.tcp_worker.status_updated.connect()
        
        # Clean cleanup loops upon exit
        self.network_thread.finished.connect(self.tcp_worker.stop)
        
        # 4. Fire up the execution thread
        self.network_thread.start()

    def chat_msg_send_handler(self, text_input):
        self.tcp_worker.send_broadcast_message(text_input)

    def chat_msg_recieved_handler(self, sender, recieved_text):
        self.message_recieved.emit(sender, recieved_text)
        
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
        

    # def process_video_frame(self, frame):
    #     """Intercepts the frame, compresses it, and sends it to the worker."""
    #     if not self.tcp_worker.socket or not self.tcp_worker.socket.isOpen():
    #         return

    #     # 1. Convert QVideoFrame to QImage
    #     image = frame.toImage()
    #     if image.isNull():
    #         return

    #     # 2. Compress to bytes (JPEG)
    #     byte_array = QByteArray()
    #     buffer = QBuffer(byte_array)
    #     buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    #     image.save(buffer, "JPG", 70) # 70 is quality: balance between speed and clarity
        
    #     # 3. Send via TCP
    #     frame_bytes = byte_array.data()
    #     self.tcp_worker.send_data(b'IMG:' + frame_bytes) 
        
