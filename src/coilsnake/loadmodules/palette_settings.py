import src.misc.common as common
from src.coilsnake.fts_interpreter import Palette
from src.coilsnake.loadmodules.load_module import YMLCoilsnakeResourceLoadModule
from src.objects.palette_settings import PaletteSettings


class PaletteSettingsModule(YMLCoilsnakeResourceLoadModule):
    NAME = "palette settings"
    MODULE = "eb.TilesetModule"
    RESOURCE = "map_palette_settings"
    
    def _resourceLoad(data, map_palette_settings):
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