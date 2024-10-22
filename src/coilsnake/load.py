import logging
import os
import traceback

import numpy
import yaml
from PIL import Image, ImageQt

import src.misc.common as common
from src.coilsnake.fts_interpreter import FullTileset
from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords
from src.misc.exceptions import NotBase32Error, NotHexError
from src.objects.enemy import EnemyGroup, EnemyMapGroup, EnemyTile
from src.objects.hotspot import Hotspot
from src.objects.music import MapMusicEntry, MapMusicHierarchy
from src.objects.npc import NPC, NPCInstance
from src.objects.sector import Sector
from src.objects.sprite import BattleSprite, Sprite
from src.objects.tile import MapTile, MapTileGraphic
from src.objects.trigger import (Trigger, TriggerDoor, TriggerEscalator,
                                 TriggerLadder, TriggerObject, TriggerPerson,
                                 TriggerRope, TriggerStairway, TriggerSwitch)
from src.objects.warp import Teleport, Warp


def readDirectory(parent, dir):
    try:
        projectData = ProjectData(dir)
        try:
            projectData.loadProjectSnake()
        except Exception as e:
            parent.returns.emit({"title": "Failed to load Project.snake",
                                    "text": "Could not load Project.snake. Is this a valid CoilSnake project?",
                                    "info": str(e)})
            raise

        parent.updates.emit("Loading tilesets...")
        try:
            readTilesets(projectData)
        except Exception as e:
            parent.returns.emit({"title": "Failed to load tilesets",
                                    "text": "Could not load tileset data.",
                                    "info": str(e)})
            raise
            
        parent.updates.emit("Loading sectors...")
        try:
            readSectors(projectData)
        except Exception as e:
            parent.returns.emit({"title": "Failed to load sectors",
                                    "text": "Could not load sector data.",
                                    "info": str(e)})
            raise

        parent.updates.emit("Loading tiles...")
        try:
            readTiles(projectData)
        except Exception as e:
            parent.returns.emit({"title": "Failed to load tiles",
                                    "text": "Could not load tile data.",
                                    "info": str(e)})
            raise

        try:
            readTileGraphics(projectData)
        except Exception as e:
            parent.returns.emit({"title": "Failed to load tiles",
                                    "text": "Could not initialise tile grahpics cache.",
                                    "info": str(e)})
            raise
        
        parent.updates.emit("Loading sprites...")
        try:
            readSpriteGroups(projectData)
        except Exception as e:
            parent.returns.emit({"title": "Failed to load sprites",
                                    "text": "Could not load sprite data.",
                                    "info": str(e)})
            raise
        try:
            readBattleSprites(projectData)
        except Exception as e:
            parent.returns.emit({"title": "Failed to load battle sprites",
                                    "text": "Could not load battle sprite data.",
                                    "info": str(e)})
            raise

        parent.updates.emit("Loading NPCs...")
        try:
            readNPCTable(projectData)
        except Exception as e:
            parent.returns.emit({"title": "Failed to load NPCs",
                                    "text": "Could not load NPC data.",
                                    "info": str(e)})
            raise
        
        try:
            readNPCInstances(projectData)
        except Exception as e:
            parent.returns.emit({"title": "Failed to load NPC placements",
                                    "text": "Could not load NPC placement data.",
                                    "info": str(e)})
            raise

        parent.updates.emit("Loading triggers...")
        try:
            readTriggers(projectData)
        except Exception as e:
            parent.returns.emit({"title": "Failed to load triggers",
                                    "text": "Could not load trigger data.",
                                    "info": str(e)})
            raise
            
        parent.updates.emit("Loading enemies...")
        try:
            readEnemyPlacements(projectData)
        except Exception as e:
            parent.returns.emit({"title": "Failed to load enemy placements",
                                    "text": "Could not load enemy placement data.",
                                    "info": str(e)})
            raise
        try:
            readMapEnemyGroups(projectData)
        except Exception as e:
            parent.returns.emit({"title": "Failed to load map enemy groups",
                                    "text": "Could not load map enemy group data.",
                                    "info": str(e)})
            raise
        try:
            readEnemyGroups(projectData)
        except Exception as e:
            parent.returns.emit({"title": "Failed to load enemy groups",
                                    "text": "Could not load enemy group data.",
                                    "info": str(e)})
            raise

        try:
            readEnemySprites(projectData)
        except Exception as e:
            parent.returns.emit({"title": "Failed to load enemy sprites",
                                    "text": "Could not load enemy sprite data.",
                                    "info": str(e)})
            raise
            
        parent.updates.emit("Loading hotspots...")
        try:
            readHotspots(projectData)
        except Exception as e:
            parent.returns.emit({"title": "Failed to load hotspots",
                                    "text": "Could not load hotspot.",
                                    "info": str(e)})
            raise
        
        parent.updates.emit("Loading warps...")
        try:
            readWarps(projectData)
        except Exception as e:
            parent.returns.emit({"title": "Failed to load warps",
                                    "text": "Could not load warp data.",
                                    "info": str(e)})
            raise
        
        parent.updates.emit("Loading teleports...")
        try:
            readTeleports(projectData)
        except Exception as e:
            parent.returns.emit({"title": "Failed to load teleports",
                                    "text": "Could not load teleport data.",
                                    "info": str(e)})
            raise
        
        parent.updates.emit("Loading map music...")
        try:
            readMapMusic(projectData)
        except Exception as e:
            parent.returns.emit({"title": "Failed to load map music",
                                    "text": "Could not load map music data.",
                                    "info": str(e)})
            raise
        
        logging.info(f"Successfully loaded project at {projectData.dir}")
        parent.returns.emit(projectData)

    except Exception:
        logging.warning(traceback.format_exc())
        raise


def readTilesets(data: ProjectData):
    """Read project tilesets"""
    data.tilesets = []
    try:
        for i, _ in data.projectSnake["resources"]["eb.TilesetModule"].items():
            if not i.startswith("Tilesets/"):
                continue
            id = int(i.split("/")[-1])
            with open(data.getResourcePath("eb.TilesetModule", i), encoding='utf-8') as fts:
                data.tilesets.append(FullTileset(contents=fts.readlines(), id=id))

    except KeyError as e:
        raise KeyError(f"Could not find path to .fts file {i:02d} in Project.snake.") from e
    
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Could not find the file at {data.getResourcePath('eb.TilesetModule',f'Tilesets/{i:02d}')}") from e
    
    except NotHexError or NotBase32Error or ValueError as e:
        raise ValueError(f"Invalid data in tileset {id}.") from e
    

def readSectors(data: ProjectData):
    """Read project sectors"""
    try:
        hasLoadedYml = False 
        with open(data.getResourcePath("eb.MapModule", "map_sectors"), encoding="utf-8") as map_sectors:
            sectorList = []
            map_sectors = yaml.load(map_sectors, Loader=yaml.CSafeLoader)
            hasLoadedYml = True

            for i in range(len(map_sectors)): # this so we can pass the sector ID to the Sector
                sector = map_sectors[i]
                for t in data.tilesets:
                    try:
                        t.getPalette(sector["Tileset"], sector["Palette"])
                    except ValueError:
                        t = None
                        continue
                    else:
                        break
                    
                if not t:
                    raise ValueError(f"Could not find a tileset containing palette {sector['Palette']} and palette group {sector['Tileset']}.")

                sectorList.append(Sector(i, sector["Item"], sector["Music"], sector["Palette"], sector["Tileset"], t.id,
                                         sector["Setting"], sector["Teleport"], sector["Town Map"], sector["Town Map Arrow"],
                                         sector["Town Map Image"], sector["Town Map X"], sector["Town Map Y"]))

            sectorList = [sectorList[i:i+32] for i in range(0,len(sectorList),32)]

            sectorArray = numpy.array(sectorList, dtype=numpy.object_)
            
            data.sectors = sectorArray
        
    except KeyError as e:
        if not hasLoadedYml:
            raise KeyError("Could not find path to map_sectors in Project.snake.") from e
        else:
            raise KeyError(f"Could not read data of sector {i}.") from e
        
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Could not find the file at {data.getResourcePath('eb.MapModule','map_sectors')}.") from e
    
    except yaml.YAMLError as e:
        raise yaml.YAMLError("Could not interpret sector data.") from e
        

def readTiles(data: ProjectData):
    """Read project tiles"""
    
    try:
        path = data.getResourcePath("eb.MapModule", "map_tiles")
        with open(path, encoding="utf-8") as map_tiles:
            tileArray = numpy.zeros(shape=[320, 256], dtype=numpy.object_)
            map_tiles = map_tiles.read()

            map_tiles = [r.split(" ") for r in map_tiles.split("\n")]
            if map_tiles[-1] == ['']:
                del map_tiles[-1] # last newline causes issues, so we do this

            map_tiles = numpy.array(map_tiles)

            iterated = numpy.nditer(map_tiles, flags=["multi_index"])

            for i in iterated: # i dont know anymore lol
                x = iterated.multi_index[1]
                y = iterated.multi_index[0]
                coords = EBCoords.fromTile(x, y)
                sector = data.getSector(coords)
                id = int(i.item(), 16)
                assert id in range(0, common.MAXTILES), f"Tile ID {id} out of range."
                
                tile = MapTile(id, coords,
                               sector.tileset,
                               sector.palettegroup,
                               sector.palette)
                
                tileArray[iterated.multi_index[0], iterated.multi_index[1]] = tile

            data.tiles = tileArray
        
    except KeyError as e:
        raise KeyError("Could not find path to map_tiles in Project.snake.") from e
    
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Could not find the file at {data.getResourcePath('eb.MapModule', 'map_tiles')}.") from e

def readTileGraphics(data: ProjectData):
    """Read project tile graphics. This differs from just using Tile objects as they are not unique per-palette, whereas these are"""
    data.tilegfx = {}
    # try:
    for t in data.tilesets:
            data.tilegfx[t.id] = {}
            for g in t.paletteGroups:
                data.tilegfx[t.id][g.groupID] = {}
                for p in g.palettes:
                    data.tilegfx[t.id][g.groupID][p.paletteID] = {}
                    for mt in range(common.MAXTILES):
                        data.tilegfx[t.id][g.groupID][p.paletteID][mt] = MapTileGraphic(mt, t.id, g.groupID, p.paletteID)

def readNPCTable(data: ProjectData):
    """Read project NPC table"""
    try:
        hasLoadedYml = False
        data.npcs = []
        try:
            path = data.getResourcePath("eb.MiscTablesModule", "npc_config_table")
        except KeyError:
            path = data.getResourcePath("eb.ExpandedTablesModule", "npc_config_table") # projects made with coilsnake-next
        with open(path, encoding="utf-8") as npc_config_table:
            npc_config_table = yaml.load(npc_config_table, Loader=yaml.CSafeLoader)
            hasLoadedYml = True
            for n in npc_config_table.items(): 
                id = n[0]
                n = n[1]

                if "EBME_Comment" in n:
                    comment = n["EBME_Comment"]
                else:
                    comment = None
                    
                assert n["Sprite"] in range(len(data.sprites)), f"Sprite ID {n['Sprite']} out of range."

                data.npcs.append(NPC(id, n["Direction"], n["Event Flag"], n["Movement"], n["Show Sprite"],
                                     n["Sprite"], n["Text Pointer 1"], n["Text Pointer 2"], n["Type"], comment))

    except KeyError as e:
        if not hasLoadedYml:
            raise KeyError("Could not find path to npc_config_table in Project.snake.") from e
        else:
            raise KeyError(f"Could not read data of NPC {n[0]}.") from e
        
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Could not find the file at {data.getResourcePath('eb.MiscTablesModule', 'npc_config_table')}.") from e
    
        
def readNPCInstances(data: ProjectData):
    """Read project NPC instances"""
    try:
        hasLoadedYml = False
        data.npcinstances = []
        path = data.getResourcePath("eb.MapSpriteModule", "map_sprites")
        with open(path, encoding="utf-8") as map_sprites:
            hasLoadedYml = True
            map_sprites = yaml.load(map_sprites, Loader=yaml.CSafeLoader)

            for y in map_sprites.items():
                for x in y[1].items():
                    if x[1] != None:
                        for n in x[1]:
                            
                            assert n["NPC ID"] in range(len(data.npcs)), f"NPC ID {n['NPC ID']} out of range."
                            data.npcinstances.append(NPCInstance(n["NPC ID"], EBCoords(x[0]*8*32+n["X"], y[0]*8*32+n["Y"]))) # what the fuck is this??

    except KeyError as e:
        if not hasLoadedYml:
            raise KeyError("Could not find path to map_sprites in Project.snake.") from e
        else:
            raise KeyError(f"Could not read data of NPC instances.") from e
    
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Could not find the file at {data.getResourcePath('eb.MapSpriteModule', 'map_sprites')}.") from e

def readSpriteGroups(data: ProjectData):
    """Read project sprite groups"""
    try:
        hasLoadedYml = False
        data.sprites = []
        path = data.getResourcePath("eb.SpriteGroupModule", "sprite_groups")
        with open(path, encoding="utf-8") as sprite_groups:
            sprite_groups = yaml.load(sprite_groups, Loader=yaml.CSafeLoader)
            hasLoadedYml = True

            isGettingSpritePath = True
            for spr in sprite_groups.items():
                try:
                    sprPath = data.getResourcePath("eb.SpriteGroupModule", f"SpriteGroups/{spr[0]:03}")
                except KeyError: # CoilSnake-next projects do not include extra sprite paths in Project.snake
                    logging.warning("Couldn't find sprite {spr[0]:03} in Project.snake, probably a CoilSnake-next project. Trying to load directly...")
                    try:
                        sprPath = os.path.normpath(os.path.join(data.dir, "SpriteGroups", f"{spr[0]:03}.png"))
                    except FileNotFoundError: 
                        logging.warning("Couldn't load sprite {spr[0]:03} directly!")
                        raise
                sprImg = Image.open(sprPath).convert("RGBA")
                data.sprites.append(Sprite(sprImg, spr))
            isGettingSpritePath = False
        
    except KeyError as e:
        if not hasLoadedYml:
            raise KeyError("Could not find path to sprite_groups in Project.snake.") from e
        else:
            raise KeyError(f"Could not read data of sprite {spr[0]}.") from e
        
    except FileNotFoundError as e:
        if isGettingSpritePath:
            try:
                raise FileNotFoundError(f"Could not find the file at {data.getResourcePath('eb.SpriteGroupModule',f'SpriteGroups/{spr[0]:03}')}.") from e
            except:
                raise # -next sprites
        else:    
            raise FileNotFoundError(f"Could not find the file at {data.getResourcePath('eb.SpriteGroupModule','sprite_groups')}.") from e
        
def readTriggers(data: ProjectData):
    """Read project triggers (aka doors)"""
    try:
        hasLoadedYml = False
        data.triggers = []
        path = data.getResourcePath("eb.DoorModule", "map_doors")
        with open(path, encoding="utf-8") as map_doors:
            map_doors = yaml.load(map_doors, Loader=yaml.CSafeLoader)
            hasLoadedYml = True

            for y in map_doors.items():
                for x in y[1].items():
                    if x[1] != None:
                        for i in x[1]:
                            match i["Type"]:
                                case "door":
                                    triggerData = TriggerDoor(EBCoords.fromWarp(i["Destination X"], i["Destination Y"]), i["Direction"],
                                                                    i["Event Flag"], i["Style"], i["Text Pointer"])
                                case "escalator":
                                    triggerData = TriggerEscalator(i["Direction"])
                                case "ladder":
                                    triggerData = TriggerLadder()
                                case "object":
                                    triggerData = TriggerObject(i["Text Pointer"])
                                case "person":
                                    triggerData = TriggerPerson(i["Text Pointer"])
                                case "rope":
                                    triggerData = TriggerRope()
                                case "stairway":
                                    triggerData = TriggerStairway(i["Direction"])
                                case "switch":
                                    triggerData = TriggerSwitch(i["Text Pointer"], i["Event Flag"])
                                case _:
                                    raise ValueError(f"Unknown trigger type {i['Type']}")

                            biscectorPos = EBCoords.fromBisector(x[0], y[0])
                            warpOffset = EBCoords.fromWarp(i["X"], i["Y"])
                            absolutePos = biscectorPos+warpOffset
                            data.triggers.append(Trigger(absolutePos, triggerData))
                        
    except KeyError as e:
            if not hasLoadedYml:
                raise KeyError("Could not find path to map_doors in Project.snake.") from e
            else:
                raise
        
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Could not find the file at {data.getResourcePath('eb.DoorModule', 'map_doors')}.") from e
    
    
def readEnemyPlacements(data: ProjectData):
    """Read project enemy placements"""
    try:
        hasLoadedYml = False
        enemyPlacementList = []
        path = data.getResourcePath("eb.MapEnemyModule", "map_enemy_placement")
        with open(path, encoding="utf-8") as map_enemy_placement:
            map_enemy_placement = yaml.load(map_enemy_placement, Loader=yaml.CSafeLoader)
            hasLoadedYml = True
            for i in map_enemy_placement.items():
                enemyPlacementList.append(EnemyTile(EBCoords.fromEnemy(int(i[0]%128), int(i[0]//128)),
                                                    i[1]["Enemy Map Group"]))

            enemyArray = numpy.array(enemyPlacementList, dtype=numpy.object_)
            enemyArray = numpy.reshape(enemyArray, (160, 128))
        
        data.enemyPlacements = enemyArray

    except KeyError as e:
        if not hasLoadedYml:
            raise KeyError("Could not find path to map_enemy_placement in Project.snake.") from e
        else:
            raise KeyError(f"Could not read data of enemy placements.") from e
        
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Could not find the file at {data.getResourcePath('eb.MapEnemyModule', 'map_enemy_placement')}.") from e
    
    
def readMapEnemyGroups(data: ProjectData):
    """Read project map enemy groups"""
    try:
        hasLoadedYml = False
        enemyMapGroups = []
        path = data.getResourcePath("eb.MapEnemyModule", "map_enemy_groups")
        with open(path, encoding="utf-8") as map_enemy_groups:
            map_enemy_groups = yaml.load(map_enemy_groups, Loader=yaml.CSafeLoader)
            hasLoadedYml = True
            for i in map_enemy_groups.items():
                if "EBME_Colour" in i[1]:
                    colourRaw = i[1]["EBME_Colour"]
                    colour = (int(colourRaw[1:3], 16), int(colourRaw[3:5], 16), int(colourRaw[5:7], 16))
                else:
                    colour = None
                    
                enemyMapGroups.append(EnemyMapGroup(i[0], i[1]["Event Flag"], colour, i[1]["Sub-Group 1"], i[1]["Sub-Group 2"],
                                                    i[1]["Sub-Group 1 Rate"], i[1]["Sub-Group 2 Rate"]))

        data.enemyMapGroups = enemyMapGroups

    except KeyError as e:
        if not hasLoadedYml:
            raise KeyError("Could not find path to map_enemy_groups in Project.snake.") from e
        else:
            raise KeyError(f"Could not read data of map enemy group {i[0]}.") from e
        
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Could not find the file at {data.getResourcePath('eb.MapEnemyModule', 'map_enemy_groups')}.") from e

def readEnemyGroups(data: ProjectData):
    """Read project enemy groups"""
    try:
        hasLoadedYml = False
        enemyGroups = []
        path = data.getResourcePath("eb.EnemyModule", "enemy_groups")
        with open(path, encoding="utf-8") as enemy_groups:
            enemy_groups = yaml.load(enemy_groups, Loader=yaml.CSafeLoader)
            hasLoadedYml = True
            for i in enemy_groups.items():
                enemyGroups.append(EnemyGroup(i[0], i[1]["Background 1"], i[1]["Background 2"], i[1]["Enemies"],
                                              i[1]["Fear event flag"], i[1]["Fear mode"], i[1]["Letterbox Size"]))

        data.enemyGroups = enemyGroups

    except KeyError as e:
        if not hasLoadedYml:
            raise KeyError("Could not find path to enemy_groups in Project.snake.") from e
        else:
            raise KeyError(f"Could not read data of enemy group {i[0]}.") from e
        
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Could not find the file at {data.getResourcePath('eb.EnemyModule', 'enemy_groups')}.") from e
    
    
def readEnemySprites(data: ProjectData):
    """We DEFINITELY don't need to load all the enemy config, so just get a list of their sprites"""
    try:
        hasLoadedYml = False
        enemySprites = []
        path = data.getResourcePath("eb.EnemyModule", "enemy_configuration_table")
        with open(path, encoding="utf-8") as enemy_configuration_table:
            enemy_configuration_table = yaml.load(enemy_configuration_table, Loader=yaml.CSafeLoader)
            hasLoadedYml = True
            for i in enemy_configuration_table.items():       
                enemySprites.append(int(i[1]["Overworld Sprite"]))

        data.enemySprites = enemySprites

    except KeyError as e:
        if not hasLoadedYml:
            raise KeyError("Could not find path to enemy_configuration_table in Project.snake.") from e
        else:
            raise KeyError(f"Could not read data of enemy {i[0]}.") from e
        
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Could not find the file at {data.getResourcePath('eb.EnemyModule', 'enemy_configuration_table')}.") from e
    
def readBattleSprites(data: ProjectData):
    try:
        battleSprites = []
        readingIds = False
        for i in data.projectSnake["resources"]["eb.EnemyModule"].items():
            readingIds = True
            if str(i[0]).split("/")[0] == "BattleSprites": # cursed but i dont know how 
                sprPath = os.path.normpath(os.path.join(data.dir, i[1]))
                sprImg = ImageQt.ImageQt(Image.open(sprPath).convert("RGBA"))
                battleSprites.append(BattleSprite(int(str(i[0]).split("/")[1].split("png")[0]), sprImg)) # VERY cursed

        data.battleSprites = battleSprites

    except KeyError as e:
        if readingIds:
            raise KeyError(f"Could not get path of {i[1]} in Project.snake.") from e
        else:
            raise KeyError("Could not get battle sprite path listing in Project.snake")
        
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Could not find the file of {i[1]} specified in Project.snake.") from e
    
def readHotspots(data: ProjectData):
    try:
        hasLoadedYml = False
        hotspots = []
        path = data.getResourcePath("eb.MiscTablesModule", "map_hotspots")
        with open(path, encoding="utf-8") as map_hotspots:
            map_hotspots = yaml.load(map_hotspots, Loader=yaml.CSafeLoader)
            hasLoadedYml = True
            for i in map_hotspots.items():    
                start = EBCoords.fromWarp(i[1]["X1"], i[1]["Y1"])
                end = EBCoords.fromWarp(i[1]["X2"], i[1]["Y2"])
                
                if "EBME_Colour" in i[1]:
                    colourRaw = i[1]["EBME_Colour"]
                    if isinstance(colourRaw, list):
                        colour = colourRaw
                    else:    
                        colour = (int(colourRaw[1:3], 16), int(colourRaw[3:5], 16), int(colourRaw[5:7], 16))
                else:
                    colour = None
                if "EBME_Comment" in i[1]:
                    comment = i[1]["EBME_Comment"]
                else:
                    comment = None
                
                if colour:
                    hotspots.append(Hotspot(i[0], start, end, colour=colour, comment=comment))
                else:
                    hotspots.append(Hotspot(i[0], start, end, comment=comment))

        data.hotspots = hotspots

    except KeyError as e:
        if not hasLoadedYml:
            raise KeyError("Could not find path to map_hotspots in Project.snake.") from e
        else:
            raise
        
def readWarps(data: ProjectData):
    try:
        hasLoadedYml = False
        warps = []
        path = data.getResourcePath("eb.MiscTablesModule", "teleport_destination_table")     
        with open(path, encoding="utf-8") as warp_table:
            warp_table = yaml.load(warp_table, Loader=yaml.CSafeLoader)
            hasLoadedYml = True
            for i in warp_table.items():
                if "EBME_Comment" in i[1]:
                    comment = i[1]["EBME_Comment"]
                else:
                    comment = None
                warps.append(Warp(i[0], EBCoords.fromWarp(i[1]["X"], i[1]["Y"]), i[1]["Direction"], i[1]["Warp Style"], i[1]["Unknown"], comment))
                
            data.warps = warps
    except KeyError as e:
        if not hasLoadedYml:
            raise KeyError("Could not find path to teleport_destination_table in Project.snake.") from e
        else:
            raise
        
def readTeleports(data: ProjectData):
    try:
        hasLoadedYml = False
        teleports = []
        path = data.getResourcePath("eb.MiscTablesModule", "psi_teleport_dest_table")
        with open(path, encoding="utf-8") as teleport_table:
            teleport_table = yaml.load(teleport_table, Loader=yaml.CSafeLoader)
            hasLoadedYml = True
            for i in teleport_table.items():
                teleports.append(Teleport(i[0], EBCoords.fromWarp(i[1]["X"], i[1]["Y"]), i[1]["Event Flag"], i[1]["Name"]))
                
            data.teleports = teleports
    except KeyError as e:
        if not hasLoadedYml:
            raise KeyError("Could not find path to psi_teleport_dest_table in Project.snake.") from e
        raise
        
def readMapMusic(data: ProjectData):
    try:
        hasLoadedYml = False
        hiearchies = []
        path = data.getResourcePath("eb.MapMusicModule", "map_music")
        with open(path, encoding="utf-8") as map_music:
            map_music = yaml.load(map_music, Loader=yaml.CSafeLoader)
            hasLoadedYml = True
            for i in map_music.items():
                current = MapMusicHierarchy(i[0])
                hiearchies.append(current)
                for j in i[1]:
                    current.addEntry(MapMusicEntry(j["Event Flag"], j["Music"]))
            
            data.mapMusic = hiearchies
    except KeyError as e:
        if not hasLoadedYml:
            raise KeyError("Could not find path to map_music in Project.snake") from e
        raise