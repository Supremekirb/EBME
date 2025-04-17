from src.coilsnake.datamodules.data_module import YMLResourceDataModule
from src.coilsnake.project_data import ProjectData


class EnemySpriteModule(YMLResourceDataModule):
    NAME = "enemy sprites"
    MODULE = "eb.EnemyModule"
    RESOURCE = "enemy_configuration_table"
    
    def _resourceLoad(data: ProjectData, enemy_configuration_table):
        enemySprites = []
        for enemy in enemy_configuration_table.values():       
            enemySprites.append(int(enemy["Overworld Sprite"]))

        data.enemySprites = enemySprites
    
    def save(data: ProjectData):
        return # this data is not saved