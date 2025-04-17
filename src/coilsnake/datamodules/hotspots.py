from src.coilsnake.datamodules.data_module import YMLResourceDataModule
from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords
from src.objects.hotspot import Hotspot


class HotspotModule(YMLResourceDataModule):
    NAME = "hotspots"
    MODULE = "eb.MiscTablesModule"
    RESOURCE = "map_hotspots"
    FLOW_STYLE = None
    
    def _resourceLoad(data: ProjectData, map_hotspots):
        hotspots = []
        for id, hotspot in map_hotspots.items():    
            start = EBCoords.fromWarp(hotspot["X1"], hotspot["Y1"])
            end = EBCoords.fromWarp(hotspot["X2"], hotspot["Y2"])
            
            if "EBME_Colour" in hotspot:
                colourRaw = hotspot["EBME_Colour"]
                if isinstance(colourRaw, list):
                    # Old save format conversion. See cfa0a9d
                    colour = colourRaw
                else:    
                    colour = (int(colourRaw[1:3], 16), int(colourRaw[3:5], 16), int(colourRaw[5:7], 16))
            else:
                colour = None
            if "EBME_Comment" in hotspot:
                comment = hotspot["EBME_Comment"]
            else:
                comment = None
            
            if colour:
                hotspots.append(Hotspot(id, start, end, colour=colour, comment=comment))
            else:
                hotspots.append(Hotspot(id, start, end, comment=comment))

        data.hotspots = hotspots
    
    
    def _resourceSave(data: ProjectData):
        hotspots_yml = {}
        for i in data.hotspots:
            hotspots_yml[i.id] = {
                "Y1": i.start.coordsWarp()[1],
                "X1": i.start.coordsWarp()[0],
                "Y2": i.end.coordsWarp()[1],
                "X2": i.end.coordsWarp()[0],
                "EBME_Colour": "#{0:02x}{1:02x}{2:02x}".format(i.colour[0], i.colour[1], i.colour[2]),
                "EBME_Comment": i.comment if i.comment != "" else None
            }
            
        return hotspots_yml