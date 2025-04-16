from src.coilsnake.loadmodules.load_module import YMLCoilsnakeResourceLoadModule
from src.objects.enemy import EnemyMapGroup

class EnemyMapGroupModule(YMLCoilsnakeResourceLoadModule):
    NAME = "enemy map groups"
    MODULE = "eb.MapEnemyModule"
    RESOURCE = "map_enemy_groups"
    
    def _resourceLoad(data, map_enemy_groups):
        enemyMapGroups = []
        for id, group in map_enemy_groups.items():
            if "EBME_Colour" in group:
                colourRaw = group["EBME_Colour"]
                colour = (int(colourRaw[1:3], 16), int(colourRaw[3:5], 16), int(colourRaw[5:7], 16))
            else:
                colour = None
                
            enemyMapGroups.append(EnemyMapGroup(id, group["Event Flag"], colour, group["Sub-Group 1"], group["Sub-Group 2"],
                                                group["Sub-Group 1 Rate"], group["Sub-Group 2 Rate"]))

        data.enemyMapGroups = enemyMapGroups