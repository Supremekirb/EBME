import numpy

from src.coilsnake.loadmodules.load_module import YMLCoilsnakeResourceLoadModule
from src.objects.sector import Sector


class SectorModule(YMLCoilsnakeResourceLoadModule):
    NAME = "sectors"
    MODULE = "eb.MapModule"
    RESOURCE = "map_sectors"
    
    def _resourceLoad(data, map_sectors):
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