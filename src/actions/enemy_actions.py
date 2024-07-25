from PySide6.QtGui import QUndoCommand

import src.misc.common as common
from src.objects.enemy import EnemyTile, EnemyMapGroup

class ActionPlaceEnemyTile(QUndoCommand):
    def __init__(self, enemytile: EnemyTile, group: int):
        super().__init__()
        self.setText("Place enemy tile")

        self.enemytile = enemytile
        self.group = group

        self._group = self.enemytile.groupID
    
    def redo(self):
        self.enemytile.groupID = self.group
        
    def undo(self):
        self.enemytile.groupID = self._group
        
    def mergeWith(self, other: QUndoCommand):
        return False
    
    def id(self):
        return common.ACTIONINDEX.ENEMYTILEPLACE
    
class ActionUpdateEnemyMapGroup(QUndoCommand):
    def __init__(self, group: EnemyMapGroup,
                 flag: int, colour: tuple, subGroup1: dict,
                 subGroup2: dict, subGroup1Rate: int,
                 subGroup2Rate: int):
        super().__init__()
        self.setText("Update enemy map group")
        
        self.group = group
        self.flag = flag
        self.colour = colour
        self.subGroup1 = subGroup1
        self.subGroup2 = subGroup2
        self.subGroup1Rate = subGroup1Rate
        self.subGroup2Rate = subGroup2Rate
        
        self._flag = group.flag
        self._colour = group.colour
        self._subGroup1 = group.subGroup1
        self._subGroup2 = group.subGroup2
        self._subGroup1Rate = group.subGroup1Rate
        self._subGroup2Rate = group.subGroup2Rate
        
    def redo(self):
        self.group.flag = self.flag
        self.group.colour = self.colour
        EnemyMapGroup.colours[self.group.groupID] = self.colour
        self.group.subGroup1 = self.subGroup1
        self.group.subGroup2 = self.subGroup2
        self.group.subGroup1Rate = self.subGroup1Rate
        self.group.subGroup2Rate = self.subGroup2Rate
        
    def undo(self):
        self.group.flag = self._flag
        self.group.colour = self._colour
        EnemyMapGroup.colours[self.group.groupID] = self._colour
        self.group.subGroup1 = self._subGroup1
        self.group.subGroup2 = self._subGroup2
        self.group.subGroup1Rate = self._subGroup1Rate
        self.group.subGroup2Rate = self._subGroup2Rate
        
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.ENEMYMAPGROUPUPDATE:
            return False
        # operates on wrong group
        if other.group != self.group:
            return False
        
        # success
        self.flag = other.flag
        self.colour = other.colour
        self.subGroup1 = other.subGroup1
        self.subGroup2 = other.subGroup2
        self.subGroup1Rate = other.subGroup1Rate
        self.subGroup2Rate = other.subGroup2Rate
        return True
    
    def id(self):
        return common.ACTIONINDEX.ENEMYMAPGROUPUPDATE