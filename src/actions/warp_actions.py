from typing import TYPE_CHECKING

from PySide6.QtGui import QUndoCommand

import src.misc.common as common
from src.misc.coords import EBCoords

if TYPE_CHECKING:
    from src.objects.warp import Teleport, Warp

class ActionMoveWarp(QUndoCommand):
    def __init__(self, warp: "Warp", coords: EBCoords):
        super().__init__()
        self.setText("Move Warp")

        self.warp = warp
        self.coords = coords

        self._coords = warp.dest
        self.fromSidebar = False
        
    def redo(self):
        self.warp.dest = self.coords
        
    def undo(self):
        self.warp.dest = self._coords
        
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.WARPMOVESIDEBAR:
            return False
        # operates on wrong warp
        if other.warp != self.warp:
            return False
        # success
        self.coords = other.coords
        return True
    
    def id(self):
        if self.fromSidebar:
            return common.ACTIONINDEX.WARPMOVESIDEBAR
        else: return common.ACTIONINDEX.WARPMOVE
        
        
class ActionUpdateWarp(QUndoCommand):
    def __init__(self, warp: "Warp", dir: int, style: int, unknown: int, comment: str):
        super().__init__()
        self.setText("Update Warp")

        self.warp = warp
        self.dir = dir
        self.style = style
        self.unknown = unknown
        self.comment = comment

        self._dir = warp.dir
        self._style = warp.style
        self._unknown = warp.unknown
        self._comment = warp.comment
        
    def redo(self):
        self.warp.dir = self.dir
        self.warp.style = self.style
        self.warp.unknown = self.unknown
        self.warp.comment = self.comment
        
    def undo(self):
        self.warp.dir = self._dir
        self.warp.style = self._style
        self.warp.unknown = self._unknown
        self.warp.comment = self._comment
        
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.WARPUPDATE:
            return False
        # operates on wrong warp
        if other.warp != self.warp:
            return False
        # success
        self.dir = other.dir
        self.style = other.style
        self.unknown = other.unknown
        self.comment = other.comment
        return True
    
    def id(self):
        return common.ACTIONINDEX.WARPUPDATE
    
    
class ActionMoveTeleport(ActionMoveWarp):
    def __init__(self, teleport: "Teleport", coords: EBCoords):
        super().__init__(teleport, coords)
        self.teleport = self.warp
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.TELEPORTMOVESIDEBAR:
            return False
        # operates on wrong warp
        if other.warp != self.warp:
            return False
        # success
        self.coords = other.coords
        return True
    
        
    def id(self):
        if self.fromSidebar:
            return common.ACTIONINDEX.TELEPORTMOVESIDEBAR
        else: return common.ACTIONINDEX.TELEPORTMOVE
        
class ActionUpdateTeleport(QUndoCommand):
    def __init__(self, teleport: "Teleport", flag: int, name: str):
        super().__init__()
        self.setText("Update Teleport")

        self.teleport = teleport
        self.flag = flag
        self.name = name

        self._flag = teleport.flag
        self._name = teleport.name
        
    def redo(self):
        self.teleport.flag = self.flag
        self.teleport.name = self.name
        
    def undo(self):
        self.teleport.flag = self._flag
        self.teleport.name = self._name
        
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.TELEPORTUPDATE:
            return False
        # operates on wrong warp
        if other.teleport != self.teleport:
            return False
        # success
        self.flag = other.flag
        self.name = other.name
        return True
    
    def id(self):
        return common.ACTIONINDEX.TELEPORTUPDATE