from PySide6.QtWidgets import QTreeWidgetItem

import src.misc.icons as icons


class MapChange:
    def __init__(self, tileset: int, changes: list["MapChangeEvent"]):
        self.tileset = tileset
        self.events = changes

class MapChangeEvent:
    def __init__(self, tileset: int, flag: int, changes: list["TileChange"]):
        self.tileset = tileset
        self.flag = flag
        self.changes = changes
        

class TileChange:
    def __init__(self, before: int, after: int):
        self.before = before
        self.after = after
        
        
class MapChangeEventListItem(QTreeWidgetItem):
    def __init__(self, event: MapChangeEvent):
        super().__init__()
        self.event = event
        self.updateFlagText()
        self.setIcon(0, icons.ICON_FLAG)
        
    def updateFlagText(self):
        self.setText(0, str(self.event.flag) if self.event.flag < 0x8000 else f"{self.event.flag - 0x8000} (Inverted)")

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