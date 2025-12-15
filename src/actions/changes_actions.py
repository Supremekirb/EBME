from PySide6.QtGui import QUndoCommand

import src.misc.common as common
from src.objects.changes import MapChange, MapChangeEvent, TileChange, MapChangeEventListItem, TileChangeListItem
from src.coilsnake.project_data import ProjectData

class ActionChangeMapChangeEvent(QUndoCommand):
    def __init__(self, event: MapChangeEvent, flag: int, changes: list[TileChange], comment: str):
        super().__init__()
        self.setText("Change map change event")
        
        self.event = event
        
        self.flag = flag
        self.changes = changes
        self.comment = comment
        
        self._flag = event.flag
        self._changes = event.changes
        self._comment = event.comment
    
    def redo(self):
        self.event.flag = self.flag
        self.event.changes = self.changes
        self.event.comment = self.comment
        
    def undo(self):
        self.event.flag = self._flag
        self.event.changes = self._changes
        self.event.comment = self._comment
    
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.CHANGEMAPCHANGEEVENT:
            return False
        # operates on wrong sector
        if other.event != self.event:
            return False
        # 'changes' list mismatches
        if other.changes != self.changes:
            return False
        # success
        self.flag = other.flag
        self.changes = other.changes
        self.comment = other.comment
        return True

    def id(self):
        return common.ACTIONINDEX.CHANGEMAPCHANGEEVENT