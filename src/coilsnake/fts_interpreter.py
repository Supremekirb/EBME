import functools

from PIL import Image, ImageOps

from src.misc.exceptions import NotBase32Error, NotHexError


class FullTileset:
    """An .fts file. Includes minitile, palette, and tile data, the minitile and tile data being shared with multiple tilesets."""
    def __init__(self, contents, id):
        self.contents = contents

        self.id = id
        self.interpretFTS()
    
    def verify_hex(self, val):
        str_ = str(val)
        try:
            int(str_, 16)
        except ValueError as e:
            raise NotHexError from e
    
    def verify_b32(self, val):
        try:
            str_ = str(val)
            int(str_, 32)
        except ValueError as e:
            raise NotBase32Error from e

    def getPaletteGroup(self, groupID):
        """From a palette group ID, get a PaletteGroup object\n\nReturns -1 if no match was found"""
        for i in self.paletteGroups:
            if i.groupID == groupID:
                return i
        return -1

    def getPalette(self, groupID, paletteID):
        """From a palette group ID and palette ID, get a Palette object\n\nReturns -1 if no match was found"""
        for i in self.palettes:
            if (i.groupID == groupID) and (i.paletteID == paletteID):
                return i
        return -1
            
    def getTilesetFromPaletteGroup(self, groupID):
        """From a palette group ID, get a Tileset ID\n\nReturns -1 if no match was found"""
        for i in self.paletteGroups:
            if i.groupID == groupID:
                return self.id
        return -1

    def interpretMinitiles(self, fts):
        """From an .fts file, read the data of all 512 minitiles.
        ### Returns
        `minitiles` - a list of Minitile objects"""
        minitiles = []
        for t in range(0, 512*3, 3): # 512 minitiles per tileset, three lines per minitile
            bg = []
            fg = []
            for i in range(0, 32*2, 1): # 32 bytes per bitmap (byte = 2 characters)
                # verify data
                self.verify_hex(fts[t][i])
                self.verify_hex(fts[t+1][i])

                bg.append(fts[t][i]) # handle background and foreground iteration all at once
                fg.append(fts[t+1][i])
        
            minitiles.append(Minitile(bg, fg)) # create list of minitiles
            
        return minitiles

    def interpretPalettes(self, fts):
        """From an .fts file, read the data of the various palettes.
        ### Returns
        `palettes` - a list of Palette objects"""
        palettes = []

        offset = 1537 # all .fts files start palettes here
        while fts[offset] != "\n": # palette listing is of variable length, so check it until we hit a whitespace gap
            # verify that data is in base 32
            self.verify_b32(fts[offset])
            palettes.append(Palette(fts[offset])) # create list of palettes
            offset+=1
        
        self.tileOffset = offset+2 # 2 newlines at end of this block + save this for interpreting tiles as they don't start at a consistent location
        return palettes   

    def buildPaletteGroups(self):
        """Group palettes of the same ID together.
        ### Returns
        `paletteGroups` - a list of PaletteGroup objects"""

        oldID = self.palettes[0].groupID
        groupBuilder = []
        groupList = []
        for i in self.palettes:
            if i.groupID == oldID:
                groupBuilder.append(i)

            else:
                groupList.append(PaletteGroup(groupBuilder))
                groupBuilder = []
                groupBuilder.append(i)
                oldID = i.groupID

        groupList.append(PaletteGroup(groupBuilder)) # add the final group too
        return groupList      

    def interpretTiles(self, fts):
        """From an .fts file, read the data of all <=960 tiles.
        ### Returns
           `tiles` - a list of Tile ob6jects"""
        tiles = []
        # verify tiles
        for i in range(self.tileOffset, self.tileOffset+960):
            self.verify_hex(fts[i])
            tiles.append(Tile(fts[i]))

        return tiles

    def interpretFTS(self):
        """Collection of functions to initialise fts content - minitiles, palettes, and tiles."""
        self.minitiles = self.interpretMinitiles(self.contents)
        self.palettes = self.interpretPalettes(self.contents)
        self.paletteGroups = self.buildPaletteGroups()
        self.tiles = self.interpretTiles(self.contents)


class PaletteGroup:
    """A collection of palettes in a tileset
    ### Parameters
        `palettes` - a list of Palette objects (of the same ID)"""
    def __init__(self, palettes):
        self.palettes = palettes
        self.groupID = palettes[0].groupID
    

class Palette:
    """A single palette in an .fts file, including a collection of Subpalette objects
    ### Parameters
        `palette` - raw palette from an .fts file"""
    def __init__(self, palette):
        self.groupID = int(palette[0], 32) # base 32 number, convert to int
        self.paletteID = int(palette[1], 32) # same
        self.subpalettes = []

        # build subpalette list on init (we'll use it all the time anyway)
        for subpalette in range(6):
            offset = subpalette*48+2
            buildSub = []
            for entry in range(0, 16*3, 3): 
                buildSub.append((palette[offset+entry] + palette[offset+entry+1] + palette[offset+entry+2])) # R, G, B out of base 32
            self.subpalettes.append(Subpalette(buildSub))

        self.raw = palette
    
    def getSubpalette(self, id):
        return self.subpalettes[id]


class Subpalette:
    """A single subpalette in an .fts file
    ### Parameters
        `subpalette` - raw subpalette from an .fts file palette"""
    def __init__(self, subpalette):
        self.subpalette = subpalette
        self.subpaletteRGBA = []

        for entry in range(16):  # create RGBA list too
            if entry == 0: self.subpaletteRGBA.append((int(str(self.subpalette[entry][0]), 32)*8, int(str(self.subpalette[entry][1]), 32)*8, int(str(self.subpalette[entry][2]), 32)*8, 0)) # alpha channel = 0 for first colour
            else: self.subpaletteRGBA.append((int(str(self.subpalette[entry][0]), 32)*8, int(str(self.subpalette[entry][1]), 32)*8, int(str(self.subpalette[entry][2]), 32)*8, 255)) # R, G, B out of base 32 + A

    @functools.lru_cache(maxsize=5000)
    def getSubpaletteColourRGBA(self, index):
        return self.subpaletteRGBA[int(index, 16)]


class Tile:
    """Collection of minitiles, along with collision data, palette metadata, and other SNES metadata for each."""
    def __init__(self, tile):

        self.tile = tile
        # make the proper data
        self.metadata = []
        self.collision = []

        for i in range(0, 96, 6):
            self.metadata.append(self.tile[i] + self.tile[i+1] + self.tile[i+2] + self.tile[i+3])
            self.collision.append(self.tile[i+4] + self.tile[i+5])
    
    def getMetadata(self, id):
        """Return the SNES metadata of a given minitile placement in a tile"""
        return int(self.metadata[id], 16)
        # We will extract the actual metadata in the other functions - see below
    
    def getMinitileID(self, id):
        """Get minitile ID from placement metadata"""
        metadata = self.getMetadata(id)
        return (metadata & 0x3FF) # minitile ID is bits 0-9
    
    def getMinitileSubpalette(self, id):
        """Get subpalette from placement metadata"""
        metadata = self.getMetadata(id)
        # TODO Verify that this fix for metadata avoidance causing backwards indexing in non-vanilla projects is correct
        # See DM with Gabbi about the issue (causing bright green tiles in EBBR)
        subPal = (((metadata & 0x1C00) >> 10)-2)
        if subPal < 0:
            return 0
        return subPal # minitile subpalette is bits 10-12 (bit 13 - priority flag - is irrelevant and never set in fts files). Subtract 2 because the first two are reserved for other things in the game, and we are indexing from 0

    def getMinitileHorizontalFlip(self, id):
        """Get horizontal flip flag from placement metadata"""
        metadata = self.getMetadata(id)
        return bool(((metadata & 0x4000) >> 14)) # minitile horizontal flip flag is bit 14
    
    def getMinitileVerticalFlip(self, id):
        """Get vertical flip flag from placement metadata"""
        metadata = self.getMetadata(id)
        return bool(((metadata & 0x8000) >> 15)) # minitile vertical flip flag is bit 15
    
    def getMinitileCollision(self, id):
        """Get collision data from placement metadata"""
        return self.collision[id]
    
    def getMinitileDataList(self):
        """Get a list of all minitile data.
        ### Returns
            `minitiles` - a list of minitile data, formatted like:\n
            [ID, subpalette, Hflip, Vflip, collision]\n
            Sixteen times in a list."""
        # TODO is it worth using a dictionary? they're slower but this is a mess
        
        build = []
        for i in range(16):
            subbuild = [] # it works OKAy
            subbuild.append(self.getMinitileID(i)) # TODO possibly reformat these functions - we grab metadata five separate times. why not pass it to them? or cache.
            subbuild.append(self.getMinitileSubpalette(i))
            subbuild.append(self.getMinitileHorizontalFlip(i))
            subbuild.append(self.getMinitileVerticalFlip(i))
            subbuild.append(self.getMinitileCollision(i))
            build.append(subbuild)
        return build
    
    def toImage(self, palette, fts):
        """Convert to a PIL Image"""
        # seems a little weird to pass the entire fts file, but it means we can cache it, which is significantly better for performance..!
        img = Image.new("RGB", (32, 32))
        x = 0
        y = 0
        for i in self.getMinitileDataList():
            minitile = fts.minitiles[i[0]].BothToImage(palette.subpalettes[i[1]])
            
            # debugging: check if the image contains (0, 248, 0)
            if (0, 248, 0, 255) in list(minitile.getdata()):
                pass
            
            if x == 32:
                x = 0
                y += 8

            if i[2] == True:
                minitile = ImageOps.mirror(minitile)
            if i[3] == True:
                minitile = ImageOps.flip(minitile)
            img.paste(minitile, (x, y))

            x += 8
        
        return img


class Minitile:
    """Raw bitmap graphics, 4bpp. No associated palette."""
    def __init__(self, background, foreground):
        self.background = background
        self.foreground = foreground

    @functools.lru_cache(maxsize=5000)
    def mapIndexToRGBABackground(self, subpalette):
        RGBAbuild = []
        for i in self.background:
            RGBAbuild.append(subpalette.getSubpaletteColourRGBA(i))

        return RGBAbuild
    
    @functools.lru_cache(maxsize=5000)
    def mapIndexToRGBAForeground(self, subpalette):
        RGBAbuild = []
        for i in self.foreground:
            RGBAbuild.append(subpalette.getSubpaletteColourRGBA(i))

        return RGBAbuild
        
    def BackgroundToImage(self, subpalette):
        """Convert raw bitmap graphics to a usable PIL Image.\n
        Just the background.
        ### Params
            `subpalette` - a Subpalette object
        ### Returns
            `img` - a PIL Image"""
        
        img = Image.new("RGBA", (8, 8))
        img.putdata(self.mapIndexToRGBABackground(subpalette))
        return img


    def ForegroundToImage(self, subpalette):
        """Convert raw bitmap graphics to a usable PIL Image.\n
        Just the foreground.
        ### Params
            `subpalette` - a Subpalette object
        ### Returns
            `img` - a PIL Image"""
        
        img = Image.new("RGBA", (8, 8))
        img.putdata(self.mapIndexToRGBAForeground(subpalette))
        return img
    
    @functools.lru_cache(maxsize=5000)
    def BothToImage(self, subpalette):
        """Convert raw bitmap graphics to a usable PIL Image.\n
        Foreground layers on background.
        ### Params
            `subpalette` - a Subpalette object
        ### Returns
            `img` - a PIL Image"""
        
        img = Image.new("RGBA", (8, 8))
        img.putdata(self.mapIndexToRGBABackground(subpalette))
        fg = self.ForegroundToImage(subpalette)
        img.paste(fg, (0, 0), fg)
        return img