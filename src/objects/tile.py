from PIL import ImageQt
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QPainterPath, QPixmap
from PySide6.QtWidgets import (QGraphicsItem, QGraphicsPixmapItem,
                               QGraphicsRectItem, QGraphicsSimpleTextItem)

import src.misc.common as common
from src.coilsnake.fts_interpreter import FullTileset
from src.misc.coords import EBCoords

WHITEBRUSH = QBrush(Qt.white)
BLACKBRUSH = QBrush(Qt.black)

class MapTile:
    """Instance of a tile on the map. Contains coords, palette palette group and tileset IDs, and a tile ID for a Tile object. Created alongside the map editor itself. Use its data to reference and render a MapTileGraphic"""
    def __init__(self, tile: int, coords: EBCoords, tileset: int, palettegroup: int, palette: int):
        self.tile = tile
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
        self.hasRenderedFg = False
        self.rendered: QPixmap = None
        self.renderedFg: QPixmap = None
    
    def render(self, tileset: FullTileset): 
        """Create the image of this tile graphic and save it to this instance. Also sets `hasRendered` to True"""
        palette = tileset.getPalette(self.palettegroup, self.palette)
        self.rendered = QPixmap.fromImage(ImageQt.ImageQt(tileset.tiles[self.tile].toImage(palette, tileset)))
        self.hasRendered = True
    
    def renderFg(self, tileset: FullTileset):
        """Create the foreground image of this tile graphic and save it to this instance. Also sets `hasRenderedFg` to True"""
        palette = tileset.getPalette(self.palettegroup, self.palette)
        self.renderedFg = QPixmap.fromImage(ImageQt.ImageQt(tileset.tiles[self.tile].toImage(palette, tileset, fgOnly=True)))
        self.hasRenderedFg = True