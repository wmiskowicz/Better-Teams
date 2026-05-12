import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTextEdit, QLineEdit, QFrame)
from PyQt6.QtCore import pyqtSignal, Qt

class ChatSidebar(QWidget):
    """
    Subclass representing the sidebar.
    Emits a signal whenever a message is sent.
    """
    # Define a signal that carries a string (the message)
    messageSent = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # --- Chat Container ---
        chat_container = QFrame()
        chat_container.setStyleSheet("border: 1px solid #A0A0A0; border-radius: 10px; background: white;")
        chat_vbox = QVBoxLayout(chat_container)
        
        # Header
        chat_header = QPushButton("Chat")
        chat_header.setEnabled(False) # Visual only as per obraz.png
        chat_header.setStyleSheet("color: black; border: 1px solid #A0A0A0; border-radius: 10px; padding: 5px;")
        
        # History Display
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setText("Timon: aaaaa\nPumba: +1\nTimon: Kiedy liga?")
        self.chat_history.setStyleSheet("border: none; background: transparent;")

        # --- Message Input Area ---
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type message...")
        self.message_input.setStyleSheet("border: 1px solid #CCC; border-radius: 5px; padding: 5px;")
        # Allow sending by pressing "Enter"
        self.message_input.returnPressed.connect(self.handle_send)

        send_btn = QPushButton("Send")
        send_btn.setStyleSheet("background-color: #E0E0E0; border-radius: 5px; padding: 5px 10px;")
        send_btn.clicked.connect(self.handle_send)

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(send_btn)
        
        # Assemble chat box
        chat_vbox.addWidget(chat_header)
        chat_vbox.addWidget(self.chat_history)
        chat_vbox.addLayout(input_layout)
        
        layout.addWidget(chat_container)
        self.setLayout(layout)

    def handle_send(self):
        """Handler to grab text, emit signal, and clear the field."""
        text = self.message_input.text().strip()
        if text:
            self.messageSent.emit(text)
            self.chat_history.append(f"You: {text}")            
            self.message_input.clear()

# Example of how to connect to the signal in your MainWindow
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(400, 500)
        layout = QVBoxLayout(self)
        
        self.sidebar = ChatSidebar()
        # Connect the custom signal to a slot (function)
        self.sidebar.messageSent.connect(self.on_new_message)
        
        layout.addWidget(self.sidebar)

    def on_new_message(self, msg):
        print(f"Main window received signal! Message: {msg}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())