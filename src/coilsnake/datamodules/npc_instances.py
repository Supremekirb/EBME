from src.coilsnake.datamodules.data_module import YMLResourceDataModule
from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords
from src.objects.npc import NPCInstance


class NPCInstanceModule(YMLResourceDataModule):
    NAME = "NPC instances"
    MODULE = "eb.MapSpriteModule"
    RESOURCE = "map_sprites"
    FLOW_STYLE = None
    
    def _resourceLoad(data: ProjectData, map_sprites):        
        npcInstanceList = []
        for y, row in map_sprites.items():
            for x, instances in row.items():
                biscectorPos = EBCoords.fromBisector(x, y)
                if instances != None:
                    for instance in instances:
                        assert instance["NPC ID"] in range(len(data.npcs)), \
                            f"NPC ID {instance['NPC ID']} is out of range (max {len(data.npcs)-1})."
                            
                        pxOffset = EBCoords(instance["X"], instance["Y"])
                        absolutePos = biscectorPos+pxOffset
                        npcInstanceList.append(NPCInstance(instance["NPC ID"], absolutePos))
        
        data.npcinstances = npcInstanceList


    def _resourceSave(data: ProjectData):
        instances_yml = {}
        for c in range(40):
            instances_yml[c] = {}
            for r in range(32):
                instances_yml[c][r] = []

        for i in data.npcinstances:
            pos = i.posToMapSpritesFormat()
            instances_yml[pos[1]][pos[0]].append({
                "NPC ID": i.npcID,
                "X": pos[2],
                "Y": pos[3]
            })
        
        for c in range(40):
            for r in range(32):
                if instances_yml[c][r] == []: instances_yml[c][r] = None
            
        return instances_yml