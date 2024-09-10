from typing import TYPE_CHECKING

from PySide6.QtGui import QBrush, QPixmap
from PySide6.QtWidgets import QGraphicsScene

from src.coilsnake.project_data import ProjectData

if TYPE_CHECKING:
    from tile_editor import TileEditor


class ArrangementScene(QGraphicsScene):
    SIZE_MULTIPLIER = 4
    
    def __init__(self, parent, projectData: ProjectData):
        super().__init__(parent)
        
        self.projectData = projectData
        
        self.setSceneRect(0, 0, 32*self.SIZE_MULTIPLIER, 32*self.SIZE_MULTIPLIER)
        
        self.setBackgroundBrush(
            QBrush(QPixmap(":/ui/bg.png")))
        
    def parent(self) -> "TileEditor": # for typing
        return super().parent()