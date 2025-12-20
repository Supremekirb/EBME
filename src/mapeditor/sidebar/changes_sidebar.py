from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QFormLayout, QGroupBox, QHBoxLayout,
                               QHeaderView, QMessageBox, QPlainTextEdit,
                               QSizePolicy, QToolButton, QVBoxLayout, QWidget)

import src.misc.common as common
from src.actions.changes_actions import (ActionAddMapChangeEvent,
                                         ActionChangeMapChangeEvent,
                                         ActionMoveMapChangeEvent,
                                         ActionMoveTileChange,
                                         ActionRemoveMapChangeEvent,
                                         ActionRemoveTileChange)
from src.coilsnake.project_data import ProjectData
from src.misc import icons as icons
from src.misc.dialogues import TileChangeEditDialog
from src.objects.changes import (MapChangeEvent, MapChangeEventListItem,
                                 MapChangesTree, TileChange,
                                 TileChangeListItem)
from src.widgets.input import FlagInput
from src.widgets.misc import IconLabel

if TYPE_CHECKING:
    from src.mapeditor.map_editor import MapEditor, MapEditorState
    
class SidebarChanges(QWidget):
    def __init__(self, parent, state: "MapEditorState", mapeditor: "MapEditor", projectData: ProjectData):
        super().__init__(parent)
        
        self.state = state
        self.mapeditor = mapeditor
        self.projectData = projectData
        
        self.setupUI()
    
    def refreshEvent(self, event: MapChangeEvent|None = None):
        # Attempt to refresh current if None is passed
        if event is None:
            currentItem = self.eventsTree.currentItem()
            if isinstance(currentItem, MapChangeEventListItem):
                event = currentItem.event
            elif isinstance(currentItem, TileChangeListItem):
                event = currentItem.parent().event
            else:
                return
    
        lastItem = self.eventsTree.currentItem()
        lastTileChange = None
        
        if isinstance(lastItem, TileChangeListItem):
            lastTileChange = lastItem.change
            lastItem = lastItem.parent()
        
        for i in range(self.eventsTree.topLevelItemCount()):
            item: MapChangeEventListItem = self.eventsTree.topLevelItem(i)
            if item.event == event:
                item.updateFlagText()
                item.rebuildChildren()
                
                # Now figure out if we need to re-select it (or a child)
                if lastItem is not None and item.event == lastItem.event:
                    self.fromEvent(item) # Loads data into the other UI elements
                    # If a tile change was previously selected, reselect it.
                    if lastTileChange is not None:
                        for i in range(item.childCount()):
                            if (child := item.child(i)).change == lastTileChange: # Big fan of this line tbh
                                self.eventsTree.setCurrentItem(child)
                                break
    
    def selectFromTileID(self, tile: int):
        # This is a bit complicated:
        # Provided a tile ID, we need to work backwards to find what to pick.
        # However, several events can actually provide changes!
        # We're not provided with a TileChange object, so we are a bit limited in our effectiveness.
        # First: Try to find an entry where the "before" tile matches
        # (it's more likely to have many different "befores" leading into the same "afters" than visa-versa, so "before" is better)
        # Then we can improve our approximation a little bit extra:
        # If anything is being previewed, see if it's part of that preview. If so, select it.
        # The only weakness here is several events being previewed and having the same "befores" - the first one found will be selected.
        # If nothing is being previewed, then just choose the first one out of all of them.
        # BUG is what I'll mark it as for now, but it's not a big deal.
        
        for i in range(self.eventsTree.topLevelItemCount()):
            item: MapChangeEventListItem = self.eventsTree.topLevelItem(i)
            if len(self.mapeditor.scene.enabledMapEvents) == 0 or item.event in self.mapeditor.scene.enabledMapEvents:
                for j in range(item.childCount()):
                    tileChange: TileChangeListItem = item.child(j)
                    if tileChange.change.before == tile:
                        self.eventsTree.setCurrentItem(tileChange)
                        self.eventsTree.scrollToItem(tileChange)
                        return
        # Fail silently if not found; this is called from any tile pick and may not correspond to a valid option
        
    def selectTileChange(self, event: MapChangeEvent, change: TileChange):           
        # Search until we find it
        for i in range(self.eventsTree.topLevelItemCount()):
            item: MapChangeEventListItem = self.eventsTree.topLevelItem(i)
            if item.event == event:
                for j in range(item.childCount()):
                    child: TileChangeListItem = item.child(j)
                    if child.change == change:
                        self.eventsTree.setCurrentItem(child)
                        self.eventsTree.scrollToItem(child)
                        break
                break
        # Otherwise it was likely removed as a part of an undo/redo, so we can ignore it.

        
    def selectEvent(self, event: MapChangeEvent):
        currentItem = self.eventsTree.currentItem()
        if isinstance(currentItem, TileChangeListItem):
            currentItem = currentItem.parent()
            
        # If it's the same as the selection, just refresh it
        if currentItem and currentItem.event == event:
            self.refreshEvent()
            
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
        # Otherwise it was likely removed as a part of an undo/redo, so we can ignore it.
        
    def fromTileset(self, tilesetID: int):
        # Attempt to preserve the selected item.
        lastItem = self.eventsTree.currentItem()
        # it's necessary to do this now as the item will be deleted internally
        # when the list is cleared.
        if lastItem is not None:
            if isinstance(lastItem, MapChangeEventListItem):
                lastThing = (lastItem.event,)
            elif isinstance(lastItem, TileChangeListItem):
                lastThing = (lastItem.parent().event, lastItem.change) # eh
            else:
                lastThing = None
        else:
            lastThing = None
        
        if lastThing is not None and lastThing[0].tileset != tilesetID:
            lastThing = None # Prevents re-selection as we do not want it
        
        self.tilesetSelect.setCurrentIndex(tilesetID)
        self.mapeditor.scene.enabledMapEvents.clear()
        self.eventsTree.clear()
        items = []
        for i in self.projectData.mapChanges[tilesetID].events:
            items.append(MapChangeEventListItem(i))
            
        self.eventsTree.addTopLevelItems(items)
        
        # Re-select the old selected item if applicable
        if lastThing is not None:
            if len(lastThing) == 1: # just the event
                self.selectEvent(*lastThing)
            else: # both event and tile change
                self.selectTileChange(*lastThing)
        else:
            self.fromEvent(None) # Fixes a small issue that occurs when going from TileChangeListItem -> None. No clue why, but it doesn't get called right.

        self.mapeditor.scene.update()
        
    def fromEvent(self, item: MapChangeEventListItem|TileChangeListItem|None):
        self.eventFlag.blockSignals(True)
        self.eventComment.blockSignals(True)
        
        if isinstance(item, MapChangeEventListItem):
            self.addTileChangeButton.setDisabled(False)
            self.removeEventButton.setDisabled(False)
            self.moveEventUpButton.setDisabled(False)
            self.moveEventDownButton.setDisabled(False)
            
        if isinstance(item, TileChangeListItem):
            item = item.parent()
            self.addTileChangeButton.setDisabled(False) # Extra needed in case we go from None to this
            self.removeTileChangeButton.setDisabled(False)
            self.moveTileChangeUpButton.setDisabled(False)
            self.moveTileChangeDownButton.setDisabled(False)
        else:
            self.removeTileChangeButton.setDisabled(True)
            self.moveTileChangeUpButton.setDisabled(True)
            self.moveTileChangeDownButton.setDisabled(True)

        if item is None:
            # disable things
            self.eventGroupBox.setDisabled(True)
            self.eventComment.setPlaceholderText("Select an event.")
            self.eventComment.setPlainText("")
            self.removeEventButton.setDisabled(True)
            self.moveEventUpButton.setDisabled(True)
            self.moveEventDownButton.setDisabled(True)
            self.addTileChangeButton.setDisabled(True) 
            self.removeTileChangeButton.setDisabled(True)
            self.moveTileChangeUpButton.setDisabled(True)
            self.moveTileChangeDownButton.setDisabled(True)
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
            action = TileChangeEditDialog.configureTileChange(self, self.projectData, item.parent().event.tileset, item.change, item.parent().event)
            if action is not None:
                self.mapeditor.scene.undoStack.push(action)
            
    def onAddEvent(self):
        currentSelected = self.eventsTree.currentItem()
        if isinstance(currentSelected, TileChangeListItem):
            index = self.eventsTree.indexOfTopLevelItem(currentSelected.parent())+1
        elif isinstance(currentSelected, MapChangeEventListItem):
            index = self.eventsTree.indexOfTopLevelItem(currentSelected)+1
        else:
            index = self.eventsTree.topLevelItemCount()

        event = MapChangeEvent(self.tilesetSelect.currentIndex())
        action = ActionAddMapChangeEvent(event, self.projectData.mapChanges[event.tileset], index)
        self.mapeditor.scene.undoStack.push(action)
    
    def onRemoveEvent(self):
        currentSelected = self.eventsTree.currentItem()
        if isinstance(currentSelected, TileChangeListItem):
            currentSelected = currentSelected.parent()
        if currentSelected is None:
            return common.showErrorMsg("Cannot remove map change event.",
                                       "You must first select a map change event.", icon=QMessageBox.Icon.Warning)

        action = ActionRemoveMapChangeEvent(currentSelected.event, self.projectData.mapChanges[currentSelected.event.tileset])
        self.mapeditor.scene.undoStack.push(action)
    
    def onMoveEventUp(self):
        currentSelected = self.eventsTree.currentItem()
        if isinstance(currentSelected, TileChangeListItem):
            event = currentSelected.parent().event
            currentSelected = currentSelected.parent()
        elif isinstance(currentSelected, MapChangeEventListItem):
            event = currentSelected.event
        else:
            return common.showErrorMsg("Cannot move map change event.", 
                                "You must first select a map change event.", icon=QMessageBox.Icon.Warning)
            
        index = self.eventsTree.indexOfTopLevelItem(currentSelected)

        if index == 0: return

        action = ActionMoveMapChangeEvent(event, self.projectData.mapChanges[event.tileset], index-1)
        self.mapeditor.scene.undoStack.push(action)
    
    def onMoveEventDown(self):
        currentSelected = self.eventsTree.currentItem()
        if isinstance(currentSelected, TileChangeListItem):
            event = currentSelected.parent().event
            currentSelected = currentSelected.parent()
        elif isinstance(currentSelected, MapChangeEventListItem):
            event = currentSelected.event
        else:
            return common.showErrorMsg("Cannot move map change event.", 
                                "You must first select a map change event.", icon=QMessageBox.Icon.Warning)

        index = self.eventsTree.indexOfTopLevelItem(currentSelected)

        if index == self.eventsTree.topLevelItemCount()-1: return

        action = ActionMoveMapChangeEvent(event, self.projectData.mapChanges[event.tileset], index+2)
        self.mapeditor.scene.undoStack.push(action)
    
    def onAddTileChange(self):
        currentSelected = self.eventsTree.currentItem()
        if isinstance(currentSelected, TileChangeListItem):
            event = currentSelected.parent().event
            index = event.changes.index(currentSelected.change)+1
        elif isinstance(currentSelected, MapChangeEventListItem):
            event = currentSelected.event
            index = len(currentSelected.event.changes)
        else:
            index = None

        if index is None:
            return common.showErrorMsg("Cannot add tile change.", 
                                "You must first select a tile change or a map change event.", icon=QMessageBox.Icon.Warning)

        action = TileChangeEditDialog.newTileChange(self, self.projectData, event.tileset, event, index)
        if action is not None:
            self.mapeditor.scene.undoStack.push(action)
    
    def onRemoveTileChange(self):
        currentSelected = self.eventsTree.currentItem()
        if isinstance(currentSelected, TileChangeListItem):
            event = currentSelected.parent().event
            change = currentSelected.change
        else:
            return common.showErrorMsg("Cannot remove tile change.", 
                                "You must first select a tile change.", icon=QMessageBox.Icon.Warning)

        action = ActionRemoveTileChange(event, change)
        self.mapeditor.scene.undoStack.push(action)
    
    def onMoveTileChangeUp(self):
        currentSelected = self.eventsTree.currentItem()
        if isinstance(currentSelected, TileChangeListItem):
            event = currentSelected.parent().event
            change = currentSelected.change
            index = currentSelected.parent().indexOfChild(currentSelected)
        else:
            return common.showErrorMsg("Cannot move tile change.", 
                                "You must first select a tile change.", icon=QMessageBox.Icon.Warning)
        
        if index == 0: return

        action = ActionMoveTileChange(event, change, index-1)
        self.mapeditor.scene.undoStack.push(action)
    
    def onMoveTileChangeDown(self):
        currentSelected = self.eventsTree.currentItem()
        if isinstance(currentSelected, TileChangeListItem):
            event = currentSelected.parent().event
            change = currentSelected.change
            index = currentSelected.parent().indexOfChild(currentSelected)
        else:
            return common.showErrorMsg("Cannot move tile change.", 
                                "You must first select a tile change.", icon=QMessageBox.Icon.Warning)
        
        if index == currentSelected.parent().childCount()-1: return

        action = ActionMoveTileChange(event, change, index+2)
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
        
        
        addEventButtonsLayout = QHBoxLayout()
        
        self.addEventButton = QToolButton()
        self.addEventButton.setIcon(icons.ICON_NEW)
        self.addEventButton.setToolTip("Add new event")
        self.addEventButton.clicked.connect(self.onAddEvent)
        
        self.removeEventButton = QToolButton()
        self.removeEventButton.setIcon(icons.ICON_DELETE)
        self.removeEventButton.setToolTip("Remove selected event")
        self.removeEventButton.setDisabled(True)
        self.removeEventButton.clicked.connect(self.onRemoveEvent)
        
        self.moveEventUpButton = QToolButton()
        self.moveEventUpButton.setIcon(icons.ICON_UP)
        self.moveEventUpButton.setToolTip("Move selected event up")
        self.moveEventUpButton.setDisabled(True)
        self.moveEventUpButton.clicked.connect(self.onMoveEventUp)
        
        self.moveEventDownButton = QToolButton()
        self.moveEventDownButton.setIcon(icons.ICON_DOWN)
        self.moveEventDownButton.setToolTip("Move selected event down")
        self.moveEventDownButton.setDisabled(True)
        self.moveEventDownButton.clicked.connect(self.onMoveEventDown)
        
        addEventButtonsLayout.addWidget(self.addEventButton)
        addEventButtonsLayout.addWidget(self.removeEventButton)
        addEventButtonsLayout.addWidget(self.moveEventUpButton)
        addEventButtonsLayout.addWidget(self.moveEventDownButton)
        
        
        addTileChangeButtonsLayout = QHBoxLayout()
        self.addTileChangeButton = QToolButton()
        self.addTileChangeButton.setIcon(icons.ICON_NEW)
        self.addTileChangeButton.setToolTip("Add new tile change")
        self.addTileChangeButton.setDisabled(True)
        self.addTileChangeButton.clicked.connect(self.onAddTileChange)
        
        self.removeTileChangeButton = QToolButton()
        self.removeTileChangeButton.setIcon(icons.ICON_DELETE)
        self.removeTileChangeButton.setToolTip("Remove selected tile change")
        self.removeTileChangeButton.setDisabled(True)
        self.removeTileChangeButton.clicked.connect(self.onRemoveTileChange)
        
        self.moveTileChangeUpButton = QToolButton()
        self.moveTileChangeUpButton.setIcon(icons.ICON_UP)
        self.moveTileChangeUpButton.setToolTip("Move selected tile change up")
        self.moveTileChangeUpButton.setDisabled(True)
        self.moveTileChangeUpButton.clicked.connect(self.onMoveTileChangeUp)
        
        self.moveTileChangeDownButton = QToolButton()
        self.moveTileChangeDownButton.setIcon(icons.ICON_DOWN)
        self.moveTileChangeDownButton.setToolTip("Move selected tile change down")
        self.moveTileChangeDownButton.setDisabled(True)
        self.moveTileChangeDownButton.clicked.connect(self.onMoveTileChangeDown)
        
        addTileChangeButtonsLayout.addWidget(self.addTileChangeButton)
        addTileChangeButtonsLayout.addWidget(self.removeTileChangeButton)
        addTileChangeButtonsLayout.addWidget(self.moveTileChangeUpButton)
        addTileChangeButtonsLayout.addWidget(self.moveTileChangeDownButton)

        
        self.eventGroupBox = QGroupBox("Event Data")
        eventGroupBoxLayout = QFormLayout()
        self.eventGroupBox.setLayout(eventGroupBoxLayout)
        self.eventGroupBox.setDisabled(True)
        
        self.eventFlag = FlagInput()
        self.eventFlag.valueChanged.connect(self.toEvent)
        self.eventFlag.inverted.connect(self.toEvent)
        self.eventFlag.valueChanged.connect(lambda: self.refreshEvent()) # Otherwise it passes an int and that messes with some things
        self.eventFlag.inverted.connect(self.refreshEvent)
        self.eventFlag.spinbox.setToolTip("When the flag is set, the tile changes associated with this event will be applied.")
        
        self.eventComment = QPlainTextEdit()
        self.eventComment.setPlaceholderText("Select an event.")
        self.eventComment.textChanged.connect(self.toEvent)
        self.eventComment.setSizePolicy(self.eventComment.sizePolicy().horizontalPolicy(), QSizePolicy.Policy.Minimum)
        
        eventsLayout.addRow("Tileset", self.tilesetSelect)
        eventsLayout.addRow(self.eventsTree)
        
        eventsLayout.addRow(IconLabel("Event", icons.ICON_FLAG), addEventButtonsLayout)
        eventsLayout.addRow(IconLabel("Tile change", icons.ICON_TILE_CHANGE), addTileChangeButtonsLayout)
        
        eventGroupBoxLayout.addRow("Flag", self.eventFlag)
        eventGroupBoxLayout.addRow("Comment", self.eventComment)
        eventsLayout.addRow(self.eventGroupBox)
        
        eventsGroupbox.setLayout(eventsLayout)
        
        contentLayout.addWidget(eventsGroupbox)
        
        self.setLayout(contentLayout)
        
        self.tilesetSelect.addItems(str(i.id) for i in self.projectData.tilesets)
        self.tilesetSelect.setCurrentIndex(0)