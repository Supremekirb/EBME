from PySide6.QtGui import QUndoCommand

import src.misc.common as common
from src.objects.music import MapMusicEntryListItem, MapMusicHierarchyListItem


from PySide6.QtWidgets import QTreeWidget

# these ones are a little different because we actually only
# modify the visual representation of the music hierarchy.
# we only save to project data when the user hits the save button


class ActionChangeMapMusicTrack(QUndoCommand):
    def __init__(self, track: MapMusicEntryListItem, music: int, flag: int):
        super().__init__()
        self.setText("Change map music track")
        
        self.track = track
        self.music = music
        self.flag = flag
        
        self._music = track.music
        self._flag = track.flag
        
    def redo(self):
        self.track.music = self.music
        self.track.flag = self.flag
        self.track.setText(1, str(self.flag) if self.flag < 0x8000 else f"{self.flag-0x8000} (Inverted)")
        
    def undo(self):
        self.track.music = self._music
        self.track.flag = self._flag
        self.track.setText(1, str(self._flag) if self._flag < 0x8000 else f"{self._flag-0x8000} (Inverted)") 
        
    def id(self):
        return common.ACTIONINDEX.MAPMUSICCHANGE
    
    def mergeWith(self, other: QUndoCommand):
        if other.id() != common.ACTIONINDEX.MAPMUSICCHANGE:
            return False
        
        if other.track != self.track:
            return False
        
        self.music = other.music
        self.flag = other.flag
        
        return True
        
    
class ActionMoveMapMusicTrack(QUndoCommand):
    def __init__(self, tree: QTreeWidget, entry: MapMusicHierarchyListItem, track: MapMusicEntryListItem, target: int):
        super().__init__()
        self.setText("Move map music track")
        
        self.tree = tree
        self.entry = entry
        self.track = track
        self.target = target
        
        self._target = entry.indexOfChild(track)
        
    def redo(self):
        self.entry.removeChild(self.track)
        self.tree.clearSelection()
        self.entry.insertChild(self.target, self.track)
        
        self.tree.setCurrentItem(self.track)
        
    def undo(self):
        self.entry.removeChild(self.track)
        self.tree.clearSelection()
        self.entry.insertChild(self._target, self.track)
        
        self.tree.setCurrentItem(self.track)
        
    def id(self):
        return common.ACTIONINDEX.MAPMUSICMOVE
    
    def mergeWith(self, other: QUndoCommand):
        return False
    
class ActionAddMapMusicTrack(QUndoCommand):
    def __init__(self, tree: QTreeWidget, entry: MapMusicHierarchyListItem, index: int):
        super().__init__()
        self.setText("Add map music track")
        
        self.tree = tree
        self.entry = entry
        self.track = MapMusicEntryListItem(0, 1) 
        self.index = index
    
    def redo(self):
        self.entry.insertChild(self.index, self.track)
        self.tree.setCurrentItem(self.track)
    
    def undo(self):
        ActionDeleteMapMusicTrack.redo(self)  
    
    def id(self):
        return common.ACTIONINDEX.MAPMUSICADD
    
    def mergeWith(self, other: QUndoCommand):
        return False
    
class ActionDeleteMapMusicTrack(QUndoCommand):
    def __init__(self, tree: QTreeWidget, entry: MapMusicHierarchyListItem, track: MapMusicEntryListItem):
        super().__init__()
        self.setText("Delete map music track")
        
        self.tree = tree
        self.entry = entry
        self.track = track
        self.index = self.entry.indexOfChild(self.track)
    
    def redo(self):
        self.index = self.entry.indexOfChild(self.track)
        self.entry.removeChild(self.track)
        self.tree.setCurrentItem(self.entry.child(self.index) if self.index < self.entry.childCount() else self.index-1)
    
    def undo(self):
        ActionAddMapMusicTrack.redo(self)    
    
    def id(self):
        return common.ACTIONINDEX.MAPMUSICDELETE
    
    def mergeWith(self, other: QUndoCommand):
        return False