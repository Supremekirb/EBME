import json
import logging
import traceback
from typing import TYPE_CHECKING

from PySide6.QtCore import (QAbstractItemModel, QModelIndex, QObject,
                            QPersistentModelIndex, QPoint, QSettings, Qt)
from PySide6.QtGui import (QColor, QImage, QMouseEvent, QPainter, QPaintEvent,
                           QPixmap)
from PySide6.QtWidgets import (QHBoxLayout, QListWidget, QListWidgetItem,
                               QMessageBox, QSpinBox, QStyledItemDelegate,
                               QStyleOptionViewItem, QToolButton, QVBoxLayout,
                               QWidget)

import src.misc.common as common
import src.misc.icons as icons
from src.actions.fts_actions import ActionChangeCollision
from src.coilsnake.fts_interpreter import Tile
from src.misc.dialogues import PresetEditorDialog
from src.misc.widgets import TileGraphicsWidget

if TYPE_CHECKING:
    from tile_editor import TileEditorState
    
class TileCollisionWidget(TileGraphicsWidget):
    def __init__(self, state: "TileEditorState"):
        super().__init__()
        self.state = state
        
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if Qt.KeyboardModifier.ShiftModifier in event.modifiers() or Qt.KeyboardModifier.ControlModifier in event.modifiers():
                self.pickCollision(event.pos())
            else:
                self.placeCollision(event.pos())
        
    def placeCollision(self, pos: QPoint):
        index = self.indexAtPos(pos)
        if index == None:
            return

        action = ActionChangeCollision(self.currentTile, self.state.currentCollision, index)
        self.state.tileEditor.undoStack.push(action)
        
    def pickCollision(self, pos: QPoint):
        index = self.indexAtPos(pos)
        if index == None:
            return
        value = self.currentTile.getMinitileCollision(index)
        
        preset = self.state.tileEditor.presetList.getPreset(value)
        if preset:
            self.state.tileEditor.presetList.list.setCurrentItem(preset)
            
        
    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        
        if self.currentTile == None or self.currentPalette == None:
            return
        
        
        width = self.width()
        height = self.height()
        
        if width > height:
            width = height
        else:
            height = width
        
        painter = QPainter(self)
        
        scale = width / 32
        
        painter.scale(scale, scale)
        painter.setPen(Qt.PenStyle.NoPen)
        
        for i in range(16):
            collision = self.currentTile.getMinitileCollision(i)
            if collision == 0:
                colour = 0x000000
                painter.setOpacity(0)
            else:
                painter.setOpacity(0.7)
                try:
                    colour = self.state.tileEditor.presetList.getPreset(collision).colour
                except AttributeError:
                    colour = 0x000000
            
            painter.setBrush(QColor(colour))
            painter.drawRect((i % 4)*8, (i // 4)*8, 8, 8)   
    
class PresetItem(QListWidgetItem):
    def __init__(self, name: str, value: int, colour: int):
        super().__init__(name)
        
        self.value = value
        self.colour = colour
        self.unknown = False # unknown presets (when collision doesn't match) will be removed when the current tile is changed
        
        self.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable)
        self.generateIcon()
    
    def generateIcon(self):
        image = QImage(8, 8, QImage.Format.Format_RGB32)
        image.fill(QColor(self.colour))
        pixmap = QPixmap(image)
        self.setIcon(pixmap)
        
class PresetItemDelegate(QStyledItemDelegate):
    def __init__(self, presetList: "CollisionPresetList", parent: QObject = None):
        self.presetList = presetList
        super().__init__(parent)
        
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex):
        preset: PresetItem = self.presetList.list.item(index.row())
        if not index.isValid():
            return
        
        if preset.unknown:
            result = PresetEditorDialog.editPreset(self.presetList.state.tileEditor,
                                                   preset.text(), QColor(preset.colour), preset.value)
            if result:
                preset.setText(result[0])
                preset.colour = result[1].rgb()
                preset.value = result[2]
                preset.unknown = False
                preset.generateIcon()
                self.presetList.verifyTileCollision(self.presetList.state.tileEditor.collisionScene.currentTile)
                self.presetList.state.tileEditor.collisionScene.update()
                self.presetList.savePresets()
            
            return               
        
        spinbox = QSpinBox(parent)
        spinbox.setDisplayIntegerBase(16)
        spinbox.setPrefix("0x")
        spinbox.setMaximum(common.BYTELIMIT)
        spinbox.setMinimum(0)
        spinbox.setValue(preset.value)  
              
        return spinbox
    
    def setModelData(self, editor: QSpinBox, model: QAbstractItemModel, index: QModelIndex | QPersistentModelIndex):
        preset: PresetItem = self.presetList.list.item(index.row())
        
        if not index.isValid():
            return
        
        if preset.value != editor.value():
            preset.value = editor.value()
            self.presetList.verifyTileCollision(self.presetList.state.tileEditor.collisionScene.currentTile)
            self.presetList.state.tileEditor.collisionScene.update()
    
    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex):
        super().initStyleOption(option, index)
        preset: PresetItem = self.presetList.list.item(index.row())
        
        if self.presetList.list.currentItem() == preset:
            option.font.setBold(True)
    
class CollisionPresetList(QVBoxLayout):
    def __init__(self, state: "TileEditorState"):
        super().__init__()
        self.state = state
        
        self.list = QListWidget()
        self.list.setItemDelegate(PresetItemDelegate(self))
        self.loadPresets()
        self.list.currentItemChanged.connect(self.onCurrentItemChanged)
        self.addWidget(self.list)
        self.list.setMinimumWidth(self.list.sizeHint().width()) # it is a little too smol
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.onItemRightClicked)
        
        self.list.setEditTriggers(QListWidget.EditTrigger.DoubleClicked)
        
        buttonLayout = QHBoxLayout()
        
        # TODO better icons
        # QtAwesome?
        
        self.addButton = QToolButton()
        self.addButton.setIcon(icons.ICON_NEW)
        self.addButton.setToolTip("Add")
        self.addButton.clicked.connect(self.onAddClicked)
        self.editButton = QToolButton()
        self.editButton.setIcon(icons.ICON_EDIT)
        self.editButton.setToolTip("Edit")
        self.editButton.clicked.connect(self.onEditClicked)
        self.deleteButton = QToolButton()
        self.deleteButton.setIcon(icons.ICON_DELETE)
        self.deleteButton.setToolTip("Delete")
        self.deleteButton.clicked.connect(self.onDeleteClicked)
        self.moveUpButton = QToolButton()
        self.moveUpButton.setIcon(icons.ICON_UP)
        self.moveUpButton.setToolTip("Move up")
        self.moveUpButton.clicked.connect(self.onMoveUpClicked)
        self.moveDownButton = QToolButton()
        self.moveDownButton.setIcon(icons.ICON_DOWN)
        self.moveDownButton.setToolTip("Move down")
        self.moveDownButton.clicked.connect(self.onMoveDownClicked)
        self.resetPresetsButton = QToolButton()
        self.resetPresetsButton.setIcon(icons.ICON_UNDO)
        self.resetPresetsButton.setToolTip("Reset presets")
        self.resetPresetsButton.clicked.connect(self.onResetPresetsClicked)
        
        buttonLayout.addWidget(self.addButton)
        buttonLayout.addWidget(self.editButton)
        buttonLayout.addWidget(self.deleteButton)
        buttonLayout.addWidget(self.moveUpButton)
        buttonLayout.addWidget(self.moveDownButton)
        buttonLayout.addWidget(self.resetPresetsButton)
        self.addLayout(buttonLayout)
        
    def onCurrentItemChanged(self):
        item: PresetItem = self.list.currentItem()
        if item:
            self.state.currentCollision = item.value
    
    def onItemRightClicked(self, pos: QPoint):
        item = self.list.itemAt(pos)
        if not item:
            return
        
        self.list.setCurrentItem(item)
        self.onEditClicked()
    
    def onAddClicked(self):
        result = PresetEditorDialog.editPreset(self.state.tileEditor, "New preset", QColor(0), 0)
        
        if result:
            item = PresetItem(result[0], result[2], result[1].rgb())
            self.list.addItem(item)
            self.verifyTileCollision(self.state.tileEditor.collisionScene.currentTile)
            self.state.tileEditor.collisionScene.update()
            self.savePresets()
        
    def onEditClicked(self):
        item: PresetItem = self.list.currentItem()    
        result = PresetEditorDialog.editPreset(self.state.tileEditor,
                                               item.text(), QColor(item.colour), item.value)
        if result:
            item.setText(result[0])
            item.colour = result[1].rgb()
            item.value = result[2]
            item.unknown = False
            item.generateIcon()
            self.verifyTileCollision(self.state.tileEditor.collisionScene.currentTile)
            self.state.tileEditor.collisionScene.update()
            self.savePresets()
        
    def onDeleteClicked(self):
        item: PresetItem = self.list.currentItem()
        if item.unknown:
            return
        
        confirm = QMessageBox.question(self.state.tileEditor, "Delete preset",
                                       f"Delete preset \"{item.text()}\"? It cannot be recovered.",
                                       QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:  
            row = self.list.row(item)
            self.list.setCurrentItem(self.list.item(self.list.row(item) if row > 0 else 0))
            self.list.takeItem(row)
            self.verifyTileCollision(self.state.tileEditor.collisionScene.currentTile)
            self.state.tileEditor.collisionScene.update()
            self.savePresets()
        
    def onMoveUpClicked(self):
        item: PresetItem = self.list.currentItem()        
        row = self.list.row(item)
        self.list.takeItem(row)
        self.list.insertItem(row-1, item)
        self.savePresets()
        self.list.setCurrentItem(item)
        
    def onMoveDownClicked(self):
        item: PresetItem = self.list.currentItem()
        row = self.list.row(item)
        self.list.takeItem(row)
        self.list.insertItem(row+1, item)
        self.savePresets()
        self.list.setCurrentItem(item)
        
    def onResetPresetsClicked(self):
        confirm = QMessageBox.question(self.state.tileEditor, "Reset presets",
                                       "Reset to default collision presets? You'll lose any custom or modified presets.",
                                       QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            QSettings().remove("presets/presets")
            self.loadPresets()
            self.verifyTileCollision(self.state.tileEditor.collisionScene.currentTile)
            self.state.tileEditor.collisionScene.update()
            
        
    def loadPresets(self):
        self.list.blockSignals(True)
        self.list.clear()
        
        presets = QSettings().value("presets/presets", defaultValue=common.DEFAULTCOLLISIONPRESETS)
        try:
            if presets:
                for name, value, colour in json.loads(presets):
                    item = PresetItem(name, value, colour)
                    self.list.addItem(item)
        except Exception:
            logging.warning(f"Unable to load user-specified presets! Trying to load defaults... {traceback.format_exc()}")
            try:
                QSettings().remove("presets/presets")
                for name, value, colour in json.loads(common.DEFAULTCOLLISIONPRESETS):
                    item = PresetItem(name, value, colour)
                    self.list.addItem(item)
            except Exception:
                logging.warning("Unable to load default presets!")
                raise 
        
        self.list.blockSignals(False)
        self.list.setCurrentRow(0)
            
    def savePresets(self):
        presets: list[tuple[str, int, int]] = []
        for i in self.list.findItems("*", Qt.MatchFlag.MatchWildcard):
            i: PresetItem            
            if i.unknown:
                continue
            presets.append((i.text(), i.value, i.colour))
        
        if len(presets) > 0:
            QSettings().setValue("presets/presets", json.dumps(presets))
        else:
            QSettings().remove("presets/presets")
            
    def removeUnknowns(self):
        for i in self.list.findItems("*", Qt.MatchFlag.MatchWildcard): # janky way to iterate despite removals
            i: PresetItem
            if i.unknown:
                row = self.list.row(i)
                self.list.takeItem(row)
        
    def getPreset(self, value: int) -> PresetItem | None:
        for i in range(0, self.list.count()):
            item = self.list.item(i)
            if isinstance(item, PresetItem):
                if item.value == value:
                    return item

                
    def verifyTileCollision(self, tile: Tile):
        self.removeUnknowns()
        
        for i in range(16):
            if self.getPreset(tile.getMinitileCollision(i)) == None:
                value = tile.getMinitileCollision(i)
                item = PresetItem(f"Unknown 0x{hex(value)[2:].zfill(2).capitalize()}", value, 0x303030)
                item.unknown = True
                self.list.addItem(item)
                if not self.list.currentItem():
                    self.list.setCurrentItem(item)