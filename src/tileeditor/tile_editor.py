import json
import logging
from copy import copy
from typing import TYPE_CHECKING

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import (QAction, QActionGroup, QColor, QKeySequence,
                           QUndoCommand, QUndoStack)
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox, QHBoxLayout,
                               QLabel, QMenu, QPushButton, QSizePolicy,
                               QSplitter, QStyle, QToolButton, QVBoxLayout,
                               QWidget)

import src.misc.common as common
import src.misc.debug as debug
import src.misc.icons as icons
from src.actions.fts_actions import (ActionAddPalette, ActionChangeArrangement,
                                     ActionChangeBitmap, ActionChangeCollision,
                                     ActionChangeSubpaletteColour,
                                     ActionRemovePalette, ActionSwapMinitiles)
from src.actions.misc_actions import MultiActionWrapper
from src.coilsnake.fts_interpreter import Minitile, Tile
from src.coilsnake.project_data import ProjectData
from src.misc.dialogues import (AboutDialog, AutoMinitileRearrangerDialog,
                                FindUnusedMinitilesDialog,
                                RenderMinitilesDialog, RenderTilesDialog,
                                SettingsDialog)
from src.tileeditor.arrangement_editor import TileArrangementWidget
from src.tileeditor.collision_editor import (TileEditorCollisionPresetList,
                                             TileEditorCollisionWidget)
from src.tileeditor.graphics_editor import (GraphicsEditorPaletteSelector,
                                            MinitileEditorWidget)
from src.tileeditor.minitile_selector import MinitileScene, MinitileView
from src.widgets.layout import AspectRatioWidget, HorizontalGraphicsView
from src.widgets.tile import TilesetDisplayGraphicsScene

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
        self.undoStack = self.parent().undoStack
        
        self.undoStack.undone.connect(self.onAction)
        self.undoStack.redone.connect(self.onAction)
        self.undoStack.pushed.connect(self.onAction)
        
        self.setupUI()
        self.tilesetSelect.setCurrentIndex(0)
        self.tilesetSelect.activated.emit(0)
            
    def onAction(self, command: QUndoCommand):
        
        if not command:
            return
        
        commands = []
        
        count = command.childCount()
        if count > 0:
            for c in range(count):
                commands.append(command.child(c))
            commands.append(command)
        
        elif hasattr(command, "commands"):
            for c in command.commands:
                commands.append(c)
        
        # do this *always* to be safe        
        commands.append(command)
        
        actionType: str = None
        for c in commands:
            if isinstance(c, ActionChangeBitmap):
                actionType = "bitmap"
                self.updateMinitile(c.minitile)
            elif isinstance(c, ActionChangeArrangement):
                actionType = "arrangement"
            elif isinstance(c, ActionChangeSubpaletteColour):
                actionType = "colour"
                self.onColourEdit()
            elif isinstance(c, ActionChangeCollision):
                actionType = "collision"
            elif isinstance(c, ActionSwapMinitiles):
                actionType = "swap"
            elif isinstance(c, ActionAddPalette) or isinstance(c, ActionRemovePalette):
                self.onPaletteGroupSelect()
        
        match actionType:
            case "bitmap":
                self.projectData.clobberTileGraphicsCache()
                self.tileScene.update()
                self.arrangementScene.update()
                self.collisionScene.update()
                self.minitileScene.renderTileset(self.state.currentTileset,
                                                self.state.currentPaletteGroup,
                                                self.state.currentPalette,
                                                self.state.currentSubpalette)
                self.fgScene.copyToScratch()
                self.bgScene.copyToScratch()
                self.fgScene.update()
                self.bgScene.update()
            case "arrangement":
                self.projectData.clobberTileGraphicsCache()
                self.tileScene.update()
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
                self.selectMinitile(self.state.currentMinitile)
                 
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
        
    def copyFgToBg(self):
        fgBitmap = self.fgScene._scratchBitmap
        action = ActionChangeBitmap(self.bgScene.currentMinitile, fgBitmap, False)
        self.undoStack.push(action)
        
    def swapBgAndFg(self):
        self.undoStack.beginMacro("Swap BG and FG")
        bgBitmap = copy(self.bgScene._scratchBitmap)
        self.copyFgToBg()
        action = ActionChangeBitmap(self.fgScene.currentMinitile, bgBitmap, True)
        self.undoStack.push(action)
        self.undoStack.endMacro()
    
    FLIPHORDER = [
        0x3, 0x2, 0x1, 0x0,
        0x7, 0x6, 0x5, 0x4,
        0xB, 0xA, 0x9, 0x8,
        0xF, 0xE, 0xD, 0xC
    ]
    def flipArrangementH(self):
        tile = self.arrangementScene.currentTile
        metadatas = []
        for i in range(16):
            metadatas.append(tile.getMetadata(i))
        
        self.undoStack.beginMacro("Flip arrangement horizontally")
        for base, inverted in enumerate(TileEditor.FLIPHORDER):
            self.undoStack.push(ActionChangeArrangement(tile, metadatas[base] ^ 0x4000, inverted))
        self.undoStack.endMacro()
        
    def flipCollisionH(self):
        tile = self.collisionScene.currentTile
        collisions = []
        for i in range(16):
            collisions.append(tile.getMinitileCollision(i))
            
        self.undoStack.beginMacro("Flip collision horizontally")
        for base, inverted in enumerate(TileEditor.FLIPHORDER):
            self.undoStack.push(ActionChangeCollision(tile, collisions[base], inverted))
        self.undoStack.endMacro()
    
    FLIPVORDER = [
        0xC, 0xD, 0xE, 0xF,
        0x8, 0x9, 0xA, 0xB,
        0x4, 0x5, 0x6, 0x7,
        0x0, 0x1, 0x2, 0x3
    ]
    def flipArrangementV(self):
        tile = self.arrangementScene.currentTile
        metadatas = []
        for i in range(16):
            metadatas.append(tile.getMetadata(i))

        self.undoStack.beginMacro("Flip arrangement vertically")
        for base, inverted in enumerate(TileEditor.FLIPVORDER):
            self.undoStack.push(ActionChangeArrangement(tile, metadatas[base] ^ 0x8000, inverted))
        self.undoStack.endMacro()
        
    def flipCollisionV(self):
        tile = self.collisionScene.currentTile
        collisions = []
        for i in range(16):
            collisions.append(tile.getMinitileCollision(i))

        self.undoStack.beginMacro("Flip collision vertically")
        for base, inverted in enumerate(TileEditor.FLIPVORDER):
            self.undoStack.push(ActionChangeCollision(tile, collisions[base], inverted))
        self.undoStack.endMacro()
    
    def onAutoRearrange(self):
        action = AutoMinitileRearrangerDialog.rearrangeMinitiles(self, self.projectData, self.state.currentTileset)
        
        if action:
            self.undoStack.push(action)
            
    def onFindUnused(self):
        FindUnusedMinitilesDialog.findUnusedMinitiles(self, self.projectData, self.state.currentTileset)
        
    def updateMinitile(self, minitile: Minitile|int):
        if isinstance(minitile, int):
            minitile = self.projectData.getTileset(self.state.currentTileset).minitiles[minitile]
        
        minitile.BothToImage.cache_clear() 
        # TODO fix the following:
        # the instances of clearTileGraphicsCache() in this file should be more specific.
        # however, if the current tileset/palette group/palette/subpalette doesn't match the
        # one we *should* be undoing (ie. it was changed), then cached graphics aren't invalidated.
        # in other words, we don't know the context of the change.
        # right now, I've just bitten the bullet and clobbered the entire cache each time.
        # it's less than ideal, but it doesn't seem to have too much of a performance impact.
        # Still... I'd like to do it properly. But I don't know where this data will go.
        # (the function does support specification as per definition and documentation)
        
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
            
    def onCopyMinitile(self):
        minitile = self.projectData.getTileset(self.state.currentTileset).minitiles[self.state.currentMinitile]
        fg = minitile.foreground
        bg = minitile.background
        copied = json.dumps({"Type": "Minitile", "Data": {"FG": fg, "BG": bg}})
        QApplication.clipboard().setText(copied)
        
    def onCopyArrangement(self):
        tile = self.projectData.getTileset(self.state.currentTileset).tiles[self.state.currentTile]
        arrangement = tile.metadata
        copied = json.dumps({"Type": "Arrangement", "Data": {"Metadata": arrangement}})
        QApplication.clipboard().setText(copied)
        
    def onCopyCollision(self):
        tile = self.projectData.getTileset(self.state.currentTileset).tiles[self.state.currentTile]
        collision = tile.collision
        copied = json.dumps({"Type": "Collision", "Data": {"Collision": collision}})
        QApplication.clipboard().setText(copied)
        
    def onCopyTile(self):
        tile = self.projectData.getTileset(self.state.currentTileset).tiles[self.state.currentTile]
        arrangement = tile.metadata
        collision = tile.collision
        copied = json.dumps({"Type": "Tile", "Data": {"Metadata": arrangement, "Collision": collision}})
        QApplication.clipboard().setText(copied)
        
    def onPaste(self):
        inMacro = False
        try:
            text = json.loads(QApplication.clipboard().text())
            match text["Type"]:
                case "Minitile":
                    self.undoStack.beginMacro("Paste minitile")
                    inMacro = True
                    
                    current = self.projectData.getTileset(self.state.currentTileset).minitiles[self.state.currentMinitile]
                    self.undoStack.push(ActionChangeBitmap(current, text["Data"]["FG"], True))
                    self.undoStack.push(ActionChangeBitmap(current, text["Data"]["BG"], False))
                    
                    self.undoStack.endMacro()
                    inMacro = False
                
                case "Arrangement":
                    self.undoStack.beginMacro("Paste tile arrangement")
                    inMacro = True
                    
                    current = self.projectData.getTileset(self.state.currentTileset).tiles[self.state.currentTile]
                    for index, i in enumerate(text["Data"]["Metadata"]):
                        self.undoStack.push(ActionChangeArrangement(current, i, index))
                        
                    self.undoStack.endMacro()
                    inMacro = False
                    
                case "Collision":
                    self.undoStack.beginMacro("Paste tile collision")
                    inMacro = True
                    
                    current = self.projectData.getTileset(self.state.currentTileset).tiles[self.state.currentTile]
                    for index, i in enumerate(text["Data"]["Collision"]):
                        self.undoStack.push(ActionChangeCollision(current, i, index))
                    
                    self.undoStack.endMacro()
                    inMacro = False
                
                case "Tile":
                    self.undoStack.beginMacro("Paste tile data")
                    inMacro = True
                    
                    current = self.projectData.getTileset(self.state.currentTileset).tiles[self.state.currentTile]
                    for index, i in enumerate(text["Data"]["Collision"]):
                        self.undoStack.push(ActionChangeCollision(current, i, index))
                    for index, i in enumerate(text["Data"]["Metadata"]):
                        self.undoStack.push(ActionChangeArrangement(current, i, index))
                    
                    self.undoStack.endMacro()
                    inMacro = False
                
        except json.decoder.JSONDecodeError:
            if inMacro:
                self.undoStack.endMacro()
            logging.warning("Clipboard data is not valid for pasting.")
        except Exception as e:
            if inMacro:
                self.undoStack.endMacro()
            logging.warning(f"Failed to paste possibly valid data: {e}")
            raise
    
    def tileScratchSpacePicked(self, tile: int, tileset: int, palettegroup: int, palette: int):
        self.state.currentTile = tile
        self.tilesetSelect.setCurrentText(str(tileset))
        self.paletteGroupSelect.setCurrentText(str(palettegroup))
        self.paletteSelect.setCurrentText(str(palette))
        self.tileScene.moveCursorToTile(tile)
        self.tileView.centerOn(self.tileScene.selectionIndicator)
        self.onTilesetSelect()
        self.onTileSelect(tile)
        self.arrangementScene.update()
        self.collisionScene.update()
        
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
        
        self.tileScene = TilesetDisplayGraphicsScene(self.projectData, True, 6)
        self.tileScene.tileSelected.connect(self.onTileSelect)
        self.tileView = HorizontalGraphicsView(self.tileScene)
        self.tileView.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.tileView.setFixedHeight(32*self.tileScene.rowSize+1+self.tileView.horizontalScrollBar().sizeHint().height())
        # self.tileView.setMaximumWidth(32*12)
        self.tileView.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tileView.centerOn(0, 0)
        
        arrangementLayout = QVBoxLayout()
        self.arrangementScene = TileArrangementWidget(self.state)
        self.arrangementAspectRatioContainer = AspectRatioWidget(self.arrangementScene)
        
        arrangementToolsLayout = QHBoxLayout()
        self.arrangementFlipHButton = QToolButton()
        self.arrangementFlipHButton.setIcon(icons.ICON_MIRROR_H)
        self.arrangementFlipHButton.setToolTip("Flip horizontally")
        self.arrangementFlipHButton.clicked.connect(self.flipArrangementH)
        self.arrangementFlipVButton = QToolButton()
        self.arrangementFlipVButton.setIcon(icons.ICON_MIRROR_V)
        self.arrangementFlipVButton.setToolTip("Flip vertically")
        self.arrangementFlipVButton.clicked.connect(self.flipArrangementV)
        arrangementToolsLayout.addWidget(self.arrangementFlipHButton)
        arrangementToolsLayout.addWidget(self.arrangementFlipVButton)
        
        arrangementLayout.addWidget(self.arrangementScene)
        arrangementLayout.addLayout(arrangementToolsLayout)
        

        collisionDispLayout = QVBoxLayout() 
        self.collisionScene = TileEditorCollisionWidget(self.state)
        self.collisionAspectRatioContainer = AspectRatioWidget(self.collisionScene)
        
        collisionToolsLayout = QHBoxLayout()
        self.collisionFlipHButton = QToolButton()
        self.collisionFlipHButton.setIcon(icons.ICON_MIRROR_H)
        self.collisionFlipHButton.setToolTip("Flip horizontally")
        self.collisionFlipHButton.clicked.connect(self.flipCollisionH)
        self.collisionFlipVButton = QToolButton()
        self.collisionFlipVButton.setIcon(icons.ICON_MIRROR_V)
        self.collisionFlipVButton.setToolTip("Flip vertically")
        self.collisionFlipVButton.clicked.connect(self.flipCollisionV)
        collisionToolsLayout.addWidget(self.collisionFlipHButton)
        collisionToolsLayout.addWidget(self.collisionFlipVButton)
        
        collisionDispLayout.addWidget(self.collisionScene)
        collisionDispLayout.addLayout(collisionToolsLayout)
        
        self.presetList = TileEditorCollisionPresetList(self.state)
        
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
        minitileLayout.addStretch()
        
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
        tileLayout.addLayout(arrangementLayout)  
        
        collisionLayout.addLayout(self.presetList)
        collisionLayout.addLayout(collisionDispLayout)
        
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
        self.menuFile.addActions([self.saveAction, self.openAction, self.reloadAction])
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.parent().sharedActionSettings)
        
        self.menuEdit = QMenu("&Edit")
        self.copyMenu = QMenu("&Copy...")
        self.copyMenu.setIcon(icons.ICON_COPY)
        self.copyMinitileAction = QAction(icons.ICON_SUBPALETTE, "Copy &minitile graphics", shortcut=QKeySequence("Ctrl+C"))
        self.copyMinitileAction.triggered.connect(self.onCopyMinitile)
        self.copyArrangementAction = QAction(icons.ICON_TILESET, "Copy tile &arrangement", shortcut=QKeySequence("Ctrl+Shift+C"))
        self.copyArrangementAction.triggered.connect(self.onCopyArrangement)
        self.copyCollisionAction = QAction(icons.ICON_WALL, "Copy tile &collision", shortcut=QKeySequence("Ctrl+Alt+C"))
        self.copyCollisionAction.triggered.connect(self.onCopyCollision)
        self.copyAllTileAction = QAction(icons.ICON_SQUARE, "Copy entire &tile", shortcut=QKeySequence("Ctrl+Alt+Shift+C"))
        self.copyAllTileAction.triggered.connect(self.onCopyTile)
        self.copyMenu.addActions([self.copyMinitileAction, self.copyArrangementAction, self.copyCollisionAction, self.copyAllTileAction])
        
        self.pasteAction = QAction(icons.ICON_PASTE, "&Paste", shortcut=QKeySequence("Ctrl+V"))
        self.pasteAction.triggered.connect(self.onPaste)
        
        self.menuEdit.addMenu(self.copyMenu)
        self.menuEdit.addAction(self.pasteAction)
        self.menuEdit.addSeparator()
        self.menuEdit.addActions([self.parent().sharedActionUndo, self.parent().sharedActionRedo])
        
        self.menuView = QMenu("&View")
        self.tileIDAction = self.parent().sharedActionTileIDs
        self.tileIDAction.triggered.connect(self.toggleTileIDs)
        if self.tileIDAction.isChecked():
            self.toggleTileIDs()
        self.gridAction = self.parent().sharedActionShowGrid
        self.gridAction.triggered.connect(self.toggleGrid)
        self.gridAction.triggered.connect(self.collisionScene.update)
        self.gridAction.triggered.connect(self.arrangementScene.update)
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
        self.findUnusedAction = QAction(icons.ICON_UNUSED_OBJECT, "&Unused minitile finder...")
        self.findUnusedAction.triggered.connect(self.onFindUnused)
        self.menuTools.addActions([self.renderTilesAction, self.renderMinitilesAction, self.autoRearrangeAction, self.findUnusedAction, self.parent().sharedActionTileSpace])
        self.parent().tileScratchSpace.scene.tileSelected.connect(self.tileScratchSpacePicked)
        
        self.menuHelp = QMenu("&Help")        
        self.menuHelp.addAction(self.parent().sharedActionAbout)
        if not debug.SYSTEM_OUTPUT:
            self.menuHelp.addAction(self.parent().sharedActionDebug)
        self.menuHelp.addAction(self.parent().sharedActionReport)
        
        self.menuItems = (self.menuFile, self.menuEdit, self.menuView, self.menuTools, self.menuHelp)
    
    def parent(self) -> "MainApplication": # for typing
        return super().parent()