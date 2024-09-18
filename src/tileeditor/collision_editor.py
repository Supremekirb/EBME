from typing import TYPE_CHECKING

from PySide6.QtGui import QBrush, QColor, QPixmap, Qt
from PySide6.QtWidgets import (QGraphicsScene, QHBoxLayout, QListWidget,
                               QListWidgetItem, QPushButton, QVBoxLayout)

from src.coilsnake.project_data import ProjectData

if TYPE_CHECKING:
    from tile_editor import TileEditor, TileEditorState
    
COLLISIONPRESETS = {          # value, colour
    "Solid":                  [0b10000000, 0xFF0000],
    "Trigger":                [0b00010000, 0xFFFF00],
    "Solid trigger":          [0b10010000, 0xDD00FF],
    "Water":                  [0b00001000, 0x0000FF],
    "Deep water":             [0b00001100, 0x00007F],
    "Sunstroke":              [0b00000100, 0xFF7F00],
    "Foreground top half":    [0b00000010, 0x50D000],
    "Foreground bottom half": [0b00000001, 0x30A000],
    "Foreground full":        [0b00000011, 0xA0F000],
    "Talk through":           [0b01000010, 0xB000FF],
}


class CollisionScene(QGraphicsScene):
    SIZE_MULTIPLIER = 4
    
    def __init__(self, parent, projectData: ProjectData):
        super().__init__(parent)
        
        self.projectData = projectData
        
        self.setSceneRect(0, 0, 32*self.SIZE_MULTIPLIER, 32*self.SIZE_MULTIPLIER)
        
        self.setBackgroundBrush(
            QBrush(QPixmap(":/ui/bg.png")))
        
    def parent(self) -> "TileEditor": # for typing
        return super().parent()
    
class PresetItem(QListWidgetItem):
    def __init__(self, name: str, value: int, colour: int):
        super().__init__(name)
        
        self.value = value
        self.protected = False
        
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
        for name, value in COLLISIONPRESETS.items():
            item = PresetItem(name, value[0], value[1])
            item.protected = True
            self.list.addItem(item)
        self.list.itemActivated.connect(self.onItemClicked)
        self.addWidget(self.list)
        self.list.setMinimumWidth(self.list.sizeHint().width()-75) # it is a little too smol
        
        buttonLayout = QHBoxLayout()
        self.editButton = QPushButton("Edit")
        # self.editButton.clicked.connect(self.onEditClicked)
        self.deleteButton = QPushButton("Delete")
        # self.deleteButton.clicked.connect(self.onDeleteClicked)
        
        buttonLayout.addWidget(self.editButton)
        buttonLayout.addWidget(self.deleteButton)
        self.addLayout(buttonLayout)
        
    def onItemClicked(self, item):
        self.state.currentCollision = item.value
