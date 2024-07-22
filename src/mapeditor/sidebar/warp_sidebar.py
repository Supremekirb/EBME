from typing import TYPE_CHECKING

from PySide6.QtWidgets import (QComboBox, QFormLayout, QGroupBox, QLabel,
                               QLineEdit, QPlainTextEdit, QSizePolicy,
                               QVBoxLayout, QWidget)

import src.misc.common as common
from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords
from src.misc.widgets import (BaseChangerSpinbox, CoordsInput, FlagInput,
                              HSeparator)
from src.objects.warp import Warp, Teleport

if TYPE_CHECKING:
    from src.mapeditor.map.map_scene import MapEditorScene
    from src.mapeditor.map_editor import MapEditorState

class SidebarWarp(QWidget):
    def __init__(self, parent, state: "MapEditorState", scene: "MapEditorScene", projectData: ProjectData):
        super().__init__(parent)
        
        self.scene = scene
        self.state = state
        self.projectData = projectData
        
        self.setupUI()
        
    def fromWarp(self):
        warp = self.state.currentWarp
        
        if isinstance(warp, Warp):
            self.warpLabel.setText(f"Warp {warp.id}")
            self.warpCoords.x.setValue(warp.dest.x)
            self.warpCoords.y.setValue(warp.dest.y)
            self.warpDir.setCurrentIndex(warp.dir)
            self.warpStyle.setValue(warp.style)
            self.warpUnknown.setValue(warp.unknown)
            self.warpComment.setPlainText(warp.comment)
            
            self.warpGroupBox.setEnabled(True)
            self.teleportGroupBox.setDisabled(True)
            
        elif isinstance(warp, Teleport):
            self.teleportLabel.setText(f"Teleport {warp.id}")
            self.teleportCoords.x.setValue(warp.dest.x)
            self.teleportCoords.y.setValue(warp.dest.y)
            self.teleportFlag.setValue(warp.flag)
            self.teleportName.setText(warp.name)
            
            self.warpGroupBox.setDisabled(True)
            self.teleportGroupBox.setEnabled(True)
        
    def toWarp(self):
        ...
            
        
    def setupUI(self):
        layout = QVBoxLayout()
        
        self.warpLabel = QLabel("Select a warp to edit")
        self.warpLabel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        self.warpGroupBox = QGroupBox("Warp Data")
        warpGroupBoxLayout = QFormLayout()
        
        self.warpCoords = CoordsInput()
        self.warpCoords.x.setMaximum(common.EBMAPWIDTH//8)
        self.warpCoords.y.setMaximum(common.EBMAPHEIGHT//8)
        self.warpCoords.x.setToolTip("Warp destination position. Warp coordinates are in pixels/8.")
        self.warpCoords.y.setToolTip("Warp destination position. Warp coordinates are in pixels/8.")
        
        self.warpDir = QComboBox()
        self.warpDir.addItems(["Up", "Down", "Left", "Right"])
        self.warpDir.setToolTip("Direction to face after warping.")
        
        self.warpStyle = BaseChangerSpinbox()
        self.warpStyle.setMaximum(common.BYTELIMIT)
        self.warpStyle.setToolTip("Warp style to use. See the Warp Styles Table script in the CCS Library.")
        
        self.warpUnknown = BaseChangerSpinbox()
        self.warpUnknown.setMaximum(common.BYTELIMIT)
        self.warpUnknown.setToolTip("Unknown value. Seems to either be 0 or 127.")
        
        self.warpComment = QPlainTextEdit()
        
        warpGroupBoxLayout.addRow("Destination", self.warpCoords)
        warpGroupBoxLayout.addRow("Direction", self.warpDir)
        warpGroupBoxLayout.addRow("Style", self.warpStyle)
        warpGroupBoxLayout.addRow("Unknown", self.warpUnknown)
        warpGroupBoxLayout.addRow("Comment", self.warpComment)
        
        self.warpGroupBox.setLayout(warpGroupBoxLayout)
        
        ########
        
        self.teleportLabel = QLabel("Select a teleport to edit")
        self.teleportLabel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        self.teleportGroupBox = QGroupBox("Teleport Data")
        teleportGroupBoxLayout = QFormLayout()
        
        self.teleportCoords = CoordsInput()
        self.teleportCoords.x.setMaximum(common.EBMAPWIDTH//8)
        self.teleportCoords.y.setMaximum(common.EBMAPHEIGHT//8)
        self.teleportCoords.x.setToolTip("Teleport destination position. Teleport coordinates are in pixels/8.")
        self.teleportCoords.y.setToolTip("Teleport destination position. Teleport coordinates are in pixels/8.")
        
        self.teleportFlag = FlagInput()
        
        self.teleportName = QLineEdit()
        
        teleportGroupBoxLayout.addRow("Destination", self.teleportCoords)
        teleportGroupBoxLayout.addRow("Flag", self.teleportFlag)
        teleportGroupBoxLayout.addRow("Name", self.teleportName)
        
        self.teleportGroupBox.setLayout(teleportGroupBoxLayout)
        
        
        layout.addWidget(self.warpLabel)
        layout.addWidget(HSeparator())
        layout.addWidget(self.warpGroupBox)
        layout.addWidget(self.teleportLabel)
        layout.addWidget(HSeparator())
        layout.addWidget(self.teleportGroupBox)
        
        self.setLayout(layout)
        
        