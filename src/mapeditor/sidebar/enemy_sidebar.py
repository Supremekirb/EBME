from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QObject, QPoint, Signal
from PySide6.QtGui import QBrush, QColor, QIntValidator, QPixmap, Qt
from PySide6.QtWidgets import (QFormLayout, QGraphicsItem, QGraphicsPixmapItem,
                               QGraphicsRectItem, QGraphicsScene,
                               QGraphicsSimpleTextItem, QGraphicsView,
                               QGroupBox, QHBoxLayout, QHeaderView,
                               QItemDelegate, QLabel, QLineEdit, QSizePolicy,
                               QSpinBox, QTableWidget, QTableWidgetItem,
                               QTabWidget, QVBoxLayout, QWidget)

import src.misc.common as common
from src.actions.enemy_actions import ActionUpdateEnemyMapGroup
from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords
from src.misc.widgets import ColourButton, FlagInput

if TYPE_CHECKING:
    from mapeditor.map_editor import MapEditor, MapEditorState


WHITEBRUSH = QBrush(Qt.white)


class SidebarEnemy(QWidget):
    """Sidebar for enemy mode"""

    def __init__(self, mapeditor: "MapEditor", state: "MapEditorState", projectData: ProjectData):
        QWidget.__init__(self)
        self.mapeditor = mapeditor
        self.state = state
        self.projectData = projectData
        self.setupUI()
        
        self.fromEnemyTile()
        
    def selectEnemyTile(self, id: int):
        self.view.selectedIndicator.setPos((id%SidebarEnemyCanvas.tileWidth)*32, (id//SidebarEnemyCanvas.tileWidth)*32)
        self.view.centerOn(self.view.selectedIndicator)
        self.fromEnemyTile()
        
    # def fromSubGroupTable1(self, row, col):
    #     if col == 0:
    #         self.state.currentEnemyGroup = int(self.mapGroupSubGroup1Table.item(row, 0).text())
    #         self.fromEnemyGroup()
        
    # def fromSubGroupTable2(self, row, col):
    #     if col == 0:
    #         self.state.currentEnemyGroup = int(self.mapGroupSubGroup2Table.item(row, 0).text())
    #         self.fromEnemyGroup()
        
    def fromEnemyTile(self):
        self.mapGroupLabel.setText(f"Map Enemy Group {self.state.currentEnemyTile}")
        
        group = self.projectData.enemyMapGroups[self.state.currentEnemyTile]
        
        self.mapGroupEventFlag.blockSignals(True)
        self.mapGroupColour.blockSignals(True)
        self.mapGroupSubGroup1Rate.blockSignals(True)
        self.mapGroupSubGroup1Table.blockSignals(True)
        self.mapGroupSubGroup2Rate.blockSignals(True)
        self.mapGroupSubGroup2Table.blockSignals(True)
        
        self.mapGroupEventFlag.setValue(group.flag)
        self.mapGroupSubGroup1Rate.setValue(group.subGroup1Rate)
        self.mapGroupSubGroup2Rate.setValue(group.subGroup2Rate)
        
        self.mapGroupColour.setColour(QColor(*group.colour))
        
        for row in range(0, 7):
            try:
                entry = group.subGroup1[row]
                self.mapGroupSubGroup1Table.setItem(row, 0, QTableWidgetItem(str(entry["Enemy Group"])))
                self.mapGroupSubGroup1Table.setItem(row, 1, QTableWidgetItem(str(entry["Probability"])))
            except KeyError:
                self.mapGroupSubGroup1Table.setItem(row, 0, QTableWidgetItem("0"))
                self.mapGroupSubGroup1Table.setItem(row, 1, QTableWidgetItem("0"))
                
        for row in range(0, 7):
            try:
                entry = group.subGroup2[row]
                self.mapGroupSubGroup2Table.setItem(row, 0, QTableWidgetItem(str(entry["Enemy Group"])))
                self.mapGroupSubGroup2Table.setItem(row, 1, QTableWidgetItem(str(entry["Probability"])))
            except KeyError:
                self.mapGroupSubGroup2Table.setItem(row, 0, QTableWidgetItem("0"))
                self.mapGroupSubGroup2Table.setItem(row, 1, QTableWidgetItem("0"))
        
        self.mapGroupEventFlag.blockSignals(False)
        self.mapGroupColour.blockSignals(False)
        self.mapGroupSubGroup1Rate.blockSignals(False)
        self.mapGroupSubGroup1Table.blockSignals(False)
        self.mapGroupSubGroup2Rate.blockSignals(False)
        self.mapGroupSubGroup2Table.blockSignals(False)
        
        self.mapGroupBox.setEnabled(True)
        
    def toEnemyMapGroup(self):
        group = self.projectData.enemyMapGroups[self.state.currentEnemyTile]
        
        # build subgroups bc that SUCKS
        subGroup1 = {}
        for row in range(0, 7):
            if self.mapGroupSubGroup1Table.item(row, 0).text() == "0" and self.mapGroupSubGroup1Table.item(row, 1).text() == "0":
                continue
            else:
                subGroup1[row] = {
                    "Enemy Group": int(self.mapGroupSubGroup1Table.item(row, 0).text()),
                    "Probability": int(self.mapGroupSubGroup1Table.item(row, 1).text())
                }
        
        subGroup2 = {}
        for row in range(0, 7):
            if self.mapGroupSubGroup2Table.item(row, 0).text() == "0" and self.mapGroupSubGroup2Table.item(row, 1).text() == "0":
                continue
            else:
                subGroup2[row] = {
                    "Enemy Group": int(self.mapGroupSubGroup2Table.item(row, 0).text()),
                    "Probability": int(self.mapGroupSubGroup2Table.item(row, 1).text())
                }
            
        action = ActionUpdateEnemyMapGroup(group,
                                           self.mapGroupEventFlag.value(),
                                           self.mapGroupColour.chosenColour.toTuple(),
                                           subGroup1,
                                           subGroup2,
                                           self.mapGroupSubGroup1Rate.value(),
                                           self.mapGroupSubGroup2Rate.value())
        
        self.mapeditor.scene.undoStack.push(action)
        self.mapeditor.scene.refreshEnemyMapGroup(group.groupID)
        
        
    # def fromEnemyGroup(self):
    #     self.groupLabel.setText(f"Enemy Group {self.state.currentEnemyGroup}")
        
    #     group = self.projectData.enemyGroups[self.state.currentEnemyGroup]
        
    #     self.groupGroupBox.setEnabled(True)
        

    def validateTable1(self):
        total = 0
        for row in range(0, 7):
            contents = self.mapGroupSubGroup1Table.item(row, 1).text()
            total += int(contents) if contents != "" else 0
        
        if total != 8:
            self.mapGroupSubGroup1Warning.show()
        else:
            self.mapGroupSubGroup1Warning.hide()
            
    def validateTable2(self):
        # im so tired i cannot be bothered to write this better
        total = 0
        for row in range(0, 7):
            contents = self.mapGroupSubGroup2Table.item(row, 1).text()
            total += int(contents) if contents != "" else 0
        
        if total != 8:
            self.mapGroupSubGroup2Warning.show()
        else:
            self.mapGroupSubGroup2Warning.hide()
            
        
    def setupUI(self):
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 32*SidebarEnemyCanvas.tileWidth,
                                32*len(self.projectData.enemyMapGroups)//SidebarEnemyCanvas.tileWidth)
        
        self.layoutLeft = QVBoxLayout()
        self.view = SidebarEnemyCanvas(self, self.state, self.projectData, self.scene)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setFixedWidth((32*SidebarEnemyCanvas.tileWidth)+1+self.view.verticalScrollBar().sizeHint().width())
        self.view.centerOn(0, 0)
        self.layoutLeft.addWidget(self.view)

        self.mapGroupLabel = QLabel("Select a map enemy group to edit")
        
        self.mapGroupBox = QGroupBox("Map Enemy Group Data")
        self.mapGroupLayout = QFormLayout(self.mapGroupBox)
        self.mapGroupEventFlag = FlagInput(True)
        self.mapGroupEventFlag.valueChanged.connect(self.toEnemyMapGroup)
        self.mapGroupEventFlag.inverted.connect(self.toEnemyMapGroup)
        
        self.mapGroupColour = ColourButton()
        self.mapGroupColour.colourChanged.connect(self.toEnemyMapGroup)
        
        self.mapGroupEditorTabs = QTabWidget()
        
        self.mapGroupSubGroup1Widget = QWidget()
        self.mapGroupSubGroup1Layout = QFormLayout()
        self.mapGroupSubGroup1Table = QTableWidget(7, 2)
        self.mapGroupSubGroup1Table.setHorizontalHeaderLabels(["Group", "Weight"])
        self.mapGroupSubGroup1Table.setItemDelegateForColumn(0, SidebarEnemyGroupDelegate(self))
        self.mapGroupSubGroup1Table.setItemDelegateForColumn(1, SidebarEnemyProbablilityDelegate(self))
        self.mapGroupSubGroup1Table.itemChanged.connect(self.validateTable1)
        # self.mapGroupSubGroup1Table.currentCellChanged.connect(self.fromSubGroupTable1)
        self.mapGroupSubGroup1Table.cellChanged.connect(self.toEnemyMapGroup)
        self.mapGroupSubGroup1Table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.mapGroupSubGroup1Table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.mapGroupSubGroup1Table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.mapGroupSubGroup1Warning = QLabel("<span style='color:red'>WARNING - Weight must total 8</span>")
        self.mapGroupSubGroup1Warning.setWordWrap(True)
        self.mapGroupSubGroup1Warning.hide()
        self.mapGroupSubGroup1Rate = QSpinBox()
        self.mapGroupSubGroup1Rate.setMaximum(100)
        self.mapGroupSubGroup1Rate.setMinimum(0)
        self.mapGroupSubGroup1Rate.setSuffix("%")
        self.mapGroupSubGroup1Rate.valueChanged.connect(self.toEnemyMapGroup)
        
        self.mapGroupSubGroup1Layout.addRow("Spawn rate", self.mapGroupSubGroup1Rate)
        self.mapGroupSubGroup1Layout.addRow(self.mapGroupSubGroup1Warning)
        self.mapGroupSubGroup1Layout.addRow(self.mapGroupSubGroup1Table)
        self.mapGroupSubGroup1Widget.setLayout(self.mapGroupSubGroup1Layout)
        self.mapGroupEditorTabs.addTab(self.mapGroupSubGroup1Widget, "Subgroup 1")
        
        self.mapGroupSubGroup2Widget = QWidget()
        self.mapGroupSubGroup2Layout = QFormLayout()
        self.mapGroupSubGroup2Table = QTableWidget(7, 2)
        self.mapGroupSubGroup2Table.setHorizontalHeaderLabels(["Group", "Weight"])
        self.mapGroupSubGroup2Table.setItemDelegateForColumn(0, SidebarEnemyGroupDelegate(self))
        self.mapGroupSubGroup2Table.setItemDelegateForColumn(1, SidebarEnemyProbablilityDelegate(self))
        self.mapGroupSubGroup2Table.itemChanged.connect(self.validateTable2)
        # self.mapGroupSubGroup2Table.currentCellChanged.connect(self.fromSubGroupTable2)
        self.mapGroupSubGroup2Table.cellChanged.connect(self.toEnemyMapGroup)
        self.mapGroupSubGroup2Table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.mapGroupSubGroup2Table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.mapGroupSubGroup2Table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.mapGroupSubGroup2Warning = QLabel("<span style='color:red'>WARNING - Weight must total 8</span>")
        self.mapGroupSubGroup2Warning.setWordWrap(True)
        self.mapGroupSubGroup2Warning.hide()
        self.mapGroupSubGroup2Rate = QSpinBox()
        self.mapGroupSubGroup2Rate.setMaximum(100)
        self.mapGroupSubGroup2Rate.setMinimum(0)
        self.mapGroupSubGroup2Rate.setSuffix("%")
        self.mapGroupSubGroup2Rate.valueChanged.connect(self.toEnemyMapGroup)
        
        self.mapGroupSubGroup2Layout.addRow("Spawn rate", self.mapGroupSubGroup2Rate)
        self.mapGroupSubGroup2Layout.addRow(self.mapGroupSubGroup2Warning)
        self.mapGroupSubGroup2Layout.addRow(self.mapGroupSubGroup2Table)
        self.mapGroupSubGroup2Widget.setLayout(self.mapGroupSubGroup2Layout)
        self.mapGroupEditorTabs.addTab(self.mapGroupSubGroup2Widget, "Subgroup 2")
             
        self.mapGroupLayout.addRow("Flag", self.mapGroupEventFlag)
        self.mapGroupLayout.addRow("Colour", self.mapGroupColour)
        self.mapGroupLayout.addRow(self.mapGroupEditorTabs)
        
        self.layoutLeft.addWidget(self.mapGroupLabel)
        self.layoutLeft.addWidget(self.mapGroupBox)
        self.mapGroupBox.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        # self.layoutRight = QVBoxLayout()
        
        # self.groupLayout = QVBoxLayout()
        # self.groupLabel = QLabel("Select an enemy group to edit")
        # self.groupLabel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # self.groupGroupBox = QGroupBox("Enemy Group")
        # self.groupBoxLayout = QVBoxLayout(self.groupGroupBox)
        # self.groupLayout.addWidget(self.groupLabel)
        # self.groupLayout.addWidget(HSeparator())
        # self.groupLayout.addWidget(self.groupGroupBox)
        
        # self.layoutRight.addLayout(self.groupLayout, 2)

        self.contentLayout = QHBoxLayout(self)
        self.contentLayout.addLayout(self.layoutLeft, 2)
        # self.contentLayout.addLayout(self.layoutRight, 1)
        
        # self.mapGroupBox.setDisabled(True)
        # self.groupGroupBox.setDisabled(True)
        
        self.setLayout(self.contentLayout)

    # for typing
    def parent(self) -> "MapEditor":
        return super().parent()

# item delegate which allows only integers and limits the input to the size of the enemy group list
class SidebarEnemyGroupDelegate(QItemDelegate):
    def __init__(self, parent: SidebarEnemy):
        super().__init__(parent)
        
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        sizeLimit = len(self.parent().projectData.enemyGroups)
        
        editor.setValidator(QIntValidator(0, sizeLimit-1, editor))
        return editor
    
    def parent(self) -> SidebarEnemy:
        return super().parent()
    
# item delegate which allows only integers 0-8
class SidebarEnemyProbablilityDelegate(QItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)
    
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(QIntValidator(0, 8, editor))
        return editor
    
    
class SidebarEnemyCanvas(QGraphicsView):
    tileWidth = 7
    def __init__(self, parent: SidebarEnemy, state: "MapEditorState", projectData: ProjectData, scene: QGraphicsScene):
        super().__init__(parent)

        self.state = state
        self.projectData = projectData
        self.setScene(scene)

        for i in self.projectData.enemyMapGroups:
            placement = MiniEnemyTile(i.groupID,
                                      QBrush(QColor(*i.colour)),
                                      common.tileToPix(i.groupID%self.tileWidth),
                                      common.tileToPix(i.groupID//self.tileWidth))
            self.scene().addItem(placement)
            
        self.selectedIndicator = QGraphicsPixmapItem()
        self.selectedIndicator.setPixmap(QPixmap(":/ui/selectTile.png"))
        self.selectedIndicator.setZValue(255)
        self.scene().addItem(self.selectedIndicator)
        
        self.scene().setSceneRect(0, 0, (SidebarEnemyCanvas.tileWidth*32), (32*203)//SidebarEnemyCanvas.tileWidth)
        self.scene().installEventFilter(self)
        
    def ensureCorrectColour(self, groupID):
        items = self.scene().items(QPoint(common.tileToPix(groupID%self.tileWidth)+1, # little leeway since they do overlap
                                          common.tileToPix(groupID//self.tileWidth)+1)) # isn't this nice and slightly cursed?
        for i in items:
            if isinstance(i, MiniEnemyTile):
                i.setBrush(QBrush(QColor(*self.projectData.enemyMapGroups[groupID].colour)))
        
    def eventFilter(self, object: QObject, event: QEvent):
        if event.type() == QEvent.Type(QEvent.GraphicsSceneMousePress):
            if event.buttons() == Qt.MouseButton.LeftButton:
                coords = EBCoords(event.scenePos().x(), event.scenePos().y())
                items = self.scene().items(QPoint(coords.x, coords.y))
                for i in items:
                    if isinstance(i, MiniEnemyTile):  
                        self.state.currentEnemyTile = i.getID()
                        self.selectedIndicator.setPos(coords.roundToTile()[0], coords.roundToTile()[1])
                        self.parent().fromEnemyTile()
                        break
                else:
                    raise ValueError("Something went wrong when selecting an enemy tile")
        return False
    
    def parent(self) -> SidebarEnemy:
        return super().parent()        


class MiniEnemyTile(QGraphicsRectItem):
    def __init__(self, id: int, colourBrush: QBrush, x: int, y: int):
        super().__init__()
        self.setRect(0, 0, 32, 32)
        self.id = id

        if id == 0:
            self.bgImage = QGraphicsPixmapItem(self)
            self.bgImage.setPixmap(QPixmap(":/ui/erase.png"))
        else:
            self.setBrush(colourBrush)
            self.setPos(x, y)

            self.idShadow = QGraphicsSimpleTextItem(self)
            self.idShadow.setText(str(id).zfill(3))
            self.idShadow.setFont("EBMain")
            self.idShadow.setPos(8, 12)
            self.idShadow.setFlag(QGraphicsItem.ItemIsSelectable, False)

            self.idDisp = QGraphicsSimpleTextItem(self)
            self.idDisp.setText(str(id).zfill(3))
            self.idDisp.setBrush(WHITEBRUSH)
            self.idDisp.setFont("EBMain")
            self.idDisp.setPos(7, 11)
            self.idDisp.setFlag(QGraphicsItem.ItemIsSelectable, False)
            
    def getID(self):
        return self.id
