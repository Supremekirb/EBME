from PySide6.QtWidgets import QTreeWidgetItem

import src.misc.icons as icons


class MapChange:
    def __init__(self, tileset: int, changes: list["MapChangeEvent"]):
        self.tileset = tileset
        self.events = changes

class MapChangeEvent:
    def __init__(self, tileset: int, flag: int, changes: list["TileChange"], comment: str=None):
        self.tileset = tileset
        self.flag = flag
        self.changes = changes
        self.comment = comment
        

class TileChange:
    def __init__(self, before: int, after: int):
        self.before = before
        self.after = after
        
        
class MapChangeEventListItem(QTreeWidgetItem):
    def __init__(self, event: MapChangeEvent):
        super().__init__()
        self.event = event
        self.updateFlagText()
        self.createChildren()
        self.refreshChildren()
        self.setIcon(0, icons.ICON_FLAG)
        
    def updateFlagText(self):
        self.setText(0, str(self.event.flag) if self.event.flag < 0x8000 else f"{self.event.flag - 0x8000} (Inverted)")
    
    def createChildren(self):
        for i in range(self.childCount()):
            self.removeChild(i)
        
        changes = []
        for j in self.event.changes:
            entry = TileChangeListItem(j)
            changes.append(entry)
        self.addChildren(changes)
    
    def refreshChildren(self):
        # Doesn't recalculate if children exist or not
        for i in range(self.childCount()):
            child = self.child(i)
            if isinstance(child, TileChangeListItem):
                child.updateChangeText()

class TileChangeListItem(QTreeWidgetItem):
    def __init__(self, change: TileChange):
        super().__init__()
        self.change = change
        self.updateChangeText()
        self.setIcon(0, icons.ICON_TILE_CHANGE)
        
    def updateChangeText(self):
        self.setText(0, f"{self.change.before} → {self.change.after}")

    def parent(self) -> MapChangeEventListItem:
        return super().parent()