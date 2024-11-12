import logging
import traceback
from math import ceil
from typing import TYPE_CHECKING

from PIL import ImageQt
from PySide6.QtCore import QFile, QRectF, QSettings, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
                               QDialogButtonBox, QFileDialog, QFormLayout,
                               QGraphicsScene, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem,
                               QMessageBox, QPushButton, QScrollArea,
                               QSizePolicy, QSpinBox, QStyleFactory, QTextEdit,
                               QUndoView, QVBoxLayout, QWidget)

import src.misc.common as common
import src.misc.icons as icons
import src.misc.quotes as quotes
from src.actions.fts_actions import (ActionChangeSubpaletteColour,
                                     ActionReplacePalette, ActionSwapMinitiles)
from src.actions.misc_actions import MultiActionWrapper
from src.coilsnake.fts_interpreter import (FullTileset, Minitile, Palette,
                                           PaletteGroup, Subpalette)
from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords
from src.widgets.input import ColourButton, CoordsInput
from src.widgets.layout import HorizontalGraphicsView, HSeparator
from src.widgets.misc import IconLabel
from src.widgets.palette import (PaletteListItem, PaletteSelector,
                                 PaletteTreeWidget, SubpaletteListItem)
from src.widgets.tile import TilesetDisplayGraphicsScene

if TYPE_CHECKING:
    from src.mapeditor.map.map_scene import MapEditorScene


class FindDialog(QDialog):
    LAST_TYPE = 0
    """Input dialog for finding various map objects"""

    def __init__(self, parent, projectData: ProjectData):
        QDialog.__init__(self, parent)
        
        self.projectData = projectData

        self.setWindowTitle("Find")
        form = QFormLayout(self)

        self.findType = QComboBox()
        self.findType.addItems(["NPC", "Enemy tile", "Hotspot", "Warp", "Teleport"])
        self.findType.setCurrentIndex(FindDialog.LAST_TYPE)

        self.input = QSpinBox()
        self.input.setRange(0, common.WORDLIMIT)

        self.findCancelLayout = QHBoxLayout()
        self.findButton = QPushButton("Find")
        self.cancelButton = QPushButton("Cancel")
        self.findCancelLayout.addWidget(self.findButton)
        self.findCancelLayout.addWidget(self.cancelButton)

        self.resultsBox = QGroupBox("Results")
        self.resultsLayout = QHBoxLayout(self.resultsBox)
        self.resultsList = QListWidget()
        self.resultsList.setDisabled(True)
        self.resultsList.addItem("Choose an object type and input an ID to find.")
        self.resultsLayout.addWidget(self.resultsList)

        self.goButton = QPushButton("Go to this object")
        self.goButton.setDisabled(True)
        
        self.findButton.pressed.connect(self.findThings)
        self.cancelButton.pressed.connect(self.reject)
        self.resultsList.doubleClicked.connect(self.accept)

        form.addRow("Type", self.findType)
        form.addRow("ID", self.input)
        form.addRow(self.findCancelLayout)
        form.addRow(self.resultsBox)
        form.addRow(QLabel("Double-click an item to go to it."))


    def findThings(self):
        objType = self.findType.currentText()
        objID = self.input.value()
        self.resultsList.clear()
        
        FindDialog.LAST_TYPE = self.findType.currentIndex()

        match objType:
            case "NPC":
                for i in self.projectData.npcinstances:
                    if i.npcID == objID:
                        item = FindDialogListItem(i, f"-At ({i.coords.x}, {i.coords.y})")
                        self.resultsList.addItem(item)
            case "Enemy tile":
                if objID != 0:
                    for x in self.projectData.enemyPlacements:
                        for i in x:
                            if i.groupID == objID:
                                item = FindDialogListItem(i, f"-At {i.coords.coordsEnemy()}")
                                self.resultsList.addItem(item)
            case "Hotspot":
                for i in self.projectData.hotspots:
                    if i.id == objID:
                        item = FindDialogListItem(i, f"-At {i.start.coordsWarp()} to {i.end.coordsWarp()}")
                        self.resultsList.addItem(item)
            
            case "Warp":
                for i in self.projectData.warps:
                    if i.id == objID:
                        item = FindDialogListItem(i, f"-At {i.dest.coordsWarp()}")
                        self.resultsList.addItem(item)
                        
            case "Teleport":
                for i in self.projectData.teleports:
                    if i.id == objID:
                        name = i.name if i.name != "" else "<unnamed>"
                        item = FindDialogListItem(i, f"-{name}, at {i.dest.coordsWarp()}")
                        self.resultsList.addItem(item)

        if self.resultsList.count() == 0:
            self.resultsList.addItem("Nothing was found.")
            self.resultsList.setDisabled(True)
            self.goButton.setDisabled(True)
        else:
            self.resultsList.setEnabled(True)
            self.goButton.setEnabled(True)
            
    @staticmethod
    def findObject(parent, projectData: ProjectData):
        """Search for an object on the map. Returns False if cancelled, and the object (non-map type) if found"""
        try:
            dialog = FindDialog(parent, projectData)
            result = dialog.exec()

            if result == QDialog.Accepted:
                if dialog.resultsList.currentItem():
                    return dialog.resultsList.currentItem().obj
                else:
                    return False
            else:
                return False

        except Exception as e:
            logging.warning(f"Error finding object: {str(e)}")
            return False
            
class FindDialogListItem(QListWidgetItem):
    """Quick little subclass so we can remember associated found objects."""
    def __init__(self, obj, *args, **kwargs):
        QListWidgetItem.__init__(self, *args, **kwargs)
        self.obj = obj


class CoordsDialog(QDialog):
    LAST_TYPE = 0
    """Input dialog for EB map coordinates"""

    def __init__(self, *args, **kwargs):
        QDialog.__init__(self, *args, **kwargs)

        self.setWindowTitle("Go to coordinates")
        form = QFormLayout(self)
        form.addRow(QLabel("Coordinates"))

        self.coordsLayout = QHBoxLayout()
        self.inputX = QSpinBox()
        self.inputY = QSpinBox()
        self.inputX.setRange(0, common.WORDLIMIT)
        self.inputY.setRange(0, common.WORDLIMIT)
        self.inputXLabel = QLabel("X")
        self.inputYLabel = QLabel("Y")
        self.coordsLayout.addWidget(self.inputXLabel)
        self.coordsLayout.addWidget(self.inputX)
        self.coordsLayout.addWidget(self.inputYLabel)
        self.coordsLayout.addWidget(self.inputY)

        self.coordsType = QComboBox()
        self.coordsType.addItems(["Pixels (1:1)",
                                  "Warps / minitiles (1:8)",
                                  "Tiles (1:32)",
                                  "Enemy tiles (1:64)",
                                  "Sectors (1:256 / 1:128)",
                                  "Double sectors (1:256)"])
        self.coordsType.setCurrentIndex(CoordsDialog.LAST_TYPE)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                   Qt.Horizontal, self)
        
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        form.addRow(self.coordsLayout)
        form.addRow("Type", self.coordsType)
        form.addRow(buttons)

    @staticmethod
    def getCoords(parent) -> EBCoords:
        """Get user-inputted coordinates from the dialog."""
        try:
            dialog = CoordsDialog(parent)
            result = dialog.exec()

            if result == QDialog.Accepted:
                CoordsDialog.LAST_TYPE = dialog.coordsType.currentIndex()
                match dialog.coordsType.currentText():
                    case "Pixels (1:1)":
                        return EBCoords(dialog.inputX.value(), dialog.inputY.value())
                    case "Warps / minitiles (1:8)":
                        return EBCoords.fromWarp(dialog.inputX.value(), dialog.inputY.value())
                    case "Tiles (1:32)":
                        return EBCoords.fromTile(dialog.inputX.value(), dialog.inputY.value())
                    case "Enemy tiles (1:64)":
                        return EBCoords.fromEnemy(dialog.inputX.value(), dialog.inputY.value())
                    case "Sectors (1:256 / 1:128)":
                        return EBCoords.fromSector(dialog.inputX.value(), dialog.inputY.value())
                    case "Double sectors (1:256)":
                        return EBCoords.fromBisector(dialog.inputX.value(), dialog.inputY.value())
                    
            else: return False

        except Exception as e:
            logging.warning(f"Error getting coordinates: {str(e)}")
            return False
        
class AboutDialog(QDialog):
    """About the program dialog"""
    
    def __init__(self, *args, **kwargs):
        QDialog.__init__(self, *args, **kwargs)

        self.setWindowTitle("About EBME")
        form = QFormLayout(self)
        imgLabel = QLabel()
        imgLabel.setPixmap(QPixmap(":/logos/logo.png"))
        form.addRow(imgLabel)
        form.addRow(QLabel("""<span style=font-family:Onett;font-size:20px>
                           <span style=color:#F80858>Earth</span><!--(This trick removes the space caused by a newline)
                           --><span style=color:#9070F0>Bound</span>
                           <span style=color:#F80858>Map</span>
                           <span style=color:#9070F0>Editor</span></span>"""))
        form.addRow(QLabel(f"Version {common.VERSION}"))

        form.addRow(HSeparator())
        form.addRow(QLabel("EBME was written by SupremeKirb."))
        unlicenseButton = QPushButton("View unlicense...")
        unlicenseButton.clicked.connect(lambda: EBMELicenseDialog.showLicense(self))
        form.addRow(unlicenseButton)
        
        repoLink = QLabel('<a href="https://github.com/Supremekirb/EBME" style=color:#7038D0>Visit the repository on GitHub.</a>')
        repoLink.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        repoLink.setOpenExternalLinks(True)
        form.addRow(repoLink)

        form.addRow(HSeparator())
        form.addRow(QLabel("""<span style=font-family:Onett;font-size:20px>
                           <span style=color:#F80858>Special</span> <span style=color:#9070F0>thanks</span></span><br>
                           Everyone who worked on CoilSnake<br>
                           CataLatas and Cooper Harasyn for png2fts<br>
                           Phoenixbound for .fts documentation<br>
                           Tomato and null for EB fonts<br>
                           And to everyone on the forum and Discord!"""))

        form.addRow(HSeparator())
        form.addRow(QLabel("""<span style=font-family:Onett;font-size:20px>
                           <span style=color:#F80858>Change</span><span style=color:#9070F0>log</span></span>"""))
        changelogText = QTextEdit()
        changelogText.setReadOnly(True)
        changelogText.setPlainText(common.CHANGELOG)
        form.addRow(changelogText)

        # use EBMain for quotes, as they have < > and stuff which only works there
        quote, saturn = quotes.getRandomQuote()
        if saturn:
            quoteLabel = QLabel(f'<span style=font-size:20px;>{quote}</span>')
            quoteLabel.setStyleSheet('font-family:"Saturn Boing"') # font names with spaces need to go like this..?
        else:
            quoteLabel = QLabel(f'<span style=font-family:EBMain;font-size:20px>{quote}</span>')
        quoteLabel.setWordWrap(True)
        form.addRow(quoteLabel)
            
    @staticmethod
    def showAbout(parent):
        """Show the about dialog"""
        try:
            dialog = AboutDialog(parent)
            dialog.exec()
        except Exception as e:
            logging.warning(f"Error showing about dialog: {str(e)}")
            return False
        
class EBMELicenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("EBME Unlicense")
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        file = QFile(":/misc/LICENSE")
        file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text)
        label = QLabel(file.readAll().data().decode())
        label.setTextFormat(Qt.TextFormat.MarkdownText)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        label.setOpenExternalLinks(True)
        label.setWordWrap(True)
        layout.addWidget(label)
        
        closeButton = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        closeButton.rejected.connect(self.accept)
        layout.addWidget(closeButton)
        
    @staticmethod
    def showLicense(parent):
        dialog = EBMELicenseDialog(parent)
        return dialog.exec()
    
class png2ftsLicenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("png2fts License")
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        with open(common.absolutePath("eb-png2fts/LICENSE")) as f:
            layout.addWidget(QLabel(f.read()))
        
        closeButton = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        closeButton.rejected.connect(self.accept)
        layout.addWidget(closeButton)
        
    @staticmethod
    def showLicense(parent):
        dialog = png2ftsLicenseDialog(parent)
        return dialog.exec()


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        
        self.setWindowTitle("Settings")
        
        self.settings = QSettings()
        self.setupUI()
        self.fromSettings()

    def setupUI(self):
        self.generalBox = QGroupBox("General")
        self.generalLayout = QFormLayout()
        self.generalBox.setLayout(self.generalLayout)
        
        self.loadLastProject = QCheckBox("")
        self.noCtrlZoom = QCheckBox("")
        self.absolutePaste = QCheckBox("")
        self.generalLayout.addRow("Load most recent project on startup:", self.loadLastProject)
        self.generalLayout.addRow("Zoom without holding Ctrl:", self.noCtrlZoom)
        self.generalLayout.addRow("Paste NPCs and triggers at original locations:", self.absolutePaste)
        
        self.personalisationBox = QGroupBox("Personalisation")
        self.personalisationLayout = QFormLayout()
        self.personalisationBox.setLayout(self.personalisationLayout)
    
        self.applicationTheme = QComboBox()
        for i in QStyleFactory.keys():
            self.applicationTheme.addItem(i)
        self.applicationTheme.addItem("EarthBound")
        self.personalisationLayout.addRow("Application theme:", self.applicationTheme)
        self.personalisationLayout.addWidget(QLabel("Restart to apply themes."))

        self.smoothGoto = QComboBox()
        self.smoothGoto.addItems(["Enabled",
                                 "Enabled for short distances",
                                 "Disabled"])
        self.personalisationLayout.addRow("Smooth go to:", self.smoothGoto)
        self.personalisationLayout.addWidget(QLabel("Change this if you experience performance issues when using go-to features."))

        self.defaultProgramsBox = QGroupBox("Default programs")
        self.defaultProgramsLayout = QFormLayout()
        self.defaultProgramsBox.setLayout(self.defaultProgramsLayout)

        self.textEditorSetterLayout = QHBoxLayout()
        self.textEditorCommand = QLineEdit()
        self.textEditorCommand.setPlaceholderText("(Auto)")
        self.textEditorHint = QLabel("Use %F to represent the file path and %L to represent the line number.")
        self.textEditorClear = QPushButton("Use default")
        self.textEditorClear.clicked.connect(lambda: self.textEditorCommand.setText(""))
        self.textEditorSetterLayout.addWidget(self.textEditorCommand)
        self.textEditorSetterLayout.addWidget(self.textEditorClear)

        # self.imageEditorSetterLayout = QHBoxLayout()
        # self.imageEditorCommand = QLineEdit()
        # self.imageEditorCommand.setPlaceholderText("(Auto)")
        # self.imageEditorHint = QLabel("Use %F to represent the file path.")
        # self.imageEditorClear = QPushButton("Use default")
        # self.imageEditorClear.clicked.connect(lambda: self.imageEditorCommand.setText(""))
        # self.imageEditorSetterLayout.addWidget(self.imageEditorCommand)
        # self.imageEditorSetterLayout.addWidget(self.imageEditorClear)

        self.png2ftsSetterLayout = QHBoxLayout()
        self.png2ftsLabel = QLineEdit()
        self.png2ftsLabel.setPlaceholderText("(Use bundled)")
        self.png2ftsPath = QPushButton("Browse...")
        self.png2ftsPath.clicked.connect(self.browsepng2ftsPath)
        self.png2ftsClear = QPushButton("Use default")
        self.png2ftsClear.clicked.connect(lambda: self.png2ftsLabel.setText(""))
        self.png2ftsSetterLayout.addWidget(self.png2ftsLabel)
        self.png2ftsSetterLayout.addWidget(self.png2ftsPath)
        self.png2ftsSetterLayout.addWidget(self.png2ftsClear)

        self.saveCancelLayout = QHBoxLayout()
        self.saveButton = QPushButton("Save")
        self.saveButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.saveButton.clicked.connect(self.saveAndClose)
        self.cancelButton = QPushButton("Cancel")
        self.saveButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.cancelButton.clicked.connect(self.close)
        self.saveCancelLayout.addWidget(self.saveButton)
        self.saveCancelLayout.addWidget(self.cancelButton)
        self.saveCancelLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.defaultProgramsLayout.addRow("CCScript editor command:", self.textEditorSetterLayout)
        self.defaultProgramsLayout.addWidget(self.textEditorHint)
        # self.defaultProgramsLayout.addRow(HSeparator())
        # self.defaultProgramsLayout.addRow("Image editor command:", self.imageEditorSetterLayout)
        # self.defaultProgramsLayout.addWidget(self.imageEditorHint)
        # self.defaultProgramsLayout.addRow(HSeparator())
        self.defaultProgramsLayout.addRow("png2fts path:", self.png2ftsSetterLayout)
        self.defaultProgramsLayout.addWidget(QLabel("You must use a version of png2fts that supports map output (-m)."))

        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.generalBox)
        self.mainLayout.addWidget(self.personalisationBox)
        self.mainLayout.addWidget(self.defaultProgramsBox)
        self.mainLayout.addLayout(self.saveCancelLayout)
        self.setLayout(self.mainLayout)

    def fromSettings(self):
        self.loadLastProject.setChecked(not(self.settings.value("main/disableLoadLast", False, type=bool)))
        self.noCtrlZoom.setChecked(self.settings.value("main/noCtrlZoom", False, type=bool))
        self.absolutePaste.setChecked(self.settings.value("main/absolutePaste", False, type=bool))
        self.applicationTheme.setCurrentText(self.settings.value("personalisation/applicationTheme", QApplication.style().objectName(), type=str))
        self.smoothGoto.setCurrentText(self.settings.value("personalisation/smoothGoto", "Always enabled", type=str))
        self.textEditorCommand.setText(self.settings.value("programs/textEditorCommand", ""))
        # self.imageEditorCommand.setText(self.settings.value("programs/imageEditorCommand", ""))
        self.png2ftsLabel.setText(self.settings.value("programs/png2fts", ""))

    def toSettings(self):
        self.settings.setValue("main/disableLoadLast", not(self.loadLastProject.isChecked()))
        self.settings.setValue("main/noCtrlZoom", self.noCtrlZoom.isChecked())
        self.settings.setValue("main/absolutePaste", self.absolutePaste.isChecked())
        
        self.settings.setValue("personalisation/applicationTheme", self.applicationTheme.currentText())
        self.settings.setValue("personalisation/smoothGoto", self.smoothGoto.currentText())
        
        self.settings.setValue("programs/textEditorCommand", self.textEditorCommand.text())

        # command = self.imageEditorCommand.text()
        # self.settings.setValue("programs/imageEditorCommand", command)

        path = self.png2ftsLabel.text()
        if path != "":
            self.settings.setValue("programs/png2fts", path)
        else: self.settings.setValue("programs/png2fts", "")


    def browsepng2ftsPath(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select png2fts.py", "", "Python Source File (*.py)")
        if path:
            self.png2ftsLabel.setText(path)
            
    def saveAndClose(self):
        self.toSettings()
        self.accept()

    @staticmethod
    def openSettings(parent=None):
        settings = SettingsDialog(parent)
        settings.exec_()
        
class RenderMapDialog(QDialog):
    def __init__(self, parent, scene: "MapEditorScene", x1=0, y1=0, x2=0, y2=0, immediate=False):
        super().__init__(parent)
        
        self.setWindowTitle("Render Map")
        self.scene = scene
        
        self.form = QFormLayout(self)
        
        self.renderStartPos = CoordsInput()
        self.renderStartPos.x.setRange(0, common.EBMAPWIDTH-1)
        self.renderStartPos.y.setRange(0, common.EBMAPHEIGHT-1)
        self.renderEndPos = CoordsInput()
        self.renderEndPos.x.setRange(0, common.EBMAPWIDTH-1)
        self.renderEndPos.y.setRange(0, common.EBMAPHEIGHT-1)
        
        self.renderCancelWidget = QWidget()
        self.renderCancelLayout = QHBoxLayout()
        self.renderButton = QPushButton("Render")
        self.renderButton.clicked.connect(self.renderImage)
        self.renderCancelLayout.addWidget(self.renderButton)

        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.reject)
        self.renderCancelLayout.addWidget(self.cancelButton)
        self.renderCancelWidget.setLayout(self.renderCancelLayout)
        
        self.preview = QGroupBox("Output")
        self.previewLayout = QHBoxLayout()
        self.previewScrollArea = QScrollArea()
        self.previewImage = QLabel("Render an image")
        self.previewScrollArea.setWidget(self.previewImage)
        self.previewLayout.addWidget(self.previewScrollArea)
        self.preview.setLayout(self.previewLayout)
        
        self.saveButton = QPushButton("Save")
        self.saveButton.clicked.connect(self.saveImage)
        self.saveButton.setDisabled(True)
        
        self.renderStartPos.x.setValue(x1)
        self.renderStartPos.y.setValue(y1)
        self.renderEndPos.x.setValue(x2)
        self.renderEndPos.y.setValue(y2)
        
        self.form.addRow(QLabel("Adjust shown objects in the map editor before rendering."))
        self.form.addRow("Top-left", self.renderStartPos)
        self.form.addRow("Bottom-right", self.renderEndPos)
        self.form.addRow(self.renderCancelWidget)
        self.form.addRow(self.preview)
        self.form.addRow(self.saveButton)
        
        self.setLayout(self.form)
        
        self.resize(500, 500)
        
        if immediate:
            self.renderImage()
        
    def renderImage(self):
        # if they're equal, make the end one pixel bigger
        if self.renderEndPos.x.value() == self.renderStartPos.x.value():
            self.renderEndPos.x.setValue(self.renderEndPos.x.value() + 1)
        
        if self.renderEndPos.y.value() == self.renderStartPos.y.value():
            self.renderEndPos.y.setValue(self.renderEndPos.y.value() + 1)
            
        # if both are the size of the whole map, make the start one pixel smaller
        if self.renderStartPos.x.value() == common.EBMAPWIDTH-1 and self.renderEndPos.x.value() == common.EBMAPWIDTH-1:
            self.renderStartPos.x.setValue(self.renderStartPos.x.value()-1)
        if self.renderStartPos.y.value() == common.EBMAPHEIGHT-1 and self.renderEndPos.y.value() == common.EBMAPHEIGHT-1:
            self.renderStartPos.y.setValue(self.renderStartPos.y.value()-1)     
            
        # flip them if they're in the wrong order
        if self.renderEndPos.x.value() < self.renderStartPos.x.value():
            end = self.renderEndPos.x.value()
            start = self.renderStartPos.x.value()
            self.renderStartPos.x.setValue(end)
            self.renderEndPos.x.setValue(start)
        
        if self.renderEndPos.y.value() < self.renderStartPos.y.value():
            end = self.renderEndPos.y.value()
            start = self.renderStartPos.y.value()
            self.renderStartPos.y.setValue(end)
            self.renderEndPos.y.setValue(start)       
        
        rect = QRectF(self.renderStartPos.x.value(), self.renderStartPos.y.value(),
                      self.renderEndPos.x.value() - self.renderStartPos.x.value(),
                      self.renderEndPos.y.value() - self.renderStartPos.y.value())
        
        image = QImage(rect.width(), rect.height(), QImage.Format.Format_ARGB32)
        painter = QPainter(image)
        
        self.scene.render(painter, image.rect(), rect)
        painter.end()
        
        self.previewImage = QLabel()
        self.previewImage.setPixmap(QPixmap.fromImage(image))
        self.previewScrollArea.setWidget(self.previewImage)
        
        self.saveButton.setDisabled(False)
    
    def saveImage(self):
        dir, _ = QFileDialog.getSaveFileName(self, "Save image", "", "PNG Image (*.png)")
        if dir:
            self.previewImage.pixmap().save(common.normaliseFileExtension(dir, "png"), "PNG")
        
    @staticmethod
    def renderMap(parent=None, scene=QGraphicsScene, x1=0, y1=0, x2=0, y2=0, immediate=False):
        dialog = RenderMapDialog(parent, scene, x1, y1, x2, y2, immediate)
        dialog.exec_()

class RenderTilesDialog(QDialog):
    def __init__(self, parent, tileset: FullTileset, palette: Palette):
        super().__init__(parent)
        self.setWindowTitle("Render Tiles")
        self.tileset = tileset
        self.paletteObj = palette # conflicts with qwidget method
        form = QFormLayout()
        self.setLayout(form)
        
        self.renderRows = QSpinBox()
        self.renderRows.setMinimum(1)
        self.renderRows.setMaximum(960)
        self.renderRows.setValue(30)
        
        form.addRow("Rows", self.renderRows)
        
        self.renderWithGaps = QCheckBox()
        form.addRow("Gap between tiles", self.renderWithGaps)
        
        self.renderCancelWidget = QWidget()
        self.renderCancelLayout = QHBoxLayout()
        self.renderButton = QPushButton("Render")
        self.renderButton.clicked.connect(self.renderImage)
        self.renderCancelLayout.addWidget(self.renderButton)

        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.reject)
        self.renderCancelLayout.addWidget(self.cancelButton)
        self.renderCancelWidget.setLayout(self.renderCancelLayout)
        
        form.addRow(self.renderCancelWidget)
        
        self.preview = QGroupBox("Output")
        self.previewLayout = QHBoxLayout()
        self.previewScrollArea = QScrollArea()
        self.previewImage = QLabel("Render an image")
        self.previewScrollArea.setWidget(self.previewImage)
        self.previewLayout.addWidget(self.previewScrollArea)
        self.preview.setLayout(self.previewLayout)
        
        form.addRow(self.preview)
        
        self.saveButton = QPushButton("Save")
        self.saveButton.clicked.connect(self.saveImage)
        self.saveButton.setDisabled(True)
        
        form.addRow(self.saveButton)
    
    def renderImage(self):
        h = self.renderRows.value()
        w = ceil(960/self.renderRows.value())
        gaps = self.renderWithGaps.isChecked()
        
        image = QImage(w*32+(gaps*w), h*32+(gaps*h), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        
        for id, tile in enumerate(self.tileset.tiles):
            x = id % w
            y = id // w
            painter.drawImage(x*32+(gaps*x), y*32+(gaps*y), ImageQt.ImageQt(tile.toImage(self.paletteObj, self.tileset)))
        
        painter.end()
        
        self.previewImage = QLabel()
        self.previewImage.setPixmap(QPixmap.fromImage(image))
        self.previewScrollArea.setWidget(self.previewImage)
        
        self.saveButton.setDisabled(False)
    
    def saveImage(self):
        dir, _ = QFileDialog.getSaveFileName(self, "Save image", "", "PNG Image (*.png)")
        if dir:
            self.previewImage.pixmap().save(common.normaliseFileExtension(dir, "png"), "PNG")
    
    @staticmethod
    def renderTiles(parent, tileset: FullTileset, palette: Palette):
        dialog = RenderTilesDialog(parent, tileset, palette)
        dialog.exec_()
        
class RenderMinitilesDialog(QDialog):
    def __init__(self, parent, tileset: FullTileset, subpalette: Subpalette):
        super().__init__(parent)
        self.setWindowTitle("Render Minitiles")
        self.tileset = tileset
        self.subpalette = subpalette
        form = QFormLayout()
        self.setLayout(form)
        
        self.renderRows = QSpinBox()
        self.renderRows.setMinimum(1)
        self.renderRows.setMaximum(512)
        self.renderRows.setValue(16)
        
        form.addRow("Rows", self.renderRows)
        
        self.renderWithGaps = QCheckBox()
        form.addRow("Gap between minitiles", self.renderWithGaps)
        
        self.renderCancelWidget = QWidget()
        self.renderCancelLayout = QHBoxLayout()
        self.renderButton = QPushButton("Render")
        self.renderButton.clicked.connect(self.renderImage)
        self.renderCancelLayout.addWidget(self.renderButton)

        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.reject)
        self.renderCancelLayout.addWidget(self.cancelButton)
        self.renderCancelWidget.setLayout(self.renderCancelLayout)
        
        form.addRow(self.renderCancelWidget)
        
        self.preview = QGroupBox("Output")
        self.previewLayout = QHBoxLayout()
        self.previewScrollArea = QScrollArea()
        self.previewImage = QLabel("Render an image")
        self.previewScrollArea.setWidget(self.previewImage)
        self.previewLayout.addWidget(self.previewScrollArea)
        self.preview.setLayout(self.previewLayout)
        
        form.addRow(self.preview)
        
        self.saveButton = QPushButton("Save")
        self.saveButton.clicked.connect(self.saveImage)
        self.saveButton.setDisabled(True)
        
        form.addRow(self.saveButton)
    
    def renderImage(self):
        h = self.renderRows.value()
        w = ceil(512/self.renderRows.value())
        gaps = self.renderWithGaps.isChecked()
        
        image = QImage(w*8+(gaps*w), h*8+(gaps*h), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        
        for id, minitile in enumerate(self.tileset.minitiles):
            x = id % w
            y = id // w
            painter.drawImage(x*8+(gaps*x), y*8+(gaps*y), ImageQt.ImageQt(minitile.BothToImage(self.subpalette)))
        
        painter.end()
        
        self.previewImage = QLabel()
        self.previewImage.setPixmap(QPixmap.fromImage(image))
        self.previewScrollArea.setWidget(self.previewImage)
        
        self.saveButton.setDisabled(False)
    
    def saveImage(self):
        dir, _ = QFileDialog.getSaveFileName(self, "Save image", "", "PNG Image (*.png)")
        if dir:
            self.previewImage.pixmap().save(common.normaliseFileExtension(dir, "png"), "PNG")
    
    @staticmethod
    def renderMinitiles(parent, tileset: FullTileset, subpalette: Subpalette):
        dialog = RenderMinitilesDialog(parent, tileset, subpalette)
        dialog.exec_()
        
class RenderPaletteDialog(QDialog):
    def __init__(self, parent, palette: Palette):
        super().__init__(parent)
        self.setWindowTitle("Render Palette")
        self.paletteObj = palette # conflicts with qwidget method
        form = QFormLayout()
        self.setLayout(form)
        
        self.renderColourSize = QSpinBox()
        self.renderColourSize.setMinimum(1)
        self.renderColourSize.setMaximum(64)
        self.renderColourSize.setValue(8)
        form.addRow("Colour size", self.renderColourSize)
        
        self.renderWithGaps = QCheckBox()
        form.addRow("Gap between colours", self.renderWithGaps)
        
        self.renderCancelWidget = QWidget()
        self.renderCancelLayout = QHBoxLayout()
        self.renderButton = QPushButton("Render")
        self.renderButton.clicked.connect(self.renderImage)
        self.renderCancelLayout.addWidget(self.renderButton)

        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.reject)
        self.renderCancelLayout.addWidget(self.cancelButton)
        self.renderCancelWidget.setLayout(self.renderCancelLayout)
        
        form.addRow(self.renderCancelWidget)
        
        self.preview = QGroupBox("Output")
        self.previewLayout = QHBoxLayout()
        self.previewScrollArea = QScrollArea()
        self.previewImage = QLabel("Render an image")
        self.previewScrollArea.setWidget(self.previewImage)
        self.previewLayout.addWidget(self.previewScrollArea)
        self.preview.setLayout(self.previewLayout)
        
        form.addRow(self.preview)
        
        self.saveButton = QPushButton("Save")
        self.saveButton.clicked.connect(self.saveImage)
        self.saveButton.setDisabled(True)
        
        form.addRow(self.saveButton)
    
    def renderImage(self):
        colourSize = self.renderColourSize.value()
        h = 6
        w = 16
        gaps = self.renderWithGaps.isChecked()
        
        image = QImage(w*colourSize+(gaps*w), h*colourSize+(gaps*h), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        painter.setPen(Qt.PenStyle.NoPen)
        
        for y, subpal in enumerate(self.paletteObj.subpalettes):
            for x, colour in enumerate(subpal.subpaletteRGBA):
                painter.setBrush(QColor.fromRgb(*colour[:3])) # no alpha on first index
                painter.drawRect(x*colourSize+(gaps*x), y*colourSize+(gaps*y), colourSize, colourSize)
        
        painter.end()
        
        self.previewImage = QLabel()
        self.previewImage.setPixmap(QPixmap.fromImage(image))
        self.previewScrollArea.setWidget(self.previewImage)
        
        self.saveButton.setDisabled(False)
    
    def saveImage(self):
        dir, _ = QFileDialog.getSaveFileName(self, "Save image", "", "PNG Image (*.png)")
        if dir:
            self.previewImage.pixmap().save(common.normaliseFileExtension(dir, "png"), "PNG")
    
    @staticmethod
    def renderPalette(parent, palette: Palette):
        dialog = RenderPaletteDialog(parent, palette)
        dialog.exec_()
        
        
class ClearDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        
        layout = QVBoxLayout()
        
        self.setWindowTitle("Clear map")
        
        self.clearTiles = QCheckBox("Clear tiles")
        self.clearSectors = QCheckBox("Clear sector properties")
        self.clearNPCs = QCheckBox("Clear NPCs")
        self.clearTriggers = QCheckBox("Clear triggers")
        self.clearEnemies = QCheckBox("Clear enemies")
        
        self.buttons = QDialogButtonBox(Qt.Orientation.Horizontal)
        self.buttons.addButton(QDialogButtonBox.StandardButton.Apply)
        self.buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        
        self.buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.clearTiles)
        layout.addWidget(self.clearSectors)
        layout.addWidget(self.clearNPCs)
        layout.addWidget(self.clearTriggers)
        layout.addWidget(self.clearEnemies)
        layout.addWidget(self.buttons)
        
        self.setLayout(layout)
        
    @staticmethod
    def clearMap(parent=None):
        dialog = ClearDialog(parent)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            return {"tiles": dialog.clearTiles.isChecked(),
                    "sectors": dialog.clearSectors.isChecked(),
                    "npcs": dialog.clearNPCs.isChecked(),
                    "triggers": dialog.clearTriggers.isChecked(),
                    "enemies": dialog.clearEnemies.isChecked()}
            
        else:
            return False
        
class PresetEditorDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Editing Collision Preset")
        
        layout = QFormLayout()
        self.setLayout(layout)
        
        self.name = QLineEdit()
        layout.addRow("Preset name", self.name)
        
        self.checkboxes: list[QCheckBox] = []
        self.checkboxes.append(QCheckBox("Solid"))
        self.checkboxes.append(QCheckBox("Unused 1 (acts solid)"))
        self.checkboxes.append(QCheckBox("Unused 2 (no effect)"))
        self.checkboxes.append(QCheckBox("Supports triggers"))
        self.checkboxes.append(QCheckBox("Water"))
        self.checkboxes.append(QCheckBox("Damage"))
        self.checkboxes.append(QCheckBox("Mask top half of sprites"))
        self.checkboxes.append(QCheckBox("Mask bottom half of sprites"))
        for i in self.checkboxes: 
            i.toggled.connect(self.calculateHex)
            layout.addRow(i)
        
        self.colourButton = ColourButton()
        layout.addRow("Display colour", self.colourButton)
        
        self.hexInput = QSpinBox()
        self.hexInput.setDisplayIntegerBase(16)
        self.hexInput.setPrefix("0x")
        self.hexInput.setMaximum(common.BYTELIMIT)
        self.hexInput.setMinimum(0)
        self.hexInput.valueChanged.connect(self.calculateCheckboxes)
        layout.addRow("Raw value", self.hexInput)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)
        
    def calculateHex(self):
        self.hexInput.blockSignals(True)
        value = 0
        for i in range(8):
            checkbox = self.checkboxes[7-i]
            if checkbox.isChecked():
                value += 1 << i
        self.hexInput.setValue(value)
        self.hexInput.blockSignals(False)
        
    def calculateCheckboxes(self):
        value = self.hexInput.value()
        for i in range(8):
            checkbox = self.checkboxes[7-i]
            checkbox.blockSignals(True)
            if value & 1 << i:
                checkbox.setChecked(True)
            else:
                checkbox.setChecked(False)
            checkbox.blockSignals(False)
             
    @staticmethod
    def editPreset(parent, presetName: str, presetColour: QColor, presetValue: int):
        dialog = PresetEditorDialog(parent)
        dialog.hexInput.setValue(presetValue)
        dialog.name.setText(presetName)
        dialog.colourButton.setColour(presetColour)
        
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            return (dialog.name.text(), dialog.colourButton.chosenColour, dialog.hexInput.value())      

class AutoMinitileRearrangerDialog(QDialog):
    def __init__(self, parent, projectData: ProjectData):
        super().__init__(parent)
        self.setWindowTitle("Auto Minitile Rearranger")
        self.projectData = projectData
        
        layout = QFormLayout()
        self.setLayout(layout)
        
        label = QLabel("Automatically rearrange minitile order in a tileset to ensure that tiles with foreground graphics are able to use them.\n(Can be undone.)")
        label.setWordWrap(True)
        layout.addRow(label)
        
        self.tilesetInput = QSpinBox()
        self.tilesetInput.setMaximum(len(self.projectData.tilesets)-1)
        layout.addRow("Tileset", self.tilesetInput)
        
        self.buttons = QDialogButtonBox()
        self.buttons.addButton(QDialogButtonBox.StandardButton.Apply)
        self.buttons.addButton(QDialogButtonBox.StandardButton.Close)
        
        self.buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.rearrange)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)
        
        self.action: MultiActionWrapper|None = None
        
    def rearrange(self):
        try:
            tileset = self.projectData.getTileset(self.tilesetInput.value())
            countWithFg = 0
            toMove: list[int] = []
            canBeReplaced: list[int] = []
            
            for id, minitile in enumerate(tileset.minitiles):
                raw = minitile.fgToRaw() 
                if raw != "0000000000000000000000000000000000000000000000000000000000000000":
                    countWithFg += 1
                    if id >= 384:
                        toMove.append(id)
                    
                elif raw == "0000000000000000000000000000000000000000000000000000000000000000"\
                and id < 384:
                    canBeReplaced.append(id)
                
            if countWithFg > 384:
                return common.showErrorMsg("Unable to rearrange minitiles",
                                        f"There are {countWithFg} minitiles with foreground graphics in this tileset. The maximum to be able to rearrange is 384.",
                                        icon = QMessageBox.Icon.Warning)
            
            # I've decided to reverse it for a few reasons:
            #   - minitile 0 should probably not be messed with first... i dont know the ramifications of that if any
            #   - this algorithm moves them out from the end so I guess it visually makes sense..?
            canBeReplaced = list(reversed(canBeReplaced))
            toMove = list(reversed(toMove))
                
            actions: list[ActionSwapMinitiles] = []
            for id, minitile in enumerate(toMove):
                actions.append(ActionSwapMinitiles(tileset, canBeReplaced[id], minitile))
            
            if len(actions) > 0:
                self.action = MultiActionWrapper(actions, "Auto rearrange minitiles")
            return self.accept()
        
        except Exception as e:
            logging.warning(traceback.format_exc())
            return common.showErrorMsg("Unable to rearrange minitiles",
                                       f"There was an issue when rearranging minitiles.",
                                       str(e))
    
    @staticmethod
    def rearrangeMinitiles(parent, projectData: ProjectData, initTileset: int|None=None):
        dialog = AutoMinitileRearrangerDialog(parent, projectData)
        if initTileset:
            dialog.tilesetInput.setValue(initTileset)
        dialog.exec()
        return dialog.action
        
        
class EditEventPaletteDialog(QDialog):
    def __init__(self, parent, palette: Palette, tileset: int, projectData: ProjectData):
        super().__init__(parent)
        
        self.setWindowTitle("Editing Event Palette")
        
        self.paletteCopy = Palette(palette.toRaw())
        self.projectData = projectData
        self.tileset = tileset
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.paletteSelector = PaletteSelector()
        self.paletteSelector.loadPalette(palette)
        self.paletteSelector.colourEdited.connect(self.onPaletteEdited)
        layout.addWidget(self.paletteSelector)
        
        self.tilesetDisplay = TilesetDisplayGraphicsScene(projectData, horizontal=True, forcedPalette=self.paletteCopy)
        self.tilesetDisplay.selectionIndicator.hide()
        self.tilesetDisplay.currentTileset = tileset
        self.tilesetDisplay.currentPaletteGroup = palette.groupID
        self.tilesetDisplay.currentPalette = palette.paletteID
        self.tilesetDisplayView = HorizontalGraphicsView(self.tilesetDisplay)
        self.tilesetDisplayView.setFixedHeight(self.tilesetDisplay.rowSize*32 + self.tilesetDisplayView.horizontalScrollBar().sizeHint().height())
        self.tilesetDisplayView.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.tilesetDisplayView.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tilesetDisplayView.centerOn(0, 0)
        
        layout.addWidget(self.tilesetDisplayView)
        
        self.buttons = QDialogButtonBox()
        self.buttons.addButton(QDialogButtonBox.StandardButton.Apply)
        self.buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        
        self.buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.buttons)
        
    def onPaletteEdited(self, subpalette: int, index: int):
        ActionChangeSubpaletteColour(self.paletteCopy.subpalettes[subpalette], index,
                                    self.paletteSelector.buttons[subpalette][index].chosenColour.toTuple()[:3]
                                    ).redo()
        
        for i in self.projectData.getTileset(self.tileset).minitiles:
            i.BothToImage.cache_clear()
            
        self.tilesetDisplay.forcedPaletteCache = {}
        self.tilesetDisplay.update()
    
    @staticmethod
    def editEventPalette(parent, palette: Palette, tileset: int, projectData: ProjectData):
        dialog = EditEventPaletteDialog(parent, palette, tileset, projectData)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            actions = []
            for subpalette in range(0, 6):
                for colour in range(0, 16):
                    action = ActionChangeSubpaletteColour(palette.subpalettes[subpalette], colour,
                                dialog.paletteSelector.buttons[subpalette][colour].chosenColour.toTuple()[:3])
                    if not action.isObsolete():
                        actions.append(action)
            
            if len(actions) > 0:
                return MultiActionWrapper(actions, "Edit event palette")

class CopyEventPaletteDialog(QDialog):
    def __init__(self, parent, palette: Palette, projectData: ProjectData):
        super().__init__(parent)
        self.setWindowTitle("Copy Palette to Event Palette")
        self.projectData = projectData
        
        layout = QVBoxLayout()
        contentLayout = QHBoxLayout()
        layout.addLayout(contentLayout)
        self.setLayout(layout)
        
        self.currentPalette: Palette = None
        
        self.copyFromSelector = PaletteTreeWidget(projectData)
        self.copyFromSelector.currentItemChanged.connect(self.onSelectorCurrentItemChanged)
        contentLayout.addWidget(self.copyFromSelector)
        
        compareLayout = QVBoxLayout()
        
        compareLayout.addWidget(IconLabel("Copying from this palette", icons.ICON_EXPORT))
        self.copyFromPaletteSelector = PaletteSelector()
        self.copyFromPaletteSelector.setViewOnly(True)
        self.copyFromPaletteSelector.setDisabled(True)
        compareLayout.addWidget(self.copyFromPaletteSelector)
        
        labelLayout = QHBoxLayout()
        labelLayout.addStretch()
        labelLayout.addWidget(IconLabel(icon=icons.ICON_DOWN))
        compareLayout.addLayout(labelLayout)
        
        compareLayout.addWidget(IconLabel("Overwriting this event palette", icons.ICON_IMPORT))
        self.copyToPaletteSelector = PaletteSelector()
        self.copyToPaletteSelector.loadPalette(palette)
        self.copyToPaletteSelector.setViewOnly(True)
        compareLayout.addWidget(self.copyToPaletteSelector)
        
        contentLayout.addLayout(compareLayout)
        
        self.buttons = QDialogButtonBox()
        self.buttons.addButton(QDialogButtonBox.StandardButton.Apply)
        self.buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        self.buttons.button(QDialogButtonBox.StandardButton.Apply).setDisabled(True)
        
        self.buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.buttons)
        
    def onSelectorCurrentItemChanged(self, new):
        if isinstance(new, SubpaletteListItem):
            new = new.parent()
            
        if isinstance(new, PaletteListItem):
            self.currentPalette = self.projectData.getTileset(new.parent().parent().tileset).getPalette(
                new.parent().paletteGroup,
                new.palette
            )
            self.copyFromPaletteSelector.setEnabled(True)
            self.copyFromPaletteSelector.loadPalette(self.currentPalette)
            self.buttons.button(QDialogButtonBox.StandardButton.Apply).setEnabled(True)
            
        else:
            self.copyFromPaletteSelector.setDisabled(True)
            self.buttons.button(QDialogButtonBox.StandardButton.Apply).setEnabled(False)
            
    def accept(self):
        if not self.currentPalette:
            return
        return super().accept()
        
    @staticmethod
    def copyEventPalette(parent, palette: Palette, projectData: ProjectData):
        dialog = CopyEventPaletteDialog(parent, palette, projectData)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return ActionReplacePalette(dialog.copyFromPaletteSelector.currentPalette, palette)

class AdvancedPalettePreviewDialog(QDialog):
    def __init__(self, parent, projectData: ProjectData):
        super().__init__(parent)
        self.setWindowTitle("Advanced Palette Preview")
        self.projectData = projectData
        
        layout = QFormLayout()
        self.setLayout(layout)
        
        label = QLabel("Preview any tileset with any palette, regardless of in which tileset palette groups are located.\nCertain control codes allow any palette to be set in this way, such as in Magicant.")
        label.setWordWrap(True)
        layout.addRow(label)
        
        tilesetSelect = QComboBox()
        for i in range(len(self.projectData.tilesets)):
            tilesetSelect.addItem(str(i))
        tilesetSelect.currentIndexChanged.connect(self.onTilesetChange)
        layout.addRow("Tileset", tilesetSelect)
        
        layout.addRow(HSeparator())
        
        self.paletteGroupSelect = QComboBox()
        self.paletteGroups: list[PaletteGroup] = []
        for i in self.projectData.tilesets:
            for j in i.paletteGroups:
                self.paletteGroups.append(j)            
        # no lambda type hints :(
        self.paletteGroups.sort(key=lambda pg: pg.groupID)  
        for i in self.paletteGroups:
            self.paletteGroupSelect.addItem(str(i.groupID))
        self.paletteGroupSelect.currentIndexChanged.connect(self.onPaletteGroupChange)
        layout.addRow("Palette Group", self.paletteGroupSelect)
            
        self.paletteSelect = QComboBox()
        for i in self.paletteGroups[0].palettes:
            self.paletteSelect.addItem(str(i.paletteID))
        self.paletteSelect.currentIndexChanged.connect(self.onPaletteChange)
        layout.addRow("Palette", self.paletteSelect)
        
        initPalette = self.projectData.tilesets[0].paletteGroups[0].palettes[0]
        self.previewScene = TilesetDisplayGraphicsScene(self.projectData, True, 8, forcedPalette=initPalette)
        self.previewScene.selectionIndicator.hide()
        previewView = HorizontalGraphicsView(self.previewScene)
        previewView.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        previewView.setFixedHeight(self.previewScene.rowSize*32 + previewView.horizontalScrollBar().sizeHint().height())
        previewView.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        previewView.centerOn(0, 0)
        layout.addRow(previewView)
        
    def onTilesetChange(self, new: str):
        self.previewScene.currentTileset = int(new)
        self.previewScene.forcedPaletteCache = {}
        self.previewScene.update()
        
    def onPaletteGroupChange(self, new: str):
        self.paletteSelect.blockSignals(True)
        self.paletteSelect.clear()
        for i in self.paletteGroups[int(new)].palettes:
            self.paletteSelect.addItem(str(i.paletteID))
        self.paletteSelect.setCurrentIndex(0)
        self.paletteSelect.blockSignals(False)
        self.onPaletteChange(self.paletteSelect.currentText())
        
    def onPaletteChange(self, new: str):
        palette = self.paletteGroups[int(self.paletteGroupSelect.currentText())].palettes[int(new)]
        self.previewScene.forcedPalette = palette
        self.previewScene.forcedPaletteCache = {}
        self.previewScene.update()
        
        
    @staticmethod
    def advancedPalettePreview(parent, projectData: ProjectData):
        dialog = AdvancedPalettePreviewDialog(parent, projectData)
        dialog.exec()