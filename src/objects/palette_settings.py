from src.coilsnake.fts_interpreter import Palette


class PaletteSettings:
    def __init__(self, flag: int, flashEffect: int, spritePalette: int):
        self.flag = flag
        self.flashEffect = flashEffect
        self.spritePalette = spritePalette
        
        self.palette: Palette|None = None
        self.child: PaletteSettings|None = None
        
    def addChild(self, child: "PaletteSettings", palette: Palette):
        self.child = child
        self.child.palette = palette
        
    def removeChild(self):
        child = self.child
        while child != None: # recursively remove children and children's children
            child = child.child
            child.child = None
            child.palette = None