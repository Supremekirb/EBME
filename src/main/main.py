import logging

from PySide6.QtGui import QFontDatabase, QIcon
from PySide6.QtWidgets import (QMainWindow, QMenuBar, QMessageBox, QTabWidget,
                               QWidget)

import src.misc.common as common
import src.project.project as project
from src.mapeditor.map_editor import MapEditor


class MainApplication(QMainWindow):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logging.info("Main application initialised")

        self.app = app
        
        self.icon = QIcon(":/logos/icon.ico")
        self.setWindowIcon(self.icon)

        # TODO test for other platforms
        self.resize(common.DEFAULTEDITORWIDTH, common.DEFAULTEDITORHEIGHT)
        self.setMinimumSize(common.MINEDITORWIDTH, common.MINEDITORHEIGHT) # ~ minimum map editor size on windows
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
                    
            if not self.mapWin.scene.undoStack.isClean():                    
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
        # self.tileWin = QWidget()

        self.mainTabWin.addTab(self.projectWin, "Project")
        self.mainTabWin.addTab(self.mapWin, "Map Editor")
        # self.mainTabWin.addTab(self.tileWin, "Tile Editor")

        self.mainTabWin.setTabEnabled(1, False)
        self.mainTabWin.setTabEnabled(2, False)

        self.mainTabWin.currentChanged.connect(self.onTabSwitch)

        self.setCentralWidget(self.mainTabWin)

        self.menu = QMenuBar(self)
        self.setMenuBar(self.menu)

        for i in self.projectWin.menuItems:
            self.menu.addMenu(i)