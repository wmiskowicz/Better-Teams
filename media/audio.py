"""
media/audio.py

AudioCaptureThread — reads from the local microphone and emits PCM chunks.
AudioPlaybackThread — receives PCM chunks and plays them through speakers.

KEY FIXES vs original:
  1. PortAudio's callback runs on a C-level thread that PyQt6 cannot safely
     emit signals from.  We now use a queue.Queue to transfer chunks from the
     C callback into a regular Python thread, which does the emit.
  2. AudioPlaybackThread no longer uses __import__("numpy") inside the loop.
  3. Proper numpy reshape so blocksize mismatches don't corrupt the stream.
"""

import queue
import threading
import time

import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal

from constants import AUDIO_RATE, AUDIO_CHANNELS, AUDIO_CHUNK

try:
    import sounddevice as sd
    _SD_AVAILABLE = True
except ImportError:
    _SD_AVAILABLE = False


class AudioSignals(QObject):
    chunk_ready = pyqtSignal(bytes)   # raw PCM int16 bytes


class AudioCaptureThread(threading.Thread):
    """
    Captures microphone audio on a background thread.

    Architecture:
      • PortAudio callback  → puts float32 frames into _cb_queue  (C thread, no Qt)
      • _emit_thread        → gets from _cb_queue, converts, emits chunk_ready signal
                              (Python thread — safe to emit Qt signals)
    """

    def __init__(self):
        super().__init__(daemon=True, name="AudioCapture")
        self.signals   = AudioSignals()
        self._active   = threading.Event()   # set = capture active
        self._running  = True
        self._cb_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=20)

    # ── Control ────────────────────────────────────────────────────────────────

    def enable(self):
        self._active.set()

    def disable(self):
        self._active.clear()
        # Drain the queue so stale audio doesn't play after unmute
        while not self._cb_queue.empty():
            try:
                self._cb_queue.get_nowait()
            except queue.Empty:
                break

    def stop(self):
        self._running = False
        self._active.set()   # unblock the emit thread if it's waiting

    # ── Thread entry ───────────────────────────────────────────────────────────

    def run(self):
        if not _SD_AVAILABLE:
            return

        # Spin up the emit thread BEFORE opening the stream
        emit_thread = threading.Thread(
            target=self._emit_loop, daemon=True, name="AudioEmit"
        )
        emit_thread.start()

        def _callback(indata: np.ndarray, frames: int, time_info, status):
            """Called by PortAudio on its own C thread — NO Qt calls here."""
            if self._active.is_set():
                try:
                    self._cb_queue.put_nowait(indata.copy())
                except queue.Full:
                    pass   # drop frame rather than block the audio thread

        try:
            with sd.InputStream(
                samplerate=AUDIO_RATE,
                channels=AUDIO_CHANNELS,
                dtype="float32",
                blocksize=AUDIO_CHUNK,
                callback=_callback,
            ):
                while self._running:
                    time.sleep(0.05)
        except Exception as exc:
            pass   # device not available — silently skip

        emit_thread.join(timeout=1)

    def _emit_loop(self):
        """Python thread: safe to emit Qt signals."""
        while self._running:
            try:
                indata = self._cb_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            # Convert float32 [-1, 1] → int16
            pcm = (np.clip(indata, -1.0, 1.0) * 32767).astype(np.int16).tobytes()
            self.signals.chunk_ready.emit(pcm)


class AudioPlaybackThread(threading.Thread):
    """
    Plays incoming PCM int16 audio through the default output device.
    Enqueue raw PCM bytes with put(pcm).
    """

    def __init__(self):
        super().__init__(daemon=True, name="AudioPlayback")
        self._queue: queue.Queue[bytes] = queue.Queue(maxsize=50)
        self._running = True

    def put(self, pcm: bytes):
        """Non-blocking enqueue; drops if buffer is full to avoid latency build-up."""
        try:
            self._queue.put_nowait(pcm)
        except queue.Full:
            pass

    def stop(self):
        self._running = False

    def run(self):
        if not _SD_AVAILABLE:
            return

        try:
            with sd.OutputStream(
                samplerate=AUDIO_RATE,
                channels=AUDIO_CHANNELS,
                dtype="int16",
                blocksize=AUDIO_CHUNK,
            ) as stream:
                while self._running:
                    try:
                        pcm = self._queue.get(timeout=0.1)
                    except queue.Empty:
                        continue

                    # Convert bytes → numpy int16, reshape to (frames, channels)
                    arr = np.frombuffer(pcm, dtype=np.int16)
                    # Guard against packets that aren't a whole number of frames
                    frames = len(arr) // AUDIO_CHANNELS
                    if frames == 0:
                        continue
                    arr = arr[: frames * AUDIO_CHANNELS].reshape(frames, AUDIO_CHANNELS)
                    stream.write(arr)

        except Exception:
            pass
