import json
import math
import uuid
from typing import TYPE_CHECKING

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import (QBitmap, QBrush, QColor, QImage, QKeySequence,
                           QPainter, QPainterPath, QPen, QPixmap, QRegion)
from PySide6.QtWidgets import (QGraphicsItem, QGraphicsPixmapItem,
                               QGraphicsRectItem,
                               QGraphicsSceneContextMenuEvent,
                               QGraphicsSceneMouseEvent,
                               QGraphicsSimpleTextItem, QMenu, QStyle)

import src.misc.common as common
import src.misc.icons as icons
from src.actions.npc_actions import ActionMoveNPCInstance
from src.misc.coords import EBCoords
from src.objects.tile import MapTile

if TYPE_CHECKING:
    from src.mapeditor.map.map_scene import MapEditorScene
    

WHITEBRUSH = QBrush(Qt.GlobalColor.white)
BLACKBRUSH = QBrush(Qt.GlobalColor.black)
REDPEN = QPen(Qt.GlobalColor.red)
CYANPEN = QPen(Qt.GlobalColor.cyan)
YELLOWPEN = QPen(Qt.GlobalColor.yellow)
BLUEPEN = QPen(Qt.GlobalColor.blue)

class NPC:
    """NPC table entry"""
    def __init__(self, id: int, direction: str, flag: int, movement: int,
                 show: str, sprite: int, text1: str, text2: str, type: str,
                 comment: str = None):
        self.id = id

        self.direction = direction
        self.flag = flag
        self.movement = movement
        self.show = show
        self.sprite = sprite
        self.text1 = text1
        self.text2 = text2
        self.type = type
        self.comment = comment

        self.rendered = False
        
    def render(self, sprite) -> None:
        self.img = sprite.renderFacingImg(common.DIRECTION8[self.direction].value)
        self.rendered = True
        

class NPCInstance:
    """NPC map object (or, map_sprites.yml entry)\n
    Although never utilised by the vanilla game, there may be multiple instances of a single NPC."""
    def __init__(self, nid: int, coords: EBCoords):
        self.uuid = uuid.uuid4()
        self.npcID = nid
        self.placed = False
        self.coords = coords

    def posToMapSpritesFormat(self) -> tuple[int, int, int, int]:
        """Convert NPC pixel position to bisector and offset.

        Returns:
            Tuple: Bisector X, Bisector Y, Offset X, Offset Y
        """
        bsX = self.coords.coordsBisector()[0]
        bsY = self.coords.coordsBisector()[1]
        oX = int(self.coords.x - (bsX*256))
        oY = int(self.coords.y - (bsY*256))

        return bsX, bsY, oX, oY

    # im not extending this to saving, because I want
    # to keep the conversion of object data in
    # the save/load functions entirely, so that
    # maybe we don't always have to use coilsnake
    def toDataDict(self) -> dict[str, int | tuple[int, int]]:
        """Get a dict containing relevant data for copying and pasting.

        Returns:
            dict: Dict containing NPC ID (as an int) and coordinates (as a tuple) at keys [id] and [coords]
        """
        return {'id': self.npcID, 'coords': self.coords.coords()}
    
class MapEditorNPC(QGraphicsPixmapItem):
    instances = []
    
    NPCIDsEnabled = False
    visualBoundsEnabled = False
    collisionBoundsEnabled = False 
    
    def __init__(self, coords: EBCoords, id: int, uuid: uuid.UUID):
        QGraphicsPixmapItem.__init__(self)
        MapEditorNPC.instances.append(self)
        coords.restrictToMap()

        self.id = id
        self.uuid = uuid

        self.numBgRect = QGraphicsRectItem(self)
        self.numShadow = QGraphicsSimpleTextItem(self)
        self.num = QGraphicsSimpleTextItem(self)
        self.visualBounds = QGraphicsRectItem(self)
        self.collisionBounds = QGraphicsRectItem(self)
            
        self.numBgRect.setOpacity(0.5)
        self.numBgRect.setBrush(BLACKBRUSH)
        self.numBgRect.setPen(Qt.PenStyle.NoPen)
        self.num.setFont("EBMain")
        self.numShadow.setFont("EBMain")
        self.num.setBrush(WHITEBRUSH)
        self.visualBounds.setPen(REDPEN)
        self.collisionBounds.setPen(CYANPEN)

        self.setPos(coords.x, coords.y)
        self.setZValue(common.MAPZVALUES.NPC)
        self.numBgRect.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.numShadow.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.num.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.visualBounds.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.collisionBounds.setFlag(QGraphicsItem.ItemIsSelectable, False)

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        
        self.isDummy = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)


        if not MapEditorNPC.NPCIDsEnabled:
            self.num.hide()
            self.numShadow.hide()
            self.numBgRect.hide()
        
        if not MapEditorNPC.visualBoundsEnabled:
            self.visualBounds.hide()
        
        if not MapEditorNPC.collisionBoundsEnabled:
            self.collisionBounds.hide()

    def setText(self, text: str):
        self.numShadow.setText(text)
        self.num.setText(text)

    # reimplementing function to allow ALL of visible NPC area to be selected.
    # otherwise only the opaque pixels will be detected, which is an issue for
    # small or invisible sprites
    def shape(self):
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path
    
    # reimplementing function to properly offset and reposition image,
    # ID display, and visual bounds properly.
    # The cool thing about this is that we can use coordinates directly
    # from map_sprites.yml and we don't have to worry about converting
    # them from top-left to bottom-centre-plus-eight.
    def setPixmap(self, pixmap: QPixmap | QImage | str) -> None:
        offsetX = pixmap.width()//2
        offsetY = pixmap.height()-8 
 
        self.setOffset(offsetX*-1, offsetY*-1)
        self.numBgRect.setRect(0-offsetX, -13-offsetY, 27, 13)
        self.numShadow.setPos(2-offsetX, -11-offsetY)
        self.num.setPos(1-offsetX, -12-offsetY)
        self.visualBounds.setRect(0-offsetX, 
                                  0-offsetY,
                                  pixmap.width(), 
                                  pixmap.height())

        return super().setPixmap(pixmap)
    
    def setCollisionBounds(self, w: int, h: int) -> None:
        pixmap = self.pixmap()
        offsetY = 0
        # for each of the following sprite sizes, add the following offset
        # provided by jtolmar
        # EntitySize._8x16:  2
        # EntitySize._16x16: -8
        # EntitySize._24x16: 2
        # EntitySize._32x16: 2
        # EntitySize._48x16: 2
        # EntitySize._16x24: 0
        # EntitySize._24x24: 0
        # EntitySize._16x32: 0
        # EntitySize._32x24: -8
        # EntitySize._48x32: -8
        # EntitySize._24x48: -32
        # EntitySize._16x48: 0
        # EntitySize._32x48: -8
        # EntitySize._48x48: -8
        # EntitySize._64x48: -8
        # EntitySize._64x64: -56
        # EntitySize._64x80: -7
        match pixmap.size().toTuple():
            case (8, 16):
                offsetY += 2
            case (16, 16):
                offsetY += -8
            case (24, 16):
                offsetY += 2
            case (32, 16):
                offsetY += 2
            case (48, 16):
                offsetY += 2
            case (32, 24):
                offsetY += -8
            case (48, 32):
                offsetY += -8
            case (24, 48):
                offsetY += -32
            case (32, 48):
                offsetY += -8
            case (48, 48):
                offsetY += -8
            case (64, 48):
                offsetY += -8
            case (64, 64):
                offsetY += -56
            case (64, 80):
                offsetY += -7

        self.collisionBounds.setRect(-w, -h, w*2, h*2)
        self.collisionBounds.setY(offsetY)
        
    def sampleCollision(self) -> int:
        colliderTopLeft = self.mapToScene(self.collisionBounds.rect().topLeft())
        colliderBottomRight = self.mapToScene(self.collisionBounds.rect().bottomRight())
        return self.scene().sampleCollisionRegion(EBCoords(colliderTopLeft.x(), colliderTopLeft.y()+self.collisionBounds.y()),
                                                  EBCoords(colliderBottomRight.x()-1, colliderBottomRight.y()+self.collisionBounds.y()-1))
    
    # reimplementing function to highlight the border as that obscures the vanilla Qt selection border
    def paint(self, painter: QPainter, option, a):        
        if QStyle.StateFlag.State_Selected in option.state:
            self.visualBounds.setPen(YELLOWPEN)
            self.collisionBounds.setPen(BLUEPEN)
        else:
            self.visualBounds.setPen(REDPEN)
            self.collisionBounds.setPen(CYANPEN)
            
        super().paint(painter, option, a)
        
        if QSettings().value("mapeditor/MaskNPCsWithForeground", type=bool, defaultValue=True):
        # get the mask based on tiles we intersect with
        # what we actually do is just kinda paint on top. a real mask would be nice...
        # BUG masks can overlap with other NPCs, looks weird
        # QRegion mask?
        
            topLeft = self.mapToScene(self.boundingRect().topLeft())
            bottomRight = self.mapToScene(self.boundingRect().bottomRight())
            
            collision = self.sampleCollision()
            
            if collision & common.COLLISIONBITS.FOREGROUNDBOTTOM or collision & common.COLLISIONBITS.FOREGROUNDTOP:
                height = self.pixmap().rect().height()
                half = (8 * round((height//2)/8))
                diff = height-half
                adjusted = self.pixmap().rect().adjusted(self.offset().x(),
                                                         self.offset().y(),
                                                         0, 0)
                bottomHalfRect = adjusted.adjusted(0, diff, 0, 0)
                
                # get the tiles we intersect with
                x0, y0 = EBCoords(int(topLeft.x()), int(topLeft.y())).coordsTile()
                x1, y1 = EBCoords(int(bottomRight.x()), int(bottomRight.y())).coordsTile()
                tiles: list[MapTile] = []
                for y in range(y0, y1+1):
                    for x in range(x0, x1+1):
                        try:
                            tiles.append(self.scene().projectData.getTile(EBCoords.fromTile(x, y)))
                        except IndexError:
                            pass

                grid = self.scene().grid
                if grid.isVisible():
                    brush = grid.brush()
                else:
                    brush = None
                        
                for tile in tiles:
                    graphic = self.scene().projectData.getTileGraphic(tile.tileset,
                                                                    tile.palettegroup,
                                                                    tile.palette,
                                                                    tile.tile)
                    
                    if not graphic.hasRenderedFg:
                        graphic.renderFg(self.scene().projectData.getTileset(tile.tileset))
                    
                    target = (tile.coords.x - math.ceil(topLeft.x()) + self.offset().x(),
                            tile.coords.y - math.ceil(topLeft.y()) + self.offset().y())

                    pixmap = graphic.renderedFg.copy() # seems inefficient but doesn't appear to have an actual impact?
                    
                    collisionPainter = QPainter(pixmap)
                    collisionPainter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
                    collisionPainter.setOpacity(0.7)
                    collisionPainter.setPen(Qt.PenStyle.NoPen)
                    presets = QSettings().value("presets/presets", defaultValue=common.DEFAULTCOLLISIONPRESETS)
                    presetColours: dict[int, int] = {}
                    for _, value, colour in json.loads(presets):
                        presetColours[value] = colour
                    for cx in range(0, 4):
                        for cy in range(0, 4):
                            minitileCollision = self.scene().collisionAt(EBCoords.fromWarp(tile.coords.coordsWarp()[0]+cx, tile.coords.coordsWarp()[1]+cy))
                            if minitileCollision:
                                try:
                                    colour = presetColours[minitileCollision]
                                except KeyError:
                                    colour = 0x303030
                                collisionPainter.setBrush(QColor.fromRgb(colour))
                                collisionPainter.drawRect(cx*8, cy*8, 8, 8)
                    collisionPainter.end()
                
                    if brush:
                        gridPainter = QPainter(pixmap)
                        gridPainter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
                        gridPainter.setBrush(brush)
                        gridPainter.setPen(Qt.GlobalColor.transparent)
                        gridPainter.drawRect(0, 0, 32, 32)
                        gridPainter.end()
                    
                    if (collision & common.COLLISIONBITS.FOREGROUNDBOTTOM) and not (collision & common.COLLISIONBITS.FOREGROUNDTOP):
                        painter.setClipRect(bottomHalfRect)
                    else:
                        painter.setClipRect(adjusted)
                    painter.drawPixmap(*target, pixmap)
        
    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        if (not self.isDummy) and self.scene().state.mode == common.MODEINDEX.NPC:
            menu = QMenu()
            menu.addAction(icons.ICON_NEW, "New NPC",
                        lambda: self.scene().newNPC(EBCoords(event.scenePos().x(), event.scenePos().y())))
            menu.addAction(icons.ICON_DELETE, "Delete", self.scene().deleteSelectedNPCs, shortcut=QKeySequence(Qt.Key.Key_Delete))
            menu.addSeparator()
            menu.addAction(icons.ICON_CUT, "Cut", self.scene().onCut)
            menu.addAction(icons.ICON_COPY, "Copy", self.scene().onCopy)
            menu.addAction(icons.ICON_PASTE, "Paste", self.scene().onPaste)
            menu.exec(event.screenPos())
            super().contextMenuEvent(event)
            
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if (not self.isDummy) and self.scene().state.mode == common.MODEINDEX.NPC:
            if event.buttons() == Qt.MouseButton.RightButton:
                event.setButtons(Qt.MouseButton.LeftButton) # fixes context menu not highlighting

            super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):  
        if (not self.isDummy) and self.scene().state.mode == common.MODEINDEX.NPC:
            super().mouseMoveEvent(event)
            for i in self.scene().selectedItems(): # make sure other selected items align to the grid
                pos = i.pos()
                pos.setX(common.cap(int(pos.x()), 0, common.EBMAPWIDTH-1))
                pos.setY(common.cap(int(pos.y()), 0, common.EBMAPHEIGHT-1))
                i.setPos(pos)
            
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if event.buttons() == Qt.MouseButton.NoButton: # only if this was the *last* button released
            if (not self.isDummy) and self.scene().state.mode == common.MODEINDEX.NPC:
                super().mouseReleaseEvent(event)
                isMovingNPCs = False
                for i in self.scene().selectedItems():
                    inst = self.scene().projectData.npcInstanceFromUUID(i.uuid)
                    coords = EBCoords(i.x(), i.y())
                    coords.restrictToMap()

                    if coords == inst.coords: # if we didn't move, don't bother
                        break

                    else:
                        if not isMovingNPCs:
                            isMovingNPCs = True
                            self.scene().undoStack.beginMacro("Move NPCs")

                        i.setPos(coords.x, coords.y)
                    
                        action = ActionMoveNPCInstance(inst, coords)
                        self.scene().undoStack.push(action)

                if isMovingNPCs:
                    self.scene().undoStack.endMacro()
                
                self.scene().parent().sidebarNPC.fromNPCInstances()

    # for typing
    def scene(self) -> "MapEditorScene":
        return super().scene()
    
    def setDummy(self):
        """Make this item non-interactable, hide IDs, visual boundaries, etc.
        Also, this means the item won't be covered by large-scale NPC hiding/showing.
        You'll need to manage that on your own.
        """
        self.isDummy = True
        MapEditorNPC.instances.remove(self)
        self.num.hide()
        self.numShadow.hide()
        self.numBgRect.hide()
        self.visualBounds.hide()
        self.collisionBounds.hide()
        self.unsetCursor()
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable, False)
    
    @classmethod
    def hideNPCs(cls):
        for i in cls.instances:
            i.hide()
    @classmethod
    def showNPCs(cls):
        for i in cls.instances:
            i.show()

    @classmethod
    def hideNPCIDs(cls):
        for i in cls.instances:
            i.num.hide()
            i.numShadow.hide()
            i.numBgRect.hide()
        MapEditorNPC.NPCIDsEnabled = False

    @classmethod
    def showNPCIDs(cls):
        for i in cls.instances:
            i.num.show()
            i.numShadow.show()
            i.numBgRect.show()
        MapEditorNPC.NPCIDsEnabled = True

    @classmethod
    def hideVisualBounds(cls):
        for i in cls.instances:
            i.visualBounds.hide()
        MapEditorNPC.visualBoundsEnabled = False
    
    @classmethod
    def showVisualBounds(cls):
        for i in cls.instances:
            i.visualBounds.show()
        MapEditorNPC.visualBoundsEnabled = True

    @classmethod
    def hideCollisionBounds(cls):
        for i in cls.instances:
            i.collisionBounds.hide()
        MapEditorNPC.collisionBoundsEnabled = False

    @classmethod
    def showCollisionBounds(cls):
        for i in cls.instances:
            i.collisionBounds.show()
        MapEditorNPC.collisionBoundsEnabled = True