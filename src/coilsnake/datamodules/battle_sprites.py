import glob
import os

from PIL import Image, ImageQt

import src.misc.common as common
from src.coilsnake.datamodules.data_module import DataModule
from src.coilsnake.project_data import ProjectData
from src.misc.exceptions import SubResourceNotFoundError
from src.objects.sprite import BattleSprite


class BattleSpriteModule(DataModule):
    NAME = "battle sprites"
    
    def load(data: ProjectData):
        battleSprites = {}
        
        if data.isFeatureAvailable(common.COILSNAKEFEATUREIDS.DEPRECATEFILEMAPPINGS):
            for path in glob.glob(os.path.join(data.dir, "BattleSprites", "*.png")):
                filename = os.path.split(path)[1]
                # Valid files take the pattern: ###.png, where ### is numeric
                # Glob covers checking for the png extension
                if len(filename) == 7 and filename[:3].isnumeric():
                    sprImg = ImageQt.ImageQt(Image.open(path))
                    id = int(filename[:3])
                    battleSprites[id] = BattleSprite(id, sprImg)
                    
        else:
            for key in data.projectSnake["resources"]["eb.EnemyModule"].keys():
                path = data.getResourcePath("eb.EnemyModule", key)
                if str(key).split("/")[0] == "BattleSprites": # cursed but i dont know how else
                    try:
                        sprImg = ImageQt.ImageQt(Image.open(path).convert("RGBA"))
                    except FileNotFoundError:
                        raise SubResourceNotFoundError(f"Couldn't find battle sprite at {path}")
                    id = int(str(key).split("/")[1]) # also cursed
                    battleSprites[id] = BattleSprite(id, sprImg)

        data.battleSprites = battleSprites
    
    def save(data: ProjectData):
        return # this data is not saved