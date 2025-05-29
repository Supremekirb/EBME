from src.coilsnake.datamodules.battle_sprites import BattleSpriteModule
from src.coilsnake.datamodules.enemy_groups import EnemyGroupModule
from src.coilsnake.datamodules.enemy_map_groups import EnemyMapGroupModule
from src.coilsnake.datamodules.enemy_placements import EnemyPlacementsModule
from src.coilsnake.datamodules.enemy_sprites import EnemySpriteModule
from src.coilsnake.datamodules.hotspots import HotspotModule
from src.coilsnake.datamodules.map_changes import MapChangesModule
from src.coilsnake.datamodules.map_music import MapMusicModule
from src.coilsnake.datamodules.npc_instances import NPCInstanceModule
from src.coilsnake.datamodules.npcs import NPCModule
from src.coilsnake.datamodules.palette_settings import PaletteSettingsModule
from src.coilsnake.datamodules.player_gfx import PlayerGFXModule
from src.coilsnake.datamodules.project_snake import ProjectSnakeModule
from src.coilsnake.datamodules.sectors import SectorModule
from src.coilsnake.datamodules.spritefx import SpriteFXModule
from src.coilsnake.datamodules.sprites import SpriteModule
from src.coilsnake.datamodules.teleports import TeleportModule
from src.coilsnake.datamodules.tile_graphics import TileGraphicsModule
from src.coilsnake.datamodules.tiles import TileModule
from src.coilsnake.datamodules.tilesets import TilesetModule
from src.coilsnake.datamodules.triggers import TriggerModule
from src.coilsnake.datamodules.warps import WarpModule

# The order IS important. Modules are loaded in the order of this list.
# If a module depends on the data loaded by another, place it after the dependency.
MODULES = (ProjectSnakeModule,
           TilesetModule, PaletteSettingsModule, SectorModule, TileModule, 
           TileGraphicsModule, SpriteModule, PlayerGFXModule, SpriteFXModule, NPCModule, NPCInstanceModule, 
           TriggerModule, EnemyPlacementsModule, EnemyMapGroupModule, 
           EnemyGroupModule, EnemySpriteModule, BattleSpriteModule, HotspotModule,
           WarpModule, TeleportModule, MapMusicModule, MapChangesModule,)
