from PySide6.QtGui import QUndoCommand

import src.misc.common as common
from src.objects.sector import Sector

class ActionChangeSectorAttributes(QUndoCommand):
    def __init__(self, sector: Sector, tileset: int, palettegroup: int, palette: int,
                 item: int, music: int, settings: str, teleport: str, townMap: str,
                 townMapArrow: str, townMapImage: str, townMapX: int, townMapY: int):
        super().__init__()
        self.setText("Change sector attributes")
        
        self.sector = sector
        self.tileset = tileset
        self.palettegroup = palettegroup
        self.palette = palette
        self.item = item
        self.music = music
        self.settings = settings
        self.teleport = teleport
        self.townMap = townMap
        self.townMapArrow = townMapArrow
        self.townMapImage = townMapImage
        self.townMapX = townMapX
        self.townMapY = townMapY
        
        self._tileset = self.sector.tileset
        self._palettegroup = self.sector.palettegroup
        self._palette = self.sector.palette
        self._item = self.sector.item
        self._music = self.sector.music
        self._settings = self.sector.setting
        self._teleport = self.sector.teleport
        self._townMap = self.sector.townmap
        self._townMapArrow = self.sector.townmaparrow
        self._townMapImage = self.sector.townmapimage
        self._townMapX = self.sector.townmapx
        self._townMapY = self.sector.townmapy
            
    def redo(self):
        self.sector.tileset = self.tileset
        self.sector.palettegroup = self.palettegroup
        self.sector.palette = self.palette
        self.sector.item = self.item
        self.sector.music = self.music
        self.sector.setting = self.settings
        self.sector.teleport = self.teleport
        self.sector.townmap = self.townMap
        self.sector.townmaparrow = self.townMapArrow
        self.sector.townmapimage = self.townMapImage
        self.sector.townmapx = self.townMapX
        self.sector.townmapy = self.townMapY
        
    def undo(self):
        self.sector.tileset = self._tileset
        self.sector.palettegroup = self._palettegroup
        self.sector.palette = self._palette
        self.sector.item = self._item
        self.sector.music = self._music
        self.sector.setting = self._settings
        self.sector.teleport = self._teleport
        self.sector.townmap = self._townMap
        self.sector.townmaparrow = self._townMapArrow
        self.sector.townmapimage = self._townMapImage
        self.sector.townmapx = self._townMapX
        self.sector.townmapy = self._townMapY
        
    def mergeWith(self, other: QUndoCommand):
        # wrong action type
        if other.id() != common.ACTIONINDEX.SECTORATTRUPDATE:
            return False
        # operates on wrong sector
        if other.sector != self.sector:
            return False
        # success
        self.tileset = other.tileset
        self.palettegroup = other.palettegroup
        self.palette = other.palette
        self.item = other.item
        self.music = other.music
        self.settings = other.settings
        self.teleport = other.teleport
        self.townMap = other.townMap
        self.townMapArrow = other.townMapArrow
        self.townMapImage = other.townMapImage
        self.townMapX = other.townMapX
        self.townMapY = other.townMapY
        return True
    
    def id(self):
        return common.ACTIONINDEX.SECTORATTRUPDATE  
        