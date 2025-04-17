import numpy

from src.coilsnake.datamodules.data_module import YMLResourceDataModule
from src.objects.sector import Sector
from src.coilsnake.project_data import ProjectData


class SectorModule(YMLResourceDataModule):
    NAME = "sectors"
    MODULE = "eb.MapModule"
    RESOURCE = "map_sectors"
    FLOW_STYLE = False
    
    def _resourceLoad(data: ProjectData, map_sectors):
        sectorList = []

        for id, sector in map_sectors.items():
            # the "Tileset" field is actually a palette group
            tileset = data.getTilesetFromPaletteGroup(sector["Tileset"])

            sectorList.append(Sector(id, sector["Item"], sector["Music"], sector["Palette"], sector["Tileset"], tileset.id,
                                        sector["Setting"], sector["Teleport"], sector["Town Map"], sector["Town Map Arrow"],
                                        sector["Town Map Image"], sector["Town Map X"], sector["Town Map Y"]))

        sectorList = [sectorList[i:i+32] for i in range(0,len(sectorList),32)]

        sectorArray = numpy.array(sectorList, dtype=numpy.object_)
        
        data.sectors = sectorArray
    
    
    def _resourceSave(data: ProjectData):
        sector_yml = {}
        for column in data.sectors:
            for s in column:
                sector_yml[s.id] = {
                    "Item": s.item,
                    "Palette": s.palette,
                    "Town Map X": s.townmapx,
                    "Town Map Y": s.townmapy,
                    "Town Map Arrow": s.townmaparrow,
                    "Music": s.music,
                    "Setting": s.setting,
                    "Town Map Image": s.townmapimage,
                    "Town Map": s.townmap,
                    "Teleport": s.teleport,
                    "Tileset": s.palettegroup,
                }
        
        return sector_yml