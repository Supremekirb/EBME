import src.misc.common as common
from src.coilsnake.datamodules.data_module import DataModule
from src.coilsnake.project_data import ProjectData
from src.objects.tile import MapTileGraphic


class TileGraphicsModule(DataModule):
    NAME = "tile graphics"
    
    def load(data: ProjectData):
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
    
    
    def save(data: ProjectData):
        return # this data is not saved