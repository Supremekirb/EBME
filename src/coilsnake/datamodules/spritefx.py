from PIL import ImageQt

from src.coilsnake.datamodules.data_module import DataModule
from src.coilsnake.project_data import ProjectData
from src.objects.sprite import Sprite


class SpriteFXModule(DataModule):
    NAME = "sprite effects"
    
    def load(data: ProjectData):
        ripple_small = ImageQt.ImageQt(data.getSprite(348).renderFacingImg(0, 0))
        ripple_large = ImageQt.ImageQt(data.getSprite(349).renderFacingImg(0, 0))
        
        data._ripple_small = ripple_small
        data._ripple_large = ripple_large
    
    def save(data: ProjectData):
        return # this data is not saved