from typing import TYPE_CHECKING

from PySide6.QtWidgets import (QComboBox, QFormLayout, QGroupBox, QLabel,
                               QLineEdit, QPlainTextEdit, QSizePolicy,
                               QVBoxLayout, QWidget)

import src.misc.common as common
from src.actions.warp_actions import (ActionMoveTeleport, ActionMoveWarp,
                                      ActionUpdateTeleport, ActionUpdateWarp)
from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords
from src.misc.widgets import (BaseChangerSpinbox, CoordsInput, FlagInput,
                              HSeparator)
from src.objects.warp import Teleport, Warp

if TYPE_CHECKING:
    from src.mapeditor.map_editor import MapEditor, MapEditorState

class SidebarWarp(QWidget):
    def __init__(self, parent, state: "MapEditorState", mapeditor: "MapEditor", projectData: ProjectData):
        super().__init__(parent)
        
        self.mapeditor = mapeditor
        self.state = state
        self.projectData = projectData
        
        self.setupUI()
        
    def fromWarp(self):
        warp = self.state.currentWarp
        
        self.warpCoords.x.blockSignals(True)
        self.warpCoords.y.blockSignals(True)
        self.warpDir.blockSignals(True)
        self.warpStyle.blockSignals(True)
        self.warpUnknown.blockSignals(True)
        self.warpComment.blockSignals(True)
        
        self.teleportCoords.x.blockSignals(True)
        self.teleportCoords.y.blockSignals(True)
        self.teleportFlag.blockSignals(True)
        self.teleportName.blockSignals(True)
        
        if isinstance(warp, Warp):
            self.teleportLabel.setText("Select a teleport to edit.")
            self.warpLabel.setText(f"Warp {warp.id}")
            self.warpCoords.x.setValue(warp.dest.coordsWarp()[0])
            self.warpCoords.y.setValue(warp.dest.coordsWarp()[1])
            self.warpDir.setCurrentIndex(warp.dir)
            self.warpStyle.setValue(warp.style)
            self.warpUnknown.setValue(warp.unknown)
            self.warpComment.setPlainText(warp.comment)
            
            self.warpGroupBox.setEnabled(True)
            self.teleportGroupBox.setDisabled(True)
            
        elif isinstance(warp, Teleport):
            self.warpLabel.setText("Select a warp to edit.")
            self.teleportLabel.setText(f"Teleport {warp.id}")
            self.teleportCoords.x.setValue(warp.dest.coordsWarp()[0])
            self.teleportCoords.y.setValue(warp.dest.coordsWarp()[1])
            self.teleportFlag.setValue(warp.flag)
            self.teleportName.setText(warp.name)
            
            self.warpGroupBox.setDisabled(True)
            self.teleportGroupBox.setEnabled(True)
            
        else: # probably None
            self.warpLabel.setText("Select a warp to edit.")
            self.warpGroupBox.setDisabled(True)
            self.teleportLabel.setText("Select a teleport to edit.")
            self.teleportGroupBox.setDisabled(True)
            

        self.warpCoords.x.blockSignals(False)
        self.warpCoords.y.blockSignals(False)
        self.warpDir.blockSignals(False)
        self.warpStyle.blockSignals(False)
        self.warpUnknown.blockSignals(False)
        self.warpComment.blockSignals(False)
        
        self.teleportCoords.x.blockSignals(False)
        self.teleportCoords.y.blockSignals(False)
        self.teleportFlag.blockSignals(False)
        self.teleportName.blockSignals(False)
        
    def toWarp(self):
        warp = self.state.currentWarp
        if warp == None:
            return
        
        if isinstance(warp, Warp):
            coords = EBCoords.fromWarp(self.warpCoords.x.value(), 
                                       self.warpCoords.y.value())
            if warp.dest != coords:
                action = ActionMoveWarp(warp, coords)
                action.fromSidebar = True
                
                self.mapeditor.scene.undoStack.push(action)

            else:
                action = ActionUpdateWarp(warp,
                                          self.warpStyle.value(),
                                          self.warpUnknown.value(),
                                          self.warpComment.toPlainText())
                self.mapeditor.scene.undoStack.push(action)
            
            self.mapeditor.scene.refreshWarp(warp.id)
                
        if isinstance(warp, Teleport):
            coords = EBCoords.fromWarp(self.teleportCoords.x.value(),
                                       self.teleportCoords.y.value())

            if warp.dest != coords:
                action = ActionMoveTeleport(warp, coords)
                action.fromSidebar = True
                
                self.mapeditor.scene.undoStack.push(action)
                
            else:
                action = ActionUpdateTeleport(warp,
                                              self.teleportFlag.value(),
                                              self.teleportName.text())
                self.mapeditor.scene.undoStack.push(action)
            
            self.mapeditor.scene.refreshTeleport(warp.id)
        
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
        self.warpCoords.x.valueChanged.connect(self.toWarp)
        self.warpCoords.y.valueChanged.connect(self.toWarp)
        
        self.warpDir = QComboBox()
        self.warpDir.addItems(["Null",
                               "Up",
                               "Up-right",
                               "Right",
                               "Down-right",
                               "Down",
                               "Down-left",
                               "Left",
                               "Up-left"])
        self.warpDir.setToolTip("Direction to face after warping.")
        self.warpDir.currentIndexChanged.connect(self.toWarp)
        
        self.warpStyle = BaseChangerSpinbox()
        self.warpStyle.setMaximum(common.BYTELIMIT)
        self.warpStyle.setToolTip("Warp style to use. See the Warp Styles Table script in the CCS Library.")
        self.warpStyle.editingFinished.connect(self.toWarp)
        
        self.warpUnknown = BaseChangerSpinbox()
        self.warpUnknown.setMaximum(common.BYTELIMIT)
        self.warpUnknown.setToolTip("Unknown value. Seems to either be 0 or 127.")
        self.warpUnknown.editingFinished.connect(self.toWarp)
        
        self.warpComment = QPlainTextEdit()
        self.warpComment.textChanged.connect(self.toWarp)
        
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
        self.teleportCoords.x.valueChanged.connect(self.toWarp)
        self.teleportCoords.y.valueChanged.connect(self.toWarp)
        
        self.teleportFlag = FlagInput()
        self.teleportFlag.spinbox.setToolTip("Flag that unlocks this teleport location.")
        self.teleportFlag.editingFinished.connect(self.toWarp)
        
        self.teleportName = QLineEdit()
        self.teleportName.setToolTip("Name of the location in the PSI Teleport menu.")
        self.teleportName.editingFinished.connect(self.toWarp)
        
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
        
        self.warpGroupBox.setDisabled(True)
        self.teleportGroupBox.setDisabled(True)
        
        