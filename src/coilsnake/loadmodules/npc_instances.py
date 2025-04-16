from src.coilsnake.loadmodules.load_module import YMLCoilsnakeResourceLoadModule
from src.objects.npc import NPCInstance
from src.misc.coords import EBCoords

class NPCInstanceModule(YMLCoilsnakeResourceLoadModule):
    NAME = "NPC instances"
    MODULE = "eb.MapSpriteModule"
    RESOURCE = "map_sprites"
    
    def _resourceLoad(data, map_sprites):        
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
