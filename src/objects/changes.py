from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

import src.misc.common as common
import src.misc.icons as icons


class MapChange:
    def __init__(self, tileset: int, changes: list["MapChangeEvent"]):
        self.tileset = tileset
        self.events = changes
    
    def moveEventTo(self, event: "MapChangeEvent|int", target: int):
        if isinstance(event, MapChangeEvent):
            index = self.events.index(event)
        else:
            index = event
        common.moveListItem(self.events, index, target)

class MapChangeEvent:
    def __init__(self, tileset: int, flag: int, changes: list["TileChange"], comment: str=None):
        self.tileset = tileset
        self.flag = flag
        self.changes = changes
        self.comment = comment
    
    def moveTileChangeTo(self, change: "TileChange|int", target: int):
        if isinstance(change, TileChange):
            index = self.changes.index(change)
        else:
            index = change
        common.moveListItem(self.changes, index, target)
        

class TileChange:
    def __init__(self, before: int, after: int):
        self.before = before
        self.after = after
        
        
class MapChangeEventListItem(QTreeWidgetItem):
    def __init__(self, event: MapChangeEvent):
        super().__init__()
        self.event = event
        self.updateFlagText()
        self.rebuildChildren()
        self.setIcon(0, icons.ICON_FLAG)
        self.setCheckState(1, Qt.CheckState.Unchecked)
        
    def updateFlagText(self):
        self.setText(0, str(self.event.flag) if self.event.flag < 0x8000 else f"{self.event.flag - 0x8000} (Inverted)")
    
    def rebuildChildren(self):
        for _ in range(self.childCount()):
            self.removeChild(self.child(0))
        
        changes = []
        for j in self.event.changes:
            entry = TileChangeListItem(j)
            changes.append(entry)
        self.addChildren(changes)
    
    # reimplementing this for checkbox state change signal. A bit unfortunate that this is needed.
    # inspired by https://stackoverflow.com/a/32403843
    def setData(self, column: int, role: int, value):
        isCheck = column == 1 \
                and role == Qt.ItemDataRole.CheckStateRole \
                and self.data(column, role) is not None \
                and self.checkState(1) != value
        super().setData(column, role, value)
        if isCheck:
            tree: MapChangesTree|None = self.treeWidget()
            if tree is not None:
                tree.previewStateChanged.emit(self, self.checkState(1))
# See above...
class MapChangesTree(QTreeWidget):
    previewStateChanged = Signal(MapChangeEventListItem, Qt.CheckState)

class TileChangeListItem(QTreeWidgetItem):
    def __init__(self, change: TileChange):
        super().__init__()
        self.change = change
        self.updateChangeText()
        self.setIcon(0, icons.ICON_TILE_CHANGE)
        
    def updateChangeText(self):
        self.setText(0, f"{str(self.change.before).zfill(3)} → {str(self.change.after).zfill(3)}")

    def parent(self) -> MapChangeEventListItem:
        return super().parent()