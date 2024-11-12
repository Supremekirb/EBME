from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QFormLayout, QGraphicsView,
                               QGridLayout, QGroupBox, QPushButton, QWidget)

from src.actions.sector_actions import ActionChangeSectorAttributes
from src.coilsnake.project_data import ProjectData
from src.objects.sector import Sector
from src.widgets.tile import TilesetDisplayGraphicsScene

if TYPE_CHECKING:
    from src.mapeditor.map_editor import MapEditor, MapEditorState


class SidebarTile(QWidget):
    """Sidebar for tile mode"""
    def __init__(self, parent, state: "MapEditorState", mapeditor: "MapEditor", projectData: ProjectData):
        super().__init__(parent)
        self.state = state 
        self.mapeditor = mapeditor
        self.projectData = projectData

        self.setupUI()
        
    def getPaletteGroups(self):
        for i in self.projectData.tilesets[int(self.tilesetSelect.currentText())].paletteGroups:
            yield str(i.groupID)

    def getPalettes(self):
        for i in self.projectData.tilesets[int(self.tilesetSelect.currentText())].getPaletteGroup(
            int(self.paletteGroupSelect.currentText())).palettes:
                yield str(i.paletteID)

    def onTilesetSelect(self):
        value = int(self.tilesetSelect.currentText())
        
        self.paletteGroupSelect.blockSignals(True)
        self.paletteGroupSelect.clear()
        self.paletteGroupSelect.addItems(i for i in self.getPaletteGroups())
        
        self.scene.currentTileset = value
        self.onPaletteGroupSelect()
        self.paletteGroupSelect.blockSignals(False)
        
    def onPaletteGroupSelect(self):
        value = int(self.paletteGroupSelect.currentText())
        
        self.paletteSelect.blockSignals(True)
        self.paletteSelect.clear()
        self.paletteSelect.addItems(i for i in self.getPalettes())
        
        self.scene.currentPaletteGroup = value
        self.onPaletteSelect()
        self.paletteSelect.blockSignals(False)
    
    def onPaletteSelect(self):
        value = int(self.paletteSelect.currentText())
        
        self.scene.currentPalette = value
        self.scene.update()
    
    def onTileSelect(self, tile: int):
        self.state.currentTile = tile

    def fromSector(self, sector: Sector):
        self.tilesetSelect.setCurrentText(str(sector.tileset))
        self.paletteGroupSelect.setCurrentText(str(sector.palettegroup))
        self.paletteSelect.setCurrentText(str(sector.palette))
    
    def toSector(self):
        sectors = self.state.currentSectors
        self.mapeditor.scene.undoStack.beginMacro("Update sector graphics")
        for i in sectors:
            tileset = int(self.tilesetSelect.currentData(0))
            palettegroup = int(self.paletteGroupSelect.currentData(0))
            palette = int(self.paletteSelect.currentData(0))  
            action = ActionChangeSectorAttributes(i, tileset, palettegroup, palette,
                                                  i.item, i.music, i.setting, i.teleport,
                                                  i.townmap, i.townmaparrow, i.townmapimage,
                                                  i.townmapx, i.townmapy)
            self.mapeditor.scene.undoStack.push(action)
            self.mapeditor.scene.refreshSector(i.coords)
        self.mapeditor.scene.undoStack.endMacro()

    def selectTile(self, id: int):
        self.scene.moveCursorToTile(id)
        self.view.centerOn(self.scene.selectionIndicator)

    def setupUI(self):
        #####
        self.sectorSettingsBox = QGroupBox("Tile Data", self)
        self.sectorSettingsLayout = QFormLayout(self.sectorSettingsBox)
        
        self.tilesetSelect = QComboBox(self.sectorSettingsBox)
        self.tilesetSelect.setToolTip("Tileset = fts in /Tilesets.")

        self.paletteGroupSelect = QComboBox(self.sectorSettingsBox)
        self.paletteGroupSelect.setToolTip("Palette groups organise palettes.")

        self.paletteSelect = QComboBox(self.sectorSettingsBox)
        self.paletteSelect.setToolTip("Palettes contain colour data for tiles.")

        self.saveSectorButton = QPushButton("Quick Save\nto Sector", self.sectorSettingsBox)
        self.saveSectorButton.clicked.connect(self.toSector)
        self.saveSectorButton.setToolTip("Save the tileset and palette data to the selected sector.")

        self.sectorSettingsLayout.addRow("Tileset", self.tilesetSelect)
        self.sectorSettingsLayout.addRow("Palette Group", self.paletteGroupSelect)
        self.sectorSettingsLayout.addRow("Palette", self.paletteSelect)
        self.sectorSettingsLayout.addRow(self.saveSectorButton)

        self.sectorSettingsBox.setLayout(self.sectorSettingsLayout)
        #####

        self.scene = TilesetDisplayGraphicsScene(self.projectData)
        self.scene.tileSelected.connect(self.onTileSelect)
        self.view = QGraphicsView()
        self.view.setScene(self.scene)
        # to be sure
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # minimum width accounting for scroll bar
        self.view.setFixedWidth((32*self.scene.rowSize)+1+self.view.verticalScrollBar().sizeHint().width())
        self.view.centerOn(0, 0)

        self.contentLayout = QGridLayout(self)
        self.contentLayout.addWidget(self.sectorSettingsBox, 0, 0)
        self.contentLayout.addWidget(self.view, 1, 0)

        self.setLayout(self.contentLayout)

        self.tilesetSelect.addItems(str(i.id) for i in self.projectData.tilesets)
        self.paletteGroupSelect.addItems(i for i in self.getPaletteGroups())
        self.paletteSelect.addItems(i for i in self.getPalettes())

        self.tilesetSelect.currentIndexChanged.connect(self.onTilesetSelect)
        self.paletteGroupSelect.currentIndexChanged.connect(self.onPaletteGroupSelect)
        self.paletteSelect.currentIndexChanged.connect(self.onPaletteSelect)