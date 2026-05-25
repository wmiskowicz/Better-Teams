"""
ui/controls_bar.py

Bottom control bar with Mute / Camera toggle buttons.
Exposes:
  mute_toggled(bool)     — True = now muted
  camera_toggled(bool)   — True = now disabled
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore    import Qt, pyqtSignal
from PyQt6.QtGui     import QIcon
import os

_BTN_BASE = """
    QPushButton {{
        background: {bg};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 22px;
        font-size: 13px;
        font-weight: bold;
        min-width: 130px;
    }}
    QPushButton:hover {{ background: {hover}; }}
    QPushButton:pressed {{ background: {press}; }}
"""


def _style(bg, hover, press):
    return _BTN_BASE.format(bg=bg, hover=hover, press=press)


class ControlsBar(QWidget):
    mute_toggled   = pyqtSignal(bool)   # True = muted
    camera_toggled = pyqtSignal(bool)   # True = camera disabled

    def __init__(self, parent=None):
        super().__init__(parent)
        self._muted         = True   # start muted
        self._camera_off    = True   # start camera off

        self._build_ui()
        self._refresh()

    def _build_ui(self):
        """
        Build the UI elements of the controls bar,
        including the Mute and Camera toggle buttons,
        and set up their event handlers.
        """
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        self._mute_btn   = QPushButton()
        self._camera_btn = QPushButton()

        for btn in (self._mute_btn, self._camera_btn):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self._mute_btn.clicked.connect(self._toggle_mute)
        self._camera_btn.clicked.connect(self._toggle_camera)

        layout.addStretch()
        layout.addWidget(self._mute_btn)
        layout.addWidget(self._camera_btn)
        layout.addStretch()

        self.setStyleSheet("background: #12141a; border-top: 1px solid #2e3240;")
        self.setFixedHeight(58)

    def _refresh(self):
        """
        Update the text and styles of the Mute and Camera buttons based on the current state.
        """
        
        if self._muted:
            self._mute_btn.setIcon(QIcon(os.path.join("assets", "mic-svgrepo-com.svg")))
            self._mute_btn.setText("Unmute")
            self._mute_btn.setStyleSheet(_style("#27ae60", "#2ecc71", "#1e8449"))
        else:
            self._mute_btn.setIcon(QIcon(os.path.join("assets", "mic-off-svgrepo-com.svg")))
            self._mute_btn.setText("Mute")
            self._mute_btn.setStyleSheet(_style("#c0392b", "#e74c3c", "#a93226"))

        if self._camera_off:
            self._camera_btn.setIcon(QIcon(os.path.join("assets", "cam-svgrepo-com.svg")))
            self._camera_btn.setText("Start Camera")
            self._camera_btn.setStyleSheet(_style("#27ae60", "#2ecc71", "#1e8449"))
        else:
            self._camera_btn.setIcon(QIcon(os.path.join("assets", "cam-disabled-svgrepo-com.svg")))
            self._camera_btn.setText("Stop Camera")
            self._camera_btn.setStyleSheet(_style("#c0392b", "#e74c3c", "#a93226"))

    def _toggle_mute(self):
        self._muted = not self._muted
        self._refresh()
        self.mute_toggled.emit(self._muted)

    def _toggle_camera(self):
        self._camera_off = not self._camera_off
        self._refresh()
        self.camera_toggled.emit(self._camera_off)
