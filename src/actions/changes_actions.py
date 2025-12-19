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


class ActionAddMapChangeEvent(QUndoCommand):
    def __init__(self, event: MapChangeEvent, tilesetEvents: MapChange, index: int):
        super().__init__()
        self.setText("Add new map change event")
        
        self.event = event
        self.tilesetEvents = tilesetEvents
        self.index = index
        
    def redo(self):
        self.tilesetEvents.events.insert(self.index, self.event)
    
    def undo(self):
        ActionRemoveMapChangeEvent.redo(self)
    
    def mergeWith(self, other: QUndoCommand):
        return False

    def id(self):
        return common.ACTIONINDEX.ADDMAPCHANGEEVENT


class ActionRemoveMapChangeEvent(QUndoCommand):
    def __init__(self, event: MapChangeEvent, tilesetEvents: MapChange):
        super().__init__()
        self.setText("Remove map change event")
        
        self.event = event
        self.tilesetEvents = tilesetEvents
        self.index = self.tilesetEvents.events.index(event)
        
    def redo(self):
        self.tilesetEvents.events.remove(self.event)
    
    def undo(self):
        ActionAddMapChangeEvent.redo(self)
    
    def mergeWith(self, other: QUndoCommand):
        return False

    def id(self):
        return common.ACTIONINDEX.REMOVEMAPCHANGEEVENT
        
class ActionMoveMapChangeEvent(QUndoCommand):
    def __init__(self, event: MapChangeEvent, tilesetEvents: MapChange, target: int):
        super().__init__()
        self.setText("Move map change event")
        
        self.event = event
        self.tilesetEvents = tilesetEvents
        self.target = target
        
        self._target = tilesetEvents.events.index(event)
        if self._target > self.target:
            self._target += 1
    
    def redo(self):
        self.tilesetEvents.moveEventTo(self.event, self.target)

    def undo(self):
        self.tilesetEvents.moveEventTo(self.event, self._target)

    def id(self):
        return common.ACTIONINDEX.MOVEMAPCHANGEEVENT

    def mergeWith(self, other: QUndoCommand):
        return False

class ActionChangeTileChange(QUndoCommand):
    def __init__(self, change: TileChange, event: MapChangeEvent, before: int, after: int):
        super().__init__()
        self.setText("Edit tile change")
        
        self.change = change
        self.event = event # Needs this so we know what to refresh in the UI on undo/redo
        
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
        return False

    def id(self):
        return common.ACTIONINDEX.CHANGETILECHANGE

class ActionAddTileChange(QUndoCommand):
    def __init__(self, event: MapChangeEvent, index: int, change: TileChange):
        super().__init__()
        self.setText("Add new tile change")
        
        self.event = event
        self.change = change
        self.index = index
        
    def redo(self):
        self.event.changes.insert(self.index, self.change)
    
    def undo(self):
        ActionRemoveTileChange.redo(self)
    
    def mergeWith(self, other: QUndoCommand):
        return False

    def id(self):
        return common.ACTIONINDEX.ADDTILECHANGE


class ActionRemoveTileChange(QUndoCommand):
    def __init__(self, event: MapChangeEvent, change: TileChange):
        super().__init__()
        self.setText("Remove tile change")
        
        self.event = event
        self.change = change
        self.index = self.event.changes.index(change)
        
    def redo(self):
        self.event.changes.remove(self.change)
    
    def undo(self):
        ActionAddTileChange.redo(self)
    
    def mergeWith(self, other: QUndoCommand):
        return False

    def id(self):
        return common.ACTIONINDEX.REMOVETILECHANGE


class ActionMoveTileChange(QUndoCommand):
    def __init__(self, event: MapChangeEvent, change: TileChange, target: int):
        super().__init__()
        self.setText("Move tile change")
        
        self.event = event
        self.change = change
        self.target = target
        
        self._target = event.changes.index(change)
        if self._target > self.target:
            self._target += 1
    
    def redo(self):
        self.event.moveTileChangeTo(self.change, self.target)

    def undo(self):
        self.event.moveTileChangeTo(self.change, self._target)

    def id(self):
        return common.ACTIONINDEX.MOVETILECHANGE

    def mergeWith(self, other: QUndoCommand):
        return False