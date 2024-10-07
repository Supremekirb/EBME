from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QGridLayout, QSizePolicy, QWidget

from src.actions.fts_actions import ActionChangeBitmap
from src.coilsnake.fts_interpreter import Minitile, Subpalette
from src.misc.widgets import ColourButton, MinitileGraphicsWidget

if TYPE_CHECKING:
    from tile_editor import TileEditorState
    
class PaletteSelector(QWidget):
    colourChanged = Signal(int)
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        layout = QGridLayout()
        self.setLayout(layout)
        
        self.buttons: list[ColourButton] = []
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        for i in range(16):
            button = ColourButton(self)
            button.setCheckable(True)
            button.clicked.disconnect()
            button.colourChanged.connect(self.onColourChanged)
            button.clicked.connect(self.onColourChanged)
            button.setAutoExclusive(True)
            button.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred))
            layout.addWidget(button, i // 4, i % 4)
            self.buttons.append(button)
            
        self.buttons[0].setChecked(True)
        self.onColourChanged()
            
    def onColourChanged(self):
        for index, button in enumerate(self.buttons):
            if button.isChecked():
                self.currentColour = button.chosenColour
                self.currentColourIndex = index
                break
        self.colourChanged.emit(index)
        
    def setColourIndex(self, index: int):
        self.buttons[index].setChecked(True)
        self.currentColourIndex = index
        self.currentColour = self.buttons[index].chosenColour
        
    def updateButtons(self):
        for index, button in enumerate(self.buttons):
            if self.currentColourIndex == index:
                button.setChecked(True)
            else:
                button.setChecked(False)
        
    def openEditor(self):
        # maybe new implementation later,
        # but right now just open the dialog of the selected button
        for button in self.buttons:
            if button.isChecked():
                button.openColourDialog()
                break
        
class MinitileEditorWidget(MinitileGraphicsWidget):
    colourPicked = Signal(int)
    
    def __init__(self, state: "TileEditorState"):
        super().__init__()      
        self.state = state
        self._painting = False
        self._lastOldIndex: int = None
        self._scratchBitmap: list[str] = []
        
    def mousePressEvent(self, event: QMouseEvent):
        if self.isEnabled():
            if event.button() == Qt.MouseButton.LeftButton:
                self._painting = True
                self.copyToScratch()
                self.paintPixel(event.pos())
            
            if event.button() == Qt.MouseButton.RightButton:
                self.pickPixel(event.pos())
        
        return super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.isEnabled():
            if self._painting:
                self.paintPixel(event.pos())     
            
        return super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.isEnabled():
            if event.button() == Qt.MouseButton.LeftButton:
                self._painting = False
                action = ActionChangeBitmap(self.currentMinitile, self._scratchBitmap, self.isForeground)
                self.state.tileEditor.undoStack.push(action)
            
        return super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if self.isEnabled():
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