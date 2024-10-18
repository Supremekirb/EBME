from typing import TYPE_CHECKING

from PIL import ImageQt
from PySide6.QtCore import QEvent, QPoint, QRectF, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPixmap
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGraphicsRectItem,
                               QGraphicsScene, QGraphicsSceneMouseEvent,
                               QGraphicsView, QLabel, QSizePolicy, QVBoxLayout,
                               QWidget)

import src.misc.common as common
from src.actions.fts_actions import ActionSwapMinitiles
from src.coilsnake.project_data import ProjectData

if TYPE_CHECKING:
    from tile_editor import TileEditor

class MinitileView(QGraphicsView):
    def __init__(self, scene: "MinitileScene"):
        super().__init__(scene)
        self.scale(2, 2)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.setMouseTracking(True)
        self.setFixedWidth(self.scene().width()*2 + self.verticalScrollBar().sizeHint().width() + 2)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
    
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
    MINITILE_WIDTH = 16
    
    def __init__(self, parent: "TileEditor", projectData: ProjectData):
        super().__init__(parent)
        
        self.projectData = projectData
        
        self.setSceneRect(0, 0, 8*self.MINITILE_WIDTH, 8*self.MINITILE_COUNT//self.MINITILE_WIDTH)
        
        self.setBackgroundBrush(Qt.GlobalColor.white)
        
        self.minitiles: list[TileEditorMinitile] = []
        
        self.lastMinitileHovered = -1
        self.hoverInfo = MinitileHoverDisplay()
        self.hoverInfo.hide()
        
        self.selector = QGraphicsRectItem()
        self.selector.setPen(QColor(Qt.GlobalColor.yellow))
        self.selector.setRect(-1, -1, 10, 10)
        self.selector.setBrush(Qt.BrushStyle.NoBrush)
        self.selector.setZValue(3)
        self.addItem(self.selector)
        
        self.destIndicator = QGraphicsRectItem()
        self.destIndicator.setPen(QColor(Qt.GlobalColor.white))
        self.destIndicator.setRect(-1, -1, 10, 10)
        self.destIndicator.setBrush(Qt.BrushStyle.NoBrush)
        self.destIndicator.setZValue(2)
        self.destIndicator.hide()
        self.addItem(self.destIndicator)
        
        self._mouseDownPos = QPoint()
        
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
                ))))
        self.updateHoverPreview(self.lastMinitileHovered)
                 
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        pos = event.scenePos()
        x = common.cap(pos.x() // 8, 0, self.MINITILE_WIDTH-1)
        y = common.cap(pos.y() // 8, 0, (self.MINITILE_COUNT/self.MINITILE_WIDTH)-1)
            
        index = int(y * self.MINITILE_WIDTH + x)
        if index not in range(self.MINITILE_COUNT):
            return super().mouseMoveEvent(event)

        if Qt.MouseButton.LeftButton in event.buttons():
            sourceIndex = int(self._mouseDownPos.y() // 8) * self.MINITILE_WIDTH + int(self._mouseDownPos.x() // 8)
            source = self.minitiles[sourceIndex]     
                    
            if x != int(self._mouseDownPos.x() // 8) or y != int(self._mouseDownPos.y() // 8):                
                source.setPos(QPoint(pos.x()-4, pos.y()-10))
                source.setZValue(5)
                self.selector.setPos(QPoint(pos.x()-4, pos.y()-10))
                
                self.destIndicator.show()
                self.destIndicator.setPos(x*8, y*8)
            else:
                source.setPos((self._mouseDownPos.x() // 8) * 8, (self._mouseDownPos.y() // 8) * 8)
                source.setZValue(0)
                self.selector.setPos((self._mouseDownPos.x() // 8) * 8, (self._mouseDownPos.y() // 8) * 8)
                self.destIndicator.hide()
                
        else:
            self.destIndicator.hide()
            
        if self.lastMinitileHovered != index:
            self.updateHoverPreview(index)

        return super().mouseMoveEvent(event)
    
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        pos = event.scenePos()
        x = common.cap(pos.x() // 8, 0, self.MINITILE_WIDTH)
        y = common.cap(pos.y() // 8, 0, self.MINITILE_COUNT/self.MINITILE_WIDTH)
        
        if event.button() == Qt.MouseButton.LeftButton:
            self._mouseDownPos = QPoint(x*8, y*8)
            index = int(y * self.MINITILE_WIDTH + x)
            if index not in range(self.MINITILE_COUNT):
                return super().mousePressEvent(event)
            
            self.selector.setPos(x*8, y*8)
            self.parent().selectMinitile(index)
        
        return super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        pos = event.scenePos()
        x = common.cap(pos.x() // 8, 0, self.MINITILE_WIDTH)
        y = common.cap(pos.y() // 8, 0, self.MINITILE_COUNT/self.MINITILE_WIDTH)
        index = int(y * self.MINITILE_WIDTH + x)
        if index not in range(self.MINITILE_COUNT):
            return super().mouseReleaseEvent(event)
        
        if event.button() == Qt.MouseButton.LeftButton:
            sourceIndex = int(self._mouseDownPos.y() // 8) * self.MINITILE_WIDTH + int(self._mouseDownPos.x() // 8)
            source = self.minitiles[sourceIndex] 
            
            if sourceIndex == index:
                return super().mouseReleaseEvent(event)
            
            action = ActionSwapMinitiles(self.projectData.getTileset(self.parent().state.currentTileset),
                                        sourceIndex, index)
            self.parent().undoStack.push(action)        
            
            source.setZValue(0)
            source.setPos((self._mouseDownPos.x() // 8) * 8, (self._mouseDownPos.y() // 8) * 8)
            
            self.destIndicator.hide()
            self.parent().selectMinitile(index)
            # aka the part where I realised that i should just pass state instead of set up parenting
            self.renderTileset(self.parent().state.currentTileset,
                            self.parent().state.currentPaletteGroup,
                            self.parent().state.currentPalette,
                            self.parent().state.currentSubpalette)
            self.updateHoverPreview(index)
        
        return super().mouseReleaseEvent(event)

    def moveCursorToMinitile(self, minitile: int):
        if minitile >= self.MINITILE_COUNT: raise ValueError(f"Minitile must be in range 0-{self.MINITILE_COUNT}! Recieved {minitile}")
        
        x = minitile % self.MINITILE_WIDTH
        y = minitile // self.MINITILE_WIDTH
        self.selector.setPos(x*8, y*8)
        
    def updateHoverPreview(self, minitile: int):
        self.hoverInfo.setImage(self.minitiles[minitile].pixmap().scaled(64, 64))
        self.hoverInfo.setData(minitile, True if minitile < common.MINITILENOFOREGROUND else False)
        self.lastMinitileHovered = minitile
    
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