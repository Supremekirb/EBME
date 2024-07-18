from PIL import ImageQt
from PySide6.QtCore import QEvent, QObject, QPoint, Qt
from PySide6.QtGui import QBrush, QPixmap
from PySide6.QtWidgets import (QComboBox, QFormLayout, QGraphicsPixmapItem,
                               QGraphicsScene, QGraphicsView, QGridLayout,
                               QGroupBox, QPushButton, QWidget)

from src.actions.sector_actions import ActionChangeSectorAttributes
from src.objects.sector import Sector
from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords
from src.objects.tile import MapEditorTile


class SidebarTile(QWidget):
    """Sidebar for tile mode"""
    def __init__(self, parent, state, mapeditor, projectData: ProjectData):
        super().__init__(parent)
        self.state = state 
        self.mapeditor = mapeditor
        self.projectData = projectData

        self.setupUI()

        # initial render
        self.view.renderTileset(int(self.tilesetSelect.currentData(0)),
                                int(self.paletteGroupSelect.currentData(0)),
                                int(self.paletteSelect.currentData(0))
                                )


        
    def getPaletteGroups(self):
        for i in self.projectData.tilesets[int(self.tilesetSelect.currentData(0))].paletteGroups:
            yield str(i.groupID)

    def getPalettes(self):
        for i in self.projectData.tilesets[int(self.tilesetSelect.currentData(0))].getPaletteGroup(
            int(self.paletteGroupSelect.currentData(0))).palettes:
                yield str(i.paletteID)

    def onTilesetSelect(self, tileset: str = None):
        self.paletteGroupSelect.clear()
        self.paletteGroupSelect.addItems(i for i in self.getPaletteGroups())
        self.onPaletteGroupSelect()
    def onPaletteGroupSelect(self, palette: str = None):
        self.paletteSelect.clear()
        self.paletteSelect.addItems(i for i in self.getPalettes())
        self.onPaletteSelect()
    
    def onPaletteSelect(self, event=None):
        self.view.renderTileset(int(self.tilesetSelect.currentData(0)),
                                int(self.paletteGroupSelect.currentData(0)),
                                int(self.paletteSelect.currentData(0))
                                )

    def fromSector(self, sector: Sector):
        self.tilesetSelect.setCurrentText(str(sector.tileset))
        self.paletteGroupSelect.clear()
        self.paletteGroupSelect.addItems(i for i in self.getPaletteGroups())

        self.paletteGroupSelect.setCurrentText(str(sector.palettegroup))
        self.paletteSelect.clear()
        self.paletteSelect.addItems(i for i in self.getPalettes())

        self.paletteSelect.setCurrentText(str(sector.palette))
        self.onPaletteSelect()
    
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
        self.view.selectedIndicator.setPos((id%SidebarTileCanvas.tileWidth)*32, (id//SidebarTileCanvas.tileWidth)*32)
        self.view.centerOn(self.view.selectedIndicator)

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

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 32*SidebarTileCanvas.tileWidth, 32*960//SidebarTileCanvas.tileWidth)
        self.view = SidebarTileCanvas(self, self.state, self.projectData, self.scene)

        self.contentLayout = QGridLayout(self)
        self.contentLayout.addWidget(self.sectorSettingsBox, 0, 0)
        self.contentLayout.addWidget(self.view, 1, 0)

        # to be sure
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # minimum width accounting for scroll bar
        self.view.setFixedWidth((32*SidebarTileCanvas.tileWidth)+1+self.view.verticalScrollBar().sizeHint().width())
        self.view.centerOn(0, 0)

        self.setLayout(self.contentLayout)

        self.tilesetSelect.addItems(str(i.id) for i in self.projectData.tilesets)
        self.paletteGroupSelect.addItems(i for i in self.getPaletteGroups())
        self.paletteSelect.addItems(i for i in self.getPalettes())

        self.tilesetSelect.activated.connect(self.onTilesetSelect)
        self.paletteGroupSelect.activated.connect(self.onPaletteGroupSelect)
        self.paletteSelect.activated.connect(self.onPaletteSelect)


class SidebarTileCanvas(QGraphicsView):
    tileWidth = 6
    """How many tiles across the selector should be. Should be a factor of 960"""
    def __init__(self, parent, state, projectData: ProjectData, scene: QGraphicsScene):
        super().__init__(parent)
        self.state = state
        self.projectData = projectData
        self.setScene(scene)

        self.tiles = []

        x = 0
        y = 0
        for i in range(0, 960):
            item = MapEditorTile(EBCoords.fromTile(x, y))
            item.setText(str(i).zfill(3))

            self.scene().addItem(item)
            self.tiles.append(item)

            x += 1
            if x >= SidebarTileCanvas.tileWidth:
                x = 0
                y += 1

        self.selectedIndicator = QGraphicsPixmapItem()
        self.selectedIndicator.setPixmap(QPixmap(":/ui/selectTile.png"))
        self.selectedIndicator.setZValue(255)
        self.scene().addItem(self.selectedIndicator)

        # kinda weird to do it backwards like this but it makes more sense to have the width kept here...
        self.scene().setSceneRect(0, 0, (SidebarTileCanvas.tileWidth*32), (32*960)//SidebarTileCanvas.tileWidth)
        self.scene().installEventFilter(self) # me when i subclass the wrong thing probably

        self.setBackgroundBrush(
            QBrush(QPixmap(":/ui/bg.png")))
        self.setForegroundBrush(
            QBrush(QPixmap(":/grids/32grid0.png")))

    def eventFilter(self, object: QObject, event: QEvent):
        if event.type() == QEvent.Type(QEvent.GraphicsSceneMousePress):
            if event.buttons() == Qt.MouseButton.LeftButton:
                coords = EBCoords(event.scenePos().x(), event.scenePos().y())

                items = self.scene().items(QPoint(coords.x, coords.y))
                for i in items:
                    if isinstance(i, MapEditorTile):  
                        self.state.currentTile = i.getID()
                        self.selectedIndicator.setPos(coords.roundToTile()[0], coords.roundToTile()[1])
                        break     
                else:
                    raise ValueError("Something went wrong when selecting a tile")

        return False

    def renderTileset(self, tilesetID: int, paletteGroupID: int, paletteID: int):
        for i in self.tiles:
            graphic = self.projectData.getTileGraphic(tilesetID, paletteGroupID, paletteID, i.getID())
            if not graphic.hasRendered:
                graphic.render(self.projectData.tilesets[tilesetID])
            i.setPixmap(graphic.rendered)