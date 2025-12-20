from copy import copy

from PySide6.QtGui import QUndoCommand

import src.misc.common as common
from src.actions.sector_actions import ActionChangeSectorAttributes
from src.coilsnake.fts_interpreter import (FullTileset, Minitile, Palette,
                                           PaletteGroup, Subpalette, Tile)
from src.coilsnake.project_data import ProjectData
from src.objects.palette_settings import PaletteSettings
from src.objects.sector import Sector
from src.objects.tile import MapTile, MapTileGraphic


class ActionChangeBitmap(QUndoCommand):
    def __init__(self, minitile: Minitile, bitmap: list[str], isForeground: bool):
        super().__init__()
        self.setText("Draw minitile graphics")
        
        self.isForeground = isForeground
        
        self.minitile = minitile
        self.bitmap = bitmap
        
        if isForeground:
            if self.bitmap == minitile.foreground:
                self.setObsolete(True)
            self._bitmap = copy(minitile.foreground)
        else:
            if self.bitmap == minitile.background:
                self.setObsolete(True)
            self._bitmap = copy(minitile.background)
            
    def redo(self):
        if self.isForeground:
            self.minitile.foreground = self.bitmap
        else:
            self.minitile.background = self.bitmap
            
    def undo(self):
        if self.isForeground:
            self.minitile.foreground = self._bitmap
        else:
            self.minitile.background = self._bitmap
    
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.MINITILEDRAW:
            return False
        # operates on wrong minitile
        if other.minitile != self.minitile:
            return False
        # minitile data isnt the same
        if self.bitmap != other.bitmap:
            return False
        # operates on wrong layer
        if self.isForeground != other.isForeground:
            return False        
        # success
        self.bitmap = other.bitmap
        return True
    
    def id(self):
        return common.ACTIONINDEX.MINITILEDRAW
    
class ActionChangeArrangement(QUndoCommand):
    def __init__(self, tile: Tile, metadata: int, index: int):
        super().__init__()
        self.setText("Change tile arrangement metadata")
        
        self.tile = tile
        self.index = index
        
        self.metadata = metadata
        
        self._metadata = tile.metadata[index]
        
        
    def redo(self):
        self.tile.metadata[self.index] = self.metadata
        
    def undo(self):
        self.tile.metadata[self.index] = self._metadata
    
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.ARRANGEMENTCHANGE:
            return False
        # operates on wrong tile
        if other.tile != self.tile:
            return False
        # operates on wrong index
        if other.index != self.index:
            return False
        # tile metadata isnt the same
        if self.metadata != other.metadata:
            return False
        
        # success
        self.metadata = other.metadata
        return True
    
    def id(self):
        return common.ACTIONINDEX.ARRANGEMENTCHANGE  
    
class ActionChangeCollision(QUndoCommand):
    def __init__(self, tile: Tile, collision: int, index: int):
        super().__init__()
        self.setText("Change tile collision")
        
        self.tile = tile
        self.index = index
        
        self.collision = collision
        
        self._collision = tile.collision[index]
        
        if self.collision == self._collision:
            self.setObsolete(True)
        
    def redo(self):
        self.tile.collision[self.index] = self.collision
        
    def undo(self):
        self.tile.collision[self.index] = self._collision
    
    def mergeWith(self, other: QUndoCommand):
        return False
    
    def id(self):
        return common.ACTIONINDEX.COLLISIONCHANGE

class ActionChangeSubpaletteColour(QUndoCommand):
    def __init__(self, subpalette: Subpalette, index: int, colour: tuple[int, int, int]):
        super().__init__()
        self.setText("Change subpalette colour")
        
        self.subpalette = subpalette
        self.index = index
        
        if index == 0:
            self.alpha = 0
        else: self.alpha = 255
        
        self.colour = colour
        
        self._colour = subpalette.subpaletteRGBA[index]
        
        if self._colour[:3] == self.colour:
            self.setObsolete(True)
        
    def redo(self):
        self.subpalette.subpaletteRGBA[self.index] = (*self.colour, self.alpha)
        
    def undo(self):
        self.subpalette.subpaletteRGBA[self.index] = self._colour
    
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.SUBPALETTECHANGE:
            return False
        # operates on wrong subpalette
        if other.subpalette != self.subpalette:
            return False
        # operates on wrong index
        if other.index != self.index:
            return False
        # colour change isn't the same
        if other.colour != self.colour:
            return False
        
        # success
        self.colour = other.colour
        return True
        
    def id(self):
        return common.ACTIONINDEX.SUBPALETTECHANGE
    
class ActionSwapMinitiles(QUndoCommand):
    def __init__(self, tileset: FullTileset, mt1: int, mt2: int):
        super().__init__()
        self.setText("Swap minitiles")
        
        self.tileset = tileset
        self.mt1 = mt1
        self.mt2 = mt2
        
    def redo(self):
        self.tileset.swapMinitiles(self.mt1, self.mt2)
    
    def undo(self):
        self.redo()
        
    def mergeWith(self, other: QUndoCommand):
        return False

    def id(self):
        return common.ACTIONINDEX.MINITILESWAP
    
class ActionReplacePalette(QUndoCommand):
    def __init__(self, new: Palette, old: Palette):
        super().__init__()
        self.setText("Replace palette")
        
        self.new = new
        self.old = old
        
        self._oldSubpalettes = copy(old.subpalettes)
        
    def redo(self):
        self.old.subpalettes = self.new.subpalettes
    
    def undo(self):
        self.old.subpalettes = self._oldSubpalettes
        
    def mergeWith(self, other: QUndoCommand):
        return False
    
    def id(self):
        return common.ACTIONINDEX.REPLACEPALETTE
    
# not technically fts, but still...
class ActionChangePaletteSettings(QUndoCommand):
    def __init__(self, paletteSettings: PaletteSettings, flag: int, flashEffect: int, spritePalette: int):
        super().__init__()
        self.setText("Change palette settings")
        
        self.paletteSettings = paletteSettings
        
        self.flag = flag
        self.flashEffect = flashEffect
        self.spritePalette = spritePalette
        
        self._flag = paletteSettings.flag
        self._flashEffect = paletteSettings.flashEffect
        self._spritePalette = paletteSettings.spritePalette
        
        if flag == self._flag and \
           flashEffect == self._flashEffect and \
           spritePalette == self._spritePalette:
               self.setObsolete(True)
        
    def redo(self):
        self.paletteSettings.flag = self.flag
        self.paletteSettings.flashEffect = self.flashEffect
        self.paletteSettings.spritePalette = self.spritePalette
        
    def undo(self):
        self.paletteSettings.flag = self._flag
        self.paletteSettings.flashEffect = self._flashEffect
        self.paletteSettings.spritePalette = self._spritePalette
        
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.PALETTESETTINGSUPDATE:
            return False
        # operates on wrong settings
        if other.paletteSettings != self.paletteSettings:
            return False
        # success
        self.flag = other.flag
        self.flashEffect = other.flashEffect
        self.spritePalette = other.spritePalette
        return True

    def id(self):
        return common.ACTIONINDEX.PALETTESETTINGSUPDATE
    
class ActionAddPalette(QUndoCommand):
    def __init__(self, palette: Palette, projectData: ProjectData):
        # quite a big one. we will need the ProjectData because we need to deal with a lot of stuff
        
        super().__init__()
        self.setText("Add palette")
        
        self.palette = palette
        self.projectData = projectData
        
    def redo(self):
        tileset = self.projectData.getTilesetFromPaletteGroup(self.palette.groupID)
        tileset.palettes.append(self.palette)
        tileset.palettes.sort(key=lambda p: (p.groupID, p.paletteID))
        paletteGroup = tileset.getPaletteGroup(self.palette.groupID)
        paletteGroup.palettes.append(self.palette)
        paletteGroup.palettes.sort(key=lambda p: p.paletteID)
        
        settings = PaletteSettings(0, 0, 0)
        self.projectData.paletteSettings[self.palette.groupID][self.palette.paletteID] = settings
        
        for key, t in self.projectData.tilegfx.items():
            t[common.combinePaletteAndGroup(self.palette.groupID, self.palette.paletteID)] = {}
        
            # for i in range(common.MAXTILES):
            #     graphic = MapTileGraphic(i, key, self.palette.groupID, self.palette.paletteID)
            #     t[common.combinePaletteAndGroup(self.palette.groupID, self.palette.paletteID)][i] = graphic
    
    def undo(self):   
        tileset = self.projectData.getTilesetFromPaletteGroup(self.palette.groupID)
        tileset.palettes.remove(self.palette)
        tileset.getPaletteGroup(self.palette.groupID).palettes.remove(self.palette)
        
        self.projectData.paletteSettings[self.palette.groupID].pop(self.palette.paletteID, None)
        
        for t in self.projectData.tilegfx.values():
            keys = list(t.keys())
            for key in keys:
                if key == common.combinePaletteAndGroup(self.palette.groupID, self.palette.paletteID):
                    t.pop(key, None)
                   
    def mergeWith(self, other):
        return False

    def id(self):
        return common.ACTIONINDEX.ADDPALETTE
    
class ActionRemovePalette(QUndoCommand):
    def __init__(self, palette: Palette, projectData: ProjectData):
        super().__init__()
        self.setText("Remove palette")
        
        self.palette = palette
        self.projectData = projectData

        # truth be told I was hoping for a rather elegant undo/redo swap of ActionAddPalette but no dice
        # the nice thing about making them separate is that we only have to verify stuff for this action specifically
        
        # verification of objects using this palette
        # objects using this palette will be set to use palette 0
        # BIT OF CONTEX TIME
        # Qt does provide a command parenting system, where all children are also undone/redone
        # however!
        # some strange issue is causing it to not like... something about what I've done here
        # and crash the entire program (yikes!)
        # This specifically happens in the QUndoStack.push() function after
        # 1. deleting a palette 2. undoing 3. deleting it again with a new action
        # Since this seems to be both a Qt issue and a C++ issue, (probably something with pointers)
        # and I can't really debug, I hereby give up.
        # and now similar functionality to MultiActionWrapper will take its place.
        # it works, okay?!
        self.commands: list[QUndoCommand] = []
        
        for i in self.projectData.sectors.flat:
            i: Sector
            if i.palettegroup == self.palette.groupID and i.palette == self.palette.paletteID:
                self.commands.append(ActionChangeSectorAttributes(
                    i, i.tileset, i.palettegroup,
                    self.projectData.getTileset(i.tileset).getPaletteGroup(
                    i.palettegroup).palettes[0].paletteID,
                    i.item, i.music, i.setting, i.teleport,
                    i.townmap, i.townmaparrow, i.townmapimage,
                    i.townmapx, i.townmapy))
                
        # change things using palettes past this ID to use ID -1
        # (don't actually apply the change here, only create actions)
        palettes = self.projectData.getPaletteGroup(palette.groupID).palettes
        for i in palettes:
            self.test = i
            if i.paletteID > palette.paletteID:
                # for sectors
                for j in self.projectData.sectors.flat:
                    j: Sector
                    if j.palette == i.paletteID and j.palettegroup == i.groupID:
                        self.commands.append(ActionChangeSectorAttributes(
                            j, j.tileset, j.palettegroup, j.palette-1, # <-- the important bit
                            j.item, j.music, j.setting, j.teleport,
                            j.townmap, j.townmaparrow, j.townmapimage,
                            j.townmapx, j.townmapy))
                        
                
        # for palette settings
        # TODO currently nonfunctional -- need actions for adding/removing event palettes first!
        # for id, settings in self.projectData.paletteSettings[palette.groupID].items():
        #     if id > palette.paletteID:
        #         self.childActions.append(ActionChangePaletteSettings(
        #             self.projectData.paletteSettings[i.groupID][id-1],
        #             settings.flag,
        #             settings.flashEffect,
        #             settings.spritePalette))
        #
        #         eventPalette = settings.palette
        #         previousEventPalette = self.projectData.paletteSettings[palette.groupID][id-1].palette
        #         if eventPalette and previousEventPalette:
        #             for subpalette in range(0, 6):
        #                 for colour in range(0, 16):
        #                     self.childActions.append(ActionChangeSubpaletteColour(previousEventPalette.subpalettes[subpalette],
        #                         colour, eventPalette.subpalettes[subpalette].subpaletteRGBA[colour][:3]))
        #             # we can safely ... ignore leaving one extra palette settings :3
        
    def redo(self):
        tileset = self.projectData.getTilesetFromPaletteGroup(self.palette.groupID)
        paletteGroup = self.projectData.getPaletteGroup(self.palette.groupID)
        # first let's shift all the other palettes down by one
        # do this first to make sure nothing happens with child actions I guess?
        # not that anything should
        for i in paletteGroup.palettes:
            if i.paletteID > self.palette.paletteID:
                i.paletteID -= 1
        
        for i in self.commands:
            i.redo()
            
        tileset.palettes.remove(self.palette)
        tileset.palettes.sort(key=lambda p: p.paletteID) # probably not necessary, but why not
        paletteGroup.palettes.remove(self.palette)
        paletteGroup.palettes.sort(key=lambda p: p.paletteID)
        
        self.projectData.clobberTileGraphicsCache(tileset.id, paletteGroup.groupID)
            
    def undo(self):
        tileset = self.projectData.getTilesetFromPaletteGroup(self.palette.groupID)
        paletteGroup = self.projectData.getPaletteGroup(self.palette.groupID)
        # shift palettes back up again
        for i in paletteGroup.palettes:
            if i.paletteID >= self.palette.paletteID:
                i.paletteID += 1

        for i in self.commands:
            i.undo()
        
        tileset.palettes.append(self.palette)
        tileset.palettes.sort(key=lambda p: p.paletteID)
        paletteGroup.palettes.append(self.palette)
        paletteGroup.palettes.sort(key=lambda p: p.paletteID)
        
        self.projectData.clobberTileGraphicsCache(tileset.id, paletteGroup.groupID)
            
    def mergeWith(self, other):
        return False
    
    def id(self):
        return common.ACTIONINDEX.REMOVEPALETTE
    
    
class ActionAddPaletteSettingsChild(QUndoCommand):
    def __init__(self, settings: PaletteSettings, parent: PaletteSettings):
        super().__init__()
        self.setText("Add palette settings child")
        
        assert settings.palette != None, "Child settings must have palette! Something has gone wrong!"
        
        self.settings = settings
        self.parent = parent
        
        self._settings = parent.child
        
    def redo(self):
        self.parent.child = self.settings 
    
    def undo(self): # should always be None...?
        self.parent.child = self._settings

    def mergeWith(self, other):
        return False

    def id(self):
        return common.ACTIONINDEX.ADDPALETTESETTINGSCHILD

class ActionRemovePaletteSettingsChild(QUndoCommand):
    def __init__(self, parent: PaletteSettings, top: PaletteSettings):
        super().__init__()
        self.setText("Remove palette settings children")
        
        self.parent = parent
        self.top = top
        
        self._settings = parent.child
        
        if self._settings == None:
            self.setObsolete(True)
        
    def redo(self):
        # manage reparenting
        children = []
        settings = self.top
        while settings.child:
            children.append(settings.child)
            settings = settings.child
        
        for index, i in enumerate(children):
            if i == self.parent.child:
                try:
                    self.parent.child = children[index+1]
                    break
                except IndexError: # nothing is able to be reparented
                    pass
        else: # fallback
            self.parent.child = None 
    
    def undo(self):
        self.parent.child = self._settings

    def mergeWith(self, other):
        return False

    def id(self):
        return common.ACTIONINDEX.REMOVEPALETTESETTINGSCHILD