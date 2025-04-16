from src.coilsnake.loadmodules.battle_sprites import BattleSpriteModule
from src.coilsnake.loadmodules.enemy_groups import EnemyGroupModule
from src.coilsnake.loadmodules.enemy_map_groups import EnemyMapGroupModule
from src.coilsnake.loadmodules.enemy_placements import EnemyPlacementsModule
from src.coilsnake.loadmodules.enemy_sprites import EnemySpriteModule
from src.coilsnake.loadmodules.hotspots import HotspotModule
from src.coilsnake.loadmodules.map_changes import MapChangesModule
from src.coilsnake.loadmodules.map_music import MapMusicModule
from src.coilsnake.loadmodules.npc_instances import NPCInstanceModule
from src.coilsnake.loadmodules.npcs import NPCModule
from src.coilsnake.loadmodules.palette_settings import PaletteSettingsModule
from src.coilsnake.loadmodules.sectors import SectorModule
from src.coilsnake.loadmodules.sprites import SpriteModule
from src.coilsnake.loadmodules.teleports import TeleportModule
from src.coilsnake.loadmodules.tile_graphics import TileGraphicsModule
from src.coilsnake.loadmodules.tiles import TileModule
from src.coilsnake.loadmodules.tilesets import TilesetModule
from src.coilsnake.loadmodules.triggers import TriggerModule
from src.coilsnake.loadmodules.warps import WarpModule
from src.coilsnake.loadmodules.project_snake import ProjectSnakeModule

# The order IS important. Modules are loaded in the order of this list.
# If a module depends on the data loaded by another, place it after the dependency.
MODULES = (ProjectSnakeModule,
           TilesetModule, PaletteSettingsModule, SectorModule, TileModule, 
           TileGraphicsModule, SpriteModule, NPCModule, NPCInstanceModule, 
           TriggerModule, EnemyPlacementsModule, EnemyMapGroupModule, 
           EnemyGroupModule, EnemySpriteModule, BattleSpriteModule, HotspotModule,
           WarpModule, TeleportModule, MapMusicModule, MapChangesModule,)
