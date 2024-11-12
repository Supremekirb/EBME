from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPainter, QUndoCommand, QUndoStack
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QStyle, QStyleOptionFrame,
                               QWidget)


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
        
# https://stackoverflow.com/a/68092991/15287613
class ElidedLabel(QLabel):
    _elideMode = Qt.TextElideMode.ElideRight

    def elideMode(self):
        return self._elideMode

    def setElideMode(self, mode):
        if self._elideMode != mode and mode != Qt.TextElideMode.ElideNone:
            self._elideMode = mode
            self.updateGeometry()

    def minimumSizeHint(self):
        return self.sizeHint()

    def sizeHint(self):
        hint = self.fontMetrics().boundingRect(self.text()).size()
        margins = self.contentsMargins()
        l = margins.left()
        r = margins.right()
        t = margins.top()
        b = margins.bottom()
        margin = self.margin() * 2
        return QSize(
            min(100, hint.width()) + l + r + margin, 
            min(self.fontMetrics().height(), hint.height()) + t + b + margin
        )

    def paintEvent(self, event):
        qp = QPainter(self)
        opt = QStyleOptionFrame()
        self.initStyleOption(opt)
        self.style().drawControl(
            QStyle.CE_ShapedFrame, opt, qp, self)
        margins = self.contentsMargins()
        l = margins.left()
        r = margins.right()
        t = margins.top()
        b = margins.bottom()
        margin = self.margin()
        try:
            # since Qt >= 5.11
            m = self.fontMetrics().horizontalAdvance('x') / 2 - margin
        except:
            m = self.fontMetrics().width('x') / 2 - margin
        r = self.contentsRect().adjusted(
            margin + m,  margin, -(margin + m), -margin)
        qp.drawText(r, self.alignment(), 
            self.fontMetrics().elidedText(
                self.text(), self.elideMode(), r.width()))
        
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
        if command:
            if not self.inMacro:
                self.pushed.emit(command)
    
            
class UndoHistoryLine(ElidedLabel):
    def __init__(self, stack: SignalUndoStack):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.setText("No history")
        self.setDisabled(True)
        
        self.stack = stack
        stack.undone.connect(self.updateText)
        stack.redone.connect(self.updateText)
        stack.pushed.connect(self.updateText)
        
    def updateText(self):
        befores: list[str] = []
        previous: str = ""
        
        index = self.stack.index()
        
        for i in range(index-20, index-1):
            if command := self.stack.command(i):
                befores.append(command.text())
        
        if command := self.stack.command(index-1):
            previous = command.text()
            
        text = ""
        for i in befores:
            text += i + ", "
        text += previous
        
        if not text:
            text = "No history"
            self.setDisabled(True)
        else:
            self.setEnabled(True)
            
        self.setText(text)

class UndoFutureLine(ElidedLabel):
    def __init__(self, stack: SignalUndoStack):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setText("No future")
        self.setDisabled(True)

        self.stack = stack
        stack.undone.connect(self.updateText)
        stack.redone.connect(self.updateText)
        stack.pushed.connect(self.updateText)
        
    def updateText(self):
        afters: list[str] = []
        next: str = ""
        
        index = self.stack.index()
        
        for i in range(index+1, index+20):
            if command := self.stack.command(i):
                afters.append(command.text())
        
        if command := self.stack.command(index):
            next = command.text()
        
        text = ""
        text += next
        for i in afters:
            text += ", " + i
            
        if not text:
            text = "No future"
            self.setDisabled(True)
        else:
            self.setEnabled(True)
            
        self.setText(text)