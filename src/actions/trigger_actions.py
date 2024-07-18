import logging
from typing import TYPE_CHECKING

from PySide6.QtGui import QUndoCommand

import src.misc.common as common
from src.misc.coords import EBCoords

if TYPE_CHECKING:
    from src.mapeditor.map.map_scene import MapEditorScene
    from src.objects.trigger import (Trigger, TriggerDoor, TriggerEscalator,
                                     TriggerLadder, TriggerObject,
                                     TriggerPerson, TriggerRope,
                                     TriggerStairway, TriggerSwitch)


class ActionMoveTrigger(QUndoCommand):
    def __init__(self, trigger: "Trigger", coords: EBCoords):
        super().__init__()
        self.setText("Move Trigger")

        self.trigger = trigger
        self.coords = coords

        self._coords = trigger.coords
        self.fromSidebar = False
        
    def redo(self):
        self.trigger.coords = self.coords
        
    def undo(self):
        self.trigger.coords = self._coords
        
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.TRIGGERMOVESIDEBAR:
            return False
        # operates on wrong trigger
        if other.trigger != self.trigger:
            return False
        # success
        self.coords = other.coords
        return True
    
    def id(self):
        if self.fromSidebar:
            return common.ACTIONINDEX.TRIGGERMOVESIDEBAR
        else: return common.ACTIONINDEX.TRIGGERMOVE
        
# this should preserve old trigger data too, for switching types
class ActionUpdateTrigger(QUndoCommand):
    def __init__(self, trigger: "Trigger", typeData):
        super().__init__()
        self.setText("Update Trigger")

        self.trigger = trigger
        self.typeData = typeData

        self._typeData = trigger.typeData
        
        self.unmergable = False
        if type(trigger.typeData) != type(typeData):
            self.unmergable = True
        
    def redo(self):
        self.trigger.typeData = self.typeData
        
    def undo(self):
        self.trigger.typeData = self._typeData
        
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.TRIGGERUPDATE:
            return False
        # operates on wrong trigger
        if other.trigger != self.trigger:
            return False
        # changed trigger type, shouldn't merge
        if self.unmergable:
            return False
        # success
        self.typeData = other.typeData
        return True
    
    def id(self):
        return common.ACTIONINDEX.TRIGGERUPDATE
    
class ActionDeleteTrigger(QUndoCommand):
    def __init__(self, trigger: "Trigger", scene: "MapEditorScene"):
        super().__init__()
        self.setText("Delete Trigger")

        self.trigger = trigger
        self.scene = scene
        
    def redo(self):
        item = self.scene.placedTriggersByUUID[self.trigger.uuid]
        if item:
            self.scene.removeItem(item)
            self.scene.placedTriggersByUUID.pop(self.trigger.uuid)
            self.scene.projectData.triggers.remove(self.trigger)
            
    def undo(self):
        ActionAddTrigger.redo(self)
        
    def mergeWith(self, other: QUndoCommand):
        return False

    def id(self):
        return common.ACTIONINDEX.TRIGGERADD
    
class ActionAddTrigger(QUndoCommand):
    def __init__(self, trigger: "Trigger", scene: "MapEditorScene"):
        super().__init__()
        self.setText("Add Trigger")

        self.trigger = trigger
        self.scene = scene
    
    def redo(self):
        import src.objects.trigger as trigger
        placement = trigger.MapEditorTrigger(self.trigger.coords, self.trigger.uuid)
        match type(self.trigger.typeData):
            case trigger.TriggerDoor:
                placement.setPixmap(self.scene.imgTriggerDoor)
            case trigger.TriggerEscalator:
                placement.setPixmap(self.scene.imgTriggerEscalator)
            case trigger.TriggerLadder:
                placement.setPixmap(self.scene.imgTriggerLadder)
            case trigger.TriggerObject:
                placement.setPixmap(self.scene.imgTriggerObject)
            case trigger.TriggerPerson:
                placement.setPixmap(self.scene.imgTriggerPerson)
            case trigger.TriggerRope:
                placement.setPixmap(self.scene.imgTriggerRope)
            case trigger.TriggerStairway:
                placement.setPixmap(self.scene.imgTriggerStairway)
            case trigger.TriggerSwitch:
                placement.setPixmap(self.scene.imgTriggerSwitch)
            case _: # should never happen
                logging.warn(f"Unknown trigger type {self.trigger.typeData}")
                placement.setPixmap(self.scene.imgTriggerDoor)
                
        if not self.trigger in self.scene.projectData.triggers:
            self.scene.projectData.triggers.append(self.trigger)
            
        else:
            logging.warn(f"Can't add a trigger multiple times! (UUID: {self.trigger.uuid})")
            self.setObsolete(True)
            return
        
        if not self.trigger.uuid in self.scene.placedTriggersByUUID:
            self.scene.placedTriggersByUUID[self.trigger.uuid] = placement
            placement.setSelected(True)
            self.scene.addItem(placement)
        else:
            logging.warn(f"Can't add a trigger multiple times! (UUID: {self.trigger.uuid})")
            self.setObsolete(True)
            
    def undo(self):
        ActionDeleteTrigger.redo(self)
        
    def mergeWith(self, other: QUndoCommand):
        return False
    
    def id(self):
        return common.ACTIONINDEX.TRIGGERDELETE
        