import socket
import threading
import time
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser

class TCPWorker(QObject):

    # --- MVC COMMUNICATION SIGNALS ---
    # Emitted when a peer sends a message: (sender_ip, message_text)
    message_received = pyqtSignal(str, str)
    # Emitted when a new peer is discovered: (peer_name, ip, port)
    peer_discovered = pyqtSignal(str, str, int)
    # Emitted when a peer drops off the local network
    peer_lost = pyqtSignal(str)
    # Emitted when the worker starts up to report its assignment details
    status_updated = pyqtSignal(str)

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
        
        # Instantiate the internal discovery listener
        self._discovery_listener = ChatDiscoveryListener(self.MY_NAME, self.peer_discovered, self.peer_lost)

    # ==========================================
    # PUBLIC SLOTS / API (Called by Controller)
    # ==========================================

    @pyqtSlot()
    def start(self):
        """Initializes the listener socket, starts networking threads, and registers Zeroconf."""
        # 1. Start TCP Listener
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', 0)) 
        self._my_port = self._server_socket.getsockname()[1]
        self._server_socket.listen(5)
        
        # Fire up the background server loop
        threading.Thread(target=self._listener_loop, daemon=True).start()
        self.status_updated.emit(f"Listening on Port: {self._my_port} | Searching for peers...")

        # 2. Register Zeroconf Service
        local_ip = socket.gethostbyname(socket.gethostname())
        self._service_info = ServiceInfo(
            self.SERVICE_TYPE, 
            f"{self.MY_NAME}.{self.SERVICE_TYPE}",
            addresses=[socket.inet_aton(local_ip)], 
            port=self._my_port
        )
        self._zc = Zeroconf()
        self._zc.register_service(self._service_info)
        
        # 3. Start Browser to discover peers
        self._browser = ServiceBrowser(self._zc, self.SERVICE_TYPE, self._discovery_listener)

    @pyqtSlot(str)
    def send_broadcast_message(self, message: str):
        """Loops through known peers and sends the text string payload."""
        peers = self._discovery_listener.get_peers()
        if not peers:
            self.status_updated.emit("No peers found yet...")
            return

        for name, (ip, port) in list(peers.items()):
            # Offload individual connections to background tasks to prevent UI hang
            threading.Thread(target=self._send_to_peer, args=(name, ip, port, message), daemon=True).start()

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

    def _listener_loop(self):
        """Background loop accepting incoming client connections."""
        while True:
            try:
                conn, addr = self._server_socket.accept()
                with conn:
                    data = conn.recv(1024).decode('utf-8')
                    if data:
                        # Safely alert the controller about the incoming message payload
                        self.message_received.emit(addr[0], data)
            except Exception:
                break  # Socket was closed or encountered an unrecoverable failure

    def _send_to_peer(self, name: str, ip: str, port: int, message: str):
        """Worker connection logic targeting individual network nodes."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect((ip, port))
                s.sendall(message.encode('utf-8'))
        except Exception:
            self.status_updated.emit(f"Peer {name} seems offline.")


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
            # Propagate event out to main worker interface thread-safely
            self._discovery_signal.emit(name, ip, info.port)

    def update_service(self, zc, type_, name):
        pass

    def remove_service(self, zc, type_, name):
        if name in self._peers:
            del self._peers[name]
            self._loss_signal.emit(name)