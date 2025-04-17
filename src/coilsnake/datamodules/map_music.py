from src.coilsnake.datamodules.data_module import YMLResourceDataModule
from src.coilsnake.project_data import ProjectData
from src.objects.music import MapMusicEntry, MapMusicHierarchy


class MapMusicModule(YMLResourceDataModule):
    NAME = "map music"
    MODULE = "eb.MapMusicModule"
    RESOURCE = "map_music"
    FLOW_STYLE = None
    
    def _resourceLoad(data: ProjectData, map_music):
        hiearchies = []
        for hierarchy, entries in map_music.items():
            current = MapMusicHierarchy(hierarchy)
            hiearchies.append(current)
            for entry in entries:
                current.addEntry(MapMusicEntry(entry["Event Flag"], entry["Music"]))
                
        data.mapMusic = hiearchies
        
    
    def _resourceSave(data: ProjectData):
        music_yml = {}
        for i in data.mapMusic:
            entries = []
            for j in i.entries:
                entries.append({"Event Flag": j.flag,
                                "Music": j.music})
            music_yml[i.id] = entries
            
        return music_yml