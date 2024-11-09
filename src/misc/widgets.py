from copy import copy
import logging
import traceback

from PIL import ImageQt
from PySide6.QtCore import QPoint, QRect, QRectF, QSettings, QSize, Qt, Signal
from PySide6.QtGui import (QBrush, QColor, QGuiApplication, QIcon, QMouseEvent,
                           QPainter, QPaintEvent, QPalette, QPen, QPixmap,
                           QResizeEvent, QTransform, QUndoCommand, QUndoStack,
                           QWheelEvent)
from PySide6.QtWidgets import (QApplication, QBoxLayout, QCheckBox,
                               QColorDialog, QFrame, QGraphicsPixmapItem,
                               QGraphicsScene, QGraphicsSceneMouseEvent,
                               QGraphicsView, QGridLayout, QHBoxLayout, QLabel,
                               QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
                               QTabWidget, QTreeWidget, QTreeWidgetItem,
                               QWidget)

import src.misc.common as common
import src.misc.icons as icons
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
    
    def __init__(self, parent: QWidget | None = None, initialColour: QColor = QColor(255, 255, 255), viewOnly: bool = False):
        super().__init__(parent)
        
        self.viewOnly = viewOnly
        self.setToolTip("Click to edit, right click to copy hex code")
        
        if QGuiApplication.palette().color(QPalette.ColorGroup.Normal, QPalette.ColorRole.Base).lightness() < 128:
            self._border = "#FFFFFF"
        else:
            self._border = "#000000"
            
        self._thickPen = QPen()
        self._thickPen.setWidth(3)
        self._thickPen.setColor(self._border)
    
        self.chosenColour = None
        self.clicked.connect(self.openColourDialog)
        if not self.viewOnly:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.setColour(initialColour)
        
    def setViewOnly(self, viewOnly: bool):
        self.viewOnly = viewOnly
        if not self.viewOnly:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setAutoExclusive(True)
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.setToolTip("Click to edit, right click to copy hex code")
        else:
            self.unsetCursor()
            self.setAutoExclusive(False)
            self.setChecked(False)
            self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.setToolTip("Right click to copy hex code")
        
        if not self.isEnabled():
            self.setToolTip("")
        
    def openColourDialog(self):
        if not self.viewOnly:
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
        
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.RightButton:
            QApplication.clipboard().setText("#{0:02x}{1:02x}{2:02x}".format(*self.chosenColour.toTuple()))
            
        if not self.viewOnly:
            return super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if not self.viewOnly:
            return super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if not self.viewOnly:
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
        
        color = self.chosenColour
        brush = QBrush(color) 
        
        if not self.isEnabled():
            brush.setStyle(Qt.BrushStyle.Dense5Pattern)
            
        painter.setBrush(brush)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        painter.end()

    def setDisabled(self, disabled: bool):
        if disabled:
            self.setToolTip("")
        return super().setDisabled(disabled)
    
    def setEnabled(self, enabled: bool):
        if self.viewOnly:
            self.setToolTip("Right click to copy hex code")
        else:
            self.setToolTip("Click to edit, right click to copy hex code")
        return super().setEnabled(enabled)

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
        
    def __init__(self, projectData: ProjectData, horizontal: bool = False, rowSize: int = 6, forcedPalette: Palette|None=None):
        super().__init__()
        
        self.projectData = projectData
        self.horizontal = horizontal
        self.rowSize = rowSize
        self.forcedPalette = forcedPalette
        self.forcedPaletteCache: dict[int, QPixmap] = {}
        
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
                try:
                    tileID = self.posToTileIndex(x, y)
                    if tileID >= common.MAXTILES or tileID < 0:
                        continue
                    
                    if not self.forcedPalette:
                        tileGfx = self.projectData.getTileGraphic(self.currentTileset,
                                                                self.currentPaletteGroup,
                                                                self.currentPalette,
                                                                tileID)
                        if not tileGfx.hasRendered:
                            tileGfx.render(tileset)
                            tileGfx.hasRendered = True
                            
                        painter.drawPixmap(x*32, y*32, tileGfx.rendered)
                        
                    else:
                        try:
                            pixmap = self.forcedPaletteCache[tileID]
                        except KeyError:
                            tileset = self.projectData.getTileset(self.currentTileset)
                            tile = tileset.tiles[tileID]
                            self.forcedPaletteCache[tileID] = QPixmap.fromImage(ImageQt.ImageQt(
                                tile.toImage(self.forcedPalette, tileset)
                            ))
                            pixmap = self.forcedPaletteCache[tileID]
                        
                        painter.drawPixmap(x*32, y*32, pixmap)
                except Exception:
                    painter.drawPixmap(x*32, y*32, QPixmap(":ui/errorTile.png"))
                    logging.warning(traceback.format_exc())
                    
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
                    try:
                        tileID = self.posToTileIndex(x, y)
                        painter.setPen(Qt.GlobalColor.black)
                        painter.drawText((x*32)+8, (y*32)+23, str(tileID).zfill(3))
                        painter.setPen(Qt.GlobalColor.white)
                        painter.drawText((x*32)+7, (y*32)+22, str(tileID).zfill(3))
                    except Exception:
                        logging.warning(traceback.format_exc())
    
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

# https://stackoverflow.com/a/64279374
class IconLabel(QWidget):
    IconSize = QSize(16, 16)
    HorizontalSpacing = 2

    def __init__(self, text: str|None=None, icon: QIcon|None=None, final_stretch=True):
        super().__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.iconLabel = QLabel()
        if icon:
            self.setIcon(icon)
            
        self.textLabel = QLabel()
        if text:
            self.setText(text)

        layout.addWidget(self.iconLabel)
        layout.addSpacing(self.HorizontalSpacing)
        layout.addWidget(self.textLabel)

        if final_stretch:
            layout.addStretch()
    
    def setIcon(self, icon: QIcon):
        self.iconLabel.setPixmap(icon.pixmap(self.IconSize))
    
    def setText(self, text: str):
        self.textLabel.setText(text)
        
        
class PaletteSelector(QWidget):
    colourChanged = Signal(int)
    subpaletteChanged = Signal(int)
    colourEdited = Signal(int, int)
    
    def __init__(self):
        super().__init__()
        
        layout = QGridLayout()
        self.setLayout(layout)
        
        self.buttons: list[list[ColourButton]] = [[], [], [], [], [], []]
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.arrowIndicatorLabels: list[QLabel] = []
        self.subpaletteLabels: list[QLabel] = []
        self.viewOnly: bool = False
        
        for i in range(6):
            label = QLabel(str(i))
            label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            label.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(label, i, 1)
            
            indicator = QLabel("")
            indicator.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            if i == 0: 
                label.setText(f"<b>{i}</b>")
                indicator.setText("▶")
            layout.addWidget(indicator, i, 0)
            
            self.subpaletteLabels.append(label)
            self.arrowIndicatorLabels.append(indicator)
            
            for j in range(16):                
                button = ColourButton(self)
                button.setCheckable(True)
                button.clicked.disconnect()
                button.colourChanged.connect(self.onColourEdited)
                button.clicked.connect(self.onColourChanged)
                button.setAutoExclusive(True)
                button.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed))
                button.setFixedSize(24, 24)
                button.setToolTip("Double click to edit, right click to copy hex code")
                layout.addWidget(button, i, j+2)
                self.buttons[i].append(button)
            
        self.buttons[0][0].setChecked(True)
        self.currentSubpaletteIndex = 0
        self.currentColour = self.buttons[0][0].chosenColour
        self.currentColourIndex = 0
        
        self.currentPalette: Palette = None
        
        self.onColourChanged()
            
    def onColourChanged(self):
        for subpalette, list in enumerate(self.buttons):
            for index, button in enumerate(list):
                if button.isChecked():
                    self.currentColour = button.chosenColour
                    if subpalette != self.currentSubpaletteIndex:
                        self.currentSubpaletteIndex = subpalette
                        self.subpaletteChanged.emit(subpalette)
                        self.updateSubpaletteLabels()
                    if index != self.currentColourIndex:
                        self.currentColourIndex = index
                        self.colourChanged.emit(index)
                    return
                
    def onColourEdited(self):
        for subpalette in self.buttons:
            for button in subpalette:
                if button.isChecked():
                    self.colourEdited.emit(self.buttons.index(subpalette), subpalette.index(button))
                    return
        
    def setColourIndex(self, index: int):
        self.currentColourIndex = index
        self.buttons[self.currentSubpaletteIndex][index].setChecked(True)
        
    def setSubpaletteIndex(self, subpalette: int):
        self.currentSubpaletteIndex = subpalette
        self.buttons[subpalette][self.currentColourIndex].setChecked(True)
        self.updateSubpaletteLabels()
    
    def updateSubpaletteLabels(self):
        for id, label in enumerate(self.subpaletteLabels):
            if id == self.currentSubpaletteIndex and not self.viewOnly:
                label.setText(f"<b>{id}</b>")
                self.arrowIndicatorLabels[id].setText("▶")
            else:
                label.setText(str(id))
                self.arrowIndicatorLabels[id].setText("")
        
    def openEditor(self):
        # maybe new implementation later,
        # but right now just open the dialog of the selected button
        if not self.viewOnly:
            for subpaletteButtons in self.buttons:
                for button in subpaletteButtons:
                    if button.isChecked():
                        button.openColourDialog()
                        return
            
    def loadPalette(self, palette: Palette):
        for index, subpalette in enumerate(palette.subpalettes):
            for colour, button in enumerate(self.buttons[index]):
                button.blockSignals(True)
                button.setColour(QColor.fromRgb(*subpalette.subpaletteRGBA[colour]))
                button.blockSignals(False)
            
        self.currentPalette = palette 
        
        self.onColourChanged()
        
    def setViewOnly(self, viewOnly: bool):
        self.viewOnly = viewOnly
        self.updateSubpaletteLabels()
        
        for subpal in self.buttons:
            for button in subpal:
                button.setViewOnly(viewOnly)
            
        
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
    
    def getCurrentSubpalette(self):
        current = self.currentItem()
        if isinstance(current, SubpaletteListItem):
            return current
        else: return None
    
    def getCurrentPalette(self):
        current = self.currentItem()
        if isinstance(current, SubpaletteListItem):
            return current.parent()
        elif isinstance(current, PaletteListItem):
            return current
        else: return None
    
    def getCurrentPaletteGroup(self):
        current = self.currentItem()
        if isinstance(current, SubpaletteListItem):
            return current.parent().parent()
        elif isinstance(current, PaletteListItem):
            return current.parent()
        elif isinstance(current, PaletteGroupListItem):
            return current
        else: return None
        
    def getCurrentTileset(self):
        current = self.currentItem()
        if isinstance(current, SubpaletteListItem):
            return current.parent().parent().parent()
        elif isinstance(current, PaletteListItem):
            return current.parent().parent()
        elif isinstance(current, PaletteGroupListItem):
            return current.parent()
        elif isinstance(current, TilesetListItem):
            return current
        else: return None

    def syncPaletteGroup(self, group: int):
        tileset = self.topLevelItem(self.projectData.getTilesetFromPaletteGroup(group).id)
        for i in range(tileset.childCount()):
            paletteGroup: PaletteGroupListItem = tileset.child(i)
            if paletteGroup.paletteGroup == group:
                for j in reversed(range(paletteGroup.childCount())):
                    paletteGroup.removeChild(paletteGroup.child(j))
                for j in self.projectData.getPaletteGroup(group).palettes:
                    palette = PaletteListItem(j.paletteID, paletteGroup, [f"Palette {j.paletteID}"])
                    paletteGroup.addChild(palette)
                    for k in range(0, 6):
                        subpalette = SubpaletteListItem(k, palette, [f"Subpalette {k}"])
                        palette.addChild(subpalette)

class TilesetListItem(QTreeWidgetItem):
    def __init__(self, tileset: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tileset = tileset
        
        self.setIcon(0, icons.ICON_TILESET)

class PaletteGroupListItem(QTreeWidgetItem):
    def __init__(self, palettegroup: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.paletteGroup = palettegroup
        
        self.setIcon(0, icons.ICON_PALETTE_GROUP)
    
    def parent(self) -> TilesetListItem:
        return super().parent()

class PaletteListItem(QTreeWidgetItem):
    def __init__(self, palette: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.palette = palette
        
        self.setIcon(0, icons.ICON_PALETTE)
    
    def parent(self) -> PaletteGroupListItem:
        return super().parent()

class SubpaletteListItem(QTreeWidgetItem):
    def __init__(self, subpalette: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subpalette = subpalette
        
        self.setIcon(0, icons.ICON_SUBPALETTE)

    def parent(self) -> PaletteListItem:
        return super().parent()
    
# not really a widget...
class SignalUndoStack(QUndoStack):
    """QUndoStack with signals for undo, redo, and push. These signals also transmit the command that was just undone/redone/pushed."""
    undone = Signal(QUndoCommand)
    redone = Signal(QUndoCommand)
    pushed = Signal(QUndoCommand)
    """Doesn't emit during macros, only at the end of them"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.inMacro = False
        
    def beginMacro(self, text: str):
        self.inMacro = True
        return super().beginMacro(text)    

    def endMacro(self):
        self.inMacro = False
        super().endMacro()
        self.pushed.emit(self.command(self.index()-1))

    def undo(self):
        super().undo()
        command = self.command(self.index())
        if command:
            self.undone.emit(command)
    
    def redo(self):
        super().redo()
        command = self.command(self.index()-1)
        if command:
            self.redone.emit(command)
    
    def push(self, command: QUndoCommand):
        super().push(command)
        if not self.inMacro:
            self.pushed.emit(command)