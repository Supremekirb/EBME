import logging
from typing import TYPE_CHECKING

import numpy
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import (QAction, QActionGroup, QGuiApplication, QImage,
                           QKeySequence, QPalette, QPixmap)
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGridLayout, QInputDialog,
                               QMenu, QProgressDialog, QSizePolicy, QTabWidget,
                               QWidget)

import src.mapeditor.map.map_scene as map_scene
import src.mapeditor.map.map_view as map_view
import src.mapeditor.sidebar.all_sidebar as all_sidebar
import src.mapeditor.sidebar.changes_sidebar as changes_sidebar
import src.mapeditor.sidebar.collision_sidebar as collision_sidebar
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
import src.misc.icons as icons
from src.coilsnake.fts_interpreter import Tile
from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords
from src.misc.dialogues import (AboutDialog, CoordsDialog, FindDialog,
                                MapAdvancedPalettePreviewDialog,
                                RenderMapDialog, SettingsDialog)
from src.misc.map_music_editor import MapMusicEditor
from src.objects.enemy import EnemyTile
from src.objects.hotspot import Hotspot
from src.objects.npc import MapEditorNPC, NPCInstance
from src.objects.sector import Sector
from src.objects.trigger import Trigger
from src.objects.warp import MapEditorWarp, Teleport, Warp
from src.png2fts.png2fts_gui import png2ftsMapEditorGui
from src.widgets.layout import UprightIconsWestTabWidget

if TYPE_CHECKING:
    from src.main.main import MainApplication


class MapEditor(QWidget):
    def __init__(self, parent: "MainApplication", projectData: ProjectData):
        super().__init__(parent)
        
        self.projectData = projectData
        self.state = MapEditorState(self)

        self.scene = map_scene.MapEditorScene(self, self.state, self.projectData)
        self.view = map_view.MapEditorView(self, self.state, self.projectData, self.scene)
        self.view.centerOn(0, 0)
        
        self.setupUI()

        self.updateTabSize(0)
        self.scene.selectSector(EBCoords(0, 0))
        self.scene.pickCollision(EBCoords(0, 0))
        logging.info("Map editor initialised")

    def changeSidebarTab(self, index):
        self.updateTabSize(index)
        self.scene.onChangeMode(index)
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
            
            self.update()

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
        RenderMapDialog.renderMap(self, self.scene, x1, y1, x2, y2, immediate)
    
    def openAdvancedPreview(self):
        if not self.state.isPreviewingPalette():
            menu = MapAdvancedPalettePreviewDialog(self, self.projectData)
            menu.palettechanged.connect(self.state.setPreviewPalette)
            # no way to accept it, so rejected covers this
            menu.rejected.connect(self.state.clearPreviewPalette)
            menu.onPaletteGroupChange(menu.paletteGroupSelect.currentText())
            menu.show()

    def setupUI(self):
        self.view.setLayoutDirection(Qt.LayoutDirection.RightToLeft) # vert. scrollbar on left edge
        # also, allows the sidebar to eat up space

        self.status = status_bar.MapEditorStatus(self)

        self.sidebar = UprightIconsWestTabWidget()
        self.sidebar.currentChanged.connect(self.changeSidebarTab)

        # future modes / features
        # map_changes

        self.sidebarTile = tile_sidebar.SidebarTile(self, self.state, self, self.projectData)
        self.sidebarSector = sector_sidebar.SidebarSector(self, self.state, self, self.projectData)
        self.sidebarNPC = npc_sidebar.SidebarNPC(self, self.state, self, self.projectData)
        self.sidebarTrigger = trigger_sidebar.SidebarTrigger(self, self.state, self, self.projectData)
        self.sidebarEnemy = enemy_sidebar.SidebarEnemy(self, self.state, self.projectData)
        self.sidebarHotspot = hotspot_sidebar.SidebarHotspot(self, self.state, self, self.projectData)
        self.sidebarWarp = warp_sidebar.SidebarWarp(self, self.state, self, self.projectData)
        self.sidebarCollision = collision_sidebar.SidebarCollision(self, self.state, self, self.projectData)
        self.sidebarChanges = changes_sidebar.SidebarChanges(self, self.state, self, self.projectData)
        self.sidebarAll = all_sidebar.SidebarAll(self, self.state, self, self.projectData)
        self.sidebarGame = game_sidebar.SidebarGame(self, self.state, self, self.projectData)

        self.sidebar.addTab(self.sidebarTile, icons.EBICON_TILE, "Tile")
        self.sidebar.addTab(self.sidebarSector, icons.EBICON_SECTOR, "Sector")
        self.sidebar.addTab(self.sidebarNPC, icons.EBICON_NPC, "NPC")
        self.sidebar.addTab(self.sidebarTrigger, icons.EBICON_TRIGGER, "Trigger")
        self.sidebar.addTab(self.sidebarEnemy, icons.EBICON_ENEMY, "Enemy")
        self.sidebar.addTab(self.sidebarHotspot, icons.EBICON_HOTSPOT, "Hotspot")
        self.sidebar.addTab(self.sidebarWarp, icons.EBICON_WARP, "Warp && TP")
        self.sidebar.addTab(self.sidebarCollision, icons.EBICON_COLLISION, "Collision")
        self.sidebar.addTab(self.sidebarChanges, icons.EBICON_CHANGES, "Changes")
        self.sidebar.addTab(self.sidebarAll, icons.EBICON_ALL, "View All")
        self.sidebar.addTab(self.sidebarGame, icons.EBICON_GAME, "View Game")
        self.sidebar.setTabPosition(QTabWidget.TabPosition.West)
            
        self.menuFile = QMenu("&File")
        self.saveAction = QAction(icons.ICON_SAVE, "&Save", shortcut=QKeySequence("Ctrl+S"))
        self.saveAction.triggered.connect(self.parent().projectWin.saveAction.trigger)
        self.openAction = QAction(icons.ICON_LOAD, "&Open", shortcut=QKeySequence("Ctrl+O"))
        self.openAction.triggered.connect(self.parent().projectWin.openAction.trigger)
        self.reloadAction = QAction(icons.ICON_RELOAD, "&Reload", shortcut=QKeySequence("Ctrl+R"))
        self.reloadAction.triggered.connect(self.parent().projectWin.reloadAction.trigger)
        self.menuFile.addActions([self.saveAction, self.openAction, self.reloadAction])
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.parent().sharedActionSettings)        

        self.menuEdit = QMenu("&Edit")
        self.deleteAction = QAction(icons.ICON_DELETE, "&Delete", shortcut=QKeySequence(Qt.Key.Key_Delete))
        self.deleteAction.triggered.connect(self.scene.onDelete)
        self.copyAction = QAction(icons.ICON_COPY, "&Copy", shortcut=QKeySequence("Ctrl+C"))
        self.copyAction.triggered.connect(self.scene.onCopy)
        self.cutAction = QAction(icons.ICON_CUT, "Cu&t", shortcut=QKeySequence("Ctrl+X"))
        self.cutAction.triggered.connect(self.scene.onCut)
        self.pasteAction = QAction(icons.ICON_PASTE, "&Paste", shortcut=QKeySequence("Ctrl+V"))
        self.pasteAction.triggered.connect(self.scene.onPaste)
        self.cancelAction = QAction(icons.ICON_CANCEL, "C&ancel")
        self.cancelAction.setShortcuts([QKeySequence("Esc"), QKeySequence("Ctrl+D")])
        self.cancelAction.triggered.connect(self.scene.onCancel)
        self.menuEdit.addActions([self.deleteAction, self.cutAction, self.copyAction, self.pasteAction])
        self.menuEdit.addSeparator()
        self.menuEdit.addActions([self.parent().sharedActionUndo, self.parent().sharedActionRedo])
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.cancelAction)
        
        # hidden actions for sectors
        self.copyShiftAction = QAction(icons.ICON_COPY, "Copy", shortcut=QKeySequence("Ctrl+Shift+C"))
        self.addAction(self.copyShiftAction)
        self.copyShiftAction.triggered.connect(self.scene.copySelectedSectorAttributes)
        
        self.copyAltShiftAction = QAction(icons.ICON_COPY, "Copy", shortcut=QKeySequence("Ctrl+Alt+Shift+C"))
        self.addAction(self.copyAltShiftAction)
        self.copyAltShiftAction.triggered.connect(self.scene.copySelectedSectorPalettes)

        self.menuView = QMenu("&View")
        settings = QSettings()
        self.zoomInAction = QAction(icons.ICON_ZOOM_IN, "Zoom in")
        self.zoomInAction.setShortcuts([QKeySequence.StandardKey.ZoomIn, QKeySequence("Ctrl+=")])
        self.zoomInAction.triggered.connect(self.view.zoomIn)
        
        self.zoomOutAction = QAction(icons.ICON_ZOOM_OUT, "Zoom out", shortcut=QKeySequence.ZoomOut)
        self.zoomOutAction.triggered.connect(self.view.zoomOut)

        self.hexAction = self.parent().sharedActionHex

        settings.beginGroup("mapeditor")

        self.gridAction = self.parent().sharedActionShowGrid
        self.gridAction.changed.connect(self.scene.toggleGrid)
        self.gridAction.changed.connect(self.sidebarCollision.display.update)
        if self.gridAction.isChecked():
            self.scene.grid.show()

        self.gridMenu = QMenu("Grid &style...")
        self.gridMenu.setIcon(icons.ICON_GRID)
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

        self.tileIDAction = self.parent().sharedActionTileIDs
        self.tileIDAction.changed.connect(self.scene.toggleTileIDs)
        if self.tileIDAction.isChecked():
            self.scene.toggleTileIDs()

        self.npcIDAction = QAction("Show &NPC IDs", shortcut=QKeySequence("Ctrl+N"))
        self.npcIDAction.setCheckable(True)
        if settings.value("ShowNPCIDs", type=bool):
            self.npcIDAction.setChecked(True)
            MapEditorNPC.showNPCIDs()
        self.npcIDAction.changed.connect(self.scene.toggleNPCIDs)

        self.npcVisualBoundsAction = QAction("Show NPC &visual bounds")
        self.npcVisualBoundsAction.setCheckable(True)
        if settings.value("ShowNPCVisualBounds", type=bool):
            self.npcVisualBoundsAction.setChecked(True)
            MapEditorNPC.showVisualBounds()
        self.npcVisualBoundsAction.changed.connect(self.scene.toggleNPCVisualBounds)

        self.npcCollisionBoundsAction = QAction("Show NPC &collision bounds")
        self.npcCollisionBoundsAction.setCheckable(True)
        if settings.value("ShowNPCCollisionBounds", type=bool):
            self.npcCollisionBoundsAction.setChecked(True)
            MapEditorNPC.showCollisionBounds()
        self.npcCollisionBoundsAction.changed.connect(self.scene.toggleNPCCollisionBounds)
        
        self.npcForegroundMaskAction = QAction("Show &foreground in front of NPCs")
        self.npcForegroundMaskAction.setCheckable(True)
        if settings.value("MaskNPCsWithForeground", type=bool, defaultValue=True):
            self.npcForegroundMaskAction.setChecked(True)
        self.npcForegroundMaskAction.changed.connect(self.scene.toggleNPCForegroundMask)
        
        self.enemyLinesAction = QAction("Show &enemy spawn lines in Enemy mode")
        self.enemyLinesAction.setCheckable(True)
        if settings.value("ShowEnemyLines", type=bool, defaultValue=False):
            self.enemyLinesAction.setChecked(True)
        self.enemyLinesAction.changed.connect(self.scene.toggleEnemySpawnLines)

        self.warpIDAction = QAction("Show &warp && teleport IDs")
        self.warpIDAction.setCheckable(True)
        if settings.value("ShowWarpIDs") == "true":
            self.warpIDAction.setChecked(True)
            MapEditorWarp.showWarpIDs()
        self.warpIDAction.changed.connect(self.scene.toggleWarpIDs)
        
        self.changesTintAction = QAction("Tint previewed tile changes &red")
        self.changesTintAction.setCheckable(True)
        if settings.value("TileChangesTint", type=bool, defaultValue=False):
            self.changesTintAction.setChecked(True)
        # it's necessary to include the prefix in this line as the lambda is, of course, executed after endGroup, even though the code is "within" it.
        self.changesTintAction.changed.connect(lambda: QSettings().setValue("mapeditor/TileChangesTint", self.changesTintAction.isChecked()))
        
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
        self.menuView.addActions([self.npcIDAction, self.npcVisualBoundsAction,
                                  self.npcCollisionBoundsAction, self.npcForegroundMaskAction])
        self.menuView.addSeparator()
        self.menuView.addActions([self.enemyLinesAction])
        self.menuView.addSeparator()
        self.menuView.addActions([self.warpIDAction])
        self.menuView.addSeparator()
        self.menuView.addActions([self.changesTintAction])
        
        self.menuMode = QMenu("&Mode")
        self.modeTileAction = QAction(icons.EBICON_TILE, "&Tile", shortcut=QKeySequence("F1"))
        self.modeTileAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.TILE))
        self.modeSectorAction = QAction(icons.EBICON_SECTOR, "&Sector", shortcut=QKeySequence("F2"))
        self.modeSectorAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.SECTOR))
        self.modeNPCAction = QAction(icons.EBICON_NPC, "&NPC", shortcut=QKeySequence("F3"))
        self.modeNPCAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.NPC))
        self.modeTriggerAction = QAction(icons.EBICON_TRIGGER, "&Trigger", shortcut=QKeySequence("F4"))
        self.modeTriggerAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.TRIGGER))
        self.modeEnemyAction = QAction(icons.EBICON_ENEMY, "&Enemy", shortcut=QKeySequence("F5"))
        self.modeEnemyAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.ENEMY))
        self.modeHotspotAction = QAction(icons.EBICON_HOTSPOT, "&Hotspot", shortcut=QKeySequence("F6"))
        self.modeHotspotAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.HOTSPOT))
        self.modeWarpAction = QAction(icons.EBICON_WARP, "&Warp && TP", shortcut=QKeySequence("F7"))
        self.modeWarpAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.WARP))
        self.modeCollisionAction = QAction(icons.EBICON_COLLISION, "&Collision", shortcut=QKeySequence("F8"))
        self.modeCollisionAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.COLLISION))
        self.modeChangesAction = QAction(icons.EBICON_CHANGES, "Chan&ges", shortcut=QKeySequence("F9"))
        self.modeChangesAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.CHANGES))
        self.modeAllAction = QAction(icons.EBICON_ALL, "&All", shortcut=QKeySequence("F10"))
        self.modeAllAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.ALL))
        self.modeGameAction = QAction(icons.EBICON_GAME, "&Game", shortcut=QKeySequence("F11"))
        self.modeGameAction.triggered.connect(lambda: self.sidebar.setCurrentIndex(common.MODEINDEX.GAME))
        
        self.menuMode.addActions([self.modeTileAction, self.modeSectorAction, self.modeNPCAction, self.modeTriggerAction,
                                  self.modeEnemyAction, self.modeHotspotAction, self.modeWarpAction, self.modeCollisionAction,
                                  self.modeChangesAction, self.modeAllAction, self.modeGameAction])
        
        self.menuGoto = QMenu("&Go to")
        self.gotoGenericAction = QAction(icons.ICON_FIND, "&Find...", shortcut=QKeySequence.Find)
        self.gotoGenericAction.triggered.connect(self.doFind)
        self.gotoCoordsAction = QAction(icons.ICON_COORDS, "Go to &coordinates...", shortcut=QKeySequence("Ctrl+Shift+G"))
        self.gotoCoordsAction.triggered.connect(self.doGoto)
        self.gotoSectorAction = QAction(icons.ICON_RECT, "Go to &sector...")
        self.gotoSectorAction.triggered.connect(self.doGotoSector)

        self.menuGoto.addActions([self.gotoGenericAction, self.gotoCoordsAction, self.gotoSectorAction])


        self.menuTools = QMenu("&Tools")
        self.renderMapAction = QAction(icons.ICON_RENDER_IMG, "&Render image of map...")
        self.renderMapAction.triggered.connect(self.renderMap)
        self.png2ftsAction = QAction(icons.ICON_IMPORT, "&Import PNG with png2fts...")
        self.png2ftsAction.triggered.connect(self.dopng2fts)
        self.clearAction = QAction(icons.ICON_CLEAR, "&Clear map...")
        self.clearAction.triggered.connect(self.scene.onClear)
        self.mapMusicAction = QAction(icons.ICON_MUSIC_LIST, "&Map music editor...")
        self.mapMusicAction.triggered.connect(lambda: MapMusicEditor.openMapMusicEditor(self, self.scene.undoStack, self.projectData))
        self.advancedPreviewAction = QAction(icons.ICON_PALETTE, "&Advanced palette preview...")
        self.advancedPreviewAction.triggered.connect(self.openAdvancedPreview)
        self.menuTools.addActions([self.renderMapAction, self.png2ftsAction, self.clearAction, self.mapMusicAction, 
                                   self.advancedPreviewAction, self.parent().sharedActionTileSpace])
        self.parent().tileScratchSpace.scene.tileSelected.connect(self.scene.tileScratchSpacePicked)

        self.menuHelp = QMenu("&Help")
        self.menuHelp.addAction(self.parent().sharedActionAbout)
        if not debug.SYSTEM_OUTPUT:
            self.menuHelp.addAction(self.parent().sharedActionDebug)
        self.menuHelp.addAction(self.parent().sharedActionReport)

        self.menuItems = (self.menuFile, self.menuEdit, self.menuView, self.menuMode, self.menuGoto, self.menuTools, self.menuHelp)

        self.contentLayout = QGridLayout(self)
        self.contentLayout.addWidget(self.sidebar, 0, 0)
        self.contentLayout.addWidget(self.view, 0, 1)
        self.contentLayout.addWidget(self.status, 1, 0, 1, 2)

        self.sidebar.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred))
        self.view.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        
    def parent(self) -> "MainApplication": # for typing
        return super().parent()

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
        self.currentCollision = 0

        self.placingTiles = False
        self.placingEnemyTiles = False
        self.placingCollision = False
        
        self.previewScreenOpacity = 0.5
        self.showPreviewScreen = True
        self.showPreviewMap = True
        self.showPreviewNPC = True
        self.previewLocked = False
        self.previewCollides = True
        
        self.allModeShowsCollision = True
        self.allModeShowsEnemyTiles = True
        
        self.previewingPaletteGroup: int|None = None
        self.previewingPalette: int|None = None
    
    # TODO these two are unused. remove
    def selectTrigger(self, trigger: Trigger, add: bool=False):
        """Select a trigger or add one to the current  

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
    
    def setPreviewPalette(self, group: int, palette: int):
        self.previewingPaletteGroup = group
        self.previewingPalette = palette
        self.mapeditor.scene.update()
    
    def clearPreviewPalette(self):
        self.previewingPaletteGroup = None
        self.previewingPalette = None
        self.mapeditor.scene.update()
    
    def isPreviewingPalette(self):
        return self.previewingPaletteGroup is not None and self.previewingPalette is not None