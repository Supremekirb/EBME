import os
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (QComboBox, QFormLayout, QGroupBox, QLabel,
                               QLineEdit, QPlainTextEdit, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget)

import src.misc.common as common
from src.actions.misc_actions import MultiActionWrapper
from src.actions.npc_actions import (ActionChangeNPCInstance,
                                     ActionMoveNPCInstance, ActionUpdateNPC)
from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords
from src.misc.widgets import (BaseChangerSpinbox, CoordsInput, FlagInput,
                              HSeparator)
from src.objects.npc import NPC

if TYPE_CHECKING:
    from src.mapeditor.map_editor import MapEditor, MapEditorState


class SidebarNPC(QWidget):
    """Sidebar for NPC mode"""

    def __init__(self, parent, state: "MapEditorState", mapeditor: "MapEditor", projectData: ProjectData):
        super().__init__(parent)
        self.mapeditor = mapeditor
        self.state = state
        self.projectData = projectData

        self.setupUI()

    def fromNPCInstances(self):
        """Load NPCInstance data into sidebar. Also load NPC data right after."""
        
        self.instancePos.x.blockSignals(True)
        self.instancePos.y.blockSignals(True)
        self.instanceNPC.blockSignals(True)
        
        instances = self.state.currentNPCInstances
        
        if len(instances) == 0:
            self.deselectNPC()
            return
        
        if len(instances) == 1:
            self.instanceLabel.setText(f"Instance of NPC {instances[0].npcID}")
        else:
            self.instanceLabel.setText(f"{len(instances)} NPC instances selected.")
        
        if len(set(i.coords.x for i in instances)) == 1:
            self.instancePos.x.setValue(instances[0].coords.x)
        else:
            self.instancePos.x.clear()
        
        if len(set(i.coords.y for i in instances)) == 1:
            self.instancePos.y.setValue(instances[0].coords.y)
        else:
            self.instancePos.y.clear()
        
        if len(set(i.npcID for i in instances)) == 1:
            self.instanceNPC.setValue(instances[0].npcID)
        else:
            self.instanceNPC.clear()

        self.instancePos.x.blockSignals(False)
        self.instancePos.y.blockSignals(False)
        self.instanceNPC.blockSignals(False)

        self.instanceData.setEnabled(True)

        self.fromNPCs()
    
    def toNPCInstances(self):
        """Save NPC instance data from sidebar to the active NPC instances"""

        if len(self.state.currentNPCInstances) > 1:
            actionWrapper = MultiActionWrapper()
            if len(self.state.currentNPCInstances) == 1:
                actionWrapper.setText("Update NPC instance")
            else:
                actionWrapper.setText(f"Update {len(self.state.currentNPCInstances)} NPC instances")
            
            posChanged = False
            for i in self.state.currentNPCInstances:
                if i.coords.x != self.instancePos.x.value() or i.coords.y != self.instancePos.y.value():
                    posChanged = True
            
            if posChanged:
                for i in self.state.currentNPCInstances:
                    coords = EBCoords(self.instancePos.x.value() if not self.instancePos.isBlankX() else i.coords.x,
                                    self.instancePos.y.value() if not self.instancePos.isBlankY() else i.coords.y)
                    action = ActionMoveNPCInstance(i, coords)
                    action.fromSidebar = True # allow merge (does this work....?)
                    actionWrapper.addCommand(action)
                    
            npcChanged = False
            for i in self.state.currentNPCInstances:
                if i.npcID != self.instanceNPC.value():
                    npcChanged = True
                    
            if npcChanged:
                for i in self.state.currentNPCInstances:
                    action = ActionChangeNPCInstance(i,
                                                    self.instanceNPC.value() if not self.instanceNPC.isBlank() else i.npcID)
                    actionWrapper.addCommand(action)           
            
            self.mapeditor.scene.undoStack.push(actionWrapper)
            
        else:
            instance = self.state.currentNPCInstances[0]
            if instance.coords.x != self.instancePos.x.value() or instance.coords.y != self.instancePos.y.value():
                action = ActionMoveNPCInstance(instance,
                                               EBCoords(self.instancePos.x.value(),
                                                        self.instancePos.y.value()))
                
                action.fromSidebar = True # allow merge
                self.mapeditor.scene.undoStack.push(action)

            if instance.npcID != self.instanceNPC.value():
                action = ActionChangeNPCInstance(instance, self.instanceNPC.value())
                self.mapeditor.scene.undoStack.push(action)
         
        for i in self.state.currentNPCInstances:
            self.mapeditor.scene.refreshInstance(i.uuid)

    def fromNPCs(self):
        """Load NPC data into sidebar"""
        
        self.NPCSprite.blockSignals(True)
        self.NPCDirection.blockSignals(True)
        self.NPCMovement.blockSignals(True)
        self.NPCFlag.blockSignals(True)
        self.NPCShowSprite.blockSignals(True)
        self.NPCText1.blockSignals(True)
        self.NPCText2.blockSignals(True)
        self.NPCType.blockSignals(True)
        self.NPCComment.blockSignals(True)
        
        npcs = []
        for i in self.state.currentNPCInstances:
            npcs.append(self.projectData.getNPC(i.npcID))
        npcs = list(set(npcs)) # remove duplicates
        
        if len(set(i.sprite for i in npcs)) == 1:
            self.NPCSprite.setValue(npcs[0].sprite)
        else:
            self.NPCSprite.clear()
        
        if len(set(i.direction for i in npcs)) == 1:
            self.NPCDirection.setCurrentText(npcs[0].direction.capitalize())
        else:
            self.NPCDirection.setCurrentIndex(-1)
            
        if len(set(i.movement for i in npcs)) == 1:
            self.NPCMovement.setValue(npcs[0].movement)
        else:
            self.NPCMovement.clear()
            
        if len(set(i.flag for i in npcs)) == 1:
            self.NPCFlag.setValue(npcs[0].flag)
        else:
            self.NPCFlag.clear()
            
        if len(set(i.show for i in npcs)) == 1:
            self.NPCShowSprite.setCurrentText(npcs[0].show.capitalize())
        else:
            self.NPCShowSprite.setCurrentIndex(-1)
            
        if len(set(i.text1 for i in npcs)) == 1:
            self.NPCText1.setText(npcs[0].text1)
        else:
            self.NPCText1.clear()
            
        if len(set(i.text2 for i in npcs)) == 1:
            self.NPCText2.setText(npcs[0].text2)
        else:
            self.NPCText2.clear()
            
        if len(set(i.type for i in npcs)) == 1:
            self.NPCType.setCurrentText(npcs[0].type.capitalize())
        else:
            self.NPCType.setCurrentIndex(-1)
            
        if len(set(i.comment for i in npcs)) == 1:
            self.NPCComment.setPlainText(npcs[0].comment)
        else:
            self.NPCComment.clear()

        self.NPCSprite.blockSignals(False)
        self.NPCDirection.blockSignals(False)
        self.NPCMovement.blockSignals(False)
        self.NPCFlag.blockSignals(False)
        self.NPCShowSprite.blockSignals(False)
        self.NPCText1.blockSignals(False)
        self.NPCText2.blockSignals(False)
        self.NPCType.blockSignals(False)
        self.NPCComment.blockSignals(False)

        self.NPCData.setEnabled(True)
    
    def toNPCs(self):
        """Save NPC data from sidebar to active state NPCs"""
        
        npcs: list[NPC] = []
        for i in self.state.currentNPCInstances:
            npcs.append(self.projectData.getNPC(i.npcID))
        npcs = list(set(npcs)) # remove duplicates
        
        actionWrapper = MultiActionWrapper()
        if len(npcs) == 1:
            actionWrapper.setText(f"Update NPC {npcs[0].id}")
        else:
            actionWrapper.setText(f"Update {len(npcs)} NPCs")
            
        for i in npcs:
            action = ActionUpdateNPC(i,
                        self.NPCSprite.value() if not self.NPCSprite.isBlank() else i.sprite,
                        self.NPCDirection.currentText().lower() if self.NPCDirection.currentText() != "" else i.direction,
                        self.NPCMovement.value() if not self.NPCMovement.isBlank() else i.movement,
                        self.NPCFlag.value() if not self.NPCFlag.isBlank() else i.flag,
                        self.NPCShowSprite.currentText().lower() if self.NPCShowSprite.currentText() != "" else i.show,
                        self.NPCText1.text() if self.NPCText1.text() != "" else i.text1,
                        self.NPCText2.text() if self.NPCText2.text() != "" else i.text2,
                        self.NPCType.currentText().lower() if self.NPCType.currentText() != "" else i.type,
                        self.NPCComment.toPlainText() if self.NPCComment.toPlainText() != "" else i.comment)

            actionWrapper.addCommand(action)
        
        self.mapeditor.scene.undoStack.push(actionWrapper)
        for i in npcs:
            self.mapeditor.scene.refreshNPC(i.id)

    def deselectNPC(self):
        self.instanceData.setEnabled(False)
        self.NPCData.setEnabled(False)
        self.instanceLabel.setText("Select an NPC to edit.")

    def setupUI(self):
        self.instanceLabel = QLabel("Select an NPC to edit.")
        self.instanceLabel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        #####
        self.instanceData = QGroupBox("Instance Data", self)
        self.instanceData.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.instanceDataLayout = QFormLayout(self.instanceData)

        self.instancePos = CoordsInput()
        self.instancePos.x.setMaximum(common.EBMAPWIDTH-1)
        self.instancePos.y.setMaximum(common.EBMAPHEIGHT-1)

        self.instanceNPC = BaseChangerSpinbox(self.instanceData)
        self.instanceNPC.setMaximum(len(self.projectData.npcs)-1)

        self.instanceDataLayout.addRow("Position", self.instancePos)
        self.instanceDataLayout.addRow("NPC ID", self.instanceNPC)
        self.instanceData.setLayout(self.instanceDataLayout)

        self.instancePos.x.valueChanged.connect(self.toNPCInstances)
        self.instancePos.y.valueChanged.connect(self.toNPCInstances)
        self.instanceNPC.valueChanged.connect(self.toNPCInstances)
        self.instanceNPC.valueChanged.connect(self.fromNPCs)
        self.instanceNPC.valueChanged.connect(lambda: self.instanceLabel.setText(f"Instance of NPC {self.instanceNPC.value()}") if len(self.state.currentNPCInstances) == 1 else None)
        #####

        #####
        self.NPCData = QGroupBox("NPC Data", self)
        self.NPCDataLayout = QFormLayout(self.NPCData)

        self.NPCSprite = BaseChangerSpinbox(self.NPCData)
        self.NPCSprite.setMaximum(len(self.projectData.sprites)-1)
        self.NPCSprite.setToolTip("Sprite to use for the NPC. This is a sprite in /SpriteGroups.")

        self.NPCDirection = QComboBox(self.NPCData)
        self.NPCDirection.addItems(["Up",
                                    "Up-right",
                                    "Right",
                                    "Down-right",
                                    "Down",
                                    "Down-left",
                                    "Left",
                                    "Up-left"])
        self.NPCDirection.setToolTip("Direction the NPC is facing when it spawns. Item-type NPCs should be set to Down.")
        
        self.NPCMovement = BaseChangerSpinbox(self.NPCData)
        self.NPCMovement.setMaximum(common.WORDLIMIT)
        self.NPCMovement.setToolTip("""Action Script ID for the NPC to use.
Common values include:
0x08 (8): Stand in place, turn to face when spoken to.
0x09 (9): Present boxes. Controls if they are open or closed based on their flag.
0x0C (12): Standard NPC wandering.
0x025D (605): Stand in place, turn to face when spoken to, turn back.
0x025E (606): Walk in place, turn to face when spoken to, turn back.""")

        self.NPCFlag = FlagInput(False)
        self.NPCFlag.spinbox.setToolTip("""Flag to use for the NPC. Use 0 if you don't need it.
This can control more than just when it appears.
Item-type NPCs use this to determine if they are open or closed.""")
        
        
        self.NPCShowSprite = QComboBox(self.NPCData)
        self.NPCShowSprite.addItems(["Always",
                                  "When event flag set",
                                  "When event flag unset"])
        self.NPCShowSprite.setToolTip("Depending on the flag, if the NPC will appear.")
        
        self.NPCText1 = QLineEdit(self.NPCData)
        self.NPCText1.setToolTip("Dialogue to use when the NPC is interacted with. $0 for no interaction.")
        self.openNPCText1 = QPushButton("Edit CCS", self.NPCData)
        self.openNPCText1.clicked.connect(lambda: common.openCCSFromLabel(self.NPCText1.text(),
                                                                          os.path.join(self.projectData.dir,
                                                                                       "ccscript")))
        self.NPCText2 = QLineEdit(self.NPCData)
        self.NPCText2.setToolTip("""Different behavior depending on type:
Person & Object: Dialogue to display when an item is used. $0 for no interaction.
Item: Item ID to give. 0x100 (256) is empty. Higher values give (value-0x100) cash.""")
        self.openNPCText2 = QPushButton("Edit CCS", self.NPCData)
        self.openNPCText2.clicked.connect(lambda: common.openCCSFromLabel(self.NPCText2.text(),
                                                                          os.path.join(self.projectData.dir,
                                                                                       "ccscript")))
        self.NPCType = QComboBox(self.NPCData)
        self.NPCType.addItems(["Person",
                               "Item",
                               "Object"])
        self.NPCType.setToolTip("""Person: NPC that can be interacted with via "Talk To".
Item: Present boxes and the like.
Object: NPC that can be interacted with via "Check".""")
        
        self.NPCComment = QPlainTextEdit(self.NPCData)
        
        self.NPCDataLayout.addRow("Sprite", self.NPCSprite)
        self.NPCDataLayout.addRow("Direction", self.NPCDirection)
        self.NPCDataLayout.addRow("Movement", self.NPCMovement)
        self.NPCDataLayout.addRow(HSeparator())
        self.NPCDataLayout.addRow("Flag", self.NPCFlag)
        self.NPCDataLayout.addRow("Appears", self.NPCShowSprite)
        self.NPCDataLayout.addRow(HSeparator())
        self.NPCDataLayout.addRow("Dialogue", self.NPCText1)
        self.NPCDataLayout.addWidget(self.openNPCText1)
        self.NPCDataLayout.addRow("Extra Data", self.NPCText2)
        self.NPCDataLayout.addWidget(self.openNPCText2)
        self.NPCDataLayout.addRow("Type", self.NPCType)
        self.NPCDataLayout.addRow("Comments", self.NPCComment)

        self.NPCSprite.valueChanged.connect(self.toNPCs)
        self.NPCDirection.currentIndexChanged.connect(self.toNPCs)
        self.NPCMovement.editingFinished.connect(self.toNPCs)
        self.NPCFlag.editingFinished.connect(self.toNPCs)
        self.NPCFlag.inverted.connect(self.toNPCs)
        self.NPCShowSprite.currentIndexChanged.connect(self.toNPCs)
        self.NPCText1.editingFinished.connect(self.toNPCs)
        self.NPCText2.editingFinished.connect(self.toNPCs)
        self.NPCType.currentIndexChanged.connect(self.toNPCs)
        self.NPCComment.textChanged.connect(self.toNPCs)
        #####

        self.contentLayout = QVBoxLayout(self)
        self.contentLayout.addWidget(self.instanceLabel)
        self.contentLayout.addWidget(HSeparator())
        self.contentLayout.addWidget(self.instanceData)
        self.contentLayout.addWidget(HSeparator())
        self.contentLayout.addWidget(self.NPCData)
        
        self.setLayout(self.contentLayout)

        self.instanceData.setEnabled(False)
        self.NPCData.setEnabled(False)