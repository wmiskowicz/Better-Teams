from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenuBar, QApplication

class TopBar(QMenuBar):
    """Subclass for the top navigation menu."""
    def __init__(self, parent_container): # Pass controller to link actions
        super().__init__()
        self.parent_container = parent_container
        self.controller = parent_container.controller
        self.init_ui()

    def init_ui(self):
        # File Menu
        file_menu = self.addMenu("File")
        
        host_action = QAction("Host Session", self)
        host_action.triggered.connect(self.controller.host_session)
        file_menu.addAction(host_action)

        join_action = QAction("Join Session", self)
        join_action.triggered.connect(self.controller.join_session)
        file_menu.addAction(join_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        file_menu.addAction(exit_action)

        # Settings Menu (Keep your existing code)
        settings_menu = self.addMenu("Settings")
        settings_menu.addAction(QAction("Preferences", self))
        settings_menu.addAction(QAction("Audio Settings", self))