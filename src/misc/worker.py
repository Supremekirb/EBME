# for threading

from PySide6.QtCore import QObject, Signal


class Worker(QObject):
    returns = Signal(object)
    updates = Signal(object)
    
    def __init__(self, process, *args):
        super().__init__()
        self.process = process
        self.args = args
    
    def run(self):
        self.process(self, *self.args)
