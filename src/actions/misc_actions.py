from PySide6.QtGui import QUndoCommand

import src.misc.common as common
from src.coilsnake.fts_interpreter import FullTileset
from src.coilsnake.project_data import ProjectData


class MultiActionWrapper(QUndoCommand):
    """Submit a list of commands, and execute them as a single action.
    The benefit of this over a simple QUndoCommand is that it allows for merging of actions.
    This is done by checking if every child can merge with the children of the merged command,
    and if they can, then merge them all in one go."""
    # hackiness level: high
    # p. much only used for merging multi-select edits from the sidebars into one
    def __init__(self, commands: list[QUndoCommand] = None, text: str=None):
        super().__init__()
        if commands is None:
            self.commands = []
        else: self.commands = commands
        
        if text is None:
            self.textOverridden = False
            super().setText(f"{len(self.commands)} action(s)")
        else:
            self.setText(text)
                
    def redo(self):
        for c in self.commands:
            c.redo()
            
    def undo(self):
        for c in self.commands:
            c.undo()
            
    def addCommand(self, command: QUndoCommand):
        self.commands.append(command)
        if not self.textOverridden:
            super().setText(f"{len(self.commands)} action(s)")
        
    def setText(self, text: str):
        self.textOverridden = True
        super().setText(text)
            
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.MULTI:
            return False
        
        # can't merge children
        for c, o in zip(self.commands, other.commands):
            if not c.mergeWith(o):
                return False
            
        # success
        return True
    
    def id(self):
        return common.ACTIONINDEX.MULTI

# Effectively just for png2fts, but I'll build it
# to be a generic "replace tileset" for the sake of future me
# TODO -- this (or rather, ProjectData.replaceTileset) still has the "assume one palette, merge the rest" behaviour. It can be fixed, but not easily! Necessary for truly generic function.
class ActionReplaceTileset(QUndoCommand):
    def __init__(self, tileset: FullTileset, projectData: ProjectData):
        super().__init__()
        self.setText("Import tileset")
        
        self.projectData = projectData
        
        self.tileset = tileset
        self.index = self.tileset.id
        
        self._tileset = self.projectData.getTileset(self.index)
    
    def redo(self):
        self.projectData.replaceTileset(self.tileset)
    
    def undo(self):
        self.projectData.replaceTileset(self._tileset)
    
    def mergeWith(self, other):
        return False
    
    def id(self):
        return common.ACTIONINDEX.REPLACETILESET