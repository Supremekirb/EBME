from copy import copy
from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import (QBrush, QColor, QMouseEvent, QPainter, QPaintEvent,
                           QPixmap)
from PySide6.QtWidgets import QGridLayout, QSizePolicy, QWidget

from src.actions.minitile_actions import ActionChangeBitmap
from src.coilsnake.fts_interpreter import Minitile, Subpalette
from src.coilsnake.project_data import ProjectData
from src.misc.widgets import ColourButton

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
        
class MinitileGraphicsWidget(QWidget):
    colourPicked = Signal(int)
    
    def __init__(self, projectData: ProjectData, state: "TileEditorState"):
        super().__init__()
        
        self.projectData = projectData
        self.state = state
        
        self.currentMinitile: Minitile = None
        self.currentSubpalette: Subpalette = None
        self.isForeground = True
        
        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        policy.setHeightForWidth(True)
        policy.setWidthForHeight(True)
        self.setSizePolicy(policy)
        
        self._painting = False
        self._lastOldIndex: int = None
        self._scratchBitmap: list[str] = []
    
    def copyToScratch(self):
        """For better undo/redo support, we copy the bitmap to this scratch space to modify it.
        
        Then undo/redo actions apply it to the model."""
        if self.isForeground:
            self._scratchBitmap = copy(self.currentMinitile.foreground)
        else:
            self._scratchBitmap = copy(self.currentMinitile.background)
        
    def loadMinitile(self, minitile: Minitile, id: int=0):
        self.currentMinitile = minitile
        if id >= 384 and self.isForeground:
            self.setDisabled(True)
        else: self.setEnabled(True)
        self.copyToScratch()
        
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
        colour = hex(self.state.currentColourIndex)[2:]
        index = self.indexAtPos(pos)
        if index == None:
            return 
        
        if self.isForeground:
            self._lastOldIndex = int(self.currentMinitile.foreground[index], 16)
            self._scratchBitmap[index] = colour
        else:
            self._lastOldIndex = int(self.currentMinitile.background[index], 16)
            self._scratchBitmap[index] = colour
        
        self.update()
        
    def pickPixel(self, pos: QPoint):
        index = self.indexAtPos(pos)
        if index == None:
            return
        
        if self.isForeground:
            colourIndex = int(self.currentMinitile.foreground[index], 16)
        else:
            colourIndex = int(self.currentMinitile.background[index], 16)
            
        self.colourPicked.emit(colourIndex)
        
    def fill(self, pos: QPoint):
        
        self.copyToScratch()
            
        index = self.indexAtPos(pos)
        if index == None:
            return
        
        toFill = self.adjacentMatchingPixels(index, [])
        colour = hex(self.state.currentColourIndex)[2:]
        
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
            if i != None and int(source[i], 16) == self._lastOldIndex and i not in matches:
                matches.append(i)
                matches = self.adjacentMatchingPixels(i, matches)

        return list(matches)

    def adjacentPixelIndexes(self, index: int):
        above = index - 8 if index - 8 >= 0 else None
        right = index + 1 if (index + 1) // 8 == index // 8 else None
        below = index + 8 if index + 8 < 64 else None
        left = index - 1 if (index - 1) // 8 == index // 8 else None
        
        return (above, right, below, left)
        
    def indexAtPos(self, pos: QPoint):
        """Get the index (0-63) of the pixel at the given position

        Args:
            pos (QPoint): Location on the widget, such as from an event

        Returns:
            int: index
        """
        w = self.width()
        h = self.height()
        
        if w > h:       
            w = h
        else:
            h = w
            
        x = pos.x() // (w / 8)
        y = pos.y() // (h / 8)
        
        if x < 0 or x > 7 or y < 0 or y > 7:
            return
        
        return int(y * 8 + x)
        
        
    def paintEvent(self, event: QPaintEvent):
        if self.currentMinitile == None or self.currentSubpalette == None:
            return super().paintEvent(event)
        
        width = self.width()
        height = self.height()
        
        if width > height:
            width = height
        else:
            height = width
        
        painter = QPainter(self)
           
        scale = width / 8
              
        painter.scale(scale, scale)
        
        # draw bg at half the size of the minitile pixel 
        painter.scale(0.5, 0.5)
        painter.setBrush(QBrush(QPixmap(":/ui/bg.png").scaled(2, 2)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, 16, 16)
        painter.scale(2, 2)
        
        for i in range(64):
            x = i % 8
            y = i // 8
            colour = self.currentSubpalette.getSubpaletteColourRGBA(self._scratchBitmap[i])
            painter.fillRect(x, y, 1, 1, QColor.fromRgb(*colour))
        
        if not self.isEnabled():
            painter.setBrush(QColor(0, 0, 0, 128))
            painter.drawRect(0, 0, 8, 8)
            # painter.setBrush(Qt.BrushStyle.NoBrush)
            
        return super().paintEvent(event)
    
    def heightForWidth(self, width: int) -> int:
        return width
    
    def hasHeightForWidth(self):
        return True
    
    def minimumSizeHint(self):
        return QSize(128, 128)