import json
import logging
import traceback

from PySide6.QtCore import QRect, QSettings, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (QComboBox, QDialog, QFormLayout, QGraphicsScene,
                               QGraphicsSceneMouseEvent, QGraphicsView,
                               QHBoxLayout, QLabel, QPushButton, QVBoxLayout)

from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords
from src.widgets.tile import TilesetDisplayGraphicsScene


class TileScratchSpace(QDialog):
    tiles = []
    def __init__(self, projectData: ProjectData, parent):
        super().__init__(parent)
        self.setWindowTitle("Tile Scratch Space")
        
        self.projectData = projectData
        
        labelLayout = QVBoxLayout()
        label = QLabel("\
You can place arrangements of tiles here for future reference, with no sector limitations. \
To select a placed tile in the map editor or tile editor, Shift+click it. \
Right-click to remove a tile. \
If a tile shows up as a warning symbol, it means that its tileset, palette group, or palette may have been removed, or doesn't exist in this project. \
")
        label.setWordWrap(True)
        labelLayout.addWidget(label)
        
        showHideHelp = QPushButton("Show/hide usage tip")
        showHideHelp.setCheckable(True)
        showHideHelp.toggled.connect(lambda x: label.setVisible(not x))
        labelLayout.addWidget(showHideHelp)
        
        layout = QHBoxLayout()
        
        sidebarLayout = QFormLayout()
        
        self.tilesetSelect = QComboBox()
        self.paletteGroupSelect = QComboBox()
        self.paletteSelect = QComboBox()
        self.tileScene = TilesetDisplayGraphicsScene(self.projectData, rowSize=5)
        self.tileScene.tileSelected.connect(self.onTileSelect)
        self.tileView = QGraphicsView(self.tileScene)
        self.tileView.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tileView.setFixedWidth((32*self.tileScene.rowSize)+1+self.tileView.verticalScrollBar().sizeHint().width())
        self.tileView.centerOn(0, 0)
        
        sidebarLayout.addRow("Tileset", self.tilesetSelect)
        self.tilesetSelect.currentIndexChanged.connect(self.onTilesetSelect)
        sidebarLayout.addRow("Palette Group", self.paletteGroupSelect)
        self.paletteGroupSelect.currentIndexChanged.connect(self.onPaletteGroupSelect)
        sidebarLayout.addRow("Palette", self.paletteSelect)
        self.paletteSelect.currentIndexChanged.connect(self.onPaletteSelect)
        sidebarLayout.addRow(self.tileView)
        
        self.scene = TileScratchScene(self.projectData)
        self.scene.tileSelected.connect(self.onTilePick)
        self.view = QGraphicsView(self.scene)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.view.setMaximumHeight((32*self.scene.SIZE)+1+self.view.horizontalScrollBar().sizeHint().height())
        self.view.setMaximumWidth((32*self.scene.SIZE)+1+self.view.verticalScrollBar().sizeHint().width()) # TODO seems to still be a little small?
        
        layout.addLayout(sidebarLayout)
        layout.addWidget(self.view)
        
        labelLayout.addLayout(layout)
        self.setLayout(labelLayout)  
        
        self.setGeometry(self.x(), self.y(), 600, 500)
        self.tilesetSelect.addItems(str(i.id) for i in self.projectData.tilesets)  
    
    def onTilesetSelect(self):
        self.paletteGroupSelect.blockSignals(True)
        self.paletteGroupSelect.clear()
        self.paletteGroupSelect.addItems(str(i.groupID) for i in self.projectData.getTileset(
            int(self.tilesetSelect.currentText())).paletteGroups)
        self.onPaletteGroupSelect()
        
        self.paletteGroupSelect.blockSignals(False)
        
    def onPaletteGroupSelect(self):
        self.paletteSelect.blockSignals(True)
        self.paletteSelect.clear()
        self.paletteSelect.addItems(str(i.paletteID) for i in self.projectData.getTileset(
            int(self.tilesetSelect.currentText())).getPaletteGroup(
                int(self.paletteGroupSelect.currentText())).palettes)
        self.onPaletteSelect()
        
        self.paletteSelect.blockSignals(False)
        
    def onPaletteSelect(self):
        self.scene.currentTileset = self.tileScene.currentTileset = int(self.tilesetSelect.currentText())
        self.scene.currentPaletteGroup = self.tileScene.currentPaletteGroup = int(self.paletteGroupSelect.currentText())
        self.scene.currentPalette = self.tileScene.currentPalette = int(self.paletteSelect.currentText())
        self.tileScene.update()
        
    def onTileSelect(self, tile: int): # on sidebar
        self.scene.currentTile = tile
        
    def onTilePick(self, tile: int, tileset: int, palettegroup: int, palette: int): # on scene
        self.tileScene.moveCursorToTile(tile)
        self.tileView.centerOn(self.tileScene.selectionIndicator)
        self.scene.currentTile = tile
        self.tilesetSelect.setCurrentText(str(tileset)) # also sets scene currents
        self.paletteGroupSelect.setCurrentText(str(palettegroup))
        self.paletteSelect.setCurrentText(str(palette))

class TileScratchScene(QGraphicsScene):
    SIZE = 20
    tileSelected = Signal(int, int, int, int) # tile, tileset, palette group, palette    
    def __init__(self, projectData: ProjectData):
        super().__init__(0, 0, self.SIZE*32, self.SIZE*32)
        
        self.projectData = projectData
        
        self.tileMatrix: list[list[list[int]|None]] = [[None for _ in range(0, self.SIZE)] for _ in range(0, self.SIZE)]
        """access with x and y, gets you tile, tileset, palette group, palette or none"""
        
        value = QSettings().value("scratch/tile")
        if value:
            self.tileMatrix = json.loads(value)
        
        self.setBackgroundBrush(QPixmap(":/ui/bg.png"))
        self.setForegroundBrush(QPixmap(":/grids/32grid0.png"))
        
        self.currentTile = 0
        self.currentTileset = 0
        self.currentPaletteGroup = 0
        self.currentPalette = 0
        
    def saveMatrix(self):
        QSettings().setValue("scratch/tile", json.dumps(self.tileMatrix))

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        super().mousePressEvent(event)
        coords = EBCoords(*event.scenePos().toTuple())
        if coords.x < 0 or coords.y < 0:
            return
        if coords.x >= self.SIZE*32 or coords.y >= self.SIZE*32:
            return
        
        x, y = coords.coordsTile()
        
        if event.button() == Qt.MouseButton.LeftButton: 
            if Qt.KeyboardModifier.ControlModifier in event.modifiers() or Qt.KeyboardModifier.ShiftModifier in event.modifiers():
                tile = self.tileMatrix[x][y]
                if not tile:
                    return
                else:
                    self.tileSelected.emit(*tile)
            else:
                self.tileMatrix[x][y] = [self.currentTile,
                                        self.currentTileset,
                                        self.currentPaletteGroup,
                                        self.currentPalette]
                self.update()
                
        elif event.button() == Qt.MouseButton.RightButton:
            self.tileMatrix[x][y] = None
            self.update()
        
        self.saveMatrix()
    
    def drawBackground(self, painter: QPainter, rect: QRect):
        super().drawBackground(painter, rect)
        start = EBCoords(*rect.topLeft().toTuple())
        end = EBCoords(*rect.bottomRight().toTuple())
        x0, y0 = start.coordsTile()
        x1, y1 = end.coordsTile()
              
        for y in range(y0, y1+1):
            for x in range(x0, x1+1):
                try:
                    if x >= self.SIZE or y >= self.SIZE:
                        continue
                    
                    tile = self.tileMatrix[x][y]
                    if not tile:
                        continue
                    
                    tileID, tileset, palettegroup, palette = tile
                    
                    tileGfx = self.projectData.getTileGraphic(tileset,
                                                              palettegroup,
                                                              palette,
                                                              tileID)
                    if not tileGfx.hasRendered:
                        tileGfx.render(self.projectData.getTileset(tileset))
                        tileGfx.hasRendered = True
                            
                    painter.drawPixmap(x*32, y*32, tileGfx.rendered)
                        
                except Exception:
                    painter.drawPixmap(x*32, y*32, QPixmap(":ui/errorTile.png"))
                    # logging.warning(traceback.format_exc())
                    # we dont need to log this because it's expected behaviour
                    
        if QSettings().value("mapeditor/ShowTileIDs", False, bool):
            painter.setFont("EBMain")
            font = painter.font()
            font.setPointSize(12)
            painter.setFont(font)
            painter.setBrush(QColor(0, 0, 0, 128))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(rect)
            
            for y in range(y0, y1+1):
                for x in range(x0, x1+1):
                    try:
                        if x >= self.SIZE or y >= self.SIZE:
                            continue
                        
                        tile = self.tileMatrix[x][y]
                        if not tile:
                            continue
                        
                        tileID = tile[0]
                        painter.setPen(Qt.GlobalColor.black)
                        painter.drawText((x*32)+8, (y*32)+23, str(tileID).zfill(3))
                        painter.setPen(Qt.GlobalColor.white)
                        painter.drawText((x*32)+7, (y*32)+22, str(tileID).zfill(3))
                    except Exception:
                        logging.warning(traceback.format_exc())
