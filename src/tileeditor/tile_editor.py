from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QKeySequence
from PySide6.QtWidgets import (QComboBox, QGraphicsView, QGroupBox,
                               QHBoxLayout, QListWidget, QMenu, QPushButton,
                               QSizePolicy, QToolButton, QVBoxLayout, QWidget)

import src.misc.common as common
import src.misc.debug as debug
from src.coilsnake.project_data import ProjectData
from src.misc.dialogues import (AboutDialog, SettingsDialog,
                                TileEditorAboutDialog)
from src.misc.widgets import AspectRatioWidget
from src.tileeditor.arrangement_editor import ArrangementScene
from src.tileeditor.collision_editor import CollisionScene
from src.tileeditor.graphics_editor import (MinitileGraphicsWidget,
                                            PaletteSelector)
from src.tileeditor.minitile_selector import MinitileScene, MinitileView
from src.tileeditor.tile_selector import TileScene


class TileEditorState():
    def __init__(self, tileeditor: "TileEditor"):
        
        self.tileEditor = tileeditor
        
        self.currentTileset = 0
        self.currentPaletteGroup = 0
        self.currentPalette = 0
        self.currentSubpalette = 0
        self.currentMinitile = 0
        

class TileEditor(QWidget):
    def __init__(self, parent, projectData: ProjectData):
        super().__init__(parent)
        
        self.projectData = projectData
        self.state = TileEditorState(self)
        
        self.setupUI()
        # self.onTilesetSelect()

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
        
    def selectMinitile(self, minitile: int):
        self.state.currentMinitile = minitile
        minitileObj = self.projectData.getTileset(self.state.currentTileset).minitiles[minitile]
        subpaletteObj = self.projectData.getTileset(self.state.currentTileset).getPalette(
            self.state.currentPaletteGroup, self.state.currentPalette
            ).subpalettes[self.state.currentSubpalette]
        
        self.fgScene.currentMinitile = minitileObj
        self.fgScene.currentSubpalette = subpaletteObj
        self.fgScene.update()
        
        self.bgScene.currentMinitile = minitileObj
        self.bgScene.currentSubpalette = subpaletteObj
        self.bgScene.update()
        
        
    def setupUI(self):
        contentLayout = QVBoxLayout()
        topLayout = QHBoxLayout()
        bottomLayout = QHBoxLayout()
        
        minitileBox = QGroupBox("Minitiles")
        minitileLayout = QVBoxLayout()
        tilesetSelectLayout = QHBoxLayout()
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
        self.tileView = QGraphicsView(self.tileScene)
        self.tileView.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.tileView.setFixedHeight(32*TileScene.TILE_HEIGHT+1+self.tileView.verticalScrollBar().sizeHint().height())
        self.tileView.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.arrangementScene = ArrangementScene(self, self.projectData)
        self.arrangementView = QGraphicsView(self.arrangementScene)
        self.arrangementView.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        self.collisionScene = CollisionScene(self, self.projectData)
        self.collisionView = QGraphicsView(self.collisionScene)
        self.collisionView.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        self.presetList = QListWidget()
        self.presetList.addItem("Foobar")
        self.presetList.addItem("Boofar")
        self.presetList.setMinimumWidth(self.presetList.sizeHint().width()-100) # it is a little too smol
        
        self.fgScene = MinitileGraphicsWidget(self.projectData)
        self.fgAspectRatioContainer = AspectRatioWidget(self.fgScene)
        
        self.bgScene = MinitileGraphicsWidget(self.projectData)
        self.bgScene.isForeground = False
        self.bgAspectRatioContainer = AspectRatioWidget(self.bgScene)
        
        self.paletteView = PaletteSelector(self)
        
                
        self.tilesetSelect = QComboBox()
        self.tilesetSelect.addItems(str(i.id) for i in self.projectData.tilesets)
        self.paletteGroupSelect = QComboBox()
        self.paletteSelect = QComboBox()
        self.subpaletteSelect = QComboBox()
        self.tilesetSelect.activated.connect(self.onTilesetSelect)
        self.paletteGroupSelect.activated.connect(self.onPaletteGroupSelect)
        self.paletteSelect.activated.connect(self.onPaletteSelect)
        self.subpaletteSelect.activated.connect(self.onSubpaletteSelect)
        
        tilesetSelectLayout.addWidget(self.tilesetSelect)
        tilesetSelectLayout.addWidget(self.paletteGroupSelect)
        tilesetSelectLayout.addWidget(self.paletteSelect)
        tilesetSelectLayout.addWidget(self.subpaletteSelect)
        
        minitileLayout.addLayout(tilesetSelectLayout)
        minitileLayout.addWidget(self.minitileView)
        
        drawingLayout.addWidget(self.fgAspectRatioContainer)
        self.bgToFgButton = QToolButton()
        self.bgToFgButton.setArrowType(Qt.ArrowType.UpArrow)
        self.fgToBgButton = QToolButton()
        self.fgToBgButton.setArrowType(Qt.ArrowType.DownArrow)
        swapperButtonLayout.addWidget(self.bgToFgButton)
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
        
        collisionLayout.addWidget(self.presetList)
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
        
        self.menuItems = (self.menuFile, self.menuHelp)