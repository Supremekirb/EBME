from io import StringIO

import numpy

import src.misc.common as common
from src.coilsnake.datamodules.data_module import ProjectResourceDataModule
from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords
from src.objects.tile import MapTile


class TileModule(ProjectResourceDataModule):
    NAME = "tiles"
    MODULE = "eb.MapModule"
    RESOURCE = "map_tiles"
    
    def _resourceLoad(data: ProjectData, map_tiles):    
        tileArray = numpy.zeros(shape=[320, 256], dtype=numpy.object_)
        map_tiles = map_tiles.read()

        map_tiles = [r.split(" ") for r in map_tiles.split("\n")]
        if map_tiles[-1] == ['']:
            del map_tiles[-1] # last newline causes issues, so we do this

        map_tiles = numpy.array(map_tiles)

        iterated = numpy.nditer(map_tiles, flags=["multi_index"])

        for i in iterated: # i dont know anymore lol
            x = iterated.multi_index[1]
            y = iterated.multi_index[0]
            coords = EBCoords.fromTile(x, y)
            sector = data.getSector(coords)
            id = int(i.item(), 16)
            assert id in range(0, common.MAXTILES), \
                f"Tile ID {id} out of range (max {common.MAXTILES-1})."
            
            tile = MapTile(id, coords,
                            sector.tileset,
                            sector.palettegroup,
                            sector.palette)
            
            tileArray[iterated.multi_index[0], iterated.multi_index[1]] = tile

        data.tiles = tileArray

    
    def _resourceSave(data: ProjectData):
        map = StringIO()
        for column in data.tiles:
            for row in column:
                map.write(hex(row.tile)[2:].zfill(3))
                map.write(" ")

            offset = map.tell()
            map.seek(offset-1, 0) # remove extra space at end of each row. can't use .seek(-1, 1) because we aren't in byte mode and i dont wanna figure that out
            map.write("\n")
        
        map.seek(0)
        return map