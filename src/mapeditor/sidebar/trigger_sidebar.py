import os
from typing import TYPE_CHECKING

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QComboBox, QFormLayout, QGroupBox, QLabel,
                               QLineEdit, QPushButton, QSizePolicy,
                               QVBoxLayout, QWidget)

import src.misc.common as common
import src.objects.trigger as trigger
from src.actions.misc_actions import MultiActionWrapper
from src.actions.trigger_actions import ActionMoveTrigger, ActionUpdateTrigger
from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords
from src.misc.widgets import (BaseChangerSpinbox, CoordsInput, FlagInput,
                              HSeparator)

if TYPE_CHECKING:
    from src.mapeditor.map_editor import MapEditor, MapEditorState
    

class SidebarTrigger(QWidget):
    """Sidebar for trigger mode"""

    def __init__(self, parent, state: "MapEditorState", mapeditor: "MapEditor", projectData: ProjectData):
        QWidget.__init__(self)
        self.setParent(parent)
        self.mapeditor = mapeditor
        self.state = state
        self.projectData = projectData

        self.setupUI()

    def switchTriggerForm(self):
        type = self.generalType.currentData(0)

        self.doorData.hide()
        self.escalatorData.hide()
        self.ladderData.hide()
        self.objectData.hide()
        self.personData.hide()
        self.ropeData.hide()
        self.stairwayData.hide()
        self.switchData.hide()
        self.dummyData.hide()

        match type:
            case "Door":
                self.doorData.show()
            case "Escalator":
                self.escalatorData.show()
            case "Ladder":
                self.ladderData.show()
            case "Object":
                self.objectData.show()
            case "Person":
                self.personData.show()
            case "Rope":
                self.ropeData.show()
            case "Stairway":
                self.stairwayData.show()
            case "Switch":
                self.switchData.show()
            
            case _:
                self.dummyData.show()
                # Otherwise the spacing goes funky

    def setDoorDest(self, coords: EBCoords):
        self.doorDest.x.setValue(coords.coordsWarp()[0])
        self.doorDest.y.setValue(coords.coordsWarp()[1])
        self.toTriggers()

    def deselectTrigger(self):
        self.generalData.setEnabled(False)
        self.doorData.setEnabled(False)
        self.escalatorData.setEnabled(False)
        self.ladderData.setEnabled(False)
        self.objectData.setEnabled(False)
        self.personData.setEnabled(False)
        self.ropeData.setEnabled(False)
        self.stairwayData.setEnabled(False)
        self.switchData.setEnabled(False)
        self.dummyData.setEnabled(False)
        self.triggerLabel.setText("Select a trigger to edit.")

    def fromTriggers(self):
        """Load the data from a trigger into the sidebar for editing"""

        self.generalPos.x.blockSignals(True)
        self.generalPos.y.blockSignals(True)
        self.generalType.blockSignals(True)
        self.doorDest.x.blockSignals(True)
        self.doorDest.y.blockSignals(True)
        self.doorDirection.blockSignals(True)
        self.doorFlag.blockSignals(True)
        self.doorStyle.blockSignals(True)
        self.doorText.blockSignals(True)
        self.escalatorDir.blockSignals(True)
        self.objectText.blockSignals(True)
        self.personText.blockSignals(True)
        self.stairwayDir.blockSignals(True)
        self.switchFlag.blockSignals(True)
        self.switchText.blockSignals(True)

        self.generalData.setEnabled(True)
        self.doorData.setEnabled(True)
        self.escalatorData.setEnabled(True)
        self.ladderData.setEnabled(True)
        self.objectData.setEnabled(True)
        self.personData.setEnabled(True)
        self.ropeData.setEnabled(True)
        self.stairwayData.setEnabled(True)
        self.switchData.setEnabled(True)
        self.dummyData.setEnabled(True)
        
        triggers = self.state.currentTriggers
        
        if len(triggers) == 0:
            self.deselectTrigger()
            return
    
        if len(triggers) == 1:
            self.triggerLabel.setText(f"Trigger at ({triggers[0].coords.coordsWarp()[0]}, {triggers[0].coords.coordsWarp()[1]})")
        else:
            self.triggerLabel.setText(f"{len(triggers)} triggers selected.")

        if len(set(i.coords.x for i in triggers)) == 1:
            self.generalPos.x.setValue(triggers[0].coords.coordsWarp()[0])
        else:
            self.generalPos.x.clear()
            
        if len(set(i.coords.y for i in triggers)) == 1:
            self.generalPos.y.setValue(triggers[0].coords.coordsWarp()[1])
        else: self.generalPos.y.clear()
        
        # if they use different types
        if not all(isinstance(i.typeData, type(triggers[0].typeData)) for i in triggers):
            self.generalType.setCurrentIndex(-1)
        else:
            match type(triggers[0].typeData):
                case trigger.TriggerDoor:
                    self.generalType.setCurrentIndex(0)
                    if len(set(i.typeData.destCoords.coordsWarp()[0] for i in triggers)) == 1:    
                        self.doorDest.x.setValue(triggers[0].typeData.destCoords.coordsWarp()[0])
                    else:
                        self.doorDest.x.clear()
                    
                    if len(set(i.typeData.destCoords.coordsWarp()[1] for i in triggers)) == 1:
                        self.doorDest.y.setValue(triggers[0].typeData.destCoords.coordsWarp()[1])
                    else:
                        self.doorDest.y.clear()
                    
                    if len(set(i.typeData.dir for i in triggers)) == 1:
                        self.doorDirection.setCurrentText(triggers[0].typeData.dir.capitalize())
                    else:
                        self.doorDirection.setCurrentIndex(-1)
                    
                    if len(set(i.typeData.flag for i in triggers)) == 1:
                        self.doorFlag.setValue(triggers[0].typeData.flag)
                    else:
                        self.doorFlag.clear()
                        
                    if len(set(i.typeData.style for i in triggers)) == 1:
                        self.doorStyle.setValue(triggers[0].typeData.style)
                    else:
                        self.doorStyle.clear()
                        
                    if len(set(i.typeData.textPointer for i in triggers)) == 1:
                        self.doorText.setText(triggers[0].typeData.textPointer)
                    else:
                        self.doorText.clear()
                        
                case trigger.TriggerEscalator:
                    self.generalType.setCurrentIndex(1)
                    if len(set(i.typeData.direction for i in triggers)) == 1:
                        if triggers[0].typeData.direction == "nowhere":
                            self.escalatorDir.setCurrentText("Nowhere")
                        else:
                            self.escalatorDir.setCurrentText(triggers[0].typeData.direction.upper())
                    else:
                        self.escalatorDir.setCurrentIndex(-1)

                case trigger.TriggerLadder:
                    self.generalType.setCurrentIndex(2)
                    
                case trigger.TriggerObject:
                    self.generalType.setCurrentIndex(3)
                    if len(set(i.typeData.textPointer for i in triggers)) == 1:
                        self.objectText.setText(triggers[0].typeData.textPointer)
                    else:
                        self.objectText.clear()
                        
                case trigger.TriggerPerson:
                    self.generalType.setCurrentIndex(4)
                    if len(set(i.typeData.textPointer for i in triggers)) == 1:
                        self.personText.setText(triggers[0].typeData.textPointer)
                    else:
                        self.personText.clear()
                        
                case trigger.TriggerRope:
                    self.generalType.setCurrentIndex(5)
                    
                case trigger.TriggerStairway:
                    self.generalType.setCurrentIndex(6)
                    if len(set(i.typeData.direction for i in triggers)) == 1:
                        self.stairwayDir.setCurrentText(triggers[0].typeData.direction.upper())
                    else:
                        self.stairwayDir.setCurrentIndex(-1)

                case trigger.TriggerSwitch:
                    self.generalType.setCurrentIndex(7)
                    if len(set(i.typeData.flag for i in triggers)) == 1:
                        self.switchFlag.setValue(triggers[0].typeData.flag)
                    else:
                        self.switchFlag.clear()
                    if len(set(i.typeData.textPointer for i in triggers)) == 1:
                        self.switchText.setText(triggers[0].typeData.textPointer)
                    else:
                        self.switchText.clear()
        
        self.switchTriggerForm()

        self.generalPos.x.blockSignals(False)
        self.generalPos.y.blockSignals(False)
        self.generalType.blockSignals(False)
        self.doorDest.x.blockSignals(False)
        self.doorDest.y.blockSignals(False)
        self.doorDirection.blockSignals(False)
        self.doorFlag.blockSignals(False)
        self.doorStyle.blockSignals(False)
        self.doorText.blockSignals(False)
        self.escalatorDir.blockSignals(False)
        self.objectText.blockSignals(False)
        self.personText.blockSignals(False)
        self.stairwayDir.blockSignals(False)
        self.switchFlag.blockSignals(False)
        self.switchText.blockSignals(False)

    def toTriggers(self):
        """Save the data from the sidebar to the current triggers"""
        if len(self.state.currentTriggers) > 0:
            actionWrapper = MultiActionWrapper()
            if len(self.state.currentTriggers) == 1:
                actionWrapper.setText("Update trigger")
            else:
                actionWrapper.setText(f"Update {len(self.state.currentTriggers)} triggers")
            for i in self.state.currentTriggers:
                if i.coords.coordsWarp()[0] != self.generalPos.x.value() or i.coords.coordsWarp()[1] != self.generalPos.y.value():
                    action = ActionMoveTrigger(i,
                                               EBCoords.fromWarp(self.generalPos.x.value() if not self.generalPos.isBlankX() else i.coords.x//8,
                                                                 self.generalPos.y.value() if not self.generalPos.isBlankY() else i.coords.y//8))
                    action.fromSidebar = True # does it do anything?
                    actionWrapper.addCommand(action)

                # first, check if the to-be-saved type is different from the current
                # if so, create a new one with blank data
                # otherwise fields like text are blank
                match self.generalType.currentData(0):
                    case "Door":
                        if not isinstance(i.typeData, trigger.TriggerDoor):
                            typeData = trigger.TriggerDoor()
                        else:
                            typeData = trigger.TriggerDoor(
                                EBCoords.fromWarp(self.doorDest.x.value() if not self.doorDest.isBlankX() else i.typeData.destCoords.x//8,
                                                  self.doorDest.y.value() if not self.doorDest.isBlankY() else i.typeData.destCoords.y//8),
                                                  self.doorDirection.currentText().lower() if self.doorDirection.currentText() != "" else i.typeData.dir,
                                                  self.doorFlag.value() if not self.doorFlag.isBlank() else i.typeData.flag,
                                                  self.doorStyle.value() if not self.doorStyle.isBlank() else i.typeData.style,
                                                  self.doorText.text() if self.doorText.text() != "" else i.typeData.textPointer)
                    case "Escalator":
                        if not isinstance(i.typeData, trigger.TriggerEscalator):
                            typeData = trigger.TriggerEscalator()
                        else:
                            typeData = trigger.TriggerEscalator(self.escalatorDir.currentText().lower() if self.escalatorDir.currentText() != "" else i.typeData.direction)
                    case "Ladder":
                        if not isinstance(i.typeData, trigger.TriggerLadder):
                            typeData = trigger.TriggerLadder()
                        else: # not strictly necessary. just consistent
                            typeData = trigger.TriggerLadder()
                    case "Object":
                        if not isinstance(i.typeData, trigger.TriggerObject):
                            typeData = trigger.TriggerObject()
                        else:
                            typeData = trigger.TriggerObject(self.objectText.text() if self.objectText.text() != "" else i.typeData.textPointer)
                    case "Person":
                        if not isinstance(i.typeData, trigger.TriggerPerson):
                            typeData = trigger.TriggerPerson()
                        else:
                            typeData = trigger.TriggerPerson(self.personText.text() if self.personText.text() != "" else i.typeData.textPointer)
                    case "Rope":
                        if not isinstance(i.typeData, trigger.TriggerRope):
                            typeData = trigger.TriggerRope()
                        else:
                            typeData = trigger.TriggerRope()
                    case "Stairway":
                        if not isinstance(i.typeData, trigger.TriggerStairway):
                            typeData = trigger.TriggerStairway()
                        else:
                            typeData = trigger.TriggerStairway(self.stairwayDir.currentText().lower() if self.stairwayDir.currentText() != "" else i.typeData.direction)
                    case "Switch":
                        if not isinstance(i.typeData, trigger.TriggerSwitch):
                            typeData = trigger.TriggerSwitch()
                        else:
                            typeData = trigger.TriggerSwitch(self.switchText.text() if self.switchText.text() != "" else i.typeData.textPointer,
                                                             self.switchFlag.value() if not self.switchFlag.isBlank() else i.typeData.flag)
                    case _:
                        typeData = i.typeData
                        
                action = ActionUpdateTrigger(i, typeData)
                actionWrapper.addCommand(action)
            self.mapeditor.scene.undoStack.push(actionWrapper)
        
        for i in self.state.currentTriggers:
            self.mapeditor.scene.refreshTrigger(i.uuid)

    def setupUI(self):
        self.triggerLabel = QLabel("Select a trigger to edit.")
        self.triggerLabel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        #####
        self.generalData = QGroupBox("General Data")
        self.generalData.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.generalDataLayout = QFormLayout(self.generalData)

        self.generalPos = CoordsInput()
        self.generalPos.x.setMaximum(common.pixToWarp(common.EBMAPWIDTH-1))
        self.generalPos.y.setMaximum(common.pixToWarp(common.EBMAPHEIGHT-1))

        self.generalPos.x.setToolTip("Position of the trigger. Trigger coordinates are in pixels/8.")
        self.generalPos.y.setToolTip("Position of the trigger. Trigger coordinates are in pixels/8.")

        self.generalType = QComboBox(self.generalData)
        self.generalType.addItem(QIcon(":/triggers/triggerDoor.png"), "Door")
        self.generalType.addItem(QIcon(":/triggers/triggerEscalator.png"), "Escalator")
        self.generalType.addItem(QIcon(":/triggers/triggerLadder.png"), "Ladder")
        self.generalType.addItem(QIcon(":/triggers/triggerObject.png"), "Object")
        self.generalType.addItem(QIcon(":/triggers/triggerPerson.png"), "Person")
        self.generalType.addItem(QIcon(":/triggers/triggerRope.png"), "Rope")
        self.generalType.addItem(QIcon(":/triggers/triggerStairway.png"), "Stairway")
        self.generalType.addItem(QIcon(":/triggers/triggerSwitch.png"), "Switch") 
        self.generalType.setToolTip("""Type of the trigger.
Door: Warps the player to a different location and/or displays text.
Escalator: Moves the player in a certain direction until they hit a "Nowhere" escalator.
Ladder: A climbable area. Characters use ladder sprites.
Object: A location that can be "Check"ed
Person: A location that can be "Talk To"'d
Rope: A climbable area. Characters use rope sprites.
Stairway: The player can only move diagonally until they hit another stairway.
Switch: Automatically triggers some text when walked over, if the flag is set.""")      
        self.generalType.currentIndexChanged.connect(self.toTriggers)
        self.generalType.currentIndexChanged.connect(self.switchTriggerForm)
        
        self.generalDataLayout.addRow("Position", self.generalPos)
        self.generalDataLayout.addRow("Type", self.generalType)

        self.generalData.setLayout(self.generalDataLayout)

        self.generalPos.x.valueChanged.connect(self.toTriggers)
        self.generalPos.y.valueChanged.connect(self.toTriggers)
        #####

        # The idea from here is that each type of door will have its own data form, and
        # we switch those out based on the currently selected type in generalType.
        # (wrote this before i knew about QStackedWidget lol)

        #####
        self.doorData = QGroupBox("Door Data")
        self.doorDataLayout = QFormLayout(self.doorData)

        self.doorDest = CoordsInput()
        self.doorDest.x.setMaximum((common.EBMAPWIDTH-1)//8)
        self.doorDest.y.setMaximum((common.EBMAPHEIGHT-1)//8)
        self.doorDest.x.setToolTip("Destination of the door. Trigger coordinates are in pixels/8.")
        self.doorDest.y.setToolTip("Destination of the door. Trigger coordinates are in pixels/8.")

        self.doorJump = QPushButton("Jump to")
        self.doorSet = QPushButton("Set destination")

        self.doorDirection = QComboBox(self.doorData)
        self.doorDirection.addItems(["Up",
                                     "Right",
                                     "Down",
                                     "Left"])
        self.doorDirection.setToolTip("Direction the player will face after warping.")
        
        self.doorFlag = FlagInput(True)
        self.doorFlag.spinbox.setToolTip("The door will only work if this flag is set.")

        self.doorStyle = BaseChangerSpinbox(self.doorData)
        self.doorStyle.setMaximum(common.BYTELIMIT)
        self.doorStyle.setToolTip("Warp style to use. See the Warp Styles Table script in the CCS Library.")

        self.doorText = QLineEdit(self.doorData)
        self.doorText.setToolTip("""Text to display when the player touches the door.
Do this and set the position to one warp tile below the door to only display text and not warp.""")
        
        self.openDoorText = QPushButton("Edit CCS", self.doorData)
        self.openDoorText.clicked.connect(lambda: common.openCCSFromLabel(self.doorText.text(),
                                                                         os.path.join(self.projectData.dir,
                                                                                      "ccscript")))

        self.doorDataLayout.addRow("Destination", self.doorDest)
        self.doorDataLayout.addRow(self.doorJump, self.doorSet)
        self.doorDataLayout.addRow("Direction", self.doorDirection)
        self.doorDataLayout.addRow("Flag", self.doorFlag)
        self.doorDataLayout.addRow("Style", self.doorStyle)
        self.doorDataLayout.addRow("Pointer", self.doorText)
        self.doorDataLayout.addWidget(self.openDoorText)

        self.doorData.setLayout(self.doorDataLayout)

        self.doorDest.x.editingFinished.connect(self.toTriggers)
        self.doorDest.y.editingFinished.connect(self.toTriggers)
        self.doorDirection.currentIndexChanged.connect(self.toTriggers)
        self.doorFlag.editingFinished.connect(self.toTriggers)
        self.doorFlag.inverted.connect(self.toTriggers)
        self.doorStyle.editingFinished.connect(self.toTriggers)
        self.doorText.editingFinished.connect(self.toTriggers)

        self.doorJump.pressed.connect(lambda: self.mapeditor.view.revealTriggerDestination(
            EBCoords.fromWarp(self.generalPos.x.value(), self.generalPos.y.value()),
            EBCoords.fromWarp(self.doorDest.x.value(), self.doorDest.y.value())))
        
        self.doorSet.pressed.connect(lambda: self.mapeditor.scene.startSetDoorDest(
            EBCoords.fromWarp(self.generalPos.x.value(), self.generalPos.y.value())))
        #####

        #####
        self.escalatorData = QGroupBox("Escalator Data")
        self.escalatorDataLayout = QFormLayout(self.escalatorData)
        
        self.escalatorDir = QComboBox(self.escalatorData)
        self.escalatorDir.addItems(["NW",
                                    "NE",
                                    "SW",
                                    "SE",
                                    "Nowhere"])
        self.escalatorDir.setToolTip("Direction the escalator will send the player in. Nowhere specifies end points of escalators.")
        
        self.escalatorDataLayout.addRow("Direction", self.escalatorDir)

        self.escalatorData.setLayout(self.escalatorDataLayout)

        self.escalatorDir.currentIndexChanged.connect(self.toTriggers)
        #####

        #####
        self.ladderData = QWidget()
        #####

        #####
        self.objectData = QGroupBox("Object Data")
        self.objectDataLayout = QFormLayout(self.objectData)

        self.objectText = QLineEdit(self.objectData)
        self.objectText.setToolTip("Text to display when the player checks the trigger.")

        self.openObjectText = QPushButton("Edit CCS", self.objectData)
        self.openObjectText.clicked.connect(lambda: common.openCCSFromLabel(self.objectText.text(),
                                                                           os.path.join(self.projectData.dir,
                                                                                        "ccscript")))

        self.objectDataLayout.addRow("Pointer", self.objectText)
        self.objectDataLayout.addWidget(self.openObjectText)
        self.objectData.setLayout(self.objectDataLayout)

        self.objectText.editingFinished.connect(self.toTriggers)
        #####

        #####
        self.personData = QGroupBox("Person Data")
        self.personDataLayout = QFormLayout(self.personData)

        self.personText = QLineEdit(self.personData)
        self.openPersonText = QPushButton("Edit CCS", self.personData)
        self.personText.setToolTip("Text to display when the player talks to the trigger.")

        self.openPersonText.clicked.connect(lambda: common.openCCSFromLabel(self.personText.text(),
                                                                            os.path.join(self.projectData.dir,
                                                                                         "ccscript")))

        self.personDataLayout.addRow("Pointer", self.personText)
        self.personDataLayout.addWidget(self.openPersonText)
        self.personData.setLayout(self.personDataLayout)

        self.personText.editingFinished.connect(self.toTriggers)
        #####

        #####
        self.ropeData = QWidget()
        #####

        #####
        self.stairwayData = QGroupBox("Stairway Data")
        self.stairwayDataLayout = QFormLayout(self.stairwayData)
        
        self.stairwayDir = QComboBox(self.stairwayData)
        self.stairwayDir.addItems(["NW",
                                    "NE",
                                    "SW",
                                    "SE",
                                    "Nowhere"])
        self.stairwayDir.setToolTip("Direction the stairs will send the player in. Players can walk forwards and backwards along this angle.")
        
        self.stairwayDataLayout.addRow("Direction", self.stairwayDir)

        self.stairwayData.setLayout(self.stairwayDataLayout)

        self.stairwayDir.currentIndexChanged.connect(self.toTriggers)
        #####

        #####
        self.switchData = QGroupBox("Switch Data")
        self.switchDataLayout = QFormLayout(self.switchData)

        self.switchText = QLineEdit(self.switchData)
        self.openSwitchText = QPushButton("Edit CCS", self.switchData)
        self.openSwitchText.clicked.connect(lambda: common.openCCSFromLabel(self.switchText.text(),
                                                                           os.path.join(self.projectData.dir,
                                                                                        "ccscript")))
        self.switchText.setToolTip("Text to display when the player steps on the trigger.")

        self.switchFlag = FlagInput(True)
        self.switchFlag.spinbox.setToolTip("The switch will only work if this flag is set.")

        self.switchDataLayout.addRow("Flag", self.switchFlag)
        self.switchDataLayout.addRow("Pointer", self.switchText)
        self.switchDataLayout.addWidget(self.openSwitchText)
        self.switchData.setLayout(self.switchDataLayout)

        self.switchFlag.editingFinished.connect(self.toTriggers)
        self.switchFlag.inverted.connect(self.toTriggers)
        self.switchText.editingFinished.connect(self.toTriggers)
        #####

        #####
        self.dummyData = QWidget()
        #####

        self.contentLayout = QVBoxLayout(self)
        self.contentLayout.addWidget(self.triggerLabel)
        self.contentLayout.addWidget(HSeparator())
        self.contentLayout.addWidget(self.generalData)
        self.contentLayout.addWidget(self.doorData)
        self.contentLayout.addWidget(self.escalatorData)
        self.contentLayout.addWidget(self.ladderData)
        self.contentLayout.addWidget(self.objectData)
        self.contentLayout.addWidget(self.personData)
        self.contentLayout.addWidget(self.ropeData)
        self.contentLayout.addWidget(self.stairwayData)
        self.contentLayout.addWidget(self.switchData)
        self.contentLayout.addWidget(self.dummyData)

        self.switchTriggerForm()
        self.setLayout(self.contentLayout)

        self.generalData.setEnabled(False)
        self.doorData.setEnabled(False)
        self.escalatorData.setEnabled(False)
        self.ladderData.setEnabled(False)
        self.objectData.setEnabled(False)
        self.personData.setEnabled(False)
        self.ropeData.setEnabled(False)
        self.stairwayData.setEnabled(False)
        self.switchData.setEnabled(False)
        self.dummyData.setEnabled(False)
