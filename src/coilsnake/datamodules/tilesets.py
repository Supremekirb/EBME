import glob
import os
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
        
        if data.isFeatureAvailable(common.COILSNAKEFEATUREIDS.DEPRECATEFILEMAPPINGS):
            fts_files = glob.glob(os.path.join(data.dir, "Tilesets", "*.fts"))
            fts_files.sort()
            last_id = 0
            # FTS filenames take the format ##.fts, where ## is numeric.
            # I'm not sure strictly how true this is, but I'm going to be enforcing a continuous list of IDs.
            # Beacuse I will have to refactor a lot otherwise!
            for path in fts_files:
                file = os.path.split(path)[1]
                name = file.split(".fts")[0]
                if len(name) != 2 or not name.isnumeric(): continue # Not a validly-named FTS
                id = int(name)
                if id < last_id:
                    raise RuntimeError("FTS filename numbers are not continuous. Please ensure none are skipped.")
                last_id = id
                
            for id, path in enumerate(fts_files):
                with openCoilsnakeResource("eb.TilesetModule", f"Tilesets/{id:02d}", path, "r", data) as fts:
                    tilesetList.append(FullTileset(contents=fts.readlines(), id=id))
        
        else:
            for i in data.projectSnake["resources"]["eb.TilesetModule"].keys():
                if not i.startswith("Tilesets/"):
                    continue
                id = int(i.split("/")[-1])
                with openCoilsnakeResource("eb.TilesetModule", str(i), f"Tilesets/{id:02d}", "r", data) as fts:
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
            with openCoilsnakeResource("eb.TilesetModule", f"Tilesets/{i:02d}", f"Tilesets/{i:02d}.fts", "w", data) as file:
                shutil.copyfileobj(fts, file)