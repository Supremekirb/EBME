from src.coilsnake.datamodules.data_module import YMLResourceDataModule
from src.coilsnake.project_data import ProjectData
from src.objects.enemy import EnemyMapGroup


class EnemyMapGroupModule(YMLResourceDataModule):
    NAME = "enemy map groups"
    MODULE = "eb.MapEnemyModule"
    RESOURCE = "map_enemy_groups"
    FLOW_STYLE = None
    
    def _resourceLoad(data: ProjectData, map_enemy_groups):
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


    def _resourceSave(data: ProjectData):
        groups_yml = {}
        for i in data.enemyMapGroups:
            subGroup1 = {}
            for id, values in i.subGroup1.items():
                if values["Enemy Group"] == 0 and values["Probability"] == 0:
                    continue
                else:
                    subGroup1[id] = values
                    
            subGroup2 = {}
            for id, values in i.subGroup2.items():
                if values["Enemy Group"] == 0 and values["Probability"] == 0:
                    continue
                else:
                    subGroup2[id] = values
            
            groups_yml[data.enemyMapGroups.index(i)] = {
                "Event Flag": i.flag,
                "Sub-Group 1": subGroup1,
                "Sub-Group 1 Rate": i.subGroup1Rate,
                "Sub-Group 2": subGroup2,
                "Sub-Group 2 Rate": i.subGroup2Rate,
                "EBME_Colour": "#{0:02x}{1:02x}{2:02x}".format(i.colour[0], i.colour[1], i.colour[2])
            }
        
        return groups_yml