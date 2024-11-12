from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QColor, QKeySequence, QUndoCommand
from PySide6.QtWidgets import (QFileDialog, QFormLayout, QGroupBox,
                               QHBoxLayout, QListWidget, QListWidgetItem,
                               QMenu, QMessageBox, QPushButton, QSpinBox,
                               QToolButton, QTreeWidgetItem, QVBoxLayout,
                               QWidget)

import src.misc.common as common
import src.misc.debug as debug
import src.misc.icons as icons
from src.actions.fts_actions import (ActionAddPalette,
                                     ActionAddPaletteSettingsChild,
                                     ActionChangePaletteSettings,
                                     ActionChangeSubpaletteColour,
                                     ActionRemovePalette,
                                     ActionRemovePaletteSettingsChild,
                                     ActionReplacePalette)
from src.coilsnake.fts_interpreter import Palette
from src.coilsnake.project_data import ProjectData
from src.misc.dialogues import (AboutDialog, AdvancedPalettePreviewDialog,
                                CopyEventPaletteDialog, EditEventPaletteDialog,
                                RenderPaletteDialog, SettingsDialog)
from src.objects.palette_settings import PaletteSettings
from src.widgets.input import ColourButton, FlagInput
from src.widgets.misc import IconLabel
from src.widgets.palette import (PaletteListItem, PaletteTreeWidget,
                                 SubpaletteListItem)

if TYPE_CHECKING:
    from src.main.main import MainApplication


class PaletteEditor(QWidget):
    def __init__(self, projectData: ProjectData, parent: QWidget|None = None):
        super().__init__(parent)
        self.projectData = projectData
        
        self.subpalette1Buttons: list[ColourButton] = []
        self.subpalette2Buttons: list[ColourButton] = []
        self.subpaletteTransferButtons: list[QToolButton] = [] # only for iterating, order is NOT reliable
        
        self.undoStack = self.parent().undoStack
        self.undoStack.undone.connect(self.onAction)
        self.undoStack.redone.connect(self.onAction)
        self.undoStack.pushed.connect(self.onAction)
        
        self.setupUI()
        self.paletteTree.setCurrentItem(self.paletteTree.topLevelItem(0), 0)
        
    def clobberAllCachedMinitiles(self):
        # for use on undo/redo. As with the gfx/tile editor,
        # we don't know what tileset to clobber the cache of,
        # so let's just do them all
        # (even with 10k iterations, it doesn't have a performance hit like I expected...?)
        for i in self.projectData.tilesets:
            for j in i.minitiles:
                j.BothToImage.cache_clear()
    
    def onAction(self, command: QUndoCommand):
        
        if not command:
            return
        
        actionType = None
        commands = []

        count = command.childCount()
        if count > 0: # handle macros
            for c in range(command.childCount()):
                commands.append(command.child(c))
                        
        if hasattr(command, "commands"): # handle multis (which should not have children)
            for c in command.commands:
                commands.append(c)
        
        # do this *always* to be safe        
        commands.append(command)
            
        for c in commands:
            if isinstance(c, ActionChangeSubpaletteColour):
                actionType = "subpalette"
            if isinstance(c, ActionReplacePalette):
                actionType = "palette"
            if isinstance(c, ActionChangePaletteSettings):
                actionType = "settings"
            if isinstance(c, ActionAddPaletteSettingsChild):
                self.paletteSettingsList.populateSettings(self.paletteSettingsList.item(0).settings)
                focus = self.paletteSettingsList.itemFromSettings(c.settings)
                if focus:
                    self.paletteSettingsList.setCurrentItem(focus)
                else:
                    focus = self.paletteSettingsList.itemFromSettings(c.parent) # may be undoing
                    if focus:
                        self.paletteSettingsList.setCurrentItem(focus)
                    else:
                        self.paletteSettingsList.setCurrentRow(0)
            if isinstance(c, ActionRemovePaletteSettingsChild):
                self.paletteSettingsList.populateSettings(self.paletteSettingsList.item(0).settings)
                focus = self.paletteSettingsList.itemFromSettings(c._settings) # first check if undoing
                if focus:
                    self.paletteSettingsList.setCurrentItem(focus)
                else:
                    focus = self.paletteSettingsList.itemFromSettings(c.parent) # otherwise this is redo behavior
                    if focus:
                        self.paletteSettingsList.setCurrentItem(focus)
                    else:
                        self.paletteSettingsList.setCurrentRow(0)
            if isinstance(c, ActionAddPalette) or isinstance(c, ActionRemovePalette):
                self.paletteTree.syncPaletteGroup(c.palette.groupID)
                self.comparePaletteTree.syncPaletteGroup(c.palette.groupID)
                
        match actionType:
            case "subpalette":
                self.refreshSubpaletteDisplay()
                # see gfx editor for why we don't/can't specify what to clobber :(
                self.projectData.clobberTileGraphicsCache()
                self.clobberAllCachedMinitiles()
            case "palette":
                self.refreshSubpaletteDisplay()
                self.projectData.clobberTileGraphicsCache()
                self.clobberAllCachedMinitiles()
            case "settings":
                self.onPaletteSettingsListCurrentChanged(self.paletteSettingsList.currentItem())
                self.paletteSettingsList.updateLabels()
                
    def refreshSubpaletteDisplay(self):
        self.onPaletteTreeCurrentChanged(self.paletteTree.currentItem())
        self.onCompareTreeCurrentChanged(self.comparePaletteTree.currentItem())
        
    def transferColourUp(self, index: int):
        """If lite, don't refresh display and clobber gfx cache"""
        current = self.paletteTree.getCurrentSubpalette()
        if current:
            subpalette = self.projectData.getTileset(self.paletteTree.getCurrentTileset().tileset).getPalette(
                self.paletteTree.getCurrentPaletteGroup().paletteGroup, self.paletteTree.getCurrentPalette().palette
            ).subpalettes[current.subpalette]
            action = ActionChangeSubpaletteColour(subpalette, index, self.subpalette2Buttons[index].chosenColour.toTuple()[:3])
            self.undoStack.push(action)
        
    def transferColourDown(self, index: int):
        """If lite, don't refresh display and clobber gfx cache"""
        current = self.comparePaletteTree.getCurrentSubpalette()
        if current:
            subpalette = self.projectData.getTileset(self.comparePaletteTree.getCurrentTileset().tileset).getPalette(
                self.comparePaletteTree.getCurrentPaletteGroup().paletteGroup, self.comparePaletteTree.getCurrentPalette().palette
            ).subpalettes[current.subpalette]
            action = ActionChangeSubpaletteColour(subpalette, index, self.subpalette1Buttons[index].chosenColour.toTuple()[:3])
            self.undoStack.push(action)
        
    # TODO what the fuck is making these so slow???
    def transferAllColoursUp(self):
        current = self.paletteTree.getCurrentSubpalette()
        if current:
            subpalette = self.projectData.getTileset(self.paletteTree.getCurrentTileset().tileset).getPalette(
                self.paletteTree.getCurrentPaletteGroup().paletteGroup, self.paletteTree.getCurrentPalette().palette
            ).subpalettes[current.subpalette]
            
            self.undoStack.beginMacro("Copy subpalette colours")
            
            for i in range(0, 16):
                action = ActionChangeSubpaletteColour(subpalette, i, self.subpalette2Buttons[i].chosenColour.toTuple()[:3])
                self.undoStack.push(action)
            self.undoStack.endMacro()
        
    def transferAllColoursDown(self):
        current = self.comparePaletteTree.getCurrentSubpalette()
        if current:
            subpalette = self.projectData.getTileset(self.comparePaletteTree.getCurrentTileset().tileset).getPalette(
                self.comparePaletteTree.getCurrentPaletteGroup().paletteGroup, self.comparePaletteTree.getCurrentPalette().palette
            ).subpalettes[current.subpalette]
            
            self.undoStack.beginMacro("Copy subpalette colours")
            for i in range(0, 16):
                action = ActionChangeSubpaletteColour(subpalette, i, self.subpalette1Buttons[i].chosenColour.toTuple()[:3])
                self.undoStack.push(action)
            self.undoStack.endMacro()
    
    def onTopColourChanged(self, colour: int):
        current = self.paletteTree.getCurrentSubpalette()
        if current:
            subpalette = self.projectData.getTileset(self.paletteTree.getCurrentTileset().tileset).getPalette(
                self.paletteTree.getCurrentPaletteGroup().paletteGroup, self.paletteTree.getCurrentPalette().palette
            ).subpalettes[current.subpalette]
            
            newColour = self.subpalette1Buttons[colour].chosenColour.toTuple()[:3]
            
            self.undoStack.push(ActionChangeSubpaletteColour(subpalette, colour, newColour))
        
        
    def onBottomColourChanged(self, colour: int):
        current = self.comparePaletteTree.getCurrentSubpalette()
        if current:
            subpalette = self.projectData.getTileset(self.comparePaletteTree.getCurrentTileset().tileset).getPalette(
                self.comparePaletteTree.getCurrentPaletteGroup().paletteGroup, self.comparePaletteTree.getCurrentPalette().palette
            ).subpalettes[current.subpalette]
            
            newColour = self.subpalette2Buttons[colour].chosenColour.toTuple()[:3]
            
            self.undoStack.push(ActionChangeSubpaletteColour(subpalette, colour, newColour))
        
    def onPaletteTreeCurrentChanged(self, new: QTreeWidgetItem):        
        if isinstance(new, SubpaletteListItem):
            self.comparePaletteTree.setEnabled(True)
            
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
            
            if self.comparePaletteTree.getCurrentSubpalette():
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
            self.comparePaletteTree.setDisabled(True)
        
            if isinstance(new, PaletteListItem):
                self.loadPaletteSettingsTree(new.parent().paletteGroup,
                                        new.palette)
            
            else:
                self.paletteSettingsGroupBox.setDisabled(True)
    
    def loadPaletteSettingsTree(self, paletteGroup: int, palette: int):
        self.paletteSettingsGroupBox.setEnabled(True)
        
        settings = self.projectData.paletteSettings[paletteGroup][palette]
        
        if settings != self.paletteSettingsList.lastSettings:
            self.paletteSettingsList.blockSignals(True)
            self.paletteSettingsList.populateSettings(settings)
            self.paletteSettingsList.blockSignals(False)
            
            self.paletteSettingsList.setCurrentItem(self.paletteSettingsList.item(0))
    
    def onPaletteSettingsListCurrentChanged(self, new: "PaletteSettingsListItem"):
        if new:
            settings = new.settings
            
            if self.paletteSettingsList.item(0) == new:
                self.paletteSettingsColoursWarning.show()
                self.paletteSettingsColoursEdit.hide()
                self.paletteSettingsColoursCopy.hide()
                self.paletteSettingsColoursExport.hide()
                self.paletteSettingsColoursImport.hide()
                self.paletteSettingsColoursRender.hide()
            else:
                self.paletteSettingsColoursWarning.hide()
                self.paletteSettingsColoursEdit.show()
                self.paletteSettingsColoursCopy.show()
                self.paletteSettingsColoursExport.show()
                self.paletteSettingsColoursImport.show()
                self.paletteSettingsColoursRender.show()
                
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
        palette = self.paletteSettingsList.currentItem().settings.palette
        if palette:
            actions = EditEventPaletteDialog.editEventPalette(self, palette,
                                                              self.paletteTree.getCurrentTileset().tileset,
                                                              self.projectData)
            if actions:
                self.undoStack.push(actions)
    
    def onCopyEventPalette(self):
        palette = self.paletteSettingsList.currentItem().settings.palette
        if palette:
            action = CopyEventPaletteDialog.copyEventPalette(self, palette, self.projectData)
            if action:
                self.undoStack.push(action)
             
    def onCompareTreeCurrentChanged(self, new: QTreeWidgetItem):
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
            
            if self.paletteTree.getCurrentSubpalette():
                for i in self.subpaletteTransferButtons:
                    i.setEnabled(True)
        
        else:
            for i in self.subpalette2Buttons:
                i.setDisabled(True)
            for i in self.subpaletteTransferButtons:
                i.setDisabled(True)
                
    def toPaletteSettings(self):
        current = self.paletteSettingsList.currentItem()
        action = ActionChangePaletteSettings(current.settings,
                                             self.paletteSettingsFlag.value(),
                                             self.paletteSettingsFlashEffect.value(),
                                             self.paletteSettingsSpritePalette.value())
        self.undoStack.push(action)
                        
    def renderPaletteImage(self):
        palette = self.paletteTree.getCurrentPalette()
        if not palette:
            return common.showErrorMsg("Cannot render palette",
                                       "Please select a palette to render.",
                                       icon = QMessageBox.Icon.Warning)
        else:
            palette = self.projectData.getTileset(palette.parent().parent().tileset
            ).getPalette(palette.parent().paletteGroup, palette.palette)
            RenderPaletteDialog.renderPalette(self, palette)
        
    def renderEventPaletteImage(self):
        palette = self.paletteSettingsList.currentItem().settings.palette
        if not palette:
            return common.showErrorMsg("Cannot render event palette",
                                       "Please select palette settings with an event palette to render.",
                                       icon = QMessageBox.Icon.Warning)
        else:
            RenderPaletteDialog.renderPalette(self, palette)
        
    def exportPalette(self):
        current = self.paletteTree.getCurrentPalette()
        if not current:
            return common.showErrorMsg("Cannot export palette",
                                       "Please select a palette to export from.",
                                       icon = QMessageBox.Icon.Warning)
        
        path, _ = QFileDialog.getSaveFileName(self,
                                           "Export palette",
                                           self.projectData.dir,
                                           "*.ebpal")
        if path:
            path = common.normaliseFileExtension(path, "ebpal")
            try:
                with open(path, "w", encoding="utf-8") as file:
                    palette = self.projectData.getTileset(current.parent().parent().tileset).getPalette(
                        current.parent().paletteGroup, current.palette
                    )
                    file.write(palette.toRaw())
            except Exception as e:
                common.showErrorMsg("Cannot export palette",
                                    "An error occured when exporting the palette.",
                                    str(e))
                raise
    
    def exportEventPalette(self):
        palette = self.paletteSettingsList.currentItem().settings.palette
        if not palette:
            return common.showErrorMsg("Cannot export event palette",
                                       "Please select palette settings with a palette to export from.",
                                       icon = QMessageBox.Icon.Warning)
        
        path, _ = QFileDialog.getSaveFileName(self,
                                           "Export event palette",
                                           self.projectData.dir,
                                           "*.ebpal")
        if path:
            path = common.normaliseFileExtension(path, "ebpal")
            try:
                with open(path, "w", encoding="utf-8") as file:
                    file.write(palette.toRaw())
            except Exception as e:
                common.showErrorMsg("Cannot export palette",
                                    "An error occured when exporting the event palette.",
                                    str(e))
                raise
        
    def importPalette(self):
        current = self.paletteTree.getCurrentPalette()
        if not current:
            return common.showErrorMsg("Cannot import palette",
                                       "Please select a palette to import over.",
                                       icon = QMessageBox.Icon.Warning)
        
        path, _ = QFileDialog.getOpenFileName(self,
                                           "Import palette",
                                           self.projectData.dir,
                                           "*.ebpal")
        if path:
            try:
                with open(path, encoding="utf-8") as file:
                    oldPalette = self.projectData.getTileset(current.parent().parent().tileset).getPalette(
                        current.parent().paletteGroup, current.palette
                    )
                    
                    newPalette = Palette(file.read())
                    
                    self.undoStack.push(ActionReplacePalette(newPalette, oldPalette))                        
                    
            except Exception as e:
                common.showErrorMsg("Cannot import palette",
                                    "An error occured when importing the palette.",
                                    str(e))
                raise
    
    def importEventPalette(self):
        palette = self.paletteSettingsList.currentItem().settings.palette
        if not palette:
            return common.showErrorMsg("Cannot import event palette",
                                       "Please select palette settings with an event palette to import over.",
                                       icon = QMessageBox.Icon.Warning)
        
        path, _ = QFileDialog.getOpenFileName(self,
                                           "Import event palette",
                                           self.projectData.dir,
                                           "*.ebpal")
        if path:
            try:
                with open(path, encoding="utf-8") as file:                    
                    newPalette = Palette(file.read())
                    
                    self.undoStack.push(ActionReplacePalette(newPalette, palette))
                    
            except Exception as e:
                common.showErrorMsg("Cannot import event palette",
                                    "An error occured when importing the event palette.",
                                    str(e))
                raise
            
    def addPalette(self):
        current = self.paletteTree.getCurrentPaletteGroup()
        if not current:
            return common.showErrorMsg("Cannot add palette",
                                       "Please select a palette group to add a palette to.",
                                       icon=QMessageBox.Icon.Warning)
            
        tileset = self.projectData.getTileset(current.parent().tileset)
        paletteGroup = tileset.getPaletteGroup(current.paletteGroup)
        # "add" more like duplicate
        base = paletteGroup.palettes[-1]
        if base.paletteID >= 7:
            return common.showErrorMsg("Cannot add palette",
                                       "The maximum number of palettes in this palette group has been reached.",
                                       icon=QMessageBox.Icon.Warning)
        
        new = Palette(common.baseN(current.paletteGroup, 32)
                      + common.baseN(base.paletteID+1, 32)
                      + base.toRaw()[2:])
        
        action = ActionAddPalette(new, self.projectData)
        self.undoStack.push(action)
        
    def removePalette(self):
        current = self.paletteTree.getCurrentPalette()
        if not current:
            return common.showErrorMsg("Cannot remove palette",
                                       "Please select a palette to remove.",
                                       icon=QMessageBox.Icon.Warning)
            
        tileset = self.projectData.getTileset(current.parent().parent().tileset)
        paletteGroup = tileset.getPaletteGroup(current.parent().paletteGroup)
        palette = paletteGroup.palettes[current.palette]
        # "add" more like duplicate
        base = paletteGroup.palettes[current.palette]
        if len(paletteGroup.palettes) == 1:
            return common.showErrorMsg("Cannot remove palette",
                                       "Cannot leave a palette group with no palettes.",
                                       icon=QMessageBox.Icon.Warning)
        
        action = ActionRemovePalette(base, self.projectData)
        self.undoStack.push(action)
    
    def addPaletteSettingsChild(self):
        current = self.paletteSettingsList.currentItem()
        new = PaletteSettings(0, 0, 0)
        
        if current.settings.palette:
            new.palette = current.settings.palette
        else:
            palette = self.projectData.getPaletteGroup(self.paletteTree.getCurrentPaletteGroup().paletteGroup
                                                      ).palettes[self.paletteTree.getCurrentPalette().palette]
            new.palette = Palette(palette.toRaw()) # make a copy of the current if top-level
        
        action = ActionAddPaletteSettingsChild(new, current.settings)
        self.undoStack.push(action)
    
    def removePaletteSettingsChild(self):
        current = self.paletteSettingsList.currentItem()
        top = self.paletteSettingsList.item(0)
        
        action = ActionRemovePaletteSettingsChild(current.settings, top.settings)
        self.undoStack.push(action)
        
    def setupUI(self):
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        paletteSelectionLayout = QVBoxLayout()
        self.paletteTree = PaletteTreeWidget(self.projectData, self)
        self.paletteTree.setMaximumWidth(self.paletteTree.sizeHint().width())
        self.paletteTree.currentItemChanged.connect(self.onPaletteTreeCurrentChanged)
        paletteSelectionLayout.addWidget(self.paletteTree)
        
        addRemoveLayout = QHBoxLayout()
        self.addPaletteButton = QPushButton("Add palette")
        self.addPaletteButton.setIcon(icons.ICON_NEW)
        self.addPaletteButton.clicked.connect(self.addPalette)
        self.removePaletteButton = QToolButton()
        self.removePaletteButton.setIcon(icons.ICON_DELETE)
        self.removePaletteButton.setToolTip("Remove palette")
        self.removePaletteButton.clicked.connect(self.removePalette)
        addRemoveLayout.addWidget(self.addPaletteButton)
        addRemoveLayout.addWidget(self.removePaletteButton)
        paletteSelectionLayout.addLayout(addRemoveLayout)
        
        editorsLayout = QVBoxLayout()
        
        compareGroupBox = QGroupBox("Compare Subpalettes")
        compareGroupBoxLayout = QHBoxLayout() 
        compareGroupBox.setLayout(compareGroupBoxLayout)
        
        self.comparePaletteTree = PaletteTreeWidget(self.projectData, self)
        self.comparePaletteTree.setMaximumWidth(self.comparePaletteTree.sizeHint().width())
        self.comparePaletteTree.currentItemChanged.connect(self.onCompareTreeCurrentChanged)
        self.comparePaletteTree.setHeaderHidden(False)
        self.comparePaletteTree.setHeaderLabel("Compare against...")
        
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
        compareGroupBoxLayout.addWidget(self.comparePaletteTree)
        
        for i in range(0, 16):
            button = ColourButton()
            button.setFixedSize(24, 24)
            button.colourChanged.connect(lambda i=i: self.onTopColourChanged(i)) # bypass a rather curious lambda-in-loop side effect with i=i
            self.subpalette1Buttons.append(button)
            editTopRowLayout.addWidget(button)
            
            tempCopyButtonsLayout = QVBoxLayout()
            button = QToolButton()
            button.setIcon(icons.ICON_UP)
            button.setToolTip("Copy from bottom to top")
            button.clicked.connect(lambda _, i=i: self.transferColourUp(i)) # passes "isChecked" bool to first argument
            button.setDisabled(True)
            self.subpaletteTransferButtons.append(button)
            tempCopyButtonsLayout.addWidget(button)
            
            button = QToolButton()
            button.setIcon(icons.ICON_DOWN)
            button.setToolTip("Copy from top to bottom")
            button.clicked.connect(lambda _, i=i: self.transferColourDown(i))
            button.setDisabled(True)
            self.subpaletteTransferButtons.append(button)
            tempCopyButtonsLayout.addWidget(button)
            
            editMiddleRowLayout.addLayout(tempCopyButtonsLayout)
            
            button = ColourButton()
            button.setFixedSize(24, 24)
            button.colourChanged.connect(lambda i=i: self.onBottomColourChanged(i))
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
        
        self.paletteSettingsList = PaletteSettingsTreeWidget(self.projectData)
        self.paletteSettingsList.currentItemChanged.connect(self.onPaletteSettingsListCurrentChanged)
        self.paletteSettingsList.setMaximumWidth(self.paletteSettingsList.sizeHint().width())
        settingsGroupBoxLayout.addWidget(self.paletteSettingsList)
        
        settingsGroupBoxEditLayout = QFormLayout()
        settingsGroupBoxLayout.addLayout(settingsGroupBoxEditLayout)
        
        self.paletteSettingsFlashEffect = QSpinBox()
        self.paletteSettingsFlashEffect.setToolTip("Palette animation, such as in Stonehenge Base. Currently uneditable in CoilSnake. Only values 0-8 have data in vanilla.")
        self.paletteSettingsFlashEffect.setMaximum(common.BYTELIMIT)
        self.paletteSettingsFlashEffect.editingFinished.connect(self.toPaletteSettings)
        
        self.paletteSettingsSpritePalette = QSpinBox()
        self.paletteSettingsSpritePalette.setToolTip("Subpalette for sprites of palette 4 to use.")
        self.paletteSettingsSpritePalette.setMaximum(5)
        self.paletteSettingsSpritePalette.editingFinished.connect(self.toPaletteSettings)
        
        self.paletteSettingsFlag = FlagInput()
        self.paletteSettingsFlag.spinbox.setToolTip("If this flag is set, use these settings, if not, use the elsewise settings. Set to 0 to always occur and therefore terminate the chain.")
        self.paletteSettingsFlag.editingFinished.connect(self.toPaletteSettings)
        self.paletteSettingsFlag.inverted.connect(self.toPaletteSettings)
        
        childOptionsLayout = QHBoxLayout()
        self.paletteSettingsAddChild = QToolButton()
        self.paletteSettingsAddChild.setIcon(icons.ICON_NEW)
        self.paletteSettingsAddChild.setToolTip("Add elsewise settings")
        self.paletteSettingsAddChild.clicked.connect(self.addPaletteSettingsChild)
        self.paletteSettingsRemoveChild = QToolButton()
        self.paletteSettingsRemoveChild.setIcon(icons.ICON_DELETE)
        self.paletteSettingsRemoveChild.setToolTip("Remove elsewise settings")
        self.paletteSettingsRemoveChild.clicked.connect(self.removePaletteSettingsChild)
        self.paletteSettingsChildWarning = IconLabel()
        
        eventPaletteLayout = QHBoxLayout()
        self.paletteSettingsColoursWarning = IconLabel("Top level uses existing palette", icons.ICON_INFO)
        self.paletteSettingsColoursWarning.hide()
        self.paletteSettingsColoursEdit = QPushButton("Edit...")
        self.paletteSettingsColoursEdit.clicked.connect(self.onEditEventPalette)
        self.paletteSettingsColoursWarning.setMinimumHeight(self.paletteSettingsColoursEdit.sizeHint().height())
        self.paletteSettingsColoursCopy = QPushButton("Copy from...")
        self.paletteSettingsColoursCopy.clicked.connect(self.onCopyEventPalette)
        self.paletteSettingsColoursExport = QToolButton()
        self.paletteSettingsColoursExport.setIcon(icons.ICON_EXPORT)
        self.paletteSettingsColoursExport.clicked.connect(self.exportEventPalette)
        self.paletteSettingsColoursExport.setToolTip("Export")
        self.paletteSettingsColoursImport = QToolButton()
        self.paletteSettingsColoursImport.setIcon(icons.ICON_IMPORT)
        self.paletteSettingsColoursImport.clicked.connect(self.importEventPalette)
        self.paletteSettingsColoursImport.setToolTip("Import")
        self.paletteSettingsColoursRender = QToolButton()
        self.paletteSettingsColoursRender.setIcon(icons.ICON_RENDER_IMG)
        self.paletteSettingsColoursRender.clicked.connect(self.renderEventPaletteImage)
        self.paletteSettingsColoursRender.setToolTip("Render image")
        
        eventPaletteLayout.addWidget(self.paletteSettingsColoursWarning)
        eventPaletteLayout.addWidget(self.paletteSettingsColoursEdit)
        eventPaletteLayout.addWidget(self.paletteSettingsColoursCopy)
        eventPaletteLayout.addWidget(self.paletteSettingsColoursExport)
        eventPaletteLayout.addWidget(self.paletteSettingsColoursImport)
        eventPaletteLayout.addWidget(self.paletteSettingsColoursRender)
            
        childOptionsLayout.addWidget(self.paletteSettingsAddChild)
        childOptionsLayout.addWidget(self.paletteSettingsRemoveChild)
        childOptionsLayout.addWidget(self.paletteSettingsChildWarning)
        
        settingsGroupBoxEditLayout.addRow("Palette Animation", self.paletteSettingsFlashEffect)
        settingsGroupBoxEditLayout.addRow("Sprite Subpalette", self.paletteSettingsSpritePalette)
        settingsGroupBoxEditLayout.addRow("Event Flag", self.paletteSettingsFlag)
        settingsGroupBoxEditLayout.addRow("Elsewise Settings", childOptionsLayout)
        settingsGroupBoxEditLayout.addRow("Event Palette", eventPaletteLayout)
        
        editorsLayout.addWidget(self.paletteSettingsGroupBox)
        
        layout.addLayout(paletteSelectionLayout)
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
        
        self.menuEdit = QMenu("&Edit")
        self.menuEdit.addActions([self.parent().sharedActionUndo, self.parent().sharedActionRedo])
        
        self.menuView = QMenu("&View")
        self.hexAction = self.parent().sharedActionHex
        self.tileIDAction = self.parent().sharedActionTileIDs
        self.menuView.addActions([self.hexAction, self.tileIDAction])

        self.menuTools = QMenu("&Tools")
        self.renderPaletteAction = QAction(icons.ICON_RENDER_IMG, "&Render image of palette...")
        self.renderPaletteAction.triggered.connect(self.renderPaletteImage)
        self.exportPaletteAction = QAction(icons.ICON_EXPORT, "&Export palette...")
        self.exportPaletteAction.triggered.connect(self.exportPalette)
        self.importPaletteAction = QAction(icons.ICON_IMPORT, "&Import palette...")
        self.importPaletteAction.triggered.connect(self.importPalette)
        self.advancedPalettePreviewAction = QAction(icons.ICON_PALETTE, "&Advanced palette preview...")
        self.advancedPalettePreviewAction.triggered.connect(lambda: AdvancedPalettePreviewDialog.advancedPalettePreview(self, self.projectData))
        self.menuTools.addActions([self.renderPaletteAction, self.advancedPalettePreviewAction])
        self.menuTools.addSeparator()
        self.menuTools.addActions([self.exportPaletteAction, self.importPaletteAction])
        
        self.menuHelp = QMenu("&Help")        
        self.aboutAction = QAction(icons.ICON_INFO, "&About EBME...")
        self.aboutAction.triggered.connect(lambda: AboutDialog.showAbout(self))
        self.menuHelp.addAction(self.aboutAction)
        
        if not debug.SYSTEM_OUTPUT:
            self.openDebugAction = QAction(icons.ICON_DEBUG, "Debug output")
            self.openDebugAction.triggered.connect(lambda: debug.DebugOutputDialog.openDebug(self))
            self.menuHelp.addAction(self.openDebugAction)
        
        self.menuItems = (self.menuFile, self.menuEdit, self.menuView, self.menuTools, self.menuHelp)
        
    def parent(self) -> "MainApplication": # for typing
        return super().parent()
    
class PaletteSettingsTreeWidget(QListWidget):
    def __init__(self, projectData: ProjectData, parent: QWidget|None=None):
        super().__init__(parent)
        
        self.projectData = projectData
        self.lastSettings: PaletteSettings = None
    
    def populateSettings(self, settings: PaletteSettings):
        self.clear()
        
        self.lastSettings = settings
        
        previous: PaletteSettingsListItem|None = None
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
            
            item = PaletteSettingsListItem(settings, icon, string)
            self.addItem(item)  
            
            previous = item
            settings = settings.child
    
    def updateLabels(self):
        for i in [self.item(j) for j in range(self.count())]:
            i: PaletteSettingsListItem
            if i.settings.flag == 0:
                if self.item(0) == i:
                    string = "Settings always"
                else:
                    string = "Settings if nothing else"
                icon = icons.ICON_DIAMOND
            else:
                if i.settings.flag >= 0x8000:
                    string = f"Settings if not flag {i.settings.flag-0x8000}"
                else:
                    string = f"Settings if flag {i.settings.flag}"
                icon = icons.ICON_SPLIT
            
            i.setText(string)
            i.setIcon(icon)
            
    def itemFromSettings(self, settings: PaletteSettings):
        for i in [self.item(j) for j in range(self.count())]:
            i: PaletteSettingsListItem
            if i.settings == settings:
                return i
    
    def currentItem(self) -> "PaletteSettingsListItem":
        return super().currentItem()

class PaletteSettingsListItem(QListWidgetItem):
    def __init__(self, settings: PaletteSettings, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = settings