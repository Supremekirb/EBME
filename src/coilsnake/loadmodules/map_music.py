from src.coilsnake.loadmodules.load_module import YMLCoilsnakeResourceLoadModule
from src.objects.music import MapMusicHierarchy, MapMusicEntry

class MapMusicModule(YMLCoilsnakeResourceLoadModule):
    NAME = "map music"
    MODULE = "eb.MapMusicModule"
    RESOURCE = "map_music"
    
    def _resourceLoad(data, map_music):
        hiearchies = []
        for hierarchy, entries in map_music.items():
            current = MapMusicHierarchy(hierarchy)
            hiearchies.append(current)
            for entry in entries:
                current.addEntry(MapMusicEntry(entry["Event Flag"], entry["Music"]))
                
        data.mapMusic = hiearchies