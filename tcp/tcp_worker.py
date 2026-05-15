from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtNetwork import QTcpServer, QTcpSocket, QHostAddress

import struct

class TCPWorker(QObject):
    """The Networking Engine running in a separate thread."""
    connection_status = pyqtSignal(bool, str) # (success, message)
    message_received = pyqtSignal(str)        # (the actual text)
    frame_received = pyqtSignal(bytes)

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
            # Convert to bytes and pass through send_data to attach the length header
            payload = message.encode('utf-8')
            self.send_data(payload)

            
    def send_data(self, data_bytes):
        """Sends size-prefixed data so the receiver knows when to stop reading."""
        if self.socket and self.socket.isOpen():
            # Pack the length of data into a 4-byte integer (Standard 'I' format)
            header = struct.pack(">I", len(data_bytes))
            self.socket.write(header + data_bytes)

    def read_data(self):
        while self.socket.bytesAvailable() >= 4:
            header = self.socket.peek(4)
            data_size = struct.unpack(">I", header)[0]

            if self.socket.bytesAvailable() < data_size + 4:
                break 

        self.socket.read(4)
        payload = self.socket.read(data_size)
        if len(payload) < data_size:
            payload += self.socket.read(data_size - len(payload))
                
