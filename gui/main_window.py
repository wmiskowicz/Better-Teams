import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QTextEdit, QFrame)


from gui.chat_sidebar import ChatSidebar
from gui.video_display import VideoDisplay
from gui.top_bar import TopBar

class MainWindow(QWidget):
    """The main application window holding both components."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Interface")
        self.resize(800, 450)
        self.setStyleSheet("background-color: #F5F5F5;")
        
        # 1. This is the only layout that gets (self)
        main_layout = QVBoxLayout(self)
        
        # 2. Initialize sub-layouts without passing 'self'
        chat_and_screen_layout = QHBoxLayout() 
        
        self.top_bar = TopBar()
        self.display = VideoDisplay()
        self.sidebar = ChatSidebar()
        
        # 3. Add widgets/layouts to their respective parents
        chat_and_screen_layout.addWidget(self.display, stretch=3)
        chat_and_screen_layout.addWidget(self.sidebar, stretch=1)
        
        main_layout.addWidget(self.top_bar)
        main_layout.addLayout(chat_and_screen_layout) # Nesting the horizontal inside the vertical