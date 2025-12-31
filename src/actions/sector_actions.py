from typing import OrderedDict

from PySide6.QtGui import QUndoCommand

import src.misc.common as common
from src.coilsnake.project_data import ProjectData
from src.objects.sector import Sector
from src.objects.sector_userdata import UserDataType


class ActionChangeSectorAttributes(QUndoCommand):
    def __init__(self, sector: Sector, tileset: int, palettegroup: int, palette: int,
                 item: int, music: int, settings: str, teleport: str, townMap: str,
                 townMapArrow: str, townMapImage: str, townMapX: int, townMapY: int,
                 userdata: dict):
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
        self.userdata = userdata
        
        # Quickly sanitise userdata input to remove any keys that don't belong.
        # This is particularly for copy/paste stuff.
        # (There is still the issue of pasting one data type into another, but... I'm feeling lazy!)
        # TODO deal with pasting one data type into another. Try to validate it?
        for k in self.userdata.keys():
            if k not in Sector.SECTORS_USERDATA.keys():
                self.userdata.pop(k, 0)
        
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
        self._userdata = self.sector.userdata
            
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
        self.sector.userdata = self.userdata
        
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
        self.sector.userdata = self._userdata
        
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
        self.userdata = other.userdata
        return True
    
    def id(self):
        return common.ACTIONINDEX.SECTORATTRUPDATE  


class ActionAddSectorUserDataField(QUndoCommand):
    def __init__(self, name: str, datatype: type[UserDataType]):
        super().__init__()
        self.setText("Add user data field")
        
        self.name = name
        self.datatype = datatype
        
    def redo(self):
        Sector.SECTORS_USERDATA[self.name] = self.datatype
    
    def undo(self):
        Sector.SECTORS_USERDATA.pop(self.name)
        
    def mergeWith(self, other: QUndoCommand):
        return False

    def id(self):
        return common.ACTIONINDEX.USERDATAADDFIELD

class ActionRemoveSectorUserDataField(QUndoCommand):
    def __init__(self, projectData: ProjectData, name: str):
        super().__init__()
        self.setText("Remove user data field")
        
        self.projectData = projectData
        self.name = name
        self.datatype = Sector.SECTORS_USERDATA[self.name]
        self.index = tuple(Sector.SECTORS_USERDATA.keys()).index(self.name)
        
        # We need to also back up the data the sectors are holding onto.
        # It's a little more complex than adding userdata, where we don't need to
        # due to the .get()/.pop() interface with a 0 default being the way to read,
        # so we don't need to provide sectors with initial values.
        # Using a dict here is a small optimisation. Avoid collecting default-value data
        self._data = {}
        for n, i in enumerate(self.projectData.sectors.flat):
            i: Sector
            val = i.userdata.pop(self.name, 0)
            if val != 0:
                self._data[n] = val
        
    def redo(self):
        Sector.SECTORS_USERDATA.pop(self.name)
        # Logically it may seem that it's unecessary to do this whole thing,
        # but it's legal to delete a field and then later re-add another of the same name.
        # In that case, we don't want the old data to show up.
        for i in self.projectData.sectors.flat:
            i: Sector
            i.userdata.pop(self.name, 0)
    
    def undo(self):
        # Preserve insertion order by rebuilding the dict
        data = list(Sector.SECTORS_USERDATA.items())
        data.insert(self.index, (self.name, self.datatype))
        Sector.SECTORS_USERDATA = OrderedDict(data)
        # And reinstate the data that we backed up earlier.
        for n, i in enumerate(self.projectData.sectors.flat):
            i: Sector
            i.userdata[self.name] = self._data.get(n, 0)
        
    def mergeWith(self, other: QUndoCommand):
        return False

    def id(self):
        return common.ACTIONINDEX.USERDATAREMOVEFIELD


class ActionImportSectorUserData(QUndoCommand):
    def __init__(self, projectData: ProjectData, dataFields: OrderedDict[str, type[UserDataType]], sectorsData: list[dict[str, ]]):
        super().__init__()
        self.setText("Add user data field")

        self.projectData = projectData
        self.dataFields = dataFields
        self.sectorsData = sectorsData
        
        self._dataFields = Sector.SECTORS_USERDATA
        
        self._sectorsData = []
        for i in self.projectData.sectors.flat:
            i: Sector
            self._sectorsData.append(i.userdata)

    def redo(self):
        Sector.SECTORS_USERDATA = self.dataFields
        for n, i in enumerate(self.projectData.sectors.flat):
            i: Sector
            i.userdata = self.sectorsData[n]

    def undo(self):
        Sector.SECTORS_USERDATA = self._dataFields
        for n, i in enumerate(self.projectData.sectors.flat):
            i: Sector
            i.userdata = self._sectorsData[n]

    def mergeWith(self, other: QUndoCommand):
        return False

    def id(self):
        return common.ACTIONINDEX.USERDATAIMPORT