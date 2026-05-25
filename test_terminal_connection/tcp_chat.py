import socket
import threading
import sys

# Configuration
PORT = 5050
BUFFER_SIZE = 1024

def receive_messages(sock):
    """Listens for incoming messages and prints them to the terminal."""
    while True:
        try:
            message = sock.recv(BUFFER_SIZE).decode('utf-8')
            if not message:
                print("\n[!] Connection closed by peer.")
                break
            print(f"\r[Peer]: {message}\n> ", end="")   # \r carriage return to overwrite the input prompt
        except Exception:
            print("\n[!] Connection lost.")
            break
    sock.close()
    sys.exit(0)

def start_server():
    """Starts the server to listen for incoming connections."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # wildcard
    server.bind(('0.0.0.0', PORT))
    server.listen(1)
    
    print(f"[*] Listening for connections on port {PORT}...")
    client_socket, client_address = server.accept()
    print(f"[*] Connected to {client_address[0]}:{client_address[1]}")
    
    handle_communication(client_socket)
    server.close()

def start_client():
    """Connects to an existing server."""
    host = input("Enter the Host IP (leave blank for localhost): ").strip()
    if not host:
        host = '127.0.0.1'
        
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        print(f"[*] Connecting to {host}:{PORT}...")
        client.connect((host, PORT))
        print("[*] Connected successfully!")
        handle_communication(client)
    except ConnectionRefusedError:
        print("[!] Connection refused. Is the host running?")
    except Exception as e:
        print(f"[!] Error connecting: {e}")

def handle_communication(sock):
    """Handles the main input loop for sending messages."""
    
    # Start the background thread for receiving messages
    recv_thread = threading.Thread(target=receive_messages, args=(sock,))
    recv_thread.daemon = True
    recv_thread.start()
    
    print("Type your messages below. Type 'quit' to exit.")
    try:
        while True:
            msg = input("> ")
            if msg.lower() == 'quit':
                break
            if msg.strip():
                sock.send(msg.encode('utf-8'))
    except KeyboardInterrupt:
        pass
    finally:
        print("\n[*] Closing connection...")
        sock.close()

if __name__ == "__main__":
    print("=== Python TCP Terminal Chat ===")
    role = input("Do you want to (H)ost a chat or (C)onnect to one? [H/C]: ").strip().lower()
    
    if role == 'h':
        start_server()
    elif role == 'c':
        start_client()
    else:
        print("Invalid choice. Exiting.")