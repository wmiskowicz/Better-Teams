from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtNetwork import QTcpServer, QTcpSocket, QHostAddress
import socket
import threading
import time
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser
import struct

class TCPWorker(QObject):
    # --- CONFIGURATION ---
    SERVICE_TYPE = "_mychat._tcp.local."
    MY_NAME = f"User_{socket.gethostname()}_{int(time.time()) % 1000}" # Added unique ID

    def __init__(self, parent = None):
        super().__init__(parent)
                


    # --- PART 1: THE LISTENER (Server) ---
    def start_listener(self):
        """Background thread that waits for messages."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Binding to port 0 tells the OS to pick a random available port
        server_socket.bind(('', 0)) 
        actual_port = server_socket.getsockname()[1]
        server_socket.listen(5)
        
        # We need to return this port so we can register it with Zeroconf
        return server_socket, actual_port

    def listener_loop(self, server_socket):
        while True:
            try:
                conn, addr = server_socket.accept()
                with conn:
                    data = conn.recv(1024).decode('utf-8')
                    print(f"\n[RECEIVED from {addr[0]}]: {data}")
                    print("Enter message: ", end="", flush=True)
            except:
                break

# --- PART 2: THE DISCOVERY ---
class ChatDiscoveryListener:
    def __init__(self, name):
        self.name = name
        self.peers = {}

    def add_service(self, zc, type_, name):
        if name.startswith(self.name): 
            return
         
        info = zc.get_service_info(type_, name)
        if info:
            ip = socket.inet_ntoa(info.addresses[0])
            self.peers[name] = (ip, info.port)
            print(f"\n[DISCOVERED]: {name} at {ip}:{info.port}")

    def update_service(self, zc, type_, name):
        """Mandatory for newer Zeroconf versions."""
        pass

    def remove_service(self, zc, type_, name):
        if name in self.peers:
            del self.peers[name]

# --- MAIN APP ---
def run_app():
    tcp_worker = TCPWorker()
    # 1. Setup Listener and get the dynamically assigned port
    server_sock, my_port = tcp_worker.start_listener()
    threading.Thread(target=tcp_worker.listener_loop, args=(server_sock,), daemon=True).start()

    # 2. Register with Zeroconf using the unique port we just got
    local_ip = socket.gethostbyname(socket.gethostname())
    info = ServiceInfo(tcp_worker.SERVICE_TYPE, f"{tcp_worker.MY_NAME}.{tcp_worker.SERVICE_TYPE}",
                       addresses=[socket.inet_aton(local_ip)], port=my_port)
    zc = Zeroconf()
    zc.register_service(info)
    
    listener = ChatDiscoveryListener()
    browser = ServiceBrowser(zc, tcp_worker.SERVICE_TYPE, listener)

    print(f"--- Welcome {tcp_worker.MY_NAME} ---")
    print(f"Listening on Port: {my_port} | Searching for peers...")

    try:
        while True:
            msg = input("Enter message: ")
            if msg.lower() == 'quit': break
            
            if not listener.peers:
                print("No peers found yet...")
                continue

            for name, (ip, port) in list(listener.peers.items()):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(2.0)
                        s.connect((ip, port))
                        s.sendall(msg.encode('utf-8'))
                except:
                    print(f"Peer {name} seems offline.")
    finally:
        zc.unregister_service(info)
        zc.close()

if __name__ == "__main__":
    run_app()