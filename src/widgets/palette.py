from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QGridLayout, QLabel, QSizePolicy, QTreeWidget,
                               QTreeWidgetItem, QWidget)

import src.misc.icons as icons
from src.coilsnake.fts_interpreter import Palette
from src.coilsnake.project_data import ProjectData
from src.widgets.input import ColourButton


class PaletteSelector(QWidget):
    colourChanged = Signal(int)
    subpaletteChanged = Signal(int)
    colourEdited = Signal(int, int)
    
    def __init__(self):
        super().__init__()
        
        layout = QGridLayout()
        self.setLayout(layout)
        
        self.buttons: list[list[ColourButton]] = [[], [], [], [], [], []]
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.arrowIndicatorLabels: list[QLabel] = []
        self.subpaletteLabels: list[QLabel] = []
        self.viewOnly: bool = False
        
        for i in range(6):
            label = QLabel(str(i))
            label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            label.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(label, i, 1)
            
            indicator = QLabel("")
            indicator.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            if i == 0: 
                label.setText(f"<b>{i}</b>")
                indicator.setText("▶")
            layout.addWidget(indicator, i, 0)
            
            self.subpaletteLabels.append(label)
            self.arrowIndicatorLabels.append(indicator)
            
            for j in range(16):                
                button = ColourButton(self)
                button.setCheckable(True)
                button.clicked.disconnect()
                button.colourChanged.connect(self.onColourEdited)
                button.clicked.connect(self.onColourChanged)
                button.setAutoExclusive(True)
                button.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed))
                button.setFixedSize(24, 24)
                button.setToolTip("Double click to edit, right click to copy hex code")
                layout.addWidget(button, i, j+2)
                self.buttons[i].append(button)
            
        self.buttons[0][0].setChecked(True)
        self.currentSubpaletteIndex = 0
        self.currentColour = self.buttons[0][0].chosenColour
        self.currentColourIndex = 0
        
        self.currentPalette: Palette = None
        
        self.onColourChanged()
            
    def onColourChanged(self):
        for subpalette, list in enumerate(self.buttons):
            for index, button in enumerate(list):
                if button.isChecked():
                    self.currentColour = button.chosenColour
                    if subpalette != self.currentSubpaletteIndex:
                        self.currentSubpaletteIndex = subpalette
                        self.subpaletteChanged.emit(subpalette)
                        self.updateSubpaletteLabels()
                    if index != self.currentColourIndex:
                        self.currentColourIndex = index
                        self.colourChanged.emit(index)
                    return
                
    def onColourEdited(self):
        for subpalette in self.buttons:
            for button in subpalette:
                if button.isChecked():
                    self.colourEdited.emit(self.buttons.index(subpalette), subpalette.index(button))
                    return
        
    def setColourIndex(self, index: int):
        self.currentColourIndex = index
        self.buttons[self.currentSubpaletteIndex][index].setChecked(True)
        
    def setSubpaletteIndex(self, subpalette: int):
        self.currentSubpaletteIndex = subpalette
        self.buttons[subpalette][self.currentColourIndex].setChecked(True)
        self.updateSubpaletteLabels()
    
    def updateSubpaletteLabels(self):
        for id, label in enumerate(self.subpaletteLabels):
            if id == self.currentSubpaletteIndex and not self.viewOnly:
                label.setText(f"<b>{id}</b>")
                self.arrowIndicatorLabels[id].setText("▶")
            else:
                label.setText(str(id))
                self.arrowIndicatorLabels[id].setText("")
        
    def openEditor(self):
        # maybe new implementation later,
        # but right now just open the dialog of the selected button
        if not self.viewOnly:
            for subpaletteButtons in self.buttons:
                for button in subpaletteButtons:
                    if button.isChecked():
                        button.openColourDialog()
                        return
            
    def loadPalette(self, palette: Palette):
        for index, subpalette in enumerate(palette.subpalettes):
            for colour, button in enumerate(self.buttons[index]):
                button.blockSignals(True)
                button.setColour(QColor.fromRgb(*subpalette.subpaletteRGBA[colour]))
                button.blockSignals(False)
            
        self.currentPalette = palette 
        
        self.onColourChanged()
        
    def setViewOnly(self, viewOnly: bool):
        self.viewOnly = viewOnly
        self.updateSubpaletteLabels()
        
        for subpal in self.buttons:
            for button in subpal:
                button.setViewOnly(viewOnly)
            
        
class PaletteTreeWidget(QTreeWidget):
    def __init__(self, projectData: ProjectData, parent: QWidget|None=None):
        super().__init__(parent)
        
        self.projectData = projectData
        
        self.setColumnCount(1)
        self.setHeaderHidden(True)
        
        for tileset in self.projectData.tilesets:
            tilesetWidget = TilesetListItem(tileset.id, [f"Tileset {tileset.id}"])
            self.addTopLevelItem(tilesetWidget)
            for paletteGroup in tileset.paletteGroups:
                paletteGroupWidget = PaletteGroupListItem(paletteGroup.groupID, tilesetWidget, [f"Palette Group {paletteGroup.groupID}"])
                tilesetWidget.addChild(paletteGroupWidget)
                for palette in paletteGroup.palettes:
                    paletteWidget = PaletteListItem(palette.paletteID, paletteGroupWidget, [f"Palette {palette.paletteID}"])
                    paletteGroupWidget.addChild(paletteWidget)
                    for subpalette in range(0, 6):
                        subpaletteWidget = SubpaletteListItem(subpalette, paletteWidget, [f"Subpalette {subpalette}"])
                        paletteWidget.addChild(subpaletteWidget)
    
    def getCurrentSubpalette(self):
        current = self.currentItem()
        if isinstance(current, SubpaletteListItem):
            return current
        else: return None
    
    def getCurrentPalette(self):
        current = self.currentItem()
        if isinstance(current, SubpaletteListItem):
            return current.parent()
        elif isinstance(current, PaletteListItem):
            return current
        else: return None
    
    def getCurrentPaletteGroup(self):
        current = self.currentItem()
        if isinstance(current, SubpaletteListItem):
            return current.parent().parent()
        elif isinstance(current, PaletteListItem):
            return current.parent()
        elif isinstance(current, PaletteGroupListItem):
            return current
        else: return None
        
    def getCurrentTileset(self):
        current = self.currentItem()
        if isinstance(current, SubpaletteListItem):
            return current.parent().parent().parent()
        elif isinstance(current, PaletteListItem):
            return current.parent().parent()
        elif isinstance(current, PaletteGroupListItem):
            return current.parent()
        elif isinstance(current, TilesetListItem):
            return current
        else: return None

    def syncPaletteGroup(self, group: int):
        tileset = self.topLevelItem(self.projectData.getTilesetFromPaletteGroup(group).id)
        for i in range(tileset.childCount()):
            paletteGroup: PaletteGroupListItem = tileset.child(i)
            if paletteGroup.paletteGroup == group:
                for j in reversed(range(paletteGroup.childCount())):
                    paletteGroup.removeChild(paletteGroup.child(j))
                for j in self.projectData.getPaletteGroup(group).palettes:
                    palette = PaletteListItem(j.paletteID, paletteGroup, [f"Palette {j.paletteID}"])
                    paletteGroup.addChild(palette)
                    for k in range(0, 6):
                        subpalette = SubpaletteListItem(k, palette, [f"Subpalette {k}"])
                        palette.addChild(subpalette)

class TilesetListItem(QTreeWidgetItem):
    def __init__(self, tileset: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tileset = tileset
        
        self.setIcon(0, icons.ICON_TILESET)

class PaletteGroupListItem(QTreeWidgetItem):
    def __init__(self, palettegroup: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.paletteGroup = palettegroup
        
        self.setIcon(0, icons.ICON_PALETTE_GROUP)
    
    def parent(self) -> TilesetListItem:
        return super().parent()

class PaletteListItem(QTreeWidgetItem):
    def __init__(self, palette: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.palette = palette
        
        self.setIcon(0, icons.ICON_PALETTE)
    
    def parent(self) -> PaletteGroupListItem:
        return super().parent()

class SubpaletteListItem(QTreeWidgetItem):
    def __init__(self, subpalette: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subpalette = subpalette
        
        self.setIcon(0, icons.ICON_SUBPALETTE)

    def parent(self) -> PaletteListItem:
        return super().parent()
    