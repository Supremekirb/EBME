from typing import TYPE_CHECKING

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QPolygon
from PySide6.QtWidgets import (QCheckBox, QFormLayout, QGroupBox, QLabel,
                               QPushButton, QSlider, QVBoxLayout, QWidget)

from src.coilsnake.project_data import ProjectData

if TYPE_CHECKING:
    from src.mapeditor.map_editor import MapEditor, MapEditorState


class SidebarGame(QWidget):
    def __init__(self, parent, state: "MapEditorState", mapeditor: "MapEditor", projectData: ProjectData):
        QWidget.__init__(self, parent)
        
        self.state = state
        self.mapeditor = mapeditor
        self.projectData = projectData
        
        self.setupUI()
        
    def setupUI(self):
        contentLayout = QVBoxLayout()
        layout = QFormLayout()
        groupbox = QGroupBox("Game preview options")
        
        self.showScreenMask = QCheckBox("Show screen size")
        self.showScreenMask.setChecked(True)
        self.showScreenMask.toggled.connect(self.toggleScreenMask)
        
        self.screenMaskOpacityLabel = QLabel("Screen size opacity (50%)")
        self.screenMaskOpacity = QSlider()
        self.screenMaskOpacity.setOrientation(Qt.Orientation.Horizontal)
        self.screenMaskOpacity.setTickInterval(1)
        self.screenMaskOpacity.setSingleStep(1)
        self.screenMaskOpacity.setPageStep(1)
        self.screenMaskOpacity.setTickPosition(QSlider.TickPosition.TicksBothSides)
        self.screenMaskOpacity.setRange(0, 10)
        self.screenMaskOpacity.setValue(5)
        self.screenMaskOpacity.valueChanged.connect(self.changeScreenMaskOpacity)
                
        self.showTileMask = QCheckBox("Show out-of-bounds tiles")
        self.showTileMask.setChecked(True)
        self.showTileMask.toggled.connect(self.toggleTileMask)
        
        self.showPreviewNPC = QCheckBox("Show player")
        self.showPreviewNPC.setChecked(True)
        self.showPreviewNPC.toggled.connect(self.togglePreviewNPC)

        # self.obeyCollision = QCheckBox("Obey collision")
        # self.obeyCollision.setChecked(True)
        # self.obeyCollision.toggled.connect(self.toggleObeyCollision)
        
        self.renderThisRegion = QPushButton("Render this region")
        self.renderThisRegion.clicked.connect(self.renderRegion)
        
        layout.addWidget(QLabel("Click to lock the preview in place."))
        layout.addWidget(self.showScreenMask)
        layout.addWidget(self.screenMaskOpacityLabel)
        layout.addWidget(self.screenMaskOpacity)
        layout.addWidget(self.showTileMask)
        layout.addWidget(self.showPreviewNPC)
        layout.addWidget(self.renderThisRegion)
        groupbox.setLayout(layout)
        contentLayout.addWidget(groupbox)
        contentLayout.addStretch()
        self.setLayout(contentLayout)
        
    def toggleScreenMask(self):
        self.state.showPreviewScreen = self.showScreenMask.isChecked()
        self.mapeditor.scene.update()
            
    def changeScreenMaskOpacity(self):
        self.screenMaskOpacityLabel.setText(f"Screen size opacity ({self.screenMaskOpacity.value()*10}%)")
        self.state.previewScreenOpacity = self.screenMaskOpacity.value()/10
        self.mapeditor.scene.update()
            
    def toggleTileMask(self):
        self.state.showPreviewMap = self.showTileMask.isChecked()
        self.mapeditor.scene.update()
            
    def togglePreviewNPC(self):
        if self.showPreviewNPC.isChecked():
            self.mapeditor.scene.previewNPC.show()
        else:
            self.mapeditor.scene.previewNPC.hide()
        self.state.showPreviewNPC = self.showPreviewNPC.isChecked()
        self.mapeditor.scene.update()
        
    def renderRegion(self):
        sectors = self.projectData.adjacentMatchingSectors(self.mapeditor.scene._lastSector, [])
        
        rects = []
        for sector in sectors:
            rects.append(QRect(sector.coords.x, sector.coords.y, 256, 128))
            
        master = QPolygon(rects[0])
        for i in rects:
            master = master.united(i)
            
        rect = master.boundingRect()
        self.mapeditor.renderMap(rect.left(), rect.top(), rect.right(), rect.bottom(), True)
            
            
    def toggleShowNPCs(self):
        ...
            
    def toggleObeyCollision(self):
        ...