from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QKeySequence, Qt
from PySide6.QtWidgets import (QGraphicsView, QHBoxLayout, QMenu, QSizePolicy,
                               QWidget)

import src.misc.debug as debug
import src.misc.icons as icons
from src.gnat.game_scene import GameScene

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