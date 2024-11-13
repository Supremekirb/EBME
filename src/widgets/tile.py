import json
import logging
import traceback
from copy import copy

from PIL import ImageQt
from PySide6.QtCore import QPoint, QRect, QRectF, QSettings, QSize, Qt, Signal
from PySide6.QtGui import (QBrush, QColor, QMouseEvent, QPainter, QPaintEvent,
                           QPixmap, QResizeEvent)
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGraphicsScene,
                               QGraphicsSceneMouseEvent, QSizePolicy, QWidget)

import src.misc.common as common
from src.coilsnake.fts_interpreter import (FullTileset, Minitile, Palette,
                                           Subpalette, Tile)
from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords


class MinitileGraphicsWidget(QWidget):    
    def __init__(self):
        super().__init__()
        
        self.currentMinitile: Minitile = None
        self.currentSubpalette: Subpalette = None
        self.isForeground = True
        
        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        policy.setHeightForWidth(True)
        policy.setWidthForHeight(True)
        self.setSizePolicy(policy)
        
        self._scratchBitmap: list[str] = []
        
    def loadMinitile(self, minitile: Minitile, id: int=0):
        self.currentMinitile = minitile
        self.copyToScratch()

    def copyToScratch(self):
        """For better undo/redo support, we copy the bitmap to this scratch space to modify it.
        
        Then undo/redo actions apply it to the model.
        
        Keeping it in the base class so we don't have to rewrite painting in the editing subclass"""
        if self.isForeground:
            self._scratchBitmap = copy(self.currentMinitile.foreground)
        else:
            self._scratchBitmap = copy(self.currentMinitile.background)
        
    def indexAtPos(self, pos: QPoint) -> int|None:
        """Get the index (0-63) of the pixel at the given position

        Args:
            pos (QPoint): Location on the widget, such as from an event

        Returns:
            int|None: index, None if out of bounds
        """
        w = self.width()
        h = self.height()
        
        if w > h:       
            w = h
        else:
            h = w
            
        x = pos.x() // (w / 8)
        y = pos.y() // (h / 8)
        
        if x < 0 or x > 7 or y < 0 or y > 7:
            return
        
        return int(y * 8 + x)
        
        
    def paintEvent(self, event: QPaintEvent):
        if self.currentMinitile == None or self.currentSubpalette == None:
            return super().paintEvent(event)
        
        width = self.width()
        height = self.height()
        
        if width > height:
            width = height
        else:
            height = width
        
        painter = QPainter(self)
           
        scale = width / 8
              
        painter.scale(scale, scale)
        
        # draw bg at half the size of the minitile pixel 
        painter.scale(0.5, 0.5)
        painter.setBrush(QBrush(QPixmap(":/ui/bg.png").scaled(2, 2)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, 16, 16)
        painter.scale(2, 2)
        
        for i in range(64):
            x = i % 8
            y = i // 8
            colour = self.currentSubpalette.subpaletteRGBA[self._scratchBitmap[i]]
            if not self.isForeground and colour[-1] == 0:
                colour = list(colour)
                colour[-1] = 255
            painter.fillRect(x, y, 1, 1, QColor.fromRgb(*colour))
            
        return super().paintEvent(event)
    
    def heightForWidth(self, width: int) -> int:
        return width
    
    def hasHeightForWidth(self):
        return True
    
    def minimumSizeHint(self):
        return QSize(128, 128)

    def resizeEvent(self, event: QResizeEvent):
        self.setMinimumWidth(event.size().height())       
        return super().resizeEvent(event)
    
class TileGraphicsWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        self.currentTile: Tile = None
        self.currentPalette: Palette = None
        self.currentTileset: FullTileset = None
        
        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        policy.setHeightForWidth(True)
        policy.setWidthForHeight(True)
        self.setSizePolicy(policy)
    
    def loadTile(self, tile: Tile):
        self.currentTile = tile
        self.update()
    
    def loadPalette(self, palette: Palette):
        self.currentPalette = palette
        self.update()
    
    def loadTileset(self, tileset: FullTileset):
        self.currentTileset = tileset
        self.update()
    
    def indexAtPos(self, pos: QPoint) -> int|None:
        """Get the index (0-15) of the minitile at the given positon

        Args:
            pos (QPoint): Location on the widget, such as from an event
        
        Returns:
            int|None: index, None if out of bounds
        """
        w = self.width()
        h = self.height()
        
        if w > h:
            w = h
        else:
            h = w
        
        x = pos.x() // (w / 4)
        y = pos.y() // (h / 4)
        
        if x < 0 or x > 3 or y < 0 or y > 3:
            return
        
        return int(y * 4 + x)
    
    def paintEvent(self, event: QPaintEvent):
        if self.currentTile == None or self.currentPalette == None:
            return super().paintEvent(event)

        width = self.width()
        height = self.height()
        
        if width > height:
            width = height
        else:
            height = width
        
        painter = QPainter(self)
        
        scale = width / 32
        
        painter.scale(scale, scale)
        
        painter.scale(0.5, 0.5)
        painter.setBrush(QBrush(QPixmap(":/ui/bg.png").scaled(2, 2)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, 64, 64)
        painter.scale(2, 2)
        
        painter.drawImage(0, 0, ImageQt.ImageQt(self.currentTile.toImage(self.currentPalette, self.currentTileset)))
        
        if QSettings().value("mapeditor/ShowGrid", type=bool):
            painter.scale(0.25, 0.25)
            painter.setBrush(QPixmap(":/grids/32grid0.png"))
            painter.drawRect(0, 0, 128, 128)
            painter.scale(4, 4)

        return super().paintEvent(event)

    def heightForWidth(self, width: int) -> int:
        return width

    def hasHeightForWidth(self):
        return True

    def minimumSizeHint(self):
        return QSize(128, 128)
    
    def resizeEvent(self, event: QResizeEvent):
        self.setMinimumWidth(event.size().height())       
        return super().resizeEvent(event)
    
class TileCollisionWidget(TileGraphicsWidget):
    collisionPlaced = Signal(int)
    collisionPicked = Signal(int)
    
    def __init__(self, readOnly: bool=True):
        super().__init__()
        self.readOnly = readOnly
        
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if Qt.KeyboardModifier.ShiftModifier in event.modifiers() or Qt.KeyboardModifier.ControlModifier in event.modifiers():
                self.pickCollision(event.pos())
            else:
                self.placeCollision(event.pos())
        
    def placeCollision(self, pos: QPoint):
        index = self.indexAtPos(pos)
        if index == None:
            return
        self.collisionPlaced.emit(index)
        
    def pickCollision(self, pos: QPoint):
        index = self.indexAtPos(pos)
        if index == None:
            return
        value = self.currentTile.getMinitileCollision(index)
        
        self.collisionPicked.emit(value)

    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        
        if self.currentTile == None or self.currentPalette == None:
            return
        presets = QSettings().value("presets/presets", defaultValue=common.DEFAULTCOLLISIONPRESETS)
        presetColours: dict[int, int] = {}
        for _, value, colour in json.loads(presets):
            presetColours[value] = colour
        
        width = self.width()
        height = self.height()
        
        if width > height:
            width = height
        else:
            height = width
        
        painter = QPainter(self)
        
        scale = width / 32
        
        painter.scale(scale, scale)
        painter.setPen(Qt.PenStyle.NoPen)
        
        for i in range(16):
            collision = self.currentTile.getMinitileCollision(i)
            if collision == 0:
                colour = 0x000000
                painter.setOpacity(0)
            else:
                painter.setOpacity(0.7)
                try:
                    colour = presetColours[collision]
                except KeyError:
                    colour = 0x303030
            
            painter.setBrush(QColor(colour))
            painter.drawRect((i % 4)*8, (i // 4)*8, 8, 8)
    
        if QSettings().value("mapeditor/ShowGrid", type=bool):
            painter.setOpacity(1)
            painter.scale(0.25, 0.25)
            painter.setBrush(QPixmap(":/grids/32grid0.png"))
            painter.drawRect(0, 0, 128, 128)
            painter.scale(4, 4)
    
class TilesetDisplayGraphicsScene(QGraphicsScene):
    tileSelected = Signal(int)
        
    def __init__(self, projectData: ProjectData, horizontal: bool = False, rowSize: int = 6, forcedPalette: Palette|None=None):
        super().__init__()
        
        self.projectData = projectData
        self.horizontal = horizontal
        self.rowSize = rowSize
        self.forcedPalette = forcedPalette
        self.forcedPaletteCache: dict[int, QPixmap] = {}
        
        self.selectionIndicator = QGraphicsPixmapItem(QPixmap(":/ui/selectTile.png"))
        
        if not horizontal:
            self.setSceneRect(0, 0, self.rowSize*32, (common.MAXTILES*32)//self.rowSize)
        else:
            self.setSceneRect(0, 0, (common.MAXTILES*32)//self.rowSize, self.rowSize*32)
            
        self.addItem(self.selectionIndicator)
        self.setForegroundBrush((QBrush(QPixmap(":/grids/32grid0.png"))))
        self.setBackgroundBrush((QBrush(QPixmap(":/ui/bg.png"))))
        
        self.currentTileset = 0
        self.currentPaletteGroup = 0
        self.currentPalette = 0
    
    def cursorOverTile(self):
        return self.posToTileIndex(*self.selectionIndicator.pos().toTuple())
    
    def moveCursorToTile(self, tile: int):
        x, y = self.tileIndexToPos(tile)
        self.selectionIndicator.setPos(x*32, y*32)
        
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        pos = EBCoords(*event.scenePos().toTuple())
        self.tileSelected.emit(self.posToTileIndex(*pos.coordsTile()))
        self.selectionIndicator.setPos(*pos.roundToTile())
        
        super().mousePressEvent(event)
    
    def drawBackground(self, painter: QPainter, rect: QRectF | QRect):
        super().drawBackground(painter, rect)
        start = EBCoords(*rect.topLeft().toTuple())
        end = EBCoords(*rect.bottomRight().toTuple())
        x0, y0 = start.coordsTile()
        x1, y1 = end.coordsTile()
        
        tileset = self.projectData.getTileset(self.currentTileset)        
        for y in range(y0, y1+1):
            for x in range(x0, x1+1):
                try:
                    tileID = self.posToTileIndex(x, y)
                    if tileID >= common.MAXTILES or tileID < 0:
                        continue
                    
                    if not self.forcedPalette:
                        tileGfx = self.projectData.getTileGraphic(self.currentTileset,
                                                                self.currentPaletteGroup,
                                                                self.currentPalette,
                                                                tileID)
                        if not tileGfx.hasRendered:
                            tileGfx.render(tileset)
                            tileGfx.hasRendered = True
                            
                        painter.drawPixmap(x*32, y*32, tileGfx.rendered)
                        
                    else:
                        try:
                            pixmap = self.forcedPaletteCache[tileID]
                        except KeyError:
                            tileset = self.projectData.getTileset(self.currentTileset)
                            tile = tileset.tiles[tileID]
                            self.forcedPaletteCache[tileID] = QPixmap.fromImage(ImageQt.ImageQt(
                                tile.toImage(self.forcedPalette, tileset)
                            ))
                            pixmap = self.forcedPaletteCache[tileID]
                        
                        painter.drawPixmap(x*32, y*32, pixmap)
                except Exception:
                    painter.drawPixmap(x*32, y*32, QPixmap(":ui/errorTile.png"))
                    logging.warning(traceback.format_exc())
                    
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
                        tileID = self.posToTileIndex(x, y)
                        painter.setPen(Qt.GlobalColor.black)
                        painter.drawText((x*32)+8, (y*32)+23, str(tileID).zfill(3))
                        painter.setPen(Qt.GlobalColor.white)
                        painter.drawText((x*32)+7, (y*32)+22, str(tileID).zfill(3))
                    except Exception:
                        logging.warning(traceback.format_exc())
    
    def posToTileIndex(self, x: int, y: int):
        if self.horizontal:
            return int(x * self.rowSize + y)
        else:
            return int(y * self.rowSize + x)
        
    def tileIndexToPos(self, tile: int):
        if self.horizontal:
            return tile // self.rowSize, tile % self.rowSize
        else:
            return tile % self.rowSize, tile // self.rowSize
