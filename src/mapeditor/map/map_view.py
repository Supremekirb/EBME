from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QSettings, Qt, QTimeLine, QTimer
from PySide6.QtGui import (QBrush, QMouseEvent, QPaintEvent, QPen,
                           QResizeEvent, QWheelEvent)
from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsPixmapItem,
                               QGraphicsView)

import src.misc.common as common
from src.coilsnake.project_data import ProjectData
from src.mapeditor.map.map_scene import MapEditorScene
from src.misc.coords import EBCoords

if TYPE_CHECKING:
    from src.mapeditor.map_editor import MapEditor, MapEditorState
   

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
        
        # default is true, set to false
        # we arrange the scene with the RightToLeft property in MapEditor, because it lets us
        # put the vertical scrollbar on the left side, which fits better
        self.horizontalScrollBar().setInvertedControls(False)

        self.scaleFactor = 100
        
        # bonuses
        #self.shear(1, 0) # unisometric mode
        #self.rotate(45) # normal fourside mode

    def leaveEvent(self, event: QEvent):
        self.parent().status.updateCoords(EBCoords(-1, -1))
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        # TODO - it's probably possible to move much of this logic out to the scene itself.
        # that'll make it easier to create other interactive views in the future, if necessary.
        # Alternatively, create a generic MapEditorView class.
        
        # coord copying requires this event always
        if event.buttons() == Qt.MouseButton.RightButton and Qt.KeyboardModifier.AltModifier in event.modifiers():
            return super().mousePressEvent(event)
        
        # we're wanting to pan, so don't click on stuff
        if ((event.modifiers() == Qt.KeyboardModifier.ShiftModifier and event.buttons() == Qt.MouseButton.LeftButton) or
            Qt.MouseButton.MiddleButton in event.buttons()):
            return
        
        # contextMenuEvent handles this, so return (is this necessary?)
        if Qt.MouseButton.RightButton in event.buttons() and self.state.mode in [common.MODEINDEX.NPC, common.MODEINDEX.TRIGGER]:
            return
        
        # adjust rubberband drag mode
        if self.state.mode in [common.MODEINDEX.NPC, common.MODEINDEX.TRIGGER]:
            # requires being unset and reset apparently..?
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        
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
        if (Qt.KeyboardModifier.ControlModifier in event.modifiers()) ^ QSettings().value("main/noCtrlZoom", False, type=bool):
            if event.angleDelta().y() > 0:
                self.zoomIn(True)
            else:
                self.zoomOut(True)
        else: 
            if QSettings().value("main/noCtrlZoom", False, type=bool):  
                event.setModifiers(event.modifiers() & ~Qt.KeyboardModifier.ControlModifier) # otherwise it only does fast scroll
                
            if Qt.KeyboardModifier.AltModifier in event.modifiers():
                delta = event.angleDelta().y()
                if Qt.KeyboardModifier.ShiftModifier in event.modifiers():
                    delta *= 2                      
                
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + delta)
            
            else: super().wheelEvent(event)


    def revealTriggerDestination(self, start: EBCoords, end: EBCoords):
        """Reveal the destination of a trigger

        Args:
            start (EBCoords): position of the trigger origin
            end (EBCoords): position of the trigger destination
        """
        
        self.autoCenterOn(EBCoords(end.x+4, end.y+4))

        self.scene().doorDestShowLine.setLine(start.x+4, start.y+4, end.x+4, end.y+4)
        self.scene().doorDestShowLine.show()

        # hide after 2 seconds
        QTimer.singleShot(2000, self.scene().doorDestShowLine.hide)

    def zoomIn(self, onMouse = False):
        self.horizontalScrollBar().blockSignals(True)
            
        if self.scaleFactor < 800:
            if onMouse:
                self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
            
            self.scaleFactor *= 2
            self.scale(2, 2)
                
            self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
            
        self.horizontalScrollBar().blockSignals(False)
        self.parent().status.setZoom(self.scaleFactor)
        
        
    def zoomOut(self, onMouse = False):
        self.horizontalScrollBar().blockSignals(True)
        if self.scaleFactor > 25:
            if onMouse:
                self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
                
            self.scaleFactor //= 2
            self.scale(0.5, 0.5)
            
            self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
            
        self.horizontalScrollBar().blockSignals(False)
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