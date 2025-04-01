from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QColor, QKeySequence, Qt, QUndoCommand
from PySide6.QtWidgets import (QFileDialog, QFormLayout, QGraphicsScene,
                               QGraphicsView, QGridLayout, QGroupBox,
                               QHBoxLayout, QListWidget, QListWidgetItem,
                               QMenu, QMessageBox, QPushButton, QSizePolicy,
                               QSpinBox, QToolButton, QTreeWidgetItem,
                               QVBoxLayout, QWidget)

import src.misc.common as common
import src.misc.debug as debug
import src.misc.icons as icons
from src.coilsnake.fts_interpreter import Palette
from src.coilsnake.project_data import ProjectData
from src.gnat.game_scene import GameScene
from src.misc.dialogues import (AboutDialog, AdvancedPalettePreviewDialog,
                                CopyEventPaletteDialog, EditEventPaletteDialog,
                                RenderPaletteDialog, SettingsDialog)
from src.objects.palette_settings import PaletteSettings
from src.widgets.input import ColourButton, FlagInput
from src.widgets.misc import IconLabel
from src.widgets.palette import (PaletteListItem, PaletteTreeWidget,
                                 SubpaletteListItem)

if TYPE_CHECKING:
    from src.main.main import MainApplication

class GnatAttack(QWidget):
    def __init__(self, parent: QWidget|None = None):
        super().__init__(parent)        
        self.setupUI()
        
    def setupUI(self):
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        self.gameScene = GameScene()
        
        self.gameView = QGraphicsView(self.gameScene)
        self.gameView.scale(2, 2)
        self.gameView.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.gameView.setCursor(Qt.CursorShape.BlankCursor)

        layout.addWidget(self.gameView)
        
        self.menuFile = QMenu("&File")
        self.saveAction = QAction(icons.ICON_SAVE, "&Save", shortcut=QKeySequence("Ctrl+S"))
        self.saveAction.triggered.connect(self.parent().projectWin.saveAction.trigger)
        self.openAction = QAction(icons.ICON_LOAD, "&Open", shortcut=QKeySequence("Ctrl+O"))
        self.openAction.triggered.connect(self.parent().projectWin.openAction.trigger)
        self.reloadAction = QAction(icons.ICON_RELOAD, "&Reload", shortcut=QKeySequence("Ctrl+R"))
        self.reloadAction.triggered.connect(self.parent().projectWin.reloadAction.trigger)
        self.menuFile.addActions([self.openAction, self.saveAction, self.reloadAction])
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.parent().sharedActionSettings)

        self.menuHelp = QMenu("&Help")
        self.menuHelp.addAction(self.parent().sharedActionAbout)
        if not debug.SYSTEM_OUTPUT:
            self.menuHelp.addAction(self.parent().sharedActionDebug)
        self.menuHelp.addAction(self.parent().sharedActionReport)

        self.menuItems = (self.menuFile, self.menuHelp)
        
    def parent(self) -> "MainApplication": # for typing
        return super().parent()