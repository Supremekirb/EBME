from PySide6.QtWidgets import (QDialog, QFileDialog, QFormLayout, QHBoxLayout,
                               QLabel, QLineEdit, QMessageBox, QPushButton,
                               QSpinBox, QTextEdit, QVBoxLayout)

import src.misc.common as common
from src.coilsnake.project_data import ProjectData
from src.misc.dialogues import png2ftsLicenseDialog
from src.png2fts.ebme_png2fts import EBME_png2fts


class png2ftsMapEditorGui(QDialog):
    """Returns 0 if no conversion/cancel, 1 if conversion, QTemporaryFile if place on map"""
    def __init__(self, parent, projectData: ProjectData):
        QDialog.__init__(self, parent)

        self.setWindowTitle("Import PNG with png2fts")
        self.projectData = projectData
        self.success = False
        self.running = False

        self.setupUI()

        self.png2fts = EBME_png2fts(self)
        self.png2fts.succeeded.connect(self.onSuccess)
        self.png2fts.failed.connect(self.onFailure)
        self.png2fts.newOutput.connect(lambda x: self.output.append(x))

    def closeEvent(self, event):
        if not self.running: # dont close when executing png2fts
            if self.success:
                self.done(1)
            else:
                self.done(0)

    def convert(self):
        if not self.pngInput.text():
            return common.showErrorMsg("No input file",
                                       "No input file was specified",
                                       "You must specify a PNG file to import.",
                                       QMessageBox.Icon.Warning)
        
        if not QMessageBox.question(self, "Import PNG", "This will overwrite the selected tileset and cannot be undone. Continue?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            return
        
        self.output.setText("") # clear the output
        self.pngInput.setDisabled(True)
        self.pngBrowse.setDisabled(True)
        self.tilesetNumber.setDisabled(True)
        self.goButton.setDisabled(True)
        self.cancelButton.setDisabled(True)
        self.placeOnMapButton.setDisabled(True)
        
        self.running = True
        self.png2fts.convert(self.projectData, 
                             self.pngInput.text(),
                             int(self.tilesetNumber.text()))

    def onSuccess(self):
        self.running = False
        self.placeOnMapButton.setEnabled(True)
        self.doneButton.setEnabled(True)

        self.success = True
        
    def onFailure(self):
        self.running = False
        self.pngInput.setEnabled(True)
        self.pngBrowse.setEnabled(True)
        self.tilesetNumber.setEnabled(True)
        self.goButton.setEnabled(True)
        self.cancelButton.setEnabled(True)

    def setupUI(self):
        self.disclaimer = QLabel("png2fts support is still somewhat experimental.\nUse at your own risk!")

        self.pngInputLayout = QHBoxLayout()
        self.pngInput = QLineEdit()
        self.pngInput.setPlaceholderText("Path to PNG file")
        self.pngBrowse = QPushButton("Browse...")
        self.pngBrowse.clicked.connect(self.pngBrowseClicked)
        self.pngInputLayout.addWidget(self.pngInput)
        self.pngInputLayout.addWidget(self.pngBrowse)

        self.tilesetNumber = QSpinBox()
        self.tilesetNumber.setRange(0, len(self.projectData.tilesets)-1)

        self.goCancelLayout = QHBoxLayout()
        self.goButton = QPushButton("Go")
        self.goButton.clicked.connect(self.convert)
        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.close)
        self.goCancelLayout.addWidget(self.goButton)
        self.goCancelLayout.addWidget(self.cancelButton)

        self.outputLabel = QLabel("Output")
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        self.placeOnMapButton = QPushButton("Place on map")
        self.placeOnMapButton.clicked.connect(lambda: self.done(2))
        self.placeOnMapButton.setDisabled(True)

        self.doneButton = QPushButton("Done")
        self.doneButton.clicked.connect(lambda: self.done(1))
        self.doneButton.setDisabled(True)

        self.credits = QLabel("png2fts by CataLatas & Cooper Harasyn (cooprocks123e)")
        self.openLicenseButton = QPushButton("View license...")
        self.openLicenseButton.clicked.connect(lambda: png2ftsLicenseDialog.showLicense(self))

        layout = QVBoxLayout()
        formLayout = QFormLayout()
        formLayout.addRow(self.disclaimer)
        formLayout.addRow("Input file", self.pngInputLayout)
        formLayout.addRow("Tileset to replace", self.tilesetNumber)
        formLayout.addRow(self.goCancelLayout)
        formLayout.addRow(self.outputLabel)
        formLayout.addRow(self.output)
        formLayout.addRow(self.placeOnMapButton)
        formLayout.addRow(self.doneButton)
        formLayout.addRow(self.credits)
        formLayout.addRow(self.openLicenseButton)

        layout.addLayout(formLayout)
        self.setLayout(layout)

    def pngBrowseClicked(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open PNG File", "", "PNG Files (*.png)")
        if path:
            self.pngInput.setText(path)

    @staticmethod # this so we can return the map file if we want
    def dopng2fts(parent, projectData: ProjectData) -> int | list:
        """Create a modal dialog to convert a PNG to a tileset using png2fts.

        Args:
            parent (QObject)
            projectData (ProjectData)

        Returns:
            int | list: 0 if no conversion/cancel, list[int of tileset] if successful, list[int of tileset, QTemporaryFile, str of map file] if place on map
        """
        dialog = png2ftsMapEditorGui(parent, projectData)
        dialog.exec()

        if dialog.result() == 1:
            return [dialog.tilesetNumber.value(),]
        if dialog.result() == 2:
            return [dialog.tilesetNumber.value(), dialog.png2fts.getMapFile(), dialog.pngInput.text()]
        
        
        else: return dialog.result()