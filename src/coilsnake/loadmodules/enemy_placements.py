import numpy

from src.coilsnake.loadmodules.load_module import YMLCoilsnakeResourceLoadModule
from src.misc.coords import EBCoords
from src.objects.enemy import EnemyTile


class EnemyPlacementsModule(YMLCoilsnakeResourceLoadModule):
    NAME = "enemy placements"
    MODULE = "eb.MapEnemyModule"
    RESOURCE = "map_enemy_placement"
    
    def _resourceLoad(data, map_enemy_placement):
        enemyPlacementList = []
        for location, placement in map_enemy_placement.items():
            enemyPlacementList.append(EnemyTile(EBCoords.fromEnemy(int(location%128), int(location//128)),
                                                placement["Enemy Map Group"]))

        enemyArray = numpy.array(enemyPlacementList, dtype=numpy.object_)
        enemyArray = numpy.reshape(enemyArray, (160, 128))
        
        data.enemyPlacements = enemyArray