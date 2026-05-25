"""
ui/welcome_window.py

The first screen the user sees.  Lets them:
  1. Enter their display name.
  2. Choose to Host or Join.
  3. (Join) Enter the host's IP address.

On success, opens MeetingWindow and closes itself.
"""

import socket

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, 
    QLabel, QLineEdit, QPushButton,
    QRadioButton, QButtonGroup, QFrame,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot

from constants import APP_NAME, HOST_CHAT_PORT


# ── Stylesheet ─────────────────────────────────────────────────────────────────
STYLE = """
QWidget {
    background: #12141a;
    color: #d4d8e8;
    font-family: 'Segoe UI', 'Arial', sans-serif;
}
QLabel#title {
    font-size: 28px;
    font-weight: bold;
    color: #4f8ef7;
    letter-spacing: 2px;
}
QLabel#subtitle {
    font-size: 13px;
    color: #6b7599;
}
QLabel.field-label {
    font-size: 12px;
    color: #8899bb;
    font-weight: bold;
}
QLineEdit {
    background: #1c1f27;
    border: 1px solid #2e3240;
    border-radius: 7px;
    min-height: 25px;
    padding: 11px 12px;
    font-size: 14px;
    color: #d4d8e8;
}
QLineEdit:focus {
    border-color: #4f8ef7;
}
QRadioButton {
    font-size: 13px;
    color: #d4d8e8;
    spacing: 8px;
}
QRadioButton::indicator {
    width: 16px; height: 16px;
}
QPushButton#main-btn {
    background: #4f8ef7;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 11px 0;
    font-size: 15px;
    font-weight: bold;
}
QPushButton#main-btn:hover   { background: #6aa0ff; }
QPushButton#main-btn:pressed { background: #3a6fd8; }
QPushButton#main-btn:disabled { background: #2a3050; color: #555; }
QFrame#card {
    background: #1c1f27;
    border: 1px solid #2e3240;
    border-radius: 12px;
}
"""


class ConnectWorker(QThread):
    """Tries to TCP-connect to the host in a thread so the UI doesn't freeze."""
    success = pyqtSignal()
    failure = pyqtSignal(str)

    def __init__(self, host_ip: str):
        super().__init__()
        self.host_ip = host_ip

    def run(self):
        try:
            s = socket.create_connection((self.host_ip, HOST_CHAT_PORT), timeout=4)
            s.close()
            self.success.emit()
        except OSError as e:
            self.failure.emit(str(e))


class WelcomeWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setFixedSize(440, 520)
        self.setStyleSheet(STYLE)
        self._build_ui()

    # UI Building

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 36, 40, 36)
        root.setSpacing(20)

        # Title
        title = QLabel(APP_NAME)
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Lightweight team communication — LAN & localhost")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addSpacing(4)

        # Card
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(14)

        # Name
        name_label = QLabel("Display Name")
        name_label.setProperty("class", "field-label")
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Your name (shown to others)")
        self._name_input.setMaxLength(32)

        # Mode selection
        mode_label = QLabel("Mode")
        mode_label.setProperty("class", "field-label")

        self._host_radio = QRadioButton("Host a Meeting")
        self._join_radio = QRadioButton("Join a Meeting")
        self._host_radio.setChecked(True)

        bg = QButtonGroup(self)
        bg.addButton(self._host_radio)
        bg.addButton(self._join_radio)

        self._host_radio.toggled.connect(self._on_mode_changed)

        # IP input (join mode only)
        self._ip_label = QLabel("Host IP Address")
        self._ip_label.setProperty("class", "field-label")
        self._ip_input = QLineEdit()
        self._ip_input.setPlaceholderText("e.g. 192.168.1.100 or 127.0.0.1")
        self._ip_label.hide()
        self._ip_input.hide()

        # Go button
        self._go_btn = QPushButton("Start Meeting")
        self._go_btn.setObjectName("main-btn")
        self._go_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._go_btn.clicked.connect(self._on_go)

        for w in [
            name_label, self._name_input,
            mode_label, self._host_radio, self._join_radio,
            self._ip_label, self._ip_input,
        ]:
            card_layout.addWidget(w)

        root.addWidget(card)
        root.addWidget(self._go_btn)
        root.addStretch()

        # # Version label
        # ver = QLabel("v2.0  •  PyQt6  •  Open Source")
        # ver.setObjectName("subtitle")
        # ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # root.addWidget(ver)

    # Slots

    def _on_mode_changed(self, host_checked: bool):
        is_join = self._join_radio.isChecked()
        self._ip_label.setVisible(is_join)
        self._ip_input.setVisible(is_join)
        self._go_btn.setText("Start Meeting" if host_checked else "Join Meeting")

    def _on_go(self):
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Name required", "Please enter a display name.")
            return

        if self._host_radio.isChecked():
            self._launch("host", name, "")
        else:
            ip = self._ip_input.text().strip()
            if not ip:
                QMessageBox.warning(self, "IP required", "Please enter the host's IP address.")
                return
            # Verify connectivity first
            self._go_btn.setEnabled(False)
            self._go_btn.setText("Connecting…")
            self._worker = ConnectWorker(ip)
            self._worker.success.connect(lambda: self._launch("peer", name, ip))
            self._worker.failure.connect(self._on_connect_fail)
            self._worker.start()

    @pyqtSlot(str)
    def _on_connect_fail(self, reason: str):
        self._go_btn.setEnabled(True)
        self._go_btn.setText("Join Meeting")
        QMessageBox.critical(
            self,
            "Connection failed",
            f"Could not reach the host server:\n{reason}\n\n"
            "Make sure the host is running and the IP is correct.",
        )

    def _launch(self, mode: str, name: str, host_ip: str):
        from ui.meeting_window import MeetingWindow
        self._room = MeetingWindow(name=name, mode=mode, host_ip=host_ip)
        self._room.show()
        self.close()
