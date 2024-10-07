from copy import copy

from PySide6.QtGui import QUndoCommand

import src.misc.common as common
from src.coilsnake.fts_interpreter import Minitile, Tile


class ActionChangeBitmap(QUndoCommand):
    def __init__(self, minitile: Minitile, bitmap: list[str], isForeground: bool):
        super().__init__()
        self.setText("Draw minitile graphics")
        
        self.isForeground = isForeground
        
        self.minitile = minitile
        self.bitmap = bitmap
        
        if isForeground:
            if self.bitmap == minitile.foreground:
                self.setObsolete(True)
            self._bitmap = copy(minitile.foreground)
        else:
            if self.bitmap == minitile.background:
                self.setObsolete(True)
            self._bitmap = copy(minitile.background)
            
    def redo(self):
        if self.isForeground:
            self.minitile.foreground = self.bitmap
        else:
            self.minitile.background = self.bitmap
            
    def undo(self):
        if self.isForeground:
            self.minitile.foreground = self._bitmap
        else:
            self.minitile.background = self._bitmap
    
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.MINITILEDRAW:
            return False
        # operates on wrong minitile
        if other.minitile != self.minitile:
            return False
        # minitile data isnt the same
        if self.bitmap != other.bitmap:
            return False
        
        # success
        self.bitmap = other.bitmap
        return True
    
    def id(self):
        return common.ACTIONINDEX.MINITILEDRAW
    
class ActionChangeArrangement(QUndoCommand):
    def __init__(self, tile: Tile, metadata: int, index: int):
        super().__init__()
        self.setText("Change tile arrangement metadata")
        
        self.tile = tile
        self.index = index
        
        self.metadata = metadata
        
        self._metadata = tile.metadata[index]
        
        
    def redo(self):
        self.tile.metadata[self.index] = self.metadata
        
    def undo(self):
        self.tile.metadata[self.index] = self._metadata
    
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.ARRANGEMENTCHANGE:
            return False
        # operates on wrong tile
        if other.tile != self.tile:
            return False
        # operates on wrong index
        if other.index != self.index:
            return False
        # tile metadata isnt the same
        if self.metadata != other.metadata:
            return False
        
        # success
        self.metadata = other.metadata
        return True
    
    def id(self):
        return common.ACTIONINDEX.ARRANGEMENTCHANGE  
         