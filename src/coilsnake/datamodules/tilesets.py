import shutil
from src.coilsnake.datamodules.data_module import DataModule
from src.coilsnake.fts_interpreter import FullTileset
from src.coilsnake.project_data import ProjectData
from src.coilsnake.resource_manager import openCoilsnakeResource
from io import StringIO
import src.misc.common as common


class TilesetModule(DataModule):
    NAME = "tilesets"
    
    def load(data: ProjectData):
        tilesetList = []
        for i in data.projectSnake["resources"]["eb.TilesetModule"].keys():
            if not i.startswith("Tilesets/"):
                continue
            id = int(i.split("/")[-1])
            with openCoilsnakeResource("eb.TilesetModule", str(i), "r", data) as fts:
                tilesetList.append(FullTileset(contents=fts.readlines(), id=id))
                
        data.tilesets = tilesetList
    
    
    def save(data: ProjectData):
        files = []
        
        for i in data.tilesets:
            fts_file = StringIO()
            for m in i.minitiles:               
                fts_file.write(m.bgToRaw() + "\n")
                fts_file.write(m.fgToRaw() + "\n")
                fts_file.write("\n")
            
            fts_file.write("\n")

            # TODO
            # Ensure that the sorting of this is
            # correct (PG, P) before saving.
            # This can cause issues on the next load.
            for p in i.palettes:
                fts_file.write(p.toRaw())
                fts_file.write("\n")
            
            fts_file.write("\n\n")

            for t in i.tiles:
                fts_file.write(t.toRaw())
                fts_file.write("\n")

            for _ in range(common.MAXTILES, 1024):
                # bunch of empty tiles needed
                fts_file.write("000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000\n")

            fts_file.seek(0)
            files.append(fts_file)
        
        for i, fts in enumerate(files):
            with openCoilsnakeResource("eb.TilesetModule", f"Tilesets/{i:02d}", "w", data) as file:
                shutil.copyfileobj(fts, file)