from src.coilsnake.datamodules.data_module import YMLResourceDataModule
from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords
from src.objects.warp import Warp


class WarpModule(YMLResourceDataModule):
    NAME = "warps"
    MODULE = "eb.MiscTablesModule"
    RESOURCE = "teleport_destination_table"
    FLOW_STYLE = None
    
    def _resourceLoad(data: ProjectData, warp_table):
        warps = []
        for id, warp in warp_table.items():
            if "EBME_Comment" in warp:
                comment = warp["EBME_Comment"]
            else:
                comment = None
            warps.append(Warp(id, EBCoords.fromWarp(warp["X"], warp["Y"]), warp["Direction"], warp["Warp Style"], warp["Unknown"], comment))
            
        data.warps = warps
    
    
    def _resourceSave(data: ProjectData):
        warps_yml = {}
        for i in data.warps:
            warps_yml[i.id] = {
                "Direction": i.dir,
                "Unknown": i.unknown,
                "Warp Style": i.style,
                "X": i.dest.coordsWarp()[0],
                "Y": i.dest.coordsWarp()[1],
                "EBME_Comment": i.comment,
            }
        
        return warps_yml