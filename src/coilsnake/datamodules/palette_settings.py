import src.misc.common as common
from src.coilsnake.datamodules.data_module import YMLResourceDataModule
from src.coilsnake.fts_interpreter import Palette
from src.coilsnake.project_data import ProjectData
from src.objects.palette_settings import PaletteSettings


class PaletteSettingsModule(YMLResourceDataModule):
    NAME = "palette settings"
    MODULE = "eb.TilesetModule"
    RESOURCE = "map_palette_settings"
    FLOW_STYLE = False
    
    def _resourceLoad(data: ProjectData, map_palette_settings):
        paletteSettings = {}
        
        for paletteGroup, palettes in map_palette_settings.items():
            paletteSettings[paletteGroup] = {}
            for palette, settings in palettes.items():
                root = PaletteSettings(settings["Event Flag"],
                                        settings["Flash Effect"],
                                        settings["Sprite Palette"])
                parent = root
                parentSettings = settings
                while "Event Palette" in parentSettings:
                    childSettings = parentSettings["Event Palette"]
                    child = PaletteSettings(childSettings["Event Flag"],
                                            childSettings["Flash Effect"],
                                            childSettings["Sprite Palette"])
                    try:
                        paletteObj = Palette(common.baseN(paletteGroup, 32) + common.baseN(palette, 32)
                                            + childSettings["Colors"])
                        parent.addChild(child, paletteObj)
                    except KeyError as e:
                        raise KeyError("Nested palette settings must contain a colour palette.") from e
                    
                    parent = child
                    parentSettings = childSettings
                
                paletteSettings[paletteGroup][palette] = root
        
        data.paletteSettings = paletteSettings
    
    
    def _resourceSave(data: ProjectData):
        settings_yml = {}
        for paletteGroup in data.paletteSettings.keys():
            settings_yml[paletteGroup] = {}
            for palette, settings in data.paletteSettings[paletteGroup].items():
                settings_yml[paletteGroup][palette] = {
                    "Event Flag": settings.flag,
                    "Flash Effect": settings.flashEffect,
                    "Sprite Palette": settings.spritePalette
                }
                key = settings_yml[paletteGroup][palette]
                nested = settings.child
                while nested:
                    key["Event Palette"] = {
                        "Colors": nested.palette.toRaw()[2:], # no id for palette/group in these, just raw colours
                        "Event Flag": nested.flag,
                        "Flash Effect": nested.flashEffect,
                        "Sprite Palette": nested.spritePalette
                    }
                    nested = nested.child
                    key = key["Event Palette"] # feels cursed but... works??
        
        return settings_yml