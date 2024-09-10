from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtGui import (QColor, QGuiApplication, QMouseEvent, QPainter,
                           QPalette, QPen, QResizeEvent)
from PySide6.QtWidgets import (QBoxLayout, QCheckBox, QColorDialog, QFrame,
                               QHBoxLayout, QLabel, QPushButton, QSpacerItem,
                               QSpinBox, QWidget)

import src.misc.common as common


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