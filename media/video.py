"""
media/video.py

VideoThread — captures frames from the local webcam, compresses them to
JPEG, and emits them for sending over the network.

KEY FIXES vs original:
  1. Windows / MSMF deadlock: the original code called cv2.VideoCapture()
     inside enable() while holding self._lock, then run() also acquired the
     same lock before cap.read().  On Windows, MSMF requires capture init
     and read() to happen on the same OS thread, and the lock was preventing
     that.  Fixed by:
       • Never holding the lock across VideoCapture() or cap.read().
       • Using threading.Event flags to signal enable/disable to run().
       • Opening and closing the capture entirely inside run().
  2. Windows backend: try CAP_DSHOW first (DirectShow), fall back to default
     (MSMF) if unavailable.  CAP_DSHOW is more reliable on most Windows systems.
  3. jpeg_to_qpixmap: copy frame.data before passing to QImage to avoid
     a dangling-pointer crash on some builds.
"""

import platform
import threading
import time

import cv2
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui  import QImage, QPixmap

from constants import VIDEO_FPS, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_QUALITY

_ON_WINDOWS = platform.system() == "Windows"


class VideoSignals(QObject):
    frame_ready = pyqtSignal(bytes)   # JPEG-compressed bytes


class VideoThread(threading.Thread):
    """
    Captures webcam frames on a background thread.

    Control flow:
      enable()  → sets _enable_event; run() opens the capture and starts reading.
      disable() → sets _disable_event; run() closes the capture and waits.
      stop()    → sets _stop_event; run() exits.

    The run() loop owns the VideoCapture object exclusively — no locks needed.
    """

    def __init__(self):
        super().__init__(daemon=True, name="VideoCapture")
        self.signals        = VideoSignals()
        self._stop_event    = threading.Event()
        self._enable_event  = threading.Event()
        self._disable_event = threading.Event()
        self._enabled       = False   # current state inside run()

    # ── Control API (called from any thread) ───────────────────────────────────

    def enable(self):
        self._disable_event.clear()
        self._enable_event.set()

    def disable(self):
        self._enable_event.clear()
        self._disable_event.set()

    def stop(self):
        self._stop_event.set()
        self._enable_event.set()    # unblock any wait()
        self._disable_event.set()

    # ── Thread entry (runs entirely on the capture thread) ────────────────────

    def run(self):
        cap = None
        interval = 1.0 / VIDEO_FPS

        while not self._stop_event.is_set():

            # ── Waiting for enable ────────────────────────────────────────────
            if not self._enabled:
                self._enable_event.wait(timeout=0.2)
                if self._stop_event.is_set():
                    break
                if not self._enable_event.is_set():
                    continue

                # Open capture on THIS thread (required by MSMF on Windows)
                cap = self._open_capture()
                if cap is None or not cap.isOpened():
                    # Camera unavailable — wait and retry
                    if cap:
                        cap.release()
                    cap = None
                    time.sleep(1.0)
                    continue

                self._enabled = True
                self._enable_event.clear()

            # ── Active capture loop ───────────────────────────────────────────
            if self._disable_event.is_set():
                self._disable_event.clear()
                self._enabled = False
                if cap:
                    cap.release()
                    cap = None
                continue

            t0 = time.monotonic()

            if cap and cap.isOpened():
                ok, frame = cap.read()
                if ok:
                    ok2, buf = cv2.imencode(
                        ".jpg", frame,
                        [cv2.IMWRITE_JPEG_QUALITY, VIDEO_QUALITY],
                    )
                    if ok2:
                        self.signals.frame_ready.emit(bytes(buf))
                else:
                    # Camera disconnected mid-session
                    cap.release()
                    cap = None
                    self._enabled = False

            elapsed = time.monotonic() - t0
            sleep_t = interval - elapsed
            if sleep_t > 0:
                time.sleep(sleep_t)

        # Cleanup
        if cap and cap.isOpened():
            cap.release()

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _open_capture() -> cv2.VideoCapture | None:
        """
        Open the first available webcam.
        On Windows try DirectShow first (more reliable than MSMF for many devices).
        """
        if _ON_WINDOWS:
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap.release()
                cap = cv2.VideoCapture(0)   # fall back to MSMF
        else:
            cap = cv2.VideoCapture(0)

        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  VIDEO_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, VIDEO_HEIGHT)
            cap.set(cv2.CAP_PROP_FPS,          VIDEO_FPS)

        return cap


# ── Stateless decoder helper ──────────────────────────────────────────────────

def jpeg_to_qpixmap(jpeg_bytes: bytes,
                    w: int = VIDEO_WIDTH,
                    h: int = VIDEO_HEIGHT) -> QPixmap:
    """Decode JPEG bytes → QPixmap, resized to (w, h)."""
    arr   = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        return QPixmap()
    frame = cv2.resize(frame, (w, h))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h_px, w_px, ch = frame.shape
    # .copy() ensures the buffer stays alive for QImage
    img = QImage(
        frame.copy().data,
        w_px, h_px, ch * w_px,
        QImage.Format.Format_RGB888,
    )
    return QPixmap.fromImage(img)
