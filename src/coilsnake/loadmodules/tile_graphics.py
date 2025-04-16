import src.misc.common as common
from src.coilsnake.loadmodules.load_module import LoadModule
from src.objects.tile import MapTileGraphic


class TileGraphicsModule(LoadModule):
    NAME = "tile graphics"
    
    def load(data):
        tilegfx = {}
        for t in data.tilesets:
            tilegfx[t.id] = {}
            for g in t.paletteGroups:
                tilegfx[t.id][g.groupID] = {}
                for p in g.palettes:
                    tilegfx[t.id][g.groupID][p.paletteID] = {}
                    for mt in range(common.MAXTILES):
                        tilegfx[t.id][g.groupID][p.paletteID][mt] = MapTileGraphic(mt, t.id, g.groupID, p.paletteID)

        data.tilegfx = tilegfx