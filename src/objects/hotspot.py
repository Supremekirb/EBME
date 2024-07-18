from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.mapeditor.map.map_scene import MapEditorScene

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (QGraphicsRectItem, QGraphicsSceneHoverEvent,
                               QGraphicsSceneMouseEvent)

import src.misc.common as common
from src.actions.hotspot_actions import ActionChangeHotspotLocation
from src.misc.coords import EBCoords

MOUSEACTION = IntEnum( "MOUSEACTION", [
    "MOVE",
    "RESIZELEFT",
    "RESIZERIGHT",
    "RESIZETOP",
    "RESIZEBOTTOM",
    "RESIZETOPLEFT",
    "RESIZETOPRIGHT",
    "RESIZEBOTTOMLEFT",
    "RESIZEBOTTOMRIGHT"
])

class Hotspot:
    """Hotspot objects"""
    def __init__(self, id: int, start: EBCoords, end: EBCoords, colour: tuple[int, int, int] = (255, 0, 0), comment: str = None):
        self.id = id
        self.start = start
        self.end = end
        self.colour = colour
        self.comment = comment
        
    def size(self) -> EBCoords:
        return self.end-self.start
    
class MapEditorHotspot(QGraphicsRectItem):
    hotspots = []
    def __init__(self, id: int, start: EBCoords, end: EBCoords, colour: tuple[int, int, int]):
        super().__init__(start.x, start.y, end.x-start.x, end.y-start.y)
        
        self.id = id
        self.setPen(Qt.PenStyle.NoPen)
        self.setBrush(QBrush(QColor(*colour, 128)))
        self.setZValue(common.MAPZVALUES.HOTSPOT)
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable)
        
        MapEditorHotspot.hotspots.append(self)
        
        self.actionMode = MOUSEACTION.MOVE
        self._mousePressOffset = (0, 0)
        
    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        if self.scene().state.mode == common.MODEINDEX.HOTSPOT:
            # get mouse pos - if it's near the edges, set the cursor to the appropriate resize
            pos = self.mapToItem(self, event.pos())
            
            # fix rect weirdness (we set rect size, never item pos, so we need to adjust the pos to the top left of the rect)
            pos -= self.rect().topLeft()
            MARGIN = 5
            
            if (pos.x() < MARGIN and pos.y() < MARGIN):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                self.actionMode = MOUSEACTION.RESIZETOPLEFT
            
            elif (pos.x() > self.rect().width() - MARGIN and pos.y() > self.rect().height() - MARGIN):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                self.actionMode = MOUSEACTION.RESIZEBOTTOMRIGHT
                
            elif (pos.x() > self.rect().width() - MARGIN and pos.y() < MARGIN):
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
                self.actionMode = MOUSEACTION.RESIZETOPRIGHT
            
            elif (pos.x() < MARGIN and pos.y() > self.rect().height() - MARGIN):
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
                self.actionMode = MOUSEACTION.RESIZEBOTTOMLEFT
            
            elif pos.x() < MARGIN:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
                self.actionMode = MOUSEACTION.RESIZELEFT
            
            elif pos.x() > self.rect().width() - MARGIN:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
                self.actionMode = MOUSEACTION.RESIZERIGHT
                
            elif pos.y() < MARGIN:
                self.setCursor(Qt.CursorShape.SizeVerCursor)
                self.actionMode = MOUSEACTION.RESIZETOP
                
            elif pos.y() > self.rect().height() - MARGIN:
                self.setCursor(Qt.CursorShape.SizeVerCursor)
                self.actionMode = MOUSEACTION.RESIZEBOTTOM
        
            else:
                self.setCursor(Qt.CursorShape.SizeAllCursor)
                self.actionMode = MOUSEACTION.MOVE 
            
            super().hoverMoveEvent(event)     

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):  
        if self.scene().state.mode == common.MODEINDEX.HOTSPOT:
            self._mousePressOffset = (event.scenePos().x() - self.rect().left(), event.scenePos().y() - self.rect().top())
            self.scene().clearSelection()     
            super().mousePressEvent(event)
        
        
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self.scene().state.mode == common.MODEINDEX.HOTSPOT:
            if event.buttons() == Qt.MouseButton.LeftButton:
                    if self.actionMode == MOUSEACTION.RESIZELEFT:
                        self.setRect(self.rect().adjusted((event.scenePos().x()-self.rect().left())//8*8, 0, 0, 0))
                    elif self.actionMode == MOUSEACTION.RESIZERIGHT:
                        self.setRect(self.rect().adjusted(0, 0, (event.scenePos().x()-self.rect().right())//8*8, 0))
                    elif self.actionMode == MOUSEACTION.RESIZETOP:
                        self.setRect(self.rect().adjusted(0, (event.scenePos().y()-self.rect().top())//8*8, 0, 0))
                    elif self.actionMode == MOUSEACTION.RESIZEBOTTOM:
                        self.setRect(self.rect().adjusted(0, 0, 0, (event.scenePos().y()-self.rect().bottom())//8*8))
                    elif self.actionMode == MOUSEACTION.RESIZETOPLEFT:
                        self.setRect(self.rect().adjusted((event.scenePos().x()-self.rect().left())//8*8, (event.scenePos().y()-self.rect().top())//8*8, 0, 0))
                    elif self.actionMode == MOUSEACTION.RESIZETOPRIGHT:
                        self.setRect(self.rect().adjusted(0, (event.scenePos().y()-self.rect().top())//8*8, (event.scenePos().x()-self.rect().right())//8*8, 0))
                    elif self.actionMode == MOUSEACTION.RESIZEBOTTOMLEFT:
                        self.setRect(self.rect().adjusted((event.scenePos().x()-self.rect().left())//8*8, 0, 0, (event.scenePos().y()-self.rect().bottom())//8*8))
                    elif self.actionMode == MOUSEACTION.RESIZEBOTTOMRIGHT:
                        self.setRect(self.rect().adjusted(0, 0, (event.scenePos().x()-self.rect().right())//8*8, (event.scenePos().y()-self.rect().bottom())//8*8))
                    elif self.actionMode == MOUSEACTION.MOVE:
                        # moving should also use the rect, not set the pos
                        # otherwise things break
                        # idk why they have rect offset AND pos stuff
                        dx = (event.scenePos().x()-self.rect().left()-self._mousePressOffset[0])//8*8
                        dy = (event.scenePos().y()-self.rect().top()-self._mousePressOffset[1])//8*8
                        self.setRect(self.rect().adjusted(dx, dy, dx, dy))
                        
                    # minimum size
                    # BUG: resizing past minimum on the left and top causes it to move
                    rect = self.rect()
                    rect.setWidth(max(8, self.rect().width()))
                    rect.setHeight(max(8, self.rect().height()))
                    self.setRect(rect)                
                        
                    # don't go oob
                    if self.rect().left() < 0:
                        self.setRect(self.rect().adjusted(-self.rect().left(), 0, -self.rect().left(), 0))
                    if self.rect().right() > common.EBMAPWIDTH:
                        self.setRect(self.rect().adjusted(common.EBMAPWIDTH-self.rect().right(), 0, common.EBMAPWIDTH-self.rect().right(), 0))
                    if self.rect().top() < 0:
                        self.setRect(self.rect().adjusted(0, -self.rect().top(), 0, -self.rect().top()))
                    if self.rect().bottom() > common.EBMAPHEIGHT:
                        self.setRect(self.rect().adjusted(0, common.EBMAPHEIGHT-self.rect().bottom(), 0, common.EBMAPHEIGHT-self.rect().bottom()))
                            
            super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self.scene().state.mode == common.MODEINDEX.HOTSPOT:
            if event.buttons() == Qt.MouseButton.NoButton: # only if this was the *last* button released
                if self.scene().state.mode == common.MODEINDEX.HOTSPOT:
                    start = EBCoords(self.rect().left(), self.rect().top())
                    end = EBCoords(self.rect().right(), self.rect().bottom())
                    
                    if start != self.scene().state.currentHotspot.start or end != self.scene().state.currentHotspot.end:
                        action = ActionChangeHotspotLocation(self.scene().state.currentHotspot, start, end)
                    
                        self.scene().undoStack.push(action)
                        self.scene().parent().sidebarHotspot.fromHotspot()
        
    # for typing
    def scene(self) -> "MapEditorScene":
        return super().scene()

    @classmethod
    def showHotspots(cls):
        for i in cls.hotspots:
            i.show()
    
    @classmethod
    def hideHotspots(cls):
        for i in cls.hotspots:
            i.hide()          
