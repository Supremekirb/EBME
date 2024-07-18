import uuid
from typing import TYPE_CHECKING

from src.actions.trigger_actions import ActionMoveTrigger

if TYPE_CHECKING:
    from src.mapeditor.map.map_scene import MapEditorScene

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QGraphicsItem, QGraphicsPixmapItem,
                               QGraphicsSceneContextMenuEvent,
                               QGraphicsSceneMouseEvent, QMenu)

import src.misc.common as common
from src.misc.coords import EBCoords


class TriggerDoor:
    """Door trigger type. Creating this with no arguments creates a door with basic data"""
    def __init__(self, destCoords: EBCoords = EBCoords(), dir: str="up", flag: int=0, style: int=0, textPointer: str="$0"):
        self.destCoords = destCoords
        self.dir = dir
        self.flag = flag
        self.style = style
        self.textPointer = textPointer
    def toDataDict(self) -> dict[str, str|int|tuple[int, int]]:
        """Keys: type, dest, dir, flag, style, text"""
        return {"type": "door",
                "dest": self.destCoords.coords(),
                "dir": self.dir,
                "flag": self.flag,
                "style": self.style,
                "text": self.textPointer}
class TriggerEscalator:
    """Escalator trigger type. Creating this with no arguments creates an escalator with basic data"""
    def __init__(self, direction: str="nowhere"):
        self.direction = direction        
    def toDataDict(self) -> dict[str, str]:
        """Keys: type, dir"""
        return {"type": "escalator",
                "dir": self.direction}
class TriggerLadder:
    """Ladder trigger type. Ladders have no extra data."""
    def __init__(self):
        pass
    def toDataDict(self) -> dict[str, str]:
        """Keys: type"""
        return {"type": "ladder"}
class TriggerObject:
    """Object trigger type. Creating this with no arguments creates an object with basic data"""
    def __init__(self, textPointer: str="$0"):
        self.textPointer = textPointer
    def toDataDict(self) -> dict[str, str]:
        """Keys: type, text"""
        return {"type": "object",
                "text": self.textPointer}
class TriggerPerson:
    """Person trigger type. Creating this with no arguments creates a person with basic data"""
    def __init__(self, textPointer: str="$0"):
        self.textPointer = textPointer
    def toDataDict(self) -> dict[str, str]:
        """Keys: type, text"""
        return {"type": "person",
                "text": self.textPointer}
class TriggerRope:
    """Rope trigger type. Ropes have no extra data."""
    def __init__(self):
        pass
    def toDataDict(self) -> dict[str, str]:
        """Keys: type"""
        return {"type": "rope"}
class TriggerStairway:
    """Stairway trigger type. Creating this with no arguments creates a stairway with basic data"""
    def __init__(self, direction: str="ne"):
        self.direction = direction
    def toDataDict(self) -> dict[str, str]:
        """Keys: type, dir"""
        return {"type": "stairway",
                "dir": self.direction}
class TriggerSwitch:
    """Switch trigger type. Creating this with no arguments creates a switch with basic data"""
    def __init__(self, textPointer: str="$0", flag: int=0):
        self.textPointer = textPointer
        self.flag = flag
    def toDataDict(self) -> dict[str, str|int]:
        """Keys: type, text, flag"""
        return {"type": "switch",
                "text": self.textPointer,
                "flag": self.flag}

class Trigger:
    """Triggers on the map"""
    def __init__(self, coords: EBCoords, typeData: TriggerDoor|TriggerEscalator|TriggerLadder|TriggerObject|TriggerPerson|TriggerRope|TriggerStairway|TriggerSwitch):
        self.coords = EBCoords(coords.roundToWarp()[0], coords.roundToWarp()[1])
        self.typeData = typeData

        self.uuid = uuid.uuid4()

    def posToMapDoorsFormat(self) -> tuple[int, int, int, int]:
        """Convert trigger pixel position to bisector and offset.

        Returns:
            Tuple: Bisector X, Bisector Y, Offset X, Offset Y
        """
        x, y = self.coords.coords()
        bsX, bsY = self.coords.coordsBisector()
        
        # i dont even know whats going on here
        # converted from an older function to the new coords system
        # works though...
        oX = (x - (bsX*256))//8
        oY = (y - (bsY*256))//8

        return bsX, bsY, oX, oY
    
    def toDataDict(self) -> dict[str, tuple[int, int] | dict]:
        """Get a dict containing relevant data for copying and pasting.
        
        Returns:
            dict: Dict containing trigger coordinates (as a tuple) and type data at keys [id] and [data].
            For type data info, check each type data class.
        """
        return {'coords': self.coords.coords(), 'data': self.typeData.toDataDict()}

class MapEditorTrigger(QGraphicsPixmapItem):
    instances = []
    def __init__(self, coords: EBCoords, uuid: uuid.UUID):
        QGraphicsPixmapItem.__init__(self)
        MapEditorTrigger.instances.append(self)

        self.uuid = uuid

        self.setPos(coords.x, coords.y)
        self.setZValue(common.MAPZVALUES.TRIGGER)

        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if self.scene().state.mode == common.MODEINDEX.TRIGGER:
            super().mousePressEvent(event)
    
    # reimplementing function to make sure that the trigger is always aligned to the pixel grid
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self.scene().state.mode == common.MODEINDEX.TRIGGER:
            pos = event.scenePos()
            coords = EBCoords(pos.x(), pos.y())
            pos.setX(coords.roundToWarp()[0]+8) # dont know why I need to add this but oh well
            pos.setY(coords.roundToWarp()[1]+8)
            event.setScenePos(pos)
            
            super().mouseMoveEvent(event)
            
            for i in self.scene().selectedItems(): # make sure other selected items align to the grid
                pos = i.pos()
                pos.setX(common.cap((pos.x()//8)*8, 0, common.EBMAPWIDTH-1))
                pos.setY(common.cap((pos.y()//8)*8, 0, common.EBMAPHEIGHT-1))
                i.setPos(pos)
    
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self.scene().state.mode == common.MODEINDEX.TRIGGER:
            if event.buttons() == Qt.MouseButton.NoButton: # only if this was the *last* button released   
                super().mouseReleaseEvent(event)
                isMovingTriggers = False
                for i in self.scene().selectedItems():
                    trigger = self.scene().projectData.triggerFromUUID(i.uuid)
                    coords = EBCoords(i.x(), i.y())
                    coords.restrictToMap()
                    
                    if coords == trigger.coords: # if we didn't move, don't bother updating the map
                        break
                    
                    else:
                        if not isMovingTriggers:
                            isMovingTriggers = True
                            self.scene().undoStack.beginMacro("Move Triggers")
                        
                        i.setPos(coords.x, coords.y)
                        
                        action = ActionMoveTrigger(trigger, coords)
                        self.scene().undoStack.push(action)
                    
                if isMovingTriggers:
                    self.scene().undoStack.endMacro()     
                
                self.scene().parent().sidebarTrigger.fromTriggers()                
    
    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        if self.scene().state.mode == common.MODEINDEX.TRIGGER:
            menu = QMenu()
            menu.addAction("New trigger",
                        lambda: self.scene().newTrigger(EBCoords(event.scenePos().x(), event.scenePos().y())))
            menu.addAction("New &ladder", lambda: self.scene().addTrigger(Trigger(EBCoords(event.scenePos().x(), event.scenePos().y()),
                                                                                TriggerLadder())))
            menu.addAction("New &rope", lambda: self.scene().addTrigger(Trigger(EBCoords(event.scenePos().x(), event.scenePos().y()),
                                                                                TriggerRope())))
            menu.addAction("Delete", self.scene().deleteSelectedTriggers, shortcut=QKeySequence(Qt.Key.Key_Delete))
            menu.addSeparator()
            menu.addAction("Cut", self.scene().onCut)
            menu.addAction("Copy", self.scene().onCopy)
            menu.addAction("Paste", self.scene().onPaste)
            
            menu.exec(event.screenPos())
            super().contextMenuEvent(event)
        
    # for typing
    def scene(self) -> "MapEditorScene":
        return super().scene()

    @classmethod
    def hideTriggers(cls):
        for i in cls.instances:
            i.hide()
    @classmethod
    def showTriggers(cls):
        for i in cls.instances:
            i.show()