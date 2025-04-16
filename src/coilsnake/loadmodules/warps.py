from src.coilsnake.loadmodules.load_module import YMLCoilsnakeResourceLoadModule
from src.objects.warp import Warp
from src.misc.coords import EBCoords

class WarpModule(YMLCoilsnakeResourceLoadModule):
    NAME = "warps"
    MODULE = "eb.MiscTablesModule"
    RESOURCE = "teleport_destination_table"
    
    def _resourceLoad(data, warp_table):
        warps = []
        for id, warp in warp_table.items():
            if "EBME_Comment" in warp:
                comment = warp["EBME_Comment"]
            else:
                comment = None
            warps.append(Warp(id, EBCoords.fromWarp(warp["X"], warp["Y"]), warp["Direction"], warp["Warp Style"], warp["Unknown"], comment))
            
        data.warps = warps