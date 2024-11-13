import logging

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import (QAction, QDesktopServices, QFontDatabase, QIcon,
                           QKeySequence, QUndoStack)
from PySide6.QtWidgets import (QLabel, QMainWindow, QMenuBar, QMessageBox,
                               QTabWidget, QWidget)

import src.misc.common as common
import src.project.project as project
from src.mapeditor.map_editor import MapEditor
from src.misc import debug as debug
from src.misc import icons as icons
from src.misc.dialogues import AboutDialog, SettingsDialog
from src.paletteeditor.palette_editor import PaletteEditor
from src.tileeditor.tile_editor import TileEditor
from src.widgets.input import BaseChangerSpinbox
from src.widgets.misc import SignalUndoStack, UndoFutureLine, UndoHistoryLine


class MainApplication(QMainWindow):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logging.info("Main application initialised")

        self.app = app
        
        self.icon = QIcon(":/logos/icon.ico")
        self.setWindowIcon(self.icon)
        
        self.undoStack = SignalUndoStack()
        self.undoStack.cleanChanged.connect(self.updateTitle)
        
        self.undoHistoryLabel = UndoHistoryLine(self.undoStack)
        self.undoHistoryLabel.setElideMode(Qt.TextElideMode.ElideLeft)
        self.undoFutureLabel = UndoFutureLine(self.undoStack)

        # TODO test for other platforms
        self.resize(common.DEFAULTEDITORWIDTH, common.DEFAULTEDITORHEIGHT)
        self.setMinimumSize(common.MINEDITORWIDTH, common.MINEDITORHEIGHT) # ~ minimum map editor size on windows        
        # set up shared actions
        self.sharedActionTileIDs = QAction("Show &tile IDs", shortcut=QKeySequence("Ctrl+T"))
        self.sharedActionTileIDs.setCheckable(True)
        if QSettings().value("mapeditor/ShowTileIDs", type=bool):
            self.sharedActionTileIDs.trigger()
        self.sharedActionTileIDs.triggered.connect(lambda: QSettings().setValue("mapeditor/ShowTileIDs", self.sharedActionTileIDs.isChecked()))
        
        self.sharedActionShowGrid = QAction("Show &grid", shortcut=QKeySequence("Ctrl+G"))
        self.sharedActionShowGrid.setCheckable(True)
        if QSettings().value("mapeditor/ShowGrid", type=bool):
            self.sharedActionShowGrid.trigger()
        self.sharedActionShowGrid.triggered.connect(lambda: QSettings().setValue("mapeditor/ShowGrid", self.sharedActionShowGrid.isChecked()))
        self.sharedActionShowGrid.triggered.connect(lambda: QSettings().sync())
        
        self.sharedActionHex = QAction("Use &hexadecimal", shortcut=QKeySequence("Ctrl+H"))
        self.sharedActionHex.setCheckable(True)
        self.sharedActionHex.triggered.connect(lambda: BaseChangerSpinbox.toggleMode())
        if QSettings().value("main/HexMode", type=bool):
            self.sharedActionHex.trigger()
        self.sharedActionHex.triggered.connect(lambda: QSettings().setValue("main/HexMode", self.sharedActionHex.isChecked()))

        self.sharedActionUndo = QAction(icons.ICON_UNDO, "&Undo", shortcut=QKeySequence("Ctrl+Z"))
        self.sharedActionUndo.triggered.connect(self.undoStack.undo)
        self.sharedActionRedo = QAction(icons.ICON_REDO, "&Redo")
        self.sharedActionRedo.setShortcuts([QKeySequence("Ctrl+Y"), QKeySequence("Ctrl+Shift+Z")])
        self.sharedActionRedo.triggered.connect(self.undoStack.redo)
        
        self.sharedActionAbout = QAction(icons.ICON_INFO, "&About EBME...")
        self.sharedActionAbout.triggered.connect(lambda: AboutDialog.showAbout(self))
        self.sharedActionDebug = QAction(icons.ICON_DEBUG, "&Debug output...")
        self.sharedActionDebug.triggered.connect(lambda: debug.DebugOutputDialog.openDebug(self))
        self.sharedActionReport = QAction(icons.ICON_BUG, "&Report a bug...")
        self.sharedActionReport.triggered.connect(lambda: QDesktopServices.openUrl("https://github.com/Supremekirb/EBME/issues/new"))
        
        self.sharedActionSettings = QAction(icons.ICON_SETTINGS, "&Settings...")
        self.sharedActionSettings.triggered.connect(lambda: SettingsDialog.openSettings(self))
        
        self.setupUI()
        

        # initialise EB fonts, because you need to do that after the program has begun and whatever
        # EBMain has monospaced numbers, so we use it in the map editor
        # Apple Kid has a full set of regular characters, so we use it for the EB theme
        # StatusPlz is the mini font, also for the EB theme
        # Onett is good for headers, which we use for About EBME
        # Saturn Boing is exclusively for Mr. Saturn quotes in About EBME
        # Also, there are some issues with QResources with fonts, so we need to use absolute paths...
        try:
            QFontDatabase.addApplicationFont(common.absolutePath("assets/fonts/EBMain.ttf"))
        except Exception as _:
            logging.warning("Couldn't initialise EB font! Trying default")

        try:
            QFontDatabase.addApplicationFont(common.absolutePath("assets/fonts/apple_kid.ttf"))
        except Exception as _:
            logging.warning("Couldn't initialise EB display font!")

        try:
            QFontDatabase.addApplicationFont(common.absolutePath("assets/fonts/statusplz.ttf"))
        except Exception as _:
            logging.warning("Couldn't initialise EB mini font!")

        try:
            QFontDatabase.addApplicationFont(common.absolutePath("assets/fonts/onett.ttf"))
        except Exception as _:
            logging.warning("Couldn't initialise EB header font!")

        try:
            QFontDatabase.addApplicationFont(common.absolutePath("assets/fonts/saturn_boing.ttf"))
        except Exception as _:
            logging.warning("Couldn't initialise Mr. Saturn font!")

    def onTabSwitch(self):
        # So there are some weird garbage collection things
        # regarding menus.
        # instead of replacing it outright, just change
        # the contents.
        self.menu.clear()
        new = self.mainTabWin.widget(self.mainTabWin.currentIndex())
        if hasattr(new, "menuItems"):
            for i in new.menuItems:
                self.menu.addMenu(i)
                
    def updateTitle(self):
        title = self.window().windowTitle()
        if not self.undoStack.isClean():
            if not title.endswith("*"):
                self.window().setWindowTitle(title + "*")
        else:
            if title.endswith("*"):
                self.window().setWindowTitle(title[:-1])


    def closeEvent(self, event):
        if isinstance(self.mapWin, MapEditor):
            if self.projectWin.isSaving:
                msg = QMessageBox(self)
                msg.setText("The program shouldn't be closed while it's saving.")
                msg.setInformativeText("Please wait and try again, or close the program anyway (may be unsafe).")
                msg.setDefaultButton(QMessageBox.StandardButton.Ok)
                msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Close)
                if msg.exec() == QMessageBox.StandardButton.Close:
                    event.accept()
                else:
                    event.ignore()
                    
            if not self.mapWin.scene.undoStack.isClean() or not self.tileWin.undoStack.isClean() \
            or not self.paletteWin.undoStack.isClean():
                msg = QMessageBox(self)
                msg.setText("Save your changes before closing?")
                msg.setStandardButtons(QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
                msg.setDefaultButton(QMessageBox.StandardButton.Save)
                
                result = msg.exec()
                
                if result == QMessageBox.StandardButton.Save:
                    if self.projectWin.saveAction.isEnabled():
                        self.projectWin.saveProject()
                        event.ignore()
                        
                elif result == QMessageBox.StandardButton.Cancel:
                    event.ignore()

                else:
                    event.accept()
                    
        else: event.accept()
            
    def setupUI(self):
        self.mainTabWin = QTabWidget(self)
        self.projectWin = project.Project(self)
        self.mapWin: MapEditor = QWidget() # replaced by MapEditor
        self.tileWin: TileEditor = QWidget() # replaced by TileEditor
        self.paletteWin: PaletteEditor = QWidget() # replaced by PaletteEditor

        self.mainTabWin.addTab(self.projectWin, "Project")
        self.mainTabWin.addTab(self.mapWin, "Map Editor")
        self.mainTabWin.addTab(self.tileWin, "Tile Editor")
        self.mainTabWin.addTab(self.paletteWin, "Palette Editor")

        self.mainTabWin.setTabEnabled(1, False)
        self.mainTabWin.setTabEnabled(2, False)
        self.mainTabWin.setTabEnabled(3, False)

        self.mainTabWin.currentChanged.connect(self.onTabSwitch)

        self.setCentralWidget(self.mainTabWin)
        self.statusBar().addWidget(self.undoHistoryLabel, 1)
        label = QLabel()
        label.setPixmap(icons.ICON_DOWN_DOUBLE.pixmap(16, 16))
        self.statusBar().addWidget(label)
        self.statusBar().addWidget(self.undoFutureLabel, 1)
        self.statusBar().setSizeGripEnabled(False)
        
        if not QSettings().value("main/showUndoRedo", True, type=bool):
            self.statusBar().hide()

        self.menu = QMenuBar(self)
        self.setMenuBar(self.menu)

        for i in self.projectWin.menuItems:
            self.menu.addMenu(i)