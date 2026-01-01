from typing import TYPE_CHECKING

from PySide6.QtWidgets import (QCheckBox, QFormLayout, QGroupBox, QLabel,
                               QVBoxLayout, QWidget)

from src.coilsnake.project_data import ProjectData
from src.objects.hotspot import MapEditorHotspot
from src.objects.npc import MapEditorNPC
from src.objects.trigger import MapEditorTrigger
from src.objects.warp import MapEditorWarp

if TYPE_CHECKING:
    from src.mapeditor.map_editor import MapEditor, MapEditorState


class SidebarAll(QWidget):
    def __init__(self, parent, state: "MapEditorState", mapeditor: "MapEditor", projectData: ProjectData):
        QWidget.__init__(self, parent)
        
        self.state = state
        self.mapeditor = mapeditor
        self.projectData = projectData
        
        self.setupUI()
        
    def onToggleCollision(self): # lambdas have failed me.
        self.state.allModeShowsCollision = self.showCollision.isChecked()
        self.mapeditor.scene.update()
    
    def onToggleEnemyTiles(self): # I agree, me from a year ago
        self.state.allModeShowsEnemyTiles = self.showEnemyTiles.isChecked()
        self.mapeditor.scene.update()
    
    def onToggleEnemyLines(self):
        if self.showEnemyLines.isChecked():
            self.mapeditor.scene.hoverSpawnLines.show()
        else:
            self.mapeditor.scene.hoverSpawnLines.hide()
        
    def setupUI(self):
        contentLayout = QVBoxLayout()
        layout = QFormLayout()
        groupbox = QGroupBox("View options")
        
        self.showNPCs = QCheckBox("Show NPCs")
        self.showNPCs.setChecked(True)
        self.showNPCs.toggled.connect(lambda: MapEditorNPC.showNPCs() if self.showNPCs.isChecked() else MapEditorNPC.hideNPCs())
        
        self.showTriggers = QCheckBox("Show triggers")
        self.showTriggers.setChecked(True)
        self.showTriggers.toggled.connect(lambda: MapEditorTrigger.showTriggers() if self.showTriggers.isChecked() else MapEditorTrigger.hideTriggers())
        
        self.showEnemyTiles = QCheckBox("Show enemy tiles")
        self.showEnemyTiles.setChecked(True)
        self.showEnemyTiles.toggled.connect(self.onToggleEnemyTiles)
        
        self.showEnemyLines = QCheckBox("Show enemy spawn lines")
        self.showEnemyLines.setChecked(False)
        self.showEnemyLines.toggled.connect(self.onToggleEnemyLines)
        
        self.showHotspots = QCheckBox("Show hotspots")
        self.showHotspots.setChecked(True)
        self.showHotspots.toggled.connect(lambda: MapEditorHotspot.showHotspots() if self.showHotspots.isChecked() else MapEditorHotspot.hideHotspots())
        
        self.showWarps = QCheckBox("Show warps")
        self.showWarps.setChecked(True)
        self.showWarps.toggled.connect(lambda: MapEditorWarp.showWarps() if self.showWarps.isChecked() else MapEditorWarp.hideWarps())
        
        self.showCollision = QCheckBox("Show collision")
        self.showCollision.setChecked(True)
        self.showCollision.toggled.connect(self.onToggleCollision)
        
        self.viewHint = QLabel("Use the View menu to toggle visibility of things like NPC IDs.")
        self.viewHint.setWordWrap(True)
        
        layout.addWidget(self.viewHint)
        layout.addWidget(self.showNPCs)
        layout.addWidget(self.showTriggers)
        layout.addWidget(self.showEnemyTiles)
        layout.addWidget(self.showEnemyLines)
        layout.addWidget(self.showHotspots)
        layout.addWidget(self.showWarps)
        layout.addWidget(self.showCollision)
        groupbox.setLayout(layout)
        contentLayout.addWidget(groupbox)
        contentLayout.addStretch()
        self.setLayout(contentLayout)