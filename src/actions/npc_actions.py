import logging
from typing import TYPE_CHECKING

from PIL import ImageQt
from PySide6.QtGui import QPixmap, QUndoCommand

import src.misc.common as common
from src.misc.coords import EBCoords

if TYPE_CHECKING:
    from src.coilsnake.project_data import ProjectData
    from src.mapeditor.map.map_scene import MapEditorScene
    from src.objects.npc import NPC, NPCInstance


class ActionMoveNPCInstance(QUndoCommand):
    def __init__(self, instance: "NPCInstance", coords: EBCoords, parent=None):
        super().__init__(parent)
        self.setText("Move NPC")

        coords.restrictToMap()

        self.instance = instance
        self.coords = coords

        self._coords = instance.coords

        self.fromSidebar = False 

    def redo(self):
        self.instance.coords = self.coords

    def undo(self):
        self.instance.coords = self._coords

    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.NPCMOVESIDEBAR:
            return False
        # operates on wrong NPC
        if other.instance != self.instance:
            return False
        # success
        self.coords = other.coords
        return True

    def id(self):
        if self.fromSidebar:
            return common.ACTIONINDEX.NPCMOVESIDEBAR
        else:
            return common.ACTIONINDEX.NPCMOVE

class ActionChangeNPCInstance(QUndoCommand):
    def __init__(self, instance: "NPCInstance", npc: int):
        super().__init__()
        self.setText("Change NPC instance")

        self.instance = instance
        self.npc = npc

        self._npc = instance.npcID
    
    def redo(self):
        self.instance.npcID = self.npc

    def undo(self):
        self.instance.npcID = self._npc

    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.NPCCHANGE:
            return False
        # operates on wrong NPC
        if other.instance != self.instance:
            return False
        # success
        self.npc = other.npc
        return True
    
    def id(self):
        return common.ACTIONINDEX.NPCCHANGE

class ActionDeleteNPCInstance(QUndoCommand):
    def __init__(self, instance: "NPCInstance", scene: "MapEditorScene"):
        super().__init__()
        self.setText("Delete NPC instance")

        self.instance = instance
        self.scene = scene

    def redo(self):
        item = self.scene.placedNPCsByUUID[self.instance.uuid]
        if item:
            self.scene.removeItem(item) # this specific function is slow, is there a better way? probably not
            self.scene.placedNPCsByUUID.pop(self.instance.uuid)
            self.scene.placedNPCsByID[self.instance.npcID].remove(item)
            self.scene.projectData.npcinstances.remove(self.instance)
        
    def undo(self):
        ActionAddNPCInstance.redo(self)
        
    def mergeWith(self, other: QUndoCommand):
        return False

    def id(self):
        return common.ACTIONINDEX.NPCDELETE
    
class ActionAddNPCInstance(QUndoCommand):
    def __init__(self, instance: "NPCInstance", scene: "MapEditorScene"):
        super().__init__()
        self.setText("Add NPC instance")

        self.instance = instance
        self.scene = scene

    def redo(self):
        from src.objects.npc import \
            MapEditorNPC  # i dont like it either but it's necessary
        npc = self.scene.projectData.getNPC(self.instance.npcID)
        spr = self.scene.projectData.getSprite(npc.sprite)
        inst = MapEditorNPC(self.instance.coords, self.instance.npcID, self.instance.uuid, spr)
        inst.setFacing(common.DIRECTION8[npc.direction])

        # TODO this would be better as a set instead of a list
        if not self.instance in self.scene.projectData.npcinstances:
            self.scene.projectData.npcinstances.append(self.instance)
        
        else:
            logging.warning(f"Can't add an instance multiple times! (UUID: {self.instance.uuid}, NPC ID: {self.instance.npcID})")
            self.setObsolete(True)
            return
            
        if not self.instance.npcID in self.scene.placedNPCsByID:
            self.scene.placedNPCsByID[self.instance.npcID] = [inst,]
        else:
            self.scene.placedNPCsByID[self.instance.npcID].append(inst)

        if not self.instance.uuid in self.scene.placedNPCsByUUID:
            self.scene.placedNPCsByUUID[self.instance.uuid] = inst
            inst.setSelected(True)
            self.scene.addItem(inst)
        else:
            logging.warning(f"Can't add an instance multiple times! (ID: {self.instance.uuid}, NPC ID: {self.instance.npcID})")
            self.setObsolete(True)

    def undo(self):
        ActionDeleteNPCInstance.redo(self) # does this just work???
        
    def mergeWith(self, other: QUndoCommand):
        return False

    def id(self):
        return common.ACTIONINDEX.NPCADD
    
class ActionUpdateNPC(QUndoCommand):
    def __init__(self, npc: "NPC", sprite: int,
                 direction: str, movement: int,
                 flag: int, show: str,
                 text1: str, text2: str,
                 type: str, comment: str,
                 parent=None):
        super().__init__(parent)
        self.setText("Update NPC")

        self.npc = npc
        self.sprite = sprite
        self.direction = direction
        self.movement = movement
        self.flag = flag
        self.show = show
        self.text1 = text1
        self.text2 = text2
        self.type = type
        self.comment = comment

        self._sprite = npc.sprite
        self._direction = npc.direction
        self._movement = npc.movement
        self._flag = npc.flag
        self._show = npc.show
        self._text1 = npc.text1
        self._text2 = npc.text2
        self._type = npc.type
        self._comment = npc.comment

    def redo(self):
        self.npc.sprite = self.sprite
        self.npc.direction = self.direction
        self.npc.movement = self.movement
        self.npc.flag = self.flag
        self.npc.show = self.show
        self.npc.text1 = self.text1
        self.npc.text2 = self.text2
        self.npc.type = self.type
        self.npc.comment = self.comment

    def undo(self):
        self.npc.sprite = self._sprite
        self.npc.direction = self._direction
        self.npc.movement = self._movement
        self.npc.flag = self._flag
        self.npc.show = self._show
        self.npc.text1 = self._text1
        self.npc.text2 = self._text2
        self.npc.type = self._type
        self.npc.comment = self._comment
    
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.NPCUPDATE:
            return False
        # operates on wrong NPC
        if other.npc != self.npc:
            return False
        # success
        self.sprite = other.sprite
        self.direction = other.direction
        self.movement = other.movement
        self.flag = other.flag
        self.show = other.show
        self.text1 = other.text1
        self.text2 = other.text2
        self.type = other.type
        self.comment = other.comment
        return True
    
    def id(self):
        return common.ACTIONINDEX.NPCUPDATE
    

class ActionCreateNPC(QUndoCommand):
    def __init__(self, projectData: "ProjectData", npc: "NPC"):
        super().__init__()
        self.setText("Create new NPC")
        
        self.projectData = projectData
        self.npc = npc
        
        if len(self.projectData.npcs) >= 3855:
            common.showErrorMsg("Could not create NPC",
                                "The maximum number of NPCs is 3855.")
            raise RuntimeError("Maximum number of NPCs reached.")
    
    def redo(self):
        self.projectData.npcs.append(self.npc)
    
    def undo(self):
        self.projectData.npcs.pop()
    
    def mergeWith(self, other):
        return False

    def id(self):
        return common.ACTIONINDEX.NPCCREATE