import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTextEdit, QLineEdit, QFrame)
from PyQt6.QtCore import pyqtSignal, Qt

from controller.app_controller import AppController

class ChatSidebar(QWidget):
    """
    Subclass representing the sidebar.
    Emits a signal whenever a message is sent.
    """
    # Define a signal that carries a string (the message)
    chat_msg_sent = pyqtSignal(str)

    def __init__(self, parent_container):
        super().__init__()
        self.parent_container = parent_container


        self.controller: AppController = parent_container.controller

        self.chat_msg_sent.connect(self.controller.chat_msg_send_handler)
        self.controller.message_recieved.connect(self.handle_msg_recieved)
        self.controller.status_updated.connect(self.handle_status_updated)
        
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
            self.chat_msg_sent.emit(text)
            self.chat_history.append(f"You: {text}")            
            self.message_input.clear()

    def handle_msg_recieved(self, sender: str, recieved_text: str):
        self.chat_history.append(f"{sender}: {recieved_text}")
        
    def handle_status_updated(self, status: str):
        self.chat_history.append(status)
