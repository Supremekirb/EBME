from typing import TYPE_CHECKING

from PySide6.QtCore import (QAbstractItemModel, QModelIndex, QObject,
                            QPersistentModelIndex, QPoint)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QSpinBox, QStyleOptionViewItem, QWidget

import src.misc.common as common
from src.actions.fts_actions import ActionChangeCollision
from src.misc.dialogues import PresetEditorDialog
from src.widgets.collision import (CollisionPresetList, PresetItem,
                                   PresetItemDelegate)
from src.widgets.tile import TileCollisionWidget

if TYPE_CHECKING:
    from tile_editor import TileEditorState
    
class TileEditorCollisionWidget(TileCollisionWidget):
    def __init__(self, state: "TileEditorState"):
        super().__init__()
        self.state = state
        
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
        
class TileEditorPresetItemDelegate(PresetItemDelegate):
    def __init__(self, presetList: "TileEditorCollisionPresetList", parent: QObject = None):
        self.presetList = presetList
        super().__init__(parent)
        
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex):
        preset: PresetItem = self.presetList.list.item(index.row())
        if not index.isValid():
            return
        
        if preset.unknown:
            result = PresetEditorDialog.editPreset(self.presetList.list,
                                                   preset.text(), QColor(preset.colour), preset.value)
            if result:
                preset.setText(result[0])
                preset.colour = result[1].rgb()
                preset.value = result[2]
                preset.unknown = False
                preset.generateIcon()
                self.presetList.verifyTileCollision(self.presetList.state.tileEditor.collisionScene.currentTile)
                self.presetList.state.tileEditor.collisionScene.update()
            
            return               
        
        spinbox = QSpinBox(parent)
        spinbox.setDisplayIntegerBase(16)
        spinbox.setPrefix("0x")
        spinbox.setMaximum(common.BYTELIMIT)
        spinbox.setMinimum(0)
        spinbox.setValue(preset.value)  
              
        return spinbox
    
    def setModelData(self, editor: QSpinBox, model: QAbstractItemModel, index: QModelIndex | QPersistentModelIndex):
        super().setModelData()
    
class TileEditorCollisionPresetList(CollisionPresetList):
    def __init__(self, state: "TileEditorState"):
        super().__init__()
        self.state = state
        self.list.currentItemChanged.connect(self.onCurrentItemChanged)
        
    def onCurrentItemChanged(self):
        item: PresetItem = self.list.currentItem()
        if item:
            self.state.currentCollision = item.value
        self.state.tileEditor.collisionScene.update()
    
    def onAddClicked(self):
        super().onAddClicked()
        self.state.tileEditor.collisionScene.update()
        
    def onEditClicked(self):
        super().onEditClicked()
        self.state.tileEditor.collisionScene.update()
        
    def onDeleteClicked(self):
        super().onDeleteClicked()
        self.state.tileEditor.collisionScene.update()
        
    def onResetPresetsClicked(self):
        super().onResetPresetsClicked()
        self.state.tileEditor.collisionScene.update()
            