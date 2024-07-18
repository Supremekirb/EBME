from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPalette
from PySide6.QtWidgets import (QColorDialog, QFrame, QHBoxLayout, QLabel,
                               QPushButton, QSpinBox, QWidget)

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
    def __init__(self, *args, **kwargs):
        QHBoxLayout.__init__(self, *args, **kwargs)
        self.spinbox = BaseChangerSpinbox()
        self.spinbox.setMaximum(common.WORDLIMIT)
        self.spinbox.editingFinished.connect(self.editingFinished.emit)
        self.spinbox.valueChanged.connect(lambda new: self.valueChanged.emit(new))
        self.addWidget(self.spinbox)

        self.button = QPushButton("Invert")
        self.button.clicked.connect(lambda: self.spinbox.setValue(common.invertFlag(self.spinbox.value())))
        self.button.clicked.connect(self.inverted.emit)
        self.button.setToolTip("Flags above 0x8000 (32,678) are the inversion of the same flags below 0x8000.")
        self.addWidget(self.button)

    def value(self) -> int:
        return self.spinbox.value()
    
    def setValue(self, val: int) -> None:
        self.spinbox.setValue(val)
        
    def clear(self) -> None:
        self.spinbox.clear()
        
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
    
        self.chosenColour = None
        self.clicked.connect(self.openColourDialog)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.setColour(initialColour)
        
    def openColourDialog(self):
        colour = QColorDialog.getColor(self.chosenColour, self, "Choose a colour")
        if colour.isValid():
            self.setColour(colour)
            
    def setColour(self, colour: QColor):
        self.chosenColour = colour
        self.colourChanged.emit()
        self.repaint()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(self._border)
        painter.setBrush(self.chosenColour)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        painter.end()
