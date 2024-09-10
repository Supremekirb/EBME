from typing import TYPE_CHECKING

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPaintEvent, QPixmap
from PySide6.QtWidgets import QGridLayout, QSizePolicy, QWidget

from src.coilsnake.fts_interpreter import Minitile, Subpalette
from src.coilsnake.project_data import ProjectData
from src.misc.widgets import ColourButton

if TYPE_CHECKING:
    from tile_editor import TileEditor
    
class PaletteSelector(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        layout = QGridLayout()
        self.setLayout(layout)
        
        self.buttons: list[ColourButton] = []
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        for i in range(16):
            button = ColourButton(self)
            button.setCheckable(True)
            button.clicked.disconnect()
            button.setAutoExclusive(True)
            button.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred))
            layout.addWidget(button, i // 4, i % 4)
            self.buttons.append(button)
            
    def openEditor(self):
        # maybe new implementation later,
        # but right now just open the dialog of the selected button
        for button in self.buttons:
            if button.isChecked():
                button.openColourDialog()
                break
        
class MinitileGraphicsWidget(QWidget):
    def __init__(self, projectData: ProjectData):
        super().__init__()
        
        self.projectData = projectData
        
        self.currentMinitile: Minitile = None
        self.currentSubpalette: Subpalette = None
        self.isForeground = True
        
        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        policy.setHeightForWidth(True)
        policy.setWidthForHeight(True)
        self.setSizePolicy(policy)
        
        
    def paintEvent(self, event: QPaintEvent):
        if self.currentMinitile == None or self.currentSubpalette == None:
            return super().paintEvent(event)
        
        width = self.width()
        height = self.height()
        
        if width > height:
            width = height
        else:
            height = width
        
        painter = QPainter(self)
        
        painter.setBrush(QBrush(QPixmap(":/ui/bg.png")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, width, height)
           

        scale = width / 8
        painter.scale(scale, scale)
        
        for i in range(64):
            x = i % 8
            y = i // 8
            if self.isForeground:
                color = self.currentMinitile.mapIndexToRGBAForeground(self.currentSubpalette)[i]
            else:
                color = self.currentMinitile.mapIndexToRGBABackground(self.currentSubpalette)[i]
            painter.fillRect(x, y, 1, 1, QColor.fromRgb(*color))
            
        return super().paintEvent(event)
    
    def heightForWidth(self, width: int) -> int:
        return width
    
    def hasHeightForWidth(self):
        return True
    
    def minimumSizeHint(self):
        return QSize(128, 128)