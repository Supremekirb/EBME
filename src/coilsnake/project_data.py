import os
from typing import Literal
from uuid import UUID

import numpy

import src.misc.common as common
from src.misc.exceptions import CoilsnakeResourceNotFoundError
from src.coilsnake.fts_interpreter import FullTileset
from src.misc.coords import EBCoords
from src.objects.changes import MapChange
from src.objects.enemy import EnemyGroup, EnemyMapGroup, EnemyTile
from src.objects.hotspot import Hotspot
from src.objects.music import MapMusicHierarchy
from src.objects.npc import NPC, NPCInstance
from src.objects.palette_settings import PaletteSettings
from src.objects.sector import Sector
from src.objects.sprite import BattleSprite, Sprite
from src.objects.tile import MapTile, MapTileGraphic
from src.objects.trigger import Trigger
from src.objects.warp import Teleport, Warp


class ProjectData():
    """Container for loaded project data"""
    def __init__(self, directory: str):
        
        self.dir = directory
        self.projectSnake: dict = {}
        self.tilesets: list[FullTileset] = []
        self.paletteSettings: dict[int, dict[int, PaletteSettings]] = {}
        self.sectors: numpy.ndarray[Sector] = []
        self.tiles: numpy.ndarray[MapTile] = []
        self.tilegfx: dict[int, dict[str, dict[int, MapTileGraphic]]] = {}
        self.npcs: list[NPC] = []
        self.npcinstances: list[NPCInstance] = []
        self.sprites: list[Sprite] = []
        self.triggers: list[Trigger] = []
        self.enemyPlacements: numpy.ndarray[EnemyTile] = []
        self.enemyMapGroups: list[EnemyMapGroup] = []
        self.enemyGroups: list[EnemyGroup] = []
        self.enemySprites: list[int] = [] # enemy id --> sprite id
        self.battleSprites: list[BattleSprite] = []
        self.hotspots: list[Hotspot] = []
        self.warps: list[Warp] = []
        self.teleports: list[Teleport] = []
        self.mapMusic: list[MapMusicHierarchy] = []
        self.mapChanges: list[MapChange] = []
        

    def getResourcePath(self, module: Literal[
        "eb.ExpandedTablesModule",
        "eb.MapEnemyModule",
        "eb.MapEventModule",
        "eb.MapModule",
        "eb.MapMusicModule",
        "eb.MapSpriteModule",
        "eb.MiscTablesModule",
        "eb.SpriteGroupModule",
        "eb.TilesetModule",
        "eb.TownMapIconModule",
        "eb.DoorModule",
        "eb.EnemyModule"],
        resource: str) -> str:
        """Get the file path to a resource in a project

        Args:
            module (Literal[ &quot;eb.ExpandedTablesModule&quot;, &quot;eb.MapEnemyModule&quot;, &quot;eb.MapEventModule&quot;, &quot;eb.MapModule&quot;, &quot;eb.MapMusicModule&quot;, &quot;eb.MapSpriteModule&quot;, &quot;eb.MiscTablesModule&quot;, &quot;eb.SpriteGroupModule&quot;, &quot;eb.TilesetModule&quot;, &quot;eb.TownMapIconModule&quot;]): Module the resource is in
            resource (str): Resource name (reference Project.snake)

        Returns:
            str: path to resource
        """
        try:
            return os.path.normpath(os.path.join(self.dir, self.projectSnake['resources'][module][resource]))
        except KeyError:
            raise CoilsnakeResourceNotFoundError(f"Could not find the path to resource {module}.{resource} in Project.snake")
    
    def replaceTileset(self, newTileset: list[str], tilesetNumber: int):
        """Reload a tileset from a file. Also deals with tiles that use it.

        Args:
            newtileset (list[str]): the contents of the new tileset file
            tilesetNumber (int): the tileset number
        """

        newTileset = FullTileset(contents=newTileset, id=tilesetNumber)

        # merging palettes so stuff doesnt break
        for p in self.tilesets[tilesetNumber].palettes[1:]: # dont merge first
            newTileset.palettes.append(p)
        # update palette group 
        newTileset.palettes[0].groupID = self.tilesets[tilesetNumber].palettes[0].groupID
        # rebuild palette groups
        newTileset.paletteGroups = newTileset.buildPaletteGroups()

        self.tilesets[tilesetNumber] = newTileset
    
        self.clobberTileGraphicsCache(tilesetNumber)
    
    def clobberTileGraphicsCache(self, tileset: int|None=None, paletteGroup: int|None=None, palette: int|None=None, tile: int|None=None):
        """Clear cached tile graphics. Failing to specify an argument clears all graphics under that argument."""
        if tileset:
            if paletteGroup:
                if palette:
                    if tile: # all params
                        gfx = self.getTileGraphic(tileset, paletteGroup, palette, tile)
                        gfx.hasRendered = False
                        gfx.hasRenderedFg = False
                    else: # clear one palette
                        self.tilegfx[tileset][
                            common.combinePaletteAndGroup(paletteGroup, palette)] = {}
                else: # clear one palette group
                    group = self.getPaletteGroup(paletteGroup)
                    for p in group.palettes:
                        self.tilegfx[tileset][
                            common.combinePaletteAndGroup(paletteGroup, p.paletteID)] = {}
            else: # clear one tileset
                for pg in self.tilegfx[tileset].keys():
                    self.tilegfx[tileset][pg] = {}
        else: # clear entire cache
            for t in self.tilegfx.values():
                for pg in t.keys():
                    t[pg] = {}
                            
    # project getters
    def getProjectVersion(self) -> str:
        return self.projectSnake['version']
    
    def getProjectName(self) -> str:
        try:
            return self.projectSnake['Title']
        except KeyError:
            return "Untitled"
    
    def getProjectAuthor(self) -> str:
        try:
            return self.projectSnake['Author']
        except KeyError:
            return "Anonymous"
    
    def getProjectDescription(self) -> str:
        try:
            return self.projectSnake['Description']
        except KeyError:
            return "No description."
    
    # special getters for some of the more cursed accesses(
    def getTilesetFromPaletteGroup(self, paletteGroup: int):
        for i in self.tilesets:
            try:
                if i.getPaletteGroup(paletteGroup):
                    return i
            except ValueError:
                continue
        else:
            raise ValueError(f"Could not find any tileset containing palette group {paletteGroup}.")
    
    def getPaletteGroup(self, paletteGroup: int):
        for i in self.tilesets:
            try:
                return i.getPaletteGroup(paletteGroup)
            except ValueError:
                continue
        else:
            raise ValueError(f"Could not find palette group {paletteGroup} in any tileset.")
    
    def sectorFromID(self, id: int) -> Sector:
        return self.sectors.flat[id]

    def adjacentSectors(self, sector: Sector) -> tuple[Sector|None, Sector|None, Sector|None, Sector|None]:
        """Get the four direcly adjacent sectors to a given sector. Returns None if there is no sector in that direction (edge).

        Args:
            sector (Sector): Target to find adjacents

        Returns:
            tuple[Sector|None, Sector|None, Sector|None, Sector|None]: up, right, down, left
        """
        
        x, y = sector.coords.coordsSector()
        
        above = self.sectors[y-1, x] if y > 0 else None
        right = self.sectors[y, x+1] if x < 31 else None
        below = self.sectors[y+1, x] if y < 79 else None
        left = self.sectors[y, x-1] if x > 0 else None
        
        return above, right, below, left

    def adjacentMatchingSectors(self, sector: Sector, selected: list = []) -> list[Sector]:
        """Recursively get matching adjacent sectors

        Args:
            sector (Sector): the root sector

        Returns:
            list[Sector]: list of all valid sectors
        """
        
        selected.append(sector)
        
        above, right, below, left = self.adjacentSectors(sector)
        
        for i in [above, right, below, left]:
            if (i and not i in selected and 
                i.tileset == sector.tileset and
                i.palettegroup == sector.palettegroup
                and i.palette == sector.palette):
                selected.append(i)
                
                selected = self.adjacentMatchingSectors(i, selected)
                
        return list(set(selected)) # ensure no duplicates

    def npcInstanceFromUUID(self, uuid: UUID) -> NPCInstance:
        """Get an NPCInstance by UUID

        Args:
            uuid (UUID): the UUID

        Returns:
            NPCInstance: the matching NPCInstance
        """
        for i in self.npcinstances:
            if i.uuid == uuid:
                return i
    def npcInstancesFromNPCID(self, id: int) -> list[NPCInstance]:
        """Get all NPCInstances that use a given NPC ID

        Args:
            id (int): an NPC ID

        Returns:
            list[NPCInstance]: All matching NPCInstances. Blank list if none.
        """
        npcs = []
        for i in self.npcinstances:
            if i.npcID == id:
                npcs.append(i)
        return npcs
    
    def triggerFromUUID(self, uuid: UUID) -> Trigger:
        """Get a Trigger by UUID

        Args:
            uuid (UUID): the UUID

        Returns:
            Trigger: the matching Trigger
        """
        for i in self.triggers:
            if i.uuid == uuid:
                return i
    
    # generic getters (so return type is known)
    # assume that oob errors are checked by the caller
    def getTileset(self, id: int) -> FullTileset:
        return self.tilesets[id]
    def getSector(self, coords: EBCoords) -> Sector:
        return self.sectors[coords.coordsSector()[1], coords.coordsSector()[0]]
    def getTile(self, coords: EBCoords) -> MapTile:
        return self.tiles[coords.coordsTile()[1], coords.coordsTile()[0]]
    def getTileGraphic(self, tileset: int, 
                       palettegroup: int, 
                       palette: int, 
                       tile: int) -> MapTileGraphic:
        return self.tilegfx[tileset][common.combinePaletteAndGroup(palettegroup, palette)].setdefault(
            tile, MapTileGraphic(tile, tileset, palettegroup, palette)
        )
                    
    def getNPC(self, id: int) -> NPC:
        return self.npcs[id]
    def getSprite(self, id: int) -> Sprite:
        return self.sprites[id]
    def getEnemyTile(self, coords: EBCoords) -> EnemyTile:
        return self.enemyPlacements[coords.coordsEnemy()[1], coords.coordsEnemy()[0]]