import os
from typing import Literal
from uuid import UUID

import numpy
import yaml

import src.misc.common as common
from src.coilsnake.fts_interpreter import FullTileset
from src.misc.coords import EBCoords
from src.objects.enemy import EnemyGroup, EnemyMapGroup, EnemyTile
from src.objects.hotspot import Hotspot
from src.objects.npc import NPC, NPCInstance
from src.objects.sector import Sector
from src.objects.sprite import BattleSprite, Sprite
from src.objects.tile import MapTile, MapTileGraphic
from src.objects.trigger import Trigger
from src.objects.warp import Warp, Teleport


class ProjectData():
    """Container for loaded project data"""
    def __init__(self, directory: str):
        
        self.dir = directory
        self.tilesets: list[FullTileset] = []
        self.sectors: numpy.ndarray[Sector] = []
        self.tiles: numpy.ndarray[MapTile] = []
        self.tilegfx: list[MapTileGraphic] = []
        self.npcs: list[NPC] = []
        self.npcinstances: list[NPCInstance] = []
        self.sprites: list[Sprite] = []
        self.triggers: list[Trigger] = []
        self.enemyPlacements: numpy.ndarray[EnemyTile] = []
        self.enemyMapGroups: list[EnemyMapGroup] = []
        self.enemyGroups: list[EnemyGroup] = []
        self.battleSprites: list[BattleSprite] = []
        self.hotspots: list[Hotspot] = []
        self.warps: list[Warp] = []
        self.teleports: list[Teleport] = []
    
    def loadProjectSnake(self):
        try:
            with open(os.path.join(self.dir, "Project.snake")) as project:
                self.projectSnake = yaml.load(project, Loader=yaml.CSafeLoader)

        except FileNotFoundError as e:
            raise FileNotFoundError(f"Could not open Project.snake at {os.path.normpath(os.path.join(self.dir, 'Project.snake'))}.") from e
        
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Could not interpret Project.snake at {os.path.normpath(os.path.join(self.dir, 'Project.snake'))}.") from e
        
        except Exception as e:
            raise Exception(f"Could not read Project.snake at {os.path.normpath(os.path.join(self.dir, 'Project.snake'))}.") from e
        

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

        return os.path.normpath(os.path.join(self.dir, self.projectSnake['resources'][module][resource]))
    
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
    
        for pg in self.tilegfx[tilesetNumber].items():
            for p in pg[1].items():
                for t in p[1].items():
                    t[1].hasRendered = False

    def resolveTileGraphic(self, tileset: int, palettegroup: int, palette: int, tile: int) -> MapTileGraphic:
        """Find the closest valid tile graphic if the requested one is invalid."""
        tile = common.cap(tile, 0, 960)

        for i in self.tilegfx.items():
            if i[0] == tileset:
                break
            else:
                tileset = i[0]
        for i in self.tilegfx[tileset].items():
            if i[0] == palettegroup:
                break
            else:
                palettegroup = i[0]
        for i in self.tilegfx[tileset][palettegroup].items():
            if i[0] == palette:
                break
            else:
                palette = i[0]
                
        return self.tilegfx[tileset][palettegroup][palette][tile]

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
    
    # special getters for some of the more cursed accesses
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
        return self.tilegfx[tileset][palettegroup][palette][tile]
                    
    def getNPC(self, id: int) -> NPC:
        return self.npcs[id]
    def getSprite(self, id: int) -> Sprite:
        return self.sprites[id]
    def getEnemyTile(self, coords: EBCoords) -> EnemyTile:
        return self.enemyPlacements[coords.coordsEnemy()[1], coords.coordsEnemy()[0]]