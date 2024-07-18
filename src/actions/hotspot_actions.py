from PySide6.QtGui import QUndoCommand
from typing import TYPE_CHECKING

import src.misc.common as common
from src.misc.coords import EBCoords

if TYPE_CHECKING:
    from src.objects.hotspot import Hotspot

class ActionChangeHotspotLocation(QUndoCommand):
    def __init__(self, hotspot: "Hotspot", start: EBCoords, end: EBCoords):
        super().__init__()
        self.setText("Change hotspot location")
        
        self.hotspot = hotspot
        self.start = start
        self.end = end
        
        self._start = hotspot.start
        self._end = hotspot.end
        
        self.fromSidebar = False
        
    def redo(self):
        self.hotspot.start = self.start
        self.hotspot.end = self.end
        
    def undo(self):
        self.hotspot.start = self._start
        self.hotspot.end = self._end
        
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.HOTSPOTMOVESIDEBAR:
            return False
        # operates on wrong hotspot
        if other.hotspot != self.hotspot:
            return False
        # success
        self.start = other.start
        self.end = other.end
        return True
    
    def id(self):
        if self.fromSidebar:
            return common.ACTIONINDEX.HOTSPOTMOVESIDEBAR
        else:
            return common.ACTIONINDEX.HOTSPOTMOVE

class ActionChangeHotspotColour(QUndoCommand):
    def __init__(self, hotspot: "Hotspot", colour: tuple[int, int, int]):
        super().__init__()
        self.setText("Change hotspot colour")
        
        self.hotspot = hotspot
        self.colour = colour
        
        self._colour = hotspot.colour
        
    def redo(self):
        self.hotspot.colour = self.colour
        
    def undo(self):
        self.hotspot.colour = self._colour
    
    def id(self):
        return common.ACTIONINDEX.HOTSPOTCOLOURUPDATE
    
class ActionChangeHotspotComment(QUndoCommand):
    def __init__(self, hotspot: "Hotspot", comment: str):
        super().__init__()
        self.setText("Change hotspot comment")
        
        self.hotspot = hotspot
        self.comment = comment
        
        self._comment = hotspot.comment
        
    def redo(self):
        self.hotspot.comment = self.comment
        
    def undo(self):
        self.hotspot.comment = self._comment
        
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.HOTSPOTCOMMENTUPDATE:
            return False
        # operates on wrong hotspot
        if other.hotspot != self.hotspot:
            return False
        # success
        self.comment = other.comment
        return True
        
    def id(self):
        return common.ACTIONINDEX.HOTSPOTCOMMENTUPDATE