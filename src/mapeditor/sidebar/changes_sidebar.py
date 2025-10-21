from typing import TYPE_CHECKING

from PySide6.QtWidgets import (QComboBox, QFormLayout, QGroupBox, QHeaderView,
                               QSizePolicy, QTreeWidget, QTreeWidgetItem,
                               QVBoxLayout, QWidget)

from src.actions.fts_actions import ActionChangeCollision
from src.coilsnake.project_data import ProjectData
from src.objects.changes import MapChangeEventListItem, TileChangeListItem
from src.widgets.collision import CollisionPresetList, PresetItem
from src.widgets.tile import TileCollisionWidget

if TYPE_CHECKING:
    from src.mapeditor.map_editor import MapEditor, MapEditorState
    
class SidebarChanges(QWidget):
    def __init__(self, parent, state: "MapEditorState", mapeditor: "MapEditor", projectData: ProjectData):
        super().__init__(parent)
        
        self.state = state
        self.mapeditor = mapeditor
        self.projectData = projectData
        
        self.setupUI()
    
    def fromTileset(self, tilesetID: int):
        self.tilesetSelect.setCurrentIndex(tilesetID)
        self.mapeditor.scene.enabledMapEvents = []
        self.eventsTree.clear()
        items = []
        for i in self.projectData.mapChanges[tilesetID].events:
            self.mapeditor.scene.enabledMapEvents.append(i)
            item = MapChangeEventListItem(i)
            changes = []
            for j in i.changes:
                entry = TileChangeListItem(j)
                changes.append(entry)
            item.addChildren(changes)
                
            items.append(item)
            
        self.eventsTree.addTopLevelItems(items)
        
        self.mapeditor.scene.update()
        
    def fromEvent(self, item: QTreeWidgetItem):
        ...
        
    def setupUI(self):
        contentLayout = QVBoxLayout()
        eventsLayout = QFormLayout()
        eventsGroupbox = QGroupBox("Map changes")
        
        self.tilesetSelect = QComboBox()
        self.tilesetSelect.setToolTip("Changes in this tileset. Tileset = fts in /Tilesets.")
        self.tilesetSelect.currentIndexChanged.connect(self.fromTileset)
        
        self.eventsTree = QTreeWidget()
        self.eventsTree.setColumnCount(2)
        self.eventsTree.setHeaderLabels(["Event", "Preview"])
        self.eventsTree.header().setStretchLastSection(False)
        self.eventsTree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.eventsTree.currentItemChanged.connect(self.fromEvent)
        self.eventsTree.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        eventsLayout.addRow("Tileset", self.tilesetSelect)
        eventsLayout.addRow(self.eventsTree)
        
        eventsGroupbox.setLayout(eventsLayout)
        
        contentLayout.addWidget(eventsGroupbox)
        
        self.setLayout(contentLayout)
        
        self.tilesetSelect.addItems(str(i.id) for i in self.projectData.tilesets)
        self.tilesetSelect.setCurrentIndex(0)