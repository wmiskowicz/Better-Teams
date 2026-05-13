from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtNetwork import QTcpServer, QTcpSocket, QHostAddress

import struct

class TCPWorker(QObject):
    """The Networking Engine running in a separate thread."""
    connection_status = pyqtSignal(bool, str) # (success, message)
    message_received = pyqtSignal(str)        # (the actual text)

    def __init__(self):
        super().__init__()
        self.server = None
        self.socket = None

    @pyqtSlot(int)
    def start_host(self, port=12345):
        """Logic for User 1 (Host)"""
        self.server = QTcpServer()
        if self.server.listen(QHostAddress.SpecialAddress.Any, port):
            self.server.newConnection.connect(self.handle_new_connection)
            self.connection_status.emit(True, f"Hosting on port {port}...")
        else:
            self.connection_status.emit(False, "Failed to start server.")

    def handle_new_connection(self):
        self.socket = self.server.nextPendingConnection()
        self.socket.readyRead.connect(self.read_data)
        self.connection_status.emit(True, "Peer Connected!")

    @pyqtSlot(str, int)
    def start_join(self, ip, port):
        """Logic for User 2 (Joiner)"""
        self.socket = QTcpSocket()
        self.socket.connected.connect(lambda: self.connection_status.emit(True, "Connected to Host!"))
        self.socket.readyRead.connect(self.read_data)
        self.socket.connectToHost(ip, port)

    @pyqtSlot(str)
    def send_message(self, message):
        if self.socket and self.socket.isOpen():
            # Add \n if you want to keep using canReadLine, 
            # or just send raw bytes.
            self.socket.write(message.encode('utf-8'))

    def read_data(self):
        """Read all available bytes if you aren't using line-based protocol."""
        if self.socket:
            data = self.socket.readAll().data().decode('utf-8')
            self.message_received.emit(data)
            
    def send_data(self, data_bytes):
        """Sends size-prefixed data so the receiver knows when to stop reading."""
        if self.socket and self.socket.isOpen():
            # Pack the length of data into a 4-byte integer (Standard 'I' format)
            header = struct.pack(">I", len(data_bytes))
            self.socket.write(header + data_bytes)

    def read_data(self):
        """Reassembles chunks into a full message/frame."""
        while self.socket.bytesAvailable() >= 4:
            # 1. Peek at the header to see how much data is coming
            header = self.socket.peek(4)
            data_size = struct.unpack(">I", header)[0]

            # 2. Check if the full payload has arrived
            if self.socket.bytesAvailable() < data_size + 4:
                break # Wait for more data to arrive

            # 3. Actually read the data now that we know it's all there
            self.socket.read(4) # Consume the header
            payload = self.socket.read(data_size)
            
            # 4. Route the data
            if payload.startswith(b'IMG:'):
                self.message_received.emit("FRAME_DATA") # Logic for VideoDisplay
                # You'll likely create a new signal: frame_received = pyqtSignal(bytes)
            else:
                self.message_received.emit(payload.decode('utf-8'))
                
