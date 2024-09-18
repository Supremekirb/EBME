import logging
import os
import shutil
import traceback
from io import StringIO

import yaml

import src.misc.common as common
from src.coilsnake.project_data import ProjectData
from src.objects import trigger


def writeDirectory(parent, data):
    try:
        try:
            saveProject(data)
        except Exception as e:
            parent.returns.emit({"title": "Failed to save Project.snake",
                                 "text": "Could not save Project.snake.",
                                 "info": str(e)})
            raise
        parent.updates.emit("Saving tilesets...")
        try:
            saveTilesets(data)
        except Exception as e:
            parent.returns.emit({"title": "Failed to save tilesets",
                                 "text": "Could not save tilesets.",
                                 "info": str(e)})
            raise
        parent.updates.emit("Saving sectors...")
        try:
            saveSectors(data)
        except Exception as e:
            parent.returns.emit({"title": "Failed to save sectors",
                                 "text": "Could not save sectors.",
                                 "info": str(e)})
            raise
        parent.updates.emit("Saving tiles...")
        try:
            saveTiles(data)
        except Exception as e:
            parent.returns.emit({"title": "Failed to save tiles",
                                 "text": "Could not save tiles.",
                                 "info": str(e)})
            raise
        parent.updates.emit("Saving NPCs...")
        try:
            saveNPCTable(data)
        except Exception as e:
            parent.returns.emit({"title": "Failed to save NPCs",
                                 "text": "Could not save NPCs.",
                                 "info": str(e)})
            raise
        parent.updates.emit("Saving NPC instances...")
        try:
            saveNPCInstances(data)
        except Exception as e:
            parent.returns.emit({"title": "Failed to save NPC instances",
                                 "text": "Could not save NPC instances.",
                                 "info": str(e)})
            raise
        parent.updates.emit("Saving triggers...")
        try:
            saveTriggers(data)
        except Exception as e:
            parent.returns.emit({"title": "Failed to save triggers",
                                 "text": "Could not save triggers.",
                                 "info": str(e)})
            raise
        parent.updates.emit("Saving enemies...")
        try:
            saveEnemyPlacements(data)
        except Exception as e:
            parent.returns.emit({"title": "Failed to save enemies",
                                 "text": "Could not save enemies.",
                                 "info": str(e)})
            raise
        try:
            saveMapEnemyGroups(data)
        except Exception as e:
            parent.returns.emit({"title": "Failed to save map enemy groups",
                                 "text": "Could not save map enemy groups.",
                                 "info": str(e)})
            raise
        
        parent.updates.emit("Saving hotspots...")
        try:
            saveHotspots(data)
        except Exception as e:
            parent.returns.emit({"title": "Failed to save hotspots",
                                 "text": "Could not save hotspots.",
                                 "info": str(e)})
            
        parent.updates.emit("Saving warps...")
        try:
            saveWarps(data)
        except Exception as e:
            parent.returns.emit({"title": "Failed to save warps",
                                 "text": "Could not save warps.",
                                 "info": str(e)})
        
        parent.updates.emit("Saving teleports...")
        try:
            saveTeleports(data)
        except Exception as e:
            parent.returns.emit({"title": "Failed to save teleports",
                                 "text": "Could not save teleports.",
                                 "info": str(e)})

        parent.updates.emit("Saving music...")
        try:
            saveMapMusic(data)
        except Exception as e:
            parent.returns.emit({"title": "Failed to save map music",
                                 "text": "Could not save map music.",
                                 "info": str(e)})

        logging.info(f"Successfully saved project at {data.dir}")
        parent.returns.emit(True)

    except Exception:
        logging.warning(traceback.format_exc())
        raise

def saveProject(data: ProjectData):
    project = data.projectSnake
    try:
        with open(os.path.normpath(os.path.join(data.dir, "Project.snake")), "w") as file:
            yaml.dump(project, file, Dumper=yaml.CSafeDumper, default_flow_style=None, sort_keys=False)
    except Exception as e:
        raise Exception(f"Could not write Project.snake to {os.path.normpath(os.path.join(data.dir, 'Project.snake'))}.") from e

def saveTilesets(data: ProjectData):
    # big note: this heavily relies on how the raw data is saved within each class when it doesnt need to be. make conversion functions.
    for i in data.tilesets:
        fts_file = StringIO()
        try:
            for m in i.minitiles:
                fts_file.write(''.join(str(px) for px in m.background) + "\n")
                fts_file.write(''.join(str(px) for px in m.foreground) + "\n")
                fts_file.write("\n")
            
            fts_file.write("\n")

            for p in i.palettes:
                fts_file.write(p.raw)
            
            fts_file.write("\n\n")

            for t in i.tiles:
                fts_file.write(t.tile)

            for _ in range(common.MAXTILES, 1024):
                # bunch of empty tiles needed
                fts_file.write("000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000\n")
        except Exception as e:
            raise Exception(f"Could not convert tileset {i.id:02d} to .fts format.") from e

        try:
            fts_file.seek(0)
            with open(data.getResourcePath('eb.TilesetModule', f'Tilesets/{i.id:02d}'), "w") as file:
                shutil.copyfileobj(fts_file, file)
        except Exception as e:
            raise Exception(f"Could not write tileset {i.id:02d} at {os.path.normpath(data.getResourcePath('eb.TilesetModule', f'Tilesets/{i.id:02d}'))}.") from e

def saveSectors(data: ProjectData):
    try:
        sector_yml = {}
        for column in data.sectors:
            for s in column:
                sector_yml[s.id] = {
                    "Item": s.item,
                    "Palette": s.palette,
                    "Town Map X": s.townmapx,
                    "Town Map Y": s.townmapy,
                    "Town Map Arrow": s.townmaparrow,
                    "Music": s.music,
                    "Setting": s.setting,
                    "Town Map Image": s.townmapimage,
                    "Town Map": s.townmap,
                    "Teleport": s.teleport,
                    "Tileset": s.palettegroup,
                }
    except Exception as e:
        raise Exception(f"Could not convert sectors to .yml format.") from e
    
    try:
        with open(data.getResourcePath('eb.MapModule', 'map_sectors'), "w") as file:
            yaml.dump(sector_yml, file, Dumper=yaml.CSafeDumper, default_flow_style=False, sort_keys=False)
    except Exception as e:
        raise Exception(f"Could not write sectors to {os.path.normpath(data.getResourcePath('eb.MapModule', 'map_sectors'))}.") from e

def saveTiles(data: ProjectData):
    map = StringIO()
    try:
        for column in data.tiles:
            for row in column:
                map.write(hex(row.tile)[2:].zfill(3))
                map.write(" ")

            offset = map.tell()
            map.seek(offset-1, 0) # remove extra space at end of each row. can't use .seek(-1, 1) because we aren't in byte mode and i dont wanna figure that out
            map.write("\n")
    except Exception as e:
        raise Exception("Could not convert map tiles to .map format.") from e

    try:
        map.seek(0)
        with open(data.getResourcePath('eb.MapModule', 'map_tiles'), "w") as file:
            shutil.copyfileobj(map, file)
    except Exception as e:
        raise Exception(f"Could not write map tiles to {os.path.normpath(data.getResourcePath('eb.MapModule', 'map_tiles'))}.") from e
        
def saveNPCTable(data: ProjectData):
    try:
        npc_yml = {}
        for n in data.npcs:
            npc_yml[n.id] = {
                "Direction": n.direction,
                "Event Flag": n.flag,
                "Movement": n.movement,
                "Show Sprite": n.show,
                "Sprite": n.sprite,
                "Text Pointer 1": n.text1,
                "Text Pointer 2": n.text2,
                "Type": n.type,
                "EBME_Comment": n.comment if n.comment != "" else None,
            }
    except Exception as e:
        raise Exception(f"Could not convert NPCs to .yml format.") from e

    try:
        try:
            path = data.getResourcePath('eb.MiscTablesModule', 'npc_config_table')
        except KeyError:
            path = data.getResourcePath('eb.ExpandedTablesModule', 'npc_config_table')
        with open(path, "w") as file:
            yaml.dump(npc_yml, file, Dumper=yaml.CSafeDumper, default_flow_style=False, sort_keys=False)
    except Exception as e:
        raise Exception(f"Could not write NPCs to {os.path.normpath(path)}.") from e
        

def saveNPCInstances(data: ProjectData):
    try:
        instances_yml = {}
        for c in range(40):
            instances_yml[c] = {}
            for r in range(32):
                instances_yml[c][r] = []

        for i in data.npcinstances:
            pos = i.posToMapSpritesFormat()
            instances_yml[pos[1]][pos[0]].append({
                "NPC ID": i.npcID,
                "X": pos[2],
                "Y": pos[3]
            })
        
        for c in range(40):
            for r in range(32):
                if instances_yml[c][r] == []: instances_yml[c][r] = None

    except Exception as e:
        raise Exception(f"Could not convert NPC instances to .yml format.") from e

    try:
        with open(data.getResourcePath('eb.MapSpriteModule', 'map_sprites'), "w") as file:
            yaml.dump(instances_yml, file, Dumper=yaml.CSafeDumper, default_flow_style=None, sort_keys=False)
    except Exception as e:
        raise Exception(f"Could not write NPC instances to {os.path.normpath(data.getResourcePath('eb.MapSpriteModule', 'map_sprites'))}.") from e
    
def saveTriggers(data: ProjectData):
    try:
        triggers_yml = {}
        for c in range(40):
            triggers_yml[c] = {}
            for r in range(32):
                triggers_yml[c][r] = []
        
        for i in data.triggers:
            buildDict = {}

            pos = i.posToMapDoorsFormat()

            buildDict["X"] = pos[2]
            buildDict["Y"] = pos[3]

            match type(i.typeData):
                case trigger.TriggerDoor:
                    buildDict["Type"] = "door"
                    buildDict["Destination X"] = i.typeData.destCoords.coordsWarp()[0]
                    buildDict["Destination Y"] = i.typeData.destCoords.coordsWarp()[1]
                    buildDict["Direction"] = i.typeData.dir
                    buildDict["Event Flag"] = i.typeData.flag
                    buildDict["Style"] = i.typeData.style
                    buildDict["Text Pointer"] = i.typeData.textPointer
                case trigger.TriggerEscalator:
                    buildDict["Type"] = "escalator"
                    buildDict["Direction"] = i.typeData.direction
                case trigger.TriggerLadder:
                    buildDict["Type"] = "ladder"
                case trigger.TriggerObject:
                    buildDict["Type"] = "object"
                    buildDict["Text Pointer"] = i.typeData.textPointer
                case trigger.TriggerPerson:
                    buildDict["Type"] = "person"
                    buildDict["Text Pointer"] = i.typeData.textPointer
                case trigger.TriggerRope:
                    buildDict["Type"] = "rope"
                case trigger.TriggerStairway:
                    buildDict["Type"] = "stairway"
                    buildDict["Direction"] = i.typeData.direction
                case trigger.TriggerSwitch:
                    buildDict["Type"] = "switch"
                    buildDict["Event Flag"] = i.typeData.flag
                    buildDict["Text Pointer"] = i.typeData.textPointer

            triggers_yml[pos[1]][pos[0]].append(buildDict)

        for c in range(40):
            for r in range(32):
                if triggers_yml[c][r] == []: triggers_yml[c][r] = None

    except Exception as e:
        raise Exception(f"Could not convert triggers to .yml format.") from e

    try:
        with open(data.getResourcePath('eb.DoorModule', 'map_doors'), "w") as file:
            yaml.dump(triggers_yml, file, Dumper=yaml.CSafeDumper, default_flow_style=None, sort_keys=False)
    except Exception as e:
        raise Exception(f"Could not write triggers to {os.path.normpath(data.getResourcePath('eb.DoorModule', 'map_doors'))}.") from e
    
def saveEnemyPlacements(data: ProjectData):
    try:
        placements_yml = {}
        placements_list = data.enemyPlacements.flat
        for i in range(len(placements_list)):
            placements_yml[i] = {
                "Enemy Map Group": placements_list[i].groupID,
            }
    except Exception as e:
        raise Exception(f"Could not convert enemy placements to .yml format.") from e
    
    try:
        with open(data.getResourcePath('eb.MapEnemyModule', 'map_enemy_placement'), "w") as file:
            yaml.dump(placements_yml, file, Dumper=yaml.CSafeDumper, default_flow_style=False, sort_keys=False)
    except Exception as e:
        raise Exception(f"Could not write enemy placements to {os.path.normpath(data.getResourcePath('eb.MapEnemyModule', 'map_enemy_placement'))}.") from e
    
def saveMapEnemyGroups(data: ProjectData):
    try:
        groups_yml = {}
        for i in data.enemyMapGroups:
            subGroup1 = {}
            for id, values in i.subGroup1.items():
                if values["Enemy Group"] == 0 and values["Probability"] == 0:
                    continue
                else:
                    subGroup1[id] = values
                    
            subGroup2 = {}
            for id, values in i.subGroup2.items():
                if values["Enemy Group"] == 0 and values["Probability"] == 0:
                    continue
                else:
                    subGroup2[id] = values
            
            groups_yml[data.enemyMapGroups.index(i)] = {
                "Event Flag": i.flag,
                "Sub-Group 1": subGroup1,
                "Sub-Group 1 Rate": i.subGroup1Rate,
                "Sub-Group 2": subGroup2,
                "Sub-Group 2 Rate": i.subGroup2Rate,
                "EBME_Colour": "#{0:02x}{1:02x}{2:02x}".format(i.colour[0], i.colour[1], i.colour[2])
            }
        
    except Exception as e:
        raise Exception("Could not convert map enemy groups to .yml format") from e
    
    try:
        with open(data.getResourcePath('eb.MapEnemyModule', 'map_enemy_groups'), "w") as file:
            yaml.dump(groups_yml, file, Dumper=yaml.CSafeDumper, default_flow_style=None, sort_keys=False)
    except Exception as e:
        raise Exception(f"Could not write map enemy groups to {os.path.normpath(data.getResourcePath('eb.MapEnemyModule', 'map_enemy_groups'))}.") from e

def saveHotspots(data: ProjectData):
    try:
        hotspots_yml = {}
        for i in data.hotspots:
            hotspots_yml[i.id] = {
                "Y1": i.start.coordsWarp()[1],
                "X1": i.start.coordsWarp()[0],
                "Y2": i.end.coordsWarp()[1],
                "X2": i.end.coordsWarp()[0],
                "EBME_Colour": "#{0:02x}{1:02x}{2:02x}".format(i.colour[0], i.colour[1], i.colour[2]),
                "EBME_Comment": i.comment if i.comment != "" else None
            }
    except Exception as e:
        raise Exception("Could not convert hotspots to .yml format") from e
    
    try:
        with open(data.getResourcePath('eb.MiscTablesModule', 'map_hotspots'), "w") as file:
            yaml.dump(hotspots_yml, file, Dumper=yaml.CSafeDumper, default_flow_style=None, sort_keys=False)
    except Exception as e:
        raise Exception(f"Could not write hotspots to {os.path.normpath(data.getResourcePath('eb.MiscTablesModule', 'map_hotspots'))}.") from e
    
def saveWarps(data: ProjectData):
    try:
        warps_yml = {}
        for i in data.warps:
            warps_yml[i.id] = {
                "Direction": i.dir,
                "Unknown": i.unknown,
                "Warp Style": i.style,
                "X": i.dest.coordsWarp()[0],
                "Y": i.dest.coordsWarp()[1],
                "EBME_Comment": i.comment,
            }
    except Exception as e:
        raise Exception("Could not convert warps to .yml format") from e
    
    try:
        with open(data.getResourcePath('eb.MiscTablesModule', 'teleport_destination_table'), "w") as file:
            yaml.dump(warps_yml, file, Dumper=yaml.CSafeDumper, default_flow_style=None, sort_keys=False)
    except Exception as e:
        raise Exception(f"Could not write hotspots to {os.path.normpath(data.getResourcePath('eb.MiscTablesModule', 'teleport_destination_table'))}.") from e 
    
def saveTeleports(data: ProjectData):
    try:
        teleports_yml = {}
        for i in data.teleports:
            teleports_yml[i.id] = {
                "Event Flag": i.flag,
                "Name": i.name,
                "X": i.dest.coordsWarp()[0],
                "Y": i.dest.coordsWarp()[1]
            }
    except Exception as e:
        raise Exception("Could not convert teleports to .yml format") from e
    
    try:
        with open(data.getResourcePath('eb.MiscTablesModule', 'psi_teleport_dest_table'), "w") as file:
            yaml.dump(teleports_yml, file, Dumper=yaml.CSafeDumper, default_flow_style=None, sort_keys=False)
    except Exception as e:
        raise Exception(f"Could not write teleports to {os.path.normpath(data.getResourcePath('eb.MiscTablesModule', 'psi_teleport_dest_table'))}.") from e

def saveMapMusic(data: ProjectData):
    try:
        music_yml = {}
        for i in data.mapMusic:
            entries = []
            for j in i.entries:
                entries.append({"Event Flag": j.flag,
                                "Music": j.music})
            music_yml[i.id] = entries
            
    except Exception as e:
        raise Exception("Could not convert map music to .yml format") from e
    
    try:
        with open(data.getResourcePath('eb.MapMusicModule', 'map_music'), "w") as file:
            yaml.dump(music_yml, file, Dumper=yaml.CSafeDumper, default_flow_style=None, sort_keys=False)
    except Exception as e:
        raise Exception(f"Could not write map music to {os.path.normpath(data.getResourcePath('eb.MapMusicModule', 'map_music'))}.") from e