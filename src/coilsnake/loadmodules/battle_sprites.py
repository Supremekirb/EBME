from PIL import Image, ImageQt

from src.coilsnake.loadmodules.load_module import LoadModule
from src.coilsnake.project_data import ProjectData
from src.objects.sprite import BattleSprite


class BattleSpriteModule(LoadModule):
    NAME = "battle sprites"
    
    def load(data: ProjectData):
        battleSprites = []
        for key in data.projectSnake["resources"]["eb.EnemyModule"].keys():
            path = data.getResourcePath("eb.EnemyModule", key)
            if str(key).split("/")[0] == "BattleSprites": # cursed but i dont know how else
                sprImg = ImageQt.ImageQt(Image.open(path).convert("RGBA"))
                battleSprites.append(BattleSprite(int(str(key).split("/")[1]), sprImg)) # also cursed

        data.battleSprites = battleSprites