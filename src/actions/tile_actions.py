from PySide6.QtGui import QUndoCommand

import src.misc.common as common
from src.objects.tile import MapTile


class ActionPlaceTile(QUndoCommand):
    def __init__(self, maptile: MapTile, tile: int):
        super().__init__()
        self.setText("Place tile")

        self.maptile = maptile
        self.tile = tile

        self._tile = self.maptile.tile

    def redo(self):
        self.maptile.tile = self.tile

    def undo(self):
        self.maptile.tile = self._tile

    def mergeWith(self, other: QUndoCommand):
        return False

    def id(self):
        return common.ACTIONINDEX.TILEPLACE