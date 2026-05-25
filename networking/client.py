"""
networking/client.py

Peer-side networking.  Opens three TCP connections to the host server
(chat, video, audio) and spins up receive threads for each.

Signals propagate incoming data to the UI layer safely.
"""

import socket
import threading

from PyQt6.QtCore import QObject, pyqtSignal

from constants import (
    HOST_CHAT_PORT, HOST_VIDEO_PORT, HOST_AUDIO_PORT,
    TAG_CHAT, TAG_JOIN, TAG_LEAVE, TAG_ROSTER,
    TAG_VIDFRM, TAG_PING,
)
from networking.protocol import (
    recv_message, pack_message,
    make_join, make_chat, make_video_frame,
    parse_chat, parse_join, parse_leave, parse_roster, parse_video_frame,
)


class ClientSignals(QObject):
    connected       = pyqtSignal(list)        # initial roster [str, ...]
    user_joined     = pyqtSignal(str)
    user_left       = pyqtSignal(str)
    chat_received   = pyqtSignal(str, str)    # sender, text
    video_frame     = pyqtSignal(str, bytes)  # name, JPEG bytes
    audio_received  = pyqtSignal(bytes)       # raw PCM
    disconnected    = pyqtSignal(str)         # reason
    error           = pyqtSignal(str)


class PeerClient:
    """
    Manages a peer's outbound connections to the meeting server.
    Call connect() which blocks briefly then returns (or raises).
    """

    def __init__(self, name: str, host_ip: str, signals: ClientSignals):
        self.name      = name
        self.host_ip   = host_ip
        self.signals   = signals
        self._running  = False

        self._chat_sock  = None
        self._video_sock = None
        self._audio_sock = None
        self._chat_lock  = threading.Lock()
        self._video_lock = threading.Lock()
        self._audio_lock = threading.Lock()

    # ── Public API ─────────────────────────────────────────────────────────────

    def connect(self):
        """
        Open the three TCP connections and perform handshakes in the correct
        order so the server's pending maps are populated before video/audio
        JOINs arrive.

        Order:
          1. Open all three sockets.
          2. Send JOIN on chat → server adds session to _pending_video/_audio.
          3. Receive roster (confirms chat handshake complete on server side).
          4. Send JOIN on video and audio channels.
          5. Start receive threads.
        """
        self._chat_sock  = self._open(HOST_CHAT_PORT)
        self._video_sock = self._open(HOST_VIDEO_PORT)
        self._audio_sock = self._open(HOST_AUDIO_PORT)

        join_pkt = make_join(self.name)

        # Step 2: chat JOIN first — this makes the server populate pending maps
        self._chat_sock.sendall(join_pkt)

        # Step 3: wait for roster (server sends it after inserting into pending)
        tag, payload = recv_message(self._chat_sock)
        roster = parse_roster(payload) if tag == TAG_ROSTER else []

        # Step 4: NOW send JOIN on video + audio (pending maps are ready)
        self._video_sock.sendall(join_pkt)
        self._audio_sock.sendall(join_pkt)

        # Step 5: start receive threads
        self._running = True
        threading.Thread(target=self._recv_chat,  daemon=True).start()
        threading.Thread(target=self._recv_video, daemon=True).start()
        threading.Thread(target=self._recv_audio, daemon=True).start()

        self.signals.connected.emit(roster)

    def disconnect(self):
        self._running = False
        for s in [self._chat_sock, self._video_sock, self._audio_sock]:
            try:
                if s:
                    s.close()
            except OSError:
                pass

    def send_chat(self, text: str):
        pkt = make_chat(self.name, text)
        self._send(self._chat_sock, self._chat_lock, pkt)

    def send_video_frame(self, jpeg: bytes):
        pkt = make_video_frame(self.name, jpeg)
        self._send(self._video_sock, self._video_lock, pkt)

    def send_audio(self, pcm: bytes):
        pkt = pack_message(b"AUDI", pcm)
        self._send(self._audio_sock, self._audio_lock, pkt)

    # ── Private helpers ────────────────────────────────────────────────────────

    def _open(self, port: int) -> socket.socket:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((self.host_ip, port))
        s.settimeout(None)
        return s

    def _send(self, sock, lock, data: bytes):
        try:
            with lock:
                sock.sendall(data)
        except OSError:
            pass

    # ── Receive loops ─────────────────────────────────────────────────────────

    def _recv_chat(self):
        try:
            while self._running:
                tag, payload = recv_message(self._chat_sock)

                if tag == TAG_CHAT:
                    d = parse_chat(payload)
                    self.signals.chat_received.emit(d["sender"], d["text"])

                elif tag == TAG_JOIN:
                    self.signals.user_joined.emit(parse_join(payload))

                elif tag == TAG_LEAVE:
                    self.signals.user_left.emit(parse_leave(payload))

                elif tag == TAG_PING:
                    pass

        except (ConnectionError, OSError) as e:
            if self._running:
                self.signals.disconnected.emit(str(e))

    def _recv_video(self):
        try:
            while self._running:
                tag, payload = recv_message(self._video_sock)
                if tag == TAG_VIDFRM:
                    name, jpeg = parse_video_frame(payload)
                    self.signals.video_frame.emit(name, jpeg)
        except (ConnectionError, OSError):
            pass

    def _recv_audio(self):
        try:
            while self._running:
                tag, payload = recv_message(self._audio_sock)
                if tag == b"AUDI":
                    self.signals.audio_received.emit(payload)
        except (ConnectionError, OSError):
            pass
