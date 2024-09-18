from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QDialog, QTextEdit, QVBoxLayout


class Stream(QObject):
    logged = ""
    newText = Signal(str)
    
    def write(self, text: str):
        Stream.logged += text
        self.newText.emit(text)
        
STREAM = Stream()
SYSTEM_OUTPUT = False
        
class DebugOutputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        STREAM.newText.connect(self.appendText)
        
        self.setWindowTitle("Debug Output")
        
        layout = QVBoxLayout()
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text)
        
        self.text.setText(STREAM.logged)
        
        self.setLayout(layout)
        
    def appendText(self, text):
        self.text.append(text)
        
    @staticmethod
    def openDebug(parent=None):
        dialog = DebugOutputDialog(parent)
        dialog.show()