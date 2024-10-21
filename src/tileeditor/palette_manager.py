from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QApplication, QDialog, QFormLayout, QGroupBox,
                               QHBoxLayout, QStyle, QToolButton, QTreeWidget,
                               QTreeWidgetItem, QVBoxLayout, QWidget)

from src.coilsnake.project_data import ProjectData
from src.misc.widgets import ColourButton


class PaletteManagerDialog(QDialog):
    def __init__(self, projectData: ProjectData, parent: QWidget|None = None):
        super().__init__(parent)
        self.projectData = projectData
        
        self.setWindowTitle("Palette Manager")
        
        self.subpalette1Buttons: list[ColourButton] = []
        self.subpalette2Buttons: list[ColourButton] = []
        self.subpaletteTransferButtons: list[QToolButton] = [] # only for iterating, order is NOT reliable
        
        self.setupUI()
        
    def transferColourUp(self, index: int):
        ...
        
    def transferColourDown(self, index: int):
        ...
        
    def transferAllColoursUp(self):
        ...
        
    def transferAllColoursDown(self):
        ...
        
    def on1CurrentChanged(self, new: QTreeWidgetItem):        
        if isinstance(new, SubpaletteListItem):
            subpalette = self.projectData.getTileset(
                new.parent().parent().parent().tileset).getPalette(new.parent().parent().paletteGroup,
                                                                   new.parent().palette
                    ).subpalettes[new.subpalette]
                
            for i in range(0, 16):
                button = self.subpalette1Buttons[i]
                button.blockSignals(True)
                button.setColour(QColor.fromRgb(*subpalette.subpaletteRGBA[i]))
                button.blockSignals(False)
                button.setEnabled(True)
            
            if isinstance(self.selection2.currentItem(), SubpaletteListItem):
                for i in self.subpaletteTransferButtons:
                    i.setEnabled(True)
        
        else:
            for i in self.subpalette1Buttons:
                i.setDisabled(True)
            for i in self.subpaletteTransferButtons:
                i.setDisabled(True)
            
    def on2CurrentChanged(self, new: QTreeWidgetItem):
        if isinstance(new, SubpaletteListItem):
            subpalette = self.projectData.getTileset(
                new.parent().parent().parent().tileset).getPalette(new.parent().parent().paletteGroup,
                                                                   new.parent().palette
                    ).subpalettes[new.subpalette]
                
            for i in range(0, 16):
                button = self.subpalette2Buttons[i]
                button.blockSignals(True)
                button.setColour(QColor.fromRgb(*subpalette.subpaletteRGBA[i]))
                button.blockSignals(False)
                button.setEnabled(True)
            
            if isinstance(self.selection1.currentItem(), SubpaletteListItem):
                for i in self.subpaletteTransferButtons:
                    i.setEnabled(True)
        
        else:
            for i in self.subpalette2Buttons:
                i.setDisabled(True)
            for i in self.subpaletteTransferButtons:
                i.setDisabled(True)
        
    def setupUI(self):
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        self.selection1 = PaletteTreeWidget(self.projectData, self)
        self.selection1.currentItemChanged.connect(self.on1CurrentChanged)
        self.selection2 = PaletteTreeWidget(self.projectData, self)
        self.selection2.currentItemChanged.connect(self.on2CurrentChanged)
        self.selection2.setHeaderHidden(False)
        self.selection2.setHeaderLabel("Compare against...")
        
        editGroupBox = QGroupBox("Compare subpalettes")
        editGroupBoxLayout = QHBoxLayout() 
        editGroupBox.setLayout(editGroupBoxLayout)
        
        editRowsLayout = QVBoxLayout()
        editRowsLayout.addStretch()
        editTopRowLayout = QHBoxLayout()
        editRowsLayout.addLayout(editTopRowLayout)
        editMiddleRowLayout = QHBoxLayout()
        editRowsLayout.addLayout(editMiddleRowLayout)
        editBottomRowLayout = QHBoxLayout()
        editRowsLayout.addLayout(editBottomRowLayout)
        editRowsLayout.addStretch()
        
        editOtherButtonsLayout = QHBoxLayout()
        
        editGroupBoxLayout.addLayout(editRowsLayout)
        editGroupBoxLayout.addLayout(editOtherButtonsLayout)
        editGroupBoxLayout.addWidget(self.selection2)
        
        iconProvider = QApplication.style().standardIcon
        for i in range(0, 16):
            button = ColourButton()
            button.setFixedSize(24, 24)
            self.subpalette1Buttons.append(button)
            editTopRowLayout.addWidget(button)
            
            tempCopyButtonsLayout = QVBoxLayout()
            button = QToolButton()
            button.setIcon(iconProvider(QStyle.StandardPixmap.SP_ArrowUp))
            button.setToolTip("Copy from bottom to top")
            button.clicked.connect(lambda: self.transferColourUp(i))
            button.setDisabled(True)
            self.subpaletteTransferButtons.append(button)
            tempCopyButtonsLayout.addWidget(button)
            
            button = QToolButton()
            button.setIcon(iconProvider(QStyle.StandardPixmap.SP_ArrowDown))
            button.setToolTip("Copy from top to bottom")
            button.clicked.connect(lambda: self.transferColourDown(i))
            button.setDisabled(True)
            self.subpaletteTransferButtons.append(button)
            tempCopyButtonsLayout.addWidget(button)
            
            editMiddleRowLayout.addLayout(tempCopyButtonsLayout)
            
            button = ColourButton()
            button.setFixedSize(24, 24)
            self.subpalette2Buttons.append(button)
            editBottomRowLayout.addWidget(button)
        
        button = QToolButton()
        button.setIcon(iconProvider(QStyle.StandardPixmap.SP_ArrowUp))
        button.setToolTip("Copy all from bottom to top")
        button.clicked.connect(self.transferAllColoursUp)
        button.setDisabled(True)
        self.subpaletteTransferButtons.append(button)
        editOtherButtonsLayout.addWidget(button)
        
        button = QToolButton()
        button.setIcon(iconProvider(QStyle.StandardPixmap.SP_ArrowDown))
        button.setToolTip("Copy all from top to bottom")
        button.setDisabled(True)
        button.clicked.connect(self.transferAllColoursDown)
        self.subpaletteTransferButtons.append(button)
        editOtherButtonsLayout.addWidget(button)
            
        layout.addWidget(self.selection1)
        layout.addWidget(editGroupBox)
    

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

class TilesetListItem(QTreeWidgetItem):
    def __init__(self, tileset: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tileset = tileset

class PaletteGroupListItem(QTreeWidgetItem):
    def __init__(self, palettegroup: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.paletteGroup = palettegroup
    
    def parent(self) -> TilesetListItem:
        return super().parent()

class PaletteListItem(QTreeWidgetItem):
    def __init__(self, palette: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.palette = palette
    
    def parent(self) -> PaletteGroupListItem:
        return super().parent()

class SubpaletteListItem(QTreeWidgetItem):
    def __init__(self, subpalette: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subpalette = subpalette
    
    def parent(self) -> PaletteListItem:
        return super().parent()