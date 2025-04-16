from src.coilsnake.fts_interpreter import FullTileset
from src.coilsnake.loadmodules.load_module import LoadModule
from src.coilsnake.resource_manager import openCoilsnakeResource


class TilesetModule(LoadModule):
    NAME = "tilesets"
    
    def load(data):
        tilesetList = []
        for i in data.projectSnake["resources"]["eb.TilesetModule"].keys():
            if not i.startswith("Tilesets/"):
                continue
            id = int(i.split("/")[-1])
            with openCoilsnakeResource("eb.TilesetModule", str(i), "r", data) as fts:
                tilesetList.append(FullTileset(contents=fts.readlines(), id=id))
                
        data.tilesets = tilesetList