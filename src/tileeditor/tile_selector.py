from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtGui import QBrush, QPixmap
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGraphicsScene,
                               QGraphicsSceneMouseEvent)

from src.coilsnake.project_data import ProjectData
from src.misc.coords import EBCoords
from src.objects.tile import MapEditorTile

if TYPE_CHECKING:
    from tile_editor import TileEditor


# TODO merge a looooot of this code with tile_sidebar.py's tile selector to create a generic tile selector 
class TileScene(QGraphicsScene):
    tileSelected = Signal(int)
    TILE_COUNT = 960
    TILE_HEIGHT = 5 # should be a factor of TILE_COUNT
    
    def __init__(self, parent, projectData: ProjectData):
        super().__init__(parent)
        
        self.projectData = projectData
        self.currentTile = 0
        
        self.setSceneRect(0, 0, 32*self.TILE_COUNT//self.TILE_HEIGHT, 32*self.TILE_HEIGHT)
        
        self.setBackgroundBrush(
            QBrush(QPixmap(":/ui/bg.png")))
        
        self.tiles: list[MapEditorTile] = []
        x = 0
        y = 0
        for i in range(0, self.TILE_COUNT):
            item = MapEditorTile(EBCoords.fromTile(x, y))
            item.setText(str(i).zfill(3))
            self.addItem(item)
            self.tiles.append(item)
            
            y += 1 # could do this via some maths but w/e
            if y >= self.TILE_HEIGHT:
                y = 0
                x += 1
        
        self.selectedIndicator = QGraphicsPixmapItem()
        self.selectedIndicator.setPixmap(QPixmap(":/ui/selectTile.png"))
        self.selectedIndicator.setZValue(255)
        self.addItem(self.selectedIndicator)
        self.setForegroundBrush(QBrush(QPixmap(":/grids/32grid0.png")))
        
        self.renderTileset(0, 0, 0)
    
    def renderTileset(self, tilesetID: int, paletteGroupID: int, paletteID: int):
        tileset = self.projectData.getTileset(tilesetID)
        for id, i in enumerate(self.tiles):
            graphic = self.projectData.getTileGraphic(tilesetID, paletteGroupID, paletteID, id)
            if not graphic.hasRendered:
                graphic.render(tileset)
            i.setPixmap(graphic.rendered)
    
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        x, y = event.scenePos().toTuple()
        self.selectedIndicator.setPos(*EBCoords(x, y).roundToTile())
        items = self.items(event.scenePos())
        for i in items:
            if isinstance(i, MapEditorTile):
                self.currentTile = i.getID()
                self.tileSelected.emit(self.currentTile)
                break
    
    def selectTile(self, tile: int):
        if tile >= self.TILE_COUNT: raise ValueError(f"Tile must be in range 0-{self.TILE_COUNT}! Recieved {tile}")
        x = tile // self.TILE_HEIGHT
        y = tile % self.TILE_HEIGHT
        self.selectedIndicator.setPos(x*32, y*32)
        self.currentTile = tile
        self.tileSelected.emit(self.currentTile)
                
    def parent(self) -> "TileEditor": # for typing
        return super().parent()