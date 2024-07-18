from PIL import ImageQt
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QPainterPath, QPixmap
from PySide6.QtWidgets import (QGraphicsItem, QGraphicsPixmapItem,
                               QGraphicsRectItem, QGraphicsSimpleTextItem)

import src.misc.common as common
from src.misc.coords import EBCoords

WHITEBRUSH = QBrush(Qt.white)
BLACKBRUSH = QBrush(Qt.black)

class MapTile:
    """Instance of a tile on the map. Contains coords, palette palette group and tileset IDs, and a tile ID for a Tile object. Created alongside the map editor itself. Use its data to reference and render a MapTileGraphic"""
    def __init__(self, tile: str, coords: EBCoords, tileset: int, palettegroup: int, palette: int):
        self.tile = int(tile, 16)
        self.coords = coords
        self.palette = palette
        self.palettegroup = palettegroup
        self.tileset = tileset

        self.isPlaced = False

class MapTileGraphic:
    """Graphics for a map tile. Contains a rendered image. All args are IDs"""
    def __init__(self, tile, tileset, palettegroup, palette):
        self.tile = tile
        self.tileset = tileset
        self.palettegroup = palettegroup
        self.palette = palette

        self.hasRendered = False
        self.rendered: QPixmap = None
    
    def render(self, tileset) -> None: 
        """Create the image of this tile graphic and save it to this instance. Also sets `hasRendered` to True"""
        palette = tileset.getPalette(self.palettegroup, self.palette)
        self.rendered = QPixmap.fromImage(ImageQt.ImageQt(tileset.tiles[self.tile].toImage(palette, tileset)))
        self.hasRendered = True

class MapEditorTile(QGraphicsPixmapItem):
    instances = []
    tileIDsEnabled = False
    tileIDsShown = False
    
    def __init__(self, coords: EBCoords):
        QGraphicsPixmapItem.__init__(self)
        MapEditorTile.instances.append(self)
        
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)

        self.numBgRect = QGraphicsRectItem(0, 0, 32, 32, self)
        self.numShadow = QGraphicsSimpleTextItem(self)
        self.num = QGraphicsSimpleTextItem(self)

        self.numBgRect.setOpacity(0.5)
        self.numBgRect.setBrush(BLACKBRUSH)
        self.numBgRect.setPen(Qt.PenStyle.NoPen)
        self.num.setFont("EBMain") 
        self.numShadow.setFont("EBMain")
        self.num.setBrush(WHITEBRUSH)
        
        self.setPos(coords.x, coords.y)
        self.setZValue(common.MAPZVALUES.TILE)
        self.numBgRect.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.numShadow.setPos(8, 12)
        self.numShadow.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.num.setPos(7, 11)
        self.num.setFlag(QGraphicsItem.ItemIsSelectable, False)

        if (not MapEditorTile.tileIDsEnabled) or (not MapEditorTile.tileIDsShown):
            self.num.hide()
            self.numShadow.hide()
            self.numBgRect.hide()
    
    def setText(self, text: str):
        self.numShadow.setText(text)
        self.num.setText(text)

    def getID(self) -> int:
        return int(self.num.text())
    
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, 32, 32)
    
    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(0, 0, 32, 32)
        return path

    @classmethod
    def hideTileIDs(cls):
        for i in cls.instances:
            i.num.hide()
            i.numShadow.hide()
            i.numBgRect.hide()
        MapEditorTile.tileIDsEnabled = False

    @classmethod
    def showTileIDs(cls):
        if MapEditorTile.tileIDsShown:
            for i in cls.instances:
                i.num.show()
                i.numShadow.show()
                i.numBgRect.show()
        MapEditorTile.tileIDsEnabled = True

    @classmethod
    def hideTileIDsModeSwitch(cls):
        """Alternate version which checks for if IDs should actually be hidden or not.
        
        This is because we can't just hide the parent object like other map objects."""
        if MapEditorTile.tileIDsEnabled:
            for i in cls.instances:
                i.num.hide()
                i.numShadow.hide()
                i.numBgRect.hide()
        MapEditorTile.tileIDsShown = False

    @classmethod
    def showTileIDsModeSwitch(cls):
        """Alternate version which checks for if IDs should actually be shown or not.
        
        This is because we can't just hide the parent object like other map objects."""
        if MapEditorTile.tileIDsEnabled:
            for i in cls.instances:
                i.num.show()
                i.numShadow.show()
                i.numBgRect.show()
        MapEditorTile.tileIDsShown = True
