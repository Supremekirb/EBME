from src.coilsnake.loadmodules.load_module import YMLCoilsnakeResourceLoadModule
from src.objects.npc import NPC

class NPCModule(YMLCoilsnakeResourceLoadModule):
    NAME = "NPCs"
    MODULE = ("eb.MiscTablesModule", "eb.ExpandedTablesModule")
    RESOURCE = "npc_config_table"
    
    def _resourceLoad(data, npc_config_table):
        npcList = []
        for id, npc in npc_config_table.items(): 
            if "EBME_Comment" in npc:
                comment = npc["EBME_Comment"]
            else:
                comment = None
                
            assert npc["Sprite"] in range(len(data.sprites)), \
                f"Sprite ID {npc['Sprite']} out of range (max {len(data.sprites)-1})."

            npcList.append(NPC(id, npc["Direction"], npc["Event Flag"], npc["Movement"], npc["Show Sprite"],
                               npc["Sprite"], npc["Text Pointer 1"], npc["Text Pointer 2"], npc["Type"], comment))
            
        data.npcs = npcList
