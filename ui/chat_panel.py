"""
ui/chat_panel.py

A self-contained chat panel: scrollable history + input row.
Exposes:
  add_message(sender, text)
  add_system(text)
  message_send signal(str)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel,
)
from PyQt6.QtCore    import Qt, pyqtSignal
from PyQt6.QtGui     import QTextCursor

# Colors (dark theme)
BG          = "#16181e"
PANEL_BG    = "#1c1f27"
INPUT_BG    = "#22263a"
BORDER      = "#2e3240"
ACCENT      = "#4f8ef7"
TEXT_FG     = "#d4d8e8"
SYSTEM_FG   = "#6b7599"
SENDER_FG   = "#a0b4ff"


class ChatPanel(QWidget):
    message_send = pyqtSignal(str)   # from protocol to UI: new message to send

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # UI

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QLabel("Chat")
        header.setFixedHeight(40)
        header.setStyleSheet(f"""
            background: {PANEL_BG};
            color: {TEXT_FG};
            font-size: 13px;
            font-weight: bold;
            border-bottom: 1px solid {BORDER};
        """)
        root.addWidget(header)

        # Message history
        self._history = QTextEdit()
        self._history.setReadOnly(True)
        self._history.setStyleSheet(f"""
            QTextEdit {{
                background: {BG};
                color: {TEXT_FG};
                font-size: 13px;
                border: none;
                padding: 8px;
            }}
        """)
        self._history.document().setDefaultStyleSheet(f"""
            .sender {{ color: {SENDER_FG}; font-weight: bold; }}
            .system  {{ color: {SYSTEM_FG}; font-style: italic; }}
            .text    {{ color: {TEXT_FG}; }}
        """)
        root.addWidget(self._history, stretch=1)

        # Input field + send button
        input_row = QHBoxLayout()
        input_row.setSpacing(6)
        input_row.setContentsMargins(8, 8, 8, 8)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Type a message…")
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: {INPUT_BG};
                color: {TEXT_FG};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {ACCENT};
            }}
        """)
        self._input.returnPressed.connect(self._on_send)

        send_btn = QPushButton("Send")
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.clicked.connect(self._on_send)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #6aa0ff; }}
            QPushButton:pressed {{ background: #3a6fd8; }}
        """)

        input_row.addWidget(self._input)
        input_row.addWidget(send_btn)

        input_container = QWidget()
        input_container.setLayout(input_row)
        input_container.setStyleSheet(f"background: {PANEL_BG}; border-top: 1px solid {BORDER};")
        root.addWidget(input_container)

        self.setStyleSheet(f"background: {BG};")

    # Public API

    def add_message(self, sender: str, text: str):
        """Append a regular chat message.

        Args:
            sender (str): Name of the sender (will be escaped and colored).
            text (str): Message text (will be escaped, newlines converted to <br>, and colored).
        """
        # Escape HTML
        safe_sender = sender.replace("&", "&amp;").replace("<", "&lt;")
        safe_text   = text.replace("&", "&amp;").replace("<", "&lt;").replace("\n", "<br/>")
        html = (
            f'<span class="sender">{safe_sender}</span>'
            f'<span class="text">: {safe_text}</span>'
        )
        self._append_html(html)

    def add_system(self, text: str):
        """Append a system notification line.

        Args:
            text (str): System message text (will be escaped and colored).
        """
        safe = text.replace("&", "&amp;").replace("<", "&lt;")
        self._append_html(f'<span class="system">⬩ {safe}</span>')

    # Internal shit

    def _append_html(self, html: str):
        """
        Append HTML to the history box, scrolling to the bottom.

        Args:
            html (str): HTML snippet to append (should be a <div> or similar block element).
        """
        cursor = self._history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(html + "<br/>")
        self._history.setTextCursor(cursor)
        self._history.ensureCursorVisible()

    def _on_send(self):
        """
        Handle the user pressing Enter or clicking Send:
        emit message_send signal with the input text, then clear the input.
        """
        text = self._input.text().strip()
        if text:
            self._input.clear()
            self.message_send.emit(text)
