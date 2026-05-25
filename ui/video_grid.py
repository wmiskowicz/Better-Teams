"""
ui/video_grid.py

VideoGrid — a QWidget that arranges VideoTile widgets in a dynamic grid.
Tiles re-flow automatically as participants join or leave (up to 16).
"""

import math

from PyQt6.QtWidgets import QWidget, QGridLayout
from PyQt6.QtCore    import Qt

from ui.video_tile import VideoTile


class VideoGrid(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QGridLayout(self)
        self._layout.setSpacing(4)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._tiles: dict[str, VideoTile] = {}   # name → tile

    # Public API

    def add_tile(self, name: str, is_local: bool = False) -> VideoTile:
        """Add a video tile for the given participant name, or return the existing one if already present.

        Args:
            name (str): Participant name (used as a unique identifier for the tile; will be displayed on the tile).
            is_local (bool, optional): Whether the tile represents the local participant. Defaults to False.

        Returns:
            VideoTile: The created or existing video tile.
        """
        if name in self._tiles:
            return self._tiles[name]
        tile = VideoTile(name, is_local=is_local)
        self._tiles[name] = tile
        self._relayout()
        return tile

    def remove_tile(self, name: str):
        """Remove the video tile for the given participant name, if it exists.

        Args:
            name (str): Participant name (used as a unique identifier for the tile).
        """
        tile = self._tiles.pop(name, None)
        if tile:
            self._layout.removeWidget(tile)
            tile.deleteLater()
            self._relayout()

    def get_tile(self, name: str) -> VideoTile | None:
        """Get the video tile for the given participant name, or None if it doesn't exist.

        Args:
            name (str): Participant name (used as a unique identifier for the tile).

        Returns:
            VideoTile | None: The video tile for the participant, or None if not found.
        """
        return self._tiles.get(name)

    def all_names(self) -> list[str]:
        """Get a list of all participant names currently in the grid.

        Returns:
            list[str]: List of participant names (keys of the tiles dictionary).
        """
        return list(self._tiles.keys())

    # Internals

    def _relayout(self):
        """
        Re-arrange the video tiles in a grid layout based on the current number of tiles.
        """
        # Clear the layout (without deleting the widgets, since we'll re-add them)
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)  # detach without deleting

        n = len(self._tiles)
        if n == 0:
            return

        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)

        for idx, tile in enumerate(self._tiles.values()):
            row = idx // cols
            col = idx % cols
            self._layout.addWidget(tile, row, col)
            tile.setParent(self)
            tile.show()

        # stretching: make all rows and columns expand equally
        for c in range(cols):
            self._layout.setColumnStretch(c, 1)
        for r in range(rows):
            self._layout.setRowStretch(r, 1)
