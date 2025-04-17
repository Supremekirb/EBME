from src.coilsnake.datamodules.data_module import YMLResourceDataModule
from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords
from src.objects.warp import Teleport


class TeleportModule(YMLResourceDataModule):
    NAME = "teleports"
    MODULE = "eb.MiscTablesModule"
    RESOURCE = "psi_teleport_dest_table"
    FLOW_STYLE = None
    
    def _resourceLoad(data: ProjectData, teleport_table):
        teleports = []
        for id, tp in teleport_table.items():
            teleports.append(Teleport(id, EBCoords.fromWarp(tp["X"], tp["Y"]), tp["Event Flag"], tp["Name"]))
            
        data.teleports = teleports
    
    
    def _resourceSave(data: ProjectData):
        teleports_yml = {}
        for i in data.teleports:
            teleports_yml[i.id] = {
                "Event Flag": i.flag,
                "Name": i.name,
                "X": i.dest.coordsWarp()[0],
                "Y": i.dest.coordsWarp()[1]
            }
        
        return teleports_yml