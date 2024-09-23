from typing import TYPE_CHECKING

from PySide6.QtGui import QBrush, QColor, QPixmap, Qt
from PySide6.QtWidgets import (QApplication, QGraphicsScene, QHBoxLayout,
                               QListWidget, QListWidgetItem, QPushButton,
                               QStyle, QToolButton, QVBoxLayout)

import src.misc.common as common
from src.coilsnake.project_data import ProjectData

if TYPE_CHECKING:
    from tile_editor import TileEditor, TileEditorState


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
        for name, value in common.COLLISIONPRESETS.items():
            item = PresetItem(name, value[0], value[1])
            item.protected = True
            self.list.addItem(item)
        self.list.itemActivated.connect(self.onItemClicked)
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
        
    def onItemClicked(self, item):
        self.state.currentCollision = item.value
