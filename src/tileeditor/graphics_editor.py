from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent
from PySide6.QtWidgets import QGridLayout, QLabel, QSizePolicy, QWidget

from src.actions.fts_actions import (ActionChangeBitmap,
                                     ActionChangeSubpaletteColour)
from src.coilsnake.fts_interpreter import Palette
from src.misc.widgets import (ColourButton, MinitileGraphicsWidget,
                              PaletteSelector)

if TYPE_CHECKING:
    from tile_editor import TileEditorState
    
class GraphicsEditorPaletteSelector(PaletteSelector):    
    def __init__(self, state: "TileEditorState"):
        super().__init__()
        
        self.state = state
                
    def onColourEdited(self):
        for subpalette in self.buttons:
            for button in subpalette:
                if button.isChecked():
                    new = button.chosenColour
                    
                    action = ActionChangeSubpaletteColour(self.state.tileEditor.projectData.getTileset(
                        self.state.currentTileset).getPalette(
                            self.state.currentPaletteGroup, self.state.currentPalette).subpalettes[self.currentSubpaletteIndex],
                        self.currentColourIndex, new.toTuple()[:3]) # :3
                    
                    self.state.tileEditor.undoStack.push(action)
                    return super().onColourEdited()
                
        return super().onColourEdited()
        
class MinitileEditorWidget(MinitileGraphicsWidget):
    colourPicked = Signal(int)
    
    def __init__(self, state: "TileEditorState"):
        super().__init__()      
        self.state = state
        self._painting = False
        self._lastOldIndex: int = None
        self._scratchBitmap: list[str] = []
        
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if Qt.KeyboardModifier.ControlModifier in event.modifiers() or Qt.KeyboardModifier.ShiftModifier in event.modifiers():
                self.pickPixel(event.pos())
            self._painting = True
            self.copyToScratch()
            self.paintPixel(event.pos())
        
        if event.button() == Qt.MouseButton.RightButton:
            self.pickPixel(event.pos())
        
        return super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event: QMouseEvent):
        if self._painting:
            self.paintPixel(event.pos())     
            
        return super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._painting = False
            action = ActionChangeBitmap(self.currentMinitile, self._scratchBitmap, self.isForeground)
            self.state.tileEditor.undoStack.push(action)
            self.state.tileEditor.updateMinitile(self.currentMinitile)
            
        return super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        # fill bucket
        if event.button() == Qt.MouseButton.LeftButton:
            if self._lastOldIndex == None:
                return super().mouseDoubleClickEvent(event)
            
            self.fill(event.pos())
        
        self.update()
        return super().mouseDoubleClickEvent(event)
    
    def paintPixel(self, pos: QPoint):
        colour = self.state.currentColourIndex
        index = self.indexAtPos(pos)
        if index == None:
            return 
        
        if self.isForeground:
            self._lastOldIndex = self.currentMinitile.foreground[index]
            self._scratchBitmap[index] = colour
        else:
            self._lastOldIndex = self.currentMinitile.background[index]
            self._scratchBitmap[index] = colour
        
        self.update()
        
    def pickPixel(self, pos: QPoint):
        index = self.indexAtPos(pos)
        if index == None:
            return
        
        if self.isForeground:
            colourIndex = self.currentMinitile.foreground[index]
        else:
            colourIndex = self.currentMinitile.background[index]
            
        self.colourPicked.emit(colourIndex)
        
    def fill(self, pos: QPoint):
        
        self.copyToScratch()
            
        index = self.indexAtPos(pos)
        if index == None:
            return
        
        toFill = self.adjacentMatchingPixels(index, [])
        colour = self.state.currentColourIndex
        
        for i in toFill:
            if self.isForeground:
                self._scratchBitmap[i] = colour
            else:
                self._scratchBitmap[i] = colour
        
        action = ActionChangeBitmap(self.currentMinitile, self._scratchBitmap, self.isForeground)
        self.state.tileEditor.undoStack.push(action)
        self.state.tileEditor.updateMinitile(self.currentMinitile)
        
        self.update()
                
    def adjacentMatchingPixels(self, index: int, matches: list = []):  
        if self.isForeground:
            source = self.currentMinitile.foreground
        else:
            source = self.currentMinitile.background
                  
        above, right, below, left = self.adjacentPixelIndexes(index)
        for i in [above, right, below, left]:
            if i != None and source[i] == self._lastOldIndex and i not in matches:
                matches.append(i)
                matches = self.adjacentMatchingPixels(i, matches)

        return list(matches)

    def adjacentPixelIndexes(self, index: int):
        above = index - 8 if index - 8 >= 0 else None
        right = index + 1 if (index + 1) // 8 == index // 8 else None
        below = index + 8 if index + 8 < 64 else None
        left = index - 1 if (index - 1) // 8 == index // 8 else None
        
        return (above, right, below, left)