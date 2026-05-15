from PyQt6.QtMultimedia import QMediaCaptureSession, QCamera, QAudioInput, QMediaDevices
from PyQt6.QtCore import QObject, QThread, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QImage

from tcp.tcp_worker_mcv import TCPWorker

class AppController(QObject):

    message_recieved = pyqtSignal(str, str) # Sender, message
    image_recieved = pyqtSignal(str, QImage)  # Added to route incoming images out to the UI view layer

    def __init__(self, parent_container):
        super().__init__()
        self.capture_session = QMediaCaptureSession()
        self.parent_container = parent_container # MainWindow
        self.audio_input = QAudioInput()
        self.capture_session.setAudioInput(self.audio_input)
                
        self.setup_network_worker()

    def init_camera(self):
        self.video_output_widget = self.parent_container.display.video_surface
        
        # UNCOMMENTED: Connect the camera change hook to stream your video dynamically
        self.video_output_widget.videoSink().videoFrameChanged.connect(self.process_video_frame)

        self.camera = QCamera(QMediaDevices.defaultVideoInput())
        self.capture_session.setCamera(self.camera)
        self.capture_session.setVideoOutput(self.video_output_widget)
        self.camera.start()

    def setup_network_worker(self):
        self.network_thread = QThread()
        self.tcp_worker = TCPWorker()
        self.tcp_worker.moveToThread(self.network_thread)
        
        self.network_thread.started.connect(self.tcp_worker.start)
        self.tcp_worker.message_received.connect(self.chat_msg_recieved_handler)
        
        # CONNECT the image reception signal down to the controller handler
        self.tcp_worker.image_received.connect(self.image_received_handler)
        
        self.network_thread.finished.connect(self.tcp_worker.stop)
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
        

    def image_received_handler(self, sender_ip, q_image):
        """Passes the received frame from a remote peer up to the UI/View layer."""
        self.image_recieved.emit(sender_ip, q_image)

    def process_video_frame(self, frame):
        """Intercepts local camera hardware frames and requests the worker to broadcast them."""
        # Convert QVideoFrame to a standard QImage format object safely
        q_image = frame.toImage()
        if not q_image.isNull():
            # Simply pass the QImage object to the slot across thread boundaries cleanly
            self.tcp_worker.send_broadcast_image(q_image)