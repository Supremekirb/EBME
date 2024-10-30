from copy import copy

from PySide6.QtGui import QUndoCommand

import src.misc.common as common
from src.coilsnake.fts_interpreter import (FullTileset, Minitile, Palette,
                                           Subpalette, Tile)
from src.objects.palette_settings import PaletteSettings


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
        
        if self._colour == [*self.colour, 255]:
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