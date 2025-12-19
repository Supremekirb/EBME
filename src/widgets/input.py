from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtGui import (QBrush, QColor, QGuiApplication, QMouseEvent,
                           QPainter, QPalette, QPen)
from PySide6.QtWidgets import (QApplication, QCheckBox, QColorDialog,
                               QHBoxLayout, QLabel, QPushButton, QSpinBox,
                               QWidget)

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
    
    def setDisabled(self, disabled: bool):
        self.invert.setDisabled(disabled)
        self.spinbox.setDisabled(disabled)
        
        
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