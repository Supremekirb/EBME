from typing import TYPE_CHECKING

from PySide6.QtGui import QBrush, QPixmap
from PySide6.QtWidgets import QGraphicsScene

from src.coilsnake.project_data import ProjectData

if TYPE_CHECKING:
    from tile_editor import TileEditor


class TileScene(QGraphicsScene):
    TILE_COUNT = 960
    TILE_HEIGHT = 4
    
    def __init__(self, parent, projectData: ProjectData):
        super().__init__(parent)
        
        self.projectData = projectData
        
        self.setSceneRect(0, 0, 32*self.TILE_COUNT//self.TILE_HEIGHT, 32*self.TILE_HEIGHT)
        
        self.setBackgroundBrush(
            QBrush(QPixmap(":/ui/bg.png")))
        
    def parent(self) -> "TileEditor": # for typing
        return super().parent()