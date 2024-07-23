from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QSettings, Qt, QTimeLine, QTimer
from PySide6.QtGui import QBrush, QMouseEvent, QPaintEvent, QPen, QResizeEvent, QWheelEvent
from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsPixmapItem,
                               QGraphicsView)

if TYPE_CHECKING:
    from src.mapeditor.map_editor import MapEditorState, MapEditor

import src.misc.common as common
from src.coilsnake.project_data import ProjectData
from src.mapeditor.map.map_scene import MapEditorScene
from src.misc.coords import EBCoords

WHITEBRUSH = QBrush(Qt.white)
BLACKBRUSH = QBrush(Qt.black)

class MapEditorView(QGraphicsView):
    def __init__(self, parent: "MapEditor", state: "MapEditorState", data: ProjectData, scene: MapEditorScene):

        QGraphicsView.__init__(self, parent)

        self.setMouseTracking(True)
        
        self.state = state
        self.projectData = data
        self.setScene(scene)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        self.scaleFactor = 100
        
        # bonuses
        #self.shear(1, 0) # unisometric mode
        #self.rotate(45) # normal fourside mode

        self._lastTransform = self.viewportTransform()
    
    # overriding to render shown
    def paintEvent(self, event: QPaintEvent):
        if self.viewportTransform() != self._lastTransform:
            self._lastTransform = self.viewportTransform()
            self.renderShown()
            
        super().paintEvent(event)
    
    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.renderShown()

    def leaveEvent(self, event: QEvent):
        self.parent().status.updateCoords(EBCoords(-1, -1))
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if ((event.modifiers() == Qt.KeyboardModifier.ShiftModifier and event.buttons() == Qt.MouseButton.LeftButton) or
            Qt.MouseButton.MiddleButton in event.buttons()):
            return
        
        if Qt.MouseButton.RightButton in event.buttons() and self.state.mode in [common.MODEINDEX.NPC, common.MODEINDEX.TRIGGER]:
            return
            
        if self.state.mode in [common.MODEINDEX.TILE, common.MODEINDEX.SECTOR, common.MODEINDEX.ENEMY,
                                common.MODEINDEX.HOTSPOT, common.MODEINDEX.WARP,
                                common.MODEINDEX.GAME, common.MODEINDEX.ALL]:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event: QMouseEvent):
        if not hasattr(self, "_lastMousePos"):
            self._lastMousePos = event.pos()
            
        # custom implementation of panning. because the vanilla one stinks
        if ((event.modifiers() == Qt.KeyboardModifier.ShiftModifier and event.buttons() == Qt.MouseButton.LeftButton) or
            Qt.MouseButton.MiddleButton in event.buttons()):
            
            # since we check for left button a lot, let's just fake a middle-only one
            event = QMouseEvent(event.type(), event.pos(), Qt.MouseButton.MiddleButton, Qt.MouseButton.MiddleButton, Qt.KeyboardModifier.NoModifier)
            
            delta = event.pos() - self._lastMousePos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - (-delta.x() if self.isRightToLeft() else delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            
        else:
            self.unsetCursor()
        super().mouseMoveEvent(event)
        
        self._lastMousePos = event.pos()
    
    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoomIn()
            else:
                self.zoomOut()
        else: super().wheelEvent(event)

    def renderShown(self):
        """Get the shown area of the viewport and render it"""
        rect = self.mapToScene(self.viewport().geometry()).boundingRect().getRect()
        
        self.scene().renderArea(
            EBCoords(rect[0], rect[1]), # top left
            common.pixToTile(rect[2]),
            common.pixToTile(rect[3])
            )
    
        if self.state.mode == common.MODEINDEX.ENEMY or self.state.mode == common.MODEINDEX.ALL:
            self.scene().renderEnemies(
                EBCoords(rect[0], rect[1]), # top left
                common.pixToEnemy(rect[2]),
                common.pixToEnemy(rect[3])
            )


    def revealTriggerDestination(self, start: EBCoords, end: EBCoords):
        """Reveal the destination of a trigger

        Args:
            start (EBCoords): position of the trigger origin
            end (EBCoords): position of the trigger destination
        """
        
        self.autoCenterOn(EBCoords(end.x+4, end.y+4))

        if not hasattr(self.scene(), "triggerDestShowLine"): # a lot of this would be simpler if i added them at init...
            self.scene().doorDestShowLine = QGraphicsLineItem()
            self.scene().addItem(self.scene().doorDestShowLine)

        self.scene().doorDestShowLine.setPen(QPen(Qt.red, 2))
        self.scene().doorDestShowLine.setLine(start.x+4, start.y+4, end.x+4, end.y+4)
        self.scene().doorDestShowLine.setZValue(common.MAPZVALUES.DOORDESTLINE)

        if not hasattr(self.scene(), "triggerDestShowIcon"):
            self.scene().doorDestShowIcon = QGraphicsPixmapItem(self.scene().imgTriggerDest)
            self.scene().addItem(self.scene().doorDestShowIcon)

        self.scene().doorDestShowIcon.setPos(end.x, end.y)
        self.scene().doorDestShowIcon.setZValue(common.MAPZVALUES.DOORDESTICON)

        self.scene().doorDestShowIcon.show()
        self.scene().doorDestShowLine.show()

        QTimer.singleShot(2000, self.scene().doorDestShowIcon.hide) # hide after 2 seconds
        QTimer.singleShot(2000, self.scene().doorDestShowLine.hide)

    def zoomIn(self):
        self.horizontalScrollBar().blockSignals(True)
        if self.scaleFactor < 800:
            self.scaleFactor *= 2
            self.scale(2, 2)
        self.horizontalScrollBar().blockSignals(False)
        self.renderShown()
        self.parent().status.setZoom(self.scaleFactor)

    def zoomOut(self):
        self.horizontalScrollBar().blockSignals(True)
        if self.scaleFactor > 25:
            self.scaleFactor //= 2
            self.scale(0.5, 0.5)
        self.horizontalScrollBar().blockSignals(False)
        self.renderShown()
        self.parent().status.setZoom(self.scaleFactor)

    def autoCenterOn(self, coords: EBCoords, msecs: int=500):
        """Check settings and center on with or without an animation depending on that and distance

        Args:
            coords (EBCoords): location to center on
            msecs (int, optional): time to animate in milliseconds, if animating. Defaults to 500.
        """

        settings = QSettings()

        if settings.value("personalisation/smoothGoto", type=str) == "Enabled":
            self.smoothCenterOn(coords, msecs)
        
        elif settings.value("personalisation/smoothGoto", type=str) == "Enabled for short distances":
            # find the total linear distance between the two points, and if it's not more than 2500 pixels, animate
            # otherwise, just snap to it.
            distance = ((self.mapToScene(self.viewport().rect().center()).x() - coords.x)**2 + (self.mapToScene(self.viewport().rect().center()).y() - coords.y)**2)**0.5
            if distance <= 2500:
                self.smoothCenterOn(coords, msecs)
            else: self.centerOn(coords.x, coords.y)

        else:
            self.centerOn(coords.x, coords.y)

    def smoothCenterOn(self, coords: EBCoords, msecs: int=500):
        """Shift the view to center on a point smoothly.

        Args:
            coords (EBCoords): end location
            msecs (int, optional): time to animate in milliseconds. Defaults to 500.
        """
        # QTimeLine only accepts one value to animate, so we have to do this manually
        # (Running an X animation and a Y animation in parallel breaks things)
        # So, we'll calculate all the centering values, and iterate over them ourselves.

        STEPS = 1000 # the highest granularity of the animation.
        # this will not affect the time it takes to animate - QTimeLine always completes at the same speed
        # So, this only applies if the rendering is faster than the animation.

        startX = self.mapToScene(self.viewport().rect().center()).x()
        locationsX = []
        intervalX = (coords.x - startX) / STEPS
        for i in range(0, STEPS+1):
            locationsX.append(startX+(intervalX*i))
            
        startY = self.mapToScene(self.viewport().rect().center()).y()
        locationsY = []
        intervalY = (coords.y - startY) / STEPS
        for i in range(0, STEPS+1):
            locationsY.append(startY+(intervalY*i))

        anim = QTimeLine(msecs, self)
        anim.setFrameRange(0, STEPS)
        anim.frameChanged.connect(lambda frame: self.centerOn(locationsX[frame], locationsY[frame]))
        anim.start()
        
    # for type checking
    def parent(self) -> "MapEditor":
        return super().parent()
    
    def scene(self) -> MapEditorScene:
        return super().scene()