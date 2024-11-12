import logging

from PySide6.QtCore import QFile, Qt
from PySide6.QtGui import QAction, QUndoStack
from PySide6.QtWidgets import (QComboBox, QCompleter, QDialog, QFileDialog,
                               QFormLayout, QGroupBox, QHBoxLayout,
                               QHeaderView, QMessageBox, QPushButton,
                               QSizePolicy, QTreeWidget, QVBoxLayout)

import src.misc.icons as icons
from src.actions.music_actions import (ActionAddMapMusicTrack,
                                       ActionChangeMapMusicTrack,
                                       ActionDeleteMapMusicTrack,
                                       ActionMoveMapMusicTrack)
from src.coilsnake.project_data import ProjectData
from src.objects.music import (MapMusicEntry, MapMusicEntryListItem,
                               MapMusicHierarchy, MapMusicHierarchyListItem)
from src.widgets.input import FlagInput


def parseMetadata(path: str) -> dict:
    """Given a path to an .ebmused file, parse the metadata and return a list of substitutions.

    Args:
        path (str): Path to an .ebmused file

    Returns:
        dict: Track names for IDs. Format: {ID: NAME}
    """
    
    substitutions = {}
    with open(path, encoding="utf-8", errors='replace') as metadata:
        for i in metadata.readlines():
            try:
                # format is "T [ID] [NAME]"
                if not i.startswith("T"):
                    continue
                id = int(i.split(" ")[1], 16)
                name = (" ".join(i.split(" ")[2:])).strip()
                substitutions[id] = name
            except Exception:
                logging.warning(f"Invalid metadata line: {i}")
    return substitutions  


class MapMusicEditor(QDialog):
    LAST_EBMUSED = None
    def __init__(self, parent, projectData: ProjectData):
        super().__init__(parent)
        self.projectData = projectData
        self.substitutions = {}
        self.undoStack = QUndoStack(self)
        self.undoStack.cleanChanged.connect(self.onCleanChanged)
        
        self.undoAction = QAction("Undo")
        self.undoAction.setShortcut("Ctrl+Z")
        self.undoAction.triggered.connect(self.onUndo)
        
        self.redoAction = QAction("Redo")
        self.redoAction.setShortcuts(["Ctrl+Y", "Ctrl+Shift+Z"])
        self.redoAction.triggered.connect(self.onRedo)
        
        self.addActions([self.undoAction, self.redoAction])
        
        self.setWindowTitle("Map Music Editor")        
        
        self.setupUI()
        
        self.applyDefaultSubstitutions()
        if MapMusicEditor.LAST_EBMUSED != None:
            self.substitutions = self.substitutions | parseMetadata(MapMusicEditor.LAST_EBMUSED)
        self.applySubstitutions() 
        
    def onUndo(self):
        self.undoStack.undo()
        self.applySubstitutions()
        
    def onRedo(self):
        self.undoStack.redo()
        self.applySubstitutions()
        
    def onCleanChanged(self):
        if self.undoStack.isClean():
            self.setWindowTitle("Map Music Editor")
        else: self.setWindowTitle("Map Music Editor*")
        
    def shiftUp(self):
        selected = self.tree.currentItem()
        if not isinstance(selected, MapMusicEntryListItem):
            return
        
        parent = selected.parent()
        index = parent.indexOfChild(selected)
        if index == 0:
            return
        
        self.undoStack.push(ActionMoveMapMusicTrack(self.tree, parent, selected, index-1))
        
    
    def shiftDown(self):
        selected = self.tree.currentItem()
        if not isinstance(selected, MapMusicEntryListItem):
            return
        
        parent = selected.parent()
        index = parent.indexOfChild(selected)
        if index == parent.childCount()-1:
            return
        
        self.undoStack.push(ActionMoveMapMusicTrack(self.tree, parent, selected, index+1))
        
    def addTrack(self):
        selected = self.tree.currentItem()
        if not isinstance(selected, MapMusicEntryListItem):
            return
        
        parent = selected.parent()
        index = parent.indexOfChild(selected)
        action = ActionAddMapMusicTrack(self.tree, parent, index)
        action.track.setText(0, f"1 {self.substitutions[1]}")
        
        self.undoStack.push(action)    
        
    def removeTrack(self):
        selected = self.tree.currentItem()
        if not isinstance(selected, MapMusicEntryListItem):
            return
        
        parent = selected.parent()
        if parent.childCount() == 1:
            return
        
        self.undoStack.push(ActionDeleteMapMusicTrack(self.tree, parent, selected))
        
    def fromCurrentItem(self):
        currentItem = self.tree.currentItem()
        
        self.musicTrack.blockSignals(True)
        self.musicFlag.blockSignals(True)
        
        if isinstance(currentItem, MapMusicEntryListItem):
            self.musicTrack.setCurrentIndex(currentItem.music-1)
            self.musicFlag.setValue(currentItem.flag)
            self.editorBox.setDisabled(False)
            self.editorBox.setTitle("Track Details")
        else:
            self.musicTrack.setCurrentIndex(-1)
            self.musicFlag.setValue(0)
            self.editorBox.setDisabled(True)
            self.editorBox.setTitle("No Track Selected")
        
        self.musicTrack.blockSignals(False)
        self.musicFlag.blockSignals(False) 
        
    def toCurrentItem(self):
        currentItem = self.tree.currentItem()
        
        if not isinstance(currentItem, MapMusicEntryListItem):
            return
        
        action = ActionChangeMapMusicTrack(currentItem, self.musicTrack.currentIndex()+1,
                                           self.musicFlag.value())
        
        self.undoStack.push(action)
        
        currentItem.setText(0, self.musicTrack.itemText(self.musicTrack.currentIndex()))
        currentItem.setText(1, str(self.musicFlag.value()) if self.musicFlag.value() < 0x8000 else f"{self.musicFlag.value()-0x8000} (Inverted)")
        
    def toMapMusic(self):
        for i in range(0, self.tree.topLevelItemCount()):
            entries = []
            i = self.tree.topLevelItem(i)
            if isinstance(i, MapMusicHierarchyListItem):
                for j in range(0, i.childCount()):
                    j = i.child(j)
                    if isinstance(j, MapMusicEntryListItem):
                        entries.append(MapMusicEntry(j.flag, j.music))
                
                item = MapMusicHierarchy(i.id)
                item.entries = entries
                self.projectData.mapMusic[i.id-1] = item
                        
                
    def importMetadata(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import EBMusEd metadata",
                                           self.projectData.dir, "*.ebmused")
        if path != "":
            self.substitutions = self.substitutions | parseMetadata(path)
            MapMusicEditor.LAST_EBMUSED = path
            self.applySubstitutions()
            
    def clearMetadata(self):
        MapMusicEditor.LAST_EBMUSED = None
        self.substitutions = {}
        self.applyDefaultSubstitutions()
        self.applySubstitutions()
            
    def applyDefaultSubstitutions(self):
        file = QFile(":/misc/songs.txt")
        file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text)
        file = file.readAll().data().decode().split("\n")
        for i in range(0, len(file)):
            name = file[i].strip()
            self.substitutions[i+1] = name
        
    def applySubstitutions(self):
        self.musicTrack.blockSignals(True)
        self.musicFlag.blockSignals(True)
        self.tree.blockSignals(True)
        
        strings = list(f"{i} {j}" for i, j in self.substitutions.items())
        
        for i in range(0, self.tree.topLevelItemCount()):
                i = self.tree.topLevelItem(i)
                for j in range(0, i.childCount()):
                    j = i.child(j)
                    if isinstance(j, MapMusicEntryListItem):
                        if j.music in self.substitutions:
                            j.setText(0, strings[j.music-1])
                            
        self.musicCompleter = QCompleter(strings)
        self.musicCompleter.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.musicCompleter.setFilterMode(Qt.MatchFlag.MatchContains)
        self.musicTrack.setCompleter(self.musicCompleter)
        self.musicTrack.clear()
        self.musicTrack.addItems(strings)
        
        self.fromCurrentItem()
        
        self.musicTrack.blockSignals(False)
        self.musicFlag.blockSignals(False)
        self.tree.blockSignals(False)

    def onSaveClose(self):
        self.toMapMusic()
        self.undoStack.setClean()
        self.close()
        
    def onClose(self):
        if not self.undoStack.isClean():
            msg = QMessageBox()
            msg.setText("Save your changes before returning to the map editor?")
            msg.setStandardButtons(QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
            msg.setDefaultButton(QMessageBox.StandardButton.Save)
            result = msg.exec()
            
            if result == QMessageBox.StandardButton.Save:
                self.toMapMusic()
                self.undoStack.setClean()
                self.close()
                
            if result == QMessageBox.StandardButton.Discard:
                self.close()
                
        else: self.close()
                
            
    @staticmethod
    def openMapMusicEditor(parent, projectData: ProjectData, goto: int|None = None):
        dialog = MapMusicEditor(parent, projectData)
        
        if goto != None:
            for i in range(0, dialog.tree.topLevelItemCount()):
                i = dialog.tree.topLevelItem(i)
                if i.id == goto:
                    i.setSelected(True)
                    i.setExpanded(True)
                    dialog.show()
                    dialog.tree.scrollToItem(i)
                    break
        
        dialog.exec_()
        
        
    def setupUI(self):
        layout = QVBoxLayout()
        contentLayout = QHBoxLayout()
        
        self.importButton = QPushButton("Import EBMusEd metadata...")
        self.importButton.clicked.connect(self.importMetadata)
        
        self.clearButton = QPushButton("Clear imported metadata")
        self.clearButton.clicked.connect(self.clearMetadata)
        
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Entry/track", "Flag"])
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.currentItemChanged.connect(self.fromCurrentItem)
        
        items = []
        for i in self.projectData.mapMusic:
            item = MapMusicHierarchyListItem(i.id)
            entries = []
            for j in i.entries:
                entry = MapMusicEntryListItem(j.flag, j.music)
                entries.append(entry)
            item.addChildren(entries)
                
            items.append(item)
            
        self.tree.addTopLevelItems(items)
        contentLayout.addWidget(self.tree)
        
        self.editorBox = QGroupBox("Track Details")
        editorLayout = QFormLayout()
        self.editorBox.setLayout(editorLayout)
        
        self.musicTrack = QComboBox()
        self.musicTrack.setEditable(True)
        self.musicTrack.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.musicTrack.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.musicTrack.currentIndexChanged.connect(self.toCurrentItem)
        editorLayout.addRow("Song", self.musicTrack)
        
        self.musicFlag = FlagInput(True)
        self.musicFlag.valueChanged.connect(self.toCurrentItem)
        self.musicFlag.inverted.connect(self.toCurrentItem)
        editorLayout.addRow("Flag", self.musicFlag)
        
        trackEditLayout = QHBoxLayout()
        self.musicUp = QPushButton("Move up")
        self.musicUp.clicked.connect(self.shiftUp)
        self.musicDown = QPushButton("Move down")
        self.musicDown.clicked.connect(self.shiftDown)
        self.musicAdd = QPushButton("Add track")
        self.musicAdd.clicked.connect(self.addTrack)
        self.musicRemove = QPushButton("Remove track")
        self.musicRemove.clicked.connect(self.removeTrack)
        trackEditLayout.addWidget(self.musicUp)
        trackEditLayout.addWidget(self.musicDown)
        trackEditLayout.addWidget(self.musicAdd)
        trackEditLayout.addWidget(self.musicRemove)
        editorLayout.addRow(trackEditLayout)
        
        saveCloseLayout = QHBoxLayout()
        self.saveButton = QPushButton("Save")
        self.saveButton.clicked.connect(self.onSaveClose)
        self.saveButton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.closeButton = QPushButton("Close")
        self.closeButton.clicked.connect(self.onClose)
        self.closeButton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        saveCloseLayout.addWidget(self.saveButton)
        saveCloseLayout.addWidget(self.closeButton)
        
        contentLayout.addWidget(self.editorBox)
        
        layout.addWidget(self.importButton)
        layout.addWidget(self.clearButton)
        layout.addLayout(contentLayout)
        layout.addLayout(saveCloseLayout)
        self.setLayout(layout)
    