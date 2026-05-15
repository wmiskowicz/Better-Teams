import socket
import threading
import time
import struct
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage
from PyQt6.QtCore import QBuffer, QIODevice, QByteArray
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser

# --- PROTOCOL PAYLOAD CONSTANTS ---
MSG_TYPE_CHAT = 1
MSG_TYPE_IMAGE = 2
HEADER_FORMAT = "!BI"  # 1 Byte unsigned Char (Type), 4 Bytes unsigned Int (Length)
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  # Exactly 5 bytes

class TCPWorker(QObject):

    # --- MVC COMMUNICATION SIGNALS ---
    message_received = pyqtSignal(str, str)     # (sender_ip, message_text)
    image_received = pyqtSignal(str, QImage)    # (sender_ip, q_image)
    peer_discovered = pyqtSignal(str, str, int) # (peer_name, ip, port)
    peer_lost = pyqtSignal(str)                 # (peer_name)
    status_updated = pyqtSignal(str)            # (status_text)

    # --- CONFIGURATION ---
    SERVICE_TYPE = "_mychat._tcp.local."
    MY_NAME = f"User_{socket.gethostname()}_{int(time.time()) % 1000}"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._server_socket = None
        self._my_port = None
        self._zc = None
        self._service_info = None
        self._browser = None
        
        self._discovery_listener = ChatDiscoveryListener(self.MY_NAME, self.peer_discovered, self.peer_lost)

    # ==========================================
    # PUBLIC SLOTS / API (Called by Controller)
    # ==========================================

    @pyqtSlot()
    def start(self):
        """Initializes the listener socket, starts networking threads, and registers Zeroconf."""
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', 0)) 
        self._my_port = self._server_socket.getsockname()[1]
        self._server_socket.listen(5)
        
        threading.Thread(target=self._listener_loop, daemon=True).start()
        self.status_updated.emit(f"Listening on Port: {self._my_port} | Searching for peers...")

        local_ip = socket.gethostbyname(socket.gethostname())
        self._service_info = ServiceInfo(
            self.SERVICE_TYPE, 
            f"{self.MY_NAME}.{self.SERVICE_TYPE}",
            addresses=[socket.inet_aton(local_ip)], 
            port=self._my_port
        )
        self._zc = Zeroconf()
        self._zc.register_service(self._service_info)
        self._browser = ServiceBrowser(self._zc, self.SERVICE_TYPE, self._discovery_listener)

    @pyqtSlot(str)
    def send_broadcast_message(self, message: str):
        """Frames and broadcasts a text string to all discovered peers."""
        payload = message.encode('utf-8')
        header = struct.pack(HEADER_FORMAT, MSG_TYPE_CHAT, len(payload))
        self._broadcast_packet(header + payload)

    @pyqtSlot(QImage)
    def send_broadcast_image(self, image: QImage):
        """Frames and broadcasts a compressed QImage to all discovered peers."""
        if image.isNull():
            return

        # Compress QImage to raw JPEG bytes using Qt's internal buffer mechanics
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "JPG", 75)  # 75: Optimal balance between compression size and visual quality
        payload = byte_array.data()

        header = struct.pack(HEADER_FORMAT, MSG_TYPE_IMAGE, len(payload))
        self._broadcast_packet(header + payload)

    @pyqtSlot()
    def stop(self):
        """Gracefully unregisters services and cleans up allocations."""
        if self._zc:
            if self._service_info:
                self._zc.unregister_service(self._service_info)
            self._zc.close()
        if self._server_socket:
            self._server_socket.close()

    # ==========================================
    # PRIVATE METHODS
    # ==========================================

    def _broadcast_packet(self, full_packet: bytes):
        """Helper to dispatch bytes. We do this sequentially to prevent thread exhaustion."""
        peers = self._discovery_listener.get_peers()
        if not peers:
            return

        for name, (ip, port) in list(peers.items()):
            # REMOVE threading.Thread here. 
            # Sequential sending is safer when sending high-frequency image data.
            self._send_to_peer(name, ip, port, full_packet)

    def _send_to_peer(self, name: str, ip: str, port: int, packet: bytes):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # Tighten timeouts for video frames
                s.settimeout(1.0) 
                s.connect((ip, port))
                s.sendall(packet)
        except Exception:
            # Optionally remove peer from discovery if they keep failing
            pass

    def _read_exact(self, conn, num_bytes):
        """Helper ensuring exact byte requirements are extracted safely from the TCP stream block."""
        buffer = b""
        while len(buffer) < num_bytes:
            packet = conn.recv(num_bytes - len(buffer))
            if not packet:
                raise ConnectionError("Socket connection closed by remote peer.")
            buffer += packet
        return buffer

    def _listener_loop(self):
        """Background loop accepting incoming connections and parsing framing protocols."""
        while True:
            try:
                conn, addr = self._server_socket.accept()
                with conn:
                    # 1. Read structural boundary frame header
                    header_bytes = self._read_exact(conn, HEADER_SIZE)
                    msg_type, payload_length = struct.unpack(HEADER_FORMAT, header_bytes)

                    # 2. Read exact body slice boundaries
                    payload = self._read_exact(conn, payload_length)

                    # 3. Multiplex message types to their respective handlers
                    if msg_type == MSG_TYPE_CHAT:
                        text_message = payload.decode('utf-8')
                        self.message_received.emit(addr[0], text_message)

                    elif msg_type == MSG_TYPE_IMAGE:
                        received_image = QImage.fromData(payload, "JPG")
                        if not received_image.isNull():
                            self.image_received.emit(addr[0], received_image)

            except Exception:
                break  # Break out cleanly if server socket gets closed by stop()


# ==========================================
# INTERNAL SUBCLASS
# ==========================================

class ChatDiscoveryListener:
    """Internal discovery handler managing node caching and routing signals back up."""
    def __init__(self, my_name, discovery_signal, loss_signal):
        self.my_name = my_name
        self._peers = {}
        self._discovery_signal = discovery_signal
        self._loss_signal = loss_signal

    def get_peers(self):
        return self._peers

    def add_service(self, zc, type_, name):
        if name.startswith(self.my_name): 
            return
            
        info = zc.get_service_info(type_, name)
        if info:
            ip = socket.inet_ntoa(info.addresses[0])
            self._peers[name] = (ip, info.port)
            self._discovery_signal.emit(name, ip, info.port)

    def update_service(self, zc, type_, name):
        pass

    def remove_service(self, zc, type_, name):
        if name in self._peers:
            del self._peers[name]
            self._loss_signal.emit(name)