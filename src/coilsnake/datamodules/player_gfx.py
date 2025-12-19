import src.misc.common as common
from src.coilsnake.datamodules.data_module import YMLResourceDataModule
from src.coilsnake.project_data import ProjectData


class PlayerGFXModule(YMLResourceDataModule):
    NAME = "player character graphics"
    MODULE = "eb.MiscTablesModule"
    RESOURCE = "playable_char_gfx_table"
    
    def _resourceLoad(data: ProjectData, playable_char_gfx_table):
        gfx = {}
        gfx[common.PLAYERSPRITES.NORMAL] = playable_char_gfx_table[0]["Default Sprite Group"]
        gfx[common.PLAYERSPRITES.LADDER] = playable_char_gfx_table[0]["Ladder Sprite Group"]
        gfx[common.PLAYERSPRITES.ROPE] = playable_char_gfx_table[0]["Rope Sprite Group"]
        gfx[common.PLAYERSPRITES.TINY] = playable_char_gfx_table[0]["Tiny Sprite Group"]
        gfx[common.PLAYERSPRITES.ROBOT] = playable_char_gfx_table[0]["Robot Sprite Group"]
        # TODO - should probably make this (and other harcoded things?) configurable, with defaults to match vanilla and a reset button.
        gfx[common.PLAYERSPRITES.MAGICANT] = 6 # woo hardcoding! love earthbound
        data.playerSprites = gfx

    
    def save(data: ProjectData):
        return # this data is not saved