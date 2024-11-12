from PySide6.QtGui import QUndoCommand

import src.misc.common as common
from src.objects.music import MapMusicEntry, MapMusicHierarchy


class ActionChangeMapMusicTrack(QUndoCommand):
    def __init__(self, entry: MapMusicEntry, music: int, flag: int):
        super().__init__()
        self.setText("Change map music track")
        
        self.entry = entry
        self.music = music
        self.flag = flag
        
        self._music = entry.music
        self._flag = entry.flag
        
    def redo(self):
        self.entry.music = self.music
        self.entry.flag = self.flag
        
    def undo(self):
        self.entry.music = self._music
        self.entry.flag = self._flag
        
    def id(self):
        return common.ACTIONINDEX.MAPMUSICCHANGE
    
    def mergeWith(self, other: QUndoCommand):
        if other.id() != common.ACTIONINDEX.MAPMUSICCHANGE:
            return False
        
        if other.entry != self.entry:
            return False
        
        self.music = other.music
        self.flag = other.flag
        
        return True
        
    
class ActionMoveMapMusicTrack(QUndoCommand):
    def __init__(self, hierachy: MapMusicHierarchy, entry: MapMusicEntry, target: int):
        super().__init__()
        self.setText("Move map music track")
        
        self.hierachy = hierachy
        self.entry = entry
        self.target = target
        
        self._target = hierachy.entries.index(entry)
        if self._target > self.target:
            self._target += 1
        
    def redo(self):
        self.hierachy.moveEntryTo(self.entry, self.target)
        
    def undo(self):
        self.hierachy.moveEntryTo(self.entry, self._target)
        
    def id(self):
        return common.ACTIONINDEX.MAPMUSICMOVE
    
    def mergeWith(self, other: QUndoCommand):
        return False
    
class ActionAddMapMusicTrack(QUndoCommand):
    def __init__(self, hierachy: MapMusicHierarchy, index: int):
        super().__init__()
        self.setText("Add map music track")
        
        self.hierachy = hierachy
        self.entry = MapMusicEntry(0, 1) 
        self.index = index
    
    def redo(self):
        self.hierachy.entries.insert(self.index, self.entry)
    
    def undo(self):
        ActionDeleteMapMusicTrack.redo(self)  
    
    def id(self):
        return common.ACTIONINDEX.MAPMUSICADD
    
    def mergeWith(self, other: QUndoCommand):
        return False
    
class ActionDeleteMapMusicTrack(QUndoCommand):
    def __init__(self, hierachy: MapMusicHierarchy, entry: MapMusicEntry):
        super().__init__()
        self.setText("Delete map music track")
        
        self.hierachy = hierachy
        self.entry = entry
        self.index = self.hierachy.entries.index(entry)
        
    def redo(self):
        self.hierachy.entries.remove(self.entry)
    
    def undo(self):
        ActionAddMapMusicTrack.redo(self)    
    
    def id(self):
        return common.ACTIONINDEX.MAPMUSICDELETE
    
    def mergeWith(self, other: QUndoCommand):
        return False