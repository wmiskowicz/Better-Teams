"""
ui/video_tile.py

A single participant video tile.  Displays:
  • a live QPixmap when the camera is active
  • an avatar / name card when the camera is off
  • the participant's display name always overlaid at the bottom
"""

from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore    import Qt, QTimer
from PyQt6.QtGui     import (
    QPixmap, QPainter, QColor, QFont, QPen, QBrush,
)


TILE_BG        = QColor("#1a1d23")
TILE_BORDER    = QColor("#2e3240")
AVATAR_BG      = QColor("#2a3050")
NAME_BAR_COLOR = QColor(0, 0, 0, 160)
ACCENT         = QColor("#4f8ef7")


class VideoTile(QWidget):
    """
    One participant tile in the video grid.
    Call update_frame(jpeg_bytes) to display live video.
    Call set_camera_active(False) to switch to the avatar view.
    """

    def __init__(self, name: str, is_local: bool = False, parent=None):
        super().__init__(parent)
        self.participant_name = name
        self.is_local         = is_local
        self._pixmap          = None
        self._pixmap_timeout  = 5000 # ms
        self._camera_on       = False
        
        self._timer = QTimer(self)
        self._timer.setInterval(self._pixmap_timeout)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)

        self.setMinimumSize(160, 120)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

    # Public API

    def update_frame(self, pixmap: QPixmap):
        """Update the video tile with a new camera frame.  The pixmap will be scaled to fit the tile while maintaining aspect ratio.

        Args:
            pixmap (QPixmap): The new video frame to display on the tile.
        """
        self._pixmap = pixmap
        self._camera_on = True
        self._timer.start()
        self.update()

    def set_camera_active(self, active: bool):
        """Switch between live video and avatar view.  If deactivating the camera, the current pixmap will be cleared.

        Args:
            active (bool): Whether the camera is active (True) or not (False).
        """
        if not active:
            self._pixmap = None
            self._timer.stop()
        self._camera_on = active
        self.update()

    def _on_timeout(self):
        """Triggered automatically if no frame is received for 5000ms."""
        self.set_camera_active(False)

    # Paint Event

    def paintEvent(self, event):
        """
        Paint the video tile.  Displays either:
          • a live video frame (scaled to fit)
          • an avatar view (circle with initials)
          • a name bar at the bottom
          • a "YOU" badge for the local participant

        Args:
            event (_type_): The paint event (not used directly since we call update() to trigger a repaint).
        """
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()

        # Background
        p.fillRect(r, TILE_BG)

        if self._camera_on and self._pixmap and not self._pixmap.isNull():
            # Scale and center the camera frame
            scaled = self._pixmap.scaled(
                r.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (r.width()  - scaled.width())  // 2
            y = (r.height() - scaled.height()) // 2
            p.drawPixmap(x, y, scaled)
        else:
            # Avatar view
            self._draw_avatar(p, r)

        # Name bar at bottom
        self._draw_name_bar(p, r)

        # Border
        p.setPen(QPen(TILE_BORDER, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(r.adjusted(0, 0, -1, -1))

        # "YOU" badge for local tile
        if self.is_local:
            self._draw_you_badge(p, r)

    def _draw_avatar(self, p: QPainter, r):
        """Draw the avatar view (circle with initials).

        Args:
            p (QPainter): The QPainter to draw with.
            r (_type_): The QRect of the tile (available as self.rect()).
        """
        cx, cy = r.center().x(), r.center().y()
        radius = min(r.width(), r.height()) // 5

        # Circle background
        p.setBrush(QBrush(AVATAR_BG))
        p.setPen(QPen(ACCENT, 2))
        p.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

        # Initials
        initials = "".join(w[0].upper() for w in self.participant_name.split()[:2]) or "?"
        font = QFont("Arial", max(10, radius // 2), QFont.Weight.Bold)
        p.setFont(font)
        p.setPen(QPen(QColor("white")))
        p.drawText(
            cx - radius, cy - radius,
            radius * 2, radius * 2,
            Qt.AlignmentFlag.AlignCenter,
            initials,
        )

    def _draw_name_bar(self, p: QPainter, r):
        """Draw the name bar at the bottom of the tile.

        Args:
            p (QPainter): The QPainter to draw with.
            r (_type_): The QRect of the tile (available as self.rect()).
        """
        bar_h = 26
        bar_rect_y = r.bottom() - bar_h
        p.fillRect(r.left(), bar_rect_y, r.width(), bar_h, NAME_BAR_COLOR)

        font = QFont("Arial", 9)
        font.setBold(True)
        p.setFont(font)
        p.setPen(QPen(QColor("white")))
        name = self.participant_name
        if self.is_local:
            name += " (You)"
        p.drawText(
            r.left() + 6, bar_rect_y,
            r.width() - 12, bar_h,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            name,
        )

    def _draw_you_badge(self, p: QPainter, r):
        """Draw the "YOU" badge in the top-right corner of the local participant's tile.

        Args:
            p (QPainter): The QPainter to draw with.
            r (_type_): The QRect of the tile (available as self.rect()).
        """
        badge_w, badge_h = 34, 16
        bx = r.right() - badge_w - 6
        by = r.top() + 6
        p.setBrush(QBrush(ACCENT))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(bx, by, badge_w, badge_h, 4, 4)
        font = QFont("Arial", 7, QFont.Weight.Bold)
        p.setFont(font)
        p.setPen(QPen(QColor("white")))
        p.drawText(bx, by, badge_w, badge_h, Qt.AlignmentFlag.AlignCenter, "YOU")
