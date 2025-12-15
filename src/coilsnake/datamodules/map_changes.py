from src.coilsnake.datamodules.data_module import YMLResourceDataModule
from src.coilsnake.project_data import ProjectData
from src.objects.changes import MapChange, MapChangeEvent, TileChange


class MapChangesModule(YMLResourceDataModule):
    NAME = "map changes"
    MODULE = "eb.MapEventModule"
    RESOURCE = "map_changes"
    FLOW_STYLE = None
    
    def _resourceLoad(data: ProjectData, map_changes):
        mapChanges = []
        for tileset, changes in map_changes.items():
            changeList = []
            for change in changes:
                tileChangeList = []
                for tileChange in change["Tile Changes"]:
                    tileChangeList.append(TileChange(tileChange["Before"], tileChange["After"]))
                if "EBME_Comment" in change:
                    comment = change["EBME_Comment"]
                else:
                    comment = None 
                changeList.append(MapChangeEvent(tileset, change["Event Flag"], tileChangeList, comment))
            mapChanges.append(MapChange(tileset, changeList))
        data.mapChanges = mapChanges
    
    def _resourceSave(data: ProjectData):
        changes_yml = {}
        for i in data.mapChanges:
            events = []
            for event in i.events:
                changes = []
                for tile in event.changes:
                    # coilsnake dumps them in this order, counterintuitively. Probably just alphabetical stuff
                    changes.append({"After": tile.after, "Before": tile.before})
                events.append({"Event Flag": event.flag, "Tile Changes": changes, "EBME_Comment": event.comment})
            changes_yml[i.tileset] = events

        return changes_yml