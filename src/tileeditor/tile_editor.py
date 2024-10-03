from copy import copy
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import (QAction, QColor, QKeySequence, QUndoCommand,
                           QUndoStack)
from PySide6.QtWidgets import (QComboBox, QGraphicsView, QGroupBox,
                               QHBoxLayout, QLabel, QMenu, QPushButton,
                               QSizePolicy, QStyle, QToolButton, QUndoView,
                               QVBoxLayout, QWidget)

import src.misc.common as common
import src.misc.debug as debug
from src.actions.minitile_actions import ActionChangeBitmap
from src.actions.misc_actions import MultiActionWrapper
from src.coilsnake.project_data import ProjectData
from src.misc.dialogues import (AboutDialog, SettingsDialog,
                                TileEditorAboutDialog)
from src.misc.widgets import AspectRatioWidget, HorizontalGraphicsView
from src.tileeditor.arrangement_editor import ArrangementScene
from src.tileeditor.collision_editor import CollisionPresetList, CollisionScene
from src.tileeditor.graphics_editor import (MinitileGraphicsWidget,
                                            PaletteSelector)
from src.tileeditor.minitile_selector import MinitileScene, MinitileView
from src.tileeditor.tile_selector import TileScene

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
        
        for c in commands:
            if isinstance(c, ActionChangeBitmap):
                self.fgScene.copyToScratch()
                self.bgScene.copyToScratch()
                self.fgScene.update()
                self.bgScene.update()
                
    def onTilesetSelect(self):
        
        value = int(self.tilesetSelect.currentText())
        self.state.currentTileset = value
        self.paletteGroupSelect.blockSignals(True)
        self.paletteGroupSelect.clear()
        self.paletteGroupSelect.addItems(str(i.groupID) for i in self.projectData.getTileset(value).paletteGroups)
        self.onPaletteGroupSelect()
        self.paletteGroupSelect.blockSignals(False)
        
    def onPaletteGroupSelect(self):
        value = int(self.paletteGroupSelect.currentText())
        self.state.currentPaletteGroup = value
        self.paletteSelect.blockSignals(True)
        self.paletteSelect.clear()
        self.paletteSelect.addItems(str(i.paletteID) for i in self.projectData.getTileset(
            self.state.currentTileset).getPaletteGroup(value).palettes)
        
        self.onPaletteSelect()
        self.paletteSelect.blockSignals(False)    
        
    def onPaletteSelect(self):
        value = int(self.paletteSelect.currentText())
        self.state.currentPalette = value
        self.subpaletteSelect.blockSignals(True)
        self.subpaletteSelect.clear()
        self.subpaletteSelect.addItems(str(i) for i in range(len(self.projectData.getTileset(
            self.state.currentTileset).getPalette(self.state.currentPaletteGroup, value).subpalettes)))
        self.onSubpaletteSelect()
        self.subpaletteSelect.blockSignals(False)
        
        self.tileScene.renderTileset(self.state.currentTileset, self.state.currentPaletteGroup, self.state.currentPalette)
        
    def onSubpaletteSelect(self):
        value = int(self.subpaletteSelect.currentText())
        self.state.currentSubpalette = value
        self.minitileScene.renderTileset(self.state.currentTileset,
                                         self.state.currentPaletteGroup,
                                         self.state.currentPalette,
                                         self.state.currentSubpalette)
        for i in range(16):
            self.paletteView.buttons[i].setColour(QColor.fromRgb(*self.projectData.getTileset(
                self.state.currentTileset).getPalette(
                    self.state.currentPaletteGroup, self.state.currentPalette
                ).subpalettes[self.state.currentSubpalette].subpaletteRGBA[i]))
            
        self.selectMinitile(self.state.currentMinitile)
    
    def onTileSelect(self):
        self.state.currentTile = self.tileScene.currentTile
        
    def selectMinitile(self, minitile: int):
        self.state.currentMinitile = minitile
        
        if minitile >= common.MINITILENOFOREGROUND:
            self.fgToBgButton.setDisabled(True)
            self.bgToFgButton.setDisabled(True)
            self.swapBgAndFgButton.setDisabled(True)
        else:
            self.fgToBgButton.setEnabled(True)
            self.bgToFgButton.setEnabled(True)
            self.swapBgAndFgButton.setEnabled(True)
        
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
        
    def selectColour(self, index: int):
        self.state.currentColourIndex = index
        self.paletteView.setColourIndex(index)
        
    def copyBgToFg(self):
        if self.state.currentMinitile >= common.MINITILENOFOREGROUND:
            return
        bgBitmap = self.bgScene._scratchBitmap
        action = ActionChangeBitmap(self.fgScene.currentMinitile, bgBitmap, True)
        self.undoStack.push(action)
        self.fgScene.copyToScratch()
        self.fgScene.update()
        
    def copyFgToBg(self):
        if self.state.currentMinitile >= common.MINITILENOFOREGROUND:
            return
        fgBitmap = self.fgScene._scratchBitmap
        action = ActionChangeBitmap(self.bgScene.currentMinitile, fgBitmap, False)
        self.undoStack.push(action)
        self.bgScene.copyToScratch()
        self.bgScene.update()
        
    def swapBgAndFg(self):
        if self.state.currentMinitile >= common.MINITILENOFOREGROUND:
            return
        self.undoStack.beginMacro("Swap BG and FG")
        bgBitmap = copy(self.bgScene._scratchBitmap)
        self.copyFgToBg()
        action = ActionChangeBitmap(self.fgScene.currentMinitile, bgBitmap, True)
        self.undoStack.push(action)
        self.undoStack.endMacro()
        self.fgScene.copyToScratch()
        self.fgScene.update()
        
    def setupUI(self):
        contentLayout = QVBoxLayout()
        topLayout = QHBoxLayout()
        bottomLayout = QHBoxLayout()
        
        minitileBox = QGroupBox("Minitiles")
        minitileLayout = QVBoxLayout()
        tilesetSelectLayout = QHBoxLayout()
        tilesetSelectTilesetLayout = QVBoxLayout()
        tilesetSelectPaletteGroupLayout = QVBoxLayout()
        tilesetSelectPaletteLayout = QVBoxLayout()
        tilesetSelectSubpaletteLayout = QVBoxLayout()
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
        
        self.tileScene = TileScene(self, self.projectData)
        self.tileScene.tileSelected.connect(self.onTileSelect)
        self.tileView = HorizontalGraphicsView(self.tileScene)
        self.tileView.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.tileView.setFixedHeight(32*TileScene.TILE_HEIGHT+1+self.tileView.horizontalScrollBar().sizeHint().height())
        self.tileView.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tileView.centerOn(0, 0)
        
        self.arrangementScene = ArrangementScene(self, self.projectData)
        self.arrangementView = QGraphicsView(self.arrangementScene)
        self.arrangementView.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        self.collisionScene = CollisionScene(self, self.projectData)
        self.collisionView = QGraphicsView(self.collisionScene)
        self.collisionView.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        self.presetList = CollisionPresetList(self.state)
        self.presetList.list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.fgScene = MinitileGraphicsWidget(self.projectData, self.state)
        self.fgScene.colourPicked.connect(self.selectColour)
        self.fgAspectRatioContainer = AspectRatioWidget(self.fgScene)
        
        self.bgScene = MinitileGraphicsWidget(self.projectData, self.state)
        self.bgScene.isForeground = False
        self.bgScene.colourPicked.connect(self.selectColour)
        self.bgAspectRatioContainer = AspectRatioWidget(self.bgScene)
        
        self.paletteView = PaletteSelector(self)
        self.paletteView.colourChanged.connect(self.selectColour)
                
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
        
        self.subpaletteSelect = QComboBox()
        tilesetSelectSubpaletteLayout.addWidget(QLabel("Subpalette"))
        tilesetSelectSubpaletteLayout.addWidget(self.subpaletteSelect)
        
        self.tilesetSelect.activated.connect(self.onTilesetSelect)
        self.paletteGroupSelect.activated.connect(self.onPaletteGroupSelect)
        self.paletteSelect.activated.connect(self.onPaletteSelect)
        self.subpaletteSelect.activated.connect(self.onSubpaletteSelect)
        
        tilesetSelectLayout.addLayout(tilesetSelectTilesetLayout)
        tilesetSelectLayout.addLayout(tilesetSelectPaletteGroupLayout)
        tilesetSelectLayout.addLayout(tilesetSelectPaletteLayout)
        tilesetSelectLayout.addLayout(tilesetSelectSubpaletteLayout)
        
        minitileLayout.addLayout(tilesetSelectLayout)
        minitileLayout.addWidget(self.minitileView)
        
        drawingLayout.addWidget(self.fgAspectRatioContainer)
        self.bgToFgButton = QToolButton()
        self.bgToFgButton.setArrowType(Qt.ArrowType.UpArrow)
        self.bgToFgButton.setToolTip("Copy background to foreground")
        self.bgToFgButton.clicked.connect(self.copyBgToFg)
        self.swapBgAndFgButton = QToolButton()
        self.swapBgAndFgButton.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.swapBgAndFgButton.setToolTip("Swap foreground and background")
        self.swapBgAndFgButton.clicked.connect(self.swapBgAndFg)
        self.fgToBgButton = QToolButton()
        self.fgToBgButton.setArrowType(Qt.ArrowType.DownArrow)
        self.fgToBgButton.setToolTip("Copy foreground to background")
        self.fgToBgButton.clicked.connect(self.copyFgToBg)
        swapperButtonLayout.addWidget(self.bgToFgButton)
        swapperButtonLayout.addWidget(self.swapBgAndFgButton)
        swapperButtonLayout.addWidget(self.fgToBgButton)
        drawingLayout.addLayout(swapperButtonLayout)
        drawingLayout.addWidget(self.bgAspectRatioContainer)
        paletteLayout.addWidget(self.paletteView)
        self.editPaletteButton = QPushButton("Edit")
        self.editPaletteButton.clicked.connect(self.paletteView.openEditor)
        paletteLayout.addWidget(self.editPaletteButton)
        
        graphicsLayout.addLayout(drawingLayout)
        graphicsLayout.addLayout(paletteLayout)
        
        tileLayout.addWidget(self.tileView)
        tileLayout.addWidget(self.arrangementView)
        
        collisionLayout.addLayout(self.presetList)
        collisionLayout.addWidget(self.collisionView)
        
        topLayout.addWidget(minitileBox)
        topLayout.addWidget(graphicsBox)
        bottomLayout.addWidget(tileBox)
        bottomLayout.addWidget(collisionBox)
        
        contentLayout.addLayout(topLayout)
        contentLayout.addLayout(bottomLayout)
        
        self.setLayout(contentLayout)       
        
        
        self.menuFile = QMenu("&File")
        self.saveAction = QAction("&Save", shortcut=QKeySequence("Ctrl+S"))
        self.saveAction.triggered.connect(self.parent().projectWin.saveAction.trigger)
        self.openAction = QAction("&Open", shortcut=QKeySequence("Ctrl+O"))
        self.openAction.triggered.connect(self.parent().projectWin.openAction.trigger)
        self.reloadAction = QAction("&Reload", shortcut=QKeySequence("Ctrl+R"))
        self.reloadAction.triggered.connect(self.parent().projectWin.reloadAction.trigger)
        self.openSettingsAction = QAction("Settings...")
        self.openSettingsAction.triggered.connect(lambda: SettingsDialog.openSettings(self))
        self.menuFile.addActions([self.saveAction, self.openAction, self.reloadAction])
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.openSettingsAction)
        
        self.menuEdit = QMenu("&Edit")
        self.undoAction = QAction("&Undo", shortcut=QKeySequence("Ctrl+Z"))
        self.undoAction.triggered.connect(self.onUndo)
        self.redoAction = QAction("&Redo")
        self.redoAction.setShortcuts([QKeySequence("Ctrl+Y"), QKeySequence("Ctrl+Shift+Z")])
        self.redoAction.triggered.connect(self.onRedo)
        self.menuEdit.addActions([self.undoAction, self.redoAction])
        
        self.menuHelp = QMenu("&Help")
        self.aboutTileEditorAction = QAction("About the &tile editor...")
        self.aboutTileEditorAction.triggered.connect(lambda: TileEditorAboutDialog.showAbout(self))
        self.menuHelp.addAction(self.aboutTileEditorAction)
        
        self.aboutAction = QAction("&About EBME...")
        self.aboutAction.triggered.connect(lambda: AboutDialog.showAbout(self))
        self.menuHelp.addAction(self.aboutAction)
        
        if not debug.SYSTEM_OUTPUT:
            self.openDebugAction = QAction("Debug output")
            self.openDebugAction.triggered.connect(lambda: debug.DebugOutputDialog.openDebug(self))
            self.menuHelp.addAction(self.openDebugAction)
        
        self.menuItems = (self.menuFile, self.menuEdit, self.menuHelp)
    
    def parent(self) -> "MainApplication": # for typing
        return super().parent()