from src.coilsnake.datamodules.data_module import YMLResourceDataModule
from src.coilsnake.project_data import ProjectData
from src.objects.changes import MapChange, MapChangeEvent, TileChange


class MapChangesModule(YMLResourceDataModule):
    NAME = "map changes"
    MODULE = "eb.MapEventModule"
    RESOURCE = "map_changes"
    
    def _resourceLoad(data: ProjectData, map_changes):
        mapChanges = []
        for tileset, changes in map_changes.items():
            changeList = []
            for change in changes:
                tileChangeList = []
                for tileChange in change["Tile Changes"]:
                    tileChangeList.append(TileChange(tileChange["Before"], tileChange["After"]))
                changeList.append(MapChangeEvent(change["Event Flag"], tileChangeList))
            mapChanges.append(MapChange(tileset, changeList))
        data.mapChanges = mapChanges
    
    def save(data: ProjectData):
        ...