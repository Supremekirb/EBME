from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import (QBrush, QColor, QMouseEvent, QPainter, QPaintEvent,
                           QPixmap)
from PySide6.QtWidgets import (QApplication, QGraphicsScene, QHBoxLayout,
                               QListWidget, QListWidgetItem, QPushButton,
                               QStyle, QToolButton, QVBoxLayout)

import src.misc.common as common
from src.coilsnake.fts_interpreter import Tile
from src.coilsnake.project_data import ProjectData
from src.misc.widgets import TileGraphicsWidget

if TYPE_CHECKING:
    from tile_editor import TileEditor, TileEditorState

class TileCollisionWidget(TileGraphicsWidget):
    def __init__(self, state: "TileEditorState"):
        super().__init__()
        self.state = state
        
    def mousePressEvent(self, event: QMouseEvent):
        if Qt.KeyboardModifier.ShiftModifier in event.modifiers() or Qt.KeyboardModifier.ControlModifier in event.modifiers():
            self.pickCollision(event.pos())
            
        

    def pickCollision(self, pos: QPoint):
        index = self.indexAtPos(pos)
        if index == None:
            return
        value = self.currentTile.getMinitileCollision(index)
        
        preset = self.state.tileEditor.presetList.getPreset(value)
        if preset:
            self.state.tileEditor.presetList.list.setCurrentItem(preset)
            
        
    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        
        if self.currentTile == None or self.currentPalette == None:
            return
        
        
        width = self.width()
        height = self.height()
        
        if width > height:
            width = height
        else:
            height = width
        
        painter = QPainter(self)
        
        scale = width / 32
        
        painter.scale(scale, scale)
        painter.setPen(Qt.PenStyle.NoPen)
        
        for i in range(16):
            collision = self.currentTile.getMinitileCollision(i)
            if collision == 0:
                colour = 0x000000
                painter.setOpacity(0)
            else:
                painter.setOpacity(0.7)
                try:
                    colour = self.state.tileEditor.presetList.getPreset(collision).colour
                except AttributeError:
                    colour = 0x000000
            
            painter.setBrush(QColor(colour))
            painter.drawRect((i % 4)*8, (i // 4)*8, 8, 8)   
    
class PresetItem(QListWidgetItem):
    def __init__(self, name: str, value: int, colour: int):
        super().__init__(name)
        
        self.value = value
        self.colour = colour
        self.protected = False
        self.unknown = False
        
        dimmed = QColor(colour)#.darker()
        
        self.setBackground(dimmed)
        if dimmed.lightness() > 100:
            self.setForeground(Qt.GlobalColor.black)
        else:
            self.setForeground(Qt.GlobalColor.white)
        
        
class CollisionPresetList(QVBoxLayout):
    def __init__(self, state: "TileEditorState"):
        super().__init__()
        self.state = state
        
        self.list = QListWidget()
        self.loadPresets()
        self.list.itemActivated.connect(self.onItemClicked)
        self.list.itemDoubleClicked.connect(self.onItemDoubleClicked)
        self.addWidget(self.list)
        self.list.setMinimumWidth(self.list.sizeHint().width()-75) # it is a little too smol
        
        buttonLayout = QHBoxLayout()
        
        # TODO better icons
        # QtAwesome?
        
        self.addButton = QToolButton()
        self.addButton.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        self.addButton.setToolTip("Add")
        # self.addButton.clicked.connect(self.onAddClicked)
        self.editButton = QToolButton()
        self.editButton.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))
        self.editButton.setToolTip("Edit")
        # self.editButton.clicked.connect(self.onEditClicked)
        self.deleteButton = QToolButton()
        self.deleteButton.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        self.deleteButton.setToolTip("Delete")
        # self.deleteButton.clicked.connect(self.onDeleteClicked)
        self.moveUpButton = QToolButton()
        self.moveUpButton.setArrowType(Qt.ArrowType.UpArrow)
        self.moveUpButton.setToolTip("Move up")
        # self.moveUpButton.clicked.connect(self.onMoveUpClicked)
        self.moveDownButton = QToolButton()
        self.moveDownButton.setArrowType(Qt.ArrowType.DownArrow)
        self.moveDownButton.setToolTip("Move down")
        # self.moveDownButton.clicked.connect(self.onMoveDownClicked)
        
        buttonLayout.addWidget(self.addButton)
        buttonLayout.addWidget(self.editButton)
        buttonLayout.addWidget(self.deleteButton)
        buttonLayout.addWidget(self.moveUpButton)
        buttonLayout.addWidget(self.moveDownButton)
        self.addLayout(buttonLayout)
        
    def onItemClicked(self, item: PresetItem):
        self.state.currentCollision = item.value
    
    def onItemDoubleClicked(self, item: PresetItem):
        ...
        
    def loadPresets(self):
        self.list.clear()
        for name, value in common.COLLISIONPRESETS.items():
            item = PresetItem(name, value[0], value[1])
            item.protected = True
            self.list.addItem(item)
        
    def getPreset(self, value: int) -> PresetItem | None:
        for i in range(0, self.list.count()):
            item = self.list.item(i)
            if isinstance(item, PresetItem):
                if item.value == value:
                    return item
                
                
    def verifyTileCollision(self, tile: Tile):
        self.loadPresets()
        
        for i in range(16):
            if not self.getPreset(tile.getMinitileCollision(i)):
                value = tile.getMinitileCollision(i)
                item = PresetItem(f"Unknown 0x{hex(value)[2:].zfill(2)}", value, 0x303030)
                item.unknown = True
                self.list.addItem(item)