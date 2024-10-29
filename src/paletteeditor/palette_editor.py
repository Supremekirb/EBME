from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QColor, QKeySequence, QUndoStack
from PySide6.QtWidgets import (QFormLayout, QGroupBox, QHBoxLayout, QMenu,
                               QPushButton, QSpinBox, QToolButton, QTreeWidget,
                               QTreeWidgetItem, QVBoxLayout, QWidget)

import src.misc.common as common
import src.misc.debug as debug
import src.misc.icons as icons
from src.coilsnake.project_data import ProjectData
from src.misc.dialogues import (AboutDialog, CopyEventPaletteDialog, EditEventPaletteDialog,
                                SettingsDialog)
from src.misc.widgets import (ColourButton, FlagInput, IconLabel,
                              PaletteListItem, PaletteTreeWidget,
                              SubpaletteListItem)
from src.objects.palette_settings import PaletteSettings

if TYPE_CHECKING:
    from src.main.main import MainApplication


class PaletteEditor(QWidget):
    def __init__(self, projectData: ProjectData, parent: QWidget|None = None):
        super().__init__(parent)
        self.projectData = projectData
        
        self.subpalette1Buttons: list[ColourButton] = []
        self.subpalette2Buttons: list[ColourButton] = []
        self.subpaletteTransferButtons: list[QToolButton] = [] # only for iterating, order is NOT reliable
        
        self.undoStack = QUndoStack()
        self.undoStack.cleanChanged.connect(self.parent().updateTitle)
        
        self.setupUI()
        self.selection1.setCurrentItem(self.selection1.topLevelItem(0), 0)
        
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
            self.selection2.setEnabled(True)
            
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
                for i in self.subpalette2Buttons:
                    i.setEnabled(True)
                    
            self.loadPaletteSettingsTree(new.parent().parent().paletteGroup,
                                     new.parent().palette)
            
        else:
            for i, j in zip(self.subpalette1Buttons, self.subpalette2Buttons):
                i.setDisabled(True)
                j.setDisabled(True)
            for i in self.subpaletteTransferButtons:
                i.setDisabled(True)
            self.selection2.setDisabled(True)
        
            if isinstance(new, PaletteListItem):
                self.loadPaletteSettingsTree(new.parent().paletteGroup,
                                        new.palette)
            
            else:
                self.paletteSettingsGroupBox.setDisabled(True)
    
    def loadPaletteSettingsTree(self, paletteGroup: int, palette: int):
        self.paletteSettingsGroupBox.setEnabled(True)
        
        settings = self.projectData.paletteSettings[paletteGroup][palette]
        
        if settings != self.paletteSettingsTree.lastSettings:
            self.paletteSettingsTree.blockSignals(True)
            self.paletteSettingsTree.populateSettings(settings)
            self.paletteSettingsTree.blockSignals(False)
            
            self.paletteSettingsTree.setCurrentItem(self.paletteSettingsTree.topLevelItem(0))
    
    def onPaletteSettingsTreeCurrentChanged(self, new: "PaletteSettingsTreeItem"):
        settings = new.settings
        
        if self.paletteSettingsTree.topLevelItem(0) == new:
            self.paletteSettingsColoursWarning.show()
            self.paletteSettingsColoursEdit.hide()
            self.paletteSettingsColoursCopy.hide()
        else:
            self.paletteSettingsColoursWarning.hide()
            self.paletteSettingsColoursEdit.show()
            self.paletteSettingsColoursCopy.show()
            
        if settings.child:
            self.paletteSettingsAddChild.setDisabled(True)
            self.paletteSettingsRemoveChild.setEnabled(True)
        else:
            self.paletteSettingsAddChild.setEnabled(True)
            self.paletteSettingsRemoveChild.setDisabled(True)
        
        self.paletteSettingsFlag.setValue(settings.flag)
        self.paletteSettingsFlashEffect.setValue(settings.flashEffect)
        self.paletteSettingsSpritePalette.setValue(settings.spritePalette)
        
        if settings.child:
            if settings.flag == 0:
                self.paletteSettingsChildWarning.setIcon(icons.ICON_WARNING)
                self.paletteSettingsChildWarning.setText("Elsewise palette even when flag is 0")
            else:
                self.paletteSettingsChildWarning.setIcon(icons.ICON_OK)
                self.paletteSettingsChildWarning.setText("Valid configuration")
        else:
            if settings.flag != 0:
                self.paletteSettingsChildWarning.setIcon(icons.ICON_WARNING)
                self.paletteSettingsChildWarning.setText("No elsewise palette when flag is not 0")
            else:
                self.paletteSettingsChildWarning.setIcon(icons.ICON_OK)
                self.paletteSettingsChildWarning.setText("Valid configuration")
                
    def onEditEventPalette(self):
        palette = self.paletteSettingsTree.currentItem().settings.palette
        if palette:
            actions = EditEventPaletteDialog.editEventPalette(self, palette)
            if actions:
                self.undoStack.push(actions)
    
    def onCopyEventPalette(self):
        palette = self.paletteSettingsTree.currentItem().settings.palette
        if palette:
            CopyEventPaletteDialog.copyEventPalette(self, palette, self.projectData)
             
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
        self.selection1.setMaximumWidth(self.selection1.sizeHint().width())
        self.selection1.currentItemChanged.connect(self.on1CurrentChanged)
        
        editorsLayout = QVBoxLayout()
        
        compareGroupBox = QGroupBox("Compare Subpalettes")
        compareGroupBoxLayout = QHBoxLayout() 
        compareGroupBox.setLayout(compareGroupBoxLayout)
        
        self.selection2 = PaletteTreeWidget(self.projectData, self)
        self.selection2.setMaximumWidth(self.selection2.sizeHint().width())
        self.selection2.currentItemChanged.connect(self.on2CurrentChanged)
        self.selection2.setHeaderHidden(False)
        self.selection2.setHeaderLabel("Compare against...")
        
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
        
        compareGroupBoxLayout.addLayout(editRowsLayout)
        compareGroupBoxLayout.addLayout(editOtherButtonsLayout)
        compareGroupBoxLayout.addWidget(self.selection2)
        
        for i in range(0, 16):
            button = ColourButton()
            button.setFixedSize(24, 24)
            self.subpalette1Buttons.append(button)
            editTopRowLayout.addWidget(button)
            
            tempCopyButtonsLayout = QVBoxLayout()
            button = QToolButton()
            button.setIcon(icons.ICON_UP)
            button.setToolTip("Copy from bottom to top")
            button.clicked.connect(lambda: self.transferColourUp(i))
            button.setDisabled(True)
            self.subpaletteTransferButtons.append(button)
            tempCopyButtonsLayout.addWidget(button)
            
            button = QToolButton()
            button.setIcon(icons.ICON_DOWN)
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
        button.setIcon(icons.ICON_UP_DOUBLE)
        button.setToolTip("Copy all from bottom to top")
        button.clicked.connect(self.transferAllColoursUp)
        button.setDisabled(True)
        self.subpaletteTransferButtons.append(button)
        editOtherButtonsLayout.addWidget(button)
        
        button = QToolButton()
        button.setIcon(icons.ICON_DOWN_DOUBLE)
        button.setToolTip("Copy all from top to bottom")
        button.setDisabled(True)
        button.clicked.connect(self.transferAllColoursDown)
        self.subpaletteTransferButtons.append(button)
        editOtherButtonsLayout.addWidget(button)
        
        editorsLayout.addWidget(compareGroupBox)
        
        self.paletteSettingsGroupBox = QGroupBox("Palette Settings")
        settingsGroupBoxLayout = QHBoxLayout()
        self.paletteSettingsGroupBox.setLayout(settingsGroupBoxLayout)
        
        self.paletteSettingsTree = PaletteSettingsTreeWidget(self.projectData)
        self.paletteSettingsTree.currentItemChanged.connect(self.onPaletteSettingsTreeCurrentChanged)
        self.paletteSettingsTree.setMaximumWidth(self.paletteSettingsTree.sizeHint().width())
        settingsGroupBoxLayout.addWidget(self.paletteSettingsTree)
        
        settingsGroupBoxEditLayout = QFormLayout()
        settingsGroupBoxLayout.addLayout(settingsGroupBoxEditLayout)
        
        self.paletteSettingsFlashEffect = QSpinBox()
        self.paletteSettingsFlashEffect.setToolTip("Palette animation, such as in Stonehenge Base. Currently uneditable in CoilSnake. Only values 0-8 have data in vanilla.")
        self.paletteSettingsFlashEffect.setMaximum(common.BYTELIMIT)
        self.paletteSettingsSpritePalette = QSpinBox()
        self.paletteSettingsSpritePalette.setToolTip("Subpalette for sprites of palette 4 to use.")
        self.paletteSettingsSpritePalette.setMaximum(5)
        self.paletteSettingsFlag = FlagInput()
        self.paletteSettingsFlag.spinbox.setToolTip("If this flag is set, use these settings, if not, use the elsewise settings. Set to 0 to always occur and therefore terminate the chain.")
        
        childOptionsLayout = QHBoxLayout()
        self.paletteSettingsAddChild = QToolButton()
        self.paletteSettingsAddChild.setIcon(icons.ICON_NEW)
        self.paletteSettingsAddChild.setToolTip("Add elsewise settings")
        self.paletteSettingsRemoveChild = QToolButton()
        self.paletteSettingsRemoveChild.setIcon(icons.ICON_DELETE)
        self.paletteSettingsRemoveChild.setToolTip("Remove elsewise settings")
        self.paletteSettingsChildWarning = IconLabel()
        
        eventPaletteLayout = QHBoxLayout()
        self.paletteSettingsColoursWarning = IconLabel("Top level uses existing palette", icons.ICON_INFO)
        self.paletteSettingsColoursWarning.hide()
        self.paletteSettingsColoursEdit = QPushButton("Edit...")
        self.paletteSettingsColoursEdit.clicked.connect(self.onEditEventPalette)
        self.paletteSettingsColoursWarning.setMinimumHeight(self.paletteSettingsColoursEdit.sizeHint().height())
        self.paletteSettingsColoursCopy = QPushButton("Copy from...")
        self.paletteSettingsColoursCopy.clicked.connect(self.onCopyEventPalette)
        eventPaletteLayout.addWidget(self.paletteSettingsColoursWarning)
        eventPaletteLayout.addWidget(self.paletteSettingsColoursEdit)
        eventPaletteLayout.addWidget(self.paletteSettingsColoursCopy)
            
        childOptionsLayout.addWidget(self.paletteSettingsAddChild)
        childOptionsLayout.addWidget(self.paletteSettingsRemoveChild)
        childOptionsLayout.addWidget(self.paletteSettingsChildWarning)
        
        settingsGroupBoxEditLayout.addRow("Palette Animation", self.paletteSettingsFlashEffect)
        settingsGroupBoxEditLayout.addRow("Sprite Subpalette", self.paletteSettingsSpritePalette)
        settingsGroupBoxEditLayout.addRow("Event Flag", self.paletteSettingsFlag)
        settingsGroupBoxEditLayout.addRow("Elsewise Settings", childOptionsLayout)
        settingsGroupBoxEditLayout.addRow("Event Palette", eventPaletteLayout)
        
        editorsLayout.addWidget(self.paletteSettingsGroupBox)
        
        layout.addWidget(self.selection1)
        layout.addLayout(editorsLayout)
        
        self.menuFile = QMenu("&File")
        self.saveAction = QAction(icons.ICON_SAVE, "&Save", shortcut=QKeySequence("Ctrl+S"))
        self.saveAction.triggered.connect(self.parent().projectWin.saveAction.trigger)
        self.openAction = QAction(icons.ICON_LOAD, "&Open", shortcut=QKeySequence("Ctrl+O"))
        self.openAction.triggered.connect(self.parent().projectWin.openAction.trigger)
        self.reloadAction = QAction(icons.ICON_RELOAD, "&Reload", shortcut=QKeySequence("Ctrl+R"))
        self.reloadAction.triggered.connect(self.parent().projectWin.reloadAction.trigger)
        self.openSettingsAction = QAction(icons.ICON_SETTINGS, "Settings...")
        self.openSettingsAction.triggered.connect(lambda: SettingsDialog.openSettings(self))
        self.menuFile.addActions([self.saveAction, self.openAction, self.reloadAction])
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.openSettingsAction)
        
        
        self.menuHelp = QMenu("&Help")        
        self.aboutAction = QAction(icons.ICON_INFO, "&About EBME...")
        self.aboutAction.triggered.connect(lambda: AboutDialog.showAbout(self))
        self.menuHelp.addAction(self.aboutAction)
        
        if not debug.SYSTEM_OUTPUT:
            self.openDebugAction = QAction(icons.ICON_DEBUG, "Debug output")
            self.openDebugAction.triggered.connect(lambda: debug.DebugOutputDialog.openDebug(self))
            self.menuHelp.addAction(self.openDebugAction)
        
        self.menuItems = (self.menuFile, self.menuHelp)
        
    def parent(self) -> "MainApplication": # for typing
        return super().parent()
    
class PaletteSettingsTreeWidget(QTreeWidget):
    def __init__(self, projectData: ProjectData, parent: QWidget|None=None):
        super().__init__(parent)
        
        self.projectData = projectData
        
        self.setColumnCount(1)
        self.setHeaderLabels(["Palette Settings Hierachy"])
        
        self.lastSettings: PaletteSettings = None
    
    def populateSettings(self, settings: PaletteSettings):
        self.clear()
        
        self.lastSettings = settings
        
        previous: PaletteSettingsTreeItem|None = None
        while settings != None:
            if settings.flag == 0 and previous:
                string = "Settings if nothing else"
                icon = icons.ICON_DIAMOND
            elif settings.flag == 0 and not previous:
                string = "Settings always"
                icon = icons.ICON_DIAMOND
            else:
                if settings.flag >= 0x8000:
                    string = f"Settings if not flag {settings.flag-0x8000}"
                else:
                    string = f"Settings if flag {settings.flag}"
                icon = icons.ICON_SPLIT
            
            if isinstance(previous, PaletteSettingsTreeItem):
                item = PaletteSettingsTreeItem(settings, [string])
                previous.addChild(item)    
            else: 
                item = PaletteSettingsTreeItem(settings, previous, [string])
                self.addTopLevelItem(item)
            
            item.setIcon(0, icon)
                
            previous = item
            settings = settings.child
            
        self.expandAll()
    
    def currentItem(self) -> "PaletteSettingsTreeItem":
        return super().currentItem()

class PaletteSettingsTreeItem(QTreeWidgetItem):
    def __init__(self, settings: PaletteSettings, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = settings