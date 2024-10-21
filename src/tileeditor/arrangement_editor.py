from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent

from src.actions.fts_actions import ActionChangeArrangement
from src.misc.widgets import TileGraphicsWidget

if TYPE_CHECKING:
    from tile_editor import TileEditorState

class TileArrangementWidget(TileGraphicsWidget):
    def __init__(self, state: "TileEditorState"):
        super().__init__()
        self.state = state
        
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if Qt.KeyboardModifier.ShiftModifier in event.modifiers() or Qt.KeyboardModifier.ControlModifier in event.modifiers():
                self.pickMinitile(event.pos())
            else:
                self.placeMinitile(event.pos())
        elif event.button() == Qt.MouseButton.RightButton:
            self.modifyMinitile(event.pos())

    def placeMinitile(self, pos: QPoint):
        index = self.indexAtPos(pos)
        if index == None:
            return
        
        # use current minitile
        metadata = self.currentTile.getMetadata(index) - self.currentTile.getMinitileID(index) + self.state.currentMinitile
        
        # reset hflip and vflip flags
        metadata = metadata & ~0xC000
        
        # use current subpalette
        metadata -= self.currentTile.getMinitileSubpalette(index) << 10
        metadata += self.state.currentSubpalette << 10
        
        action = ActionChangeArrangement(self.currentTile, metadata, index)
        action.setText("Place minitile")
        self.state.tileEditor.undoStack.push(action)
        self.state.tileEditor.updateTile(self.currentTile)
        
        self.update()
        
    def modifyMinitile(self, pos: QPoint):
        index = self.indexAtPos(pos)
        if index == None:
            return
        
        # cycle: none -> hflip -> vflip -> hvflip -> ...
        
        metadata = self.currentTile.getMetadata(index)
        
        # hvflip --> none
        if self.currentTile.getMinitileHorizontalFlip(index) and self.currentTile.getMinitileVerticalFlip(index):
            metadata = metadata & ~0xC000 # unset both
        
        # vflip --> hvflip
        elif self.currentTile.getMinitileVerticalFlip(index):
            metadata = metadata | 0xC000 # set both
            
        # hflip --> vflip
        elif self.currentTile.getMinitileHorizontalFlip(index):
            metadata = metadata & ~0x4000 # unset h
            metadata = metadata | 0x8000 # set v
        
        # none --> hflip
        else:
            metadata = metadata | 0x4000 # set h
            
        action = ActionChangeArrangement(self.currentTile, metadata, index)
        action.setText("Modify minitile mirroring/flipping")
        self.state.tileEditor.undoStack.push(action)
        self.state.tileEditor.updateTile(self.currentTile)
        
        self.update()
        
    def pickMinitile(self, pos: QPoint):
        index = self.indexAtPos(pos)
        if index == None:
            return
        
        minitile = self.currentTile.getMinitileID(index)
        self.state.tileEditor.selectMinitile(minitile)
        subpalette = self.currentTile.getMinitileSubpalette(index)
        self.state.tileEditor.paletteView.setSubpaletteIndex(subpalette)
        self.state.tileEditor.onSubpaletteSelect()