"""
networking/server.py

The Host server.  Three listener threads accept incoming connections on the
chat, video, and audio ports.  All traffic is relayed to every other
connected client (broadcast hub model).

Signals are emitted via a ServerSignals object so the UI can react without
threading issues.
"""

import socket
import threading
import json
import time
import struct

from PyQt6.QtCore import QObject, pyqtSignal

from constants import (
    HOST_CHAT_PORT, HOST_VIDEO_PORT, HOST_AUDIO_PORT,
    MAX_PEERS, TCP_BACKLOG, BUFFER_SIZE,
    TAG_CHAT, TAG_JOIN, TAG_LEAVE, TAG_ROSTER,
    TAG_VIDFRM, TAG_PING,
)
from networking.protocol import (
    recv_message, pack_message, make_roster,
    parse_chat, parse_join, parse_leave, parse_video_frame,
    make_join, make_leave, make_video_frame,
)


class ServerSignals(QObject):
    user_joined    = pyqtSignal(str)          # display name
    user_left      = pyqtSignal(str)          # display name
    chat_received  = pyqtSignal(str, str)     # sender, text
    video_frame    = pyqtSignal(str, bytes)   # sender name, JPEG bytes
    audio_received = pyqtSignal(bytes)        # raw PCM (ADD THIS LINE)
    error          = pyqtSignal(str)


class ClientSession:
    """Holds the three sockets for one connected peer."""
    def __init__(self, name: str, chat_sock, video_sock=None, audio_sock=None):
        self.name       = name
        self.chat_sock  = chat_sock
        self.video_sock = video_sock
        self.audio_sock = audio_sock
        self.lock       = threading.Lock()

    def send_chat(self, data: bytes):
        try:
            with self.lock:
                self.chat_sock.sendall(data)
        except OSError:
            pass

    def send_video(self, data: bytes):
        if self.video_sock:
            try:
                self.video_sock.sendall(data)
            except OSError:
                pass

    def send_audio(self, data: bytes):
        if self.audio_sock:
            try:
                self.audio_sock.sendall(data)
            except OSError:
                pass


class MeetingServer:
    """
    Manages all server-side networking for a hosted meeting.
    Call start() to spin up listener threads.
    """

    def __init__(self, host_name: str, signals: ServerSignals):
        self.host_name  = host_name
        self.signals    = signals
        self._sessions: dict[str, ClientSession] = {}   # name → session
        self._sessions_lock = threading.Lock()
        self._running   = False

        # Pending half-open sessions waiting for video/audio sockets
        self._pending_video: dict[str, ClientSession] = {}
        self._pending_audio: dict[str, ClientSession] = {}
        self._pending_lock  = threading.Lock()

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self):
        self._running = True
        threading.Thread(target=self._listen_chat,  daemon=True).start()
        threading.Thread(target=self._listen_video, daemon=True).start()
        threading.Thread(target=self._listen_audio, daemon=True).start()

    def stop(self):
        self._running = False

    def broadcast_chat(self, sender: str, text: str, raw: bytes):
        """Relay a chat packet to all peers (called for host messages too)."""
        self._broadcast_all_chat(raw, exclude=None)

    def broadcast_video(self, name: str, jpeg: bytes):
        """Relay a video frame from the host to all peers.
        Already-framed with make_video_frame so peers' recv_video can parse it.
        """
        pkt = make_video_frame(name, jpeg)   # TAG_VIDFRM + len + (name_hdr + jpeg)
        self._broadcast_all_video(pkt, exclude=None)

    def broadcast_audio(self, pcm: bytes):
        """Relay audio from the host to all peers.
        Must be framed with pack_message so peers\'\' recv_message() can parse it.
        """
        raw = pack_message(b"AUDI", pcm)
        self._broadcast_all_audio(raw, exclude=None)

    # ── Chat listener ─────────────────────────────────────────────────────────

    def _listen_chat(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", HOST_CHAT_PORT))
        srv.listen(TCP_BACKLOG)
        while self._running:
            try:
                conn, addr = srv.accept()
                threading.Thread(
                    target=self._handle_chat_client,
                    args=(conn,), daemon=True
                ).start()
            except OSError:
                break

    def _handle_chat_client(self, sock):
        try:
            # First message must be JOIN
            tag, payload = recv_message(sock)
            if tag != TAG_JOIN:
                sock.close()
                return
            name = parse_join(payload)

            with self._sessions_lock:
                if len(self._sessions) >= MAX_PEERS:
                    sock.close()
                    return
                session = ClientSession(name=name, chat_sock=sock)
                self._sessions[name] = session

            with self._pending_lock:
                self._pending_video[name] = session
                self._pending_audio[name] = session

            # Build roster for the new peer:
            # all current peers EXCEPT itself, PLUS the host name
            with self._sessions_lock:
                current = [n for n in self._sessions.keys() if n != name]
            # Always include host at position 0
            roster = [self.host_name] + [n for n in current if n != self.host_name]
            sock.sendall(make_roster(roster))

            # Notify everyone (including UI) of the join
            join_pkt = pack_message(TAG_JOIN, name.encode())
            self._broadcast_all_chat(join_pkt, exclude=name)
            self.signals.user_joined.emit(name)

            # Pump messages from this peer
            while self._running:
                tag, payload = recv_message(sock)

                if tag == TAG_CHAT:
                    d = parse_chat(payload)
                    self.signals.chat_received.emit(d["sender"], d["text"])
                    raw = pack_message(TAG_CHAT, payload)
                    self._broadcast_all_chat(raw, exclude=name)

                elif tag == TAG_PING:
                    pass  # ignore

        except (ConnectionError, OSError):
            pass
        finally:
            self._remove_client(sock)

    # ── Video listener ────────────────────────────────────────────────────────

    def _listen_video(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", HOST_VIDEO_PORT))
        srv.listen(TCP_BACKLOG)
        while self._running:
            try:
                conn, addr = srv.accept()
                threading.Thread(
                    target=self._handle_video_client,
                    args=(conn,), daemon=True
                ).start()
            except OSError:
                break

    def _handle_video_client(self, sock):
        try:
            # First packet: JOIN with name so we can match sessions
            tag, payload = recv_message(sock)
            if tag != TAG_JOIN:
                sock.close()
                return
            name = parse_join(payload)

            # The chat thread may not have created the session yet — retry briefly
            session = None
            for _ in range(30):   # up to 3 seconds
                with self._pending_lock:
                    session = self._pending_video.pop(name, None)
                if session is not None:
                    break
                time.sleep(0.1)

            if session is None:
                sock.close()
                return
            session.video_sock = sock

            while self._running:
                tag, payload = recv_message(sock)
                if tag == TAG_VIDFRM:
                    peer_name, jpeg = parse_video_frame(payload)
                    self.signals.video_frame.emit(peer_name, jpeg)
                    raw = pack_message(TAG_VIDFRM, payload)
                    self._broadcast_all_video(raw, exclude=name)
        except (ConnectionError, OSError):
            pass

    # ── Audio listener ────────────────────────────────────────────────────────

    def _listen_audio(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", HOST_AUDIO_PORT))
        srv.listen(TCP_BACKLOG)
        while self._running:
            try:
                conn, addr = srv.accept()
                threading.Thread(
                    target=self._handle_audio_client,
                    args=(conn,), daemon=True
                ).start()
            except OSError:
                break

    def _handle_audio_client(self, sock):
        try:
            tag, payload = recv_message(sock)
            if tag != TAG_JOIN:
                sock.close()
                return
            name = parse_join(payload)

            with self._pending_lock:
                session = self._pending_audio.pop(name, None)
            if session is None:
                # Retry briefly — chat thread may not have run yet
                for _ in range(30):
                    time.sleep(0.1)
                    with self._pending_lock:
                        session = self._pending_audio.pop(name, None)
                    if session is not None:
                        break
            if session is None:
                sock.close()
                return
            session.audio_sock = sock

            while self._running:
                tag, payload = recv_message(sock)
                if tag == b"AUDI":
                    # 1. Send PCM to the Host's local speakers
                    self.signals.audio_received.emit(payload)
                    
                    # 2. Relay PCM to all other peers
                    raw = pack_message(b"AUDI", payload)
                    self._broadcast_all_audio(raw, exclude=name)
        except (ConnectionError, OSError):
            pass

    # ── Broadcast helpers ─────────────────────────────────────────────────────

    def _broadcast_all_chat(self, data: bytes, exclude: str | None):
        with self._sessions_lock:
            sessions = list(self._sessions.values())
        for s in sessions:
            if s.name != exclude:
                s.send_chat(data)

    def _broadcast_all_video(self, data: bytes, exclude: str | None):
        with self._sessions_lock:
            sessions = list(self._sessions.values())
        for s in sessions:
            if s.name != exclude:
                s.send_video(data)

    def _broadcast_all_audio(self, data: bytes, exclude: str | None):
        with self._sessions_lock:
            sessions = list(self._sessions.values())
        for s in sessions:
            if s.name != exclude:
                s.send_audio(data)

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def _remove_client(self, sock):
        name = None
        with self._sessions_lock:
            for n, s in list(self._sessions.items()):
                if s.chat_sock is sock:
                    name = n
                    del self._sessions[n]
                    break
        if name:
            leave_pkt = pack_message(TAG_LEAVE, name.encode())
            self._broadcast_all_chat(leave_pkt, exclude=None)
            self.signals.user_left.emit(name)
        try:
            sock.close()
        except OSError:
            pass
