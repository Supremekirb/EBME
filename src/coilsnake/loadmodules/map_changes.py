from src.objects.changes import MapChange, MapChangeEvent, TileChange
from src.coilsnake.loadmodules.load_module import YMLCoilsnakeResourceLoadModule

class MapChangesModule(YMLCoilsnakeResourceLoadModule):
    NAME = "map changes"
    MODULE = "eb.MapEventModule"
    RESOURCE = "map_changes"
    
    def _resourceLoad(data, map_changes):
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