from copy import copy

from PIL import ImageQt
from PySide6.QtCore import QPoint, QRect, QRectF, QSettings, QSize, Qt, Signal
from PySide6.QtGui import (QBrush, QColor, QGuiApplication, QIcon, QMouseEvent,
                           QPainter, QPaintEvent, QPalette, QPen, QPixmap,
                           QResizeEvent, QTransform, QWheelEvent)
from PySide6.QtWidgets import (QBoxLayout, QCheckBox, QColorDialog, QFrame,
                               QGraphicsPixmapItem, QGraphicsScene,
                               QGraphicsSceneMouseEvent, QGraphicsView,
                               QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                               QSpacerItem, QSpinBox, QTabWidget, QWidget)

import src.misc.common as common
from src.coilsnake.fts_interpreter import (FullTileset, Minitile, Palette,
                                           Subpalette, Tile)
from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords


class BaseChangerSpinbox(QSpinBox):
    """
    Spinbox which updates base display mode based on user settings.\n
    Do not use with spinboxes that do not need to update their base, like coords.\n
    
    Special methods are:\n
    `hexMode()` - set display base to `16`, set prefix to `0x` for all instances\n
    `decMode()` - set display base to `10`, set prefix to empty for all instances\n

    (i don't know if what i'm doing here is cursed or not but whatever)
    """
    instances = []
    isHex = False

    def __init__(self, *args, **kwargs):
        QSpinBox.__init__(self, *args, **kwargs)
        BaseChangerSpinbox.instances.append(self)

        if BaseChangerSpinbox.isHex:
            self.setDisplayIntegerBase(16)
            self.setPrefix("0x")
            
    def isBlank(self) -> bool:
        return True if (self.text() == "" or self.text() == "0x") else False

    @classmethod
    def hexMode(cls):
        for i in cls.instances:
            i.setDisplayIntegerBase(16)
            i.setPrefix("0x")
    @classmethod
    def decMode(cls):
        for i in cls.instances:
            i.setDisplayIntegerBase(10)
            i.setPrefix("")

    @classmethod
    def toggleMode(cls):
        settings = QSettings()
        if BaseChangerSpinbox.isHex:
            BaseChangerSpinbox.isHex = False
            BaseChangerSpinbox.decMode()
        else:
            BaseChangerSpinbox.isHex = True
            BaseChangerSpinbox.hexMode()
        settings.setValue("main/HexMode", int(BaseChangerSpinbox.isHex))

            
class FlagInput(QHBoxLayout):
    """Flag spinbox with inversion button"""
    editingFinished = Signal()
    valueChanged = Signal(int)
    inverted = Signal()
    def __init__(self, invertable: bool=True, parent=None):
        super().__init__(parent)
        
        self.invertable = invertable
        
        self.spinbox = BaseChangerSpinbox()
        self.spinbox.setMaximum(common.WORDLIMIT if not self.invertable else common.WORDLIMIT//2)
        
        self.spinbox.editingFinished.connect(self.editingFinished.emit)
        self.spinbox.valueChanged.connect(lambda new: self.valueChanged.emit(new))
        self.addWidget(self.spinbox)

        self.invert = QCheckBox("Invert")
        self.invert.toggled.connect(lambda: self.inverted.emit())
        self.invert.setToolTip("Adds 0x8000 to the flag, which is interpreted as inverting the flag's state in some scenarios.")
        
        if invertable:
            self.addWidget(self.invert)

    def value(self) -> int:
        if self.invertable and self.invert.isChecked():
            return self.spinbox.value() + 0x8000
        return self.spinbox.value()
    
    def setValue(self, val: int) -> None:
        self.invert.blockSignals(True)
        self.spinbox.blockSignals(True)
        
        if self.invertable:
            if val >= 0x8000:
                self.invert.setChecked(True)
                val -= 0x8000
            else: self.invert.setChecked(False)
        self.spinbox.setValue(val)
        
        self.invert.blockSignals(False)
        self.spinbox.blockSignals(False)
        
    def clear(self) -> None:
        self.invert.blockSignals(True)
        self.spinbox.blockSignals(True)
        
        self.spinbox.clear()
        
        if self.invertable:
            self.invert.setChecked(False)
        
        self.invert.blockSignals(False)
        self.spinbox.blockSignals(False)
        
        
    def text(self) -> str:
        return self.spinbox.text()
    
    def isBlank(self) -> bool:
        return True if self.text() == ("" or "0x") else False

class CoordsInput(QHBoxLayout):
    """Coordinates input with X and Y labels and fields. Use `x` and `y` spinboxes to connect things and whatever."""
    def __init__(self, *args, **kwargs):
        QHBoxLayout.__init__(self, *args, **kwargs)
        self.x = QSpinBox()
        self.y = QSpinBox()

        self.addWidget(QLabel("X"))
        self.addWidget(self.x)
        self.addWidget(QLabel("Y"))
        self.addWidget(self.y)
    
    def isBlankAnd(self) -> bool:
        return True if self.x.text() == "" and self.y.text() == "" else False
    
    def isBlankOr(self) -> bool:
        return True if self.x.text() == "" or self.y.text() == "" else False
    
    def isBlankX(self) -> bool:
        return True if self.x.text() == "" else False
    
    def isBlankY(self) -> bool:
        return True if self.y.text() == "" else False


# https://stackoverflow.com/questions/10053839/how-does-designer-create-a-line-widget
class HSeparator(QFrame):
    """Custom horizontal separation line"""
    def __init__(self, *args, **kwargs):
        QFrame.__init__(self, *args, **kwargs)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class VSeparator(QFrame):
    """Custom vertical separation line"""
    def __init__(self, *args, **kwargs):
        QFrame.__init__(self, *args, **kwargs)
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)
        
        
class ColourButton(QPushButton):
    """A coloured "button" that opens a colour dialog when clicked"""
    colourChanged = Signal()
    
    def __init__(self, parent: QWidget | None = None, initialColour: QColor = QColor(255, 255, 255)):
        super().__init__(parent)
        
        if QGuiApplication.palette().color(QPalette.ColorGroup.Normal, QPalette.ColorRole.Base).lightness() < 128:
            self._border = "#FFFFFF"
        else:
            self._border = "#000000"
            
        self._thickPen = QPen()
        self._thickPen.setWidth(3)
        self._thickPen.setColor(self._border)
    
        self.chosenColour = None
        self.clicked.connect(self.openColourDialog)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.setColour(initialColour)
        
    def openColourDialog(self):
        colour = QColorDialog.getColor(self.chosenColour, self, "Choose a colour")
        if colour.isValid():
            self.setColour(colour)
            
    def setColour(self, colour: QColor):
        colour.setAlpha(255)
        self.chosenColour = colour
        self.colourChanged.emit()
        if self.chosenColour.lightness() < 100:
            self._thickPen.setColor("#FFFFFF")
        else:
            self._thickPen.setColor("#000000")
        self.repaint()
        
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.openColourDialog()
        return super().mouseDoubleClickEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.isCheckable():
            painter.setPen(self._border)
            
        else:
            if self.isChecked():
                painter.setPen(self._thickPen)
            else:
                painter.setPen(Qt.PenStyle.NoPen)
            
        painter.setBrush(self.chosenColour)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        painter.end()

# https://stackoverflow.com/a/49851646
class AspectRatioWidget(QWidget):
    def __init__(self, widget: QWidget, parent: QWidget = None):
        super().__init__(parent)
        self.aspect_ratio = widget.size().width() / widget.size().height()
        self.setLayout(QBoxLayout(QBoxLayout.Direction.LeftToRight, self))
        #  add spacer, then widget, then spacer
        self.layout().addItem(QSpacerItem(0, 0))
        self.layout().addWidget(widget)
        self.layout().addItem(QSpacerItem(0, 0))
        
        self.setContentsMargins(0, 0, 0, 0)
        # self.layout().setAlignment(widget, Qt.AlignmentFlag.AlignCenter)

    def resizeEvent(self, event: QResizeEvent):
        w = event.size().width()
        h = event.size().height()

        if w / h > self.aspect_ratio:  # too wide
            self.layout().setDirection(QBoxLayout.Direction.LeftToRight)
            widget_stretch = h * self.aspect_ratio
            outer_stretch = (w - widget_stretch) / 2 + 0.5
        else:  # too tall
            self.layout().setDirection(QBoxLayout.Direction.TopToBottom)
            widget_stretch = w / self.aspect_ratio
            outer_stretch = (h - widget_stretch) / 2 + 0.5

        self.layout().setStretch(0, outer_stretch)
        self.layout().setStretch(1, widget_stretch)
        self.layout().setStretch(2, outer_stretch)
        
class HorizontalGraphicsView(QGraphicsView):    
    def wheelEvent(self, event: QWheelEvent):
        self.horizontalScrollBar().event(event)
        
class MinitileGraphicsWidget(QWidget):    
    def __init__(self):
        super().__init__()
        
        self.currentMinitile: Minitile = None
        self.currentSubpalette: Subpalette = None
        self.isForeground = True
        
        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        policy.setHeightForWidth(True)
        policy.setWidthForHeight(True)
        self.setSizePolicy(policy)
        
        self._scratchBitmap: list[str] = []
        
    def loadMinitile(self, minitile: Minitile, id: int=0):
        self.currentMinitile = minitile
        self.copyToScratch()

    def copyToScratch(self):
        """For better undo/redo support, we copy the bitmap to this scratch space to modify it.
        
        Then undo/redo actions apply it to the model.
        
        Keeping it in the base class so we don't have to rewrite painting in the editing subclass"""
        if self.isForeground:
            self._scratchBitmap = copy(self.currentMinitile.foreground)
        else:
            self._scratchBitmap = copy(self.currentMinitile.background)
        
    def indexAtPos(self, pos: QPoint) -> int|None:
        """Get the index (0-63) of the pixel at the given position

        Args:
            pos (QPoint): Location on the widget, such as from an event

        Returns:
            int|None: index, None if out of bounds
        """
        w = self.width()
        h = self.height()
        
        if w > h:       
            w = h
        else:
            h = w
            
        x = pos.x() // (w / 8)
        y = pos.y() // (h / 8)
        
        if x < 0 or x > 7 or y < 0 or y > 7:
            return
        
        return int(y * 8 + x)
        
        
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
           
        scale = width / 8
              
        painter.scale(scale, scale)
        
        # draw bg at half the size of the minitile pixel 
        painter.scale(0.5, 0.5)
        painter.setBrush(QBrush(QPixmap(":/ui/bg.png").scaled(2, 2)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, 16, 16)
        painter.scale(2, 2)
        
        for i in range(64):
            x = i % 8
            y = i // 8
            colour = self.currentSubpalette.subpaletteRGBA[self._scratchBitmap[i]]
            if not self.isForeground and colour[-1] == 0:
                colour = list(colour)
                colour[-1] = 255
            painter.fillRect(x, y, 1, 1, QColor.fromRgb(*colour))
            
        return super().paintEvent(event)
    
    def heightForWidth(self, width: int) -> int:
        return width
    
    def hasHeightForWidth(self):
        return True
    
    def minimumSizeHint(self):
        return QSize(128, 128)

    def resizeEvent(self, event: QResizeEvent):
        self.setMinimumWidth(event.size().height())       
        return super().resizeEvent(event)
    
class TileGraphicsWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        self.currentTile: Tile = None
        self.currentPalette: Palette = None
        self.currentTileset: FullTileset = None
        
        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        policy.setHeightForWidth(True)
        policy.setWidthForHeight(True)
        self.setSizePolicy(policy)
    
    def loadTile(self, tile: Tile):
        self.currentTile = tile
        self.update()
    
    def loadPalette(self, palette: Palette):
        self.currentPalette = palette
        self.update()
    
    def loadTileset(self, tileset: FullTileset):
        self.currentTileset = tileset
        self.update()
    
    def indexAtPos(self, pos: QPoint) -> int|None:
        """Get the index (0-15) of the minitile at the given positon

        Args:
            pos (QPoint): Location on the widget, such as from an event
        
        Returns:
            int|None: index, None if out of bounds
        """
        w = self.width()
        h = self.height()
        
        if w > h:
            w = h
        else:
            h = w
        
        x = pos.x() // (w / 4)
        y = pos.y() // (h / 4)
        
        if x < 0 or x > 3 or y < 0 or y > 3:
            return
        
        return int(y * 4 + x)
    
    def paintEvent(self, event: QPaintEvent):
        if self.currentTile == None or self.currentPalette == None:
            return super().paintEvent(event)

        width = self.width()
        height = self.height()
        
        if width > height:
            width = height
        else:
            height = width
        
        painter = QPainter(self)
        
        scale = width / 32
        
        painter.scale(scale, scale)
        
        painter.scale(0.5, 0.5)
        painter.setBrush(QBrush(QPixmap(":/ui/bg.png").scaled(2, 2)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, 64, 64)
        painter.scale(2, 2)
        
        painter.drawImage(0, 0, ImageQt.ImageQt(self.currentTile.toImage(self.currentPalette, self.currentTileset)))

        return super().paintEvent(event)

    def heightForWidth(self, width: int) -> int:
        return width

    def hasHeightForWidth(self):
        return True

    def minimumSizeHint(self):
        return QSize(128, 128)
    
    def resizeEvent(self, event: QResizeEvent):
        self.setMinimumWidth(event.size().height())       
        return super().resizeEvent(event)
    
class TilesetDisplayGraphicsScene(QGraphicsScene):
    tileSelected = Signal(int)
        
    def __init__(self, projectData: ProjectData, horizontal: bool = False, rowSize: int = 6):
        super().__init__()
        
        self.projectData = projectData
        self.horizontal = horizontal
        self.rowSize = rowSize
        
        self.selectionIndicator = QGraphicsPixmapItem(QPixmap(":/ui/selectTile.png"))
        
        if not horizontal:
            self.setSceneRect(0, 0, self.rowSize*32, (common.MAXTILES*32)//self.rowSize)
        else:
            self.setSceneRect(0, 0, (common.MAXTILES*32)//self.rowSize, self.rowSize*32)
            
        self.addItem(self.selectionIndicator)
        self.setForegroundBrush((QBrush(QPixmap(":/grids/32grid0.png"))))
        self.setBackgroundBrush((QBrush(QPixmap(":/ui/bg.png"))))
        
        self.currentTileset = 0
        self.currentPaletteGroup = 0
        self.currentPalette = 0
    
    def cursorOverTile(self):
        return self.posToTileIndex(*self.selectionIndicator.pos().toTuple())
    
    def moveCursorToTile(self, tile: int):
        x, y = self.tileIndexToPos(tile)
        self.selectionIndicator.setPos(x*32, y*32)
        
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        pos = EBCoords(*event.scenePos().toTuple())
        self.tileSelected.emit(self.posToTileIndex(*pos.coordsTile()))
        self.selectionIndicator.setPos(*pos.roundToTile())
        
        super().mousePressEvent(event)
    
    def drawBackground(self, painter: QPainter, rect: QRectF | QRect):
        super().drawBackground(painter, rect)
        start = EBCoords(*rect.topLeft().toTuple())
        end = EBCoords(*rect.bottomRight().toTuple())
        x0, y0 = start.coordsTile()
        x1, y1 = end.coordsTile()
        
        tileset = self.projectData.getTileset(self.currentTileset)        
        for y in range(y0, y1+1):
            for x in range(x0, x1+1):
                tileID = self.posToTileIndex(x, y)
                if tileID >= common.MAXTILES or tileID < 0:
                    continue
                tileGfx = self.projectData.getTileGraphic(self.currentTileset,
                                                          self.currentPaletteGroup,
                                                          self.currentPalette,
                                                          tileID)
                if not tileGfx.hasRendered:
                    tileGfx.render(tileset)
                    tileGfx.hasRendered = True
                    
                painter.drawPixmap(x*32, y*32, tileGfx.rendered)
                
        if QSettings().value("mapeditor/ShowTileIDs", False, bool):
            painter.setFont("EBMain")
            font = painter.font()
            font.setPointSize(12)
            painter.setFont(font)
            painter.setBrush(QColor(0, 0, 0, 128))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(rect)
            
            for y in range(y0, y1+1):
                for x in range(x0, x1+1):
                    tileID = self.posToTileIndex(x, y)
                    painter.setPen(Qt.GlobalColor.black)
                    painter.drawText((x*32)+8, (y*32)+23, str(tileID).zfill(3))
                    painter.setPen(Qt.GlobalColor.white)
                    painter.drawText((x*32)+7, (y*32)+22, str(tileID).zfill(3))
    
    def posToTileIndex(self, x: int, y: int):
        if self.horizontal:
            return int(x * self.rowSize + y)
        else:
            return int(y * self.rowSize + x)
        
    def tileIndexToPos(self, tile: int):
        if self.horizontal:
            return tile // self.rowSize, tile % self.rowSize
        else:
            return tile % self.rowSize, tile // self.rowSize

class UprightIconsWestTabWidget(QTabWidget):
    def addTab(self, widget: QWidget, icon: QIcon, label: str):
        icon = QIcon(icon.pixmap(QSize(100, 100)).transformed(QTransform().rotate(90)))
        return super().addTab(widget, icon, label)