"""
constants.py — Shared configuration for Teams-v2.
All networking ports, protocol tags, and runtime limits live here.
"""

# Network configuration
HOST_CHAT_PORT  = 50000   # TCP: text chat + control signals
HOST_VIDEO_PORT = 50001   # TCP: video frame relay
HOST_AUDIO_PORT = 50002   # UDP: audio stream relay

MAX_PEERS = 15            # host + 15 peers = 16 total
BUFFER_SIZE = 65536       # bytes per UDP audio packet
TCP_BACKLOG = 16

# Proto 4B tags for message types
TAG_CHAT    = b"CHAT"     # text message
TAG_JOIN    = b"JOIN"     # user joined  (payload = display name)
TAG_LEAVE   = b"LEAV"     # user left    (payload = display name)
TAG_ROSTER  = b"ROST"     # server → new peer: JSON roster of current users
TAG_VIDFRM  = b"VIDF"     # video frame chunk
TAG_PING    = b"PING"     # keep-alive

# Video and audio settings
VIDEO_FPS        = 15
VIDEO_WIDTH      = 320
VIDEO_HEIGHT     = 240
VIDEO_QUALITY    = 50     # JPEG compression quality (0-100)

AUDIO_RATE       = 16000  # Hz
AUDIO_CHANNELS   = 1
AUDIO_CHUNK      = 1024   # frames per buffer
AUDIO_FORMAT     = "int16"  # used by sounddevice

# UI stuff
APP_NAME = "Teams-v2"
WINDOW_MIN_W = 1100
WINDOW_MIN_H = 680
