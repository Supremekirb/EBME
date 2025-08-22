from typing import TYPE_CHECKING

from PySide6.QtCore import QFile, QIODevice, QTextStream
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (QComboBox, QFileDialog, QFormLayout, QGroupBox,
                               QHBoxLayout, QItemDelegate, QLabel, QLineEdit,
                               QPushButton, QSizePolicy, QTableWidget,
                               QTableWidgetItem, QToolButton, QVBoxLayout,
                               QWidget)

import src.misc.common as common
import src.misc.icons as icons
from src.actions.sector_actions import ActionChangeSectorAttributes
from src.coilsnake.project_data import ProjectData
from src.misc.dialogues import ImportUserdataDialog, NewUserdataDialog
from src.misc.map_music_editor import MapMusicEditor
from src.objects.sector import Int8, Int16, Sector
from src.widgets.input import BaseChangerSpinbox, CoordsInput
from src.widgets.layout import HSeparator

if TYPE_CHECKING:
    from src.mapeditor.map_editor import MapEditor, MapEditorState
    

class SidebarSector(QWidget):
    """Sidebar for sector mode"""

    def __init__(self, parent, state: "MapEditorState", mapeditor: "MapEditor", projectData: ProjectData):
        super().__init__(parent)
        
        self.mapeditor = mapeditor
        self.state = state
        self.projectData = projectData

        self.setupUI()
        
    def fromSectors(self):
        # block signals so we don't save as we load
        self.tilesetSelect.blockSignals(True)
        self.paletteGroupSelect.blockSignals(True)
        self.paletteSelect.blockSignals(True)
        self.itemSelect.blockSignals(True)
        self.musicSelect.blockSignals(True)
        self.propertySelect.blockSignals(True)
        self.teleportSelect.blockSignals(True)  
        self.townMapSelect.blockSignals(True)
        self.townMapArrowSelect.blockSignals(True)
        self.townMapImageSelect.blockSignals(True)
        self.townMapPos.x.blockSignals(True)
        self.townMapPos.y.blockSignals(True)
        self.dataTable.blockSignals(True)
        
        sectors = self.state.currentSectors
        # if all sectors are the same, show their data
        # otherwise, blank out data spots
        if len(sectors) == 1:
            self.sectorLabel.setText(f"Sector {sectors[0].id} at {sectors[0].coords.coordsSector()[0], sectors[0].coords.coordsSector()[1]}")
        elif len(sectors) > 1:
            self.sectorLabel.setText(f"{len(sectors)} sectors selected")            

        if len(set(sector.tileset for sector in sectors)) == 1:
            self.tilesetSelect.setCurrentText(str(sectors[0].tileset))
            self.paletteGroupSelect.clear()
            self.paletteGroupSelect.addItems(i for i in self.getPaletteGroups())
        else:
            self.paletteGroupSelect.clear()
            self.tilesetSelect.setCurrentIndex(-1)
        
        if len(set(sector.palettegroup for sector in sectors)) == 1:
            self.paletteGroupSelect.setCurrentText(str(sectors[0].palettegroup))
            self.paletteSelect.clear()
            self.paletteSelect.addItems(i for i in self.getPalettes())
        else:
            self.paletteSelect.clear()
            self.paletteGroupSelect.setCurrentIndex(-1)
            
        if len(set(sector.palette for sector in sectors)) == 1:
            self.paletteSelect.setCurrentText(str(sectors[0].palette))
        else:
            self.paletteSelect.setCurrentIndex(-1)
            
        if len(set(sector.item for sector in sectors)) == 1:
            self.itemSelect.setValue(sectors[0].item)
        else:
            self.itemSelect.clear()
        if len(set(sector.music for sector in sectors)) == 1:
            self.musicSelect.setValue(sectors[0].music)
        else:
            self.musicSelect.clear()
            
        if len(set(sector.setting for sector in sectors)) == 1:
            self.propertySelect.setCurrentText(sectors[0].setting.capitalize())
        else:
            self.propertySelect.setCurrentIndex(-1)
            
        if len(set(sector.teleport for sector in sectors)) == 1:
            self.teleportSelect.setCurrentText(sectors[0].teleport.capitalize())
        else:
            self.teleportSelect.setCurrentIndex(-1)
        if len(set(sector.townmap for sector in sectors)) == 1:
            self.townMapSelect.setCurrentText(sectors[0].townmap.capitalize())
        else:
            self.townMapSelect.setCurrentIndex(-1)
        if len(set(sector.townmaparrow for sector in sectors)) == 1:
            self.townMapArrowSelect.setCurrentText(sectors[0].townmaparrow.capitalize())
        else:
            self.townMapArrowSelect.setCurrentIndex(-1)
        if len(set(sector.townmapimage for sector in sectors)) == 1:
            self.townMapImageSelect.setCurrentText(sectors[0].townmapimage.capitalize())
        else:
            self.townMapImageSelect.setCurrentIndex(-1)
        if len(set(sector.townmapx for sector in sectors)) == 1:
            self.townMapPos.x.setValue(sectors[0].townmapx)
        else:
            self.townMapPos.x.clear()
        if len(set(sector.townmapy for sector in sectors)) == 1:
            self.townMapPos.y.setValue(sectors[0].townmapy)
        else:
            self.townMapPos.y.clear()
            
        
        self.dataTable.clearContents()
        self.dataTable.setRowCount(0)
        # can't hash this type
        if len(sectors) == 1:
            self.populateUserDataOne(sectors[0])
        else:
            self.populateUserDataMany()
            
        # unblock signals
        self.tilesetSelect.blockSignals(False)
        self.paletteGroupSelect.blockSignals(False)
        self.paletteSelect.blockSignals(False)
        self.itemSelect.blockSignals(False)
        self.musicSelect.blockSignals(False)
        self.propertySelect.blockSignals(False)
        self.teleportSelect.blockSignals(False)
        self.townMapSelect.blockSignals(False)
        self.townMapArrowSelect.blockSignals(False)
        self.townMapImageSelect.blockSignals(False)
        self.townMapPos.x.blockSignals(False)
        self.townMapPos.y.blockSignals(False)
        self.dataTable.blockSignals(False)
        
            
    def toSectors(self):
        self.mapeditor.scene.undoStack.beginMacro("Update sector attributes")
        
        for i in self.state.currentSectors:
            # only actually change the value if the input isn't blank
            # otherwise, use the sector's existing value
            
            action = ActionChangeSectorAttributes(i,
                int(self.tilesetSelect.currentText()) if self.tilesetSelect.currentText() != "" else i.tileset,
                int(self.paletteGroupSelect.currentText()) if self.paletteGroupSelect.currentText() != "" else i.palettegroup,
                int(self.paletteSelect.currentText()) if self.paletteSelect.currentText() != "" else i.palette,
                self.itemSelect.value() if not self.itemSelect.isBlank() else i.item,
                self.musicSelect.value() if not self.musicSelect.isBlank() else i.music,
                self.propertySelect.currentText().lower() if self.propertySelect.currentText() != "" else i.setting,
                self.teleportSelect.currentText().lower() if self.teleportSelect.currentText() != "" else i.teleport,
                self.townMapSelect.currentText().lower() if self.townMapSelect.currentText() != "" else i.townmap,
                self.townMapArrowSelect.currentText().lower() if self.townMapArrowSelect.currentText() != "" else i.townmaparrow,
                self.townMapImageSelect.currentText().lower() if self.townMapImageSelect.currentText() != "" else i.townmapimage,
                self.townMapPos.x.value() if not self.townMapPos.isBlankX() else i.townmapx,
                self.townMapPos.y.value() if not self.townMapPos.isBlankY() else i.townmapy)
            
            self.mapeditor.scene.undoStack.push(action)
            self.mapeditor.scene.refreshSector(i.coords)
            
            i.userdata = i.userdata | self.userDataToDict()
            
        self.mapeditor.scene.undoStack.endMacro()
    
    def getPaletteGroups(self):
        for i in self.projectData.tilesets[int(self.tilesetSelect.currentData(0))].paletteGroups:
            yield str(i.groupID)

    def getPalettes(self):
        for i in self.projectData.tilesets[int(self.tilesetSelect.currentData(0))].getPaletteGroup(
            int(self.paletteGroupSelect.currentData(0))).palettes:
                yield str(i.paletteID)

    def onTilesetSelect(self):
        self.tilesetSelect.blockSignals(True)
        self.paletteGroupSelect.clear()
        self.paletteGroupSelect.addItems(i for i in self.getPaletteGroups())
        self.onPaletteGroupSelect()
        
    def onPaletteGroupSelect(self):
        self.paletteGroupSelect.blockSignals(True)
        self.paletteSelect.blockSignals(True)
        self.paletteSelect.clear()
        self.paletteSelect.addItems(i for i in self.getPalettes())
        self.toSectors()
        
        self.tilesetSelect.blockSignals(False)
        self.paletteGroupSelect.blockSignals(False)
        self.paletteSelect.blockSignals(False)
        

    def exportBinary(self):
        dir, _ = QFileDialog.getSaveFileName(self, "Save sector userdata binary", self.projectData.dir, "Binary file (*.bin)")
        if dir:
            data = []
            for i in self.projectData.sectors.flat:
                i: Sector
                data.append(i.serialiseUserData())

            with open(dir, "wb") as file:
                file.write(bytes().join(data))
            
    
    def exportCCS(self):
        dir, _ = QFileDialog.getSaveFileName(self, "Save sector userdata struct layout", self.projectData.dir, "CCScript file (*.ccs)")
        if dir:
            with open(dir, "w") as file:
                file.write(Sector.serialiseStructLayoutToCCS())
        
    def importBinary(self):
        if ImportUserdataDialog.importUserdata(self, self.projectData):
            self.fromSectors()
        
    def addUserdata(self):
        if NewUserdataDialog.addNewUserdata(self):
            self.fromSectors()
    
    def removeUserdata(self):
        selected = self.dataTable.selectedItems()
        if len(selected) == 0: return
        
        for i in selected:
            key = self.dataTable.verticalHeaderItem(i.row()).text()
            self.dataTable.removeRow(i.row())
            
            Sector.SECTORS_USERDATA.pop(key)
            for s in self.projectData.sectors.flat:
                s: Sector
                s.userdata.pop(key, 0)
        
        self.fromSectors()
    
    def userDataToDict(self):
        data = {}
        for i in range(0, self.dataTable.rowCount()):
            item = self.dataTable.item(i, 0)
            if item.text() == "": continue # this is OR'd onto the dict later, so blank keys are ignored.
            data[self.dataTable.verticalHeaderItem(i).text()] = int(item.text())
        return data

    def populateUserDataOne(self, sector: Sector):
        for k, v in Sector.SECTORS_USERDATA.items():
            row = self.dataTable.rowCount()
            self.dataTable.insertRow(row)
            match v:
                case a if a is Int8:
                    delegate = SidebarSectorInt8Delegate
                case b if b is Int16:
                    delegate = SidebarSectorInt16Delegate
                case _:
                    raise ValueError(f"Unknown user data type {str(v)}")
            self.dataTable.setItem(row, 0, QTableWidgetItem(str(sector.userdata.get(k, 0))))
            self.dataTable.setItemDelegateForRow(row, delegate(self))
            header = QTableWidgetItem()
            header.setText(k)
            self.dataTable.setVerticalHeaderItem(row, header)
        
    def populateUserDataMany(self):
        for k, v in Sector.SECTORS_USERDATA.items():
            row = self.dataTable.rowCount()
            self.dataTable.insertRow(row)
            match v:
                case a if a is Int8:
                    delegate = SidebarSectorInt8Delegate
                case b if b is Int16:
                    delegate = SidebarSectorInt16Delegate
                case _:
                    raise ValueError(f"Unknown user data type {str(k)}")
            self.dataTable.setItem(row, 0, QTableWidgetItem(""))
            self.dataTable.setItemDelegateForRow(row, delegate(self))
            header = QTableWidgetItem()
            header.setText(k)
            self.dataTable.setVerticalHeaderItem(row, header)

    def setupUI(self):
        self.sectorLabel = QLabel("Sector 0 at (0, 0)")
        self.sectorLabel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        #####
        self.paletteData = QGroupBox("Palette Data", self)
        self.paletteDataLayout = QFormLayout(self.paletteData)

        self.tilesetSelect = QComboBox(self.paletteData)
        self.tilesetSelect.setToolTip("Tileset of this sector. Tileset = fts in /Tilesets.")

        self.paletteGroupSelect = QComboBox(self.paletteData)
        self.paletteGroupSelect.setToolTip("Palette group of this sector. Palette groups organise palettes.")

        self.paletteSelect = QComboBox(self.paletteData)
        self.paletteSelect.setToolTip("Palette of this sector. Palettes contain colour data for tiles.")

        self.paletteDataLayout.addRow("Tileset", self.tilesetSelect)
        self.paletteDataLayout.addRow("Palette Group", self.paletteGroupSelect)
        self.paletteDataLayout.addRow("Palette", self.paletteSelect)

        self.paletteData.setLayout(self.paletteDataLayout)
        
        self.tilesetSelect.addItems(str(i.id) for i in self.projectData.tilesets)
        self.tilesetSelect.activated.connect(self.onTilesetSelect)
        self.paletteGroupSelect.activated.connect(self.onPaletteGroupSelect)
        self.paletteSelect.currentIndexChanged.connect(self.toSectors)
        
        #####

        #####
        # https://github.com/pk-hack/CoilSnake/blob/10a335e539f9368a7018f435a9642282fc4f10f4/coilsnake/modules/eb/MapModule.py#L20
        self.miscData = QGroupBox("Misc Data", self)
        self.miscDataLayout = QFormLayout(self.miscData)

        self.itemSelect = BaseChangerSpinbox(self.miscData)
        self.itemSelect.setMaximum(common.BYTELIMIT)
        self.itemSelect.setToolTip("Items of type 58 can only be used in a sector with their ID here.")
        self.itemSelect.editingFinished.connect(self.toSectors)

        musicLayout = QHBoxLayout()
        self.musicSelect = BaseChangerSpinbox(self.miscData)
        self.musicSelect.setMaximum(common.BYTELIMIT)
        self.musicSelect.setToolTip("Music area table entry. This is not a song ID.")
        self.musicSelect.editingFinished.connect(self.toSectors)
        
        self.musicEdit = QPushButton("Edit")
        self.musicEdit.clicked.connect(lambda: MapMusicEditor.openMapMusicEditor(self, self.mapeditor.scene.undoStack,
                                                                                 self.projectData,
                                                                                 self.musicSelect.value()))
        
        musicLayout.addWidget(self.musicSelect)
        musicLayout.addWidget(self.musicEdit)

        self.propertySelect = QComboBox(self.miscData)
        self.propertySelect.addItems(["None", 
                                      "Indoors", 
                                      "Exit mouse usable", 
                                      "Lost underworld sprites", 
                                      "Magicant sprites", 
                                      "Robot sprites", 
                                      "Butterflies", # note: broken in-game
                                      "Indoors and butterflies"]) # same
        self.propertySelect.setToolTip("Extra properties of the sector. Butterflies and Indoors and butterflies do not work.")
        self.propertySelect.currentIndexChanged.connect(self.toSectors)
                                
        self.teleportSelect = QComboBox(self.miscData)
        self.teleportSelect.addItems(["Enabled",
                                      "Disabled"])
        self.teleportSelect.setToolTip("If the player can use PSI Teleport in this sector.")
        self.teleportSelect.currentIndexChanged.connect(self.toSectors)

        self.miscDataLayout.addRow("Item", self.itemSelect)
        self.miscDataLayout.addRow("Music", musicLayout)
        self.miscDataLayout.addRow("Properties", self.propertySelect)
        self.miscDataLayout.addRow("PSI Teleport", self.teleportSelect)

        self.miscData.setLayout(self.miscDataLayout)
        #####

        #####
        self.mapData = QGroupBox("Town Map Data", self)
        self.mapDataLayout = QFormLayout(self.mapData)

        self.townMapSelect = QComboBox(self.mapData)
        self.townMapSelect.addItems(["None", 
                                     "Onett", 
                                     "Twoson", 
                                     "Threed", 
                                     "Fourside", 
                                     "Scaraba", 
                                     "Summers",
                                     "None 2"])
        self.townMapSelect.setToolTip("Icon placement data to use. Not the image to use.")
        self.townMapSelect.currentIndexChanged.connect(self.toSectors)

        self.townMapArrowSelect = QComboBox(self.mapData)
        self.townMapArrowSelect.addItems(["None", 
                                          "Up", 
                                          "Down", 
                                          "Right", 
                                          "Left"])
        self.townMapArrowSelect.setToolTip("If Ness's icon should be replaced with an arrow here (to indicate being past the edge).")
        self.townMapArrowSelect.currentIndexChanged.connect(self.toSectors)

        self.townMapImageSelect = QComboBox(self.mapData)
        self.townMapImageSelect.addItems(["None", 
                                          "Onett", 
                                          "Twoson", 
                                          "Threed", 
                                          "Fourside", 
                                          "Scaraba", 
                                          "Summers"])
        self.townMapImageSelect.setToolTip("Image to use for the town map. Not the icon placement data.")
        self.townMapImageSelect.currentIndexChanged.connect(self.toSectors)

        self.townMapPos = CoordsInput()
        self.townMapPos.x.setMaximum(common.BYTELIMIT)
        self.townMapPos.y.setMaximum(common.BYTELIMIT)
        self.townMapPos.x.setToolTip("Position of the Ness icon on the town map when here.")
        self.townMapPos.y.setToolTip("Position of the Ness icon on the town map when here.")
        self.townMapPos.x.editingFinished.connect(self.toSectors)
        self.townMapPos.y.editingFinished.connect(self.toSectors)

        self.mapDataLayout.addRow("Properties of", self.townMapSelect)
        self.mapDataLayout.addRow("Image", self.townMapImageSelect)
        self.mapDataLayout.addRow("Arrow", self.townMapArrowSelect)
        self.mapDataLayout.addRow("Icon Position", self.townMapPos)

        self.mapData.setLayout(self.mapDataLayout)
        #####
        
        #####
        self.userData = QGroupBox("User Data", self)
        userDataLayout = QFormLayout(self.userData)
        
        controlButtonsLayout = QHBoxLayout()
        
        self.exportBinaryButton = QToolButton(icon=icons.ICON_EXPORT)
        self.exportBinaryButton.setToolTip("Export .bin file")
        self.exportBinaryButton.clicked.connect(self.exportBinary)
        
        self.exportCCSButton = QToolButton(icon=icons.ICON_TEXT_FILE)
        self.exportCCSButton.setToolTip("Export .ccs definitions file")
        self.exportCCSButton.clicked.connect(self.exportCCS)
        
        self.importBinaryButton = QToolButton(icon=icons.ICON_IMPORT)
        self.importBinaryButton.setToolTip("Import .bin file")
        self.importBinaryButton.clicked.connect(self.importBinary)
        
        controlButtonsLayout.addWidget(self.exportBinaryButton)
        controlButtonsLayout.addWidget(self.exportCCSButton)
        controlButtonsLayout.addWidget(self.importBinaryButton)
        
        fieldButtonsLayout = QHBoxLayout()
        
        self.addUserdataButton = QToolButton(icon=icons.ICON_NEW)
        self.addUserdataButton.setToolTip("Add user data field")
        self.addUserdataButton.clicked.connect(self.addUserdata)
        
        self.removeUserdataButton = QToolButton(icon=icons.ICON_DELETE)
        self.removeUserdataButton.setToolTip("Remove user data field")
        self.removeUserdataButton.clicked.connect(self.removeUserdata)
        
        fieldButtonsLayout.addWidget(self.addUserdataButton)
        fieldButtonsLayout.addWidget(self.removeUserdataButton)
        
        self.dataTable = QTableWidget(0, 1)
        self.dataTable.setHorizontalHeaderLabels(["Value"])
        self.dataTable.cellChanged.connect(self.toSectors)
        
        userDataLayout.addRow(controlButtonsLayout)
        userDataLayout.addRow(fieldButtonsLayout)
        userDataLayout.addRow(self.dataTable)
        
        self.userData.setLayout(userDataLayout)
        #####

        self.contentLayout = QVBoxLayout(self)
        self.contentLayout.addWidget(self.sectorLabel)
        self.contentLayout.addWidget(HSeparator())
        self.contentLayout.addWidget(self.paletteData)
        self.contentLayout.addWidget(self.miscData)
        self.contentLayout.addWidget(self.mapData)
        self.contentLayout.addWidget(HSeparator())
        self.contentLayout.addWidget(self.userData)

        self.setLayout(self.contentLayout)
        

# item delegate which allows only integers and limits the input to 2^8
class SidebarSectorInt8Delegate(QItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)
        
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        sizeLimit = 2**8
        
        editor.setValidator(QIntValidator(0, sizeLimit-1, editor))
        return editor

# item delegate which allows only integers and limits the input to 2^16
class SidebarSectorInt16Delegate(QItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)
        
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        sizeLimit = 2**16
        
        editor.setValidator(QIntValidator(0, sizeLimit-1, editor))
        return editor