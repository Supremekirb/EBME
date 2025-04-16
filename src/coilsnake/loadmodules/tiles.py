import numpy

import src.misc.common as common
from src.coilsnake.loadmodules.load_module import CoilsnakeResourceLoadModule
from src.misc.coords import EBCoords
from src.objects.tile import MapTile


class TileModule(CoilsnakeResourceLoadModule):
    NAME = "tiles"
    MODULE = "eb.MapModule"
    RESOURCE = "map_tiles"
    
    def _resourceLoad(data, map_tiles):    
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