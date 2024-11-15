from PySide6.QtGui import QGuiApplication, QIcon, QPalette
from qtawesome import icon

# https://phosphoricons.com/
# (icons > v1.3 are not usable)
# or run qta-browser in your terminal

def init_icons():
    # we must defer the loading of icons until after a QApplication is created
    # is there a better way to make them globals...?
    
    # EB custom icons
    global EBICON_TILE
    global EBICON_SECTOR
    global EBICON_NPC 
    global EBICON_TRIGGER
    global EBICON_ENEMY
    global EBICON_HOTSPOT
    global EBICON_WARP
    global EBICON_COLLISION
    global EBICON_ALL
    global EBICON_GAME
    
    # check the background color of the app, if it's dark use the dark mode icons
    if QGuiApplication.palette().color(QPalette.ColorGroup.Normal, QPalette.ColorRole.Base).lightness() < 128:
        EBICON_TILE = QIcon(":/ui/modeTileDark.png")
        EBICON_SECTOR = QIcon(":/ui/modeSectorDark.png")
        EBICON_NPC = QIcon(":/ui/modeNPCDark.png")
        EBICON_TRIGGER = QIcon(":/ui/modeTriggerDark.png")
        EBICON_ENEMY = QIcon(":/ui/modeEnemyDark.png")
        EBICON_HOTSPOT = QIcon(":/ui/modeHotspotDark.png")
        EBICON_WARP = QIcon(":/ui/modeWarpDark.png")
        EBICON_COLLISION = QIcon(":/ui/modeCollisionDark.png")
        EBICON_ALL = QIcon(":/ui/modeAllDark.png")
        EBICON_GAME = QIcon(":/ui/modeGameDark.png")
    else:
        EBICON_TILE = QIcon(":/ui/modeTile.png")
        EBICON_SECTOR = QIcon(":/ui/modeSector.png")
        EBICON_NPC = QIcon(":/ui/modeNPC.png")
        EBICON_TRIGGER = QIcon(":/ui/modeTrigger.png")
        EBICON_ENEMY = QIcon(":/ui/modeEnemy.png")
        EBICON_HOTSPOT = QIcon(":/ui/modeHotspot.png")
        EBICON_WARP = QIcon(":/ui/modeWarp.png")
        EBICON_COLLISION = QIcon(":/ui/modeCollision.png")
        EBICON_ALL = QIcon(":/ui/modeAll.png")
        EBICON_GAME = QIcon(":/ui/modeGame.png")
    
    # phosphor icons
    global ICON_SAVE
    ICON_SAVE = icon("ph.floppy-disk")
    
    global ICON_LOAD
    ICON_LOAD = icon("ph.folder-open")
    
    global ICON_RELOAD
    ICON_RELOAD = icon("ph.arrows-clockwise")
    
    global ICON_SETTINGS
    ICON_SETTINGS = icon("ph.gear")
    
    global ICON_INFO
    ICON_INFO = icon("ph.info")
    
    global ICON_DEBUG
    ICON_DEBUG = icon("ph.terminal-window")
    
    global ICON_BUG
    ICON_BUG = icon("ph.bug-beetle")
    
    global ICON_DELETE
    ICON_DELETE = icon("ph.trash")
    
    global ICON_CUT
    ICON_CUT = icon("ph.scissors")
    
    global ICON_COPY
    ICON_COPY = icon("ph.copy")
    
    global ICON_PASTE
    ICON_PASTE = icon("ph.clipboard")
    
    global ICON_UNDO
    ICON_UNDO = icon("ph.arrow-counter-clockwise")
    
    global ICON_REDO
    ICON_REDO = icon("ph.arrow-clockwise")
    
    global ICON_UP
    ICON_UP = icon("ph.caret-up")
    
    global ICON_UP_DOUBLE
    ICON_UP_DOUBLE = icon("ph.caret-double-up")
    
    global ICON_DOWN
    ICON_DOWN = icon("ph.caret-down")
    
    global ICON_DOWN_DOUBLE
    ICON_DOWN_DOUBLE = icon("ph.caret-double-down")
    
    global ICON_SWAP
    ICON_SWAP = icon("ph.arrows-down-up", hflip=True) # to match copy arrows in tile editor
    
    global ICON_NEW
    ICON_NEW = icon("ph.plus")
    
    global ICON_EDIT
    ICON_EDIT = icon("ph.pencil-line")
    
    global ICON_CANCEL
    ICON_CANCEL = icon("ph.x")
    
    global ICON_CLEAR
    ICON_CLEAR = icon("ph.file-x")
    
    global ICON_RENDER_IMG
    ICON_RENDER_IMG = icon("ph.image")
    
    global ICON_ZOOM_IN
    ICON_ZOOM_IN = icon("ph.magnifying-glass-plus")
    
    global ICON_ZOOM_OUT
    ICON_ZOOM_OUT = icon("ph.magnifying-glass-minus")
    
    global ICON_IMPORT
    ICON_IMPORT = icon("ph.arrow-square-in")
    
    global ICON_EXPORT
    ICON_EXPORT = icon("ph.arrow-square-out")
    
    global ICON_WARNING
    ICON_WARNING = icon("ph.warning")
    
    global ICON_OK
    ICON_OK = icon("ph.check")
    
    global ICON_GRID
    ICON_GRID = icon("ph.grid-four")
    
    global ICON_FIND
    ICON_FIND = icon("ph.magnifying-glass")
    
    global ICON_FIX
    ICON_FIX = icon("ph.wrench")
    
    global ICON_COORDS
    ICON_COORDS = icon("ph.crosshair-simple")
    
    global ICON_SQUARE
    ICON_SQUARE = icon("ph.square")
    
    global ICON_RECT
    ICON_RECT = icon("ph.rectangle")
    
    global ICON_DIAMOND
    ICON_DIAMOND = icon("ph.diamond")
    
    global ICON_WALL
    ICON_WALL = icon("ph.wall")
    
    global ICON_SPLIT
    ICON_SPLIT = icon("ph.git-merge")
    
    global ICON_MUSIC_LIST
    ICON_MUSIC_LIST = icon("ph.playlist")
    
    global ICON_MUSIC
    ICON_MUSIC = icon("ph.music-note")
    
    global ICON_AUTO_REARRANGE
    ICON_AUTO_REARRANGE = icon("ph.swap")
    
    global ICON_TILESET
    ICON_TILESET = icon("ph.squares-four")
    
    global ICON_PALETTE_GROUP
    ICON_PALETTE_GROUP = icon("ph.swatches")
    
    global ICON_PALETTE
    ICON_PALETTE = icon("ph.palette")
    
    global ICON_SUBPALETTE
    ICON_SUBPALETTE = icon("ph.paint-brush")