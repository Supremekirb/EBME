import logging
import os
import re

from PIL import Image

from src.coilsnake.loadmodules.load_module import YMLCoilsnakeResourceLoadModule
from src.misc.exceptions import CoilsnakeResourceNotFoundError
from src.objects.sprite import Sprite


class SpriteModule(YMLCoilsnakeResourceLoadModule):
    NAME = "sprites"
    MODULE = "eb.SpriteGroupModule"
    RESOURCE = "sprite_groups"
    
    def _resourceLoad(data, sprite_groups):        
        spritesList = []
        for id, spr in sprite_groups.items():
            try:
                sprPath = data.getResourcePath("eb.SpriteGroupModule", f"SpriteGroups/{id:03}")
            except CoilsnakeResourceNotFoundError: # CoilSnake-next projects do not include extra sprite paths in Project.snake
                logging.warning(f"Couldn't find sprite {id:03} in Project.snake, probably a CoilSnake-next project. Trying to load directly...")
                try:
                    sprPath = os.path.normpath(os.path.join(data.dir, "SpriteGroups", f"{id:03}.png"))
                except FileNotFoundError: 
                    logging.warning(f"Couldn't load sprite {id:03} directly!")
                    raise
            
            sizeRaw = spr["Size"]
            size = re.split("x| ", sizeRaw) # there's a "16x16 2" so we need a more robust split. ugh
            size = (int(size[0]), int(size[1]))
            sprImg = Image.open(sprPath).convert("RGBA")
            
            spritesList.append(Sprite(id, size,
                                      (spr["East/West Collision Width"], spr["East/West Collision Height"]),
                                      (spr["North/South Collision Width"], spr["North/South Collision Height"]),
                                      spr["Swim Flags"],
                                      sprImg))
            
        data.sprites = spritesList