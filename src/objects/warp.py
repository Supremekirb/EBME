from typing import TYPE_CHECKING, Literal

from PySide6.QtGui import QBrush, QPixmap, Qt
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGraphicsRectItem,
                               QGraphicsSceneMouseEvent,
                               QGraphicsSimpleTextItem)

import src.misc.common as common
from src.actions.warp_actions import ActionMoveTeleport, ActionMoveWarp
from src.misc.coords import EBCoords

if TYPE_CHECKING:
    from src.mapeditor.map.map_scene import MapEditorScene

WHITEBRUSH = QBrush(Qt.GlobalColor.white)
BLACKBRUSH = QBrush(Qt.GlobalColor.black)

class Warp():
    """Warp objects"""
    def __init__(self, id: int, dest: EBCoords=EBCoords(), dir: str="up",
                 style: int=0, unknown: int=0, comment: str=None):  
        self.id = id   
        self.dest = dest
        self.dir = dir
        self.style = style
        self.unknown = unknown
        self.comment = comment
        
class Teleport():
    """Teleport objects"""
    def __init__(self, id: int, dest: EBCoords, flag: int, name: str=""):
        self.id = id
        self.dest = dest
        self.flag = flag
        self.name = name
        
        
class MapEditorWarp(QGraphicsPixmapItem):
    warpIDsEnabled = False
    instances = []
    def __init__(self, coords: EBCoords, id: int, pixmap: QPixmap, warpType: Literal["warp", "teleport"]):
        super().__init__(pixmap)
        self.setPixmap(pixmap)
        
        self.id = id
        self.warpType = warpType
        
        self.numBgRect = QGraphicsRectItem(self)
        self.numShadow = QGraphicsSimpleTextItem(self)
        self.num = QGraphicsSimpleTextItem(self)
        
        self.numBgRect.setBrush(BLACKBRUSH)
        self.num.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.numBgRect.setPen(Qt.PenStyle.NoPen)
        self.numBgRect.setOpacity(0.5)
        self.numBgRect.setRect(0, -13, 28, 13)
        
        self.numShadow.setFont("EBMain")
        self.numShadow.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.numShadow.setPos(2, -11)
        
        self.num.setFont("EBMain")
        self.num.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.num.setPos(1, -12)
        self.num.setBrush(WHITEBRUSH)
        
        self.setPos(coords.x, coords.y)
        self.setZValue(common.MAPZVALUES.WARP)
        
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable, True)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        if not MapEditorWarp.warpIDsEnabled:
            self.numBgRect.hide()
            self.num.hide()
            self.numShadow.hide()
        
        MapEditorWarp.instances.append(self)
    
    def setText(self, text: str):
        self.numShadow.setText(text)
        self.num.setText(text)
        
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if self.scene().state.mode == common.MODEINDEX.WARP:
            self.scene().clearSelection()
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self.scene().state.mode == common.MODEINDEX.WARP:
            pos = event.scenePos()
            coords = EBCoords(pos.x(), pos.y())
            pos.setX(coords.roundToWarp()[0]+8)
            pos.setY(coords.roundToWarp()[1]+8)
            event.setScenePos(pos)
            
            super().mouseMoveEvent(event)
            
            for i in self.scene().selectedItems():
                pos = i.pos()
                pos.setX(common.cap((pos.x()//8)*8, 0, common.EBMAPWIDTH-1))
                pos.setY(common.cap((pos.y()//8)*8, 0, common.EBMAPHEIGHT-1))
                i.setPos(pos)
                
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self.scene().state.mode == common.MODEINDEX.WARP:
            if event.buttons() == Qt.MouseButton.NoButton: # only if this was the *last* button released   
                super().mouseReleaseEvent(event)
                isMovingWarps = False
                for i in self.scene().selectedItems():
                    if i.warpType == "warp":
                        warp = self.scene().projectData.warps[i.id]
                    else:
                        warp = self.scene().projectData.teleports[i.id]
                    coords = EBCoords(i.x(), i.y())
                    coords.restrictToMap()
                    
                    if coords == warp.dest: # if we didn't move, don't bother updating the map
                        break
                    
                    else:
                        if not isMovingWarps:
                            isMovingWarps = True
                            if i.warpType == "warp":
                                self.scene().undoStack.beginMacro("Move Warps")
                            else:
                                self.scene().undoStack.beginMacro("Move Teleports")
                        
                        i.setPos(coords.x, coords.y)
                        
                        if i.warpType == "warp":
                            action = ActionMoveWarp(warp, coords)
                        else:
                            action = ActionMoveTeleport(warp, coords)
                        self.scene().undoStack.push(action)
                    
                if isMovingWarps:
                    self.scene().undoStack.endMacro()     
                
                self.scene().parent().sidebarWarp.fromWarp()
                
    # for typing
    def scene(self) -> "MapEditorScene":
        return super().scene()
    
    @classmethod
    def showWarps(cls):
        for i in cls.instances:
            i.show()
    
    @classmethod
    def hideWarps(cls):
        for i in cls.instances:
            i.hide()
            
    @classmethod
    def showWarpIDs(cls):
        for i in cls.instances:
            i.numBgRect.show()
            i.num.show()
            i.numShadow.show()
        
        MapEditorWarp.warpIDsEnabled = True
    
    @classmethod
    def hideWarpIDs(cls):
        for i in cls.instances:
            i.numBgRect.hide()
            i.num.hide()
            i.numShadow.hide()
            
        MapEditorWarp.warpIDsEnabled = False