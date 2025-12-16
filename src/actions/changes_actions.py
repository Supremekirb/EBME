from PySide6.QtGui import QUndoCommand

import src.misc.common as common
from src.objects.changes import MapChange, MapChangeEvent, TileChange, MapChangeEventListItem, TileChangeListItem
from src.coilsnake.project_data import ProjectData

class ActionChangeMapChangeEvent(QUndoCommand):
    def __init__(self, event: MapChangeEvent, flag: int, changes: list[TileChange], comment: str):
        super().__init__()
        self.setText("Edit map change event")
        
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
        # operates on wrong event
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

class ActionChangeTileChange(QUndoCommand):
    def __init__(self, change: TileChange, before: int, after: int):
        super().__init__()
        self.setText("Edit tile change")
        
        self.change = change
        
        self.before = before
        self.after = after
        
        self._before = change.before
        self._after = change.after
        
    def redo(self):
        self.change.before = self.before
        self.change.after = self.after
    
    def undo(self):
        self.change.before = self._before
        self.change.after = self._after
    
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.CHANGETILECHANGE:
            return False
        # operates on wrong change
        if other.change != self.change:
            return False
        # 'changes' list mismatches
        # success
        self.before = other.before
        self.after = other.after
        return True