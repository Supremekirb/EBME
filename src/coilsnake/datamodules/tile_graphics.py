import src.misc.common as common
from src.coilsnake.datamodules.data_module import DataModule
from src.coilsnake.project_data import ProjectData
from src.objects.tile import MapTileGraphic


class TileGraphicsModule(DataModule):
    NAME = "tile graphics"
    
    def load(data: ProjectData):
        tilegfx = {}
        
        keys = []
        for t in data.tilesets:
            for g in t.paletteGroups:
                for p in g.palettes:
                    keys.append(common.combinePaletteAndGroup(g.groupID, p.paletteID))
        
        for t in data.tilesets:
            tilegfx[t.id] = {}
            for pg in keys:
                tilegfx[t.id][pg] = {}
                for mt in range(common.MAXTILES):
                    tilegfx[t.id][pg][mt] = MapTileGraphic(mt, t.id, *common.extractPaletteAndGroup(pg))

        data.tilegfx = tilegfx
    
    
    def save(data: ProjectData):
        return # this data is not saved