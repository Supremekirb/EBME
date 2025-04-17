from src.coilsnake.datamodules.data_module import YMLResourceDataModule
from src.coilsnake.project_data import ProjectData
from src.objects.enemy import EnemyGroup


class EnemyGroupModule(YMLResourceDataModule):
    NAME = "enemy groups"
    MODULE = "eb.EnemyModule"
    RESOURCE = "enemy_groups"
    
    def _resourceLoad(data: ProjectData, enemy_groups):
        enemyGroups = []
        for id, group in enemy_groups.items():
            enemyGroups.append(EnemyGroup(id, group["Background 1"], group["Background 2"], group["Enemies"],
                                            group["Fear event flag"], group["Fear mode"], group["Letterbox Size"]))

        data.enemyGroups = enemyGroups
        
    def save(data: ProjectData):
        return # this data is not saved