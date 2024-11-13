from typing import TYPE_CHECKING

from PySide6.QtWidgets import QFormLayout, QGroupBox, QVBoxLayout, QWidget

from src.actions.fts_actions import ActionChangeCollision
from src.coilsnake.project_data import ProjectData
from src.widgets.collision import CollisionPresetList, PresetItem
from src.widgets.tile import TileCollisionWidget

if TYPE_CHECKING:
    from src.mapeditor.map_editor import MapEditor, MapEditorState


class SidebarCollision(QWidget):
    def __init__(self, parent, state: "MapEditorState", mapeditor: "MapEditor", projectData: ProjectData):
        QWidget.__init__(self, parent)
        
        self.state = state
        self.mapeditor = mapeditor
        self.projectData = projectData
        
        self.setupUI()

    def onCurrentChanged(self):
        item: PresetItem = self.presets.list.currentItem()
        if item:
            self.state.currentCollision = item.value  
        self.display.update()
        self.mapeditor.scene.update() 
            
    def onCollisionPicked(self, collision: int):
        item = self.presets.getPreset(collision)
        if item:
            self.presets.list.setCurrentItem(item)
        
    def onCollisionPlaced(self, index: int):
        tile = self.display.currentTile
        action = ActionChangeCollision(tile, self.state.currentCollision, index)
        self.mapeditor.scene.undoStack.push(action)
        self.display.update()
    
    def setupUI(self):
        contentLayout = QVBoxLayout()
        layout = QVBoxLayout()
        groupbox = QGroupBox("Collision Presets")
        
        self.presets = CollisionPresetList()
        self.presets.list.currentItemChanged.connect(self.onCurrentChanged)
        layout.addLayout(self.presets)
        
        self.display = TileCollisionWidget(readOnly=False)
        self.display.collisionPicked.connect(self.onCollisionPicked)
        self.display.collisionPlaced.connect(self.onCollisionPlaced)
        self.display.setFixedHeight(256)
        layout.addWidget(self.display)
        
        groupbox.setLayout(layout)
        contentLayout.addWidget(groupbox)
        self.setLayout(contentLayout)