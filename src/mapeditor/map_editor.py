import logging

import numpy
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import (QAction, QActionGroup, QGuiApplication, QImage,
                           QKeySequence, QPalette, QPixmap)
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGridLayout, QInputDialog,
                               QMenu, QProgressDialog, QSizePolicy, QTabWidget,
                               QUndoView, QWidget)

import src.mapeditor.map.map_scene as map_scene
import src.mapeditor.map.map_view as map_view
import src.mapeditor.sidebar.all_sidebar as all_sidebar
import src.mapeditor.sidebar.enemy_sidebar as enemy_sidebar
import src.mapeditor.sidebar.game_sidebar as game_sidebar
import src.mapeditor.sidebar.hotspot_sidebar as hotspot_sidebar
import src.mapeditor.sidebar.npc_sidebar as npc_sidebar
import src.mapeditor.sidebar.sector_sidebar as sector_sidebar
import src.mapeditor.sidebar.tile_sidebar as tile_sidebar
import src.mapeditor.sidebar.trigger_sidebar as trigger_sidebar
import src.mapeditor.sidebar.warp_sidebar as warp_sidebar
import src.mapeditor.status_bar as status_bar
import src.misc.common as common
import src.misc.debug as debug
from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords
from src.misc.dialogues import (AboutDialog, CoordsDialog, FindDialog,
                                RenderDialog, SettingsDialog)
from src.misc.map_music_editor import MapMusicEditor
from src.misc.widgets import BaseChangerSpinbox
from src.objects.enemy import EnemyTile
from src.objects.hotspot import Hotspot
from src.objects.npc import MapEditorNPC, NPCInstance
from src.objects.sector import Sector
from src.objects.trigger import Trigger
from src.objects.warp import MapEditorWarp, Teleport, Warp
from src.png2fts.png2fts_gui import png2ftsMapEditorGui


class MapEditor(QWidget):
    def __init__(self, parent, projectData: ProjectData):
        super().__init__(parent)
        
        self.projectData = projectData
        self.state = MapEditorState(self)

        self.scene = map_scene.MapEditorScene(self, self.state, self.projectData)
        self.view = map_view.MapEditorView(self, self.state, self.projectData, self.scene)
        self.view.centerOn(0, 0)
        
        self.setupUI()

        self.updateTabSize(0)
        self.scene.selectSector(EBCoords(0, 0))
        logging.info("Map editor initialised")

    def changeSidebarTab(self, index):
        self.updateTabSize(index)
        self.scene.changeMode(index)
        self.state.mode = index

    def updateTabSize(self, index):
        # https://stackoverflow.com/a/29138370
        for i in range(self.sidebar.count()):
            if i != index:
                self.sidebar.widget(i).setSizePolicy(QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred))
                # (Ignored, Preferred) means that the Y size will be fixed and the X will be dynamic
                # This is because the X has space to eat up (the map) but the Y doesn't
                # So the Y would otherwise modify window size which we don't want to do

        widget = self.sidebar.widget(index)
        widget.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred))
        widget.resize(widget.minimumSizeHint())
        widget.adjustSize()

    def dopng2fts(self):
        result = png2ftsMapEditorGui.dopng2fts(self, self.projectData)
        if result == 0: # cancelled
            return
        
        else:
            progressDialog = QProgressDialog("Importing new tileset...", "NONCANELLABLE", 0, 3, self)
            progressDialog.setCancelButton(None) # no cancel button
            progressDialog.setWindowFlag(Qt.WindowCloseButtonHint, False) # no system close button, either
            progressDialog.setWindowModality(Qt.WindowModal)
            progressDialog.setMinimumDuration(0)

            self.sidebarTile.tilesetSelect.setCurrentText(str(result[0]))
            self.sidebarTile.onTilesetSelect()

            progressDialog.setValue(1)

            progressDialog.setLabelText("Updating sectors...")
            progressDialog.setMaximum(len(self.projectData.sectors) * len(self.projectData.sectors[0]))
            progressDialog.setValue(0)
            for y in self.projectData.sectors:
                for s in y:
                    if s.tileset == result[0]: # refresh all sectors that use the tileset
                        self.scene.refreshSector(s.coords)
                    progressDialog.setValue(progressDialog.value() + 1)

            progressDialog.setLabelText("Finalising...")
            progressDialog.setValue(2)
            progressDialog.setMaximum(3)

            if len(result) > 1: # passed back map tiles and png
                with open(result[1].fileName()) as map_tiles:
                    tiles = map_tiles.read()
                    
                    tiles = [r.split(" ") for r in tiles.split("\n")]
                    del tiles[-1] # last newline causes issues

                    tiles = numpy.array(tiles)
                
                png = QGraphicsPixmapItem(QPixmap.fromImage(QImage(result[2])))
                progressDialog.setValue(3)

                self.scene.importpng2ftsMap(png, tiles, result[0])

            else:
                progressDialog.setValue(3)

    def doFind(self):
        result = FindDialog.findObject(self, self.projectData)
        if result:
            if isinstance(result, NPCInstance):
                self.sidebar.setCurrentIndex(common.MODEINDEX.NPC)
                self.state.currentNPCInstances = [result,]
                self.sidebarNPC.fromNPCInstances()
            elif isinstance(result, EnemyTile):
                self.sidebar.setCurrentIndex(common.MODEINDEX.ENEMY)
                self.state.currentEnemyTile = result.groupID
                self.sidebarEnemy.selectEnemyTile(result.groupID)
            elif isinstance(result, Hotspot):
                self.sidebar.setCurrentIndex(common.MODEINDEX.HOTSPOT)
                self.state.currentHotspot = result
                self.sidebarHotspot.fromHotspot()
                return self.view.autoCenterOn(result.start)
            elif isinstance(result, Warp):
                self.sidebar.setCurrentIndex(common.MODEINDEX.WARP)
                self.state.currentWarp = result
                self.sidebarWarp.fromWarp()
                return self.view.autoCenterOn(result.dest)
            elif isinstance(result, Teleport):
                self.sidebar.setCurrentIndex(common.MODEINDEX.WARP)
                self.state.currentWarp = result
                self.sidebarWarp.fromWarp()
                return self.view.autoCenterOn(result.dest)
                
            self.view.autoCenterOn(result.coords)

    def doGoto(self):
        coords = CoordsDialog.getCoords(self)
        if isinstance(coords, EBCoords):
            self.view.autoCenterOn(coords)

    def doGotoSector(self):
        result = QInputDialog.getInt(self, "Go to sector", "Sector ID:", 0,
                                     0, len(self.projectData.sectors)*len(self.projectData.sectors[1])-1, 1)

        if not result[1]:
            return
        
        id = result[0]        
        sector = self.projectData.sectorFromID(id)
        
        self.view.autoCenterOn(sector.coords)
    
    def renderMap(self, x1 = 0, y1 = 0, x2 = 0, y2 = 0, immediate = False):
        RenderDialog.renderMap(self, self.scene, x1, y1, x2, y2, immediate)
        
    def updateWindowTitle(self):
        title = self.window().windowTitle()
        if not self.scene.undoStack.isClean():
            if not title.endswith("*"):
                self.window().setWindowTitle(title + "*")
        else:
            if title.endswith("*"):
                self.window().setWindowTitle(title[:-1])

    def setupUI(self):
        self.view.setLayoutDirection(Qt.LayoutDirection.RightToLeft) # vert. scrollbar on left edge
        # also, allows the sidebar to eat up space

        self.status = status_bar.MapEditorStatus(self)

        self.sidebar = QTabWidget()
        self.sidebar.currentChanged.connect(self.changeSidebarTab)
       
        # check the background color of the app, if it's dark use the dark mode icons
        if QGuiApplication.palette().color(QPalette.ColorGroup.Normal, QPalette.ColorRole.Base).lightness() < 128:
            iconTile = QPixmap(":/ui/modeTileDark.png")
            iconSector = QPixmap(":/ui/modeSectorDark.png")
            iconNPC = QPixmap(":/ui/modeNPCDark.png")
            iconDoor = QPixmap(":/ui/modeDoorDark.png")
            iconEnemy = QPixmap(":/ui/modeEnemyDark.png")
            iconHotspot = QPixmap(":/ui/modeHotspotDark.png")
            iconWarp = QPixmap(":/ui/modeWarpDark.png")
            iconAll = QPixmap(":/ui/modeAllDark.png")
            iconGame = QPixmap(":/ui/modeGameDark.png")
        else:
            iconTile = QPixmap(":/ui/modeTile.png")
            iconSector = QPixmap(":/ui/modeSector.png")
            iconNPC = QPixmap(":/ui/modeNPC.png")
            iconDoor = QPixmap(":/ui/modeDoor.png")
            iconEnemy = QPixmap(":/ui/modeEnemy.png")
            iconHotspot = QPixmap(":/ui/modeHotspot.png")
            iconWarp = QPixmap(":/ui/modeWarp.png")
            iconAll = QPixmap(":/ui/modeAll.png")
            iconGame = QPixmap(":/ui/modeGame.png")

        # future modes / features
        # warps
        # psi teleport
        # map_music hierachy editor? doesnt exactly apply to map
        # map_changes

        self.sidebarTile = tile_sidebar.SidebarTile(self, self.state, self, self.projectData)
        self.sidebarSector = sector_sidebar.SidebarSector(self, self.state, self, self.projectData)
        self.sidebarNPC = npc_sidebar.SidebarNPC(self, self.state, self, self.projectData)
        self.sidebarTrigger = trigger_sidebar.SidebarTrigger(self, self.state, self, self.projectData)
        self.sidebarEnemy = enemy_sidebar.SidebarEnemy(self, self.state, self.projectData)
        self.sidebarHotspot = hotspot_sidebar.SidebarHotspot(self, self.state, self, self.projectData)
        self.sidebarWarp = warp_sidebar.SidebarWarp(self, self.state, self, self.projectData)
        self.sidebarAll = all_sidebar.SidebarAll(self, self.state, self, self.projectData)
        self.sidebarGame = game_sidebar.SidebarGame(self, self.state, self, self.projectData)

        self.sidebar.addTab(self.sidebarTile, iconTile, "Tile")
        self.sidebar.addTab(self.sidebarSector, iconSector, "Sector")
        self.sidebar.addTab(self.sidebarNPC, iconNPC, "NPC")
        self.sidebar.addTab(self.sidebarTrigger, iconDoor, "Trigger")
        self.sidebar.addTab(self.sidebarEnemy, iconEnemy, "Enemy")
        self.sidebar.addTab(self.sidebarHotspot, iconHotspot, "Hotspot")
        self.sidebar.addTab(self.sidebarWarp, iconWarp, "Warp && TP")
        self.sidebar.addTab(self.sidebarAll, iconAll, "View All")
        self.sidebar.addTab(self.sidebarGame, iconGame, "View Game")
        self.sidebar.setTabPosition(QTabWidget.TabPosition.West)
            
        self.menuFile = QMenu("&File")
        self.saveAction = QAction("&Save", shortcut=QKeySequence("Ctrl+S"))
        self.saveAction.triggered.connect(self.parent().saveAction.trigger)
        self.openAction = QAction("&Open", shortcut=QKeySequence("Ctrl+O"))
        self.openAction.triggered.connect(self.parent().openAction.trigger)
        self.reloadAction = QAction("&Reload", shortcut=QKeySequence("Ctrl+R"))
        self.reloadAction.triggered.connect(self.parent().reloadAction.trigger)
        self.openSettingsAction = QAction("Settings...")
        self.openSettingsAction.triggered.connect(lambda: SettingsDialog.openSettings(self))
        self.menuFile.addActions([self.saveAction, self.openAction, self.reloadAction])
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.openSettingsAction)        

        self.menuEdit = QMenu("&Edit")
        self.deleteAction = QAction("&Delete", shortcut=QKeySequence(Qt.Key.Key_Delete))
        self.deleteAction.triggered.connect(self.scene.onDelete)
        self.copyAction = QAction("&Copy", shortcut=QKeySequence("Ctrl+C"))
        self.copyAction.triggered.connect(self.scene.onCopy)
        self.cutAction = QAction("Cu&t", shortcut=QKeySequence("Ctrl+X"))
        self.cutAction.triggered.connect(self.scene.onCut)
        self.pasteAction = QAction("&Paste", shortcut=QKeySequence("Ctrl+V"))
        self.pasteAction.triggered.connect(self.scene.onPaste)
        self.undoAction = QAction("&Undo", shortcut=QKeySequence("Ctrl+Z"))
        self.undoAction.triggered.connect(self.scene.onUndo)
        self.redoAction = QAction("&Redo")
        self.redoAction.setShortcuts([QKeySequence("Ctrl+Y"), QKeySequence("Ctrl+Shift+Z")])
        self.redoAction.triggered.connect(self.scene.onRedo)
        self.cancelAction = QAction("C&ancel")
        self.cancelAction.setShortcuts([QKeySequence("Esc"), QKeySequence("Ctrl+D")])
        self.cancelAction.triggered.connect(self.scene.onCancel)
        self.menuEdit.addActions([self.deleteAction, self.cutAction, self.copyAction, self.pasteAction])
        self.menuEdit.addSeparator()
        self.menuEdit.addActions([self.undoAction, self.redoAction])
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.cancelAction)
        
        # hidden actions for sectors
        self.copyShiftAction = QAction("Copy", shortcut=QKeySequence("Ctrl+Shift+C"))
        self.addAction(self.copyShiftAction)
        self.copyShiftAction.triggered.connect(self.scene.copySelectedSectorAttributes)
        
        self.copyAltShiftAction = QAction("Copy", shortcut=QKeySequence("Ctrl+Alt+Shift+C"))
        self.addAction(self.copyAltShiftAction)
        self.copyAltShiftAction.triggered.connect(self.scene.copySelectedSectorPalettes)
        
        self.scene.undoStack.cleanChanged.connect(self.updateWindowTitle)

        self.menuView = QMenu("&View")
        settings = QSettings()
        self.zoomInAction = QAction("Zoom in")
        self.zoomInAction.setShortcuts([QKeySequence.StandardKey.ZoomIn, QKeySequence("Ctrl+=")])
        self.zoomInAction.triggered.connect(self.view.zoomIn)
        
        self.zoomOutAction = QAction("Zoom out", shortcut=QKeySequence.ZoomOut)
        self.zoomOutAction.triggered.connect(self.view.zoomOut)

        self.hexAction = QAction("Use &hexadecimal", shortcut=QKeySequence("Ctrl+H"))
        self.hexAction.setCheckable(True)
        self.hexAction.changed.connect(BaseChangerSpinbox.toggleMode)
        if settings.value("main/HexMode", type=bool):
            self.hexAction.trigger()

        settings.beginGroup("mapeditor")

        self.gridAction = QAction("Show &grid", shortcut=QKeySequence("Ctrl+G"))
        self.gridAction.setCheckable(True)
        self.gridAction.changed.connect(self.scene.toggleGrid) # ehhh... could this go somewhere else?
        if settings.value("ShowGrid") == "true":
            self.gridAction.setChecked(True)
            self.scene.grid.show()

        self.gridMenu = QMenu("Grid &style...")
        self.gridStyleActionGroup = QActionGroup(self.gridMenu)
        self.gridStyle0Action = QAction("&Solid")
        self.gridStyle0Action.setCheckable(True)
        self.gridStyle0Action.triggered.connect(lambda: self.scene.setGrid(0))
        self.gridStyle1Action = QAction("Solid &high-contrast")
        self.gridStyle1Action.setCheckable(True)
        self.gridStyle1Action.triggered.connect(lambda: self.scene.setGrid(1))
        self.gridStyle2Action = QAction("&Dotted")
        self.gridStyle2Action.setCheckable(True)
        self.gridStyle2Action.triggered.connect(lambda: self.scene.setGrid(2))
        self.gridStyle3Action = QAction("Dotted high-&constrast")
        self.gridStyle3Action.setCheckable(True)
        self.gridStyle3Action.triggered.connect(lambda: self.scene.setGrid(3))

        self.gridStyleActionGroup.addAction(self.gridStyle0Action)
        self.gridStyleActionGroup.addAction(self.gridStyle1Action)
        self.gridStyleActionGroup.addAction(self.gridStyle2Action)
        self.gridStyleActionGroup.addAction(self.gridStyle3Action)
        self.gridMenu.addActions([self.gridStyle0Action, self.gridStyle1Action, self.gridStyle2Action, self.gridStyle3Action])
        
        match settings.value("GridStyle", type=int):
            case 0:
                self.gridStyle0Action.trigger()
            case 1:
                self.gridStyle1Action.trigger()
            case 2:
                self.gridStyle2Action.trigger()
            case 3:
                self.gridStyle3Action.trigger()
            case _:
                self.gridStyle0Action.setChecked(True)

        self.tileIDAction = QAction("Show &tile IDs", shortcut=QKeySequence("Ctrl+T"))
        self.tileIDAction.setCheckable(True)
        self.tileIDAction.changed.connect(self.scene.toggleTileIDs)
        if settings.value("ShowTileIDs") == "true":
            self.tileIDAction.trigger()

        self.npcIDAction = QAction("Show &NPC IDs", shortcut=QKeySequence("Ctrl+N"))
        self.npcIDAction.setCheckable(True)
        if settings.value("ShowNPCIDs") == "true":
            self.npcIDAction.setChecked(True)
            MapEditorNPC.showNPCIDs()
        self.npcIDAction.changed.connect(self.scene.toggleNPCIDs)

        self.npcVisualBoundsAction = QAction("Show NPC &visual bounds")
        self.npcVisualBoundsAction.setCheckable(True)
        if settings.value("ShowNPCVisualBounds") == "true":
            self.npcVisualBoundsAction.setChecked(True)
            MapEditorNPC.showVisualBounds()
        self.npcVisualBoundsAction.changed.connect(self.scene.toggleNPCVisualBounds)

        self.npcCollisionBoundsAction = QAction("Show NPC &collision bounds")
        self.npcCollisionBoundsAction.setCheckable(True)
        if settings.value("ShowNPCCollisionBounds") == "true":
            self.npcCollisionBoundsAction.setChecked(True)
            MapEditorNPC.showCollisionBounds()
        self.npcCollisionBoundsAction.changed.connect(self.scene.toggleNPCCollisionBounds)

        self.warpIDAction = QAction("Show &warp && teleport  IDs")
        self.warpIDAction.setCheckable(True)
        if settings.value("ShowWarpIDs") == "true":
            self.warpIDAction.setChecked(True)
            MapEditorWarp.showWarpIDs()
        self.warpIDAction.changed.connect(self.scene.toggleWarpIDs)
        
        settings.endGroup()

        self.menuView.addActions([self.zoomInAction, self.zoomOutAction])
        self.menuView.addSeparator()
        self.menuView.addActions([self.hexAction])
        self.menuView.addSeparator()
        self.menuView.addActions([self.gridAction])
        self.menuView.addMenu(self.gridMenu)
        self.menuView.addSeparator()
        self.menuView.addActions([self.tileIDAction])
        self.menuView.addSeparator()
        self.menuView.addActions([self.npcIDAction, self.npcVisualBoundsAction, self.npcCollisionBoundsAction])
        self.menuView.addSeparator()
        self.menuView.addActions([self.warpIDAction])
        
        self.menuMode = QMenu("&Mode")
        self.modeTileAction = QAction("&Tile", shortcut=QKeySequence("F1"))
        self.modeTileAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.TILE))
        self.modeSectorAction = QAction("&Sector", shortcut=QKeySequence("F2"))
        self.modeSectorAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.SECTOR))
        self.modeNPCAction = QAction("&NPC", shortcut=QKeySequence("F3"))
        self.modeNPCAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.NPC))
        self.modeTriggerAction = QAction("&Trigger", shortcut=QKeySequence("F4"))
        self.modeTriggerAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.TRIGGER))
        self.modeEnemyAction = QAction("&Enemy", shortcut=QKeySequence("F5"))
        self.modeEnemyAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.ENEMY))
        self.modeHotspotAction = QAction("&Hotspot", shortcut=QKeySequence("F6"))
        self.modeHotspotAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.HOTSPOT))
        self.modeWarpAction = QAction("&Warp && TP", shortcut=QKeySequence("F7"))
        self.modeWarpAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.WARP))
        self.modeAllAction = QAction("&All", shortcut=QKeySequence("F8"))
        self.modeAllAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.ALL))
        self.modeGameAction = QAction("&Game", shortcut=QKeySequence("F9"))
        self.modeGameAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.GAME))
        
        self.menuMode.addActions([self.modeTileAction, self.modeSectorAction, self.modeNPCAction, self.modeTriggerAction,
                                  self.modeEnemyAction, self.modeHotspotAction, self.modeWarpAction,
                                  self.modeAllAction, self.modeGameAction])
        
        self.menuGoto = QMenu("&Go to")
        self.gotoGenericAction = QAction("&Find...", shortcut=QKeySequence.Find)
        self.gotoGenericAction.triggered.connect(self.doFind)
        self.gotoCoordsAction = QAction("Go to &coordinates...", shortcut=QKeySequence("Ctrl+Shift+G"))
        self.gotoCoordsAction.triggered.connect(self.doGoto)
        self.gotoSectorAction = QAction("Go to &sector...")
        self.gotoSectorAction.triggered.connect(self.doGotoSector)

        self.menuGoto.addActions([self.gotoGenericAction, self.gotoCoordsAction, self.gotoSectorAction])


        self.menuTools = QMenu("&Tools")
        self.renderMapAction = QAction("&Render image of map...")
        self.renderMapAction.triggered.connect(self.renderMap)
        self.png2ftsAction = QAction("&Import PNG with png2fts...")
        self.png2ftsAction.triggered.connect(self.dopng2fts)
        self.clearAction = QAction("&Clear map...")
        self.clearAction.triggered.connect(self.scene.onClear)
        self.mapMusicAction = QAction("&Map music editor...")
        self.mapMusicAction.triggered.connect(lambda: MapMusicEditor.openMapMusicEditor(self, self.projectData))
        self.menuTools.addActions([self.renderMapAction, self.png2ftsAction, self.clearAction, self.mapMusicAction])

        self.menuHelp = QMenu("&Help")
        self.aboutAction = QAction("&About EBME...")
        self.aboutAction.triggered.connect(lambda: AboutDialog.showAbout(self))
        self.menuHelp.addAction(self.aboutAction)
        
        if not debug.SYSTEM_OUTPUT:
            self.openDebugAction = QAction("Debug output")
            self.openDebugAction.triggered.connect(lambda: debug.DebugOutputDialog.openDebug(self))
            self.menuHelp.addAction(self.openDebugAction)

        self.menuItems = (self.menuFile, self.menuEdit, self.menuView, self.menuMode, self.menuGoto, self.menuTools, self.menuHelp)

        self.contentLayout = QGridLayout(self)
        self.contentLayout.addWidget(self.sidebar, 0, 0)
        self.contentLayout.addWidget(self.view, 0, 1)
        self.contentLayout.addWidget(self.status, 1, 0, 1, 2)

        self.sidebar.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred))
        self.view.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))

class MapEditorState():
    def __init__(self, mapeditor: MapEditor):
        self.mapeditor = mapeditor
        
        self.mode = common.MODEINDEX.TILE
        self.tempMode = common.TEMPMODEINDEX.NONE
        
        self.currentTile = 0
        self.currentEnemyTile = 0
        self.currentNPCInstances: list[NPCInstance] = []
        self.currentSectors: list[Sector] = []
        self.currentTriggers: list[Trigger] = []
        self.currentHotspot: Hotspot = None
        self.currentWarp: Warp|Teleport = None

        self.placingTiles = False
        self.placingEnemyTiles = False
        
        self.previewScreenOpacity = 0.5
        self.showPreviewScreen = True
        self.showPreviewMap = True
        self.showPreviewNPC = True
        self.previewLocked = False
        
    def selectTrigger(self, trigger: Trigger, add: bool=False):
        """Select a trigger or add one to the current selection

        Args:
            trigger (Trigger): Trigger to select
            add (bool, optional): ctrl+click behavior, such as adding and removing. Defaults to False.
        """
        if add:
            if trigger in self.currentTriggers:
                self.currentTriggers.remove(trigger)
            else:
                self.currentTriggers.append(trigger)
        else:
            self.currentTriggers = [trigger,]
        
        self.mapeditor.sidebarTrigger.fromTriggers()
        
    def deselectTrigger(self, trigger: Trigger):
        self.currentTriggers.remove(trigger)
        self.mapeditor.sidebarTrigger.fromTriggers()