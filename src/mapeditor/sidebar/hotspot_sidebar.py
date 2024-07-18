from typing import TYPE_CHECKING

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QFormLayout, QGroupBox, QLabel, QPlainTextEdit,
                               QVBoxLayout, QWidget)

import src.misc.common as common
from src.actions.hotspot_actions import (ActionChangeHotspotColour,
                                         ActionChangeHotspotComment,
                                         ActionChangeHotspotLocation)
from src.misc.coords import EBCoords
from src.misc.widgets import ColourButton, CoordsInput, HSeparator

if TYPE_CHECKING:
    from src.mapeditor.map_editor import MapEditor, MapEditorState

from src.coilsnake.project_data import ProjectData
    
class SidebarHotspot(QWidget):
    def __init__(self, parent, state: "MapEditorState", mapeditor: "MapEditor", projectData: ProjectData):
        super().__init__(parent)
        
        self.state = state
        self.mapeditor = mapeditor
        self.projectData = projectData
        
        self.setupUI()
        
    def fromHotspot(self):        
        hotspot = self.state.currentHotspot
        if hotspot is None:
            self.hotspotLabel.setText("Select a hotspot to edit.")
            self.hotspotData.setEnabled(False)
            return
        
        self.hotspotTopLeft.x.blockSignals(True)
        self.hotspotTopLeft.y.blockSignals(True)
        self.hotspotBottomRight.x.blockSignals(True)
        self.hotspotBottomRight.y.blockSignals(True)
        self.hotspotColour.blockSignals(True)
        self.hotspotComment.blockSignals(True)
        
        self.hotspotData.setEnabled(True)
        self.hotspotLabel.setText(f"Hotspot {hotspot.id}")
        
        self.hotspotTopLeft.x.setValue(hotspot.start.coordsWarp()[0])
        self.hotspotTopLeft.y.setValue(hotspot.start.coordsWarp()[1])
        self.hotspotBottomRight.x.setValue(hotspot.end.coordsWarp()[0])
        self.hotspotBottomRight.y.setValue(hotspot.end.coordsWarp()[1])
        
        self.hotspotColour.setColour(QColor.fromRgb(*hotspot.colour))
        
        self.hotspotComment.setPlainText(hotspot.comment)
        
        self.hotspotData.setEnabled(True)
        
        self.hotspotTopLeft.x.blockSignals(False)
        self.hotspotTopLeft.y.blockSignals(False)
        self.hotspotBottomRight.x.blockSignals(False)
        self.hotspotBottomRight.y.blockSignals(False)
        self.hotspotColour.blockSignals(False)
        self.hotspotComment.blockSignals(False)
        
        
    def toHotspot(self):
        hotspot = self.state.currentHotspot
        if hotspot is None:
            return
        
        start = EBCoords.fromWarp(self.hotspotTopLeft.x.value(), self.hotspotTopLeft.y.value())
        end = EBCoords.fromWarp(self.hotspotBottomRight.x.value(), self.hotspotBottomRight.y.value())
        
        if start != hotspot.start or end != hotspot.end:
            if start.x > end.x:
                start.x, end.x = end.x, start.x
                
            if start.y > end.y:
                start.y, end.y = end.y, start.y
                
            action = ActionChangeHotspotLocation(hotspot, start, end)
            action.fromSidebar = True
            
            self.mapeditor.scene.undoStack.push(action)
            self.mapeditor.scene.refreshHotspot(hotspot.id)
            
        colour = self.hotspotColour.chosenColour.getRgb()[:3]
        if colour != hotspot.colour:
            action = ActionChangeHotspotColour(hotspot, colour)
            
            self.mapeditor.scene.undoStack.push(action)
            self.mapeditor.scene.refreshHotspot(hotspot.id)
    
        if self.hotspotComment.toPlainText() != hotspot.comment:
            action = ActionChangeHotspotComment(hotspot, self.hotspotComment.toPlainText())
            
            self.mapeditor.scene.undoStack.push(action)
        
    def setupUI(self):
        contentLayout = QVBoxLayout()
        
        self.hotspotLabel = QLabel("Select a hotspot to edit.")
        self.hotspotData = QGroupBox("Hotspot data")
        hotspotDataLayout = QFormLayout()
        self.hotspotTopLeft = CoordsInput()
        self.hotspotBottomRight = CoordsInput()
        self.hotspotTopLeft.x.setMaximum(common.EBMAPWIDTH//8-1)
        self.hotspotTopLeft.y.setMaximum(common.EBMAPHEIGHT//8-1)
        self.hotspotBottomRight.x.setMaximum(common.EBMAPWIDTH//8-1)
        self.hotspotBottomRight.y.setMaximum(common.EBMAPHEIGHT//8-1)
        
        self.hotspotTopLeft.x.valueChanged.connect(self.toHotspot)
        self.hotspotTopLeft.y.valueChanged.connect(self.toHotspot)
        self.hotspotBottomRight.x.valueChanged.connect(self.toHotspot)
        self.hotspotBottomRight.y.valueChanged.connect(self.toHotspot)
        
        self.hotspotColour = ColourButton()
        self.hotspotColour.colourChanged.connect(self.toHotspot)
        
        self.hotspotComment = QPlainTextEdit()
        self.hotspotComment.textChanged.connect(self.toHotspot)
        
        hotspotDataLayout.addRow("Top left", self.hotspotTopLeft)
        hotspotDataLayout.addRow("Bottom right", self.hotspotBottomRight)
        hotspotDataLayout.addRow("Colour", self.hotspotColour)
        hotspotDataLayout.addRow("Comment", self.hotspotComment)
        
        self.hotspotData.setLayout(hotspotDataLayout)
        self.hotspotData.setEnabled(False)
        
        contentLayout.addWidget(self.hotspotLabel)
        contentLayout.addWidget(HSeparator())
        contentLayout.addWidget(self.hotspotData)
        
        self.setLayout(contentLayout)