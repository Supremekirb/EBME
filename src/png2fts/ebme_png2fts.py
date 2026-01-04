from PySide6.QtCore import (QObject, QProcess, QSettings, QTemporaryFile,
                            QThread, Signal)

import src.misc.common as common
from src.coilsnake.fts_interpreter import FullTileset
from src.coilsnake.project_data import ProjectData


class EBME_png2fts(QObject):
    """Qt (non-graphical) interface for using eb-png2fts.py"""

    failed = Signal()
    succeeded = Signal()
    newOutput = Signal(str)
    
    def convert(self, projectData: ProjectData, pngPath: str, tilesetNumber: int):
        self.temporaryMapFile = QTemporaryFile()
        self.temporaryMapFile.open()

        self.temporaryTilesetFile = QTemporaryFile()
        self.temporaryTilesetFile.open()

        self.projectData = projectData # remember for later
        self.tilesetNumber = tilesetNumber

        self.png2ftsThread = QThread()
        self.png2ftsProcess = QProcess()
        self.png2ftsProcess.setProgram("python") # TODO double-check if it's possible to use the bundled Python (it may not be?)
        
        self.convertedTileset: FullTileset|None = None

        userPath = QSettings().value("programs/png2fts", type=str)
        if userPath != "":
            self.png2ftsProcess.setArguments((userPath,))
        else: self.png2ftsProcess.setArguments((common.absolutePath("eb-png2fts/eb_png2fts.py"),))

        args = self.png2ftsProcess.arguments()
        args.extend([
                    '-t', str(tilesetNumber),
                    '-o', self.temporaryTilesetFile.fileName(),
                    '-m', self.temporaryMapFile.fileName(),
                    pngPath
                    ])
        
        self.png2ftsProcess.setArguments(args)

        # https://stackoverflow.com/a/18550580/15287613 (breaks compiled code)
        env = [env for env in QProcess.systemEnvironment() if not env.startswith('PYTHONHOME=')]
        self.png2ftsProcess.setEnvironment(env)
        
        self.png2ftsProcess.readyReadStandardOutput.connect(self.readpng2ftsOutput)
        self.png2ftsProcess.readyReadStandardError.connect(self.readpng2ftsError)
        self.png2ftsProcess.finished.connect(self.finishedConversion)
        self.png2ftsThread.started.connect(self.png2ftsProcess.start)
        
        self.png2ftsProcess.moveToThread(self.png2ftsThread)
        self.png2ftsThread.start()

    def finishedConversion(self):
        self.png2ftsThread.quit()

        if not self.png2ftsProcess.exitCode() != 0: # only if we didnt error
            with open(self.temporaryTilesetFile.fileName()) as tileset:
                self.convertedTileset = FullTileset(tileset.readlines(), self.tilesetNumber)
            self.succeeded.emit()
        else: self.failed.emit()

    def readpng2ftsOutput(self):
        self.newOutput.emit(self.png2ftsProcess.readAllStandardOutput().data().decode())

    def readpng2ftsError(self):
        self.newOutput.emit(self.png2ftsProcess.readAllStandardError().data().decode())

    def getMapFile(self) -> QTemporaryFile | None:
        try:
            return self.temporaryMapFile
        except AttributeError:
            return None