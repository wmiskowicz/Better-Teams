"""
ui/meeting_window.py

The main room window.  Wires together:
  • VideoGrid  (left panel)
  • ChatPanel  (right panel)
  • ControlsBar (bottom)
  • VideoThread / AudioCapture / AudioPlayback (media threads)
  • MeetingServer (if hosting) or PeerClient (if joining)

Constructor params:
  name      — local display name
  mode      — "host" | "peer"
  host_ip   — required when mode == "peer"
"""

import threading

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui  import QColor

from constants      import WINDOW_MIN_W, WINDOW_MIN_H, APP_NAME, VIDEO_FPS
from ui.video_grid  import VideoGrid
from ui.chat_panel  import ChatPanel
from ui.controls_bar import ControlsBar
from media.video    import VideoThread, jpeg_to_qpixmap
from media.audio    import AudioCaptureThread, AudioPlaybackThread


class MeetingWindow(QMainWindow):

    def __init__(self, name: str, mode: str, host_ip: str = "127.0.0.1"):
        super().__init__()
        self.local_name = name
        self.mode       = mode        # "host" | "peer"
        self.host_ip    = host_ip

        self.setWindowTitle(f"{APP_NAME} — {name}")
        self.setMinimumSize(WINDOW_MIN_W, WINDOW_MIN_H)
        self.resize(WINDOW_MIN_W + 100, WINDOW_MIN_H + 80)
        self._apply_theme()

        self._build_ui()
        self._init_media()
        self._init_network()

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(3)
        splitter.setStyleSheet("QSplitter::handle { background: #2e3240; }")

        # Left: video grid
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(0)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.video_grid = VideoGrid()
        left_layout.addWidget(self.video_grid, stretch=1)

        # Right: chat
        self.chat_panel = ChatPanel()
        self.chat_panel.setMinimumWidth(260)
        self.chat_panel.message_send.connect(self._on_send_chat)

        splitter.addWidget(left_widget)
        splitter.addWidget(self.chat_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        root.addWidget(splitter, stretch=1)

        # Bottom controls
        self.controls = ControlsBar()
        self.controls.mute_toggled.connect(self._on_mute_toggled)
        self.controls.camera_toggled.connect(self._on_camera_toggled)
        root.addWidget(self.controls)

        # Add local tile immediately
        self._local_tile = self.video_grid.add_tile(self.local_name, is_local=True)

    def _apply_theme(self):
        self.setStyleSheet("""
            QMainWindow { background: #12141a; }
            QWidget      { background: #12141a; color: #d4d8e8; }
        """)

    # ── Media init ─────────────────────────────────────────────────────────────

    def _init_media(self):
        # Video capture
        self._video_thread = VideoThread()
        self._video_thread.signals.frame_ready.connect(self._on_local_frame)
        self._video_thread.start()

        # Audio
        self._audio_cap = AudioCaptureThread()
        self._audio_cap.signals.chunk_ready.connect(self._on_audio_captured)
        self._audio_cap.start()

        self._audio_play = AudioPlaybackThread()
        self._audio_play.start()

    # ── Network init ───────────────────────────────────────────────────────────

    def _init_network(self):
        if self.mode == "host":
            self._init_host()
        else:
            self._init_peer()

    def _init_host(self):
        from networking.server import MeetingServer, ServerSignals
        self._srv_signals = ServerSignals()
        self._srv_signals.user_joined.connect(self._on_peer_joined)
        self._srv_signals.user_left.connect(self._on_peer_left)
        self._srv_signals.chat_received.connect(self._on_chat_received)
        self._srv_signals.video_frame.connect(self._on_remote_frame)
        self._srv_signals.audio_received.connect(self._on_remote_audio) # ADD THIS LINE

        self._server = MeetingServer(self.local_name, self._srv_signals)
        self._server.start()

        self.chat_panel.add_system(f"Room started. Waiting for participants…")

    def _init_peer(self):
        from networking.client import PeerClient, ClientSignals
        self._cli_signals = ClientSignals()
        self._cli_signals.connected.connect(self._on_connected)
        self._cli_signals.user_joined.connect(self._on_peer_joined)
        self._cli_signals.user_left.connect(self._on_peer_left)
        self._cli_signals.chat_received.connect(self._on_chat_received)
        self._cli_signals.video_frame.connect(self._on_remote_frame)
        self._cli_signals.audio_received.connect(self._on_remote_audio)
        self._cli_signals.disconnected.connect(self._on_disconnected)
        self._cli_signals.error.connect(self._on_net_error)

        self._client = PeerClient(self.local_name, self.host_ip, self._cli_signals)
        threading.Thread(target=self._client.connect, daemon=True).start()

    # ── Local media slots ──────────────────────────────────────────────────────

    @pyqtSlot(bytes)
    def _on_local_frame(self, jpeg: bytes):
        """Show local frame in local tile; relay to network."""
        # Use a sensible default size; the tile widget will scale it via paintEvent
        px = jpeg_to_qpixmap(jpeg)
        self._local_tile.update_frame(px)

        # Send to server/peers
        if self.mode == "host" and hasattr(self, "_server"):
            self._server.broadcast_video(self.local_name, jpeg)
        elif self.mode == "peer" and hasattr(self, "_client"):
            self._client.send_video_frame(jpeg)

    @pyqtSlot(bytes)
    def _on_audio_captured(self, pcm: bytes):
        if self.mode == "host" and hasattr(self, "_server"):
            self._server.broadcast_audio(pcm)
        elif self.mode == "peer" and hasattr(self, "_client"):
            self._client.send_audio(pcm)

    # ── Remote media slots ─────────────────────────────────────────────────────

    @pyqtSlot(str, bytes)
    def _on_remote_frame(self, name: str, jpeg: bytes):
        tile = self.video_grid.get_tile(name)
        if tile is None:
            tile = self.video_grid.add_tile(name, is_local=False)
        px = jpeg_to_qpixmap(jpeg)
        tile.update_frame(px)

    @pyqtSlot(bytes)
    def _on_remote_audio(self, pcm: bytes):
        self._audio_play.put(pcm)

    # ── Network event slots ────────────────────────────────────────────────────

    @pyqtSlot(list)
    def _on_connected(self, roster: list):
        self.chat_panel.add_system("Connected to the meeting.")
        for name in roster:
            if name == self.local_name:
                continue
            if self.video_grid.get_tile(name) is None:
                self.video_grid.add_tile(name)
            self.chat_panel.add_system(f"{name} is already in the room.")

    @pyqtSlot(str)
    def _on_peer_joined(self, name: str):
        if name == self.local_name:
            return   # don't create a second tile for ourselves
        if self.video_grid.get_tile(name) is None:
            self.video_grid.add_tile(name)
        self.chat_panel.add_system(f"{name} has joined the room.")

    @pyqtSlot(str)
    def _on_peer_left(self, name: str):
        self.video_grid.remove_tile(name)
        self.chat_panel.add_system(f"{name} has left the room.")

    @pyqtSlot(str, str)
    def _on_chat_received(self, sender: str, text: str):
        self.chat_panel.add_message(sender, text)

    @pyqtSlot(str)
    def _on_disconnected(self, reason: str):
        self.chat_panel.add_system(f"Disconnected: {reason}")

    @pyqtSlot(str)
    def _on_net_error(self, msg: str):
        self.chat_panel.add_system(f"Network error: {msg}")

    # ── UI control slots ───────────────────────────────────────────────────────

    @pyqtSlot(str)
    def _on_send_chat(self, text: str):
        # Show locally
        self.chat_panel.add_message(self.local_name, text)
        # Send
        if self.mode == "host" and hasattr(self, "_server"):
            from networking.protocol import make_chat, pack_message, TAG_CHAT
            raw = make_chat(self.local_name, text)
            self._server.broadcast_chat(self.local_name, text, raw)
        elif self.mode == "peer" and hasattr(self, "_client"):
            self._client.send_chat(text)

    @pyqtSlot(bool)
    def _on_mute_toggled(self, muted: bool):
        if muted:
            self._audio_cap.disable()
        else:
            self._audio_cap.enable()

    @pyqtSlot(bool)
    def _on_camera_toggled(self, disabled: bool):
        if disabled:
            self._video_thread.disable()
            self._local_tile.set_camera_active(False)
        else:
            self._video_thread.enable()
            self._local_tile.set_camera_active(True)

    # ── Cleanup ────────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._video_thread.stop()
        self._audio_cap.stop()
        self._audio_play.stop()
        if self.mode == "peer" and hasattr(self, "_client"):
            self._client.disconnect()
        if self.mode == "host" and hasattr(self, "_server"):
            self._server.stop()
        event.accept()
