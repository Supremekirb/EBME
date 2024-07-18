from src.misc.coords import EBCoords

class Sector:
    """Instance of a sector on the map."""
    def __init__(self, id: int, item: int, music: int, palette: int, palettegroup: int, tileset: int, setting: str, teleport: str,
                 townmap: str, townmaparrow: str, townmapimage: str, townmapx: int, townmapy: int):
        self.id = id
        self.item = item
        self.music = music
        self.palette = palette
        self.palettegroup = palettegroup
        self.tileset = tileset
        self.setting = setting
        self.teleport = teleport
        self.townmap = townmap
        self.townmaparrow = townmaparrow
        self.townmapimage = townmapimage
        self.townmapx = townmapx
        self.townmapy = townmapy

        self.coords = EBCoords.fromSector(int(id%32), int(id/32)) # (x, y) of sector location (in sector array)
        
    
    def attributesToDataDict(self) -> dict:
        return {
            "item": self.item,
            "music": self.music,
            "palette": self.palette,
            "palettegroup": self.palettegroup,
            "tileset": self.tileset,
            "setting": self.setting,
            "teleport": self.teleport,
            "townmap": self.townmap,
            "townmaparrow": self.townmaparrow,
            "townmapimage": self.townmapimage,
            "townmapx": self.townmapx,
            "townmapy": self.townmapy
        }
    
    def paletteToDataDict(self) -> dict:
        return {
            "palette": self.palette,
            "palettegroup": self.palettegroup,
            "tileset": self.tileset
        }