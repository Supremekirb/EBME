from typing import TYPE_CHECKING

from PIL import ImageQt
from PySide6.QtCore import QEvent, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QMouseEvent, QPixmap
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGraphicsRectItem,
                               QGraphicsScene, QGraphicsSceneMouseEvent,
                               QGraphicsView, QLabel, QSizePolicy, QVBoxLayout,
                               QWidget)

import src.misc.common as common
from src.coilsnake.project_data import ProjectData

if TYPE_CHECKING:
    from tile_editor import TileEditor

class MinitileView(QGraphicsView):
    def __init__(self, scene: "MinitileScene"):
        super().__init__(scene)
        self.scale(2, 2)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
    
    def leaveEvent(self, event: QEvent):
        self.scene().hoverInfo.hide()
        super().leaveEvent(event)
        
    def mouseMoveEvent(self, event: QMouseEvent):        
        self.scene().hoverInfo.setGeometry(self.pos().x() + self.size().width() + 
                                           self.scene().hoverInfo.layout().spacing() + 2, # TODO MULTIPLATFORM check if this leeway works on other platforms
                                           self.pos().y() + self.size().height()//2,
                                           1, 1) # size arguments default to widget minimum if they're too small, which is what we want
        
        self.scene().hoverInfo.show()   
        
        return super().mouseMoveEvent(event)
        
    def scene(self) -> "MinitileScene": # for typing
        return super().scene()
    
class MinitileScene(QGraphicsScene):
    MINITILE_COUNT = 512
    MINITILE_WIDTH = 32
    
    def __init__(self, parent: "TileEditor", projectData: ProjectData):
        super().__init__(parent)
        
        self.projectData = projectData
        
        self.setSceneRect(0, 0, 8*self.MINITILE_WIDTH, 8*self.MINITILE_COUNT//self.MINITILE_WIDTH)
        
        self.setBackgroundBrush(
            QBrush(QPixmap(":/ui/bg.png")))
        
        self.minitiles: list[TileEditorMinitile] = []
        
        self.lastMinitileHovered = 0
        self.hoverInfo = MinitileHoverDisplay()
        self.hoverInfo.hide()
        
        self.selector = QGraphicsRectItem()
        self.selector.setPen(QColor(Qt.GlobalColor.yellow))
        self.selector.setRect(-1, -1, 10, 10)
        self.selector.setBrush(Qt.BrushStyle.NoBrush)
        self.selector.setZValue(2)
        self.addItem(self.selector)
        
        # populate
        for i in range(self.MINITILE_COUNT):
            minitile = TileEditorMinitile()
            minitile.setPixmap(QPixmap.fromImage(ImageQt.ImageQt(
                projectData.tilesets[0].minitiles[i].BothToImage(
                self.projectData.tilesets[0].palettes[0].subpalettes[0]
            ))))
            minitile.setPos((i % self.MINITILE_WIDTH) * 8, (i // self.MINITILE_WIDTH) * 8)
            self.addItem(minitile)
            self.minitiles.append(minitile)
            
    def renderTileset(self, tileset: int, paletteGroup: int, palette: int, subpalette: int):
        for id, i in enumerate(self.minitiles):
            i.setPixmap(QPixmap.fromImage(ImageQt.ImageQt(
                self.projectData.getTileset(tileset).minitiles[id].BothToImage(
                    self.projectData.getTileset(tileset).getPalette(
                        paletteGroup, palette).subpalettes[subpalette]
                )
            )))
                 
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        pos = event.scenePos()
        x = int(pos.x() // 8)
        y = int(pos.y() // 8)
        index = y * self.MINITILE_WIDTH + x
        if index not in range(self.MINITILE_COUNT):
            return super().mouseMoveEvent(event)
        
        if self.lastMinitileHovered != index:
            self.hoverInfo.setImage(self.minitiles[index].pixmap().scaled(64, 64))
            self.hoverInfo.setData(index, True if index < common.MINITILENOFOREGROUND else False)
            self.lastMinitileHovered = index

        return super().mouseMoveEvent(event)
    
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        pos = event.scenePos()
        x = int(pos.x() // 8)
        y = int(pos.y() // 8)
        index = y * self.MINITILE_WIDTH + x
        if index not in range(self.MINITILE_COUNT):
            return super().mousePressEvent(event)
        
        self.selector.setPos(x*8, y*8)
        self.parent().selectMinitile(index)
        
        return super().mousePressEvent(event)

    def moveCursorToMinitile(self, minitile: int):
        if minitile >= self.MINITILE_COUNT: raise ValueError(f"Minitile must be in range 0-{self.MINITILE_COUNT}! Recieved {minitile}")
        x = minitile % self.MINITILE_WIDTH
        y = minitile // self.MINITILE_WIDTH
        self.selector.setPos(x*8, y*8)
    
    def parent(self) -> "TileEditor": # for typing
        return super().parent()


class TileEditorMinitile(QGraphicsPixmapItem):
    def __init__(self):
        super().__init__()

    def boundingRect(self):
        return QRectF(0, 0, 8, 8)


class MinitileHoverDisplay(QWidget):
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.imLabel = QLabel()
        self.IDLabel = QLabel("ID:")
        self.hasFgLabel = QLabel("Has FG:")
        
        layout.addWidget(self.imLabel)
        layout.addWidget(self.IDLabel)
        layout.addWidget(self.hasFgLabel)
        
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowTransparentForInput | Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
    def setImage(self, image: QPixmap):
        self.imLabel.setPixmap(image)
        
    def setData(self, id: int, hasFg: bool):
        self.IDLabel.setText(f"ID: {id}")
        self.hasFgLabel.setText(f"FG: {'Yes' if hasFg else 'No'}")