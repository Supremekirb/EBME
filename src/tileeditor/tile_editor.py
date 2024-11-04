from copy import copy
from typing import TYPE_CHECKING

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import (QAction, QColor, QKeySequence, QUndoCommand,
                           QUndoStack)
from PySide6.QtWidgets import (QComboBox, QGroupBox, QHBoxLayout, QLabel,
                               QMenu, QPushButton, QSizePolicy, QSplitter,
                               QStyle, QToolButton, QVBoxLayout, QWidget)

import src.misc.common as common
import src.misc.debug as debug
import src.misc.icons as icons
from src.actions.fts_actions import (ActionChangeArrangement,
                                     ActionChangeBitmap, ActionChangeCollision,
                                     ActionChangeSubpaletteColour,
                                     ActionSwapMinitiles)
from src.actions.misc_actions import MultiActionWrapper
from src.coilsnake.fts_interpreter import Minitile, Tile
from src.coilsnake.project_data import ProjectData
from src.misc.dialogues import (AboutDialog, AutoMinitileRearrangerDialog,
                                RenderMinitilesDialog, RenderTilesDialog,
                                SettingsDialog)
from src.misc.widgets import (AspectRatioWidget, HorizontalGraphicsView,
                              TilesetDisplayGraphicsScene)
from src.tileeditor.arrangement_editor import TileArrangementWidget
from src.tileeditor.collision_editor import (CollisionPresetList,
                                             TileCollisionWidget)
from src.tileeditor.graphics_editor import (GraphicsEditorPaletteSelector,
                                            MinitileEditorWidget)
from src.tileeditor.minitile_selector import MinitileScene, MinitileView

if TYPE_CHECKING:
    from src.main.main import MainApplication

class TileEditorState():
    def __init__(self, tileeditor: "TileEditor"):
        
        self.tileEditor = tileeditor
        
        self.currentTileset = 0
        self.currentPaletteGroup = 0
        self.currentPalette = 0
        self.currentSubpalette = 0
        
        self.currentMinitile = 0
        self.currentTile = 0
        self.currentCollision = 0
        
        self.currentColour: QColor = None
        self.currentColourIndex = 0
        

class TileEditor(QWidget):
    def __init__(self, parent: "MainApplication", projectData: ProjectData):
        super().__init__(parent)
        
        self.projectData = projectData
        self.state = TileEditorState(self)
        self.undoStack = QUndoStack(self)
        self.undoStack.cleanChanged.connect(self.parent().updateTitle)
        
        self.setupUI()
        self.tilesetSelect.setCurrentIndex(0)
        self.tilesetSelect.activated.emit(0)
    
    def onUndo(self):
        command = self.undoStack.command(self.undoStack.index()-1)
        if command and not self.fgScene._painting and not self.bgScene._painting:
            self.undoStack.undo()
            self.onUndoRedoCommon(command)
            
    def onRedo(self):
        command = self.undoStack.command(self.undoStack.index())

        if command and not self.fgScene._painting and not self.bgScene._painting:
            self.undoStack.redo()
            self.onUndoRedoCommon(command)
            
    def onUndoRedoCommon(self, command: QUndoCommand):
        commands = []
        
        count = command.childCount()
        if count > 0:
            for c in range(count):
                commands.append(command.child(c))
        
        elif isinstance(command, MultiActionWrapper):
            for c in command.commands:
                commands.append(c)
        
        else:
            commands.append(command)
        
        actionType: str = None
        for c in commands:
            if isinstance(c, ActionChangeBitmap):
                actionType = "bitmap"
                self.updateMinitile(c.minitile)
            elif isinstance(c, ActionChangeArrangement):
                actionType = "arrangement"
                self.updateTile(c.tile)
            elif isinstance(c, ActionChangeSubpaletteColour):
                actionType = "colour"
                self.onColourEdit()
            elif isinstance(c, ActionChangeCollision):
                actionType = "collision"
            elif isinstance(c, ActionSwapMinitiles):
                actionType = "swap"
        
        match actionType:
            case "bitmap":
                self.fgScene.copyToScratch()
                self.bgScene.copyToScratch()
                self.fgScene.update()
                self.bgScene.update()
            case "arrangement":
                self.arrangementScene.update()
                self.collisionScene.update()
            case "colour":
                self.fgScene.update()
                self.bgScene.update()
                self.paletteView.loadPalette(self.paletteView.currentPalette)
            case "collision":
                self.collisionScene.update()
            case "swap":
                self.minitileScene.renderTileset(self.state.currentTileset,
                                                 self.state.currentPaletteGroup,
                                                 self.state.currentPalette,
                                                 self.state.currentSubpalette)
                self.minitileScene.updateHoverPreview(self.minitileScene.lastMinitileHovered)
                 
    def onTilesetSelect(self):
        value = int(self.tilesetSelect.currentText())
        self.state.currentTileset = value
        self.paletteGroupSelect.blockSignals(True)
        self.paletteGroupSelect.clear()
        self.paletteGroupSelect.addItems(str(i.groupID) for i in self.projectData.getTileset(value).paletteGroups)
        
        tileset = self.projectData.getTileset(self.state.currentTileset)
        self.arrangementScene.loadTile(tileset.tiles[self.state.currentTile])
        self.arrangementScene.loadTileset(tileset)
        self.collisionScene.loadTile(tileset.tiles[self.state.currentTile])
        self.collisionScene.loadTileset(tileset)
        
        self.tileScene.currentTileset = value
        
        self.onPaletteGroupSelect()
        self.paletteGroupSelect.blockSignals(False)
        
    def onPaletteGroupSelect(self):
        value = int(self.paletteGroupSelect.currentText())
        self.state.currentPaletteGroup = value
        self.paletteSelect.blockSignals(True)
        self.paletteSelect.clear()
        self.paletteSelect.addItems(str(i.paletteID) for i in self.projectData.getTileset(
            self.state.currentTileset).getPaletteGroup(value).palettes)
        
        self.tileScene.currentPaletteGroup = value 
        
        self.onPaletteSelect()
        self.paletteSelect.blockSignals(False)    
        
    def onPaletteSelect(self):
        value = int(self.paletteSelect.currentText())
        self.state.currentPalette = value
        self.onSubpaletteSelect()
        
        palette = self.projectData.getTileset(self.state.currentTileset).getPalette(
            self.state.currentPaletteGroup, self.state.currentPalette)
        self.arrangementScene.loadPalette(palette)
        self.collisionScene.loadPalette(palette)
        self.paletteView.loadPalette(palette)
        
        self.tileScene.currentPalette = value
        self.tileScene.update()
        
    def onSubpaletteSelect(self):
        value = self.paletteView.currentSubpaletteIndex
        self.state.currentSubpalette = value
        self.minitileScene.renderTileset(self.state.currentTileset,
                                         self.state.currentPaletteGroup,
                                         self.state.currentPalette,
                                         self.state.currentSubpalette)
    
        self.selectMinitile(self.state.currentMinitile)
    
    def onTileSelect(self, tile: int):
        self.state.currentTile = tile
        tileObj = self.projectData.getTileset(
            self.state.currentTileset).tiles[self.state.currentTile]
        self.arrangementScene.loadTile(tileObj)
        self.collisionScene.loadTile(tileObj)
        self.presetList.verifyTileCollision(tileObj)
    
    def onColourEdit(self):
        self.projectData.clobberTileGraphicsCache()
        for i in self.projectData.getTileset(self.state.currentTileset).minitiles:
            i.BothToImage.cache_clear()

        self.minitileScene.renderTileset(self.state.currentTileset,
                                         self.state.currentPaletteGroup,
                                         self.state.currentPalette,
                                         self.state.currentSubpalette)
        self.tileScene.update()
        self.arrangementScene.update()
        self.collisionScene.update()
        self.fgScene.update()
        self.bgScene.update()
        
    def selectMinitile(self, minitile: int):
        self.state.currentMinitile = minitile
        
        if minitile >= common.MINITILENOFOREGROUND:
            self.minitileFgWarning.show()
        else:
            self.minitileFgWarning.hide()
        minitileObj = self.projectData.getTileset(self.state.currentTileset).minitiles[minitile]
        subpaletteObj = self.projectData.getTileset(self.state.currentTileset).getPalette(
            self.state.currentPaletteGroup, self.state.currentPalette
            ).subpalettes[self.state.currentSubpalette]
        
        self.fgScene.loadMinitile(minitileObj, minitile)
        self.fgScene.currentSubpalette = subpaletteObj
        self.fgScene.update()
        
        self.bgScene.loadMinitile(minitileObj, minitile)
        self.bgScene.currentSubpalette = subpaletteObj
        self.bgScene.update()
        
        self.minitileScene.moveCursorToMinitile(minitile)
        
    def selectColour(self, index: int):
        self.state.currentColourIndex = index
        self.paletteView.setColourIndex(index)
        
    def copyBgToFg(self):
        bgBitmap = self.bgScene._scratchBitmap
        action = ActionChangeBitmap(self.fgScene.currentMinitile, bgBitmap, True)
        self.undoStack.push(action)
        self.fgScene.copyToScratch()
        self.fgScene.update()
        
    def copyFgToBg(self):
        fgBitmap = self.fgScene._scratchBitmap
        action = ActionChangeBitmap(self.bgScene.currentMinitile, fgBitmap, False)
        self.undoStack.push(action)
        self.bgScene.copyToScratch()
        self.bgScene.update()
        
    def swapBgAndFg(self):
        self.undoStack.beginMacro("Swap BG and FG")
        bgBitmap = copy(self.bgScene._scratchBitmap)
        self.copyFgToBg()
        action = ActionChangeBitmap(self.fgScene.currentMinitile, bgBitmap, True)
        self.undoStack.push(action)
        self.undoStack.endMacro()
        self.fgScene.copyToScratch()
        self.fgScene.update()
    
    def onAutoRearrange(self):
        action = AutoMinitileRearrangerDialog.rearrangeMinitiles(self, self.projectData)
        
        if action:
            self.undoStack.push(action)
            self.minitileScene.renderTileset(self.state.currentTileset,
                                             self.state.currentPaletteGroup,
                                             self.state.currentPalette,
                                             self.state.currentSubpalette)
            self.selectMinitile(self.state.currentMinitile)
        
    def updateTile(self, tile: Tile|int):
        if isinstance(tile, Tile):
            tile = self.projectData.getTileset(self.state.currentTileset).tiles.index(tile)
        self.projectData.clobberTileGraphicsCache()
        self.tileScene.update()
        self.arrangementScene.update()
        self.collisionScene.update()
        
    def updateMinitile(self, minitile: Minitile|int):
        if isinstance(minitile, int):
            minitile = self.projectData.getTileset(self.state.currentTileset).minitiles[minitile]
        
        minitile.BothToImage.cache_clear() 
        # TODO fix the following:
        # the three instances of clearTileGraphicsCache() in this file should be more specific.
        # however, if the current tileset/palette group/palette/subpalette doesn't match the
        # one we *should* be undoing (ie. it was changed), then cached graphics aren't invalidated.
        # in other words, we don't know the context of the change.
        # right now, I've just bitten the bullet and clobbered the entire cache each time.
        # it's less than ideal, but it doesn't seem to have too much of a performance impact.
        # Still... I'd like to do it properly. But I don't know where this data will go.
        # (the function does support specification as per definition and documentation)
        
        self.projectData.clobberTileGraphicsCache()
        
        self.tileScene.update()
        self.arrangementScene.update()
        self.collisionScene.update()
        self.minitileScene.renderTileset(self.state.currentTileset,
                                         self.state.currentPaletteGroup,
                                         self.state.currentPalette,
                                         self.state.currentSubpalette)
        
    def renderTiles(self):
        tileset = self.projectData.getTileset(self.state.currentTileset)
        palette = tileset.getPalette(self.state.currentPaletteGroup, self.state.currentPalette)
        RenderTilesDialog.renderTiles(self, tileset, palette)
    
    def renderMiniiles(self):
        tileset = self.projectData.getTileset(self.state.currentTileset)
        palette = tileset.getPalette(self.state.currentPaletteGroup, self.state.currentPalette)
        RenderMinitilesDialog.renderMinitiles(self, tileset, palette.subpalettes[self.state.currentSubpalette])
    
    def toggleTileIDs(self):
        self.tileScene.update()
        
    def toggleGrid(self):
        if self.gridAction.isChecked():
            self.minitileScene.grid.show()
        else:
            self.minitileScene.grid.hide()
        
    def setupUI(self):
        contentLayout = QVBoxLayout()
        splitter = QSplitter()
        topWidget = QWidget()
        topWidget.setContentsMargins(0, 0, 0, 0)
        topLayout = QHBoxLayout()
        topWidget.setLayout(topLayout)
        bottomWidget = QWidget()
        bottomWidget.setContentsMargins(0, 0, 0, 0)
        bottomLayout = QHBoxLayout()
        bottomWidget.setLayout(bottomLayout)
        self.setLayout(contentLayout)       
        
        splitter.addWidget(topWidget)
        splitter.addWidget(bottomWidget)
        splitter.setOrientation(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        contentLayout.addWidget(splitter)
        
        minitileBox = QGroupBox("Minitiles")
        minitileLayout = QVBoxLayout()
        tilesetSelectLayout = QHBoxLayout()
        tilesetSelectTilesetLayout = QVBoxLayout()
        tilesetSelectPaletteGroupLayout = QVBoxLayout()
        tilesetSelectPaletteLayout = QVBoxLayout()
        minitileBox.setLayout(minitileLayout)
        
        graphicsBox = QGroupBox("Graphics")
        graphicsLayout = QHBoxLayout()
        drawingLayout = QVBoxLayout()
        swapperButtonLayout = QHBoxLayout()
        paletteLayout = QVBoxLayout()
        graphicsBox.setLayout(graphicsLayout)
        
        tileBox = QGroupBox("Tiles")
        tileLayout = QHBoxLayout()
        tileBox.setLayout(tileLayout)
        
        collisionBox = QGroupBox("Attributes (collision)")
        collisionLayout = QHBoxLayout()
        collisionBox.setLayout(collisionLayout)
        
        self.minitileScene = MinitileScene(self, self.projectData)
        self.minitileView = MinitileView(self.minitileScene)
        
        self.tileScene = TilesetDisplayGraphicsScene(self.projectData, True, 5)
        self.tileScene.tileSelected.connect(self.onTileSelect)
        self.tileView = HorizontalGraphicsView(self.tileScene)
        self.tileView.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.tileView.setFixedHeight(32*self.tileScene.rowSize+1+self.tileView.horizontalScrollBar().sizeHint().height())
        # self.tileView.setMaximumWidth(32*12)
        self.tileView.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tileView.centerOn(0, 0)
        
        self.arrangementScene = TileArrangementWidget(self.state)
        self.arrangementAspectRatioContainer = AspectRatioWidget(self.arrangementScene)
        
        self.collisionScene = TileCollisionWidget(self.state)
        self.collisionAspectRatioContainer = AspectRatioWidget(self.collisionScene)
        
        self.presetList = CollisionPresetList(self.state)
        
        self.minitileFgWarning = QLabel("<span style='color: red'>Foreground graphics won't display in-game.</span>")
        self.minitileFgWarning.setTextFormat(Qt.TextFormat.RichText)
        self.minitileFgWarning.setWordWrap(True)
        
        self.fgScene = MinitileEditorWidget(self.state)
        self.fgScene.colourPicked.connect(self.selectColour)
        self.fgAspectRatioContainer = AspectRatioWidget(self.fgScene)
        
        self.bgScene = MinitileEditorWidget(self.state)
        self.bgScene.isForeground = False
        self.bgScene.colourPicked.connect(self.selectColour)
        self.bgAspectRatioContainer = AspectRatioWidget(self.bgScene)
        
        self.paletteView = GraphicsEditorPaletteSelector(self.state)
        self.paletteView.colourChanged.connect(self.selectColour)
        self.paletteView.colourEdited.connect(self.onColourEdit)
        self.paletteView.subpaletteChanged.connect(self.onSubpaletteSelect)
                
        self.tilesetSelect = QComboBox()
        self.tilesetSelect.addItems(str(i.id) for i in self.projectData.tilesets)
        tilesetSelectTilesetLayout.addWidget(QLabel("Tileset"))
        tilesetSelectTilesetLayout.addWidget(self.tilesetSelect)
        
        self.paletteGroupSelect = QComboBox()
        tilesetSelectPaletteGroupLayout.addWidget(QLabel("Palette Group"))
        tilesetSelectPaletteGroupLayout.addWidget(self.paletteGroupSelect)
        
        self.paletteSelect = QComboBox()
        tilesetSelectPaletteLayout.addWidget(QLabel("Palette"))
        tilesetSelectPaletteLayout.addWidget(self.paletteSelect)
        
        self.tilesetSelect.activated.connect(self.onTilesetSelect)
        self.paletteGroupSelect.activated.connect(self.onPaletteGroupSelect)
        self.paletteSelect.activated.connect(self.onPaletteSelect)
        
        tilesetSelectLayout.addLayout(tilesetSelectTilesetLayout)
        tilesetSelectLayout.addLayout(tilesetSelectPaletteGroupLayout)
        tilesetSelectLayout.addLayout(tilesetSelectPaletteLayout)
        
        minitileLayout.addLayout(tilesetSelectLayout)
        minitileLayout.addWidget(self.minitileView)
        
        drawingLayout.addWidget(self.minitileFgWarning)
        drawingLayout.addWidget(self.fgAspectRatioContainer)
        self.bgToFgButton = QToolButton()
        self.bgToFgButton.setIcon(icons.ICON_UP)
        self.bgToFgButton.setToolTip("Copy background to foreground")
        self.bgToFgButton.clicked.connect(self.copyBgToFg)
        self.swapBgAndFgButton = QToolButton()
        self.swapBgAndFgButton.setIcon(icons.ICON_SWAP)
        self.swapBgAndFgButton.setToolTip("Swap foreground and background")
        self.swapBgAndFgButton.clicked.connect(self.swapBgAndFg)
        self.fgToBgButton = QToolButton()
        self.fgToBgButton.setIcon(icons.ICON_DOWN)
        self.fgToBgButton.setToolTip("Copy foreground to background")
        self.fgToBgButton.clicked.connect(self.copyFgToBg)
        swapperButtonLayout.addWidget(self.bgToFgButton)
        swapperButtonLayout.addWidget(self.swapBgAndFgButton)
        swapperButtonLayout.addWidget(self.fgToBgButton)
        drawingLayout.addLayout(swapperButtonLayout)
        drawingLayout.addWidget(self.bgAspectRatioContainer)
        
        paletteLayout.addStretch()
        paletteLayout.addWidget(QLabel("Subpalettes"))
        paletteLayout.addWidget(self.paletteView)
        self.editPaletteButton = QPushButton("Edit")
        self.editPaletteButton.clicked.connect(self.paletteView.openEditor)
        paletteLayout.addWidget(self.editPaletteButton)
        paletteLayout.addStretch()
        # paletteLayout.setStretch(0, 100)
        
        graphicsLayout.addLayout(drawingLayout)
        graphicsLayout.addLayout(paletteLayout)
        
        tileLayout.addWidget(self.tileView)
        tileLayout.addWidget(self.arrangementScene)  
        
        collisionLayout.addLayout(self.presetList)
        collisionLayout.addWidget(self.collisionScene)
        
        topLayout.addWidget(minitileBox)
        topLayout.addWidget(graphicsBox)
        bottomLayout.addWidget(tileBox)
        bottomLayout.addWidget(collisionBox)
        
        
        self.menuFile = QMenu("&File")
        self.saveAction = QAction(icons.ICON_SAVE, "&Save", shortcut=QKeySequence("Ctrl+S"))
        self.saveAction.triggered.connect(self.parent().projectWin.saveAction.trigger)
        self.openAction = QAction(icons.ICON_LOAD, "&Open", shortcut=QKeySequence("Ctrl+O"))
        self.openAction.triggered.connect(self.parent().projectWin.openAction.trigger)
        self.reloadAction = QAction(icons.ICON_RELOAD, "&Reload", shortcut=QKeySequence("Ctrl+R"))
        self.reloadAction.triggered.connect(self.parent().projectWin.reloadAction.trigger)
        self.openSettingsAction = QAction(icons.ICON_SETTINGS, "Settings...")
        self.openSettingsAction.triggered.connect(lambda: SettingsDialog.openSettings(self))
        self.menuFile.addActions([self.saveAction, self.openAction, self.reloadAction])
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.openSettingsAction)
        
        self.menuEdit = QMenu("&Edit")
        self.undoAction = QAction(icons.ICON_UNDO, "&Undo", shortcut=QKeySequence("Ctrl+Z"))
        self.undoAction.triggered.connect(self.onUndo)
        self.redoAction = QAction(icons.ICON_REDO, "&Redo")
        self.redoAction.setShortcuts([QKeySequence("Ctrl+Y"), QKeySequence("Ctrl+Shift+Z")])
        self.redoAction.triggered.connect(self.onRedo)
        self.menuEdit.addActions([self.undoAction, self.redoAction])
        
        self.menuView = QMenu("&View")
        self.tileIDAction = self.parent().sharedActionTileIDs
        self.tileIDAction.triggered.connect(self.toggleTileIDs)
        if self.tileIDAction.isChecked():
            self.toggleTileIDs()
        self.gridAction = self.parent().sharedActionShowGrid
        self.gridAction.triggered.connect(self.toggleGrid)
        if self.gridAction.isChecked():
            self.toggleGrid()
        self.menuView.addActions([self.tileIDAction, self.gridAction])
        
        self.menuTools = QMenu("&Tools")
        self.renderTilesAction = QAction(icons.ICON_RENDER_IMG, "Render image of &tiles...")
        self.renderTilesAction.triggered.connect(self.renderTiles)
        self.renderMinitilesAction = QAction(icons.ICON_RENDER_IMG, "Render image of &minitiles...")
        self.renderMinitilesAction.triggered.connect(self.renderMiniiles)
        self.autoRearrangeAction = QAction(icons.ICON_AUTO_REARRANGE, "&Auto minitile rearranger...")
        self.autoRearrangeAction.triggered.connect(self.onAutoRearrange)
        self.menuTools.addActions([self.renderTilesAction, self.renderMinitilesAction, self.autoRearrangeAction])
        
        self.menuHelp = QMenu("&Help")        
        self.aboutAction = QAction(icons.ICON_INFO, "&About EBME...")
        self.aboutAction.triggered.connect(lambda: AboutDialog.showAbout(self))
        self.menuHelp.addAction(self.aboutAction)
        
        if not debug.SYSTEM_OUTPUT:
            self.openDebugAction = QAction(icons.ICON_DEBUG, "Debug output")
            self.openDebugAction.triggered.connect(lambda: debug.DebugOutputDialog.openDebug(self))
            self.menuHelp.addAction(self.openDebugAction)
        
        self.menuItems = (self.menuFile, self.menuEdit, self.menuView, self.menuTools, self.menuHelp)
    
    def parent(self) -> "MainApplication": # for typing
        return super().parent()