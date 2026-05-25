"""
networking/protocol.py

Wire format for TCP streams:
    [4 bytes TAG][4 bytes big-endian payload length][N bytes payload]

Helpers for packing / unpacking messages and sending/receiving them
reliably over a blocking TCP socket.
"""

import json
import struct
from constants import (
    TAG_CHAT, TAG_JOIN, TAG_LEAVE, TAG_ROSTER,
    TAG_VIDFRM, TAG_PING,
)

HEADER_SIZE = 8  # 4 tag + 4 length


# ── Low-level framing ─────────────────────────────────────────────────────────

def pack_message(tag: bytes, payload: bytes = b"") -> bytes:
    """Return a complete framed message ready to send."""
    assert len(tag) == 4, "Tag must be exactly 4 bytes"
    return tag + struct.pack(">I", len(payload)) + payload


def recv_exact(sock, n: int) -> bytes:
    """Read exactly *n* bytes from *sock*; raises ConnectionError on EOF."""
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Socket closed during recv_exact")
        buf.extend(chunk)
    return bytes(buf)


def recv_message(sock):
    """
    Block until one complete framed message arrives.
    Returns (tag: bytes, payload: bytes) or raises ConnectionError.
    """
    header = recv_exact(sock, HEADER_SIZE)
    tag = header[:4]
    length = struct.unpack(">I", header[4:])[0]
    payload = recv_exact(sock, length) if length else b""
    return tag, payload


# ── High-level constructors ───────────────────────────────────────────────────

def make_chat(sender: str, text: str) -> bytes:
    data = json.dumps({"sender": sender, "text": text}).encode()
    return pack_message(TAG_CHAT, data)


def make_join(name: str) -> bytes:
    return pack_message(TAG_JOIN, name.encode())


def make_leave(name: str) -> bytes:
    return pack_message(TAG_LEAVE, name.encode())


def make_roster(users: list[str]) -> bytes:
    return pack_message(TAG_ROSTER, json.dumps(users).encode())


def make_video_frame(name: str, jpeg_bytes: bytes) -> bytes:
    """Prefix the frame with a 1-byte name-length + name, then JPEG."""
    name_bytes = name.encode()[:255]
    header = bytes([len(name_bytes)]) + name_bytes
    return pack_message(TAG_VIDFRM, header + jpeg_bytes)


def make_ping() -> bytes:
    return pack_message(TAG_PING)


# ── Parsers ───────────────────────────────────────────────────────────────────

def parse_chat(payload: bytes) -> dict:
    return json.loads(payload.decode())


def parse_join(payload: bytes) -> str:
    return payload.decode()


def parse_leave(payload: bytes) -> str:
    return payload.decode()


def parse_roster(payload: bytes) -> list[str]:
    return json.loads(payload.decode())


def parse_video_frame(payload: bytes) -> tuple[str, bytes]:
    name_len = payload[0]
    name = payload[1: 1 + name_len].decode()
    jpeg = payload[1 + name_len:]
    return name, jpeg


def send_message(sock, tag: bytes, payload: bytes = b""):
    """Thread-safe wrapper — just writes the framed bytes."""
    data = pack_message(tag, payload)
    sock.sendall(data)
