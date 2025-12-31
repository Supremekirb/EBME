import logging
import os
import traceback
from typing import TYPE_CHECKING

import requests
from PySide6.QtCore import QPoint, QSettings, Qt, QThread, QTimer
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence, QPixmap
from PySide6.QtWidgets import (QApplication, QFileDialog, QFormLayout,
                               QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QMenu, QMessageBox,
                               QPlainTextEdit, QProgressBar, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget)

import src.coilsnake.load as load
import src.coilsnake.save as save
import src.mapeditor.map_editor as map_editor
import src.misc.common as common
import src.misc.debug as debug
import src.misc.icons as icons
import src.tileeditor.tile_editor as tile_editor
from src.coilsnake.project_data import ProjectData
from src.gnat.gnat_attack import GnatAttack
from src.misc import flushrefs
from src.misc.dialogues import AboutDialog, SettingsDialog
from src.misc.scratch import TileScratchSpace
from src.misc.worker import Worker
from src.paletteeditor.palette_editor import PaletteEditor
from src.widgets.misc import IconLabel

if TYPE_CHECKING:
    from src.main.main import MainApplication


class Project(QWidget):
    def __init__(self, mainWin: "MainApplication", *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.mainWin = mainWin

        self.setupUI()
        self.disableSave()
        self.disableReload()
        self.disableEditors()
        self.projectInfo.setDisabled(True)
        
        self.isSaving = False

    def enableOpen(self):
        self.openProjectButton.setEnabled(True)
        self.openAction.setEnabled(True)

    def disableOpen(self):
        self.openProjectButton.setEnabled(False)
        self.openAction.setEnabled(False)

    def enableSave(self):
        self.saveProjectButton.setEnabled(True)
        self.saveAction.setEnabled(True)

    def disableSave(self):
        self.saveProjectButton.setEnabled(False)
        self.saveAction.setEnabled(False)

    def enableReload(self):
        self.reloadProjectButton.setEnabled(True)
        self.reloadAction.setEnabled(True)

    def disableReload(self):
        self.reloadProjectButton.setEnabled(False)
        self.reloadAction.setEnabled(False)

    def enableEditors(self):
        self.mainWin.mainTabWin.setTabEnabled(1, True)
        self.mainWin.mainTabWin.setTabEnabled(2, True)
        self.mainWin.mainTabWin.setTabEnabled(3, True)
        self.mainWin.mainTabWin.setTabEnabled(4, True)

    def disableEditors(self):
        self.mainWin.mainTabWin.setTabEnabled(1, False)
        self.mainWin.mainTabWin.setTabEnabled(2, False)
        self.mainWin.mainTabWin.setTabEnabled(3, False)
        self.mainWin.mainTabWin.setTabEnabled(4, False)

    def openDirectory(self, dir: str=None):
        """Open a project at `dir` and initialise data. (If the user cancels, don't do anything)

        Args:
            dir (str, optional): Path to a project. Defaults to None. If left default, a file dialog will open.
        """
        
        # if we have unsaved changes, ask about that first
        if isinstance(self.mainWin.mapWin, map_editor.MapEditor):
            if not self.mainWin.mapWin.scene.undoStack.isClean():
                msg = QMessageBox(self)
                if dir == self.projectData.dir:
                    msg.setText("Save your changes before reloading the project?")
                else:
                    msg.setText("Save your changes before opening a new project?")
                msg.setStandardButtons(QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
                msg.setDefaultButton(QMessageBox.StandardButton.Save)
                result = msg.exec()
                
                if result == QMessageBox.StandardButton.Save:
                    if self.saveAction.isEnabled():
                        self.saveProject()
                        return
                
                elif result == QMessageBox.StandardButton.Cancel:
                    return
        if not dir:
            dir = os.path.normpath(
                QFileDialog.getExistingDirectory(
                    self, "Select a CoilSnake project folder"))
            
        if dir != ".": # file dialog returns "." if cancelled
            logging.info(f"Loading project at {dir}")
            self.currentDirectory = dir
            self.disableSave()
            self.disableReload()
            self.disableEditors()
            self.projectInfo.setDisabled(True)
            self.disableOpen()

            self.window().setWindowTitle("EBME")
            self.updateStatusLabel("Loading project...")
            
            # close non-blocking project-related dialogues
            # only do it if they exist (ie. we loaded a project)
            if self.mainWin.tileScratchSpace:
                self.mainWin.tileScratchSpace.close()

            self.loadingProgress.setMaximum(0)
            self.loadingProgress.setMinimum(0)
            self.loadingProgress.setValue(0)

            self.workerThread = QThread()

            self.worker = Worker(load.readDirectory, dir)
            self.worker.updates.connect(self.updateStatusLabel)
            self.worker.returns.connect(self.finishedProjectLoad)
            
            self.worker.moveToThread(self.workerThread)
            self.workerThread.started.connect(self.worker.run)

            self.workerThread.start()

    def updateStatusLabel(self, text: str):
        self.statusLabel.setText(text)
    
    def finishedProjectLoad(self, data):
        self.workerThread.quit()

        # successful load
        if isinstance(data, ProjectData):
            try:
                flushrefs.flush() # VERY IMPORTANT I THINK
                self.projectData = data
                settings = QSettings()
                settings.setValue("main/LastProjectPath", self.projectData.dir)

                self.addRecent(self.projectData.getProjectName(), self.projectData.dir)
                
                try:
                    self.updateStatusLabel("Loading things...") # needs to come first b/c of connections
                    self.statusLabel.repaint()
                    try:
                        self.mainWin.tileScratchSpace = TileScratchSpace(self.projectData, self.mainWin)
                    except Exception as e:
                        common.showErrorMsg(title="Error loading tile scratch space", text="An error occured while loading the tile scratch space.", info=str(e))
                        self.updateStatusLabel("Error loading tile scratch space.")
                        logging.warning(f"Error loading tile scratch space: {traceback.format_exc()}")
                        raise
                    
                    self.updateStatusLabel("Loading map editor...")
                    self.statusLabel.repaint() # otherwise it may not show before we actually process the next bit
                    try:
                        self.mainWin.mapWin = map_editor.MapEditor(self.mainWin, self.projectData)
                    except Exception as e:
                        common.showErrorMsg(title="Error loading map editor", text="An error occurred while loading the map editor.", info=str(e))
                        self.updateStatusLabel("Error loading map editor.")
                        logging.warning(f"Error loading map editor: {traceback.format_exc()}")
                        raise
                    
                    self.updateStatusLabel("Loading tile editor...")
                    self.statusLabel.repaint()
                    try:
                        self.mainWin.tileWin = tile_editor.TileEditor(self.mainWin, self.projectData)
                    except Exception as e:
                        common.showErrorMsg(title="Error loading tile editor", text="An error occurred while loading the tile editor.", info=str(e))
                        self.updateStatusLabel("Error loading tile editor.")
                        logging.warning(f"Error loading tile editor: {traceback.format_exc()}")
                        raise
                    
                    self.updateStatusLabel("Loading palette editor...")
                    self.statusLabel.repaint()
                    try:
                        self.mainWin.paletteWin = PaletteEditor(self.projectData, self.mainWin)
                    except Exception as e:
                        common.showErrorMsg(title="Error loading palette manager", text="An error occured while loading the palette editor.", info=str(e))
                        self.updateStatusLabel("Error loading palette editor.")
                        logging.warning(f"Error loading palette editor: {traceback.format_exc()}")
                        raise
                    
                    # self.updateStatusLabel("Loading Gnat Attack...")
                    # self.statusLabel.repaint()
                    # try:
                    #     if isinstance(self.mainWin.gnatWin, GnatAttack):
                    #         self.mainWin.gnatWin.gameScene.gameState.stopBGM()
                    #         for i in self.mainWin.gnatWin.gameScene.gameState.enemiesOnScreen:
                    #             self.mainWin.gnatWin.gameScene.removeItem(i)
                    #             i.deleteLater()
                    #     self.mainWin.gnatWin = GnatAttack(self.projectData, self.mainWin)
                    # except Exception as e:
                    #     common.showErrorMsg(title="Error loading Gnat Attack", text="An error occured while loading Gnat Attack.", info=str(e))
                    #     self.updateStatusLabel("Error loading Gnat Attack.")
                    #     logging.warning(f"Error loading Gnat Attack: {traceback.format_exc()}")
                    #     raise
                                            
                except: pass # we've already shown an error message and logged it, so just continue
                
                else:
                    self.mainWin.mainTabWin.removeTab(4)
                    self.mainWin.mainTabWin.removeTab(3)
                    self.mainWin.mainTabWin.removeTab(2)
                    self.mainWin.mainTabWin.removeTab(1)
                    self.mainWin.mainTabWin.addTab(self.mainWin.mapWin, "Map Editor")
                    self.mainWin.mainTabWin.addTab(self.mainWin.tileWin, "Tile Editor")
                    self.mainWin.mainTabWin.addTab(self.mainWin.paletteWin, "Palette Editor")
                    self.mainWin.mainTabWin.addTab(self.mainWin.gnatWin, "☕")
                    
                    self.updateStatusLabel(f"Project: {self.projectData.getProjectName()}")
                    self.enableEditors()
                    self.enableSave()
                    
                    self.mainWin.undoStack.clear()
                    self.mainWin.undoHistoryLabel.updateText()
                    self.mainWin.undoFutureLabel.updateText()
                    
                self.loadProjectInfo()
                self.projectInfo.setDisabled(False)
                self.enableReload()
            
            except Exception as e:
                common.showErrorMsg(title="Error loading project", text="An error occurred while loading the project.", info=str(e))
                self.updateStatusLabel("Error loading project.")
                logging.warning(f"Error loading project: {traceback.format_exc()}")
            
        else: # returns error data if failed
            self.disableSave()
            self.disableReload()
            self.disableEditors()
            self.projectInfo.setDisabled(True)
            common.showErrorMsg(title=data["title"], text=data["text"], info=data["info"])
            self.updateStatusLabel("Error loading project.")
            
        
        self.enableOpen()
        self.loadingProgress.setMaximum(1)
        self.loadingProgress.setMinimum(0)
        self.loadingProgress.setValue(-1)
    
    def saveProject(self):
        self.isSaving = True
        logging.info(f"Saving project to {self.projectData.dir}")
        self.disableOpen()
        self.disableSave()
        self.disableReload()
        self.disableEditors()
        self.projectInfo.setDisabled(True)

        self.updateStatusLabel("Saving project...")
        
        self.loadingProgress.setMaximum(0)
        self.loadingProgress.setMinimum(0) 
        self.loadingProgress.setValue(0)

        self.workerThread = QThread()
        
        self.worker = Worker(save.writeDirectory, self.projectData)
        self.worker.updates.connect(self.updateStatusLabel)
        self.worker.returns.connect(self.finishedProjectSave)
        
        self.worker.moveToThread(self.workerThread)
        self.workerThread.started.connect(self.worker.run)

        self.workerThread.start()

    def finishedProjectSave(self, result):
        self.workerThread.quit()
        self.isSaving = False

        if isinstance(result, bool) and result == True:
            self.updateStatusLabel("Project saved.")
            self.mainWin.mapWin.scene.undoStack.setClean()
            self.mainWin.tileWin.undoStack.setClean()
            self.mainWin.paletteWin.undoStack.setClean()

        else:
            common.showErrorMsg(title=result["title"], text=result["text"], info=result["info"])
            self.updateStatusLabel("Error saving project.")

        
        # put the name back after a second
        QTimer.singleShot(1000, lambda: self.updateStatusLabel(f"Project: {self.projectData.getProjectName()}"))

        self.enableOpen()
        self.enableSave()
        self.enableReload()
        self.enableEditors()
        self.projectInfo.setDisabled(False)

        self.loadProjectInfo()

        self.loadingProgress.setMaximum(1)
        self.loadingProgress.setMinimum(0)
        self.loadingProgress.setValue(-1)

    def populateRecents(self):
        """Read recents from settings and populate the list"""
        self.recents = []
        settings = QSettings()
        for i in range(common.MAXRECENTS).__reversed__():
            path = settings.value(f"main/recents/{i}Path", type=str)
            name = settings.value(f"main/recents/{i}Name", type=str)
            if path:
                self.recentsList.insertItem(0, f"{name} - {path}")
                self.recents.insert(0, {"name": name, "path": path})

    def addRecent(self, name: str, path: str):
        """Add a recent project to the list and settings"""

        for i in self.recents: # if we're already in recents
            if i["path"] == path: 
                self.recentsList.takeItem(self.recents.index(i))
                self.recents.remove(i) # remove and put back at the start
                self.recents.insert(0, {"name": name, "path": path})
                self.recentsList.insertItem(0, f"{name} - {path}")
                break
            
        else: # if we're not in recents
            self.recents.insert(0, {"name": name, "path": path})
            self.recentsList.insertItem(0, f"{name} - {path}")
            if len(self.recents) > common.MAXRECENTS:
                self.recents.pop(-1)
                self.recentsList.takeItem(10)

        # either way, take this opportunity to save the recents to settings
        self.saveRecents()

    def saveRecents(self):
        settings = QSettings()
        # Clear all recorded recents
        for i in range(0, common.MAXRECENTS):
            settings.remove(f"main/recents/{i}Path")
            settings.remove(f"main/recents/{i}Name")
        # Populate it again with our list
        for i, recent in enumerate(self.recents):
            settings.setValue(f"main/recents/{i}Path", recent["path"])
            settings.setValue(f"main/recents/{i}Name", recent["name"])

    def openFromRecents(self, path):
        if self.openAction.isEnabled():
            self.openDirectory(path)

    def onRecentsContextMenu(self, point: QPoint):
        if self.recentsList.itemAt(point) is not None:
            globalPoint = self.recentsList.mapToGlobal(point)
            contextMenu = QMenu()
            contextMenu.addAction(icons.ICON_LOAD, "&Open in file browser", self.openSelectedRecentPath)
            contextMenu.addAction(icons.ICON_COPY, "&Copy path", self.copySelectedRecentPath)
            contextMenu.addAction(icons.ICON_DELETE, "&Remove from recents list", self.deleteSelectedRecent)
            contextMenu.exec(globalPoint)
    
    def deleteSelectedRecent(self):
        index = self.recentsList.currentIndex().row()
        self.recentsList.takeItem(index)
        self.recents.pop(index)
        self.saveRecents()
    
    def copySelectedRecentPath(self):
        index = self.recentsList.currentIndex().row()
        QApplication.clipboard().setText(self.recents[index]["path"])
    
    def openSelectedRecentPath(self):
        index = self.recentsList.currentIndex().row()
        QDesktopServices.openUrl("file://" + self.recents[index]["path"])

    def loadProjectInfo(self):
        self.projectTitleInput.setText(self.projectData.getProjectName())
        self.projectAuthorInput.setText(self.projectData.getProjectAuthor())
        self.projectDescInput.setPlainText(self.projectData.getProjectDescription())
        self.projectVersionLabel.setText(f"CoilSnake version: {common.getCoilsnakeVersion(self.projectData.getProjectVersion())}")
        
        # rebuild the list of available features
        # start by clearing the layout
        while self.projectFeaturesLayout.count():
            widget = self.projectFeaturesLayout.itemAt(0).widget()
            if widget:
                self.projectFeaturesLayout.removeWidget(widget)
                widget.deleteLater()
        # then add new things
        r = c = 0
        for i in common.COILSNAKEFEATUREIDS:
            available = self.projectData.isFeatureAvailable(i)
            icon = icons.ICON_OK if available else icons.ICON_NO
            label = IconLabel(common.COILSNAKEFEATURES[i]["name"], icon)
            tooltip = common.COILSNAKEFEATURES[i]["desc"]
            if available:
                tooltip += "\nThis feature is available with this CoilSnake version."
            else:
                tooltip += "\nThis feature is not available with this CoilSnake version."
                label.setEnabled(False)
            label.setToolTip(tooltip)
            self.projectFeaturesLayout.addWidget(label, r, c)
            c += 1
            if c == 3:
                c = 0
                r += 1
        
        # paths have a tendency to be REALLY long,
        # so we can sprinkle zwsps thoughout to trick
        # qt into wrapping the text (there's no support for per-char wrap here)
        path = self.projectData.dir
        fixedPath = "\u200b".join(path[i:i+1] for i in range(0, len(path)))
        self.projectPathLabel.setText(f"Path: {fixedPath}")

        # since we call this when changing project names too, update the recents list
        self.addRecent(self.projectData.getProjectName(), path)

        self.window().setWindowTitle(f"EBME - {self.projectData.getProjectName()} - {self.projectData.dir}")
        
    # TODO make this undo-able
    def changeProjectInfo(self):
        if hasattr(self, "projectData"):
            self.projectData.projectSnake['Title'] = self.projectTitleInput.text()
            self.projectData.projectSnake['Author'] = self.projectAuthorInput.text()
            # the other fields have an "editing finished" signal, but this one only has "text changed"
            self.projectDescInput.blockSignals(True) # so we don't want to trigger this function again
            self.projectData.projectSnake['Description'] = self.projectDescInput.toPlainText()
            self.projectDescInput.blockSignals(False)
            
            
    def checkForUpdates(self):
        try:
            response = requests.get(f"https://api.github.com/repos/{common.OWNER}/{common.REPOSITORY}/releases/latest")
            response.raise_for_status()
        except requests.HTTPError as e:
            self.versionStatus.setText(f"Error {e.errno} fetching update info.")
            raise
        except Exception as e:
            self.versionStatus.setText("Error fetching update info.")
            raise
        latest = response.json()["tag_name"]
        if latest != common.VERSION:
            self.versionStatus.setText(f"Update available! {common.VERSION} --> {latest}. <a href='https://github.com/{common.OWNER}/{common.REPOSITORY}/releases/latest'>Download it here.</a>")
        else:
            self.versionStatus.setText("You are up to date!")

    def setupUI(self):
        self.menuFile = QMenu("&File")
        self.openAction = QAction(icons.ICON_LOAD, "&Open", shortcut=QKeySequence("Ctrl+O"))
        self.openAction.triggered.connect(self.openDirectory)
        self.saveAction = QAction(icons.ICON_SAVE, "&Save", shortcut=QKeySequence("Ctrl+S"))
        self.saveAction.triggered.connect(self.saveProject)
        self.reloadAction = QAction(icons.ICON_RELOAD, "&Reload", shortcut=QKeySequence("Ctrl+R"))
        self.reloadAction.triggered.connect(lambda: self.openDirectory(self.projectData.dir))
        self.menuFile.addActions([self.openAction, self.saveAction, self.reloadAction])
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.mainWin.sharedActionSettings)

        self.menuHelp = QMenu("&Help")
        self.menuHelp.addAction(self.mainWin.sharedActionAbout)
        if not debug.SYSTEM_OUTPUT:
            self.menuHelp.addAction(self.mainWin.sharedActionDebug)
        self.menuHelp.addAction(self.mainWin.sharedActionReport)

        self.menuItems = (self.menuFile, self.menuHelp)

        self.titleLabel = QLabel(pixmap=QPixmap(":/logos/logo.png"))
        self.statusLabel = QLabel("No project loaded yet")

        self.openProjectButton = QPushButton("Open")
        self.openProjectButton.clicked.connect(self.openDirectory)
        self.saveProjectButton = QPushButton("Save")
        self.saveProjectButton.clicked.connect(self.saveProject)
        self.reloadProjectButton = QPushButton("Reload")
        self.reloadProjectButton.clicked.connect(lambda: self.openDirectory(self.projectData.dir))

        self.loadingProgress = QProgressBar(textVisible=False)
        self.loadingProgress.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.versionLabel = QLabel(common.VERSION)

        self.recentsBox = QGroupBox("Recent Projects")
        self.recentsList = QListWidget(self)
        self.recentsLayout = QVBoxLayout()
        self.recentsLayout.addWidget(self.recentsList)
        self.recentsBox.setLayout(self.recentsLayout)
        self.populateRecents()
        self.recentsList.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.recentsList.customContextMenuRequested.connect(self.onRecentsContextMenu)
        self.recentsList.itemDoubleClicked.connect(lambda: self.openFromRecents(self.recents[self.recentsList.currentIndex().row()]["path"]))

        self.projectInfo = QGroupBox("Project Info")
        self.projectTitleLabel = QLabel("Title")
        self.projectTitleInput = QLineEdit("(Load a project first)")
        self.projectTitleInput.editingFinished.connect(self.changeProjectInfo)
        self.projectAuthorLabel = QLabel("Author")
        self.projectAuthorInput = QLineEdit("(Load a project first)")
        self.projectAuthorInput.editingFinished.connect(self.changeProjectInfo)
        self.projectDescLabel = QLabel("Description")
        self.projectDescInput = QPlainTextEdit("(Load a project first)")
        self.projectDescInput.textChanged.connect(self.changeProjectInfo) # no editing finished here, see changeProjectInfo
        self.projectVersionLabel = QLabel("CoilSnake version: (Load a project first)")
        self.projectPathLabel = QLabel("Path: (Load a project first)")
        self.projectPathLabel.setWordWrap(True)
        self.projectFeaturesLayout = QGridLayout()
        self.projectFeaturesLayout.addWidget(QLabel("(Load a project first)"), 0, 0)
        
        self.projectInfoLayout = QFormLayout()
        self.projectInfoLayout.addRow(self.projectTitleLabel, self.projectTitleInput)
        self.projectInfoLayout.addRow(self.projectAuthorLabel, self.projectAuthorInput)
        self.projectInfoLayout.addRow(self.projectDescLabel, self.projectDescInput)
        self.projectInfoLayout.addWidget(self.projectVersionLabel)
        self.projectInfoLayout.addWidget(self.projectPathLabel)
        self.projectInfoLayout.addRow("Features", self.projectFeaturesLayout)

        self.projectInfo.setLayout(self.projectInfoLayout)
        self.projectInfo.setDisabled(True)

        self.ebmeInfo = QGroupBox("EBME Changelog")
        self.ebmeInfoLayout = QVBoxLayout()
        
        self.versionStatusLayout = QHBoxLayout()
        self.versionStatus = QLabel(f"You're on version {common.VERSION}.")
        self.versionStatus.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.versionStatus.setOpenExternalLinks(True)
        self.checkForUpdatesButton = QPushButton("Check for update")
        self.checkForUpdatesButton.clicked.connect(self.checkForUpdates)
        self.checkForUpdatesButton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.versionStatusLayout.addWidget(self.checkForUpdatesButton)
        self.versionStatusLayout.addWidget(self.versionStatus)
        self.ebmeInfoLayout.addLayout(self.versionStatusLayout)

        self.ebmeChangelog = QPlainTextEdit()
        self.ebmeChangelog.setPlainText(common.CHANGELOG)
        self.ebmeChangelog.setReadOnly(True)
        self.ebmeInfoLayout.addWidget(self.ebmeChangelog)
        self.ebmeInfo.setLayout(self.ebmeInfoLayout)

        self.contentLayout = QHBoxLayout(self)

        self.contentLeftHalf = QVBoxLayout()
        self.contentLeftHalf.addWidget(self.titleLabel)
        self.contentLeftHalf.addWidget(self.versionLabel)
        self.contentLeftHalf.addWidget(self.statusLabel)

        self.openSaveReloadLayout = QHBoxLayout()
        self.openSaveReloadLayout.addWidget(self.openProjectButton)
        self.openSaveReloadLayout.addWidget(self.saveProjectButton)
        self.openSaveReloadLayout.addWidget(self.reloadProjectButton)

        self.contentLeftHalf.addLayout(self.openSaveReloadLayout)
        self.contentLeftHalf.addWidget(self.loadingProgress)
        self.contentLeftHalf.addWidget(self.recentsBox)

        self.contentRightHalf = QVBoxLayout()
        self.contentRightHalf.addWidget(self.projectInfo)
        self.contentRightHalf.addWidget(self.ebmeInfo)

        self.contentLayout.addLayout(self.contentLeftHalf, 3)
        self.contentLayout.addLayout(self.contentRightHalf, 5)