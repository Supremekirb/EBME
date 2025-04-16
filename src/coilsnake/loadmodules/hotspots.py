from src.coilsnake.loadmodules.load_module import YMLCoilsnakeResourceLoadModule
from src.objects.hotspot import Hotspot
from src.misc.coords import EBCoords

class HotspotModule(YMLCoilsnakeResourceLoadModule):
    NAME = "hotspots"
    MODULE = "eb.MiscTablesModule"
    RESOURCE = "map_hotspots"
    
    def _resourceLoad(data, map_hotspots):
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