from src.coilsnake.loadmodules.load_module import YMLCoilsnakeResourceLoadModule
from src.objects.enemy import EnemyGroup

class EnemyGroupModule(YMLCoilsnakeResourceLoadModule):
    NAME = "enemy groups"
    MODULE = "eb.EnemyModule"
    RESOURCE = "enemy_groups"
    
    def _resourceLoad(data, enemy_groups):
        enemyGroups = []
        for id, group in enemy_groups.items():
            enemyGroups.append(EnemyGroup(id, group["Background 1"], group["Background 2"], group["Enemies"],
                                            group["Fear event flag"], group["Fear mode"], group["Letterbox Size"]))

        data.enemyGroups = enemyGroups