import numpy

from src.coilsnake.datamodules.data_module import YMLResourceDataModule
from src.misc.coords import EBCoords
from src.objects.enemy import EnemyTile
from src.coilsnake.project_data import ProjectData


class EnemyPlacementsModule(YMLResourceDataModule):
    NAME = "enemy placements"
    MODULE = "eb.MapEnemyModule"
    RESOURCE = "map_enemy_placement"
    FLOW_STYLE = False
    
    def _resourceLoad(data: ProjectData, map_enemy_placement):
        enemyPlacementList = []
        for location, placement in map_enemy_placement.items():
            enemyPlacementList.append(EnemyTile(EBCoords.fromEnemy(int(location%128), int(location//128)),
                                                placement["Enemy Map Group"]))

        enemyArray = numpy.array(enemyPlacementList, dtype=numpy.object_)
        enemyArray = numpy.reshape(enemyArray, (160, 128))
        
        data.enemyPlacements = enemyArray


    def _resourceSave(data: ProjectData):
        placements_yml = {}
        placements_list = data.enemyPlacements.flat
        for i in range(len(placements_list)):
            placements_yml[i] = {
                "Enemy Map Group": placements_list[i].groupID,
            }
        
        return placements_yml