from PySide6.QtGui import QUndoCommand

import src.misc.common as common
from src.coilsnake.project_data import ProjectData
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


class ActionSwapTiles(QUndoCommand):
    def __init__(self, projectData: ProjectData, before: int, after: int, tileset: int):
        super().__init__()
        self.setText("Swap tiles")
        
        self.projectData = projectData
        self.before = before
        self.after = after
        self.tileset = tileset
        
    def redo(self):
        for i in self.projectData.tiles.flat:
            i: MapTile
            if i.tileset == self.tileset:
                if i.tile == self.before:
                    i.tile = self.after
                elif i.tile == self.after:
                    i.tile = self.before
        tileset = self.projectData.getTileset(self.tileset)
        tileset.swapTiles(self.before, self.after)
        self.projectData.clobberTileGraphicsCache(self.tileset)
    
    def undo(self):
        self.redo()
    
    def mergeWith(self, other: QUndoCommand):
        return False

    def id(self):
        return common.ACTIONINDEX.TILESWAP
