from src.coilsnake.loadmodules.load_module import YMLCoilsnakeResourceLoadModule
from src.objects.warp import Teleport
from src.misc.coords import EBCoords

class TeleportModule(YMLCoilsnakeResourceLoadModule):
    NAME = "teleports"
    MODULE = "eb.MiscTablesModule"
    RESOURCE = "psi_teleport_dest_table"
    
    def _resourceLoad(data, teleport_table):
        teleports = []
        for id, tp in teleport_table.items():
            teleports.append(Teleport(id, EBCoords.fromWarp(tp["X"], tp["Y"]), tp["Event Flag"], tp["Name"]))
            
        data.teleports = teleports