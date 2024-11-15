import logging

from PySide6.QtCore import QFile, Qt
from PySide6.QtGui import QAction, QUndoCommand
from PySide6.QtWidgets import (QComboBox, QCompleter, QDialog, QFileDialog,
                               QFormLayout, QGroupBox, QHBoxLayout,
                               QHeaderView, QPushButton, QSizePolicy,
                               QTreeWidget, QVBoxLayout)

from src.actions.music_actions import (ActionAddMapMusicTrack,
                                       ActionChangeMapMusicTrack,
                                       ActionDeleteMapMusicTrack,
                                       ActionMoveMapMusicTrack)
from src.coilsnake.project_data import ProjectData
from src.objects.music import (MapMusicEntryListItem, MapMusicHierarchy,
                               MapMusicHierarchyListItem)
from src.widgets.input import FlagInput
from src.widgets.misc import SignalUndoStack


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
    def __init__(self, parent, undoStack: SignalUndoStack, projectData: ProjectData):
        super().__init__(parent)
        self.projectData = projectData
        self.substitutions = {}
        self.undoStack = undoStack
        self.undoStack.redone.connect(self.onAction)
        self.undoStack.undone.connect(self.onAction)
        self.undoStack.pushed.connect(self.onAction)
        
        self.undoAction = QAction("Undo")
        self.undoAction.setShortcut("Ctrl+Z")
        self.undoAction.triggered.connect(self.undoStack.undo)

        self.redoAction = QAction("Redo")
        self.redoAction.setShortcuts(["Ctrl+Y", "Ctrl+Shift+Z"])
        self.redoAction.triggered.connect(self.undoStack.redo)
        
        self.addActions([self.undoAction, self.redoAction])
        
        self.setWindowTitle("Map Music Editor")        
        
        self.setupUI()
        
        self.applyDefaultSubstitutions()
        if MapMusicEditor.LAST_EBMUSED != None:
            self.substitutions = self.substitutions | parseMetadata(MapMusicEditor.LAST_EBMUSED)
        self.applySubstitutions() 
        
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
        
        for c in commands:
            if isinstance(c, ActionChangeMapMusicTrack):
                for i in self.projectData.mapMusic:
                    if c.entry in i.entries:
                        self.refreshHierachy(i)
                        break
                self.fromCurrentItem()
            if isinstance(c, ActionMoveMapMusicTrack):
                self.refreshHierachy(c.hierachy)
            if isinstance(c, ActionAddMapMusicTrack):
                self.refreshHierachy(c.hierachy)
            if isinstance(c, ActionDeleteMapMusicTrack):
                self.refreshHierachy(c.hierachy)
    
    def shiftUp(self):
        selected = self.tree.currentItem()
        if not isinstance(selected, MapMusicEntryListItem):
            return
        
        parent = selected.parent()
        index = parent.indexOfChild(selected)
        if index == 0:
            return
        
        self.undoStack.push(ActionMoveMapMusicTrack(parent.hierachy, selected.entry, index-1))
        
    def shiftDown(self):
        selected = self.tree.currentItem()
        if not isinstance(selected, MapMusicEntryListItem):
            return
        
        parent = selected.parent()
        index = parent.indexOfChild(selected)
        if index == parent.childCount()-1:
            return
        
        self.undoStack.push(ActionMoveMapMusicTrack(parent.hierachy, selected.entry, index+2))
        
    def addTrack(self):
        selected = self.tree.currentItem()
        if not isinstance(selected, MapMusicEntryListItem):
            return
        
        parent = selected.parent()
        index = parent.indexOfChild(selected)
        action = ActionAddMapMusicTrack(parent.hierachy, index+1)        
        self.undoStack.push(action)    
        
    def removeTrack(self):
        selected = self.tree.currentItem()
        if not isinstance(selected, MapMusicEntryListItem):
            return
        
        parent = selected.parent()
        if parent.childCount() == 1:
            return
        
        self.undoStack.push(ActionDeleteMapMusicTrack(parent.hierachy, selected.entry))
        
    def refreshHierachy(self, hierachy: MapMusicHierarchy):
        lastSelected = self.tree.currentItem()
        lastEntry = None
        if isinstance(lastSelected, MapMusicEntryListItem):
            lastEntry = lastSelected.entry
        
        for i in range(self.tree.topLevelItemCount()):
            item: MapMusicHierarchyListItem = self.tree.topLevelItem(i)
            if item.hierachy == hierachy:
                for j in reversed(range(item.childCount())):
                    item.removeChild(item.child(j))
                    
                for entry in hierachy.entries:
                    new = MapMusicEntryListItem(entry)
                    item.addChild(new)
                    if lastEntry == entry:
                        self.tree.setCurrentItem(new)
                break
                        
        self.applySubstitutions()
        
    def fromCurrentItem(self):
        currentItem = self.tree.currentItem()
        
        self.musicTrack.blockSignals(True)
        self.musicFlag.blockSignals(True)
        
        if isinstance(currentItem, MapMusicEntryListItem):
            self.musicTrack.setCurrentIndex(currentItem.entry.music-1)
            self.musicFlag.setValue(currentItem.entry.flag)
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
        
        action = ActionChangeMapMusicTrack(currentItem.entry, self.musicTrack.currentIndex()+1,
                                           self.musicFlag.value())
        
        self.undoStack.push(action)
        
        currentItem.setText(0, self.musicTrack.itemText(self.musicTrack.currentIndex()))
        currentItem.updateFlagText()                       
                
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
            
    def applyDefaultSubstitutions(self):
        file = QFile(":/misc/songs.txt")
        file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text)
        file = file.readAll().data().decode().split("\n")
        for i in range(0, len(file)):
            name = file[i].strip()
            self.substitutions[i+1] = name
        self.applySubstitutions()
        
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
                        if j.entry.music in self.substitutions:
                            j.setText(0, strings[j.entry.music-1])
                            
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
            
    @staticmethod
    def openMapMusicEditor(parent, undoStack: SignalUndoStack, projectData: ProjectData, goto: int|None = None):
        dialog = MapMusicEditor(parent, undoStack, projectData)
        
        if goto != None:
            for i in range(0, dialog.tree.topLevelItemCount()):
                i = dialog.tree.topLevelItem(i)
                if i.hierachy.id == goto:
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
            item = MapMusicHierarchyListItem(i)
            entries = []
            for j in i.entries:
                entry = MapMusicEntryListItem(j)
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
        
        closeLayout = QHBoxLayout()
        self.closeButton = QPushButton("Close")
        self.closeButton.clicked.connect(self.close)
        self.closeButton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        closeLayout.addWidget(self.closeButton)
        
        contentLayout.addWidget(self.editorBox)
        
        layout.addWidget(self.importButton)
        layout.addWidget(self.clearButton)
        layout.addLayout(contentLayout)
        layout.addLayout(closeLayout)
        self.setLayout(layout)
    