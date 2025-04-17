from src.coilsnake.datamodules.data_module import YMLResourceDataModule
from src.coilsnake.project_data import ProjectData
from src.objects.npc import NPC


class NPCModule(YMLResourceDataModule):
    NAME = "NPCs"
    MODULE = ("eb.MiscTablesModule", "eb.ExpandedTablesModule")
    RESOURCE = "npc_config_table"
    FLOW_STYLE = False
    
    def _resourceLoad(data: ProjectData, npc_config_table):
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

    
    def _resourceSave(data: ProjectData):
        npc_yml = {}
        for n in data.npcs:
            npc_yml[n.id] = {
                "Direction": n.direction,
                "Event Flag": n.flag,
                "Movement": n.movement,
                "Show Sprite": n.show,
                "Sprite": n.sprite,
                "Text Pointer 1": n.text1,
                "Text Pointer 2": n.text2,
                "Type": n.type,
                "EBME_Comment": n.comment if n.comment != "" else None,
            }
        
        return npc_yml