# Teams-v2

A lightweight, cross-platform voice / video / text chat application built with **Python 3** and **PyQt6**. Designed as a minimal Microsoft Teams alternative for LAN and localhost use.

---

## Features

| Feature | Detail |
| --- | --- |
| **Capacity** | 1 host + up to 15 peers (16 total) |
| **Video** | Live webcam tiles, JPEG-compressed, 15 fps |
| **Audio** | Full-duplex PCM via `sounddevice` |
| **Chat** | Real-time text broadcast with system notifications |
| **UI** | Responsive PyQt6 grid — tiles auto-reflow |
| **Default state** | Mic **muted** + camera **off** on entry |
| **Platforms** | Windows & Linux (macOS should work too) |

---

## Project Structure

```
teams-v2/
├── main.py                   ← Entry point
├── constants.py              ← Ports, limits, format config
├── requirements.txt
├── networking/
│   ├── __init__.py
│   ├── protocol.py           ← Wire framing, pack/unpack helpers
│   ├── server.py             ← Host server (3 listener threads)
│   └── client.py             ← Peer client (3 connections)
├── media/
│   ├── __init__.py
│   ├── video.py              ← VideoThread (capture + compress)
│   └── audio.py              ← AudioCaptureThread + AudioPlaybackThread
└── ui/
    ├── __init__.py
    ├── welcome_window.py     ← Setup / login screen
    ├── meeting_window.py     ← Main room, wires everything together
    ├── video_grid.py         ← Dynamic tile grid
    ├── video_tile.py         ← Single participant tile widget
    ├── chat_panel.py         ← Scrollable chat + input bar
    └── controls_bar.py       ← Mute / Camera toggle buttons
```

---

## Installation

```bash
# 1. Clone / unzip the project
cd teams-v2

# 2. Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
.venv\Scripts\activate         # Windows 
# Sometimes following command is required: Set-ExecutionPolicy Unrestricted

# 3. Install dependencies
pip install -r requirements
```

> **Linux note:** `sounddevice` requires PortAudio.
> Install it with: `sudo apt install libportaudio2`

---

## Running

```bash
python main.py
```

### Hosting a meeting

1. Select **Host a Meeting**.
2. Enter your name and click **Start Meeting**.
3. Share your LAN IP (e.g. `192.168.1.50`) with participants.

### Joining a meeting

1. Select **Join a Meeting**.
2. Enter your name and the host's IP address.
3. Click **Join Meeting**.

---

## Network Ports (TCP)

| Port  | Purpose              |
|-------|----------------------|
| 50000 | Chat & control (TCP) |
| 50001 | Video relay (TCP)    |
| 50002 | Audio relay (TCP)    |

Make sure these ports are open / not blocked by your firewall when using across a LAN.

---

## Threading Model

Each connected peer uses **3 dedicated threads** on both client and server:

```txt
VideoThread      → capture → compress → send
AudioCapture     → record  → send
AudioPlayback    ← receive → play

Server per-peer:
  handle_chat_client()   (thread)
  handle_video_client()  (thread)
  handle_audio_client()  (thread)
```

PyQt6 signals + slots are used to bridge background threads to the UI safely.

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Send chat message | `Enter` |

---

## Known Limitations & Future Work

- Audio mixing is additive (all peers heard, no per-user mute from host).
- No encryption — intended for trusted LAN use only.
- NAT traversal / internet use not implemented (TURN/STUN would be needed).
- Screen sharing not yet implemented.
