from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QFormLayout, QGroupBox, QHeaderView,
                               QPlainTextEdit, QSizePolicy, QTreeWidget,
                               QTreeWidgetItem, QVBoxLayout, QWidget)

from src.actions.changes_actions import ActionChangeMapChangeEvent
from src.actions.fts_actions import ActionChangeCollision
from src.coilsnake.project_data import ProjectData
from src.misc.dialogues import TileChangeEditDialog
from src.objects.changes import (MapChangeEvent, MapChangeEventListItem,
                                 MapChangesTree, TileChangeListItem)
from src.widgets.collision import CollisionPresetList, PresetItem
from src.widgets.input import FlagInput
from src.widgets.tile import TileCollisionWidget

if TYPE_CHECKING:
    from src.mapeditor.map_editor import MapEditor, MapEditorState
    
class SidebarChanges(QWidget):
    def __init__(self, parent, state: "MapEditorState", mapeditor: "MapEditor", projectData: ProjectData):
        super().__init__(parent)
        
        self.state = state
        self.mapeditor = mapeditor
        self.projectData = projectData
        
        self.setupUI()
    
    def refreshCurrent(self):
        currentItem = self.eventsTree.currentItem()
        if isinstance(currentItem, TileChangeListItem):
            currentItem = currentItem.parent()

        # Re-select it and update its text
        if isinstance(currentItem, MapChangeEventListItem):
            currentItem.updateFlagText()
            currentItem.refreshChildren()
            self.fromEvent(currentItem)
        
    def selectEvent(self, event: MapChangeEvent):
        currentItem = self.eventsTree.currentItem()
        if isinstance(currentItem, TileChangeListItem):
            currentItem = currentItem.parent()
            
        # If it's the same as the selection, just refresh it
        if currentItem and currentItem.event == event:
            self.refreshCurrent()
            
        # Only rebuild the list if we need to.
        # Otherwise this will cause collapsed-items state to be reset.
        if self.tilesetSelect.currentIndex() != event.tileset:
            self.fromTileset(event.tileset)
        
        # Search until we find it
        # (triggers fromEvent always, as we do refreshCurrent in the case of it already being selected)
        for i in range(self.eventsTree.topLevelItemCount()):
            item: MapChangeEventListItem = self.eventsTree.topLevelItem(i)
            if item.event == event:
                self.eventsTree.setCurrentItem(item)
                self.eventsTree.scrollToItem(item)
                break
        else:
            raise ValueError(f"Event not found in its tileset ({event.tileset})")
        
    def fromTileset(self, tilesetID: int):
        self.tilesetSelect.setCurrentIndex(tilesetID)
        self.mapeditor.scene.enabledMapEvents.clear()
        self.eventsTree.clear()
        items = []
        for i in self.projectData.mapChanges[tilesetID].events:
            items.append(MapChangeEventListItem(i))
            
        self.eventsTree.addTopLevelItems(items)
        
        self.mapeditor.scene.update()
        
    def fromEvent(self, item: MapChangeEventListItem|TileChangeListItem):
        self.eventFlag.blockSignals(True)
        self.eventComment.blockSignals(True)
        
        if isinstance(item, TileChangeListItem):
            item = item.parent()

        if item is None:
            # disable things
            self.eventGroupBox.setDisabled(True)
            self.eventComment.setPlaceholderText("Select an event.")
            self.eventComment.setPlainText("")
        else:
            # re-enable things
            self.eventGroupBox.setDisabled(False)
            self.eventFlag.setValue(item.event.flag)
            self.eventComment.setPlaceholderText("")
            self.eventComment.setPlainText(item.event.comment)
        
        self.eventFlag.blockSignals(False)
        self.eventComment.blockSignals(False)
    
    def toEvent(self):
        item: MapChangeEventListItem|TileChangeListItem = self.eventsTree.currentItem()
        if item is None:
            return
        if isinstance(item, TileChangeListItem):
            item = item.parent()
        event = item.event
        action = ActionChangeMapChangeEvent(event, self.eventFlag.value(), event.changes, self.eventComment.toPlainText())
        self.mapeditor.scene.undoStack.push(action)
        self.mapeditor.scene.update()
    
    def onChangePreviewState(self, item: MapChangeEventListItem, state: Qt.CheckState):
        event = item.event
        match state:
            case Qt.CheckState.Checked:
                self.mapeditor.scene.enabledMapEvents.add(event)
            case Qt.CheckState.Unchecked:
                self.mapeditor.scene.enabledMapEvents.discard(event)
        self.mapeditor.scene.update()
    
    def onDoubleClick(self, item: MapChangeEventListItem|TileChangeListItem):
        if isinstance(item, TileChangeListItem):
            action = TileChangeEditDialog.configureTileChange(self, self.projectData, item.parent().event.tileset, item.change)
            if action is not None:
                self.mapeditor.scene.undoStack.push(action)
        
    def setupUI(self):
        contentLayout = QVBoxLayout()
        eventsLayout = QFormLayout()
        eventsGroupbox = QGroupBox("Map changes")
        
        self.tilesetSelect = QComboBox()
        self.tilesetSelect.setToolTip("Changes in this tileset. Tileset = fts in /Tilesets.")
        self.tilesetSelect.currentIndexChanged.connect(self.fromTileset)
        
        self.eventsTree = MapChangesTree()
        self.eventsTree.setColumnCount(2)
        self.eventsTree.setHeaderLabels(["Event", "Preview"])
        self.eventsTree.header().setStretchLastSection(False)
        self.eventsTree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.eventsTree.currentItemChanged.connect(self.fromEvent)
        self.eventsTree.previewStateChanged.connect(self.onChangePreviewState)
        self.eventsTree.itemDoubleClicked.connect(self.onDoubleClick)
        self.eventsTree.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        self.eventGroupBox = QGroupBox("Event Data")
        eventGroupBoxLayout = QFormLayout()
        self.eventGroupBox.setLayout(eventGroupBoxLayout)
        self.eventGroupBox.setDisabled(True)
        
        self.eventFlag = FlagInput()
        self.eventFlag.valueChanged.connect(self.toEvent)
        self.eventFlag.inverted.connect(self.toEvent)
        self.eventFlag.valueChanged.connect(self.refreshCurrent)
        self.eventFlag.inverted.connect(self.refreshCurrent)
        
        self.eventComment = QPlainTextEdit()
        self.eventComment.setPlaceholderText("Select an event.")
        self.eventComment.textChanged.connect(self.toEvent)
        self.eventComment.setSizePolicy(self.eventComment.sizePolicy().horizontalPolicy(), QSizePolicy.Policy.Minimum)
        
        eventsLayout.addRow("Tileset", self.tilesetSelect)
        eventsLayout.addRow(self.eventsTree)
        
        eventGroupBoxLayout.addRow("Flag", self.eventFlag)
        eventGroupBoxLayout.addRow("Comment", self.eventComment)
        eventsLayout.addRow(self.eventGroupBox)
        
        eventsGroupbox.setLayout(eventsLayout)
        
        contentLayout.addWidget(eventsGroupbox)
        
        self.setLayout(contentLayout)
        
        self.tilesetSelect.addItems(str(i.id) for i in self.projectData.tilesets)
        self.tilesetSelect.setCurrentIndex(0)